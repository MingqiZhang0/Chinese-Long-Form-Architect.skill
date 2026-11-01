#!/usr/bin/env python3
"""Deterministic event-sourced runtime utilities for long-form fiction projects.

The runtime is intentionally generic. It manages event history, branch lineage,
projection replay, dependency impact, and merge planning. It does not write prose
or decide which branch should become canon.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any
from dependency_activity import active_edges, is_edge_active
from event_provenance import canonical_event, event_closure, promotion_errors


class RuntimeErrorData(ValueError):
    pass


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeErrorData(f"{path}:{lineno}: invalid JSON: {exc}") from exc
        if not isinstance(item, dict):
            raise RuntimeErrorData(f"{path}:{lineno}: event must be an object")
        rows.append(item)
    return rows


def emit(data: Any, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif isinstance(data, list):
        for row in data:
            if isinstance(row, dict):
                print(" | ".join(f"{k}={v}" for k, v in row.items()))
            else:
                print(row)
    elif isinstance(data, dict):
        for k, v in data.items():
            print(f"{k}: {v}")
    else:
        print(data)


def branch_map(raw: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, dict):
        raise RuntimeErrorData("branches file must be an object")
    data = raw.get("branches", raw)
    if not isinstance(data, dict):
        raise RuntimeErrorData("branches must be an object")
    result: dict[str, dict[str, Any]] = {}
    for name, rec in data.items():
        if not isinstance(rec, dict):
            raise RuntimeErrorData(f"branch {name} must be an object")
        result[str(name)] = dict(rec)
    return result


def event_index(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for e in events:
        eid = str(e.get("event_id", ""))
        if eid:
            out[eid] = e
    return out


def events_by_branch(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for e in events:
        b = str(e.get("branch", "main"))
        out.setdefault(b, []).append(e)
    for rows in out.values():
        rows.sort(key=lambda e: int(e.get("seq", 0)))
    return out


def validate_runtime(events: list[dict[str, Any]], branches: dict[str, dict[str, Any]], dependencies: Any | None = None,
                     provenance: dict[str, Any] | None = None, strict_audit: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    ids: set[str] = set()
    seqs: dict[str, set[int]] = {}

    if "main" not in branches:
        errors.append("missing main branch")

    for name, rec in branches.items():
        parent = rec.get("parent")
        if name == "main" and parent not in (None, ""):
            errors.append("main branch must not have a parent")
        if parent not in (None, "") and str(parent) not in branches:
            errors.append(f"branch {name} references missing parent {parent}")
        if parent not in (None, "") and not rec.get("fork_event"):
            errors.append(f"branch {name} requires fork_event")

    by_branch = events_by_branch(events)
    idx = event_index(events)
    for e in events:
        closure_errors = promotion_errors(e, idx, provenance)
        if canonical_event(e) or strict_audit:
            errors.extend(closure_errors)
        else:
            warnings.extend(closure_errors)
        eid = e.get("event_id")
        if not isinstance(eid, str) or not eid.strip():
            errors.append("event missing event_id")
            continue
        if eid in ids:
            errors.append(f"duplicate event_id {eid}")
        ids.add(eid)
        branch = str(e.get("branch", "main"))
        if branch not in branches:
            errors.append(f"event {eid} references unknown branch {branch}")
        seq = e.get("seq")
        if not isinstance(seq, int) or seq <= 0:
            errors.append(f"event {eid} requires positive integer seq")
        else:
            if seq in seqs.setdefault(branch, set()):
                errors.append(f"branch {branch} has duplicate seq {seq}")
            seqs[branch].add(seq)
        if not isinstance(e.get("event_type"), str) or not e.get("event_type"):
            errors.append(f"event {eid} missing event_type")
        event_status = str(e.get("status", "committed")).lower()
        if event_status not in {"committed"}:
            errors.append(f"event {eid} has non-committed status {event_status}; provisional discoveries belong outside the event store")
        if not isinstance(e.get("intent"), str) or not e.get("intent"):
            warnings.append(f"event {eid} has no intent")
        effects = e.get("effects", [])
        if not isinstance(effects, list):
            errors.append(f"event {eid} effects must be a list")
        else:
            for i, effect in enumerate(effects):
                if not isinstance(effect, dict):
                    errors.append(f"event {eid} effect[{i}] must be an object")
                    continue
                if effect.get("op") not in {"set", "delete", "append", "add_to_set", "remove_from_set", "increment"}:
                    errors.append(f"event {eid} effect[{i}] has invalid op {effect.get('op')}")
                if not isinstance(effect.get("path"), str) or not effect.get("path"):
                    errors.append(f"event {eid} effect[{i}] missing path")
        for key in ("compensates", "supersedes"):
            ref = e.get(key)
            if ref and str(ref) not in idx:
                warnings.append(f"event {eid} {key} missing event {ref}")

    for branch, rows in by_branch.items():
        seq_values = [int(e.get("seq", 0)) for e in rows if isinstance(e.get("seq"), int)]
        if seq_values and seq_values != sorted(seq_values):
            errors.append(f"branch {branch} sequence order is not monotonic")

    for name, rec in branches.items():
        parent = rec.get("parent")
        fork = rec.get("fork_event")
        if parent in (None, ""):
            continue
        if str(fork) not in idx:
            errors.append(f"branch {name} fork_event {fork} does not exist")
        elif str(idx[str(fork)].get("branch", "main")) != str(parent):
            # A fork may point to inherited history of the parent branch. Check later by effective history.
            try:
                hist = effective_events(str(parent), branches, by_branch)
                if str(fork) not in {str(x.get("event_id")) for x in hist}:
                    errors.append(f"branch {name} fork_event {fork} is not in parent history")
            except RuntimeErrorData as exc:
                errors.append(str(exc))

    # cycle check
    for name in branches:
        seen: set[str] = set()
        cur = name
        while cur:
            if cur in seen:
                errors.append(f"branch lineage cycle at {cur}")
                break
            seen.add(cur)
            parent = branches.get(cur, {}).get("parent")
            cur = str(parent) if parent not in (None, "") else ""

    if dependencies is not None:
        dep_rows = dependencies.get("edges", dependencies) if isinstance(dependencies, dict) else dependencies
        if not isinstance(dep_rows, list):
            errors.append("dependencies must be a list or object with edges")
        else:
            for i, edge in enumerate(dep_rows):
                if not isinstance(edge, dict):
                    errors.append(f"dependency[{i}] must be an object")
                    continue
                if edge.get("source") is None or edge.get("target") is None:
                    errors.append(f"dependency[{i}] requires source and target")
                if edge.get("source") == edge.get("target"):
                    warnings.append(f"dependency[{i}] self-edge {edge.get('source')}")
    return errors, warnings


def effective_events(branch: str, branches: dict[str, dict[str, Any]], by_branch: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    if branch not in branches:
        raise RuntimeErrorData(f"unknown branch {branch}")
    rec = branches[branch]
    parent = rec.get("parent")
    own = list(by_branch.get(branch, []))
    if parent in (None, ""):
        return own
    parent_name = str(parent)
    inherited = effective_events(parent_name, branches, by_branch)
    fork = str(rec.get("fork_event"))
    cut = None
    for i, e in enumerate(inherited):
        if str(e.get("event_id")) == fork:
            cut = i
            break
    if cut is None:
        raise RuntimeErrorData(f"branch {branch} fork_event {fork} not found in parent history")
    return inherited[: cut + 1] + own


def path_parts(path: str) -> list[str]:
    return [p for p in path.split(".") if p]


def get_parent(state: dict[str, Any], parts: list[str], create: bool) -> tuple[dict[str, Any], str]:
    if not parts:
        raise RuntimeErrorData("empty projection path")
    cur: dict[str, Any] = state
    for key in parts[:-1]:
        nxt = cur.get(key)
        if nxt is None and create:
            nxt = {}
            cur[key] = nxt
        if not isinstance(nxt, dict):
            raise RuntimeErrorData(f"projection path crosses non-object at {key}")
        cur = nxt
    return cur, parts[-1]


def apply_effect(state: dict[str, Any], effect: dict[str, Any]) -> None:
    op = str(effect.get("op"))
    parts = path_parts(str(effect.get("path", "")))
    parent, key = get_parent(state, parts, create=op not in {"delete", "remove_from_set"})
    value = copy.deepcopy(effect.get("value"))
    if op == "set":
        parent[key] = value
    elif op == "delete":
        parent.pop(key, None)
    elif op == "append":
        arr = parent.setdefault(key, [])
        if not isinstance(arr, list):
            raise RuntimeErrorData(f"append target {effect.get('path')} is not a list")
        arr.append(value)
    elif op == "add_to_set":
        arr = parent.setdefault(key, [])
        if not isinstance(arr, list):
            raise RuntimeErrorData(f"add_to_set target {effect.get('path')} is not a list")
        if value not in arr:
            arr.append(value)
    elif op == "remove_from_set":
        arr = parent.get(key, [])
        if not isinstance(arr, list):
            raise RuntimeErrorData(f"remove_from_set target {effect.get('path')} is not a list")
        parent[key] = [x for x in arr if x != value]
    elif op == "increment":
        cur = parent.get(key, 0)
        if not isinstance(cur, (int, float)) or not isinstance(value, (int, float)):
            raise RuntimeErrorData(f"increment target {effect.get('path')} requires numeric values")
        parent[key] = cur + value
    else:
        raise RuntimeErrorData(f"unsupported projection op {op}")


def replay(events: list[dict[str, Any]], branches: dict[str, dict[str, Any]], branch: str, through_event: str | None = None, base_state: dict[str, Any] | None = None, start_after_event: str | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    by_branch = events_by_branch(events)
    history = effective_events(branch, branches, by_branch)
    if start_after_event:
        found = False
        trimmed: list[dict[str, Any]] = []
        for e in history:
            if found:
                trimmed.append(e)
            elif str(e.get("event_id")) == start_after_event:
                found = True
        if not found:
            raise RuntimeErrorData(f"snapshot event {start_after_event} not in branch history")
        history = trimmed
    state = copy.deepcopy(base_state or {})
    applied: list[dict[str, Any]] = []
    for e in history:
        for effect in e.get("effects", []) or []:
            apply_effect(state, effect)
        applied.append(e)
        if through_event and str(e.get("event_id")) == through_event:
            break
    if through_event and not any(str(e.get("event_id")) == through_event for e in applied):
        raise RuntimeErrorData(f"through_event {through_event} not reached on branch {branch}")
    return state, applied


def load_snapshot(path: Path | None, branch: str) -> tuple[dict[str, Any], str | None]:
    if path is None:
        return {}, None
    snap = load_json(path)
    if not isinstance(snap, dict):
        raise RuntimeErrorData("snapshot must be an object")
    if str(snap.get("branch")) != branch:
        raise RuntimeErrorData(f"snapshot branch {snap.get('branch')} does not match {branch}")
    state = snap.get("state", {})
    if not isinstance(state, dict):
        raise RuntimeErrorData("snapshot.state must be an object")
    return state, snap.get("through_event")


def dependency_rows(raw: Any) -> list[dict[str, Any]]:
    rows = raw.get("edges", raw) if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise RuntimeErrorData("dependencies must be a list or object with edges")
    return [x for x in rows if isinstance(x, dict)]


def impact(rows: list[dict[str, Any]], node: str, at: float | None = None, policy: str = "active_at") -> list[dict[str, Any]]:
    graph: dict[str, list[dict[str, Any]]] = {}
    for edge in active_edges(rows, at, policy):
        source, target = edge.get("source"), edge.get("target")
        if source is None or target is None:
            continue
        graph.setdefault(str(source), []).append(edge)
    seen = {node}
    q: list[tuple[str, int]] = [(node, 0)]
    result: list[dict[str, Any]] = []
    while q:
        cur, depth = q.pop(0)
        for edge in graph.get(cur, []):
            target = str(edge.get("target"))
            if target in seen:
                continue
            seen.add(target)
            result.append({
                "source": cur,
                "target": target,
                "kind": edge.get("kind"),
                "strength": edge.get("strength", "hard"),
                "depth": depth + 1,
            })
            q.append((target, depth + 1))
    return result


def why_trace(rows: list[dict[str, Any]], node: str, at: float | None = None, policy: str = "active_at") -> list[dict[str, Any]]:
    """Return upstream dependency edges explaining why `node` depends on earlier nodes."""
    reverse: dict[str, list[dict[str, Any]]] = {}
    for edge in active_edges(rows, at, policy):
        source, target = edge.get("source"), edge.get("target")
        if source is None or target is None:
            continue
        reverse.setdefault(str(target), []).append(edge)
    seen = {node}
    q: list[tuple[str, int]] = [(node, 0)]
    result: list[dict[str, Any]] = []
    while q:
        cur, depth = q.pop(0)
        for edge in reverse.get(cur, []):
            source = str(edge.get("source"))
            result.append({
                "source": source,
                "target": cur,
                "kind": edge.get("kind"),
                "strength": edge.get("strength", "hard"),
                "reason": edge.get("reason"),
                "edge_id": edge.get("id"),
                "depth": depth + 1,
            })
            if source not in seen:
                seen.add(source)
                q.append((source, depth + 1))
    result.sort(key=lambda edge: (edge["depth"], edge["target"], edge["source"], str(edge["kind"]), str(edge["reason"])))
    return result


def trace_query(rows: list[dict[str, Any]], node: str, events: list[dict[str, Any]] | None = None,
                provenance: dict[str, Any] | None = None, at: float | None = None,
                policy: str = "active_at", mode: str = "complete") -> dict[str, Any]:
    """Complete registered graph traversal plus machine-readable terminal closure."""
    from event_provenance import event_closure
    if mode not in {"minimal", "complete"}:
        raise ValueError(f"unsupported trace mode: {mode}")
    trace = why_trace(rows, node, at, policy)
    gaps = set()
    idx = event_index(events or [])
    nodes = {node} | {r['source'] for r in trace} | {r['target'] for r in trace}
    terminals = nodes - {r['target'] for r in trace}
    if not terminals:
        gaps.add("NO_TERMINAL_PROVENANCE")
    grounded = set(terminals)
    while True:
        next_grounded = grounded | {r['target'] for r in trace if r['source'] in grounded}
        if next_grounded == grounded:
            break
        grounded = next_grounded
    if nodes - grounded:
        gaps.add("UNTERMINATED_SUPPORT_PATH")
    for terminal in terminals:
        if terminal not in idx:
            gaps.add("MISSING_TERMINAL_PROVENANCE")
        elif event_closure(idx[terminal], idx, provenance)["provenance_status"] != "CLOSED":
            gaps.add("UNCLOSED_TERMINAL_PROVENANCE")
    # Every visited event must have valid closure, including non-terminal events.
    for ref in nodes & idx.keys():
        if event_closure(idx[ref], idx, provenance)["provenance_status"] != "CLOSED":
            gaps.add("UNCLOSED_EVENT_PROVENANCE")
    if mode == "minimal":
        gaps.add("MINIMAL_TRACE")
        trace = trace[:1]
    return {"edges": trace, "mode": mode, "completeness": "PARTIAL" if gaps else "FULL",
            "gap_reasons": sorted(gaps), "provenance_status": "PARTIAL" if gaps else "CLOSED"}


def flatten_state(value: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        for k, v in value.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(flatten_state(v, key))
    else:
        out[prefix] = value
    return out


def effect_paths(events: list[dict[str, Any]]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for e in events:
        paths = {str(x.get("path")) for x in (e.get("effects", []) or []) if isinstance(x, dict) and x.get("path")}
        out[str(e.get("event_id"))] = paths
    return out


def cmd_validate(args: argparse.Namespace) -> int:
    events = load_jsonl(Path(args.events))
    branches = branch_map(load_json(Path(args.branches)))
    deps = load_json(Path(args.dependencies)) if args.dependencies else None
    catalog = load_json(Path(args.provenance)) if args.provenance else None
    errors, warnings = validate_runtime(events, branches, deps, catalog, args.strict_audit)
    idx = event_index(events)
    closures = {eid: event_closure(e, idx, catalog) for eid, e in idx.items()}
    emit({"errors": errors, "warnings": warnings, "event_count": len(events), "branch_count": len(branches), "event_provenance": closures}, args.json)
    return 1 if errors else 0


def cmd_replay(args: argparse.Namespace) -> int:
    events = load_jsonl(Path(args.events))
    branches = branch_map(load_json(Path(args.branches)))
    base, through = load_snapshot(Path(args.snapshot) if args.snapshot else None, args.branch)
    state, applied = replay(events, branches, args.branch, args.through_event, base_state=base, start_after_event=through)
    result = {"branch": args.branch, "through_event": applied[-1].get("event_id") if applied else through, "events_applied": len(applied), "state": state}
    emit(result, True if args.json else False)
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    events = load_jsonl(Path(args.events))
    branches = branch_map(load_json(Path(args.branches)))
    state, applied = replay(events, branches, args.branch, args.through_event)
    out = {
        "schema_version": "3.0.0",
        "branch": args.branch,
        "through_event": applied[-1].get("event_id") if applied else None,
        "state": state,
    }
    save_json(Path(args.out), out)
    print(args.out)
    return 0


def cmd_impact(args: argparse.Namespace) -> int:
    rows = dependency_rows(load_json(Path(args.dependencies)))
    emit(impact(rows, args.node, args.at, args.policy), args.json)
    return 0


def cmd_branch_create(args: argparse.Namespace) -> int:
    path = Path(args.branches)
    raw = load_json(path)
    branches = branch_map(raw)
    if args.name in branches:
        print(f"ERROR: branch already exists: {args.name}", file=sys.stderr)
        return 2
    if args.parent not in branches:
        print(f"ERROR: missing parent branch: {args.parent}", file=sys.stderr)
        return 2
    events = load_jsonl(Path(args.events))
    by = events_by_branch(events)
    hist = effective_events(args.parent, branches, by)
    if args.fork_event not in {str(e.get("event_id")) for e in hist}:
        print(f"ERROR: fork event {args.fork_event} not in parent history", file=sys.stderr)
        return 2
    branches[args.name] = {
        "parent": args.parent,
        "fork_event": args.fork_event,
        "purpose": args.purpose or "",
        "status": args.status,
    }
    schema_version = raw.get("schema_version", "3.0.0") if isinstance(raw, dict) else "3.0.0"
    save_json(path, {"schema_version": schema_version, "branches": branches})
    print(args.name)
    return 0


def cmd_merge_plan(args: argparse.Namespace) -> int:
    events = load_jsonl(Path(args.events))
    branches = branch_map(load_json(Path(args.branches)))
    source_rec = branches.get(args.source)
    if not source_rec:
        print(f"ERROR: unknown source branch {args.source}", file=sys.stderr)
        return 2
    if str(source_rec.get("parent")) != args.target:
        print("ERROR: merge-plan currently requires source to be a direct child of target", file=sys.stderr)
        return 2
    fork = str(source_rec.get("fork_event"))
    by = events_by_branch(events)
    source_events = list(by.get(args.source, []))
    target_hist = effective_events(args.target, branches, by)
    fork_index = next((i for i, e in enumerate(target_hist) if str(e.get("event_id")) == fork), None)
    if fork_index is None:
        print(f"ERROR: fork event {fork} not found in target history", file=sys.stderr)
        return 2
    target_after = target_hist[fork_index + 1 :]
    spaths = effect_paths(source_events)
    tpaths = effect_paths(target_after)
    conflicts: list[dict[str, Any]] = []
    for se in source_events:
        sid = str(se.get("event_id"))
        for te in target_after:
            tid = str(te.get("event_id"))
            overlap = sorted(spaths[sid] & tpaths[tid])
            if overlap:
                conflicts.append({"source_event": sid, "target_event": tid, "overlapping_paths": overlap})
    plan = {
        "source": args.source,
        "target": args.target,
        "fork_event": fork,
        "source_events": [e.get("event_id") for e in source_events],
        "target_events_after_fork": [e.get("event_id") for e in target_after],
        "path_conflicts": conflicts,
        "semantic_review_required": True,
        "automatic_merge_performed": False,
    }
    emit(plan, args.json)
    return 1 if conflicts else 0



def cmd_why(args: argparse.Namespace) -> int:
    rows = dependency_rows(load_json(Path(args.dependencies)))
    events = load_jsonl(Path(args.events)) if args.events else []
    catalog = load_json(Path(args.provenance)) if args.provenance else None
    result = trace_query(rows, args.node, events, catalog, args.at, args.policy, args.mode)
    trace = result['edges']
    if args.events:
        idx = event_index(load_jsonl(Path(args.events)))
        for row in trace:
            src = idx.get(str(row.get("source")))
            if src:
                row["source_event_type"] = src.get("event_type")
                row["source_intent"] = src.get("intent")
    emit(result, args.json)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    events = load_jsonl(Path(args.events))
    branches = branch_map(load_json(Path(args.branches)))
    left, left_events = replay(events, branches, args.left)
    right, right_events = replay(events, branches, args.right)
    lf, rf = flatten_state(left), flatten_state(right)
    keys = sorted(set(lf) | set(rf))
    diffs = []
    missing = object()
    for key in keys:
        a, b = lf.get(key, missing), rf.get(key, missing)
        if a != b:
            diffs.append({
                "path": key,
                "left": None if a is missing else a,
                "right": None if b is missing else b,
                "left_missing": a is missing,
                "right_missing": b is missing,
            })
    result = {
        "left": args.left,
        "right": args.right,
        "left_head": left_events[-1].get("event_id") if left_events else None,
        "right_head": right_events[-1].get("event_id") if right_events else None,
        "state_differences": diffs,
        "semantic_interpretation_required": True,
    }
    emit(result, True if args.json else False)
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("validate")
    q.add_argument("--events", required=True)
    q.add_argument("--branches", required=True)
    q.add_argument("--dependencies")
    q.add_argument("--provenance")
    q.add_argument("--strict-audit", action="store_true")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_validate)

    q = sub.add_parser("replay")
    q.add_argument("--events", required=True)
    q.add_argument("--branches", required=True)
    q.add_argument("--branch", default="main")
    q.add_argument("--through-event")
    q.add_argument("--snapshot")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_replay)

    q = sub.add_parser("snapshot")
    q.add_argument("--events", required=True)
    q.add_argument("--branches", required=True)
    q.add_argument("--branch", default="main")
    q.add_argument("--through-event")
    q.add_argument("--out", required=True)
    q.set_defaults(func=cmd_snapshot)

    q = sub.add_parser("impact")
    q.add_argument("--dependencies", required=True)
    q.add_argument("--node", required=True)
    q.add_argument("--at", type=float)
    q.add_argument("--policy", choices=["active_at", "historical_all"], default="active_at")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_impact)

    q = sub.add_parser("why")
    q.add_argument("--dependencies", required=True)
    q.add_argument("--node", required=True)
    q.add_argument("--events")
    q.add_argument("--provenance")
    q.add_argument("--at", type=float)
    q.add_argument("--policy", choices=["active_at", "historical_all"], default="active_at")
    q.add_argument("--mode", choices=["complete", "minimal"], default="complete")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_why)

    q = sub.add_parser("compare")
    q.add_argument("--events", required=True)
    q.add_argument("--branches", required=True)
    q.add_argument("--left", required=True)
    q.add_argument("--right", required=True)
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_compare)

    q = sub.add_parser("branch-create")
    q.add_argument("--events", required=True)
    q.add_argument("--branches", required=True)
    q.add_argument("--name", required=True)
    q.add_argument("--parent", default="main")
    q.add_argument("--fork-event", required=True)
    q.add_argument("--purpose")
    q.add_argument("--status", choices=["active", "sandbox", "archived"], default="active")
    q.set_defaults(func=cmd_branch_create)

    q = sub.add_parser("merge-plan")
    q.add_argument("--events", required=True)
    q.add_argument("--branches", required=True)
    q.add_argument("--source", required=True)
    q.add_argument("--target", default="main")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_merge_plan)
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError, RuntimeErrorData) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
