#!/usr/bin/env python3
"""Snapshot a project tree and audit changed files against allowed path prefixes.

Use this when the runtime cannot enforce per-role filesystem permissions natively.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_EXCLUDES = {".git", "__pycache__", ".DS_Store"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_rel(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def snapshot(root: Path, exclude_names: set[str]) -> dict[str, Any]:
    root = root.resolve()
    files: dict[str, Any] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_names]
        base = Path(dirpath)
        for name in filenames:
            if name in exclude_names or name.endswith(".pyc"):
                continue
            path = base / name
            rel = normalize_rel(str(path.relative_to(root)))
            files[rel] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    return {"schema_version": "1.0.0", "root": str(root), "files": files}


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        raise ValueError(f"invalid snapshot: {path}")
    return data


def allowed(path: str, prefixes: list[str]) -> bool:
    path = normalize_rel(path)
    for raw in prefixes:
        prefix = normalize_rel(raw).rstrip("/")
        if not prefix:
            continue
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[str]]:
    b = before["files"]
    a = after["files"]
    added = sorted(set(a) - set(b))
    deleted = sorted(set(b) - set(a))
    modified = sorted(p for p in set(a) & set(b) if a[p].get("sha256") != b[p].get("sha256"))
    return {"added": added, "modified": modified, "deleted": deleted}


def main() -> int:
    parser = argparse.ArgumentParser(description="Snapshot or audit project workspace changes")
    sub = parser.add_subparsers(dest="command", required=True)

    ps = sub.add_parser("snapshot", help="create a content-hash tree snapshot")
    ps.add_argument("root", type=Path)
    ps.add_argument("--output", type=Path, required=True)
    ps.add_argument("--exclude", action="append", default=[])

    pd = sub.add_parser("diff", help="compare snapshots and fail on unauthorized changes")
    pd.add_argument("before", type=Path)
    pd.add_argument("after", type=Path)
    pd.add_argument("--allow", action="append", default=[], help="allowed project-relative file or directory prefix")
    pd.add_argument("--report", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            excludes = set(DEFAULT_EXCLUDES) | set(args.exclude)
            data = snapshot(args.root, excludes)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"snapshotted {len(data['files'])} file(s)")
            return 0

        before = load(args.before)
        after = load(args.after)
        changes = diff(before, after)
        unauthorized: list[str] = []
        for category in ("added", "modified", "deleted"):
            for path in changes[category]:
                if not allowed(path, list(args.allow)):
                    unauthorized.append(f"{category}:{path}")
        result = {**changes, "allowed_prefixes": list(args.allow), "unauthorized": unauthorized}
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"changes: +{len(changes['added'])} ~{len(changes['modified'])} -{len(changes['deleted'])}")
        for item in unauthorized:
            print(f"ERROR: unauthorized change {item}")
        return 1 if unauthorized else 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
