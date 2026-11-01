#!/usr/bin/env python3
"""Validate and query the Skill-wide external research ledger."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "assets/external-research-ledger.json"
SCHEMA_PATH = ROOT / "assets/external-research-ledger.schema.json"
CNE_VIEW_PATH = ROOT / "assets/chinese-narrative-eval/research-ledger.json"
MARKER_RE = re.compile(r"\[research:([a-z0-9][a-z0-9-]*)\]")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def emit(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    elif isinstance(value, str):
        print(value)
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2))


def load_ledger() -> dict[str, Any]:
    value = load_json(LEDGER_PATH)
    if not isinstance(value, dict):
        raise ValueError("external research ledger root must be an object")
    return value


def source_map(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = ledger.get("sources", [])
    return {str(row.get("id")): row for row in rows if isinstance(row, dict) and row.get("id")}


def scan_markers() -> dict[str, list[str]]:
    found: dict[str, list[str]] = defaultdict(list)
    scan_roots = [ROOT / "SKILL.md", ROOT / "references"]
    paths: list[Path] = []
    if scan_roots[0].is_file():
        paths.append(scan_roots[0])
    if scan_roots[1].is_dir():
        paths.extend(sorted(scan_roots[1].glob("*.md")))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        for source_id in MARKER_RE.findall(text):
            if rel not in found[source_id]:
                found[source_id].append(rel)
    return dict(found)


def validate_ledger() -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        ledger = load_ledger()
        schema = load_json(SCHEMA_PATH)
    except Exception as exc:
        return [str(exc)], warnings, {"source_count": 0}

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for issue in sorted(validator.iter_errors(ledger), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(x) for x in issue.absolute_path) or "<root>"
        errors.append(f"schema {loc}: {issue.message}")

    rows = ledger.get("sources", []) if isinstance(ledger.get("sources"), list) else []
    ids: set[str] = set()
    dois: dict[str, str] = {}
    arxivs: dict[str, str] = {}
    canon_ids: dict[str, str] = {}
    by_status: dict[str, int] = defaultdict(int)

    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("id", ""))
        if not source_id:
            continue
        if source_id in ids:
            errors.append(f"duplicate source id: {source_id}")
        ids.add(source_id)
        by_status[str(row.get("publication_status"))] += 1

        for field, table in (("doi", dois), ("arxiv", arxivs), ("canonical_identifier", canon_ids)):
            value = row.get(field)
            if value in (None, ""):
                continue
            key = str(value).strip().lower()
            prior = table.get(key)
            if prior and prior != source_id:
                errors.append(f"duplicate {field} {value!r}: {prior}, {source_id}")
            table[key] = source_id

        superseded = row.get("superseded_by")
        if superseded == source_id:
            errors.append(f"{source_id}: superseded_by cannot self-reference")

        try:
            checked = datetime.strptime(str(row.get("verification_date")), "%Y-%m-%d").date()
            if checked > date.today():
                warnings.append(f"{source_id}: verification_date is in the future")
        except Exception:
            pass

        for rel in row.get("used_by", []) if isinstance(row.get("used_by"), list) else []:
            path = ROOT / str(rel)
            if not path.is_file():
                errors.append(f"{source_id}: used_by path does not exist: {rel}")

    smap = source_map(ledger)
    for source_id, row in smap.items():
        superseded = row.get("superseded_by")
        if superseded is not None and superseded not in smap:
            errors.append(f"{source_id}: superseded_by target does not exist: {superseded}")

    markers = scan_markers()
    for source_id, consumers in sorted(markers.items()):
        if source_id not in smap:
            errors.append(f"unknown research marker {source_id} in {', '.join(consumers)}")
    for source_id, row in sorted(smap.items()):
        declared = sorted(str(x) for x in row.get("used_by", []) if isinstance(x, str))
        observed = sorted(markers.get(source_id, []))
        missing_markers = sorted(set(declared) - set(observed))
        undeclared = sorted(set(observed) - set(declared))
        for rel in missing_markers:
            errors.append(f"{source_id}: used_by declares {rel} but the file has no [research:{source_id}] marker")
        for rel in undeclared:
            errors.append(f"{source_id}: marker appears in {rel} but used_by does not declare it")
        if not observed:
            warnings.append(f"{source_id}: no live [research:{source_id}] consumer")

    if CNE_VIEW_PATH.is_file():
        try:
            view = load_json(CNE_VIEW_PATH)
            if view.get("canonical_ledger") != "assets/external-research-ledger.json":
                errors.append("Chinese narrative research view points to the wrong canonical ledger")
            ids_view = view.get("source_ids")
            if not isinstance(ids_view, list) or not ids_view:
                errors.append("Chinese narrative research view has no source_ids")
            else:
                if len(ids_view) != len(set(ids_view)):
                    errors.append("Chinese narrative research view contains duplicate source_ids")
                for source_id in ids_view:
                    if source_id not in smap:
                        errors.append(f"Chinese narrative research view references unknown source: {source_id}")
        except Exception as exc:
            errors.append(f"invalid Chinese narrative research view: {exc}")
    else:
        errors.append("missing Chinese narrative research view")

    summary = {
        "source_count": len(smap),
        "marker_count": sum(len(v) for v in markers.values()),
        "publication_status": dict(sorted(by_status.items())),
        "errors": len(errors),
        "warnings": len(warnings),
    }
    return errors, warnings, summary


def cmd_validate(as_json: bool) -> int:
    errors, warnings, summary = validate_ledger()
    payload = {"passed": not errors, "summary": summary, "errors": errors, "warnings": warnings}
    if as_json:
        emit(payload, True)
    else:
        print(f"external research ledger: {'PASS' if not errors else 'FAIL'}")
        print(f"sources={summary['source_count']} markers={summary['marker_count']} errors={len(errors)} warnings={len(warnings)}")
        for item in errors:
            print(f"ERROR: {item}")
        for item in warnings:
            print(f"WARN: {item}")
    return 0 if not errors else 1


def cmd_coverage(as_json: bool) -> int:
    errors, warnings, summary = validate_ledger()
    ledger = load_ledger()
    smap = source_map(ledger)
    markers = scan_markers()
    rows = []
    for source_id in sorted(smap):
        row = smap[source_id]
        rows.append({
            "id": source_id,
            "publication_status": row.get("publication_status"),
            "used_by": sorted(row.get("used_by", [])),
            "observed_in": sorted(markers.get(source_id, [])),
            "verification_date": row.get("verification_date"),
        })
    payload = {"passed": not errors, "summary": summary, "sources": rows, "errors": errors, "warnings": warnings}
    if as_json:
        emit(payload, True)
    else:
        print(f"research coverage: {'PASS' if not errors else 'FAIL'}")
        for row in rows:
            print(f"{row['id']}: {len(row['observed_in'])} consumer(s), {row['publication_status']}, verified {row['verification_date']}")
        for item in errors:
            print(f"ERROR: {item}")
        for item in warnings:
            print(f"WARN: {item}")
    return 0 if not errors else 1


def cmd_list(status: str | None, as_json: bool) -> int:
    ledger = load_ledger()
    rows = []
    for row in ledger.get("sources", []):
        if not isinstance(row, dict):
            continue
        if status and row.get("publication_status") != status:
            continue
        rows.append({
            "id": row.get("id"),
            "year": row.get("year"),
            "publication_status": row.get("publication_status"),
            "venue": row.get("venue"),
            "title": row.get("title"),
        })
    rows.sort(key=lambda x: (-int(x.get("year") or 0), str(x.get("id"))))
    if as_json:
        emit(rows, True)
    else:
        for row in rows:
            print(f"{row['id']}  [{row['publication_status']}]  {row['year']}  {row['title']}")
    return 0


def cmd_show(source_id: str, as_json: bool) -> int:
    row = source_map(load_ledger()).get(source_id)
    if row is None:
        print(f"research-ledger: unknown source id: {source_id}", file=sys.stderr)
        return 2
    emit(row, as_json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate/query the Skill-wide external research ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate-project", help="read-only temporal applicability check of project research dependencies; not the Skill bibliography")
    p.add_argument("state", type=Path)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("validate")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("coverage")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("list")
    p.add_argument("--status", choices=["peer-reviewed", "preprint", "other"])
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("show")
    p.add_argument("source_id")
    p.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate-project":
        from research_freshness import validate_research_records, temporal_applicability
        state = load_json(args.state)
        if not isinstance(state, dict):
            parser_error = {"passed": False, "errors": ["project state must be an object"]}
            emit(parser_error, args.json)
            return 1
        issues = validate_research_records(state)
        errors = [x for x in issues if x["severity"] == "error"]
        records = state.get("research_dependencies", [])
        emit({"passed": not errors, "issues": issues,
              "applicability": [{"id": r.get("fact_id", r.get("id")), **temporal_applicability(r, state.get("story_window"))}
                                for r in records if isinstance(r, dict)] if isinstance(records, list) else []}, args.json)
        return 1 if errors else 0
    if args.command == "validate":
        return cmd_validate(args.json)
    if args.command == "coverage":
        return cmd_coverage(args.json)
    if args.command == "list":
        return cmd_list(args.status, args.json)
    if args.command == "show":
        return cmd_show(args.source_id, args.json)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
