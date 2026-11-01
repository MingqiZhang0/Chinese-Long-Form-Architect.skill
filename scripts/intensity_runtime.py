#!/usr/bin/env python3
"""Validate and inspect Reasoning Intensity control-plane artifacts.

This script is deliberately small. It validates the stable interoperability
contracts and performs conservative screening; it is not a learned scheduler,
a literary judge, or a canon writer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from capability_probe import CapabilityError, require_profile

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "assets" / "intensity-schemas"
CALIBRATION_DIR = ROOT / "assets" / "intensity-calibration"
TEMPLATE_DIR = ROOT / "assets" / "intensity-templates"

SCHEMAS = {
    "config": "intensity-config.schema.json",
    "proposal": "work-proposal.schema.json",
    "result": "work-result.schema.json",
    "trace": "trace-event.schema.json",
}

AUTH_ALLOWED = {
    "noncanonical": {"noncanonical"},
    "advisory": {"noncanonical", "advisory"},
    "validation": {"noncanonical", "advisory", "validation"},
    "delta_proposal": {"noncanonical", "advisory", "validation", "delta_proposal"},
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text[0] in "[{":
        value = json.loads(text)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
        if isinstance(value, dict):
            return [value]
        raise ValueError(f"{path}: JSON must be an object or array")
    rows: list[dict[str, Any]] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{lineno}: JSONL row must be an object")
        rows.append(value)
    return rows


def schema_validator(kind: str) -> Any:
    require_profile("intensity")
    from jsonschema import Draft202012Validator

    schema = load_json(SCHEMA_DIR / SCHEMAS[kind])
    return Draft202012Validator(schema)


def validation_errors(kind: str, value: Any) -> list[str]:
    validator = schema_validator(kind)
    rows = sorted(validator.iter_errors(value), key=lambda e: list(e.absolute_path))
    out: list[str] = []
    for err in rows:
        where = ".".join(str(x) for x in err.absolute_path) or "$"
        out.append(f"{where}: {err.message}")
    return out


def work_key(proposal: dict[str, Any]) -> str:
    basis = proposal.get("basis") if isinstance(proposal.get("basis"), dict) else {}
    normalized = {
        "capability_id": proposal.get("capability_id"),
        "operation_id": proposal.get("operation_id"),
        "target_refs": sorted(proposal.get("target_refs", [])),
        "dependency_fingerprint": basis.get("dependency_fingerprint"),
        "security_domain": basis.get("security_domain"),
    }
    raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_calibration(profile: str) -> dict[str, Any]:
    direct = CALIBRATION_DIR / f"{profile}.json"
    if not direct.exists() and profile == "default-v0.1":
        direct = CALIBRATION_DIR / "default-v0.1.json"
    if not direct.is_file():
        raise ValueError(f"unknown calibration profile: {profile}")
    value = load_json(direct)
    if not isinstance(value, dict):
        raise ValueError("calibration must be a JSON object")
    return value


def screen(config: dict[str, Any], proposals: list[dict[str, Any]]) -> dict[str, Any]:
    errs = validation_errors("config", config)
    if errs:
        raise ValueError("invalid config: " + "; ".join(errs))
    for proposal in proposals:
        e = validation_errors("proposal", proposal)
        if e:
            raise ValueError(f"invalid proposal {proposal.get('proposal_id')}: {'; '.join(e)}")

    calibration = load_calibration(str(config["calibration_profile"]))
    intensity = str(config["requested_intensity"])
    profiles = calibration.get("profiles", {})
    if intensity not in profiles:
        raise ValueError(f"calibration lacks intensity profile: {intensity}")
    allowed = set(profiles[intensity].get("proactive_scopes", []))

    requires_admission: list[str] = []
    eligible_optional: list[str] = []
    deferred_optional: list[str] = []
    duplicate_of: dict[str, str] = {}
    first_for_key: dict[str, str] = {}

    for proposal in proposals:
        pid = str(proposal["proposal_id"])
        key = work_key(proposal)
        if key in first_for_key:
            duplicate_of[pid] = first_for_key[key]
            continue
        first_for_key[key] = pid
        if proposal["necessity_claim"] != "optional":
            requires_admission.append(pid)
            continue
        scopes = set(proposal.get("semantic_scope", []))
        if scopes.issubset(allowed):
            eligible_optional.append(pid)
        else:
            deferred_optional.append(pid)

    return {
        "requested_intensity": intensity,
        "calibration_version": calibration.get("calibration_version"),
        "requires_admission": requires_admission,
        "eligible_optional": eligible_optional,
        "deferred_optional": deferred_optional,
        "duplicate_of": duplicate_of,
        "note": "Screening does not grant mandatory status and does not write canon.",
    }


def check_run(config: dict[str, Any], proposals: list[dict[str, Any]], results: list[dict[str, Any]], trace: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(f"config {x}" for x in validation_errors("config", config))
    pmap: dict[str, dict[str, Any]] = {}
    keys: dict[str, str] = {}
    for proposal in proposals:
        pid = str(proposal.get("proposal_id", "?"))
        errors.extend(f"proposal {pid} {x}" for x in validation_errors("proposal", proposal))
        if pid in pmap:
            errors.append(f"duplicate proposal_id: {pid}")
        pmap[pid] = proposal
        try:
            key = work_key(proposal)
            if key in keys:
                warnings.append(f"duplicate work key: {pid} duplicates {keys[key]}")
            else:
                keys[key] = pid
        except Exception as exc:
            errors.append(f"proposal {pid} cannot compute work key: {exc}")

    rids: set[str] = set()
    for result in results:
        rid = str(result.get("result_id", "?"))
        errors.extend(f"result {rid} {x}" for x in validation_errors("result", result))
        if rid in rids:
            errors.append(f"duplicate result_id: {rid}")
        rids.add(rid)
        pid = str(result.get("proposal_id", ""))
        proposal = pmap.get(pid)
        if proposal is None:
            errors.append(f"result {rid} references unknown proposal_id {pid}")
            continue
        if result.get("epoch_id") != proposal.get("epoch_id"):
            errors.append(f"result {rid} epoch differs from proposal {pid}")
        pb = proposal.get("basis", {})
        rb = result.get("basis", {})
        if pb.get("branch") != rb.get("branch"):
            errors.append(f"result {rid} branch differs from proposal {pid}")
        if pb.get("security_domain") != rb.get("security_domain"):
            errors.append(f"result {rid} crosses security domain without a new sanitized derivation")
        ceiling = str(proposal.get("authority_ceiling"))
        authority = str(result.get("authority"))
        if authority not in AUTH_ALLOWED.get(ceiling, set()):
            errors.append(f"result {rid} authority {authority} exceeds proposal ceiling {ceiling}")

    last_seq: dict[str, int] = {}
    for event in trace:
        seq = event.get("seq")
        run_id = str(event.get("run_id", "?"))
        errors.extend(f"trace {run_id}:{seq} {x}" for x in validation_errors("trace", event))
        if isinstance(seq, int):
            if run_id in last_seq and seq <= last_seq[run_id]:
                errors.append(f"trace sequence not strictly increasing for run {run_id}: {seq} after {last_seq[run_id]}")
            last_seq[run_id] = seq

    return errors, warnings


def emit_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def cmd_validate(kind: str, path: Path) -> int:
    value = load_json(path)
    errs = validation_errors(kind, value)
    if errs:
        for err in errs:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    print(f"OK: {kind} contract valid")
    return 0


def selftest() -> None:
    config = load_json(TEMPLATE_DIR / "intensity-config-template.json")
    proposal = load_json(TEMPLATE_DIR / "work-proposal-template.json")
    result = load_json(TEMPLATE_DIR / "work-result-template.json")
    trace = load_json(TEMPLATE_DIR / "trace-event-template.json")
    for kind, value in (("config", config), ("proposal", proposal), ("result", result), ("trace", trace)):
        errs = validation_errors(kind, value)
        if errs:
            raise AssertionError(f"template failed {kind} schema: {errs}")

    screened = screen(config, [proposal, dict(proposal, proposal_id="WORK-002")])
    assert screened["eligible_optional"] == ["WORK-001"]
    assert screened["duplicate_of"] == {"WORK-002": "WORK-001"}

    errs, warns = check_run(config, [proposal], [result], [trace])
    assert not errs, errs
    assert not warns, warns

    bad_result = json.loads(json.dumps(result))
    bad_result["basis"]["security_domain"] = "writer"
    errs, _ = check_run(config, [proposal], [bad_result], [trace])
    assert any("crosses security domain" in x for x in errs)

    bad_result = json.loads(json.dumps(result))
    bad_result["authority"] = "delta_proposal"
    errs, _ = check_run(config, [proposal], [bad_result], [trace])
    assert any("exceeds proposal ceiling" in x for x in errs)

    mandatory_trace = json.loads(json.dumps(trace))
    mandatory_trace["disposition"] = "mandatory"
    mandatory_trace["admission_basis"] = None
    assert validation_errors("trace", mandatory_trace)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Reasoning Intensity contract validator and conservative screener")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, kind in (("validate-config", "config"), ("validate-proposal", "proposal"), ("validate-result", "result"), ("validate-trace", "trace")):
        sp = sub.add_parser(name)
        sp.add_argument("path", type=Path)
        sp.set_defaults(kind=kind)
    explain = sub.add_parser("explain")
    explain.add_argument("level", choices=["low", "medium", "high", "xhigh", "max"])
    explain.add_argument("--calibration", default="default-v0.1")
    screening = sub.add_parser("screen")
    screening.add_argument("config", type=Path)
    screening.add_argument("proposals", type=Path)
    check = sub.add_parser("check-run")
    check.add_argument("config", type=Path)
    check.add_argument("proposals", type=Path)
    check.add_argument("results", type=Path)
    check.add_argument("trace", type=Path)
    sub.add_parser("selftest")
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        require_profile("intensity")
    except CapabilityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.cmd.startswith("validate-"):
        return cmd_validate(args.kind, args.path)
    if args.cmd == "explain":
        calibration = load_calibration(args.calibration)
        emit_json(calibration["profiles"][args.level])
        return 0
    if args.cmd == "screen":
        cfg = load_json(args.config)
        props = load_records(args.proposals)
        emit_json(screen(cfg, props))
        return 0
    if args.cmd == "check-run":
        cfg = load_json(args.config)
        props = load_records(args.proposals)
        results = load_records(args.results)
        trace = load_records(args.trace)
        errors, warnings = check_run(cfg, props, results, trace)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        if errors:
            for err in errors:
                print(f"ERROR: {err}", file=sys.stderr)
            return 1
        print("OK: intensity run contracts consistent")
        return 0
    if args.cmd == "selftest":
        selftest()
        print("OK: intensity runtime selftest passed")
        return 0
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
