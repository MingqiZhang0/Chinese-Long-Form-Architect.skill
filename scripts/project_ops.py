#!/usr/bin/env python3
"""Project-level identity, resume, health, and non-destructive format migration.

This is intentionally above Narrative Runtime. Lean projects may use it without
Runtime Mode. It never invents canon and never rewrites story prose/state during
migration; it only creates or validates project-level representation metadata.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from open_issue import active_issue, is_v2, issue_id
from capability_probe import CapabilityError, require_profile

try:
    import jsonschema
except Exception as exc:  # pragma: no cover
    jsonschema = None
    JSONSCHEMA_IMPORT_ERROR = exc
else:
    JSONSCHEMA_IMPORT_ERROR = None

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SCRIPT_ROOT / "assets" / "project-schemas" / "project-manifest.schema.json"
PROFILES = SCRIPT_ROOT / "assets" / "project-templates" / "governance-profiles.json"
CURRENT_PROJECT_FORMAT = "1.0.0"
DIALECT = "https://json-schema.org/draft/2020-12/schema"
LEAN_STATE_TEMPLATE = SCRIPT_ROOT / "assets" / "state-templates" / "story-state-minimal-template.json"
PROJECT_POETICS_TEMPLATE = SCRIPT_ROOT / "assets" / "prewriting-templates" / "project-poetics-template.md"
DEFAULT_PROJECT_POETICS_PATH = "planning/project-poetics.md"
PROJECT_POETICS_BOOTSTRAP_VERSION = "1.0"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_semver(value: str) -> tuple[int, int, int]:
    core = value.split("+", 1)[0].split("-", 1)[0]
    parts = core.split(".")
    if len(parts) != 3 or not all(x.isdigit() for x in parts):
        raise ValueError(f"invalid semantic version: {value}")
    return tuple(int(x) for x in parts)  # type: ignore[return-value]


def validate_schema(data: Any) -> list[str]:
    if jsonschema is None:
        return [f"jsonschema package is required: {JSONSCHEMA_IMPORT_ERROR}"]
    schema = load_json(SCHEMA)
    validator = jsonschema.Draft202012Validator(schema)
    out: list[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        loc = ".".join(str(x) for x in err.absolute_path) or "$"
        out.append(f"{loc}: {err.message}")
    return out


def safe_path(root: Path, rel: str) -> Path:
    target = (root / rel).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"project path escapes root: {rel}") from exc
    return target


def governance_contract() -> dict[str, Any]:
    raw = load_json(PROFILES)
    return raw if isinstance(raw, dict) else {}


def profile_table() -> dict[str, dict[str, Any]]:
    raw = governance_contract()
    return raw.get("profiles", {}) if isinstance(raw.get("profiles"), dict) else {}


def subsystem_dependencies() -> dict[str, list[str]]:
    raw = governance_contract().get("subsystem_dependencies", {})
    if not isinstance(raw, dict):
        return {}
    return {str(k): [str(x) for x in v] for k, v in raw.items() if isinstance(v, list)}


def subsystem_path_requirements() -> dict[str, list[str]]:
    raw = governance_contract().get("subsystem_path_requirements", {})
    if not isinstance(raw, dict):
        return {}
    return {str(k): [str(x) for x in v] for k, v in raw.items() if isinstance(v, list)}


def default_subsystems(profile: str) -> list[str]:
    rec = profile_table().get(profile)
    if not isinstance(rec, dict):
        raise ValueError(f"unknown governance profile: {profile}")
    vals = rec.get("required_subsystems", [])
    return [str(x) for x in vals]


def default_humanities_analysis_policy() -> dict[str, Any]:
    return {
        "mode": "opt_in",
        "milestones": [],
        "diagnostic_triggers": [],
        "chapter_interval": None,
    }


def find_last_event(root: Path, runtime_manifest_rel: str | None) -> str | None:
    if not runtime_manifest_rel:
        return None
    runtime_manifest_path = safe_path(root, runtime_manifest_rel)
    if not runtime_manifest_path.is_file():
        return None
    runtime_manifest = load_json(runtime_manifest_path)
    if not isinstance(runtime_manifest, dict):
        return None
    events_rel = runtime_manifest.get("paths", {}).get("events") if isinstance(runtime_manifest.get("paths"), dict) else None
    if not isinstance(events_rel, str):
        return None
    # Runtime paths are project-root relative by contract.
    events = safe_path(root, events_rel)
    if not events.is_file():
        return None
    last: str | None = None
    for line in events.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("event_id") is not None:
            last = str(row.get("event_id"))
    return last


def infer_paths(root: Path) -> dict[str, str]:
    candidates = {
        "project_brief": "intake/project-brief.md",
        "story_state": "state/story-state.json",
        "context_index": "context/context-index.json",
        "secret_registry": "context/secret-registry.json",
        "runtime_manifest": "runtime/runtime-manifest.json",
        "reader_model": "planning/07-reader-model.md",
        "project_poetics": "planning/project-poetics.md",
        "research_index": "research/00-reality-research-index.md",
        "chapters_dir": "chapters",
        "scenes_dir": "scenes",
        "scene_plan_registry": "state/scene-plans.json",
        "revisions_dir": "revisions",
        "reconciliations_dir": "reconciliations",
    }
    found: dict[str, str] = {}
    for key, rel in candidates.items():
        p = root / rel
        if not p.exists():
            continue
        # Optional governance directories are evidence only when they contain a
        # durable artifact of the owned type. Empty placeholder directories must
        # not silently activate a subsystem during migration.
        if key == "revisions_dir":
            if not any(x.is_file() and x.name == "impact.json" for x in p.rglob("*.json")):
                continue
        if key == "reconciliations_dir":
            meaningful = False
            for x in p.rglob("*.json"):
                if not x.is_file():
                    continue
                try:
                    raw = load_json(x)
                except Exception:
                    continue
                if isinstance(raw, dict) and raw.get("reconciliation_version"):
                    meaningful = True
                    break
            if not meaningful:
                continue
        found[key] = rel
    if "story_state" not in found:
        found["story_state"] = "state/story-state.json"
    return found


def infer_chapter(root: Path, paths: dict[str, str]) -> int:
    rel = paths.get("story_state")
    if isinstance(rel, str):
        p = safe_path(root, rel)
        if p.is_file():
            try:
                state = load_json(p)
                value = state.get("current_chapter") if isinstance(state, dict) else None
                if isinstance(value, int) and value >= 0:
                    return value
            except Exception:
                pass
    return 0


def infer_project_id(root: Path, paths: dict[str, str]) -> str | None:
    rel = paths.get("runtime_manifest")
    if isinstance(rel, str):
        p = safe_path(root, rel)
        if p.is_file():
            try:
                runtime = load_json(p)
                value = runtime.get("project_id") if isinstance(runtime, dict) else None
                if isinstance(value, str) and value:
                    return value
            except Exception:
                pass
    return None


def infer_branch(root: Path, paths: dict[str, str]) -> str:
    rel = paths.get("runtime_manifest")
    if isinstance(rel, str):
        p = safe_path(root, rel)
        if p.is_file():
            try:
                runtime = load_json(p)
                branch = runtime.get("current_branch") if isinstance(runtime, dict) else None
                if isinstance(branch, str) and branch:
                    return branch
            except Exception:
                pass
    return "main"


def infer_existing_subsystems(root: Path, paths: dict[str, str]) -> set[str]:
    """Recover optional protections that are already evidenced by durable project artifacts.

    Migration should not silently drop a subsystem merely because the selected profile
    is lighter than the existing project. Infer protections whose durable inputs already
    exist, while avoiding capabilities that require a semantic choice rather than a file.
    """
    enabled: set[str] = set()
    if isinstance(paths.get("reader_model"), str):
        enabled.add("reader-model")
    if isinstance(paths.get("context_index"), str):
        enabled.add("context-compilation")
    runtime_rel = paths.get("runtime_manifest")
    if isinstance(runtime_rel, str):
        runtime_path = safe_path(root, runtime_rel)
        if runtime_path.is_file():
            enabled.add("narrative-runtime")
            try:
                runtime = load_json(runtime_path)
            except Exception:
                runtime = {}
            runtime_paths = runtime.get("paths", {}) if isinstance(runtime, dict) else {}
            if isinstance(runtime_paths, dict):
                dep_rel = runtime_paths.get("dependencies")
                if isinstance(dep_rel, str) and safe_path(root, dep_rel).is_file():
                    enabled.add("dependency-graph")
                inv_rel = runtime_paths.get("invariants")
                if isinstance(inv_rel, str):
                    inv_path = safe_path(root, inv_rel)
                    if inv_path.is_file():
                        try:
                            inv = load_json(inv_path)
                        except Exception:
                            inv = {}
                        if isinstance(inv, dict) and isinstance(inv.get("invariants"), list) and inv.get("invariants"):
                            enabled.add("narrative-invariants")
                branch_rel = runtime_paths.get("branches")
                if isinstance(branch_rel, str):
                    branch_path = safe_path(root, branch_rel)
                    if branch_path.is_file():
                        try:
                            branches = load_json(branch_path)
                        except Exception:
                            branches = {}
                        rows = branches.get("branches", {}) if isinstance(branches, dict) else {}
                        if isinstance(rows, dict) and any(str(branch_id) != "main" for branch_id in rows):
                            enabled.add("branches")
                        elif isinstance(rows, list) and any(isinstance(x, dict) and str(x.get("branch_id", x.get("id", "main"))) != "main" for x in rows):
                            enabled.add("branches")
    if isinstance(paths.get("research_index"), str):
        enabled.add("research-grounding")
        state_rel = paths.get("story_state")
        if isinstance(state_rel, str):
            state_path = safe_path(root, state_rel)
            if state_path.is_file():
                try:
                    state = load_json(state_path)
                except Exception:
                    state = {}
                deps = state.get("research_dependencies", []) if isinstance(state, dict) else []
                if isinstance(deps, list) and deps:
                    enabled.add("research-freshness")
    if isinstance(paths.get("revisions_dir"), str):
        enabled.add("semantic-revision")
    if isinstance(paths.get("reconciliations_dir"), str):
        enabled.add("prose-state-reconciliation")
    return enabled


def ensure_fresh_lean_scaffold(root: Path) -> None:
    """Create only the neutral artifacts needed for a brand-new Lean project.

    Existing files are never rewritten. This helper is for `init`, never legacy migration.
    """
    root.mkdir(parents=True, exist_ok=True)
    state_path = root / "state" / "story-state.json"
    if not state_path.exists():
        starter = load_json(LEAN_STATE_TEMPLATE)
        save_json(state_path, starter)
    poetics_path = root / "planning" / "project-poetics.md"
    if not poetics_path.exists():
        poetics_path.parent.mkdir(parents=True, exist_ok=True)
        poetics_path.write_bytes(PROJECT_POETICS_TEMPLATE.read_bytes())
    (root / "chapters").mkdir(parents=True, exist_ok=True)
    (root / "scenes").mkdir(parents=True, exist_ok=True)
    # Neutral prewriting skeletons prevent omission; existence never implies
    # activation, maturity, author authority or permission to draft.
    templates = SCRIPT_ROOT / "assets/prewriting-templates"
    readiness = load_json(templates / "prewriting-readiness-template.json")
    evidence = load_json(templates / "maturity-evidence-template.json")
    copies = {
        "planning/02-world-model.md": templates / "02-world-model-template.md",
        "planning/06-long-horizon-architecture.md": templates / "06-long-horizon-architecture-template.md",
        "planning/08-narrative-strategy.md": templates / "08-narrative-strategy-template.md",
        "planning/10-chapter-01-mission.md": templates / "10-chapter-01-mission-template.md",
        "context/chapter-01-writer-mission.md": templates / "chapter-writer-mission-template.md",
        "intake/project-brief.md": SCRIPT_ROOT / "assets/intake-templates/project-brief-template.md",
    }
    for rel, template in copies.items():
        target = safe_path(root, rel)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(template.read_bytes())
    skeletons = {
        "planning/prewriting-readiness.json": readiness,
        "context/context-index.json": {"entries": []},
        "context/writer-request.json": {**load_json(SCRIPT_ROOT / "assets/tooling-templates/context-request-template.json"), "project_manifest": "project-manifest.json", "required_ids": ["chapter-01-writer-mission"]},
        "state/scene-plans.json": {"scene_transactions": []},
        "planning/campaign-registration.json": {"status": "UNASSESSED", "dir_ref": "campaign", "registration_chapter": None},
    }
    for kind, row in evidence.items():
        skeletons[f"planning/evidence/{kind}.json"] = row
    for rel, value in skeletons.items():
        if not safe_path(root, rel).exists():
            save_json(safe_path(root, rel), value)
    roster = root / "planning/character-roster.md"
    if not roster.exists():
        roster.write_bytes(b"# Character Roster / Cast Architecture\n\nWho exists; identify narrative centers, social position, life anchors, opening cast and long-term versus scene-local state scope. No identities established yet.\n")


def ensure_project_poetics(
    root: Path,
    manifest: dict[str, Any],
    *,
    path_override: str | None = None,
    reason: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Establish a neutral Project Poetics owner without inferring literary commitments.

    This operation is deliberately explicit and separate from `migrate-legacy`. If a
    canonical Project Poetics artifact already exists, the operation is idempotent.
    It never adopts an unowned pre-existing file and never overwrites an existing owner.
    """
    paths = manifest.get("canonical_paths")
    if not isinstance(paths, dict):
        raise ValueError("canonical_paths must be an object before Project Poetics can be established")

    existing_rel = paths.get("project_poetics")
    if existing_rel is not None and (not isinstance(existing_rel, str) or not existing_rel.strip()):
        raise ValueError("canonical_paths.project_poetics must be a non-empty string when present")
    if existing_rel and path_override and path_override != existing_rel:
        raise ValueError(
            "ensure-poetics cannot repoint an existing Project Poetics owner; "
            "use an explicit reviewed project-format/change-control migration"
        )

    rel = str(existing_rel or path_override or DEFAULT_PROJECT_POETICS_PATH)
    target = safe_path(root, rel)
    if target.exists() and not target.is_file():
        raise ValueError(f"Project Poetics canonical path is not a file: {rel}")

    # Existing canonical ownership is already established. Do not rewrite content or
    # retroactively manufacture provenance. The command is intentionally idempotent.
    if existing_rel and target.is_file():
        return manifest, {
            "changed": False,
            "artifact_path": rel,
            "status": "already-present",
            "inference_performed": False,
            "context_generation": manifest.get("context_generation", 0),
            "provenance": manifest.get("project_poetics_provenance"),
        }

    # If an unowned file happens to occupy the desired path, do not silently promote
    # it to canonical planning state. That could convert unreviewed text into authority.
    if not existing_rel and target.exists():
        raise ValueError(
            f"refusing to adopt pre-existing unowned Project Poetics file: {rel}; "
            "review it explicitly and set the canonical pointer through change control"
        )

    template_text = PROJECT_POETICS_TEMPLATE.read_text(encoding="utf-8")
    if "Status: `provisional`" not in template_text:
        raise ValueError("Project Poetics template is not explicitly provisional; refusing neutral bootstrap")

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    source_state = "canonical-artifact-missing" if existing_rel else "legacy-unrepresented"
    provenance = {
        "provenance_version": PROJECT_POETICS_BOOTSTRAP_VERSION,
        "artifact_path": rel,
        "established_by": "project_ops.ensure-poetics",
        "established_at": now,
        "source_state": source_state,
        "creation_mode": "blank-provisional-template",
        "inference_performed": False,
        "template_sha256": hashlib.sha256(PROJECT_POETICS_TEMPLATE.read_bytes()).hexdigest(),
        "reason": reason or "Explicit neutral Project Poetics bootstrap for an existing project.",
    }

    # Deep-copy through JSON because the manifest is JSON data and nested mutation of a
    # shallow copy would otherwise mutate the caller before validation succeeds.
    candidate = json.loads(json.dumps(manifest, ensure_ascii=False))
    candidate_paths = candidate.setdefault("canonical_paths", {})
    candidate_paths["project_poetics"] = rel
    candidate["project_poetics_provenance"] = provenance

    migration_history = candidate.setdefault("migration_history", [])
    if not isinstance(migration_history, list):
        raise ValueError("migration_history must be an array")
    migration_history.append({
        "migration_id": "ensure-project-poetics-owner-v1",
        "from_version": source_state,
        "to_version": "project-poetics-provisional-owner-v1",
        "status": "applied",
        "timestamp": now,
        "notes": "Established a blank provisional Project Poetics canonical owner; no literary commitments were inferred.",
        "artifact_path": rel,
        "inference_performed": False,
        "template_sha256": provenance["template_sha256"],
    })

    current_generation = candidate.get("context_generation", 0)
    if not isinstance(current_generation, int) or current_generation < 0:
        raise ValueError("invalid context_generation")
    next_generation = current_generation + 1
    candidate["context_generation"] = next_generation
    context_history = candidate.setdefault("context_generation_history", [])
    if not isinstance(context_history, list):
        raise ValueError("context_generation_history must be an array")
    context_history.append({
        "generation": next_generation,
        "reason": "Project Poetics canonical owner established by ensure-poetics; no poetics inferred.",
        "timestamp": now,
    })

    schema_errors = validate_schema(candidate)
    if schema_errors:
        raise ValueError("candidate manifest is schema-invalid: " + "; ".join(schema_errors))

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(PROJECT_POETICS_TEMPLATE.read_bytes())
    errors, warnings = doctor(root, candidate)
    if errors:
        target.unlink(missing_ok=True)
        raise ValueError("Project Poetics bootstrap would leave project inconsistent: " + "; ".join(errors))

    return candidate, {
        "changed": True,
        "artifact_path": rel,
        "status": "created-blank-provisional",
        "inference_performed": False,
        "context_generation": next_generation,
        "provenance": provenance,
        "warnings": warnings,
    }


def make_manifest(root: Path, project_id: str | None, profile: str, *, migration_from: str | None = None) -> dict[str, Any]:
    paths = infer_paths(root)
    existing_project_id = infer_project_id(root, paths)
    if project_id and existing_project_id and project_id != existing_project_id:
        raise ValueError(f"supplied project_id {project_id} disagrees with existing Runtime project_id {existing_project_id}")
    resolved_project_id = existing_project_id or project_id
    if not resolved_project_id:
        raise ValueError("project_id is required when it cannot be inferred from an existing Runtime manifest")
    manifest: dict[str, Any] = {
        "project_format_version": CURRENT_PROJECT_FORMAT,
        "schema_dialect": DIALECT,
        "project_id": resolved_project_id,
        "governance_profile": profile,
        "current_branch": infer_branch(root, paths),
        "current_chapter": infer_chapter(root, paths),
        "last_committed_event": find_last_event(root, paths.get("runtime_manifest")),
        "context_generation": 1 if "context_index" in paths else 0,
        "context_generation_history": [],
        "enabled_subsystems": sorted(set(default_subsystems(profile)) | infer_existing_subsystems(root, paths)),
        "humanities_analysis_policy": default_humanities_analysis_policy(),
        "canonical_paths": paths,
        "optional_artifacts": [],
        "poetics_override_refs": [],
        "user_locked_constraints_path": paths.get("project_brief"),
        "migration_history": [],
    }
    if migration_from:
        manifest["migration_history"].append(
            {
                "migration_id": f"project-format-{migration_from}-to-{CURRENT_PROJECT_FORMAT}",
                "from_version": migration_from,
                "to_version": CURRENT_PROJECT_FORMAT,
                "status": "applied",
                "timestamp": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
                "notes": "Created project-level manifest only; story prose, state, and runtime history were not rewritten.",
            }
        )
    return manifest


def doctor(root: Path, manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors = [f"schema {x}" for x in validate_schema(manifest)]
    warnings: list[str] = []
    if errors:
        return errors, warnings

    version = str(manifest.get("project_format_version"))
    got = parse_semver(version)
    cur = parse_semver(CURRENT_PROJECT_FORMAT)
    if got[0] > cur[0]:
        errors.append(f"project format major {got[0]} is newer than supported major {cur[0]}")
    elif got < cur:
        warnings.append(f"project format {version} is older than current {CURRENT_PROJECT_FORMAT}; migration may be available")

    current_generation = manifest.get("context_generation", 0)
    history = manifest.get("context_generation_history", [])
    if isinstance(current_generation, int) and isinstance(history, list):
        gens = [x.get("generation") for x in history if isinstance(x, dict) and isinstance(x.get("generation"), int)]
        if gens and max(gens) > current_generation:
            errors.append("context_generation_history contains a generation newer than context_generation")
        if gens and gens != sorted(gens):
            warnings.append("context_generation_history is not monotonic")

    humanities_policy = manifest.get("humanities_analysis_policy")
    if humanities_policy is None:
        humanities_policy = default_humanities_analysis_policy()
    if isinstance(humanities_policy, dict):
        mode = str(humanities_policy.get("mode", "opt_in"))
        milestones = humanities_policy.get("milestones", [])
        diagnostic_triggers = humanities_policy.get("diagnostic_triggers", [])
        chapter_interval = humanities_policy.get("chapter_interval")
        if mode == "milestone" and not milestones:
            warnings.append("humanities_analysis_policy mode=milestone has no configured milestones; no automatic report will run")
        if mode == "diagnostic" and not diagnostic_triggers:
            warnings.append("humanities_analysis_policy mode=diagnostic has no configured diagnostic_triggers; no automatic report will run")
        if mode == "custom" and not milestones and not diagnostic_triggers and chapter_interval is None:
            warnings.append("humanities_analysis_policy mode=custom has no configured triggers; behavior is effectively opt_in")
        if mode != "custom" and chapter_interval is not None:
            errors.append("humanities_analysis_policy.chapter_interval is allowed only when mode=custom")

    profile = str(manifest.get("governance_profile"))
    rec = profile_table().get(profile, {})
    required = set(str(x) for x in rec.get("required_subsystems", []) if x is not None) if isinstance(rec, dict) else set()
    enabled = set(str(x) for x in manifest.get("enabled_subsystems", []) if x is not None)
    missing_subsystems = sorted(required - enabled)
    if missing_subsystems:
        errors.append(f"governance profile {profile} missing required subsystems: {', '.join(missing_subsystems)}")

    for subsystem, deps in subsystem_dependencies().items():
        if subsystem not in enabled:
            continue
        missing = sorted(set(deps) - enabled)
        if missing:
            errors.append(f"enabled subsystem {subsystem} missing dependency subsystem(s): {', '.join(missing)}")

    paths = manifest.get("canonical_paths", {})
    if not isinstance(paths, dict):
        return errors + ["canonical_paths must be an object"], warnings

    poetics_rel = paths.get("project_poetics")
    poetics_provenance = manifest.get("project_poetics_provenance")
    if poetics_provenance is not None:
        if not isinstance(poetics_provenance, dict):
            errors.append("project_poetics_provenance must be an object")
        else:
            prov_path = poetics_provenance.get("artifact_path")
            if not isinstance(poetics_rel, str) or not poetics_rel:
                errors.append("project_poetics_provenance exists but canonical_paths.project_poetics is missing")
            elif prov_path != poetics_rel:
                errors.append(
                    "project_poetics_provenance.artifact_path disagrees with canonical_paths.project_poetics"
                )
            if poetics_provenance.get("inference_performed") is not False:
                errors.append("Project Poetics bootstrap provenance must record inference_performed=false")

    if not isinstance(poetics_rel, str) or not poetics_rel:
        migration_history = manifest.get("migration_history", [])
        if isinstance(migration_history, list) and any(
            isinstance(row, dict) and row.get("from_version") == "legacy-unversioned"
            for row in migration_history
        ):
            warnings.append(
                "legacy project has no Project Poetics canonical owner; run explicit ensure-poetics "
                "to create a blank provisional owner without inferring literary commitments"
            )

    dir_keys = {"chapters_dir", "scenes_dir", "revisions_dir", "reconciliations_dir"}
    for key, rel in paths.items():
        if not isinstance(rel, str) or not rel:
            continue
        try:
            target = safe_path(root, rel)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if key in dir_keys:
            if not target.exists():
                warnings.append(f"canonical directory not present yet: {key}={rel}")
            elif not target.is_dir():
                errors.append(f"canonical path should be a directory: {key}={rel}")
        else:
            if not target.exists():
                if key == "story_state":
                    errors.append(f"missing required canonical artifact: {key}={rel}")
                else:
                    warnings.append(f"canonical artifact not present: {key}={rel}")
            elif not target.is_file():
                errors.append(f"canonical path should be a file: {key}={rel}")

    optional_artifacts = manifest.get("optional_artifacts", [])
    if not isinstance(optional_artifacts, list):
        errors.append("optional_artifacts must be an array")
    else:
        for idx, record in enumerate(optional_artifacts):
            if not isinstance(record, dict):
                errors.append(f"optional_artifacts[{idx}] must be an object")
                continue
            rel = record.get("path")
            if not isinstance(rel, str) or not rel.strip():
                errors.append(f"optional_artifacts[{idx}].path must be a non-empty string")
                continue
            try:
                target = safe_path(root, rel)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            status = str(record.get("status", "provisional")).strip().lower()
            if not target.exists():
                if status in {"active", "required"}:
                    errors.append(f"active optional artifact is missing: {rel}")
                else:
                    warnings.append(f"optional artifact not present: {rel} (status={status})")
            elif not target.is_file():
                errors.append(f"optional artifact path should be a file: {rel}")

    override_refs = manifest.get("poetics_override_refs", [])
    if not isinstance(override_refs, list):
        errors.append("poetics_override_refs must be an array")
    else:
        for idx, rel in enumerate(override_refs):
            if not isinstance(rel, str) or not rel.strip():
                errors.append(f"poetics_override_refs[{idx}] must be a non-empty string")
                continue
            try:
                target = safe_path(root, rel)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not target.exists():
                errors.append(f"poetics override not found: {rel}")
            elif not target.is_file():
                errors.append(f"poetics override path should be a file: {rel}")

    state_rel = paths.get("story_state")
    if isinstance(state_rel, str):
        state_path = safe_path(root, state_rel)
        if state_path.is_file():
            try:
                state = load_json(state_path)
            except Exception as exc:
                errors.append(f"cannot parse story_state: {exc}")
            else:
                if isinstance(state, dict):
                    ch = state.get("current_chapter")
                    if isinstance(ch, int) and ch != manifest.get("current_chapter"):
                        errors.append(f"chapter mismatch: manifest={manifest.get('current_chapter')} story_state={ch}")

    if "narrative-runtime" in enabled:
        runtime_rel = paths.get("runtime_manifest")
        if not isinstance(runtime_rel, str):
            errors.append("narrative-runtime enabled but canonical_paths.runtime_manifest is missing")
        else:
            runtime_path = safe_path(root, runtime_rel)
            if runtime_path.is_file():
                try:
                    runtime = load_json(runtime_path)
                except Exception as exc:
                    errors.append(f"cannot parse runtime manifest: {exc}")
                else:
                    if isinstance(runtime, dict):
                        if runtime.get("project_id") != manifest.get("project_id"):
                            errors.append("project_id mismatch between project and runtime manifests")
                        if runtime.get("current_branch") != manifest.get("current_branch"):
                            errors.append("current_branch mismatch between project and runtime manifests")
            else:
                errors.append(f"narrative-runtime enabled but runtime manifest not found: {runtime_rel}")

    for subsystem, keys in subsystem_path_requirements().items():
        if subsystem not in enabled:
            continue
        for key in keys:
            rel = paths.get(key)
            if not isinstance(rel, str) or not rel:
                errors.append(f"enabled subsystem {subsystem} requires canonical_paths.{key}")
                continue
            target = safe_path(root, rel)
            if not target.exists():
                errors.append(f"enabled subsystem {subsystem} requires existing {key}: {rel}")

    # The inverse contract matters too: a path declared canonical should not belong to
    # a subsystem that the manifest claims is disabled. This catches stale manifests that
    # keep durable revision/reconciliation/research artifacts without declaring their owner.
    path_owners: dict[str, set[str]] = {}
    for subsystem, keys in subsystem_path_requirements().items():
        for key in keys:
            path_owners.setdefault(key, set()).add(subsystem)
    for key, owners in path_owners.items():
        rel = paths.get(key)
        if not isinstance(rel, str) or not rel:
            continue
        if not (owners & enabled):
            errors.append(
                f"canonical_paths.{key} is active but none of its owning subsystems are enabled: "
                f"{', '.join(sorted(owners))}"
            )

    actual_last = find_last_event(root, paths.get("runtime_manifest") if isinstance(paths.get("runtime_manifest"), str) else None)
    recorded_last = manifest.get("last_committed_event")
    if actual_last and recorded_last and actual_last != recorded_last:
        warnings.append(f"last_committed_event is stale: manifest={recorded_last} runtime={actual_last}")
    elif actual_last and recorded_last is None:
        warnings.append(f"last_committed_event missing from manifest; runtime head is {actual_last}")

    return errors, warnings


def load_reader_helpers() -> tuple[Any, Any]:
    try:
        from reader_state import foreground_questions, reader_state_at  # type: ignore
        return reader_state_at, foreground_questions
    except Exception:
        return None, None


def load_research_helper() -> Any:
    try:
        from research_freshness import stale_research_dependencies  # type: ignore
        return stale_research_dependencies
    except Exception:
        return None


def resume_capsule(root: Path, manifest: dict[str, Any]) -> str:
    paths = manifest.get("canonical_paths", {}) if isinstance(manifest.get("canonical_paths"), dict) else {}
    state: dict[str, Any] = {}
    state_rel = paths.get("story_state")
    if isinstance(state_rel, str):
        p = safe_path(root, state_rel)
        if p.is_file():
            raw = load_json(p)
            if isinstance(raw, dict):
                state = raw

    active_threads = [
        x for x in state.get("threads", [])
        if isinstance(x, dict) and str(x.get("status", "active")).lower() not in {"resolved", "retired", "closed"}
    ]
    unknowns = [
        x for x in state.get("authorial_unknowns", [])
        if isinstance(x, dict) and active_issue(x)
    ]
    reader_state_at, foreground_questions = load_reader_helpers()
    reader_questions: list[Any] = []
    if reader_state_at and foreground_questions:
        try:
            reader_questions = foreground_questions(reader_state_at(state)) or []
        except Exception:
            reader_questions = []
    stale_research_dependencies = load_research_helper()
    stale_research: list[dict[str, Any]] = []
    if stale_research_dependencies:
        try:
            stale_research = stale_research_dependencies(state)
        except Exception:
            stale_research = []

    lines = [
        "# Resume Capsule",
        "",
        "> Director-facing recovery artifact. It is not a Writer context pack and may reference author-level project state.",
        "",
        f"- project_id: {manifest.get('project_id')}",
        f"- project_format_version: {manifest.get('project_format_version')}",
        f"- governance_profile: {manifest.get('governance_profile')}",
        f"- current_branch: {manifest.get('current_branch')}",
        f"- current_chapter: {manifest.get('current_chapter')}",
        f"- last_committed_event: {manifest.get('last_committed_event')}",
        f"- context_generation: {manifest.get('context_generation')}",
        f"- humanities_analysis_policy: {json.dumps(manifest.get('humanities_analysis_policy', default_humanities_analysis_policy()), ensure_ascii=False)}",
        f"- project_poetics: {manifest.get('canonical_paths', {}).get('project_poetics')}",
        f"- poetics_override_refs: {json.dumps(manifest.get('poetics_override_refs', []), ensure_ascii=False)}",
        f"- optional_artifacts: {json.dumps(manifest.get('optional_artifacts', []), ensure_ascii=False)}",
        "",
        "## Canonical pointers",
        "",
    ]
    for key in sorted(paths):
        lines.append(f"- {key}: `{paths[key]}`")

    lines.extend(["", "## Active story pressure", ""])
    if active_threads:
        for row in active_threads[:20]:
            ident = row.get("id", row.get("thread_id", "?"))
            label = row.get("name", row.get("summary", row.get("question", "")))
            lines.append(f"- {ident}: {label}")
    else:
        lines.append("- no active thread records found")

    lines.extend(["", "## Reader foreground", ""])
    if isinstance(reader_questions, list) and reader_questions:
        for q in reader_questions[:20]:
            if isinstance(q, dict):
                lines.append(f"- {q.get('id', '?')}: {q.get('question', q.get('text', ''))}")
            else:
                lines.append(f"- {q}")
    else:
        lines.append("- no foreground reader questions found")

    lines.extend(["", "## Open authorial issues", ""])
    if unknowns:
        for idx, row in enumerate(unknowns[:20]):
            qid = issue_id(row, idx)
            if is_v2(row):
                policy = row.get("resolution_policy", "?")
                horizon = row.get("decision_horizon")
                suffix = f"; horizon={horizon}" if horizon not in (None, "") else ""
                lines.append(f"- {qid}: {policy}{suffix}")
            else:
                mode = row.get("mode", "legacy-open")
                review = "; semantic-upgrade-review" if str(mode) == "DELIBERATELY_UNRESOLVED" else ""
                lines.append(f"- {qid}: {mode}{review}")
    else:
        lines.append("- none registered")

    lines.extend(["", "## Research freshness", "", f"- stale dependencies: {len(stale_research)}"])
    for row in stale_research[:20]:
        lines.append(f"- {row.get('id', '?')}: {row.get('scope', '')}")

    lines.extend([
        "",
        "## Resume rule",
        "",
        "Reload the canonical owners needed for the next action from the pointers above. Do not treat this capsule as canon, and do not pass it directly to a blind Writer; compile a role-scoped context pack instead.",
        "",
    ])
    return "\n".join(lines)


def print_result(errors: list[str], warnings: list[str], *, as_json: bool) -> int:
    if as_json:
        print(json.dumps({"errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    else:
        for x in errors:
            print(f"ERROR: {x}")
        for x in warnings:
            print(f"WARNING: {x}")
        if not errors and not warnings:
            print("OK: project manifest and canonical pointers are consistent")
    return 1 if errors else 0



# P0-6 metadata belongs to Project State, not a parallel chapter database.
ROLLOVER_FIELDS = ("previous_final_chapter_id", "previous_final_prose_sha256",
                   "state_snapshot_id", "reconciliation_id")


def rollover_digest(value: Any) -> str:
    from semantic_kernel import stable_hash
    return stable_hash(value)


def rollover_file_hash(path: Path) -> str:
    from prose_state_reconcile import file_sha
    return file_sha(path)


def atomic_publish(path: Path, content: bytes, recheck: Any = None, *, immutable: bool = False) -> None:
    """Stage locally; validate immediately before atomic replacement. No distributed lock."""
    import os
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".rollover-", delete=False) as f:
            temp = Path(f.name)
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        if recheck:
            recheck()
        if immutable and path.exists():
            if path.read_bytes() != content:
                raise ValueError("rollover.immutable_identity_conflict")
            return
        os.replace(temp, path)
    finally:
        if temp and temp.exists():
            temp.unlink()


def rollover_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def rollover_project(root: Path, request: dict | None = None) -> tuple[dict, Path]:
    """The standard project entrypoint wins over caller-selected alternate manifests."""
    root = root.resolve()
    canonical = root / "project-manifest.json"
    rel = (request or {}).get("project_manifest")
    selected = safe_path(root, rel) if rel else canonical
    if canonical.is_file():
        manifest = load_json(canonical)
        if "chapter_rollover" in manifest and selected != canonical:
            raise ValueError("rollover.noncanonical_project")
        return manifest, canonical
    return (load_json(selected), selected) if selected.is_file() else ({}, selected)


def rollover_records(manifest: dict) -> list[dict]:
    # Absence is legacy; an explicitly present value must satisfy activation.
    if "chapter_rollover" not in manifest:
        return []
    block = manifest["chapter_rollover"]
    if not isinstance(block, dict) or block.get("contract_version") != "1.0.0" or block.get("active") is not True:
        raise ValueError("rollover.invalid_activation")
    records = block.get("chapters")
    if not isinstance(records, list):
        raise ValueError("rollover.invalid_registry")
    keys, ids = set(), set()
    for row in records:
        key = (row["branch"], row["number"])
        ident = (row["branch"], row["chapter_id"])
        if key in keys or ident in ids or type(row["number"]) is not int or row["number"] < 1:
            raise ValueError("rollover.ambiguous_chapter")
        keys.add(key); ids.add(ident)
    return records


def resolve_final(root: Path, manifest: dict, chapter_id: str, branch: str) -> tuple[dict, dict]:
    rows = [r for r in rollover_records(manifest) if r["chapter_id"] == chapter_id and r["branch"] == branch]
    if len(rows) != 1:
        raise ValueError("rollover.chapter_mismatch")
    chapter = rows[0]
    finals = [r for r in chapter["finalizations"] if r["finalization_id"] == chapter["current_finalization_id"]]
    if len(finals) != 1:
        raise ValueError("rollover.final_not_ready")
    final = finals[0]
    payload = {k: v for k, v in final.items() if k != "finalization_id"}
    if final["finalization_id"] != "FINAL-" + rollover_digest(payload) or not final["approval_ref"].strip() or not final["approved_by"].strip():
        raise ValueError("rollover.final_approval_invalid")
    if (final["chapter_id"], final["branch"], final["project_id"]) != (chapter_id, branch, manifest["project_id"]):
        raise ValueError("rollover.chapter_mismatch")
    prose = safe_path(root, final["path"])
    if not prose.is_file() or rollover_file_hash(prose) != final["final_prose_sha256"]:
        raise ValueError("rollover.previous_hash_stale")
    return chapter, final


def register_final(root: Path, chapter_id: str, number: int, prose_ref: str,
                   expected_sha256: str, approved_by: str, approval_ref: str) -> dict:
    """Import explicit approval of exact bytes. Never infer final from a report or name."""
    import copy
    root = root.resolve()
    manifest, mp = rollover_project(root)
    old_hash = rollover_file_hash(mp)
    candidate = copy.deepcopy(manifest)
    if not chapter_id.strip() or type(number) is not int or number < 1 or not approved_by.strip() or not approval_ref.strip():
        raise ValueError("rollover.explicit_approval_required")
    branch = manifest.get("current_branch", "main")
    prose = safe_path(root, prose_ref)
    directory = safe_path(root, manifest["canonical_paths"]["chapters_dir"])
    prose.relative_to(directory)
    content = prose.read_bytes()
    if rollover_file_hash(prose) != expected_sha256:
        raise ValueError("rollover.approval_hash_mismatch")
    candidate.setdefault("chapter_rollover", {"contract_version": "1.0.0", "active": True, "chapters": []})
    records = rollover_records(candidate)
    matches = [r for r in records if r["branch"] == branch and (r["chapter_id"] == chapter_id or r["number"] == number)]
    if matches and (len(matches) != 1 or matches[0]["chapter_id"] != chapter_id or matches[0]["number"] != number):
        raise ValueError("rollover.ambiguous_chapter")
    chapter = matches[0] if matches else {"chapter_id": chapter_id, "number": number, "branch": branch, "finalizations": [], "receipts": []}
    if not matches:
        records.append(chapter)
    archive = directory / ".approved" / (expected_sha256 + ".md")
    payload = {"chapter_id": chapter_id, "branch": branch, "project_id": manifest["project_id"],
               "path": prose.relative_to(root).as_posix(), "final_prose_sha256": expected_sha256,
               "approved_copy_path": archive.relative_to(root).as_posix(), "approved_by": approved_by,
               "approval_ref": approval_ref, "algorithm": "sha256-exact-bytes"}
    final = {**payload, "finalization_id": "FINAL-" + rollover_digest(payload)}
    if not any(r["finalization_id"] == final["finalization_id"] for r in chapter["finalizations"]):
        chapter["finalizations"].append(final)
    chapter["current_finalization_id"] = final["finalization_id"]
    # Old freeze/receipt bindings stay historical and will fail live comparison.
    def recheck():
        if rollover_file_hash(mp) != old_hash or rollover_file_hash(prose) != expected_sha256:
            raise ValueError("rollover.source_changed_before_publish")
    atomic_publish(archive, content, recheck, immutable=True)
    atomic_publish(mp, rollover_json_bytes(candidate), recheck)
    return final


def rollover_state(root: Path, manifest: dict) -> dict:
    """Read the existing full canonical state owner; never accept a scoped caller export."""
    from semantic_kernel import verify_runtime
    runtime, _ = (None, None)
    if manifest.get("canonical_paths", {}).get("runtime_manifest"):
        rows = []
        runtime = verify_runtime(root, manifest, rows)
        if any(r["status"] == "fail" for r in rows) or not runtime.get("projection"):
            # An empty projection is legal if the runtime data itself is present.
            if any(r["status"] == "fail" for r in rows) or "projection" not in runtime:
                raise ValueError("rollover.state_snapshot_mismatch")
        branch = manifest.get("current_branch", "main")
        effective = runtime["effective"]
        return {"state": runtime["projection"], "branch": branch,
                "through_event": effective[-1]["event_id"] if effective else None}
    path = safe_path(root, manifest["canonical_paths"]["story_state"])
    state = load_json(path)
    from validate_story_state import validate_issues
    if not isinstance(state, dict) or any(x["severity"] == "error" for x in validate_issues(state)):
        raise ValueError("rollover.state_snapshot_mismatch")
    return {"state": state, "branch": manifest.get("current_branch", "main"), "through_event": None}


def receipt_identity(receipt: dict) -> str:
    return "RECON-" + rollover_digest({k: v for k, v in receipt.items() if k != "reconciliation_id"})


def validate_freeze(root: Path, manifest: dict, chapter: dict, final: dict) -> dict:
    """Live four-way closure; no saved FRESH flag is trusted."""
    pointer = chapter.get("current_rollover")
    if not isinstance(pointer, dict):
        raise ValueError("rollover.not_ready")
    path = safe_path(root, pointer["receipt_path"])
    if rollover_file_hash(path) != pointer["receipt_sha256"]:
        raise ValueError("rollover.reconciliation_tampered")
    receipt = load_json(path)
    binding = receipt["rollover_receipt"]
    if receipt.get("reconciliation_id") != receipt_identity(receipt) or pointer["reconciliation_id"] != receipt["reconciliation_id"]:
        raise ValueError("rollover.reconciliation_mismatch")
    if (binding["project_id"], receipt["branch"], receipt["chapter_id"]) != (manifest["project_id"], final["branch"], chapter["chapter_id"]):
        raise ValueError("rollover.chapter_mismatch")
    if binding["finalization_id"] != final["finalization_id"] or receipt["prose_sha256"] != final["final_prose_sha256"] or binding["input_final_prose_sha256"] != final["final_prose_sha256"]:
        raise ValueError("rollover.reconciliation_stale")
    if safe_path(root, receipt["prose_path"]) != safe_path(root, final["path"]):
        raise ValueError("rollover.noncanonical_previous_file")
    if receipt["status"] != "APPROVED" or binding["verification"] != "VERIFIED":
        raise ValueError("rollover.reconciliation_unverified")
    snap_ref = binding["snapshot"]
    snap_path = safe_path(root, snap_ref["path"])
    if rollover_file_hash(snap_path) != snap_ref["sha256"]:
        raise ValueError("rollover.state_snapshot_mismatch")
    snapshot = load_json(snap_path)
    if snap_ref["state_snapshot_id"] != "STATE-" + rollover_digest(snapshot) or pointer["state_snapshot_id"] != snap_ref["state_snapshot_id"]:
        raise ValueError("rollover.state_snapshot_mismatch")
    current = rollover_state(root, manifest)
    if snapshot["project_id"] != manifest["project_id"] or snapshot["branch"] != final["branch"] or any(snapshot[k] != current[k] for k in ("state", "branch", "through_event")):
        raise ValueError("rollover.state_snapshot_mismatch")
    if binding["effect"] == "FORMAT_ONLY_NO_STATE_DELTA":
        from prose_state_reconcile import verify_formatting_receipt
        verify_formatting_receipt(root, manifest, chapter, final, receipt)
    else:
        from prose_state_reconcile import validate_report
        errors, _, _ = validate_report(receipt, root, strict=True)
        from prose_state_reconcile import leaf_values
        inventory = leaf_values(current["state"])
        if any(d.get("target") not in inventory or "after" not in d or inventory[d["target"]] != d["after"] for d in receipt.get("state_deltas", [])):
            raise ValueError("rollover.durable_delta_not_committed")
        if errors or receipt.get("reconciliation_version") != "1.1.0" or not receipt.get("semantic_review", {}).get("state_snapshot"):
            raise ValueError("rollover.reconciliation_unverified")
    return {"previous_final_chapter_id": chapter["chapter_id"],
            "previous_final_prose_sha256": final["final_prose_sha256"],
            "state_snapshot_id": snap_ref["state_snapshot_id"], "reconciliation_id": receipt["reconciliation_id"]}


def rollover_view(root: Path, request: dict | None = None) -> dict:
    """Read-only public status. Diagnostics contain only stable codes/opaque identities."""
    result = {"status": "UNVERIFIED", "tuple": None, "codes": [], "stale_artifacts": []}
    try:
        manifest, _ = rollover_project(root, request)
        records = rollover_records(manifest)
        if "chapter_rollover" not in manifest:
            return result
        # Active applicability needs the schema-required canonical chapter state.
        if type(manifest.get("current_chapter")) is not int or manifest["current_chapter"] < 0:
            raise ValueError("rollover.invalid_evidence")
        branch = manifest.get("current_branch", "main")
        records = [r for r in records if r["branch"] == branch]
        target = max((r["number"] for r in records), default=0) + 1
        result["target_chapter"] = target
        if request is not None:
            if request.get("branch", branch) != branch:
                raise ValueError("rollover.branch_mismatch")
            if type(request.get("target_chapter")) is not int or request["target_chapter"] != target:
                raise ValueError("rollover.target_chapter_mismatch")
        if target == 1:
            if manifest["current_chapter"] > 0:
                raise ValueError("rollover.missing_predecessor_authority")
            result["status"] = "NOT_APPLICABLE"
            if request and request.get("previous_chapter"):
                raise ValueError("rollover.unexpected_predecessor")
            return result
        chapter = next(r for r in records if r["number"] == target - 1)
        result["chapter_id"] = chapter["chapter_id"]
        final_rows = chapter.get("finalizations", [])
        declared = next((f for f in final_rows if f["finalization_id"] == chapter.get("current_finalization_id")), {})
        result["expected_final_prose_sha256"] = declared.get("final_prose_sha256")
        if declared.get("path") and safe_path(root, declared["path"]).is_file():
            result["actual_final_prose_sha256"] = rollover_file_hash(safe_path(root, declared["path"]))
        chapter, final = resolve_final(root, manifest, chapter["chapter_id"], branch)
        result["tuple"] = validate_freeze(root, manifest, chapter, final)
        if request is not None:
            binding = request.get("previous_chapter")
            if not isinstance(binding, dict) or any(not binding.get(k) for k in ROLLOVER_FIELDS):
                raise ValueError("rollover.missing_binding")
            for k in ROLLOVER_FIELDS:
                if binding[k] != result["tuple"][k]:
                    raise ValueError({"previous_final_chapter_id": "rollover.chapter_mismatch", "previous_final_prose_sha256": "rollover.previous_hash_stale", "state_snapshot_id": "rollover.state_snapshot_mismatch", "reconciliation_id": "rollover.reconciliation_mismatch"}[k])
            for key in ("previous_chapter_path", "previous_final_prose_path"):
                if key in request and safe_path(root, request[key]) != safe_path(root, final["path"]):
                    raise ValueError("rollover.noncanonical_previous_file")
            if "path" in binding and safe_path(root, binding["path"]) != safe_path(root, final["path"]):
                raise ValueError("rollover.noncanonical_previous_file")
        result["status"] = "FRESH"
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        import sys as _sys
        exc = _sys.exc_info()[1]
        code = str(exc) if isinstance(exc, ValueError) and str(exc).startswith("rollover.") else "rollover.invalid_evidence"
        result.update(status="STALE", codes=[code])
    return result


def rollover_artifact_errors(root: Path, entries: list[dict], selected: list[dict], view: dict) -> list[str]:
    """Use the existing Context Index provenance links, bounded to the predecessor."""
    if view["status"] != "FRESH":
        return []
    by_id = {e["id"]: e for e in entries}
    manifest, _ = rollover_project(root)
    chapter, final = resolve_final(root, manifest, view["chapter_id"], manifest.get("current_branch", "main"))
    def relevant(entry: dict, seen: set) -> bool:
        if entry["id"] in seen:
            raise ValueError("rollover.provenance_cycle")
        direct = ("rollover" in entry or entry.get("chapter") == chapter["number"] or
                  entry.get("kind") in {"recent-prose", "previous-chapter-summary", "context-summary", "writer-pack"} or
                  safe_path(root, entry["path"]) in {safe_path(root, f["path"]) for f in chapter["finalizations"]})
        return direct or any(relevant(by_id[p], seen | {entry["id"]}) for p in entry.get("derived_from", []) if p in by_id)
    errors = []
    for entry in selected:
        if not relevant(entry, set()):
            continue
        binding = entry.get("rollover")
        # Uncompressed canonical final bytes directly prove their own source identity.
        if safe_path(root, entry["path"]) == safe_path(root, final["path"]) and not entry.get("summary") and binding is None:
            continue
        try:
            if not isinstance(binding, dict) or binding.get("tuple") != view["tuple"]:
                raise ValueError("rollover.derived_artifact_stale")
            if binding.get("fingerprint") != rollover_digest({k: v for k, v in binding.items() if k != "fingerprint"}):
                raise ValueError("rollover.derived_artifact_stale")
            if binding.get("source_file_sha256") != rollover_file_hash(safe_path(root, entry["path"])):
                raise ValueError("rollover.derived_artifact_stale")
            if binding.get("summary_sha256") != (hashlib.sha256(entry["summary"].encode("utf-8")).hexdigest() if entry.get("summary") else None):
                raise ValueError("rollover.derived_artifact_stale")
            if not binding.get("review_ref"):
                raise ValueError("rollover.derived_artifact_stale")
        except (OSError, ValueError, KeyError, TypeError):
            errors.append("rollover.derived_artifact_stale")
    return sorted(set(errors))


def bind_rollover_artifact(root: Path, entry_id: str, review_ref: str) -> dict:
    manifest, _ = rollover_project(root)
    view = rollover_view(root)
    if view["status"] != "FRESH" or not review_ref.strip():
        raise ValueError("rollover.not_ready")
    path = safe_path(root, manifest["canonical_paths"]["context_index"])
    old_hash = rollover_file_hash(path)
    index = load_json(path)
    matches = [e for e in index["entries"] if e["id"] == entry_id]
    if len(matches) != 1:
        raise ValueError("rollover.artifact_identity_invalid")
    entry = matches[0]
    binding = {"tuple": view["tuple"], "source_file_sha256": rollover_file_hash(safe_path(root, entry["path"])),
               "summary_sha256": hashlib.sha256(entry["summary"].encode("utf-8")).hexdigest() if entry.get("summary") else None,
               "review_ref": review_ref}
    binding["fingerprint"] = rollover_digest(binding)
    entry["rollover"] = binding
    def recheck():
        if rollover_file_hash(path) != old_hash or rollover_view(root).get("tuple") != view["tuple"] or rollover_file_hash(safe_path(root, entry["path"])) != binding["source_file_sha256"]:
            raise ValueError("rollover.source_changed_before_publish")
    atomic_publish(path, rollover_json_bytes(index), recheck)
    return binding


def rollover_status(root: Path) -> dict:
    view = rollover_view(root)
    manifest, _ = rollover_project(root)
    if "chapter_rollover" not in manifest or view["status"] == "NOT_APPLICABLE":
        return view
    paths = manifest.get("canonical_paths", {})
    index_ref = paths.get("context_index")
    if index_ref and safe_path(root, index_ref).is_file():
        from compile_context import allowed
        entries = load_json(safe_path(root, index_ref)).get("entries", [])
        req = {"role": "writer", "branch": manifest.get("current_branch", "main"), "target_chapter": view.get("target_chapter", 1)}
        for e in entries:
            if not allowed(e, req)[0]:
                continue
            stale = (rollover_artifact_errors(root, entries, [e], view) if view["status"] == "FRESH" else
                     ("rollover" in e or e.get("kind") in {"recent-prose", "previous-chapter-summary", "context-summary", "writer-pack"}))
            if stale:
                view["stale_artifacts"].append({"id": e["id"], "code": "rollover.derived_artifact_stale"})
    pack_ref = paths.get("writer_pack_manifest")
    if pack_ref and safe_path(root, pack_ref).is_file():
        pack = load_json(safe_path(root, pack_ref))
        bad = pack.get("previous_chapter") != view.get("tuple") or view["status"] != "FRESH"
        if not bad:
            from compile_context import compile_pack
            request_ref, content_ref = paths.get("writer_request"), paths.get("writer_pack")
            if not request_ref or not content_ref or not index_ref:
                bad = True
            else:
                text, expected, errors = compile_pack(load_json(safe_path(root, index_ref)), load_json(safe_path(root, request_ref)), root)
                bad = bool(errors) or expected != pack or safe_path(root, content_ref).read_bytes() != text.encode("utf-8")
        if bad:
            view["stale_artifacts"].append({"id": "writer-pack", "code": "rollover.pack_stale"})
    if view["stale_artifacts"]:
        view["status"] = "STALE"
    return view


def operational_status(root: Path) -> dict[str, Any]:
    """Read-only aggregation. Each domain owner retains its authority and checks."""
    from validate_orchestration_run import operation_view, load_obj
    from semantic_kernel import verify_project
    from prewriting_readiness import audit, review_fingerprint

    root = root.resolve()
    manifest_path = root / "project-manifest.json"
    manifest = load_obj(manifest_path)
    paths = manifest.get("canonical_paths", {})
    if not isinstance(paths, dict):
        raise ValueError("canonical_paths must be an object")
    result: dict[str, Any] = {
        "previous_chapter_rollover": rollover_status(root),
        "current_snapshot": None, "gate": None, "draft_permission": None,
        "compile_status": None, "semantic_kernel_status": None,
        "current_chapter": manifest.get("current_chapter"), "current_branch": manifest.get("current_branch"),
        "stale_artifacts": rollover_status(root)["stale_artifacts"], "approval_binding": None, "active_run_status": None,
        "operations": {}, "report_conflicts": [], "errors": [],
        "sources": {"project": "project-manifest.json", "readiness": None, "active_run": None},
        "unavailable": [],
    }
    # The registered readiness ref wins; the bootstrap's documented standard path
    # is a compatibility location, never a guessed report/snapshot field.
    readiness_ref = paths.get("prewriting_readiness", "planning/prewriting-readiness.json")
    rp = safe_path(root, readiness_ref)
    if rp.is_file():
        result["sources"]["readiness"] = readiness_ref
        r = load_obj(rp)
        checked = audit(root, manifest_path, rp, recompile=True)
        result["gate"] = checked["gate"]
        result["draft_permission"] = checked["draft_permission"]
        result["readiness_audit"] = checked
        snapshot = r.get("review_snapshot")
        if snapshot:
            try:
                if not checked["ok"] or checked["gate"] not in {"REVIEW_READY", "DRAFT_READY"} or not isinstance(snapshot, dict) or not snapshot.get("id") or snapshot.get("fingerprint") != review_fingerprint(root, manifest_path, r):
                    raise ValueError("review snapshot fingerprint is stale or invalid")
                result["current_snapshot"] = {"id": snapshot["id"], "fingerprint": snapshot["fingerprint"], "status": "VERIFIED"}
            except Exception as exc:
                result["stale_artifacts"].append({"ref": readiness_ref, "reason": str(exc)})
        if r.get("author_approval"):
            result["approval_binding"] = {"status": "VERIFIED" if checked["draft_permission"] else "UNVERIFIED", "snapshot_id": snapshot.get("id") if isinstance(snapshot, dict) else None}
        # Only the readiness owner's live recompilation can validate its saved
        # handoff. A saved PASSED flag alone remains an unverified claim.
        hand = r.get("writer_handoff", {})
        if hand.get("compile_status") is not None:
            live_compile = r.get("gate") == "DRAFT_READY" or r.get("readiness_version") == "1.1.0"
            compile_errors = [x for x in checked.get("findings", []) if any(t in x.get("code", "") for t in ("compile", "pack", "invalid-evidence"))]
            result["compile_status"] = {"status": "VERIFIED" if live_compile and checked["ok"] and not compile_errors else "UNVERIFIED", "claimed_result": hand.get("compile_status"), "source": readiness_ref}
        for finding in checked.get("findings", []):
            if any(t in finding.get("code", "") for t in ("stale", "drift", "hash", "generation")):
                result["stale_artifacts"].append({"ref": readiness_ref, "reason": finding.get("message"), "code": finding.get("code")})
    else:
        result["unavailable"].extend(["current_snapshot", "gate", "draft_permission", "compile_status", "approval_binding"])
    kernel = verify_project(root)
    kernel_failed = bool(kernel.get("errors") or kernel.get("summary", {}).get("fail"))
    result["semantic_kernel_status"] = {"status": "FAILED" if kernel_failed else "VERIFIED", "method": "semantic_kernel.verify_project", "result": kernel}
    orchestration = manifest.get("orchestration", {})
    if not isinstance(orchestration, dict):
        raise ValueError("manifest orchestration must be an object")
    checkpoint_ref = orchestration.get("active_run_checkpoint")
    if checkpoint_ref is not None:
        result["sources"]["active_run"] = checkpoint_ref
        checkpoint = load_obj(safe_path(root, checkpoint_ref))
        if "operational_version" not in checkpoint:
            result["active_run_status"] = "LEGACY_UNKNOWN_VERIFICATION"
        else:
            from validate_orchestration_run import validate_checkpoint
            operations = checkpoint.get("operations", {})
            if not isinstance(operations, dict):
                raise ValueError("checkpoint operations must be an object")
            e, _ = validate_checkpoint(checkpoint, set(operations), checkpoint.get("execution_profile"), root)
            result["errors"].extend(e)
            for op_id, operation in operations.items():
                view = operation_view(operation, root)
                result["operations"][op_id] = view
                result["report_conflicts"].extend({"operation_id": op_id, **row} for row in view["report_conflicts"])
            views = list(result["operations"].values())
            states = [v["status"] for v in views]
            # Fail closed for an invalid declared run while retaining the strongest
            # evidence-supported per-operation state for diagnosis.
            result["active_run_status"] = "INVALID" if e else next((s for s in ("FAILED", "RUNNING", "PLANNED", "DONE", "VERIFIED") if s in states), None)
    else:
        result["unavailable"].append("active_run_checkpoint:not_registered")
    state_ref = paths.get("story_state")
    if state_ref:
        from research_freshness import stale_research_dependencies
        state = load_obj(safe_path(root, state_ref))
        result["stale_artifacts"].extend(stale_research_dependencies(state))
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    mig = sub.add_parser("migrate-legacy", help="create a v1 project manifest for an unversioned existing project without rewriting story data")
    mig.add_argument("root", type=Path)
    mig.add_argument("--project-id", help="optional when an existing Runtime manifest already provides project_id")
    mig.add_argument("--profile", choices=["lean", "persistent", "forensic"], required=True)
    mig.add_argument("--output", default="project-manifest.json")

    init = sub.add_parser("init", help="initialize a brand-new project at the minimal Lean governance baseline")
    init.add_argument("root", type=Path)
    init.add_argument("--project-id", required=True, help="stable project identity for the new project")
    init.add_argument("--output", default="project-manifest.json")

    verify = sub.add_parser("verify", help="validate project format and cross-file recovery contracts")
    verify.add_argument("manifest", type=Path)
    verify.add_argument("--root", type=Path)
    verify.add_argument("--json", action="store_true")

    inspect = sub.add_parser("inspect", help="print a compact machine-readable project identity summary")
    inspect.add_argument("manifest", type=Path)

    resume = sub.add_parser("resume", help="generate a Director-facing Resume Capsule from canonical state")
    resume.add_argument("manifest", type=Path)
    resume.add_argument("--root", type=Path)
    resume.add_argument("--out", type=Path)

    plan = sub.add_parser("plan-migration", help="report whether project-format migration is needed")
    plan.add_argument("manifest", type=Path)

    ensure_poetics = sub.add_parser(
        "ensure-poetics",
        help="explicitly establish a blank provisional Project Poetics canonical owner without inferring poetics",
    )
    ensure_poetics.add_argument("manifest", type=Path)
    ensure_poetics.add_argument("--root", type=Path, help="project root; defaults to the manifest directory")
    ensure_poetics.add_argument("--path", dest="poetics_path", help=f"project-relative canonical path; default: {DEFAULT_PROJECT_POETICS_PATH}")
    ensure_poetics.add_argument("--reason", help="optional provenance note for why the neutral owner is being established")
    ensure_poetics.add_argument("--json", action="store_true")

    profile_cmd = sub.add_parser("set-profile", help="raise governance intensity; explicit flag is required for a downgrade")
    profile_cmd.add_argument("manifest", type=Path)
    profile_cmd.add_argument("profile", choices=["lean", "persistent", "forensic"])
    profile_cmd.add_argument("--allow-downgrade", action="store_true")

    humanities_cmd = sub.add_parser("set-humanities-policy", help="configure optional humanities-sidecar scheduling; default behavior is opt-in only")
    humanities_cmd.add_argument("manifest", type=Path)
    humanities_cmd.add_argument("mode", choices=["opt_in", "milestone", "diagnostic", "custom"])
    humanities_cmd.add_argument("--milestone", action="append", default=[], help="named milestone trigger; repeat as needed")
    humanities_cmd.add_argument("--diagnostic-trigger", action="append", default=[], help="named diagnostic trigger; repeat as needed")
    humanities_cmd.add_argument("--chapter-interval", type=int, help="optional deliberate interval; allowed only in custom mode")
    humanities_cmd.add_argument("--notes", default="", help="optional user-facing policy note")

    bump = sub.add_parser("bump-context", help="advance project context generation after canonical context-governance inputs change")
    bump.add_argument("manifest", type=Path)
    bump.add_argument("--reason", required=True)

    final_cmd = sub.add_parser("finalize-chapter", help="register explicit approval of exact chapter bytes in Project State")
    final_cmd.add_argument("root", type=Path)
    final_cmd.add_argument("--chapter-id", required=True)
    final_cmd.add_argument("--chapter-number", type=int, required=True)
    final_cmd.add_argument("--prose", required=True)
    final_cmd.add_argument("--expected-sha256", required=True)
    final_cmd.add_argument("--approved-by", required=True)
    final_cmd.add_argument("--approval-ref", required=True)
    bind_cmd = sub.add_parser("bind-rollover-artifact", help="record reviewed regeneration provenance for a Context Index entry")
    bind_cmd.add_argument("root", type=Path)
    bind_cmd.add_argument("--entry-id", required=True)
    bind_cmd.add_argument("--review-ref", required=True)

    args = p.parse_args()
    try:
        require_profile("project")
    except CapabilityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.cmd in {"finalize-chapter", "bind-rollover-artifact"}:
        try:
            result = (register_final(args.root, args.chapter_id, args.chapter_number, args.prose,
                                     args.expected_sha256, args.approved_by, args.approval_ref)
                      if args.cmd == "finalize-chapter" else
                      bind_rollover_artifact(args.root, args.entry_id, args.review_ref))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        except (OSError, ValueError, KeyError, TypeError):
            print("ERROR: rollover.registration_failed; verify explicit authority and current source identity", file=sys.stderr)
            return 2

    if args.cmd in {"init", "migrate-legacy"}:
        root = args.root.resolve()
        root.mkdir(parents=True, exist_ok=True)
        output = safe_path(root, args.output)
        if output.exists():
            print(f"ERROR: manifest already exists: {output}; use verify/set-profile/migration instead of overwriting project recovery history", file=sys.stderr)
            return 2
        migration_from = "legacy-unversioned" if args.cmd == "migrate-legacy" else None
        profile = args.profile if args.cmd == "migrate-legacy" else "lean"
        if args.cmd == "init":
            ensure_fresh_lean_scaffold(root)
        try:
            manifest = make_manifest(root, args.project_id, profile, migration_from=migration_from)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        if args.cmd == "init":
            manifest["chapter_rollover"] = {"contract_version": "1.0.0", "active": True, "chapters": []}
        errs, warns = doctor(root, manifest)
        if errs:
            for x in errs:
                print(f"ERROR: generated project is not internally ready: {x}", file=sys.stderr)
            return 2
        for x in warns:
            print(f"WARNING: {x}", file=sys.stderr)
        save_json(output, manifest)
        print(output)
        return 0

    if args.cmd == "ensure-poetics":
        manifest = load_json(args.manifest)
        if not isinstance(manifest, dict):
            print("ERROR: manifest must be a JSON object", file=sys.stderr)
            return 2
        root = (args.root or args.manifest.resolve().parent).resolve()
        try:
            candidate, result = ensure_project_poetics(
                root,
                manifest,
                path_override=args.poetics_path,
                reason=args.reason,
            )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        if result.get("changed"):
            save_json(args.manifest, candidate)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result.get("artifact_path"))
            if not result.get("changed"):
                print("OK: Project Poetics canonical owner already exists; no files were rewritten", file=sys.stderr)
            for warning in result.get("warnings", []) if isinstance(result.get("warnings"), list) else []:
                print(f"WARNING: {warning}", file=sys.stderr)
        return 0

    if args.cmd == "bump-context":
        manifest = load_json(args.manifest)
        if not isinstance(manifest, dict):
            print("ERROR: manifest must be a JSON object", file=sys.stderr)
            return 2
        current = manifest.get("context_generation", 0)
        if not isinstance(current, int) or current < 0:
            print("ERROR: invalid context_generation", file=sys.stderr)
            return 2
        nxt = current + 1
        manifest["context_generation"] = nxt
        history = manifest.setdefault("context_generation_history", [])
        if not isinstance(history, list):
            print("ERROR: context_generation_history must be a list", file=sys.stderr)
            return 2
        history.append({
            "generation": nxt,
            "reason": args.reason,
            "timestamp": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        })
        save_json(args.manifest, manifest)
        print(nxt)
        return 0

    if args.cmd == "set-humanities-policy":
        manifest = load_json(args.manifest)
        if not isinstance(manifest, dict):
            print("ERROR: manifest must be a JSON object", file=sys.stderr)
            return 2
        if args.chapter_interval is not None and args.chapter_interval < 1:
            print("ERROR: --chapter-interval must be >= 1", file=sys.stderr)
            return 2
        if args.chapter_interval is not None and args.mode != "custom":
            print("ERROR: --chapter-interval is allowed only with mode=custom", file=sys.stderr)
            return 2
        policy: dict[str, Any] = {
            "mode": args.mode,
            "milestones": list(dict.fromkeys(args.milestone)),
            "diagnostic_triggers": list(dict.fromkeys(args.diagnostic_trigger)),
            "chapter_interval": args.chapter_interval,
        }
        if args.notes:
            policy["notes"] = args.notes
        candidate = dict(manifest)
        candidate["humanities_analysis_policy"] = policy
        if args.mode != "opt_in":
            candidate["enabled_subsystems"] = list(dict.fromkeys([*(str(x) for x in manifest.get("enabled_subsystems", [])), "humanities-sidecar"]))
        root = args.manifest.resolve().parent
        errs, warns = doctor(root, candidate)
        if errs:
            for x in errs:
                print(f"ERROR: humanities policy would leave project internally inconsistent: {x}", file=sys.stderr)
            return 2
        save_json(args.manifest, candidate)
        print(args.manifest)
        for x in warns:
            print(f"WARNING: {x}", file=sys.stderr)
        return 0

    if args.cmd == "set-profile":
        manifest = load_json(args.manifest)
        if not isinstance(manifest, dict):
            print("ERROR: manifest must be a JSON object", file=sys.stderr)
            return 2
        current = str(manifest.get("governance_profile", "lean"))
        rank = {"lean": 0, "persistent": 1, "forensic": 2}
        if rank.get(args.profile, -1) < rank.get(current, -1) and not args.allow_downgrade:
            print(
                f"ERROR: refusing automatic governance downgrade {current} -> {args.profile}; "
                "review the guarantees being removed and re-run with --allow-downgrade if deliberate",
                file=sys.stderr,
            )
            return 2
        candidate = dict(manifest)
        candidate["governance_profile"] = args.profile
        enabled = list(dict.fromkeys([*(str(x) for x in manifest.get("enabled_subsystems", [])), *default_subsystems(args.profile)]))
        candidate["enabled_subsystems"] = enabled
        root = args.manifest.resolve().parent
        errs, warns = doctor(root, candidate)
        if errs:
            for x in errs:
                print(f"ERROR: profile change would leave project internally inconsistent: {x}", file=sys.stderr)
            print("HINT: create/declare the required artifacts first, then retry set-profile; the manifest was not changed", file=sys.stderr)
            return 2
        save_json(args.manifest, candidate)
        print(args.manifest)
        for x in warns:
            print(f"WARNING: {x}", file=sys.stderr)
        if rank.get(args.profile, -1) < rank.get(current, -1):
            print("WARNING: profile label was downgraded but existing subsystems were preserved; disable protections only through an explicit reviewed edit", file=sys.stderr)
        return 0

    if args.cmd == "inspect":
        manifest = load_json(args.manifest)
        summary = {
            "project_id": manifest.get("project_id"),
            "project_format_version": manifest.get("project_format_version"),
            "governance_profile": manifest.get("governance_profile"),
            "current_branch": manifest.get("current_branch"),
            "current_chapter": manifest.get("current_chapter"),
            "last_committed_event": manifest.get("last_committed_event"),
            "context_generation": manifest.get("context_generation"),
            "humanities_analysis_policy": manifest.get("humanities_analysis_policy", default_humanities_analysis_policy()),
            "project_poetics": manifest.get("canonical_paths", {}).get("project_poetics") if isinstance(manifest.get("canonical_paths"), dict) else None,
            "project_poetics_provenance": manifest.get("project_poetics_provenance"),
            "optional_artifacts": manifest.get("optional_artifacts", []),
            "poetics_override_refs": manifest.get("poetics_override_refs", []),
            "enabled_subsystems": manifest.get("enabled_subsystems", []),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "plan-migration":
        manifest = load_json(args.manifest)
        current = str(manifest.get("project_format_version", "0.0.0"))
        if parse_semver(current) == parse_semver(CURRENT_PROJECT_FORMAT):
            print(json.dumps({"from_version": current, "to_version": CURRENT_PROJECT_FORMAT, "required": False, "steps": []}, indent=2))
            return 0
        print(json.dumps({
            "from_version": current,
            "to_version": CURRENT_PROJECT_FORMAT,
            "required": True,
            "supported_automatically": False,
            "steps": ["Preserve project data unchanged", "Apply an explicit reviewed migration path before updating the manifest version"],
        }, indent=2))
        return 1

    manifest = load_json(args.manifest)
    root = (args.root or args.manifest.parent).resolve()

    if args.cmd == "verify":
        errors, warnings = doctor(root, manifest)
        return print_result(errors, warnings, as_json=args.json)

    if args.cmd == "resume":
        errors, warnings = doctor(root, manifest)
        if errors:
            for x in errors:
                print(f"ERROR: {x}", file=sys.stderr)
            return 1
        for x in warnings:
            print(f"WARNING: {x}", file=sys.stderr)
        text = resume_capsule(root, manifest)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
