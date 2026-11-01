#!/usr/bin/env python3
"""Deterministic read-only queries for long-form fiction project state.

This utility complements validate_story_state.py. It never writes prose or canon,
and it does not score literary quality or infer Project Poetics from state queries.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from pathlib import Path
from typing import Any
from dependency_activity import active_edges

try:
    from research_freshness import stale_research_dependencies
    from reader_state import reader_state_at, query_reader_state, NarrativePosition
    from validate_story_state import load_json, validate_issues
    from open_issue import commitment_fingerprint, is_v2, issue_id, viable_positions, working_positions
except ImportError:  # pragma: no cover - direct packaging fallback
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from research_freshness import stale_research_dependencies
    from reader_state import reader_state_at, query_reader_state, NarrativePosition
    from validate_story_state import load_json, validate_issues
    from open_issue import commitment_fingerprint, is_v2, issue_id, viable_positions, working_positions


def as_num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    return num if math.isfinite(num) else None


def interval(rec: dict[str, Any]) -> tuple[float, float]:
    start = as_num(rec.get("valid_from"))
    end = as_num(rec.get("valid_to"))
    return (float("-inf") if start is None else start, float("inf") if end is None else end)


def edge_active(edge: dict[str, Any], at: float) -> bool:
    start, end = interval(edge)
    return start <= at < end and edge.get("passable", True) is not False


def travel_path(edges: list[dict[str, Any]], start: str, end: str, at: float) -> tuple[float, list[str], list[str]] | None:
    if start == end:
        return 0.0, [start], []
    graph: dict[str, list[tuple[str, float, str]]] = {}
    for edge in edges:
        if not isinstance(edge, dict) or not edge_active(edge, at):
            continue
        a, b = edge.get("a"), edge.get("b")
        w = as_num(edge.get("min_travel_time"))
        if a is None or b is None or w is None or w < 0:
            continue
        a, b = str(a), str(b)
        eid = str(edge.get("id", f"{a}->{b}"))
        graph.setdefault(a, []).append((b, w, eid))
        if edge.get("one_way") is not True:
            graph.setdefault(b, []).append((a, w, eid))

    q: list[tuple[float, str]] = [(0.0, start)]
    best = {start: 0.0}
    prev: dict[str, tuple[str, str]] = {}
    while q:
        cost, node = heapq.heappop(q)
        if cost != best.get(node):
            continue
        if node == end:
            nodes = [end]
            edge_ids: list[str] = []
            cur = end
            while cur != start:
                p, eid = prev[cur]
                nodes.append(p)
                edge_ids.append(eid)
                cur = p
            nodes.reverse()
            edge_ids.reverse()
            return cost, nodes, edge_ids
        for nxt, weight, eid in graph.get(node, []):
            new = cost + weight
            if new < best.get(nxt, float("inf")):
                best[nxt] = new
                prev[nxt] = (node, eid)
                heapq.heappush(q, (new, nxt))
    return None


def emit(data: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                print(" | ".join(f"{k}={v}" for k, v in item.items()))
            else:
                print(item)
    elif isinstance(data, dict):
        for k, v in data.items():
            print(f"{k}: {v}")
    else:
        print(data)


def knowledge_at(state: dict[str, Any], actor: str, at: float | None) -> list[dict[str, Any]]:
    """Pure read adapter; an empty canonical interval never enables legacy fallback."""
    rows: list[dict[str, Any]] = []
    from event_provenance import event_closure
    idx = {str(e.get("event_id")): e for e in state.get("events", []) if isinstance(e, dict)}
    for rec in state.get("knowledge_state", []) or []:
        if not isinstance(rec, dict) or str(rec.get("actor")) != actor:
            continue
        acquired = as_num(rec.get("valid_from", rec.get("acquired_at", rec.get("acquired"))))
        if acquired is None and rec.get("acquisition_event_ref"):
            # Only an actual registered event supplies a missing acquisition time.
            event = next((e for e in state.get("events", []) if isinstance(e, dict) and e.get("event_id") == rec["acquisition_event_ref"]), {})
            if event_closure(event, idx, state.get("provenance_catalog"))["provenance_status"] == "CLOSED":
                acquired = as_num(event.get("story_time"))
        retired = as_num(rec.get("valid_until", rec.get("valid_to", rec.get("retired_at"))))
        raw_end = rec.get("valid_until", rec.get("valid_to", rec.get("retired_at")))
        invalid_time = raw_end is not None and retired is None
        closure = event_closure(rec, idx, state.get("provenance_catalog"))
        temporal_gaps = ["MISSING_TEMPORAL_PROVENANCE"] if at is not None and acquired is None else []
        if invalid_time:
            temporal_gaps.append("INVALID_TEMPORAL_PROVENANCE")
        if at is not None and acquired is not None and acquired > at:
            continue
        if at is not None and retired is not None and at >= retired:
            continue
        rows.append({
            "fact": rec.get("fact"),
            "status": "unknown" if at is not None and (acquired is None or invalid_time) else rec.get("status", "known"),
            "acquired_at": acquired,
            "belief": rec.get("belief"),
            "source": rec.get("source"),
            "completeness": "PARTIAL" if temporal_gaps or closure['provenance_status'] != 'CLOSED' else "FULL",
            "gap_reasons": sorted(set(temporal_gaps + closure['gap_reasons'])),
            "provenance_status": closure['provenance_status'],
        })
    if "knowledge_state" not in state:
        # Fallback to legacy knowledge_uses records.
        for rec in state.get("knowledge_uses", []) or []:
            if not isinstance(rec, dict) or str(rec.get("actor")) != actor:
                continue
            acquired = as_num(rec.get("acquired"))
            if at is not None and acquired is not None and acquired > at:
                continue
            retired = as_num(rec.get("valid_until", rec.get("valid_to", rec.get("retired_at"))))
            if at is not None and retired is not None and at >= retired:
                continue
            rows.append({"fact": rec.get("fact"), "status": "unknown" if at is not None and acquired is None else "known", "acquired_at": acquired,
                         "completeness": "PARTIAL", "gap_reasons": ["LEGACY_PROVENANCE"], "provenance_status": "UNRESOLVED"})
    return sorted(rows, key=lambda row: json.dumps(row, sort_keys=True, ensure_ascii=False))


def cmd_knowledge(state: dict[str, Any], args: argparse.Namespace) -> int:
    rows = knowledge_at(state, args.actor, args.at)
    emit(rows, args.json)
    return 0


def cmd_travel(state: dict[str, Any], args: argparse.Namespace) -> int:
    at = args.at if args.at is not None else float(state.get("current_day", 0) or 0)
    edges = [x for x in (state.get("spatial_edges", []) or []) if isinstance(x, dict)]
    result = travel_path(edges, args.start, args.end, float(at))
    if result is None:
        print(f"NO_PATH: {args.start} -> {args.end} at {at}")
        return 1
    cost, nodes, edge_ids = result
    emit({"from": args.start, "to": args.end, "at": at, "min_travel_time": cost, "path": nodes, "edges": edge_ids}, args.json)
    return 0


def cmd_scene_check(state: dict[str, Any], args: argparse.Namespace) -> int:
    scene_id = args.scene_id
    if not any(isinstance(s, dict) and str(s.get("id")) == scene_id for s in (state.get("scene_packets", []) or [])):
        print(f"ERROR: scene packet not found: {scene_id}")
        return 2
    related = [issue for issue in validate_issues(state) if scene_id in issue.get("scene_ids", [])]
    rel_errors = [str(x.get("message", "")) for x in related if x.get("severity") == "error"]
    rel_warnings = [str(x.get("message", "")) for x in related if x.get("severity") == "warning"]
    result = {"scene": scene_id, "errors": rel_errors, "warnings": rel_warnings}
    emit(result, args.json)
    return 1 if rel_errors else 0


def cmd_stale_research(state: dict[str, Any], args: argparse.Namespace) -> int:
    chapter = args.chapter if args.chapter is not None else state.get("current_chapter")
    day = args.day if args.day is not None else state.get("current_day")
    rows = stale_research_dependencies(state, chapter=chapter, day=day)
    emit(rows, args.json)
    return 1 if rows else 0


def cmd_thread_status(state: dict[str, Any], args: argparse.Namespace) -> int:
    rows = []
    for rec in state.get("threads", []) or []:
        if not isinstance(rec, dict):
            continue
        if args.thread_id and str(rec.get("id")) != args.thread_id:
            continue
        rows.append({
            "id": rec.get("id"),
            "status": rec.get("status"),
            "pressure": rec.get("pressure"),
            "owner": rec.get("owner"),
            "last_update_chapter": rec.get("last_update_chapter"),
            "next_trigger": rec.get("next_trigger"),
            "reader_visibility": rec.get("reader_visibility"),
        })
    emit(rows, args.json)
    return 0


def cmd_reader_state(state: dict[str, Any], args: argparse.Namespace) -> int:
    if args.chapter is None:
        emit(reader_state_at(state), args.json)
    else:
        result = query_reader_state(state, NarrativePosition(getattr(args, "axis", "presentation"), args.chapter))
        emit(result, args.json)
    return 0


def dependency_edges(state: dict[str, Any], args: argparse.Namespace) -> tuple[list[dict[str, Any]], str]:
    if args.dependencies is not None:
        raw = load_json(args.dependencies)
        source = str(args.dependencies)
    else:
        # Runtime Mode owns the authoritative dependency artifact. Prefer it over
        # any embedded projection copy, which may lag behind event/runtime updates.
        candidate = args.state.parent.parent / "runtime" / "dependencies.json"
        if candidate.is_file():
            raw = load_json(candidate)
            source = str(candidate)
        elif "dependencies" in state:
            raw = state.get("dependencies", [])
            source = "story-state.dependencies"
        else:
            print(
                "WARNING: no dependency source found; pass --dependencies or provide story-state.dependencies",
                file=sys.stderr,
            )
            return [], "none"
    if isinstance(raw, dict):
        raw = raw.get("edges", raw.get("dependencies", []))
    if not isinstance(raw, list):
        raise ValueError(f"dependency source {source} must contain a list or an object with edges")
    return [x for x in raw if isinstance(x, dict)], source


def cmd_propagate(state: dict[str, Any], args: argparse.Namespace) -> int:
    try:
        deps, _source = dependency_edges(state, args)
    except Exception as exc:
        print(f"ERROR: could not load dependencies: {exc}", file=sys.stderr)
        return 2
    graph: dict[str, list[dict[str, Any]]] = {}
    for dep in active_edges(deps, getattr(args, "at", None), getattr(args, "policy", "active_at")):
        source = dep.get("source")
        target = dep.get("target")
        if source is None or target is None:
            continue
        graph.setdefault(str(source), []).append(dep)
    seen = {args.node}
    queue: list[tuple[str, int]] = [(args.node, 0)]
    result: list[dict[str, Any]] = []
    while queue:
        node, depth = queue.pop(0)
        for dep in graph.get(node, []):
            target = str(dep.get("target"))
            if target in seen:
                continue
            seen.add(target)
            result.append({"source": node, "target": target, "kind": dep.get("kind"), "depth": depth + 1, "status": dep.get("status", "active")})
            queue.append((target, depth + 1))
    emit(result, args.json)
    return 0


def cmd_reflection_status(state: dict[str, Any], args: argparse.Namespace) -> int:
    rows: list[dict[str, Any]] = []
    for rec in state.get("humanities_reports", []) or []:
        if not isinstance(rec, dict):
            continue
        if args.chapter is not None and rec.get("chapter") != args.chapter:
            continue
        items = rec.get("items", []) or []
        counts: dict[str, int] = {}
        for item in items:
            if isinstance(item, dict):
                status = str(item.get("status", "UNKNOWN"))
                counts[status] = counts.get(status, 0) + 1
        rows.append({
            "chapter": rec.get("chapter"),
            "path": rec.get("path"),
            "chapter_version": rec.get("chapter_version"),
            "status": rec.get("status"),
            "item_status_counts": counts,
        })
    emit(rows, args.json)
    return 0



def cmd_authorial_unknowns(state: dict[str, Any], args: argparse.Namespace) -> int:
    rows: list[dict[str, Any]] = []
    query_id = getattr(args, "question_id", None)
    for i, rec in enumerate(state.get("authorial_unknowns", []) or []):
        if not isinstance(rec, dict):
            continue
        qid = issue_id(rec, i)
        if query_id and qid != query_id:
            continue
        if is_v2(rec):
            rows.append({
                "question_id": qid,
                "record_version": rec.get("record_version"),
                "mode": rec.get("mode"),
                "state": rec.get("state"),
                "resolution_policy": rec.get("resolution_policy"),
                "domain_semantics": rec.get("domain_semantics"),
                "viable_position_ids": [x.get("position_id") for x in viable_positions(rec)],
                "working_hypothesis_ids": [x.get("position_id") for x in working_positions(rec)],
                "decision_authority": rec.get("decision_authority"),
                "decision_horizon": rec.get("decision_horizon"),
                "commitment_fingerprint": commitment_fingerprint(rec),
            })
        else:
            rows.append({
                "question_id": qid,
                "record_version": rec.get("record_version", "legacy"),
                "mode": rec.get("mode"),
                "state": rec.get("status"),
                "viable_answers": rec.get("viable_answers", []),
                "decision_horizon": rec.get("earliest_required_resolution"),
                "decision_owner": rec.get("decision_owner"),
                "semantic_upgrade_required": str(rec.get("mode")) == "DELIBERATELY_UNRESOLVED",
            })
    emit(rows, args.json)
    return 0


def cmd_irreversibility(state: dict[str, Any], args: argparse.Namespace) -> int:
    rows: list[dict[str, Any]] = []
    for rec in state.get("irreversibility", []) or []:
        if not isinstance(rec, dict):
            continue
        level = str(rec.get("reversibility", rec.get("level", "")))
        if args.level and level != args.level:
            continue
        rows.append({
            "id": rec.get("id", rec.get("event_id")),
            "reversibility": level,
            "reversal_cost": rec.get("reversal_cost"),
            "residue": rec.get("residue"),
            "status": rec.get("status", "active"),
        })
    emit(rows, args.json)
    return 0

def cmd_narrative_debt(state: dict[str, Any], args: argparse.Namespace) -> int:
    rows: list[dict[str, Any]] = []
    for rec in state.get("narrative_debt", state.get("narrative_debts", [])) or []:
        if not isinstance(rec, dict):
            continue
        status = str(rec.get("status", "open"))
        severity = str(rec.get("severity", "medium"))
        if args.status and status != args.status:
            continue
        if args.severity and severity != args.severity:
            continue
        rows.append({
            "debt_id": rec.get("debt_id", rec.get("id")),
            "kind": rec.get("kind"),
            "issue": rec.get("issue"),
            "severity": severity,
            "status": status,
            "resolve_before": rec.get("resolve_before"),
            "interest": rec.get("interest"),
            "depends_on": rec.get("depends_on", []),
        })
    emit(rows, args.json)
    return 1 if any(str(x.get("severity")) == "blocking" and str(x.get("status")) not in {"resolved", "accepted", "retired"} for x in rows) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only deterministic story-state queries")
    parser.add_argument("state", type=Path, help="story-state JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("knowledge", help="show what an actor knows at a time")
    p.add_argument("actor")
    p.add_argument("--at", type=float)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("travel", help="compute minimum modeled travel path")
    p.add_argument("start")
    p.add_argument("end")
    p.add_argument("--at", type=float)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("scene-check", help="show deterministic findings involving one scene")
    p.add_argument("scene_id")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("stale-research", help="show research dependencies requiring review")
    p.add_argument("--chapter", type=int)
    p.add_argument("--day", type=float)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("thread-status", help="show active/known causal thread state")
    p.add_argument("thread_id", nargs="?")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("reader-state", help="show current or chapter-scoped reader state")
    p.add_argument("--chapter", type=int)
    p.add_argument("--axis", default="presentation", help="chapter adapter supports only presentation")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("propagate", help="compute transitive artifacts affected by a changed node")
    p.add_argument("node")
    p.add_argument("--dependencies", type=Path, help="dependency graph JSON; Runtime Mode also auto-discovers runtime/dependencies.json")
    p.add_argument("--at", type=float, help="numeric position in the dependency artifact's declared axis")
    p.add_argument("--policy", choices=["active_at", "historical_all"], default="active_at")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("reflection-status", help="show humanities-analysis decision state")
    p.add_argument("--chapter", type=int)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("open-issues", help="show governed authorial OpenIssue state")
    p.add_argument("question_id", nargs="?")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("authorial-unknowns", help="compatibility alias for open-issues")
    p.add_argument("question_id", nargs="?")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("narrative-debt", help="show open Narrative Debt items")
    p.add_argument("--status")
    p.add_argument("--severity")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("irreversibility", help="show low-reversibility consequence records")
    p.add_argument("--level")
    p.add_argument("--json", action="store_true")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        state = load_json(args.state)
    except Exception as exc:
        print(f"ERROR: could not load state: {exc}", file=sys.stderr)
        return 2

    commands = {
        "knowledge": cmd_knowledge,
        "travel": cmd_travel,
        "scene-check": cmd_scene_check,
        "stale-research": cmd_stale_research,
        "thread-status": cmd_thread_status,
        "reader-state": cmd_reader_state,
        "propagate": cmd_propagate,
        "reflection-status": cmd_reflection_status,
        "open-issues": cmd_authorial_unknowns,
        "authorial-unknowns": cmd_authorial_unknowns,
        "narrative-debt": cmd_narrative_debt,
        "irreversibility": cmd_irreversibility,
    }
    return commands[args.command](state, args)


if __name__ == "__main__":
    raise SystemExit(main())
