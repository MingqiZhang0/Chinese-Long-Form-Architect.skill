#!/usr/bin/env python3
"""Advisory surface audit for recurrent Chinese prose patterns.

This tool never rewrites prose and never decides literary quality. It highlights
surface constructions that deserve human/Writer review when they recur or when
bounded event negation may have been compressed into an ambiguous ``不 + verb``
tail clause. Findings are subordinate to the active scoped Project Poetics: a
licensed repetition, syntactic pattern, or formal variation is not a defect merely
because it is statistically salient.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

# Conservative candidate: a short clause begins immediately after a comma or
# semicolon with 不 and ends at the next strong punctuation mark. This catches
# forms such as “他看着她，不解释。” without pretending to parse Chinese.
CLIPPED_BU_TAIL = re.compile(r"(?P<full>[，；]\s*不(?P<body>[\u4e00-\u9fff]{1,5})[。！？；])")

# Lexical/discourse forms that frequently begin with 不 but are not the target
# construction. The detector remains advisory even after these exclusions.
CLIPPED_EXCLUSIONS = (
    "不过",
    "不久",
    "不料",
    "不然",
    "不仅",
    "不只",
    "不妨",
    "不得",
    "不禁",
    "不由",
    "不如",
    "不免",
    "不曾",
    "不再",
    "不必",
    "不用",
    "不能",
    "不会",
    "不该",
    "不应",
    "不想",
    "不愿",
    "不肯",
    "不是",
)


CONNECTIVES = (
    "因此", "所以", "但是", "然而", "于是", "然后", "不过", "可是", "因而", "此外", "同时", "总之",
)

CLAUSE_INITIAL_PRONOUN = re.compile(r"(?:^|[。！？；\n])\s*(?:(?:因此|所以|但是|然而|于是|然后|不过|可是|因而|此外|同时|总之)[，,]?)?\s*(他|她|它)(?=[\u4e00-\u9fff])", re.MULTILINE)

CONTRAST_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("not_x_but_y", re.compile(r"不是[^。！？\n]{0,28}而是")),
    ("not_really_x_but_y", re.compile(r"并非[^。！？\n]{0,28}而是")),
    ("not_x_only_y", re.compile(r"不是[^。！？\n]{0,28}只是")),
    ("did_not_x_only_y", re.compile(r"没有[^。！？\n]{0,28}只是")),
)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def clipped_bu_candidates(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for match in CLIPPED_BU_TAIL.finditer(text):
        full = match.group("full")
        clause = full.lstrip("，；").strip()
        if clause.startswith(CLIPPED_EXCLUSIONS):
            continue
        rows.append(
            {
                "line": line_number(text, match.start()),
                "text": full,
                "review": (
                    "If this means a bounded scene action did not occur, prefer 没有/没 + verb "
                    "with the carried subject made clear. Keep 不 only when it genuinely expresses "
                    "habit, refusal/volition, future/generic negation, or another explicit construction."
                ),
            }
        )
    return rows


def contrastive_negation(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, pattern in CONTRAST_PATTERNS:
        for match in pattern.finditer(text):
            start = max(0, text.rfind("\n", 0, match.start()) + 1)
            end = text.find("\n", match.end())
            if end < 0:
                end = len(text)
            excerpt = text[start:end].strip()
            rows.append({"pattern": name, "line": line_number(text, match.start()), "text": excerpt})
    rows.sort(key=lambda row: (row["line"], row["pattern"]))
    return rows


def discourse_surface_metrics(text: str) -> dict[str, Any]:
    connective_counts = {word: text.count(word) for word in CONNECTIVES}
    connective_counts = {k: v for k, v in connective_counts.items() if v}
    total_connectives = sum(connective_counts.values())
    pronoun_starts = [m.group(1) for m in CLAUSE_INITIAL_PRONOUN.finditer(text)]
    chars = len(re.sub(r"\s+", "", text))
    return {
        "explicit_connective_counts": connective_counts,
        "explicit_connective_count": total_connectives,
        "explicit_connective_per_1000_chars": round(total_connectives * 1000 / chars, 3) if chars else 0.0,
        "clause_initial_third_person_pronoun_count": len(pronoun_starts),
        "clause_initial_third_person_pronoun_per_1000_chars": round(len(pronoun_starts) * 1000 / chars, 3) if chars else 0.0,
        "surface_metrics_note": (
            "Counts are diagnostic only. High connective or explicit-pronoun density is not an error by itself; "
            "review local scope, topic competition, register, and reference accessibility before changing prose."
        ),
    }


def build_report(text: str) -> dict[str, Any]:
    clipped = clipped_bu_candidates(text)
    contrasts = contrastive_negation(text)
    chars = len(re.sub(r"\s+", "", text))
    report = {
        "note": (
            "Advisory only. Natural 没有/没 negation is not a defect. Do not mechanically replace every 不. "
            "Review clipped 不-tail clauses for eventive-negation ambiguity, and review repeated corrective "
            "contrast patterns for template-like emphasis."
        ),
        "characters": chars,
        "clipped_bu_tail_candidates": clipped,
        "clipped_bu_tail_count": len(clipped),
        "corrective_contrast_instances": contrasts,
        "corrective_contrast_count": len(contrasts),
        "corrective_contrast_per_1000_chars": round(len(contrasts) * 1000 / chars, 3) if chars else 0.0,
    }
    report.update(discourse_surface_metrics(text))
    return report


def print_text(report: dict[str, Any]) -> None:
    print(report["note"])
    print(f"characters={report['characters']}")
    print(f"clipped_bu_tail_count={report['clipped_bu_tail_count']}")
    for row in report["clipped_bu_tail_candidates"]:
        print(f"review_clipped_bu_tail=line:{row['line']} text:{row['text']}")
    print(f"corrective_contrast_count={report['corrective_contrast_count']}")
    print(f"corrective_contrast_per_1000_chars={report['corrective_contrast_per_1000_chars']}")
    for row in report["corrective_contrast_instances"]:
        print(f"review_corrective_contrast=line:{row['line']} pattern:{row['pattern']} text:{row['text']}")
    print(f"explicit_connective_count={report['explicit_connective_count']}")
    print(f"explicit_connective_per_1000_chars={report['explicit_connective_per_1000_chars']}")
    print(f"clause_initial_third_person_pronoun_count={report['clause_initial_third_person_pronoun_count']}")
    print(f"clause_initial_third_person_pronoun_per_1000_chars={report['clause_initial_third_person_pronoun_per_1000_chars']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 Chinese prose file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding="utf-8")
    report = build_report(text)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
