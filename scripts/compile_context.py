#!/usr/bin/env python3
"""Deterministically compile a role-scoped fiction context pack under a token budget.

Input:
  - context index JSON with an `entries` array
  - request JSON describing target chapter/scene/role/budget and relevance tags

The compiler selects files; it does not create story content or mutate canon.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from scoped_poetics import verify_envelope
from validate_intake_state import check_project_decisions

KIND_WEIGHT = {
    "mission": 900,
    "scene-packet": 850,
    "poetics": 840,
    "knowledge": 800,
    "open-issue-boundary": 790,
    "character": 760,
    "object": 740,
    "location": 720,
    "world-state": 700,
    "thread": 680,
    "reader-state": 660,
    "research": 620,
    "poetics-capability": 560,
    "style": 520,
    "recent-prose": 480,
    "background": 200,
}

WRITER_FORBIDDEN_KINDS = {"open-issue-candidates", "authorial-possibility-space", "poetics-hypothesis", "project-poetics-author"}

def load_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def estimate_tokens(text: str) -> int:
    """Conservative mixed Chinese/Latin token estimate.

    It is intentionally approximate. A project may override this with an explicit
    `token_estimate` on an index entry.
    """
    cjk = 0
    latin = 0
    other = 0
    for ch in text:
        code = ord(ch)
        if (
            0x3400 <= code <= 0x4DBF
            or 0x4E00 <= code <= 0x9FFF
            or 0xF900 <= code <= 0xFAFF
        ):
            cjk += 1
        elif ch.isascii() and (ch.isalnum() or ch.isspace() or ch in "-_'\".,;:!?/()[]{}"):
            latin += 1
        else:
            other += 1
    return max(1, math.ceil(cjk / 1.2 + latin / 4.0 + other / 2.0))


def read_entry_text(root: Path, entry: dict[str, Any]) -> str:
    path_value = entry.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise ValueError(f"entry {entry.get('id','?')} lacks path")
    path = (root / path_value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"entry {entry.get('id','?')} escapes project root: {path_value}") from exc
    if not path.is_file():
        raise FileNotFoundError(f"entry {entry.get('id','?')} missing file: {path_value}")
    lines = path.read_text(encoding="utf-8").splitlines()
    start = entry.get("start_line")
    end = entry.get("end_line")
    if isinstance(start, int) or isinstance(end, int):
        s = max(1, int(start or 1)) - 1
        e = int(end) if isinstance(end, int) else len(lines)
        lines = lines[s:e]
    return "\n".join(lines).strip()


def as_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(x) for x in value if x is not None}


def forbidden_terms(req: dict[str, Any]) -> list[str]:
    raw = req.get("forbidden_terms", [])
    if not isinstance(raw, list):
        raise ValueError("request.forbidden_terms must be a list when provided")
    return [str(x).strip() for x in raw if str(x).strip()]


def leak_fingerprints(text: str, terms: list[str], *, case_sensitive: bool) -> list[str]:
    haystack = text if case_sensitive else text.casefold()
    hits: list[str] = []
    for term in terms:
        needle = term if case_sensitive else term.casefold()
        if needle and needle in haystack:
            hits.append(hashlib.sha256(term.encode("utf-8")).hexdigest()[:12])
    return hits


def apply_project_manifest_defaults(req: dict[str, Any], root: Path) -> dict[str, Any]:
    """Fill context-governance defaults from the project-level manifest when supplied."""
    out = dict(req)
    rel = out.get("project_manifest")
    if rel is None:
        return out
    if not isinstance(rel, str) or not rel:
        raise ValueError("request.project_manifest must be a project-relative path when provided")
    path = (root / rel).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("request.project_manifest escapes project root") from exc
    manifest = load_object(path)
    if not out.get("branch") and isinstance(manifest.get("current_branch"), str):
        out["branch"] = manifest.get("current_branch")
    paths = manifest.get("canonical_paths", {})
    if isinstance(paths, dict) and not out.get("secret_registry") and isinstance(paths.get("secret_registry"), str):
        out["secret_registry"] = paths.get("secret_registry")
    out["_project_context_generation"] = manifest.get("context_generation")
    out["_project_id"] = manifest.get("project_id")
    if isinstance(paths, dict) and isinstance(paths.get("project_poetics"), str):
        out["_project_poetics_path"] = paths.get("project_poetics")
    refs = manifest.get("poetics_override_refs", [])
    if isinstance(refs, list):
        out["_poetics_override_refs"] = [str(x) for x in refs]
    return out


def load_secret_policy(req: dict[str, Any], root: Path) -> tuple[set[str], list[str], dict[str, Any]]:
    """Resolve role-level blocked secret IDs and literal tripwires.

    Secret IDs are semantic provenance labels. Literal terms remain a final lexical
    guard. A backend registry may supply both without exposing secret text to the
    compiled pack or its diagnostics.
    """
    role = str(req.get("role", "writer"))
    blocked = as_set(req.get("blocked_secret_ids"))
    terms = forbidden_terms(req)
    registry_rel = req.get("secret_registry")
    registry_count = 0
    if registry_rel is not None:
        if not isinstance(registry_rel, str) or not registry_rel:
            raise ValueError("request.secret_registry must be a project-relative path when provided")
        registry_path = (root / registry_rel).resolve()
        try:
            registry_path.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError("request.secret_registry escapes project root") from exc
        data = load_object(registry_path)
        secrets = data.get("secrets", [])
        if not isinstance(secrets, list):
            raise ValueError("secret registry .secrets must be a list")
        for raw in secrets:
            if not isinstance(raw, dict):
                continue
            sid = raw.get("id")
            if not isinstance(sid, str) or not sid:
                continue
            status = str(raw.get("status", "active")).lower()
            if status in {"retired", "resolved", "public", "declassified"}:
                continue
            registry_count += 1
            allowed_roles = as_set(raw.get("allowed_roles")) | as_set(raw.get("declassified_for"))
            if role not in allowed_roles:
                blocked.add(sid)
                literal = raw.get("literal_terms", [])
                if isinstance(literal, list):
                    terms.extend(str(x).strip() for x in literal if str(x).strip())
    # stable de-duplication without logging literal values
    terms = list(dict.fromkeys(terms))
    meta = {
        "registry_supplied": isinstance(registry_rel, str) and bool(registry_rel),
        "registry_active_secret_count": registry_count,
        "blocked_secret_count": len(blocked),
    }
    return blocked, terms, meta


def released_secret_ids(entry: dict[str, Any], role: str, effective_taints: set[str]) -> set[str]:
    """Return the subset of semantic taints explicitly declassified to this role.

    `declassified_for: [role]` is retained as a coarse compatibility form and
    releases all taints on the entry. Prefer the structured form with explicit
    `secret_ids` so an artifact derived from several secrets can release only one.
    """
    direct = entry.get("declassified_for")
    if isinstance(direct, list) and role in {str(x) for x in direct}:
        return set(effective_taints)
    rec = entry.get("declassification")
    if not isinstance(rec, dict):
        return set()
    roles = rec.get("roles")
    if not (isinstance(roles, list) and role in {str(x) for x in roles}):
        return set()
    if str(rec.get("status", "pending")).lower() not in {"approved", "active", "declassified"}:
        return set()
    ids = rec.get("secret_ids")
    if isinstance(ids, list):
        return effective_taints & {str(x) for x in ids}
    if rec.get("all_taints") is True:
        return set(effective_taints)
    return set()


def taint_closure(entries: list[dict[str, Any]]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Propagate semantic secret taint through context-entry derivation edges."""
    by_id = {str(e.get("id")): e for e in entries if isinstance(e, dict) and e.get("id") is not None}
    cache: dict[str, set[str]] = {}
    missing: dict[str, set[str]] = {}

    def visit(entry_id: str, stack: set[str]) -> set[str]:
        if entry_id in cache:
            return set(cache[entry_id])
        if entry_id in stack:
            raise ValueError(f"context derivation cycle involving {entry_id}")
        entry = by_id.get(entry_id)
        if entry is None:
            return set()
        taints = as_set(entry.get("tainted_by"))
        next_stack = set(stack)
        next_stack.add(entry_id)
        parents = as_set(entry.get("derived_from"))
        for parent in parents:
            if parent not in by_id:
                missing.setdefault(entry_id, set()).add(parent)
                continue
            taints |= visit(parent, next_stack)
            if missing.get(parent):
                missing.setdefault(entry_id, set()).update(missing[parent])
        cache[entry_id] = set(taints)
        return taints

    for eid in by_id:
        visit(eid, set())
    return cache, missing


def opaque_fingerprints(values: set[str]) -> list[str]:
    return [hashlib.sha256(x.encode("utf-8")).hexdigest()[:12] for x in sorted(values)]


def source_identity(root: Path, entry: dict[str, Any]) -> tuple[str, int | None, int | None]:
    path_value = entry.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise ValueError(f"entry {entry.get('id','?')} lacks path")
    path = (root / path_value).resolve()
    try:
        relative = path.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"entry {entry.get('id','?')} escapes project root: {path_value}") from exc
    start = entry.get("start_line") if isinstance(entry.get("start_line"), int) else None
    end = entry.get("end_line") if isinstance(entry.get("end_line"), int) else None
    return relative, start, end


def allowed(entry: dict[str, Any], req: dict[str, Any]) -> tuple[bool, str | None]:
    role = str(req.get("role", "writer"))
    target = req.get("target_chapter")
    request_branch = str(req.get("branch", "main"))
    entry_branch = entry.get("branch")
    entry_branches = entry.get("branches")
    if isinstance(entry_branch, str) and entry_branch and entry_branch != request_branch:
        return False, "branch-mismatch"
    if isinstance(entry_branches, list) and entry_branches and request_branch not in {str(x) for x in entry_branches}:
        return False, "branch-mismatch"
    roles = entry.get("roles")
    if isinstance(roles, list) and roles and role not in {str(x) for x in roles}:
        return False, "role-not-allowed"
    kind = str(entry.get("kind", "background"))
    if role == "writer" and kind in WRITER_FORBIDDEN_KINDS:
        return False, "open-issue-backend-blocked"
    if role == "writer" and kind == "poetics-capability" and "active_capabilities" in req:
        if not (as_set(entry.get("poetics_capabilities")) & as_set(req.get("active_capabilities"))):
            return False, "inactive-poetics-capability"
    visibility = str(entry.get("visibility", "unmarked")).lower()
    strict_visibility = req.get("strict_visibility") is True
    if role == "reader-simulator" and visibility != "reader-visible":
        return False, "reader-visibility-not-explicit"
    if role in {"writer", "humanities-analyst"} and visibility in {"author-only", "backend-hidden", "future-answer"}:
        return False, "backend-visibility-blocked"
    if strict_visibility:
        if visibility == "unmarked":
            return False, "strict-visibility-unmarked"
        if role == "writer":
            allowed_visibility = {"reader-visible", "writer-visible", "role-internal"}
            if visibility not in allowed_visibility:
                return False, "strict-writer-visibility"
            if visibility == "role-internal" and not (isinstance(roles, list) and role in {str(x) for x in roles}):
                return False, "strict-role-internal-without-role"
        elif role == "humanities-analyst":
            allowed_visibility = {"reader-visible", "analyst-visible", "role-internal"}
            if visibility not in allowed_visibility:
                return False, "strict-analyst-visibility"
    status = str(entry.get("status", "active")).lower()
    if status in {"retired", "invalidated", "stale"}:
        return False, f"status-{status}"
    if isinstance(target, (int, float)):
        available_from = entry.get("available_from_chapter")
        available_to = entry.get("available_to_chapter")
        if isinstance(available_from, (int, float)) and available_from > target:
            return False, "future-availability"
        if isinstance(available_to, (int, float)) and target > available_to:
            return False, "expired-availability"
        if entry.get("future_sensitive") is True:
            chapter = entry.get("chapter")
            if isinstance(chapter, (int, float)) and chapter > target:
                return False, "future-sensitive"
    return True, None


def score(entry: dict[str, Any], req: dict[str, Any]) -> float:
    total = float(entry.get("priority", 0) or 0)
    total += KIND_WEIGHT.get(str(entry.get("kind", "background")), 100)
    if entry.get("required") is True:
        total += 100000
    # Explicit request requirements outrank index-level required aliases.
    # Otherwise an alphabetically earlier duplicate can consume the source identity
    # and silently evict the exact artifact the request named.
    if entry.get("_request_required") is True:
        total += 1000000

    pov = req.get("pov")
    if pov is not None and str(pov) in as_set(entry.get("characters")):
        total += 600

    for field, bonus in (
        ("characters", 180),
        ("locations", 180),
        ("threads", 220),
        ("research", 180),
        ("scenes", 260),
    ):
        overlap = as_set(req.get(field)) & as_set(entry.get(field))
        total += bonus * len(overlap)

    capability_overlap = as_set(req.get("active_capabilities")) & as_set(entry.get("poetics_capabilities"))
    total += 260 * len(capability_overlap)

    target_scene = req.get("target_scene")
    if target_scene is not None and str(target_scene) in as_set(entry.get("scenes")):
        total += 800

    target_chapter = req.get("target_chapter")
    chapter = entry.get("chapter")
    if isinstance(target_chapter, (int, float)) and isinstance(chapter, (int, float)) and chapter <= target_chapter:
        total += 200.0 / (1.0 + (target_chapter - chapter))

    return total


def representation(root: Path, entry: dict[str, Any], remaining: int) -> tuple[str, str, int] | None:
    full = read_entry_text(root, entry)
    explicit = entry.get("token_estimate")
    full_tokens = int(explicit) if isinstance(explicit, int) and explicit > 0 else estimate_tokens(full)
    if full_tokens <= remaining:
        return "full", full, full_tokens

    summary = entry.get("summary")
    if isinstance(summary, str) and summary.strip():
        summary_text = summary.strip()
        summary_tokens = estimate_tokens(summary_text)
        if summary_tokens <= remaining:
            return "summary", summary_text, summary_tokens
    return None


def poetics_manifest_metadata(
    req: dict[str, Any],
    scoped_poetics_envelope: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return the shared Project-Poetics provenance block for context manifests."""
    return {
        "project_poetics_ref": req.get("_project_poetics_path"),
        "scoped_project_poetics_ref": req.get("scoped_project_poetics_ref"),
        "scoped_project_poetics_envelope_ref": req.get("scoped_project_poetics_envelope_ref"),
        "scoped_project_poetics_provenance": scoped_poetics_envelope,
        "poetics_override_refs": req.get("_poetics_override_refs", []),
        "active_capabilities": sorted(as_set(req.get("active_capabilities"))),
    }


def compile_pack(index: dict[str, Any], req: dict[str, Any], root: Path) -> tuple[str, dict[str, Any], list[str]]:
    from project_ops import rollover_project, rollover_view, rollover_artifact_errors
    canonical_project, _ = rollover_project(root, req)
    if "chapter_rollover" in canonical_project and not req.get("project_manifest"):
        req = dict(req, project_manifest="project-manifest.json")
    req = apply_project_manifest_defaults(req, root)
    rollover = rollover_view(root, req) if str(req.get("role", "writer")) == "writer" else {"status": "UNVERIFIED"}
    if rollover["status"] == "STALE":
        return "", {"previous_chapter_rollover": rollover}, rollover["codes"]
    # Canonical predecessor index binding has no object on a legitimate first chapter.
    # STALE is rejected above; live NOT_APPLICABLE still runs every ordinary compiler rule.
    if ("chapter_rollover" in canonical_project and str(req.get("role", "writer")) == "writer"
            and rollover["status"] == "FRESH"):
        canonical_index = canonical_project.get("canonical_paths", {}).get("context_index")
        if canonical_index and load_object(root / canonical_index) != index:
            return "", {"previous_chapter_rollover": rollover}, ["rollover.noncanonical_context_index"]
    entries = index.get("entries") or []
    if not isinstance(entries, list):
        raise ValueError("index.entries must be a list")
    budget = req.get("budget_tokens", 6000)
    if not isinstance(budget, int) or budget <= 0:
        raise ValueError("request.budget_tokens must be a positive integer")

    required_ids = as_set(req.get("required_ids"))
    required_scene_ids = as_set(req.get("required_scene_ids"))
    blocked_secret_ids, secret_terms, secret_policy_meta = load_secret_policy(req, root)
    case_sensitive = req.get("forbidden_case_sensitive") is True
    deduplicate_content = req.get("deduplicate_content", True) is not False
    raw_entries = [dict(x) for x in entries if isinstance(x, dict)]
    ids = [e.get("id") for e in raw_entries]
    if any(not isinstance(x, str) or not x.strip() for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("context entries require unique non-empty canonical IDs")
    if len(raw_entries) != len(entries):
        raise ValueError("context entries must be objects")
    for entry in raw_entries:
        source_identity(root, entry)  # validate even hidden provenance sources

    # A writer-safe scoped Project-Poetics derivative can be injected directly by the
    # request so substantial prose work does not depend on a manually maintained
    # context-index entry. The derivative MUST be paired with a thin provenance
    # envelope. The compiler validates authority/scope/parent hashes/status/expiry but
    # never parses or schemas the literary commitments inside the Markdown.
    scoped_poetics_ref = req.get("scoped_project_poetics_ref")
    scoped_poetics_envelope_ref = req.get("scoped_project_poetics_envelope_ref")
    if (scoped_poetics_ref is None) != (scoped_poetics_envelope_ref is None):
        raise ValueError(
            "request.scoped_project_poetics_ref and request.scoped_project_poetics_envelope_ref must be provided together"
        )
    scoped_poetics_envelope: dict[str, Any] | None = None
    if scoped_poetics_ref is not None:
        if not isinstance(scoped_poetics_ref, str) or not scoped_poetics_ref.strip():
            raise ValueError("request.scoped_project_poetics_ref must be a non-empty project-relative path when provided")
        if not isinstance(scoped_poetics_envelope_ref, str) or not scoped_poetics_envelope_ref.strip():
            raise ValueError("request.scoped_project_poetics_envelope_ref must be a non-empty project-relative path when provided")
        if not isinstance(req.get("project_manifest"), str) or not str(req.get("project_manifest")).strip():
            raise ValueError("request.project_manifest is required when scoped Project Poetics provenance is supplied")
        scoped_poetics_envelope, envelope_errors = verify_envelope(
            root=root,
            content_ref=scoped_poetics_ref,
            envelope_ref=scoped_poetics_envelope_ref,
            project_manifest_ref=req.get("project_manifest") if isinstance(req.get("project_manifest"), str) else None,
            scope_context={
                "project_id": req.get("_project_id"),
                "arc": req.get("target_arc"),
                "chapter": req.get("target_chapter"),
                "scene": req.get("target_scene"),
                "task": req.get("task_id"),
            },
        )
        if envelope_errors:
            raise ValueError("invalid scoped Project Poetics provenance envelope: " + "; ".join(envelope_errors))
        if str(req.get("role", "writer")) == "writer":
            # Preserve provenance of an indexed derivative instead of injecting an
            # untainted alias of the same path. A reserved ID cannot shadow a source.
            if "__scoped_project_poetics__" in ids:
                raise ValueError("reserved scoped Project Poetics entry ID")
            scoped_sources = [e for e in raw_entries if e.get("path") == scoped_poetics_ref]
            raw_entries.append({
                "id": "__scoped_project_poetics__",
                "kind": "poetics",
                "path": scoped_poetics_ref,
                "required": True,
                "roles": ["writer"],
                "visibility": "role-internal",
                "priority": 1000,
                "poetics_capabilities": list(as_set(req.get("active_capabilities"))),
                "derived_from": [e["id"] for e in scoped_sources],
            })

    taints_by_id, missing_taint_parents = taint_closure(raw_entries)
    # An undeclared label cannot silently become harmless because the registry is
    # empty. Explicit blocked_secret_ids remains a supported diagnostic contract.
    known_secrets = set(blocked_secret_ids)
    if req.get("secret_registry"):
        known_secrets |= {str(s.get("id")) for s in load_object(root / req["secret_registry"]).get("secrets", []) if isinstance(s, dict)}
    unknown_secrets = set().union(*taints_by_id.values()) - known_secrets if taints_by_id else set()
    if unknown_secrets:
        raise ValueError("unregistered semantic secret labels: " + ", ".join(opaque_fingerprints(unknown_secrets)))
    semantic_taint_exclusions = 0
    candidates: list[tuple[float, dict[str, Any]]] = []
    excluded: list[dict[str, Any]] = []
    errors: list[str] = []
    index_ids: set[str] = set()

    for raw in raw_entries:
        if not isinstance(raw, dict):
            excluded.append({"id": "?", "reason": "non-object-entry"})
            continue
        entry = dict(raw)
        entry_id = str(entry.get("id", "?"))
        index_ids.add(entry_id)
        request_required = entry_id in required_ids
        entry["_request_required"] = request_required
        if request_required:
            entry["required"] = True
        ok, reason = allowed(entry, req)
        if not ok:
            # Index-level `required` means hard-required while the entry is eligible
            # for this role/chapter. Only an explicitly request-required entry turns
            # an eligibility failure into a compilation error.
            if request_required:
                errors.append(f"request-required entry {entry_id} excluded: {reason}")
            excluded.append({"id": entry_id, "reason": reason})
            continue

        missing_parents = missing_taint_parents.get(entry_id, set())
        if missing_parents:
            fingerprints = opaque_fingerprints(missing_parents)
            hard = request_required or entry.get("required") is True
            if hard:
                errors.append(
                    f"taint provenance incomplete for required entry {entry_id}: "
                    + ", ".join(f"parent_sha256={x}" for x in fingerprints)
                )
            excluded.append({"id": entry_id, "reason": "taint-provenance-missing-parent", "parent_fingerprints": fingerprints})
            continue

        effective_taints = taints_by_id.get(entry_id, set())
        entry["_effective_taints"] = sorted(effective_taints)
        blocked_hits = effective_taints & blocked_secret_ids
        blocked_hits -= released_secret_ids(entry, str(req.get("role", "writer")), effective_taints)
        if blocked_hits:
            semantic_taint_exclusions += 1
            fingerprints = opaque_fingerprints(blocked_hits)
            hard = request_required or entry.get("required") is True
            if hard:
                errors.append(
                    f"semantic secret taint blocks required entry {entry_id}: "
                    + ", ".join(f"secret_sha256={x}" for x in fingerprints)
                )
            excluded.append({"id": entry_id, "reason": "semantic-secret-taint", "secret_fingerprints": fingerprints})
            continue
        candidates.append((score(entry, req), entry))

    for missing in sorted(required_ids - index_ids):
        errors.append(f"request-required entry {missing} is missing from context index")

    candidates.sort(key=lambda pair: (-pair[0], str(pair[1].get("id", ""))))

    required = [pair for pair in candidates if pair[1].get("required") is True]
    optional = [pair for pair in candidates if pair[1].get("required") is not True]

    included: list[dict[str, Any]] = []
    remaining = budget
    seen_sources: dict[tuple[str, int | None, int | None], str] = {}
    seen_content: dict[str, str] = {}

    def add_entry(entry: dict[str, Any], *, hard_required: bool) -> None:
        nonlocal remaining
        entry_id = str(entry.get("id", "?"))
        src_id = source_identity(root, entry)
        kept = seen_sources.get(src_id)
        if kept is not None:
            excluded.append({"id": entry_id, "reason": f"duplicate-source:{kept}"})
            return

        full_source = read_entry_text(root, entry)
        full_hash = hashlib.sha256(full_source.encode("utf-8")).hexdigest()
        if deduplicate_content and full_hash in seen_content:
            excluded.append({"id": entry_id, "reason": f"duplicate-content:{seen_content[full_hash]}"})
            return

        rep = representation(root, entry, remaining)
        if rep is None:
            if hard_required:
                errors.append(f"required entry {entry_id} cannot fit remaining budget {remaining}")
            else:
                excluded.append({"id": entry_id, "reason": "budget"})
            return
        mode, text, tokens = rep

        hits = leak_fingerprints(text, secret_terms, case_sensitive=case_sensitive)
        if hits:
            # Never echo the literal secret in logs/manifests. The backend caller
            # already owns the forbidden-term registry; lower-clearance artifacts do not.
            errors.append(
                f"forbidden-term leakage in entry {entry_id}: "
                + ", ".join(f"term_sha256={x}" for x in hits)
            )
            excluded.append({"id": entry_id, "reason": "forbidden-term-leakage", "term_fingerprints": hits})
            return

        source_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        included.append({"entry": entry, "mode": mode, "text": text, "tokens": tokens, "source_sha256": source_sha})
        seen_sources[src_id] = entry_id
        if deduplicate_content:
            seen_content[full_hash] = entry_id
        remaining -= tokens

    for _, entry in required:
        add_entry(entry, hard_required=True)

    # Scene IDs in `scenes` are relevance hints. `required_scene_ids` is the
    # hard handoff contract for causally material Scene Packets. A required
    # scene must be represented by an included Writer-eligible entry tagged
    # with that scene, otherwise the request could claim scene coverage while
    # silently omitting the actual packet/derivative.
    if required_scene_ids:
        covered_scenes: set[str] = set()
        for item in included:
            covered_scenes |= as_set(item["entry"].get("scenes"))
        for scene_id in sorted(required_scene_ids - covered_scenes):
            errors.append(f"required scene {scene_id} has no included context entry tagged with that scene")

    included_required_ids = {str(x["entry"].get("id")) for x in included}
    silently_missing_required = sorted(required_ids - included_required_ids)
    for missing in silently_missing_required:
        if not any(missing in msg for msg in errors):
            errors.append(f"request-required entry {missing} was not included after dedup/budget resolution")

    if errors:
        return "", {
            "budget_tokens": budget,
            "estimated_tokens": budget - remaining,
            "remaining_tokens": remaining,
            "project_id": req.get("_project_id"),
            "project_context_generation": req.get("_project_context_generation"),
            **poetics_manifest_metadata(req, scoped_poetics_envelope),
            "included": [x["entry"].get("id") for x in included],
            "excluded": excluded,
            "leakage_guard": {
                "enabled": bool(secret_terms),
                "forbidden_term_count": len(secret_terms),
                "case_sensitive": case_sensitive,
            },
            "semantic_taint_guard": {
                **secret_policy_meta,
                "enabled": bool(blocked_secret_ids),
                "excluded_entry_count": semantic_taint_exclusions,
            },
        }, errors

    for _, entry in optional:
        add_entry(entry, hard_required=False)

    if rollover["status"] == "FRESH":
        errors.extend(rollover_artifact_errors(root, raw_entries, [x["entry"] for x in included], rollover))

    # Only selected, role-safe material reaches this seam. Reuse Kernel laws;
    # do not parse arbitrary prose or accept request-supplied acquisitions.
    if str(req.get("role", "writer")) == "writer":
        from semantic_kernel import temporal_epistemic_issues, risk_scoped
        fact_uses = []
        coverage_shape_error = False
        for item in included:
            entry = item["entry"]
            raw_uses = entry.get("fact_uses", [])
            if not isinstance(raw_uses, list) or any(not isinstance(x, dict) for x in raw_uses):
                coverage_shape_error = True
                continue
            if risk_scoped(entry) and not raw_uses:
                coverage_shape_error = True
            for raw in raw_uses:
                use = dict(raw)
                use.setdefault("actor", req.get("pov_actor", req.get("actor")))
                use.setdefault("used_at", req.get("story_time"))
                use["writer_visible"] = True
                use["visibility"] = "writer-visible"
                if risk_scoped(entry):
                    use["consequential"] = True
                fact_uses.append(use)
        state = {}
        manifest_ref = req.get("project_manifest")
        if manifest_ref is None and (root / "project-manifest.json").is_file():
            manifest_ref = "project-manifest.json"
        if manifest_ref is not None:
            mp = (root / manifest_ref).resolve()
            mp.relative_to(root.resolve())
            canonical = load_object(mp).get("canonical_paths", {})
            state_ref = canonical.get("story_state") if isinstance(canonical, dict) else None
            if isinstance(state_ref, str):
                sp = (root / state_ref).resolve()
                sp.relative_to(root.resolve())
                state = load_object(sp)
        actor = req.get("pov_actor", req.get("actor"))
        # Catalog Writer declarations are themselves uses; deleting knowledge_uses
        # or an entry's fact_uses cannot erase their coverage obligation.
        declared_rows = state.get("writer_visible_facts", [])
        fact_rows = state.get("facts", [])
        if not isinstance(declared_rows, list) or not isinstance(fact_rows, list):
            coverage_shape_error = True
        declared = list(declared_rows) if isinstance(declared_rows, list) else []
        if isinstance(fact_rows, list):
            declared += [dict(x, fact_id=x.get("fact_id", x.get("id"))) for x in fact_rows
                         if isinstance(x, dict) and x.get("writer_visible") is True and x.get("actor")]
        for raw in declared:
            if not isinstance(raw, dict):
                coverage_shape_error = True
                continue
            if actor is not None and raw.get("actor") not in (None, actor):
                continue
            use = dict(raw)
            use.setdefault("actor", actor)
            use.setdefault("used_at", req.get("story_time", state.get("story_time")))
            fact_uses.append(use)
        if coverage_shape_error:
            errors.append("K21: consequential Writer material requires structured fact-use coverage")
        if fact_uses or state:
            scoped_state = dict(state)
            if req.get("story_window") is not None:
                scoped_state["story_window"] = req["story_window"]
            findings = temporal_epistemic_issues(scoped_state, fact_uses)
            # No raw secret values/IDs or backend acquisition details in Writer logs.
            failed_laws = sorted({x["law"] for x in findings if x["severity"] == "error"})
            if failed_laws:
                errors.append("temporal-epistemic legality: " + ", ".join(failed_laws) + "; review canonical support before Writer compilation")

    decision_guard = None
    decision_manifest_ref = req.get("project_manifest")
    if decision_manifest_ref is None and (root / "project-manifest.json").is_file():
        # An opted-in canonical register cannot be bypassed by omitting the
        # request pointer. Legacy manifests without intake_state are unchanged.
        decision_manifest_ref = "project-manifest.json"
    if decision_manifest_ref is not None:
        manifest_path = (root / decision_manifest_ref).resolve()
        manifest_path.relative_to(root.resolve())
        consumers = {str(item["entry"]["id"]) for item in included}
        if req.get("task_id"):
            consumers.add(str(req["task_id"]))
        decision_guard = check_project_decisions(root, load_object(manifest_path), consumers)
        if decision_guard and decision_guard["errors"]:
            # Keep decision values/backend provenance out of Writer diagnostics.
            errors.append("commit-before-dependency: selected context has an invalid decision dependency; resolve/commit and regenerate upstream")

    if errors:
        return "", {
            "budget_tokens": budget,
            "estimated_tokens": budget - remaining,
            "remaining_tokens": remaining,
            "project_id": req.get("_project_id"),
            "project_context_generation": req.get("_project_context_generation"),
            **poetics_manifest_metadata(req, scoped_poetics_envelope),
            "included": [x["entry"].get("id") for x in included],
            "excluded": excluded,
            "leakage_guard": {
                "enabled": bool(secret_terms),
                "forbidden_term_count": len(secret_terms),
                "case_sensitive": case_sensitive,
            },
            "semantic_taint_guard": {
                **secret_policy_meta,
                "enabled": bool(blocked_secret_ids),
                "excluded_entry_count": semantic_taint_exclusions,
            },
        }, errors

    header = [
        "# Compiled Context Pack",
        "",
        f"- role: {req.get('role','writer')}",
        f"- branch: {req.get('branch','main')}",
        f"- target_chapter: {req.get('target_chapter','?')}",
        f"- target_scene: {req.get('target_scene','')}",
        f"- project_poetics_ref: {req.get('_project_poetics_path','')}",
        f"- scoped_project_poetics_ref: {req.get('scoped_project_poetics_ref','')}",
        f"- scoped_project_poetics_envelope_ref: {req.get('scoped_project_poetics_envelope_ref','')}",
        f"- active_capabilities: {', '.join(sorted(as_set(req.get('active_capabilities'))))}",
        f"- budget_tokens: {budget}",
        f"- estimated_tokens: {budget - remaining}",
        "",
        "> This file is a temporary working pack, not canon. Do not write state back into it.",
        "",
    ]
    body: list[str] = []
    for item in included:
        entry = item["entry"]
        body.extend([
            f"## {entry.get('id','?')} [{entry.get('kind','background')}; {item['mode']}]",
            "",
            f"Source: `{entry.get('path','?')}`",
            "",
            item["text"],
            "",
        ])
    pack = "\n".join(header + body).rstrip() + "\n"

    manifest = {
        "manifest_version": "1.1.0",
        **({"previous_chapter_rollover": rollover, "previous_chapter": rollover.get("tuple")}
           if "chapter_rollover" in canonical_project else {}),
        "context_index_sha256": hashlib.sha256(json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "provenance_sources_sha256": hashlib.sha256(json.dumps({str(e["id"]): hashlib.sha256((root / e["path"]).read_bytes()).hexdigest() if (root / e["path"]).is_file() else None for e in raw_entries}, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "secret_registry_sha256": hashlib.sha256((root / req["secret_registry"]).read_bytes()).hexdigest() if req.get("secret_registry") else None,
        "role": req.get("role", "writer"),
        "branch": req.get("branch", "main"),
        "target_chapter": req.get("target_chapter"),
        "target_scene": req.get("target_scene"),
        "budget_tokens": budget,
        "estimated_tokens": budget - remaining,
        "remaining_tokens": remaining,
        "included": [
            {
                "id": x["entry"].get("id"),
                "path": x["entry"].get("path"),
                "kind": x["entry"].get("kind"),
                "mode": x["mode"],
                "estimated_tokens": x["tokens"],
            }
            for x in included
        ],
        "excluded": excluded,
        "strict_visibility": req.get("strict_visibility") is True,
        "execution_profile": req.get("execution_profile"),
        "project_id": req.get("_project_id"),
        "project_context_generation": req.get("_project_context_generation"),
        **poetics_manifest_metadata(req, scoped_poetics_envelope),
        "deduplicate_content": deduplicate_content,
        "leakage_guard": {
            "enabled": bool(secret_terms),
            "forbidden_term_count": len(secret_terms),
            "case_sensitive": case_sensitive,
        },
        "semantic_taint_guard": {
            **secret_policy_meta,
            "enabled": bool(blocked_secret_ids),
            "excluded_entry_count": semantic_taint_exclusions,
        },
        "request_sha256": hashlib.sha256(json.dumps(req, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "pack_sha256": hashlib.sha256(pack.encode("utf-8")).hexdigest(),
    }
    if decision_guard is not None:
        manifest["decision_dependency_guard"] = {
            "intake_state_sha256": decision_guard["intake_state_sha256"],
            "dependencies_sha256": decision_guard["dependencies_sha256"],
        }
    for row, item in zip(manifest["included"], included):
        row["visibility"] = item["entry"].get("visibility", "unmarked")
        row["source_sha256"] = item["source_sha256"]
        row["source_file_sha256"] = hashlib.sha256((root / item["entry"]["path"]).read_bytes()).hexdigest()
    if rollover["status"] == "FRESH":
        live = rollover_view(root, req)
        if live["status"] != "FRESH" or live.get("tuple") != rollover["tuple"]:
            return "", {"previous_chapter_rollover": live}, ["rollover.source_changed_before_publish"]
    return pack, manifest, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile a role-scoped fiction context pack")
    parser.add_argument("index", type=Path, help="context-index.json")
    parser.add_argument("request", type=Path, help="context request JSON")
    parser.add_argument("--root", type=Path, help="project root; defaults to index parent")
    parser.add_argument("--output", type=Path, required=True, help="output Markdown context pack")
    parser.add_argument("--manifest-out", type=Path, help="optional JSON manifest")
    args = parser.parse_args()

    from project_ops import rollover_project, rollover_view, atomic_publish
    try:
        index = load_object(args.index)
        req = load_object(args.request)
        root = (args.root or args.index.parent).resolve()
        pack, manifest, errors = compile_pack(index, req, root)
    except Exception as exc:
        print(f"ERROR: context compilation failed: {exc}", file=sys.stderr)
        return 2

    if errors:
        for msg in errors:
            print(f"ERROR: {msg}", file=sys.stderr)
        if args.manifest_out and "chapter_rollover" not in rollover_project(root)[0]:
            args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
            args.manifest_out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 1

    def recheck():
        if manifest.get("previous_chapter_rollover", {}).get("status") in {"FRESH", "NOT_APPLICABLE"}:
            live = rollover_view(root, req)
            if live["status"] != manifest["previous_chapter_rollover"]["status"] or live.get("tuple") != manifest.get("previous_chapter"):
                raise ValueError("rollover.source_changed_before_publish")
            # Recompile exactly once at publication: validates index, representation and state.
            if load_object(args.index) != index or load_object(args.request) != req:
                raise ValueError("rollover.source_changed_before_publish")
            fresh_pack, fresh_manifest, fresh_errors = compile_pack(index, req, root)
            if fresh_errors or fresh_pack != pack or fresh_manifest != manifest:
                raise ValueError("rollover.source_changed_before_publish")
    previous = {path: path.read_bytes() if path.exists() else None for path in [args.output, *([args.manifest_out] if args.manifest_out else [])]}
    try:
        recheck()
        atomic_publish(args.output, pack.encode("utf-8"), recheck)
        if args.manifest_out:
            atomic_publish(args.manifest_out, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"), recheck)
    except (OSError, ValueError):
        for path, content in previous.items():
            if content is None:
                path.unlink(missing_ok=True)
            elif not path.exists() or path.read_bytes() != content:
                atomic_publish(path, content)
        print("ERROR: rollover.source_changed_before_publish", file=sys.stderr)
        return 2

    print(
        f"compiled {len(manifest['included'])} entries, "
        f"estimated {manifest['estimated_tokens']}/{manifest['budget_tokens']} tokens, "
        f"excluded {len(manifest['excluded'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
