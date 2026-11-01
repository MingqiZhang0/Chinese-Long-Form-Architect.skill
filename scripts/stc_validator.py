#!/usr/bin/env python3
"""Independent deterministic validator for STC v0.1 semantic conformance.

This module deliberately does not import the STC generator. It validates frozen
challenge artifacts and arbitrary candidate trajectories from the public STC
contract only.
"""
from __future__ import annotations

import argparse
import copy
import functools
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from capability_probe import CapabilityError, require_profile

ROOT = Path(__file__).resolve().parent.parent
CHALLENGE_SCHEMA = ROOT / "assets" / "intensity-schemas" / "stc-challenge.schema.json"
CANDIDATE_SCHEMA = ROOT / "assets" / "intensity-schemas" / "stc-candidate.schema.json"
VERSION = "0.1.1"


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@functools.lru_cache(maxsize=4)
def _schema_validator(path_text: str):
    require_profile("stc")
    from jsonschema import Draft202012Validator
    schema = json.loads(Path(path_text).read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _schema_errors(value: Any, path: Path) -> list[str]:
    rows = sorted(_schema_validator(str(path)).iter_errors(value), key=lambda e: list(e.absolute_path))
    out: list[str] = []
    for err in rows:
        where = ".".join(str(x) for x in err.absolute_path) or "$"
        out.append(f"{where}: {err.message}")
    return out


def effective_holder(entity: str, holders: dict[str, str], containment: dict[str, str]) -> tuple[str | None, list[str]]:
    seen: list[str] = []
    current = entity
    while current in containment:
        if current in seen:
            return None, seen + [current]
        seen.append(current)
        current = containment[current]
    if current in seen:
        return None, seen + [current]
    return holders.get(current), seen + [current]


def effective_location(entity: str, actor_locations: dict[str, str], holders: dict[str, str], containment: dict[str, str]) -> tuple[str | None, list[str]]:
    if entity in actor_locations:
        return actor_locations[entity], [entity]
    holder, chain = effective_holder(entity, holders, containment)
    if holder is None:
        return None, chain
    if holder in actor_locations:
        return actor_locations[holder], chain + [holder]
    # v0.1 allows nested containers; recurse if the holder itself is an entity.
    loc, tail = effective_location(holder, actor_locations, holders, containment)
    return loc, chain + tail


def route_active_interval(route: dict[str, Any], start: int, end: int, overrides: dict[str, bool]) -> bool:
    if overrides.get(route["id"]) is False:
        return False
    if start < int(route["valid_from_time"]):
        return False
    valid_to = route["valid_to_time"]
    if valid_to is not None and end > int(valid_to):
        return False
    return True


def historical_state(challenge: dict[str, Any], at_time: int) -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, bool], list[str]]:
    actors = dict(challenge["initial_state"]["actor_locations"])
    holders = dict(challenge["initial_state"]["entity_holders"])
    containment = dict(challenge["initial_state"]["containment"])
    overrides: dict[str, bool] = {}
    errors: list[str] = []
    route_ids = {r["id"] for r in challenge["routes"]}
    for event in sorted(challenge["events"], key=lambda row: (int(row["story_time"]), int(row["chapter"]))):
        if int(event["story_time"]) > at_time:
            break
        kind = event["kind"]
        if kind == "transfer":
            entity = event.get("entity")
            frm = event.get("from_holder")
            to = event.get("to_holder")
            if not entity or not frm or not to:
                errors.append(f"malformed transfer event at story_time {event['story_time']}")
                continue
            if entity in containment:
                errors.append(f"history attempts direct transfer of contained entity {entity}")
                continue
            if holders.get(entity) != frm:
                errors.append(f"transfer history invalid for {entity}: expected holder {frm}, found {holders.get(entity)}")
                continue
            holders[entity] = to
        elif kind == "move-actor":
            actor = event.get("actor")
            loc = event.get("location")
            if not actor or not loc:
                errors.append(f"malformed move-actor event at story_time {event['story_time']}")
                continue
            actors[actor] = loc
        elif kind in {"route-close", "route-open"}:
            rid = event.get("route")
            if rid not in route_ids:
                errors.append(f"event references unknown route {rid}")
                continue
            overrides[str(rid)] = kind == "route-open"
    return actors, holders, containment, overrides, errors


def _timepoint_constraints(challenge: dict[str, Any]) -> tuple[list[str], bool]:
    errors: list[str] = []
    anchors = challenge["story_time_anchors"]
    constraints = challenge["temporal_constraints"]
    for row in constraints:
        a, b = row["from"], row["to"]
        if a not in anchors or b not in anchors:
            errors.append(f"temporal constraint references unknown timepoint: {a}->{b}")
            continue
        lo, hi = int(row["min_delta"]), int(row["max_delta"])
        if lo > hi:
            errors.append(f"temporal constraint inverted: {a}->{b} min={lo} max={hi}")
            continue
        delta = int(anchors[b]) - int(anchors[a])
        if delta < lo or delta > hi:
            errors.append(f"temporal constraint violated: {a}->{b} delta={delta} not in [{lo},{hi}]")

    # Independent STN consistency check using difference-constraint negative-cycle detection.
    nodes = list(anchors)
    edges: list[tuple[str, str, int]] = []
    for row in constraints:
        a, b = row["from"], row["to"]
        if a not in anchors or b not in anchors:
            continue
        lo, hi = int(row["min_delta"]), int(row["max_delta"])
        edges.append((a, b, hi))      # t_b <= t_a + hi
        edges.append((b, a, -lo))     # t_a <= t_b - lo
    dist = {node: 0 for node in nodes}
    consistent = True
    for _ in range(max(0, len(nodes) - 1)):
        changed = False
        for u, v, w in edges:
            if dist[v] > dist[u] + w:
                dist[v] = dist[u] + w
                changed = True
        if not changed:
            break
    for u, v, w in edges:
        if dist[v] > dist[u] + w:
            consistent = False
            break
    if not consistent:
        errors.append("temporal constraint network has a negative cycle")
    return errors, consistent


def _known_surface_ids(challenge: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    state = challenge["initial_state"]
    ids.update(state["actor_locations"].keys())
    ids.update(state["actor_locations"].values())
    ids.update(state["entity_holders"].keys())
    ids.update(state["entity_holders"].values())
    ids.update(state["containment"].keys())
    ids.update(state["containment"].values())
    for route in challenge["routes"]:
        ids.update([route["id"], route["from"], route["to"]])
        if route.get("requires_entity"):
            ids.add(route["requires_entity"])
    return {x for x in ids if isinstance(x, str)}


def _reverse_labels(challenge: dict[str, Any], surface: str) -> dict[str, str]:
    if surface not in challenge["surface_views"]:
        raise ValueError(f"unknown surface: {surface}")
    labels = challenge["surface_views"][surface]["labels"]
    reverse: dict[str, str] = {}
    for latent, visible in labels.items():
        if visible in reverse and reverse[visible] != latent:
            raise ValueError(f"surface {surface} is not injective: {visible!r}")
        reverse[visible] = latent
    return reverse


def normalize_candidate(challenge: dict[str, Any], candidate: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors = _schema_errors(candidate, CANDIDATE_SCHEMA)
    if errors:
        return candidate, errors
    if candidate["challenge_id"] != challenge["challenge_id"]:
        errors.append(f"candidate challenge_id {candidate['challenge_id']} does not match {challenge['challenge_id']}")
        return candidate, errors
    surface = candidate.get("surface")
    if not surface:
        return copy.deepcopy(candidate), errors
    try:
        reverse = _reverse_labels(challenge, str(surface))
    except ValueError as exc:
        return candidate, [str(exc)]
    out = copy.deepcopy(candidate)
    out["surface"] = None
    for action in out["actions"]:
        for key in ("actor", "route", "entity", "from_holder", "to_holder"):
            value = action.get(key)
            if value is None:
                continue
            if value not in reverse:
                errors.append(f"surface candidate token {value!r} for {key} has no latent mapping")
            else:
                action[key] = reverse[value]
    return out, errors


def render_candidate(challenge: dict[str, Any], candidate: dict[str, Any], surface: str) -> dict[str, Any]:
    normalized, errors = normalize_candidate(challenge, candidate)
    if errors:
        raise ValueError("candidate invalid: " + "; ".join(errors))
    labels = challenge["surface_views"][surface]["labels"]
    out = copy.deepcopy(normalized)
    out["surface"] = surface
    for action in out["actions"]:
        for key in ("actor", "route", "entity", "from_holder", "to_holder"):
            value = action.get(key)
            if value is not None:
                action[key] = labels.get(value, value)
    return out


def _probe_results(challenge: dict[str, Any], trace: list[dict[str, Any]], final: dict[str, Any], candidate_errors: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for probe in challenge["probe_obligations"]:
        binding = probe["binding"]
        kind = binding["kind"]
        status = "FAILED"
        detail = ""
        if kind == "deadline":
            ok = final["end_time"] <= challenge["mission"]["deadline_time"] and not any("deadline" in e for e in candidate_errors)
            status = "SATISFIED" if ok else "FAILED"
            detail = f"end_time={final['end_time']} deadline={challenge['mission']['deadline_time']}"
        elif kind == "containment-propagation":
            entity = binding.get("entity")
            container = binding.get("container")
            actor = binding.get("actor")
            chain = []
            cur = entity
            containment = final["containment"]
            while cur in containment and cur not in chain:
                chain.append(cur)
                cur = containment[cur]
            holder = final["effective_holders"].get(entity)
            ok = container in chain + ([cur] if cur else []) and holder == actor
            status = "SATISFIED" if ok else "FAILED"
            detail = f"entity={entity} container={container} effective_holder={holder}"
        elif kind == "route-access":
            route = binding.get("route")
            entity = binding.get("entity")
            actor = binding.get("actor")
            matching = [row for row in trace if row.get("kind") == "move" and row.get("route") == route]
            if matching:
                ok = all(row.get("access_entity") in (None, entity) and row.get("access_holder") in (None, actor) for row in matching)
                status = "SATISFIED" if ok else "FAILED"
                detail = f"route={route} exercised={len(matching)}"
            else:
                status = "FAILED" if probe["coverage_class"] == "required" else "NOT_EXERCISED"
                detail = f"route={route} not used"
        out.append({"probe_id": probe["probe_id"], "from": probe["lifecycle"], "status": status, "detail": detail})
    return out


def validate_candidate(challenge: dict[str, Any], candidate: dict[str, Any], *, challenge_prevalidated: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not challenge_prevalidated:
        ch_errors, ch_warnings, _ = validate_challenge(challenge, verify_hashes=True, validate_witness=False)
        errors.extend(f"challenge: {e}" for e in ch_errors)
        warnings.extend(ch_warnings)
        if errors:
            return {"passed": False, "errors": errors, "warnings": warnings}

    normalized, cand_errors = normalize_candidate(challenge, candidate)
    errors.extend(cand_errors)
    if cand_errors:
        return {"passed": False, "errors": errors, "warnings": warnings}

    mission = challenge["mission"]
    actors, holders, containment, overrides, hist_errors = historical_state(challenge, int(mission["start_time"]))
    errors.extend(hist_errors)
    actor = mission["actor"]
    if actors.get(actor) != mission["start_location"]:
        errors.append(f"mission actor starts at {actors.get(actor)}, expected {mission['start_location']}")
    routes = {r["id"]: r for r in challenge["routes"]}
    now = int(mission["start_time"])
    trace: list[dict[str, Any]] = []

    for idx, action in enumerate(normalized["actions"], 1):
        kind = action["kind"]
        if kind == "move":
            a = action.get("actor")
            rid = action.get("route")
            route = routes.get(rid)
            if route is None:
                errors.append(f"candidate[{idx}] unknown route {rid}")
                continue
            if a != actor:
                errors.append(f"candidate[{idx}] only mission actor {actor} may move in STC v0.1")
                continue
            if actors.get(a) != route["from"]:
                errors.append(f"candidate[{idx}] actor at {actors.get(a)}, route starts {route['from']}")
                continue
            duration = int(route["min_travel_time"])
            end = now + duration
            if not route_active_interval(route, now, end, overrides):
                errors.append(f"candidate[{idx}] uses inactive route {rid} over [{now},{end}]")
                continue
            req = route.get("requires_entity")
            access_holder = None
            if req is not None:
                access_holder, chain = effective_holder(req, holders, containment)
                if access_holder != a:
                    errors.append(f"candidate[{idx}] route {rid} requires effective custody of {req} by {a}; holder={access_holder}; chain={chain}")
                    continue
            actors[a] = route["to"]
            trace.append({"index": idx, "kind": "move", "route": rid, "start_time": now, "end_time": end, "access_entity": req, "access_holder": access_holder})
            now = end
        elif kind == "transfer":
            entity = action.get("entity")
            frm = action.get("from_holder")
            to = action.get("to_holder")
            if not entity or not frm or not to:
                errors.append(f"candidate[{idx}] malformed transfer")
                continue
            if entity in containment:
                errors.append(f"candidate[{idx}] cannot directly transfer contained entity {entity}; transfer its containing chain")
                continue
            if holders.get(entity) != frm:
                errors.append(f"candidate[{idx}] {entity} not directly held by {frm}; found {holders.get(entity)}")
                continue
            if frm not in actors or to not in actors:
                errors.append(f"candidate[{idx}] v0.1 transfer holders must be actors")
                continue
            if actors[frm] != actors[to]:
                errors.append(f"candidate[{idx}] transfer actors are not co-located")
                continue
            duration = int(action.get("minutes", 0))
            holders[entity] = to
            trace.append({"index": idx, "kind": "transfer", "entity": entity, "from_holder": frm, "to_holder": to, "start_time": now, "end_time": now + duration})
            now += duration
        elif kind == "wait":
            minutes = int(action.get("minutes", 0))
            trace.append({"index": idx, "kind": "wait", "start_time": now, "end_time": now + minutes})
            now += minutes

    if now > int(mission["deadline_time"]):
        errors.append(f"candidate deadline exceeded: end_time={now} deadline={mission['deadline_time']}")
    if actors.get(actor) != mission["target_location"]:
        errors.append(f"candidate ends actor at {actors.get(actor)}, expected {mission['target_location']}")
    required = mission.get("required_entity_at_end")
    effective_holders: dict[str, str | None] = {}
    all_entities = set(holders) | set(containment)
    for entity in sorted(all_entities):
        holder, _ = effective_holder(entity, holders, containment)
        effective_holders[entity] = holder
    if required is not None and effective_holders.get(required) != actor:
        errors.append(f"candidate ends {required} with effective holder {effective_holders.get(required)}, expected {actor}")

    final = {
        "elapsed_minutes": now - int(mission["start_time"]),
        "end_time": now,
        "actor_locations": actors,
        "entity_holders": holders,
        "containment": containment,
        "effective_holders": effective_holders,
        "route_overrides": overrides,
    }
    probes = _probe_results(challenge, trace, final, errors)
    for probe, result in zip(challenge["probe_obligations"], probes):
        if probe["coverage_class"] == "required" and result["status"] != "SATISFIED":
            errors.append(f"required probe {probe['probe_id']} terminal status {result['status']}")

    signature_payload = {
        "elapsed_minutes": final["elapsed_minutes"],
        "actor_locations": final["actor_locations"],
        "entity_holders": final["entity_holders"],
        "containment": final["containment"],
        "effective_holders": final["effective_holders"],
        "probe_statuses": {row["probe_id"]: row["status"] for row in probes},
    }
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "normalized_candidate": normalized,
        "trajectory_hash": canonical_hash(normalized["actions"]),
        "trace": trace,
        "final": final,
        "probe_results": probes,
        "semantic_signature": canonical_hash(signature_payload),
        "semantic_signature_payload": signature_payload,
    }


def _validate_probe_bindings(challenge: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    routes = {r["id"] for r in challenge["routes"]}
    actors = set(challenge["initial_state"]["actor_locations"])
    entities = set(challenge["initial_state"]["entity_holders"]) | set(challenge["initial_state"]["containment"])
    containers = set(challenge["initial_state"]["containment"].values())
    missions = {challenge["mission"]["mission_id"]}
    seen: set[str] = set()
    for probe in challenge["probe_obligations"]:
        pid = probe["probe_id"]
        if pid in seen:
            errors.append(f"duplicate probe_id: {pid}")
        seen.add(pid)
        b = probe["binding"]
        if b["kind"] == "deadline" and b.get("mission") not in missions:
            errors.append(f"probe {pid} binds unknown mission {b.get('mission')}")
        if b["kind"] == "route-access":
            if b.get("route") not in routes:
                errors.append(f"probe {pid} binds unknown route {b.get('route')}")
            if b.get("entity") not in entities:
                errors.append(f"probe {pid} binds unknown entity {b.get('entity')}")
            if b.get("actor") not in actors:
                errors.append(f"probe {pid} binds unknown actor {b.get('actor')}")
        if b["kind"] == "containment-propagation":
            if b.get("entity") not in entities:
                errors.append(f"probe {pid} binds unknown entity {b.get('entity')}")
            if b.get("container") not in containers:
                errors.append(f"probe {pid} binds unknown container {b.get('container')}")
            if b.get("actor") not in actors:
                errors.append(f"probe {pid} binds unknown actor {b.get('actor')}")
    return errors


def validate_challenge(challenge: dict[str, Any], *, verify_hashes: bool = True, validate_witness: bool = True) -> tuple[list[str], list[str], dict[str, Any]]:
    errors = _schema_errors(challenge, CHALLENGE_SCHEMA)
    warnings: list[str] = []
    details: dict[str, Any] = {"temporal_consistent": False, "witness": None, "continuations": []}
    if errors:
        return errors, warnings, details

    anchors = challenge["story_time_anchors"]
    chapters_seen: set[int] = set()
    for row in challenge["chapter_anchors"]:
        ch = int(row["chapter"])
        if ch in chapters_seen:
            errors.append(f"duplicate chapter anchor: {ch}")
        chapters_seen.add(ch)

    for event in challenge["events"]:
        tp = event["timepoint"]
        if tp not in anchors:
            errors.append(f"event timepoint missing from story_time_anchors: {tp}")
        elif int(anchors[tp]) != int(event["story_time"]):
            errors.append(f"event {tp} story_time disagrees with anchor")
    mission = challenge["mission"]
    if anchors.get("T_MISSION") != mission["start_time"]:
        errors.append("mission start_time disagrees with T_MISSION")
    if anchors.get("T_DEADLINE") != mission["deadline_time"]:
        errors.append("mission deadline_time disagrees with T_DEADLINE")
    if int(mission["deadline_time"]) < int(mission["start_time"]):
        errors.append("mission deadline precedes mission start")

    time_errors, consistent = _timepoint_constraints(challenge)
    errors.extend(time_errors)
    details["temporal_consistent"] = consistent

    route_ids: set[str] = set()
    for route in challenge["routes"]:
        rid = route["id"]
        if rid in route_ids:
            errors.append(f"duplicate route id: {rid}")
        route_ids.add(rid)
        end = route["valid_to_time"]
        if end is not None and int(end) < int(route["valid_from_time"]):
            errors.append(f"route diegetic interval inverted: {rid}")

    state = challenge["initial_state"]
    actor_ids = set(state["actor_locations"])
    holders = state["entity_holders"]
    containment = state["containment"]
    for child in containment:
        if child in holders:
            errors.append(f"entity {child} cannot be both directly held and contained")
    # containment cycle and dangling parent checks
    known_entities = set(holders) | set(containment) | set(containment.values())
    for child, parent in containment.items():
        if parent not in known_entities:
            errors.append(f"containment parent {parent} for {child} is unknown")
        _, chain = effective_holder(child, holders, containment)
        if len(chain) != len(set(chain)):
            errors.append(f"containment cycle detected from {child}: {chain}")
    for entity, holder in holders.items():
        if holder not in actor_ids:
            errors.append(f"v0.1 direct holder for {entity} must be an actor; got {holder}")

    _, _, _, _, hist_errors = historical_state(challenge, int(mission["start_time"]))
    errors.extend(hist_errors)
    errors.extend(_validate_probe_bindings(challenge))

    needed = _known_surface_ids(challenge)
    for surface, data in challenge["surface_views"].items():
        labels = data["labels"]
        missing = sorted(needed - set(labels))
        if missing:
            errors.append(f"surface {surface} missing latent labels: {missing}")
        values = list(labels.values())
        if len(values) != len(set(values)):
            errors.append(f"surface {surface} has non-injective labels")

    if not errors and validate_witness:
        witness = {"candidate_version": VERSION, "challenge_id": challenge["challenge_id"], "surface": None, "actions": copy.deepcopy(challenge["witness"])}
        witness_report = validate_candidate(challenge, witness, challenge_prevalidated=True)
        details["witness"] = witness_report
        if not witness_report["passed"]:
            errors.extend(f"witness: {e}" for e in witness_report["errors"])

        cert_by_key = {(r["choice_id"], r["alternative_id"]): r for r in challenge["continuation_certificate"]["choice_results"]}
        expected_keys: set[tuple[str, str]] = set()
        for choice in challenge["controlled_choices"]:
            if int(choice["at_time"]) != int(mission["start_time"]):
                errors.append(f"controlled choice {choice['choice_id']} is not bound to mission start_time")
            for alt in choice["alternatives"]:
                key = (choice["choice_id"], alt["alternative_id"])
                expected_keys.add(key)
                actions = copy.deepcopy(alt["prefix"] + alt["continuation"])
                candidate = {"candidate_version": VERSION, "challenge_id": challenge["challenge_id"], "surface": None, "actions": actions}
                report = validate_candidate(challenge, candidate, challenge_prevalidated=True)
                details["continuations"].append({"choice_id": key[0], "alternative_id": key[1], "report": report})
                if not report["passed"]:
                    errors.extend(f"continuation {key[0]}/{key[1]}: {e}" for e in report["errors"])
                    continue
                cert = cert_by_key.get(key)
                if cert is None:
                    errors.append(f"missing continuation certificate for {key[0]}/{key[1]}")
                    continue
                if cert["trajectory_hash"] != report["trajectory_hash"]:
                    errors.append(f"continuation certificate trajectory hash mismatch for {key[0]}/{key[1]}")
                if int(cert["expected_elapsed_minutes"]) != int(report["final"]["elapsed_minutes"]):
                    errors.append(f"continuation certificate elapsed mismatch for {key[0]}/{key[1]}")
                req = mission.get("required_entity_at_end")
                actual_holder = report["final"]["effective_holders"].get(req) if req else None
                if cert["expected_required_entity_holder"] != actual_holder:
                    errors.append(f"continuation certificate required-entity holder mismatch for {key[0]}/{key[1]}")
        extra = set(cert_by_key) - expected_keys
        if extra:
            errors.append(f"continuation certificate contains unknown alternatives: {sorted(extra)}")

        # strict surface round-trip + behavioral conservation for the planted witness
        latent_sig = witness_report.get("semantic_signature")
        for surface in challenge["surface_views"]:
            try:
                surfaced = render_candidate(challenge, witness, surface)
                restored, rt_errors = normalize_candidate(challenge, surfaced)
                if rt_errors:
                    errors.extend(f"surface {surface} round-trip: {e}" for e in rt_errors)
                    continue
                if restored["actions"] != witness["actions"]:
                    errors.append(f"surface {surface} candidate round-trip changed latent actions")
                report = validate_candidate(challenge, surfaced, challenge_prevalidated=True)
                if not report["passed"]:
                    errors.extend(f"surface {surface} candidate: {e}" for e in report["errors"])
                elif report.get("semantic_signature") != latent_sig:
                    errors.append(f"surface {surface} changed candidate behavioral semantics")
            except ValueError as exc:
                errors.append(f"surface {surface} round-trip failed: {exc}")

    if verify_hashes:
        cert = challenge["certificate"]
        latent = copy.deepcopy(challenge)
        latent.pop("surface_views", None)
        latent.pop("certificate", None)
        expected_latent = canonical_hash(latent)
        if cert["latent_world_hash"] != expected_latent:
            errors.append("certificate latent_world_hash mismatch")
        unhashed = copy.deepcopy(challenge)
        unhashed["certificate"]["challenge_hash"] = ""
        expected_challenge = canonical_hash(unhashed)
        if cert["challenge_hash"] != expected_challenge:
            errors.append("certificate challenge_hash mismatch")

    return errors, warnings, details


def render_agent_view(challenge: dict[str, Any], surface: str) -> dict[str, Any]:
    errors, _, _ = validate_challenge(challenge)
    if errors:
        raise ValueError("challenge invalid: " + "; ".join(errors))
    labels = challenge["surface_views"][surface]["labels"]
    mission = challenge["mission"]
    actors, holders, containment, overrides, hist_errors = historical_state(challenge, int(mission["start_time"]))
    if hist_errors:
        raise ValueError("history invalid: " + "; ".join(hist_errors))

    def lab(value: str | None) -> str | None:
        return labels.get(value, value) if value is not None else None

    routes = []
    for route in challenge["routes"]:
        routes.append({
            "name": lab(route["id"]),
            "from": lab(route["from"]),
            "to": lab(route["to"]),
            "min_travel_time": route["min_travel_time"],
            "active_at_mission_start": route_active_interval(route, int(mission["start_time"]), int(mission["start_time"]), overrides),
            "valid_from_time": route["valid_from_time"],
            "valid_to_time": route["valid_to_time"],
            "requires_entity": lab(route["requires_entity"]),
        })
    effective = {}
    for entity in sorted(set(holders) | set(containment)):
        holder, _ = effective_holder(entity, holders, containment)
        effective[lab(entity)] = lab(holder)
    return {
        "challenge_id": challenge["challenge_id"],
        "surface": surface,
        "narrative_chapter": mission["chapter"],
        "diegetic_window": {"start_time": mission["start_time"], "deadline_time": mission["deadline_time"]},
        "current_state": {
            "actor_locations": {lab(k): lab(v) for k, v in actors.items()},
            "entity_holders": {lab(k): lab(v) for k, v in holders.items()},
            "containment": {lab(k): lab(v) for k, v in containment.items()},
            "effective_holders": effective,
            "routes": routes,
        },
        "mission": {
            "actor": lab(mission["actor"]),
            "start_location": lab(mission["start_location"]),
            "target_location": lab(mission["target_location"]),
            "required_entity_at_end": lab(mission["required_entity_at_end"]),
        },
    }


def _emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("challenge", help="validate a frozen STC challenge")
    c.add_argument("challenge", type=Path)
    c.add_argument("--ignore-hashes", action="store_true")
    c.add_argument("--json", action="store_true")
    cand = sub.add_parser("candidate", help="validate an arbitrary candidate trajectory")
    cand.add_argument("challenge", type=Path)
    cand.add_argument("candidate", type=Path)
    cand.add_argument("--json", action="store_true")
    r = sub.add_parser("render", help="render an Agent-visible strict surface")
    r.add_argument("challenge", type=Path)
    r.add_argument("--surface", required=True)
    rt = sub.add_parser("roundtrip", help="verify strict surface candidate round-trip")
    rt.add_argument("challenge", type=Path)
    rt.add_argument("candidate", type=Path)
    rt.add_argument("--surface", required=True)
    rt.add_argument("--json", action="store_true")
    b = sub.add_parser("batch", help="validate many challenge/candidate/round-trip cases in one independent process")
    b.add_argument("bundle", type=Path)
    b.add_argument("--json", action="store_true")
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        require_profile("stc")
    except CapabilityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    challenge = None
    if args.cmd != "batch":
        challenge = json.loads(args.challenge.read_text(encoding="utf-8"))
    if args.cmd == "challenge":
        errors, warnings, details = validate_challenge(challenge, verify_hashes=not args.ignore_hashes)
        report = {
            "passed": not errors,
            "validator_version": VERSION,
            "errors": errors,
            "warnings": warnings,
            "temporal_consistent": details.get("temporal_consistent"),
            "witness_semantic_signature": (details.get("witness") or {}).get("semantic_signature") if isinstance(details.get("witness"), dict) else None,
            "continuation_count": len(details.get("continuations", [])),
        }
        if args.json:
            _emit(report)
        elif errors:
            for err in errors:
                print(f"ERROR: {err}", file=sys.stderr)
        else:
            print(f"OK: STC challenge valid; continuations={report['continuation_count']}; temporal_consistent={report['temporal_consistent']}")
        return 0 if not errors else 1
    if args.cmd == "candidate":
        errors, _, _ = validate_challenge(challenge, verify_hashes=True, validate_witness=False)
        if errors:
            report = {"passed": False, "errors": [f"challenge: {e}" for e in errors], "warnings": []}
        else:
            candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
            report = validate_candidate(challenge, candidate, challenge_prevalidated=True)
        if args.json:
            _emit(report)
        elif report["passed"]:
            print(f"OK: candidate valid; elapsed={report['final']['elapsed_minutes']} semantic_signature={report['semantic_signature']}")
        else:
            for err in report["errors"]:
                print(f"ERROR: {err}", file=sys.stderr)
        return 0 if report["passed"] else 1
    if args.cmd == "render":
        try:
            _emit(render_agent_view(challenge, args.surface))
            return 0
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
    if args.cmd == "roundtrip":
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        try:
            normalized, errs = normalize_candidate(challenge, candidate)
            if errs:
                raise ValueError("; ".join(errs))
            surfaced = render_candidate(challenge, normalized, args.surface)
            restored, rt_errors = normalize_candidate(challenge, surfaced)
            report = {
                "passed": not rt_errors and restored.get("actions") == normalized.get("actions"),
                "surface": args.surface,
                "errors": rt_errors,
                "latent_actions_hash": canonical_hash(normalized.get("actions")),
                "roundtrip_actions_hash": canonical_hash(restored.get("actions")),
                "surface_candidate": surfaced,
            }
        except ValueError as exc:
            report = {"passed": False, "surface": args.surface, "errors": [str(exc)]}
        if args.json:
            _emit(report)
        elif report["passed"]:
            print(f"OK: strict surface round-trip preserved candidate on {args.surface}")
        else:
            for err in report["errors"]:
                print(f"ERROR: {err}", file=sys.stderr)
        return 0 if report["passed"] else 1
    if args.cmd == "batch":
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
        rows: list[dict[str, Any]] = []
        overall = True
        for case in bundle.get("challenge_cases", []):
            errs, warns, details = validate_challenge(
                case["challenge"],
                verify_hashes=bool(case.get("verify_hashes", True)),
                validate_witness=bool(case.get("validate_witness", True)),
            )
            result = {
                "passed": not errs,
                "errors": errs,
                "warnings": warns,
                "temporal_consistent": details.get("temporal_consistent"),
                "witness_semantic_signature": (details.get("witness") or {}).get("semantic_signature") if isinstance(details.get("witness"), dict) else None,
                "continuation_count": len(details.get("continuations", [])),
            }
            rows.append({"case_id": case.get("case_id"), "kind": "challenge", "result": result})
            expected = bool(case.get("expected_pass", True))
            overall = overall and (bool(result["passed"]) == expected)
        for case in bundle.get("candidate_cases", []):
            ch = case["challenge"]
            if bool(case.get("validate_challenge", True)):
                ch_errs, ch_warns, _ = validate_challenge(ch, verify_hashes=bool(case.get("verify_hashes", True)), validate_witness=False)
            else:
                ch_errs, ch_warns = [], []
            if ch_errs:
                result = {"passed": False, "errors": [f"challenge: {e}" for e in ch_errs], "warnings": ch_warns}
            else:
                result = validate_candidate(ch, case["candidate"], challenge_prevalidated=True)
            rows.append({"case_id": case.get("case_id"), "kind": "candidate", "result": result})
            expected = bool(case.get("expected_pass", True))
            overall = overall and (bool(result.get("passed")) == expected)
        for case in bundle.get("roundtrip_cases", []):
            ch = case["challenge"]
            candidate = case["candidate"]
            surface = case["surface"]
            try:
                normalized, errs = normalize_candidate(ch, candidate)
                if errs:
                    raise ValueError("; ".join(errs))
                surfaced = render_candidate(ch, normalized, surface)
                restored, rt_errors = normalize_candidate(ch, surfaced)
                result = {
                    "passed": not rt_errors and restored.get("actions") == normalized.get("actions"),
                    "errors": rt_errors,
                    "surface": surface,
                    "latent_actions_hash": canonical_hash(normalized.get("actions")),
                    "roundtrip_actions_hash": canonical_hash(restored.get("actions")),
                    "surface_candidate": surfaced,
                }
            except ValueError as exc:
                result = {"passed": False, "errors": [str(exc)], "surface": surface}
            rows.append({"case_id": case.get("case_id"), "kind": "roundtrip", "result": result})
            expected = bool(case.get("expected_pass", True))
            overall = overall and (bool(result.get("passed")) == expected)
        report = {"passed": overall, "case_count": len(rows), "rows": rows}
        if args.json:
            _emit(report)
        else:
            print(f"OK: STC validator batch {'PASS' if overall else 'FAIL'} ({len(rows)} cases)")
        return 0 if overall else 1
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
