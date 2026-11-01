#!/usr/bin/env python3
"""Shared freshness logic for structured research dependencies.

This module is intentionally read-only. It centralizes the definition of when a
research dependency is due for review so CLI queries and observability reports
cannot drift into different interpretations of the same project state.
"""

from __future__ import annotations

import math
import calendar
import re
from datetime import date
from typing import Any


def finite_number(value: Any) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(float(value)) else None



def temporal_bounds(value: Any) -> tuple[str, float, float] | None:
    """Conservative closed bounds; never compare a calendar date to a numeric axis.

    ISO years/months are uncertainty intervals, not invented first-day timestamps.
    Relative labels and unrecognized calendars deliberately remain incomparable.
    """
    number = finite_number(value)
    if number is not None:
        return ("numeric", float(number), float(number))
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}(?:-[0-9]{2}(?:-[0-9]{2})?)?", value):
        return None
    try:
        bits = [int(x) for x in value.split("-")]
        year = bits[0]
        if len(bits) == 1:
            lo, hi = date(year, 1, 1), date(year, 12, 31)
        elif len(bits) == 2:
            month = bits[1]
            lo, hi = date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
        else:
            lo = hi = date(*bits)
        return ("calendar", float(lo.toordinal()), float(hi.toordinal()))
    except (ValueError, OverflowError):
        return None


def temporal_order(before: Any, after: Any) -> bool | None:
    a, b = temporal_bounds(before), temporal_bounds(after)
    if a is None or b is None or a[0] != b[0]:
        return None
    if a[2] <= b[1]:
        return True
    if a[1] > b[2]:
        return False
    return None


def window_bounds(value: Any) -> tuple[str, float, float] | None:
    if not isinstance(value, dict):
        return temporal_bounds(value)
    a = temporal_bounds(value.get("start"))
    b = temporal_bounds(value.get("end", value.get("start")))
    if a is None or b is None or a[0] != b[0] or a[1] > b[2]:
        return None
    return a[0], a[1], b[2]


def temporal_applicability(record: dict[str, Any], story_window: Any = None) -> dict[str, Any]:
    """Truth in reality and applicability are independent; boolean is a claim.

    Full containment is required for a whole story window. Partial overlap is
    UNKNOWN and can be scoped to a narrower scene instead. valid_to is inclusive.
    Missing validity never defaults to applicable, even for a legacy true flag.
    """
    window = story_window if story_window is not None else record.get("story_window")
    w = window_bounds(window)
    start = temporal_bounds(record.get("valid_from"))
    end = temporal_bounds(record.get("valid_to"))
    status = "UNKNOWN"
    if w and (start or end):
        if ((record.get("valid_from") is not None and start is None)
                or (record.get("valid_to") is not None and end is None)
                or any(x[0] != w[0] for x in (start, end) if x)):
            pass
        elif (start and w[2] < start[1]) or (end and w[1] > end[2]):
            status = "INAPPLICABLE"
        elif ((start is None or w[1] >= start[2]) and (end is None or w[2] <= end[1])):
            status = "APPLICABLE"
    claimed = record.get("applies_to_story_window")
    # A stored claim belongs to its recorded window; changing the current window
    # invalidates that binding rather than contradicting the old historical claim.
    same_window = story_window is None or window == record.get("story_window") or "story_window" not in record
    conflict = same_window and isinstance(claimed, bool) and status != "UNKNOWN" and claimed != (status == "APPLICABLE")
    return {"status": status, "conflict": conflict, "story_window_changed": story_window is not None and "story_window" in record and window != record["story_window"]}


def validate_research_records(state: dict[str, Any]) -> list[dict[str, Any]]:
    issues = []
    rows = state.get("research_dependencies", [])
    if not isinstance(rows, list):
        return [{"severity": "error", "code": "research.shape", "message": "research_dependencies must be a list", "scene_ids": []}]
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            issues.append({"severity": "error", "code": "research.shape", "message": "research record must be an object", "scene_ids": []})
            continue
        rid = row.get("fact_id", row.get("id"))
        result = temporal_applicability(row, state.get("story_window"))
        errors = []
        if rid in seen and rid is not None:
            errors.append("duplicate research identity")
        seen.add(rid)
        if result["conflict"]:
            errors.append("manual applicability conflicts with validity/story window")
        a, b = temporal_bounds(row.get("valid_from")), temporal_bounds(row.get("valid_to"))
        if a and b and (a[0] != b[0] or a[1] > b[2]):
            errors.append("invalid validity window")
        for key in ("valid_from", "valid_to"):
            if row.get(key) is not None and temporal_bounds(row[key]) is None:
                errors.append("uncomparable " + key)
        if row.get("temporal_epistemic_version") == "1.0.0" and row.get("consequential"):
            if not rid or not row.get("provenance") or not row.get("precision") or row.get("source_scope") != "REAL_WORLD":
                errors.append("new consequential research requires identity, provenance, precision and REAL_WORLD scope")
            if result["status"] == "UNKNOWN":
                errors.append("new consequential research applicability needs review")
        for msg in errors:
            issues.append({"severity": "error", "code": "research.applicability", "message": f"{rid}: {msg}", "scene_ids": []})
        if result["status"] == "UNKNOWN" and not errors:
            issues.append({"severity": "warning", "code": "research.legacy_unknown_applicability", "message": f"{rid}: UNKNOWN applicability; not permission for consequential use", "scene_ids": []})
    return issues


def research_staleness_reasons(
    record: dict[str, Any],
    *,
    chapter: int | float | None = None,
    day: int | float | None = None,
    story_window: Any = None,
) -> list[str]:
    """Return deterministic reasons why one research dependency is stale."""
    reasons: list[str] = []
    status = str(record.get("status", "active")).lower()
    if status == "stale" or record.get("recheck_due") is True:
        reasons.append("explicit-stale")

    now_chapter = finite_number(chapter)
    last_chapter = finite_number(record.get("last_checked_chapter"))
    max_chapters = finite_number(record.get("max_staleness_chapters"))
    if now_chapter is not None and last_chapter is not None and max_chapters is not None:
        age = now_chapter - last_chapter
        if age > max_chapters:
            reasons.append(f"chapter-age={age:g}")

    now_day = finite_number(day)
    last_day = finite_number(record.get("last_checked_day"))
    max_days = finite_number(record.get("max_staleness_days"))
    if now_day is not None and last_day is not None and max_days is not None:
        age = now_day - last_day
        if age > max_days:
            reasons.append(f"day-age={age:g}")

    applicability = temporal_applicability(record, story_window)
    if applicability["story_window_changed"]:
        reasons.append("story-window-changed")
    if applicability["status"] == "INAPPLICABLE":
        reasons.append("story-window-inapplicable")
    elif applicability["status"] == "UNKNOWN" and (story_window is not None or record.get("story_window") is not None or record.get("temporal_risk") is True):
        reasons.append("unknown-applicability")
    if applicability["conflict"]:
        reasons.append("applicability-conflict")
    return reasons


def stale_research_dependencies(
    state: dict[str, Any],
    *,
    chapter: int | float | None = None,
    day: int | float | None = None,
) -> list[dict[str, Any]]:
    """Return research rows due for review under the shared freshness contract."""
    if chapter is None:
        chapter = state.get("current_chapter")
    if day is None:
        day = state.get("current_day")

    rows: list[dict[str, Any]] = []
    for record in state.get("research_dependencies", []) or []:
        if not isinstance(record, dict):
            continue
        reasons = research_staleness_reasons(record, chapter=chapter, day=day, story_window=state.get("story_window"))
        if not reasons:
            continue
        rows.append(
            {
                "id": record.get("id"),
                "status": record.get("status"),
                "scope": record.get("scope"),
                "reasons": reasons,
                "recheck_trigger": record.get("recheck_trigger"),
            }
        )
    return rows
