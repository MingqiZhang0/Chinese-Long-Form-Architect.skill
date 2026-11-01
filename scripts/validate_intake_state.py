#!/usr/bin/env python3
"""Validate normalized Front-Loaded Adaptive Intake state.

This validator checks interaction and dependency contracts. It does not decide
creative quality, infer delegation from natural-language wording, choose story content,
or require a theme/ending. It also gates declared consequential decision dependencies;
intent normalization and Project-Poetics compilation happen upstream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from dependency_activity import is_edge_active

ALLOWED_STATUSES = {
    "user_locked",
    "delegated",
    "absent",
    "user_reserved",
    "agent_discretion",
    "unresolved",
    "conflict",
}
ALLOWED_SOURCES = {
    "initial_prompt",
    "prior_context",
    "existing_brief",
    "intake_response",
    "explicit_user_update",
    "agent_scope",
}

POETICS_SIGNAL_IDS = {
    "category",
    "core_premise",
    "story_problem",
    "theme",
    "theme_question",
    "intended_reading_experience",
    "reader_activity",
    "narrative_access",
    "voice_direction",
    "structure_time",
    "formal_experimentation",
    "explicit_exclusions",
}

DECISION_CLASSES = {
    "research", "world_model", "chronology", "case_mechanics",
    "long_horizon", "writer_context", "consequential",
}
DECISION_AUTHORITIES = {"user_locked", "delegated", "agent_discretion", "absent"}
USER_SOURCES = ALLOWED_SOURCES - {"agent_scope"}


def present(value: object) -> bool:
    """False and zero are legitimate decisions; blank/empty values are not."""
    return value is not None and value != "" and value != [] and value != {} and not (isinstance(value, str) and not value.strip())


def commit_fingerprint(slot: dict) -> str:
    """Reuse the project's canonical sorted-JSON SHA-256 convention.

    Interaction labels/asked flags do not identify a semantic decision. Authority,
    resolution, value, resolver, provenance and acceptance time do.
    """
    payload = {key: slot.get(key) for key in (
        "id", "status", "source", "resolution", "resolved_value", "resolved_by", "provenance",
    )}
    commit = slot.get("semantic_commit")
    payload["committed_at"] = commit.get("committed_at") if isinstance(commit, dict) else None
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def commit_time(value: object) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("requires an ISO-8601 timestamp with timezone")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("requires an ISO-8601 timestamp with timezone")
    return parsed.astimezone(timezone.utc)


def decision_errors(slot: dict) -> list[str]:
    errors = []
    authority = slot.get("status")
    if authority not in DECISION_AUTHORITIES:
        errors.append("no authorized decision authority")
    if slot.get("resolution") != "resolved":
        errors.append("decision remains unresolved")
    if not present(slot.get("resolved_value")):
        errors.append("resolved_value is missing")
    resolver = "user" if authority in {"user_locked", "absent"} else "agent"
    if slot.get("resolved_by") != resolver:
        errors.append(f"resolved_by must be {resolver} under this authority")
    provenance = slot.get("provenance")
    if not isinstance(provenance, dict) or not all(
        isinstance(provenance.get(key), str) and provenance[key].strip()
        for key in ("authority_ref", "resolution_ref")
    ):
        errors.append("provenance needs authority_ref and resolution_ref")
    if authority in {"user_locked", "delegated", "absent"} and slot.get("source") not in USER_SOURCES:
        errors.append("user authority requires user-intent provenance, not agent_scope")
    commit = slot.get("semantic_commit")
    if not isinstance(commit, dict):
        errors.append("semantic commit is missing")
    else:
        try:
            commit_time(commit.get("committed_at"))
        except (ValueError, TypeError):
            errors.append("semantic_commit.committed_at requires a timezone timestamp")
        if commit.get("content_sha256") != commit_fingerprint(slot):
            errors.append("semantic_commit.content_sha256 is missing or mismatched")
    return errors


def validate_decision_dependencies(data: dict, dependencies: dict | None = None,
                                   consumers: set[str] | None = None) -> tuple[list[str], list[str]]:
    """Check active decision edges in the requested dependency cone.

    Runtime callers pass their existing graph. Non-runtime ledgers store the same
    source->target edges in dependencies; neither path creates a decision registry.
    """
    errors, warnings = [], []
    graph = dependencies if dependencies is not None else data.get("dependencies", {"edges": []})
    if not isinstance(graph, dict) or not isinstance(graph.get("edges"), list):
        return ["decision dependencies must be an object with an edges list"], []
    edges = graph["edges"]
    malformed = [idx for idx, edge in enumerate(edges) if not isinstance(edge, dict) or
                 not all(isinstance(edge.get(key), str) and edge[key].strip() for key in ("source", "target"))]
    if malformed:
        return [f"dependencies.edges[{idx}] needs nonempty string source/target" for idx in malformed], []
    slots = data.get("slots", [])
    by_id = {s.get("id"): s for s in slots if isinstance(s, dict) and isinstance(s.get("id"), str)} if isinstance(slots, list) else {}
    cone = None if consumers is None else set(consumers)
    if cone is not None:
        # Only traverse registered active dependencies, preserving source->target.
        changed = True
        while changed:
            changed = False
            for edge in edges:
                if isinstance(edge, dict) and is_edge_active(edge) and edge.get("target") in cone:
                    source = edge.get("source")
                    if isinstance(source, str) and source not in cone:
                        cone.add(source)
                        changed = True
    for idx, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"dependencies.edges[{idx}] must be an object")
            continue
        # Existing general runtime edges are unchanged. A slot source or explicit
        # decision marker opts into P0-1; deleting kind alone cannot bypass it.
        if not (edge.get("kind") == "decision-dependency" or edge.get("source") in by_id
                or "dependency_class" in edge or "source_commit_sha256" in edge):
            continue
        if edge.get("status", "active") not in {"active", "retired", "invalidated", "superseded"}:
            errors.append(f"dependencies.edges[{idx}].status is invalid")
            continue
        if not is_edge_active(edge) or (cone is not None and edge.get("target") not in cone):
            continue
        prefix = f"dependency {edge.get('source')}->{edge.get('target')}"
        if not isinstance(edge.get("target"), str) or not edge["target"].strip():
            errors.append(f"{prefix}: consumer target is missing")
        if edge.get("dependency_class") not in DECISION_CLASSES:
            errors.append(f"{prefix}: declare a consequential dependency_class")
        slot = by_id.get(edge.get("source"))
        if slot is None:
            errors.append(f"{prefix}: source decision does not exist in canonical slots")
            continue
        failures = decision_errors(slot)
        errors.extend(f"{prefix}: {msg}" for msg in failures)
        commit = slot.get("semantic_commit")
        captured = edge.get("source_commit_sha256")
        if not isinstance(commit, dict) or not isinstance(captured, str) or captured != commit.get("content_sha256"):
            errors.append(f"{prefix}: INVALID_REQUIRES_REGENERATION (missing/stale activation fingerprint)")
        try:
            activated = commit_time(edge.get("activated_at"))
            committed = commit_time(commit.get("committed_at") if isinstance(commit, dict) else None)
            if committed >= activated:
                errors.append(f"{prefix}: INVALID_REQUIRES_REGENERATION (commit must precede activation)")
        except (TypeError, ValueError):
            errors.append(f"{prefix}: INVALID_REQUIRES_REGENERATION (activation/commit order is unproven)")
    return errors, warnings


def check_project_decisions(root: Path, manifest: dict, consumers: set[str] | None = None) -> dict | None:
    """Read only the existing canonical intake register and optional Runtime graph."""
    paths = manifest.get("canonical_paths", {})
    ref = paths.get("intake_state") if isinstance(paths, dict) else None
    if ref is None:
        return None  # Legacy projects remain readable; never invent authority.

    def read(ref: str) -> tuple[dict, str]:
        if not isinstance(ref, str) or not ref.strip():
            raise ValueError("canonical decision path must be a nonempty string")
        path = (root / ref).resolve()
        path.relative_to(root.resolve())
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("canonical decision artifact must be an object")
        return value, hashlib.sha256(path.read_bytes()).hexdigest()

    data, state_hash = read(ref)
    graph = None
    graph_hash = None
    runtime_ref = paths.get("runtime_manifest")
    if "narrative-runtime" in manifest.get("enabled_subsystems", []):
        runtime, _ = read(runtime_ref)
        dep_ref = runtime.get("paths", {}).get("dependencies")
        # Runtime manifest paths are project-relative, like the Runtime backend.
        graph, graph_hash = read(dep_ref)
        local = data.get("dependencies")
        if local is not None and (not isinstance(local, dict) or local.get("edges")):
            raise ValueError("Runtime decision edges must use the canonical Runtime graph only")
    errors, warnings = validate(data, graph, consumers)
    return {"errors": errors, "warnings": warnings, "intake_state_sha256": state_hash,
            "dependencies_sha256": graph_hash}


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON: {exc}") from exc


def validate(data: dict, dependencies: dict | None = None,
             consumers: set[str] | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if data.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")

    intake_status = data.get("intake_status")
    if intake_status not in {"draft", "complete"}:
        errors.append("intake_status must be 'draft' or 'complete'")

    slots = data.get("slots")
    if not isinstance(slots, list):
        errors.append("slots must be a list")
        slots = []

    seen_ids: set[str] = set()
    for idx, slot in enumerate(slots):
        prefix = f"slots[{idx}]"
        if not isinstance(slot, dict):
            errors.append(f"{prefix} must be an object")
            continue

        sid = slot.get("id")
        if not isinstance(sid, str) or not sid.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif sid in seen_ids:
            errors.append(f"duplicate slot id: {sid}")
        else:
            seen_ids.add(sid)

        status = slot.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{prefix}.status invalid: {status!r}")
            continue

        source = slot.get("source")
        if source not in ALLOWED_SOURCES:
            errors.append(f"{prefix}.source invalid: {source!r}")

        asked = slot.get("asked")
        known_before = slot.get("known_before_intake")
        required = bool(slot.get("required", False))
        value = slot.get("value")

        if not isinstance(asked, bool):
            errors.append(f"{prefix}.asked must be boolean")
        if not isinstance(known_before, bool):
            errors.append(f"{prefix}.known_before_intake must be boolean")

        if asked is True and known_before is True:
            errors.append(f"{prefix} re-asks a slot already known before intake")

        if status == "absent" and required:
            errors.append(f"{prefix} is required and cannot be absent")

        if status == "agent_discretion" and asked is True:
            errors.append(f"{prefix} was asked despite being classified as agent_discretion")

        if status == "user_reserved":
            gate = slot.get("gate")
            if not isinstance(gate, str) or not gate.strip():
                errors.append(f"{prefix} user_reserved slot requires a non-empty gate")

        if consumers is None and intake_status == "complete" and status in {"unresolved", "conflict"} and slot.get("consequential") is not False:
            errors.append(f"{prefix} remains {status} while intake_status is complete")

        if status in {"user_locked", "delegated", "absent", "user_reserved"} and not present(value):
            errors.append(f"{prefix} status {status} requires a value")

        if "resolution" in slot and slot["resolution"] not in {"resolved", "unresolved"}:
            errors.append(f"{prefix}.resolution must be resolved or unresolved")
        if "semantic_commit" in slot and consumers is None:
            errors.extend(f"{prefix}: {msg}" for msg in decision_errors(slot))
        elif status == "user_locked" and present(value) and "resolution" not in slot:
            warnings.append(f"{prefix}: legacy USER_LOCKED value is resolved intent, not a committed dependency; migrate before new consequential use")

    policy = data.get("interruption_policy")
    if not isinstance(policy, dict):
        errors.append("interruption_policy must be an object")
    else:
        if policy.get("nonessential_budget") != 0:
            errors.append("post-kickoff nonessential interruption budget must be 0")
        gates = policy.get("user_reserved_gates", [])
        if not isinstance(gates, list):
            errors.append("interruption_policy.user_reserved_gates must be a list")

    if not slots:
        warnings.append("intake state has no slots; valid only if the request truly needs none")

    if intake_status == "complete" and slots:
        signals = []
        for slot in slots:
            if not isinstance(slot, dict):
                continue
            sid = str(slot.get("id", "")).strip()
            status = str(slot.get("status", "")).strip()
            value = slot.get("value")
            if sid in POETICS_SIGNAL_IDS and status in {"user_locked", "delegated", "agent_discretion", "absent"}:
                if status in {"delegated", "agent_discretion"} or present(value):
                    signals.append(sid)
        if not signals:
            warnings.append(
                "complete intake exposes no explicit Project-Poetics signal; valid only if prior context or the Project Brief supplies enough basis for a provisional poetics"
            )

    dep_errors, dep_warnings = validate_decision_dependencies(data, dependencies, consumers)
    return errors + dep_errors, warnings + dep_warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate normalized front-loaded adaptive intake state"
    )
    parser.add_argument("path", type=Path, help="Path to intake-state JSON")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable result")
    parser.add_argument("--dependencies", type=Path, help="Existing Runtime dependency graph (otherwise use ledger dependencies)")
    parser.add_argument("--consumer", action="append", help="Validate only this consumer's active dependency cone; repeatable")
    args = parser.parse_args()

    data = load_json(args.path)
    if not isinstance(data, dict):
        raise SystemExit("intake state must be an object")
    errors, warnings = validate(data, load_json(args.dependencies) if args.dependencies else None,
                                set(args.consumer) if args.consumer is not None else None)
    result = {"errors": errors, "warnings": warnings, "ok": not errors}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for msg in warnings:
            print(f"WARNING: {msg}")
        for msg in errors:
            print(f"ERROR: {msg}")
        print(f"summary: {len(errors)} error(s), {len(warnings)} warning(s)")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
