#!/usr/bin/env python3
"""Seeded model-based fuzz checks for Narrative Runtime mechanics.

This is a runtime reliability test, not a random story generator. It generates
state-transition sequences and checks replay/snapshot/branch isolation properties.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
import tempfile
from pathlib import Path
from typing import Any

from narrative_runtime import apply_effect, effective_events, events_by_branch, replay, validate_runtime
from project_ops import doctor as project_doctor


def make_event(eid: str, branch: str, seq: int, op: str, path: str, value: Any) -> dict[str, Any]:
    return {
        "event_id": eid,
        "branch": branch,
        "seq": seq,
        "event_type": "FuzzTransition",
        "event_version": "1.0.0",
        "intent": f"fuzz {op} {path}",
        "entity_ids": ["fuzz"],
        "effects": [{"op": op, "path": path, "value": value}],
        "dependencies": [],
        "status": "committed",
    }


def direct_apply(state: dict[str, Any], event: dict[str, Any]) -> None:
    for effect in event.get("effects", []):
        apply_effect(state, effect)


def run_case(rng: random.Random, steps: int, case_id: int) -> list[str]:
    failures: list[str] = []
    branches: dict[str, dict[str, Any]] = {"main": {"parent": None, "fork_event": None, "status": "active"}}
    init = {
        "event_id": f"F{case_id:03d}-INIT",
        "branch": "main",
        "seq": 1,
        "event_type": "FuzzInitialized",
        "event_version": "1.0.0",
        "intent": "initialize typed fuzz containers",
        "entity_ids": ["fuzz"],
        "effects": [
            {"op": "set", "path": "meta", "value": {}},
            {"op": "set", "path": "resources", "value": {}},
            {"op": "set", "path": "objects", "value": {}},
        ],
        "dependencies": [],
        "status": "committed",
    }
    events: list[dict[str, Any]] = [init]
    model: dict[str, Any] = {}
    direct_apply(model, init)

    for i in range(1, steps + 1):
        op = rng.choice(["set", "increment", "add_to_set", "remove_from_set"])
        if op == "set":
            path = rng.choice(["resources.cash", "meta.counter", "objects.key.holder"])
            if path in {"resources.cash", "meta.counter"}:
                value = rng.choice([0, 1, 2, 5, 10])
            else:
                value = rng.choice(["alice", "bob", "table", None])
        elif op == "increment":
            path = "meta.counter"
            value = rng.choice([-2, -1, 1, 2, 3])
        else:
            path = "meta.tags"
            value = rng.choice(["a", "b", "c"])
        ev = make_event(f"F{case_id:03d}-{i:04d}", "main", i + 1, op, path, value)
        events.append(ev)
        direct_apply(model, ev)

    errors, _ = validate_runtime(events, branches)
    if errors:
        failures.append("runtime validation failed: " + "; ".join(errors))
        return failures

    replayed, applied = replay(events, branches, "main")
    if replayed != model:
        failures.append("full replay != direct model")

    if len(applied) >= 2:
        cut = rng.randint(1, len(applied) - 1)
        prefix_state: dict[str, Any] = {}
        for ev in applied[:cut]:
            direct_apply(prefix_state, ev)
        through = str(applied[cut - 1].get("event_id"))
        resumed, _ = replay(events, branches, "main", base_state=prefix_state, start_after_event=through)
        if resumed != replayed:
            failures.append("snapshot-prefix replay != full replay")

    # Branch isolation property.
    fork = str(events[rng.randrange(len(events))].get("event_id"))
    branches["sandbox/a"] = {"parent": "main", "fork_event": fork, "status": "sandbox"}
    branches["sandbox/b"] = {"parent": "main", "fork_event": fork, "status": "sandbox"}
    a = make_event(f"F{case_id:03d}-A", "sandbox/a", 1, "set", "branch.marker", "A")
    b = make_event(f"F{case_id:03d}-B", "sandbox/b", 1, "set", "branch.marker", "B")
    events.extend([a, b])
    state_a, _ = replay(events, branches, "sandbox/a")
    state_b, _ = replay(events, branches, "sandbox/b")
    parent, _ = replay(events, branches, "main")
    if state_a.get("branch", {}).get("marker") != "A":
        failures.append("sandbox/a lost own write")
    if state_b.get("branch", {}).get("marker") != "B":
        failures.append("sandbox/b lost own write")
    if parent.get("branch", {}).get("marker") is not None:
        failures.append("sandbox write leaked into parent")

    # Effective histories of sibling branches must share exactly the parent prefix through fork.
    by = events_by_branch(events)
    hist_main = effective_events("main", branches, by)
    fork_idx = next(i for i, e in enumerate(hist_main) if str(e.get("event_id")) == fork)
    prefix_ids = [e.get("event_id") for e in hist_main[:fork_idx + 1]]
    for branch in ("sandbox/a", "sandbox/b"):
        hist = effective_events(branch, branches, by)
        if [e.get("event_id") for e in hist[:fork_idx + 1]] != prefix_ids:
            failures.append(f"{branch} inherited wrong prefix")
    return failures


def run_project_poetics_metadata_cases(rng: random.Random, cases: int = 12) -> list[str]:
    """Fuzz optional-artifact activation and scoped-poetics pointer safety.

    This exercises the real Project Doctor rather than inventing a parallel validator.
    Literary content remains opaque; only activation/pointer obligations are tested.
    """
    failures: list[str] = []
    script_root = Path(__file__).resolve().parents[1]
    template_path = script_root / "assets" / "project-templates" / "project-manifest-template.json"
    template = json.loads(template_path.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="lwa-poetics-fuzz-") as td:
        root = Path(td)
        (root / "state").mkdir(parents=True, exist_ok=True)
        (root / "planning" / "poetics-overrides").mkdir(parents=True, exist_ok=True)
        (root / "planning" / "optional").mkdir(parents=True, exist_ok=True)
        (root / "state" / "story-state.json").write_text(
            json.dumps({"current_chapter": 0, "authorial_unknowns": []}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (root / "planning" / "project-poetics.md").write_text("# Project Poetics\n", encoding="utf-8")

        for i in range(cases):
            manifest = copy.deepcopy(template)
            manifest["project_id"] = f"FUZZ-POETICS-{i:03d}"
            status = rng.choice(["active", "inactive", "provisional", "superseded"])
            optional_rel = f"planning/optional/capability-{i:03d}.md"
            optional_exists = rng.choice([True, False])
            optional_path = root / optional_rel
            if optional_path.exists():
                optional_path.unlink()
            if optional_exists:
                optional_path.write_text("# Optional Capability\n", encoding="utf-8")
            manifest["optional_artifacts"] = [{
                "kind": "poetics-capability",
                "path": optional_rel,
                "status": status,
                "scope": "project",
                "reason": "fuzz activation contract",
            }]

            override_rel = f"planning/poetics-overrides/chapter-{i:04d}.md"
            override_exists = rng.choice([True, False])
            override_path = root / override_rel
            if override_path.exists():
                override_path.unlink()
            if override_exists:
                override_path.write_text("# Scoped Project Poetics\n", encoding="utf-8")
            manifest["poetics_override_refs"] = [override_rel]

            errors, _warnings = project_doctor(root, manifest)
            active_missing_expected = status == "active" and not optional_exists
            override_missing_expected = not override_exists
            active_missing_seen = any("active optional artifact is missing" in x for x in errors)
            override_missing_seen = any("poetics override not found" in x for x in errors)
            if active_missing_seen != active_missing_expected:
                failures.append(
                    f"poetics fuzz {i}: active optional artifact expectation mismatch status={status} exists={optional_exists}"
                )
            if override_missing_seen != override_missing_expected:
                failures.append(
                    f"poetics fuzz {i}: override pointer expectation mismatch exists={override_exists}"
                )
            if failures:
                break
    return failures


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--iterations", type=int, default=100)
    p.add_argument("--steps", type=int, default=50)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rng = random.Random(args.seed)
    all_failures: list[dict[str, Any]] = []
    for case_id in range(1, args.iterations + 1):
        failures = run_case(rng, args.steps, case_id)
        if failures:
            all_failures.append({"case": case_id, "failures": failures})
            break
    poetics_failures = [] if all_failures else run_project_poetics_metadata_cases(rng)
    if poetics_failures:
        all_failures.append({"case": "project-poetics-metadata", "failures": poetics_failures})
    result = {
        "seed": args.seed,
        "iterations_requested": args.iterations,
        "steps": args.steps,
        "project_poetics_metadata_cases": 12,
        "failures": all_failures,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if all_failures:
            print(f"FAIL case {all_failures[0]['case']}: {'; '.join(all_failures[0]['failures'])}")
        else:
            print(f"PASS {args.iterations} seeded runtime fuzz cases x {args.steps} steps")
    return 1 if all_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
