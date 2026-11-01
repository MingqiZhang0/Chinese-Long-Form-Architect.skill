#!/usr/bin/env python3
"""Shared orchestration role/clearance contract.

Keep role visibility policy in one machine-readable asset so bundle creation,
validation, and maintenance checks cannot drift independently.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ROLE_CLEARANCE_PATH = ROOT / "assets" / "orchestration" / "role-clearance.json"
ROLE_CARDS_DIR = ROOT / "assets" / "orchestration" / "role-cards"


def load_role_clearance(path: Path = ROLE_CLEARANCE_PATH) -> dict[str, int]:
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("role-clearance registry must be a JSON object")
    table = raw.get("clearance")
    if not isinstance(table, dict) or not table:
        raise ValueError("role-clearance registry must contain a non-empty clearance object")
    out: dict[str, int] = {}
    for role, level in table.items():
        if not isinstance(role, str) or not role.strip():
            raise ValueError("role-clearance keys must be non-empty strings")
        if not isinstance(level, int) or not 0 <= level <= 3:
            raise ValueError(f"invalid clearance for {role!r}: {level!r}")
        out[role] = level
    return out


def validate_role_cards(table: dict[str, int] | None = None) -> list[str]:
    table = table or load_role_clearance()
    errors: list[str] = []
    card_roles = {p.stem for p in ROLE_CARDS_DIR.glob("*.md") if p.is_file()}
    declared = set(table)
    for role in sorted(declared - card_roles):
        errors.append(f"missing role card for declared role: {role}")
    for role in sorted(card_roles - declared):
        errors.append(f"role card has no clearance declaration: {role}")
    return errors


ROLE_CLEARANCE = load_role_clearance()
ROLE_NAMES = frozenset(ROLE_CLEARANCE)
EXECUTION_PROFILES = frozenset({"native-multi-agent", "clean-room-serial", "soft-serial", "minimal-local"})

POETICS_AUTHORITY_ROLES = frozenset({"director", "planner"})
POETICS_CONSUMER_ROLES = frozenset(ROLE_NAMES - POETICS_AUTHORITY_ROLES)

def poetics_role_mode(role: str) -> str:
    """Return whether a role may author planning-level poetics or only consume scoped derivatives."""
    if role not in ROLE_NAMES:
        raise ValueError(f"unknown orchestration role: {role}")
    return "author-or-approve" if role in POETICS_AUTHORITY_ROLES else "consume-scoped-derivative"
