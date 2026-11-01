#!/usr/bin/env python3
"""Validate a thin provenance envelope for scoped Project Poetics.

The envelope formalizes only authority, scope, parent lineage, hashes, lifecycle
status, and expiry. It never parses or schemas literary commitments inside the
scoped Markdown itself.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except Exception as exc:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[assignment]
    FormatChecker = None  # type: ignore[assignment]
    JSONSCHEMA_IMPORT_ERROR = exc
else:
    JSONSCHEMA_IMPORT_ERROR = None

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = SKILL_ROOT / "assets" / "project-schemas" / "scoped-project-poetics-envelope.schema.json"
ACTIVE_STATUS = "active"
SCOPE_KEYS = ("project_id", "arc", "chapter", "scene", "task")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def resolve_inside(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel.strip():
        raise ValueError("project-relative path must be a non-empty string")
    p = (root / rel).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {rel}") from exc
    return p


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_scope_value(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def parse_expiry(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("expires_at must be null or an ISO-8601 date-time string")
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        raise ValueError("expires_at must include a timezone offset")
    return parsed.astimezone(dt.timezone.utc)


def validate_shape(envelope: dict[str, Any], schema_path: Path = DEFAULT_SCHEMA) -> list[str]:
    if Draft202012Validator is None or FormatChecker is None:
        raise RuntimeError(f"jsonschema package is required: {JSONSCHEMA_IMPORT_ERROR}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for err in sorted(validator.iter_errors(envelope), key=lambda e: list(e.absolute_path)):
        loc = ".".join(str(x) for x in err.absolute_path) or "$"
        errors.append(f"{loc}: {err.message}")
    return errors


def verify_envelope(
    *,
    root: Path,
    content_ref: str,
    envelope_ref: str,
    project_manifest_ref: str | None = None,
    scope_context: dict[str, Any] | None = None,
    now: dt.datetime | None = None,
    require_active: bool = True,
) -> tuple[dict[str, Any], list[str]]:
    """Verify envelope provenance without interpreting literary content."""
    errors: list[str] = []
    root = root.resolve()
    content_path = resolve_inside(root, content_ref)
    envelope_path = resolve_inside(root, envelope_ref)
    if not content_path.is_file():
        return {}, [f"scoped Project Poetics content missing: {content_ref}"]
    if not envelope_path.is_file():
        return {}, [f"scoped Project Poetics envelope missing: {envelope_ref}"]

    try:
        envelope = load_json(envelope_path)
    except Exception as exc:
        return {}, [f"invalid scoped Project Poetics envelope: {exc}"]
    errors.extend(validate_shape(envelope))
    if errors:
        return envelope, errors

    authority_ref = str(envelope.get("authority_ref"))
    parent_ref = str(envelope.get("parent_ref"))
    try:
        authority_path = resolve_inside(root, authority_ref)
        parent_path = resolve_inside(root, parent_ref)
    except Exception as exc:
        return envelope, [str(exc)]
    if not authority_path.is_file():
        errors.append(f"authority_ref missing artifact: {authority_ref}")
    if not parent_path.is_file():
        errors.append(f"parent_ref missing artifact: {parent_ref}")
    if content_path == parent_path:
        errors.append("scoped Project Poetics content cannot be its own parent")

    hashes = envelope.get("hash", {})
    if isinstance(hashes, dict):
        expected_content = hashes.get("content_sha256")
        expected_parent = hashes.get("parent_sha256")
        if isinstance(expected_content, str) and sha256_file(content_path) != expected_content:
            errors.append("scoped Project Poetics content_sha256 mismatch")
        if parent_path.is_file() and isinstance(expected_parent, str) and sha256_file(parent_path) != expected_parent:
            errors.append("scoped Project Poetics parent_sha256 mismatch; derivative is stale")

    if require_active and envelope.get("status") != ACTIVE_STATUS:
        errors.append(f"scoped Project Poetics status must be active for consumption, got {envelope.get('status')!r}")

    try:
        expiry = parse_expiry(envelope.get("expires_at"))
    except Exception as exc:
        errors.append(str(exc))
        expiry = None
    if expiry is not None:
        instant = now or dt.datetime.now(dt.timezone.utc)
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=dt.timezone.utc)
        if expiry <= instant.astimezone(dt.timezone.utc):
            errors.append("scoped Project Poetics envelope has expired")

    manifest: dict[str, Any] | None = None
    if project_manifest_ref is not None:
        try:
            manifest_path = resolve_inside(root, project_manifest_ref)
            manifest = load_json(manifest_path)
        except Exception as exc:
            errors.append(f"could not load project manifest for poetics authority check: {exc}")
        if manifest is not None:
            canonical_paths = manifest.get("canonical_paths", {})
            canonical = canonical_paths.get("project_poetics") if isinstance(canonical_paths, dict) else None
            if not isinstance(canonical, str) or not canonical:
                errors.append("project manifest has no canonical Project Poetics owner")
            elif authority_ref != canonical:
                errors.append(
                    f"scoped Project Poetics authority_ref {authority_ref!r} disagrees with canonical owner {canonical!r}"
                )

    expected_scope = dict(scope_context or {})
    if manifest is not None and normalize_scope_value(expected_scope.get("project_id")) is None:
        expected_scope["project_id"] = manifest.get("project_id")
    declared_scope = envelope.get("scope", {})
    if isinstance(declared_scope, dict):
        for key in SCOPE_KEYS:
            declared = normalize_scope_value(declared_scope.get(key))
            if declared is None:
                continue
            actual = normalize_scope_value(expected_scope.get(key))
            if actual is None:
                errors.append(f"cannot verify declared scoped Project Poetics {key}={declared!r}; consumer supplied no {key}")
            elif actual != declared:
                errors.append(
                    f"scoped Project Poetics scope mismatch for {key}: envelope={declared!r} consumer={actual!r}"
                )

    return envelope, errors


def build_envelope(
    *,
    root: Path,
    content_ref: str,
    authority_ref: str,
    parent_ref: str,
    scope: dict[str, Any],
    status: str,
    expires_at: str | None,
) -> dict[str, Any]:
    """Create only provenance metadata; never derive literary commitments."""
    root = root.resolve()
    content = resolve_inside(root, content_ref)
    parent = resolve_inside(root, parent_ref)
    authority = resolve_inside(root, authority_ref)
    for label, path in (("content", content), ("parent", parent), ("authority", authority)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} artifact missing: {path}")
    envelope = {
        "schema_version": "1.0.0",
        "authority_ref": authority_ref,
        "scope": {key: normalize_scope_value(scope.get(key)) for key in SCOPE_KEYS},
        "parent_ref": parent_ref,
        "hash": {
            "content_sha256": sha256_file(content),
            "parent_sha256": sha256_file(parent),
        },
        "status": status,
        "expires_at": expires_at,
    }
    shape_errors = validate_shape(envelope)
    if shape_errors:
        raise ValueError("invalid envelope: " + "; ".join(shape_errors))
    parse_expiry(expires_at)
    return envelope


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify", help="verify provenance, hashes, authority, lifecycle, and declared scope")
    verify.add_argument("envelope", type=Path)
    verify.add_argument("--root", type=Path, required=True)
    verify.add_argument("--content-ref", required=True)
    verify.add_argument("--project-manifest")
    verify.add_argument("--project-id")
    verify.add_argument("--arc")
    verify.add_argument("--chapter")
    verify.add_argument("--scene")
    verify.add_argument("--task")
    verify.add_argument("--json", action="store_true")

    create = sub.add_parser("create", help="create a thin envelope from explicit authority/scope inputs")
    create.add_argument("output", type=Path)
    create.add_argument("--root", type=Path, required=True)
    create.add_argument("--content-ref", required=True)
    create.add_argument("--authority-ref", required=True)
    create.add_argument("--parent-ref", required=True)
    create.add_argument("--project-id", required=True)
    create.add_argument("--arc")
    create.add_argument("--chapter")
    create.add_argument("--scene")
    create.add_argument("--task")
    create.add_argument("--status", choices=("provisional", "active", "superseded", "revoked"), default="active")
    create.add_argument("--expires-at")

    args = p.parse_args()
    try:
        if args.command == "create":
            env = build_envelope(
                root=args.root,
                content_ref=args.content_ref,
                authority_ref=args.authority_ref,
                parent_ref=args.parent_ref,
                scope={
                    "project_id": args.project_id,
                    "arc": args.arc,
                    "chapter": args.chapter,
                    "scene": args.scene,
                    "task": args.task,
                },
                status=args.status,
                expires_at=args.expires_at,
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(env, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"created scoped Project Poetics envelope: {args.output}")
            return 0

        envelope_ref = str(args.envelope.resolve().relative_to(args.root.resolve())).replace("\\", "/")
        env, errors = verify_envelope(
            root=args.root,
            content_ref=args.content_ref,
            envelope_ref=envelope_ref,
            project_manifest_ref=args.project_manifest,
            scope_context={
                "project_id": args.project_id,
                "arc": args.arc,
                "chapter": args.chapter,
                "scene": args.scene,
                "task": args.task,
            },
        )
        if args.json:
            print(json.dumps({"passed": not errors, "errors": errors, "envelope": env}, ensure_ascii=False, indent=2))
        else:
            for err in errors:
                print(f"ERROR: {err}")
            print(f"summary: {len(errors)} error(s)")
        return 1 if errors else 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
