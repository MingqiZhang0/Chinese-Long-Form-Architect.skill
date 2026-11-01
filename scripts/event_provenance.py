"""Versioned event closure checks against a caller-supplied provenance catalog.

Rows are references, never substitutes for registered source/confirmation records.
Legacy events remain readable but do not acquire authority from their JSON existence.
"""
import math
import re
from typing import Any


def canonical_event(event: dict[str, Any]) -> bool:
    return event.get("authority") == "canonical" or event.get("audit_closed") is True


def event_closure(event: dict[str, Any], events: dict[str, dict[str, Any]] | None = None,
                  catalog: dict[str, Any] | None = None, seen: frozenset[str] = frozenset()) -> dict[str, Any]:
    events, catalog = events or {}, catalog or {}
    p = event.get("provenance")
    gaps: list[str] = []
    broken = False
    if not isinstance(p, dict):
        return {"provenance_status": "UNRESOLVED", "gap_reasons": ["LEGACY_UNCLOSED"]}
    eid = str(event.get("event_id", ""))
    if eid in seen:
        return {"provenance_status": "BROKEN", "gap_reasons": ["PROVENANCE_CYCLE"]}
    seen = seen | {eid}
    if p.get("version") != "1.0.0":
        gaps.append("UNSUPPORTED_PROVENANCE_VERSION")
    if p.get("authority") not in {"canonical", "explicit_planning", "user_confirmed", "imported", "deterministic", "migration"}:
        gaps.append("MISSING_AUTHORITY")
    scope = p.get("temporal_scope")
    if not isinstance(scope, dict) or scope.get("axis") not in {"story_valid", "presentation", "revision"} or not scope.get("domain"):
        gaps.append("MISSING_TEMPORAL_SCOPE")
    else:
        start, end = scope.get("from"), scope.get("until")
        if not isinstance(start, (int, float)) or isinstance(start, bool) or not math.isfinite(start) or (end is not None and (not isinstance(end, (int, float)) or isinstance(end, bool) or not math.isfinite(end) or end <= start)):
            gaps.append("INVALID_TEMPORAL_SCOPE")

    def record(group: str, ref: Any) -> dict[str, Any] | None:
        nonlocal broken
        if not isinstance(ref, str) or not ref:
            gaps.append("MISSING_" + group.upper() + "_REF")
            return None
        table = catalog.get(group, {})
        value = table.get(ref) if isinstance(table, dict) else None
        if not isinstance(value, dict):
            gaps.append("DANGLING_" + group.upper() + "_REF")
            broken = True
            return None
        if value.get("status", "valid") not in {"valid", "active", "confirmed"}:
            gaps.append("INVALID_" + group.upper())
            broken = True
        return value

    def source(group: str, ref: Any, kind: str) -> dict[str, Any] | None:
        value = record(group, ref)
        if value is not None and (value.get("kind") != kind or not isinstance(value.get("revision"), str) or not value.get("revision") or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("content_sha256", "")))):
            gaps.append("INVALID_SOURCE_IDENTITY")
        return value

    kind = p.get("class")
    if kind == "manuscript":
        evidence = record("evidence", p.get("origin_ref"))
        anchor = record("anchors", evidence.get("anchor_ref")) if evidence else None
        revision = source("source_revisions", anchor.get("source_revision_ref"), "manuscript") if anchor else None
        if anchor and (not isinstance(anchor.get("span"), list) or len(anchor["span"]) != 2 or
                       not all(isinstance(x, int) and not isinstance(x, bool) for x in anchor["span"]) or
                       anchor["span"][0] < 0 or anchor["span"][1] <= anchor["span"][0] or not re.fullmatch(r"[0-9a-f]{64}", str(anchor.get("content_sha256", "")))):
            gaps.append("INVALID_ANCHOR")
        if revision is None:
            gaps.append("MISSING_SOURCE_REVISION")
    elif kind in {"planning", "imported", "migration"}:
        source("sources", p.get("origin_ref"), kind)
    elif kind == "user_confirmed":
        confirmation = record("confirmations", p.get("origin_ref"))
        if confirmation and (confirmation.get("confirmed") is not True or
                             not all(isinstance(confirmation.get(k), str) and confirmation.get(k) for k in ("canon_ref", "confirmed_by"))):
            gaps.append("MISSING_EXPLICIT_CONFIRMATION")
    elif kind == "derived":
        parents = p.get("derived_from")
        rule = record("rules", p.get("origin_ref"))
        if rule and (not isinstance(rule.get("version"), str) or not rule.get("version") or rule.get("version") != p.get("rule_version") or rule.get("deterministic") is not True):
            gaps.append("INVALID_DERIVATION_RULE")
        if not isinstance(parents, list) or not parents:
            gaps.append("MISSING_DERIVATION_PARENTS")
        else:
            for ref in parents:
                parent = events.get(str(ref))
                if parent is None:
                    gaps.append("DANGLING_DERIVATION_PARENT")
                    broken = True
                else:
                    closure = event_closure(parent, events, catalog, seen)
                    if closure["provenance_status"] != "CLOSED":
                        gaps.extend(closure["gap_reasons"])
                        broken |= closure["provenance_status"] == "BROKEN"
    else:
        gaps.append("MISSING_PROVENANCE_CLASS")
    return {"provenance_status": "BROKEN" if broken else "PARTIAL" if gaps else "CLOSED", "gap_reasons": sorted(set(gaps))}


def promotion_errors(event: dict[str, Any], events: dict[str, dict[str, Any]], catalog: dict[str, Any] | None = None) -> list[str]:
    result = event_closure(event, events, catalog)
    if result['provenance_status'] == 'CLOSED':
        return []
    return [f"UNRESOLVED_PROVENANCE: event {event.get('event_id')} {result['provenance_status']}: {','.join(result['gap_reasons'])}"]
