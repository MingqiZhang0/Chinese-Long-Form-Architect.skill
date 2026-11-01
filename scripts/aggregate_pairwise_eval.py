#!/usr/bin/env python3
"""Aggregate blinded pairwise evaluation results with order-consistency checks.

Input: JSONL rows with fields:
  case_id: string
  left: candidate/version identifier
  right: candidate/version identifier
  winner: "left", "right", or "tie"

For a strong order-control design, each case should normally appear twice with
left/right swapped. A case receives a consistent winner only when both orders
map to the same candidate. Otherwise it is marked uncertain/tie.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def resolved_winner(row: dict) -> str | None:
    winner = row.get("winner")
    if winner == "left":
        return str(row["left"])
    if winner == "right":
        return str(row["right"])
    if winner == "tie":
        return None
    raise ValueError(f"invalid winner {winner!r}; expected left/right/tie")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    args = parser.parse_args()

    rows_by_case: dict[str, list[dict]] = defaultdict(list)
    candidates: set[str] = set()

    with args.jsonl.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            for field in ("case_id", "left", "right", "winner"):
                if field not in row:
                    raise ValueError(f"line {line_no}: missing field {field}")
            if row["left"] == row["right"]:
                raise ValueError(f"line {line_no}: left and right must differ")
            resolved_winner(row)  # validate winner
            case_id = str(row["case_id"])
            rows_by_case[case_id].append(row)
            candidates.update((str(row["left"]), str(row["right"])))

    score = Counter()
    uncertain = []
    incomplete = []

    for case_id, rows in sorted(rows_by_case.items()):
        if len(rows) < 2:
            incomplete.append(case_id)
            continue

        pair_sets = {frozenset((str(r["left"]), str(r["right"]))) for r in rows}
        if len(pair_sets) != 1:
            uncertain.append((case_id, "different candidate pairs"))
            continue

        winners = [resolved_winner(r) for r in rows]
        non_tie = [w for w in winners if w is not None]

        if len(non_tie) == len(rows) and len(set(non_tie)) == 1:
            score[non_tie[0]] += 1
        elif all(w is None for w in winners):
            score["__tie__"] += 1
        else:
            uncertain.append((case_id, "order disagreement or mixed tie"))

    summary = {
        "cases_seen": len(rows_by_case),
        "consistent_wins": {c: score[c] for c in sorted(candidates)},
        "consistent_ties": score["__tie__"],
        "uncertain_cases": uncertain,
        "incomplete_cases": incomplete,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
