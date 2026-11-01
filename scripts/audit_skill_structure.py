#!/usr/bin/env python3
"""Audit structural hygiene for the literary-webnovel-architect skill.

This is a maintenance tool for the Skill itself, not for fiction projects.
It checks context-load hygiene, stale module references, missing internal paths,
and accidental build/backup artifacts before packaging.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

RETIRED_REFERENCES = {
    "scene-engine.md",
    "scene-dynamics.md",
    "pressure-tests.md",
    "story-red-team.md",
}

IGNORED_PROJECT_DOC_RE = re.compile(r"^(?:0[0-9]|10)-.*\.md$")
EVALUATION_CASE_HEADING_RE = re.compile(r"^###\s+([A-Z]+[0-9]+)\.\s+", re.MULTILINE)
NUMBERED_HEADING_RE = re.compile(r"^(#{2,6})\s+(\d+)\.\s+", re.MULTILINE)
PHASE0_REFERENCE_BASELINE_SHA256 = "45a71fc46a85d6af01af5835cdd5169b3babfbba95670423e312e1f19bfe5700"


def find_evaluation_case_id_duplicates(text: str) -> dict[str, list[int]]:
    """Return duplicate evaluation-corpus case IDs with their 1-based heading lines.

    Case IDs are identifiers, not display numbering. Reusing one makes benchmark,
    failure, and regression links ambiguous even when the titles differ.
    """
    seen: dict[str, list[int]] = {}
    for match in EVALUATION_CASE_HEADING_RE.finditer(text):
        case_id = match.group(1)
        line = text.count("\n", 0, match.start()) + 1
        seen.setdefault(case_id, []).append(line)
    return {case_id: lines for case_id, lines in seen.items() if len(lines) > 1}


def find_duplicate_numbered_headings(text: str) -> dict[tuple[int, int], list[int]]:
    """Return duplicate numbered Markdown headings at the same heading level.

    Numbering need not be contiguous: historical documents may intentionally skip
    numbers. This lint only rejects reuse of the same number at the same level in
    one file, which is ambiguous for maintenance and section references.
    """
    seen: dict[tuple[int, int], list[int]] = {}
    for match in NUMBERED_HEADING_RE.finditer(text):
        key = (len(match.group(1)), int(match.group(2)))
        line = text.count("\n", 0, match.start()) + 1
        seen.setdefault(key, []).append(line)
    return {key: lines for key, lines in seen.items() if len(lines) > 1}


def architecture_freeze_violations(contract: dict[str, Any], current_reference_paths: set[str]) -> list[str]:
    """Validate the Phase 0 reference-surface freeze against a current inventory.

    The machine gate intentionally protects only the canonical reference surface.
    Whether an existing owner has been semantically over-expanded remains a human
    architecture-review question documented in system-map.md.
    """
    violations: list[str] = []
    if contract.get("phase") != "phase-0" or contract.get("status") != "active":
        violations.append("architecture-freeze registry must declare active phase-0 status")

    baseline_raw = contract.get("baseline_reference_inventory", [])
    if not isinstance(baseline_raw, list) or not all(isinstance(x, str) for x in baseline_raw):
        return violations + ["architecture-freeze baseline_reference_inventory must be a string list"]
    baseline = set(baseline_raw)
    if len(baseline) != len(baseline_raw):
        violations.append("architecture-freeze baseline_reference_inventory contains duplicate paths")
    declared_count = contract.get("baseline_reference_count")
    if declared_count != len(baseline_raw):
        violations.append(
            f"architecture-freeze baseline_reference_count mismatch: declared={declared_count!r} actual={len(baseline_raw)}"
        )
    baseline_payload = "".join(f"{path}\n" for path in baseline_raw).encode("utf-8")
    baseline_sha256 = hashlib.sha256(baseline_payload).hexdigest()
    if contract.get("baseline_reference_sha256") != baseline_sha256:
        violations.append("architecture-freeze baseline_reference_sha256 does not match the declared inventory")
    if baseline_sha256 != PHASE0_REFERENCE_BASELINE_SHA256:
        violations.append(
            "Phase 0 frozen reference baseline changed; use approved_reference_additions rather than rewriting the baseline"
        )

    exception_contract = contract.get("exception_record_contract", {})
    required = exception_contract.get("required_fields", []) if isinstance(exception_contract, dict) else []
    if not isinstance(required, list) or not all(isinstance(x, str) for x in required):
        required = []
    approved_status = (
        exception_contract.get("status_required_for_authorization", "approved")
        if isinstance(exception_contract, dict)
        else "approved"
    )

    exceptions = contract.get("approved_reference_additions", [])
    if not isinstance(exceptions, list):
        return violations + ["architecture-freeze approved_reference_additions must be a list"]

    approved_paths: set[str] = set()
    seen_paths: set[str] = set()
    for index, item in enumerate(exceptions):
        label = f"architecture-freeze exception #{index + 1}"
        if not isinstance(item, dict):
            violations.append(f"{label} must be an object")
            continue
        path = item.get("path")
        if isinstance(path, str):
            if path in seen_paths:
                violations.append(f"{label} duplicates exception path {path}")
            seen_paths.add(path)
        missing = []
        for field in required:
            value = item.get(field)
            if value is None or value == "" or value == []:
                missing.append(field)
        if missing:
            violations.append(f"{label} is incomplete; missing {', '.join(missing)}")
            continue
        if item.get("status") != approved_status:
            continue
        if not isinstance(path, str) or not path.startswith("references/") or not path.endswith(".md"):
            violations.append(f"{label} has invalid reference path {path!r}")
            continue
        owners = item.get("existing_owners_considered")
        if not isinstance(owners, list) or not owners or not all(isinstance(x, str) and x for x in owners):
            violations.append(f"{label} must name at least one existing owner considered")
            continue
        approved_paths.add(path)

    for path in sorted(current_reference_paths - baseline - approved_paths):
        violations.append(
            f"unapproved Phase 0 reference addition: {path}; extend an existing owner or record a complete approved owner-gap exception"
        )
    return violations


def audit(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    skill = root / "SKILL.md"
    refs = root / "references"
    if not skill.is_file():
        errors.append("missing SKILL.md")
        return errors, warnings
    if not refs.is_dir():
        errors.append("missing references/ directory")
        return errors, warnings

    skill_lines = skill.read_text(encoding="utf-8").splitlines()
    if len(skill_lines) > 500:
        errors.append(f"SKILL.md has {len(skill_lines)} lines; keep the control plane <= 500")

    reference_files = sorted(refs.glob("*.md"))

    freeze_path = root / "assets/architecture-freeze.json"
    if not freeze_path.is_file():
        errors.append("missing assets/architecture-freeze.json while Phase 0 architecture freeze is active")
    else:
        try:
            freeze_contract = json.loads(freeze_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid architecture-freeze registry: {exc}")
        else:
            current_refs = {str(path.relative_to(root)).replace("\\", "/") for path in reference_files}
            errors.extend(architecture_freeze_violations(freeze_contract, current_refs))

    evaluation_corpus = refs / "evaluation-corpus.md"
    if not evaluation_corpus.is_file():
        errors.append("missing references/evaluation-corpus.md")
    else:
        corpus_text = evaluation_corpus.read_text(encoding="utf-8")
        duplicate_case_ids = find_evaluation_case_id_duplicates(corpus_text)
        for case_id, lines in sorted(duplicate_case_ids.items()):
            line_list = ", ".join(str(x) for x in lines)
            errors.append(
                f"duplicate evaluation-corpus case ID {case_id} at lines {line_list}; "
                "benchmark/holdout IDs must be globally unique within the corpus"
            )

    required_poetics_assets = {
        "references/literary-meta-core.md",
        "references/project-poetics.md",
        "assets/prewriting-templates/project-poetics-template.md",
        "assets/project-schemas/scoped-project-poetics-envelope.schema.json",
        "scripts/scoped_poetics.py",
    }
    for rel in sorted(required_poetics_assets):
        if not (root / rel).is_file():
            errors.append(f"missing Project Poetics architecture asset: {rel}")

    skill_text = skill.read_text(encoding="utf-8")
    for required_ref in ("literary-meta-core.md", "project-poetics.md", "skill-scope-identity.md"):
        if required_ref not in skill_text:
            errors.append(f"SKILL.md lacks one-hop routing to {required_ref}")

    # Product identity is Chinese-language long-form fiction, while the historical
    # slug remains a compatibility identifier until an explicit migration release.
    if not re.search(r"(?m)^name:\s*literary-webnovel-architect\s*$", skill_text):
        errors.append("SKILL frontmatter compatibility slug drifted; migration requires an explicit identity release")
    if "# Chinese Long-Form Architect" not in skill_text:
        errors.append("SKILL.md public H1 must remain Chinese Long-Form Architect")
    if "Chinese-language long-form fiction" not in skill_text:
        errors.append("SKILL.md no longer states the Chinese-language product scope")

    identity_ref = refs / "skill-scope-identity.md"
    if not identity_ref.is_file():
        errors.append("missing references/skill-scope-identity.md")

    agent_meta = root / "agents/openai.yaml"
    if not agent_meta.is_file():
        errors.append("missing agents/openai.yaml")
    else:
        agent_text = agent_meta.read_text(encoding="utf-8")
        if 'display_name: "Chinese Long-Form Architect"' not in agent_text:
            errors.append("agents/openai.yaml display_name drifted from Chinese Long-Form Architect")
        if "Chinese-language long-form fiction" not in agent_text:
            errors.append("agents/openai.yaml short_description no longer states the Chinese-language scope")

    for path in reference_files:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if len(lines) > 100 and "## Contents" not in lines[:70]:
            errors.append(f"long reference lacks early Contents section: {path.relative_to(root)} ({len(lines)} lines)")
        for (level, number), heading_lines in sorted(find_duplicate_numbered_headings(text).items()):
            line_list = ", ".join(str(x) for x in heading_lines)
            errors.append(
                f"duplicate numbered heading at level {level} in {path.relative_to(root)}: "
                f"section {number} appears at lines {line_list}"
            )

    all_files = {str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*") if p.is_file()}
    docs = [skill, *reference_files]
    path_pat = re.compile(r"`([^`]+\.(?:md|py|json|jsonl|yaml|yml))`")
    for path in docs:
        text = path.read_text(encoding="utf-8")
        for match in path_pat.finditer(text):
            raw = match.group(1)
            if raw == "SKILL.md":
                candidates = ["SKILL.md"]
            elif raw.startswith(("references/", "assets/", "scripts/")):
                candidates = [raw]
            elif "/" not in raw:
                candidates = [f"references/{raw}", f"assets/{raw}", f"scripts/{raw}"]
            else:
                candidates = [raw]

            if any(c in all_files for c in candidates):
                continue

            # These are project-workspace output filenames, not Skill package paths.
            if path.name in {"prewriting-readiness.md", "reality-grounding-research.md"}:
                if IGNORED_PROJECT_DOC_RE.match(raw) or raw in {"source-ledger.md", "00-reality-research-index.md"}:
                    continue
            if path.name == "context-compilation.md" and raw == "context-index.json":
                continue
            if path.name == "chapter-humanities-analysis.md" and re.match(r"^analysis/chapter-[0-9]+-humanities\.md$", raw):
                continue
            if raw in {"project-manifest.json", "resume-capsule.md"} and path.name in {"SKILL.md", "project-operability.md", "runtime-schema-migration.md", "system-map.md", "prewriting-readiness.md", "story-observatory.md", "narrative-runtime.md"}:
                continue
            if path.name == "project-operability.md" and raw == "state/story-state.json":
                continue
            if path.name == "spatiotemporal-scene-state.md" and raw == "state/scene-plans.json":
                continue  # project-local neutral plan registry, not a Skill asset
            if path.name in {"narrative-runtime.md", "runtime-schema-migration.md", "state-validation.md", "semantic-revision.md", "story-observatory.md"}:
                if raw.startswith(("runtime/", "revision/", "analysis/reader-sim/")):
                    continue

            errors.append(f"unresolved internal file mention in {path.relative_to(root)}: {raw}")

    for path in docs:
        text = path.read_text(encoding="utf-8")
        for retired in RETIRED_REFERENCES:
            if retired in text:
                errors.append(f"retired module name {retired} still referenced by {path.relative_to(root)}")

    for path in root.rglob("*"):
        rel = str(path.relative_to(root)).replace("\\", "/")
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            errors.append(f"cache artifact must not be packaged: {rel}")
        if path.is_file() and (
            path.suffix in {".bak", ".tmp"}
            or ".before-" in path.name
            or path.name.endswith("~")
        ):
            errors.append(f"backup/temp artifact must not be packaged: {rel}")

    # Lightweight ownership-hygiene signal: the maintenance map must exist and
    # the main control plane must route to it rather than duplicating ad hoc owners.
    system_map = refs / "system-map.md"
    if not system_map.is_file():
        errors.append("missing references/system-map.md")
    else:
        system_map_text = system_map.read_text(encoding="utf-8")
        if "canonical ownership" not in skill.read_text(encoding="utf-8").lower():
            warnings.append("SKILL.md does not explicitly route ambiguous ownership to system-map.md")
        # Every reference must be reachable from the one canonical ownership/router map.
        for ref in reference_files:
            if ref.name == "system-map.md":
                continue
            if ref.name not in system_map_text:
                errors.append(f"reference is disconnected from system-map.md: {ref.relative_to(root)}")

    # Public script entrypoints must be discoverable from the control/docs layer.
    # Internal shared libraries are intentionally not exposed as user-facing commands.
    internal_script_helpers = {
        "orchestration_contract.py",
        "reader_state.py",
        "research_freshness.py",
        "architecture_diversity.py",
        "rule_entropy_audit.py",
        "stc_validator.py",
    }
    doc_text = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    scripts_dir = root / "scripts"
    public_cli_scripts: set[str] = set()
    if scripts_dir.is_dir():
        for script_path in sorted(scripts_dir.glob("*.py")):
            if script_path.name in internal_script_helpers:
                continue
            source = script_path.read_text(encoding="utf-8")
            if 'if __name__ == "__main__"' in source:
                public_cli_scripts.add(script_path.name)
            if script_path.name not in doc_text:
                errors.append(f"public script is disconnected from SKILL/references: {script_path.relative_to(root)}")

    # All executable public CLIs must be reachable through the one storyctl discovery surface.
    storyctl = scripts_dir / "storyctl.py"
    if not storyctl.is_file():
        errors.append("missing unified scripts/storyctl.py front controller")
    else:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("lwa_storyctl_audit", storyctl)
            module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(module)
            covered = {str(meta.get("script")) for meta in module.TOOLS.values()}
        except Exception as exc:
            errors.append(f"cannot inspect storyctl tool registry: {exc}")
            covered = set()
        missing = sorted(public_cli_scripts - covered - {"storyctl.py"})
        if missing:
            errors.append(f"public CLI(s) missing from storyctl catalog: {', '.join(missing)}")
        unknown = sorted(x for x in covered if x and not (scripts_dir / x).is_file())
        if unknown:
            errors.append(f"storyctl catalog references missing backend(s): {', '.join(unknown)}")

    # Orchestration policy must have one source of truth.
    clearance_path = root / "assets/orchestration/role-clearance.json"
    cards_dir = root / "assets/orchestration/role-cards"
    capabilities_template = root / "assets/orchestration/capabilities-template.json"
    retired_asset_paths = {
        "assets/orchestration/execution-profile-template.json": "stale preselected orchestration template",
        "assets/tooling-templates/story-ops-state-template.json": "retired ambiguously named Story State template",
    }
    for rel, reason in retired_asset_paths.items():
        if (root / rel).exists():
            errors.append(f"{reason} must not return: {rel}")
    if not capabilities_template.is_file():
        errors.append("missing assets/orchestration/capabilities-template.json")
    if not clearance_path.is_file():
        errors.append("missing assets/orchestration/role-clearance.json")
    elif cards_dir.is_dir():
        try:
            clearance = json.loads(clearance_path.read_text(encoding="utf-8")).get("clearance", {})
        except Exception as exc:
            errors.append(f"invalid role-clearance registry: {exc}")
            clearance = {}
        declared = set(clearance) if isinstance(clearance, dict) else set()
        cards = {x.stem for x in cards_dir.glob("*.md") if x.is_file()}
        for role in sorted(declared - cards):
            errors.append(f"role clearance has no role card: {role}")
        for role in sorted(cards - declared):
            errors.append(f"role card has no clearance declaration: {role}")

    # Packaged Chinese narrative evaluation assets must remain reproducible and non-private.
    cne_dir = root / "assets/chinese-narrative-eval"
    cne_required = {
        "README.md",
        "corpus-manifest.json",
        "research-ledger.json",
        "taxonomy.json",
        "contrast-family.schema.json",
        "annotation.schema.json",
        "seed-families.jsonl",
        "annotation-template.jsonl",
    }
    if not cne_dir.is_dir():
        errors.append("missing assets/chinese-narrative-eval directory")
    else:
        for name in sorted(cne_required):
            if not (cne_dir / name).is_file():
                errors.append(f"missing Chinese narrative evaluation asset: assets/chinese-narrative-eval/{name}")
        cne_script = scripts_dir / "chinese_narrative_eval.py"
        seed = cne_dir / "seed-families.jsonl"
        if cne_script.is_file() and seed.is_file():
            proc = subprocess.run(
                [sys.executable, str(cne_script), "validate", str(seed), "--json"],
                text=True, capture_output=True, check=False,
            )
            if proc.returncode != 0:
                detail = proc.stdout.strip() or proc.stderr.strip()
                errors.append(f"Chinese narrative evaluation seed failed validator: {detail}")
        for jsonl_path in sorted(cne_dir.glob("*.jsonl")):
            for lineno, raw in enumerate(jsonl_path.read_text(encoding="utf-8").splitlines(), start=1):
                if not raw.strip():
                    continue
                try:
                    obj = json.loads(raw)
                except Exception as exc:
                    errors.append(f"invalid Chinese evaluation JSONL {jsonl_path.relative_to(root)}:{lineno}: {exc}")
                    continue
                if isinstance(obj, dict) and obj.get("split") == "private_holdout":
                    errors.append(f"private_holdout must not be packaged: {jsonl_path.relative_to(root)}:{lineno}")

    # Regression corpora should store durable/adversarial inputs, not routine regenerated outputs.
    corpus_root = root / "assets/regression-corpora"
    if corpus_root.is_dir():
        forbidden_generated = [
            "**/*writer-pack*.manifest.json",
            "**/*writer-pack*.md",
            "**/observatory/*.md",
            "**/runtime/tx-*.json",
            "**/runtime/replay-*.json",
            "**/runtime/snapshots/*.json",
            "**/revisions/*/diff.json",
            "**/*paragraph-profile*.txt",
            "**/REAL-USER-E2E-REPORT.md",
        ]
        for pattern in forbidden_generated:
            for item in corpus_root.glob(pattern):
                if item.is_file():
                    errors.append(f"regression corpus contains disposable generated artifact: {item.relative_to(root)}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Skill structural hygiene before packaging")
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    root = args.root.resolve()
    errors, warnings = audit(root)

    for msg in warnings:
        print(f"WARNING: {msg}")
    for msg in errors:
        print(f"ERROR: {msg}")
    print(f"summary: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
