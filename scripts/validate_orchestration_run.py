#!/usr/bin/env python3
"""Validate orchestration profiles, pass isolation claims, hashes, and checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from orchestration_contract import EXECUTION_PROFILES, ROLE_CLEARANCE
PROFILES = EXECUTION_PROFILES
STATUSES = {"PENDING", "PLANNED", "RUNNING", "BLOCKED", "DONE", "VERIFIED", "FAILED", "REJECTED"}

OPERATION_VERSION = "1.0.0"
OPERATION_STATES = {"PLANNED", "RUNNING", "DONE", "VERIFIED", "FAILED"}
OPERATION_TRANSITIONS = {
    "PLANNED": {"RUNNING"}, "RUNNING": {"DONE", "FAILED"},
    "DONE": {"VERIFIED", "FAILED"}, "VERIFIED": set(), "FAILED": set(),
}


def evidence_record(root: Path | None, ref: Any) -> dict[str, Any]:
    """Read a content-bound receipt, never a timestamp or narration flag."""
    if root is None:
        raise ValueError("operational evidence requires --root")
    if not isinstance(ref, dict) or not isinstance(ref.get("ref"), str) or not ref["ref"]:
        raise ValueError("evidence requires ref and sha256")
    path = resolve_inside(root, ref["ref"])
    if not path.is_file() or sha256_file(path) != ref.get("sha256"):
        raise ValueError(f"missing or changed evidence: {ref['ref']}")
    return load_obj(path)


def operation_view(item: dict[str, Any], root: Path | None) -> dict[str, Any]:
    """Validate the existing run extension; reports cannot promote/demote evidence."""
    if "operational_version" not in item:
        return {"status": "LEGACY_UNKNOWN_VERIFICATION", "declared_status": item.get("status"),
                "errors": ["legacy record cannot declare VERIFIED"] if item.get("status") == "VERIFIED" else [], "report_conflicts": [], "verification": "unavailable"}
    errors: list[str] = []
    supported = "PLANNED"
    op_id = item.get("operation_id")
    if item.get("operational_version") != OPERATION_VERSION:
        errors.append("unknown operational_version")
    if not isinstance(op_id, str) or not op_id.strip() or not item.get("operation_type"):
        errors.append("operation_id and operation_type are required")
    invocation = completion = None
    try:
        if item.get("started_evidence") is not None:
            invocation = evidence_record(root, item["started_evidence"])
            if (invocation.get("kind") != "invocation" or invocation.get("operation_id") != op_id
                    or not invocation.get("invocation_id") or not invocation.get("executor")):
                raise ValueError("start requires an operation-bound executor invocation receipt")
            supported = "RUNNING"
        if item.get("completion_evidence") is not None:
            if invocation is None:
                raise ValueError("completion without invocation")
            completion = evidence_record(root, item["completion_evidence"])
            if (completion.get("kind") != "completion" or completion.get("operation_id") != op_id
                    or completion.get("invocation_id") != invocation["invocation_id"]
                    or completion.get("outcome") != "success"):
                raise ValueError("completion must bind the successful invocation result")
            outputs = completion.get("outputs")
            if not isinstance(outputs, list) or not outputs:
                raise ValueError("completion requires at least one expected artifact/tool-result")
            for output in outputs:
                if not isinstance(output, dict) or not output.get("ref"):
                    raise ValueError("completion output requires ref and sha256")
                path = resolve_inside(root, output["ref"])
                if not path.is_file() or sha256_file(path) != output.get("sha256"):
                    raise ValueError("completion output missing or changed")
            supported = "DONE"
        if item.get("verification_evidence") is not None:
            if completion is None:
                raise ValueError("verification without completion")
            verification = evidence_record(root, item["verification_evidence"])
            if (verification.get("kind") != "verification" or verification.get("operation_id") != op_id
                    or verification.get("completion_sha256") != item["completion_evidence"]["sha256"]
                    or verification.get("method") not in {"deterministic-check", "main-agent-inspection"}
                    or not verification.get("verifier") or verification.get("result") != "PASS"
                    or verification.get("basis") != "artifact-inspection"
                    or verification.get("verifier") != item.get("verified_by")):
                raise ValueError("verification requires method, verifier, PASS and completion-bound independent artifact inspection")
            supported = "VERIFIED"
        if item.get("failure_evidence") is not None:
            failure = evidence_record(root, item["failure_evidence"])
            if (invocation is None or failure.get("kind") != "failure" or failure.get("operation_id") != op_id
                    or failure.get("invocation_id") != invocation["invocation_id"]
                    or not item.get("failure_reason") or failure.get("reason") != item["failure_reason"]
                    or not isinstance(item.get("retryable"), bool)):
                raise ValueError("FAILED requires invocation, failure receipt, reason and retryable boolean")
            if item.get("verification_evidence") is not None:
                raise ValueError("FAILED cannot retain successful verification")
            supported = "FAILED"
    except (ValueError, TypeError, KeyError, OSError) as exc:
        errors.append(str(exc))
    declared = item.get("status")
    if not isinstance(declared, str) or declared not in OPERATION_STATES or declared != supported:
        errors.append(f"declared status {declared!r} disagrees with evidence-supported {supported}")
    history = item.get("transitions")
    if not isinstance(history, list) or not history or history[0] != "PLANNED":
        errors.append("transitions must start at PLANNED")
    else:
        for before, after in zip(history, history[1:]):
            if not isinstance(before, str) or not isinstance(after, str) or after not in OPERATION_TRANSITIONS.get(before, set()):
                errors.append(f"impossible transition: {before!r}->{after!r}")
        if history[-1] != declared:
            errors.append("last transition disagrees with declared status")
    reports = item.get("reports", [])
    conflicts = []
    if not isinstance(reports, list):
        errors.append("reports must be a list")
    else:
        for report in reports:
            if not isinstance(report, dict) or not report.get("reported_by") or not isinstance(report.get("status"), str) or report.get("status") not in OPERATION_STATES:
                errors.append("report requires reported_by and reported status")
            elif report["status"] != supported:
                conflicts.append({**report, "authoritative_status": supported})
    return {"status": supported, "declared_status": declared, "errors": errors,
            "report_conflicts": conflicts, "verified_by": item.get("verified_by") if supported == "VERIFIED" else None}


def load_obj(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_inside(root: Path, rel: str) -> Path:
    path = (root / rel).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes root: {rel}") from exc
    return path


def validate_profile(profile: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    selected = profile.get("selected_profile")
    if selected not in PROFILES:
        errors.append(f"unknown selected_profile: {selected!r}")
    cap = profile.get("capabilities")
    if not isinstance(cap, dict):
        errors.append("profile.capabilities must be an object")
        cap = {}
    for key in (
        "native_subagents",
        "fresh_model_contexts",
        "isolated_agent_contexts",
        "persistent_files",
        "deterministic_tools",
        "isolated_workspaces",
        "filesystem_permission_enforcement",
        "independent_evaluator",
    ):
        if key in cap and not isinstance(cap.get(key), bool):
            errors.append(f"capability {key!r} must be boolean")

    if selected == "native-multi-agent" and not cap.get("native_subagents", False):
        errors.append("native-multi-agent selected without native_subagents capability")
    if selected == "clean-room-serial" and not cap.get("fresh_model_contexts", False):
        errors.append("clean-room-serial selected without fresh_model_contexts capability")
    if selected in {"clean-room-serial", "soft-serial"} and not cap.get("persistent_files", False):
        errors.append(f"{selected} requires persistent_files for explicit handoffs/checkpoints")
    strong_blind_capability = (selected == "clean-room-serial" and cap.get("fresh_model_contexts", False)) or (selected == "native-multi-agent" and cap.get("isolated_agent_contexts", False))
    if profile.get("blind_writer_supported") is True and not strong_blind_capability:
        errors.append("blind_writer_supported overclaims the selected profile/capabilities")
    if profile.get("blind_reader_supported") is True and not strong_blind_capability:
        errors.append("blind_reader_supported overclaims the selected profile/capabilities")
    if profile.get("independent_audit_supported") is True and not cap.get("independent_evaluator", False):
        errors.append("independent_audit_supported requires independent_evaluator capability")
    if not cap.get("deterministic_tools", False):
        warnings.append("deterministic_tools unavailable; do not treat same-model review as equivalent external verification")
    return errors, warnings


def load_passes(path: Path) -> list[tuple[Path, dict[str, Any]]]:
    if path.is_file():
        return [(path, load_obj(path))]
    if not path.is_dir():
        raise ValueError(f"passes path does not exist: {path}")
    files = sorted(p for p in path.glob("*.json") if p.is_file())
    return [(p, load_obj(p)) for p in files]


def validate_passes(
    profile: dict[str, Any],
    pass_items: list[tuple[Path, dict[str, Any]]],
    root: Path | None,
) -> tuple[list[str], list[str], set[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    selected = str(profile.get("selected_profile", ""))
    independent_supported = bool(profile.get("independent_audit_supported", False))

    # Track maximum clearance seen inside each continuing model context.
    max_seen_by_context: dict[str, int] = {}

    for path, item in pass_items:
        prefix = f"{path.name}: "
        pass_id = str(item.get("pass_id", "")).strip()
        if not pass_id:
            errors.append(prefix + "missing pass_id")
        elif pass_id in seen_ids:
            errors.append(prefix + f"duplicate pass_id {pass_id!r}")
        else:
            seen_ids.add(pass_id)

        role = str(item.get("role", ""))
        if role not in ROLE_CLEARANCE:
            errors.append(prefix + f"unknown role {role!r}")
            expected_clearance = None
        else:
            expected_clearance = ROLE_CLEARANCE[role]

        status = str(item.get("status", ""))
        if status not in STATUSES:
            errors.append(prefix + f"unknown status {status!r}")

        view = operation_view(item, root)
        errors.extend(prefix + msg for msg in view["errors"])
        warnings.extend(prefix + "report conflicts with authoritative machine state: " + str(row) for row in view["report_conflicts"])
        if "operational_version" not in item:
            warnings.append(prefix + "legacy operational evidence: verification unknown; no VERIFIED promotion")

        item_profile = str(item.get("execution_profile", selected))
        if item_profile != selected:
            errors.append(prefix + f"execution_profile {item_profile!r} disagrees with run profile {selected!r}")

        clearance = item.get("clearance")
        if not isinstance(clearance, int) or not 0 <= clearance <= 3:
            errors.append(prefix + "clearance must be integer 0..3")
        elif expected_clearance is not None and clearance != expected_clearance:
            warnings.append(prefix + f"clearance {clearance} differs from canonical role clearance {expected_clearance}")

        fresh = item.get("fresh_context") is True
        blindness_required = item.get("blindness_required") is True
        blindness_claimed = item.get("blindness_claimed") is True
        independent_claimed = item.get("independent_review_claimed") is True
        context_id = str(item.get("context_id", "")).strip()

        cap = profile.get("capabilities") if isinstance(profile.get("capabilities"), dict) else {}
        native_isolated = selected == "native-multi-agent" and bool(cap.get("isolated_agent_contexts", False))
        serial_isolated = selected == "clean-room-serial" and fresh
        pass_isolated = native_isolated or serial_isolated
        if blindness_claimed and not pass_isolated:
            errors.append(prefix + "claims blindness without an isolated/fresh model context")
        if blindness_required and not blindness_claimed:
            errors.append(prefix + "blindness is required but not claimed/satisfied")
        if blindness_claimed and selected == "clean-room-serial" and not fresh:
            errors.append(prefix + "clean-room blind pass must use fresh_context=true")
        if role == "reader-simulator" and blindness_claimed and not pass_isolated:
            errors.append(prefix + "blind Reader Simulator requires an isolated/fresh context")
        if independent_claimed and not independent_supported:
            errors.append(prefix + "claims independent review without an independent evaluator")

        if context_id:
            previous_max = max_seen_by_context.get(context_id)
            if isinstance(clearance, int):
                if previous_max is not None and clearance < previous_max:
                    if blindness_claimed:
                        errors.append(prefix + f"clearance downgrade {previous_max}->{clearance} reuses contaminated context {context_id!r}")
                    else:
                        warnings.append(prefix + f"clearance downgrade {previous_max}->{clearance} in same context is soft/nonblind")
                max_seen_by_context[context_id] = max(previous_max if previous_max is not None else clearance, clearance)

        if item.get("handoff_sanitized_for_role") is False and role in {"writer", "reader-simulator"}:
            errors.append(prefix + "lower-clearance role received an unsanitized handoff")

        blockers = item.get("blockers", [])
        if not isinstance(blockers, list):
            errors.append(prefix + "blockers must be a list")
        elif status in {"DONE", "VERIFIED"} and blockers:
            errors.append(prefix + "DONE pass cannot retain blockers")

        for field in ("input_artifacts", "allowed_outputs", "output_artifacts", "handoff_from"):
            if field in item and not isinstance(item.get(field), list):
                errors.append(prefix + f"{field} must be a list")

        if role in {"writer", "reader-simulator"}:
            if not str(item.get("context_pack_path", "")).strip():
                errors.append(prefix + "role requires context_pack_path")
            if not str(item.get("context_manifest_path", "")).strip():
                errors.append(prefix + "role requires context_manifest_path")

        expected_hash = item.get("context_pack_sha256")
        pack_path = item.get("context_pack_path")
        manifest_path = item.get("context_manifest_path")
        if root is not None and isinstance(pack_path, str) and pack_path and isinstance(expected_hash, str) and expected_hash:
            try:
                p = resolve_inside(root, pack_path)
                if not p.is_file():
                    errors.append(prefix + f"context pack missing: {pack_path}")
                elif sha256_file(p) != expected_hash:
                    errors.append(prefix + "context_pack_sha256 mismatch")
            except Exception as exc:
                errors.append(prefix + str(exc))

        if root is not None and isinstance(manifest_path, str) and manifest_path:
            try:
                mp = resolve_inside(root, manifest_path)
                if not mp.is_file():
                    errors.append(prefix + f"context manifest missing: {manifest_path}")
                else:
                    manifest = load_obj(mp)
                    if manifest.get("role") != role:
                        errors.append(prefix + "context manifest role disagrees with pass role")
                    if str(manifest.get("branch", "main")) != str(item.get("branch", "main")):
                        errors.append(prefix + "context manifest branch disagrees with pass branch")
                    manifest_profile = manifest.get("execution_profile")
                    if manifest_profile is not None and str(manifest_profile) != selected:
                        errors.append(prefix + "context manifest execution_profile disagrees with run profile")
                    if isinstance(expected_hash, str) and expected_hash and manifest.get("pack_sha256") != expected_hash:
                        errors.append(prefix + "context manifest pack_sha256 disagrees with pass envelope")
                    if blindness_claimed and manifest.get("strict_visibility") is not True:
                        errors.append(prefix + "blind pass requires strict_visibility context manifest")
                    if role == "writer":
                        scoped_ref = manifest.get("scoped_project_poetics_ref")
                        pass_scoped_ref = item.get("scoped_project_poetics_ref")
                        scoped_envelope_ref = manifest.get("scoped_project_poetics_envelope_ref")
                        pass_envelope_ref = item.get("scoped_project_poetics_envelope_ref")
                        if pass_scoped_ref is not None and scoped_ref != pass_scoped_ref:
                            errors.append(prefix + "pass envelope scoped_project_poetics_ref disagrees with context manifest")
                        if pass_envelope_ref is not None and scoped_envelope_ref != pass_envelope_ref:
                            errors.append(prefix + "pass envelope scoped_project_poetics_envelope_ref disagrees with context manifest")
                        if scoped_ref and not scoped_envelope_ref:
                            errors.append(prefix + "writer context has scoped Project Poetics without provenance envelope")
                        if manifest.get("project_poetics_ref") and not scoped_ref:
                            warnings.append(prefix + "writer context has canonical Project Poetics but no explicit writer-safe scoped derivative; valid for legacy packs but review substantial drafting flows")
                    included = manifest.get("included", [])
                    if not isinstance(included, list):
                        errors.append(prefix + "context manifest included must be a list")
                    else:
                        for row in included:
                            if not isinstance(row, dict):
                                continue
                            vis = str(row.get("visibility", "unmarked"))
                            if role == "reader-simulator" and vis != "reader-visible":
                                errors.append(prefix + f"reader context includes non-reader-visible item {row.get('id')!r}: {vis}")
                            if role == "writer" and blindness_claimed and vis not in {"reader-visible", "writer-visible", "role-internal"}:
                                errors.append(prefix + f"blind writer context includes unsafe visibility {vis!r} for {row.get('id')!r}")
            except Exception as exc:
                errors.append(prefix + f"context manifest validation failed: {exc}")

        if status in {"DONE", "VERIFIED"} and root is not None:
            outputs = item.get("output_artifacts", [])
            if isinstance(outputs, list):
                for raw in outputs:
                    if isinstance(raw, str):
                        rel = raw
                        expected = None
                    elif isinstance(raw, dict):
                        rel = str(raw.get("path", ""))
                        expected = raw.get("sha256")
                    else:
                        errors.append(prefix + "output_artifacts entries must be strings or objects")
                        continue
                    if not rel:
                        errors.append(prefix + "output artifact lacks path")
                        continue
                    try:
                        p = resolve_inside(root, rel)
                        if not p.is_file():
                            errors.append(prefix + f"DONE output missing: {rel}")
                        elif isinstance(expected, str) and expected and sha256_file(p) != expected:
                            errors.append(prefix + f"output hash mismatch: {rel}")
                    except Exception as exc:
                        errors.append(prefix + str(exc))

    return errors, warnings, seen_ids


def validate_checkpoint(checkpoint: dict[str, Any], pass_ids: set[str], profile_name: str, root: Path | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if checkpoint.get("execution_profile") != profile_name:
        errors.append("checkpoint execution_profile disagrees with profile")
    for key in ("last_completed_pass", "active_pass"):
        value = checkpoint.get(key)
        if value is not None and str(value) not in pass_ids:
            errors.append(f"checkpoint {key} references unknown pass {value!r}")
    pending = checkpoint.get("pending_passes", [])
    if not isinstance(pending, list):
        errors.append("checkpoint pending_passes must be a list")
    else:
        unknown = [str(x) for x in pending if str(x) not in pass_ids]
        if unknown:
            errors.append("checkpoint pending_passes reference unknown passes: " + ", ".join(unknown))
    refs = checkpoint.get("pass_envelopes", [])
    if not isinstance(refs, list):
        errors.append("checkpoint pass_envelopes must be a list")
    if checkpoint.get("status") == "DONE" and checkpoint.get("active_pass") is not None:
        warnings.append("DONE checkpoint still has active_pass")
    if "operational_version" in checkpoint:
        if checkpoint["operational_version"] != OPERATION_VERSION:
            errors.append("unknown checkpoint operational_version")
        operations = checkpoint.get("operations")
        if not isinstance(operations, dict):
            errors.append("new checkpoint requires registered operations")
        else:
            for op_id, item in operations.items():
                if not isinstance(item, dict) or item.get("operation_id") != op_id or item.get("operational_version") != OPERATION_VERSION:
                    errors.append("checkpoint operation identity mismatch")
                    continue
                view = operation_view(item, root)
                errors.extend(f"{op_id}: {msg}" for msg in view["errors"])
                warnings.extend(f"{op_id}: report conflicts with authoritative machine state" for row in view["report_conflicts"])
    else:
        warnings.append("legacy checkpoint: operational verification unknown")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate role-isolated orchestration run artifacts")
    parser.add_argument("profile", type=Path, help="execution-profile JSON")
    parser.add_argument("passes", type=Path, help="pass envelope JSON or directory of pass JSON files")
    parser.add_argument("--root", type=Path, help="project root for artifact/hash checks")
    parser.add_argument("--checkpoint", type=Path, help="optional run checkpoint JSON")
    args = parser.parse_args()

    try:
        profile = load_obj(args.profile)
        pass_items = load_passes(args.passes)
        root = args.root.resolve() if args.root else None
        errors, warnings = validate_profile(profile)
        e2, w2, pass_ids = validate_passes(profile, pass_items, root)
        errors.extend(e2)
        warnings.extend(w2)
        if args.checkpoint:
            checkpoint = load_obj(args.checkpoint)
            e3, w3 = validate_checkpoint(checkpoint, pass_ids, str(profile.get("selected_profile", "")), root)
            errors.extend(e3)
            warnings.extend(w3)
            for path, item in pass_items:
                op = checkpoint.get("operations", {}).get(item.get("operation_id")) if isinstance(checkpoint.get("operations"), dict) else None
                if isinstance(op, dict) and item.get("status") != op.get("status"):
                    errors.append(f"{path.name}: pass status conflicts with canonical checkpoint operation")
    except Exception as exc:
        print(f"ERROR: orchestration validation failed: {exc}", file=sys.stderr)
        return 2

    for msg in warnings:
        print(f"WARNING: {msg}")
    for msg in errors:
        print(f"ERROR: {msg}")
    print(f"summary: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
