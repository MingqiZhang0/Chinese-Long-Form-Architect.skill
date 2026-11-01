#!/usr/bin/env python3
"""Multi-regime evidence mechanics under the existing behavioral-evaluation owner.

Selftests run real scoped compilation and canonical readiness. They never claim
that a model has generated acceptable literature. Stage campaigns use the
existing multi_poetics_oracle CLI with --stage before the subcommand.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import multi_poetics_oracle as oracle
from compile_context import compile_pack
from scoped_poetics import build_envelope
from readiness_selftest import test_poetics_dependencies

ROOT = Path(__file__).resolve().parents[1]


def context_checks() -> dict:
    """M1-M3 demonstrate context propagation, not reader/literary effects."""
    pairs = [
        ("witness-sensitive-social", "Same public statement; colleague witnesses it.", "Same public statement; patron witnesses it.", "public statement"),
        ("narrating-age-memory", "At age 20 the loan is recalled as generosity.", "At age 60 the same loan is recalled as dependence.", "loan was made"),
        ("object-relation", "The dented plate is admired as a model.", "The same dented plate now invites comparison and shame.", "plate has one dent"),
    ]
    rows = []
    with tempfile.TemporaryDirectory(prefix="lwa-regime-context-") as td:
        root = Path(td)
        (root / "poetics.md").write_text("Project authority permits the declared local changes; facts remain stable.", encoding="utf-8")
        (root / "project-manifest.json").write_text(json.dumps({"project_id": "TEST", "canonical_paths": {"project_poetics": "poetics.md"}}), encoding="utf-8")
        for name, before, after, fact in pairs:
            packs = []
            for filename in ("active-cap.md", "inactive-cap.md"):
                (root / filename).write_text(filename, encoding="utf-8")
            (root / "fact.md").write_text(fact, encoding="utf-8")
            fact_hash = hashlib.sha256((root / "fact.md").read_bytes()).hexdigest()
            for local in (before, after):
                (root / "scope.md").write_text(local, encoding="utf-8")
                env = build_envelope(root=root, content_ref="scope.md", authority_ref="poetics.md", parent_ref="poetics.md", scope={"project_id": "TEST", "chapter": 1, "scene": name}, status="active", expires_at=None)
                (root / "scope.envelope.json").write_text(json.dumps(env), encoding="utf-8")
                idx = {"entries": [{"id": "fact", "path": "fact.md", "kind": "character", "roles": ["writer"], "visibility": "writer-visible"},
                    {"id": "active-cap", "path": "active-cap.md", "kind": "poetics-capability", "poetics_capabilities": [name], "roles": ["writer"], "visibility": "writer-visible"},
                    {"id": "inactive-cap", "path": "inactive-cap.md", "kind": "poetics-capability", "poetics_capabilities": ["unrelated"], "roles": ["writer"], "visibility": "writer-visible"}]}
                req = {"project_manifest": "project-manifest.json", "role": "writer", "target_chapter": 1, "target_scene": name, "budget_tokens": 1000, "active_capabilities": [name], "required_ids": ["fact", "active-cap"], "strict_visibility": True, "scoped_project_poetics_ref": "scope.md", "scoped_project_poetics_envelope_ref": "scope.envelope.json"}
                pack, manifest, errors = compile_pack(idx, req, root)
                if errors or local not in pack or fact not in pack:
                    raise AssertionError(f"{name}: propagation failed: {errors}")
                if "inactive-cap.md" in pack or "active-cap.md" not in pack:
                    raise AssertionError(f"{name}: inactive capability contamination")
                blocked_request = dict(req, required_ids=["fact", "inactive-cap"])
                _blocked_pack, _blocked_manifest, blocked_errors = compile_pack(idx, blocked_request, root)
                if not any("inactive-poetics-capability" in x for x in blocked_errors):
                    raise AssertionError("explicit required inactive capability was silently admitted")
                packs.append(pack)
            if packs[0] == packs[1] or hashlib.sha256((root / "fact.md").read_bytes()).hexdigest() != fact_hash:
                raise AssertionError(f"{name}: changed context erased invariant fact")
            rows.append({"id": name, "passed": True, "source": {"scope": before, "fact_sha256": fact_hash}, "followup": {"scope": after, "fact_sha256": fact_hash}, "claim": "authorized context changes; physical/event fact bytes stay unchanged; inactive capabilities are excluded"})
    return {"passed": True, "relations": rows, "claim_boundary": "Semantic effects on generated consequences/interpretation require the model metamorphic campaign, not this compiler selftest."}


def selftest() -> dict:
    saved_stage = oracle.STAGE
    reports = {}
    try:
        for stage in (None, "planning", "chapter", "drafting"):
            oracle.STAGE = stage
            reports[stage or "revision"] = oracle.selftest()
        context = context_checks()
        test_poetics_dependencies()
    finally:
        oracle.STAGE = saved_stage
    errors = [stage for stage, result in reports.items() if not result["passed"]]
    return {"passed": not errors, "stages": reports, "context_metamorphic": context, "readiness": "PASS: four applicability cases and two openness-laundering controls", "errors": errors, "promotion": "PROVISIONAL", "model_qualification": "NOT RUN", "claim_boundary": "Passing control/manually authored mutant checks proves harness mechanics only. Planning, chapter, drafting and revision model qualifications remain pending."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "selftest"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.command == "selftest":
        result = selftest()
    else:
        saved = oracle.STAGE
        try:
            results = {}
            for stage in (None, "planning", "chapter", "drafting"):
                oracle.STAGE = stage
                results[stage or "revision"] = oracle.validate_suite()
            result = {"passed": all(r["passed"] for r in results.values()), "stages": results}
        finally:
            oracle.STAGE = saved
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
