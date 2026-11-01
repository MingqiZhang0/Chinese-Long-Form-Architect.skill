#!/usr/bin/env python3
"""Generate a compact read-only observatory report from structured story state."""

from __future__ import annotations

from dependency_activity import is_edge_active

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from research_freshness import stale_research_dependencies
    from reader_state import foreground_questions, reader_state_at
    from open_issue import summarize_state as summarize_open_issues
except ImportError:  # pragma: no cover - direct packaging fallback
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from research_freshness import stale_research_dependencies
    from reader_state import foreground_questions, reader_state_at
    from open_issue import summarize_state as summarize_open_issues


def load(path: str | None, default: Any) -> Any:
    if not path:
        return default
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def load_records(
    path: str | None,
    *,
    recursive: bool = False,
    predicate: Any = None,
) -> list[dict[str, Any]]:
    if not path:
        return []
    p = Path(path)
    if p.is_dir():
        paths = sorted(p.rglob("*.json") if recursive else p.glob("*.json"))
    else:
        paths = [p]
    rows: list[dict[str, Any]] = []
    for item in paths:
        try:
            data = load(str(item), {})
        except Exception:
            continue
        candidates: list[dict[str, Any]] = []
        if isinstance(data, dict):
            candidates = [data]
        elif isinstance(data, list):
            candidates = [x for x in data if isinstance(x, dict)]
        for rec in candidates:
            if predicate is None or predicate(rec):
                rows.append(rec)
    return rows


def is_revision_impact_report(rec: dict[str, Any]) -> bool:
    required = {"chapter_id", "branch", "before_hash", "after_hash", "changes", "approval_status"}
    return required.issubset(rec) and isinstance(rec.get("changes"), list)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state")
    p.add_argument("--project-manifest", help="optional project-manifest.json; fills canonical state/runtime/dependency/revision paths when omitted")
    p.add_argument("--branches")
    p.add_argument("--dependencies")
    p.add_argument("--artifacts", help="optional artifact-registry JSON for read-only GC candidates")
    p.add_argument("--manifest", help="optional runtime manifest JSON")
    p.add_argument("--debt", help="optional Narrative Debt registry JSON")
    p.add_argument("--invariant-report", help="optional JSON output from validate_invariants.py")
    p.add_argument("--task-orders", help="optional task-order JSON file or directory")
    p.add_argument("--revision-reports", help="optional revision-impact JSON file or directory; directories are searched recursively and non-report JSON is ignored")
    p.add_argument("--merge-plans", help="optional merge-plan JSON file or directory")
    p.add_argument("--out")
    args = p.parse_args()

    project_manifest: dict[str, Any] = {}
    project_root: Path | None = None
    if args.project_manifest:
        project_manifest_path = Path(args.project_manifest).resolve()
        project_root = project_manifest_path.parent
        project_manifest = load(str(project_manifest_path), {})
        paths = project_manifest.get("canonical_paths", {}) if isinstance(project_manifest, dict) else {}
        if not isinstance(paths, dict):
            paths = {}
        def project_path(key: str) -> str | None:
            rel = paths.get(key)
            if not isinstance(rel, str) or not rel:
                return None
            target = (project_root / rel).resolve()
            try:
                target.relative_to(project_root)
            except ValueError as exc:
                raise SystemExit(f"project manifest path escapes root: {key}={rel}") from exc
            return str(target)
        args.state = args.state or project_path("story_state")
        args.manifest = args.manifest or project_path("runtime_manifest")
        args.revision_reports = args.revision_reports or project_path("revisions_dir")
        if args.manifest and (not args.dependencies or not args.branches):
            runtime_manifest = load(args.manifest, {})
            rpaths = runtime_manifest.get("paths", {}) if isinstance(runtime_manifest, dict) else {}
            if isinstance(rpaths, dict):
                if not args.dependencies and isinstance(rpaths.get("dependencies"), str):
                    args.dependencies = str((project_root / rpaths["dependencies"]).resolve())
                if not args.branches and isinstance(rpaths.get("branches"), str):
                    args.branches = str((project_root / rpaths["branches"]).resolve())
                if not args.debt and isinstance(rpaths.get("narrative_debt"), str):
                    args.debt = str((project_root / rpaths["narrative_debt"]).resolve())
    if not args.state:
        p.error("--state is required unless --project-manifest resolves canonical_paths.story_state")

    state = load(args.state, {})
    branches_raw = load(args.branches, {})
    branches = branches_raw.get("branches", branches_raw) if isinstance(branches_raw, dict) else {}
    deps_raw = load(args.dependencies, [])
    deps = deps_raw.get("edges", deps_raw) if isinstance(deps_raw, dict) else deps_raw
    if not isinstance(deps, list):
        deps = []
    artifacts_raw = load(args.artifacts, [])
    artifacts = artifacts_raw.get("artifacts", artifacts_raw) if isinstance(artifacts_raw, dict) else artifacts_raw
    if not isinstance(artifacts, list):
        artifacts = []

    manifest = load(args.manifest, {}) if args.manifest else {}
    debt_raw = load(args.debt, {}) if args.debt else state.get("narrative_debt", state.get("narrative_debts", []))
    debt_items = debt_raw.get("items", debt_raw) if isinstance(debt_raw, dict) else debt_raw
    if not isinstance(debt_items, list):
        debt_items = []
    invariant_report = load(args.invariant_report, {}) if args.invariant_report else {}
    task_orders = load_records(args.task_orders)
    revision_reports = load_records(args.revision_reports, recursive=True, predicate=is_revision_impact_report)
    merge_plans = load_records(args.merge_plans)

    threads = [x for x in state.get("threads", []) if isinstance(x, dict)]
    active_threads = [x for x in threads if str(x.get("status", "active")) not in {"resolved", "retired", "closed"}]
    stale_research = stale_research_dependencies(state)
    scenes = [x for x in state.get("scene_packets", []) if isinstance(x, dict)]
    invalid_scenes = [x for x in scenes if str(x.get("status", "")) == "invalidated"]
    reports = [x for x in state.get("humanities_reports", []) if isinstance(x, dict)]
    pending_reports = [x for x in reports if str(x.get("status", "")).upper() in {"PENDING_USER_DECISION", "STALE_AFTER_REVISION"}]
    open_issue_summary = summarize_open_issues(state)
    unknowns = [x for x in state.get("authorial_unknowns", []) if isinstance(x, dict)]
    irreversible = [x for x in state.get("irreversibility", []) if isinstance(x, dict) and str(x.get("status", "active")).lower() == "active"]

    open_debt = [x for x in debt_items if isinstance(x, dict) and str(x.get("status", "open")).lower() not in {"resolved", "accepted", "retired"}]
    blocking_debt = [x for x in open_debt if str(x.get("severity", "")).lower() == "blocking"]
    invariant_errors = invariant_report.get("errors", []) if isinstance(invariant_report, dict) else []
    blocking_objections = []
    for order in task_orders:
        for obj in order.get("objections", []) or []:
            if isinstance(obj, dict) and str(obj.get("severity", "")).lower() == "blocking" and str(obj.get("status", "open")).lower() not in {"resolved", "overridden"}:
                blocking_objections.append({"task_id": order.get("task_id"), **obj})
    pending_revisions = [r for r in revision_reports if str(r.get("approval_status", "PENDING_REVIEW")).upper() in {"PENDING_REVIEW", "REQUIRES_CHANGE_CONTROL"}]
    unresolved_merges = [m for m in merge_plans if str(m.get("status", "pending")).lower() not in {"resolved", "rejected", "merged"}]
    runtime_version = manifest.get("runtime_schema_version") if isinstance(manifest, dict) else None

    out_degree = Counter()
    in_degree = Counter()
    for edge in deps:
        if not isinstance(edge, dict) or not is_edge_active(edge):
            continue
        if edge.get("source") is not None:
            out_degree[str(edge.get("source"))] += 1
        if edge.get("target") is not None:
            in_degree[str(edge.get("target"))] += 1
    hotspots = [{"node": n, "downstream_edges": c} for n, c in out_degree.most_common(10) if c > 1]

    safe_status = {"stale", "invalidated", "temporary", "rejected", "retired", "superseded-cache"}
    gc_candidates = []
    for rec in artifacts:
        if not isinstance(rec, dict):
            continue
        if rec.get("rebuildable") is True and str(rec.get("status", "")).lower() in safe_status and rec.get("audit_required") is not True:
            gc_candidates.append(rec)

    reader = reader_state_at(state)
    open_questions = foreground_questions(reader)
    project_paths = project_manifest.get("canonical_paths", {}) if isinstance(project_manifest, dict) else {}
    project_poetics_ref = project_paths.get("project_poetics") if isinstance(project_paths, dict) else None
    poetics_override_refs = project_manifest.get("poetics_override_refs", []) if isinstance(project_manifest, dict) else []
    optional_artifacts = project_manifest.get("optional_artifacts", []) if isinstance(project_manifest, dict) else []

    lines = [
        "# Story Observatory",
        "",
        f"- current_chapter: {state.get('current_chapter', '?')}",
        f"- active_threads: {len(active_threads)}",
        f"- stale_research_dependencies: {len(stale_research)}",
        f"- invalidated_scene_packets: {len(invalid_scenes)}",
        f"- humanities_reports_needing_attention: {len(pending_reports)}",
        f"- open_authorial_issues: {open_issue_summary['open']}",
        f"- must_resolve_open_issues: {open_issue_summary['must_resolve_open']}",
        f"- preserve_open_issues: {open_issue_summary['preserve_open']}",
        f"- legacy_open_issues_needing_semantic_review: {open_issue_summary['legacy_review_required']}",
        f"- active_irreversibility_records: {len(irreversible)}",
        f"- reader_questions_visible_in_state: {len(open_questions) if isinstance(open_questions, list) else 0}",
        f"- branches: {len(branches) if isinstance(branches, dict) else 0}",
        f"- runtime_schema_version: {runtime_version or 'not-supplied'}",
        f"- project_poetics_ref: {project_poetics_ref or 'not-supplied'}",
        f"- poetics_overrides: {len(poetics_override_refs) if isinstance(poetics_override_refs, list) else 0}",
        f"- optional_planning_artifacts: {len(optional_artifacts) if isinstance(optional_artifacts, list) else 0}",
        f"- hard_invariant_failures: {len(invariant_errors) if isinstance(invariant_errors, list) else 0}",
        f"- open_narrative_debt: {len(open_debt)} (blocking={len(blocking_debt)})",
        f"- unresolved_blocking_objections: {len(blocking_objections)}",
        f"- semantic_revision_reports_needing_review: {len(pending_revisions)}",
        f"- unresolved_merge_plans: {len(unresolved_merges)}",
        "",
        "## Project health (triage, not a score)",
        "",
        f"- schema/runtime: {'provided' if runtime_version else 'not assessed'}",
        f"- invariants: {'FAIL' if invariant_errors else 'clear/not assessed'}",
        f"- blocking debt: {len(blocking_debt)}",
        f"- blocking objections: {len(blocking_objections)}",
        f"- invalid scene packets: {len(invalid_scenes)}",
        f"- stale research: {len(stale_research)}",
        "",
        "## Dependency hot spots",
        "",
    ]
    if hotspots:
        for h in hotspots:
            lines.append(f"- {h['node']}: {h['downstream_edges']} direct downstream edges")
    else:
        lines.append("- none detected")

    lines.extend(["", "## Stale research", ""])
    if stale_research:
        for x in stale_research:
            lines.append(f"- {x.get('id', '?')}: {x.get('scope', '')}")
    else:
        lines.append("- none")

    lines.extend(["", "## Invalidated scene packets", ""])
    if invalid_scenes:
        for x in invalid_scenes:
            lines.append(f"- {x.get('id', '?')}")
    else:
        lines.append("- none")

    lines.extend(["", "## Project Poetics (read-only pointers)", ""])
    lines.append(f"- canonical: {project_poetics_ref or 'not supplied'}")
    if isinstance(poetics_override_refs, list) and poetics_override_refs:
        for ref in poetics_override_refs:
            lines.append(f"- override: {ref}")
    else:
        lines.append("- overrides: none declared")

    lines.extend(["", "## Authorial unknowns", ""])
    if unknowns:
        for x in unknowns:
            lines.append(f"- {x.get('question_id', '?')}: mode={x.get('mode')}, resolve_by={x.get('earliest_required_resolution')}")
    else:
        lines.append("- none")

    lines.extend(["", "## Low-reversibility consequences", ""])
    if irreversible:
        for x in irreversible:
            lines.append(f"- {x.get('id', x.get('event_id', '?'))}: {x.get('reversibility', x.get('level', 'unspecified'))}")
    else:
        lines.append("- none")

    lines.extend(["", "## Narrative Debt", ""])
    if open_debt:
        rank = {"blocking": 0, "high": 1, "medium": 2, "low": 3}
        for x in sorted(open_debt, key=lambda r: (rank.get(str(r.get("severity", "medium")).lower(), 9), str(r.get("resolve_before", "")))):
            lines.append(f"- {x.get('debt_id', x.get('id', '?'))}: severity={x.get('severity')}, resolve_before={x.get('resolve_before')}, interest={x.get('interest', '')}")
    else:
        lines.append("- none")

    lines.extend(["", "## Garbage-collection candidates (report only)", ""])
    if gc_candidates:
        for x in gc_candidates:
            lines.append(f"- {x.get('path', x.get('id', '?'))}: status={x.get('status')}, class={x.get('class', '')}")
    else:
        lines.append("- none")

    lines.extend(["", "## Active branches", ""])
    if isinstance(branches, dict) and branches:
        for name, rec in branches.items():
            if not isinstance(rec, dict):
                continue
            lines.append(f"- {name}: status={rec.get('status', 'active')}, parent={rec.get('parent')}, fork={rec.get('fork_event')}")
    else:
        lines.append("- none registered")

    text = "\n".join(lines).rstrip() + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
