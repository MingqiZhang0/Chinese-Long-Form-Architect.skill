#!/usr/bin/env python3
"""Run deterministic metamorphic/adversarial narrative relations.

The benchmark transforms valid source cases into valid or intentionally boundary-shifted
follow-up cases, then asks canonical subsystem owners whether the registered relation
holds. It does not replace Context Compiler, Runtime, Kernel, or reconciliation logic.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compile_context import compile_pack  # type: ignore  # noqa: E402
from narrative_runtime import (  # type: ignore  # noqa: E402
    branch_map,
    events_by_branch,
    flatten_state,
    impact,
    load_jsonl,
    replay,
    validate_runtime,
    why_trace,
)
from prose_state_reconcile import file_sha, sha, validate_report  # type: ignore  # noqa: E402
from semantic_kernel import verify_project  # type: ignore  # noqa: E402
from scoped_poetics import build_envelope  # type: ignore  # noqa: E402

REGISTRY = ROOT / "assets" / "metamorphic" / "metamorphic-relations.json"
ALLOWED_TYPES = {"INV", "MONO", "DIR", "ISO", "CON", "ROUNDTRIP"}
ALLOWED_STRATA = {f"S{i}" for i in range(8)}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def bytes_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any, *, indent: int | None = 2, sort_keys: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=indent, sort_keys=sort_keys) + "\n", encoding="utf-8")


def context_semantics(manifest: dict[str, Any]) -> dict[str, Any]:
    included = []
    for row in manifest.get("included", []) or []:
        if isinstance(row, dict):
            included.append({
                "id": row.get("id"),
                "path": row.get("path"),
                "kind": row.get("kind"),
                "mode": row.get("mode"),
                "visibility": row.get("visibility"),
                "source_sha256": row.get("source_sha256"),
            })
        else:
            included.append(row)
    excluded = []
    for row in manifest.get("excluded", []) or []:
        if isinstance(row, dict):
            excluded.append({
                "id": row.get("id"),
                "reason": row.get("reason"),
                "secret_fingerprints": sorted(row.get("secret_fingerprints", []) or []),
                "term_fingerprints": sorted(row.get("term_fingerprints", []) or []),
            })
    return {
        "included": included,
        "excluded": sorted(excluded, key=lambda x: (str(x.get("id")), str(x.get("reason")))),
        "semantic_taint_guard": manifest.get("semantic_taint_guard"),
        "leakage_guard": manifest.get("leakage_guard"),
    }


def compile_obs(root: Path, entries: list[dict[str, Any]], req: dict[str, Any]) -> dict[str, Any]:
    pack, manifest, errors = compile_pack({"entries": entries}, req, root)
    return {
        "pack": pack,
        "manifest": manifest,
        "semantics": context_semantics(manifest),
        "errors": list(errors),
    }


def canonical_impact(rows: list[dict[str, Any]], node: str) -> list[tuple[str, str, str]]:
    return sorted((str(x.get("source")), str(x.get("target")), str(x.get("kind"))) for x in impact(rows, node))


def canonical_why(rows: list[dict[str, Any]], node: str) -> list[tuple[str, str, str]]:
    return sorted((str(x.get("source")), str(x.get("target")), str(x.get("kind"))) for x in why_trace(rows, node))


def result(status: str, message: str, source: Any, followup: Any, **details: Any) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "source_observation_sha256": stable_hash(source),
        "followup_observation_sha256": stable_hash(followup),
        "details": details,
    }


def mr_context_index_permutation(work: Path) -> dict[str, Any]:
    write(work / "a.md", "alpha")
    write(work / "b.md", "beta")
    write(work / "c.md", "gamma")
    entries = [
        {"id": "a", "path": "a.md", "kind": "mission", "priority": 10, "required": True, "roles": ["writer"], "visibility": "writer-visible"},
        {"id": "b", "path": "b.md", "kind": "character", "priority": 5, "roles": ["writer"], "visibility": "writer-visible"},
        {"id": "c", "path": "c.md", "kind": "background", "priority": 1, "roles": ["writer"], "visibility": "writer-visible"},
    ]
    req = {"role": "writer", "branch": "main", "budget_tokens": 2000, "required_ids": ["a"]}
    src = compile_obs(work, entries, req)
    fol = compile_obs(work, list(reversed(entries)), req)
    if src["errors"] or fol["errors"]:
        return result("INVALID", "source/follow-up compile failed", src, fol, source_errors=src["errors"], followup_errors=fol["errors"])
    ok = src["semantics"] == fol["semantics"] and src["pack"] == fol["pack"]
    return result("PASS" if ok else "FAIL", "Context Index order is semantically irrelevant." if ok else "Context Index order changed compiled semantics.", src["semantics"], fol["semantics"])


def mr_request_set_permutation(work: Path) -> dict[str, Any]:
    write(work / "a.md", "A")
    write(work / "b.md", "B")
    entries = [
        {"id": "a", "path": "a.md", "kind": "character", "priority": 2, "characters": ["C1"], "threads": ["T1"], "roles": ["writer"], "visibility": "writer-visible"},
        {"id": "b", "path": "b.md", "kind": "thread", "priority": 2, "characters": ["C2"], "threads": ["T2"], "roles": ["writer"], "visibility": "writer-visible"},
    ]
    src_req = {"role": "writer", "budget_tokens": 1000, "required_ids": ["a", "b"], "characters": ["C1", "C2"], "threads": ["T1", "T2"], "locations": ["L1", "L2"]}
    fol_req = {**src_req, "required_ids": ["b", "a"], "characters": ["C2", "C1"], "threads": ["T2", "T1"], "locations": ["L2", "L1"]}
    src = compile_obs(work, entries, src_req)
    fol = compile_obs(work, entries, fol_req)
    if stable_hash(src_req) == stable_hash(fol_req):
        return result("INVALID", "request transformation was a no-op", src_req, fol_req)
    ok = not src["errors"] and not fol["errors"] and src["semantics"] == fol["semantics"] and src["pack"] == fol["pack"]
    return result("PASS" if ok else "FAIL", "Set-valued request order does not change selection." if ok else "Request set order changed selection.", src["semantics"], fol["semantics"], source_errors=src["errors"], followup_errors=fol["errors"])


def mr_secret_paraphrase(work: Path) -> dict[str, Any]:
    write(work / "backend.md", "Backend truth alpha")
    summary = work / "summary.md"
    write(summary, "A quiet operational summary with no secret literal.")
    entries = [
        {"id": "backend", "path": "backend.md", "kind": "background", "roles": ["director"], "visibility": "backend-hidden", "tainted_by": ["SECRET-A"]},
        {"id": "summary", "path": "summary.md", "kind": "mission", "roles": ["writer"], "visibility": "writer-visible", "derived_from": ["backend"]},
    ]
    req = {"role": "writer", "budget_tokens": 1000, "blocked_secret_ids": ["SECRET-A"]}
    src_text_hash = bytes_hash(summary)
    src = compile_obs(work, entries, req)
    write(summary, "The same harmless-looking guidance is phrased in completely different words.")
    fol_text_hash = bytes_hash(summary)
    fol = compile_obs(work, entries, req)
    if src_text_hash == fol_text_hash:
        return result("INVALID", "paraphrase transform did not change bytes", src, fol)
    def blocked(obs: dict[str, Any]) -> list[dict[str, Any]]:
        return [x for x in obs["semantics"]["excluded"] if x.get("id") == "summary" and x.get("reason") == "semantic-secret-taint"]
    ok = not src["errors"] and not fol["errors"] and blocked(src) == blocked(fol) and bool(blocked(src))
    return result("PASS" if ok else "FAIL", "Provenance taint survives literal-free paraphrase." if ok else "Paraphrase changed taint enforcement.", blocked(src), blocked(fol))


def mr_irrelevant_context_expansion(work: Path) -> dict[str, Any]:
    write(work / "core.md", "core")
    write(work / "scene.md", "scene")
    write(work / "noise.md", "irrelevant appendix")
    base = [
        {"id": "core", "path": "core.md", "kind": "mission", "priority": 10, "required": True, "roles": ["writer"], "visibility": "writer-visible"},
        {"id": "scene", "path": "scene.md", "kind": "scene-packet", "priority": 8, "roles": ["writer"], "visibility": "writer-visible"},
    ]
    noise = {"id": "noise", "path": "noise.md", "kind": "background", "priority": -100, "roles": ["writer"], "visibility": "writer-visible"}
    req = {"role": "writer", "budget_tokens": 4000, "required_ids": ["core"]}
    src = compile_obs(work, base, req)
    fol = compile_obs(work, base + [noise], req)
    if src["errors"] or fol["errors"]:
        return result("INVALID", "context source/follow-up invalid", src, fol)
    src_rows = {x["id"]: x for x in src["semantics"]["included"]}
    fol_rows = {x["id"]: x for x in fol["semantics"]["included"]}
    protected = {k: v for k, v in src_rows.items() if k in {"core", "scene"}}
    ok = all(fol_rows.get(k) == v for k, v in protected.items()) and "noise" in fol_rows and set(src_rows).issubset(fol_rows)
    return result("PASS" if ok else "FAIL", "Irrelevant expansion preserves the protected source subset." if ok else "Irrelevant context displaced or changed protected context.", src_rows, fol_rows)


def mr_chapter_window(work: Path) -> dict[str, Any]:
    write(work / "local.md", "chapter-local")
    write(work / "global.md", "always")
    entries = [
        {"id": "local", "path": "local.md", "kind": "mission", "priority": 10, "roles": ["writer"], "visibility": "writer-visible", "available_from_chapter": 8, "available_to_chapter": 8},
        {"id": "global", "path": "global.md", "kind": "background", "priority": 1, "roles": ["writer"], "visibility": "writer-visible"},
    ]
    src = compile_obs(work, entries, {"role": "writer", "budget_tokens": 1000, "target_chapter": 8})
    fol = compile_obs(work, entries, {"role": "writer", "budget_tokens": 1000, "target_chapter": 9})
    sids = [x["id"] for x in src["semantics"]["included"]]
    fids = [x["id"] for x in fol["semantics"]["included"]]
    expired = [x for x in fol["semantics"]["excluded"] if x.get("id") == "local" and x.get("reason") == "expired-availability"]
    ok = not src["errors"] and not fol["errors"] and "local" in sids and "local" not in fids and "global" in sids and "global" in fids and bool(expired)
    return result("PASS" if ok else "FAIL", "Availability boundary changes only the chapter-local artifact." if ok else "Availability boundary behavior drifted.", src["semantics"], fol["semantics"])


def mr_declassification(work: Path) -> dict[str, Any]:
    write(work / "safe.md", "safe")
    write(work / "tainted.md", "derived operational fact")
    base_entry = {"id": "tainted", "path": "tainted.md", "kind": "knowledge", "priority": 5, "roles": ["writer"], "visibility": "writer-visible", "tainted_by": ["SECRET-A"]}
    safe = {"id": "safe", "path": "safe.md", "kind": "background", "priority": 1, "roles": ["writer"], "visibility": "writer-visible"}
    req = {"role": "writer", "budget_tokens": 1000, "blocked_secret_ids": ["SECRET-A"]}
    src = compile_obs(work, [safe, base_entry], req)
    released = copy.deepcopy(base_entry)
    released["declassification"] = {"roles": ["writer"], "status": "approved", "secret_ids": ["SECRET-A"]}
    fol = compile_obs(work, [safe, released], req)
    sids = [x["id"] for x in src["semantics"]["included"]]
    fids = [x["id"] for x in fol["semantics"]["included"]]
    safe_src = next((x for x in src["semantics"]["included"] if x["id"] == "safe"), None)
    safe_fol = next((x for x in fol["semantics"]["included"] if x["id"] == "safe"), None)
    ok = not src["errors"] and not fol["errors"] and "tainted" not in sids and "tainted" in fids and safe_src == safe_fol and released.get("tainted_by") == base_entry.get("tainted_by")
    return result("PASS" if ok else "FAIL", "Declassification changes permission while preserving taint/provenance identity." if ok else "Declassification changed unrelated semantics or failed to release permission.", src["semantics"], fol["semantics"])


def simple_branches() -> dict[str, dict[str, Any]]:
    return branch_map({"branches": {"main": {"parent": None}, "left": {"parent": "main", "fork_event": "E1"}, "right": {"parent": "main", "fork_event": "E1"}}})


def mr_event_serialization(work: Path) -> dict[str, Any]:
    events = [
        {"event_id": "E1", "branch": "main", "seq": 1, "event_type": "Set", "status": "committed", "intent": "seed", "effects": [{"op": "set", "path": "world.flag", "value": True}]},
        {"event_id": "E2", "branch": "main", "seq": 2, "event_type": "Set", "status": "committed", "intent": "counter", "effects": [{"op": "set", "path": "world.count", "value": 2}]},
    ]
    src_path = work / "src.jsonl"
    fol_path = work / "fol.jsonl"
    write(src_path, "\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in events) + "\n")
    reversed_events = [{k: row[k] for k in reversed(list(row.keys()))} for row in events]
    write(fol_path, "\n".join(json.dumps(x, ensure_ascii=False, separators=(", ", ": ")) for x in reversed_events) + "\n")
    if bytes_hash(src_path) == bytes_hash(fol_path):
        return result("INVALID", "serialization transform was a no-op", {}, {})
    src_events, fol_events = load_jsonl(src_path), load_jsonl(fol_path)
    branches = branch_map({"branches": {"main": {"parent": None}}})
    se, sw = validate_runtime(src_events, branches)
    fe, fw = validate_runtime(fol_events, branches)
    sstate, _ = replay(src_events, branches, "main")
    fstate, _ = replay(fol_events, branches, "main")
    ok = not se and not fe and sstate == fstate
    return result("PASS" if ok else "FAIL", "Event representation changes do not alter replay." if ok else "Event serialization changed Runtime semantics.", sstate, fstate, source_warnings=sw, followup_warnings=fw)


def mr_dependency_permutation(work: Path) -> dict[str, Any]:
    del work
    rows = [
        {"source": "A", "target": "B", "kind": "causal"},
        {"source": "B", "target": "C", "kind": "promise"},
        {"source": "X", "target": "Y", "kind": "context"},
    ]
    src = {"impact": canonical_impact(rows, "A"), "why": canonical_why(rows, "C")}
    fol = {"impact": canonical_impact(list(reversed(rows)), "A"), "why": canonical_why(list(reversed(rows)), "C")}
    ok = src == fol
    return result("PASS" if ok else "FAIL", "Dependency order does not change graph semantics." if ok else "Dependency order changed graph semantics.", src, fol)


def mr_dependency_noise(work: Path) -> dict[str, Any]:
    del work
    rows = [{"source": "A", "target": "B", "kind": "causal"}, {"source": "B", "target": "C", "kind": "promise"}]
    src = {"impact": canonical_impact(rows, "A"), "why": canonical_why(rows, "C")}
    follow_rows = rows + [{"source": "X", "target": "Y", "kind": "unrelated"}, {"source": "Y", "target": "Z", "kind": "unrelated"}]
    fol = {"impact": canonical_impact(follow_rows, "A"), "why": canonical_why(follow_rows, "C")}
    ok = src == fol
    return result("PASS" if ok else "FAIL", "Disconnected dependency noise stays isolated." if ok else "Disconnected graph component contaminated impact semantics.", src, fol)


def mr_sibling_branch(work: Path) -> dict[str, Any]:
    del work
    branches = simple_branches()
    base = [
        {"event_id": "E1", "branch": "main", "seq": 1, "event_type": "Seed", "status": "committed", "intent": "fork base", "effects": [{"op": "set", "path": "world.seed", "value": True}]},
        {"event_id": "L1", "branch": "left", "seq": 1, "event_type": "Left", "status": "committed", "intent": "left", "effects": [{"op": "set", "path": "branch.left", "value": 1}]},
        {"event_id": "R1", "branch": "right", "seq": 1, "event_type": "Right", "status": "committed", "intent": "right", "effects": [{"op": "set", "path": "branch.right", "value": 1}]},
    ]
    follow = base + [{"event_id": "L2", "branch": "left", "seq": 2, "event_type": "Left", "status": "committed", "intent": "left perturbation", "effects": [{"op": "set", "path": "branch.left", "value": 2}]}]
    be, _ = validate_runtime(base, branches)
    fe, _ = validate_runtime(follow, branches)
    src = {b: replay(base, branches, b)[0] for b in ("main", "left", "right")}
    fol = {b: replay(follow, branches, b)[0] for b in ("main", "left", "right")}
    ok = not be and not fe and src["main"] == fol["main"] and src["right"] == fol["right"] and src["left"] != fol["left"]
    return result("PASS" if ok else "FAIL", "Sibling-branch perturbation remains isolated." if ok else "Sibling branch perturbation leaked or failed to affect target branch.", src, fol)


def replay_single(value: str, path: str = "characters.CH-A.display_name") -> dict[str, Any]:
    events = [
        {"event_id": "E1", "branch": "main", "seq": 1, "event_type": "Seed", "status": "committed", "intent": "identity", "effects": [
            {"op": "set", "path": path, "value": value},
            {"op": "set", "path": "characters.CH-A.knowledge.code", "value": "K-1"},
            {"op": "set", "path": "objects.KEY.holder", "value": "CH-A"},
        ]},
    ]
    branches = branch_map({"branches": {"main": {"parent": None}}})
    state, _ = replay(events, branches, "main")
    return state


def mr_stable_label(work: Path) -> dict[str, Any]:
    del work
    src, fol = replay_single("林珂"), replay_single("林岚")
    sf, ff = flatten_state(src), flatten_state(fol)
    diffs = sorted(k for k in set(sf) | set(ff) if sf.get(k) != ff.get(k))
    ok = diffs == ["characters.CH-A.display_name"] and sf.get("characters.CH-A.knowledge.code") == ff.get("characters.CH-A.knowledge.code") and sf.get("objects.KEY.holder") == ff.get("objects.KEY.holder")
    return result("PASS" if ok else "FAIL", "Display-label contrast is local to the stable entity label." if ok else "Display-label change disturbed stable-ID semantics.", sf, ff, diff_paths=diffs)


def mr_prose_roundtrip(work: Path) -> dict[str, Any]:
    prose = work / "chapter.md"
    write(prose, "他把钥匙放在桌上。\n")
    evidence = "他把钥匙放在桌上。"
    report = {
        "reconciliation_version": "1.0.0",
        "chapter_id": "CH-1",
        "branch": "main",
        "prose_path": "chapter.md",
        "prose_sha256": file_sha(prose),
        "status": "APPROVED",
        "prose_candidates": [{"candidate_id": "PC-1", "description": "钥匙被放到桌上", "disposition": "committed", "delta_ids": ["D-1"], "notes": ""}],
        "state_deltas": [{"delta_id": "D-1", "description": "钥匙位置变化", "target": "objects.KEY.location", "before": "hand", "after": "table", "basis": "prose", "basis_note": "", "evidence": [{"path": "chapter.md", "start_line": 1, "end_line": 1, "sha256": sha(evidence)}]}],
    }
    src_errors, _, src_summary = validate_report(report, work, strict=True)
    delta_semantics = [{k: row.get(k) for k in ("delta_id", "description", "target", "before", "after", "basis", "basis_note")} for row in report["state_deltas"]]
    delta_hash = stable_hash(delta_semantics)
    write(prose, "他把钥匙搁到了桌面上。\n")
    stale_errors, _, stale_summary = validate_report(report, work, strict=True)
    refreshed = copy.deepcopy(report)
    refreshed["prose_sha256"] = file_sha(prose)
    refreshed["state_deltas"][0]["evidence"][0]["sha256"] = sha("他把钥匙搁到了桌面上。")
    fresh_errors, _, fresh_summary = validate_report(refreshed, work, strict=True)
    stale_detected = any("stale" in x or "hash mismatch" in x for x in stale_errors)
    refreshed_delta_semantics = [{k: row.get(k) for k in ("delta_id", "description", "target", "before", "after", "basis", "basis_note")} for row in refreshed["state_deltas"]]
    ok = not src_errors and stale_detected and not fresh_errors and stable_hash(refreshed_delta_semantics) == delta_hash
    source = {"errors": src_errors, "summary": src_summary, "delta_hash": delta_hash}
    follow = {"stale_errors": stale_errors, "stale_summary": stale_summary, "refreshed_errors": fresh_errors, "refreshed_summary": fresh_summary, "delta_hash": stable_hash(refreshed_delta_semantics)}
    return result("PASS" if ok else "FAIL", "Evidence goes stale on prose rewrite and recovers after explicit refresh without changing reviewed delta." if ok else "Evidence round-trip contract failed.", source, follow)


def reverse_dicts(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: reverse_dicts(value[k]) for k in reversed(list(value.keys()))}
    if isinstance(value, list):
        return [reverse_dicts(x) for x in value]
    return value


def normalize_kernel(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": report.get("project_id"),
        "current_branch": report.get("current_branch"),
        "summary": report.get("summary"),
        "laws": [{"law": x.get("law"), "law_name": x.get("law_name"), "status": x.get("status"), "details": x.get("details")} for x in report.get("laws", []) if isinstance(x, dict)],
        "runtime_projection_sha256": report.get("runtime_projection_sha256"),
    }


def mr_project_json_representation(work: Path) -> dict[str, Any]:
    fixture = ROOT / "assets" / "regression-corpora" / "relationship-lean"
    src_root, fol_root = work / "source", work / "follow"
    shutil.copytree(fixture, src_root)
    shutil.copytree(fixture, fol_root)
    before_hashes: list[str] = []
    after_hashes: list[str] = []
    for path in sorted(fol_root.rglob("*.json")):
        data = load_json(path)
        before_hashes.append(bytes_hash(path))
        path.write_text(json.dumps(reverse_dicts(data), ensure_ascii=False, indent=None, separators=(", ", ": ")) + "\n", encoding="utf-8")
        after_hashes.append(bytes_hash(path))
    if before_hashes == after_hashes:
        return result("INVALID", "JSON representation transformation changed no bytes", before_hashes, after_hashes)
    src, fol = normalize_kernel(verify_project(src_root)), normalize_kernel(verify_project(fol_root))
    ok = src == fol and int(src.get("summary", {}).get("fail", 1)) == 0 and int(fol.get("summary", {}).get("fail", 1)) == 0
    return result("PASS" if ok else "FAIL", "JSON representation changes preserve Kernel semantics." if ok else "JSON representation changed Kernel semantics.", src, fol)


def mr_branch_context_noise(work: Path) -> dict[str, Any]:
    write(work / "core.md", "main core")
    write(work / "noise.md", "sibling branch only")
    base = [{"id": "core", "path": "core.md", "kind": "mission", "priority": 10, "required": True, "roles": ["writer"], "visibility": "writer-visible", "branch": "main"}]
    noise = {"id": "sibling-noise", "path": "noise.md", "kind": "mission", "priority": 999999, "required": True, "roles": ["writer"], "visibility": "writer-visible", "branch": "loop-b"}
    req = {"role": "writer", "branch": "main", "budget_tokens": 1000, "required_ids": ["core"]}
    src, fol = compile_obs(work, base, req), compile_obs(work, base + [noise], req)
    ok = not src["errors"] and not fol["errors"] and src["semantics"]["included"] == fol["semantics"]["included"] and src["pack"] == fol["pack"] and any(x.get("id") == "sibling-noise" and x.get("reason") == "branch-mismatch" for x in fol["semantics"]["excluded"])
    return result("PASS" if ok else "FAIL", "Sibling-branch context noise cannot steal main-branch context." if ok else "Branch-scoped context noise contaminated main pack.", src["semantics"], fol["semantics"])


def mr_secret_registry_permutation(work: Path) -> dict[str, Any]:
    write(work / "safe.md", "safe")
    write(work / "a.md", "derived a")
    write(work / "b.md", "derived b")
    registry = work / "secrets.json"
    secrets = [
        {"id": "SECRET-A", "status": "active", "allowed_roles": ["director"]},
        {"id": "SECRET-B", "status": "active", "allowed_roles": ["director"]},
    ]
    write_json(registry, {"secrets": secrets})
    entries = [
        {"id": "safe", "path": "safe.md", "kind": "background", "roles": ["writer"], "visibility": "writer-visible"},
        {"id": "a", "path": "a.md", "kind": "knowledge", "roles": ["writer"], "visibility": "writer-visible", "tainted_by": ["SECRET-A"]},
        {"id": "b", "path": "b.md", "kind": "knowledge", "roles": ["writer"], "visibility": "writer-visible", "tainted_by": ["SECRET-B"]},
    ]
    req = {"role": "writer", "budget_tokens": 1000, "secret_registry": "secrets.json"}
    src = compile_obs(work, entries, req)
    write_json(registry, {"secrets": list(reversed(secrets))})
    fol = compile_obs(work, entries, req)
    ok = not src["errors"] and not fol["errors"] and src["semantics"] == fol["semantics"] and src["pack"] == fol["pack"]
    return result("PASS" if ok else "FAIL", "Secret Registry order does not change information-flow decisions." if ok else "Secret Registry order changed blocking semantics.", src["semantics"], fol["semantics"])


def mr_local_event_contrast(work: Path) -> dict[str, Any]:
    del work
    branches = branch_map({"branches": {"main": {"parent": None}}})
    def hist(holder: str) -> list[dict[str, Any]]:
        return [{"event_id": "E1", "branch": "main", "seq": 1, "event_type": "Move", "status": "committed", "intent": "holder contrast", "effects": [
            {"op": "set", "path": "objects.KEY.holder", "value": holder},
            {"op": "set", "path": "weather.state", "value": "rain"},
            {"op": "set", "path": "characters.CH-A.knowledge.code", "value": "K-1"},
        ]}]
    src, _ = replay(hist("CH-A"), branches, "main")
    fol, _ = replay(hist("CH-B"), branches, "main")
    sf, ff = flatten_state(src), flatten_state(fol)
    diffs = sorted(k for k in set(sf) | set(ff) if sf.get(k) != ff.get(k))
    ok = diffs == ["objects.KEY.holder"] and sf.get("weather.state") == ff.get("weather.state") and sf.get("characters.CH-A.knowledge.code") == ff.get("characters.CH-A.knowledge.code")
    return result("PASS" if ok else "FAIL", "Small semantic contrast changes exactly its addressed replay path." if ok else "Local event contrast changed unrelated semantics or was ignored.", sf, ff, diff_paths=diffs)


def mr_knowledge_record_permutation(work: Path) -> dict[str, Any]:
    source_state = {
        "current_day": 12,
        "knowledge_state": [
            {"actor": "CH-A", "fact": "F-1", "status": "known", "acquired_at": 2, "source": "scene-1"},
            {"actor": "CH-A", "fact": "F-2", "status": "suspected", "acquired_at": 7, "belief": "likely", "source": "scene-4"},
            {"actor": "CH-B", "fact": "F-X", "status": "known", "acquired_at": 1, "source": "scene-x"}
        ]
    }
    follow_state = copy.deepcopy(source_state)
    follow_state["knowledge_state"] = list(reversed(follow_state["knowledge_state"]))
    src_path, fol_path = work / "source-state.json", work / "follow-state.json"
    write_json(src_path, source_state)
    write_json(fol_path, follow_state)
    if bytes_hash(src_path) == bytes_hash(fol_path):
        return result("INVALID", "knowledge permutation changed no bytes", source_state, follow_state)

    def query(path: Path) -> tuple[int, list[dict[str, Any]], str]:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "story_ops.py"), str(path), "knowledge", "CH-A", "--at", "12", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        try:
            rows = json.loads(proc.stdout) if proc.stdout.strip() else []
        except json.JSONDecodeError:
            rows = []
        norm = sorted((x for x in rows if isinstance(x, dict)), key=lambda x: (str(x.get("fact")), str(x.get("status"))))
        return proc.returncode, norm, proc.stderr

    src_rc, src_rows, src_err = query(src_path)
    fol_rc, fol_rows, fol_err = query(fol_path)
    ok = src_rc == 0 and fol_rc == 0 and src_rows == fol_rows and len(src_rows) == 2
    return result("PASS" if ok else "FAIL", "Knowledge-record serialization order does not change actor epistemic state." if ok else "Knowledge-record order changed epistemic query semantics.", src_rows, fol_rows, source_stderr=src_err, followup_stderr=fol_err)



def mr_inactive_optional_artifact_invariance(work: Path) -> dict[str, Any]:
    """Adding an inactive optional capability declaration must not make a valid Lean project invalid."""
    source = work / "source"
    follow = work / "followup"
    init = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "project_ops.py"), "init", str(source), "--project-id", "MR-POETICS-OPTIONAL"],
        text=True, capture_output=True, check=False, cwd=ROOT,
    )
    if init.returncode != 0:
        return result("INVALID", "could not initialize source project", {"stderr": init.stderr}, {})
    shutil.copytree(source, follow)
    manifest_path = follow / "project-manifest.json"
    manifest = load_json(manifest_path)
    manifest.setdefault("optional_artifacts", []).append({
        "kind": "hidden-causal-network",
        "path": "planning/05-hidden-causal-network.md",
        "status": "inactive",
        "scope": "project",
        "reason": "metamorphic inactive-capability declaration",
    })
    write_json(manifest_path, manifest)

    def verify(project: Path) -> dict[str, Any]:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "project_ops.py"), "verify", str(project / "project-manifest.json"), "--root", str(project), "--json"],
            text=True, capture_output=True, check=False, cwd=ROOT,
        )
        try:
            payload = json.loads(proc.stdout or "{}")
        except Exception:
            payload = {"stdout": proc.stdout, "stderr": proc.stderr}
        return {"returncode": proc.returncode, "errors": payload.get("errors", []), "warnings": payload.get("warnings", [])}

    src = verify(source)
    fol = verify(follow)
    transformed = bytes_hash(source / "project-manifest.json") != bytes_hash(follow / "project-manifest.json")
    if not transformed:
        return result("INVALID", "inactive-artifact transformation changed no bytes", src, fol)
    ok = src["returncode"] == 0 and fol["returncode"] == 0 and not src["errors"] and not fol["errors"]
    return result(
        "PASS" if ok else "FAIL",
        "Inactive optional capability does not become a readiness obligation." if ok else "Inactive optional capability invalidated the project.",
        src, fol,
    )


def _init_poetics_project(root: Path, project_id: str) -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "project_ops.py"), "init", str(root), "--project-id", project_id],
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )
    return proc.returncode == 0, (proc.stderr or proc.stdout)


def _poetics_projection(manifest: dict[str, Any]) -> dict[str, Any]:
    provenance = manifest.get("scoped_project_poetics_provenance")
    if isinstance(provenance, dict):
        provenance = {
            "authority_ref": provenance.get("authority_ref"),
            "scope": provenance.get("scope"),
            "parent_ref": provenance.get("parent_ref"),
            "hash": provenance.get("hash"),
            "status": provenance.get("status"),
            "expires_at": provenance.get("expires_at"),
        }
    return {
        "project_poetics_ref": manifest.get("project_poetics_ref"),
        "scoped_project_poetics_ref": manifest.get("scoped_project_poetics_ref"),
        "scoped_project_poetics_envelope_ref": manifest.get("scoped_project_poetics_envelope_ref"),
        "scoped_project_poetics_provenance": provenance,
        "active_capabilities": sorted(str(x) for x in (manifest.get("active_capabilities") or [])),
    }


def mr_poetics_scope_override_locality(work: Path) -> dict[str, Any]:
    """A chapter override must be local, inherited from an unchanged parent, and rejected out of scope."""
    root = work / "project"
    ok_init, init_msg = _init_poetics_project(root, "MR-POETICS-SCOPE")
    if not ok_init:
        return result("INVALID", "could not initialize poetics scope project", {"message": init_msg}, {})

    parent = root / "planning/project-poetics.md"
    parent_hash_before = bytes_hash(parent)
    mission_rel = "context/shared-mission.md"
    write(root / mission_rel, "# Mission\n\nPreserve the established hard facts while drafting the requested chapter.\n")
    index = {"entries": [{
        "id": "mission",
        "path": mission_rel,
        "kind": "mission",
        "required": True,
        "roles": ["writer"],
        "visibility": "writer-visible",
    }]}
    later_req = {
        "role": "writer",
        "branch": "main",
        "task_id": "TASK-13",
        "target_chapter": 13,
        "budget_tokens": 3000,
        "strict_visibility": True,
        "project_manifest": "project-manifest.json",
    }
    source_later = compile_obs(root, index["entries"], later_req)
    if source_later["errors"]:
        return result("INVALID", "baseline later-chapter context failed", source_later, {})

    override_rel = "planning/poetics-overrides/chapter-0012.md"
    envelope_rel = "planning/poetics-overrides/chapter-0012.envelope.json"
    write(
        root / override_rel,
        "# Chapter 12 Scoped Project Poetics\n\n"
        "Authorized deviation: one chapter may use a visibly fragmented form.\n"
        "Return condition: Chapter 13 resumes the inherited project-level form.\n",
    )
    manifest_path = root / "project-manifest.json"
    project_manifest = load_json(manifest_path)
    project_manifest["poetics_override_refs"] = [override_rel]
    write_json(manifest_path, project_manifest)
    envelope = build_envelope(
        root=root,
        content_ref=override_rel,
        authority_ref="planning/project-poetics.md",
        parent_ref="planning/project-poetics.md",
        scope={"project_id": "MR-POETICS-SCOPE", "arc": None, "chapter": "12", "scene": None, "task": "TASK-12"},
        status="active",
        expires_at=None,
    )
    write_json(root / envelope_rel, envelope)

    target_req = {
        **later_req,
        "task_id": "TASK-12",
        "target_chapter": 12,
        "scoped_project_poetics_ref": override_rel,
        "scoped_project_poetics_envelope_ref": envelope_rel,
        "active_capabilities": ["formal-heterogeneity"],
    }
    target = compile_obs(root, index["entries"], target_req)
    follow_later = compile_obs(root, index["entries"], later_req)

    out_of_scope_rejected = False
    out_of_scope_message = ""
    wrong_req = {
        **later_req,
        "scoped_project_poetics_ref": override_rel,
        "scoped_project_poetics_envelope_ref": envelope_rel,
    }
    try:
        compile_pack(index, wrong_req, root)
    except ValueError as exc:
        out_of_scope_message = str(exc)
        out_of_scope_rejected = "scope mismatch" in out_of_scope_message

    target_ids = {str(x.get("id")) for x in target["manifest"].get("included", []) if isinstance(x, dict)}
    target_local_effect = (
        not target["errors"]
        and "__scoped_project_poetics__" in target_ids
        and "visibly fragmented form" in target["pack"]
    )
    later_unchanged = (
        not follow_later["errors"]
        and source_later["pack"] == follow_later["pack"]
        and source_later["semantics"] == follow_later["semantics"]
    )
    parent_unchanged = bytes_hash(parent) == parent_hash_before
    transformed = stable_hash(source_later["manifest"].get("poetics_override_refs", [])) != stable_hash(follow_later["manifest"].get("poetics_override_refs", []))
    if not transformed:
        return result("INVALID", "scope-override transformation did not change project override registration", source_later["manifest"], follow_later["manifest"])
    ok = target_local_effect and later_unchanged and parent_unchanged and out_of_scope_rejected
    source_obs = {
        "later_pack_sha256": stable_hash(source_later["pack"]),
        "later_semantics": source_later["semantics"],
        "parent_sha256": parent_hash_before,
        "override_refs": source_later["manifest"].get("poetics_override_refs", []),
    }
    follow_obs = {
        "target_chapter_has_override": target_local_effect,
        "later_pack_sha256": stable_hash(follow_later["pack"]),
        "later_semantics": follow_later["semantics"],
        "parent_sha256": bytes_hash(parent),
        "override_refs": follow_later["manifest"].get("poetics_override_refs", []),
        "out_of_scope_rejected": out_of_scope_rejected,
    }
    return result(
        "PASS" if ok else "FAIL",
        "Scoped poetics override is local, does not rewrite its parent, and cannot leak past scope." if ok else "Scoped poetics override leaked, rewrote its parent, or was accepted outside scope.",
        source_obs,
        follow_obs,
        out_of_scope_message=out_of_scope_message,
    )


def mr_authorized_heterogeneity_contrast(work: Path) -> dict[str, Any]:
    """The same measured voice shift is reviewable when unscoped and authorized when valid scoped poetics says so."""
    root = work / "project"
    ok_init, init_msg = _init_poetics_project(root, "MR-POETICS-VOICE")
    if not ok_init:
        return result("INVALID", "could not initialize authorized-heterogeneity project", {"message": init_msg}, {})

    dialogue = root / "analysis/dialogue.jsonl"
    dialogue.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for chapter in range(1, 6):
        rows.append({"character": "C1", "chapter": chapter, "text": "好。"})
    for chapter in range(10, 15):
        rows.append({"character": "C1", "chapter": chapter, "text": "你真的认为事情会这么简单吗？我完全不同意！"})
    dialogue.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows), encoding="utf-8")

    def run(extra: list[str]) -> tuple[int, list[dict[str, Any]], str]:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "voice_drift.py"), str(dialogue), "--baseline-through", "5", "--recent-from", "10", "--json", *extra],
            text=True,
            capture_output=True,
            check=False,
            cwd=ROOT,
        )
        try:
            payload = json.loads(proc.stdout) if proc.stdout.strip() else []
        except Exception:
            payload = []
        return proc.returncode, payload if isinstance(payload, list) else [], proc.stderr

    src_rc, src_rows, src_err = run([])
    if src_rc != 0 or not src_rows:
        return result("INVALID", "baseline voice diagnostic failed", {"returncode": src_rc, "stderr": src_err}, {})

    scoped_rel = "context/voice-authorized-poetics.md"
    envelope_rel = "context/voice-authorized-poetics.envelope.json"
    write(root / scoped_rel, "# Scoped Project Poetics\n\nAuthorized deviation: C1 may shift into a confrontational register for this task.\n")
    envelope = build_envelope(
        root=root,
        content_ref=scoped_rel,
        authority_ref="planning/project-poetics.md",
        parent_ref="planning/project-poetics.md",
        scope={"project_id": "MR-POETICS-VOICE", "arc": None, "chapter": None, "scene": None, "task": "VOICE-MR"},
        status="active",
        expires_at=None,
    )
    write_json(root / envelope_rel, envelope)
    fol_rc, fol_rows, fol_err = run([
        "--authorized-shift", "C1",
        "--project-root", str(root),
        "--project-manifest", "project-manifest.json",
        "--scoped-poetics-ref", scoped_rel,
        "--scoped-poetics-envelope-ref", envelope_rel,
        "--scope-task", "VOICE-MR",
    ])
    if fol_rc != 0 or not fol_rows:
        return result("INVALID", "authorized voice diagnostic failed", src_rows, {"returncode": fol_rc, "stderr": fol_err})

    source = src_rows[0]
    follow = fol_rows[0]
    same_measurement = source.get("drift_indicator") == follow.get("drift_indicator") and source.get("baseline") == follow.get("baseline") and source.get("recent") == follow.get("recent")
    transformed = source.get("status") != follow.get("status")
    if not transformed:
        return result("INVALID", "authorization transformation produced no classification contrast", source, follow)
    ok = (
        source.get("status") == "review"
        and follow.get("status") == "authorized-variation"
        and follow.get("authorized_by_scoped_poetics") is True
        and follow.get("scoped_poetics_envelope_ref") == envelope_rel
        and same_measurement
    )
    return result(
        "PASS" if ok else "FAIL",
        "Valid scoped authorization changes drift classification without changing the measured voice shift." if ok else "Authorized heterogeneity did not produce the required classification contrast.",
        source,
        follow,
        source_stderr=src_err,
        followup_stderr=fol_err,
    )


def mr_poetics_preserving_surface_variation(work: Path) -> dict[str, Any]:
    """Surface names/settings may change while the Project-Poetics projection stays identical."""
    root = work / "project"
    ok_init, init_msg = _init_poetics_project(root, "MR-POETICS-SURFACE")
    if not ok_init:
        return result("INVALID", "could not initialize surface-variation project", {"message": init_msg}, {})

    scoped_rel = "context/task-scoped-poetics.md"
    envelope_rel = "context/task-scoped-poetics.envelope.json"
    write(
        root / scoped_rel,
        "# Scoped Project Poetics\n\n"
        "Salience: ordinary route familiarity and small perceptual changes.\n"
        "Reader activity: inhabit and notice.\n"
        "Progression: relational/perceptual accumulation, not mandatory escalation.\n",
    )
    envelope = build_envelope(
        root=root,
        content_ref=scoped_rel,
        authority_ref="planning/project-poetics.md",
        parent_ref="planning/project-poetics.md",
        scope={"project_id": "MR-POETICS-SURFACE", "arc": None, "chapter": "4", "scene": None, "task": "SURFACE-MR"},
        status="active",
        expires_at=None,
    )
    write_json(root / envelope_rel, envelope)

    mission_rel = "context/surface-mission.md"
    mission = root / mission_rel
    source_text = "# Mission\n\nMara walks Harbor Street after work and notices the bakery shutter and wet tram rail.\n"
    follow_text = "# Mission\n\nIvo walks Cedar Lane after work and notices the laundromat shutter and wet bus rail.\n"
    write(mission, source_text)
    entries = [{
        "id": "mission",
        "path": mission_rel,
        "kind": "mission",
        "required": True,
        "roles": ["writer"],
        "visibility": "writer-visible",
    }]
    req = {
        "role": "writer",
        "branch": "main",
        "task_id": "SURFACE-MR",
        "target_chapter": 4,
        "budget_tokens": 3000,
        "strict_visibility": True,
        "project_manifest": "project-manifest.json",
        "scoped_project_poetics_ref": scoped_rel,
        "scoped_project_poetics_envelope_ref": envelope_rel,
        "active_capabilities": ["ordinary-familiarity"],
    }
    src = compile_obs(root, entries, req)
    source_mission_hash = bytes_hash(mission)
    write(mission, follow_text)
    follow_mission_hash = bytes_hash(mission)
    fol = compile_obs(root, entries, req)
    if source_mission_hash == follow_mission_hash:
        return result("INVALID", "surface transformation changed no mission bytes", src, fol)
    if src["errors"] or fol["errors"]:
        return result("INVALID", "surface-variation context compilation failed", src, fol, source_errors=src["errors"], followup_errors=fol["errors"])

    src_projection = _poetics_projection(src["manifest"])
    fol_projection = _poetics_projection(fol["manifest"])
    src_rows = {str(x.get("id")): x for x in src["manifest"].get("included", []) if isinstance(x, dict)}
    fol_rows = {str(x.get("id")): x for x in fol["manifest"].get("included", []) if isinstance(x, dict)}
    poetics_hash_stable = src_rows.get("__scoped_project_poetics__", {}).get("source_sha256") == fol_rows.get("__scoped_project_poetics__", {}).get("source_sha256")
    mission_hash_changed = src_rows.get("mission", {}).get("source_sha256") != fol_rows.get("mission", {}).get("source_sha256")
    pack_changed = src["pack"] != fol["pack"]
    ok = src_projection == fol_projection and poetics_hash_stable and mission_hash_changed and pack_changed
    return result(
        "PASS" if ok else "FAIL",
        "Surface names/settings changed while scoped-poetics provenance and capability activation stayed invariant." if ok else "Surface variation mutated the Project-Poetics projection or was behaviorally vacuous.",
        {"poetics": src_projection, "mission_source_sha256": src_rows.get("mission", {}).get("source_sha256"), "pack_sha256": stable_hash(src["pack"])},
        {"poetics": fol_projection, "mission_source_sha256": fol_rows.get("mission", {}).get("source_sha256"), "pack_sha256": stable_hash(fol["pack"])},
    )


def mr_hard_core_invariance_across_poetics(work: Path) -> dict[str, Any]:
    """Conflicting valid poetics may change literary planning but cannot change Hard-Core verdicts."""
    fixture = ROOT / "assets" / "regression-corpora" / "xianxia-growth"
    source_root = work / "quiet-poetics"
    follow_root = work / "conflict-poetics"
    shutil.copytree(fixture, source_root)
    shutil.copytree(fixture, follow_root)

    poetics_rel = "planning/project-poetics.md"
    quiet_poetics = (
        "# Project Poetics\n\nStatus: active\n\n"
        "Salience: bodily recovery, routine, and quiet relational accumulation.\n"
        "Progression: small material and epistemic changes; do not manufacture event escalation.\n"
        "Mind: partial inference; preserve opacity.\n"
    )
    conflict_poetics = (
        "# Project Poetics\n\nStatus: active\n\n"
        "Salience: public conflict, institutional collision, and overt argument.\n"
        "Progression: rapid event escalation and explicit reversals.\n"
        "Mind: comparatively transparent; authorize conspicuous formal contrast.\n"
    )
    for root, text in ((source_root, quiet_poetics), (follow_root, conflict_poetics)):
        write(root / poetics_rel, text)
        manifest_path = root / "project-manifest.json"
        manifest = load_json(manifest_path)
        manifest.setdefault("canonical_paths", {})["project_poetics"] = poetics_rel
        write_json(manifest_path, manifest)

    source_poetics_hash = bytes_hash(source_root / poetics_rel)
    follow_poetics_hash = bytes_hash(follow_root / poetics_rel)
    if source_poetics_hash == follow_poetics_hash:
        return result("INVALID", "conflicting-poetics transformation changed no poetics bytes", source_poetics_hash, follow_poetics_hash)

    source_valid = normalize_kernel(verify_project(source_root))
    follow_valid = normalize_kernel(verify_project(follow_root))

    source_bad = work / "quiet-poetics-hard-fault"
    follow_bad = work / "conflict-poetics-hard-fault"
    shutil.copytree(source_root, source_bad)
    shutil.copytree(follow_root, follow_bad)
    for root in (source_bad, follow_bad):
        manifest_path = root / "project-manifest.json"
        manifest = load_json(manifest_path)
        manifest["last_committed_event"] = "EV-NONEXISTENT-HARD-FAULT"
        write_json(manifest_path, manifest)
    source_fault = normalize_kernel(verify_project(source_bad))
    follow_fault = normalize_kernel(verify_project(follow_bad))

    def fail_laws(report: dict[str, Any]) -> list[str]:
        return sorted(str(x.get("law")) for x in report.get("laws", []) if isinstance(x, dict) and x.get("status") == "fail")

    valid_same = source_valid == follow_valid and int(source_valid.get("summary", {}).get("fail", 1)) == 0
    fault_same = source_fault == follow_fault
    source_fail_laws = fail_laws(source_fault)
    follow_fail_laws = fail_laws(follow_fault)
    hard_fault_detected = (
        int(source_fault.get("summary", {}).get("fail", 0)) > 0
        and "K2" in source_fail_laws
        and source_fail_laws == follow_fail_laws
    )
    ok = valid_same and fault_same and hard_fault_detected
    return result(
        "PASS" if ok else "FAIL",
        "Conflicting Project Poetics preserve Hard-Core verdicts for both valid state and the same injected hard fault." if ok else "Project Poetics changed, masked, or relaxed Hard-Core semantic verdicts.",
        {"poetics_sha256": source_poetics_hash, "valid": source_valid, "hard_fault": source_fault},
        {"poetics_sha256": follow_poetics_hash, "valid": follow_valid, "hard_fault": follow_fault},
        source_fail_laws=source_fail_laws,
        followup_fail_laws=follow_fail_laws,
    )

def mr_regime_context(name: str) -> dict[str, Any]:
    from narrative_regime_qualification import context_checks
    row = next(x for x in context_checks()["relations"] if x["id"] == name)
    return result("PASS" if row["passed"] else "FAIL", row["claim"] + "; no model-literary effect claimed", row["source"], row["followup"])


OPERATORS: dict[str, Callable[[Path], dict[str, Any]]] = {
    "regime_witness_context": lambda work: mr_regime_context("witness-sensitive-social"),
    "regime_narrating_age_context": lambda work: mr_regime_context("narrating-age-memory"),
    "regime_object_relation_context": lambda work: mr_regime_context("object-relation"),
    "context_index_permutation": mr_context_index_permutation,
    "request_set_permutation": mr_request_set_permutation,
    "secret_paraphrase_taint_invariance": mr_secret_paraphrase,
    "irrelevant_context_expansion": mr_irrelevant_context_expansion,
    "chapter_window_direction": mr_chapter_window,
    "declassification_locality": mr_declassification,
    "event_serialization_invariance": mr_event_serialization,
    "dependency_permutation_invariance": mr_dependency_permutation,
    "dependency_noise_isolation": mr_dependency_noise,
    "sibling_branch_isolation": mr_sibling_branch,
    "stable_label_locality": mr_stable_label,
    "prose_rewrite_evidence_roundtrip": mr_prose_roundtrip,
    "project_json_representation_invariance": mr_project_json_representation,
    "branch_context_noise_isolation": mr_branch_context_noise,
    "secret_registry_permutation": mr_secret_registry_permutation,
    "local_event_contrast": mr_local_event_contrast,
    "knowledge_record_permutation": mr_knowledge_record_permutation,
    "inactive_optional_artifact_invariance": mr_inactive_optional_artifact_invariance,
    "poetics_scope_override_locality": mr_poetics_scope_override_locality,
    "authorized_heterogeneity_contrast": mr_authorized_heterogeneity_contrast,
    "poetics_preserving_surface_variation": mr_poetics_preserving_surface_variation,
    "hard_core_invariance_across_poetics": mr_hard_core_invariance_across_poetics,
}


def registry_data() -> dict[str, Any]:
    raw = load_json(REGISTRY)
    if not isinstance(raw, dict):
        raise ValueError("metamorphic registry must be an object")
    return raw


def validate_registry() -> dict[str, Any]:
    data = registry_data()
    errors: list[str] = []
    seen: set[str] = set()
    automated = 0
    documented = 0
    signatures: set[tuple[str, str, str]] = set()
    relation_types: set[str] = set()
    strata: set[str] = set()
    for row in data.get("relations", []) or []:
        if not isinstance(row, dict):
            errors.append("relation entry must be an object")
            continue
        rid = str(row.get("id", ""))
        if not rid.startswith("MR-") or len(rid) != 6 or not rid[3:].isdigit():
            errors.append(f"invalid relation id: {rid}")
        if rid in seen:
            errors.append(f"duplicate relation id: {rid}")
        seen.add(rid)
        rtype = str(row.get("relation_type", ""))
        if rtype not in ALLOWED_TYPES:
            errors.append(f"{rid}: invalid relation_type {rtype}")
        relation_types.add(rtype)
        owner = str(row.get("owner", ""))
        if not owner or not (ROOT / owner).is_file():
            errors.append(f"{rid}: owner missing or not found: {owner}")
        row_strata = row.get("strata", [])
        if not isinstance(row_strata, list) or not row_strata:
            errors.append(f"{rid}: strata must be a non-empty list")
        else:
            for s in row_strata:
                if str(s) not in ALLOWED_STRATA:
                    errors.append(f"{rid}: invalid semantic stratum {s}")
                strata.add(str(s))
        for key in ("transform", "expected_relation", "title", "category"):
            if not str(row.get(key, "")).strip():
                errors.append(f"{rid}: missing {key}")
        automation = str(row.get("automation", ""))
        if automation == "automated":
            automated += 1
            op = str(row.get("operator", ""))
            if op not in OPERATORS:
                errors.append(f"{rid}: unknown automated operator {op}")
            sig = (op, owner, rtype)
            if sig in signatures:
                errors.append(f"{rid}: duplicate automated relation signature")
            signatures.add(sig)
        elif automation == "documented":
            documented += 1
            if row.get("operator"):
                errors.append(f"{rid}: documented relation must not pretend to have an automated operator")
        else:
            errors.append(f"{rid}: automation must be automated or documented")
    policy = data.get("policy", {}) if isinstance(data.get("policy"), dict) else {}
    min_types = int(policy.get("minimum_automated_relation_types", 0) or 0)
    automated_types = {str(x.get("relation_type")) for x in data.get("relations", []) if isinstance(x, dict) and x.get("automation") == "automated"}
    automated_strata = {str(s) for x in data.get("relations", []) if isinstance(x, dict) and x.get("automation") == "automated" for s in (x.get("strata", []) or [])}
    min_strata = int(policy.get("minimum_covered_semantic_strata", 0) or 0)
    automated_poetics_ids = sorted(str(x.get("id")) for x in data.get("relations", []) if isinstance(x, dict) and x.get("automation") == "automated" and x.get("category") == "project-poetics")
    min_poetics = int(policy.get("minimum_automated_project_poetics_relations", 0) or 0)
    if len(automated_types) < min_types:
        errors.append(f"automated relation-type coverage {len(automated_types)} below minimum {min_types}")
    if len(automated_strata) < min_strata:
        errors.append(f"automated semantic-stratum coverage {len(automated_strata)} below minimum {min_strata}")
    if len(automated_poetics_ids) < min_poetics:
        errors.append(f"automated Project-Poetics relation coverage {len(automated_poetics_ids)} below minimum {min_poetics}")
    return {
        "registry_version": data.get("registry_version"),
        "relation_count": automated + documented,
        "automated_count": automated,
        "documented_count": documented,
        "automated_relation_types": sorted(automated_types),
        "automated_semantic_strata": sorted(automated_strata),
        "automated_project_poetics_count": len(automated_poetics_ids),
        "automated_project_poetics_ids": automated_poetics_ids,
        "errors": errors,
    }


def run_suite(selected: set[str] | None = None) -> dict[str, Any]:
    validation = validate_registry()
    if validation["errors"]:
        return {**validation, "results": [], "passed": 0, "failed": 0, "invalid": 0, "promotion_gate": "FAIL"}
    data = registry_data()
    rows = [x for x in data.get("relations", []) if isinstance(x, dict) and x.get("automation") == "automated"]
    if selected:
        known = {str(x.get("id")) for x in rows}
        missing = sorted(selected - known)
        if missing:
            return {**validation, "errors": [f"unknown or non-automated relation: {x}" for x in missing], "results": [], "passed": 0, "failed": 0, "invalid": 0, "promotion_gate": "FAIL"}
        rows = [x for x in rows if str(x.get("id")) in selected]
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="lwa-metamorphic-") as td:
        base = Path(td)
        for row in rows:
            rid = str(row["id"])
            work = base / rid
            work.mkdir(parents=True, exist_ok=True)
            try:
                outcome = OPERATORS[str(row["operator"])](work)
            except Exception as exc:
                outcome = result("INVALID", f"operator raised: {exc}", {}, {})
            results.append({
                "id": rid,
                "title": row.get("title"),
                "relation_type": row.get("relation_type"),
                "category": row.get("category"),
                "owner": row.get("owner"),
                "strata": row.get("strata"),
                **outcome,
            })
    passed = sum(1 for x in results if x.get("status") == "PASS")
    failed = sum(1 for x in results if x.get("status") == "FAIL")
    invalid = sum(1 for x in results if x.get("status") == "INVALID")
    covered_types = sorted({str(x.get("relation_type")) for x in results})
    covered_strata = sorted({str(s) for x in results for s in (x.get("strata", []) or [])})
    full_gate = not selected
    gate = "PASS" if failed == 0 and invalid == 0 and (not full_gate or passed == validation["automated_count"]) else "FAIL"
    return {
        **validation,
        "automated_selected": len(results),
        "passed": passed,
        "failed": failed,
        "invalid": invalid,
        "covered_relation_types": covered_types,
        "covered_semantic_strata": covered_strata,
        "promotion_gate": gate,
        "results": results,
    }


def emit(payload: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if isinstance(payload, dict) and "results" in payload:
        for row in payload.get("results", []):
            print(f"{row.get('status'):7} {row.get('id')} [{row.get('relation_type')}] {row.get('title')}: {row.get('message')}")
        print(f"summary: passed={payload.get('passed')} failed={payload.get('failed')} invalid={payload.get('invalid')} relation_types={len(payload.get('covered_relation_types', []))} strata={len(payload.get('covered_semantic_strata', []))} promotion_gate={payload.get('promotion_gate')}")
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    q = sub.add_parser("validate", help="validate the metamorphic relation registry")
    q.add_argument("--json", action="store_true")
    q = sub.add_parser("catalog", help="list metamorphic relations")
    q.add_argument("--json", action="store_true")
    q = sub.add_parser("run", help="run automated metamorphic/adversarial relations")
    q.add_argument("--relation", action="append", default=[], help="run only this automated MR id; repeatable")
    q.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.command == "validate":
        payload = validate_registry()
        emit(payload, args.json)
        return 1 if payload["errors"] else 0
    if args.command == "catalog":
        data = registry_data()
        payload = data.get("relations", [])
        if args.json:
            emit(payload, True)
        else:
            for row in payload:
                print(f"{row.get('id')} [{row.get('relation_type')}/{row.get('automation')}] {row.get('title')}")
        return 0
    selected = set(args.relation) if args.relation else None
    payload = run_suite(selected)
    emit(payload, args.json)
    return 0 if payload.get("promotion_gate") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
