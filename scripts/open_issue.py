#!/usr/bin/env python3
"""Shared deterministic helpers for OpenIssue governance.

This module validates only machine-decidable representation/provenance seams. It
never decides literary meaning, chooses an authorial answer, or enumerates
possible worlds.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

OPEN_STATES = {"open", "resolved", "retired"}
RESOLUTION_POLICIES = {"must_resolve", "may_resolve", "preserve_open"}
DOMAIN_SEMANTICS = {"open_ended", "constraint_defined", "declared_exhaustive"}
POSITION_VIABILITY = {"viable", "excluded"}
PLANNING_STANCES = {"candidate", "working_hypothesis", "parked"}
AUTHORITATIVE_BASIS_KINDS = {"authorial_decision", "committed_canon", "world_rule", "legacy_constraint"}


def issue_records(state: dict[str, Any]) -> list[Any]:
    raw = state.get("authorial_unknowns", [])
    return raw if isinstance(raw, list) else []


def is_v2(rec: dict[str, Any]) -> bool:
    return str(rec.get("record_version", "")).startswith("2.") or str(rec.get("mode", "")) == "OPEN_ISSUE"


def issue_id(rec: dict[str, Any], index: int | None = None) -> str:
    raw = rec.get("question_id", rec.get("id"))
    if raw not in (None, ""):
        return str(raw)
    return f"authorial_unknowns[{index}]" if index is not None else "?"


def state_of(rec: dict[str, Any]) -> str:
    if is_v2(rec):
        return str(rec.get("state", "open")).lower()
    return str(rec.get("status", "open")).lower()


def active_issue(rec: dict[str, Any]) -> bool:
    return state_of(rec) not in {"resolved", "retired"}


def viable_positions(rec: dict[str, Any]) -> list[dict[str, Any]]:
    if not is_v2(rec):
        return []
    rows = rec.get("positions", [])
    if not isinstance(rows, list):
        return []
    return [x for x in rows if isinstance(x, dict) and str(x.get("viability", "viable")) == "viable"]


def working_positions(rec: dict[str, Any]) -> list[dict[str, Any]]:
    return [x for x in viable_positions(rec) if str(x.get("planning_stance", "candidate")) == "working_hypothesis"]


def position_index(state: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    out: dict[str, tuple[str, dict[str, Any]]] = {}
    for i, rec in enumerate(issue_records(state)):
        if not isinstance(rec, dict) or not is_v2(rec):
            continue
        qid = issue_id(rec, i)
        rows = rec.get("positions", [])
        if not isinstance(rows, list):
            continue
        for pos in rows:
            if isinstance(pos, dict) and pos.get("position_id") not in (None, ""):
                out[str(pos["position_id"])] = (qid, pos)
    return out


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_record(rec: dict[str, Any], index: int) -> tuple[list[str], list[str]]:
    """Return (errors, review_required_warnings) for one issue record."""
    errors: list[str] = []
    warnings: list[str] = []
    ident = issue_id(rec, index)

    if not is_v2(rec):
        status = str(rec.get("status", "open")).lower()
        if status in {"open", "active", "unresolved"}:
            for key in ("selected_answer", "resolved_answer"):
                value = rec.get(key)
                if value not in (None, "", [], {}):
                    errors.append(f"{ident}: legacy open record already populates {key}")
        if str(rec.get("mode", "")) == "DELIBERATELY_UNRESOLVED":
            warnings.append(
                f"{ident}: legacy DELIBERATELY_UNRESOLVED requires semantic classification before v2 upgrade; preserve non-collapse meanwhile"
            )
        return errors, warnings

    required_strings = ("question_id", "question", "resolution_criterion")
    for key in required_strings:
        if not _nonempty(rec.get(key)):
            errors.append(f"{ident}: {key} must be a non-empty string")

    if str(rec.get("record_version")) != "2.0.0":
        errors.append(f"{ident}: unsupported OpenIssue record_version {rec.get('record_version')!r}")
    if str(rec.get("mode")) != "OPEN_ISSUE":
        errors.append(f"{ident}: v2 record mode must be OPEN_ISSUE")

    # `planning_owner_ref` is legacy non-authoritative routing metadata. It must never
    # be interpreted as S0 ownership or decision authority; see open-issue-semantics.md.
    planning_owner_ref = rec.get("planning_owner_ref")
    if planning_owner_ref is not None and not _nonempty(planning_owner_ref):
        errors.append(f"{ident}: planning_owner_ref must be null or a non-empty project-relative routing reference")
    elif str(planning_owner_ref or "").strip() == "planning/project-poetics.md":
        warnings.append(
            f"{ident}: planning_owner_ref uses the former blanket Project-Poetics default; "
            "treat it as non-authoritative legacy routing metadata and review whether it should be null"
        )

    state = str(rec.get("state", ""))
    policy = str(rec.get("resolution_policy", ""))
    domain = str(rec.get("domain_semantics", ""))
    if state not in OPEN_STATES:
        errors.append(f"{ident}: invalid state {state!r}")
    if policy not in RESOLUTION_POLICIES:
        errors.append(f"{ident}: invalid resolution_policy {policy!r}")
    if domain not in DOMAIN_SEMANTICS:
        errors.append(f"{ident}: invalid domain_semantics {domain!r}")

    authority = rec.get("decision_authority")
    if not isinstance(authority, dict):
        errors.append(f"{ident}: decision_authority must be an object")
    else:
        owner = str(authority.get("owner_type", ""))
        if owner not in {"user", "delegated_agent"}:
            errors.append(f"{ident}: decision_authority.owner_type must be user or delegated_agent")
        if owner == "delegated_agent" and not _nonempty(authority.get("delegation_ref")):
            errors.append(f"{ident}: delegated_agent authority requires delegation_ref")

    constraints = rec.get("constraints")
    if not isinstance(constraints, list):
        errors.append(f"{ident}: constraints must be a list")
        constraints = []
    seen_constraints: set[str] = set()
    for row in constraints:
        if not isinstance(row, dict):
            errors.append(f"{ident}: constraint record must be an object")
            continue
        cid = str(row.get("constraint_id", ""))
        if not cid:
            errors.append(f"{ident}: constraint missing constraint_id")
        elif cid in seen_constraints:
            errors.append(f"{ident}: duplicate constraint_id {cid}")
        seen_constraints.add(cid)
        if not _nonempty(row.get("statement")):
            errors.append(f"{ident}/{cid or '?'}: constraint statement must be non-empty")
        if str(row.get("status", "")) not in {"active", "relaxed", "superseded"}:
            errors.append(f"{ident}/{cid or '?'}: invalid constraint status")
        basis_kind = str(row.get("basis_kind", ""))
        if basis_kind not in AUTHORITATIVE_BASIS_KINDS:
            errors.append(
                f"{ident}/{cid or '?'}: constraint basis_kind {basis_kind!r} is not authoritative; working hypotheses cannot become constraints by serialization"
            )
        if not _nonempty(row.get("basis_ref")):
            errors.append(f"{ident}/{cid or '?'}: constraint requires basis_ref")

    positions = rec.get("positions")
    if not isinstance(positions, list):
        errors.append(f"{ident}: positions must be a list")
        positions = []
    seen_positions: set[str] = set()
    position_map: dict[str, dict[str, Any]] = {}
    for pos in positions:
        if not isinstance(pos, dict):
            errors.append(f"{ident}: position record must be an object")
            continue
        pid = str(pos.get("position_id", ""))
        if not pid:
            errors.append(f"{ident}: position missing position_id")
        elif pid in seen_positions:
            errors.append(f"{ident}: duplicate position_id {pid}")
        seen_positions.add(pid)
        if pid:
            position_map[pid] = pos
        if not _nonempty(pos.get("statement")):
            errors.append(f"{ident}/{pid or '?'}: position statement must be non-empty")
        viability = str(pos.get("viability", ""))
        stance = str(pos.get("planning_stance", ""))
        if viability not in POSITION_VIABILITY:
            errors.append(f"{ident}/{pid or '?'}: invalid viability {viability!r}")
        if stance not in PLANNING_STANCES:
            errors.append(f"{ident}/{pid or '?'}: invalid planning_stance {stance!r}")
        if viability == "excluded" and not _nonempty(pos.get("exclusion_basis_ref")):
            errors.append(f"{ident}/{pid or '?'}: excluded position requires exclusion_basis_ref")
        if viability == "viable" and pos.get("exclusion_basis_ref") not in (None, ""):
            warnings.append(f"{ident}/{pid or '?'}: viable position still carries exclusion_basis_ref; review stale provenance")
        if stance == "working_hypothesis" and viability != "viable":
            errors.append(f"{ident}/{pid or '?'}: excluded position cannot remain a working_hypothesis")

    resolution = rec.get("resolution")
    retirement = rec.get("retirement")
    if state == "open":
        if resolution not in (None, {}):
            errors.append(f"{ident}: open Issue cannot carry a resolution")
        if retirement not in (None, {}):
            errors.append(f"{ident}: open Issue cannot carry retirement data")
        if policy == "must_resolve" and rec.get("decision_horizon") in (None, ""):
            warnings.append(f"{ident}: must_resolve Issue has no decision_horizon")
        if domain == "declared_exhaustive":
            viable = [x for x in positions if isinstance(x, dict) and str(x.get("viability")) == "viable"]
            if not positions or not viable:
                errors.append(f"{ident}: declared_exhaustive open Issue has no viable positions")
            elif len(viable) == 1:
                warnings.append(
                    f"{ident}: declared_exhaustive open Issue has one viable position; review for implicit collapse but do not auto-resolve"
                )
    elif state == "resolved":
        if not isinstance(resolution, dict):
            errors.append(f"{ident}: resolved Issue requires resolution object")
        else:
            for key in ("statement", "basis_ref", "authority_ref"):
                if not _nonempty(resolution.get(key)):
                    errors.append(f"{ident}: resolution requires non-empty {key}")
            for pid in resolution.get("position_ids", []) if isinstance(resolution.get("position_ids"), list) else []:
                if str(pid) not in position_map:
                    errors.append(f"{ident}: resolution references unknown position_id {pid}")
                elif str(position_map[str(pid)].get("viability")) == "excluded":
                    errors.append(f"{ident}: resolution references excluded position_id {pid}")
        if policy == "preserve_open":
            errors.append(f"{ident}: preserve_open Issue cannot be resolved without an explicit policy change")
        if retirement not in (None, {}):
            errors.append(f"{ident}: resolved Issue cannot also carry retirement data")
        if any(str(x.get("planning_stance")) == "working_hypothesis" for x in positions if isinstance(x, dict)):
            warnings.append(f"{ident}: resolved Issue still has working_hypothesis stance; review stale planning state")
    elif state == "retired":
        if resolution not in (None, {}):
            errors.append(f"{ident}: retired Issue must not fabricate a resolution")
        if not isinstance(retirement, dict) or not _nonempty(retirement.get("reason")) or not _nonempty(retirement.get("basis_ref")):
            errors.append(f"{ident}: retired Issue requires retirement.reason and retirement.basis_ref")

    return errors, warnings


def validate_state(state: dict[str, Any]) -> dict[str, Any]:
    raw = state.get("authorial_unknowns", [])
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        return {"errors": ["story_state.authorial_unknowns must be a list when present"], "warnings": [], "checked": 0}

    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    checked = 0
    for i, rec in enumerate(raw):
        if not isinstance(rec, dict):
            errors.append(f"authorial_unknowns[{i}] must be an object")
            continue
        checked += 1
        ident = issue_id(rec, i)
        if ident in seen_ids:
            errors.append(f"duplicate OpenIssue/question identity: {ident}")
        seen_ids.add(ident)
        rec_errors, rec_warnings = validate_record(rec, i)
        errors.extend(rec_errors)
        warnings.extend(rec_warnings)
    return {"errors": errors, "warnings": warnings, "checked": checked}


def summarize_state(state: dict[str, Any]) -> dict[str, Any]:
    records = [x for x in issue_records(state) if isinstance(x, dict)]
    open_rows = [x for x in records if active_issue(x)]
    v2_open = [x for x in open_rows if is_v2(x)]
    return {
        "total": len(records),
        "open": len(open_rows),
        "must_resolve_open": sum(str(x.get("resolution_policy")) == "must_resolve" for x in v2_open),
        "preserve_open": sum(str(x.get("resolution_policy")) == "preserve_open" for x in v2_open),
        "legacy_review_required": sum(str(x.get("mode")) == "DELIBERATELY_UNRESOLVED" for x in open_rows if not is_v2(x)),
    }


def commitment_material(rec: dict[str, Any]) -> dict[str, Any]:
    """Canonical material for a derived commitment fingerprint.

    Working/candidate/parked stance is deliberately excluded. The fingerprint changes
    only when the authoritative commitment boundary changes.
    """
    if not is_v2(rec):
        return {
            "legacy": True,
            "question_id": rec.get("question_id", rec.get("id")),
            "mode": rec.get("mode"),
            "status": rec.get("status"),
            "compatibility_constraints": rec.get("compatibility_constraints", []),
        }

    active_constraints = []
    for row in rec.get("constraints", []) if isinstance(rec.get("constraints"), list) else []:
        if isinstance(row, dict) and str(row.get("status")) == "active":
            active_constraints.append({
                "constraint_id": row.get("constraint_id"),
                "statement": row.get("statement"),
                "basis_kind": row.get("basis_kind"),
                "basis_ref": row.get("basis_ref"),
            })
    active_constraints.sort(key=lambda x: str(x.get("constraint_id")))

    excluded_positions = []
    all_positions = []
    for pos in rec.get("positions", []) if isinstance(rec.get("positions"), list) else []:
        if not isinstance(pos, dict):
            continue
        material = {
            "position_id": pos.get("position_id"),
            "statement": pos.get("statement"),
            "viability": pos.get("viability"),
            "exclusion_basis_ref": pos.get("exclusion_basis_ref"),
        }
        all_positions.append(material)
        if str(pos.get("viability")) == "excluded":
            excluded_positions.append(material)
    all_positions.sort(key=lambda x: str(x.get("position_id")))
    excluded_positions.sort(key=lambda x: str(x.get("position_id")))

    return {
        "record_version": rec.get("record_version"),
        "question_id": rec.get("question_id"),
        "state": rec.get("state"),
        "resolution_policy": rec.get("resolution_policy"),
        "resolution_criterion": rec.get("resolution_criterion"),
        "domain_semantics": rec.get("domain_semantics"),
        "constraints": active_constraints,
        "authoritative_position_state": all_positions if rec.get("domain_semantics") == "declared_exhaustive" else excluded_positions,
        "resolution": rec.get("resolution") if rec.get("state") == "resolved" else None,
        "retirement": rec.get("retirement") if rec.get("state") == "retired" else None,
    }


def commitment_fingerprint(rec: dict[str, Any]) -> str:
    blob = json.dumps(commitment_material(rec), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
