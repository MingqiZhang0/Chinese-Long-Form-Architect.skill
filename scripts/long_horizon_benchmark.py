#!/usr/bin/env python3
"""Deterministic 60+ chapter long-horizon continuity benchmark.

The benchmark is intentionally operational, not a literary-quality claim. It
creates a temporary persistent-governance project with chapter prose, Runtime
history, dependency edges, reader state, context lifecycle, long-gap character
return, delayed payoff, object custody, and secret-taint tests. It then validates
and replays the project using the Skill's real deterministic tooling.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compile_context import compile_pack
from narrative_runtime import branch_map, impact, replay, validate_runtime
from project_ops import doctor
from semantic_kernel import verify_project as verify_semantic_kernel

PROJECT_ID_PREFIX = "LWA-LONG-HORIZON"
RUNTIME_VERSION = "3.0.0"
PROJECT_VERSION = "1.0.0"
SECRET_ID = "SECRET-EDITOR"
SECRET_LITERAL = "the editor altered the ledger before the fire"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def event(seq: int, chapter: int, effects: list[dict[str, Any]], *, intent: str) -> dict[str, Any]:
    return {
        "schema_version": RUNTIME_VERSION,
        "event_version": "1.0.0",
        "event_id": f"EV-{seq:04d}",
        "branch": "main",
        "seq": seq,
        "event_type": "ChapterCommitted" if chapter else "ProjectInitialized",
        "intent": intent,
        "story_time": chapter,
        "chapter": chapter,
        "scene": None,
        "entity_ids": ["project"],
        "effects": effects,
        "source": f"benchmark/chapter-{chapter:03d}" if chapter else "benchmark/init",
        "dependencies": [],
        "transaction_id": f"TX-{seq:04d}",
        "status": "committed",
    }


def chapter_effects(chapter: int) -> list[dict[str, Any]]:
    fx: list[dict[str, Any]] = [
        {"op": "set", "path": "current_chapter", "value": chapter},
        {"op": "set", "path": "characters.mara.last_seen_chapter", "value": chapter},
    ]
    if chapter == 1:
        fx += [
            {"op": "set", "path": "characters.mara.location", "value": "north-harbor"},
            {"op": "set", "path": "characters.ren.location", "value": "north-harbor"},
            {"op": "set", "path": "characters.ren.knowledge.old-route", "value": "suspects"},
            {"op": "set", "path": "objects.brass-key.holder", "value": "mara"},
            {"op": "set", "path": "promises.old-camera.status", "value": "open"},
            {"op": "set", "path": "reader_state.foreground_questions", "value": ["Why was the old cinema inventory rewritten?"]},
        ]
    if chapter == 5:
        fx.append({"op": "set", "path": "objects.brass-key.holder", "value": "ren"})
    if chapter == 8:
        fx.append({"op": "set", "path": "characters.ren.knowledge.tunnel-map", "value": "knows"})
    if chapter == 12:
        fx += [
            {"op": "set", "path": "characters.ren.location", "value": "inland"},
            {"op": "set", "path": "characters.ren.absent_since", "value": 12},
        ]
    if chapter == 18:
        fx.append({"op": "set", "path": "reader_state.warm_questions", "value": ["Who benefited from the inventory rewrite?"]})
    if chapter == 24:
        fx.append({"op": "set", "path": "characters.mara.injury", "value": "healing-left-wrist"})
    if chapter == 30:
        fx.append({"op": "set", "path": "reader_state.foreground_questions", "value": ["Why does the ledger disagree with the physical archive?"]})
    if chapter == 37:
        fx.append({"op": "set", "path": "promises.old-camera.status", "value": "reactivated"})
    if chapter == 44:
        fx += [
            {"op": "set", "path": "characters.ren.location", "value": "north-harbor"},
            {"op": "set", "path": "characters.ren.returned_after_gap", "value": True},
        ]
    if chapter == 48:
        fx.append({"op": "set", "path": "objects.brass-key.holder", "value": "mara"})
    if chapter == 52:
        fx.append({"op": "set", "path": "promises.old-camera.status", "value": "paid"})
    if chapter == 55:
        fx += [
            {"op": "set", "path": "reader_state.foreground_questions", "value": ["Who changed the ledger, and why?"]},
            {"op": "set", "path": "public_facts.old-screening-room", "value": "confirmed"},
        ]
    if chapter == 60:
        fx.append({"op": "set", "path": "characters.mara.injury", "value": "resolved-with-stiffness"})
    return fx


def chapter_text(chapter: int) -> str:
    anchors = {
        1: "Mara takes custody of the brass key and promises to return the old camera.",
        5: "Mara gives the brass key to Ren for the archive inspection.",
        8: "Ren studies the tunnel map closely enough to remember its service route.",
        12: "Ren leaves North Harbor for an inland contract without returning the key.",
        24: "Mara sprains her left wrist during the archive move.",
        37: "The old camera resurfaces and the long-delayed promise becomes active again.",
        44: "Ren returns after thirty-two chapters away and still remembers the tunnel map.",
        48: "Ren returns the brass key to Mara after forty-three chapters of custody.",
        52: "Mara finally returns the old camera, closing the promise opened in chapter one.",
        55: "The sealed screening room is confirmed to exist, changing the public question.",
        60: "The season closes with Mara's wrist healed but still stiff in cold weather.",
    }
    event_line = anchors.get(chapter, f"The investigation advances through a small observable consequence in chapter {chapter}.")
    return (
        f"# Chapter {chapter}\n\n"
        f"{event_line}\n\n"
        "The chapter keeps its local conflict bounded. People continue ordinary work around the investigation, "
        "and no hidden answer is stated merely because the backend knows it.\n\n"
        f"At the end of chapter {chapter}, the next move follows from what the characters can actually access."
    )


def mission_text(chapter: int) -> str:
    return (
        f"# Writer Mission - Chapter {chapter}\n\n"
        f"Write chapter {chapter} from the current public and character-accessible state. "
        "Preserve object custody, long-gap knowledge, injury residue, and reader-facing uncertainty. "
        "Do not infer hidden backend truth from the existence of this mission."
    )


def summary_text(chapter: int) -> str:
    return f"Chapter {chapter} left one local consequence in motion; use only facts already established by the prose and committed state."


def build_project(root: Path, chapters: int) -> dict[str, Any]:
    project_id = f"{PROJECT_ID_PREFIX}-{chapters}"
    for rel in ("chapters", "scenes", "context", "state", "runtime", "runtime/projections"):
        (root / rel).mkdir(parents=True, exist_ok=True)

    events: list[dict[str, Any]] = [
        event(
            1,
            0,
            [
                {"op": "set", "path": "meta.initialized", "value": True},
                {"op": "set", "path": "project_id", "value": project_id},
            ],
            intent="Initialize long-horizon benchmark",
        )
    ]
    for chapter in range(1, chapters + 1):
        events.append(event(chapter + 1, chapter, chapter_effects(chapter), intent=f"Commit benchmark chapter {chapter}"))
        write_text(root / f"chapters/chapter-{chapter:03d}.md", chapter_text(chapter))
        write_text(root / f"context/chapter-{chapter:03d}-writer-mission.md", mission_text(chapter))
        write_text(root / f"context/chapter-{chapter:03d}-summary.md", summary_text(chapter))

    (root / "runtime/events.jsonl").write_text(
        "\n".join(json.dumps(e, ensure_ascii=False, separators=(",", ":")) for e in events) + "\n",
        encoding="utf-8",
    )
    branches = {
        "schema_version": RUNTIME_VERSION,
        "branches": {"main": {"parent": None, "fork_event": None, "purpose": "Canonical benchmark line", "status": "active"}},
    }
    write_json(root / "runtime/branches.json", branches)

    deps = {
        "schema_version": RUNTIME_VERSION,
        "edges": [
            {"source": "CH-005", "target": "CH-048", "kind": "custody", "strength": "hard", "status": "active", "reason": "The later key return depends on the chapter-5 transfer."},
            {"source": "CH-008", "target": "CH-044", "kind": "knowledge", "strength": "hard", "status": "active", "reason": "Ren's return uses knowledge acquired before a long absence."},
            {"source": "CH-012", "target": "CH-044", "kind": "continuity", "strength": "hard", "status": "active", "reason": "The long absence begins here."},
            {"source": "CH-001", "target": "CH-037", "kind": "promise", "strength": "hard", "status": "active", "reason": "The camera promise is reactivated."},
            {"source": "CH-037", "target": "CH-052", "kind": "promise", "strength": "hard", "status": "active", "reason": "The reactivated promise is paid off."},
            {"source": "CH-030", "target": "CH-055", "kind": "reader-state", "strength": "soft", "status": "active", "reason": "The ledger question is transformed by the chapter-55 discovery."},
        ],
    }
    write_json(root / "runtime/dependencies.json", deps)
    write_json(root / "runtime/invariants.json", {"schema_version": "1.0.0", "invariants": []})
    write_json(root / "runtime/narrative-debt.json", {"schema_version": "1.0.0", "items": []})

    runtime_manifest = {
        "runtime_schema_version": RUNTIME_VERSION,
        "schema_dialect": "https://json-schema.org/draft/2020-12/schema",
        "project_id": project_id,
        "current_branch": "main",
        "compatibility_policy": "backward_transitive",
        "minimum_reader_version": RUNTIME_VERSION,
        "paths": {
            "events": "runtime/events.jsonl",
            "branches": "runtime/branches.json",
            "dependencies": "runtime/dependencies.json",
            "invariants": "runtime/invariants.json",
            "narrative_debt": "runtime/narrative-debt.json",
            "projections": "runtime/projections",
            "snapshots": "runtime/snapshots",
        },
        "migration_history": [],
    }
    write_json(root / "runtime/runtime-manifest.json", runtime_manifest)

    state, used = replay(events, branch_map(branches), "main")
    state.setdefault("scene_packets", [])
    state.setdefault("threads", [])
    state.setdefault("research_dependencies", [])
    state.setdefault("authorial_unknowns", [])
    write_json(root / "state/story-state.json", state)

    reader_model = {
        "current_chapter": chapters,
        "foreground_questions": state.get("reader_state", {}).get("foreground_questions", []),
        "warm_questions": state.get("reader_state", {}).get("warm_questions", []),
        "notes": "Synthetic benchmark reader model; operational only.",
    }
    write_json(root / "state/reader-model.json", reader_model)

    secret_registry = {
        "secrets": [
            {
                "id": SECRET_ID,
                "status": "active",
                "allowed_roles": ["director", "causal-architect"],
                "declassified_for": [],
                "literal_terms": [SECRET_LITERAL],
                "notes": "Long-horizon benchmark hidden backend answer.",
            }
        ]
    }
    write_json(root / "context/secret-registry.json", secret_registry)

    entries: list[dict[str, Any]] = []
    for chapter in range(1, chapters + 1):
        entries.append(
            {
                "id": f"ch-{chapter:03d}-mission",
                "path": f"context/chapter-{chapter:03d}-writer-mission.md",
                "kind": "mission",
                "priority": 100,
                "required": False,
                "roles": ["writer"],
                "visibility": "writer-visible",
                "available_from_chapter": chapter,
                "available_to_chapter": chapter,
                "chapter": chapter,
                "branch": "main",
                "tainted_by": [],
                "derived_from": [],
                "declassified_for": [],
            }
        )
        entries.append(
            {
                "id": f"ch-{chapter:03d}-summary",
                "path": f"context/chapter-{chapter:03d}-summary.md",
                "kind": "summary",
                "priority": 30,
                "required": False,
                "roles": ["writer"],
                "visibility": "writer-visible",
                "available_from_chapter": chapter,
                "available_to_chapter": min(chapters, chapter + 4),
                "chapter": chapter,
                "branch": "main",
                "tainted_by": [],
                "derived_from": [],
                "declassified_for": [],
            }
        )
    write_text(root / "context/backend-editor-note.md", "A backend note derived from the hidden editor identity.")
    entries.append(
        {
            "id": "backend-editor-note",
            "path": "context/backend-editor-note.md",
            "kind": "backend-note",
            "priority": 5,
            "required": False,
            "roles": ["director", "causal-architect"],
            "visibility": "backend-hidden",
            "available_from_chapter": 1,
            "chapter": None,
            "branch": "main",
            "tainted_by": [SECRET_ID],
            "derived_from": [],
            "declassified_for": [],
        }
    )
    write_json(root / "context/context-index.json", {"entries": entries})

    request = {
        "role": "writer",
        "branch": "main",
        "target_chapter": chapters,
        "target_scene": None,
        "budget_tokens": 8000,
        "required_ids": [f"ch-{chapters:03d}-mission"],
        "strict_visibility": True,
        "execution_profile": None,
        "secret_registry": "context/secret-registry.json",
        "blocked_secret_ids": [SECRET_ID],
        "forbidden_terms": [SECRET_LITERAL],
        "forbidden_case_sensitive": False,
        "deduplicate_content": True,
        "characters": [],
        "locations": [],
        "threads": [],
        "research": [],
        "scenes": [],
        "project_manifest": "project-manifest.json",
    }
    write_json(root / "context/writer-request.json", request)

    enabled = [
        "project-state",
        "chapter-mission",
        "scene-state",
        "reader-model",
        "context-compilation",
        "narrative-runtime",
        "dependency-graph",
    ]
    project_manifest = {
        "project_format_version": PROJECT_VERSION,
        "schema_dialect": "https://json-schema.org/draft/2020-12/schema",
        "project_id": project_id,
        "governance_profile": "persistent",
        "current_branch": "main",
        "current_chapter": chapters,
        "last_committed_event": events[-1]["event_id"],
        "context_generation": 0,
        "enabled_subsystems": enabled,
        "canonical_paths": {
            "story_state": "state/story-state.json",
            "reader_model": "state/reader-model.json",
            "context_index": "context/context-index.json",
            "secret_registry": "context/secret-registry.json",
            "runtime_manifest": "runtime/runtime-manifest.json",
            "chapters_dir": "chapters",
            "scenes_dir": "scenes",
        },
        "migration_history": [],
        "context_generation_history": [],
    }
    write_json(root / "project-manifest.json", project_manifest)
    return {
        "events": events,
        "branches": branches,
        "dependencies": deps,
        "state": state,
        "request": request,
        "index": {"entries": entries},
        "manifest": project_manifest,
        "used_events": used,
    }


def run_schema_validation(project_root: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "runtime_schema.py"), "validate-project", str(project_root)],
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def benchmark(project_root: Path, chapters: int) -> dict[str, Any]:
    project_id = f"{PROJECT_ID_PREFIX}-{chapters}"
    built = build_project(project_root, chapters)
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    errors, warnings = doctor(project_root, built["manifest"])
    check("project-doctor", not errors, f"errors={errors}; warnings={warnings}")

    runtime_errors, runtime_warnings = validate_runtime(
        built["events"], branch_map(built["branches"]), built["dependencies"]
    )
    check("runtime-validate", not runtime_errors, f"errors={runtime_errors}; warnings={runtime_warnings}")

    schema_ok, schema_detail = run_schema_validation(project_root)
    check("runtime-schema", schema_ok, schema_detail or "ok")

    kernel = verify_semantic_kernel(project_root)
    kernel_summary = kernel.get("summary", {}) if isinstance(kernel, dict) else {}
    kernel_fail = int(kernel_summary.get("fail", 0)) if isinstance(kernel_summary, dict) else 1
    check("semantic-kernel", kernel_fail == 0 and not kernel.get("errors"), f"summary={kernel_summary}; errors={kernel.get('errors', [])}")

    final_state, used = replay(built["events"], branch_map(built["branches"]), "main")
    check("replay-depth", len(used) == chapters + 1, f"replayed={len(used)} expected={chapters + 1}")
    check("chapter-head", final_state.get("current_chapter") == chapters, f"current_chapter={final_state.get('current_chapter')}")
    check(
        "long-gap-knowledge",
        final_state.get("characters", {}).get("ren", {}).get("knowledge", {}).get("tunnel-map") == "knows",
        "Ren must retain chapter-8 knowledge after returning in chapter 44.",
    )
    check(
        "long-gap-return",
        final_state.get("characters", {}).get("ren", {}).get("returned_after_gap") is True,
        "Ren must return after the long absence.",
    )
    check(
        "custody-return",
        final_state.get("objects", {}).get("brass-key", {}).get("holder") == "mara",
        "The chapter-5 key transfer must close in chapter 48.",
    )
    check(
        "delayed-payoff",
        final_state.get("promises", {}).get("old-camera", {}).get("status") == "paid",
        "The chapter-1 camera promise must pay in chapter 52.",
    )
    check(
        "injury-residue",
        final_state.get("characters", {}).get("mara", {}).get("injury") == "resolved-with-stiffness",
        "The chapter-24 injury must leave residue at chapter 60.",
    )

    impacted = impact(built["dependencies"]["edges"], "CH-012")
    impacted_targets = {row.get("node") or row.get("target") for row in impacted}
    raw_impacted = json.dumps(impacted, ensure_ascii=False)
    check("revision-propagation", "CH-044" in raw_impacted, f"impact={impacted}")

    pack, pack_manifest, pack_errors = compile_pack(built["index"], built["request"], project_root)
    included = {x.get("id") for x in pack_manifest.get("included", [])}
    check("context-compile", bool(pack) and not pack_errors, f"errors={pack_errors}")
    check("current-mission-present", f"ch-{chapters:03d}-mission" in included, f"included={sorted(included)}")
    check("old-mission-retired", "ch-001-mission" not in included, "Chapter-1 mission must not survive to the final chapter.")
    check("secret-literal-clean", SECRET_LITERAL not in pack.lower(), "Writer pack must not contain the hidden literal.")
    check("backend-secret-note-excluded", "backend-editor-note" not in included, f"included={sorted(included)}")
    check("context-budget", pack_manifest.get("estimated_tokens", 10**9) <= built["request"]["budget_tokens"], f"estimated_tokens={pack_manifest.get('estimated_tokens')}")

    malicious_index = json.loads(json.dumps(built["index"]))
    write_text(project_root / "context/malicious-paraphrase.md", "A writer-facing paraphrase inferred from the hidden editor identity.")
    malicious_index["entries"].append(
        {
            "id": "malicious-paraphrase",
            "path": "context/malicious-paraphrase.md",
            "kind": "summary",
            "priority": 200,
            "required": True,
            "roles": ["writer"],
            "visibility": "writer-visible",
            "available_from_chapter": chapters,
            "available_to_chapter": chapters,
            "chapter": chapters,
            "branch": "main",
            "tainted_by": [SECRET_ID],
            "derived_from": ["backend-editor-note"],
            "declassified_for": [],
        }
    )
    malicious_request = json.loads(json.dumps(built["request"]))
    malicious_request["required_ids"] = [f"ch-{chapters:03d}-mission", "malicious-paraphrase"]
    _, _, malicious_errors = compile_pack(malicious_index, malicious_request, project_root)
    check("semantic-taint-block", bool(malicious_errors), f"errors={malicious_errors}")
    error_blob = " ".join(malicious_errors).lower()
    check("taint-error-redaction", SECRET_LITERAL not in error_blob, "Leak errors must not echo the secret literal.")

    prose_count = len(list((project_root / "chapters").glob("chapter-*.md")))
    check("chapter-prose-count", prose_count == chapters, f"chapters={prose_count}")

    return {
        "benchmark": "long-horizon-continuity",
        "chapters": chapters,
        "project_id": project_id,
        "checks": checks,
        "passed": sum(1 for row in checks if row["ok"]),
        "failed": sum(1 for row in checks if not row["ok"]),
        "all_passed": all(row["ok"] for row in checks),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic 60+ chapter long-horizon continuity benchmark")
    sub = parser.add_subparsers(dest="command")
    run_p = sub.add_parser("run")
    run_p.add_argument("--chapters", type=int, default=60, help="chapter count; supported range 60-100")
    run_p.add_argument("--keep-project", type=Path, help="optional NEW directory in which to keep the generated benchmark project; existing paths are refused")
    run_p.add_argument("--out", type=Path, help="optional JSON report path")
    args = parser.parse_args()

    if args.command != "run":
        parser.print_help()
        return 0
    if not 60 <= args.chapters <= 100:
        print("benchmark error: --chapters must be between 60 and 100", file=sys.stderr)
        return 2

    temp_obj = None
    if args.keep_project:
        project_root = args.keep_project.resolve()
        if project_root.exists():
            print(f"benchmark error: --keep-project path already exists; refusing to delete or overwrite: {project_root}", file=sys.stderr)
            return 2
        project_root.mkdir(parents=True)
    else:
        temp_obj = tempfile.TemporaryDirectory(prefix="lwa-long-horizon-")
        project_root = Path(temp_obj.name)

    try:
        report = benchmark(project_root, args.chapters)
        if args.out:
            write_json(args.out, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["all_passed"] else 1
    finally:
        if temp_obj is not None:
            temp_obj.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
