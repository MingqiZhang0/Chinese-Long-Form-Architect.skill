#!/usr/bin/env python3
"""Select an honest orchestration fallback profile from runtime capabilities."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CAPABILITY_KEYS = {
    "native_subagents",
    "fresh_model_contexts",
    "isolated_agent_contexts",
    "persistent_files",
    "deterministic_tools",
    "isolated_workspaces",
    "filesystem_permission_enforcement",
    "independent_evaluator",
}


def load_obj(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("capabilities file must contain a JSON object")
    return data


def normalize_capabilities(data: dict[str, Any]) -> dict[str, bool]:
    src = data.get("capabilities", data)
    if not isinstance(src, dict):
        raise ValueError("capabilities must be an object")
    out: dict[str, bool] = {}
    for key in sorted(CAPABILITY_KEYS):
        value = src.get(key, False)
        if not isinstance(value, bool):
            raise ValueError(f"capability {key!r} must be boolean")
        out[key] = value
    return out


def select(cap: dict[str, bool]) -> dict[str, Any]:
    native = cap["native_subagents"]
    fresh = cap["fresh_model_contexts"]
    files = cap["persistent_files"]
    tools = cap["deterministic_tools"]
    independent = cap["independent_evaluator"]

    notes: list[str] = []
    if native:
        profile = "native-multi-agent"
        if cap["isolated_agent_contexts"]:
            grade = "agent-and-context-isolated"
            blind = True
        else:
            grade = "role-separated-shared-context"
            blind = False
            notes.append("Native subagents share model-visible context; blindness still requires an isolated/fresh context for the sensitive pass.")
            if fresh:
                notes.append("Fresh serial contexts are available as a clean-room fallback for blind Writer/Reader passes.")
    elif fresh and files:
        profile = "clean-room-serial"
        grade = "context-isolated"
        blind = True
        notes.append("No native subagents: use fresh role contexts and artifact handoffs serially.")
    elif files:
        profile = "soft-serial"
        grade = "procedural-only"
        blind = False
        notes.append("Fresh model context unavailable: role switching cannot erase previously seen secrets.")
    else:
        profile = "minimal-local"
        grade = "none"
        blind = False
        notes.append("Persistent pass artifacts unavailable: restrict claims to contained local tasks.")

    if not tools:
        notes.append("Deterministic validators unavailable: correctness checks are weaker and must be labeled accordingly.")
    if not cap["filesystem_permission_enforcement"]:
        notes.append("Write permissions require procedural enforcement plus changed-file audit.")
    if not independent:
        notes.append("Auditor may be role-separated without being model-independent.")

    return {
        "schema_version": "1.0.0",
        "capabilities": cap,
        "selected_profile": profile,
        "isolation_grade": grade,
        "blind_writer_supported": blind,
        "blind_reader_supported": blind,
        "independent_audit_supported": independent,
        "deterministic_validation_supported": tools,
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Select orchestration profile from capability JSON")
    parser.add_argument("capabilities", type=Path, help="JSON capability object or object with capabilities field")
    parser.add_argument("--output", type=Path, help="optional output JSON path")
    args = parser.parse_args()

    try:
        data = load_obj(args.capabilities)
        cap = normalize_capabilities(data)
        result = select(cap)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
