#!/usr/bin/env python3
"""Unified Fast/Core/Full/Soak maintenance test runner.

Tier membership lives in assets/test-tier-contract.json. This runner executes
that contract without duplicating the semantic meaning of individual tests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
CONTRACT_PATH = ROOT / "assets" / "test-tier-contract.json"
EXPECTED_TIERS = ["fast", "core", "full", "soak"]
TAIL_LIMIT = 4000


def load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def contract_sha256() -> str:
    return hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest()


def integration_cases() -> set[str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "integration_selftest.py"), "--list"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cannot enumerate integration tests: {proc.stderr.strip()}")
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def step_argv(step: dict[str, Any]) -> list[str]:
    runner = step.get("runner")
    if runner == "integration_case":
        return [
            str(SCRIPT_DIR / "integration_selftest.py"),
            "--only",
            str(step["case"]),
        ]
    if runner == "command":
        raw = list(step.get("argv", []))
        if not raw:
            raise ValueError(f"step {step.get('id')} has empty argv")
        first = Path(str(raw[0]))
        if not first.parts or first.parts[0] != "scripts":
            raise ValueError(f"step {step.get('id')} command must start under scripts/: {raw[0]}")
        return [str(ROOT / first), *[str(x) for x in raw[1:]]]
    raise ValueError(f"step {step.get('id')} has unsupported runner: {runner}")


def validate_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if contract.get("tier_order") != EXPECTED_TIERS:
        errors.append(f"tier_order must be {EXPECTED_TIERS}")
    tiers = contract.get("tiers")
    if not isinstance(tiers, dict) or set(tiers) != set(EXPECTED_TIERS):
        errors.append("tiers must contain exactly fast/core/full/soak")
        return errors

    try:
        known_integration = integration_cases()
    except Exception as exc:
        known_integration = set()
        errors.append(str(exc))

    all_ids: set[str] = set()
    for tier_name in EXPECTED_TIERS:
        tier = tiers.get(tier_name, {})
        for field in ("purpose", "proves", "does_not_prove", "steps"):
            if not tier.get(field):
                errors.append(f"{tier_name}.{field} must be non-empty")
        budget = tier.get("target_runtime_seconds")
        if not isinstance(budget, int) or budget <= 0:
            errors.append(f"{tier_name}.target_runtime_seconds must be a positive integer")
        if tier_name == "fast" and tier.get("automatic_default") is not True:
            errors.append("fast must be the only automatic_default tier")
        if tier_name != "fast" and tier.get("automatic_default") is not False:
            errors.append(f"{tier_name} must not be automatic_default")

        local_ids: set[str] = set()
        for step in tier.get("steps", []):
            sid = step.get("id")
            if not isinstance(sid, str) or not sid:
                errors.append(f"{tier_name} contains a step without a non-empty id")
                continue
            if sid in local_ids:
                errors.append(f"{tier_name} duplicates step id {sid}")
            local_ids.add(sid)
            if sid in all_ids:
                errors.append(f"step id must be globally unique: {sid}")
            all_ids.add(sid)
            timeout = step.get("timeout_seconds")
            if not isinstance(timeout, int) or timeout <= 0:
                errors.append(f"{sid}.timeout_seconds must be a positive integer")
            runner = step.get("runner")
            if runner == "integration_case":
                case = step.get("case")
                if case not in known_integration:
                    errors.append(f"{sid} references unknown integration case: {case}")
            elif runner == "command":
                try:
                    argv = step_argv(step)
                except Exception as exc:
                    errors.append(str(exc))
                    continue
                script = Path(argv[0])
                if not script.is_file():
                    errors.append(f"{sid} backend does not exist: {script.relative_to(ROOT)}")
            else:
                errors.append(f"{sid} has unsupported runner: {runner}")

    return errors


def display_argv(step: dict[str, Any]) -> list[str]:
    if step.get("runner") == "integration_case":
        return ["scripts/integration_selftest.py", "--only", str(step["case"])]
    return [str(x) for x in step.get("argv", [])]


def tier_plan(contract: dict[str, Any], tier_name: str) -> dict[str, Any]:
    tier = contract["tiers"][tier_name]
    return {
        "contract_version": contract["schema_version"],
        "contract_sha256": contract_sha256(),
        "tier": tier_name,
        "purpose": tier["purpose"],
        "target_runtime_seconds": tier["target_runtime_seconds"],
        "automatic_default": tier["automatic_default"],
        "proves": tier["proves"],
        "does_not_prove": tier["does_not_prove"],
        "steps": [
            {
                "id": step["id"],
                "runner": step["runner"],
                "command": [sys.executable, *display_argv(step)],
                "timeout_seconds": step["timeout_seconds"],
            }
            for step in tier["steps"]
        ],
    }


def tail(text: str) -> str:
    text = text or ""
    if len(text) <= TAIL_LIMIT:
        return text
    return text[-TAIL_LIMIT:]


def run_step(step: dict[str, Any]) -> dict[str, Any]:
    argv = [sys.executable, *step_argv(step)]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=int(step["timeout_seconds"]),
        )
        elapsed = time.monotonic() - started
        status = "PASS" if proc.returncode == 0 else "FAIL"
        return {
            "id": step["id"],
            "status": status,
            "returncode": proc.returncode,
            "elapsed_seconds": round(elapsed, 3),
            "timeout_seconds": step["timeout_seconds"],
            "command": argv,
            "stdout_tail": tail(proc.stdout),
            "stderr_tail": tail(proc.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "id": step["id"],
            "status": "TIMEOUT",
            "returncode": None,
            "elapsed_seconds": round(elapsed, 3),
            "timeout_seconds": step["timeout_seconds"],
            "command": argv,
            "stdout_tail": tail(stdout),
            "stderr_tail": tail(stderr),
        }


def emit(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        if isinstance(value, str):
            print(value)
        else:
            print(json.dumps(value, ensure_ascii=False, indent=2))


def cmd_validate(as_json: bool) -> int:
    contract = load_contract()
    errors = validate_contract(contract)
    payload = {
        "contract_version": contract.get("schema_version"),
        "contract_sha256": contract_sha256(),
        "tiers": EXPECTED_TIERS,
        "errors": errors,
        "passed": not errors,
    }
    emit(payload, as_json)
    return 0 if not errors else 1


def cmd_list(as_json: bool) -> int:
    contract = load_contract()
    errors = validate_contract(contract)
    if errors:
        emit({"passed": False, "errors": errors}, as_json)
        return 1
    rows = [
        {
            "tier": name,
            "purpose": contract["tiers"][name]["purpose"],
            "target_runtime_seconds": contract["tiers"][name]["target_runtime_seconds"],
            "automatic_default": contract["tiers"][name]["automatic_default"],
            "step_count": len(contract["tiers"][name]["steps"]),
        }
        for name in EXPECTED_TIERS
    ]
    if as_json:
        emit(rows, True)
    else:
        for row in rows:
            default = " default" if row["automatic_default"] else ""
            print(f"{row['tier']:<5}  steps={row['step_count']:<2} target~{row['target_runtime_seconds']}s{default}  {row['purpose']}")
    return 0


def cmd_plan(tier_name: str, as_json: bool) -> int:
    contract = load_contract()
    errors = validate_contract(contract)
    if errors:
        emit({"passed": False, "errors": errors}, as_json)
        return 1
    plan = tier_plan(contract, tier_name)
    if as_json:
        emit(plan, True)
    else:
        print(f"tier: {tier_name}")
        print(f"purpose: {plan['purpose']}")
        print(f"target_runtime_seconds: {plan['target_runtime_seconds']}")
        for idx, step in enumerate(plan["steps"], 1):
            command = " ".join(step["command"])
            print(f"{idx}. {step['id']}  timeout={step['timeout_seconds']}s  {command}")
    return 0


def cmd_run(tier_name: str, as_json: bool, selected_step: str | None, continue_on_failure: bool) -> int:
    contract = load_contract()
    errors = validate_contract(contract)
    if errors:
        emit({"passed": False, "errors": errors}, as_json)
        return 1

    tier = contract["tiers"][tier_name]
    steps = list(tier["steps"])
    partial = selected_step is not None
    if selected_step is not None:
        steps = [step for step in steps if step["id"] == selected_step]
        if not steps:
            msg = f"unknown step for {tier_name}: {selected_step}"
            emit({"passed": False, "error": msg}, as_json)
            return 2

    results: list[dict[str, Any]] = []
    for step in steps:
        if not as_json:
            print(f"RUN  {step['id']}", flush=True)
        result = run_step(step)
        results.append(result)
        if not as_json:
            print(f"{result['status']:<7} {step['id']}  {result['elapsed_seconds']:.3f}s", flush=True)
            if result["status"] != "PASS":
                if result["stdout_tail"]:
                    print(result["stdout_tail"], flush=True)
                if result["stderr_tail"]:
                    print(result["stderr_tail"], file=sys.stderr, flush=True)
        if result["status"] != "PASS" and not continue_on_failure:
            break

    selected_passed = len(results) == len(steps) and all(r["status"] == "PASS" for r in results)
    payload = {
        "contract_version": contract["schema_version"],
        "contract_sha256": contract_sha256(),
        "tier": tier_name,
        "partial": partial,
        "selected_step": selected_step,
        "selected_passed": selected_passed,
        "tier_passed": bool(selected_passed and not partial),
        "completed_steps": len(results),
        "planned_steps": len(steps),
        "elapsed_seconds": round(sum(float(r["elapsed_seconds"]) for r in results), 3),
        "results": results,
        "claim": (
            f"{tier_name} tier PASS" if selected_passed and not partial
            else "partial selection passed; not a tier PASS" if selected_passed
            else f"{tier_name} tier did not pass"
        ),
    }
    if as_json:
        emit(payload, True)
    else:
        print(f"summary: {payload['claim']}; {payload['completed_steps']}/{payload['planned_steps']} selected steps completed")
    return 0 if selected_passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Fast/Core/Full/Soak maintenance test contract")
    sub = parser.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate")
    v.add_argument("--json", action="store_true")

    l = sub.add_parser("list")
    l.add_argument("--json", action="store_true")

    p = sub.add_parser("plan")
    p.add_argument("tier", choices=EXPECTED_TIERS)
    p.add_argument("--json", action="store_true")

    r = sub.add_parser("run")
    r.add_argument("tier", choices=EXPECTED_TIERS)
    r.add_argument("--step", help="run one named step for debugging; never counts as a tier PASS")
    r.add_argument("--continue-on-failure", action="store_true")
    r.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.cmd == "validate":
        return cmd_validate(args.json)
    if args.cmd == "list":
        return cmd_list(args.json)
    if args.cmd == "plan":
        return cmd_plan(args.tier, args.json)
    if args.cmd == "run":
        return cmd_run(args.tier, args.json, args.step, args.continue_on_failure)
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
