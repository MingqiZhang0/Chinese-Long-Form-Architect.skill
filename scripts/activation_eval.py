#!/usr/bin/env python3
"""Activation precision benchmark for the Chinese Long-Form Architect.

This harness does not simulate ChatGPT's platform trigger. It owns the gold
activation corpus, exports a blind packet for an external trigger evaluator,
and scores observed activation decisions as FP/FN evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS = ROOT / "assets/activation-evaluation/cases.json"
CATEGORIES = ("clear_positive", "clear_negative", "boundary", "near_miss")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_corpus(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    cases = data.get("cases")
    if data.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if data.get("categories") != list(CATEGORIES):
        errors.append(f"categories must be exactly {list(CATEGORIES)}")
    if not isinstance(data.get("decision_rule"), str) or not data.get("decision_rule", "").strip():
        errors.append("decision_rule must be a non-empty string")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        cases = []

    seen: set[str] = set()
    counts = {category: 0 for category in CATEGORIES}
    labels = {category: {True: 0, False: 0} for category in CATEGORIES}
    critical_positive = 0
    critical_negative = 0
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"case[{index}] must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"case[{index}] id must be a non-empty string")
            continue
        if case_id in seen:
            errors.append(f"duplicate case id: {case_id}")
        seen.add(case_id)
        category = case.get("category")
        if category not in CATEGORIES:
            errors.append(f"{case_id}: invalid category {category!r}")
            continue
        counts[category] += 1
        expected = case.get("expected_activate")
        if not isinstance(expected, bool):
            errors.append(f"{case_id}: expected_activate must be boolean")
        else:
            labels[category][expected] += 1
            if case.get("critical") is True:
                if expected:
                    critical_positive += 1
                else:
                    critical_negative += 1
        if not isinstance(case.get("critical"), bool):
            errors.append(f"{case_id}: critical must be boolean")
        if not isinstance(case.get("prompt"), str) or not case.get("prompt", "").strip():
            errors.append(f"{case_id}: prompt must be non-empty")
        if not isinstance(case.get("rationale"), str) or not case.get("rationale", "").strip():
            errors.append(f"{case_id}: rationale must be non-empty")

    for category in CATEGORIES:
        if counts[category] < 8:
            errors.append(f"{category}: expected at least 8 cases, found {counts[category]}")
    if labels["clear_positive"][False] != 0 or labels["clear_positive"][True] == 0:
        errors.append("clear_positive must contain only activation-positive cases")
    if labels["clear_negative"][True] != 0 or labels["clear_negative"][False] == 0:
        errors.append("clear_negative must contain only activation-negative cases")
    if labels["boundary"][True] == 0 or labels["boundary"][False] == 0:
        errors.append("boundary must contain both positive and negative cases")
    if labels["near_miss"][True] != 0 or labels["near_miss"][False] == 0:
        errors.append("near_miss must contain only non-activation cases")
    if critical_positive < 2 or critical_negative < 2:
        errors.append("corpus must contain multiple critical positive and critical negative sentinels")

    return {
        "ok": not errors,
        "errors": errors,
        "case_count": len(cases),
        "category_counts": counts,
        "critical_positive_count": critical_positive,
        "critical_negative_count": critical_negative,
    }


def blind_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": case["id"],
            "prompt": case["prompt"],
        }
        for case in data["cases"]
    ]


def load_predictions(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    value = json.loads(text)
    if isinstance(value, dict) and isinstance(value.get("predictions"), list):
        return value["predictions"]
    if isinstance(value, list):
        return value
    raise ValueError("predictions must be JSONL, a JSON list, or an object with predictions[]")


def score(data: dict[str, Any], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    validation = validate_corpus(data)
    if not validation["ok"]:
        return {"ok": False, "errors": validation["errors"]}

    errors: list[str] = []
    pred_map: dict[str, bool] = {}
    for index, row in enumerate(predictions):
        if not isinstance(row, dict):
            errors.append(f"prediction[{index}] must be an object")
            continue
        case_id = row.get("id")
        decision = row.get("activate")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"prediction[{index}] id must be a non-empty string")
            continue
        if case_id in pred_map:
            errors.append(f"duplicate prediction id: {case_id}")
        if not isinstance(decision, bool):
            errors.append(f"{case_id}: activate must be boolean")
            continue
        pred_map[case_id] = decision

    case_ids = {case["id"] for case in data["cases"]}
    missing = sorted(case_ids - pred_map.keys())
    extra = sorted(pred_map.keys() - case_ids)
    if missing:
        errors.append("missing predictions: " + ", ".join(missing))
    if extra:
        errors.append("unknown prediction ids: " + ", ".join(extra))
    if errors:
        return {"ok": False, "errors": errors, "missing": missing, "extra": extra}

    confusion = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    by_category = {
        category: {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "count": 0}
        for category in CATEGORIES
    }
    false_positives: list[str] = []
    false_negatives: list[str] = []
    critical_failures: list[str] = []

    for case in data["cases"]:
        expected = case["expected_activate"]
        actual = pred_map[case["id"]]
        category = case["category"]
        by_category[category]["count"] += 1
        if expected and actual:
            key = "tp"
        elif (not expected) and (not actual):
            key = "tn"
        elif (not expected) and actual:
            key = "fp"
            false_positives.append(case["id"])
        else:
            key = "fn"
            false_negatives.append(case["id"])
        confusion[key] += 1
        by_category[category][key] += 1
        if case.get("critical") is True and expected != actual:
            critical_failures.append(case["id"])

    tp, tn, fp, fn = (confusion[k] for k in ("tp", "tn", "fp", "fn"))
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0
    total = tp + tn + fp + fn
    return {
        "ok": True,
        "evaluation_id": data.get("evaluation_id"),
        "case_count": total,
        "confusion": confusion,
        "metrics": {
            "accuracy": (tp + tn) / total if total else 1.0,
            "precision": precision,
            "recall": recall,
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
        },
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "critical_failures": critical_failures,
        "critical_gate": "PASS" if not critical_failures else "FAIL",
        "by_category": by_category,
        "claim_boundary": "These metrics describe supplied activation decisions only; the harness does not simulate or certify the platform trigger model.",
    }


def selftest(data: dict[str, Any]) -> dict[str, Any]:
    validation = validate_corpus(data)
    if not validation["ok"]:
        return {"ok": False, "errors": validation["errors"]}
    perfect = [{"id": c["id"], "activate": c["expected_activate"]} for c in data["cases"]]
    perfect_report = score(data, perfect)
    checks: dict[str, bool] = {
        "perfect_zero_fp_fn": perfect_report.get("confusion") == {"tp": 14, "tn": 18, "fp": 0, "fn": 0},
        "perfect_gate_pass": perfect_report.get("critical_gate") == "PASS",
    }

    fp_predictions = [dict(row) for row in perfect]
    fp_id = next(c["id"] for c in data["cases"] if c["id"] == "AM01")
    for row in fp_predictions:
        if row["id"] == fp_id:
            row["activate"] = True
    fp_report = score(data, fp_predictions)
    checks["small_polish_false_positive_detected"] = (
        fp_report.get("confusion", {}).get("fp") == 1
        and fp_id in fp_report.get("false_positives", [])
        and fp_report.get("critical_gate") == "FAIL"
    )

    fn_predictions = [dict(row) for row in perfect]
    fn_id = "AP01"
    for row in fn_predictions:
        if row["id"] == fn_id:
            row["activate"] = False
    fn_report = score(data, fn_predictions)
    checks["long_form_false_negative_detected"] = (
        fn_report.get("confusion", {}).get("fn") == 1
        and fn_id in fn_report.get("false_negatives", [])
        and fn_report.get("critical_gate") == "FAIL"
    )

    packet = blind_rows(data)
    forbidden = {"expected_activate", "critical", "rationale", "decision_rule"}
    checks["blind_packet_hides_gold"] = all(not (forbidden & set(row)) for row in packet)
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "validation": validation,
        "perfect_report": perfect_report,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--json", action="store_true")

    p_build = sub.add_parser("build-blind")
    p_build.add_argument("--out", type=Path, required=True)
    p_build.add_argument("--json", action="store_true")

    p_score = sub.add_parser("score")
    p_score.add_argument("predictions", type=Path)
    p_score.add_argument("--require-critical-pass", action="store_true")
    p_score.add_argument("--json", action="store_true")

    p_selftest = sub.add_parser("selftest")
    p_selftest.add_argument("--json", action="store_true")

    args = parser.parse_args()
    data = load_json(args.corpus)

    if args.command == "validate":
        report = validate_corpus(data)
    elif args.command == "build-blind":
        report = validate_corpus(data)
        if report["ok"]:
            rows = blind_rows(data)
            write_jsonl(args.out, rows)
            report = {**report, "out": str(args.out), "row_count": len(rows)}
    elif args.command == "score":
        try:
            report = score(data, load_predictions(args.predictions))
            if args.require_critical_pass and report.get("ok") and report.get("critical_gate") != "PASS":
                report["ok"] = False
                report.setdefault("errors", []).append("critical activation sentinels failed")
        except (ValueError, json.JSONDecodeError) as exc:
            report = {"ok": False, "errors": [str(exc)]}
    else:
        report = selftest(data)

    json_mode = getattr(args, "json", False)
    if json_mode:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if report.get("ok"):
            print("PASS activation evaluation")
            if "confusion" in report:
                print(json.dumps(report["confusion"], ensure_ascii=False))
        else:
            print("FAIL activation evaluation")
            for error in report.get("errors", []):
                print(f"- {error}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
