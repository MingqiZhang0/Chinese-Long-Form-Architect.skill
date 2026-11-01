#!/usr/bin/env python3
"""Shared helpers for canonical Reader Model state shapes."""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass
import math
import json


@dataclass(frozen=True)
class NarrativePosition:
    axis: str
    value: float
    domain: str = "chapter"


def chapter_position(chapter: int) -> NarrativePosition:
    """Legacy chapter adapter: chapters are presentation order, never story time."""
    return NarrativePosition("presentation", chapter)


def query_reader_state(state: dict[str, Any], position: NarrativePosition) -> dict[str, Any]:
    """Chapter presentation adapter. Unknown chronology fails closed."""
    gaps: set[str] = set()
    if position.axis != "presentation" or position.domain != "chapter" or not isinstance(position.value, (int, float)) or not math.isfinite(position.value):
        return {"state": {}, "completeness": "PARTIAL", "gap_reasons": ["UNSUPPORTED_READER_AXIS"], "provenance_status": "UNRESOLVED"}

    def filter_value(value: Any, inherited: bool = False) -> Any:
        if isinstance(value, list):
            selected = [filtered for item in value if (filtered := filter_value(item, inherited)) is not None]
            # Event/list histories may repeat the same fact. Latest exposure wins,
            # while anonymous snapshots retain their independent contents.
            latest: dict[str, dict[str, Any]] = {}
            anonymous = []
            for item in selected:
                key = item.get("fact", item.get("id")) if isinstance(item, dict) else None
                if key is None:
                    anonymous.append(item)
                elif str(key) not in latest or float(item.get("from_chapter", 0)) > float(latest[str(key)].get("from_chapter", 0)):
                    latest[str(key)] = item
                elif item.get("from_chapter") == latest[str(key)].get("from_chapter") and item != latest[str(key)]:
                    gaps.add("AMBIGUOUS_READER_HISTORY")
                    latest[str(key)] = min(item, latest[str(key)], key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
            return anonymous + [latest[k] for k in sorted(latest)]
        if not isinstance(value, dict):
            if inherited:
                return value
            gaps.add("MISSING_READER_TIME")
            return None
        start = value.get("from_chapter")
        end = value.get("to_chapter")
        timed = start is not None
        if timed:
            try:
                if not math.isfinite(float(start)) or (end is not None and not math.isfinite(float(end))):
                    raise ValueError("nonfinite chronology")
                # Existing chapter snapshots use inclusive to_chapter boundaries.
                if float(start) > position.value or (end is not None and position.value > float(end)):
                    return None
            except (ValueError, TypeError):
                gaps.add("INVALID_READER_TIME")
                return None
        elif not inherited and not any(isinstance(v, (list, dict)) for v in value.values()):
            gaps.add("MISSING_READER_TIME")
            return None
        out = {}
        for key, item in value.items():
            if timed and key in {"from_chapter", "to_chapter", "id", "fact", "status", "story_time"}:
                out[key] = item
                continue
            filtered = filter_value(item, inherited or timed)
            if filtered is not None:
                out[key] = filtered
        return out

    data = state.get("reader_state")
    # Runtime import/reconstruction: presentation chapter is the event adapter.
    # Only reader effects participate; story time never orders exposures.
    reader_events = [e for e in state.get("events", []) if isinstance(e, dict) and
                     any(isinstance(f, dict) and (f.get("path") == "reader_state" or str(f.get("path", "")).startswith("reader_state.")) for f in (e.get("effects") or []))]
    reconstructed = False
    if reader_events:
        from narrative_runtime import apply_effect
        eligible = []
        for event in reader_events:
            if event.get("status", "committed") != "committed":
                gaps.add("UNCOMMITTED_READER_EVENT")
                continue
            if str(event.get("branch", "main")) != str(state.get("branch", "main")):
                gaps.add("UNSUPPORTED_READER_BRANCH_HISTORY")
                continue
            try:
                chapter = float(event.get("chapter"))
                if not math.isfinite(chapter):
                    raise ValueError("nonfinite chapter")
            except (TypeError, ValueError):
                gaps.add("MISSING_READER_EVENT_TIME")
                continue
            if chapter <= position.value:
                eligible.append((chapter, event))
                if not isinstance(event.get("seq"), int):
                    gaps.add("MISSING_READER_EVENT_SEQUENCE")
        projection: dict[str, Any] = {}
        for _, event in sorted(eligible, key=lambda pair: (pair[0], pair[1].get("seq") if isinstance(pair[1].get("seq"), int) else 0, str(pair[1].get("event_id", "")))):
            for effect in event.get("effects", []):
                if not isinstance(effect, dict):
                    gaps.add("INVALID_READER_EVENT_EFFECT")
                    continue
                if effect.get("path") == "reader_state" or str(effect.get("path", "")).startswith("reader_state."):
                    try:
                        apply_effect(projection, effect)
                    except ValueError:
                        gaps.add("INVALID_READER_EVENT_EFFECT")
        data = projection.get("reader_state", {})
        reconstructed = True
    if not data:
        gaps.add("MISSING_READER_HISTORY")
    result = filter_value(data or {}, reconstructed) or ([] if isinstance(data, list) else {})
    if not result or (isinstance(result, dict) and not any(v for k, v in result.items() if k not in {"from_chapter", "to_chapter"})):
        gaps.add("NO_READER_STATE_AT_POSITION")
    return {"state": result, "completeness": "PARTIAL" if gaps else "FULL", "gap_reasons": sorted(gaps), "provenance_status": "UNRESOLVED"}


def reader_state_at(state: dict[str, Any], chapter: int | NarrativePosition | None = None) -> Any:
    data = state.get("reader_state", {}) or {}
    if chapter is not None:
        position = chapter if isinstance(chapter, NarrativePosition) else chapter_position(chapter)
        return query_reader_state(state, position)["state"]
    return data


def foreground_questions(reader_state: Any) -> list[Any]:
    if isinstance(reader_state, dict):
        for key in ("foreground_questions", "foreground", "questions"):
            value = reader_state.get(key)
            if isinstance(value, list):
                return value
        return []
    if isinstance(reader_state, list):
        if all(not isinstance(x, dict) for x in reader_state):
            return list(reader_state)
        out: list[Any] = []
        for rec in reader_state:
            if isinstance(rec, dict):
                out.extend(foreground_questions(rec))
        return out
    return []


def _collect_list(reader_state: Any, keys: tuple[str, ...]) -> list[Any]:
    if isinstance(reader_state, dict):
        for key in keys:
            value = reader_state.get(key)
            if isinstance(value, list):
                return list(value)
        return []
    if isinstance(reader_state, list):
        out: list[Any] = []
        for rec in reader_state:
            if isinstance(rec, dict):
                out.extend(_collect_list(rec, keys))
        return out
    return []


def gist_items(reader_state: Any) -> list[Any]:
    """Return durable gist/summary representations if the project records them."""
    return _collect_list(reader_state, ("gist", "gist_items", "durable_gist"))


def familiarity_items(reader_state: Any) -> list[Any]:
    """Return accumulated familiarity/acquaintance records when present."""
    return _collect_list(reader_state, ("familiarity", "familiarity_items", "acquaintance"))


def active_reading_modes(reader_state: Any) -> list[Any]:
    """Return project-declared reader activities/modes, not inferred universal preferences."""
    return _collect_list(reader_state, ("reader_activities", "active_reading_modes", "reading_modes"))


def likely_misreadings(reader_state: Any) -> list[Any]:
    """Return tracked reader misattributions/hypotheses that may be intentionally wrong."""
    return _collect_list(reader_state, ("likely_misreadings", "misattributions", "wrong_hypotheses"))


def learned_expectations(reader_state: Any) -> list[Any]:
    """Return expectations the text has taught the reader about form/world/character."""
    return _collect_list(reader_state, ("learned_expectations", "expectation_learning", "form_expectations"))
