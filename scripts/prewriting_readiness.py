#!/usr/bin/env python3
"""Verify operational prewriting readiness without judging literary quality.

This checker belongs to the existing prewriting-readiness owner. It verifies that
risk activation decisions are explicit, activated artifacts are discoverable,
opening anchors are resolved when required, long-horizon projects have a
provisional volume decision plus a near-term chapter map, causally required
Scene Packets are actually wired into Writer context, and DRAFT_READY claims are
backed by a successful current context compilation and semantic-kernel pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import copy
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

from compile_context import allowed

try:
    import jsonschema
except Exception as exc:  # pragma: no cover
    jsonschema = None
    JSONSCHEMA_IMPORT_ERROR = exc
else:
    JSONSCHEMA_IMPORT_ERROR = None

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "assets" / "project-schemas" / "prewriting-readiness.schema.json"
PROJECT_OPS = ROOT / "scripts" / "project_ops.py"
COMPILER = ROOT / "scripts" / "compile_context.py"
KERNEL = ROOT / "scripts" / "semantic_kernel.py"

ARTIFACT_KINDS = {
    "world_model": "world-model",
    "character_state": "character-state",
    "knowledge_topology": "knowledge-topology",
    "hidden_causal_network": "hidden-causal-network",
    "long_horizon_architecture": "long-horizon-architecture",
    "timeline": "initial-world-timeline",
}

VERSION = "1.1.0"
CHAPTER_FIELDS = ("causal_function", "major_progression", "pressure", "decision", "revelation", "state_change", "exit_state", "incoming_interface", "outgoing_interface", "tension_phase")
WORLD_FIELDS = ("institutions", "ordinary_life", "space", "power", "information", "resources", "offscreen_autonomy", "social_countermeasures", "cultural_constraints")
SCENE_FIELDS = ("entry_state", "trigger", "local_transition", "rollback_or_branch", "retained_state", "reverted_state", "exit_state", "persistent_effects")
BASE_ARTIFACTS = ("project_brief", "project_poetics", "narrative_strategy", "author_mission", "writer_mission", "cast")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def file_hash(root: Path, ref: str) -> str:
    return hashlib.sha256(safe_path(root, ref).read_bytes()).hexdigest()


def substantive(value: Any) -> bool:
    """Check completion, never rate the literary meaning of a free-text answer."""
    if isinstance(value, dict) and value.get("status") == "NOT_APPLICABLE":
        return substantive(value.get("reason"))
    return isinstance(value, str) and bool(value.strip()) and not re.search(r"\b(TBD|TODO|PLACEHOLDER)\b|待定|待补|正文时再|choose later", value, re.I)


def user_evidence(root: Path, ref: Any, action: str) -> dict[str, Any]:
    """Imported transcript attestation. The CLI never creates human messages.

    Like existing campaign attestations, local files cannot authenticate a human;
    callers must import actual conversation evidence, never fabricate these fields.
    IDs/order/hash bindings prevent accidental reuse, not a malicious filesystem owner.
    """
    rec = load_json(safe_path(root, ref)) if isinstance(ref, str) and ref else {}
    if not isinstance(rec, dict) or rec.get("source") != "user" or rec.get("action") != action or not substantive(rec.get("statement")):
        raise ValueError(f"{action} requires imported explicit user-message evidence")
    if not substantive(rec.get("message_id")) or type(rec.get("message_order")) is not int or rec["message_order"] < 1:
        raise ValueError("user evidence needs a stable message_id and positive conversation message_order")
    return rec


def artifact_evidence(root: Path, r: dict[str, Any], findings: list, *, check_hashes: bool = True) -> dict[str, Any]:
    out = {}
    required = set(BASE_ARTIFACTS)
    required |= {k for k, v in r["risk_activation"].items() if v.get("decision") == "ACTIVE" and k != "scene_packets"}
    if r.get("causal_risks", {}).get("historical_grounding"):
        required.add("grounding")
    artifacts = r.get("artifacts", {})
    for kind in sorted(required):
        row = artifacts.get(kind, {})
        try:
            if row.get("status") != "MATURE_FOR_DRAFT":
                raise ValueError("requires evidence-backed MATURE_FOR_DRAFT")
            ref, eref = row["ref"], row["evidence_ref"]
            evidence = load_json(safe_path(root, eref))
            if not isinstance(evidence, dict):
                raise ValueError("structured evidence must be an object")
            if evidence.get("artifact_ref") != ref or evidence.get("open_items") != []:
                raise ValueError("evidence must bind the artifact_ref and close open_items")
            if not isinstance(evidence.get("coverage"), list) or not evidence["coverage"] or not all(substantive(x) for x in evidence["coverage"]):
                raise ValueError("requires concrete coverage statements")
            if not substantive(safe_path(root, ref).read_text(encoding="utf-8")):
                raise ValueError("artifact contains unresolved placeholders")
            decision = r["risk_activation"].get(kind)
            if decision and decision.get("artifact_ref") != ref:
                raise ValueError("maturity artifact does not match active risk artifact_ref")
            if check_hashes and (row.get("sha256") != file_hash(root, ref) or row.get("evidence_sha256") != file_hash(root, eref)):
                raise ValueError("maturity stale/missing: run --action refresh, then freeze and obtain fresh approval")
            out[kind] = evidence
        except Exception as exc:
            findings.append(issue("readiness.maturity." + kind, str(exc)))
    return out


def structural_evidence(root: Path, r: dict[str, Any], manifest: dict[str, Any], findings: list) -> None:
    def fail(code: str, message: str) -> None:
        findings.append(issue("readiness." + code, message))
    risks = r.get("causal_risks", {})
    if not isinstance(risks, dict) or not all(type(risks.get(k)) is bool for k in ("world_systems", "time_loop_or_branch", "historical_grounding", "secret_asymmetry")):
        fail("risk-evidence", "assess causal_risks explicitly; a scaffold INACTIVE default is not a risk decision")
        risks = {}
    forced = set()
    if risks.get("world_systems") or risks.get("time_loop_or_branch") or risks.get("historical_grounding"):
        forced.add("world_model")
    if risks.get("time_loop_or_branch"):
        forced |= {"scene_packets", "timeline", "knowledge_topology", "character_state"}
    if risks.get("secret_asymmetry"):
        forced.add("knowledge_topology")
    if r["risk_activation"]["hidden_causal_network"]["decision"] == "ACTIVE":
        forced.add("world_model")
    # Independent activation sentinels from the live project, not just self-report.
    subs = set(manifest.get("enabled_subsystems", []))
    if subs & {"branches", "semantic-revision"}:
        forced |= {"world_model", "scene_packets"}
    for key, kind in ARTIFACT_KINDS.items():
        if any(row.get("kind") == kind and str(row.get("status", "")).lower() == "active" for row in manifest.get("optional_artifacts", [])):
            forced.add(key)
    for k in forced:
        if r["risk_activation"][k]["decision"] != "ACTIVE":
            fail("risk-activation." + k, "causal risk requires ACTIVE " + k)
    for k, row in r["risk_activation"].items():
        if row.get("reason", "").startswith("Assess "):
            fail("risk-unassessed." + k, "replace neutral scaffold reason with a project-specific activation decision")
    ev = artifact_evidence(root, r, findings)
    for kind in ("project_poetics", "narrative_strategy"):
        validate_draft_dependencies(root, ev.get(kind, {}), findings)
    cast = ev.get("cast", {})
    centers = cast.get("narrative_centers")
    if centers is None and cast.get("central_character") is not None:
        centers = [cast["central_character"]]
    characters = cast.get("characters", [])
    if not isinstance(characters, list):
        characters = []
    ids = [c.get("id") for c in characters if isinstance(c, dict)]
    by_id = {c.get("id"): c for c in characters if isinstance(c, dict)}
    if len(ids) != len(characters) or len(set(ids)) != len(ids) or any(not substantive(x) for x in ids):
        fail("cast-identities", "Cast must contain unique character IDs")
    if not isinstance(centers, list) or not centers or len(set(centers)) != len(centers) or any(c not in by_id for c in centers):
        fail("cast-centers", "narrative_centers[] (or legacy central_character) must resolve to real roster entries")
        centers = []
    appearing = cast.get("opening_character_ids", [])
    if not isinstance(appearing, list) or not appearing or any(c not in by_id for c in appearing):
        fail("cast-opening", "declare actual important opening characters in the roster")
        appearing = []
    for cid in set(centers + appearing):
        c = by_id[cid]
        if not all(substantive(c.get(k)) for k in ("identity", "social_position", "life_anchor")) or c.get("state_scope") not in {"long-term", "scene-local"}:
            fail("cast-anchors", f"{cid} needs identity, social position, life anchor, and explicit state_scope")
        if c.get("state_scope") == "long-term" and r["risk_activation"]["character_state"]["decision"] != "ACTIVE":
            fail("cast-state", f"{cid} needs separate active Character State; roster is not its state projection")
        elif c.get("state_scope") == "long-term":
            states = ev.get("character_state", {}).get("states", [])
            if not isinstance(states, list) or not any(isinstance(s, dict) and s.get("character_id") == cid and substantive(s.get("current_state")) for s in states):
                fail("cast-state", f"{cid} requires an actual separate current-state evidence entry")
    if "world_model" in ev:
        world = ev["world_model"]
        if not all(substantive(world.get(k)) for k in WORLD_FIELDS):
            fail("world-coverage", "World evidence needs current-cone institutions/life/space/power/information/resources/autonomy/counters/culture; irrelevant items may carry justified NOT_APPLICABLE")
    if "writer_mission" in ev and ev["writer_mission"].get("target_chapter") != r["target_chapter"]:
        fail("mission-target", "Writer Mission evidence must target the current chapter")
    for kind in ("project_brief", "project_poetics"):
        if r.get("artifacts", {}).get(kind, {}).get("ref") != manifest.get("canonical_paths", {}).get(kind):
            fail("authority-artifact", f"{kind} evidence must bind the canonical manifest owner")
    if "grounding" in ev:
        claims = ev["grounding"].get("dependencies", [])
        if not isinstance(claims, list) or not claims:
            fail("grounding", "historical grounding requires scoped adopted dependencies")
        else:
            for c in claims:
                try:
                    if c.get("status") != "VERIFIED" or not substantive(c.get("scope")) or not substantive(c.get("source")) or not substantive(c.get("constraint")):
                        raise ValueError("dependency needs VERIFIED source, scope, and adopted constraint")
                    if file_hash(root, c["ref"]) != c["sha256"]:
                        raise ValueError("grounding source snapshot stale")
                except Exception as exc:
                    fail("grounding", str(exc))
    override = r.get("draft_mode", "NORMAL") == "FRAGMENTARY_OVERRIDE"
    if override:
        try:
            validate_override(root, r)
        except Exception as exc:
            fail("override", str(exc))
    # A normal substantial Chapter 1 must have a volume contract, even if the
    # project has a thin/quiet literary architecture and one continuous volume.
    if not override:
        if r["risk_activation"]["long_horizon_architecture"]["decision"] != "ACTIVE":
            fail("volume-activation", "normal substantial long-form drafting requires active volume/chapter preparation")
        validate_volumes(root, r, findings)


def validate_draft_dependencies(root: Path, evidence: dict[str, Any], findings: list) -> None:
    """Verify declared planning dependencies, never infer a literary regime.

    Optional on legacy evidence. Planner/author identifies consequential choices;
    the checker verifies completion and bounded openness, not their meanings.
    """
    rows = evidence.get("draft_dependencies", [])
    if not isinstance(rows, list):
        findings.append(issue("readiness.poetics-dependency", "draft_dependencies must be a list"))
        return
    ids = set()
    for row in rows:
        try:
            if not isinstance(row, dict) or not substantive(row.get("id")) or row["id"] in ids:
                raise ValueError("dependency needs a unique id")
            ids.add(row["id"])
            if type(row.get("required_for_draft")) is not bool or not substantive(row.get("reason")):
                raise ValueError("declare draft applicability and project-specific reason")
            handling = row.get("handling")
            if handling not in {"decided", "preserve-open", "not-applicable", "unresolved"}:
                raise ValueError("unknown dependency handling")
            if handling == "not-applicable":
                if row["required_for_draft"]:
                    raise ValueError("a required dependency cannot be not-applicable")
                continue
            if handling == "unresolved":
                if row["required_for_draft"]:
                    raise ValueError("required choice remains unresolved")
                continue
            ref = row.get("evidence_ref")
            if not isinstance(ref, str) or not substantive(safe_path(root, ref).read_text(encoding="utf-8")):
                raise ValueError("completed dependency needs substantive evidence")
            if handling == "preserve-open":
                if row["required_for_draft"]:
                    raise ValueError("a choice required as a decided answer cannot be preserve-open")
                if not substantive(row.get("compatibility_boundary")):
                    raise ValueError("preserve-open needs a stable current-volume compatibility boundary")
        except Exception as exc:
            findings.append(issue("readiness.poetics-dependency", str(exc)))


def validate_volumes(root: Path, r: dict[str, Any], findings: list) -> None:
    try:
        ref = r["long_horizon"]["volume_evidence_ref"]
        v = load_json(safe_path(root, ref))
        authority = user_evidence(root, v["author_decision_ref"], "volume-plan")
        count = v["planned_volume_count"]
        structural_choice = {"planned_volume_count": count, "later_volumes": v.get("later_volumes")}
        bound_choice = authority.get("structure_sha256") == digest(structural_choice)
        bound_full_plan = authority.get("plan_sha256") == digest({k: val for k, val in v.items() if k != "author_decision_ref"})
        if type(count) is not int or count < 1 or authority.get("planned_volume_count") != count or not (bound_choice or bound_full_plan):
            raise ValueError("volume count/plan requires hash-bound author structural decision; agent cannot declare single/two-volume exemptions")
        volumes = v["volumes"]
        if not isinstance(volumes, list) or [x.get("number") for x in volumes] != list(range(1, count + 1)):
            raise ValueError("actual ordered volume entries must match declared count")
        first = volumes[0]
        chapter_numbers = first["planned_chapters"]
        chapters = first["chapters"]
        if not isinstance(chapter_numbers, list) or not chapter_numbers or any(type(n) is not int or n < 1 for n in chapter_numbers) or chapter_numbers != sorted(set(chapter_numbers)) or chapter_numbers != list(range(1, max(chapter_numbers) + 1)):
            raise ValueError("first-volume planned_chapters must enumerate the complete contiguous chapter range from 1")
        if not isinstance(chapters, list) or [c.get("number") for c in chapters] != chapter_numbers:
            raise ValueError("first-volume actual chapter evidence must match every planned chapter; counts alone do not qualify")
        if len({c.get("id") for c in chapters}) != len(chapters) or any(not substantive(c.get("id")) or not all(substantive(c.get(k)) for k in CHAPTER_FIELDS) for c in chapters):
            raise ValueError("each first-volume chapter needs unique id and complete causal/contribution/interface evidence without large TBDs")
        for vol in volumes[1:]:
            fields = ("inherited_state", "core_pressure", "development_direction", "structural_change", "exit_direction") if vol["number"] == 2 else ("long_term_function", "development_direction", "reason_for_volume", "interfaces")
            if not all(substantive(vol.get(k)) for k in fields):
                raise ValueError(f"volume {vol['number']} lacks required direction evidence")
        if v.get("later_volumes") != "NOT_APPLICABLE":
            raise ValueError("volumes beyond author-approved plan must be explicitly NOT_APPLICABLE")
        rart = r.get("artifacts", {}).get("long_horizon_architecture", {})
        if ref != rart.get("evidence_ref"):
            raise ValueError("volume evidence must be the snapshotted long-horizon maturity evidence")
    except Exception as exc:
        findings.append(issue("readiness.volume-evidence", str(exc)))


def validate_override(root: Path, r: dict[str, Any]) -> None:
    o = r.get("fragmentary_override", {})
    warning = load_json(safe_path(root, o["warning_ref"]))
    insistence = user_evidence(root, o["insistence_ref"], "fragmentary-insistence")
    first = user_evidence(root, warning["first_request_ref"], "early-draft-request")
    if warning.get("source") != "assistant" or warning.get("action") != "refused" or not warning.get("missing_volume_items") or not substantive(warning.get("statement")):
        raise ValueError("first request must have a concrete refusal/warning, with no prose generated")
    if warning.get("prose_generated") is not False or warning.get("target_chapter") != r["target_chapter"] or insistence.get("target_chapter") != r["target_chapter"]:
        raise ValueError("override evidence must bind current target and a refusal without prose")
    if first["message_id"] == insistence["message_id"] or not first["message_order"] < warning.get("message_order", 0) < insistence["message_order"]:
        raise ValueError("insistence must be a later independent user message after refusal")
    if first.get("target_chapter") != r["target_chapter"]:
        raise ValueError("first request must target the same chapter")
    if insistence.get("warning_sha256") != file_hash(root, o["warning_ref"]):
        raise ValueError("insistence must acknowledge this exact warning")


def snapshot_payload(root: Path, manifest_path: Path, r: dict[str, Any]) -> dict[str, Any]:
    claims = copy.deepcopy(r)
    for key in ("review_snapshot", "author_approval", "consumed_approval_ids"):
        claims.pop(key, None)
    claims["gate"] = "REVIEW_READY"  # authorization transition only; all other claims remain bound
    refs = set()
    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k, value in node.items():
                if (k.endswith("_ref") or k == "ref") and k != "dir_ref":
                    if isinstance(value, str) and value:
                        refs.add(value)
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(claims)
    # Context graph sources include backend/unused nodes: metadata and upstream
    # provenance changes invalidate review even if selected Markdown stays identical.
    hand = r["writer_handoff"]
    index = load_json(safe_path(root, hand["context_index_ref"]))
    request = load_json(safe_path(root, hand["request_ref"]))
    for e in index.get("entries", []):
        refs.add(e["path"])
    walk(request)
    manifest = load_json(manifest_path)
    walk(manifest.get("canonical_paths", {}))
    paths = manifest.get("canonical_paths", {})
    for value in paths.values():
        if isinstance(value, str) and safe_path(root, value).is_file():
            refs.add(value)
    for row in r.get("artifacts", {}).values():
        if row.get("evidence_ref"):
            walk(load_json(safe_path(root, row["evidence_ref"])))
    for row in r.get("scene_transactions", []):
        if row.get("evidence_ref"):
            walk(load_json(safe_path(root, row["evidence_ref"])))
    if r.get("fragmentary_override", {}).get("warning_ref"):
        walk(load_json(safe_path(root, r["fragmentary_override"]["warning_ref"])))
    runtime_ref = paths.get("runtime_manifest")
    if runtime_ref:
        rm = load_json(safe_path(root, runtime_ref))
        for value in rm.get("paths", {}).values():
            if isinstance(value, str) and safe_path(root, value).is_file():
                refs.add(value)
    campaign_registration = None
    if r.get("campaign", {}).get("required"):
        cm = load_json(safe_path(root, r["campaign"]["dir_ref"]) / "campaign-manifest.json")
        campaign_registration = {k: cm.get(k) for k in ("campaign_id", "project_id", "track_id", "registration", "source_attestation")}
    gate_tools = [Path(__file__), COMPILER, KERNEL, SCHEMA, ROOT / "scripts/runtime_schema.py", ROOT / "scripts/validate_invariants.py", ROOT / "scripts/validate_story_state.py", ROOT / "scripts/scoped_poetics.py", ROOT / "scripts/research_freshness.py"]
    return {"claims": claims, "campaign_registration": campaign_registration, "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(), "sources": {ref: file_hash(root, ref) if safe_path(root, ref).is_file() else None for ref in sorted(refs)}, "gate_tool_hashes": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in gate_tools}}


def review_fingerprint(root: Path, manifest_path: Path, r: dict[str, Any]) -> str:
    return digest(snapshot_payload(root, manifest_path, r))


def refresh(root: Path, r: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(r)
    candidate["readiness_version"] = VERSION
    candidate["gate"] = "BLOCKED"
    candidate.pop("author_approval", None)
    candidate.pop("review_snapshot", None)
    # Refresh captures bytes; it does not invent structure or decide maturity.
    for row in candidate.get("artifacts", {}).values():
        for key, hash_key in (("ref", "sha256"), ("evidence_ref", "evidence_sha256")):
            if row.get(key):
                row[hash_key] = file_hash(root, row[key])
    for row in candidate.get("scene_transactions", []):
        if row.get("evidence_ref"):
            row["evidence_sha256"] = file_hash(root, row["evidence_ref"])
        if row.get("packet_ref"):
            row["packet_sha256"] = file_hash(root, row["packet_ref"])
    return candidate


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_path(root: Path, rel: str) -> Path:
    p = (root / rel).resolve()
    p.relative_to(root.resolve())
    return p


def issue(code: str, message: str, *, severity: str = "error") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def schema_issues(data: Any) -> list[dict[str, str]]:
    if jsonschema is None:
        return [issue("readiness.dependency", f"jsonschema package is required: {JSONSCHEMA_IMPORT_ERROR}")]
    validator = jsonschema.Draft202012Validator(load_json(SCHEMA))
    out = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        loc = ".".join(str(x) for x in err.absolute_path) or "$"
        out.append(issue("readiness.schema", f"{loc}: {err.message}"))
    return out


def optional_map(manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in manifest.get("optional_artifacts", []) if isinstance(manifest.get("optional_artifacts"), list) else []:
        if isinstance(row, dict):
            out.setdefault(str(row.get("kind", "")), []).append(row)
    return out


def eligible_scene_entry(entry: dict[str, Any], scene_id: str) -> bool:
    scenes = {str(x) for x in entry.get("scenes", []) if x is not None} if isinstance(entry.get("scenes"), list) else set()
    roles = {str(x) for x in entry.get("roles", []) if x is not None} if isinstance(entry.get("roles"), list) else set()
    visibility = str(entry.get("visibility", ""))
    return scene_id in scenes and "writer" in roles and visibility in {"writer-visible", "role-internal", "reader-visible"}


def _audit(root: Path, manifest_path: Path, readiness_path: Path, *, recompile: bool = True, require_draft_permission: bool = False, check_approval: bool = True) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    try:
        manifest = load_json(manifest_path)
        readiness = load_json(readiness_path)
    except Exception as exc:
        return {"ok": False, "gate": None, "findings": [issue("readiness.parse", str(exc))]}
    findings.extend(schema_issues(readiness))
    if findings:
        return {"ok": False, "gate": readiness.get("gate") if isinstance(readiness, dict) else None, "findings": findings}

    gate = str(readiness["gate"])
    target = int(readiness["target_chapter"])
    modern = readiness["readiness_version"] == VERSION
    if require_draft_permission and not recompile:
        return {"ok": False, "gate": "BLOCKED", "findings": [issue("readiness.no-recompile", "formal draft permission requires live recompile; diagnostic skip cannot be combined with a formal gate")]}
    if require_draft_permission and not check_approval:
        return {"ok": False, "gate": "BLOCKED", "findings": [issue("readiness.approval-required", "formal permission cannot skip frozen author approval validation")]}
    if require_draft_permission and (not modern or gate != "DRAFT_READY"):
        findings.append(issue("readiness.draft-permission", "formal drafting requires 1.1.0 DRAFT_READY evidence; migrate with --action refresh, supply missing evidence, freeze, present review and bind a fresh user approval"))
    if not modern:
        findings.append(issue("readiness.legacy", "legacy 1.0.0 is diagnostic only; --action refresh upgrades representation without fabricating missing evidence or authority", severity="warning"))
    if modern:
        structural_evidence(root, readiness, manifest, findings)
        if manifest.get("current_chapter") != target - 1:
            findings.append(issue("readiness.current-target", "target chapter must follow live manifest.current_chapter"))

    # Project Doctor remains the identity/recovery prerequisite.
    proc = subprocess.run(
        [sys.executable, str(PROJECT_OPS), "verify", str(manifest_path), "--root", str(root), "--json"],
        text=True, capture_output=True,
    )
    if proc.returncode != 0:
        findings.append(issue("readiness.project-doctor", "Project Doctor does not pass for the current project."))

    if modern:
        paths = manifest.get("canonical_paths", {})
        state_path = safe_path(root, paths["story_state"])
        state_check = subprocess.run([sys.executable, str(ROOT / "scripts/validate_story_state.py"), str(state_path)], text=True, capture_output=True)
        if state_check.returncode:
            findings.append(issue("readiness.story-state", "current Story State validation fails; override cannot waive state safety"))
        if "narrative-runtime" in manifest.get("enabled_subsystems", []):
            runtime_path = safe_path(root, paths["runtime_manifest"])
            rt_check = subprocess.run([sys.executable, str(ROOT / "scripts/runtime_schema.py"), "validate-project", str(root), "--manifest", str(runtime_path), "--json"], text=True, capture_output=True)
            if rt_check.returncode:
                findings.append(issue("readiness.runtime-schema", "current Runtime schema validation fails"))
            runtime_paths = load_json(runtime_path)["paths"]
            if "narrative-invariants" in manifest.get("enabled_subsystems", []) or runtime_paths.get("invariants"):
                iv_check = subprocess.run([sys.executable, str(ROOT / "scripts/validate_invariants.py"), "--events", str(safe_path(root, runtime_paths["events"])), "--branches", str(safe_path(root, runtime_paths["branches"])), "--invariants", str(safe_path(root, runtime_paths["invariants"])), "--branch", str(manifest["current_branch"]), "--json"], text=True, capture_output=True)
                if iv_check.returncode:
                    findings.append(issue("readiness.runtime-invariants", "active Runtime invariants fail; override cannot waive them"))

    optional = optional_map(manifest)
    canonical = manifest.get("canonical_paths", {}) if isinstance(manifest.get("canonical_paths"), dict) else {}
    risk = readiness["risk_activation"]

    for key, rec in risk.items():
        if rec.get("decision") != "ACTIVE":
            continue
        ref = rec.get("artifact_ref")
        if key == "scene_packets":
            continue
        if key == "reader_model":
            ref = ref or canonical.get("reader_model")
            if not isinstance(ref, str) or not ref:
                findings.append(issue("readiness.reader-model-missing", "Reader Model is ACTIVE but no artifact_ref/canonical reader_model is declared."))
                continue
        elif key in ARTIFACT_KINDS:
            kind = ARTIFACT_KINDS[key]
            if not isinstance(ref, str) or not ref:
                findings.append(issue(f"readiness.{key}-ref", f"{key} is ACTIVE but artifact_ref is missing."))
                continue
            registered = [x for x in optional.get(kind, []) if x.get("path") == ref and str(x.get("status", "")).lower() in {"active", "provisional"}]
            if not registered:
                findings.append(issue(f"readiness.{key}-registration", f"ACTIVE {key} is not registered in project-manifest optional_artifacts at {ref}."))
        if isinstance(ref, str) and ref:
            try:
                p = safe_path(root, ref)
            except Exception:
                findings.append(issue(f"readiness.{key}-path", f"artifact_ref escapes project root: {ref}"))
            else:
                if not p.is_file():
                    findings.append(issue(f"readiness.{key}-missing", f"ACTIVE {key} artifact does not exist: {ref}"))

    anchors = readiness["opening_anchors"]
    if anchors.get("ordinary_life_baseline_required") is True and (modern or gate in {"REVIEW_READY", "DRAFT_READY"}):
        for key in ("livelihood_or_social_role", "current_task_or_reason_here", "location_anchor"):
            if anchors[key].get("status") != "RESOLVED":
                findings.append(issue(f"readiness.opening-anchor.{key}", f"ordinary-life opening requires {key} to be RESOLVED before readiness."))
        if anchors["relationship_anchor"].get("status") == "BLOCKED":
            findings.append(issue("readiness.opening-anchor.relationship_anchor", "relationship_anchor remains BLOCKED."))

    long_h = readiness["long_horizon"]
    active_long = risk["long_horizon_architecture"].get("decision") == "ACTIVE"
    if bool(long_h.get("required")) != active_long:
        findings.append(issue("readiness.long-horizon-activation", "long_horizon.required must agree with risk_activation.long_horizon_architecture."))
    if active_long and gate in {"REVIEW_READY", "DRAFT_READY"} and not modern:
        volume = long_h["volume_strategy"]
        if volume.get("status") not in {"RESOLVED", "NOT_APPLICABLE"}:
            findings.append(issue("readiness.volume-strategy", "active long-horizon architecture requires an explicit provisional volume strategy or an explicit NOT_APPLICABLE decision."))
        if volume.get("status") == "NOT_APPLICABLE" and not str(volume.get("reason") or "").strip():
            findings.append(issue("readiness.volume-strategy-reason", "NOT_APPLICABLE volume strategy requires a reason; do not silently omit volume structure."))
        near = long_h["near_term_chapter_map"]
        if near.get("status") != "RESOLVED":
            findings.append(issue("readiness.near-term-chapter-map", "active long-horizon architecture requires a resolved near-term chapter map before Chapter 1."))
        planned = near.get("planned_through_chapter")
        if not isinstance(planned, int) or planned < target + 2:
            findings.append(issue("readiness.near-term-chapter-horizon", f"near-term chapter map must extend at least through Chapter {target + 2}; it must not stop at the current chapter."))
        ref = near.get("ref")
        if near.get("status") == "RESOLVED" and (not isinstance(ref, str) or not ref or not safe_path(root, ref).is_file()):
            findings.append(issue("readiness.near-term-chapter-ref", "resolved near-term chapter map must reference an existing project artifact."))

    hand = readiness["writer_handoff"]
    index_ref, request_ref = hand.get("context_index_ref"), hand.get("request_ref")
    index: dict[str, Any] = {}
    request: dict[str, Any] = {}
    if isinstance(index_ref, str) and index_ref and safe_path(root, index_ref).is_file():
        index = load_json(safe_path(root, index_ref))
    elif risk["scene_packets"].get("decision") == "ACTIVE" or gate == "DRAFT_READY":
        findings.append(issue("readiness.context-index", "readiness requires an existing context index."))
    if isinstance(request_ref, str) and request_ref and safe_path(root, request_ref).is_file():
        request = load_json(safe_path(root, request_ref))
    elif gate == "DRAFT_READY":
        findings.append(issue("readiness.context-request", "DRAFT_READY requires an existing Writer context request."))
    if modern:
        if request.get("role") != "writer" or request.get("target_chapter") != target:
            findings.append(issue("readiness.request-target", "Context Request must explicitly target the current chapter and Writer role"))
        if not request.get("project_manifest") or safe_path(root, request["project_manifest"]) != manifest_path.resolve():
            findings.append(issue("readiness.request-manifest", "Writer Request must bind this authoritative Project Manifest"))
        if request.get("strict_visibility") is not True or not request.get("scoped_project_poetics_ref") or not request.get("scoped_project_poetics_envelope_ref"):
            findings.append(issue("readiness.writer-safe-poetics", "current Writer handoff requires strict visibility and verified scoped Project Poetics"))
        state = load_json(safe_path(root, canonical["story_state"]))
        from research_freshness import stale_research_dependencies
        needed_research = set(request.get("research", []))
        grounding = readiness.get("artifacts", {}).get("grounding", {})
        if grounding.get("evidence_ref"):
            needed_research |= {d.get("id") for d in load_json(safe_path(root, grounding["evidence_ref"])).get("dependencies", []) if isinstance(d, dict)}
        if any(d.get("id") in needed_research for d in stale_research_dependencies(state, chapter=target)):
            findings.append(issue("readiness.grounding-stale", "current-cone research dependencies are stale under the canonical research freshness owner"))

    scene_records = {str(x.get("scene_id")): x for x in readiness.get("scene_transactions", []) if isinstance(x, dict)}
    requested_scenes = []
    if isinstance(request.get("required_scene_ids"), list) and request.get("required_scene_ids"):
        requested_scenes = [str(x) for x in request["required_scene_ids"]]
    elif risk["scene_packets"].get("decision") == "ACTIVE" and isinstance(request.get("scenes"), list):
        requested_scenes = [str(x) for x in request["scenes"]]
    entries = [x for x in index.get("entries", []) if isinstance(x, dict)] if isinstance(index, dict) else []
    required_ids = {str(x) for x in request.get("required_ids", [])} if isinstance(request.get("required_ids"), list) else set()
    if modern:
        if readiness.get("causal_risks", {}).get("secret_asymmetry"):
            from compile_context import apply_project_manifest_defaults, load_secret_policy, taint_closure
            try:
                effective_request = apply_project_manifest_defaults(request, root)
                blocked_secrets, _, meta = load_secret_policy(effective_request, root)
                taints, _ = taint_closure(entries)
                protected = [e for e in entries if e.get("visibility") in {"author-only", "backend-hidden", "future-answer"}]
                if not meta["registry_supplied"] or not meta["registry_active_secret_count"] or not blocked_secrets or not any(taints.get(e["id"], set()) & blocked_secrets for e in protected):
                    raise ValueError("secret asymmetry requires nonempty live registry connected to actual protected source taint nodes")
                if any((e.get("visibility") == "future-answer" or e.get("future_sensitive") is True) and not taints.get(e["id"]) for e in entries):
                    raise ValueError("declared future-truth entries require registered semantic taint, not visibility alone")
            except Exception as exc:
                findings.append(issue("readiness.secret-graph", str(exc)))
        requested_scenes = sorted(set(requested_scenes) | {sid for sid, row in scene_records.items() if row.get("required")})
        if risk["scene_packets"]["decision"] == "ACTIVE" and not requested_scenes:
            findings.append(issue("readiness.scene-requirements", "ACTIVE scene risk requires explicit required scene records; an empty request cannot hide the obligation"))
        if len(scene_records) != len(readiness["scene_transactions"]):
            findings.append(issue("readiness.scene-duplicates", "scene transaction IDs must be unique"))
        mandatory = hand.get("required_writer_entry_ids", [])
        mission_id = hand.get("mission_entry_id")
        mission_ref = readiness.get("artifacts", {}).get("writer_mission", {}).get("ref")
        missions = [e for e in entries if e.get("id") == mission_id and e.get("kind") == "mission" and e.get("path") == mission_ref and e.get("chapter") == target and allowed(e, request)[0]]
        if not missions or mission_id not in required_ids or not isinstance(mandatory, list) or not mandatory or not set(mandatory).issubset(required_ids):
            findings.append(issue("readiness.mission-wiring", "current mature Writer Mission and required safe entry IDs must be explicitly required by request"))
        for kind in ("cast", "writer_mission", "world_model", "character_state", "grounding"):
            row = readiness.get("artifacts", {}).get(kind)
            if not row or (kind not in {"cast", "writer_mission", "grounding"} and risk.get(kind, {}).get("decision") != "ACTIVE"):
                continue
            try:
                ev = load_json(safe_path(root, row["evidence_ref"]))
                safe_ids = ev["writer_entry_ids"]
                if not isinstance(safe_ids, list) or not safe_ids or not set(safe_ids).issubset(required_ids) or any(not any(e.get("id") == sid and allowed(e, request)[0] for e in entries) for sid in safe_ids):
                    raise ValueError("mature current-cone artifact needs actual eligible required Writer-safe derivatives")
            except Exception as exc:
                findings.append(issue("readiness.safe-source-wiring", f"{kind}: {exc}"))
    for scene_id in requested_scenes:
        row = scene_records.get(scene_id)
        if not row:
            findings.append(issue("readiness.scene-transaction-missing", f"required scene {scene_id} has no readiness transaction record."))
            continue
        if row.get("status") != "READY" or row.get("open_items"):
            findings.append(issue("readiness.scene-transaction-open", f"required scene {scene_id} transaction is not closed."))
        packet_ref = row.get("packet_ref")
        if not isinstance(packet_ref, str) or not packet_ref or not safe_path(root, packet_ref).is_file():
            findings.append(issue("readiness.scene-packet-ref", f"required scene {scene_id} does not reference an existing Scene Packet."))
        entry_id = row.get("context_entry_id")
        matching = [e for e in entries if str(e.get("id")) == str(entry_id) and eligible_scene_entry(e, scene_id)] if entry_id else []
        if not matching:
            findings.append(issue("readiness.scene-context-wiring", f"required scene {scene_id} lacks a Writer-eligible context-index entry tagged with that scene."))
        elif str(entry_id) not in required_ids:
            findings.append(issue("readiness.scene-not-required", f"required scene {scene_id} context entry {entry_id} is not in request.required_ids; scene coverage could be silently omitted."))
        if modern:
            try:
                if scene_id not in request.get("required_scene_ids", []):
                    raise ValueError("readiness scene obligation missing from request.required_scene_ids")
                ev = load_json(safe_path(root, row["evidence_ref"]))
                if not matching or matching[0].get("kind") != "scene-packet" or not allowed(matching[0], request)[0]:
                    raise ValueError("scene coverage must be an eligible Scene Packet entry, not an arbitrary tag")
                if ev.get("scene_id") != scene_id or ev.get("target_chapter") != target or not all(substantive(ev.get(k)) for k in SCENE_FIELDS) or ev.get("open_items") != []:
                    raise ValueError("scene evidence must close entry/trigger/transition/rollback/retained/reverted/exit/persistent effects")
                if row.get("evidence_sha256") != file_hash(root, row["evidence_ref"]) or row.get("packet_sha256") != file_hash(root, packet_ref):
                    raise ValueError("scene evidence/packet maturity snapshot stale; refresh and re-review")
                status = ev.get("transaction_status")
                registry = load_json(safe_path(root, ev["registration_ref"]))
                if ev["registration_ref"] != canonical.get("scene_plan_registry"):
                    raise ValueError("scene registration must use manifest canonical scene_plan_registry")
                records = registry.get("scene_transactions", [])
                if status not in {"PLANNED", "COMMITTED"} or not any(s.get("scene_id") == scene_id and s.get("status") == status and s.get("evidence_sha256") == file_hash(root, row["evidence_ref"]) for s in records):
                    raise ValueError("scene plan must be registered as PLANNED separately from committed Story State/Runtime")
                if status == "COMMITTED":
                    runtime = load_json(safe_path(root, canonical["runtime_manifest"]))
                    events_ref = runtime.get("paths", {}).get("events")
                    if not events_ref or not any(json.loads(line).get("event_id") == ev.get("event_id") for line in safe_path(root, events_ref).read_text(encoding="utf-8").splitlines() if line.strip()):
                        raise ValueError("COMMITTED scene requires an actual Runtime event")
            except Exception as exc:
                findings.append(issue("readiness.scene-evidence", f"{scene_id}: {exc}"))

    blockers = readiness.get("blockers", [])
    if (modern or gate in {"REVIEW_READY", "DRAFT_READY"}) and blockers:
        findings.append(issue("readiness.blockers", f"{gate} claim has unresolved structural blockers: {len(blockers)}"))

    if gate == "DRAFT_READY" or (modern and recompile):
        if hand.get("compile_status") != "PASSED":
            findings.append(issue("readiness.compile-status", "DRAFT_READY requires compile_status=PASSED."))
        if hand.get("semantic_kernel_status") != "PASSED":
            findings.append(issue("readiness.kernel-status", "DRAFT_READY requires semantic_kernel_status=PASSED."))
        pack_ref, pack_manifest_ref = hand.get("compiled_pack_ref"), hand.get("compiled_pack_manifest_ref")
        if not isinstance(pack_ref, str) or not isinstance(pack_manifest_ref, str):
            findings.append(issue("readiness.pack-evidence", "DRAFT_READY requires compiled_pack_ref and compiled_pack_manifest_ref."))
        else:
            pp, mp = safe_path(root, pack_ref), safe_path(root, pack_manifest_ref)
            if not pp.is_file() or not mp.is_file():
                findings.append(issue("readiness.pack-missing", "compiled Writer pack or manifest is missing."))
            else:
                pm = load_json(mp)
                raw_hash = hashlib.sha256(pp.read_bytes()).hexdigest()
                if pm.get("pack_sha256") != raw_hash:
                    findings.append(issue("readiness.pack-hash", "compiled Writer pack bytes do not match manifest pack_sha256."))
                if pm.get("project_context_generation") != manifest.get("context_generation"):
                    findings.append(issue("readiness.pack-generation", "compiled Writer pack was built against a stale project context_generation."))
                if modern and (pm.get("role") != "writer" or pm.get("target_chapter") != target):
                    findings.append(issue("readiness.pack-target", "pack must bind current Writer role and target chapter"))
        if recompile and isinstance(index_ref, str) and isinstance(request_ref, str) and safe_path(root, index_ref).is_file() and safe_path(root, request_ref).is_file():
            with tempfile.TemporaryDirectory(prefix="lwa-readiness-") as td:
                out = Path(td) / "pack.md"
                mout = Path(td) / "pack.manifest.json"
                cp = subprocess.run([sys.executable, str(COMPILER), str(safe_path(root, index_ref)), str(safe_path(root, request_ref)), "--root", str(root), "--output", str(out), "--manifest-out", str(mout)], text=True, capture_output=True)
                if cp.returncode != 0:
                    findings.append(issue("readiness.recompile", "current Writer context does not compile successfully; stored PASS evidence is stale or incorrect."))
                elif modern:
                    live_manifest = load_json(mout)
                    if not isinstance(pack_manifest_ref, str) or not safe_path(root, pack_manifest_ref).is_file() or load_json(safe_path(root, pack_manifest_ref)) != live_manifest:
                        findings.append(issue("readiness.pack-stale", "stored manifest differs from live compilation (request/index/secret/provenance/source/mission/poetics metadata); regenerate pack before review"))
                    if not isinstance(pack_ref, str) or not safe_path(root, pack_ref).is_file() or safe_path(root, pack_ref).read_bytes() != out.read_bytes():
                        findings.append(issue("readiness.pack-stale-bytes", "stored pack differs from current live compilation"))
        kp = subprocess.run([sys.executable, str(KERNEL), "verify", str(root), "--json"], text=True, capture_output=True)
        if kp.returncode != 0:
            findings.append(issue("readiness.kernel-recheck", "current Narrative Semantics Kernel verification fails."))

    if modern and check_approval:
        snapshot = readiness.get("review_snapshot")
        if snapshot or gate == "DRAFT_READY":
            try:
                if not isinstance(snapshot, dict) or snapshot.get("fingerprint") != review_fingerprint(root, manifest_path, readiness):
                    raise ValueError("review state changed/missing: freeze again, present it and obtain a new approval")
                if gate == "DRAFT_READY":
                    approval = readiness["author_approval"]
                    evidence = user_evidence(root, approval["evidence_ref"], "draft-approval")
                    if evidence.get("snapshot_id") != snapshot.get("id") or evidence.get("review_fingerprint") != snapshot.get("fingerprint") or evidence.get("target_chapter") != target or evidence.get("draft_mode") != readiness.get("draft_mode", "NORMAL") or file_hash(root, approval["evidence_ref"]) != approval.get("sha256"):
                        raise ValueError("approval must bind this exact frozen state, chapter and draft mode")
                    if evidence["message_id"] not in readiness.get("consumed_approval_ids", []):
                        raise ValueError("approval must be bound via --action bind-approval")
            except Exception as exc:
                findings.append(issue("readiness.approval-drift", str(exc)))

    if modern:
        campaign = readiness.get("campaign", {})
        if readiness.get("causal_risks", {}).get("time_loop_or_branch") and campaign.get("required") is not True:
            findings.append(issue("readiness.campaign-registration", "time-loop/branch project requires prospective live campaign registration before Chapter 1"))
        if campaign.get("required"):
            try:
                from live_campaign import load_campaign, verify_campaign
                cdir = safe_path(root, campaign["dir_ref"])
                _, cm = load_campaign(cdir)
                if cm.get("project_id") != manifest.get("project_id") or (target == 1 and cm.get("registration", {}).get("project_chapter") != 0) or not verify_campaign(cdir, root).get("verified"):
                    raise ValueError("requires verified project-matched prospective Chapter 0 baseline")
            except Exception as exc:
                findings.append(issue("readiness.campaign-registration", str(exc)))

    return {
        "ok": not any(x["severity"] == "error" for x in findings),
        "gate": "BLOCKED" if any(x["severity"] == "error" for x in findings) else gate,
        "claimed_gate": gate,
        "draft_permission": modern and gate == "DRAFT_READY" and recompile and check_approval and not any(x["severity"] == "error" for x in findings),
        "target_chapter": target,
        "finding_count": len(findings),
        "findings": findings,
    }


def audit(root: Path, manifest_path: Path, readiness_path: Path, **kwargs: Any) -> dict[str, Any]:
    """Malformed/untrusted project artifacts fail closed with a diagnostic."""
    try:
        result = _audit(root, manifest_path, readiness_path, **kwargs)
        result.setdefault("draft_permission", False)
        if not result.get("ok"):
            result["gate"] = "BLOCKED"
        return result
    except Exception as exc:
        return {"ok": False, "gate": "BLOCKED", "draft_permission": False, "findings": [issue("readiness.invalid-evidence", str(exc))]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    p.add_argument("readiness", type=Path)
    p.add_argument("--root", type=Path)
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-recompile", action="store_true", help="skip live Writer-pack recompile; intended only for focused diagnostics/tests")
    p.add_argument("--require-draft-permission", "--require-draft-ready", dest="formal", action="store_true")
    p.add_argument("--action", choices=["check", "refresh", "freeze", "bind-approval", "start-chapter-1"], default="check")
    p.add_argument("--approval-evidence", help="project-relative imported user-message evidence; never synthesized by this CLI")
    p.add_argument("--session-id", help="prospective campaign session to start only after formal permission passes")
    args = p.parse_args()
    root = (args.root or args.manifest.resolve().parent).resolve()
    formal = args.formal or args.action == "start-chapter-1"
    try:
        if args.no_recompile and (formal or args.action in {"freeze", "bind-approval"}):
            raise ValueError("--no-recompile cannot be combined with formal permission, freeze or bind-approval")
        r = load_json(args.readiness)
        if args.action == "refresh":
            if args.formal:
                raise ValueError("refresh is representation/evidence capture, never draft permission")
            r = refresh(root, r)
            args.readiness.write_bytes((json.dumps(r, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            result = {"ok": True, "gate": "BLOCKED", "draft_permission": False, "approval_invalidated": True}
        elif args.action in {"freeze", "bind-approval"}:
            if r.get("readiness_version") != VERSION:
                raise ValueError("run --action refresh and supply 1.1.0 evidence before freezing review")
            # Check candidate without treating pending approval as a safety failure.
            result = audit(root, args.manifest.resolve(), args.readiness.resolve(), check_approval=False)
            if not result["ok"]:
                raise ValueError("review cannot freeze/bind while safety/evidence blockers remain: " + "; ".join(x["code"] for x in result["findings"]))
            fingerprint = review_fingerprint(root, args.manifest.resolve(), r)
            if args.action == "freeze":
                r["gate"] = "REVIEW_READY"
                r.pop("author_approval", None)
                r["review_snapshot"] = {"id": str(uuid.uuid4()), "fingerprint": fingerprint, "payload": snapshot_payload(root, args.manifest.resolve(), r)}
                result = {"ok": True, "gate": "REVIEW_READY", "draft_permission": False, "review_snapshot": r["review_snapshot"], "next": "Present this exact review snapshot to the author, then import a new explicit approval bound to its id/fingerprint."}
            else:
                snapshot = r.get("review_snapshot", {})
                if snapshot.get("fingerprint") != fingerprint:
                    raise ValueError("review changed since freeze; old approval cannot be rebound: freeze, present review, obtain fresh approval")
                evidence = user_evidence(root, args.approval_evidence, "draft-approval")
                if evidence.get("snapshot_id") != snapshot.get("id") or evidence.get("review_fingerprint") != fingerprint or evidence.get("target_chapter") != r["target_chapter"] or evidence.get("draft_mode") != r.get("draft_mode", "NORMAL"):
                    raise ValueError("approval is not for this frozen review snapshot/chapter/mode")
                used = r.setdefault("consumed_approval_ids", [])
                if evidence["message_id"] in used:
                    raise ValueError("approval message was already consumed; obtain a new author approval")
                used.append(evidence["message_id"])
                r["author_approval"] = {"evidence_ref": args.approval_evidence, "sha256": file_hash(root, args.approval_evidence)}
                r["gate"] = "DRAFT_READY"
                result = {"ok": True, "gate": "DRAFT_READY", "draft_permission": True}
            args.readiness.write_bytes((json.dumps(r, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        else:
            result = audit(root, args.manifest.resolve(), args.readiness.resolve(), recompile=not args.no_recompile, require_draft_permission=formal)
            if args.action == "start-chapter-1" and result.get("draft_permission"):
                if r["target_chapter"] != 1 or not args.session_id:
                    raise ValueError("start-chapter-1 requires Chapter 1 and an explicit --session-id")
                c = r.get("campaign", {})
                if c.get("required"):
                    session = subprocess.run([sys.executable, str(ROOT / "scripts/live_campaign.py"), "session-start", str(safe_path(root, c["dir_ref"])), "--project-root", str(root), "--session-id", args.session_id], text=True, capture_output=True)
                    if session.returncode:
                        raise ValueError("campaign session-start failed: " + session.stderr.strip())
                    result["campaign_session_started"] = args.session_id
                result["next"] = "Draft only from the verified current Writer pack; reconcile/commit before canonical campaign checkpoint."
    except Exception as exc:
        result = {"ok": False, "gate": "BLOCKED", "draft_permission": False, "findings": [issue("readiness.operation", str(exc))]}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"gate={result.get('gate')} ok={result.get('ok')} findings={result.get('finding_count', len(result.get('findings', [])))}")
        for row in result.get("findings", []):
            print(f"{row['severity'].upper()} {row['code']}: {row['message']}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
