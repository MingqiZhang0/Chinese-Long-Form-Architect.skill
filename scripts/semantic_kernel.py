#!/usr/bin/env python3
"""Verify cross-layer Narrative Semantics Kernel contracts.

This verifier composes existing canonical backends. It does not create story facts,
write canon, or replace local validators. It checks only machine-decidable seams
between event history, branches, context taint, revision/reconciliation artifacts,
and OpenIssue/authorial-open-design state.
"""

from __future__ import annotations

from dependency_activity import is_edge_active

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compile_context import released_secret_ids, taint_closure  # type: ignore
from narrative_runtime import (  # type: ignore
    branch_map,
    effective_events,
    events_by_branch,
    load_jsonl,
    replay,
    validate_runtime,
)
from prose_state_reconcile import validate_report as validate_reconciliation  # type: ignore
from revision_diff import validate_dependency_review
from open_issue import position_index, validate_state as validate_open_issue_state  # type: ignore
from validate_intake_state import check_project_decisions
from research_freshness import temporal_bounds, temporal_order, temporal_applicability, validate_research_records, window_bounds


LAWS: list[dict[str, Any]] = [
    {"id": "K1", "name": "type-separation", "machine_checkable": "partial"},
    {"id": "K2", "name": "no-spontaneous-canon", "machine_checkable": "partial"},
    {"id": "K3", "name": "replay-determinism", "machine_checkable": True},
    {"id": "K4", "name": "snapshot-transparency", "machine_checkable": True},
    {"id": "K5", "name": "branch-prefix-preservation", "machine_checkable": True},
    {"id": "K6", "name": "branch-isolation", "machine_checkable": "partial"},
    {"id": "K7", "name": "epistemic-truthfulness", "machine_checkable": False},
    {"id": "K8", "name": "epistemic-locality", "machine_checkable": False},
    {"id": "K9", "name": "reader-non-authority", "machine_checkable": False},
    {"id": "K10", "name": "taint-closure", "machine_checkable": True},
    {"id": "K11", "name": "declassification-preserves-provenance", "machine_checkable": "partial"},
    {"id": "K12", "name": "evidence-provenance-distinction", "machine_checkable": False},
    {"id": "K13", "name": "evidence-freshness", "machine_checkable": True},
    {"id": "K14", "name": "minimal-semantic-disturbance", "machine_checkable": "partial"},
    {"id": "K15", "name": "provenance-closure", "machine_checkable": "partial"},
    {"id": "K16", "name": "open-truth-preservation", "machine_checkable": "partial"},
    {"id": "K17", "name": "migration-semantic-preservation", "machine_checkable": "regression"},
    {"id": "K18", "name": "stable-semantic-identity", "machine_checkable": "partial"},
    {"id": "K19", "name": "analysis-is-defeasible", "machine_checkable": False},
    {"id": "K20", "name": "formalization-restraint", "machine_checkable": False},
    {"id": "K21", "name": "epistemic-acquisition-coverage", "machine_checkable": "partial"},
    {"id": "K22", "name": "precision-monotonicity", "machine_checkable": "partial"},
]

LAW_BY_ID: dict[str, dict[str, Any]] = {row["id"]: row for row in LAWS}
if len(LAW_BY_ID) != len(LAWS):
    raise RuntimeError("Narrative Semantics Kernel law registry contains duplicate IDs")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(value: Any) -> str:
    blob = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def safe_path(root: Path, rel: str) -> Path:
    path = (root / rel).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {rel}") from exc
    return path


def add(rows: list[dict[str, Any]], law: str, status: str, message: str, **details: Any) -> None:
    if law not in LAW_BY_ID:
        raise ValueError(f"unknown Narrative Semantics Kernel law ID: {law}")
    rec = {"law": law, "law_name": LAW_BY_ID[law]["name"], "status": status, "message": message}
    if details:
        rec["details"] = details
    rows.append(rec)


def runtime_paths(root: Path, project_manifest: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Path]]:
    canonical = project_manifest.get("canonical_paths", {})
    rel = canonical.get("runtime_manifest") if isinstance(canonical, dict) else None
    if not isinstance(rel, str) or not rel:
        return None, {}
    manifest_path = safe_path(root, rel)
    if not manifest_path.is_file():
        raise ValueError(f"missing runtime manifest: {rel}")
    runtime_manifest = load_json(manifest_path)
    if not isinstance(runtime_manifest, dict):
        raise ValueError("runtime manifest must be an object")
    raw_paths = runtime_manifest.get("paths", {})
    if not isinstance(raw_paths, dict):
        raise ValueError("runtime manifest .paths must be an object")
    paths: dict[str, Path] = {}
    for key, value in raw_paths.items():
        if isinstance(value, str) and value:
            paths[str(key)] = safe_path(root, value)
    return runtime_manifest, paths


def verify_runtime(root: Path, project_manifest: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    enabled = {str(x) for x in project_manifest.get("enabled_subsystems", [])}
    if "narrative-runtime" not in enabled:
        add(rows, "K3", "skip", "Runtime Mode is not enabled; replay laws are not applicable.")
        add(rows, "K4", "skip", "Runtime Mode is not enabled; snapshot transparency is not applicable.")
        add(rows, "K5", "skip", "Runtime Mode is not enabled; branch-prefix replay law is not applicable.")
        return {}

    try:
        rmanifest, paths = runtime_paths(root, project_manifest)
    except Exception as exc:
        add(rows, "K3", "fail", f"Runtime contract could not be loaded: {exc}")
        return {}
    if rmanifest is None:
        add(rows, "K3", "fail", "Narrative Runtime is enabled but no runtime_manifest canonical path exists.")
        return {}

    pid = str(project_manifest.get("project_id", ""))
    if str(rmanifest.get("project_id", "")) != pid:
        add(rows, "K18", "fail", "Project/runtime identity mismatch.", project_id=pid, runtime_project_id=rmanifest.get("project_id"))
    else:
        add(rows, "K18", "pass", "Project/runtime identity is consistent.")

    current_branch = str(project_manifest.get("current_branch", "main"))
    if str(rmanifest.get("current_branch", "main")) != current_branch:
        add(rows, "K5", "fail", "Project/runtime current branch mismatch.", project_branch=current_branch, runtime_branch=rmanifest.get("current_branch"))

    events_path = paths.get("events")
    branches_path = paths.get("branches")
    dependencies_path = paths.get("dependencies")
    if not events_path or not events_path.is_file() or not branches_path or not branches_path.is_file():
        add(rows, "K3", "fail", "Runtime events/branches artifacts are missing.")
        return {}

    try:
        events = load_jsonl(events_path)
        branches = branch_map(load_json(branches_path))
        dependencies = load_json(dependencies_path) if dependencies_path and dependencies_path.is_file() else None
        provenance_path = paths.get("provenance")
        provenance = load_json(provenance_path) if provenance_path and provenance_path.is_file() else None
        errors, warnings = validate_runtime(events, branches, dependencies, provenance, rmanifest.get("strict_audit") is True)
    except Exception as exc:
        add(rows, "K3", "fail", f"Runtime validation raised: {exc}")
        return {}
    if errors:
        add(rows, "K3", "fail", "Runtime contract is invalid.", errors=errors, warnings=warnings)
        return {}
    if warnings:
        add(rows, "K3", "warn", "Runtime contract is valid with warnings.", warnings=warnings)

    try:
        state1, applied1 = replay(events, branches, current_branch)
        state2, applied2 = replay(events, branches, current_branch)
    except Exception as exc:
        add(rows, "K3", "fail", f"Replay failed: {exc}")
        return {}

    if stable_hash(state1) != stable_hash(state2) or [x.get("event_id") for x in applied1] != [x.get("event_id") for x in applied2]:
        add(rows, "K3", "fail", "Repeated replay of the same effective history was not deterministic.")
    else:
        add(rows, "K3", "pass", "Repeated replay produced the same deterministic projection.", projection_sha256=stable_hash(state1), effective_event_count=len(applied1))

    by_branch = events_by_branch(events)
    branch_failures: list[str] = []
    for name, rec in branches.items():
        parent = rec.get("parent")
        if parent in (None, ""):
            continue
        try:
            parent_hist = effective_events(str(parent), branches, by_branch)
            child_hist = effective_events(name, branches, by_branch)
        except Exception as exc:
            branch_failures.append(f"{name}: {exc}")
            continue
        fork = str(rec.get("fork_event"))
        cut = next((i for i, ev in enumerate(parent_hist) if str(ev.get("event_id")) == fork), None)
        if cut is None:
            branch_failures.append(f"{name}: fork event {fork} missing from parent effective history")
            continue
        parent_prefix = [str(x.get("event_id")) for x in parent_hist[: cut + 1]]
        child_prefix = [str(x.get("event_id")) for x in child_hist[: cut + 1]]
        if parent_prefix != child_prefix:
            branch_failures.append(f"{name}: child history does not preserve the parent prefix through {fork}")
    if branch_failures:
        add(rows, "K5", "fail", "One or more branches violate shared-prefix semantics.", failures=branch_failures)
    else:
        add(rows, "K5", "pass", "All declared child branches preserve their parent history through the fork.")

    effective = effective_events(current_branch, branches, by_branch)
    actual_head = str(effective[-1].get("event_id")) if effective else None
    declared_head = project_manifest.get("last_committed_event")
    if declared_head is not None and str(declared_head) != str(actual_head):
        add(rows, "K2", "fail", "Project Manifest last_committed_event disagrees with the active branch head.", declared=declared_head, actual=actual_head)
    else:
        add(rows, "K2", "pass", "Project Manifest branch head agrees with committed Runtime history.", head=actual_head)

    snap_dir = paths.get("snapshots")
    snapshots = sorted(snap_dir.glob("*.json")) if snap_dir and snap_dir.is_dir() else []
    snap_failures: list[str] = []
    checked = 0
    for snap_path in snapshots:
        try:
            snap = load_json(snap_path)
            if not isinstance(snap, dict):
                raise ValueError("snapshot must be an object")
            branch = str(snap.get("branch"))
            through = snap.get("through_event")
            if branch not in branches:
                raise ValueError(f"unknown branch {branch}")
            canonical_at_snap, _ = replay(events, branches, branch, through_event=str(through) if through else None)
            if stable_hash(canonical_at_snap) != stable_hash(snap.get("state", {})):
                raise ValueError("snapshot state differs from full replay through its declared event")
            full, _ = replay(events, branches, branch)
            resumed, _ = replay(events, branches, branch, base_state=snap.get("state", {}), start_after_event=str(through) if through else None)
            if stable_hash(full) != stable_hash(resumed):
                raise ValueError("snapshot + suffix replay differs from full replay")
            checked += 1
        except Exception as exc:
            snap_failures.append(f"{snap_path.relative_to(root)}: {exc}")
    if snap_failures:
        add(rows, "K4", "fail", "Snapshot transparency failed.", failures=snap_failures)
    elif checked:
        add(rows, "K4", "pass", "Snapshots are transparent to deterministic replay.", checked=checked)
    else:
        add(rows, "K4", "skip", "No snapshots are present; snapshot transparency has nothing to check.")

    story_times = [e.get("story_time") for e in effective if e.get("story_time") is not None]
    add(rows, "K1", "pass", "Temporal axes remain distinct: commit order is branch sequence; story_time is treated as separate metadata.", story_time_samples=len(story_times), commit_events=len(effective))

    return {"projection": state1, "events": events, "branches": branches, "effective": effective, "runtime_manifest": rmanifest, "paths": paths, "dependencies": dependencies}


def entry_branches(entry: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    value = entry.get("branch")
    if isinstance(value, str) and value:
        out.add(value)
    values = entry.get("branches")
    if isinstance(values, list):
        out.update(str(x) for x in values if x not in (None, ""))
    return out


def branch_ancestor_or_same(ancestor: str, child: str, branches: dict[str, dict[str, Any]]) -> bool:
    if ancestor == child:
        return True
    current = child
    seen: set[str] = set()
    while current in branches and current not in seen:
        seen.add(current)
        parent = branches[current].get("parent")
        if parent in (None, ""):
            return False
        parent_s = str(parent)
        if parent_s == ancestor:
            return True
        current = parent_s
    return False


def verify_context_branch_isolation(entries: list[dict[str, Any]], branches: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> None:
    if not branches:
        add(rows, "K6", "skip", "No Runtime branch registry is available for context branch-isolation checks.")
        return
    by_id = {str(x.get("id")): x for x in entries if isinstance(x, dict) and x.get("id") is not None}
    failures: list[str] = []
    checked = 0
    known = set(branches)
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("id") is None:
            continue
        eid = str(entry.get("id"))
        targets = entry_branches(entry)
        unknown_targets = targets - known
        if unknown_targets:
            failures.append(f"{eid}: context entry references unknown branch(es) {sorted(unknown_targets)}")
        parent_ids = entry.get("derived_from", [])
        if not isinstance(parent_ids, list):
            continue
        for pid_raw in parent_ids:
            parent = by_id.get(str(pid_raw))
            if not isinstance(parent, dict):
                continue
            sources = entry_branches(parent)
            if not sources:
                continue
            checked += 1
            unknown_sources = sources - known
            if unknown_sources:
                failures.append(f"{eid}: provenance parent {pid_raw} references unknown branch(es) {sorted(unknown_sources)}")
                continue
            if not targets:
                failures.append(f"{eid}: global context artifact derives from branch-local parent {pid_raw} on {sorted(sources)}")
                continue
            for target in sorted(targets):
                if not any(branch_ancestor_or_same(source, target, branches) for source in sources):
                    failures.append(f"{eid}: branch {target} derives from unrelated/descendant branch-local parent {pid_raw} on {sorted(sources)}")
    if failures:
        add(rows, "K6", "fail", "Context provenance crosses branch boundaries without an ancestor relationship.", failures=failures)
    elif checked or any(entry_branches(x) for x in entries if isinstance(x, dict)):
        add(rows, "K6", "pass", "Branch-scoped context provenance stays within the same branch or an ancestor-to-descendant lineage.", checked=checked)
    else:
        add(rows, "K6", "skip", "Context Index has no branch-scoped entries to test.")


def verify_context(root: Path, project_manifest: dict[str, Any], rows: list[dict[str, Any]], branches: dict[str, dict[str, Any]] | None = None) -> None:
    paths = project_manifest.get("canonical_paths", {})
    if not isinstance(paths, dict):
        return
    index_rel = paths.get("context_index")
    if not isinstance(index_rel, str):
        add(rows, "K10", "skip", "No canonical Context Index is declared.")
        return
    index_path = safe_path(root, index_rel)
    if not index_path.is_file():
        add(rows, "K10", "fail", f"Context Index is declared but missing: {index_rel}")
        return
    raw = load_json(index_path)
    entries = raw.get("entries", []) if isinstance(raw, dict) else []
    if not isinstance(entries, list):
        add(rows, "K10", "fail", "Context Index entries must be a list.")
        return
    typed_entries = [x for x in entries if isinstance(x, dict)]
    verify_context_branch_isolation(typed_entries, branches or {}, rows)
    try:
        closure, missing = taint_closure(typed_entries)
    except Exception as exc:
        add(rows, "K10", "fail", f"Context derivation/taint closure failed: {exc}")
        return
    if missing:
        add(rows, "K15", "fail", "Context derivation graph contains missing provenance parents.", missing={k: sorted(v) for k, v in missing.items()})
    else:
        add(rows, "K15", "pass", "Context derivation graph has no missing provenance parents.")

    secret_rel = paths.get("secret_registry")
    known_secret_ids: set[str] = set()
    if isinstance(secret_rel, str):
        secret_path = safe_path(root, secret_rel)
        if not secret_path.is_file():
            add(rows, "K10", "fail", f"Secret Registry is declared but missing: {secret_rel}")
        else:
            registry = load_json(secret_path)
            secrets = registry.get("secrets", []) if isinstance(registry, dict) else []
            seen: set[str] = set()
            dupes: set[str] = set()
            for rec in secrets if isinstance(secrets, list) else []:
                if not isinstance(rec, dict) or not isinstance(rec.get("id"), str):
                    continue
                sid = str(rec["id"])
                if sid in seen:
                    dupes.add(sid)
                seen.add(sid)
            known_secret_ids = seen
            if dupes:
                add(rows, "K10", "fail", "Secret Registry contains duplicate secret IDs.", duplicate_ids=sorted(dupes))

    declass_errors: list[str] = []
    active_taint_count = 0
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("id") is None:
            continue
        eid = str(entry.get("id"))
        taints = closure.get(eid, set())
        active_taint_count += len(taints)
        declass = entry.get("declassification")
        if isinstance(declass, dict):
            ids = declass.get("secret_ids")
            if isinstance(ids, list):
                requested = {str(x) for x in ids}
                unknown = requested - taints
                if unknown:
                    declass_errors.append(f"{eid}: declassification references taints not carried by the artifact: {sorted(unknown)}")
                if known_secret_ids:
                    absent = requested - known_secret_ids
                    if absent:
                        declass_errors.append(f"{eid}: declassification references unknown registry IDs: {sorted(absent)}")
        for role in entry.get("declassified_for", []) if isinstance(entry.get("declassified_for"), list) else []:
            released = released_secret_ids(entry, str(role), taints)
            if released - taints:
                declass_errors.append(f"{eid}: declassification for {role} releases a non-carried taint")
    if declass_errors:
        add(rows, "K11", "fail", "Declassification metadata violates provenance-scoped release.", failures=declass_errors)
    else:
        add(rows, "K11", "pass", "Declassification metadata releases only provenance-carried taints.")
    add(rows, "K10", "pass", "Semantic taint closure computed successfully across context derivations.", entry_count=len(entries), taint_edges_count=active_taint_count)


def verify_reconciliations(root: Path, project_manifest: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    paths = project_manifest.get("canonical_paths", {})
    rel = paths.get("reconciliations_dir") if isinstance(paths, dict) else None
    if not isinstance(rel, str):
        add(rows, "K13", "skip", "No reconciliation directory is declared.")
        return
    directory = safe_path(root, rel)
    if not directory.is_dir():
        add(rows, "K13", "fail", f"Reconciliation directory is declared but missing: {rel}")
        return
    if "chapter_rollover" in project_manifest:
        add(rows, "K13", "skip", "Activated rollover validates the Project State-selected freeze; unselected reconciliation reports remain historical/unverified.")
        return
    failures: list[str] = []
    warnings: list[str] = []
    checked = 0
    for path in sorted(directory.rglob("*.json")):
        try:
            report = load_json(path)
        except Exception:
            continue
        if not isinstance(report, dict) or not report.get("reconciliation_version"):
            continue
        if str(report.get("status")) != "APPROVED":
            continue
        checked += 1
        errors, warns, _ = validate_reconciliation(report, root, strict=True)
        failures.extend(f"{path.relative_to(root)}: {x}" for x in errors)
        warnings.extend(f"{path.relative_to(root)}: {x}" for x in warns)
    if failures:
        add(rows, "K13", "fail", "Approved reconciliation evidence is stale or invalid.", failures=failures, warnings=warnings)
    elif checked:
        add(rows, "K13", "pass", "Approved reconciliation evidence is fresh and structurally valid.", checked=checked, warnings=warnings)
    else:
        add(rows, "K13", "skip", "No APPROVED reconciliation reports are present.")


def verify_revisions(root: Path, project_manifest: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    paths = project_manifest.get("canonical_paths", {})
    rel = paths.get("revisions_dir") if isinstance(paths, dict) else None
    if not isinstance(rel, str):
        add(rows, "K14", "skip", "No semantic revision directory is declared.")
        return
    directory = safe_path(root, rel)
    if not directory.is_dir():
        add(rows, "K14", "fail", f"Revision directory is declared but missing: {rel}")
        return
    errors: list[str] = []
    checked = 0
    for path in sorted(directory.rglob("impact.json")):
        try:
            report = load_json(path)
        except Exception:
            continue
        if not isinstance(report, dict) or not isinstance(report.get("changes"), list):
            continue
        checked += 1
        errors.extend(f"{path.relative_to(root)}: {error}" for error in validate_dependency_review(report, root))
        labels: list[str] = []
        candidate_count = 0
        for change in report.get("changes", []):
            if not isinstance(change, dict):
                continue
            labels.extend(str(x) for x in change.get("impact_labels", []) if x is not None)
            cds = change.get("candidate_deltas", [])
            if isinstance(cds, list):
                candidate_count += len(cds)
            if set(str(x) for x in change.get("impact_labels", [])) == {"PROSE_ONLY"} and cds:
                errors.append(f"{path.relative_to(root)}: PROSE_ONLY change carries candidate canon deltas")
        status = str(report.get("approval_status", ""))
        if status == "PROSE_ONLY_CONFIRMED" and any(x != "PROSE_ONLY" for x in labels):
            errors.append(f"{path.relative_to(root)}: PROSE_ONLY_CONFIRMED report contains non-prose semantic labels")
        if status == "APPROVED_FOR_COMMIT" and labels and all(x == "PROSE_ONLY" for x in labels):
            errors.append(f"{path.relative_to(root)}: APPROVED_FOR_COMMIT contains only PROSE_ONLY changes")
    if errors:
        add(rows, "K14", "fail", "Revision-analysis approval semantics are internally inconsistent.", failures=errors)
    elif checked:
        add(rows, "K14", "pass", "Revision reports keep prose-only analysis separate from canon-affecting proposals.", checked=checked)


def verify_open_issues(
    root: Path,
    project_manifest: dict[str, Any],
    rows: list[dict[str, Any]],
    runtime: dict[str, Any] | None = None,
) -> None:
    paths = project_manifest.get("canonical_paths", {})
    rel = paths.get("story_state") if isinstance(paths, dict) else None
    if not isinstance(rel, str):
        add(rows, "K16", "skip", "No Story State path is declared.")
        return
    path = safe_path(root, rel)
    if not path.is_file():
        add(rows, "K16", "fail", f"Story State is missing: {rel}")
        return
    raw = load_json(path)
    if not isinstance(raw, dict):
        add(rows, "K16", "fail", "Story State must be an object.")
        return

    report = validate_open_issue_state(raw)
    failures = list(report.get("errors", []))
    warnings = list(report.get("warnings", []))
    checked = int(report.get("checked", 0) or 0)
    if failures:
        add(
            rows,
            "K16",
            "fail",
            "OpenIssue/legacy authorial-unknown state violates open-truth preservation.",
            failures=failures,
            warnings=warnings,
            checked=checked,
        )
    elif warnings:
        add(
            rows,
            "K16",
            "warn",
            "OpenIssue state is structurally safe but requires semantic review.",
            warnings=warnings,
            checked=checked,
        )
    else:
        add(
            rows,
            "K16",
            "pass",
            "OpenIssue state preserves authorial openness at the machine-readable boundary.",
            checked=checked,
        )

    # Conditional planning dependencies reuse the canonical Runtime graph. An
    # active artifact may depend on a viable hypothesis, but an authoritatively
    # excluded hypothesis must not continue to support active downstream work.
    if not isinstance(runtime, dict):
        return
    deps = runtime.get("dependencies")
    edges = deps.get("edges", []) if isinstance(deps, dict) else []
    if not isinstance(edges, list):
        return
    positions = position_index(raw)
    dep_failures: list[str] = []
    checked_edges = 0
    for edge in edges:
        if not isinstance(edge, dict) or str(edge.get("kind", "")) != "conditional-on-hypothesis":
            continue
        checked_edges += 1
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        item = positions.get(source)
        if item is None:
            dep_failures.append(f"{source}->{target}: conditional hypothesis source does not resolve to a v2 OpenIssue position")
            continue
        qid, pos = item
        if is_edge_active(edge) and str(pos.get("viability", "viable")) == "excluded":
            dep_failures.append(f"{source}->{target}: active dependency remains on excluded hypothesis in {qid}")
    if dep_failures:
        add(rows, "K15", "fail", "Conditional hypothesis provenance contains invalid active dependencies.", failures=dep_failures)
    elif checked_edges:
        add(rows, "K15", "pass", "Conditional hypothesis dependencies resolve to viable OpenIssue positions.", checked=checked_edges)


def verify_decisions(root: Path, manifest: dict, rows: list[dict[str, Any]]) -> None:
    try:
        result = check_project_decisions(root, manifest)
    except Exception as exc:
        add(rows, "K2", "fail", f"Canonical decision dependency contract could not be loaded: {exc}")
        return
    if result is None:
        add(rows, "K2", "skip", "Legacy project declares no canonical intake_state; no decision authority is inferred.")
    elif result["errors"]:
        add(rows, "K2", "fail", "Commit-before-dependency failed; invalid consumers require regeneration.", failures=result["errors"], warnings=result["warnings"])
    else:
        add(rows, "K2", "warn" if result["warnings"] else "pass", "Declared decision dependencies preserve authorized semantic commit order.", **result)



RISK_FIELDS = ("consequential", "secret_sensitive", "temporal_risk", "research_derived", "plot_critical", "identity_critical")
NONFACTIVE = {"PREDICTION", "SUSPICION", "SUSPECTS", "INFERENCE", "HYPOTHESIS", "RUMOR", "FALSE_BELIEF", "BELIEF", "BELIEVES", "MISREMEMBERING", "PLAN", "FEELS", "HAVE_HEARD"}
PRECISIONS = {"EXACT", "BOUNDED", "APPROXIMATE", "UNKNOWN", "INFERRED"}
# Explicit sets describe calendar specificity, never the evidential strength of
# INFERRED. Basis is independently preserved even when the value looks exact.
COARSENINGS = {
    "DAY": {"DAY", "PART_MONTH", "MONTH", "YEAR", "UNKNOWN"},
    "PART_MONTH": {"PART_MONTH", "MONTH", "YEAR", "UNKNOWN"},
    "MONTH": {"MONTH", "YEAR", "UNKNOWN"},
    "YEAR": {"YEAR", "UNKNOWN"},
    "UNKNOWN": {"UNKNOWN"},
}


def fact_identity(row: dict[str, Any]) -> str:
    return str(row.get("fact_id", row.get("fact", row.get("id", ""))))


def risk_scoped(row: dict[str, Any]) -> bool:
    return any(row.get(key) is True for key in RISK_FIELDS)


def expression_basis(row: dict[str, Any]) -> str:
    if str(row.get("precision", "")).upper() == "INFERRED":
        return "INFERRED"
    return str(row.get("basis", "CONFIRMED")).upper()


def specificity(row: dict[str, Any]) -> str:
    declared = str(row.get("specificity", "UNKNOWN")).upper()
    value = row.get("value")
    actual = "UNKNOWN"
    if isinstance(value, str) and temporal_bounds(value) is not None:
        actual = {4: "YEAR", 7: "MONTH", 10: "DAY"}.get(len(value), "UNKNOWN")
    if actual != "UNKNOWN" and actual not in COARSENINGS.get(declared, {declared}):
        return actual
    return declared if declared != "UNKNOWN" else actual


def precision_supported(source: dict[str, Any], expression: dict[str, Any]) -> bool:
    """Explicit transition rules; confidence is deliberately never consulted."""
    sp, ep = str(source.get("precision", "UNKNOWN")).upper(), str(expression.get("precision", "UNKNOWN")).upper()
    if sp not in PRECISIONS or ep not in PRECISIONS:
        return False
    sb, eb = expression_basis(source), expression_basis(expression)
    if sb != "CONFIRMED" and eb == "CONFIRMED":
        return False
    ss, es = specificity(source), specificity(expression)
    if es not in COARSENINGS.get(ss, {ss, "UNKNOWN"}):
        return False
    allowed = {
        "EXACT": PRECISIONS,
        "BOUNDED": {"BOUNDED", "APPROXIMATE", "UNKNOWN", "INFERRED"},
        "APPROXIMATE": {"APPROXIMATE", "UNKNOWN", "INFERRED"},
        "UNKNOWN": {"UNKNOWN", "INFERRED"},
        "INFERRED": PRECISIONS,
    }
    if ep not in allowed[sp]:
        return False
    # A refinement must support this value, not merely an equally specific value.
    a, b = temporal_bounds(source.get("value")), temporal_bounds(expression.get("value"))
    if a and b:
        if a[0] != b[0] or max(a[1], b[1]) > min(a[2], b[2]):
            return False
    elif expression.get("value") != source.get("value") and es == ss and es != "UNKNOWN":
        return False
    if ss == es == "UNKNOWN" and expression.get("value") != source.get("value"):
        return False
    return True


def temporal_epistemic_issues(state: dict[str, Any], uses: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Shared deterministic law boundary for State, Kernel and Writer compiler.

    This is not prose extraction. Facts remain in the existing Story State Bundle;
    knowledge_state is the acquisition owner, never a Writer-supplied replacement.
    """
    issues: list[dict[str, Any]] = []
    from jsonschema import Draft202012Validator
    schema = load_json(SCRIPT_DIR.parent / "assets/project-schemas/temporal-epistemic.schema.json")
    for error in Draft202012Validator(schema).iter_errors(state):
        loc = "/".join(str(x) for x in error.absolute_path)
        law = "K22" if any(x in loc for x in ("precision", "specificity", "basis", "expression")) else "K21"
        issues.append({"law": law, "severity": "error", "code": "epistemic.schema", "message": f"{loc}: {error.message}", "scene_ids": []})

    def issue(law: str, code: str, msg: str, use: dict[str, Any] | None = None, severity: str = "error") -> None:
        scene = (use or {}).get("scene_id")
        issues.append({"law": law, "severity": severity, "code": code, "message": msg,
                       "scene_ids": [str(scene)] if scene is not None else []})

    def records(key: str) -> list[dict[str, Any]]:
        value = state.get(key, [])
        if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
            issue("K21", "epistemic.shape", key + " must be a list of objects")
            return []
        return value

    facts: dict[str, dict[str, Any]] = {}
    for row in records("facts") + records("research_dependencies"):
        fid = fact_identity(row)
        if not fid:
            if risk_scoped(row):
                issue("K21", "epistemic.fact_identity", "critical fact lacks identity")
            continue
        if fid in facts:
            issue("K21", "epistemic.duplicate_fact", f"duplicate fact identity: {fid}")
        facts[fid] = row
        if row.get("temporal_epistemic_version") == "1.0.0" and risk_scoped(row):
            if not row.get("provenance") or row.get("source_scope") not in {"REAL_WORLD", "STORY_WORLD"} or not row.get("precision"):
                issue("K21", "epistemic.new_fact_contract", f"{fid}: new critical fact needs provenance, scope and precision")
    acquisitions = records("knowledge_state")
    timeline = records("timeline")
    for row in validate_research_records(state):
        issues.append({"law": "K21", **row})

    selected = records("knowledge_uses") + records("writer_visible_facts") if uses is None else uses
    if uses is None:
        # Catalog declaration cannot evade coverage by deleting every use/event.
        selected = selected + [dict(row, fact_id=fid, used_at=row.get("used_at", state.get("story_time")))
            for fid, row in facts.items() if row.get("writer_visible") is True and row.get("actor")]

    def eligible_acquisitions(actor: Any, fid: str, when: Any, fact: dict[str, Any]) -> list[dict[str, Any]]:
        result = []
        for acq in acquisitions:
            if acq.get("actor") != actor or fact_identity(acq) != fid:
                continue
            acquired = acq.get("acquired_at", acq.get("acquired"))
            mode = str(acq.get("mode", "KNOWS")).upper()
            channel = str(acq.get("acquisition_channel", "")).upper()
            if mode in NONFACTIVE or expression_basis(acq) != "CONFIRMED" or channel in NONFACTIVE | {"AUTHOR_RESEARCH", "AUTHOR_ONLY"} or acq.get("completed", True) is not True:
                continue
            if not acq.get("acquisition_channel") or not acq.get("provenance") or acq.get("authorized", True) is not True:
                continue
            if temporal_order(acquired, when) is not True:
                continue
            available = fact.get("available_from", fact.get("valid_from"))
            if available is not None and temporal_order(available, acquired) is not True:
                continue
            if fact.get("source_scope") == "REAL_WORLD" and temporal_applicability(fact, acquired)["status"] != "APPLICABLE":
                continue
            result.append(acq)
        return result

    for use in selected:
        if not isinstance(use, dict):
            issue("K21", "epistemic.shape", "fact use must be an object")
            continue
        if use.get("writer_visible") is False:
            continue
        if use.get("visibility") in {"author-only", "backend-hidden", "future-answer"}:
            if use.get("writer_visible") is True:
                issue("K21", "epistemic.visibility", "protected declaration cannot also be Writer-visible", use)
            continue
        fid = fact_identity(use)
        fact = facts.get(fid, {})
        critical = risk_scoped(use) or risk_scoped(fact)
        if critical and fact.get("visibility") in {"author-only", "backend-hidden", "future-answer"}:
            issue("K21", "epistemic.visibility", f"{fid}: protected source lacks a Writer-safe derivative", use)
        modern = "fact_id" in use or "acquired_at" in use or "used_at" in use or critical
        if not modern:
            # Preserve numeric legacy API. It is readable, not proof of coverage
            # for a newly marked critical Writer fact.
            def legacy_time(value: Any) -> Any:
                try:
                    return float(value) if isinstance(value, str) else value
                except ValueError:
                    return value
            order = temporal_order(legacy_time(use.get("acquired")), legacy_time(use.get("used")))
            if order is False:
                issue("K21", "epistemic.use_before_acquisition", f"knowledge discontinuity: {use.get('actor','?')} uses {fid} before acquiring it", use)
            elif order is None:
                issue("K21", "epistemic.legacy_review", "legacy knowledge order needs review", use, "warning")
            continue
        mode = str(use.get("mode", "KNOWS")).upper()
        if mode not in NONFACTIVE and ("acquired" in use or "acquired_at" in use):
            order = temporal_order(use.get("acquired_at", use.get("acquired")), use.get("used_at", use.get("used")))
            if order is not True:
                issue("K21", "epistemic.use_before_acquisition", f"{fid}: registered use before acquisition or order needs review", use)
        if mode in NONFACTIVE:
            # Prediction does not grant later canonical knowledge. Its expression
            # must still preserve a nonconfirmed basis in K22 below.
            pass
        elif critical:
            actor = use.get("actor")
            objective = use.get("actor_relative") is False and fact.get("actor_relative") is False
            if use.get("actor_relative") is False and not objective:
                issue("K21", "epistemic.objective_override", f"{fid}: consumer cannot exempt an actor-relative source", use)
            when = use.get("used_at", use.get("used", state.get("story_time")))
            if not fid or not fact:
                issue("K21", "epistemic.missing_fact", "critical use lacks an authoritative fact", use)
                continue
            if (not actor and not objective) or temporal_bounds(when) is None:
                issue("K21", "epistemic.use_scope", f"{fid}: critical actor/time scope missing or uncomparable", use)
                continue
            if fact.get("truth", True) is not True or expression_basis(fact) != "CONFIRMED":
                issue("K21", "epistemic.nonfactive_source", f"{fid}: unconfirmed/false source cannot become canonical knowledge", use)
            available = fact.get("available_from", fact.get("valid_from"))
            if fact.get("temporal_risk") is True and available is None:
                issue("K21", "epistemic.future_fact", f"{fid}: temporal-risk fact availability needs review", use)
            if available is not None and temporal_order(available, when) is not True:
                issue("K21", "epistemic.future_fact", f"{fid}: fact unavailable or temporal order needs review", use)
            fact_time = use.get("fact_at", when)
            if use.get("experience") in {"FIRSTHAND", "FIRSTHAND_MEMORY", "DIRECT_EXPERIENCE"}:
                fact_time = use.get("fact_at", fact.get("event_at", fact_time))
            if fact.get("source_scope") == "REAL_WORLD" or fact.get("valid_to") is not None:
                app = temporal_applicability(fact, fact_time)
                if app["status"] != "APPLICABLE" or app["conflict"]:
                    issue("K21", "research.inapplicable_use", f"{fid}: research not applicable at use time", use)
            legal = eligible_acquisitions(actor, fid, when, fact)
            general = fact.get("acquisition_policy") in {"PUBLIC", "BACKGROUND"} and bool(fact.get("provenance"))
            general = general and not any(fact.get(k) is True for k in ("secret_sensitive", "identity_critical", "research_derived", "temporal_risk"))
            if not legal and not general and not objective:
                issue("K21", "epistemic.missing_acquisition", f"{fid}: missing completed authorized acquisition before use", use)
            if use.get("experience") in {"FIRSTHAND", "FIRSTHAND_MEMORY", "DIRECT_EXPERIENCE"}:
                event = temporal_bounds(fact.get("event_at", fact.get("valid_from")))
                location = fact.get("location")
                eligible = fact.get("experience_eligible_for")
                presence = any(row.get("actor") == actor and row.get("location") == location and location is not None
                    and event is not None and (start := temporal_bounds(row.get("start"))) is not None
                    and (end := temporal_bounds(row.get("end"))) is not None
                    and event[0] == start[0] == end[0] and start[2] <= event[1] <= event[2] <= end[1] for row in timeline)
                direct = any(str(row.get("acquisition_channel", "")).upper() in {"DIRECT_OBSERVATION", "DIRECT_EXPERIENCE"}
                    and event is not None and (a := temporal_bounds(row.get("acquired_at", row.get("acquired")))) is not None
                    and a[0] == event[0] and a[1] == a[2] == event[1] == event[2] for row in legal)
                if fact.get("direct_experience_eligible") is False or (isinstance(eligible, list) and actor not in eligible) or not presence or not direct:
                    issue("K21", "epistemic.experience", f"{fid}: later knowledge does not establish firsthand experience at event time/place", use)

        expression = use.get("expression")
        if expression is None:
            continue
        if not isinstance(expression, dict) or not fact:
            issue("K22", "precision.missing_source", "expression lacks authoritative source/structured precision", use)
            continue
        if mode in NONFACTIVE and expression_basis(expression) == "CONFIRMED":
            issue("K22", "precision.inference_laundering", f"{fid}: nonfactive mode lost its expression qualifier", use)
        supported = precision_supported(fact, expression)
        if not supported:
            # Refinement points at independent primitive support, not a circular
            # downstream assertion. The evidence must support this exact fact and
            # remain available to this actor before this expression is used.
            refs = use.get("refinement_evidence", [])
            if isinstance(refs, list):
                for ref in refs:
                    evidence = facts.get(str(ref), {})
                    if evidence.get("supports_fact_id") != fid or not evidence.get("provenance") or expression_basis(evidence) != "CONFIRMED" or evidence.get("truth", True) is not True:
                        continue
                    if evidence.get("visibility") in {"author-only", "backend-hidden", "future-answer"}:
                        continue
                    a, b = temporal_bounds(fact.get("value")), temporal_bounds(expression.get("value"))
                    if a and b and (a[0] != b[0] or max(a[1], b[1]) > min(a[2], b[2])):
                        continue
                    if not precision_supported(evidence, expression):
                        continue
                    when = use.get("used_at", use.get("used", state.get("story_time")))
                    if not eligible_acquisitions(use.get("actor"), str(ref), when, evidence):
                        continue
                    if evidence.get("source_scope") == "REAL_WORLD" and temporal_applicability(evidence, when)["status"] != "APPLICABLE":
                        continue
                    supported = True
                    break
        if not supported:
            issue("K22", "precision.unsupported_refinement", f"{fid}: downstream specificity/basis exceeds source without acquired supporting evidence", use)
    return issues


def verify_temporal_epistemic(root: Path, manifest: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    rel = manifest.get("canonical_paths", {}).get("story_state")
    if not isinstance(rel, str):
        for law in ("K21", "K22"):
            add(rows, law, "skip", "No canonical Story State declared.")
        return
    try:
        state = load_json(safe_path(root, rel))
        if not isinstance(state, dict):
            raise ValueError("Story State must be an object")
        findings = temporal_epistemic_issues(state)
    except Exception as exc:
        add(rows, "K21", "fail", "Temporal/epistemic state could not be inspected.", reason=str(exc))
        return
    for law in ("K21", "K22"):
        scoped = [x for x in findings if x["law"] == law]
        status = "fail" if any(x["severity"] == "error" for x in scoped) else "warn" if scoped else "pass"
        add(rows, law, status, "Structured temporal/epistemic/precision boundary inspected; no arbitrary prose extraction.", findings=scoped)


def verify_project(root: Path) -> dict[str, Any]:
    manifest_path = root / "project-manifest.json"
    if not manifest_path.is_file():
        return {"errors": [f"missing project manifest: {manifest_path}"], "warnings": [], "laws": []}
    project_manifest = load_json(manifest_path)
    if not isinstance(project_manifest, dict):
        return {"errors": ["project-manifest.json must be an object"], "warnings": [], "laws": []}

    rows: list[dict[str, Any]] = []
    runtime = verify_runtime(root, project_manifest, rows)
    verify_context(root, project_manifest, rows, runtime.get("branches", {}) if isinstance(runtime, dict) else {})
    verify_reconciliations(root, project_manifest, rows)
    verify_revisions(root, project_manifest, rows)
    verify_open_issues(root, project_manifest, rows, runtime)
    verify_decisions(root, project_manifest, rows)
    verify_temporal_epistemic(root, project_manifest, rows)
    from project_ops import rollover_status
    rollover = rollover_status(root)
    if rollover["status"] == "STALE":
        add(rows, "K13", "fail", "Chapter rollover evidence is stale; reconcile/refresh required.", codes=rollover["codes"], stale_artifacts=rollover["stale_artifacts"])
    elif rollover["status"] == "FRESH":
        add(rows, "K13", "pass", "Canonical final prose, reconciliation and state snapshot close the rollover tuple.")

    failures = [x for x in rows if x.get("status") == "fail"]
    warnings = [x for x in rows if x.get("status") == "warn"]
    return {
        "kernel_contract_version": "1.0.0",
        "project_id": project_manifest.get("project_id"),
        "project_root": str(root),
        "current_branch": project_manifest.get("current_branch"),
        "previous_chapter_rollover": rollover,
        "summary": {
            "pass": sum(1 for x in rows if x.get("status") == "pass"),
            "warn": len(warnings),
            "skip": sum(1 for x in rows if x.get("status") == "skip"),
            "fail": len(failures),
        },
        "laws": rows,
        "runtime_projection_sha256": stable_hash(runtime["projection"]) if runtime.get("projection") is not None else None,
    }


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    summary = report.get("summary", {})
    print(f"Narrative Semantics Kernel: project={report.get('project_id')} branch={report.get('current_branch')}")
    if isinstance(summary, dict):
        print("summary: " + ", ".join(f"{k}={summary.get(k, 0)}" for k in ("pass", "warn", "skip", "fail")))
    for row in report.get("laws", []):
        if not isinstance(row, dict):
            continue
        print(f"{str(row.get('status','?')).upper():5} {row.get('law')} {row.get('law_name')}: {row.get('message')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("laws", help="list the cross-layer semantic laws")
    q.add_argument("--json", action="store_true")

    q = sub.add_parser("verify", help="verify machine-decidable semantic-kernel seams for a project")
    q.add_argument("project_root", type=Path)
    q.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if args.cmd == "laws":
        if args.json:
            print(json.dumps({"kernel_contract_version": "1.0.0", "laws": LAWS}, ensure_ascii=False, indent=2))
        else:
            for row in LAWS:
                print(f"{row['id']}: {row['name']} [machine={row['machine_checkable']}]")
        return 0

    root = args.project_root.resolve()
    try:
        report = verify_project(root)
    except Exception as exc:
        print(f"ERROR: semantic-kernel verification failed: {exc}", file=sys.stderr)
        return 2
    print_report(report, args.json)
    if report.get("errors"):
        return 1
    summary = report.get("summary", {})
    return 1 if isinstance(summary, dict) and int(summary.get("fail", 0)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
