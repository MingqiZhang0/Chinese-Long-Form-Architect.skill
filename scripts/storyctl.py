#!/usr/bin/env python3
"""Unified front controller for the long-form fiction architect tool surface.

This file does not replace the specialized backend scripts. It gives agents one
stable discovery surface and delegates to the canonical implementation for each
operation so there is no second copy of business logic.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent

TOOLS: dict[str, dict[str, Any]] = {
    "status": {
        "script": "project_ops.py", "category": "project", "mutates": False,
        "summary": "Aggregate authoritative readiness, Kernel, manifest and evidence-backed run status.",
    },
    "narrative-regime-qualification": {
        "script": "narrative_regime_qualification.py",
        "category": "maintenance",
        "mutates": "temporary-only",
        "summary": "Validate multi-regime stage contracts and run scoped-context/readiness evidence mechanics; model qualification remains separate.",
    },
    "auditability-core": {
        "script": "auditability_core_test.py",
        "category": "maintenance",
        "mutates": False,
        "summary": "Seven auditability invariants, temporary-project regression and source mutation tests.",
    },
    "capability": {
        "script": "capability_probe.py",
        "category": "startup",
        "mutates": False,
        "summary": "Cheap startup dependency/capability preflight for deterministic tool profiles.",
    },
    "project": {
        "script": "project_ops.py",
        "category": "project",
        "mutates": "mixed",
        "summary": "Project identity, explicit chapter final approval/rollover artifact binding, migration, verification, resume, and governance profile.",
    },
    "readiness": {
        "script": "prewriting_readiness.py",
        "category": "project",
        "mutates": "mixed",
        "summary": "Evidence-backed formal draft permission, refresh/freeze/author approval, live Writer handoff and Chapter 1 campaign session start.",
    },
    "query": {
        "script": "story_ops.py",
        "category": "state",
        "mutates": False,
        "summary": "Read-only deterministic Story State queries.",
    },
    "state-validate": {
        "script": "validate_story_state.py",
        "category": "state",
        "mutates": False,
        "summary": "Mechanical continuity validation for Story State and Scene Packets.",
    },
    "semantics": {
        "script": "semantic_kernel.py",
        "category": "semantics",
        "mutates": False,
        "summary": "Cross-layer Narrative Semantics Kernel laws and project verification.",
    },
    "context": {
        "script": "compile_context.py",
        "category": "context",
        "mutates": "output-only",
        "summary": "Compile least-privilege role-scoped context packs, including approved scoped Project Poetics when declared.",
    },
    "poetics-envelope": {
        "script": "scoped_poetics.py",
        "category": "context",
        "mutates": "output-only",
        "summary": "Create or verify the thin provenance envelope for scoped Project Poetics without schema-ing literary content.",
    },
    "runtime": {
        "script": "narrative_runtime.py",
        "category": "runtime",
        "mutates": "mixed",
        "summary": "Runtime validate/replay/snapshot/impact/branch/merge planning.",
    },
    "transaction": {
        "script": "runtime_tx.py",
        "category": "runtime",
        "mutates": "mixed",
        "summary": "Optimistic-concurrency Runtime transaction status and commit.",
    },
    "schema": {
        "script": "runtime_schema.py",
        "category": "runtime",
        "mutates": "mixed",
        "summary": "Schema validation and representation migration helpers.",
    },
    "invariants": {
        "script": "validate_invariants.py",
        "category": "runtime",
        "mutates": False,
        "summary": "Evaluate project-specific mechanically decidable narrative invariants.",
    },
    "observatory": {
        "script": "story_observatory.py",
        "category": "diagnosis",
        "mutates": "report-only",
        "summary": "Read-only project health and drift observatory.",
    },
    "revision-diff": {
        "script": "revision_diff.py",
        "category": "revision",
        "mutates": "report-only",
        "summary": "Align revisions; optionally retrieve downstream graph witnesses and unindexed chapter prose for semantic impact review.",
    },
    "reconcile": {
        "script": "prose_state_reconcile.py",
        "category": "revision",
        "mutates": "report-only",
        "summary": "Prepare/verify canonical final prose review, publish source-bound rollover receipts, or prove formatting-only no-state-delta.",
    },
    "prose-audit": {
        "script": "prose_surface_audit.py",
        "category": "craft",
        "mutates": False,
        "summary": "Advisory Chinese prose surface diagnostics.",
    },
    "paragraph-audit": {
        "script": "paragraph_profile.py",
        "category": "craft",
        "mutates": False,
        "summary": "Paragraph-architecture diagnostics.",
    },
    "voice-audit": {
        "script": "voice_drift.py",
        "category": "craft",
        "mutates": False,
        "summary": "Voice-drift diagnostics against project samples.",
    },
    "orchestration-profile": {
        "script": "select_orchestration_profile.py",
        "category": "orchestration",
        "mutates": "output-only",
        "summary": "Select an execution profile from observed capabilities.",
    },
    "orchestration-validate": {
        "script": "validate_orchestration_run.py",
        "category": "orchestration",
        "mutates": False,
        "summary": "Validate role/task/write-discipline claims after an orchestration run.",
    },
    "role-bundle": {
        "script": "build_role_pass_bundle.py",
        "category": "orchestration",
        "mutates": "output-only",
        "summary": "Build role-scoped pass bundles.",
    },
    "checkpoint": {
        "script": "orchestration_checkpoint.py",
        "category": "orchestration",
        "mutates": "mixed",
        "summary": "Initialize/update/checkpoint orchestration pass records.",
    },
    "intake-validate": {
        "script": "validate_intake_state.py",
        "category": "orchestration",
        "mutates": False,
        "summary": "Validate adaptive intake state before kickoff.",
    },
    "task-order-validate": {
        "script": "validate_task_order.py",
        "category": "orchestration",
        "mutates": False,
        "summary": "Validate task-order contracts and dependency/write declarations.",
    },
    "intensity": {
        "script": "intensity_runtime.py",
        "category": "orchestration",
        "mutates": False,
        "summary": "Validate Reasoning Intensity contracts and conservatively screen Semantic Work proposals.",
    },
    "pairwise-eval": {
        "script": "aggregate_pairwise_eval.py",
        "category": "maintenance",
        "mutates": "output-only",
        "summary": "Aggregate blinded swapped-order pairwise evaluation results.",
    },
    "chinese-eval": {
        "script": "chinese_narrative_eval.py",
        "category": "maintenance",
        "mutates": "output-only",
        "summary": "Validate and run Chinese narrative behavioral contrast evaluation assets.",
    },
    "activation-eval": {
        "script": "activation_eval.py",
        "category": "maintenance",
        "mutates": "output-only",
        "summary": "Validate the trigger-precision corpus, export blind activation cases, and score observed FP/FN decisions.",
    },
    "multi-poetics-oracle": {
        "script": "multi_poetics_oracle.py",
        "category": "maintenance",
        "mutates": "output-only",
        "summary": "Validate preservation and planning/chapter/drafting Multi-Poetics contracts with deterministic and blinded judge gates.",
    },
    "research-ledger": {
        "script": "research_ledger.py",
        "category": "maintenance",
        "mutates": False,
        "summary": "Validate and query the canonical Skill-wide external research registry.",
    },
    "skill-audit": {
        "script": "audit_skill_structure.py",
        "category": "maintenance",
        "mutates": False,
        "summary": "Audit Skill packaging, ownership, references, and structural hygiene.",
    },
    "workspace-audit": {
        "script": "audit_workspace_changes.py",
        "category": "maintenance",
        "mutates": False,
        "summary": "Audit changed files against role/write-boundary expectations.",
    },
    "benchmark": {
        "script": "long_horizon_benchmark.py",
        "category": "maintenance",
        "mutates": "temporary-or-output",
        "summary": "Run the 60-100 chapter long-horizon continuity benchmark.",
    },
    "stc": {
        "script": "stc_benchmark.py",
        "category": "maintenance",
        "mutates": "temporary-or-output",
        "summary": "Generate STC v0.1 challenges and run independent semantic-conformance, candidate, surface, and assurance checks.",
    },
    "tests": {
        "script": "test_tiers.py",
        "category": "maintenance",
        "mutates": "temporary-only",
        "summary": "Run the canonical Fast/Core/Full/Soak maintenance test tiers.",
    },
    "selftest": {
        "script": "integration_selftest.py",
        "category": "maintenance",
        "mutates": "temporary-only",
        "summary": "Run cross-module deterministic regression tests.",
    },
    "fuzz": {
        "script": "narrative_fuzz.py",
        "category": "maintenance",
        "mutates": "temporary-only",
        "summary": "Run seeded Narrative Runtime property fuzzing.",
    },
    "mutation": {
        "script": "mutation_test.py",
        "category": "maintenance",
        "mutates": "temporary-or-output",
        "summary": "Validate the durable failure corpus and run semantic fault-injection mutation gates.",
    },
    "metamorphic": {
        "script": "metamorphic_benchmark.py",
        "category": "maintenance",
        "mutates": "temporary-only",
        "summary": "Run valid source/follow-up metamorphic and adversarial semantic-relation gates.",
    },
    "campaign": {
        "script": "live_campaign.py",
        "category": "maintenance",
        "mutates": "campaign-evidence-only",
        "summary": "Record and verify real longitudinal 50-300 chapter campaign evidence without confusing it with synthetic stress tests.",
    },
}


CAPABILITY_PROFILES: dict[str, str] = {
    "narrative-regime-qualification": "maintenance",
    "project": "project",
    "readiness": "project",
    "context": "project",
    "poetics-envelope": "project",
    "voice-audit": "project",
    "task-order-validate": "project",
    "runtime": "runtime",
    "transaction": "runtime",
    "schema": "runtime",
    "reconcile": "reconcile",
    "intensity": "intensity",
    "stc": "stc",
    "tests": "maintenance",
    "research-ledger": "maintenance",
    "activation-eval": "maintenance",
    "multi-poetics-oracle": "maintenance",
    "benchmark": "maintenance",
    "campaign": "maintenance",
    "selftest": "maintenance",
}

ROUTES: dict[str, list[dict[str, str]]] = {
    "new-project": [
        {"tool": "project", "example": "project init PROJECT_ROOT --project-id PROJECT-ID"},
        {"tool": "project", "example": "project verify PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT"},
        {"tool": "readiness", "example": "readiness PROJECT_ROOT/project-manifest.json PROJECT_ROOT/planning/prewriting-readiness.json --root PROJECT_ROOT --json"},
    ],
    "resume-project": [
        {"tool": "project", "example": "project verify PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT"},
        {"tool": "project", "example": "project resume PROJECT_ROOT"},
    ],
    "continue-chapter": [
        {"tool": "project", "example": "project verify PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT"},
        {"tool": "context", "example": "context INDEX REQUEST --root PROJECT_ROOT --output WRITER_PACK"},
        {"tool": "state-validate", "example": "state-validate STORY_STATE"},
        {"tool": "runtime", "example": "runtime validate EVENTS BRANCHES --dependencies DEPENDENCIES"},
    ],
    "diagnose-project": [
        {"tool": "project", "example": "project verify PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT"},
        {"tool": "state-validate", "example": "state-validate STORY_STATE"},
        {"tool": "semantics", "example": "semantics verify PROJECT_ROOT"},
        {"tool": "observatory", "example": "observatory --project-manifest PROJECT_MANIFEST --out REPORT"},
    ],
    "revise-canon": [
        {"tool": "revision-diff", "example": "revision-diff BEFORE AFTER --out IMPACT"},
        {"tool": "revision-diff", "example": "revision-diff BEFORE AFTER --out ALIGNMENT --review-root PROJECT_ROOT --dependencies DEPENDENCIES --changed-node REVIEWED_CHANGED_NODE --review-out REVIEW_PACKET"},
        {"tool": "reconcile", "example": "reconcile NEW_REPORT --root PROJECT_ROOT --prepare PROSE --state STATE_SNAPSHOT"},
        {"tool": "reconcile", "example": "reconcile RECONCILIATION --root PROJECT_ROOT --strict"},
        {"tool": "runtime", "example": "runtime impact DEPENDENCIES CHANGED_NODE --json"},
        {"tool": "semantics", "example": "semantics verify PROJECT_ROOT"},
    ],
    "maintain-skill": [
        {"tool": "tests", "example": "tests run fast"},
        {"tool": "tests", "example": "tests run core"},
        {"tool": "multi-poetics-oracle", "example": "multi-poetics-oracle validate --json"},
        {"tool": "tests", "example": "tests plan full"},
        {"tool": "tests", "example": "tests plan soak"},
    ],
}


def emit(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return
    if isinstance(value, str):
        print(value)
        return
    print(json.dumps(value, ensure_ascii=False, indent=2))


def cmd_catalog(as_json: bool) -> int:
    rows = [
        {
            "command": name,
            "category": meta["category"],
            "mutates": meta["mutates"],
            "backend": meta["script"],
            "summary": meta["summary"],
        }
        for name, meta in TOOLS.items()
    ]
    if as_json:
        emit(rows, True)
    else:
        width = max(len(row["command"]) for row in rows)
        for row in rows:
            print(f"{row['command']:<{width}}  [{row['category']}]  {row['summary']}")
    return 0


def route_steps(intent: str, manifest_path: Path | None = None) -> list[dict[str, str]]:
    if manifest_path is None:
        return list(ROUTES[intent])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    enabled = set(str(x) for x in manifest.get("enabled_subsystems", []))
    rows = list(ROUTES[intent])
    if intent == "continue-chapter":
        rows = [{"tool": "project", "example": "project verify PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT"}]
        if "context-compilation" in enabled:
            rows.append({"tool": "context", "example": "context INDEX REQUEST --root PROJECT_ROOT --output WRITER_PACK"})
        rows.append({"tool": "state-validate", "example": "state-validate STORY_STATE"})
        if "prose-state-reconciliation" in enabled:
            rows.append({"tool": "reconcile", "example": "reconcile REPORT --root PROJECT_ROOT --strict"})
        if "narrative-runtime" in enabled:
            rows.append({"tool": "transaction", "example": "transaction commit --events EVENTS --branches BRANCHES --transaction TX"})
            rows.append({"tool": "runtime", "example": "runtime validate EVENTS BRANCHES --dependencies DEPENDENCIES"})
        if "observatory" in enabled:
            rows.append({"tool": "observatory", "example": "observatory --project-manifest PROJECT_MANIFEST --out REPORT"})
    elif intent == "diagnose-project":
        rows = [
            {"tool": "project", "example": "project verify PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT"},
            {"tool": "state-validate", "example": "state-validate STORY_STATE"},
            {"tool": "semantics", "example": "semantics verify PROJECT_ROOT"},
        ]
        if "narrative-runtime" in enabled:
            rows.append({"tool": "runtime", "example": "runtime validate EVENTS BRANCHES --dependencies DEPENDENCIES"})
        if "observatory" in enabled:
            rows.append({"tool": "observatory", "example": "observatory --project-manifest PROJECT_MANIFEST --out REPORT"})
    elif intent == "revise-canon":
        rows = [{"tool": "revision-diff", "example": "revision-diff BEFORE AFTER --out IMPACT"}]
        if "dependency-graph" in enabled:
            rows.append({"tool": "revision-diff", "example": "revision-diff BEFORE AFTER --out ALIGNMENT --review-root PROJECT_ROOT --dependencies DEPENDENCIES --changed-node REVIEWED_CHANGED_NODE --review-out REVIEW_PACKET"})
        if "prose-state-reconciliation" in enabled:
            rows.append({"tool": "reconcile", "example": "reconcile NEW_REPORT --root PROJECT_ROOT --prepare PROSE --state STATE_SNAPSHOT"})
            rows.append({"tool": "reconcile", "example": "reconcile REPORT --root PROJECT_ROOT --strict"})
        if "narrative-runtime" in enabled:
            rows.append({"tool": "runtime", "example": "runtime impact DEPENDENCIES CHANGED_NODE --json"})
        rows.append({"tool": "semantics", "example": "semantics verify PROJECT_ROOT"})
    return rows


def cmd_route(intent: str, as_json: bool, manifest_path: Path | None = None) -> int:
    rows = route_steps(intent, manifest_path)
    payload = {"intent": intent, "steps": rows}
    if manifest_path is not None:
        payload["project_manifest"] = str(manifest_path)
    if as_json:
        emit(payload, True)
    else:
        print(f"intent: {intent}")
        if manifest_path is not None:
            print(f"project_manifest: {manifest_path}")
        for idx, row in enumerate(rows, 1):
            print(f"{idx}. storyctl.py {row['example']}")
    return 0


def preflight(command: str, remainder: list[str]) -> int:
    profile = CAPABILITY_PROFILES.get(command)
    if profile is None or any(token in {"-h", "--help"} for token in remainder):
        return 0
    probe = SCRIPT_DIR / "capability_probe.py"
    if not probe.is_file():
        print("storyctl error: capability probe backend is missing", file=sys.stderr)
        return 2
    proc = subprocess.run(
        [sys.executable, str(probe), "check", profile],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        if detail:
            print(detail, file=sys.stderr)
        print(
            f"storyctl error: startup capability preflight failed for {command}; "
            "resolve the declared dependency before retrying",
            file=sys.stderr,
        )
    return int(proc.returncode)


def delegate(command: str, remainder: list[str]) -> int:
    meta = TOOLS[command]
    script = SCRIPT_DIR / meta["script"]
    if not script.is_file():
        print(f"storyctl error: backend missing for {command}: {script.name}", file=sys.stderr)
        return 2
    status = preflight(command, remainder)
    if status != 0:
        return status
    proc = subprocess.run([sys.executable, str(script), *remainder], check=False)
    return int(proc.returncode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Unified discovery and dispatch surface for Literary Webnovel Architect. "
            "Specialized scripts remain canonical backends; this controller only routes to them."
        ),
        add_help=True,
    )
    parser.add_argument("command", nargs="?", help="catalog, route, or any command listed by catalog")
    parser.add_argument("remainder", nargs=argparse.REMAINDER)
    return parser


def print_front_help(parser: argparse.ArgumentParser) -> None:
    parser.print_help()
    print("\nDiscovery commands:")
    print("  catalog [--json]                  list the public tool surface")
    print("  route INTENT [--manifest FILE] [--json]  show a recommended command sequence")
    print("\nDirect commands:")
    for name in sorted(TOOLS):
        print(f"  {name:<24} {TOOLS[name]['summary']}")
    print("\nUse: storyctl.py COMMAND --help to see the canonical backend help.")


def main() -> int:
    parser = build_parser()
    argv = sys.argv[1:]
    if not argv or argv[0] in {"-h", "--help"}:
        print_front_help(parser)
        return 0

    command = argv[0]
    rest = argv[1:]
    if command == "status":
        status_parser = argparse.ArgumentParser(description=TOOLS["status"]["summary"])
        status_parser.add_argument("project_root", type=Path)
        status_parser.add_argument("--json", action="store_true")
        args = status_parser.parse_args(rest)
        try:
            from project_ops import operational_status
            result = operational_status(args.project_root)
        except Exception as exc:
            result = {"active_run_status": "INVALID", "errors": [str(exc)]}
        emit(result, args.json)
        return 1 if result.get("errors") else 0
    if command == "catalog":
        as_json = rest == ["--json"]
        if rest not in ([], ["--json"]):
            print("usage: storyctl.py catalog [--json]", file=sys.stderr)
            return 2
        return cmd_catalog(as_json)
    if command == "route":
        as_json = False
        manifest_path = None
        cleaned: list[str] = []
        i = 0
        while i < len(rest):
            token = rest[i]
            if token == "--json":
                as_json = True
                i += 1
                continue
            if token == "--manifest":
                if i + 1 >= len(rest):
                    print("storyctl route: --manifest requires a path", file=sys.stderr)
                    return 2
                manifest_path = Path(rest[i + 1]).resolve()
                i += 2
                continue
            cleaned.append(token)
            i += 1
        if len(cleaned) != 1 or cleaned[0] not in ROUTES:
            print("usage: storyctl.py route {" + ",".join(sorted(ROUTES)) + "} [--manifest PROJECT_MANIFEST] [--json]", file=sys.stderr)
            return 2
        if manifest_path is not None and not manifest_path.is_file():
            print(f"storyctl route: manifest not found: {manifest_path}", file=sys.stderr)
            return 2
        return cmd_route(cleaned[0], as_json, manifest_path)
    if command not in TOOLS:
        print(f"storyctl error: unknown command: {command}", file=sys.stderr)
        print("run 'storyctl.py catalog' to list available commands", file=sys.stderr)
        return 2
    return delegate(command, rest)


if __name__ == "__main__":
    raise SystemExit(main())
