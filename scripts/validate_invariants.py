#!/usr/bin/env python3
"""Evaluate the bounded Narrative Invariant DSL against a Runtime event history."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from narrative_runtime import apply_effect, branch_map, effective_events, events_by_branch, load_json, load_jsonl

MISSING = object()


def resolve_values(root: Any, path: str) -> list[Any]:
    parts = [p for p in path.split(".") if p]
    values = [root]
    for part in parts:
        nxt: list[Any] = []
        for value in values:
            if part == "*":
                if isinstance(value, dict):
                    nxt.extend(value.values())
                elif isinstance(value, list):
                    nxt.extend(value)
                continue
            if isinstance(value, dict) and part in value:
                nxt.append(value[part])
            else:
                nxt.append(MISSING)
        values = nxt
    return values


def compare_one(actual: Any, op: str, expected: Any = None) -> bool:
    if op == "exists":
        return actual is not MISSING
    if op == "not_exists":
        return actual is MISSING
    if actual is MISSING:
        return False
    if op == "eq":
        return actual == expected
    if op == "neq":
        return actual != expected
    if op == "in":
        return actual in expected if isinstance(expected, list) else False
    if op == "not_in":
        return actual not in expected if isinstance(expected, list) else False
    if op == "gt":
        return isinstance(actual, (int, float)) and isinstance(expected, (int, float)) and actual > expected
    if op == "gte":
        return isinstance(actual, (int, float)) and isinstance(expected, (int, float)) and actual >= expected
    if op == "lt":
        return isinstance(actual, (int, float)) and isinstance(expected, (int, float)) and actual < expected
    if op == "lte":
        return isinstance(actual, (int, float)) and isinstance(expected, (int, float)) and actual <= expected
    if op == "truthy":
        return bool(actual)
    if op == "falsy":
        return not bool(actual)
    if op == "contains":
        try:
            return expected in actual
        except TypeError:
            return False
    if op == "nonempty":
        try:
            return len(actual) > 0
        except TypeError:
            return bool(actual)
    if op == "empty":
        try:
            return len(actual) == 0
        except TypeError:
            return not bool(actual)
    raise ValueError(f"unsupported condition op {op}")


def condition_holds(condition: dict[str, Any] | None, state: dict[str, Any], entity: str | None = None) -> bool:
    if not condition:
        return True
    if "all" in condition:
        rows = condition.get("all")
        return isinstance(rows, list) and all(condition_holds(x, state, entity) for x in rows if isinstance(x, dict))
    if "any" in condition:
        rows = condition.get("any")
        return isinstance(rows, list) and any(condition_holds(x, state, entity) for x in rows if isinstance(x, dict))
    if "not" in condition:
        row = condition.get("not")
        return isinstance(row, dict) and not condition_holds(row, state, entity)
    path = str(condition.get("path", ""))
    if not path:
        raise ValueError("condition requires path")
    if entity is not None:
        path = path.replace("{entity}", entity)
    elif "{entity}" in path:
        return False
    op = str(condition.get("op", "eq"))
    expected = condition.get("value")
    values = resolve_values(state, path)
    quantifier = str(condition.get("quantifier", "all"))
    checks = [compare_one(v, op, expected) for v in values]
    if quantifier == "any":
        return any(checks)
    return bool(checks) and all(checks)


def severity_bucket(rule: dict[str, Any], text: str, errors: list[str], warnings: list[str], advisories: list[str]) -> None:
    sev = str(rule.get("severity", "error"))
    if sev == "error":
        errors.append(text)
    elif sev == "warning":
        warnings.append(text)
    else:
        advisories.append(text)


def applies_branch(rule: dict[str, Any], branch: str) -> bool:
    branches = rule.get("branches")
    return not isinstance(branches, list) or not branches or branch in {str(x) for x in branches}


def evaluate(events: list[dict[str, Any]], branches: dict[str, dict[str, Any]], branch: str, catalog: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    history = effective_events(branch, branches, events_by_branch(events))
    rules = catalog.get("invariants", [])
    if not isinstance(rules, list):
        raise ValueError("invariants must be a list")
    errors: list[str] = []
    warnings: list[str] = []
    advisories: list[str] = []
    state: dict[str, Any] = {}
    prior: list[dict[str, Any]] = []
    previous_values: dict[str, Any] = {}

    for event in history:
        eid = str(event.get("event_id", "?"))
        etype = str(event.get("event_type", ""))
        entities = [str(x) for x in (event.get("entity_ids") or [])] or [None]
        pre = copy.deepcopy(state)

        for rule in rules:
            if not isinstance(rule, dict) or not applies_branch(rule, branch):
                continue
            rid = str(rule.get("id", "?"))
            kind = str(rule.get("kind", ""))
            event_types = {str(x) for x in (rule.get("event_types") or [])}
            if event_types and etype not in event_types:
                continue
            message = str(rule.get("message") or f"invariant {rid} failed")

            if kind == "forbids_event_when":
                for entity in entities:
                    if condition_holds(rule.get("condition"), pre, entity):
                        severity_bucket(rule, f"{rid} at {eid}: {message}", errors, warnings, advisories)
                        break
            elif kind == "requires_prior_event":
                required = str(rule.get("required_event_type", ""))
                share = bool(rule.get("share_entity", False))
                ok = False
                current_entities = set(str(x) for x in (event.get("entity_ids") or []))
                for old in prior:
                    if str(old.get("event_type")) != required:
                        continue
                    if not share or current_entities & set(str(x) for x in (old.get("entity_ids") or [])):
                        ok = True
                        break
                if not ok:
                    severity_bucket(rule, f"{rid} at {eid}: {message}", errors, warnings, advisories)
            elif kind == "temporal_order":
                required = str(rule.get("before_event_type", rule.get("required_event_type", "")))
                if not any(str(x.get("event_type")) == required for x in prior):
                    severity_bucket(rule, f"{rid} at {eid}: {message}", errors, warnings, advisories)
            elif kind == "event_guard":
                for entity in entities:
                    if not condition_holds(rule.get("precondition"), pre, entity):
                        severity_bucket(rule, f"{rid} precondition at {eid}: {message}", errors, warnings, advisories)
                        break

        for effect in event.get("effects", []) or []:
            if isinstance(effect, dict):
                apply_effect(state, effect)

        for rule in rules:
            if not isinstance(rule, dict) or not applies_branch(rule, branch):
                continue
            rid = str(rule.get("id", "?"))
            kind = str(rule.get("kind", ""))
            event_types = {str(x) for x in (rule.get("event_types") or [])}
            if event_types and etype not in event_types and kind not in {"always", "monotonic", "conservation"}:
                continue
            message = str(rule.get("message") or f"invariant {rid} failed")

            if kind == "always":
                if not condition_holds(rule.get("condition"), state):
                    severity_bucket(rule, f"{rid} after {eid}: {message}", errors, warnings, advisories)
            elif kind == "event_guard" and (not event_types or etype in event_types):
                for entity in entities:
                    if not condition_holds(rule.get("postcondition"), state, entity):
                        severity_bucket(rule, f"{rid} postcondition at {eid}: {message}", errors, warnings, advisories)
                        break
            elif kind == "monotonic":
                path = str(rule.get("path", ""))
                values = resolve_values(state, path)
                if len(values) != 1 or values[0] is MISSING or not isinstance(values[0], (int, float)):
                    continue
                cur = values[0]
                prev = previous_values.get(rid, cur)
                reset_types = {str(x) for x in (rule.get("allow_reset_event_types") or [])}
                if etype not in reset_types:
                    direction = str(rule.get("direction", "nondecreasing"))
                    bad = (direction == "nondecreasing" and cur < prev) or (direction == "nonincreasing" and cur > prev)
                    if bad:
                        severity_bucket(rule, f"{rid} after {eid}: {message} ({prev} -> {cur})", errors, warnings, advisories)
                previous_values[rid] = cur
            elif kind == "conservation":
                paths = [str(x) for x in (rule.get("paths") or [])]
                if not paths:
                    continue
                def total(s: dict[str, Any]) -> float | None:
                    vals: list[Any] = []
                    for p in paths:
                        vals.extend(resolve_values(s, p))
                    nums = [x for x in vals if isinstance(x, (int, float))]
                    return float(sum(nums)) if len(nums) == len([x for x in vals if x is not MISSING]) else None
                before_total = total(pre)
                after_total = total(state)
                allow = {str(x) for x in (rule.get("allow_event_types") or [])}
                tolerance = float(rule.get("tolerance", 0) or 0)
                if before_total is not None and after_total is not None and etype not in allow and abs(after_total - before_total) > tolerance:
                    severity_bucket(rule, f"{rid} after {eid}: {message} ({before_total} -> {after_total})", errors, warnings, advisories)
        prior.append(event)
    return errors, warnings, advisories


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--events", required=True, type=Path)
    p.add_argument("--branches", required=True, type=Path)
    p.add_argument("--invariants", required=True, type=Path)
    p.add_argument("--branch", default="main")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    try:
        events = load_jsonl(args.events)
        branches = branch_map(load_json(args.branches))
        catalog = load_json(args.invariants)
        errors, warnings, advisories = evaluate(events, branches, args.branch, catalog)
    except Exception as exc:
        print(f"ERROR: invariant evaluation failed: {exc}", file=sys.stderr)
        return 2
    result = {"errors": errors, "warnings": warnings, "advisories": advisories}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for x in advisories:
            print(f"ADVISORY: {x}")
        for x in warnings:
            print(f"WARNING: {x}")
        for x in errors:
            print(f"ERROR: {x}")
        print(f"summary: {len(errors)} error(s), {len(warnings)} warning(s), {len(advisories)} advisory")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
