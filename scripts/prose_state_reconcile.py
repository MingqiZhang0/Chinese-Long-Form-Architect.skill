#!/usr/bin/env python3
"""Validate the two-way contract between chapter prose and durable story-state deltas.

The tool validates evidence and review completeness. It deliberately does not infer
story facts from prose by itself; semantic candidate extraction remains an LLM/human
review task so deterministic tooling cannot silently invent canon.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from capability_probe import CapabilityError, require_profile

try:
    import jsonschema
except Exception as exc:  # pragma: no cover
    jsonschema = None
    JSONSCHEMA_IMPORT_ERROR = exc
else:
    JSONSCHEMA_IMPORT_ERROR = None

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SCRIPT_ROOT / "assets" / "project-schemas" / "prose-state-reconciliation.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(root: Path, rel: str) -> Path:
    p = (root / rel).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {rel}") from exc
    return p


def schema_errors(data: Any) -> list[str]:
    if jsonschema is None:
        return [f"jsonschema package is required: {JSONSCHEMA_IMPORT_ERROR}"]
    schema = load_json(SCHEMA)
    validator = jsonschema.Draft202012Validator(schema)
    out: list[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        loc = ".".join(str(x) for x in err.absolute_path) or "$"
        out.append(f"{loc}: {err.message}")
    return out


def evidence_text(path: Path, start: int, end: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise ValueError(f"invalid evidence range {start}-{end} for {path} with {len(lines)} lines")
    return "\n".join(lines[start - 1:end])


def anchor(root: Path, path: Path, start: int, end: int) -> dict[str, Any]:
    return {"path": path.resolve().relative_to(root.resolve()).as_posix(),
            "start_line": start, "end_line": end,
            "sha256": sha(evidence_text(path, start, end))}


def leaf_values(value: Any, pointer: str = "") -> dict[str, Any]:
    """JSON pointers form an exhaustive inventory of a supplied (possibly scoped) state."""
    if isinstance(value, dict) and value:
        out = {}
        for key, child in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            out.update(leaf_values(child, pointer + "/" + escaped))
        return out
    if isinstance(value, list) and value:
        out = {}
        for index, child in enumerate(value):
            out.update(leaf_values(child, pointer + "/" + str(index)))
        return out
    return {pointer: value}


def prepare_report(root: Path, prose: Path, chapter: str, branch: str,
                   state: Path | None = None) -> dict[str, Any]:
    prose = safe_path(root, str(prose))
    from project_ops import rollover_project, resolve_final
    manifest, _ = rollover_project(root)
    if "chapter_rollover" in manifest:
        _, final = resolve_final(root, manifest, chapter, branch)
        if prose != safe_path(root, final["path"]):
            raise ValueError("rollover.noncanonical_reconciliation_source")
    lines = prose.read_text(encoding="utf-8").splitlines()
    # No lexical classifier: every nonblank line must be read, including quiet consequences.
    coverage = [{"evidence": anchor(root, prose, i, i), "candidate_ids": [],
                 "status": "pending", "rationale": ""}
                for i, line in enumerate(lines, 1) if line.strip()]
    review: dict[str, Any] = {"coverage": coverage,
                              "sources": [{"path": prose.relative_to(root).as_posix(), "sha256": file_sha(prose)}]}
    if state is not None:
        state = safe_path(root, str(state))
        review["state_snapshot"] = {"path": state.relative_to(root).as_posix(),
                                    "sha256": file_sha(state), "branch": branch}
        review["state_checks"] = [{"pointer": pointer, "value": value,
                                   "status": "pending", "evidence": [], "rationale": ""}
                                  for pointer, value in leaf_values(load_json(state)).items()]
    return {"reconciliation_version": "1.1.0", "chapter_id": chapter, "branch": branch,
            "prose_path": prose.relative_to(root).as_posix(), "prose_sha256": file_sha(prose),
            "status": "DRAFT", "prose_candidates": [], "state_deltas": [],
            "semantic_review": review}


def verify_anchor(ev: dict[str, Any], root: Path) -> list[str]:
    try:
        path = safe_path(root, ev["path"])
        text = evidence_text(path, ev["start_line"], ev["end_line"])
        return [] if sha(text) == ev["sha256"] else [f"evidence hash mismatch: {ev['path']}"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"invalid semantic evidence: {exc}"]


def validate_semantic_review(report: dict[str, Any], root: Path, strict: bool) -> list[str]:
    errors: list[str] = []
    review = report["semantic_review"]
    prose = safe_path(root, report["prose_path"])
    if not prose.is_file():
        return ["semantic coverage source is missing"]
    lines = prose.read_text(encoding="utf-8").splitlines()
    covered: set[int] = set()
    candidates = {x["candidate_id"]: x for x in report["prose_candidates"]}
    source_paths: set[Path] = set()
    for item in review["sources"]:
        path = safe_path(root, item["path"])
        if path in source_paths:
            errors.append("duplicate semantic evidence source")
        source_paths.add(path)
        if not path.is_file() or file_sha(path) != item["sha256"]:
            errors.append(f"semantic evidence source is missing or stale: {item['path']}")
    anchors = [row["evidence"] for row in review["coverage"]]
    anchors += [ev for row in candidates.values() for ev in row["semantics"]["evidence"]]
    anchors += [ev for row in report["state_deltas"] for ev in row["evidence"]]
    anchors += [ev for row in review.get("state_checks", []) for ev in row["evidence"]]
    if any(safe_path(root, ev["path"]) not in source_paths for ev in anchors):
        errors.append("semantic evidence references a source without a whole-file hash")
    cited: set[str] = set()
    for row in review["coverage"]:
        ev = row["evidence"]
        errors.extend(verify_anchor(ev, root))
        if safe_path(root, ev["path"]) != prose:
            errors.append("coverage evidence must belong to the reconciled prose")
        span = set(range(ev["start_line"], ev["end_line"] + 1))
        if covered & span:
            errors.append("semantic coverage ranges overlap")
        covered.update(span)
        for cid in row["candidate_ids"]:
            if cid not in candidates:
                errors.append(f"coverage references missing candidate {cid}")
            cited.add(cid)
            if cid in candidates and not any(
                safe_path(root, item["path"]) == prose
                and ev["start_line"] <= item["start_line"] <= item["end_line"] <= ev["end_line"]
                for item in candidates[cid]["semantics"]["evidence"]
            ):
                errors.append(f"coverage for {cid} does not contain its current-prose evidence")
        if strict and (row["status"] != "reviewed" or not row["rationale"].strip()):
            errors.append("semantic coverage has an unreviewed range or no rationale")
    missing = {i for i, line in enumerate(lines, 1) if line.strip()} - covered
    if missing:
        errors.append(f"semantic coverage omits prose lines: {sorted(missing)}")
    for cid, row in candidates.items():
        if cid not in cited:
            errors.append(f"candidate {cid} is absent from prose coverage")
        sem = row["semantics"]
        for ev in sem["evidence"]:
            errors.extend(verify_anchor(ev, root))
        if not any(safe_path(root, ev["path"]) == prose for ev in sem["evidence"]):
            errors.append(f"candidate {cid} needs current-chapter evidence")
        if sem["layer"] in {"actor_belief", "actor_knowledge"} and not sem.get("holder"):
            errors.append(f"candidate {cid} lacks the actor holding the belief/knowledge")
        if row["disposition"] == "committed":
            if sem["mode"] in {"metaphor", "counterfactual", "intention"}:
                errors.append(f"candidate {cid}: nonactual content needs a separate actual belief/plan/speech-act claim")
            if sem["layer"] in {"world", "actor_knowledge"} and (
                sem["truth"] != "established" or sem["mode"] != "assertion"
            ):
                errors.append(f"candidate {cid}: non-established content cannot be committed as world truth/knowledge")
        if strict and not sem["rationale"].strip():
            errors.append(f"candidate {cid} has no semantic rationale")
        for did in row["delta_ids"]:
            delta = next((item for item in report["state_deltas"] if item["delta_id"] == did), None)
            if row["disposition"] != "committed":
                errors.append(f"noncommitted candidate {cid} may not support delta {did}")
            if delta and (delta.get("layer") != sem["layer"] or delta.get("holder") != sem.get("holder")):
                errors.append(f"candidate {cid} and delta {did} differ in semantic layer/holder")
    snapshot = review.get("state_snapshot")
    checks = review.get("state_checks", [])
    if snapshot:
        if snapshot["branch"] != report["branch"]:
            errors.append("state snapshot branch differs from reconciliation branch")
        source = safe_path(root, snapshot["path"])
        if not source.is_file() or file_sha(source) != snapshot["sha256"]:
            errors.append("state snapshot is missing or stale")
        else:
            inventory = leaf_values(load_json(source))
            pointers = [row["pointer"] for row in checks]
            if len(pointers) != len(set(pointers)) or set(pointers) != set(inventory):
                errors.append("state audit must cover each snapshot leaf exactly once")
            for row in checks:
                if row["pointer"] not in inventory or row["value"] != inventory[row["pointer"]]:
                    errors.append(f"state audit value mismatch: {row['pointer']}")
    elif checks:
        errors.append("state checks require a hash-bound state snapshot")
    for row in checks:
        for ev in row["evidence"]:
            errors.extend(verify_anchor(ev, root))
        if row["status"] == "supported" and not row["evidence"]:
            errors.append(f"supported state {row['pointer']} has no evidence")
        if row["status"] == "supported" and snapshot and any(
            safe_path(root, ev["path"]) == safe_path(root, snapshot["path"]) for ev in row["evidence"]
        ):
            errors.append(f"state snapshot cannot serve as its own prose support: {row['pointer']}")
        if strict and (row["status"] in {"pending", "unsupported"} or not row["rationale"].strip()):
            errors.append(f"state audit unresolved/unsupported: {row['pointer']}")
    return errors


def validate_report(report: dict[str, Any], root: Path, *, strict: bool) -> tuple[list[str], list[str], dict[str, Any]]:
    errors = [f"schema {x}" for x in schema_errors(report)]
    warnings: list[str] = []
    if errors:
        return errors, warnings, {}

    if report.get("rollover_receipt", {}).get("effect") == "FORMAT_ONLY_NO_STATE_DELTA":
        from project_ops import rollover_project, resolve_final, validate_freeze
        try:
            manifest, _ = rollover_project(root)
            chapter, final = resolve_final(root, manifest, report["chapter_id"], report["branch"])
            current = validate_freeze(root, manifest, chapter, final)
            if current["reconciliation_id"] != report["reconciliation_id"]:
                raise ValueError("rollover.reconciliation_stale")
            return [], [], {"chapter_id": report["chapter_id"], "status": "APPROVED", "strict": strict,
                            "formatting_proof_checked": True, "semantic_coverage_checked": False,
                            "state_inventory_checked": True}
        except (OSError, ValueError, KeyError, TypeError, StopIteration):
            return ["rollover.formatting_proof_invalid"], [], {}
    prose_path = safe_path(root, str(report["prose_path"]))
    from project_ops import rollover_project, resolve_final
    manifest, _ = rollover_project(root)
    if "chapter_rollover" in manifest:
        try:
            _, final = resolve_final(root, manifest, report["chapter_id"], report["branch"])
            if prose_path != safe_path(root, final["path"]) or report["prose_sha256"] != final["final_prose_sha256"]:
                errors.append("rollover.noncanonical_reconciliation_source")
        except (OSError, ValueError, KeyError, TypeError):
            errors.append("rollover.noncanonical_reconciliation_source")
    if not prose_path.is_file():
        errors.append(f"missing prose file: {report['prose_path']}")
    else:
        actual = file_sha(prose_path)
        if actual != report.get("prose_sha256"):
            errors.append("prose_sha256 does not match the current prose bytes; reconciliation is stale")

    deltas = report.get("state_deltas", [])
    candidates = report.get("prose_candidates", [])
    delta_by_id: dict[str, dict[str, Any]] = {}
    candidate_ids: set[str] = set()
    referenced_by_committed: set[str] = set()
    pending_candidates = 0
    verified_evidence = 0

    for row in deltas:
        did = str(row.get("delta_id"))
        if did in delta_by_id:
            errors.append(f"duplicate delta_id: {did}")
        delta_by_id[did] = row

        basis = str(row.get("basis"))
        evidence = row.get("evidence", [])
        if basis == "prose" and not evidence:
            errors.append(f"prose-based delta {did} has no evidence")
        if basis != "prose" and not str(row.get("basis_note", "")).strip():
            warnings.append(f"non-prose delta {did} should explain its basis in basis_note")
            if strict and report.get("reconciliation_version") == "1.1.0":
                errors.append(f"non-prose delta {did} requires basis_note in a strict semantic review")

        for ev in evidence:
            rel = str(ev.get("path"))
            try:
                source = safe_path(root, rel)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not source.is_file():
                errors.append(f"delta {did} evidence file missing: {rel}")
                continue
            try:
                text = evidence_text(source, int(ev.get("start_line")), int(ev.get("end_line")))
            except Exception as exc:
                errors.append(f"delta {did} evidence invalid: {exc}")
                continue
            if sha(text) != ev.get("sha256"):
                errors.append(f"delta {did} evidence hash mismatch for {rel}:{ev.get('start_line')}-{ev.get('end_line')}")
            else:
                verified_evidence += 1

    for row in candidates:
        cid = str(row.get("candidate_id"))
        if cid in candidate_ids:
            errors.append(f"duplicate candidate_id: {cid}")
        candidate_ids.add(cid)
        disposition = str(row.get("disposition"))
        delta_ids = [str(x) for x in row.get("delta_ids", [])]
        for did in delta_ids:
            if did not in delta_by_id:
                errors.append(f"candidate {cid} references missing delta_id {did}")
        if disposition == "committed":
            if not delta_ids:
                errors.append(f"committed prose candidate {cid} has no delta_ids")
            referenced_by_committed.update(delta_ids)
        elif disposition == "pending":
            pending_candidates += 1
            warnings.append(f"prose candidate {cid} is still pending review")

    for did, row in delta_by_id.items():
        if str(row.get("basis")) == "prose" and did not in referenced_by_committed:
            errors.append(f"prose-based state delta {did} is not linked from any committed prose candidate")

    if strict:
        if report.get("status") != "APPROVED":
            errors.append(f"strict reconciliation requires status=APPROVED, got {report.get('status')}")
        if pending_candidates:
            errors.append(f"strict reconciliation has {pending_candidates} pending prose candidates")

    if report.get("reconciliation_version") == "1.1.0":
        try:
            errors.extend(validate_semantic_review(report, root, strict))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"invalid semantic review inputs: {exc}")
    else:
        warnings.append("legacy 1.0 report verifies submitted evidence only; semantic coverage and state audit are not checked")

    summary = {
        "chapter_id": report.get("chapter_id"),
        "status": report.get("status"),
        "candidate_count": len(candidates),
        "state_delta_count": len(deltas),
        "pending_candidate_count": pending_candidates,
        "verified_evidence_count": verified_evidence,
        "strict": strict,
        "semantic_coverage_checked": report.get("reconciliation_version") == "1.1.0",
        "state_inventory_checked": bool(report.get("semantic_review", {}).get("state_snapshot")),
    }
    return errors, warnings, summary



def formatting_bytes(content: bytes) -> bytes:
    """Only BOM, CRLF/LF and one final newline. No paragraph/punctuation normalization."""
    text = content.decode("utf-8-sig")
    return text.replace("\r\n", "\n").removesuffix("\n").encode("utf-8")


def verify_formatting_receipt(root: Path, manifest: dict, chapter: dict, final: dict, receipt: dict) -> None:
    from project_ops import rollover_digest, receipt_identity, safe_path
    binding = receipt["rollover_receipt"]
    proof = binding["formatting_proof"]
    previous = next(f for f in chapter["finalizations"] if f["finalization_id"] == proof["previous_finalization_id"])
    historic = next(r for r in chapter["receipts"] if r["reconciliation_id"] == proof["previous_reconciliation_id"])
    previous_receipt_path = safe_path(root, historic["receipt_path"])
    if file_sha(previous_receipt_path) != historic["receipt_sha256"]:
        raise ValueError("rollover.formatting_proof_invalid")
    previous_receipt = load_json(previous_receipt_path)
    old_binding = previous_receipt["rollover_receipt"]
    old_copy, new_copy = safe_path(root, previous["approved_copy_path"]), safe_path(root, final["approved_copy_path"])
    old_bytes, new_bytes = old_copy.read_bytes(), new_copy.read_bytes()
    if (file_sha(old_copy) != previous["final_prose_sha256"] or file_sha(new_copy) != final["final_prose_sha256"] or
        formatting_bytes(old_bytes) != formatting_bytes(new_bytes) or
        proof["normalized_sha256"] != hashlib.sha256(formatting_bytes(new_bytes)).hexdigest() or
        proof["classification"] != ("SAME_BYTES" if old_bytes == new_bytes else "FORMAT_ONLY") or
        previous_receipt["reconciliation_id"] != receipt_identity(previous_receipt) or
        previous_receipt["prose_sha256"] != previous["final_prose_sha256"] or
        old_binding["finalization_id"] != previous["finalization_id"] or
        old_binding["snapshot"] != binding["snapshot"] or
        old_binding["verification"] != "VERIFIED" or
        previous_receipt["status"] != "APPROVED" or
        previous_receipt["chapter_id"] != chapter["chapter_id"] or
        previous_receipt["branch"] != final["branch"] or
        old_binding["project_id"] != manifest["project_id"]):
        raise ValueError("rollover.formatting_proof_invalid")
    # Immutable recorded parent provenance is checked; live old-prose paths are historical.
    if old_binding["effect"] == "FORMAT_ONLY_NO_STATE_DELTA":
        verify_formatting_receipt(root, manifest, chapter, previous, previous_receipt)


def freeze_rollover(root: Path, report_path: Path | None, *, chapter_id: str | None = None,
                    formatting_only: bool = False) -> dict:
    """Verify full reviewed state against the explicitly registered final; publish a freeze last."""
    import copy
    from project_ops import (rollover_project, resolve_final, rollover_state, rollover_digest,
                             rollover_json_bytes, atomic_publish, validate_freeze, receipt_identity)
    root = root.resolve()
    manifest, mp = rollover_project(root)
    old_mp_hash = file_sha(mp)
    if "chapter_rollover" not in manifest:
        raise ValueError("rollover.not_activated")
    branch = manifest.get("current_branch", "main")
    source_report_hash = None
    if not formatting_only:
        if report_path is None:
            raise ValueError("rollover.reconciliation_missing")
        report_path = safe_path(root, str(report_path))
        source_report_hash = file_sha(report_path)
        report = load_json(report_path)
        chapter_id = report["chapter_id"]
    elif not chapter_id:
        raise ValueError("rollover.chapter_mismatch")
    chapter, final = resolve_final(root, manifest, chapter_id, branch)
    current = rollover_state(root, manifest)
    state_payload = {"schema_version": "3.0.0", "project_id": manifest["project_id"], **current,
                     "source_finalization_id": final["finalization_id"]}
    state_id = "STATE-" + rollover_digest(state_payload)
    paths = manifest.get("canonical_paths", {})
    if paths.get("runtime_manifest"):
        from semantic_kernel import runtime_paths
        _, rp = runtime_paths(root, manifest)
        snap_dir = rp["snapshots"]
    else:
        snap_dir = safe_path(root, paths["story_state"]).parent / "rollover-snapshots"
    snapshot_path = snap_dir / (state_id + ".json")
    snapshot = {"path": snapshot_path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(rollover_json_bytes(state_payload)).hexdigest(), "state_snapshot_id": state_id}
    binding = {"project_id": manifest["project_id"], "finalization_id": final["finalization_id"],
               "input_final_prose_sha256": final["final_prose_sha256"], "snapshot": snapshot,
               "verification": "VERIFIED", "effect": "REVIEWED_STATE"}
    if formatting_only:
        old_pointer = chapter.get("current_rollover")
        if not old_pointer:
            raise ValueError("rollover.formatting_proof_missing")
        old_path = safe_path(root, old_pointer["receipt_path"])
        if file_sha(old_path) != old_pointer["receipt_sha256"]:
            raise ValueError("rollover.reconciliation_tampered")
        old_receipt = load_json(old_path)
        before_id = old_receipt["rollover_receipt"]["finalization_id"]
        previous = next(f for f in chapter["finalizations"] if f["finalization_id"] == before_id)
        old_bytes = safe_path(root, previous["approved_copy_path"]).read_bytes()
        new_bytes = safe_path(root, final["path"]).read_bytes()
        if hashlib.sha256(old_bytes).hexdigest() != previous["final_prose_sha256"] or formatting_bytes(old_bytes) != formatting_bytes(new_bytes):
            raise ValueError("rollover.substantive_revision_requires_review")
        snapshot = old_receipt["rollover_receipt"]["snapshot"]
        snapshot_path = safe_path(root, snapshot["path"])
        state_payload = load_json(snapshot_path)
        if any(state_payload[k] != current[k] for k in ("state", "branch", "through_event")):
            raise ValueError("rollover.state_snapshot_mismatch")
        binding.update(snapshot=snapshot, effect="FORMAT_ONLY_NO_STATE_DELTA",
                       formatting_proof={"previous_finalization_id": before_id,
                                         "previous_reconciliation_id": old_receipt["reconciliation_id"],
                                         "classification": "SAME_BYTES" if old_bytes == new_bytes else "FORMAT_ONLY",
                                         "normalized_sha256": hashlib.sha256(formatting_bytes(new_bytes)).hexdigest()})
        report = {"reconciliation_version": "1.1.0", "chapter_id": chapter_id, "branch": branch,
                  "prose_path": final["path"], "prose_sha256": final["final_prose_sha256"], "status": "APPROVED",
                  "prose_candidates": [], "state_deltas": [], "rollover_receipt": binding}
        # No fabricated semantic line review: inherited state is proven by archived byte equivalence.
        verify_formatting_receipt(root, manifest, chapter, final, report)
        if before_id == final["finalization_id"]:
            return validate_freeze(root, manifest, chapter, final)
    else:
        if report.get("reconciliation_version") != "1.1.0" or report["branch"] != branch or safe_path(root, report["prose_path"]) != safe_path(root, final["path"]) or report["prose_sha256"] != final["final_prose_sha256"]:
            raise ValueError("rollover.noncanonical_reconciliation_source")
        errors, _, _ = validate_report(report, root, strict=True)
        audit_snapshot = report.get("semantic_review", {}).get("state_snapshot")
        if errors or not audit_snapshot:
            raise ValueError("rollover.reconciliation_unverified")
        audit_path = safe_path(root, audit_snapshot["path"])
        if paths.get("runtime_manifest"):
            audit_path.relative_to(snap_dir)
            audited = load_json(audit_path)
            if any(audited.get(k) != current[k] for k in ("state", "branch", "through_event")):
                raise ValueError("rollover.state_snapshot_mismatch")
        elif audit_path != safe_path(root, paths["story_state"]):
            raise ValueError("rollover.noncanonical_state_audit")
        inventory = leaf_values(current["state"])
        for delta in report["state_deltas"]:
            target = delta.get("target")
            if target not in inventory or "after" not in delta or inventory[target] != delta["after"]:
                raise ValueError("rollover.durable_delta_not_committed")
        binding["report_source"] = {"path": report_path.relative_to(root).as_posix(), "sha256": source_report_hash}
        report = copy.deepcopy(report)
        report["rollover_receipt"] = binding
    report["reconciliation_id"] = receipt_identity(report)
    receipt_path = safe_path(root, paths.get("reconciliations_dir", "reconciliations")) / (report["reconciliation_id"] + ".json")
    pointer = {"reconciliation_id": report["reconciliation_id"], "receipt_path": receipt_path.relative_to(root).as_posix(),
               "receipt_sha256": hashlib.sha256(rollover_json_bytes(report)).hexdigest(),
               "state_snapshot_id": snapshot["state_snapshot_id"]}
    candidate = copy.deepcopy(manifest)
    candidate_chapter = next(c for c in candidate["chapter_rollover"]["chapters"] if c["chapter_id"] == chapter_id and c["branch"] == branch)
    if not any(r["reconciliation_id"] == pointer["reconciliation_id"] for r in candidate_chapter["receipts"]):
        candidate_chapter["receipts"].append(pointer)
    candidate_chapter["current_rollover"] = pointer
    def recheck():
        if file_sha(mp) != old_mp_hash:
            raise ValueError("rollover.source_changed_before_publish")
        _, live_final = resolve_final(root, manifest, chapter_id, branch)
        if live_final != final or rollover_state(root, manifest) != current:
            raise ValueError("rollover.source_changed_before_publish")
        if report_path is not None and source_report_hash is not None and file_sha(report_path) != source_report_hash:
            raise ValueError("rollover.source_changed_before_publish")
    atomic_publish(snapshot_path, rollover_json_bytes(state_payload), recheck, immutable=True)
    atomic_publish(receipt_path, rollover_json_bytes(report), recheck, immutable=True)
    validate_freeze(root, candidate, candidate_chapter, final)
    atomic_publish(mp, rollover_json_bytes(candidate), recheck)
    return {k: validate_freeze(root, candidate, candidate_chapter, final)[k] for k in
            ("previous_final_chapter_id", "previous_final_prose_sha256", "state_snapshot_id", "reconciliation_id")}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("report", type=Path, help="report to validate, or output report with --prepare")
    p.add_argument("--prepare", type=Path, metavar="PROSE", help="create a pending 1.1 semantic review packet; never infer or commit facts")
    p.add_argument("--state", type=Path, help="state JSON snapshot to audit (may be a scoped export)")
    p.add_argument("--chapter-id", default="UNKNOWN")
    p.add_argument("--branch", default="main")
    p.add_argument("--root", type=Path, help="project root; defaults to report parent")
    p.add_argument("--strict", action="store_true", help="final commit gate: require APPROVED and no pending candidates")
    p.add_argument("--freeze", action="store_true", help="publish a verified source-bound rollover receipt and freeze pointer")
    p.add_argument("--formatting-only", action="store_true", help="with --freeze: prove conservative byte formatting equivalence to the recorded predecessor receipt")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    try:
        require_profile("reconcile")
    except CapabilityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    root = (args.root or args.report.parent).resolve()
    try:
        if args.freeze:
            if args.prepare:
                raise ValueError("rollover.prepare_is_not_approval")
            result = freeze_rollover(root, None if args.formatting_only else args.report.resolve(),
                                     chapter_id=None if args.chapter_id == "UNKNOWN" else args.chapter_id,
                                     formatting_only=args.formatting_only)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.formatting_only:
            raise ValueError("rollover.formatting_requires_freeze")
        if args.prepare:
            if args.strict:
                raise ValueError("--prepare cannot approve a report; do not combine with --strict")
            output = safe_path(root, str(args.report.resolve()))
            if output.exists():
                raise ValueError("refusing to overwrite an existing reconciliation report")
            raw = prepare_report(root, args.prepare, args.chapter_id, args.branch, args.state)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"status": "DRAFT", "report": str(output)}, ensure_ascii=False))
            return 0
        raw = load_json(args.report)
        if not isinstance(raw, dict):
            raise ValueError("report must be a JSON object")
        errors, warnings, summary = validate_report(raw, root, strict=args.strict)
    except Exception as exc:
        print(f"ERROR: reconciliation validation failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings, "summary": summary}, ensure_ascii=False, indent=2))
    else:
        for x in errors:
            print(f"ERROR: {x}")
        for x in warnings:
            print(f"WARNING: {x}")
        if not errors:
            print(f"OK: prose-state reconciliation valid ({summary.get('verified_evidence_count', 0)} evidence spans verified)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
