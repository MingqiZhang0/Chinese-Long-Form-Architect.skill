#!/usr/bin/env python3
"""Validate a role-isolated task order for multi-agent fiction workflows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from orchestration_contract import EXECUTION_PROFILES, ROLE_NAMES
from scoped_poetics import verify_envelope
ROLES = ROLE_NAMES
STATUSES = {"PENDING", "RUNNING", "BLOCKED", "DONE", "REJECTED"}
LIST_FIELDS = {
    "authoritative_inputs",
    "allowed_reads",
    "allowed_writes",
    "forbidden_mutations",
    "required_outputs",
    "acceptance_criteria",
    "blockers",
    "findings_for_next_role",
}
OPTIONAL_LIST_FIELDS = {"objections", "overrides"}
REQUIRED = {"task_id", "stage", "role", "status", "goal"} | LIST_FIELDS


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("task order must be a JSON object")
    return data


def validate(
    data: dict[str, Any],
    *,
    root: Path | None = None,
    project_manifest_ref: str | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = sorted(REQUIRED - set(data))
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    role = data.get("role")
    if role not in ROLES:
        errors.append(f"unknown role: {role!r}")
    status = data.get("status")
    if status not in STATUSES:
        errors.append(f"unknown status: {status!r}")
    for field in LIST_FIELDS | OPTIONAL_LIST_FIELDS:
        value = data.get(field)
        if field in data and not isinstance(value, list):
            errors.append(f"{field} must be a list")
    if not str(data.get("task_id", "")).strip():
        errors.append("task_id must be non-empty")
    if not str(data.get("stage", "")).strip():
        errors.append("stage must be non-empty")
    if not str(data.get("goal", "")).strip():
        errors.append("goal must be non-empty")

    execution_profile = data.get("execution_profile")
    if execution_profile is not None and execution_profile not in EXECUTION_PROFILES:
        errors.append(f"unknown execution_profile: {execution_profile!r}")
    isolation = data.get("isolation_requirements")
    if isolation is not None:
        if not isinstance(isolation, dict):
            errors.append("isolation_requirements must be an object")
        else:
            for key in ("fresh_context", "blindness_required", "independent_review_required"):
                if key in isolation and not isinstance(isolation.get(key), bool):
                    errors.append(f"isolation_requirements.{key} must be boolean")

    if status == "DONE" and data.get("blockers"):
        errors.append("DONE task cannot retain blockers")
    blocking = [x for x in data.get("objections", []) if isinstance(x, dict) and str(x.get("severity", "")).lower() == "blocking" and str(x.get("status", "open")).lower() not in {"resolved", "overridden"}]
    if status == "DONE" and blocking:
        errors.append("DONE task cannot retain unresolved blocking objections")
    overridden = [x for x in data.get("objections", []) if isinstance(x, dict) and str(x.get("status", "")).lower() == "overridden"]
    if overridden and not data.get("overrides"):
        errors.append("overridden objection requires an override record with rationale")
    if status == "BLOCKED" and not data.get("blockers"):
        warnings.append("BLOCKED task has no recorded blocker")

    allowed_writes = [str(x) for x in data.get("allowed_writes", []) if x is not None]
    forbidden = [str(x) for x in data.get("forbidden_mutations", []) if x is not None]
    for path in allowed_writes:
        for ban in forbidden:
            prefix = ban.rstrip("/") + "/"
            if path == ban.rstrip("/") or path.startswith(prefix):
                errors.append(f"write path {path!r} conflicts with forbidden mutation {ban!r}")

    if role == "writer":
        poetics_ref = data.get("scoped_project_poetics_ref")
        envelope_ref = data.get("scoped_project_poetics_envelope_ref")
        if poetics_ref is not None and (not isinstance(poetics_ref, str) or not poetics_ref.strip()):
            errors.append("scoped_project_poetics_ref must be a non-empty string when provided")
        if envelope_ref is not None and (not isinstance(envelope_ref, str) or not envelope_ref.strip()):
            errors.append("scoped_project_poetics_envelope_ref must be a non-empty string when provided")
        if (poetics_ref is None) != (envelope_ref is None):
            errors.append("scoped_project_poetics_ref and scoped_project_poetics_envelope_ref must be provided together")
        if poetics_ref is None:
            warnings.append("writer task has no scoped_project_poetics_ref; valid for legacy/micro tasks, but substantial fiction work should use a provenance-verified scoped poetics derivative")
        elif root is None:
            errors.append("writer task with scoped Project Poetics requires --root so provenance can be verified")
        elif isinstance(poetics_ref, str) and isinstance(envelope_ref, str):
            _, poetics_errors = verify_envelope(
                root=root,
                content_ref=poetics_ref,
                envelope_ref=envelope_ref,
                project_manifest_ref=project_manifest_ref or "project-manifest.json",
                scope_context={
                    "arc": data.get("target_arc"),
                    "chapter": data.get("target_chapter"),
                    "scene": data.get("target_scene"),
                    "task": data.get("task_id"),
                },
            )
            errors.extend("scoped Project Poetics: " + msg for msg in poetics_errors)
        risky = [p for p in allowed_writes if p.startswith(("state/", "research/", "planning/"))]
        if risky:
            warnings.append("writer is allowed to mutate non-prose project state: " + ", ".join(risky))
    if role == "humanities-analyst":
        risky = [p for p in allowed_writes if p.startswith(("chapters/", "planning/", "state/"))]
        if risky:
            errors.append("humanities-analyst may not write prose/plans/state: " + ", ".join(risky))
    if role == "reader-simulator":
        risky = [p for p in allowed_writes if not p.startswith(("analysis/reader-sim/", "analysis/reader-sim"))]
        if risky:
            errors.append("reader-simulator may write only reader-simulation diagnostics: " + ", ".join(risky))
    if role == "revision-analyst":
        risky = [p for p in allowed_writes if p.startswith(("chapters/", "state/", "runtime/events", "runtime/branches"))]
        if risky:
            errors.append("revision-analyst may not mutate prose/canon/runtime: " + ", ".join(risky))
    if role == "committer" and not allowed_writes:
        warnings.append("committer has no allowed write targets")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a multi-agent task-order JSON file")
    parser.add_argument("task_order", type=Path)
    parser.add_argument("--root", type=Path, help="project root; required when scoped Project Poetics is attached")
    parser.add_argument("--project-manifest", default="project-manifest.json", help="project-relative manifest path used to verify Project Poetics authority")
    args = parser.parse_args()
    try:
        data = load(args.task_order)
        errors, warnings = validate(
            data,
            root=args.root.resolve() if args.root else None,
            project_manifest_ref=args.project_manifest if args.root else None,
        )
    except Exception as exc:
        print(f"ERROR: could not validate task order: {exc}", file=sys.stderr)
        return 2
    for msg in warnings:
        print(f"WARNING: {msg}")
    for msg in errors:
        print(f"ERROR: {msg}")
    print(f"summary: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
