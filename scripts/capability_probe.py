#!/usr/bin/env python3
"""Cheap startup capability/dependency probe for deterministic Skill tooling.

The probe uses only the Python standard library so it can explain a missing or
incompatible dependency before Runtime/Project/Intensity/STC work starts.
"""

from __future__ import annotations

import argparse
import functools
import importlib
import importlib.metadata
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_FILE = ROOT / "requirements.txt"
JSONSCHEMA_SPEC = "jsonschema>=4.18.0,<5.0.0"
MIN_JSONSCHEMA = (4, 18, 0)
MAX_JSONSCHEMA = (5, 0, 0)

PROFILE_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "base": (),
    "project": ("jsonschema",),
    "runtime": ("jsonschema",),
    "reconcile": ("jsonschema",),
    "intensity": ("jsonschema",),
    "stc": ("jsonschema",),
    "maintenance": ("jsonschema",),
    "all": ("jsonschema",),
}


class CapabilityError(RuntimeError):
    pass


def version_tuple(value: str) -> tuple[int, int, int]:
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", value)
    if not match:
        raise CapabilityError(f"cannot parse dependency version: {value!r}")
    return tuple(int(part or 0) for part in match.groups(default="0"))  # type: ignore[return-value]


@functools.lru_cache(maxsize=1)
def probe_jsonschema() -> dict[str, Any]:
    rec: dict[str, Any] = {
        "capability": "jsonschema-draft-2020-12",
        "requirement": JSONSCHEMA_SPEC,
        "passed": False,
    }
    try:
        installed = importlib.metadata.version("jsonschema")
        rec["installed_version"] = installed
        parsed = version_tuple(installed)
        if parsed < MIN_JSONSCHEMA or parsed >= MAX_JSONSCHEMA:
            rec["error"] = f"installed jsonschema {installed} is outside supported range {JSONSCHEMA_SPEC}"
            return rec
        module = importlib.import_module("jsonschema")
        validator_cls = getattr(module, "Draft202012Validator", None)
        if validator_cls is None:
            rec["error"] = "jsonschema.Draft202012Validator is unavailable"
            return rec
        validator_cls.check_schema({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"})
    except importlib.metadata.PackageNotFoundError:
        rec["error"] = f"jsonschema is not installed; install {JSONSCHEMA_SPEC}"
        return rec
    except Exception as exc:
        rec["error"] = f"jsonschema capability check failed: {exc}"
        return rec
    rec["passed"] = True
    return rec


def probe_profile(profile: str) -> dict[str, Any]:
    if profile not in PROFILE_DEPENDENCIES:
        raise CapabilityError(f"unknown capability profile: {profile}")
    checks: list[dict[str, Any]] = []
    for dep in PROFILE_DEPENDENCIES[profile]:
        if dep == "jsonschema":
            checks.append(probe_jsonschema())
    passed = all(bool(row.get("passed")) for row in checks)
    return {
        "profile": profile,
        "passed": passed,
        "requirements_file": str(REQUIREMENTS_FILE),
        "checks": checks,
    }


def require_profile(profile: str) -> None:
    result = probe_profile(profile)
    if result["passed"]:
        return
    messages = [str(row.get("error")) for row in result["checks"] if not row.get("passed")]
    detail = "; ".join(messages) or "unknown capability failure"
    raise CapabilityError(f"capability preflight failed for {profile}: {detail}; declared dependencies: {REQUIREMENTS_FILE}")


def selftest() -> None:
    assert version_tuple("4.18") == (4, 18, 0)
    assert version_tuple("4.26.0") == (4, 26, 0)
    assert "jsonschema" in PROFILE_DEPENDENCIES["runtime"]
    assert PROFILE_DEPENDENCIES["base"] == ()
    result = probe_profile("all")
    assert result["passed"], result
    assert REQUIREMENTS_FILE.read_text(encoding="utf-8").strip() == JSONSCHEMA_SPEC


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    check = sub.add_parser("check", help="check a cheap dependency/capability profile")
    check.add_argument("profile", nargs="?", default="all", choices=sorted(PROFILE_DEPENDENCIES))
    check.add_argument("--json", action="store_true")
    sub.add_parser("requirements", help="print declared runtime requirements")
    sub.add_parser("selftest")
    args = p.parse_args()

    if args.cmd == "requirements":
        print(REQUIREMENTS_FILE.read_text(encoding="utf-8"), end="")
        return 0
    if args.cmd == "selftest":
        selftest()
        print("OK: capability probe selftest passed")
        return 0
    if args.cmd == "check":
        result = probe_profile(args.profile)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif result["passed"]:
            versions = ", ".join(
                f"{row['capability']}={row.get('installed_version', 'available')}" for row in result["checks"]
            ) or "no external dependencies required"
            print(f"OK: capability profile {args.profile}: {versions}")
        else:
            for row in result["checks"]:
                if not row.get("passed"):
                    print(f"ERROR: {row.get('error')}", file=sys.stderr)
            print(f"HINT: install dependencies from {REQUIREMENTS_FILE}", file=sys.stderr)
        return 0 if result["passed"] else 2
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
