#!/usr/bin/env python3
"""Deterministic STC v0.1 semantic-conformance generator and assurance harness.

The generator constructs frozen latent challenges. Semantic acceptance is delegated
through a process boundary to scripts/stc_validator.py so Generator and Validator
do not share implementation functions.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from capability_probe import CapabilityError, require_profile

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts" / "stc_validator.py"
VERSION = "0.1.1"


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def labels_for(surface: str) -> dict[str, str]:
    tables = {
        "neutral": {
            "P1": "Actor One", "P2": "Actor Two", "K1": "Access Token", "C1": "Carry Case",
            "L0": "Origin", "L1": "Transfer Point", "L2": "Target",
            "R0": "Direct Route", "R1": "Connector A", "R2": "Controlled Route", "R3": "Slow Route", "R4": "Connector B",
        },
        "urban": {
            "P1": "林夏", "P2": "周岚", "K1": "门禁卡", "C1": "文件袋",
            "L0": "旧港站", "L1": "中环换乘厅", "L2": "档案中心",
            "R0": "旧港快线", "R1": "环城一号线", "R2": "内环专线", "R3": "地面慢线", "R4": "跨河接驳线",
        },
        "ancient": {
            "P1": "沈砚", "P2": "陆青", "K1": "路引", "C1": "封袋",
            "L0": "南驿", "L1": "中驿", "L2": "府库",
            "R0": "旧官道", "R1": "驿道东段", "R2": "内城关道", "R3": "外郭绕道", "R4": "河堤驿路",
        },
        "scifi": {
            "P1": "阿瑟-7", "P2": "岚-3", "K1": "权限芯片", "C1": "屏蔽盒",
            "L0": "外环港", "L1": "中继舱", "L2": "资料穹顶",
            "R0": "旧跃迁线", "R1": "环轨接驳线", "R2": "内圈授权线", "R3": "低速维护线", "R4": "磁索接驳线",
        },
    }
    return tables[surface]


def _rehash(challenge: dict[str, Any]) -> dict[str, Any]:
    challenge["certificate"]["validator_version"] = VERSION
    latent = copy.deepcopy(challenge)
    latent.pop("surface_views", None)
    latent.pop("certificate", None)
    challenge["certificate"]["latent_world_hash"] = canonical_hash(latent)
    unhashed = copy.deepcopy(challenge)
    unhashed["certificate"]["challenge_hash"] = ""
    challenge["certificate"]["challenge_hash"] = canonical_hash(unhashed)
    return challenge


def _candidate(challenge: dict[str, Any], actions: list[dict[str, Any]], surface: str | None = None) -> dict[str, Any]:
    return {
        "candidate_version": VERSION,
        "challenge_id": challenge["challenge_id"],
        "surface": surface,
        "actions": copy.deepcopy(actions),
    }


def generate(seed: int, surface_seed: int, chapter_count: int, gap: int) -> dict[str, Any]:
    if chapter_count < 60:
        raise ValueError("chapter_count must be >= 60 for the v0.1 longitudinal challenge")
    if gap < 25 or gap >= chapter_count:
        raise ValueError("gap must be >=25 and less than chapter_count")
    rng = random.Random(seed)

    # Narrative distance and diegetic time are intentionally separate coordinates.
    source_ch = rng.randint(3, max(3, chapter_count - gap - 2))
    trigger_ch = source_ch + gap
    transfer_ch = source_ch + max(3, gap // 4)
    close_ch = source_ch + max(5, gap // 2)
    if close_ch >= trigger_ch:
        close_ch = trigger_ch - 1

    source_time = rng.randint(1000, 5000)
    transfer_time = source_time + rng.randint(70, 150)
    close_time = transfer_time + rng.randint(30, 90)
    mission_time = close_time + rng.randint(120, 260)

    direct_time = rng.randint(28, 34)
    first_leg = rng.randint(17, 21)
    alt_first_leg = first_leg + rng.randint(0, 2)
    second_leg = rng.randint(22, 26)
    transfer_minutes = 1
    witness_time = first_leg + transfer_minutes + second_leg
    alt_time = alt_first_leg + transfer_minutes + second_leg
    max_valid = max(witness_time, alt_time)
    slack = rng.randint(3, 6)
    deadline_time = mission_time + max_valid + slack
    slow_time = max_valid + slack + rng.randint(4, 9)

    witness = [
        {"kind": "move", "actor": "P1", "route": "R1"},
        {"kind": "transfer", "entity": "C1", "from_holder": "P2", "to_holder": "P1", "minutes": transfer_minutes},
        {"kind": "move", "actor": "P1", "route": "R2"},
    ]
    alternative = [
        {"kind": "move", "actor": "P1", "route": "R4"},
        {"kind": "transfer", "entity": "C1", "from_holder": "P2", "to_holder": "P1", "minutes": transfer_minutes},
        {"kind": "move", "actor": "P1", "route": "R2"},
    ]

    challenge: dict[str, Any] = {
        "benchmark_version": VERSION,
        "challenge_id": f"STC-{seed}-{gap}",
        "latent_seed": seed,
        "surface_seed": surface_seed,
        "chapter_count": chapter_count,
        "authoritative_slice": ["presence", "custody", "containment", "reachability", "route-validity", "access", "temporal"],
        "chapter_anchors": [
            {"chapter": source_ch, "story_time": source_time},
            {"chapter": transfer_ch, "story_time": transfer_time},
            {"chapter": close_ch, "story_time": close_time},
            {"chapter": trigger_ch, "story_time": mission_time},
        ],
        "story_time_anchors": {
            "T_SOURCE": source_time,
            "T_TRANSFER": transfer_time,
            "T_CLOSE": close_time,
            "T_MISSION": mission_time,
            "T_DEADLINE": deadline_time,
        },
        "temporal_constraints": [
            {"from": "T_SOURCE", "to": "T_TRANSFER", "min_delta": 1, "max_delta": 600},
            {"from": "T_TRANSFER", "to": "T_CLOSE", "min_delta": 1, "max_delta": 300},
            {"from": "T_CLOSE", "to": "T_MISSION", "min_delta": 1, "max_delta": 600},
            {"from": "T_MISSION", "to": "T_DEADLINE", "min_delta": max_valid, "max_delta": max_valid + 12},
        ],
        "initial_state": {
            "actor_locations": {"P1": "L0", "P2": "L1"},
            "entity_holders": {"C1": "P1"},
            "containment": {"K1": "C1"},
        },
        "routes": [
            {"id": "R0", "from": "L0", "to": "L2", "min_travel_time": direct_time, "valid_from_time": 0, "valid_to_time": close_time - 1, "requires_entity": None},
            {"id": "R1", "from": "L0", "to": "L1", "min_travel_time": first_leg, "valid_from_time": 0, "valid_to_time": None, "requires_entity": None},
            {"id": "R4", "from": "L0", "to": "L1", "min_travel_time": alt_first_leg, "valid_from_time": 0, "valid_to_time": None, "requires_entity": None},
            {"id": "R2", "from": "L1", "to": "L2", "min_travel_time": second_leg, "valid_from_time": transfer_time, "valid_to_time": deadline_time, "requires_entity": "K1"},
            {"id": "R3", "from": "L0", "to": "L2", "min_travel_time": slow_time, "valid_from_time": 0, "valid_to_time": None, "requires_entity": None},
        ],
        "events": [
            {"chapter": transfer_ch, "story_time": transfer_time, "timepoint": "T_TRANSFER", "kind": "transfer", "entity": "C1", "from_holder": "P1", "to_holder": "P2"},
            {"chapter": close_ch, "story_time": close_time, "timepoint": "T_CLOSE", "kind": "route-close", "route": "R0"},
        ],
        "mission": {
            "mission_id": "M1",
            "chapter": trigger_ch,
            "start_time": mission_time,
            "deadline_time": deadline_time,
            "actor": "P1",
            "start_location": "L0",
            "target_location": "L2",
            "required_entity_at_end": "K1",
        },
        "probe_obligations": [
            {
                "probe_id": "PO-TEMP-01",
                "semantic_primitives": ["temporal"],
                "operation": "choose-action",
                "stress": {
                    "chapter_gap": gap,
                    "diegetic_gap_minutes": mission_time - source_time,
                    "dormancy_gap": max(0, trigger_ch - transfer_ch),
                    "update_count": 2,
                    "interference_count": 2,
                    "temporal_slack": deadline_time - mission_time - witness_time,
                    "coupling": 3,
                },
                "source_chapter": source_ch,
                "trigger_chapter": trigger_ch,
                "coverage_class": "required",
                "lifecycle": "ARMED",
                "binding": {"kind": "deadline", "mission": "M1"},
            },
            {
                "probe_id": "PO-CONT-01",
                "semantic_primitives": ["custody", "containment", "access"],
                "operation": "compose",
                "stress": {
                    "chapter_gap": gap,
                    "diegetic_gap_minutes": mission_time - transfer_time,
                    "dormancy_gap": max(0, trigger_ch - transfer_ch),
                    "update_count": 1,
                    "interference_count": 1,
                    "temporal_slack": deadline_time - mission_time - witness_time,
                    "coupling": 4,
                },
                "source_chapter": transfer_ch,
                "trigger_chapter": trigger_ch,
                "coverage_class": "required",
                "lifecycle": "ARMED",
                "binding": {"kind": "containment-propagation", "entity": "K1", "container": "C1", "actor": "P1"},
            },
            {
                "probe_id": "PO-ACCESS-01",
                "semantic_primitives": ["access", "reachability"],
                "operation": "reject-replan",
                "stress": {
                    "chapter_gap": gap,
                    "diegetic_gap_minutes": mission_time - close_time,
                    "dormancy_gap": max(0, trigger_ch - close_ch),
                    "update_count": 2,
                    "interference_count": 2,
                    "temporal_slack": deadline_time - mission_time - witness_time,
                    "coupling": 3,
                },
                "source_chapter": close_ch,
                "trigger_chapter": trigger_ch,
                "coverage_class": "diagnostic",
                "lifecycle": "ARMED",
                "binding": {"kind": "route-access", "route": "R2", "entity": "K1", "actor": "P1"},
            },
        ],
        "controlled_choices": [
            {
                "choice_id": "BC1",
                "at_time": mission_time,
                "actor": "P1",
                "non_anticipatory": True,
                "alternatives": [
                    {"alternative_id": "A", "prefix": [copy.deepcopy(witness[0])], "continuation": copy.deepcopy(witness[1:])},
                    {"alternative_id": "B", "prefix": [copy.deepcopy(alternative[0])], "continuation": copy.deepcopy(alternative[1:])},
                ],
            }
        ],
        "witness": copy.deepcopy(witness),
        "surface_views": {name: {"labels": labels_for(name)} for name in ("neutral", "urban", "ancient", "scifi")},
        "continuation_certificate": {
            "certificate_version": VERSION,
            "choice_results": [
                {
                    "choice_id": "BC1", "alternative_id": "A", "trajectory_hash": canonical_hash(witness),
                    "expected_valid": True, "expected_elapsed_minutes": witness_time, "expected_required_entity_holder": "P1",
                },
                {
                    "choice_id": "BC1", "alternative_id": "B", "trajectory_hash": canonical_hash(alternative),
                    "expected_valid": True, "expected_elapsed_minutes": alt_time, "expected_required_entity_holder": "P1",
                },
            ],
        },
        "certificate": {
            "solution_policy": "any-valid",
            "validator_version": VERSION,
            "oracle_isolated": True,
            "latent_world_hash": "pending",
            "challenge_hash": "",
        },
    }
    return _rehash(challenge)


def _run_validator(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(VALIDATOR), *argv], cwd=str(ROOT), text=True, capture_output=True)


def _validator_json_for_challenge(challenge: dict[str, Any], *, ignore_hashes: bool = False) -> tuple[int, dict[str, Any], str]:
    with tempfile.TemporaryDirectory(prefix="stc-validator-") as td:
        p = Path(td) / "challenge.json"
        p.write_text(json.dumps(challenge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        argv = ["challenge", str(p), "--json"]
        if ignore_hashes:
            argv.append("--ignore-hashes")
        run = _run_validator(argv)
        try:
            payload = json.loads(run.stdout) if run.stdout.strip() else {}
        except json.JSONDecodeError:
            payload = {}
        return run.returncode, payload, run.stderr



def _validator_batch(bundle: dict[str, Any]) -> tuple[int, dict[str, Any], str]:
    with tempfile.TemporaryDirectory(prefix="stc-batch-") as td:
        bp = Path(td) / "bundle.json"
        bp.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        run = _run_validator(["batch", str(bp), "--json"])
        try:
            payload = json.loads(run.stdout) if run.stdout.strip() else {}
        except json.JSONDecodeError:
            payload = {}
        return run.returncode, payload, run.stderr

def _validator_json_for_candidate(challenge: dict[str, Any], candidate: dict[str, Any]) -> tuple[int, dict[str, Any], str]:
    with tempfile.TemporaryDirectory(prefix="stc-candidate-") as td:
        cp = Path(td) / "challenge.json"
        ap = Path(td) / "candidate.json"
        cp.write_text(json.dumps(challenge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ap.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        run = _run_validator(["candidate", str(cp), str(ap), "--json"])
        try:
            payload = json.loads(run.stdout) if run.stdout.strip() else {}
        except json.JSONDecodeError:
            payload = {}
        return run.returncode, payload, run.stderr


def _naive_temporal_assignment_ok(challenge: dict[str, Any]) -> bool:
    anchors = challenge["story_time_anchors"]
    for row in challenge["temporal_constraints"]:
        if row["from"] not in anchors or row["to"] not in anchors:
            return False
        delta = int(anchors[row["to"]]) - int(anchors[row["from"]])
        if delta < int(row["min_delta"]) or delta > int(row["max_delta"]):
            return False
    return True


def _naive_elapsed(challenge: dict[str, Any], actions: list[dict[str, Any]]) -> int:
    route_times = {r["id"]: int(r["min_travel_time"]) for r in challenge["routes"]}
    elapsed = 0
    for action in actions:
        if action["kind"] == "move":
            elapsed += route_times[action["route"]]
        elif action["kind"] in {"transfer", "wait"}:
            elapsed += int(action.get("minutes", 0))
    return elapsed


def mutation_smoke(challenge: dict[str, Any]) -> list[dict[str, Any]]:
    cases: list[tuple[str, dict[str, Any]]] = []

    x = copy.deepcopy(challenge)
    x["mission"]["deadline_time"] = x["mission"]["start_time"] + 1
    x["story_time_anchors"]["T_DEADLINE"] = x["mission"]["deadline_time"]
    cases.append(("unsatisfiable-deadline", x))

    x = copy.deepcopy(challenge)
    for route in x["routes"]:
        if route["id"] == "R2":
            route["valid_to_time"] = x["mission"]["start_time"] + 1
    cases.append(("diegetic-route-window-cut", x))

    x = copy.deepcopy(challenge)
    x["events"] = [e for e in x["events"] if e["kind"] != "transfer"]
    cases.append(("stale-custody-history", x))

    x = copy.deepcopy(challenge)
    x["initial_state"]["entity_holders"]["K1"] = "P2"
    cases.append(("held-and-contained-conflict", x))

    x = copy.deepcopy(challenge)
    x["initial_state"]["containment"]["C1"] = "K1"
    cases.append(("containment-cycle", x))

    x = copy.deepcopy(challenge)
    x["temporal_constraints"][0]["max_delta"] = 0
    cases.append(("temporal-constraint-contradiction", x))

    x = copy.deepcopy(challenge)
    x["continuation_certificate"]["choice_results"][0]["trajectory_hash"] = "0" * 64
    cases.append(("false-continuation-certificate", x))

    x = copy.deepcopy(challenge)
    for probe in x["probe_obligations"]:
        if probe["binding"]["kind"] == "route-access":
            probe["binding"]["route"] = "R-NO-SUCH"
    cases.append(("probe-binding-dangling", x))

    x = copy.deepcopy(challenge)
    del x["surface_views"]["urban"]["labels"]["K1"]
    cases.append(("surface-label-loss", x))

    x = copy.deepcopy(challenge)
    x["surface_views"]["urban"]["labels"]["K1"] = x["surface_views"]["urban"]["labels"]["C1"]
    cases.append(("surface-label-collision", x))

    bundle = {
        "challenge_cases": [
            {
                "case_id": name,
                "challenge": mutant,
                "verify_hashes": False,
                "validate_witness": True,
                "expected_pass": False,
            }
            for name, mutant in cases
        ]
    }
    code, report, stderr = _validator_batch(bundle)
    by_id = {row.get("case_id"): row.get("result", {}) for row in report.get("rows", [])}
    rows: list[dict[str, Any]] = []
    for name, _ in cases:
        result = by_id.get(name, {})
        errs = result.get("errors", []) if isinstance(result, dict) else []
        rows.append({
            "operator": name,
            "killed": bool(result) and result.get("passed") is False and bool(errs),
            "errors": errs,
            "stderr": stderr.strip() if code not in (0, 1) else "",
        })
    return rows


def differential_checks(challenge: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [("witness", challenge["witness"])]
    for alt in challenge["controlled_choices"][0]["alternatives"]:
        candidates.append((f"choice-{alt['alternative_id']}", alt["prefix"] + alt["continuation"]))
    unique: list[tuple[str, list[dict[str, Any]]]] = []
    seen: set[str] = set()
    for name, actions in candidates:
        key = canonical_hash(actions)
        if key not in seen:
            seen.add(key)
            unique.append((name, actions))
    bundle = {
        "challenge_cases": [
            {"case_id": "temporal-network", "challenge": challenge, "expected_pass": True}
        ],
        "candidate_cases": [
            {
                "case_id": name,
                "challenge": challenge,
                "candidate": _candidate(challenge, actions),
                "validate_challenge": False,
                "expected_pass": True,
            }
            for name, actions in unique
        ]
    }
    code, report, stderr = _validator_batch(bundle)
    by_id = {row.get("case_id"): row.get("result", {}) for row in report.get("rows", [])}
    rows: list[dict[str, Any]] = []
    temporal = by_id.get("temporal-network", {})
    naive_temporal = _naive_temporal_assignment_ok(challenge)
    rows.append({
        "check": "validator-stn-vs-independent-exact-temporal-assignment",
        "passed": code == 0 and temporal.get("passed") is True and bool(temporal.get("temporal_consistent")) == naive_temporal and naive_temporal,
        "generator_exact_assignment": naive_temporal,
        "validator_stn_consistent": temporal.get("temporal_consistent"),
        "stderr": stderr.strip() if code not in (0, 1) else "",
    })
    for name, actions in unique:
        result = by_id.get(name, {})
        actual = (result.get("final") or {}).get("elapsed_minutes") if isinstance(result, dict) else None
        expected = _naive_elapsed(challenge, actions)
        rows.append({
            "check": f"validator-vs-independent-naive-elapsed:{name}",
            "passed": code == 0 and result.get("passed") is True and actual == expected,
            "expected_elapsed": expected,
            "validator_elapsed": actual,
            "stderr": stderr.strip() if code not in (0, 1) else "",
        })
    return rows


def _time_translate(challenge: dict[str, Any], delta: int) -> dict[str, Any]:
    x = copy.deepcopy(challenge)
    x["story_time_anchors"] = {k: int(v) + delta for k, v in x["story_time_anchors"].items()}
    for row in x["chapter_anchors"]:
        row["story_time"] = int(row["story_time"]) + delta
    for route in x["routes"]:
        route["valid_from_time"] = int(route["valid_from_time"]) + delta
        if route["valid_to_time"] is not None:
            route["valid_to_time"] = int(route["valid_to_time"]) + delta
    for event in x["events"]:
        event["story_time"] = int(event["story_time"]) + delta
    x["mission"]["start_time"] = int(x["mission"]["start_time"]) + delta
    x["mission"]["deadline_time"] = int(x["mission"]["deadline_time"]) + delta
    for choice in x["controlled_choices"]:
        choice["at_time"] = int(choice["at_time"]) + delta
    return _rehash(x)


def _chapter_translate(challenge: dict[str, Any], delta: int) -> dict[str, Any]:
    x = copy.deepcopy(challenge)
    x["chapter_count"] = int(x["chapter_count"]) + delta
    for row in x["chapter_anchors"]:
        row["chapter"] = int(row["chapter"]) + delta
    for event in x["events"]:
        event["chapter"] = int(event["chapter"]) + delta
    x["mission"]["chapter"] = int(x["mission"]["chapter"]) + delta
    for probe in x["probe_obligations"]:
        probe["source_chapter"] = int(probe["source_chapter"]) + delta
        probe["trigger_chapter"] = int(probe["trigger_chapter"]) + delta
    return _rehash(x)


def _event_chapter_metadata_perturb(challenge: dict[str, Any]) -> dict[str, Any]:
    x = copy.deepcopy(challenge)
    mission_chapter = int(x["mission"]["chapter"])
    new_chapters: dict[int, int] = {}
    for offset, event in enumerate(x["events"], 1):
        old_story_time = int(event["story_time"])
        new_chapter = mission_chapter + offset
        event["chapter"] = new_chapter
        new_chapters[old_story_time] = new_chapter
    for row in x["chapter_anchors"]:
        st = int(row["story_time"])
        if st in new_chapters:
            row["chapter"] = new_chapters[st]
    x["chapter_count"] = max(int(x["chapter_count"]), mission_chapter + len(x["events"]) + 1)
    return _rehash(x)


def metamorphic_checks(challenge: dict[str, Any]) -> list[dict[str, Any]]:
    base_candidate = _candidate(challenge, challenge["witness"])
    shifted = _time_translate(challenge, 10000)
    chapter_shifted = _chapter_translate(challenge, 3)
    event_chapter_perturbed = _event_chapter_metadata_perturb(challenge)
    bundle = {
        "challenge_cases": [
            {"case_id": "base-challenge", "challenge": challenge, "expected_pass": True},
            {"case_id": "event-chapter-perturb-challenge", "challenge": event_chapter_perturbed, "expected_pass": True},
        ],
        "candidate_cases": [
            {"case_id": "base", "challenge": challenge, "candidate": base_candidate, "validate_challenge": False, "expected_pass": True},
            {"case_id": "time-shift", "challenge": shifted, "candidate": _candidate(shifted, shifted["witness"]), "validate_challenge": False, "expected_pass": True},
            {"case_id": "chapter-shift", "challenge": chapter_shifted, "candidate": _candidate(chapter_shifted, chapter_shifted["witness"]), "validate_challenge": False, "expected_pass": True},
            {"case_id": "event-chapter-perturb", "challenge": event_chapter_perturbed, "candidate": _candidate(event_chapter_perturbed, event_chapter_perturbed["witness"]), "validate_challenge": False, "expected_pass": True},
        ],
        "roundtrip_cases": [
            {"case_id": f"surface-{surface}", "challenge": challenge, "candidate": base_candidate, "surface": surface, "expected_pass": True}
            for surface in challenge["surface_views"]
        ],
    }
    code, report, stderr = _validator_batch(bundle)
    by_id = {row.get("case_id"): row.get("result", {}) for row in report.get("rows", [])}
    base = by_id.get("base", {})
    base_sig = base.get("semantic_signature") if isinstance(base, dict) else None
    time_report = by_id.get("time-shift", {})
    chapter_report = by_id.get("chapter-shift", {})
    event_chapter_report = by_id.get("event-chapter-perturb", {})
    event_challenge_report = by_id.get("event-chapter-perturb-challenge", {})
    rows: list[dict[str, Any]] = [
        {
            "relation": "uniform-diegetic-time-translation",
            "passed": code == 0 and base.get("passed") is True and time_report.get("passed") is True and time_report.get("semantic_signature") == base_sig,
            "source_signature": base_sig,
            "followup_signature": time_report.get("semantic_signature"),
            "stderr": stderr.strip() if code not in (0, 1) else "",
        },
        {
            "relation": "narrative-chapter-translation-does-not-change-diegetic-legality",
            "passed": code == 0 and base.get("passed") is True and chapter_report.get("passed") is True and chapter_report.get("semantic_signature") == base_sig,
            "source_signature": base_sig,
            "followup_signature": chapter_report.get("semantic_signature"),
            "stderr": stderr.strip() if code not in (0, 1) else "",
        },
        {
            "relation": "event-chapter-metadata-perturbation-does-not-change-diegetic-state",
            "passed": code == 0 and event_challenge_report.get("passed") is True and event_chapter_report.get("passed") is True and event_chapter_report.get("semantic_signature") == base_sig,
            "source_signature": base_sig,
            "followup_signature": event_chapter_report.get("semantic_signature"),
            "event_chapters_after_mission": all(int(e["chapter"]) > int(event_chapter_perturbed["mission"]["chapter"]) for e in event_chapter_perturbed["events"]),
            "stderr": stderr.strip() if code not in (0, 1) else "",
        },
    ]
    surface_hashes: dict[str, str] = {}
    surface_ok = by_id.get("base-challenge", {}).get("passed") is True
    for surface in challenge["surface_views"]:
        rr = by_id.get(f"surface-{surface}", {})
        surface_ok = surface_ok and rr.get("passed") is True
        surface_hashes[surface] = str(rr.get("roundtrip_actions_hash"))
    rows.append({
        "relation": "strict-surface-roundtrip-and-behavioral-conservation",
        "passed": code == 0 and surface_ok and len(set(surface_hashes.values())) == 1,
        "roundtrip_action_hashes": surface_hashes,
    })
    return rows


def assurance_report(challenge: dict[str, Any]) -> dict[str, Any]:
    mutations = mutation_smoke(challenge)
    differential = differential_checks(challenge)
    metamorphic = metamorphic_checks(challenge)
    return {
        "passed": all(r["killed"] for r in mutations) and all(r["passed"] for r in differential) and all(r["passed"] for r in metamorphic),
        "validator_independent_process": True,
        "mutation": {"killed": sum(bool(r["killed"]) for r in mutations), "total": len(mutations), "rows": mutations},
        "differential": {"passed": sum(bool(r["passed"]) for r in differential), "total": len(differential), "rows": differential},
        "metamorphic": {"passed": sum(bool(r["passed"]) for r in metamorphic), "total": len(metamorphic), "rows": metamorphic},
    }


def selftest(seed_count: int = 20, start_seed: int = 1) -> dict[str, Any]:
    if seed_count < 1:
        raise ValueError("seed_count must be >= 1")
    if start_seed < 0:
        raise ValueError("start_seed must be >= 0")
    challenges: list[dict[str, Any]] = []
    challenge_cases: list[dict[str, Any]] = []
    candidate_cases: list[dict[str, Any]] = []
    for seed in range(start_seed, start_seed + seed_count):
        challenge = generate(seed, seed + 100000, 80, 40)
        challenges.append(challenge)
        challenge_cases.append({"case_id": f"seed-{seed}", "challenge": challenge, "expected_pass": True})
        if len(candidate_cases) < min(3, seed_count):
            # Deliberately validate a legal trajectory that is neither the planted witness
            # nor one of the registered Bounded-Choice certificate trajectories.
            arbitrary_actions = copy.deepcopy(challenge["witness"])
            arbitrary_actions.insert(1, {"kind": "wait", "minutes": 1})
            candidate_cases.append({
                "case_id": f"seed-{seed}-arbitrary-unregistered",
                "challenge": challenge,
                "candidate": _candidate(challenge, arbitrary_actions),
                "expected_pass": True,
                "validate_challenge": False,
            })
    code, batch, stderr = _validator_batch({"challenge_cases": challenge_cases, "candidate_cases": candidate_cases})
    if code != 0 or not batch.get("passed"):
        raise AssertionError(("independent-validator-batch", batch, stderr))
    assurance = assurance_report(challenges[0])
    if not assurance["passed"]:
        raise AssertionError(("assurance", assurance))
    return {
        "passed": True,
        "version": VERSION,
        "seed_count": seed_count,
        "challenges_validated_by_independent_process": seed_count,
        "arbitrary_candidates_validated": len(candidate_cases),
        "assurance": {
            "mutation_killed": assurance["mutation"]["killed"],
            "mutation_total": assurance["mutation"]["total"],
            "differential_passed": assurance["differential"]["passed"],
            "differential_total": assurance["differential"]["total"],
            "metamorphic_passed": assurance["metamorphic"]["passed"],
            "metamorphic_total": assurance["metamorphic"]["total"],
        },
    }


def emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="STC v0.1 semantic-conformance generator and assurance harness")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--seed", type=int, required=True)
    g.add_argument("--surface-seed", type=int)
    g.add_argument("--chapters", type=int, default=80)
    g.add_argument("--gap", type=int, default=40)
    g.add_argument("--out", type=Path)
    v = sub.add_parser("validate", help="compatibility proxy to the independent challenge validator")
    v.add_argument("challenge", type=Path)
    c = sub.add_parser("candidate", help="validate an arbitrary candidate trajectory")
    c.add_argument("challenge", type=Path)
    c.add_argument("candidate", type=Path)
    c.add_argument("--json", action="store_true")
    r = sub.add_parser("render")
    r.add_argument("challenge", type=Path)
    r.add_argument("--surface", choices=["neutral", "urban", "ancient", "scifi"], default="neutral")
    rt = sub.add_parser("roundtrip")
    rt.add_argument("challenge", type=Path)
    rt.add_argument("candidate", type=Path)
    rt.add_argument("--surface", choices=["neutral", "urban", "ancient", "scifi"], required=True)
    rt.add_argument("--json", action="store_true")
    m = sub.add_parser("mutation-smoke")
    m.add_argument("challenge", type=Path)
    a = sub.add_parser("assurance")
    a.add_argument("challenge", type=Path)
    a.add_argument("--json", action="store_true")
    st = sub.add_parser("selftest")
    st.add_argument("--seeds", type=int, default=20)
    st.add_argument("--start-seed", type=int, default=1)
    st.add_argument("--json", action="store_true")
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        require_profile("stc")
    except CapabilityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.cmd == "generate":
        try:
            challenge = generate(args.seed, args.surface_seed if args.surface_seed is not None else args.seed + 100000, args.chapters, args.gap)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        code, report, stderr = _validator_json_for_challenge(challenge)
        if code != 0 or not report.get("passed"):
            print(f"ERROR: independent validator rejected generated challenge: {report} {stderr}", file=sys.stderr)
            return 1
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(challenge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(args.out)
        else:
            emit(challenge)
        return 0
    if args.cmd == "validate":
        run = _run_validator(["challenge", str(args.challenge)])
        sys.stdout.write(run.stdout)
        sys.stderr.write(run.stderr)
        return run.returncode
    if args.cmd == "candidate":
        argv = ["candidate", str(args.challenge), str(args.candidate)]
        if args.json:
            argv.append("--json")
        run = _run_validator(argv)
        sys.stdout.write(run.stdout)
        sys.stderr.write(run.stderr)
        return run.returncode
    if args.cmd == "render":
        run = _run_validator(["render", str(args.challenge), "--surface", args.surface])
        sys.stdout.write(run.stdout)
        sys.stderr.write(run.stderr)
        return run.returncode
    if args.cmd == "roundtrip":
        argv = ["roundtrip", str(args.challenge), str(args.candidate), "--surface", args.surface]
        if args.json:
            argv.append("--json")
        run = _run_validator(argv)
        sys.stdout.write(run.stdout)
        sys.stderr.write(run.stderr)
        return run.returncode
    if args.cmd in {"mutation-smoke", "assurance"}:
        challenge = json.loads(args.challenge.read_text(encoding="utf-8"))
        if args.cmd == "mutation-smoke":
            rows = mutation_smoke(challenge)
            emit(rows)
            return 0 if all(row["killed"] for row in rows) else 1
        report = assurance_report(challenge)
        if args.json:
            emit(report)
        else:
            print(f"OK: STC assurance {'PASS' if report['passed'] else 'FAIL'}; mutation={report['mutation']['killed']}/{report['mutation']['total']} differential={report['differential']['passed']}/{report['differential']['total']} metamorphic={report['metamorphic']['passed']}/{report['metamorphic']['total']}")
        return 0 if report["passed"] else 1
    if args.cmd == "selftest":
        try:
            report = selftest(args.seeds, args.start_seed)
        except (ValueError, AssertionError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        if args.json:
            emit(report)
        else:
            a = report["assurance"]
            print(f"OK: STC v0.1 semantic-conformance selftest passed ({args.seeds} seeds; arbitrary candidates={report['arbitrary_candidates_validated']}; mutation={a['mutation_killed']}/{a['mutation_total']}; differential={a['differential_passed']}/{a['differential_total']}; metamorphic={a['metamorphic_passed']}/{a['metamorphic_total']})")
        return 0
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
