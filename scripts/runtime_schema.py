#!/usr/bin/env python3
"""Validate and migrate machine-readable Narrative Runtime artifacts.

This tool governs representation/schema evolution only. It never changes story canon.
Committed event history is never rewritten by migrate-legacy; legacy events are read
through compatibility defaults/upcasters. Project Poetics and its scoped overrides are
project-level planning metadata, not Runtime canon/events, and are intentionally outside
this schema-migration surface.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from capability_probe import CapabilityError, require_profile

try:
    import jsonschema
except Exception as exc:  # pragma: no cover
    jsonschema = None
    JSONSCHEMA_IMPORT_ERROR = exc
else:
    JSONSCHEMA_IMPORT_ERROR = None

CURRENT_RUNTIME_VERSION = "3.0.0"
DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCRIPT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_DIR = SCRIPT_ROOT / "assets" / "runtime-schemas"
DEFAULT_TEMPLATE_DIR = SCRIPT_ROOT / "assets" / "runtime-templates"


class SchemaError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_semver(value: str) -> tuple[int, int, int]:
    core = value.split("+", 1)[0].split("-", 1)[0]
    parts = core.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise SchemaError(f"invalid semantic version: {value}")
    return tuple(int(p) for p in parts)  # type: ignore[return-value]


def require_jsonschema() -> None:
    if jsonschema is None:
        raise SchemaError(f"jsonschema package is required: {JSONSCHEMA_IMPORT_ERROR}")


def validate_instance(data: Any, schema_path: Path) -> list[str]:
    require_jsonschema()
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        loc = ".".join(str(x) for x in err.absolute_path) or "$"
        errors.append(f"{loc}: {err.message}")
    return errors


def schema_path(name: str, schema_dir: Path) -> Path:
    candidate = schema_dir / name
    if candidate.suffix != ".json":
        candidate = schema_dir / f"{name}.schema.json"
    if not candidate.is_file():
        raise SchemaError(f"schema not found: {candidate}")
    return candidate


def normalize_legacy_event(event: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(event)
    out.setdefault("schema_version", "1.0.0")
    out.setdefault("event_version", "1.0.0")
    return out


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SchemaError(f"{path}:{i}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise SchemaError(f"{path}:{i}: event must be a JSON object")
        rows.append(row)
    return rows


def safe_resolve(root: Path, rel: str) -> Path:
    path = (root / rel).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise SchemaError(f"manifest path escapes project root: {rel}") from exc
    return path


def validate_project(root: Path, manifest_path: Path, schema_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not manifest_path.is_file():
        return [f"missing runtime manifest: {manifest_path}"], warnings
    manifest = load_json(manifest_path)
    errors.extend(f"manifest {x}" for x in validate_instance(manifest, schema_path("runtime-manifest", schema_dir)))
    if errors:
        return errors, warnings

    version = str(manifest.get("runtime_schema_version", "0.0.0"))
    cur = parse_semver(CURRENT_RUNTIME_VERSION)
    got = parse_semver(version)
    if got[0] > cur[0]:
        errors.append(f"project runtime major {got[0]} is newer than supported major {cur[0]}; refuse to guess")
    elif got < cur:
        warnings.append(f"project runtime {version} is older than current {CURRENT_RUNTIME_VERSION}; migration may be available")

    paths = manifest.get("paths", {})
    known = {
        "events": "event",
        "invariants": "invariants",
        "narrative_debt": "narrative-debt",
    }
    for key, schema_name in known.items():
        rel = paths.get(key)
        if not isinstance(rel, str) or not rel:
            continue
        path = safe_resolve(root, rel)
        if not path.exists():
            if key == "events":
                errors.append(f"missing required artifact: {rel}")
            else:
                warnings.append(f"optional artifact not present: {rel}")
            continue
        if key == "events":
            event_schema = schema_path(schema_name, schema_dir)
            events = load_jsonl(path)
            from event_provenance import canonical_event, event_closure, promotion_errors
            idx = {str(e.get("event_id")): e for e in events}
            provenance_ref = paths.get("provenance")
            catalog = None
            if isinstance(provenance_ref, str):
                provenance_path = safe_resolve(root, provenance_ref)
                if provenance_path.is_file():
                    catalog = load_json(provenance_path)
                else:
                    warnings.append(f"missing provenance catalog: {provenance_ref}")
            for i, event in enumerate(events, start=1):
                normalized = normalize_legacy_event(event)
                for msg in validate_instance(normalized, event_schema):
                    errors.append(f"{rel}:{i} {msg}")
                messages = promotion_errors(event, idx, catalog)
                (errors if canonical_event(event) or manifest.get("strict_audit") is True else warnings).extend(messages)
        else:
            for msg in validate_instance(load_json(path), schema_path(schema_name, schema_dir)):
                errors.append(f"{rel} {msg}")

    for key, schema_name in (("branches", "branches"), ("dependencies", "dependencies")):
        rel = paths.get(key)
        if not isinstance(rel, str) or not rel:
            errors.append(f"missing required manifest path: {key}")
            continue
        artifact = safe_resolve(root, rel)
        if not artifact.is_file():
            errors.append(f"missing required artifact: {rel}")
            continue
        for msg in validate_instance(load_json(artifact), schema_path(schema_name, schema_dir)):
            errors.append(f"{rel} {msg}")

    snapshots_rel = paths.get("snapshots")
    if isinstance(snapshots_rel, str) and snapshots_rel:
        snap_dir = safe_resolve(root, snapshots_rel)
        if snap_dir.is_dir():
            for snap in sorted(snap_dir.glob("*.json")):
                for msg in validate_instance(load_json(snap), schema_path("snapshot", schema_dir)):
                    errors.append(f"{snap.relative_to(root)} {msg}")
    return errors, warnings


def backup_once(path: Path) -> Path:
    backup = path.with_suffix(path.suffix + ".pre-runtime-v3.bak")
    if not backup.exists():
        shutil.copy2(path, backup)
    return backup


def migrate_legacy(root: Path, apply: bool) -> dict[str, Any]:
    runtime = root / "runtime"
    events = runtime / "events.jsonl"
    branches = runtime / "branches.json"
    dependencies = runtime / "dependencies.json"
    manifest = runtime / "runtime-manifest.json"

    if not events.is_file() or not branches.is_file() or not dependencies.is_file():
        raise SchemaError("legacy migration expects runtime/events.jsonl, branches.json, and dependencies.json")

    operations: list[str] = []
    from_version = "legacy-unversioned"
    if manifest.exists():
        old_manifest = load_json(manifest)
        version = str(old_manifest.get("runtime_schema_version", "0.0.0"))
        if parse_semver(version) >= parse_semver(CURRENT_RUNTIME_VERSION):
            raise SchemaError(f"manifest already at runtime schema {version}")
        from_version = version
        operations.append(f"replace manifest {version} -> {CURRENT_RUNTIME_VERSION}")
    else:
        operations.append(f"create runtime/runtime-manifest.json at {CURRENT_RUNTIME_VERSION}")

    operations.append("normalize mutable branch-registry schema_version to current runtime contract")
    operations.append("normalize mutable dependency-registry schema_version to current runtime contract")
    operations.append("create empty invariant/debt registries if absent")
    operations.append("leave committed events byte-for-byte unchanged; read legacy events through compatibility defaults")

    result = {"apply": apply, "operations": operations, "runtime_schema_version": CURRENT_RUNTIME_VERSION}
    if not apply:
        return result

    runtime.mkdir(parents=True, exist_ok=True)
    if manifest.exists():
        backup_once(manifest)
    backup_once(branches)
    backup_once(dependencies)

    b = load_json(branches)
    if not isinstance(b, dict):
        raise SchemaError("branches.json must be an object")
    b["schema_version"] = CURRENT_RUNTIME_VERSION
    save_json(branches, b)

    d = load_json(dependencies)
    if not isinstance(d, dict):
        raise SchemaError("dependencies.json must be an object")
    d["schema_version"] = CURRENT_RUNTIME_VERSION
    save_json(dependencies, d)

    inv = runtime / "invariants.json"
    debt = runtime / "narrative-debt.json"
    if not inv.exists():
        save_json(inv, {"schema_version": "1.0.0", "invariants": []})
    if not debt.exists():
        save_json(debt, {"schema_version": "1.0.0", "items": []})

    template = load_json(DEFAULT_TEMPLATE_DIR / "runtime-manifest-template.json")
    template["project_id"] = root.name
    template["migration_history"] = [
        {
            "migration_id": "MIG-legacy-runtime-to-3.0.0",
            "from_version": from_version,
            "to_version": CURRENT_RUNTIME_VERSION,
            "status": "applied",
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "notes": "Mutable registries normalized; committed events were not rewritten.",
        }
    ]
    save_json(manifest, template)
    return result


def emit(errors: list[str], warnings: list[str], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
        return
    for msg in warnings:
        print(f"WARNING: {msg}")
    for msg in errors:
        print(f"ERROR: {msg}")
    print(f"summary: {len(errors)} error(s), {len(warnings)} warning(s)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("validate-artifact")
    q.add_argument("file", type=Path)
    q.add_argument("--schema", required=True, help="schema base name or JSON filename")
    q.add_argument("--schema-dir", type=Path, default=DEFAULT_SCHEMA_DIR)
    q.add_argument("--json", action="store_true")

    q = sub.add_parser("validate-project")
    q.add_argument("root", type=Path, help="project root containing runtime/runtime-manifest.json")
    q.add_argument("--manifest", type=Path)
    q.add_argument("--schema-dir", type=Path, default=DEFAULT_SCHEMA_DIR)
    q.add_argument("--json", action="store_true")

    q = sub.add_parser("migrate-legacy")
    q.add_argument("root", type=Path, help="project root whose legacy runtime/ directory should be inspected")
    q.add_argument("--apply", action="store_true")
    q.add_argument("--json", action="store_true")

    args = p.parse_args()
    try:
        require_profile("runtime")
    except CapabilityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    try:
        if args.cmd == "validate-artifact":
            data = load_json(args.file)
            errors = validate_instance(data, schema_path(args.schema, args.schema_dir))
            emit(errors, [], args.json)
            return 1 if errors else 0
        if args.cmd == "validate-project":
            root = args.root.resolve()
            manifest = args.manifest or (root / "runtime" / "runtime-manifest.json")
            errors, warnings = validate_project(root, manifest, args.schema_dir)
            emit(errors, warnings, args.json)
            return 1 if errors else 0
        if args.cmd == "migrate-legacy":
            result = migrate_legacy(args.root.resolve(), args.apply)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("APPLY" if args.apply else "DRY-RUN")
                for item in result["operations"]:
                    print(f"- {item}")
            return 0
    except (OSError, ValueError, SchemaError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
