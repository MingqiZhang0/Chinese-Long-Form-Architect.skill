#!/usr/bin/env python3
"""Run narrative fault-injection mutation tests against the durable failure corpus.

This is semantic/artifact mutation testing, not blind source-code mutation. Each
operator injects one focused historical or representative defect into a known-good
fixture, then asks the canonical owner/oracle to detect or contain it.
"""
from __future__ import annotations

import argparse
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
CORPUS_PATH = ROOT / "assets" / "failure-corpus" / "failure-cases.json"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compile_context import compile_pack  # type: ignore
from semantic_kernel import verify_project as verify_semantic_kernel  # type: ignore


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def save_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n" for x in rows), encoding="utf-8")


def load_corpus() -> dict[str, Any]:
    raw = load_json(CORPUS_PATH)
    if not isinstance(raw, dict) or not isinstance(raw.get("cases"), list):
        raise ValueError("failure corpus must be an object with a cases list")
    return raw


def project_manifest(root: Path) -> dict[str, Any]:
    raw = load_json(root / "project-manifest.json")
    if not isinstance(raw, dict):
        raise ValueError("project-manifest.json must be an object")
    return raw


def canonical_path(root: Path, key: str, fallback: str | None = None) -> Path:
    manifest = project_manifest(root)
    paths = manifest.get("canonical_paths", {})
    rel = paths.get(key) if isinstance(paths, dict) else None
    if not isinstance(rel, str):
        if fallback is None:
            raise ValueError(f"project has no canonical path for {key}")
        rel = fallback
    return root / rel


def context_request_path(root: Path) -> Path:
    candidates = [
        root / "context" / "writer-request-ch2.json",
        root / "context" / "writer-request.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise ValueError("no Writer context request fixture found")


def compile_fixture(root: Path) -> tuple[str, dict[str, Any], list[str]]:
    index_path = canonical_path(root, "context_index", "context/context-index.json")
    index = load_json(index_path)
    req = load_json(context_request_path(root))
    if not isinstance(index, dict) or not isinstance(req, dict):
        raise ValueError("context fixture must contain object index/request")
    return compile_pack(index, req, root)


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], text=True, capture_output=True, cwd=ROOT)


# ---- Mutation operators -------------------------------------------------

def mut_branch_head_drift(root: Path, case: dict[str, Any]) -> list[str]:
    path = root / "project-manifest.json"
    data = load_json(path)
    data["last_committed_event"] = "EV-MUTANT-NOT-HEAD"
    save_json(path, data)
    return ["project-manifest.json:last_committed_event"]


def mut_runtime_project_id_drift(root: Path, case: dict[str, Any]) -> list[str]:
    path = canonical_path(root, "runtime_manifest", "runtime/runtime-manifest.json")
    data = load_json(path)
    data["project_id"] = "MUTATED-PROJECT-ID"
    save_json(path, data)
    return [str(path.relative_to(root)) + ":project_id"]


def mut_prose_only_canon_delta(root: Path, case: dict[str, Any]) -> list[str]:
    path = next((root / "revisions").rglob("impact.json"))
    data = load_json(path)
    change = data["changes"][0]
    change["impact_labels"] = ["PROSE_ONLY"]
    change["candidate_deltas"] = [{"target": "loop.iteration", "before": 7, "after": 8}]
    data["approval_status"] = "PROSE_ONLY_CONFIRMED"
    save_json(path, data)
    return [str(path.relative_to(root)) + ":changes[0]"]


def mut_missing_context_parent(root: Path, case: dict[str, Any]) -> list[str]:
    path = canonical_path(root, "context_index", "context/context-index.json")
    data = load_json(path)
    data.setdefault("entries", []).append({
        "id": "mutant-missing-parent",
        "path": "context/chapter-002-writer-mission.md",
        "kind": "summary",
        "priority": 1,
        "required": False,
        "roles": ["writer"],
        "visibility": "writer-visible",
        "branch": "main",
        "derived_from": ["FC-MISSING-PARENT"],
        "tainted_by": [],
        "declassified_for": [],
    })
    save_json(path, data)
    return [str(path.relative_to(root)) + ":mutant-missing-parent"]


def mut_cross_branch_context_leak(root: Path, case: dict[str, Any]) -> list[str]:
    path = canonical_path(root, "context_index", "context/context-index.json")
    data = load_json(path)
    data.setdefault("entries", []).extend([
        {
            "id": "mutant-loop-b-source",
            "path": "context/backend-truth.md",
            "kind": "background",
            "priority": 1,
            "required": False,
            "roles": ["director"],
            "visibility": "backend-hidden",
            "branch": "loop-b",
            "derived_from": [],
            "tainted_by": [],
            "declassified_for": [],
        },
        {
            "id": "mutant-illegal-main-derivative",
            "path": "context/writer-summary.md",
            "kind": "summary",
            "priority": 1,
            "required": False,
            "roles": ["writer"],
            "visibility": "writer-visible",
            "branch": "main",
            "derived_from": ["mutant-loop-b-source"],
            "tainted_by": [],
            "declassified_for": [],
        },
    ])
    save_json(path, data)
    return [str(path.relative_to(root)) + ":branch-provenance"]


def mut_collapse_open_unknown(root: Path, case: dict[str, Any]) -> list[str]:
    path = canonical_path(root, "story_state", "state/story-state.json")
    data = load_json(path)
    data.setdefault("authorial_unknowns", []).append({
        "id": "MUTANT-UNKNOWN-01",
        "question_id": "MUTANT-UNKNOWN-01",
        "status": "open",
        "selected_answer": "silently-fixed",
    })
    save_json(path, data)
    return [str(path.relative_to(root)) + ":authorial_unknowns"]


def _base_open_issue(qid: str) -> dict[str, Any]:
    return {
        "record_version": "2.0.0",
        "mode": "OPEN_ISSUE",
        "question_id": qid,
        "question": "Why did she leave?",
        "state": "open",
        "resolution_policy": "may_resolve",
        "resolution_criterion": "Choose the direct causal trigger only when required.",
        "decision_authority": {"owner_type": "user", "delegation_ref": None},
        "decision_horizon": None,
        "domain_semantics": "open_ended",
        "constraints": [],
        "positions": [],
        "clue_refs": [],
        "resolution": None,
        "retirement": None,
    }


def mut_launder_working_hypothesis(root: Path, case: dict[str, Any]) -> list[str]:
    path = canonical_path(root, "story_state", "state/story-state.json")
    data = load_json(path)
    issue = _base_open_issue("MUTANT-OI-LAUNDER")
    issue["positions"] = [{
        "position_id": "MUTANT-H1",
        "claim_id": None,
        "statement": "The departure may be connected to her father.",
        "viability": "viable",
        "planning_stance": "working_hypothesis",
        "provenance_ref": "MUTANT-USER-MAYBE",
        "exclusion_basis_ref": None,
    }]
    issue["constraints"] = [{
        "constraint_id": "MUTANT-C1",
        "statement": "The departure is connected to her father.",
        "status": "active",
        "basis_kind": "working_hypothesis",
        "basis_ref": "MUTANT-H1",
    }]
    data.setdefault("authorial_unknowns", []).append(issue)
    save_json(path, data)
    return [str(path.relative_to(root)) + ":working-hypothesis-laundering"]


def mut_excluded_working_hypothesis(root: Path, case: dict[str, Any]) -> list[str]:
    path = canonical_path(root, "story_state", "state/story-state.json")
    data = load_json(path)
    issue = _base_open_issue("MUTANT-OI-EXCLUDED-WORKING")
    issue["positions"] = [{
        "position_id": "MUTANT-H2",
        "claim_id": None,
        "statement": "The departure was caused by debt.",
        "viability": "excluded",
        "planning_stance": "working_hypothesis",
        "provenance_ref": "MUTANT-IDEA",
        "exclusion_basis_ref": "MUTANT-AUTHOR-EXCLUDE",
    }]
    data.setdefault("authorial_unknowns", []).append(issue)
    save_json(path, data)
    return [str(path.relative_to(root)) + ":excluded-working-hypothesis"]


def mut_active_dependency_on_excluded_hypothesis(root: Path, case: dict[str, Any]) -> list[str]:
    state_path = canonical_path(root, "story_state", "state/story-state.json")
    state = load_json(state_path)
    issue = _base_open_issue("MUTANT-OI-EXCLUDED-DEPENDENCY")
    issue["positions"] = [{
        "position_id": "MUTANT-H-EXCLUDED",
        "claim_id": None,
        "statement": "A discarded explanation remains wired into planning.",
        "viability": "excluded",
        "planning_stance": "parked",
        "provenance_ref": "MUTANT-IDEA",
        "exclusion_basis_ref": "MUTANT-AUTHOR-EXCLUDE",
    }]
    state.setdefault("authorial_unknowns", []).append(issue)
    save_json(state_path, state)

    rmanifest = load_json(canonical_path(root, "runtime_manifest", "runtime/runtime-manifest.json"))
    dep_path = root / rmanifest["paths"]["dependencies"]
    deps = load_json(dep_path)
    deps.setdefault("edges", []).append({
        "source": "MUTANT-H-EXCLUDED",
        "target": "MUTANT-CONDITIONAL-PLAN",
        "kind": "conditional-on-hypothesis",
        "strength": "hard",
        "status": "active",
        "reason": "mutation: excluded hypothesis still supports active planning",
    })
    save_json(dep_path, deps)
    return [
        str(state_path.relative_to(root)) + ":excluded-hypothesis",
        str(dep_path.relative_to(root)) + ":conditional-on-hypothesis",
    ]


def mut_writer_open_issue_candidates(root: Path, case: dict[str, Any]) -> list[str]:
    index_path = canonical_path(root, "context_index", "context/context-index.json")
    data = load_json(index_path)
    raw_path = root / "context" / "mutant-open-issue-candidates.md"
    raw_path.write_text("H1 father debt\nH2 father illness\n", encoding="utf-8")
    data.setdefault("entries", []).append({
        "id": "mutant-open-issue-candidates",
        "path": "context/mutant-open-issue-candidates.md",
        "kind": "open-issue-candidates",
        "priority": 999,
        "required": False,
        "roles": ["writer"],
        "visibility": "writer-visible",
        "branch": "main",
    })
    save_json(index_path, data)
    request_path = root / "context" / "writer-request-ch2.json"
    req = load_json(request_path)
    req.setdefault("required_ids", []).append("mutant-open-issue-candidates")
    save_json(request_path, req)
    return [str(index_path.relative_to(root)) + ":mutant-open-issue-candidates", str(request_path.relative_to(root)) + ":required_ids"]


def mut_stale_reconciliation(root: Path, case: dict[str, Any]) -> list[str]:
    report = next((root / "reconciliations").glob("*.json"))
    data = load_json(report)
    prose = root / str(data["prose_path"])
    prose.write_text(prose.read_text(encoding="utf-8") + "\n<!-- mutation -->\n", encoding="utf-8")
    return [str(prose.relative_to(root))]


def mut_invalid_declassification(root: Path, case: dict[str, Any]) -> list[str]:
    path = canonical_path(root, "context_index", "context/context-index.json")
    data = load_json(path)
    target = next(x for x in data["entries"] if x.get("id") == "writer-summary")
    target["declassification"] = {"secret_ids": ["SECRET-NOT-CARRIED"], "roles": ["writer"]}
    save_json(path, data)
    return [str(path.relative_to(root)) + ":writer-summary.declassification"]


def mut_duplicate_event_seq(root: Path, case: dict[str, Any]) -> list[str]:
    rmanifest = load_json(canonical_path(root, "runtime_manifest", "runtime/runtime-manifest.json"))
    events_path = root / rmanifest["paths"]["events"]
    rows = load_jsonl(events_path)
    if len(rows) < 2:
        raise ValueError("operator requires at least two events")
    rows[1]["seq"] = rows[0]["seq"]
    save_jsonl(events_path, rows)
    return [str(events_path.relative_to(root)) + ":event[1].seq"]


def mut_missing_fork_event(root: Path, case: dict[str, Any]) -> list[str]:
    rmanifest = load_json(canonical_path(root, "runtime_manifest", "runtime/runtime-manifest.json"))
    path = root / rmanifest["paths"]["branches"]
    data = load_json(path)
    branches = data.get("branches", data)
    child = next((v for v in branches.values() if isinstance(v, dict) and v.get("parent")), None)
    if child is None:
        raise ValueError("operator requires a child branch")
    child["fork_event"] = "EV-MUTANT-MISSING-FORK"
    save_json(path, data)
    return [str(path.relative_to(root)) + ":fork_event"]


def mut_drop_context_canonical_path(root: Path, case: dict[str, Any]) -> list[str]:
    path = root / "project-manifest.json"
    data = load_json(path)
    data.get("canonical_paths", {}).pop("context_index", None)
    save_json(path, data)
    return ["project-manifest.json:canonical_paths.context_index"]


def mut_forbidden_writer_leak(root: Path, case: dict[str, Any]) -> list[str]:
    path = root / "context" / "chapter-002-writer-mission.md"
    if not path.is_file():
        raise ValueError("operator requires chapter-002-writer-mission.md")
    path.write_text(path.read_text(encoding="utf-8") + "\n水质事件\n", encoding="utf-8")
    return [str(path.relative_to(root))]


def mut_stale_embedded_dependencies(root: Path, case: dict[str, Any]) -> list[str]:
    path = canonical_path(root, "story_state", "state/story-state.json")
    data = load_json(path)
    data["dependencies"] = [{"source": "SCN-002", "target": "MUTANT-WRONG-TARGET", "kind": "causal", "status": "active"}]
    save_json(path, data)
    return [str(path.relative_to(root)) + ":dependencies"]


def mut_missing_active_optional_artifact(root: Path, case: dict[str, Any]) -> list[str]:
    """Declare a project-specific optional capability artifact active, then omit its file.

    The project doctor should reject the declared active obligation without turning
    all optional planning artifacts into universal requirements.
    """
    path = root / "project-manifest.json"
    data = load_json(path)
    data.setdefault("optional_artifacts", []).append({
        "kind": "hidden-causal-network",
        "path": "planning/05-hidden-causal-network.md",
        "status": "active",
        "scope": "project",
        "reason": "mutation: active artifact declared but missing",
    })
    save_json(path, data)
    return ["project-manifest.json:optional_artifacts"]


def mut_duplicate_context_alias(root: Path, case: dict[str, Any]) -> list[str]:
    path = canonical_path(root, "context_index", "context/context-index.json")
    data = load_json(path)
    entries = data.get("entries", [])
    source = next((x for x in entries if x.get("id") == "writer-craft"), None)
    if source is None:
        source = next((x for x in entries if x.get("roles") == ["writer"] and x.get("path")), None)
    if source is None:
        raise ValueError("operator requires an eligible Writer context entry")
    clone = dict(source)
    clone["id"] = "mutant-writer-context-alias"
    entries.append(clone)
    save_json(path, data)
    return [str(path.relative_to(root)) + ":mutant-writer-context-alias"]


def mut_regime_intervention(root: Path, case: dict[str, Any]) -> list[str]:
    source = (root / "control-preserving.md").read_text(encoding="utf-8")
    (root / "candidate.md").write_text(source + "\n\n" + case["detector"]["intervention"] + "\n", encoding="utf-8")
    return ["candidate.md"]


MUTATORS: dict[str, Callable[[Path, dict[str, Any]], list[str]]] = {
    "regime-intervention": mut_regime_intervention,
    "branch-head-drift": mut_branch_head_drift,
    "runtime-project-id-drift": mut_runtime_project_id_drift,
    "prose-only-canon-delta": mut_prose_only_canon_delta,
    "missing-context-parent": mut_missing_context_parent,
    "cross-branch-context-leak": mut_cross_branch_context_leak,
    "collapse-open-unknown": mut_collapse_open_unknown,
    "launder-working-hypothesis": mut_launder_working_hypothesis,
    "excluded-working-hypothesis": mut_excluded_working_hypothesis,
    "active-dependency-on-excluded-hypothesis": mut_active_dependency_on_excluded_hypothesis,
    "writer-open-issue-candidates": mut_writer_open_issue_candidates,
    "stale-reconciliation-evidence": mut_stale_reconciliation,
    "invalid-declassification": mut_invalid_declassification,
    "duplicate-event-seq": mut_duplicate_event_seq,
    "missing-fork-event": mut_missing_fork_event,
    "drop-context-canonical-path": mut_drop_context_canonical_path,
    "forbidden-writer-leak": mut_forbidden_writer_leak,
    "stale-embedded-dependencies": mut_stale_embedded_dependencies,
    "duplicate-context-alias": mut_duplicate_context_alias,
    "missing-active-optional-artifact": mut_missing_active_optional_artifact,
}


# ---- Oracles ------------------------------------------------------------

def semantic_clean(root: Path) -> tuple[bool, dict[str, Any]]:
    report = verify_semantic_kernel(root)
    return int(report.get("summary", {}).get("fail", 0)) == 0, report


def project_verify(root: Path) -> tuple[bool, dict[str, Any]]:
    manifest = root / "project-manifest.json"
    proc = run_cli([str(SCRIPT_DIR / "project_ops.py"), "verify", str(manifest), "--root", str(root), "--json"])
    payload: dict[str, Any]
    try:
        payload = json.loads(proc.stdout or "{}")
    except Exception:
        payload = {"stdout": proc.stdout, "stderr": proc.stderr}
    payload["returncode"] = proc.returncode
    return proc.returncode == 0, payload


def dependency_authority(root: Path, detector: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    state = canonical_path(root, "story_state", "state/story-state.json")
    node = str(detector["node"])
    target = str(detector["expected_target"])
    proc = run_cli([str(SCRIPT_DIR / "story_ops.py"), str(state), "propagate", node, "--json"])
    try:
        rows = json.loads(proc.stdout or "[]")
    except Exception:
        rows = []
    found = any(isinstance(x, dict) and str(x.get("target")) == target for x in rows if isinstance(rows, list))
    return proc.returncode == 0 and found, {"returncode": proc.returncode, "rows": rows, "stderr": proc.stderr}


def baseline_ok(case: dict[str, Any], root: Path) -> tuple[bool, dict[str, Any]]:
    kind = str(case.get("detector", {}).get("kind"))
    if kind == "poetics-preservation":
        return regime_candidate(root, "control-preserving.md")
    if kind in {"semantic-law", "semantic-law-any"}:
        return semantic_clean(root)
    if kind == "project-verify-reject":
        return project_verify(root)
    if kind in {"context-compile-reject", "context-openissue-block", "context-dedup"}:
        try:
            _pack, manifest, errors = compile_fixture(root)
        except Exception as exc:
            return False, {"exception": str(exc)}
        return not errors, {"errors": errors, "manifest": manifest}
    if kind == "runtime-dependency-authority":
        return dependency_authority(root, case["detector"])
    return False, {"error": f"unknown detector kind: {kind}"}


def detect_mutant(case: dict[str, Any], root: Path) -> tuple[bool, dict[str, Any]]:
    detector = case.get("detector", {})
    kind = str(detector.get("kind"))
    if kind == "poetics-preservation":
        clean, evidence = regime_candidate(root, "candidate.md")
        return not clean, evidence
    if kind in {"semantic-law", "semantic-law-any"}:
        report = verify_semantic_kernel(root)
        failed = {str(x.get("law")) for x in report.get("laws", []) if x.get("status") == "fail"}
        if kind == "semantic-law":
            expected = {str(detector["law"])}
        else:
            expected = {str(x) for x in detector.get("laws", [])}
        return bool(failed & expected), {"expected": sorted(expected), "failed_laws": sorted(failed), "summary": report.get("summary")}
    if kind == "project-verify-reject":
        clean, payload = project_verify(root)
        return not clean, payload
    if kind == "context-compile-reject":
        try:
            _pack, manifest, errors = compile_fixture(root)
        except Exception as exc:
            return True, {"exception": str(exc)}
        expected = [x for x in errors if "forbidden-term leakage" in x]
        return bool(expected), {"errors": errors, "excluded": manifest.get("excluded", [])}
    if kind == "context-openissue-block":
        try:
            _pack, manifest, errors = compile_fixture(root)
        except Exception as exc:
            return True, {"exception": str(exc)}
        excluded = [x for x in manifest.get("excluded", []) if isinstance(x, dict)]
        hit = next((x for x in excluded if x.get("id") == "mutant-open-issue-candidates" and x.get("reason") == "open-issue-backend-blocked"), None)
        expected_error = any("mutant-open-issue-candidates" in x and "open-issue-backend-blocked" in x for x in errors)
        return bool(hit is not None and expected_error), {"errors": errors, "hit": hit}
    if kind == "context-dedup":
        try:
            _pack, manifest, errors = compile_fixture(root)
        except Exception as exc:
            return False, {"exception": str(exc)}
        excluded = [x for x in manifest.get("excluded", []) if isinstance(x, dict)]
        hit = next((x for x in excluded if x.get("id") == "mutant-writer-context-alias" and str(x.get("reason", "")).startswith("duplicate-")), None)
        included_ids = {str(x.get("id")) for x in manifest.get("included", []) if isinstance(x, dict)}
        return not errors and hit is not None and "mutant-writer-context-alias" not in included_ids, {"errors": errors, "hit": hit, "included_ids": sorted(included_ids)}
    if kind == "runtime-dependency-authority":
        return dependency_authority(root, detector)
    return False, {"error": f"unknown detector kind: {kind}"}


def regime_candidate(root: Path, filename: str) -> tuple[bool, dict[str, Any]]:
    from multi_poetics_oracle import run_assertion
    contract = load_json(root / "oracle.json")
    source = (root / contract["refs"]["input"]).read_text(encoding="utf-8")
    candidate = (root / filename).read_text(encoding="utf-8")
    checks = []
    for assertion in contract["deterministic_assertions"]:
        passed, detail = run_assertion(assertion, candidate, source)
        checks.append({"id": assertion["id"], "passed": passed, "critical": assertion.get("critical", False), "detail": detail})
    return all(x["passed"] for x in checks if x["critical"]), {"checks": checks, "claim_boundary": "Known mechanical boundary only; paraphrased or subtle contamination needs independent judging."}


def digest_tree(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(x for x in root.rglob("*") if x.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        h.update(len(rel).to_bytes(4, "big")); h.update(rel)
        blob = path.read_bytes(); h.update(len(blob).to_bytes(8, "big")); h.update(blob)
    return h.hexdigest()


def validate_corpus(corpus: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    cases = [x for x in corpus.get("cases", []) if isinstance(x, dict)]
    ids: list[str] = [str(x.get("id")) for x in cases]
    if len(ids) != len(set(ids)):
        errors.append("failure corpus contains duplicate case IDs")
    by_id = {str(x.get("id")): x for x in cases}
    automated_signatures: set[str] = set()
    for case in cases:
        cid = str(case.get("id", ""))
        if not cid.startswith("FC-"):
            errors.append(f"{cid or '?'}: invalid stable case ID")
        owner = case.get("owner")
        if not isinstance(owner, str) or not (ROOT / owner).is_file():
            errors.append(f"{cid}: owner reference missing: {owner}")
        mode = case.get("automation")
        if mode == "automated":
            seed = case.get("seed")
            op = case.get("operator")
            detector = case.get("detector")
            if not isinstance(seed, str) or not (ROOT / seed).is_dir():
                errors.append(f"{cid}: automated seed missing: {seed}")
            if op not in MUTATORS:
                errors.append(f"{cid}: unknown mutation operator: {op}")
            if not isinstance(detector, dict) or not detector.get("kind"):
                errors.append(f"{cid}: automated case lacks detector")
            signature = json.dumps([seed, op, detector], ensure_ascii=False, sort_keys=True)
            if signature in automated_signatures:
                errors.append(f"{cid}: duplicate automated mutant signature would inflate mutation score")
            automated_signatures.add(signature)
        elif mode == "documented":
            if case.get("operator") is not None or case.get("detector") is not None:
                errors.append(f"{cid}: documented-only case must not masquerade as automated")
            auto_by = case.get("automated_by")
            if auto_by is not None:
                target = by_id.get(str(auto_by))
                if not isinstance(target, dict) or target.get("automation") != "automated":
                    errors.append(f"{cid}: automated_by does not name an automated case: {auto_by}")
        else:
            errors.append(f"{cid}: automation must be documented or automated")
    return errors


def selected_cases(corpus: dict[str, Any], only: list[str], category: str | None) -> list[dict[str, Any]]:
    rows = [x for x in corpus.get("cases", []) if isinstance(x, dict) and x.get("automation") == "automated"]
    if category:
        rows = [x for x in rows if str(x.get("category")) == category]
    if only:
        needles = [x.lower() for x in only]
        rows = [x for x in rows if any(n in (str(x.get("id")) + " " + str(x.get("title")) + " " + str(x.get("operator"))).lower() for n in needles)]
    return rows


def run_case(case: dict[str, Any], keep_survivors: Path | None = None) -> dict[str, Any]:
    seed = ROOT / str(case["seed"])
    with tempfile.TemporaryDirectory(prefix=f"lwa-mut-{case['id'].lower()}-") as tmp:
        root = Path(tmp) / "project"
        shutil.copytree(seed, root)
        baseline_hash = digest_tree(root)
        clean, baseline = baseline_ok(case, root)
        if not clean:
            return {"id": case["id"], "title": case["title"], "status": "INVALID_BASELINE", "operator": case["operator"], "baseline": baseline}
        touched = MUTATORS[str(case["operator"])](root, case)
        mutant_hash = digest_tree(root)
        if mutant_hash == baseline_hash:
            return {"id": case["id"], "title": case["title"], "status": "INVALID_MUTANT", "operator": case["operator"], "touched": touched, "reason": "operator did not change fixture bytes"}
        killed, evidence = detect_mutant(case, root)
        status = "KILLED" if killed else "SURVIVED"
        result = {
            "id": case["id"],
            "title": case["title"],
            "category": case.get("category"),
            "status": status,
            "operator": case["operator"],
            "detector": case["detector"],
            "touched": touched,
            "baseline_sha256": baseline_hash,
            "mutant_sha256": mutant_hash,
            "evidence": evidence,
        }
        if status == "SURVIVED" and keep_survivors is not None:
            out = keep_survivors / str(case["id"])
            if out.exists():
                shutil.rmtree(out)
            shutil.copytree(root, out)
            result["survivor_path"] = str(out)
        return result


def cmd_validate(as_json: bool) -> int:
    corpus = load_corpus()
    errors = validate_corpus(corpus)
    payload = {
        "corpus_version": corpus.get("corpus_version"),
        "case_count": len(corpus.get("cases", [])),
        "automated_count": sum(1 for x in corpus.get("cases", []) if isinstance(x, dict) and x.get("automation") == "automated"),
        "documented_count": sum(1 for x in corpus.get("cases", []) if isinstance(x, dict) and x.get("automation") == "documented"),
        "errors": errors,
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if errors:
            for x in errors: print(f"ERROR: {x}")
        else:
            print(f"OK: failure corpus valid ({payload['case_count']} cases; {payload['automated_count']} automated, {payload['documented_count']} documented)")
    return 1 if errors else 0


def cmd_catalog(as_json: bool) -> int:
    corpus = load_corpus()
    errors = validate_corpus(corpus)
    if errors:
        for x in errors: print(f"ERROR: {x}", file=sys.stderr)
        return 1
    rows = corpus["cases"]
    if as_json:
        print(json.dumps({"corpus_version": corpus.get("corpus_version"), "cases": rows}, ensure_ascii=False, indent=2))
    else:
        for case in rows:
            suffix = f" -> {case.get('automated_by')}" if case.get("automated_by") else ""
            print(f"{case['id']} [{case['automation']}] [{case['category']}] {case['title']}{suffix}")
    return 0


def cmd_stats(as_json: bool) -> int:
    corpus = load_corpus(); cases = [x for x in corpus["cases"] if isinstance(x, dict)]
    by_cat: dict[str, int] = {}
    for c in cases: by_cat[str(c.get("category"))] = by_cat.get(str(c.get("category")), 0) + 1
    payload = {
        "corpus_version": corpus.get("corpus_version"),
        "case_count": len(cases),
        "automated_count": sum(c.get("automation") == "automated" for c in cases),
        "documented_count": sum(c.get("automation") == "documented" for c in cases),
        "categories": dict(sorted(by_cat.items())),
    }
    if as_json: print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"failure corpus {payload['corpus_version']}: {payload['case_count']} cases; {payload['automated_count']} automated; {payload['documented_count']} documented")
        for k,v in payload["categories"].items(): print(f"  {k}: {v}")
    return 0


def cmd_run(only: list[str], category: str | None, as_json: bool, keep_survivors: Path | None) -> int:
    corpus = load_corpus()
    errors = validate_corpus(corpus)
    if errors:
        payload = {"errors": errors, "results": []}
        if as_json: print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            for x in errors: print(f"ERROR: {x}")
        return 2
    rows = selected_cases(corpus, only, category)
    if not rows:
        print("no automated failure cases matched", file=sys.stderr)
        return 2
    if keep_survivors is not None:
        keep_survivors.mkdir(parents=True, exist_ok=True)
    results = [run_case(case, keep_survivors) for case in rows]
    killed = sum(x["status"] == "KILLED" for x in results)
    survived = sum(x["status"] == "SURVIVED" for x in results)
    invalid = sum(str(x["status"]).startswith("INVALID") for x in results)
    denominator = killed + survived
    score = killed / denominator if denominator else None
    payload = {
        "corpus_version": corpus.get("corpus_version"),
        "automated_selected": len(rows),
        "killed": killed,
        "survived": survived,
        "invalid": invalid,
        "mutation_score": score,
        "promotion_gate": "PASS" if survived == 0 and invalid == 0 else "FAIL",
        "results": results,
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for row in results:
            print(f"{row['status']:<16} {row['id']} {row['operator']}: {row['title']}")
        score_s = "n/a" if score is None else f"{score:.3f}"
        print(f"summary: killed={killed} survived={survived} invalid={invalid} mutation_score={score_s} promotion_gate={payload['promotion_gate']}")
    return 0 if payload["promotion_gate"] == "PASS" else 1


def cmd_reproduce(case_id: str, out: Path, as_json: bool) -> int:
    corpus = load_corpus(); errors = validate_corpus(corpus)
    if errors:
        for x in errors: print(f"ERROR: {x}", file=sys.stderr)
        return 2
    case = next((x for x in corpus["cases"] if isinstance(x, dict) and x.get("id") == case_id), None)
    if not isinstance(case, dict):
        print(f"unknown failure case: {case_id}", file=sys.stderr); return 2
    if case.get("automation") != "automated":
        print(f"failure case {case_id} is documented-only; no deterministic reproducer is registered", file=sys.stderr); return 2
    if out.exists():
        print(f"output already exists: {out}", file=sys.stderr); return 2
    root = out / "project"
    shutil.copytree(ROOT / str(case["seed"]), root)
    clean, baseline = baseline_ok(case, root)
    if not clean:
        print(f"baseline is invalid for {case_id}", file=sys.stderr); return 2
    touched = MUTATORS[str(case["operator"])](root, case)
    killed, evidence = detect_mutant(case, root)
    meta = {
        "failure_case": case,
        "touched": touched,
        "detector_killed": killed,
        "evidence": evidence,
        "note": "This directory is a deterministic fault-injected reproducer. Minimize further before adding a new permanent fixture if unrelated bytes are not required.",
    }
    save_json(out / "reproducer.json", meta)
    if as_json: print(json.dumps(meta, ensure_ascii=False, indent=2))
    else: print(out)
    return 0 if killed else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("validate", help="validate failure-corpus structure, owners, seeds, operators, and duplicate mutant signatures")
    q.add_argument("--json", action="store_true")
    q = sub.add_parser("catalog", help="list durable historical failure cases")
    q.add_argument("--json", action="store_true")
    q = sub.add_parser("stats", help="summarize corpus coverage")
    q.add_argument("--json", action="store_true")
    q = sub.add_parser("run", help="fault-inject automated cases and measure whether canonical oracles kill/contain them")
    q.add_argument("--only", action="append", default=[], help="filter by case ID/title/operator substring; repeatable")
    q.add_argument("--category")
    q.add_argument("--json", action="store_true")
    q.add_argument("--keep-survivors", type=Path, help="copy surviving mutant projects here for debugging")
    q = sub.add_parser("reproduce", help="materialize one deterministic mutated project for debugging/minimization")
    q.add_argument("case_id")
    q.add_argument("out", type=Path)
    q.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.cmd == "validate": return cmd_validate(args.json)
    if args.cmd == "catalog": return cmd_catalog(args.json)
    if args.cmd == "stats": return cmd_stats(args.json)
    if args.cmd == "run": return cmd_run(args.only, args.category, args.json, args.keep_survivors)
    if args.cmd == "reproduce": return cmd_reproduce(args.case_id, args.out, args.json)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
