#!/usr/bin/env python3
"""Create and update durable checkpoints for serial orchestration passes."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from orchestration_contract import EXECUTION_PROFILES
from validate_orchestration_run import OPERATION_VERSION, operation_view, sha256_file, OPERATION_TRANSITIONS

VALID_STATUS = {"PENDING", "RUNNING", "BLOCKED", "DONE", "REJECTED"}


def load_obj(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _portable_ref(resolved: Path, checkpoint: Path) -> str:
    base = checkpoint.resolve().parent
    resolved = resolved.resolve()
    try:
        relative = os.path.relpath(str(resolved), start=str(base))
    except ValueError:  # different drive on Windows
        return resolved.as_posix()
    return Path(relative).as_posix()


def canonical_cli_ref(ref: str | Path, checkpoint: Path) -> str:
    """Canonicalize a command-line artifact path, which is relative to the current cwd."""
    return _portable_ref(Path(ref).resolve(), checkpoint)


def canonical_stored_ref(ref: str | Path, checkpoint: Path) -> str:
    """Canonicalize a persisted artifact ref, whose relative form is checkpoint-relative."""
    path = Path(ref)
    if not path.is_absolute():
        path = checkpoint.resolve().parent / path
    return _portable_ref(path, checkpoint)


def canonical_ref_list(refs: list[Any], checkpoint: Path, *, stored: bool) -> list[str]:
    normalizer = canonical_stored_ref if stored else canonical_cli_ref
    result: list[str] = []
    seen: set[str] = set()
    for raw in refs:
        ref = normalizer(str(raw), checkpoint)
        if ref not in seen:
            result.append(ref)
            seen.add(ref)
    return result


def cmd_init(args: argparse.Namespace) -> int:
    profile = load_obj(args.profile)
    selected = profile.get("selected_profile")
    if not isinstance(selected, str) or not selected:
        raise ValueError("profile lacks selected_profile")
    if selected not in EXECUTION_PROFILES:
        raise ValueError(f"unknown selected_profile: {selected!r}")
    checkpoint = {
        "schema_version": "1.0.0",
        "run_id": args.run_id,
        "execution_profile": selected,
        "branch": args.branch,
        "runtime_head": args.runtime_head,
        "last_completed_pass": None,
        "active_pass": None,
        "pending_passes": list(args.pass_ids),
        "pass_envelopes": canonical_ref_list(list(args.pass_envelopes or []), args.output, stored=False),
        "status": "PENDING",
        "blockers": [],
        "operational_version": OPERATION_VERSION,
        "operations": {pid: {
            "operational_version": OPERATION_VERSION, "operation_id": pid,
            "operation_type": "delegated-task", "status": "PLANNED", "transitions": ["PLANNED"],
        } for pid in args.pass_ids},
    }
    atomic_write(args.output, checkpoint)
    print(f"initialized checkpoint {args.output} with {len(args.pass_ids)} pending pass(es)")
    return 0


def cmd_set_active(args: argparse.Namespace) -> int:
    data = load_obj(args.checkpoint)
    pending = data.get("pending_passes", [])
    if not isinstance(pending, list):
        raise ValueError("checkpoint pending_passes must be a list")
    if args.pass_id not in {str(x) for x in pending}:
        raise ValueError(f"pass {args.pass_id!r} is not pending")
    if data.get("active_pass") not in {None, args.pass_id}:
        raise ValueError(f"another pass is already active: {data.get('active_pass')!r}")
    if not args.started_evidence or not args.root:
        raise ValueError("set-active requires --started-evidence and --root; a scheduling flag is not invocation")
    if "operational_version" not in data:
        raise ValueError("legacy checkpoint is read-only for new claims; initialize a new run")
    operation = dict(data["operations"][args.pass_id])
    if operation["status"] != "PLANNED":
        raise ValueError("pass must be PLANNED before start")
    evidence = args.started_evidence.resolve()
    operation.update(status="RUNNING", started_evidence={"ref": evidence.relative_to(args.root.resolve()).as_posix(), "sha256": sha256_file(evidence)}, transitions=["PLANNED", "RUNNING"])
    view = operation_view(operation, args.root.resolve())
    if view["errors"]:
        raise ValueError("; ".join(view["errors"]))
    data["operations"][args.pass_id] = operation
    data["active_pass"] = args.pass_id
    data["status"] = "RUNNING"
    atomic_write(args.checkpoint, data)
    print(f"active pass: {args.pass_id}")
    return 0


def cmd_complete(args: argparse.Namespace) -> int:
    data = load_obj(args.checkpoint)
    envelope = load_obj(args.pass_envelope)
    pass_id = str(envelope.get("pass_id", ""))
    if not pass_id:
        raise ValueError("pass envelope lacks pass_id")
    if envelope.get("status") not in {"DONE", "VERIFIED"}:
        raise ValueError("pass envelope must be DONE/VERIFIED before checkpoint completion")
    if not args.root or "operational_version" not in data:
        raise ValueError("new completion requires --root and a versioned checkpoint; legacy history remains unchanged")
    if envelope.get("operation_id") != pass_id:
        raise ValueError("pass/operation identity mismatch")
    store_operation(data, envelope, args.root.resolve())
    active = data.get("active_pass")
    if active not in {None, pass_id}:
        raise ValueError(f"checkpoint active_pass is {active!r}, not {pass_id!r}")
    pending = data.get("pending_passes", [])
    if not isinstance(pending, list):
        raise ValueError("checkpoint pending_passes must be a list")
    data["pending_passes"] = [x for x in pending if str(x) != pass_id]
    data["last_completed_pass"] = pass_id
    data["active_pass"] = None
    if args.runtime_head is not None:
        data["runtime_head"] = args.runtime_head
    refs = data.get("pass_envelopes", [])
    if not isinstance(refs, list):
        refs = []
    refs = canonical_ref_list(refs, args.checkpoint, stored=True)
    ref = canonical_cli_ref(args.pass_envelope, args.checkpoint)
    if ref not in refs:
        refs.append(ref)
    data["pass_envelopes"] = refs
    data["status"] = "DONE" if not data["pending_passes"] else "PENDING"
    atomic_write(args.checkpoint, data)
    print(f"completed pass: {pass_id}; remaining={len(data['pending_passes'])}")
    return 0


def cmd_block(args: argparse.Namespace) -> int:
    data = load_obj(args.checkpoint)
    data["active_pass"] = args.pass_id
    data["status"] = "BLOCKED"
    blockers = data.get("blockers", [])
    if not isinstance(blockers, list):
        blockers = []
    blockers.append({"pass_id": args.pass_id, "reason": args.reason})
    data["blockers"] = blockers
    atomic_write(args.checkpoint, data)
    print(f"blocked pass: {args.pass_id}")
    return 0


def store_operation(data: dict[str, Any], record: dict[str, Any], root: Path) -> None:
    """Accept only evidence-backed adjacent transitions or exact idempotent retry."""
    if data.get("operational_version") != OPERATION_VERSION:
        raise ValueError("new claims require a versioned checkpoint")
    view = operation_view(record, root)
    if view["errors"] or "operational_version" not in record:
        raise ValueError("; ".join(view["errors"]) or "legacy record cannot support a new claim")
    op_id = record["operation_id"]
    old = data.get("operations", {}).get(op_id)
    if old is None:
        if record["status"] != "PLANNED":
            raise ValueError("register PLANNED before invocation")
    elif old != record:
        before, after = old["status"], record["status"]
        if before == after and {k: v for k, v in old.items() if k != "reports"} == {k: v for k, v in record.items() if k != "reports"}:
            data["operations"][op_id] = record
            return
        if after not in OPERATION_TRANSITIONS.get(before, set()):
            raise ValueError(f"illegal checkpoint transition {before}->{after}")
        if record["transitions"] != old["transitions"] + [after]:
            raise ValueError("transition history cannot be rewritten")
        for field in ("operation_id", "operation_type", "started_evidence", "completion_evidence"):
            if field in old and record.get(field) != old[field]:
                raise ValueError(f"cannot rewrite {field} during transition")
    data.setdefault("operations", {})[op_id] = record


def cmd_record_operation(args: argparse.Namespace) -> int:
    data = load_obj(args.checkpoint)
    record = load_obj(args.record)
    store_operation(data, record, args.root.resolve())
    atomic_write(args.checkpoint, data)
    print(f"recorded operation {record['operation_id']}: {record['status']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage orchestration run checkpoints")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="initialize a run checkpoint")
    p_init.add_argument("--profile", type=Path, required=True)
    p_init.add_argument("--run-id", required=True)
    p_init.add_argument("--branch", default="main")
    p_init.add_argument("--runtime-head")
    p_init.add_argument("--pass-id", dest="pass_ids", action="append", default=[])
    p_init.add_argument("--pass-envelope", dest="pass_envelopes", action="append", default=[])
    p_init.add_argument("--output", type=Path, required=True)
    p_init.set_defaults(func=cmd_init)

    p_active = sub.add_parser("set-active", help="mark one pending pass active")
    p_active.add_argument("checkpoint", type=Path)
    p_active.add_argument("pass_id")
    p_active.add_argument("--started-evidence", type=Path)
    p_active.add_argument("--root", type=Path)
    p_active.set_defaults(func=cmd_set_active)

    p_complete = sub.add_parser("complete", help="complete a pass from a DONE pass envelope")
    p_complete.add_argument("checkpoint", type=Path)
    p_complete.add_argument("pass_envelope", type=Path)
    p_complete.add_argument("--runtime-head")
    p_complete.add_argument("--root", type=Path)
    p_complete.set_defaults(func=cmd_complete)

    p_block = sub.add_parser("block", help="record a blocking pass")
    p_block.add_argument("checkpoint", type=Path)
    p_block.add_argument("pass_id")
    p_block.add_argument("reason")
    p_block.set_defaults(func=cmd_block)

    p_record = sub.add_parser("record-operation", help="register or advance an evidence-backed operation in the existing run")
    p_record.add_argument("checkpoint", type=Path)
    p_record.add_argument("record", type=Path)
    p_record.add_argument("--root", type=Path, required=True)
    p_record.set_defaults(func=cmd_record_operation)

    args = parser.parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
