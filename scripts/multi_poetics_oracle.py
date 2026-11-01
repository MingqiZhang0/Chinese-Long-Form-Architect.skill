#!/usr/bin/env python3
"""Executable Multi-Poetics Behavioural Oracle maintenance harness.

The harness proves more than static fixture diversity without pretending that
regexes can judge literature. It validates registered adversarial fixtures, builds
exact target-generation packets, runs conservative deterministic assertions,
and creates blinded pointwise + swapped-order pairwise judge packets.

No model API is called here. Judge responses are imported explicitly so model
identity, independence, and uncertainty remain auditable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "multi-poetics-behavioral-oracle"
MANIFEST_PATH = ASSET_ROOT / "manifest.json"
SCHEMA_PATH = ASSET_ROOT / "oracle.schema.json"
FIXTURE_ROOT = ROOT / "assets" / "regression-corpora"
STAGE: str | None = None


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_no}: JSONL row must be an object")
            row["__line__"] = line_no
            rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def manifest() -> dict[str, Any]:
    return load_json(MANIFEST_PATH)


def fixture_names() -> list[str]:
    data = manifest()
    names = data.get("qualification_fixtures" if STAGE else "fixtures", [])
    if not isinstance(names, list):
        raise ValueError("oracle manifest fixtures must be an array")
    return [str(x) for x in names]


def fixture_dir(fixture_id: str) -> Path:
    return FIXTURE_ROOT / fixture_id


def fixture_oracle(fixture_id: str) -> dict[str, Any]:
    if STAGE:
        return load_json(fixture_dir(fixture_id) / "qualification.json")[STAGE]
    return load_json(fixture_dir(fixture_id) / "oracle.json")


def read_ref(fixture_id: str, oracle: dict[str, Any], key: str) -> str:
    rel = oracle["refs"][key]
    return (fixture_dir(fixture_id) / rel).read_text(encoding="utf-8")


def validate_suite() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    required_common = {"README.md", "manifest.json", "oracle.schema.json"}
    for name in sorted(required_common):
        if not (ASSET_ROOT / name).is_file():
            errors.append(f"missing oracle asset: assets/multi-poetics-behavioral-oracle/{name}")
    if errors:
        return {"passed": False, "errors": errors, "warnings": warnings}

    data = manifest()
    if data.get("schema_version") != "1.0.0":
        errors.append("oracle manifest schema_version must be 1.0.0")
    names = fixture_names()
    if len(names) < 10 or len(set(names)) != len(names):
        errors.append("oracle manifest must register at least ten unique fixtures including reverse controls")

    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    all_forbidden_classes: set[str] = set()
    profiles: set[tuple[str, ...]] = set()

    for fid in names:
        fdir = fixture_dir(fid)
        if not fdir.is_dir():
            errors.append(f"missing fixture directory: {fid}")
            continue
        opath = fdir / ("qualification.json" if STAGE else "oracle.json")
        if not opath.is_file():
            errors.append(f"{fid}: missing oracle.json")
            continue
        try:
            oracle = fixture_oracle(fid)
        except Exception as exc:
            errors.append(f"{fid}: invalid oracle JSON: {exc}")
            continue
        for err in sorted(validator.iter_errors(oracle), key=lambda x: list(x.path)):
            loc = ".".join(str(x) for x in err.path) or "<root>"
            errors.append(f"{fid}: oracle schema {loc}: {err.message}")
        if oracle.get("fixture_id") != fid:
            errors.append(f"{fid}: oracle fixture_id mismatch")
        refs = oracle.get("refs", {})
        for key in ("input", "task", "project_poetics", "positive_control", "wrong_poetics_mutant"):
            rel = refs.get(key)
            if not isinstance(rel, str) or not rel:
                errors.append(f"{fid}: missing refs.{key}")
                continue
            path = fdir / rel
            if not path.is_file():
                errors.append(f"{fid}: missing referenced artifact {rel}")
        ids: list[str] = []
        for field in ("must_preserve", "allowed_interventions", "forbidden_interventions", "deterministic_assertions"):
            rows = oracle.get(field, [])
            if isinstance(rows, list):
                ids.extend(str(x.get("id")) for x in rows if isinstance(x, dict))
        if len(ids) != len(set(ids)):
            errors.append(f"{fid}: assertion IDs must be unique within a fixture")
        classes = tuple(sorted(str(x.get("intervention_class")) for x in oracle.get("forbidden_interventions", []) if isinstance(x, dict)))
        if not classes:
            errors.append(f"{fid}: no forbidden intervention classes")
        profiles.add(classes)
        all_forbidden_classes.update(classes)
        try:
            src = read_ref(fid, oracle, "input")
            pos = read_ref(fid, oracle, "positive_control")
            neg = read_ref(fid, oracle, "wrong_poetics_mutant")
            if pos == neg:
                errors.append(f"{fid}: positive control and wrong mutant are identical")
            if src == neg:
                errors.append(f"{fid}: wrong mutant does not mutate input")
        except Exception as exc:
            errors.append(f"{fid}: cannot read fixture refs: {exc}")

    if len(profiles) < 8:
        errors.append("forbidden-intervention profiles collapsed to fewer than eight distinct signatures")
    if len(all_forbidden_classes) < 10:
        warnings.append("forbidden-intervention taxonomy has fewer than ten distinct classes; inspect flattening sensitivity")
    return {
        "passed": not errors,
        "fixture_count": len(names),
        "forbidden_intervention_classes": sorted(all_forbidden_classes),
        "distinct_forbidden_profiles": len(profiles),
        "errors": errors,
        "warnings": warnings,
    }


def paragraph_count(text: str) -> int:
    return len([x for x in re.split(r"\n\s*\n", text.strip()) if x.strip()])


def nonspace_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def run_assertion(assertion: dict[str, Any], candidate: str, source: str) -> tuple[bool, str]:
    kind = assertion["kind"]
    aid = assertion["id"]
    if kind == "regex_absent":
        found = re.search(assertion["pattern"], candidate, flags=re.MULTILINE) is not None
        return (not found, f"{aid}: forbidden pattern {'found' if found else 'absent'}")
    if kind == "regex_present":
        found = re.search(assertion["pattern"], candidate, flags=re.MULTILINE) is not None
        return (found, f"{aid}: required pattern {'found' if found else 'missing'}")
    if kind == "contains_all":
        missing = [x for x in assertion["values"] if x not in candidate]
        return (not missing, f"{aid}: missing literals {missing}" if missing else f"{aid}: required anchors preserved")
    if kind == "contains_any":
        found = [x for x in assertion["values"] if x in candidate]
        return (bool(found), f"{aid}: matching anchors {found}" if found else f"{aid}: none of required alternatives present")
    if kind == "char_ratio":
        denom = max(1, nonspace_len(source))
        ratio = nonspace_len(candidate) / denom
        ok = float(assertion["min"]) <= ratio <= float(assertion["max"])
        return (ok, f"{aid}: nonspace length ratio={ratio:.3f}, allowed=[{assertion['min']}, {assertion['max']}]")
    if kind == "paragraph_count":
        count = paragraph_count(candidate)
        ok = int(assertion["min"]) <= count <= int(assertion["max"])
        return (ok, f"{aid}: paragraph_count={count}, allowed=[{assertion['min']}, {assertion['max']}]")
    return (False, f"{aid}: unsupported assertion kind {kind}")


def deterministic_result(fid: str, candidate: str) -> dict[str, Any]:
    oracle = fixture_oracle(fid)
    source = read_ref(fid, oracle, "input")
    checks = []
    critical_failures = []
    for assertion in oracle["deterministic_assertions"]:
        ok, detail = run_assertion(assertion, candidate, source)
        row = {"id": assertion["id"], "kind": assertion["kind"], "critical": bool(assertion.get("critical")), "passed": ok, "detail": detail}
        checks.append(row)
        if not ok and row["critical"]:
            critical_failures.append(assertion["id"])
    return {
        "fixture_id": fid,
        "candidate_sha256": sha256_text(candidate),
        "passed": not critical_failures,
        "critical_failures": critical_failures,
        "checks": checks,
        "scope_note": "PASS means only that conservative mechanical checks passed; literary/poetics adequacy still requires blinded model or human evaluation.",
    }


def check_candidate_dir(candidate_dir: Path) -> dict[str, Any]:
    results = []
    errors = []
    for fid in fixture_names():
        path = candidate_dir / f"{fid}.md"
        if not path.is_file():
            errors.append(f"missing candidate file: {path}")
            continue
        results.append(deterministic_result(fid, path.read_text(encoding="utf-8")))
    return {
        "passed": not errors and all(x["passed"] for x in results),
        "candidate_dir": str(candidate_dir),
        "fixture_results": results,
        "errors": errors,
        "evidence_class": "deterministic-only",
        "promotion_note": "Do not treat deterministic-only PASS as a Multi-Poetics behavioural promotion result.",
    }


def build_generation_packet(out: Path) -> dict[str, Any]:
    rows = []
    for fid in fixture_names():
        oracle = fixture_oracle(fid)
        rows.append({
            "schema_version": "1.0.0",
            "fixture_id": fid,
            "project_poetics": read_ref(fid, oracle, "project_poetics"),
            "task": read_ref(fid, oracle, "task"),
            "input": read_ref(fid, oracle, "input"),
            "output_filename": f"{fid}.md",
            "targeted_local_defect": oracle["targeted_local_defect"],
            "provenance": {"stage": STAGE or "revision", "fixture_oracle_sha256": hashlib.sha256((fixture_dir(fid) / ("qualification.json" if STAGE else "oracle.json")).read_bytes()).hexdigest()},
        })
    write_jsonl(out, rows)
    return {"passed": True, "items": len(rows), "out": str(out)}


def blind_item_id(seed: int, fid: str, kind: str, order: int = 0) -> str:
    raw = f"{seed}|{fid}|{kind}|{order}".encode("utf-8")
    return "MPO-" + hashlib.sha256(raw).hexdigest()[:16]


def visible_context(fid: str, oracle: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_poetics": read_ref(fid, oracle, "project_poetics"),
        "task": read_ref(fid, oracle, "task"),
        "input": read_ref(fid, oracle, "input"),
        "must_preserve": [{"id": x["id"], "description": x["description"]} for x in oracle["must_preserve"]],
        "allowed_interventions": [{"id": x["id"], "description": x["description"]} for x in oracle["allowed_interventions"]],
        "forbidden_interventions": [{"id": x["id"], "description": x["description"]} for x in oracle["forbidden_interventions"]],
        "judge_instructions": {
            "principle": "Judge this project by its declared poetics, not by a universal preference for more plot, explanation, balance, symbolism, polish, or worldbuilding.",
            "pointwise_first": "For pointwise items, evaluate the candidate independently against the checklist before seeing any opponent.",
            "pairwise": oracle["model_evaluation"]["pairwise_question"],
            "tie_policy": oracle["model_evaluation"]["tie_policy"],
            "anti_bias": "Do not reward a candidate merely for being longer, more explicit, more conventionally polished, more dramatic, or more authoritative in tone.",
        },
    }


def build_blind(candidate_dir: Path, out: Path, key_out: Path, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    packet: list[dict[str, Any]] = []
    key: list[dict[str, Any]] = []
    for idx, fid in enumerate(fixture_names(), 1):
        oracle = fixture_oracle(fid)
        cpath = candidate_dir / f"{fid}.md"
        if not cpath.is_file():
            raise ValueError(f"missing candidate file: {cpath}")
        target = cpath.read_text(encoding="utf-8")
        positive = read_ref(fid, oracle, "positive_control")
        mutant = read_ref(fid, oracle, "wrong_poetics_mutant")
        case_token = f"CASE-{idx:02d}"
        context = visible_context(fid, oracle)

        item_id = blind_item_id(seed, fid, "pointwise-target")
        packet.append({
            "schema_version": "1.0.0", "item_id": item_id, "case_token": case_token, "mode": "pointwise",
            "context": context, "candidate": target,
            "response_contract": {
                "judge_id": "string", "item_id": item_id, "mode": "pointwise",
                "must_preserve": "object mapping P* -> pass|fail|uncertain",
                "forbidden": "object mapping F* -> clear|triggered|uncertain",
                "hard_integrity": "pass|fail|uncertain", "task_compliance": "pass|fail|uncertain",
                "overall": "preserves|violates|uncertain",
                "observed_intervention_classes": "optional array of short generic intervention labels",
                "rationale": "brief evidence-based explanation"
            }
        })
        key.append({"item_id": item_id, "fixture_id": fid, "mode": "pointwise", "candidate_role": "target"})

        for kind, arole, atext, brole, btext in (
            ("calibration", "positive-control", positive, "wrong-mutant", mutant),
            ("target-vs-mutant", "target", target, "wrong-mutant", mutant),
        ):
            first_left = rng.choice([True, False])
            orders = [(arole, atext, brole, btext), (brole, btext, arole, atext)] if first_left else [(brole, btext, arole, atext), (arole, atext, brole, btext)]
            for order, (lrole, ltext, rrole, rtext) in enumerate(orders):
                item_id = blind_item_id(seed, fid, kind, order)
                packet.append({
                    "schema_version": "1.0.0", "item_id": item_id, "case_token": case_token, "mode": "pairwise",
                    "comparison_token": hashlib.sha256(f"{seed}|{fid}|{kind}".encode()).hexdigest()[:12],
                    "context": context, "left": ltext, "right": rtext,
                    "response_contract": {"judge_id": "string", "item_id": item_id, "mode": "pairwise", "winner": "left|right|tie", "confidence": "high|medium|low", "rationale": "brief evidence-based explanation"}
                })
                key.append({"item_id": item_id, "fixture_id": fid, "mode": "pairwise", "comparison_kind": kind, "left_role": lrole, "right_role": rrole, "preferred_role_if_contract_satisfied": "positive-control" if kind == "calibration" else "target"})

    write_jsonl(out, packet)
    write_jsonl(key_out, key)
    return {"passed": True, "items": len(packet), "key_items": len(key), "fixtures": len(fixture_names()), "out": str(out), "key_out": str(key_out), "seed": seed}


def resolve_pairwise_role(response: dict[str, Any], key: dict[str, Any]) -> str | None:
    winner = response.get("winner")
    if winner == "left":
        return str(key["left_role"])
    if winner == "right":
        return str(key["right_role"])
    if winner == "tie":
        return None
    raise ValueError(f"invalid pairwise winner {winner!r}")


def validate_pointwise_response(response: dict[str, Any], oracle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    must = response.get("must_preserve")
    forbidden = response.get("forbidden")
    if not isinstance(must, dict):
        errors.append("must_preserve must be an object")
    else:
        for row in oracle["must_preserve"]:
            if must.get(row["id"]) not in {"pass", "fail", "uncertain"}:
                errors.append(f"must_preserve.{row['id']} invalid/missing")
    if not isinstance(forbidden, dict):
        errors.append("forbidden must be an object")
    else:
        for row in oracle["forbidden_interventions"]:
            if forbidden.get(row["id"]) not in {"clear", "triggered", "uncertain"}:
                errors.append(f"forbidden.{row['id']} invalid/missing")
    if response.get("hard_integrity") not in {"pass", "fail", "uncertain"}:
        errors.append("hard_integrity invalid/missing")
    if response.get("task_compliance") not in {"pass", "fail", "uncertain"}:
        errors.append("task_compliance invalid/missing")
    if response.get("overall") not in {"preserves", "violates", "uncertain"}:
        errors.append("overall invalid/missing")
    tags = response.get("observed_intervention_classes", [])
    if not isinstance(tags, list) or any(not isinstance(x, str) for x in tags):
        errors.append("observed_intervention_classes must be an array of strings")
    return errors


def individual_pointwise_status(response: dict[str, Any], oracle: dict[str, Any]) -> str:
    must = response["must_preserve"]
    forbidden = response["forbidden"]
    if response["hard_integrity"] == "fail" or response["task_compliance"] == "fail" or response["overall"] == "violates":
        return "fail"
    for row in oracle["must_preserve"]:
        if row.get("critical") and must[row["id"]] == "fail":
            return "fail"
    for row in oracle["forbidden_interventions"]:
        if row.get("critical") and forbidden[row["id"]] == "triggered":
            return "fail"
    vals = [response["hard_integrity"], response["task_compliance"], response["overall"]]
    vals += [must[row["id"]] for row in oracle["must_preserve"]]
    vals += [forbidden[row["id"]] for row in oracle["forbidden_interventions"]]
    if any(x == "uncertain" for x in vals):
        return "uncertain"
    return "pass"


def aggregate(responses_path: Path, key_path: Path, deterministic_path: Path | None, min_judges: int, consensus: float) -> dict[str, Any]:
    key_rows = load_jsonl(key_path)
    response_rows = load_jsonl(responses_path)
    key_by_id = {str(x["item_id"]): x for x in key_rows}
    errors: list[str] = []
    responses_by_judge_item: dict[tuple[str, str], dict[str, Any]] = {}

    for row in response_rows:
        item_id = str(row.get("item_id", ""))
        judge_id = str(row.get("judge_id", ""))
        if not item_id or item_id not in key_by_id:
            errors.append(f"line {row['__line__']}: unknown/missing item_id {item_id!r}")
            continue
        if not judge_id:
            errors.append(f"line {row['__line__']}: missing judge_id")
            continue
        key = key_by_id[item_id]
        if row.get("mode") != key.get("mode"):
            errors.append(f"line {row['__line__']}: mode mismatch for {item_id}")
            continue
        token = (judge_id, item_id)
        if token in responses_by_judge_item:
            errors.append(f"duplicate response for judge/item {judge_id}/{item_id}")
            continue
        if key["mode"] == "pairwise":
            if row.get("winner") not in {"left", "right", "tie"}:
                errors.append(f"line {row['__line__']}: invalid pairwise winner")
                continue
        else:
            oracle = fixture_oracle(str(key["fixture_id"]))
            errs = validate_pointwise_response(row, oracle)
            errors.extend(f"line {row['__line__']}: {e}" for e in errs)
            if errs:
                continue
        responses_by_judge_item[token] = row

    if errors:
        return {"passed": False, "errors": errors}

    det_by_fixture: dict[str, bool] = {}
    if deterministic_path:
        det = load_json(deterministic_path)
        for row in det.get("fixture_results", []):
            det_by_fixture[str(row["fixture_id"])] = bool(row.get("passed"))

    key_by_fixture: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in key_rows:
        key_by_fixture[str(row["fixture_id"])].append(row)
    judge_ids = sorted({judge for judge, _ in responses_by_judge_item})
    fixture_reports = []
    global_tags: dict[str, set[str]] = defaultdict(set)

    for fid in fixture_names():
        oracle = fixture_oracle(fid)
        keys = key_by_fixture[fid]
        pkey = next(x for x in keys if x["mode"] == "pointwise")
        cal_keys = [x for x in keys if x.get("comparison_kind") == "calibration"]
        target_keys = [x for x in keys if x.get("comparison_kind") == "target-vs-mutant"]
        judge_reports = []
        calibrated_count = 0
        strong_pass = 0
        strong_fail = 0
        uncertain = 0

        for judge in judge_ids:
            cal_resp = [responses_by_judge_item.get((judge, str(k["item_id"]))) for k in cal_keys]
            calibrated = False
            cal_reason = "incomplete"
            if all(cal_resp):
                winners = [resolve_pairwise_role(r, k) for r, k in zip(cal_resp, cal_keys)]
                if winners == ["positive-control", "positive-control"]:
                    calibrated = True
                    cal_reason = "consistent-positive-control"
                elif winners == [None, None]:
                    cal_reason = "calibration-tie"
                else:
                    cal_reason = "order-disagreement-or-wrong"
            if not calibrated:
                judge_reports.append({"judge_id": judge, "calibrated": False, "calibration": cal_reason, "status": "excluded"})
                continue
            calibrated_count += 1

            presp = responses_by_judge_item.get((judge, str(pkey["item_id"])))
            if presp is None:
                point_status = "uncertain"
                tags: list[str] = []
            else:
                point_status = individual_pointwise_status(presp, oracle)
                tags = [str(x) for x in presp.get("observed_intervention_classes", [])]
                for tag in tags:
                    global_tags[tag].add(fid)
                # Explicit forbidden hits also feed flattening diagnostics.
                for row in oracle["forbidden_interventions"]:
                    if presp.get("forbidden", {}).get(row["id"]) == "triggered":
                        global_tags[str(row["intervention_class"])].add(fid)

            target_resp = [responses_by_judge_item.get((judge, str(k["item_id"]))) for k in target_keys]
            pair_status = "uncertain"
            if all(target_resp):
                winners = [resolve_pairwise_role(r, k) for r, k in zip(target_resp, target_keys)]
                if winners == ["target", "target"]:
                    pair_status = "win"
                elif winners == ["wrong-mutant", "wrong-mutant"]:
                    pair_status = "loss"
            if point_status == "pass" and pair_status == "win":
                status = "pass"; strong_pass += 1
            elif point_status == "fail" or pair_status == "loss":
                status = "fail"; strong_fail += 1
            else:
                status = "uncertain"; uncertain += 1
            judge_reports.append({"judge_id": judge, "calibrated": True, "calibration": cal_reason, "pointwise": point_status, "pairwise": pair_status, "status": status, "observed_intervention_classes": tags})

        det_pass = det_by_fixture.get(fid)
        if det_pass is False:
            model_status = "fail"
            final_status = "fail"
            reason = "deterministic-critical-failure"
        elif calibrated_count < min_judges:
            model_status = "insufficient-evidence"
            final_status = "uncertain"
            reason = "too-few-calibrated-judges"
        else:
            pass_share = strong_pass / calibrated_count
            fail_share = strong_fail / calibrated_count
            if pass_share >= consensus:
                model_status = "pass"
                final_status = "pass" if det_pass is not False else "fail"
                reason = "calibrated-consensus-pass"
            elif fail_share >= consensus:
                model_status = "fail"
                final_status = "fail"
                reason = "calibrated-consensus-fail"
            else:
                model_status = "uncertain"
                final_status = "uncertain"
                reason = "judge-disagreement-or-ties"
        fixture_reports.append({
            "fixture_id": fid, "deterministic_pass": det_pass, "calibrated_judges": calibrated_count,
            "model_status": model_status, "final_status": final_status, "reason": reason,
            "judge_reports": judge_reports,
        })

    flattening = []
    for tag, fids in sorted(global_tags.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(fids) >= 3:
            flattening.append({"intervention_class": tag, "fixture_count": len(fids), "fixtures": sorted(fids), "status": "review"})

    final_counts = Counter(x["final_status"] for x in fixture_reports)
    passed = final_counts.get("fail", 0) == 0 and final_counts.get("uncertain", 0) == 0 and len(fixture_reports) == len(fixture_names())
    return {
        "passed": passed,
        "evidence_class": "deterministic+blinded-model" if deterministic_path else "blinded-model-only",
        "judge_ids": judge_ids,
        "minimum_calibrated_judges": min_judges,
        "consensus_threshold": consensus,
        "status_counts": dict(final_counts),
        "fixtures": fixture_reports,
        "cross_fixture_flattening_signals": flattening,
        "interpretation": "Cross-fixture flattening signals are diagnostic. Explicit fixture-specific forbidden hits are gating; a repeated generic intervention tag alone triggers review rather than an automatic literary verdict.",
        "errors": [],
    }


def make_control_dir(path: Path, role: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    ref_key = "positive_control" if role == "positive" else "wrong_poetics_mutant"
    for fid in fixture_names():
        oracle = fixture_oracle(fid)
        (path / f"{fid}.md").write_text(read_ref(fid, oracle, ref_key), encoding="utf-8")


def synthetic_responses(key_path: Path, judge_ids: list[str], *, order_biased_judge: str | None = None, repeated_tag: str | None = None) -> list[dict[str, Any]]:
    rows = []
    for key in load_jsonl(key_path):
        fid = str(key["fixture_id"])
        oracle = fixture_oracle(fid)
        for judge in judge_ids:
            if key["mode"] == "pointwise":
                rows.append({
                    "judge_id": judge, "item_id": key["item_id"], "mode": "pointwise",
                    "must_preserve": {x["id"]: "pass" for x in oracle["must_preserve"]},
                    "forbidden": {x["id"]: "clear" for x in oracle["forbidden_interventions"]},
                    "hard_integrity": "pass", "task_compliance": "pass", "overall": "preserves",
                    "observed_intervention_classes": [repeated_tag] if repeated_tag else [],
                    "rationale": "synthetic selftest response"
                })
            else:
                if judge == order_biased_judge:
                    winner = "left"
                else:
                    preferred = key["preferred_role_if_contract_satisfied"]
                    winner = "left" if key["left_role"] == preferred else "right"
                rows.append({"judge_id": judge, "item_id": key["item_id"], "mode": "pairwise", "winner": winner, "confidence": "high", "rationale": "synthetic selftest response"})
    return rows


def selftest() -> dict[str, Any]:
    validation = validate_suite()
    errors = list(validation.get("errors", []))
    control_results = []
    mutant_results = []
    for fid in fixture_names():
        oracle = fixture_oracle(fid)
        pos = deterministic_result(fid, read_ref(fid, oracle, "positive_control"))
        neg = deterministic_result(fid, read_ref(fid, oracle, "wrong_poetics_mutant"))
        control_results.append(pos)
        mutant_results.append(neg)
        if not pos["passed"]:
            errors.append(f"{fid}: positive control failed deterministic oracle: {pos['critical_failures']}")
        if neg["passed"]:
            errors.append(f"{fid}: wrong-poetics mutant survived every deterministic assertion")

    with tempfile.TemporaryDirectory(prefix="lwa-mpo-") as td:
        tmp = Path(td)
        cdir = tmp / "candidates"
        make_control_dir(cdir, "positive")
        det = check_candidate_dir(cdir)
        det_path = tmp / "det.json"; write_json(det_path, det)
        packet = tmp / "blind.jsonl"; key = tmp / "key.jsonl"
        build_blind(cdir, packet, key, 17)
        visible = packet.read_text(encoding="utf-8")
        for leaked in ("positive-control", "wrong-poetics-mutant", "control-preserving.md", "wrong-poetics-mutant.md"):
            if leaked in visible:
                errors.append(f"blind packet leaked hidden candidate role/provenance token: {leaked}")
        responses = synthetic_responses(key, ["J1", "J2", "J3"], order_biased_judge="J3")
        resp_path = tmp / "responses.jsonl"; write_jsonl(resp_path, responses)
        report = aggregate(resp_path, key, det_path, 2, 0.67)
        if not report.get("passed"):
            errors.append(f"calibrated synthetic panel did not pass positive controls: {report.get('status_counts')}")
        excluded = 0
        for fr in report.get("fixtures", []):
            excluded += sum(1 for jr in fr.get("judge_reports", []) if jr.get("judge_id") == "J3" and not jr.get("calibrated"))
        if excluded != len(fixture_names()):
            errors.append(f"order-biased judge was not excluded on all calibration pairs: excluded={excluded}")

        flatten_rows = synthetic_responses(key, ["J1", "J2"], repeated_tag="generic-explanation-expansion")
        flatten_path = tmp / "flatten.jsonl"; write_jsonl(flatten_path, flatten_rows)
        flatten_report = aggregate(flatten_path, key, det_path, 2, 0.67)
        if not flatten_report.get("cross_fixture_flattening_signals"):
            errors.append("cross-fixture repeated intervention signal was not surfaced")

    return {
        "passed": not errors,
        "validation": validation,
        "positive_controls_passed": sum(1 for x in control_results if x["passed"]),
        "wrong_mutants_killed": sum(1 for x in mutant_results if not x["passed"]),
        "blind_items_expected": 5 * len(fixture_names()),
        "errors": errors,
        "claim_boundary": "Selftest proves oracle mechanics, calibration, blinding, and known-mutant detection. It does not prove an unrun target model/Skill preserves poetics; real candidate outputs plus independent judge responses are required for that claim.",
    }


def emit(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        if isinstance(value, dict):
            print(json.dumps(value, ensure_ascii=False, indent=2))
        else:
            print(value)


def main() -> int:
    global STAGE
    parser = argparse.ArgumentParser(description="Run the Multi-Poetics Behavioural Oracle maintenance harness")
    parser.add_argument("--stage", choices=("planning", "chapter", "drafting"), help="use long-form qualification contracts; default is preservation revision")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("validate", help="validate registered fixture/oracle contracts")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("build-generation", help="emit exact target-Skill generation tasks as JSONL")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("check", help="run conservative deterministic assertions on target candidates")
    p.add_argument("--candidate-dir", type=Path, required=True)
    p.add_argument("--out", type=Path)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("build-blind", help="build blinded pointwise and swapped-order pairwise judge packets")
    p.add_argument("--candidate-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--key-out", type=Path, required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("aggregate", help="aggregate independent judge responses with calibration and uncertainty")
    p.add_argument("responses", type=Path)
    p.add_argument("key", type=Path)
    p.add_argument("--deterministic-report", type=Path)
    p.add_argument("--min-calibrated-judges", type=int, default=2)
    p.add_argument("--consensus", type=float, default=0.67)
    p.add_argument("--out", type=Path)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("selftest", help="verify controls, mutants, blinding, order-bias calibration, and flattening diagnostics")
    p.add_argument("--json", action="store_true")

    args = parser.parse_args()
    STAGE = args.stage
    if args.cmd == "validate":
        result = validate_suite()
    elif args.cmd == "build-generation":
        result = build_generation_packet(args.out)
    elif args.cmd == "check":
        result = check_candidate_dir(args.candidate_dir)
        if args.out:
            write_json(args.out, result)
    elif args.cmd == "build-blind":
        result = build_blind(args.candidate_dir, args.out, args.key_out, args.seed)
    elif args.cmd == "aggregate":
        if args.min_calibrated_judges < 1:
            raise SystemExit("--min-calibrated-judges must be >= 1")
        if not 0.5 < args.consensus <= 1.0:
            raise SystemExit("--consensus must be in (0.5, 1.0]")
        result = aggregate(args.responses, args.key, args.deterministic_report, args.min_calibrated_judges, args.consensus)
        if args.out:
            write_json(args.out, result)
    else:
        result = selftest()
    emit(result, getattr(args, "json", False))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
