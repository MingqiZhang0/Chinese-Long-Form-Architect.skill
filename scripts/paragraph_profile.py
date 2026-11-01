#!/usr/bin/env python3
"""Describe paragraph-shape patterns without judging prose quality.

The report is advisory only. It helps select passages for semantic paragraph
review; it must not be used as a target score or automatic rewrite rule.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from statistics import mean, median
from typing import Any

SENTENCE_END = re.compile(r"[.!?。！？]+")
PARA_SPLIT = re.compile(r"\n\s*\n+")
DIALOGUE_START = re.compile(r"^[\s\"'“‘「『—-]*[^\n]{0,8}[\"'“‘「『]?$")
QUOTE_PREFIX = tuple("\"'“‘「『—-")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", "", text)


def sentence_count(text: str) -> int:
    count = len(SENTENCE_END.findall(text))
    return max(1, count) if text.strip() else 0


def quantile(values: list[int], q: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    if len(xs) == 1:
        return float(xs[0])
    pos = (len(xs) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(xs[lo])
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def dialogue_like(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if stripped.startswith(QUOTE_PREFIX):
        return True
    quote_chars = sum(stripped.count(ch) for ch in ('“', '”', '「', '」', '『', '』', '"'))
    return quote_chars >= 2 and len(clean_text(stripped)) <= 180


def load_paragraphs(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [p.strip() for p in PARA_SPLIT.split(raw) if p.strip()]
    return paragraphs


def consecutive_runs(flags: list[bool], min_run: int) -> list[dict[str, int]]:
    runs: list[dict[str, int]] = []
    start = None
    for idx, flag in enumerate(flags):
        if flag and start is None:
            start = idx
        if (not flag or idx == len(flags) - 1) and start is not None:
            end = idx if flag and idx == len(flags) - 1 else idx - 1
            length = end - start + 1
            if length >= min_run:
                runs.append({"start_paragraph": start + 1, "end_paragraph": end + 1, "count": length})
            start = None
    return runs


def build_report(paragraphs: list[str], min_run: int) -> dict[str, Any]:
    lengths = [len(clean_text(p)) for p in paragraphs]
    sentences = [sentence_count(p) for p in paragraphs]
    one_sentence = [s == 1 for s in sentences]
    dialogue = [dialogue_like(p) for p in paragraphs]

    med = median(lengths) if lengths else 0.0
    q1 = quantile(lengths, 0.25)
    q3 = quantile(lengths, 0.75)
    iqr = q3 - q1

    # These are local review heuristics, not quality thresholds.
    local_short_cutoff = max(12.0, min(48.0, med * 0.35 if med else 24.0))
    local_long_cutoff = max(260.0, q3 + 1.5 * iqr if lengths else 260.0)
    short_flags = [l <= local_short_cutoff and s <= 1 for l, s in zip(lengths, sentences)]
    long_outliers = [
        {"paragraph": i + 1, "chars": l, "sentences": sentences[i]}
        for i, l in enumerate(lengths)
        if l >= local_long_cutoff
    ]

    return {
        "note": "Advisory only. Paragraph quality depends on semantic continuity, discourse mode, and deliberate boundary design; do not optimize toward these numbers.",
        "paragraphs": len(paragraphs),
        "characters": sum(lengths),
        "paragraph_length_chars": {
            "mean": round(mean(lengths), 2) if lengths else 0.0,
            "median": round(float(med), 2),
            "q1": round(q1, 2),
            "q3": round(q3, 2),
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
        },
        "sentences_per_paragraph": {
            "mean": round(mean(sentences), 2) if sentences else 0.0,
            "median": round(float(median(sentences)), 2) if sentences else 0.0,
        },
        "one_sentence_paragraph_rate": round(sum(one_sentence) / len(paragraphs), 4) if paragraphs else 0.0,
        "dialogue_like_paragraph_rate": round(sum(dialogue) / len(paragraphs), 4) if paragraphs else 0.0,
        "local_review_heuristics": {
            "short_one_sentence_cutoff_chars": round(local_short_cutoff, 2),
            "long_outlier_cutoff_chars": round(local_long_cutoff, 2),
            "consecutive_short_runs": consecutive_runs(short_flags, min_run),
            "long_outliers": long_outliers,
        },
    }


def print_text(report: dict[str, Any]) -> None:
    print(report["note"])
    print(f"paragraphs={report['paragraphs']} characters={report['characters']}")
    lengths = report["paragraph_length_chars"]
    print(
        "paragraph_chars="
        f"mean:{lengths['mean']} median:{lengths['median']} q1:{lengths['q1']} "
        f"q3:{lengths['q3']} min:{lengths['min']} max:{lengths['max']}"
    )
    sents = report["sentences_per_paragraph"]
    print(f"sentences_per_paragraph=mean:{sents['mean']} median:{sents['median']}")
    print(f"one_sentence_rate={report['one_sentence_paragraph_rate']}")
    print(f"dialogue_like_rate={report['dialogue_like_paragraph_rate']}")
    heur = report["local_review_heuristics"]
    for run in heur["consecutive_short_runs"]:
        print(
            "review_short_run="
            f"{run['start_paragraph']}-{run['end_paragraph']} count:{run['count']}"
        )
    for item in heur["long_outliers"]:
        print(
            "review_long_outlier="
            f"paragraph:{item['paragraph']} chars:{item['chars']} sentences:{item['sentences']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="UTF-8 prose file with paragraphs separated by blank lines")
    parser.add_argument("--min-run", type=int, default=4, help="Minimum consecutive locally-short paragraphs to report")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.min_run < 2:
        raise SystemExit("--min-run must be >= 2")

    paragraphs = load_paragraphs(Path(args.input))
    report = build_report(paragraphs, args.min_run)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
