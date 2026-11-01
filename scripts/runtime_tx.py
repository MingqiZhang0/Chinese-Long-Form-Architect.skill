#!/usr/bin/env python3
"""Atomic optimistic-concurrency transaction commits for Narrative Runtime.

A transaction is validated against the branch head it read. The commit writes all
proposed events or none, and repeated identical transaction IDs are idempotent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from narrative_runtime import branch_map, effective_events, events_by_branch, load_json, load_jsonl, validate_runtime
from runtime_schema import DEFAULT_SCHEMA_DIR, schema_path, validate_instance
from validate_invariants import evaluate as evaluate_invariants
from event_provenance import promotion_errors


class TxError(RuntimeError):
    def __init__(self, message: str, code: str = "TRANSACTION_ERROR"):
        super().__init__(message)
        self.code = code


def save_transaction(path: Path, tx: dict[str, Any]) -> None:
    path.write_text(json.dumps(tx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def acquire_lock(path: Path) -> int:
    try:
        return os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError as exc:
        raise TxError(f"runtime write lock already exists: {path}") from exc


def release_lock(fd: int, path: Path) -> None:
    try:
        os.close(fd)
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def branch_head(events: list[dict[str, Any]], branches: dict[str, dict[str, Any]], branch: str) -> tuple[str | None, int]:
    hist = effective_events(branch, branches, events_by_branch(events))
    return (str(hist[-1].get("event_id")) if hist else None, len(hist))


def own_next_seq(events: list[dict[str, Any]], branch: str) -> int:
    seqs = [int(e.get("seq")) for e in events if str(e.get("branch", "main")) == branch and isinstance(e.get("seq"), int)]
    return (max(seqs) + 1) if seqs else 1


def normalized_proposed(tx: dict[str, Any], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    branch = str(tx.get("branch", "main"))
    next_seq = own_next_seq(events, branch)
    out: list[dict[str, Any]] = []
    for offset, raw in enumerate(tx.get("proposed_events") or []):
        if not isinstance(raw, dict):
            raise TxError("proposed_events entries must be objects")
        e = dict(raw)
        e["branch"] = branch
        e["seq"] = next_seq + offset
        e.setdefault("schema_version", "3.0.0")
        e.setdefault("event_version", "1.0.0")
        e.setdefault("status", "committed")
        e["transaction_id"] = str(tx.get("transaction_id"))
        e["transaction_payload_sha256"] = transaction_payload_hash(tx)
        e["transaction_identity_version"] = "1.0.0"
        out.append(e)
    return out


def transaction_payload_hash(tx: dict[str, Any]) -> str:
    """Stable semantic request identity; transport and commit-result fields excluded.

    Unknown top-level fields are retained (fail-safe); diagnostics/retry_metadata
    are explicit nonsemantic namespaces. Event sequence/branch are writer-owned.
    """
    ignored = {"transaction_id", "status", "committed_event_ids", "diagnostics", "retry_metadata", "correlation_id", "timestamp", "committed_at"}
    payload = {k: v for k, v in tx.items() if k not in ignored}
    proposed = []
    for raw in tx.get("proposed_events", []) or []:
        event = {k: v for k, v in raw.items() if k not in {"seq", "branch", "transaction_id", "transaction_payload_sha256", "transaction_identity_version"}}
        event.setdefault("schema_version", "3.0.0")
        event.setdefault("event_version", "1.0.0")
        event.setdefault("status", "committed")
        proposed.append(event)
    payload["proposed_events"] = proposed
    payload.setdefault("branch", "main")
    payload.setdefault("expected_effective_revision", None)
    payload.setdefault("blocking_objections", [])
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def transaction_match_state(tx: dict[str, Any], events: list[dict[str, Any]]) -> str:
    """Return absent, exact, or conflict for a transaction-id retry."""
    txid = str(tx.get("transaction_id", ""))
    proposed_ids = {str(x.get("event_id")) for x in (tx.get("proposed_events") or []) if isinstance(x, dict)}
    if not txid or not proposed_ids:
        return "absent"
    committed = [e for e in events if str(e.get("transaction_id", "")) == txid]
    matched = {str(e.get("event_id")) for e in committed}
    if not matched:
        return "absent"
    if proposed_ids != matched or len(committed) != len(tx.get("proposed_events", [])):
        return "conflict"
    digest = transaction_payload_hash(tx)
    # Old logs without a durable request identity cannot prove request equivalence.
    return "exact" if all(e.get("transaction_identity_version") == "1.0.0" and e.get("transaction_payload_sha256") == digest for e in committed) else "conflict"


def idempotent_match(tx: dict[str, Any], events: list[dict[str, Any]]) -> bool:
    return transaction_match_state(tx, events) == "exact"


def atomic_append_jsonl(path: Path, proposed: list[dict[str, Any]]) -> None:
    """Atomically replace the file while preserving every pre-existing event byte.

    The temporary file receives the original byte stream verbatim, followed only by
    newly serialized events. This keeps committed-history representations stable
    while still providing all-or-none multi-event transaction semantics.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    original = path.read_bytes() if path.exists() else b""
    if original and not original.endswith(b"\n"):
        original += b"\n"
    appended = b"".join(
        (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        for event in proposed
    )
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(original)
            f.write(appended)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def validate_tx_schema(tx: dict[str, Any]) -> list[str]:
    return validate_instance(tx, schema_path("transaction", DEFAULT_SCHEMA_DIR))


def preflight(events_path: Path, branches_path: Path, tx: dict[str, Any], invariants_path: Path | None,
              provenance: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    errors = validate_tx_schema(tx)
    if errors:
        raise TxError("transaction schema invalid: " + "; ".join(errors))
    if tx.get("blocking_objections"):
        raise TxError("transaction has unresolved blocking objections")
    events = load_jsonl(events_path)
    branches = branch_map(load_json(branches_path))
    branch = str(tx.get("branch"))
    if branch not in branches:
        raise TxError(f"unknown branch {branch}")

    tx_state = transaction_match_state(tx, events)
    if tx_state == "exact":
        return events, branches, []
    if tx_state == "conflict":
        raise TxError("IDEMPOTENCY_CONFLICT: transaction_id already exists with a different or unverifiable semantic payload", "IDEMPOTENCY_CONFLICT")

    current_head, current_rev = branch_head(events, branches, branch)
    if tx.get("expected_head_event") != current_head:
        raise TxError(f"optimistic concurrency conflict: expected head {tx.get('expected_head_event')!r}, current head {current_head!r}")
    expected_rev = tx.get("expected_effective_revision")
    if expected_rev is not None and int(expected_rev) != current_rev:
        raise TxError(f"optimistic concurrency conflict: expected revision {expected_rev}, current revision {current_rev}")

    existing_ids = {str(e.get("event_id")) for e in events}
    proposed = normalized_proposed(tx, events)
    for e in proposed:
        eid = str(e.get("event_id", ""))
        if not eid:
            raise TxError("proposed event missing event_id")
        if eid in existing_ids:
            raise TxError(f"event_id collision: {eid}")

    candidate = events + proposed
    # Compatibility reads of old unclosed rows do not authorize new unclosed
    # writes into the canonical event log, including requests omitting authority.
    candidate_index = {str(e.get("event_id")): e for e in candidate}
    closure_errors = [error for e in proposed for error in promotion_errors(e, candidate_index, provenance)]
    if closure_errors:
        raise TxError("; ".join(closure_errors), "UNRESOLVED_PROVENANCE")
    runtime_errors, runtime_warnings = validate_runtime(candidate, branches, provenance=provenance)
    if runtime_errors:
        raise TxError("runtime validation failed: " + "; ".join(runtime_errors),
                      "UNRESOLVED_PROVENANCE" if any("PROVENANCE" in e for e in runtime_errors) else "TRANSACTION_ERROR")
    if runtime_warnings:
        for msg in runtime_warnings:
            print(f"WARNING: {msg}", file=sys.stderr)

    if invariants_path is not None:
        catalog = load_json(invariants_path)
        inv_errors, inv_warnings, inv_advisories = evaluate_invariants(candidate, branches, branch, catalog)
        for msg in inv_advisories:
            print(f"ADVISORY: {msg}", file=sys.stderr)
        for msg in inv_warnings:
            print(f"WARNING: {msg}", file=sys.stderr)
        if inv_errors:
            raise TxError("invariant failure: " + "; ".join(inv_errors))
    return events, branches, proposed


def cmd_status(args: argparse.Namespace) -> int:
    events = load_jsonl(args.events)
    branches = branch_map(load_json(args.branches))
    head, rev = branch_head(events, branches, args.branch)
    print(json.dumps({"branch": args.branch, "head_event": head, "effective_revision": rev}, ensure_ascii=False, indent=2))
    return 0


def committed_result(tx: dict[str, Any], events: list[dict[str, Any]], branches: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Reconstruct the original receipt even if later transactions were committed."""
    history = effective_events(str(tx.get("branch", "main")), branches, events_by_branch(events))
    committed = [e for e in history if e.get("transaction_id") == tx.get("transaction_id")]
    head = committed[-1]['event_id']
    revision = next(i + 1 for i, e in enumerate(history) if e['event_id'] == head)
    return {"status": "committed", "events": [e['event_id'] for e in committed], "head_event": head, "effective_revision": revision}


def cmd_commit(args: argparse.Namespace) -> int:
    tx = load_json(args.transaction)
    if not isinstance(tx, dict):
        raise TxError("transaction file must contain an object")
    lock_path = args.events.parent / ".narrative-runtime.lock"
    fd = acquire_lock(lock_path)
    try:
        # Re-read under lock: this is the concurrency check that matters.
        provenance = load_json(args.provenance) if getattr(args, "provenance", None) else None
        events, branches, proposed = preflight(args.events, args.branches, tx, args.invariants, provenance)
        if not proposed and idempotent_match(tx, events):
            if not args.no_update_transaction:
                tx["status"] = "committed"
                tx["committed_event_ids"] = sorted(
                    str(e.get("event_id")) for e in events if str(e.get("transaction_id", "")) == str(tx.get("transaction_id", ""))
                )
                save_transaction(args.transaction, tx)
            print(json.dumps(committed_result(tx, events, branches), ensure_ascii=False, indent=2))
            return 0
        atomic_append_jsonl(args.events, proposed)
        if not args.no_update_transaction:
            tx["status"] = "committed"
            tx["committed_event_ids"] = [e.get("event_id") for e in proposed]
            save_transaction(args.transaction, tx)
        print(json.dumps(committed_result(tx, events + proposed, branches), ensure_ascii=False, indent=2))
        return 0
    finally:
        release_lock(fd, lock_path)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("status")
    q.add_argument("--events", type=Path, required=True)
    q.add_argument("--branches", type=Path, required=True)
    q.add_argument("--branch", default="main")

    q = sub.add_parser("commit")
    q.add_argument("--events", type=Path, required=True)
    q.add_argument("--branches", type=Path, required=True)
    q.add_argument("--transaction", type=Path, required=True)
    q.add_argument("--invariants", type=Path)
    q.add_argument("--provenance", type=Path, help="versioned source/evidence/confirmation catalog for canonical promotion")
    q.add_argument("--no-update-transaction", action="store_true")

    args = p.parse_args()
    try:
        if args.cmd == "status":
            return cmd_status(args)
        return cmd_commit(args)
    except (OSError, ValueError, TxError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
