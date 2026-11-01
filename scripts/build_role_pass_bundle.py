#!/usr/bin/env python3
"""Build a self-contained, role-scoped bundle for a fresh serial agent pass.

The bundle intentionally copies only the role card, task order, execution profile,
compiled context pack, and context manifest. It does not copy the whole project.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from orchestration_contract import ROLE_CLEARANCE


def load_obj(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_named(src: Path, dst_dir: Path, name: str) -> Path:
    dst = dst_dir / name
    shutil.copyfile(src, dst)
    return dst


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a clean-room role pass bundle")
    parser.add_argument("task_order", type=Path)
    parser.add_argument("context_pack", type=Path)
    parser.add_argument("context_manifest", type=Path)
    parser.add_argument("execution_profile", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pass-id", required=True)
    parser.add_argument("--fresh-context", action="store_true")
    parser.add_argument("--blindness-required", action="store_true")
    args = parser.parse_args()

    try:
        task = load_obj(args.task_order)
        manifest = load_obj(args.context_manifest)
        profile = load_obj(args.execution_profile)
        role = str(task.get("role", ""))
        if role not in ROLE_CLEARANCE:
            raise ValueError(f"unknown task role: {role!r}")
        if manifest.get("role") != role:
            raise ValueError("context manifest role does not match task role")
        branch = str(task.get("branch", manifest.get("branch", "main")))
        if str(manifest.get("branch", "main")) != branch:
            raise ValueError("context manifest branch does not match task branch")
        selected_profile = str(profile.get("selected_profile", ""))
        manifest_profile = manifest.get("execution_profile")
        if manifest_profile is not None and str(manifest_profile) != selected_profile:
            raise ValueError("context manifest execution_profile does not match profile")
        pack_hash = sha256_file(args.context_pack)
        if manifest.get("pack_sha256") and manifest.get("pack_sha256") != pack_hash:
            raise ValueError("context pack hash does not match context manifest")
        if args.blindness_required and manifest.get("strict_visibility") is not True:
            raise ValueError("blind pass requires a strict_visibility context manifest")
        if role == "writer":
            for field in ("scoped_project_poetics_ref", "scoped_project_poetics_envelope_ref"):
                task_value = task.get(field)
                manifest_value = manifest.get(field)
                if task_value is not None and task_value != manifest_value:
                    raise ValueError(f"task {field} does not match context manifest")
            if manifest.get("scoped_project_poetics_ref") and not manifest.get("scoped_project_poetics_envelope_ref"):
                raise ValueError("writer context has scoped Project Poetics without provenance envelope")

        skill_root = Path(__file__).resolve().parent.parent
        role_card = skill_root / "assets" / "orchestration" / "role-cards" / f"{role}.md"
        if not role_card.is_file():
            raise FileNotFoundError(f"role card missing: {role_card}")

        out = args.output_dir
        if out.exists() and any(out.iterdir()):
            raise ValueError(f"output directory is not empty: {out}")
        out.mkdir(parents=True, exist_ok=True)

        copied = {
            "role-card.md": copy_named(role_card, out, "role-card.md"),
            "task-order.json": copy_named(args.task_order, out, "task-order.json"),
            "execution-profile.json": copy_named(args.execution_profile, out, "execution-profile.json"),
            "context-pack.md": copy_named(args.context_pack, out, "context-pack.md"),
            "context-manifest.json": copy_named(args.context_manifest, out, "context-manifest.json"),
        }
        files = [
            {"name": name, "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for name, path in copied.items()
        ]
        bundle_manifest = {
            "schema_version": "1.0.0",
            "pass_id": args.pass_id,
            "task_id": task.get("task_id"),
            "role": role,
            "branch": branch,
            "execution_profile": selected_profile,
            "fresh_context": args.fresh_context,
            "blindness_required": args.blindness_required,
            "clearance": ROLE_CLEARANCE[role],
            "project_poetics_ref": manifest.get("project_poetics_ref"),
            "scoped_project_poetics_ref": manifest.get("scoped_project_poetics_ref"),
            "scoped_project_poetics_envelope_ref": manifest.get("scoped_project_poetics_envelope_ref"),
            "scoped_project_poetics_provenance": manifest.get("scoped_project_poetics_provenance"),
            "poetics_override_refs": manifest.get("poetics_override_refs", []),
            "active_capabilities": manifest.get("active_capabilities", []),
            "files": files,
            "instructions": [
                "Start this pass from a fresh model context when required by the execution profile.",
                "Use only the bundled role card, task order, and context pack as model-visible project inputs unless the task order explicitly authorizes escalation.",
                "Treat bundled scoped Project Poetics as authoritative literary planning for this pass; do not import inactive capabilities as generic best practices.",
                "Persist conclusions/artifacts; do not rely on hidden reasoning as a handoff.",
            ],
        }
        (out / "bundle-manifest.json").write_text(json.dumps(bundle_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"built role pass bundle: {out}")
        print(f"role={role} profile={selected_profile} files={len(files)} pack_sha256={pack_hash}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
