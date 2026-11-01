#!/usr/bin/env python3
"""Longitudinal evidence ledger for real long-form creative campaigns.

This tool records trace-grounded checkpoints and computes evidence maturity.
It does not generate chapters, invent canon, or replace canonical validators.
Synthetic long-horizon benchmarks are explicitly ineligible for live claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
REGISTRY_PATH = ROOT / "assets/live-campaign/campaign-registry.json"
SCHEMA_VERSION = "1.0.0"
ALLOWED_TRACKS = {
    "realist-mystery-persistent",
    "xianxia-progression-persistent",
    "time-loop-prophecy-forensic",
    "custom",
}
PROBE_KINDS = {"recall", "action", "update", "interference", "abstention", "permission", "reader", "branch"}
PROBE_STATUS = {"pass", "fail", "inconclusive"}
PROBE_MODES = {"observational", "intervention", "recovery"}
SESSION_OUTCOMES = {"completed", "aborted", "recovery-required", "no-chapter", "other"}
SESSION_LOGGING_SCOPES = {"checkpoint-linked-only", "all-creative-sessions"}
RESUME_MODES = {"cold-resume", "hiatus-resume", "model-change", "migration-resume", "other"}
CREATIVE_REF_KEYS = (
    "architecture_fingerprint_ref",
    "voice_drift_ref",
    "pairwise_eval_ref",
    "project_poetics_ref",
    "poetics_observatory_ref",
)
LEVEL_ORDER = {f"L{i}": i for i in range(7)}
LEVEL_REQS: dict[str, dict[str, Any]] = {
    "L0": {"chapter": 0, "checkpoints": [], "sessions": 0, "human": 0, "cold": 0, "probe_kinds": 0, "requires_action": False},
    "L1": {"chapter": 1, "checkpoints": [1], "sessions": 1, "human": 1, "cold": 0, "probe_kinds": 0, "requires_action": False},
    "L2": {"chapter": 25, "checkpoints": [1, 10, 25], "sessions": 2, "human": 1, "cold": 1, "probe_kinds": 1, "requires_action": True},
    "L3": {"chapter": 50, "checkpoints": [1, 10, 25, 50], "sessions": 3, "human": 2, "cold": 1, "probe_kinds": 3, "requires_action": True},
    "L4": {"chapter": 100, "checkpoints": [1, 10, 25, 50, 75, 100], "sessions": 4, "human": 3, "cold": 2, "probe_kinds": 4, "requires_action": True, "requires_observational_action": True},
    "L5": {"chapter": 200, "checkpoints": [1, 10, 25, 50, 75, 100, 150, 200], "sessions": 6, "human": 4, "cold": 2, "probe_kinds": 4, "requires_action": True, "requires_observational_action": True, "major_change": True},
    "L6": {"chapter": 300, "checkpoints": [1, 10, 25, 50, 75, 100, 150, 200, 250, 300], "sessions": 8, "human": 5, "cold": 2, "probe_kinds": 4, "requires_action": True, "requires_observational_action": True, "major_change": True, "creative_review": True},
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_meta(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        rel = str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        rel = str(path.resolve())
    return {
        "path": rel,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "characters": len(text),
        "lines": text.count("\n") + (0 if text.endswith("\n") or not text else 1),
    }


def run_backend(args: list[str], cwd: Path | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )
    parsed: Any = None
    stdout = proc.stdout.strip()
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None
    return {
        "returncode": proc.returncode,
        "passed": proc.returncode == 0,
        "json": parsed,
        "stdout_tail": stdout[-2000:] if parsed is None else None,
        "stderr_tail": proc.stderr.strip()[-2000:] or None,
    }


def canonical_offsets(target: int) -> list[int]:
    points = [1, 10, 25, 50, 75, 100, 150, 200, 250, 300]
    return [x for x in points if x <= target]


def canonical_checkpoints(target: int, registration_chapter: int = 0) -> list[int]:
    return [registration_chapter + offset for offset in canonical_offsets(target)]


def validate_registry_data(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        errors.append("registry.schema_version must be 1.0.0")
        return errors
    tracks = data.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        errors.append("registry.tracks must be a non-empty list")
        return errors
    seen: set[str] = set()
    for i, row in enumerate(tracks):
        if not isinstance(row, dict):
            errors.append(f"tracks[{i}] must be an object")
            continue
        tid = row.get("track_id")
        if not isinstance(tid, str) or not tid:
            errors.append(f"tracks[{i}].track_id missing")
        elif tid in seen:
            errors.append(f"duplicate track_id: {tid}")
        else:
            seen.add(tid)
        level = row.get("evidence_level")
        if level not in LEVEL_ORDER:
            errors.append(f"tracks[{i}].evidence_level invalid: {level}")
    return errors


def validate_manifest(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["campaign manifest must be an object"]
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append("manifest.schema_version must be 1.0.0")
    if data.get("campaign_type") != "live-creative-campaign":
        errors.append("manifest.campaign_type must be live-creative-campaign")
    cid = data.get("campaign_id")
    if not isinstance(cid, str) or not cid.strip():
        errors.append("manifest.campaign_id is required")
    tid = data.get("track_id")
    if tid not in ALLOWED_TRACKS:
        errors.append(f"manifest.track_id invalid: {tid}")
    pid = data.get("project_id")
    if not isinstance(pid, str) or not pid:
        errors.append("manifest.project_id is required")
    elif pid.startswith("LWA-LONG-HORIZON-"):
        errors.append("synthetic LWA-LONG-HORIZON projects are ineligible for live campaign evidence")
    target = data.get("target_chapters")
    if not isinstance(target, int) or target < 1 or target > 10000:
        errors.append("manifest.target_chapters must be an integer >= 1")
    att = data.get("source_attestation")
    if not isinstance(att, dict):
        errors.append("manifest.source_attestation must be an object")
    else:
        if att.get("synthetic") is not False:
            errors.append("live campaign attestation.synthetic must be false")
        if att.get("real_drafting_workflow") is not True:
            errors.append("live campaign attestation.real_drafting_workflow must be true")
    idx = data.get("checkpoint_index")
    if not isinstance(idx, list):
        errors.append("manifest.checkpoint_index must be a list")
    sessions = data.get("session_index")
    if not isinstance(sessions, list):
        errors.append("manifest.session_index must be a list")
    registration = data.get("registration")
    if not isinstance(registration, dict):
        errors.append("manifest.registration must be an object")
    else:
        registered_at = registration.get("registered_at_utc")
        if not isinstance(registered_at, str):
            errors.append("manifest.registration.registered_at_utc is required")
        else:
            try:
                parse_iso8601(registered_at)
            except ValueError:
                errors.append("manifest.registration.registered_at_utc must be timezone-aware ISO 8601")
        if not isinstance(registration.get("project_chapter"), int) or int(registration.get("project_chapter") or 0) < 0:
            errors.append("manifest.registration.project_chapter must be a non-negative integer")
        trace = registration.get("trace")
        if not isinstance(trace, dict) or not isinstance((trace.get("project_manifest") or {}).get("sha256"), str):
            errors.append("manifest.registration.trace.project_manifest.sha256 is required")
    att = data.get("source_attestation") or {}
    if isinstance(att, dict) and att.get("session_logging_scope") not in SESSION_LOGGING_SCOPES:
        errors.append("manifest.source_attestation.session_logging_scope is invalid")
    return errors


def parse_iso8601(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include an explicit timezone offset")
    return parsed


def temporal_span_class(days: float) -> str:
    if days >= 180:
        return "T180"
    if days >= 90:
        return "T90"
    if days >= 30:
        return "T30"
    if days >= 7:
        return "T7"
    if days >= 1:
        return "T1"
    return "T0"


def memory_horizon_class(gap: int) -> str:
    if gap >= 200:
        return "M200"
    if gap >= 100:
        return "M100"
    if gap >= 50:
        return "M50"
    if gap >= 25:
        return "M25"
    if gap >= 10:
        return "M10"
    if gap > 0:
        return "M1"
    return "M0"


def _artifact_ref(project_root: Path, raw: str, label: str) -> dict[str, Any]:
    path = resolve_project_path(project_root, raw)
    if not path.exists() or not path.is_file():
        raise ValueError(f"{label} artifact not found: {raw}")
    return file_meta(path, project_root)


def collect_probe_evidence(
    project_root: Path,
    probes: list[dict[str, Any]],
    checkpoint_chapter: int,
    registration_chapter: int = 0,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for probe in probes:
        raw = probe.get("evidence_ref")
        artifact = None
        if isinstance(raw, str) and raw.strip():
            artifact = _artifact_ref(project_root, raw, f"probe {probe.get('probe_id')}")
        source = probe.get("source_chapter")
        gap = checkpoint_chapter - source if isinstance(source, int) else None
        source_before_registration = bool(isinstance(source, int) and source <= registration_chapter)
        campaign_gap = gap if isinstance(gap, int) and not source_before_registration else None
        out.append({
            "probe_id": probe.get("probe_id"),
            "kind": probe.get("kind"),
            "mode": probe.get("mode"),
            "status": probe.get("status"),
            "source_chapter": source,
            "gap_chapters": gap,
            "source_before_registration": source_before_registration,
            "campaign_gap_chapters": campaign_gap,
            "artifact": artifact,
        })
    return out


def collect_creative_evidence(project_root: Path, creative: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in CREATIVE_REF_KEYS:
        raw = creative.get(key)
        if raw is None:
            continue
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"creative_longitudinal.{key} must be null or a project-relative path")
        out[key] = _artifact_ref(project_root, raw, f"creative longitudinal {key}")
    return out


def collect_resume_evidence(project_root: Path, resume_probe: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(resume_probe, dict) or resume_probe.get("performed") is not True:
        return None
    evidence_ref = resume_probe.get("evidence_ref")
    artifact = _artifact_ref(project_root, evidence_ref, "resume probe") if isinstance(evidence_ref, str) and evidence_ref.strip() else None
    loaded: list[dict[str, Any]] = []
    for raw in resume_probe.get("loaded_artifacts", []):
        loaded.append(_artifact_ref(project_root, raw, "resume loaded"))
    return {
        "mode": resume_probe.get("mode"),
        "evidence_artifact": artifact,
        "loaded_artifacts": loaded,
        "correct_next_action": resume_probe.get("correct_next_action"),
        "asked_known_information": resume_probe.get("asked_known_information"),
        "resurrected_stale_plan": resume_probe.get("resurrected_stale_plan"),
        "manual_repair_actions": resume_probe.get("manual_repair_actions"),
    }


def validate_checkpoint_input(data: Any, target: int, registration_chapter: int = 0) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["checkpoint input must be an object"]
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append("checkpoint.schema_version must be 1.0.0")
    chapter = data.get("chapter")
    first_observed = registration_chapter + 1
    last_observed = registration_chapter + target
    if not isinstance(chapter, int) or chapter < first_observed or chapter > last_observed:
        errors.append(f"checkpoint.chapter must be within the prospective campaign window {first_observed}..{last_observed}")
    for key in ("recorded_at", "session_id", "chapter_path"):
        if not isinstance(data.get(key), str) or not str(data.get(key)).strip():
            errors.append(f"checkpoint.{key} is required")
    recorded_at = data.get("recorded_at")
    if isinstance(recorded_at, str) and recorded_at.strip():
        try:
            parse_iso8601(recorded_at)
        except ValueError:
            errors.append("checkpoint.recorded_at must be valid ISO 8601 with an explicit timezone offset")
    human = data.get("human_review", {})
    if not isinstance(human, dict) or not isinstance(human.get("reviewed"), bool):
        errors.append("checkpoint.human_review.reviewed must be boolean")
    elif human.get("reviewed") is True:
        if not isinstance(human.get("reviewer_role"), str) or not human.get("reviewer_role", "").strip():
            errors.append("reviewed checkpoint requires human_review.reviewer_role")
        if not isinstance(human.get("notes"), str) or not human.get("notes", "").strip():
            errors.append("reviewed checkpoint requires non-empty human_review.notes")
    integrity = data.get("integrity_notes", {})
    if not isinstance(integrity, dict) or not isinstance(integrity.get("severe_blocker"), bool):
        errors.append("checkpoint.integrity_notes.severe_blocker must be boolean")
    probes = data.get("probes", [])
    if not isinstance(probes, list):
        errors.append("checkpoint.probes must be a list")
    else:
        ids: set[str] = set()
        for i, probe in enumerate(probes):
            if not isinstance(probe, dict):
                errors.append(f"probes[{i}] must be an object")
                continue
            pid = probe.get("probe_id")
            if not isinstance(pid, str) or not pid:
                errors.append(f"probes[{i}].probe_id is required")
            elif pid in ids:
                errors.append(f"duplicate probe_id in checkpoint: {pid}")
            else:
                ids.add(pid)
            if probe.get("kind") not in PROBE_KINDS:
                errors.append(f"probes[{i}].kind invalid: {probe.get('kind')}")
            if probe.get("status") not in PROBE_STATUS:
                errors.append(f"probes[{i}].status invalid: {probe.get('status')}")
            if probe.get("mode") not in PROBE_MODES:
                errors.append(f"probes[{i}].mode invalid: {probe.get('mode')}")
            source = probe.get("source_chapter")
            if source is not None and (not isinstance(source, int) or source < 1 or (isinstance(chapter, int) and source > chapter)):
                errors.append(f"probes[{i}].source_chapter must be within 1..checkpoint.chapter when provided")
            if probe.get("status") == "pass" and (not isinstance(probe.get("evidence_ref"), str) or not probe.get("evidence_ref").strip()):
                errors.append(f"probes[{i}] passing probe requires a project-relative evidence_ref")
    env = data.get("environment", {})
    if not isinstance(env, dict):
        errors.append("checkpoint.environment must be an object")
        env = {}
    resume_required = any(env.get(k) is True for k in ("cold_resume", "hiatus_or_context_loss", "model_or_agent_changed", "migration_or_governance_changed"))
    resume = data.get("resume_probe")
    if resume_required:
        if not isinstance(resume, dict) or resume.get("performed") is not True:
            errors.append("cold/hiatus/model/migration checkpoint requires resume_probe.performed=true")
        else:
            if resume.get("mode") not in RESUME_MODES:
                errors.append(f"resume_probe.mode invalid: {resume.get('mode')}")
            if not isinstance(resume.get("evidence_ref"), str) or not resume.get("evidence_ref", "").strip():
                errors.append("performed resume_probe requires a project-relative evidence_ref")
            loaded = resume.get("loaded_artifacts")
            if not isinstance(loaded, list) or not loaded or not all(isinstance(x, str) and x.strip() for x in loaded):
                errors.append("performed resume_probe requires non-empty loaded_artifacts paths")
            for key in ("correct_next_action", "asked_known_information", "resurrected_stale_plan"):
                if not isinstance(resume.get(key), bool):
                    errors.append(f"resume_probe.{key} must be boolean")
            if not isinstance(resume.get("manual_repair_actions"), int) or int(resume.get("manual_repair_actions", -1)) < 0:
                errors.append("resume_probe.manual_repair_actions must be a non-negative integer")
    elif resume is not None and not isinstance(resume, dict):
        errors.append("checkpoint.resume_probe must be null or an object")
    creative = data.get("creative_longitudinal", {})
    if not isinstance(creative, dict):
        errors.append("checkpoint.creative_longitudinal must be an object")
    else:
        for key in CREATIVE_REF_KEYS:
            raw = creative.get(key)
            if raw is not None and (not isinstance(raw, str) or not raw.strip()):
                errors.append(f"creative_longitudinal.{key} must be null or a project-relative path")
    return errors


def load_project_manifest(project_root: Path) -> tuple[Path, dict[str, Any]]:
    path = project_root / "project-manifest.json"
    if not path.exists():
        raise ValueError(f"project manifest not found: {path}")
    obj = load_json(path)
    if not isinstance(obj, dict):
        raise ValueError("project manifest must be an object")
    return path, obj


def resolve_project_path(project_root: Path, raw: str) -> Path:
    p = (project_root / raw).resolve()
    try:
        p.relative_to(project_root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {raw}") from exc
    return p


def runtime_trace(project_root: Path, project_manifest: dict[str, Any]) -> dict[str, Any]:
    runtime_rel = (project_manifest.get("canonical_paths") or {}).get("runtime_manifest")
    runtime_path = project_root / runtime_rel if isinstance(runtime_rel, str) else project_root / "runtime/runtime-manifest.json"
    if not runtime_path.exists():
        return {"active": False}
    runtime_manifest = load_json(runtime_path)
    events_rel = (runtime_manifest.get("paths") or {}).get("events", "runtime/events.jsonl")
    events_path = project_root / events_rel
    event_count = 0
    head = None
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event_count += 1
            try:
                obj = json.loads(line)
                head = obj.get("event_id") or obj.get("id") or head
            except json.JSONDecodeError:
                pass
    return {
        "active": True,
        "runtime_manifest": file_meta(runtime_path, project_root),
        "events_path": str(events_path.resolve().relative_to(project_root.resolve())).replace("\\", "/") if events_path.exists() else events_rel,
        "event_count": event_count,
        "event_head": head,
        "events_sha256": sha256_file(events_path) if events_path.exists() else None,
    }


def collect_context_metrics(project_root: Path, raw_path: Any) -> dict[str, Any] | None:
    if raw_path is None:
        return None
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError("writer_pack_manifest_path must be null or a project-relative string")
    path = resolve_project_path(project_root, raw_path)
    if not path.exists():
        raise ValueError(f"writer pack manifest not found: {raw_path}")
    obj = load_json(path)
    included = obj.get("included") if isinstance(obj, dict) else None
    return {
        "artifact": file_meta(path, project_root),
        "included_entries": len(included) if isinstance(included, list) else None,
        "estimated_tokens": obj.get("estimated_tokens") if isinstance(obj, dict) else None,
        "budget_tokens": obj.get("budget_tokens") if isinstance(obj, dict) else None,
        "budget_ratio": (
            round(float(obj.get("estimated_tokens")) / float(obj.get("budget_tokens")), 6)
            if isinstance(obj, dict)
            and isinstance(obj.get("estimated_tokens"), (int, float))
            and isinstance(obj.get("budget_tokens"), (int, float))
            and obj.get("budget_tokens")
            else None
        ),
    }


def canonical_health(project_root: Path, project_manifest_path: Path, runtime_active: bool) -> dict[str, Any]:
    project = run_backend([str(SCRIPT_DIR / "project_ops.py"), "verify", str(project_manifest_path), "--root", str(project_root), "--json"])
    semantics = run_backend([str(SCRIPT_DIR / "semantic_kernel.py"), "verify", str(project_root), "--json"])
    runtime = None
    if runtime_active:
        runtime = run_backend([str(SCRIPT_DIR / "runtime_schema.py"), "validate-project", str(project_root)])
    return {"project_verify": project, "semantic_kernel": semantics, "runtime_schema": runtime}


def checkpoint_id(chapter: int, session_id: str, recorded_at: str, existing: set[str]) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", session_id).strip("-") or "session"
    digest = hashlib.sha256(recorded_at.encode("utf-8")).hexdigest()[:8]
    base = f"ch-{chapter:04d}-{slug}-{digest}"
    out = base
    n = 2
    while out in existing:
        out = f"{base}-{n}"
        n += 1
    return out


def checkpoint_file(campaign_dir: Path, rel: str) -> Path:
    p = (campaign_dir / rel).resolve()
    try:
        p.relative_to(campaign_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"checkpoint path escapes campaign directory: {rel}") from exc
    return p



def session_file(campaign_dir: Path, rel: str) -> Path:
    p = (campaign_dir / rel).resolve()
    try:
        p.relative_to(campaign_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"session path escapes campaign directory: {rel}") from exc
    return p


def session_slug(session_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", session_id).strip("-")
    if not slug:
        raise ValueError("session_id must contain at least one portable filename character")
    return slug


def verify_session_start_record(record: Any, previous_sha: str | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["session start record must be an object"]
    for key in ("record_type", "campaign_id", "project_id", "session_id", "captured_at_utc", "trace"):
        if key not in record:
            errors.append(f"session start missing {key}")
    if record.get("record_type") != "session-start":
        errors.append("session start record_type must be session-start")
    if record.get("previous_session_start_sha256") != previous_sha:
        errors.append("session start hash-chain predecessor mismatch")
    captured = record.get("captured_at_utc")
    if isinstance(captured, str):
        try:
            parse_iso8601(captured)
        except ValueError:
            errors.append("session start captured_at_utc must be timezone-aware ISO 8601")
    else:
        errors.append("session start captured_at_utc is required")
    trace = record.get("trace") or {}
    if not isinstance((trace.get("project_manifest") or {}).get("sha256"), str):
        errors.append("session start trace.project_manifest.sha256 is required")
    return errors


def verify_session_end_record(record: Any, *, session_id: str, start_sha: str, start_time: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["session end record must be an object"]
    if record.get("record_type") != "session-end":
        errors.append("session end record_type must be session-end")
    if record.get("session_id") != session_id:
        errors.append("session end session_id mismatch")
    if record.get("session_start_sha256") != start_sha:
        errors.append("session end does not bind to indexed session start")
    if record.get("outcome") not in SESSION_OUTCOMES:
        errors.append(f"session end outcome invalid: {record.get('outcome')}")
    captured = record.get("captured_at_utc")
    if isinstance(captured, str):
        try:
            end_dt = parse_iso8601(captured).astimezone(timezone.utc)
            start_dt = parse_iso8601(start_time).astimezone(timezone.utc)
            if end_dt < start_dt:
                errors.append("session end precedes session start")
        except ValueError:
            errors.append("session end captured_at_utc must be timezone-aware ISO 8601")
    else:
        errors.append("session end captured_at_utc is required")
    return errors


def gather_sessions(campaign_dir: Path, manifest: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    sessions: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    previous_start_sha: str | None = None
    for i, row in enumerate(manifest.get("session_index", [])):
        if not isinstance(row, dict):
            errors.append(f"session_index[{i}] must be an object")
            continue
        sid = row.get("session_id")
        start_rel = row.get("start_path")
        start_sha = row.get("start_sha256")
        if not isinstance(sid, str) or not sid:
            errors.append(f"session_index[{i}].session_id missing")
            continue
        if sid in sessions:
            errors.append(f"duplicate session_id in index: {sid}")
            continue
        if not isinstance(start_rel, str) or not start_rel:
            errors.append(f"session_index[{i}].start_path missing")
            continue
        start_path = session_file(campaign_dir, start_rel)
        if not start_path.exists():
            errors.append(f"indexed session start missing: {start_rel}")
            continue
        actual_start_sha = sha256_file(start_path)
        if not isinstance(start_sha, str) or actual_start_sha != start_sha:
            errors.append(f"session start hash mismatch for {start_rel}")
        try:
            start = load_json(start_path)
        except Exception as exc:
            errors.append(f"cannot read session start {start_rel}: {exc}")
            continue
        errors.extend(f"{sid}: {e}" for e in verify_session_start_record(start, previous_start_sha))
        previous_start_sha = actual_start_sha
        end = None
        end_rel = row.get("end_path")
        end_sha = row.get("end_sha256")
        if end_rel is not None:
            if not isinstance(end_rel, str) or not end_rel:
                errors.append(f"session_index[{i}].end_path invalid")
            else:
                end_path = session_file(campaign_dir, end_rel)
                if not end_path.exists():
                    errors.append(f"indexed session end missing: {end_rel}")
                else:
                    actual_end_sha = sha256_file(end_path)
                    if not isinstance(end_sha, str) or actual_end_sha != end_sha:
                        errors.append(f"session end hash mismatch for {end_rel}")
                    try:
                        end = load_json(end_path)
                    except Exception as exc:
                        errors.append(f"cannot read session end {end_rel}: {exc}")
                    else:
                        errors.extend(f"{sid}: {e}" for e in verify_session_end_record(
                            end,
                            session_id=sid,
                            start_sha=actual_start_sha,
                            start_time=str(start.get("captured_at_utc", "")),
                        ))
        sessions[sid] = {
            "start": start,
            "end": end,
            "start_artifact": {"path": start_rel, "sha256": actual_start_sha, "bytes": start_path.stat().st_size},
            "end_artifact": ({"path": end_rel, "sha256": sha256_file(session_file(campaign_dir, end_rel)), "bytes": session_file(campaign_dir, end_rel).stat().st_size} if isinstance(end_rel, str) and end is not None else None),
        }
    return sessions, errors


def summarize_sessions(sessions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    outcomes = {key: 0 for key in sorted(SESSION_OUTCOMES)}
    closed = 0
    for item in sessions.values():
        end = item.get("end")
        if isinstance(end, dict):
            closed += 1
            outcome = end.get("outcome")
            if outcome in outcomes:
                outcomes[outcome] += 1
    return {
        "instrumented_sessions": len(sessions),
        "closed_sessions": closed,
        "unclosed_sessions": len(sessions) - closed,
        "outcomes": outcomes,
    }

def verify_checkpoint_record(record: Any, campaign_dir: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["checkpoint record must be an object"]
    for key in ("checkpoint_id", "campaign_id", "chapter", "session_id", "recorded_at", "trace"):
        if key not in record:
            errors.append(f"checkpoint missing {key}")
    trace = record.get("trace", {})
    chapter = trace.get("chapter_artifact") if isinstance(trace, dict) else None
    if not isinstance(chapter, dict) or not chapter.get("sha256"):
        errors.append("checkpoint trace.chapter_artifact is missing hash evidence")
    health = record.get("canonical_health", {})
    if not isinstance(health, dict) or not isinstance(health.get("project_verify"), dict) or not isinstance(health.get("semantic_kernel"), dict):
        errors.append("checkpoint canonical_health is incomplete")
    probes = record.get("probes", [])
    if not isinstance(probes, list):
        errors.append("checkpoint probes must be a list")
    else:
        for i, probe in enumerate(probes):
            if not isinstance(probe, dict):
                errors.append(f"checkpoint probes[{i}] must be an object")
                continue
            if probe.get("kind") not in PROBE_KINDS:
                errors.append(f"checkpoint probes[{i}].kind invalid")
            if probe.get("mode") not in PROBE_MODES:
                errors.append(f"checkpoint probes[{i}].mode invalid")
            if probe.get("status") not in PROBE_STATUS:
                errors.append(f"checkpoint probes[{i}].status invalid")
    capture = record.get("capture", {})
    captured = capture.get("captured_at_utc") if isinstance(capture, dict) else None
    if not isinstance(captured, str):
        errors.append("checkpoint capture.captured_at_utc is required")
    else:
        try:
            parse_iso8601(captured)
        except ValueError:
            errors.append("checkpoint capture.captured_at_utc must be timezone-aware ISO 8601")
    session_evidence = trace.get("session_evidence") if isinstance(trace, dict) else None
    if not isinstance(session_evidence, dict) or not isinstance((session_evidence.get("start_artifact") or {}).get("sha256"), str):
        errors.append("checkpoint trace.session_evidence.start_artifact.sha256 is required")
    trace_probe = (trace.get("probe_evidence") if isinstance(trace, dict) else None)
    if not isinstance(trace_probe, list) or len(trace_probe) != len(probes):
        errors.append("checkpoint trace.probe_evidence must align with probes")
    else:
        by_id = {str(x.get("probe_id")): x for x in trace_probe if isinstance(x, dict)}
        for probe in probes:
            if probe.get("status") == "pass":
                snap = by_id.get(str(probe.get("probe_id")))
                if not isinstance(snap, dict) or not isinstance(snap.get("artifact"), dict) or not snap.get("artifact", {}).get("sha256"):
                    errors.append(f"passing probe lacks hashed evidence artifact: {probe.get('probe_id')}")
    env = record.get("environment") or {}
    if any(env.get(k) is True for k in ("cold_resume", "hiatus_or_context_loss", "model_or_agent_changed", "migration_or_governance_changed")):
        resume = (trace.get("resume_evidence") if isinstance(trace, dict) else None)
        if not isinstance(resume, dict) or not isinstance(resume.get("evidence_artifact"), dict) or not resume.get("evidence_artifact", {}).get("sha256"):
            errors.append("cold/hiatus/model/migration checkpoint lacks hashed resume evidence")
    return errors


def load_campaign(campaign_dir: Path) -> tuple[Path, dict[str, Any]]:
    path = campaign_dir / "campaign-manifest.json"
    if not path.exists():
        raise ValueError(f"campaign manifest not found: {path}")
    data = load_json(path)
    errors = validate_manifest(data)
    if errors:
        raise ValueError("; ".join(errors))
    return path, data


def gather_records(campaign_dir: Path, manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    ids: set[str] = set()
    previous_sha: str | None = None
    for i, row in enumerate(manifest.get("checkpoint_index", [])):
        if not isinstance(row, dict):
            errors.append(f"checkpoint_index[{i}] must be an object")
            continue
        cid = row.get("checkpoint_id")
        rel = row.get("path")
        if not isinstance(cid, str) or not cid:
            errors.append(f"checkpoint_index[{i}].checkpoint_id missing")
            continue
        if cid in ids:
            errors.append(f"duplicate checkpoint_id in index: {cid}")
            continue
        ids.add(cid)
        if not isinstance(rel, str) or not rel:
            errors.append(f"checkpoint_index[{i}].path missing")
            continue
        path = checkpoint_file(campaign_dir, rel)
        if not path.exists():
            errors.append(f"indexed checkpoint missing: {rel}")
            continue
        actual_sha = sha256_file(path)
        indexed_sha = row.get("sha256")
        if not isinstance(indexed_sha, str) or not indexed_sha:
            errors.append(f"checkpoint index missing sha256 for {rel}")
        elif indexed_sha != actual_sha:
            errors.append(f"checkpoint hash mismatch for {rel}")
        try:
            record = load_json(path)
        except Exception as exc:
            errors.append(f"cannot read checkpoint {rel}: {exc}")
            continue
        if record.get("checkpoint_id") != cid:
            errors.append(f"checkpoint id mismatch for {rel}")
        if record.get("previous_checkpoint_sha256") != previous_sha:
            errors.append(f"checkpoint hash-chain predecessor mismatch for {rel}")
        errors.extend(f"{cid}: {e}" for e in verify_checkpoint_record(record, campaign_dir))
        records.append(record)
        previous_sha = actual_sha
    return records, errors


def summarize_evidence(records: list[dict[str, Any]], registration_chapter: int = 0) -> dict[str, Any]:
    eligible = [r for r in records if (r.get("capture") or {}).get("evidence_eligible") is True]
    chapters = [int(r.get("chapter", 0)) for r in eligible if isinstance(r.get("chapter"), int)]
    sessions = {str(r.get("session_id")) for r in eligible if r.get("session_id")}
    human_records = [r for r in eligible if (r.get("human_review") or {}).get("reviewed") is True]
    cold = [r for r in eligible if (r.get("environment") or {}).get("cold_resume") is True or (r.get("environment") or {}).get("hiatus_or_context_loss") is True]
    model_change = [r for r in eligible if (r.get("environment") or {}).get("model_or_agent_changed") is True]
    kinds: set[str] = set()
    passed_kinds: set[str] = set()
    failed_probe_count = 0
    probe_modes: set[str] = set()
    context_ratios: list[dict[str, Any]] = []
    event_counts: list[dict[str, Any]] = []
    maintenance_totals = {"repairs": 0, "retcons": 0, "manual_recovery_actions": 0, "context_rebuilds": 0}
    for r in eligible:
        for p in r.get("probes", []) if isinstance(r.get("probes"), list) else []:
            kind = p.get("kind")
            if kind in PROBE_KINDS:
                kinds.add(kind)
                mode = p.get("mode")
                if mode in PROBE_MODES:
                    probe_modes.add(mode)
                if p.get("status") == "pass":
                    passed_kinds.add(kind)
                elif p.get("status") == "fail":
                    failed_probe_count += 1
        context = ((r.get("trace") or {}).get("context"))
        if isinstance(context, dict) and isinstance(context.get("budget_ratio"), (int, float)):
            context_ratios.append({"chapter": r.get("chapter"), "budget_ratio": context.get("budget_ratio"), "estimated_tokens": context.get("estimated_tokens"), "budget_tokens": context.get("budget_tokens")})
        runtime = ((r.get("trace") or {}).get("runtime"))
        if isinstance(runtime, dict) and isinstance(runtime.get("event_count"), int):
            event_counts.append({"chapter": r.get("chapter"), "event_count": runtime.get("event_count")})
        m = r.get("maintenance") or {}
        maintenance_totals["repairs"] += int(m.get("repairs_since_previous") or 0)
        maintenance_totals["retcons"] += int(m.get("retcons_since_previous") or 0)
        maintenance_totals["manual_recovery_actions"] += int(m.get("manual_recovery_actions") or 0)
        maintenance_totals["context_rebuilds"] += int(m.get("context_rebuilds") or 0)
    severe = [r for r in eligible if (r.get("integrity_notes") or {}).get("severe_blocker") is True]
    creative_review = [r for r in eligible if any((r.get("creative_longitudinal") or {}).get(k) for k in (*CREATIVE_REF_KEYS, "flattening_notes"))]
    late = [r for r in records if (r.get("capture") or {}).get("evidence_eligible") is not True]
    captured_times: list[datetime] = []
    probe_gaps: list[int] = []
    action_gaps: list[int] = []
    observational_action_gaps: list[int] = []
    campaign_probe_gaps: list[int] = []
    campaign_action_gaps: list[int] = []
    campaign_observational_action_gaps: list[int] = []
    for r in eligible:
        raw_capture = (r.get("capture") or {}).get("captured_at_utc")
        if isinstance(raw_capture, str):
            try:
                captured_times.append(parse_iso8601(raw_capture).astimezone(timezone.utc))
            except ValueError:
                pass
        for snap in ((r.get("trace") or {}).get("probe_evidence") or []):
            if not isinstance(snap, dict) or snap.get("status") != "pass":
                continue
            gap = snap.get("gap_chapters")
            if isinstance(gap, int) and gap >= 0:
                probe_gaps.append(gap)
                if snap.get("kind") == "action":
                    action_gaps.append(gap)
                    if snap.get("mode") == "observational":
                        observational_action_gaps.append(gap)
            campaign_gap = snap.get("campaign_gap_chapters")
            if isinstance(campaign_gap, int) and campaign_gap >= 0 and snap.get("status") == "pass":
                campaign_probe_gaps.append(campaign_gap)
                if snap.get("kind") == "action":
                    campaign_action_gaps.append(campaign_gap)
                    if snap.get("mode") == "observational":
                        campaign_observational_action_gaps.append(campaign_gap)
    span_days = 0.0
    if len(captured_times) >= 2:
        span_days = max(0.0, (max(captured_times) - min(captured_times)).total_seconds() / 86400.0)
    max_probe_gap = max(probe_gaps) if probe_gaps else 0
    max_action_gap = max(action_gaps) if action_gaps else 0
    max_observational_action_gap = max(observational_action_gaps) if observational_action_gaps else 0
    max_campaign_probe_gap = max(campaign_probe_gaps) if campaign_probe_gaps else 0
    max_campaign_action_gap = max(campaign_action_gaps) if campaign_action_gaps else 0
    max_campaign_observational_action_gap = max(campaign_observational_action_gaps) if campaign_observational_action_gaps else 0
    max_chapter = max(chapters) if chapters else registration_chapter
    observed = max(0, max_chapter - registration_chapter) if chapters else 0
    offsets = sorted(set(ch - registration_chapter for ch in chapters if ch > registration_chapter))
    return {
        "max_chapter": max_chapter,
        "max_observed_chapters": observed,
        "checkpoint_chapters": sorted(set(chapters)),
        "checkpoint_offsets": offsets,
        "checkpoint_count": len(records),
        "eligible_checkpoint_count": len(eligible),
        "ineligible_or_late_checkpoint_count": len(late),
        "distinct_sessions": len(sessions),
        "human_reviewed_checkpoints": len(human_records),
        "cold_resume_or_interruption_checkpoints": len(cold),
        "model_or_agent_change_checkpoints": len(model_change),
        "calendar_span_days": round(span_days, 6),
        "temporal_span_class": temporal_span_class(span_days),
        "max_probe_gap_chapters": max_probe_gap,
        "memory_horizon_class": memory_horizon_class(max_probe_gap),
        "max_action_probe_gap_chapters": max_action_gap,
        "action_memory_horizon_class": memory_horizon_class(max_action_gap),
        "max_observational_action_gap_chapters": max_observational_action_gap,
        "observational_action_memory_horizon_class": memory_horizon_class(max_observational_action_gap),
        "max_campaign_probe_gap_chapters": max_campaign_probe_gap,
        "campaign_memory_horizon_class": memory_horizon_class(max_campaign_probe_gap),
        "max_campaign_action_probe_gap_chapters": max_campaign_action_gap,
        "campaign_action_memory_horizon_class": memory_horizon_class(max_campaign_action_gap),
        "max_campaign_observational_action_gap_chapters": max_campaign_observational_action_gap,
        "campaign_observational_action_memory_horizon_class": memory_horizon_class(max_campaign_observational_action_gap),
        "probe_kinds_seen": sorted(kinds),
        "probe_modes_seen": sorted(probe_modes),
        "probe_kinds_passed": sorted(passed_kinds),
        "failed_probe_count": failed_probe_count,
        "severe_blocker_checkpoints": len(severe),
        "creative_longitudinal_review_checkpoints": len(creative_review),
        "context_budget_series": context_ratios,
        "runtime_event_count_series": event_counts,
        "maintenance_totals": maintenance_totals,
    }

def _series_trend(series: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    points = [row for row in series if isinstance(row.get("chapter"), int) and isinstance(row.get(key), (int, float))]
    if not points:
        return None
    points.sort(key=lambda row: row["chapter"])
    first, last = points[0], points[-1]
    span = last["chapter"] - first["chapter"]
    delta = float(last[key]) - float(first[key])
    return {
        "first": {"chapter": first["chapter"], "value": first[key]},
        "latest": {"chapter": last["chapter"], "value": last[key]},
        "min": min(float(row[key]) for row in points),
        "max": max(float(row[key]) for row in points),
        "delta": round(delta, 6),
        "delta_per_100_chapters": round(delta * 100.0 / span, 6) if span > 0 else None,
        "point_count": len(points),
    }


def tooling_epochs(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = [r for r in records if (r.get("capture") or {}).get("evidence_eligible") is True]
    eligible.sort(key=lambda r: (int(r.get("chapter", 0)), str((r.get("capture") or {}).get("captured_at_utc", ""))))
    epochs: list[dict[str, Any]] = []
    for r in eligible:
        tooling = (r.get("trace") or {}).get("skill_tooling") or {}
        signature = tuple(tooling.get(k) for k in ("skill_control_plane_sha256", "campaign_harness_sha256", "semantic_kernel_sha256", "storyctl_sha256"))
        if epochs and epochs[-1]["signature"] == signature:
            epochs[-1]["end_chapter"] = r.get("chapter")
            epochs[-1]["checkpoint_count"] += 1
        else:
            epochs.append({
                "start_chapter": r.get("chapter"),
                "end_chapter": r.get("chapter"),
                "checkpoint_count": 1,
                "signature": signature,
            })
    return epochs


def evidence_passport(
    records: list[dict[str, Any]],
    manifest: dict[str, Any] | None = None,
    sessions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    registration = (manifest or {}).get("registration") or {}
    registration_chapter = int(registration.get("project_chapter") or 0)
    summary = summarize_evidence(records, registration_chapter)
    level, _ = maturity(records, manifest)
    epochs = tooling_epochs(records)
    session_summary = summarize_sessions(sessions or {})
    return {
        "chapter_maturity": level,
        "calendar_span_days": summary.get("calendar_span_days"),
        "temporal_span_class": summary.get("temporal_span_class"),
        "max_probe_gap_chapters": summary.get("max_probe_gap_chapters"),
        "memory_horizon_class": summary.get("memory_horizon_class"),
        "max_action_probe_gap_chapters": summary.get("max_action_probe_gap_chapters"),
        "action_memory_horizon_class": summary.get("action_memory_horizon_class"),
        "max_observational_action_gap_chapters": summary.get("max_observational_action_gap_chapters"),
        "observational_action_memory_horizon_class": summary.get("observational_action_memory_horizon_class"),
        "distinct_sessions": summary.get("distinct_sessions"),
        "human_reviewed_checkpoints": summary.get("human_reviewed_checkpoints"),
        "cold_resume_or_interruption_checkpoints": summary.get("cold_resume_or_interruption_checkpoints"),
        "tooling_era_count": len(epochs),
        "registration_project_chapter": registration.get("project_chapter"),
        "max_observed_chapters": summary.get("max_observed_chapters"),
        "campaign_memory_horizon_class": summary.get("campaign_memory_horizon_class"),
        "campaign_action_memory_horizon_class": summary.get("campaign_action_memory_horizon_class"),
        "campaign_observational_action_memory_horizon_class": summary.get("campaign_observational_action_memory_horizon_class"),
        "registered_at_utc": registration.get("registered_at_utc"),
        "session_logging_scope": ((manifest or {}).get("source_attestation") or {}).get("session_logging_scope"),
        "instrumented_sessions": session_summary.get("instrumented_sessions"),
        "closed_sessions": session_summary.get("closed_sessions"),
        "aborted_or_recovery_sessions": int((session_summary.get("outcomes") or {}).get("aborted", 0)) + int((session_summary.get("outcomes") or {}).get("recovery-required", 0)),
        "unclosed_sessions": session_summary.get("unclosed_sessions"),
    }


def trajectory_report(
    records: list[dict[str, Any]],
    manifest: dict[str, Any] | None = None,
    sessions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    eligible = [r for r in records if (r.get("capture") or {}).get("evidence_eligible") is True]
    eligible.sort(key=lambda r: (int(r.get("chapter", 0)), str(r.get("recorded_at", ""))))
    registration = (manifest or {}).get("registration") or {}
    registration_chapter = int(registration.get("project_chapter") or 0)
    summary = summarize_evidence(records, registration_chapter)
    probe_outcomes: dict[str, dict[str, int]] = {kind: {status: 0 for status in sorted(PROBE_STATUS)} for kind in sorted(PROBE_KINDS)}
    probe_outcomes_by_mode: dict[str, dict[str, int]] = {mode: {status: 0 for status in sorted(PROBE_STATUS)} for mode in sorted(PROBE_MODES)}
    tooling_hashes: dict[str, set[str]] = {
        "skill_control_plane_sha256": set(),
        "campaign_harness_sha256": set(),
        "semantic_kernel_sha256": set(),
        "storyctl_sha256": set(),
    }
    maintenance_series: list[dict[str, Any]] = []
    maintenance_cumulative = 0
    for r in eligible:
        chapter = int(r.get("chapter", 0))
        for probe in r.get("probes", []) if isinstance(r.get("probes"), list) else []:
            kind, status = probe.get("kind"), probe.get("status")
            if kind in probe_outcomes and status in PROBE_STATUS:
                probe_outcomes[kind][status] += 1
            mode = probe.get("mode")
            if mode in probe_outcomes_by_mode and status in PROBE_STATUS:
                probe_outcomes_by_mode[mode][status] += 1
        m = r.get("maintenance") or {}
        actions = sum(int(m.get(k) or 0) for k in ("repairs_since_previous", "retcons_since_previous", "manual_recovery_actions", "context_rebuilds"))
        maintenance_cumulative += actions
        maintenance_series.append({"chapter": chapter, "actions_since_previous": actions, "cumulative_actions": maintenance_cumulative})
        tooling = (r.get("trace") or {}).get("skill_tooling") or {}
        for key in tooling_hashes:
            value = tooling.get(key)
            if isinstance(value, str) and value:
                tooling_hashes[key].add(value)
    chapters = summary.get("checkpoint_chapters", [])
    gaps = [b - a for a, b in zip(chapters, chapters[1:])]
    observed_chapters = int(summary.get("max_observed_chapters") or 0)
    return {
        "evidence_summary": summary,
        "context_budget_trend": _series_trend(summary.get("context_budget_series", []), "budget_ratio"),
        "runtime_event_growth": _series_trend(summary.get("runtime_event_count_series", []), "event_count"),
        "maintenance": {
            "series": maintenance_series,
            "total_actions": maintenance_cumulative,
            "actions_per_100_observed_chapters": round(maintenance_cumulative * 100.0 / observed_chapters, 6) if observed_chapters > 0 else None,
        },
        "probe_outcomes_by_kind": probe_outcomes,
        "probe_outcomes_by_mode": probe_outcomes_by_mode,
        "session_summary": summarize_sessions(sessions or {}),
        "checkpoint_spacing": {
            "gaps": gaps,
            "max_gap": max(gaps) if gaps else None,
        },
        "tooling_distinct_hash_counts": {key: len(values) for key, values in tooling_hashes.items()},
        "tooling_changed_during_campaign": any(len(values) > 1 for values in tooling_hashes.values()),
        "tooling_epochs": tooling_epochs(records),
        "evidence_passport": evidence_passport(records, manifest, sessions),
        "interpretation": "Descriptive trajectory only. Do not collapse longitudinal integrity, maintenance burden, creative drift, and human review into one scalar score.",
    }


def level_check(
    level: str,
    summary: dict[str, Any],
    records: list[dict[str, Any]],
    registration_chapter: int = 0,
) -> tuple[bool, list[str]]:
    req = LEVEL_REQS[level]
    reasons: list[str] = []
    if summary["max_observed_chapters"] < req["chapter"]:
        reasons.append(f"observed chapters {summary['max_observed_chapters']} < required {req['chapter']}")
    have = set(summary["checkpoint_offsets"])
    missing = [x for x in req["checkpoints"] if x not in have]
    if missing:
        reasons.append(f"missing canonical campaign checkpoint offsets: {missing}")
    if summary["distinct_sessions"] < req["sessions"]:
        reasons.append(f"distinct sessions {summary['distinct_sessions']} < required {req['sessions']}")
    if summary["human_reviewed_checkpoints"] < req["human"]:
        reasons.append(f"human-reviewed checkpoints {summary['human_reviewed_checkpoints']} < required {req['human']}")
    if summary["cold_resume_or_interruption_checkpoints"] < req["cold"]:
        reasons.append(f"cold-resume/interruption checkpoints {summary['cold_resume_or_interruption_checkpoints']} < required {req['cold']}")
    passed_kinds = set(summary["probe_kinds_passed"])
    if len(passed_kinds) < req["probe_kinds"]:
        reasons.append(f"passed probe classes {len(passed_kinds)} < required {req['probe_kinds']}")
    if req.get("requires_action") and "action" not in passed_kinds:
        reasons.append("required passing action probe is missing")
    if req.get("requires_observational_action"):
        has_observational_action = any(
            p.get("kind") == "action"
            and p.get("status") == "pass"
            and p.get("mode") == "observational"
            and isinstance(p.get("source_chapter"), int)
            and int(p.get("source_chapter")) > registration_chapter
            for r in records if (r.get("capture") or {}).get("evidence_eligible") is True
            for p in (r.get("probes") or []) if isinstance(p, dict)
        )
        if not has_observational_action:
            reasons.append("required passing observational action probe is missing")
    eligible_records = [r for r in records if (r.get("capture") or {}).get("evidence_eligible") is True]
    if level in {"L4", "L5", "L6"}:
        latest = max((r for r in eligible_records if isinstance(r.get("chapter"), int)), key=lambda r: r["chapter"], default=None)
        if latest and (latest.get("integrity_notes") or {}).get("severe_blocker") is True:
            reasons.append("latest checkpoint has an unresolved severe integrity blocker")
    if req.get("major_change"):
        has_major = any(
            (r.get("environment") or {}).get("model_or_agent_changed") is True
            or (r.get("environment") or {}).get("hiatus_or_context_loss") is True
            or (r.get("environment") or {}).get("migration_or_governance_changed") is True
            or int((r.get("maintenance") or {}).get("retcons_since_previous") or 0) > 0
            for r in eligible_records
        )
        if not has_major:
            reasons.append("no checkpoint demonstrates recovery after revision, hiatus, migration, or model/agent change")
    if req.get("creative_review") and summary["creative_longitudinal_review_checkpoints"] < 2:
        reasons.append("L6 requires longitudinal creative-drift review at multiple checkpoints")
    return (not reasons), reasons


def maturity(
    records: list[dict[str, Any]],
    manifest: dict[str, Any] | None = None,
) -> tuple[str, dict[str, list[str]]]:
    registration = (manifest or {}).get("registration") or {}
    registration_chapter = int(registration.get("project_chapter") or 0)
    summary = summarize_evidence(records, registration_chapter)
    details: dict[str, list[str]] = {}
    best = "L0"
    for level in LEVEL_ORDER:
        ok, reasons = level_check(level, summary, records, registration_chapter)
        details[level] = reasons
        if ok:
            best = level
        else:
            break
    return best, details


def cmd_registry(as_json: bool) -> int:
    data = load_json(REGISTRY_PATH)
    errors = validate_registry_data(data)
    out = {"registry": str(REGISTRY_PATH.relative_to(ROOT)), "errors": errors, "data": data}
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"tracks: {len(data.get('tracks', []))}; errors: {len(errors)}")
        for row in data.get("tracks", []):
            print(f"- {row.get('track_id')}: {row.get('status')} / {row.get('evidence_level')}")
    return 1 if errors else 0


def cmd_init(args: argparse.Namespace) -> int:
    campaign_dir = args.campaign_dir.resolve()
    project_root = args.project_root.resolve()
    if campaign_dir.exists() and any(campaign_dir.iterdir()):
        raise ValueError(f"campaign directory is not empty: {campaign_dir}")
    campaign_dir.mkdir(parents=True, exist_ok=True)
    (campaign_dir / "checkpoints").mkdir(exist_ok=True)
    (campaign_dir / "sessions").mkdir(exist_ok=True)
    project_manifest_path, project = load_project_manifest(project_root)
    project_id = project.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        raise ValueError("project manifest has no project_id")
    if project_id.startswith("LWA-LONG-HORIZON-"):
        raise ValueError("synthetic long-horizon benchmark projects cannot initialize a live campaign")
    verify = run_backend([str(SCRIPT_DIR / "project_ops.py"), "verify", str(project_manifest_path), "--root", str(project_root), "--json"])
    if not verify["passed"]:
        raise ValueError("project must verify before live campaign initialization")
    target = args.target_chapters
    registered_at_utc = datetime.now(timezone.utc).isoformat()
    canonical_paths = project.get("canonical_paths") or {}
    story_state_path = project_root / canonical_paths.get("story_state", "state/story-state.json")
    registration_trace = {
        "project_manifest": file_meta(project_manifest_path, project_root),
        "story_state": file_meta(story_state_path, project_root) if story_state_path.exists() else None,
        "skill_tooling": {
            "skill_control_plane_sha256": sha256_file(ROOT / "SKILL.md"),
            "campaign_harness_sha256": sha256_file(SCRIPT_DIR / "live_campaign.py"),
            "semantic_kernel_sha256": sha256_file(SCRIPT_DIR / "semantic_kernel.py"),
            "storyctl_sha256": sha256_file(SCRIPT_DIR / "storyctl.py"),
        },
    }
    data = {
        "schema_version": SCHEMA_VERSION,
        "campaign_id": args.campaign_id,
        "campaign_type": "live-creative-campaign",
        "track_id": args.track,
        "project_id": project_id,
        "target_chapters": target,
        "created_at": args.created_at or registered_at_utc,
        "registration": {
            "registered_at_utc": registered_at_utc,
            "project_chapter": int(project.get("current_chapter") or 0),
            "trace": registration_trace,
        },
        "source_attestation": {
            "synthetic": False,
            "real_drafting_workflow": True,
            "session_logging_scope": args.session_logging_scope,
            "notes": args.attestation_notes or "Attestation only; artifact-backed evidence and human review are still required.",
        },
        "canonical_checkpoints": canonical_checkpoints(target, int(project.get("current_chapter") or 0)),
        "checkpoints_dir": "checkpoints",
        "checkpoint_index": [],
        "sessions_dir": "sessions",
        "session_index": [],
        "notes": args.notes,
    }
    errors = validate_manifest(data)
    if errors:
        raise ValueError("; ".join(errors))
    write_json(campaign_dir / "campaign-manifest.json", data)
    result = {
        "campaign_dir": str(campaign_dir),
        "campaign_id": args.campaign_id,
        "project_id": project_id,
        "target_chapters": target,
        "registration_project_chapter": data["registration"]["project_chapter"],
        "target_end_chapter": data["registration"]["project_chapter"] + target,
        "registered_at_utc": registered_at_utc,
        "session_logging_scope": args.session_logging_scope,
        "evidence_level": "L0",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"initialized {args.campaign_id} for {project_id}; evidence L0")
    return 0



def cmd_session_start(args: argparse.Namespace) -> int:
    campaign_dir = args.campaign_dir.resolve()
    project_root = args.project_root.resolve()
    manifest_path, manifest = load_campaign(campaign_dir)
    project_manifest_path, project = load_project_manifest(project_root)
    if project.get("project_id") != manifest.get("project_id"):
        raise ValueError("campaign/project project_id mismatch")
    registration_chapter = int((manifest.get("registration") or {}).get("project_chapter") or 0)
    current_chapter = int(project.get("current_chapter") or 0)
    if current_chapter < registration_chapter:
        raise ValueError(f"project current_chapter {current_chapter} is behind campaign registration chapter {registration_chapter}")
    sessions, session_errors = gather_sessions(campaign_dir, manifest)
    if session_errors:
        raise ValueError("; ".join(session_errors))
    if args.session_id in sessions:
        raise ValueError(f"session_id already exists: {args.session_id}")
    slug = session_slug(args.session_id)
    rel = f"sessions/{slug}-start.json"
    path = session_file(campaign_dir, rel)
    if path.exists():
        raise ValueError(f"session artifact already exists: {rel}")
    canonical_paths = project.get("canonical_paths") or {}
    story_state_path = project_root / canonical_paths.get("story_state", "state/story-state.json")
    captured_at_utc = datetime.now(timezone.utc).isoformat()
    previous_start_sha = None
    if manifest.get("session_index"):
        last = manifest["session_index"][-1]
        if isinstance(last, dict):
            previous_start_sha = last.get("start_sha256")
    record = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "session-start",
        "campaign_id": manifest["campaign_id"],
        "project_id": project.get("project_id"),
        "session_id": args.session_id,
        "captured_at_utc": captured_at_utc,
        "previous_session_start_sha256": previous_start_sha,
        "project_chapter_at_start": int(project.get("current_chapter") or 0),
        "trace": {
            "project_manifest": file_meta(project_manifest_path, project_root),
            "story_state": file_meta(story_state_path, project_root) if story_state_path.exists() else None,
            "project_identity": {
                "current_branch": project.get("current_branch"),
                "current_chapter": project.get("current_chapter"),
                "last_committed_event": project.get("last_committed_event"),
                "context_generation": project.get("context_generation"),
            },
            "skill_tooling": {
                "skill_control_plane_sha256": sha256_file(ROOT / "SKILL.md"),
                "campaign_harness_sha256": sha256_file(SCRIPT_DIR / "live_campaign.py"),
                "semantic_kernel_sha256": sha256_file(SCRIPT_DIR / "semantic_kernel.py"),
                "storyctl_sha256": sha256_file(SCRIPT_DIR / "storyctl.py"),
            },
        },
        "environment": {
            "agent_or_model": args.agent_or_model,
            "context_mode": args.context_mode,
            "fresh_context_attested": bool(args.fresh_context),
            "notes": args.notes,
        },
    }
    start_errors = verify_session_start_record(record, previous_start_sha)
    if start_errors:
        raise ValueError("; ".join(start_errors))
    write_json(path, record)
    start_sha = sha256_file(path)
    manifest["session_index"].append({
        "session_id": args.session_id,
        "start_path": rel,
        "start_sha256": start_sha,
        "end_path": None,
        "end_sha256": None,
    })
    write_json(manifest_path, manifest)
    out = {
        "campaign_id": manifest["campaign_id"],
        "session_id": args.session_id,
        "captured_at_utc": captured_at_utc,
        "project_chapter_at_start": record["project_chapter_at_start"],
        "start_sha256": start_sha,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2) if args.json else f"started session {args.session_id}")
    return 0


def cmd_session_end(args: argparse.Namespace) -> int:
    campaign_dir = args.campaign_dir.resolve()
    project_root = args.project_root.resolve()
    manifest_path, manifest = load_campaign(campaign_dir)
    project_manifest_path, project = load_project_manifest(project_root)
    if project.get("project_id") != manifest.get("project_id"):
        raise ValueError("campaign/project project_id mismatch")
    registration_chapter = int((manifest.get("registration") or {}).get("project_chapter") or 0)
    current_chapter = int(project.get("current_chapter") or 0)
    if current_chapter < registration_chapter:
        raise ValueError(f"project current_chapter {current_chapter} is behind campaign registration chapter {registration_chapter}")
    sessions, session_errors = gather_sessions(campaign_dir, manifest)
    if session_errors:
        raise ValueError("; ".join(session_errors))
    item = sessions.get(args.session_id)
    if item is None:
        raise ValueError(f"unknown session_id: {args.session_id}")
    row = next((x for x in manifest.get("session_index", []) if isinstance(x, dict) and x.get("session_id") == args.session_id), None)
    if not isinstance(row, dict):
        raise ValueError(f"session index row missing: {args.session_id}")
    if row.get("end_path") is not None:
        raise ValueError(f"session already ended: {args.session_id}")
    slug = session_slug(args.session_id)
    rel = f"sessions/{slug}-end.json"
    path = session_file(campaign_dir, rel)
    if path.exists():
        raise ValueError(f"session end artifact already exists: {rel}")
    canonical_paths = project.get("canonical_paths") or {}
    story_state_path = project_root / canonical_paths.get("story_state", "state/story-state.json")
    captured_at_utc = datetime.now(timezone.utc).isoformat()
    start_sha = row.get("start_sha256")
    start_record = item["start"]
    record = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "session-end",
        "campaign_id": manifest["campaign_id"],
        "project_id": project.get("project_id"),
        "session_id": args.session_id,
        "session_start_sha256": start_sha,
        "captured_at_utc": captured_at_utc,
        "project_chapter_at_end": int(project.get("current_chapter") or 0),
        "outcome": args.outcome,
        "trace": {
            "project_manifest": file_meta(project_manifest_path, project_root),
            "story_state": file_meta(story_state_path, project_root) if story_state_path.exists() else None,
        },
        "notes": args.notes,
    }
    end_errors = verify_session_end_record(
        record,
        session_id=args.session_id,
        start_sha=str(start_sha),
        start_time=str(start_record.get("captured_at_utc", "")),
    )
    if end_errors:
        raise ValueError("; ".join(end_errors))
    write_json(path, record)
    end_sha = sha256_file(path)
    row["end_path"] = rel
    row["end_sha256"] = end_sha
    write_json(manifest_path, manifest)
    out = {
        "campaign_id": manifest["campaign_id"],
        "session_id": args.session_id,
        "captured_at_utc": captured_at_utc,
        "project_chapter_at_end": record["project_chapter_at_end"],
        "outcome": args.outcome,
        "end_sha256": end_sha,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2) if args.json else f"ended session {args.session_id}: {args.outcome}")
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    campaign_dir = args.campaign_dir.resolve()
    project_root = args.project_root.resolve()
    manifest_path, manifest = load_campaign(campaign_dir)
    project_manifest_path, project = load_project_manifest(project_root)
    if project.get("project_id") != manifest.get("project_id"):
        raise ValueError("campaign/project project_id mismatch")
    inp = load_json(args.input_json)
    registration_chapter = int((manifest.get("registration") or {}).get("project_chapter") or 0)
    errors = validate_checkpoint_input(inp, int(manifest["target_chapters"]), registration_chapter)
    if errors:
        raise ValueError("; ".join(errors))
    sessions, session_errors = gather_sessions(campaign_dir, manifest)
    if session_errors:
        raise ValueError("; ".join(session_errors))
    session = sessions.get(str(inp.get("session_id")))
    if session is None:
        raise ValueError(f"checkpoint references unregistered session_id: {inp.get('session_id')}")
    chapter_path = resolve_project_path(project_root, inp["chapter_path"])
    if not chapter_path.exists():
        raise ValueError(f"chapter artifact not found: {inp['chapter_path']}")
    # Guard specifically against substituting this Skill's synthetic stress corpus.
    text_head = chapter_path.read_text(encoding="utf-8", errors="replace")[:2000]
    if "The investigation advances through a small observable consequence" in text_head or str(project.get("project_id", "")).startswith("LWA-LONG-HORIZON-"):
        raise ValueError("built-in synthetic long-horizon benchmark artifacts are ineligible for live campaign checkpoints")

    rt = runtime_trace(project_root, project)
    health = canonical_health(project_root, project_manifest_path, bool(rt.get("active")))
    context = collect_context_metrics(project_root, inp.get("writer_pack_manifest_path"))
    probe_evidence = collect_probe_evidence(project_root, inp.get("probes", []), int(inp["chapter"]), registration_chapter)
    creative_evidence = collect_creative_evidence(project_root, inp.get("creative_longitudinal", {}))
    resume_evidence = collect_resume_evidence(project_root, inp.get("resume_probe"))
    captured_at_utc = datetime.now(timezone.utc).isoformat()
    session_start = session["start"]
    session_started_at = parse_iso8601(str(session_start.get("captured_at_utc"))).astimezone(timezone.utc)
    captured_dt = parse_iso8601(captured_at_utc).astimezone(timezone.utc)
    if session_started_at > captured_dt:
        raise ValueError("registered session start is later than checkpoint capture")
    session_project_chapter = int(session_start.get("project_chapter_at_start") or 0)
    session_anchor_consistent = session_project_chapter <= int(inp["chapter"])
    reported_at = parse_iso8601(inp["recorded_at"]).astimezone(timezone.utc)
    reported_capture_skew_hours = abs((captured_dt - reported_at).total_seconds()) / 3600.0
    temporal_attestation_consistent = reported_capture_skew_hours <= 72.0
    canonical_paths = project.get("canonical_paths") or {}
    story_state_path = project_root / canonical_paths.get("story_state", "state/story-state.json")
    trace = {
        "project_manifest": file_meta(project_manifest_path, project_root),
        "story_state": file_meta(story_state_path, project_root) if story_state_path.exists() else None,
        "chapter_artifact": file_meta(chapter_path, project_root),
        "runtime": rt,
        "context": context,
        "probe_evidence": probe_evidence,
        "creative_evidence": creative_evidence,
        "resume_evidence": resume_evidence,
        "session_evidence": {
            "start_artifact": session.get("start_artifact"),
            "end_artifact": session.get("end_artifact"),
            "started_at_utc": session_start.get("captured_at_utc"),
            "project_chapter_at_start": session_start.get("project_chapter_at_start"),
            "environment": session_start.get("environment"),
        },
        "project_identity": {
            "project_id": project.get("project_id"),
            "governance_profile": project.get("governance_profile"),
            "current_branch": project.get("current_branch"),
            "current_chapter": project.get("current_chapter"),
            "last_committed_event": project.get("last_committed_event"),
            "context_generation": project.get("context_generation"),
        },
        "skill_tooling": {
            "skill_control_plane_sha256": sha256_file(ROOT / "SKILL.md"),
            "campaign_harness_sha256": sha256_file(SCRIPT_DIR / "live_campaign.py"),
            "semantic_kernel_sha256": sha256_file(SCRIPT_DIR / "semantic_kernel.py"),
            "storyctl_sha256": sha256_file(SCRIPT_DIR / "storyctl.py"),
        },
    }
    existing = {str(x.get("checkpoint_id")) for x in manifest.get("checkpoint_index", []) if isinstance(x, dict)}
    cid = checkpoint_id(inp["chapter"], inp["session_id"], inp["recorded_at"], existing)
    current_chapter = project.get("current_chapter")
    if isinstance(current_chapter, int) and current_chapter < registration_chapter:
        raise ValueError(f"project current_chapter {current_chapter} is behind campaign registration chapter {registration_chapter}")
    capture_lag = None
    contemporaneous = False
    if isinstance(current_chapter, int):
        capture_lag = current_chapter - int(inp["chapter"])
        if capture_lag < 0:
            raise ValueError(f"checkpoint chapter {inp['chapter']} is ahead of project current_chapter {current_chapter}")
        contemporaneous = capture_lag <= 1
    health_pass = all(v is None or v.get("passed") for v in health.values())
    previous_checkpoint_sha256 = None
    if manifest.get("checkpoint_index"):
        last_row = manifest["checkpoint_index"][-1]
        if isinstance(last_row, dict):
            previous_checkpoint_sha256 = last_row.get("sha256")
    record = {
        "schema_version": SCHEMA_VERSION,
        "checkpoint_id": cid,
        "campaign_id": manifest["campaign_id"],
        "previous_checkpoint_sha256": previous_checkpoint_sha256,
        "chapter": inp["chapter"],
        "recorded_at": inp["recorded_at"],
        "session_id": inp["session_id"],
        "capture": {
            "captured_at_utc": captured_at_utc,
            "reported_recorded_at": inp["recorded_at"],
            "reported_capture_skew_hours": round(reported_capture_skew_hours, 6),
            "temporal_attestation_consistent": temporal_attestation_consistent,
            "project_current_chapter": current_chapter,
            "lag_chapters": capture_lag,
            "contemporaneous": contemporaneous,
            "canonical_health_pass": health_pass,
            "registered_session": True,
            "session_anchor_consistent": session_anchor_consistent,
            "evidence_eligible": bool(contemporaneous and health_pass and temporal_attestation_consistent and session_anchor_consistent),
        },
        "trace": trace,
        "canonical_health": health,
        "human_review": inp.get("human_review", {}),
        "integrity_notes": inp.get("integrity_notes", {}),
        "maintenance": inp.get("maintenance", {}),
        "probes": inp.get("probes", []),
        "creative_longitudinal": inp.get("creative_longitudinal", {}),
        "environment": inp.get("environment", {}),
        "resume_probe": inp.get("resume_probe"),
    }
    cp_errors = verify_checkpoint_record(record, campaign_dir)
    if cp_errors:
        raise ValueError("; ".join(cp_errors))
    rel = f"checkpoints/{cid}.json"
    checkpoint_path = campaign_dir / rel
    write_json(checkpoint_path, record)
    checkpoint_sha = sha256_file(checkpoint_path)
    manifest["checkpoint_index"].append({"checkpoint_id": cid, "chapter": inp["chapter"], "recorded_at": inp["recorded_at"], "path": rel, "sha256": checkpoint_sha})
    write_json(manifest_path, manifest)
    records, gather_errors = gather_records(campaign_dir, manifest)
    level, _ = maturity(records, manifest)
    result = {"checkpoint_id": cid, "chapter": inp["chapter"], "canonical_health_pass": health_pass, "contemporaneous": contemporaneous, "temporal_attestation_consistent": temporal_attestation_consistent, "session_anchor_consistent": session_anchor_consistent, "evidence_eligible": bool(contemporaneous and health_pass and temporal_attestation_consistent and session_anchor_consistent), "evidence_level": level, "errors": gather_errors}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"recorded {cid}; evidence {level}")
    return 1 if gather_errors else 0


def verify_campaign(campaign_dir: Path, project_root: Path) -> dict[str, Any]:
    manifest_path, manifest = load_campaign(campaign_dir)
    project_manifest_path, project = load_project_manifest(project_root)
    errors: list[str] = []
    warnings: list[str] = []
    if project.get("project_id") != manifest.get("project_id"):
        errors.append("campaign project_id does not match project manifest")
    registration_chapter = int((manifest.get("registration") or {}).get("project_chapter") or 0)
    if int(project.get("current_chapter") or 0) < registration_chapter:
        errors.append("current project chapter is behind the campaign registration anchor")
    if str(project.get("project_id", "")).startswith("LWA-LONG-HORIZON-"):
        errors.append("synthetic long-horizon benchmark project is ineligible for live evidence")
    records, record_errors = gather_records(campaign_dir, manifest)
    errors.extend(record_errors)
    sessions, session_errors = gather_sessions(campaign_dir, manifest)
    errors.extend(session_errors)
    # Check index-level uniqueness and canonical chapter range.
    index = manifest.get("checkpoint_index", [])
    indexed_ids = [x.get("checkpoint_id") for x in index if isinstance(x, dict)]
    if len(indexed_ids) != len(set(indexed_ids)):
        errors.append("checkpoint index contains duplicate IDs")
    target = int(manifest.get("target_chapters", 0))
    if manifest.get("canonical_checkpoints") != canonical_checkpoints(target, registration_chapter):
        warnings.append("canonical_checkpoints differ from current registration-relative protocol recommendation")
    # The present project may have moved since a historical checkpoint. Report current health separately.
    project_health = canonical_health(project_root, project_manifest_path, bool(runtime_trace(project_root, project).get("active")))
    if not project_health["project_verify"]["passed"]:
        errors.append("current project manifest verification fails")
    if not project_health["semantic_kernel"]["passed"]:
        errors.append("current Narrative Semantics Kernel verification fails")
    if project_health.get("runtime_schema") is not None and not project_health["runtime_schema"]["passed"]:
        errors.append("current Runtime schema verification fails")
    summary = summarize_evidence(records, registration_chapter)
    level, level_details = maturity(records, manifest)
    return {
        "campaign_manifest": str(manifest_path),
        "campaign_id": manifest.get("campaign_id"),
        "project_id": manifest.get("project_id"),
        "target_chapters": target,
        "record_count": len(records),
        "session_summary": summarize_sessions(sessions),
        "registration": manifest.get("registration"),
        "session_logging_scope": (manifest.get("source_attestation") or {}).get("session_logging_scope"),
        "evidence_summary": summary,
        "evidence_level": level,
        "level_requirements": level_details,
        "current_project_health": project_health,
        "errors": errors,
        "warnings": warnings,
        "verified": not errors,
    }


def cmd_verify(args: argparse.Namespace) -> int:
    report = verify_campaign(args.campaign_dir.resolve(), args.project_root.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"verified={report['verified']} level={report['evidence_level']} records={report['record_count']} errors={len(report['errors'])} warnings={len(report['warnings'])}")
    return 0 if report["verified"] else 1


def cmd_status(args: argparse.Namespace) -> int:
    campaign_dir = args.campaign_dir.resolve()
    report = verify_campaign(campaign_dir, args.project_root.resolve())
    _, manifest = load_campaign(campaign_dir)
    records, _ = gather_records(campaign_dir, manifest)
    sessions, _ = gather_sessions(campaign_dir, manifest)
    compact = {
        "campaign_id": report["campaign_id"],
        "project_id": report["project_id"],
        "evidence_level": report["evidence_level"],
        "evidence_summary": report["evidence_summary"],
        "session_summary": report.get("session_summary"),
        "registration": report.get("registration"),
        "session_logging_scope": report.get("session_logging_scope"),
        "evidence_passport": evidence_passport(records, manifest, sessions),
        "next_level_blockers": [],
        "errors": report["errors"],
        "warnings": report["warnings"],
    }
    current = LEVEL_ORDER[report["evidence_level"]]
    if current < 6:
        next_level = f"L{current + 1}"
        compact["next_level"] = next_level
        compact["next_level_blockers"] = report["level_requirements"].get(next_level, [])
    print(json.dumps(compact, ensure_ascii=False, indent=2) if args.json else json.dumps(compact, ensure_ascii=False, indent=2))
    return 0 if not report["errors"] else 1


def cmd_trajectory(args: argparse.Namespace) -> int:
    campaign_dir = args.campaign_dir.resolve()
    project_root = args.project_root.resolve()
    verification = verify_campaign(campaign_dir, project_root)
    _, manifest = load_campaign(campaign_dir)
    records, record_errors = gather_records(campaign_dir, manifest)
    sessions, session_errors = gather_sessions(campaign_dir, manifest)
    report = {
        "campaign_id": manifest.get("campaign_id"),
        "project_id": manifest.get("project_id"),
        "evidence_level": verification.get("evidence_level"),
        "trajectory": trajectory_report(records, manifest, sessions),
        "errors": list(verification.get("errors", [])) + record_errors + session_errors,
        "warnings": verification.get("warnings", []),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not report["errors"] else 1


def cmd_claim(args: argparse.Namespace) -> int:
    if args.level not in LEVEL_ORDER:
        raise ValueError(f"unknown evidence level: {args.level}")
    report = verify_campaign(args.campaign_dir.resolve(), args.project_root.resolve())
    achieved = LEVEL_ORDER[report["evidence_level"]]
    requested = LEVEL_ORDER[args.level]
    reasons = list(report["errors"])
    if achieved < requested:
        reasons.extend(report["level_requirements"].get(args.level, []))
    passed = not reasons and achieved >= requested
    campaign_dir = args.campaign_dir.resolve()
    _, manifest = load_campaign(campaign_dir)
    records, _ = gather_records(campaign_dir, manifest)
    sessions, _ = gather_sessions(campaign_dir, manifest)
    out = {
        "campaign_id": report["campaign_id"],
        "requested_claim": args.level,
        "achieved_level": report["evidence_level"],
        "claim_gate": "PASS" if passed else "FAIL",
        "reasons": reasons,
        "evidence_passport": evidence_passport(records, manifest, sessions),
        "session_summary": report.get("session_summary"),
        "claim_scope": "Registration-relative chapter-horizon evidence maturity only; calendar duration, inherited pre-registration memory, observational-vs-intervention probe evidence, and demonstrated memory-action distance are reported separately and are never inferred from absolute novel chapter count.",
        "limitation": "Artifact-backed protocol evidence cannot prove subjective human-review good faith or complete session logging; literary claims still require human judgment. Session-logging scope is an explicit attestation.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2) if args.json else json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if passed else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    x = sub.add_parser("registry", help="validate/show the bundled planned campaign portfolio")
    x.add_argument("--json", action="store_true")

    x = sub.add_parser("init", help="initialize longitudinal evidence for a real creative project")
    x.add_argument("campaign_dir", type=Path)
    x.add_argument("--project-root", type=Path, required=True)
    x.add_argument("--campaign-id", required=True)
    x.add_argument("--track", choices=sorted(ALLOWED_TRACKS), required=True)
    x.add_argument("--target-chapters", type=int, default=100)
    x.add_argument("--created-at")
    x.add_argument("--attestation-notes")
    x.add_argument("--session-logging-scope", choices=sorted(SESSION_LOGGING_SCOPES), default="checkpoint-linked-only")
    x.add_argument("--notes")
    x.add_argument("--json", action="store_true")

    x = sub.add_parser("session-start", help="register the start of an instrumented real creative session")
    x.add_argument("campaign_dir", type=Path)
    x.add_argument("--project-root", type=Path, required=True)
    x.add_argument("--session-id", required=True)
    x.add_argument("--agent-or-model")
    x.add_argument("--context-mode")
    x.add_argument("--fresh-context", action="store_true")
    x.add_argument("--notes")
    x.add_argument("--json", action="store_true")

    x = sub.add_parser("session-end", help="close an instrumented session and preserve its outcome, including abort/recovery")
    x.add_argument("campaign_dir", type=Path)
    x.add_argument("--project-root", type=Path, required=True)
    x.add_argument("--session-id", required=True)
    x.add_argument("--outcome", choices=sorted(SESSION_OUTCOMES), required=True)
    x.add_argument("--notes")
    x.add_argument("--json", action="store_true")

    x = sub.add_parser("checkpoint", help="record one trace-grounded live-campaign checkpoint")
    x.add_argument("campaign_dir", type=Path)
    x.add_argument("input_json", type=Path)
    x.add_argument("--project-root", type=Path, required=True)
    x.add_argument("--json", action="store_true")

    for name, help_text in (("verify", "verify campaign evidence integrity"), ("status", "summarize current evidence maturity")):
        x = sub.add_parser(name, help=help_text)
        x.add_argument("campaign_dir", type=Path)
        x.add_argument("--project-root", type=Path, required=True)
        x.add_argument("--json", action="store_true")

    x = sub.add_parser("trajectory", help="describe longitudinal trends without collapsing them into one score")
    x.add_argument("campaign_dir", type=Path)
    x.add_argument("--project-root", type=Path, required=True)
    x.add_argument("--json", action="store_true")

    x = sub.add_parser("claim", help="check whether a real-evidence maturity claim is currently supported")
    x.add_argument("campaign_dir", type=Path)
    x.add_argument("--project-root", type=Path, required=True)
    x.add_argument("--level", choices=list(LEVEL_ORDER), required=True)
    x.add_argument("--json", action="store_true")
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "registry":
            return cmd_registry(args.json)
        if args.command == "init":
            if args.target_chapters < 1:
                raise ValueError("--target-chapters must be >= 1")
            return cmd_init(args)
        if args.command == "session-start":
            return cmd_session_start(args)
        if args.command == "session-end":
            return cmd_session_end(args)
        if args.command == "checkpoint":
            return cmd_checkpoint(args)
        if args.command == "verify":
            return cmd_verify(args)
        if args.command == "status":
            return cmd_status(args)
        if args.command == "trajectory":
            return cmd_trajectory(args)
        if args.command == "claim":
            return cmd_claim(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
