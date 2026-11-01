#!/usr/bin/env python3
"""Mechanical continuity checks for long-form fiction Story State JSON.

Checks are evidence/field-driven: absence of a Hidden Network, scene delta, complex
timeline, or other optional planning artifact is never itself a validation failure.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from pathlib import Path
from typing import Any

from open_issue import validate_state as validate_open_issue_state


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Top-level JSON value must be an object")
    return data


def overlaps(a_start: float, a_end: float, b_start: float, b_end: float) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)


def as_num(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def interval(record: dict[str, Any]) -> tuple[float, float]:
    start = as_num(record.get("valid_from"))
    end = as_num(record.get("valid_to"))
    return (
        float("-inf") if start is None else start,
        float("inf") if end is None else end,
    )


def edge_active(edge: dict[str, Any], at_time: float) -> bool:
    start, end = interval(edge)
    return start <= at_time < end and edge.get("passable", True) is not False


def shortest_travel_time(
    edges: list[dict[str, Any]],
    start_loc: str,
    end_loc: str,
    at_time: float,
) -> float | None:
    if start_loc == end_loc:
        return 0.0

    graph: dict[str, list[tuple[str, float]]] = {}
    for edge in edges:
        if not isinstance(edge, dict) or not edge_active(edge, at_time):
            continue
        a, b = edge.get("a"), edge.get("b")
        weight = as_num(edge.get("min_travel_time"))
        if a is None or b is None or weight is None or weight < 0:
            continue
        a, b = str(a), str(b)
        graph.setdefault(a, []).append((b, weight))
        if edge.get("one_way", False) is not True:
            graph.setdefault(b, []).append((a, weight))

    queue: list[tuple[float, str]] = [(0.0, start_loc)]
    best: dict[str, float] = {start_loc: 0.0}
    while queue:
        cost, node = heapq.heappop(queue)
        if cost != best.get(node):
            continue
        if node == end_loc:
            return cost
        for nxt, weight in graph.get(node, []):
            new_cost = cost + weight
            if new_cost < best.get(nxt, float("inf")):
                best[nxt] = new_cost
                heapq.heappush(queue, (new_cost, nxt))
    return None


def derive_effective_causal_claim(event: dict[str, Any]) -> dict[str, bool]:
    """Optional intent labels cannot lower an outcome-bound structural claim."""
    explicit = event.get("intentional") is True or event.get("mastery_claim") is True
    strong = (event.get("causal_role") == "PRIMARY_CAUSE" or
              event.get("mastery_claim") is True or
              event.get("definite_responsibility") is True)
    preplanned = event.get("plan_type") == "PREPLANNED" and strong
    action = event.get("responsible_action_or_omission", {})
    action = action if isinstance(action, dict) else {}
    return {"intent": explicit or preplanned, "strong": strong,
            "plan_intent_conflict": preplanned and
            (event.get("intentional") is False or action.get("intent") is False)}


def build_canonical_action_index(records: list[dict[str, Any]]) -> dict[str, list[tuple[int, dict[str, Any], bool]]]:
    """Index existing event interventions; reserve branch IDs for ambiguity checks.

    A planned alternative is not an executed sufficient cause. Its realized
    intervention must have its own causal event/basis before proving redundancy.
    """
    index: dict[str, list[tuple[int, dict[str, Any], bool]]] = {}
    for pos, event in enumerate(records):
        entries = [(event.get("responsible_action_or_omission"), True)]
        entries.extend((branch.get("action"), False) for branch in event.get("fallbacks", []))
        for action, realized in entries:
            if isinstance(action, dict) and action.get("id"):
                index.setdefault(action["id"], []).append((pos, action, realized))
    return index


# Capabilities constrain incoming sufficient-cause claims, not local attribution.
# Unknown/new roles fail closed until their owner defines this capability.
SUFFICIENT_SOURCE_ROLE_POLICY = {
    "PRIMARY_CAUSE": "COUNTERFACTUAL",
    "CONTRIBUTING_CAUSE": "COUNTERFACTUAL",
    "CONDITION_PROVIDER": "COUNTERFACTUAL",
    "TRIGGER": "COUNTERFACTUAL",
    "ENABLER": "COUNTERFACTUAL",
    "OMISSION_CAUSE": "COUNTERFACTUAL",
    "ACCIDENTAL_CAUSE": "COUNTERFACTUAL",
    "OVERDETERMINED_CAUSE": "COUNTERFACTUAL_OR_REDUNDANCY",
    "INCIDENTAL": "DENIED",
    "NOT_CAUSALLY_RESPONSIBLE": "DENIED",
}


def source_supports_sufficient_cause(event: dict[str, Any], *,
                                     source_validated: bool) -> str | None:
    """Return an opaque rejection code, or None for supported source strength.

    Called only after canonical identity/action/outcome checks. source_validated
    includes local responsibility/knowledge checks and recursive reference
    closure; claimant metadata never supplies source evidence here.
    """
    policy = SUFFICIENT_SOURCE_ROLE_POLICY.get(event.get("causal_role"))
    if policy in {None, "DENIED"}:
        return "causal.overdetermination_ineligible_source_role"
    if not source_validated:
        return "causal.overdetermination_invalid_action"
    cf = event.get("counterfactual_without_action", {})
    if (event.get("closure") == "PRESERVE_OPEN" or not cf.get("provenance") or
            cf.get("material_effect") is not None):
        return "causal.overdetermination_insufficient_source_strength"
    # The current contract's closed outcome-bound comparison is the strongest
    # existing support (including B2-R); a material-effect-only comparison is
    # weaker. No new sufficiency flag or inference from intent is introduced.
    if cf.get("result") in {"OUTCOME_UNLIKELY", "OUTCOME_MATERIALLY_CHANGED"}:
        return None
    if (policy == "COUNTERFACTUAL_OR_REDUNDANCY" and
            cf.get("result") == "OVERDETERMINED"):
        return None
    return "causal.overdetermination_insufficient_source_strength"


def causal_sufficiency_issues(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Audit typed responsibility claims; not prose, probability, or legal proof.

    Hidden Causal Networks owns this optional Story State view. Diagnostics are
    opaque for safe backend handoff: no hidden action/fact text is interpolated.
    """
    import copy
    from jsonschema import Draft202012Validator
    from semantic_kernel import temporal_epistemic_issues
    from research_freshness import temporal_order, temporal_bounds

    issues: list[dict[str, Any]] = []
    schema = load_json(Path(__file__).resolve().parent.parent /
                       "assets/project-schemas/causal-event.schema.json")
    for err in Draft202012Validator(schema).iter_errors(data):
        issues.append({"severity": "error", "code": "causal.schema",
                       "message": "Causal record shape requires repair", "scene_ids": []})
    if issues:
        return issues
    records = data.get("causal_events", [])
    if not isinstance(records, list):
        return issues
    action_index = build_canonical_action_index(records)
    local_valid = [False] * len(records)
    references: dict[int, tuple[bool, bool]] = {}

    def emit_for(pos: int, code: str, severity: str = "error") -> None:
        event = records[pos]
        issues.append({"severity": severity, "code": code,
                       "message": code + ": backend causal audit requires review",
                       "scene_ids": [str(event["scene_id"])] if event.get("scene_id") else []})

    for pos, event in enumerate(records):
        start = len(issues)
        def emit(code: str, severity: str = "error") -> None:
            emit_for(pos, code, severity)

        role = event.get("causal_role")
        typed = event.get("causal_version") == "1.0.0"
        active = event.get("active_use") is True
        high_risk = event.get("high_risk") is True or role not in (None, "INCIDENTAL", "NOT_CAUSALLY_RESPONSIBLE") or event.get("mastery_claim") is True or event.get("definite_responsibility") is True
        if not typed and not active:
            emit("causal.legacy_unknown_sufficiency", "warning")
            continue
        if not high_risk:
            continue
        if not role or not event.get("outcome"):
            emit("causal.missing_outcome_or_role")
        if not event.get("mechanism_class"):
            emit("causal.missing_mechanism")
        mode = event.get("plan_type")
        claim = derive_effective_causal_claim(event)
        intent = claim["intent"]
        if claim["plan_intent_conflict"]:
            emit("causal.plan_intent_conflict")
        attributed = role not in (None, "INCIDENTAL", "NOT_CAUSALLY_RESPONSIBLE") or intent
        if intent and mode == "CHANCE_DRIVEN":
            emit("causal.chance_attribution_conflict")
        if intent and not mode:
            emit("causal.missing_plan_type")
        agent = event.get("responsible_agent")
        action = event.get("responsible_action_or_omission")
        action = action if isinstance(action, dict) else {}
        if any(len(action_index.get(a.get("id"), [])) > 1 for a in
               [action, *(b.get("action", {}) for b in event.get("fallbacks", []))]):
            emit("causal.duplicate_action")
        if attributed:
            references[pos] = (False, False)
            if not agent:
                emit("causal.missing_agent")
            if not action.get("id") or not action.get("description") or action.get("kind") not in {"ACTION", "DELIBERATE_OMISSION", "ACCIDENTAL_ACTION"}:
                emit("CAUSAL_INSUFFICIENCY")
            if action.get("actor") != agent or action.get("causal_relevance") is not True or not action.get("provenance") or action.get("outcome_ref") != event.get("outcome"):
                emit("causal.intervention_basis")
            if temporal_bounds(action.get("at")) is None:
                emit("causal.intervention_time")
            if intent and (action.get("intent") is not True or action.get("mechanism_awareness") is not True):
                emit("causal.intent_basis")
            if role == "OMISSION_CAUSE" and action.get("kind") != "DELIBERATE_OMISSION":
                emit("causal.omission_basis")
            if action.get("kind") == "DELIBERATE_OMISSION":
                if any(action.get(k) is not True for k in ("intent", "capability", "opportunity", "risk_awareness", "causal_relevance")) or not action.get("knowledge_refs"):
                    emit("causal.omission_basis")

        conditions = event.get("conditions", [])
        conditions = conditions if isinstance(conditions, list) else []
        conditions = [c for c in conditions if isinstance(c, dict)]
        ids = [c.get("id") for c in conditions]
        if len(ids) != len(set(ids)):
            emit("causal.duplicate_condition")
        basis = event.get("responsibility_basis")
        basis = basis if isinstance(basis, dict) else {}
        cf = event.get("counterfactual_without_action")
        cf = cf if isinstance(cf, dict) else {}
        if attributed:
            if (basis.get("action_ref") != action.get("id") or not basis.get("action_ref") or
                basis.get("outcome_ref") != event.get("outcome") or not basis.get("provenance") or
                not isinstance(basis.get("condition_refs"), list) or set(basis.get("condition_refs", [])) != set(ids)):
                emit("causal.responsibility_basis")
            result = cf.get("result")
            if not result or not cf.get("provenance"):
                emit("causal.counterfactual_missing")
            elif result in {"UNKNOWN", "OPEN"}:
                emit("causal.counterfactual_review", "warning")
                if event.get("closure") != "PRESERVE_OPEN" or event.get("definite_responsibility") is True or event.get("mastery_claim") is True:
                    emit("causal.open_claim_conflict")
            elif role == "PRIMARY_CAUSE" and result not in {"OUTCOME_UNLIKELY", "OUTCOME_MATERIALLY_CHANGED"}:
                emit("CAUSAL_INSUFFICIENCY")
            elif result in {"OUTCOME_UNCHANGED", "OUTCOME_STILL_LIKELY", "OVERDETERMINED"}:
                material = cf.get("material_effect") in {"RISK", "TIMING", "MECHANISM", "OPPORTUNITY"} and bool(cf.get("effect_basis"))
                # Resolve all declared other causes after each source event has
                # passed its own audit, independent of record order.
                references[pos] = (not material, result == "OVERDETERMINED")

        # Backend knowledge is not Writer disclosure. Reuse K21 on a private
        # actor-use view; remove only disclosure metadata from copied sources.
        def knowledge(fid: Any, at: Any) -> bool:
            private = copy.deepcopy(data)
            private["writer_visible_facts"] = []
            for key in ("facts", "research_dependencies"):
                for fact in private.get(key, []) or []:
                    if isinstance(fact, dict):
                        fact.pop("visibility", None)
                        fact.pop("writer_visible", None)
            use = {"actor": agent, "fact_id": fid, "used_at": at, "consequential": True}
            found = temporal_epistemic_issues(private, [use])
            if any(x.get("severity") == "error" for x in found):
                emit("causal.precondition_knowledge")
                return False
            return True

        action_at = action.get("at")
        for fid in action.get("knowledge_refs", []) or []:
            knowledge(fid, action_at)
        unresolved: list[dict[str, Any]] = []
        for condition in conditions:
            cls = condition.get("classification")
            relevance = condition.get("necessity")
            if cls not in {"CONTROLLED", "KNOWN_STABLE", "REASONABLY_EXPECTED", "UNKNOWN", "RANDOM"} or relevance not in {"NECESSARY", "SUPPORTING", "INCIDENTAL", "BACKGROUND"}:
                emit("causal.condition_classification")
                continue
            if not condition.get("provenance"):
                emit("causal.condition_basis")
            if cls == "CONTROLLED":
                if (condition.get("controlled_by") != agent or condition.get("control_action_ref") != action.get("id") or
                    condition.get("causal_relevance") is not True or condition.get("id") not in action.get("sets_conditions", [])):
                    emit("causal.control_basis")
            if cls in {"KNOWN_STABLE", "REASONABLY_EXPECTED"}:
                if not condition.get("fact_ref") or not condition.get("stability_basis" if cls == "KNOWN_STABLE" else "expectation_basis"):
                    emit("causal.precondition_basis")
                knowledge(condition.get("fact_ref"), action_at)
            if cls in {"UNKNOWN", "RANDOM"} and relevance == "NECESSARY" and intent:
                # A label or a free-text fallback does not establish adaptation.
                responses = event.get("fallbacks", [])
                covered = False
                for response in responses if isinstance(responses, list) else []:
                    if not isinstance(response, dict) or condition.get("id") not in response.get("covers_conditions", []):
                        continue
                    intervention = response.get("action", {})
                    if not isinstance(intervention, dict):
                        continue
                    prior = temporal_order(response.get("planned_at"), action_at) is True
                    after = temporal_order(condition.get("resolved_at"), intervention.get("at")) is True
                    valid = (bool(response.get("provenance")) and intervention.get("actor") == agent and
                             intervention.get("kind") == "ACTION" and intervention.get("causal_relevance") is True and
                             bool(intervention.get("id")) and bool(intervention.get("provenance")) and
                             bool(intervention.get("description")) and intervention.get("outcome_ref") == event.get("outcome") and
                             response.get("outcome_ref") == event.get("outcome") and
                             (response.get("kind") == "FALLBACK" and prior or
                              response.get("kind") == "ADAPTIVE" and mode in {"ADAPTIVE", "OPPORTUNISTIC"} and after))
                    if valid and response.get("kind") == "ADAPTIVE":
                        observation = condition.get("resolution_fact_ref")
                        valid = bool(observation) and observation in response.get("observed_fact_refs", [])
                        if valid:
                            valid = knowledge(observation, intervention.get("at"))
                    if valid and response.get("fact_ref") and knowledge(response.get("fact_ref"), intervention.get("at")):
                        covered = True
                if not covered:
                    unresolved.append(condition)
                    if mode in {"ADAPTIVE", "OPPORTUNISTIC"}:
                        emit("causal.adaptation_basis")

        if mode == "PREPLANNED" and intent and unresolved:
            # Collapse explicitly correlated/shared sources. Never infer
            # independence from a count of random labels.
            groups = {c.get("independent_group") for c in unresolved if c.get("independent_group")}
            known = all(c.get("independent_group") and c.get("independence_basis") for c in unresolved)
            if claim["strong"] and known and len(groups) > 1:
                emit("MASTERMIND_INFLATION")
            elif claim["strong"] and not known:
                emit("causal.independence_review")
            elif event.get("bounded_chance") is not True or not event.get("chance_basis"):
                emit("causal.contingency_review")
        local_valid[pos] = len(issues) == start

    checked: dict[int, bool] = {}

    def check_references(pos: int, path: frozenset[int]) -> bool:
        if pos in checked:
            return checked[pos]
        event = records[pos]
        valid = local_valid[pos]
        sufficient = False
        path = path | {pos}
        for cause in event.get("other_sufficient_causes", []) if pos in references else []:
            candidates = action_index.get(cause.get("action_ref"), [])
            code = None
            if not candidates:
                code = "causal.overdetermination_missing_action"
            elif len(candidates) != 1:
                code = "causal.overdetermination_ambiguous_action"
            else:
                source, intervention, realized = candidates[0]
                if source == pos:
                    code = "causal.overdetermination_self_reference"
                elif source in path:
                    code = "causal.overdetermination_circular_reference"
                elif intervention.get("actor") != cause.get("agent"):
                    code = "causal.overdetermination_actor_mismatch"
                elif (cause.get("outcome_ref") != event.get("outcome") or
                      intervention.get("outcome_ref") != event.get("outcome") or
                      records[source].get("outcome") != event.get("outcome")):
                    code = "causal.overdetermination_outcome_mismatch"
                elif intervention.get("kind") not in {"ACTION", "DELIBERATE_OMISSION", "ACCIDENTAL_ACTION"} or intervention.get("causal_relevance") is not True:
                    code = "causal.overdetermination_noncausal_action"
                elif not realized or source not in references or not check_references(source, path):
                    code = "causal.overdetermination_invalid_action"
                else:
                    code = source_supports_sufficient_cause(
                        records[source], source_validated=True)
                    if code is None and (cause.get("independent") is not True or
                                         cause.get("sufficient") is not True or
                                         not cause.get("provenance")):
                        code = "causal.overdetermination_basis"
            if code:
                emit_for(pos, code)
                valid = False
            else:
                sufficient = True
        needs_support, overdetermined = references.get(pos, (False, False))
        if needs_support and not (overdetermined and sufficient):
            emit_for(pos, "CAUSAL_INSUFFICIENCY")
            valid = False
        checked[pos] = valid
        return valid

    for pos in references:
        check_references(pos, frozenset())
    return issues


def narrative_artifact_issues(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Selective object-state view; no prose extraction or knowledge inference.

    Custody rows are canonical. References never grant access by themselves.
    Unknown consequential comparisons block review rather than invent precision.
    Diagnostics contain codes only, so carrier text/authorship stays backend-only.
    """
    scenes = data.get("scene_packets", []) or []
    if "narrative_artifacts" not in data and not any(
            isinstance(scene, dict) and isinstance(scene.get("objects"), list) and
            any(isinstance(obj, dict) and obj.get("artifact_ref") for obj in scene["objects"])
            for scene in scenes):
        return []
    from jsonschema import Draft202012Validator
    from research_freshness import temporal_order, temporal_bounds

    issues: list[dict[str, Any]] = []

    def add(code: str, scene_ids: list[str] | None = None, severity: str = "error") -> None:
        issues.append({"severity": severity, "code": code, "message": code,
                       "scene_ids": scene_ids or []})

    schema = load_json(Path(__file__).resolve().parent.parent /
                       "assets/project-schemas/narrative-artifact.schema.json")
    if any(Draft202012Validator(schema).iter_errors(data)):
        add("artifact.schema")
        return issues

    def ordered(a: Any, b: Any, code: str) -> bool:
        result = temporal_order(a, b)
        if result is not True:
            add(code if result is False else "artifact.time_needs_review")
        return result is True

    def extent(value: dict[str, Any]) -> None:
        if value["medium"] == "paper":
            sets = {}
            for key in ("available_surfaces", "written_surfaces", "blank_surfaces"):
                rows = value.get(key, [])
                ids = [(r["sheet"], r["side"]) for r in rows]
                sets[key] = set(ids)
                if len(ids) != len(set(ids)):
                    add("artifact.duplicate_surface")
                if any(sheet > value["sheets"] for sheet, _ in ids):
                    add("artifact.surface_out_of_range")
            available = sets["available_surfaces"]
            written = sets["written_surfaces"]
            blank = sets["blank_surfaces"]
            if {i for i, _ in available} != set(range(1, value["sheets"] + 1)):
                add("artifact.sheet_identity_mismatch")
            if not (written | blank) <= available:
                add("artifact.surface_unavailable")
            if written & blank:
                add("artifact.blank_inscribed_conflict")
            if "written_surface_count" in value and value["written_surface_count"] != len(written):
                add("artifact.written_count_mismatch")
        elif value["medium"] in {"audio", "video"}:
            seen = set()
            for segment in value.get("segments", []):
                if segment["id"] in seen:
                    add("artifact.duplicate_segment")
                seen.add(segment["id"])
                if segment["start"] > segment["end"] or segment["end"] > value["duration_seconds"]:
                    add("artifact.invalid_media_extent")

    rows = data.get("narrative_artifacts", [])
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        add("artifact.duplicate_identity")
    custody = [r for r in (data.get("custody", []) or []) if isinstance(r, dict)]
    custody_index: dict[str, list[dict[str, Any]]] = {}
    custody_item_index: dict[str, list[dict[str, Any]]] = {}
    for row in custody:
        if isinstance(row.get("id"), str):
            custody_index.setdefault(row["id"], []).append(row)
        if isinstance(row.get("item"), str):
            custody_item_index.setdefault(row["item"], []).append(row)

    def access(artifact: dict[str, Any], actor: str, start: Any, end: Any,
               ref: str | None = None) -> bool:
        candidates = custody_index.get(ref, []) if ref else custody
        if ref and len(candidates) != 1:
            add("artifact.custody_reference")
            return False
        unknown = False
        for row in candidates:
            if row.get("item") != artifact["id"] or row.get("holder") != actor:
                continue
            left = temporal_order(row.get("start"), start)
            right = True if row.get("end") is None else temporal_order(end, row["end"])
            # Canonical custody uses half-open intervals; exact end is not access.
            eb, rb = temporal_bounds(end), temporal_bounds(row.get("end"))
            if eb and rb and eb == rb and eb[1] == eb[2]:
                # An interval may finish at handover; a new point inscription
                # cannot start after the outgoing holder's half-open window.
                right = start != end and temporal_order(start, end) is True
            if left is True and right is True:
                return True
            unknown |= left is None or right is None
        add("artifact.access_needs_review" if unknown else "artifact.inscription_without_access")
        return False

    def custody_holders_at(artifact: dict[str, Any], at: Any) -> tuple[set[str], bool]:
        """Return holders whose canonical half-open custody covers a point."""
        holders: set[str] = set()
        unknown = False
        for row in custody_item_index.get(artifact["id"], []):
            left = temporal_order(row.get("start"), at)
            right = True if row.get("end") is None else temporal_order(at, row["end"])
            at_bounds, end_bounds = temporal_bounds(at), temporal_bounds(row.get("end"))
            if at_bounds and end_bounds and at_bounds == end_bounds and at_bounds[1] == at_bounds[2]:
                # Custody is [start, end); the outgoing holder has no access at end.
                right = False
            if left is True and right is True:
                if isinstance(row.get("holder"), str):
                    holders.add(row["holder"])
            else:
                unknown |= left is None or right is None
        return holders, unknown

    def holder_claim(artifact: dict[str, Any], at: Any, value: str,
                     owned: list[str] | None = None,
                     conflict: str = "artifact.holder_custody_conflict",
                     unverified: str = "artifact.holder_state_unverified") -> bool:
        """Validate a membership claim using only canonical custody."""
        holders, unknown = custody_holders_at(artifact, at)
        if value in holders:
            return True
        if unknown:
            add("artifact.access_needs_review", owned)
        elif holders:
            add(conflict, owned)
            if conflict == "artifact.scene_state_conflict":
                add("artifact.cross_chapter_contradiction", owned)
        else:
            add(unverified, owned)
        return False

    def is_physical_carrier(artifact: dict[str, Any]) -> bool:
        return artifact.get("medium") in {"paper", "audio", "video", "other"}

    tracked_scene_fields = {
        "type", "author", "created_at", "medium", "holder", "location",
        "condition", "seal_state", "physical_extent", "content_layer_ids",
    }
    scene_field_aliases = {
        "entry_holder": "holder", "exit_holder": "holder",
        "entry_location": "location", "exit_location": "location",
        "entry_condition": "condition", "exit_condition": "condition",
        "entry_seal_state": "seal_state", "exit_seal_state": "seal_state",
        "entry_physical_extent": "physical_extent", "exit_physical_extent": "physical_extent",
        "entry_content_layer_ids": "content_layer_ids", "exit_content_layer_ids": "content_layer_ids",
        "entry_type": "type", "exit_type": "type",
        "entry_author": "author", "exit_author": "author",
        "entry_created_at": "created_at", "exit_created_at": "created_at",
        "entry_medium": "medium", "exit_medium": "medium",
    }

    for artifact in rows:
        active = (artifact.get("durable") is True or artifact.get("high_risk") is True or
                  bool(artifact.get("required_for")) or any(k in artifact for k in
                  ("inscriptions", "physical_extent", "snapshots", "changes", "events", "lifecycle")))
        if not active:
            add("artifact.legacy_unknown_lifecycle", severity="warning")
            legacy_scene_claim = any(
                isinstance(scene, dict) and isinstance(scene.get("objects", []), list) and any(
                    isinstance(obj, dict) and
                    (obj.get("artifact_ref") == artifact.get("id") or obj.get("id") == artifact.get("id")) and
                    any(key in obj for key in (*tracked_scene_fields, *scene_field_aliases))
                    for obj in scene.get("objects", [])
                ) for scene in scenes
            )
            if not legacy_scene_claim:
                continue
        if active and not all(k in artifact for k in ("type", "medium", "author", "created_at")):
            add("artifact.incomplete_active_contract")
            continue
        aid, author = artifact["id"], artifact.get("author")
        if active and temporal_bounds(artifact["created_at"]) is None:
            add("artifact.time_needs_review")
        if active and not any(r.get("item") == aid for r in custody):
            add("artifact.missing_required_state")
        object_custody = [r for r in custody if r.get("item") == aid]
        for pos, row in enumerate(object_custody):
            if row.get("end") is not None:
                ordered(row.get("start"), row["end"], "artifact.custody_order")
            elif temporal_bounds(row.get("start")) is None:
                add("artifact.access_needs_review")
            if not row.get("holder"):
                add("artifact.custody_reference")
            for other in object_custody[pos + 1:]:
                if row.get("holder") == other.get("holder") or row.get("shared") is True or other.get("shared") is True:
                    continue
                ab = False if row.get("end") is None else temporal_order(row["end"], other.get("start"))
                ba = False if other.get("end") is None else temporal_order(other["end"], row.get("start"))
                if ab is False and ba is False:
                    add("artifact.custody_overlap")
                elif ab is not True and ba is not True:
                    add("artifact.access_needs_review")
        if artifact.get("source_artifact_ref") == aid:
            add("artifact.copy_identity_conflict")
        known_media = {"email": "digital", "audio": "audio", "video": "video",
                       "letter": "paper", "diary": "paper", "notebook": "paper"}
        if artifact.get("type") in known_media and artifact.get("medium") != known_media[artifact["type"]]:
            add("artifact.carrier_medium_mismatch")
        if "physical_extent" in artifact and artifact["physical_extent"]["medium"] != artifact["medium"]:
            add("artifact.carrier_medium_mismatch")
        life = artifact.get("lifecycle", {})
        required = {"inscription_timing": "inscriptions", "physical_extent": "physical_extent",
                    "sealing": "sealed_at", "sending": "sent_at", "delivery": "delivered_at",
                    "opening": "opened_at", "finalization": "finalized_at"}
        for need in artifact.get("required_for", []):
            key = required.get(need)
            if need == "custody":
                if not any(r.get("item") == aid for r in custody):
                    add("artifact.missing_required_state")
            elif key not in artifact and key not in life and not (need == "sending" and "mailed_at" in life):
                add("artifact.missing_required_state")
            elif need == "inscription_timing" and not artifact.get("inscriptions"):
                add("artifact.missing_required_state")
        for key, time in life.items():
            if "created_at" in artifact:
                ordered(artifact["created_at"], time, "artifact.lifecycle_order")
        for sending in ("sent_at", "mailed_at"):
            if sending in life and "delivered_at" in life:
                ordered(life[sending], life["delivered_at"], "artifact.lifecycle_order")
        if "delivered_at" in life and "opened_at" in life:
            ordered(life["delivered_at"], life["opened_at"], "artifact.lifecycle_order")
        opening_access_supported = False
        if active and "opened_at" in life:
            if artifact["medium"] == "digital":
                # Digital delivery is only the existing model's logical access
                # support; this is not a claim of recipient authentication.
                if "delivered_at" not in life:
                    add("artifact.opening_without_access")
                else:
                    relation = temporal_order(life["delivered_at"], life["opened_at"])
                    if relation is True:
                        opening_access_supported = True
                    elif relation is None:
                        add("artifact.access_needs_review")
            else:
                holders, unknown = custody_holders_at(artifact, life["opened_at"])
                if holders:
                    opening_access_supported = True
                elif unknown:
                    add("artifact.access_needs_review")
                else:
                    add("artifact.opening_without_access")
        if "recording_start" in life and "recording_end" in life:
            ordered(life["recording_start"], life["recording_end"], "artifact.lifecycle_order")
        if "recording_end" in life and "finalized_at" in life:
            ordered(life["recording_end"], life["finalized_at"], "artifact.lifecycle_order")
        boundaries = [life[k] for k in ("sent_at", "mailed_at", "finalized_at", "author_control_until") if k in life]
        # Existing author custody cessation is a control boundary even when a
        # convenient artifact marker is omitted or set to a later date.
        boundaries.extend(r["end"] for r in custody if r.get("item") == aid and
                          r.get("holder") == author and r.get("end") is not None)
        events = artifact.get("events", [])
        event_index: dict[str, list[dict[str, Any]]] = {}
        valid_events = set()
        for event in events:
            event_index.setdefault(event["id"], []).append(event)
            before = len(issues)
            if "created_at" in artifact:
                ordered(artifact["created_at"], event["at"], "artifact.lifecycle_order")
            access(artifact, event["actor"], event["at"], event["at"], event["custody_ref"])
            if len(issues) == before:
                valid_events.add(event["id"])
        if any(len(v) != 1 for v in event_index.values()):
            add("artifact.duplicate_event")
        layers = artifact.get("inscriptions", [])
        layer_ids = [r["id"] for r in layers]
        if len(layer_ids) != len(set(layer_ids)):
            add("artifact.duplicate_content_identity")
        if "physical_extent" in artifact:
            extent(artifact["physical_extent"])
        for layer in layers:
            if layer["layer"] == "FRAME_EXTERNAL":
                continue
            start, end = layer["start"], layer.get("end", layer["start"])
            ordered(start, end, "artifact.inscription_interval")
            if "created_at" in artifact:
                ordered(artifact["created_at"], start, "artifact.inscription_before_creation")
            access(artifact, layer["author"], start, end, layer.get("custody_ref"))
            kind = layer["layer"]
            if kind == "ORIGINAL_INSCRIPTION":
                if layer["author"] != author:
                    add("artifact.layer_author_mismatch")
                for boundary in boundaries:
                    ordered(end, boundary, "artifact.inscription_after_control_loss")
                if "recording_start" in life:
                    ordered(life["recording_start"], start, "artifact.recording_order")
                if "recording_end" in life:
                    ordered(end, life["recording_end"], "artifact.recording_order")
            else:
                matches = event_index.get(layer.get("event_ref"), [])
                permitted = {"POSTSCRIPT": {"REOPEN", "POSTSCRIPT"},
                             "REOPENED_ADDITION": {"REOPEN"},
                             "SECOND_AUTHOR_ADDITION": {"ANNOTATE"},
                             "ANNOTATION": {"ANNOTATE"},
                             "LATER_RECORDING": {"RECORD"}, "MEDIA_EDIT": {"EDIT"}}
                event = matches[0] if len(matches) == 1 else None
                if (not event or event["id"] not in valid_events or
                        event["kind"] not in permitted[kind] or event["actor"] != layer["author"]):
                    add("artifact.unsupported_exception")
                else:
                    ordered(event["at"], start, "artifact.exception_order")
                if kind in {"POSTSCRIPT", "REOPENED_ADDITION"} and layer["author"] != author:
                    add("artifact.layer_author_mismatch")
                if kind == "SECOND_AUTHOR_ADDITION" and layer["author"] == author:
                    add("artifact.layer_author_mismatch")
                if kind == "LATER_RECORDING" and artifact["medium"] not in {"audio", "video"}:
                    add("artifact.carrier_medium_mismatch")
                if kind == "MEDIA_EDIT" and artifact["medium"] not in {"audio", "video", "digital"}:
                    add("artifact.carrier_medium_mismatch")
                if artifact.get("medium") == "digital" and "sent_at" in life:
                    ordered(end, life["sent_at"], "artifact.immutable_sent_instance")
            # A seal can be reopened, but a metadata exception is not an opening.
            seals = ([life["sealed_at"]] if "sealed_at" in life else []) + [e["at"] for e in events if e["kind"] == "SEAL"]
            openings = ([life["opened_at"]] if "opened_at" in life else []) + [e["at"] for e in events if e["kind"] == "REOPEN" and e["id"] in valid_events]
            for seal in seals:
                relation = temporal_order(end, seal)
                if relation is False and not any(temporal_order(seal, o) is True and temporal_order(o, start) is True for o in openings):
                    add("artifact.inscription_while_sealed")
                elif relation is None:
                    add("artifact.time_needs_review")

        # Replay only explicit structured world changes, never chapter freshness.
        current = dict(artifact.get("world_state", {}))
        # The existing replay origin is created_at. Holder is a redundant claim
        # at that origin, never an independently replayed state dimension.
        if "holder" in current:
            holder_claim(artifact, artifact.get("created_at"), current.pop("holder"))
        for field in ("type", "author", "created_at"):
            if field in artifact:
                current[field] = artifact[field]
        if "physical_extent" in artifact:
            current["physical_extent"] = artifact["physical_extent"]
        changes = artifact.get("changes", [])
        change_ids = [c["id"] for c in changes]
        if len(change_ids) != len(set(change_ids)):
            add("artifact.duplicate_change")
        previous_time = artifact.get("created_at")
        versions = [(previous_time, dict(current))]
        valid_changes: list[dict[str, Any]] = []
        for change in changes:
            before = len(issues)
            ordered(previous_time, change["at"], "artifact.change_order")
            transfer_rows = custody_index.get(change["custody_ref"], [])
            handing_over = (change["kind"] == "TRANSFER" and len(transfer_rows) == 1 and
                            transfer_rows[0].get("item") == aid and
                            transfer_rows[0].get("holder") == change["actor"] and
                            transfer_rows[0].get("end") == change["at"] and
                            temporal_order(transfer_rows[0].get("start"), change["at"]) is True)
            if not handing_over:
                access(artifact, change["actor"], change["at"], change["at"], change["custody_ref"])
            if set(change["before"]) != set(change["after"]) or not change["before"]:
                add("artifact.invalid_change")
            allowed_keys = {"ANNOTATE": {"physical_extent"},
                            "REMOVE_SHEET": {"physical_extent", "condition"},
                            "OPEN": {"seal_state", "condition"},
                            "TRANSFER": {"holder", "location"},
                            "CHANGE_CONDITION": {"condition"},
                            "MEDIA_EDIT": {"physical_extent"}}[change["kind"]]
            if not set(change["after"]) <= allowed_keys:
                add("artifact.invalid_change")
            for key, value in change["before"].items():
                if key == "holder":
                    if handing_over:
                        # The referenced outgoing row ends at this exact point;
                        # no epsilon or precision inflation is introduced.
                        if value != transfer_rows[0]["holder"]:
                            add("artifact.holder_custody_conflict")
                    else:
                        holder_claim(artifact, change["at"], value)
                    continue
                if key not in current or current[key] != value:
                    add("artifact.change_before_mismatch")
            if "physical_extent" in change["after"]:
                new_extent = change["after"]["physical_extent"]
                extent(new_extent)
                if new_extent["medium"] != artifact["medium"]:
                    add("artifact.carrier_medium_mismatch")
                old_extent = change["before"].get("physical_extent", {})
                if change["kind"] == "ANNOTATE" and old_extent.get("medium") == "paper":
                    identity = lambda v, key: {(r["sheet"], r["side"]) for r in v.get(key, [])}
                    if (new_extent.get("sheets") != old_extent.get("sheets") or
                            identity(new_extent, "available_surfaces") != identity(old_extent, "available_surfaces") or
                            not identity(old_extent, "written_surfaces") <= identity(new_extent, "written_surfaces")):
                        add("artifact.invalid_change")
                if change["kind"] == "REMOVE_SHEET" and (old_extent.get("medium") != "paper" or
                        new_extent.get("sheets", 0) >= old_extent.get("sheets", 0)):
                    add("artifact.invalid_change")
                if artifact["medium"] == "digital" and "sent_at" in life:
                    ordered(change["at"], life["sent_at"], "artifact.immutable_sent_instance")
            if change["kind"] == "OPEN" and change["after"].get("seal_state") != "OPEN":
                add("artifact.invalid_change")
            if "holder" in change["after"]:
                access(artifact, change["after"]["holder"], change["at"], change["at"])
                holder_claim(artifact, change["at"], change["after"]["holder"])
            if len(issues) == before:
                current.update({key: value for key, value in change["after"].items() if key != "holder"})
                versions.append((change["at"], dict(current)))
                valid_changes.append(change)
            previous_time = change["at"]
        for layer in layers:
            if layer["layer"] == "FRAME_EXTERNAL" or not layer.get("surfaces"):
                continue
            physical = artifact.get("physical_extent", {})
            for at, version in versions[1:]:
                relation = temporal_order(at, layer["start"])
                if relation is True:
                    physical = version.get("physical_extent", {})
                elif relation is None:
                    add("artifact.time_needs_review")
            written = {(r["sheet"], r["side"]) for r in physical.get("written_surfaces", [])}
            claimed = [(r["sheet"], r["side"]) for r in layer["surfaces"]]
            if len(claimed) != len(set(claimed)) or not set(claimed) <= written:
                add("artifact.inscription_surface_contradiction")

        scene_object_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for scene in scenes:
            if not isinstance(scene, dict) or not isinstance(scene.get("objects", []), list):
                continue
            for obj in scene.get("objects", []):
                if isinstance(obj, dict) and (obj.get("artifact_ref") == aid or obj.get("id") == aid):
                    if obj.get("artifact_ref", aid) != aid or obj.get("id") != aid:
                        add("artifact.scene_identity_mismatch", [str(scene.get("id", "?"))])
                    scene_object_rows.append((scene, obj))

        has_seal_assertion = any(
            any(key in obj for key in ("seal_state", "entry_seal_state", "exit_seal_state"))
            for _, obj in scene_object_rows
        ) or any("seal_state" in (snapshot.get("state", {}) or {})
                 for snapshot in artifact.get("snapshots", []))
        has_seal_contract = (is_physical_carrier(artifact) and (
            "sealed_at" in life or "opened_at" in life or
            "seal_state" in artifact.get("world_state", {}) or
            has_seal_assertion or any("seal_state" in c.get("after", {}) for c in changes) or
            any(e.get("kind") in {"SEAL", "REOPEN"} for e in events)
        ))
        seal_transitions: list[tuple[Any, str, str]] = []
        if has_seal_contract:
            if "sealed_at" in life:
                seal_transitions.append((life["sealed_at"], "SEALED", "lifecycle.sealed_at"))
            if "opened_at" in life and opening_access_supported and is_physical_carrier(artifact):
                seal_transitions.append((life["opened_at"], "OPEN", "lifecycle.opened_at"))
            for event in events:
                if event["id"] in valid_events and event["kind"] == "SEAL":
                    seal_transitions.append((event["at"], "SEALED", "event.SEAL"))
                elif event["id"] in valid_events and event["kind"] == "REOPEN":
                    seal_transitions.append((event["at"], "OPEN", "event.REOPEN"))
            for change in valid_changes:
                if change["after"].get("seal_state") in {"OPEN", "SEALED", "UNSEALED"}:
                    seal_transitions.append((change["at"], change["after"]["seal_state"], "change.OPEN"))

        def latest_transition(transitions: list[tuple[Any, str, str]],
                              owned: list[str] | None = None) -> str | None:
            if not transitions:
                return None
            dominated: set[int] = set()
            uncertain = False
            for i, (left_at, left_state, _) in enumerate(transitions):
                for j in range(i + 1, len(transitions)):
                    right_at, right_state, _ = transitions[j]
                    left_bounds, right_bounds = temporal_bounds(left_at), temporal_bounds(right_at)
                    if left_bounds and right_bounds and left_bounds == right_bounds and left_bounds[1] == left_bounds[2]:
                        if left_state != right_state:
                            add("artifact.lifecycle_state_conflict", owned)
                            uncertain = True
                        continue
                    left_before_right = temporal_order(left_at, right_at)
                    right_before_left = temporal_order(right_at, left_at)
                    if left_before_right is True and right_before_left is not True:
                        dominated.add(i)
                    elif right_before_left is True and left_before_right is not True:
                        dominated.add(j)
                    elif left_before_right is None or right_before_left is None:
                        if left_state != right_state:
                            add("artifact.time_needs_review", owned)
                            uncertain = True
            winners = [row for i, row in enumerate(transitions) if i not in dominated]
            winner_states = {row[1] for row in winners}
            if len(winner_states) > 1:
                add("artifact.time_needs_review", owned)
                uncertain = True
            return None if uncertain else (winners[0][1] if winners else None)

        def effective_state_at(at: Any, owned: list[str] | None = None) -> dict[str, Any]:
            expected = versions[0][1]
            for version_at, version in versions[1:]:
                order = temporal_order(version_at, at)
                if order is True:
                    expected = version
                elif order is None:
                    add("artifact.time_needs_review", owned)
            expected = dict(expected)
            expected["content_layer_ids"] = []
            for layer in layers:
                if layer["layer"] == "FRAME_EXTERNAL":
                    continue
                relation = temporal_order(layer.get("end", layer["start"]), at)
                if relation is True:
                    expected["content_layer_ids"].append(layer["id"])
                elif relation is None:
                    add("artifact.time_needs_review", owned)
            if has_seal_contract:
                relevant = []
                for transition_at, seal_state, source in seal_transitions:
                    order = temporal_order(transition_at, at)
                    if order is True:
                        relevant.append((transition_at, seal_state, source))
                    elif order is None:
                        add("artifact.time_needs_review", owned)
                state = latest_transition(relevant, owned)
                if state is not None:
                    expected["seal_state"] = state
                elif relevant:
                    expected.pop("seal_state", None)
            return expected

        def normalized(field: str, item: Any) -> Any:
            if field == "content_layer_ids":
                return sorted(item)
            if field == "physical_extent":
                item = dict(item)
                for surface_key in ("available_surfaces", "written_surfaces", "blank_surfaces"):
                    if surface_key in item:
                        item[surface_key] = sorted(item[surface_key], key=lambda r: (r["sheet"], r["side"]))
                if item.get("medium") == "paper":
                    item.setdefault("written_surface_count", len(item["written_surfaces"]))
                return item
            return item

        def scene_conflict(owned: list[str]) -> None:
            add("artifact.scene_state_conflict", owned)
            # Retain the established cross-chapter category for existing callers.
            add("artifact.cross_chapter_contradiction", owned)

        snapshots = list(artifact.get("snapshots", []))
        for snapshot in snapshots:
            owned = [snapshot["scene_id"]] if snapshot.get("scene_id") else []
            state_schema = {"$ref": "#/$defs/state", "$defs": schema["$defs"]}
            if any(Draft202012Validator(state_schema).iter_errors(snapshot["state"])):
                add("artifact.scene_state_shape", owned)
                continue
            if "created_at" in artifact:
                ordered(artifact["created_at"], snapshot["at"], "artifact.snapshot_before_creation")
            expected = effective_state_at(snapshot["at"], owned)
            for key, value in snapshot["state"].items():
                if key == "holder":
                    holder_claim(artifact, snapshot["at"], value, owned,
                                 conflict="artifact.cross_chapter_contradiction")
                    continue
                if key == "seal_state" and (key not in expected or normalized(key, value) != normalized(key, expected.get(key))):
                    add("artifact.seal_state_conflict", owned)
                elif key not in expected:
                    add("artifact.snapshot_state_unverified", owned)
                elif normalized(key, value) != normalized(key, expected[key]):
                    add("artifact.cross_chapter_contradiction", owned)

        for scene, obj in scene_object_rows:
            scene_id = str(scene.get("id", "?"))
            assertions: list[tuple[str, Any, Any]] = []
            for key in tracked_scene_fields:
                if key in obj:
                    assertions.append((key, scene.get("start"), obj[key]))
            for key, field in scene_field_aliases.items():
                if key in obj:
                    is_exit = key.startswith("exit_")
                    assertions.append((field, scene.get("end") if is_exit else scene.get("start"), obj[key]))
            for field, at, value in assertions:
                owned = [scene_id]
                if field != "medium":
                    state_schema = {"$ref": "#/$defs/state", "$defs": schema["$defs"]}
                    if any(Draft202012Validator(state_schema).iter_errors({field: value})):
                        add("artifact.scene_state_shape", owned)
                        continue
                if at is None:
                    add("artifact.scene_state_unverified", owned)
                    continue
                if field == "medium":
                    expected_value = artifact.get("medium")
                    supported = expected_value is not None
                    unknown = False
                elif field in {"type", "author", "created_at"}:
                    expected_value = artifact.get(field)
                    supported = expected_value is not None
                    unknown = False
                elif field == "holder":
                    holder_claim(artifact, at, value, owned,
                                 conflict="artifact.scene_state_conflict",
                                 unverified="artifact.scene_state_unverified")
                    continue
                else:
                    expected = effective_state_at(at, owned)
                    expected_value = expected.get(field)
                    supported = field in expected
                    unknown = False
                if not supported:
                    add("artifact.access_needs_review" if field == "holder" and unknown else
                        "artifact.scene_state_unverified", owned)
                elif field == "holder":
                    if value not in expected_value:
                        scene_conflict(owned)
                elif field == "content_layer_ids":
                    if sorted(value) != sorted(expected_value):
                        scene_conflict(owned)
                elif field == "physical_extent":
                    if normalized(field, value) != normalized(field, expected_value):
                        scene_conflict(owned)
                elif value != expected_value:
                    scene_conflict(owned)
    known = set(ids)
    for scene in scenes:
        if isinstance(scene, dict) and isinstance(scene.get("objects", []), list):
            for obj in scene.get("objects", []):
                if isinstance(obj, dict) and obj.get("artifact_ref") and obj["artifact_ref"] not in known:
                    add("artifact.unresolved_identity", [str(scene.get("id", "?"))])
    return issues


def validate_issues(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return structured validation issues with optional Scene Packet ownership.

    `scene_ids` is authoritative for local scene queries. Human-readable messages remain
    stable enough for CLI use, but callers must not infer ownership by parsing text.
    """
    issues: list[dict[str, Any]] = []

    def add_issue(
        severity: str,
        message: str,
        *,
        code: str = "validation.generic",
        scene_ids: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        owned = []
        for raw in scene_ids or []:
            value = str(raw)
            if value and value != "?" and value not in owned:
                owned.append(value)
        issues.append({"severity": severity, "code": code, "message": message, "scene_ids": owned})

    def error(message: str, *, code: str = "validation.error", scene_ids: list[str] | tuple[str, ...] | None = None) -> None:
        add_issue("error", message, code=code, scene_ids=scene_ids)

    def warn(message: str, *, code: str = "validation.warning", scene_ids: list[str] | tuple[str, ...] | None = None) -> None:
        add_issue("warning", message, code=code, scene_ids=scene_ids)

    timeline = data.get("timeline", []) or []
    by_actor: dict[str, list[dict[str, Any]]] = {}
    for ev in timeline:
        if not isinstance(ev, dict):
            warn("timeline contains a non-object record")
            continue
        actor = ev.get("actor")
        if actor is not None:
            by_actor.setdefault(str(actor), []).append(ev)

    for actor, events in by_actor.items():
        events = sorted(events, key=lambda x: as_num(x.get("start")) if as_num(x.get("start")) is not None else float("-inf"))
        for i, left in enumerate(events):
            try:
                ls, le = float(left["start"]), float(left["end"])
            except (KeyError, TypeError, ValueError):
                warn(f"timeline record for {actor} lacks numeric start/end: {left.get('id', '?')}")
                continue
            for right in events[i + 1 :]:
                try:
                    rs, re = float(right["start"]), float(right["end"])
                except (KeyError, TypeError, ValueError):
                    continue
                if rs >= le:
                    break
                if (
                    overlaps(ls, le, rs, re)
                    and left.get("location") != right.get("location")
                    and not left.get("allow_overlap", False)
                    and not right.get("allow_overlap", False)
                ):
                    error(
                        f"timeline overlap: {actor} in {left.get('location')} ({left.get('id','?')}) "
                        f"and {right.get('location')} ({right.get('id','?')})"
                    )

    # Import at call time: Kernel composes existing backends and shares this law
    # with Compiler/Research without a second knowledge validator.
    from semantic_kernel import temporal_epistemic_issues
    issues.extend(temporal_epistemic_issues(data))
    issues.extend(causal_sufficiency_issues(data))
    issues.extend(narrative_artifact_issues(data))

    custody = data.get("custody", []) or []
    by_item: dict[str, list[dict[str, Any]]] = {}
    for rec in custody:
        if isinstance(rec, dict) and rec.get("item") is not None:
            by_item.setdefault(str(rec["item"]), []).append(rec)
    for item, records in by_item.items():
        for i, left in enumerate(records):
            if left.get("shared", False):
                continue
            try:
                ls, le = float(left["start"]), float(left["end"])
            except (KeyError, TypeError, ValueError):
                continue
            for right in records[i + 1 :]:
                if right.get("shared", False) or left.get("holder") == right.get("holder"):
                    continue
                try:
                    rs, re = float(right["start"]), float(right["end"])
                except (KeyError, TypeError, ValueError):
                    continue
                if overlaps(ls, le, rs, re):
                    error(
                        f"custody overlap: {item} held by {left.get('holder','?')} and {right.get('holder','?')}"
                    )

    spatial_edges_raw = data.get("spatial_edges", []) or []
    spatial_edges: list[dict[str, Any]] = [x for x in spatial_edges_raw if isinstance(x, dict)]
    inverse_direction = {
        "north": "south", "south": "north", "east": "west", "west": "east",
        "northeast": "southwest", "southwest": "northeast",
        "northwest": "southeast", "southeast": "northwest",
        "above": "below", "below": "above", "upstream": "downstream", "downstream": "upstream",
    }

    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for edge in spatial_edges:
        edge_id = edge.get("id", "?")
        a, b = edge.get("a"), edge.get("b")
        if a is None or b is None:
            error(f"spatial edge {edge_id} lacks endpoint a/b")
            continue
        a, b = str(a), str(b)
        start, end = interval(edge)
        if start >= end:
            error(f"spatial edge {edge_id} has invalid validity interval")
        distance = as_num(edge.get("distance"))
        if distance is not None and distance < 0:
            error(f"spatial edge {edge_id} has negative distance")
        min_time = as_num(edge.get("min_travel_time"))
        if min_time is not None and min_time < 0:
            error(f"spatial edge {edge_id} has negative min_travel_time")
        d_ab = edge.get("direction_a_to_b")
        d_ba = edge.get("direction_b_to_a")
        if isinstance(d_ab, str) and isinstance(d_ba, str):
            expected = inverse_direction.get(d_ab.lower())
            if expected and d_ba.lower() != expected:
                error(
                    f"spatial direction mismatch: edge {edge_id} says {a}->{b}={d_ab} but {b}->{a}={d_ba}"
                )
        key = tuple(sorted((a, b)))
        by_pair.setdefault(key, []).append(edge)

    for pair, records in by_pair.items():
        for i, left in enumerate(records):
            ls, le = interval(left)
            for right in records[i + 1 :]:
                rs, re = interval(right)
                if not overlaps(ls, le, rs, re):
                    continue
                if left.get("allow_overlap", False) or right.get("allow_overlap", False):
                    continue
                compared = ("distance", "min_travel_time", "passable", "direction_a_to_b", "direction_b_to_a")
                if any(left.get(k) != right.get(k) for k in compared):
                    error(
                        f"spatial edge overlap: {pair[0]}<->{pair[1]} has conflicting states "
                        f"in {left.get('id','?')} and {right.get('id','?')}"
                    )

    scene_packets_raw = data.get("scene_packets", []) or []
    scene_packets: list[dict[str, Any]] = [x for x in scene_packets_raw if isinstance(x, dict)]
    actor_scenes: dict[str, list[dict[str, Any]]] = {}
    object_scenes: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}

    frame_required = {"left_of", "right_of", "in_front_of", "behind"}

    for scene in scene_packets:
        scene_id = str(scene.get("id", "?"))
        start = as_num(scene.get("start"))
        end = as_num(scene.get("end"))
        location = scene.get("location")
        if start is None or end is None or start > end:
            error(f"scene packet {scene_id} lacks a valid numeric start/end", code="scene.invalid_time", scene_ids=[scene_id])
        if location is None:
            error(f"scene packet {scene_id} lacks global location", code="scene.missing_location", scene_ids=[scene_id])
        status = scene.get("status")
        if status == "committed" and scene.get("sync_complete") is not True:
            error(f"scene packet {scene_id} is committed but sync_complete is not true", code="scene.sync_incomplete", scene_ids=[scene_id])

        chars = scene.get("characters", []) or []
        if not isinstance(chars, list):
            error(f"scene packet {scene_id} characters must be a list", code="scene.characters_shape", scene_ids=[scene_id])
            chars = []
        for char in chars:
            if not isinstance(char, dict) or char.get("id") is None:
                warn(f"scene packet {scene_id} contains invalid character record", code="scene.character_record", scene_ids=[scene_id])
                continue
            actor_scenes.setdefault(str(char["id"]), []).append(scene)

        objs = scene.get("objects", []) or []
        if not isinstance(objs, list):
            error(f"scene packet {scene_id} objects must be a list", code="scene.objects_shape", scene_ids=[scene_id])
            objs = []
        for obj in objs:
            if not isinstance(obj, dict) or obj.get("id") is None:
                warn(f"scene packet {scene_id} contains invalid object record", code="scene.object_record", scene_ids=[scene_id])
                continue
            object_scenes.setdefault(str(obj["id"]), []).append((scene, obj))

        rels = scene.get("spatial_relations", []) or []
        if not isinstance(rels, list):
            error(f"scene packet {scene_id} spatial_relations must be a list", code="scene.spatial_relations_shape", scene_ids=[scene_id])
            rels = []
        for rel in rels:
            if not isinstance(rel, dict):
                continue
            relation = str(rel.get("relation", ""))
            if relation in frame_required and not rel.get("frame"):
                error(
                    f"spatial reference-frame ambiguity: scene {scene_id} relation {relation} "
                    f"for {rel.get('subject','?')} vs {rel.get('object','?')} lacks frame",
                    code="scene.reference_frame_ambiguity",
                    scene_ids=[scene_id],
                )

    for actor, scenes in actor_scenes.items():
        scenes = sorted(scenes, key=lambda x: as_num(x.get("start")) if as_num(x.get("start")) is not None else float("inf"))
        for prev, nxt in zip(scenes, scenes[1:]):
            p_end = as_num(prev.get("end"))
            n_start = as_num(nxt.get("start"))
            if p_end is None or n_start is None:
                continue
            p_loc, n_loc = prev.get("location"), nxt.get("location")
            if p_loc is None or n_loc is None:
                continue
            p_loc, n_loc = str(p_loc), str(n_loc)
            if n_start < p_end and p_loc != n_loc:
                error(
                    f"scene overlap: {actor} is in {p_loc} ({prev.get('id','?')}) until {p_end} "
                    f"but appears in {n_loc} ({nxt.get('id','?')}) at {n_start}",
                    code="scene.actor_overlap",
                    scene_ids=[str(prev.get("id", "?")), str(nxt.get("id", "?"))],
                )
                continue
            if p_loc == n_loc or nxt.get("allow_unmodeled_travel", False):
                continue
            min_time = shortest_travel_time(spatial_edges, p_loc, n_loc, p_end)
            if min_time is None:
                warn(
                    f"unmodeled travel: no passable spatial path recorded for {actor} from {p_loc} "
                    f"after {prev.get('id','?')} to {n_loc} before {nxt.get('id','?')}",
                    code="scene.unmodeled_travel",
                    scene_ids=[str(prev.get("id", "?")), str(nxt.get("id", "?"))],
                )
            elif n_start - p_end < min_time:
                error(
                    f"impossible travel: {actor} has {n_start - p_end:g} time units between {p_loc} "
                    f"and {n_loc}, but modeled minimum is {min_time:g}",
                    code="scene.impossible_travel",
                    scene_ids=[str(prev.get("id", "?")), str(nxt.get("id", "?"))],
                )

    for item, records in object_scenes.items():
        records = sorted(records, key=lambda pair: as_num(pair[0].get("start")) if as_num(pair[0].get("start")) is not None else float("inf"))
        for (prev_scene, prev_obj), (next_scene, next_obj) in zip(records, records[1:]):
            prev_holder = prev_obj.get("exit_holder", prev_obj.get("entry_holder"))
            next_holder = next_obj.get("entry_holder")
            prev_loc = prev_obj.get("exit_location", prev_obj.get("entry_location"))
            next_loc = next_obj.get("entry_location")
            holder_changed = prev_holder is not None and next_holder is not None and prev_holder != next_holder
            loc_changed = prev_loc is not None and next_loc is not None and prev_loc != next_loc
            if (holder_changed or loc_changed) and not (
                prev_obj.get("transition_explained", False)
                or next_obj.get("transition_explained", False)
                or next_scene.get("allow_unmodeled_object_transfer", False)
            ):
                error(
                    f"object continuity mismatch: {item} exits {prev_scene.get('id','?')} at "
                    f"holder/location {prev_holder!r}/{prev_loc!r} but enters {next_scene.get('id','?')} at "
                    f"{next_holder!r}/{next_loc!r} without an explained transfer",
                    code="scene.object_continuity",
                    scene_ids=[str(prev_scene.get("id", "?")), str(next_scene.get("id", "?"))],
                )

    current_chapter = data.get("current_chapter")
    if isinstance(current_chapter, (int, float)):
        for rec in data.get("setups", []) or []:
            if not isinstance(rec, dict) or rec.get("status") not in {"open", "partial", "transformed"}:
                continue
            last = rec.get("last_reactivated_chapter")
            max_dormancy = rec.get("max_dormancy")
            if isinstance(last, (int, float)) and isinstance(max_dormancy, (int, float)):
                if current_chapter - last > max_dormancy:
                    warn(
                        f"setup dormancy: {rec.get('id','?')} has been quiet for "
                        f"{current_chapter - last} chapters (limit {max_dormancy})"
                    )

    current_day = data.get("current_day")
    if isinstance(current_day, (int, float)):
        for rec in data.get("offscreen_processes", []) or []:
            if not isinstance(rec, dict) or rec.get("status") not in {"active", "adapting", "latent"}:
                continue
            last = rec.get("last_update_day")
            max_stale = rec.get("max_staleness")
            if isinstance(last, (int, float)) and isinstance(max_stale, (int, float)):
                if current_day - last > max_stale:
                    warn(
                        f"offscreen staleness: {rec.get('id','?')} has not been reviewed for "
                        f"{current_day - last} days (limit {max_stale})"
                    )

    for branch in data.get("branches", []) or []:
        if not isinstance(branch, dict):
            continue
        expected = branch.get("invariants_expected") or {}
        observed = branch.get("invariants_observed") or {}
        authorized = set(branch.get("authorized_changes") or [])
        if not isinstance(expected, dict) or not isinstance(observed, dict):
            warn(f"branch invariant maps invalid: {branch.get('id','?')}")
            continue
        for key, value in expected.items():
            if key in observed and observed[key] != value and key not in authorized:
                error(
                    f"branch invariant drift: {branch.get('id','?')} key {key!r} expected {value!r}, "
                    f"observed {observed[key]!r}"
                )

    open_report = validate_open_issue_state(data)
    for msg in open_report.get("errors", []):
        error(str(msg), code="open_issue.violation")
    for msg in open_report.get("warnings", []):
        warn(str(msg), code="open_issue.review_required")

    return issues


def validate(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Backward-compatible string-list view used by existing CLI/tool callers."""
    issues = validate_issues(data)
    errors = [str(x.get("message", "")) for x in issues if x.get("severity") == "error"]
    warnings = [str(x.get("message", "")) for x in issues if x.get("severity") == "warning"]
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate long-form fiction story-state JSON")
    parser.add_argument("state", type=Path, help="Path to story-state JSON file")
    args = parser.parse_args()

    try:
        data = load_json(args.state)
        errors, warnings = validate(data)
    except Exception as exc:
        print(f"ERROR: could not validate state: {exc}", file=sys.stderr)
        return 2

    for msg in warnings:
        print(f"WARNING: {msg}")
    for msg in errors:
        print(f"ERROR: {msg}")

    print(f"summary: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
