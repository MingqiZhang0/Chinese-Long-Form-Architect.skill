#!/usr/bin/env python3
"""Minimized production-readiness regressions; contains no real novel content.

All author messages below are synthetic TEST attestations, never live approvals.
The existing integration runner registers these tests for Core and Full.
"""
from __future__ import annotations
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from compile_context import compile_pack
from scoped_poetics import build_envelope
from prewriting_readiness import audit, refresh, digest, CHAPTER_FIELDS, WORLD_FIELDS, SCENE_FIELDS

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
def read(path): return json.loads(path.read_text(encoding="utf-8"))
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
def text(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode("utf-8"))
def require(ok, message):
    if not ok: raise AssertionError(message)
def cli(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)
def ready_cli(root, *args):
    return cli(SCRIPTS / "prewriting_readiness.py", root / "project-manifest.json", root / "planning/prewriting-readiness.json", "--root", root, "--json", *args)
def recompile(root):
    pack, m, errors = compile_pack(read(root / "context/context-index.json"), read(root / "context/writer-request.json"), root)
    require(not errors, f"test baseline compiler: {errors}")
    text(root / "context/writer-pack.md", pack)
    write(root / "context/writer-pack.manifest.json", m)
def volume_plan(root, count=1):
    path = root / "planning/evidence/long_horizon_architecture.json"
    v = read(path)
    v.update(planned_volume_count=count, later_volumes="NOT_APPLICABLE", author_decision_ref="authority/volumes.json")
    v["volumes"] = [{"number": 1, "planned_chapters": [1, 2, 3], "chapters": [{"id": f"C{n}", "number": n, **{k: f"Local {k} for chapter {n}; inherited continuity." for k in CHAPTER_FIELDS}} for n in (1, 2, 3)]}]
    for n in range(2, count + 1):
        keys = ("inherited_state", "core_pressure", "development_direction", "structural_change", "exit_direction") if n == 2 else ("long_term_function", "development_direction", "reason_for_volume", "interfaces")
        v["volumes"].append({"number": n, **{k: f"Volume {n} qualitative {k}." for k in keys}})
    write(path, v)
    write(root / "authority/volumes.json", {"source": "user", "action": "volume-plan", "message_id": "TEST-volume-plan", "message_order": 1, "statement": "TEST author chooses the volume count.", "planned_volume_count": count, "structure_sha256": digest({"planned_volume_count": count, "later_volumes": "NOT_APPLICABLE"})})
def capture(root):
    p = root / "planning/prewriting-readiness.json"
    r = refresh(root, read(p))
    r["gate"] = "REVIEW_READY"
    write(p, r)
def fixture(root, *, world=False, scene=False):
    proc = cli(SCRIPTS / "project_ops.py", "init", root, "--project-id", "TEST-PRODUCTION-READINESS")
    require(proc.returncode == 0, proc.stdout + proc.stderr)
    rp = root / "planning/prewriting-readiness.json"
    r = read(rp)
    r["causal_risks"] = {"world_systems": world, "time_loop_or_branch": False, "historical_grounding": False, "secret_asymmetry": False}
    for rec in r["risk_activation"].values(): rec["reason"] = "TEST current cone explicitly assessed; no relevant risk."
    r["risk_activation"]["long_horizon_architecture"] = {"decision": "ACTIVE", "reason": "TEST full first-volume preparation", "artifact_ref": r["artifacts"]["long_horizon_architecture"]["ref"]}
    r["long_horizon"]["required"] = True
    manifest = read(root / "project-manifest.json")
    manifest["optional_artifacts"] = [{"kind": "long-horizon-architecture", "path": r["artifacts"]["long_horizon_architecture"]["ref"], "status": "active"}]
    if world:
        r["risk_activation"]["world_model"] = {"decision": "ACTIVE", "reason": "TEST social causality", "artifact_ref": r["artifacts"]["world_model"]["ref"]}
        manifest["optional_artifacts"].append({"kind": "world-model", "path": r["artifacts"]["world_model"]["ref"], "status": "active"})
    write(root / "project-manifest.json", manifest)
    for kind, row in r["artifacts"].items():
        if kind == "world_model" and not world: continue
        row["status"] = "MATURE_FOR_DRAFT"
        text(root / row["ref"], f"# TEST {kind}\nCurrent-cone content reviewed for this local test.\n")
        ev = read(root / row["evidence_ref"])
        ev.update(coverage=["TEST concrete current-cone coverage."], open_items=[])
        if kind in {"cast", "writer_mission", "world_model"}: ev["writer_entry_ids"] = ["chapter-01-writer-mission"]
        if kind == "cast":
            ev.update(central_character="A", opening_character_ids=["A"], characters=[{"id": "A", "identity": "TEST actor A", "social_position": "Local worker", "life_anchor": "Current household and daily task", "state_scope": "scene-local"}])
            ev.pop("narrative_centers", None)
        if kind == "world_model": ev.update({k: f"TEST current-cone {k}." for k in WORLD_FIELDS})
        write(root / row["evidence_ref"], ev)
    volume_plan(root)
    text(root / "context/poetics.md", "# TEST Writer Poetics\nObserve ordinary local continuity.\n")
    env = build_envelope(root=root, content_ref="context/poetics.md", authority_ref="planning/project-poetics.md", parent_ref="planning/project-poetics.md", scope={"project_id": manifest["project_id"], "chapter": 1}, status="active", expires_at=None)
    write(root / "context/poetics.envelope.json", env)
    idx = {"entries": [{"id": "chapter-01-writer-mission", "path": "context/chapter-01-writer-mission.md", "kind": "mission", "roles": ["writer"], "visibility": "writer-visible", "chapter": 1, "required": True, "priority": 2000}]}
    req = read(root / "context/writer-request.json")
    req.update(scoped_project_poetics_ref="context/poetics.md", scoped_project_poetics_envelope_ref="context/poetics.envelope.json")
    if scene:
        r["risk_activation"]["scene_packets"] = {"decision": "ACTIVE", "reason": "TEST transaction risk"}
        text(root / "scenes/S1.md", "# TEST closed local Scene Packet\nEntry and planned transition.\n")
        ev = {"scene_id": "S1", "target_chapter": 1, "transaction_status": "PLANNED", "registration_ref": "state/scene-plans.json", "open_items": [], **{k: f"TEST bounded {k}." for k in SCENE_FIELDS}}
        write(root / "planning/evidence/scene-S1.json", ev)
        write(root / "state/scene-plans.json", {"scene_transactions": [{"scene_id": "S1", "status": "PLANNED", "evidence_sha256": hashlib.sha256((root / "planning/evidence/scene-S1.json").read_bytes()).hexdigest()}]})
        r["scene_transactions"] = [{"scene_id": "S1", "required": True, "status": "READY", "packet_ref": "scenes/S1.md", "evidence_ref": "planning/evidence/scene-S1.json", "context_entry_id": "scene-S1", "open_items": []}]
        text(root / "context/scene-S1.md", "# TEST safe scene\nOnly permitted local state.\n")
        idx["entries"].append({"id": "scene-S1", "path": "context/scene-S1.md", "kind": "scene-packet", "roles": ["writer"], "visibility": "writer-visible", "scenes": ["S1"]})
        req["required_scene_ids"] = ["S1"]
        req["required_ids"].append("scene-S1")
    write(root / "context/context-index.json", idx)
    write(root / "context/writer-request.json", req)
    r["writer_handoff"].update(compile_status="PASSED", semantic_kernel_status="PASSED")
    write(rp, r)
    recompile(root)
    capture(root)
    report = audit(root, root / "project-manifest.json", rp)
    require(report["ok"], f"TEST ready baseline failed: {report}")
def approve(root, message_id="TEST-approval-1"):
    frozen = ready_cli(root, "--action", "freeze")
    require(frozen.returncode == 0, frozen.stdout + frozen.stderr)
    r = read(root / "planning/prewriting-readiness.json")
    s = r["review_snapshot"]
    ev = {"source": "user", "action": "draft-approval", "message_id": message_id, "message_order": 10, "statement": "TEST explicit approval of presented snapshot.", "snapshot_id": s["id"], "review_fingerprint": s["fingerprint"], "target_chapter": 1, "draft_mode": r["draft_mode"]}
    write(root / "authority/approval.json", ev)
    proc = ready_cli(root, "--action", "bind-approval", "--approval-evidence", "authority/approval.json")
    require(proc.returncode == 0, proc.stdout + proc.stderr)
    proc = ready_cli(root, "--require-draft-permission")
    require(proc.returncode == 0 and json.loads(proc.stdout)["draft_permission"], proc.stdout + proc.stderr)
def report(root, **kwargs): return audit(root, root / "project-manifest.json", root / "planning/prewriting-readiness.json", **kwargs)
def blocked(root, code=None):
    r = report(root)
    require(not r["ok"] and not r["draft_permission"], f"invalid production readiness accepted: {r}")
    if code: require(any(x["code"] == code for x in r["findings"]), f"expected {code}: {r}")

def test_structural():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fixture(root, world=True, scene=True)
        rp = root / "planning/prewriting-readiness.json"
        original = read(rp)
        r = copy.deepcopy(original)
        r["risk_activation"]["world_model"]["decision"] = "INACTIVE"
        write(rp, r); blocked(root, "readiness.risk-activation.world_model")
        write(rp, original)
        castpath = root / original["artifacts"]["cast"]["evidence_ref"]
        cast = read(castpath)
        mutated = copy.deepcopy(cast); mutated["characters"] = []
        write(castpath, mutated); capture(root); blocked(root, "readiness.cast-centers")
        write(castpath, cast)
        mutated = copy.deepcopy(cast); mutated.pop("central_character"); mutated["narrative_centers"] = ["A", "B"]
        mutated["characters"].append({**cast["characters"][0], "id": "B", "identity": "TEST actor B"})
        write(castpath, mutated); capture(root)
        require(report(root)["ok"], "ensemble falsely requires a unique protagonist")
        sp = root / "planning/evidence/scene-S1.json"
        ev = read(sp); ev["rollback_or_branch"] = "TBD"
        write(sp, ev); capture(root); blocked(root, "readiness.scene-evidence")
        write(rp, original)
        r = copy.deepcopy(original); r["artifacts"]["cast"]["maturity"] = True
        r["artifacts"]["cast"]["status"] = "OPEN"
        write(rp, r); blocked(root)
        write(rp, original)
        # Existing Runtime owner validators are mandatory, not approximated by
        # Kernel replay or a PASS flag. A clean baseline precedes each mutation.
        mpath = root / "project-manifest.json"; m = read(mpath)
        for name in ("runtime-manifest", "branches", "invariants"):
            value = read(ROOT / f"assets/runtime-templates/{name}-template.json")
            if name == "runtime-manifest": value["project_id"] = m["project_id"]
            write(root / f"runtime/{name}.json", value)
        write(root / "runtime/narrative-debt.json", {"schema_version": "1.0.0", "items": []})
        write(root / "runtime/dependencies.json", {"schema_version": "3.0.0", "edges": []})
        text(root / "runtime/events.jsonl", (ROOT / "assets/runtime-templates/events-template.jsonl").read_text(encoding="utf-8"))
        m["canonical_paths"]["runtime_manifest"] = "runtime/runtime-manifest.json"
        m["enabled_subsystems"].extend(["narrative-runtime", "narrative-invariants"])
        m["last_committed_event"] = "EV-0001"; write(mpath, m)
        # Restore the scene evidence changed by the prior mutation.
        ev["rollback_or_branch"] = "TEST bounded rollback_or_branch."
        write(sp, ev)
        write(root / "state/scene-plans.json", {"scene_transactions": [{"scene_id": "S1", "status": "PLANNED", "evidence_sha256": hashlib.sha256(sp.read_bytes()).hexdigest()}]})
        recompile(root); capture(root)
        require(report(root)["ok"], f"Runtime baseline failed: {report(root)}")
        ivpath = root / "runtime/invariants.json"
        iv = read(ivpath); iv["invariants"] = [{"id": "TEST-bad-invariant", "kind": "always", "severity": "error", "condition": {"path": "meta.initialized", "op": "eq", "value": False}, "message": "TEST inconsistent hard rule."}]
        write(ivpath, iv); blocked(root, "readiness.runtime-invariants")
        iv["invariants"] = []; write(ivpath, iv)
        rtpath = root / "runtime/runtime-manifest.json"; rt = read(rtpath); rt["runtime_schema_version"] = "999.0.0"; write(rtpath, rt)
        blocked(root, "readiness.runtime-schema")

def test_volumes():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); fixture(root)
        for count in (1, 2, 4):
            volume_plan(root, count); capture(root)
            require(report(root)["ok"], f"author-approved {count}-volume plan rejected")
        vp = root / "planning/evidence/long_horizon_architecture.json"
        good = read(vp)
        v = copy.deepcopy(good); v["volumes"][0]["mapped_chapter_count"] = 20; v["volumes"][0]["planned_chapter_count"] = 20; v["volumes"][0]["planned_chapters"] = list(range(1, 21))
        write(vp, v)
        authority = read(root / "authority/volumes.json"); authority["plan_sha256"] = digest({k: val for k, val in v.items() if k != "author_decision_ref"}); write(root / "authority/volumes.json", authority)
        capture(root); blocked(root, "readiness.volume-evidence")
        volume_plan(root, 1)
        authority = read(root / "authority/volumes.json"); authority["source"] = "agent"; write(root / "authority/volumes.json", authority)
        capture(root); blocked(root, "readiness.volume-evidence")
        volume_plan(root, 2)
        v = read(vp); v["volumes"][1]["inherited_state"] = "TBD"; write(vp, v); capture(root); blocked(root, "readiness.volume-evidence")

def test_approval():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); fixture(root, world=True); approve(root)
        rp = root / "planning/prewriting-readiness.json"
        original = read(rp)
        r = copy.deepcopy(original); r["risk_activation"]["world_model"]["reason"] += " changed"
        write(rp, r); blocked(root, "readiness.approval-drift")
        bind = ready_cli(root, "--action", "bind-approval", "--approval-evidence", "authority/approval.json")
        require(bind.returncode != 0, "old author approval rebound after claim drift")
        write(rp, original)
        p = root / original["artifacts"]["world_model"]["ref"]
        text(p, p.read_text(encoding="utf-8") + "字")
        blocked(root, "readiness.maturity.world_model")
        refreshed = ready_cli(root, "--action", "refresh")
        require(refreshed.returncode == 0, refreshed.stdout)
        r = read(rp)
        require("author_approval" not in r and "review_snapshot" not in r and r["gate"] == "BLOCKED", "refresh preserved old approval")
        frozen = ready_cli(root, "--action", "freeze"); require(frozen.returncode == 0, frozen.stdout)
        require(ready_cli(root, "--action", "bind-approval", "--approval-evidence", "authority/approval.json").returncode != 0, "old evidence reused on new snapshot")
        approve(root, "TEST-approval-2")
        p = root / "planning/evidence/cast.json"
        ev = read(p); ev["coverage"].append("Changed structured evidence")
        write(p, ev); blocked(root, "readiness.maturity.cast")

def test_live_pack():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); fixture(root); approve(root)
        reqpath = root / "context/writer-request.json"
        idxpath = root / "context/context-index.json"
        req0, idx0 = read(reqpath), read(idxpath)
        pack0 = (root / "context/writer-pack.md").read_bytes()
        # Changes do not alter compiled Markdown but do alter authority/metadata.
        for mutate in ("request", "visibility", "provenance", "required", "source"):
            req, idx = copy.deepcopy(req0), copy.deepcopy(idx0)
            if mutate == "request": req["task_id"] = "NEW-TASK"
            if mutate == "visibility": idx["entries"][0]["visibility"] = "reader-visible"
            if mutate == "provenance":
                text(root / "context/source.md", "TEST non-Writer source.\n")
                idx["entries"].append({"id": "P", "path": "context/source.md", "roles": ["planner"], "visibility": "author-only"})
                idx["entries"][0]["derived_from"] = ["P"]
            if mutate == "required": req["required_ids"] = []
            if mutate == "source":
                p = root / "context/chapter-01-writer-mission.md"
                p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
            write(reqpath, req); write(idxpath, idx)
            pack, _, errors = compile_pack(idx, req, root)
            require(not errors and pack.encode("utf-8") == pack0, f"same-bytes regression did not preserve bytes: {mutate} {errors}")
            blocked(root, "readiness.pack-stale")
            write(reqpath, req0); write(idxpath, idx0)
            text(root / "context/chapter-01-writer-mission.md", "# TEST writer_mission\nCurrent-cone content reviewed for this local test.\n")
        for flag in ("--require-draft-permission", "--require-draft-ready"):
            require(ready_cli(root, flag, "--no-recompile").returncode != 0, "formal diagnostic bypass accepted")
        require(ready_cli(root, "--action", "start-chapter-1", "--no-recompile").returncode != 0, "start helper skip accepted")
        require(not report(root, recompile=False, require_draft_permission=True)["ok"], "API formal skip accepted")
        req = copy.deepcopy(req0); req["target_chapter"] = 2; write(reqpath, req); blocked(root, "readiness.request-target")
        req["target_chapter"] = 1; req["role"] = "planner"; write(reqpath, req); blocked(root, "readiness.request-target")
        write(reqpath, req0)
        require((root / "context/writer-pack.md").read_bytes() == pack0, "test modified saved pack bytes")
        stored = read(root / "context/writer-pack.manifest.json")
        require(hashlib.sha256(pack0).hexdigest() == stored["pack_sha256"], "saved UTF-8 LF pack integrity broken")
        output = root / "context/cli-pack.md"
        proc = cli(SCRIPTS / "compile_context.py", idxpath, reqpath, "--root", root, "--output", output, "--manifest-out", root / "context/cli-pack.manifest.json")
        require(proc.returncode == 0, proc.stdout + proc.stderr)
        require(output.read_bytes() == pack0 and b"\r\n" not in output.read_bytes() and hashlib.sha256(output.read_bytes()).hexdigest() == read(root / "context/cli-pack.manifest.json")["pack_sha256"], "real CLI newline/hash integrity failed")

def test_override():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); fixture(root, world=True, scene=True)
        rp = root / "planning/prewriting-readiness.json"
        r = read(rp); r["draft_mode"] = "FRAGMENTARY_OVERRIDE"; r["fragmentary_override"] = {"warning_ref": "authority/warning.json", "insistence_ref": "authority/insistence.json"}
        write(root / "authority/first.json", {"source": "user", "action": "early-draft-request", "message_id": "TEST-first", "message_order": 2, "target_chapter": 1, "statement": "TEST start chapter now."})
        warning = {"source": "assistant", "action": "refused", "message_order": 3, "first_request_ref": "authority/first.json", "target_chapter": 1, "statement": "TEST refused because remote volume planning is incomplete; finish it first.", "missing_volume_items": ["remaining chapter architecture"], "prose_generated": False}
        write(root / "authority/warning.json", warning)
        insist = {"source": "user", "action": "fragmentary-insistence", "message_id": "TEST-first", "message_order": 2, "statement": "TEST insist despite the warning.", "target_chapter": 1, "warning_sha256": hashlib.sha256((root / "authority/warning.json").read_bytes()).hexdigest()}
        write(root / "authority/insistence.json", insist); write(rp, r); capture(root); blocked(root, "readiness.override")
        insist.update(message_id="TEST-later", message_order=4); write(root / "authority/insistence.json", insist)
        # Only remote volume architecture is waived; current-cone artifacts remain.
        vp = root / "planning/evidence/long_horizon_architecture.json"
        v = read(vp); v["volumes"] = []; write(vp, v); capture(root)
        require(report(root)["ok"], f"legitimate two-message override rejected: {report(root)}")
        approve(root)
        r = read(rp); r["writer_handoff"]["compile_status"] = "BLOCKED"; write(rp, r); blocked(root, "readiness.compile-status")
        r["writer_handoff"]["compile_status"] = "PASSED"; write(rp, r)
        idxpath = root / "context/context-index.json"; idx = read(idxpath)
        idx["entries"][0]["derived_from"] = ["path/not-an-entry.md"]; write(idxpath, idx); blocked(root, "readiness.recompile")
        idx["entries"][0].pop("derived_from"); idx["entries"][0]["tainted_by"] = ["SECRET-TEST"]; write(idxpath, idx)
        reqpath = root / "context/writer-request.json"; req = read(reqpath); req["blocked_secret_ids"] = ["SECRET-TEST"]; write(reqpath, req); blocked(root, "readiness.recompile")
        idx["entries"][0].pop("tainted_by"); idx["entries"][0]["kind"] = "background"; write(idxpath, idx)
        req.pop("blocked_secret_ids"); write(reqpath, req); blocked(root, "readiness.mission-wiring")
        idx["entries"][0]["kind"] = "mission"; write(idxpath, idx)
        req["required_scene_ids"] = []; write(reqpath, req); blocked(root, "readiness.scene-evidence")
        req["required_scene_ids"] = ["S1"]; write(reqpath, req)
        statepath = root / "state/story-state.json"; state = read(statepath)
        state["knowledge_uses"] = [{"actor": "A", "fact": "TEST fact", "acquired": 5, "used": 1}]
        write(statepath, state); blocked(root, "readiness.story-state")
        state["knowledge_uses"] = []; write(statepath, state)
        r = read(rp); r["causal_risks"]["secret_asymmetry"] = True; write(rp, r)
        write(root / "context/secret-registry.json", {"secrets": []})
        req["secret_registry"] = "context/secret-registry.json"; write(reqpath, req)
        blocked(root, "readiness.secret-graph")

def test_campaign_scaffold():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); fixture(root)
        required = ("planning/character-roster.md", "planning/02-world-model.md", "planning/06-long-horizon-architecture.md", "planning/evidence/cast.json", "planning/evidence/long_horizon_architecture.json", "state/scene-plans.json", "planning/campaign-registration.json")
        require(all((root / ref).is_file() for ref in required), "deterministic scaffold omitted owner artifacts")
        campaign = root / "campaign"
        init = cli(SCRIPTS / "live_campaign.py", "init", campaign, "--project-root", root, "--campaign-id", "TEST-CAMPAIGN", "--track", "custom", "--target-chapters", "100", "--json")
        require(init.returncode == 0, init.stdout + init.stderr)
        cm = read(campaign / "campaign-manifest.json")
        require(cm["registration"]["project_chapter"] == 0 and not cm["checkpoint_index"], "initialization became chapter evidence")
        rp = root / "planning/prewriting-readiness.json"
        r = read(rp); r["campaign"]["required"] = True; write(rp, r); capture(root)
        blocked_start = ready_cli(root, "--action", "start-chapter-1", "--session-id", "TEST-premature")
        require(blocked_start.returncode != 0 and not read(campaign / "campaign-manifest.json")["session_index"], "campaign session bypassed formal readiness")
        approve(root)
        start = ready_cli(root, "--action", "start-chapter-1", "--session-id", "TEST-valid-session")
        require(start.returncode == 0 and json.loads(start.stdout).get("campaign_session_started") == "TEST-valid-session", start.stdout + start.stderr)
        require(report(root, require_draft_permission=True)["draft_permission"], "session ledger mutation incorrectly invalidated frozen prewriting registration")
        require(not read(campaign / "campaign-manifest.json")["checkpoint_index"], "session start became chapter evidence")
        r = read(rp); r["causal_risks"]["time_loop_or_branch"] = True; r["campaign"]["required"] = False; write(rp, r)
        blocked(root, "readiness.campaign-registration")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        text(root / "planning/character-roster.md", "Existing author roster\n")
        text(root / "planning/02-world-model.md", "Existing world model\n")
        proc = cli(SCRIPTS / "project_ops.py", "init", root, "--project-id", "TEST-PRESERVATION")
        require(proc.returncode == 0, proc.stdout + proc.stderr)
        require((root / "planning/character-roster.md").read_bytes() == b"Existing author roster\n" and (root / "planning/02-world-model.md").read_bytes() == b"Existing world model\n", "scaffold overwrote existing author content")
        r = read(root / "planning/prewriting-readiness.json")
        require(r["gate"] == "BLOCKED" and r["causal_risks"]["world_systems"] is None and r["artifacts"]["cast"]["status"] == "OPEN", "neutral scaffold fabricated readiness")
        r["readiness_version"] = "1.0.0"; write(root / "planning/prewriting-readiness.json", r)
        require(ready_cli(root, "--require-draft-permission").returncode != 0, "legacy readiness granted formal permission")

def test_provenance():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); fixture(root)
        idx = read(root / "context/context-index.json"); req = read(root / "context/writer-request.json")
        e = idx["entries"][0]
        parent = {"id": "P", "path": e["path"], "roles": ["planner"], "visibility": "author-only", "derived_from": ["missing-file.md"]}
        idx["entries"].append(parent); e["derived_from"] = ["P"]
        pack, _, errors = compile_pack(idx, req, root)
        require(not pack and any("provenance incomplete" in err for err in errors), "transitive missing parent was laundered")
        parent.pop("derived_from"); parent["tainted_by"] = ["SECRET-TEST"]
        try: compile_pack(idx, req, root)
        except ValueError as exc: require("unregistered" in str(exc), str(exc))
        else: raise AssertionError("empty registry accepted unknown secret taint")
        req["blocked_secret_ids"] = ["SECRET-TEST"]
        e.pop("derived_from")
        idx["entries"].append({"id": "poetics-source", "path": "context/poetics.md", "roles": ["planner"], "visibility": "author-only", "derived_from": ["P"]})
        pack, _, errors = compile_pack(idx, req, root)
        require(not pack and any("semantic secret taint" in err for err in errors), "scoped-poetics injection laundered secret provenance")
        idx["entries"].append(copy.deepcopy(e))
        try: compile_pack(idx, req, root)
        except ValueError as exc: require("unique" in str(exc), str(exc))
        else: raise AssertionError("duplicate canonical entry IDs accepted")

def test_poetics_dependencies():
    """Real readiness audit; synthetic project, never a live author approval."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); fixture(root)
        ep = root / "planning/evidence/project_poetics.json"
        original = read(ep)
        cases = [
            ("fair-clue-solution", True, "unresolved", None, False),
            ("confession-narrator-voice", True, "unresolved", None, False),
            ("metaphysical-ontology", False, "preserve-open", "Only recorded similarities and counterexamples; no scene needs a unique ontology.", True),
            ("action-obsession", False, "not-applicable", None, True),
        ]
        for name, required, handling, boundary, expected in cases:
            ev = copy.deepcopy(original)
            dep = {"id": name, "required_for_draft": required, "reason": "TEST project-specific declared closure / mediation dependency.", "handling": handling}
            if handling == "preserve-open":
                dep.update(evidence_ref="planning/project-poetics.md", compatibility_boundary=boundary)
            ev["draft_dependencies"] = [dep]
            write(ep, ev); capture(root)
            result = report(root)
            require(result["ok"] == expected, f"{name}: wrong conditional readiness: {result}")
            if not expected:
                require(any(x["code"] == "readiness.poetics-dependency" for x in result["findings"]), f"{name}: missing dependency finding")
        # Openness cannot launder a promised decided answer or an empty boundary.
        for required, boundary in ((True, "Bounded"), (False, "")):
            ev = copy.deepcopy(original)
            ev["draft_dependencies"] = [{"id": "ontology", "required_for_draft": required, "reason": "TEST", "handling": "preserve-open", "evidence_ref": "planning/project-poetics.md", "compatibility_boundary": boundary}]
            write(ep, ev); capture(root); blocked(root, "readiness.poetics-dependency")


TESTS = {"production-readiness-structural": test_structural, "production-readiness-volumes": test_volumes, "production-readiness-approval": test_approval, "production-readiness-live-pack": test_live_pack, "production-readiness-override": test_override, "production-readiness-provenance": test_provenance, "production-readiness-campaign-scaffold": test_campaign_scaffold, "production-readiness-poetics-dependencies": test_poetics_dependencies}
