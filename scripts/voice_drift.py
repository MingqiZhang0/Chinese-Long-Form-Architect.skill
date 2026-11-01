#!/usr/bin/env python3
"""Measure advisory dialogue drift from attributed utterance JSONL.

Each input row: {"character":"id","chapter":12,"text":"..."}
The tool compares an early baseline window with a recent window. Metrics are
language-light and intentionally advisory, not a prose quality score.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scoped_poetics import verify_envelope

SENTENCE_END = re.compile(r"[.!?。！？]+")
WORD = re.compile(r"[A-Za-z0-9_']+|[\u3400-\u9fff]")


def load_rows(path: Path) -> list[dict[str, Any]]:
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get("text"), str):
            raise ValueError(f"line {i}: expected object with text")
        out.append(row)
    return out


def feats(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {"utterances": 0, "mean_chars": 0.0, "mean_sentences": 0.0, "question_rate": 0.0, "exclamation_rate": 0.0, "fragment_rate": 0.0}
    lengths = [len(r["text"].strip()) for r in rows]
    sentence_counts = [max(1, len(SENTENCE_END.findall(r["text"]))) for r in rows]
    questions = sum(1 for r in rows if "?" in r["text"] or "？" in r["text"])
    exclaims = sum(1 for r in rows if "!" in r["text"] or "！" in r["text"])
    fragments = sum(1 for r in rows if len(WORD.findall(r["text"])) <= 3)
    return {
        "utterances": float(len(rows)),
        "mean_chars": sum(lengths) / len(lengths),
        "mean_sentences": sum(sentence_counts) / len(sentence_counts),
        "question_rate": questions / len(rows),
        "exclamation_rate": exclaims / len(rows),
        "fragment_rate": fragments / len(rows),
    }


def distance(a: dict[str, float], b: dict[str, float]) -> float:
    scales = {
        "mean_chars": max(8.0, a["mean_chars"], b["mean_chars"]),
        "mean_sentences": max(1.0, a["mean_sentences"], b["mean_sentences"]),
        "question_rate": 1.0,
        "exclamation_rate": 1.0,
        "fragment_rate": 1.0,
    }
    sq = 0.0
    for key, scale in scales.items():
        sq += ((a[key] - b[key]) / scale) ** 2
    return math.sqrt(sq / len(scales))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input")
    p.add_argument("--baseline-through", type=float, required=True)
    p.add_argument("--recent-from", type=float, required=True)
    p.add_argument("--min-lines", type=int, default=5)
    p.add_argument(
        "--authorized-shift", action="append", default=[], metavar="CHARACTER",
        help="character whose current voice/register change is explicitly authorized by the supplied scoped Project Poetics; repeatable",
    )
    p.add_argument("--project-root", type=Path, help="project root required for provenance-backed authorization")
    p.add_argument("--project-manifest", default="project-manifest.json", help="project-relative manifest used to verify Project Poetics authority")
    p.add_argument("--scoped-poetics-ref", help="project-relative Writer-safe scoped Project Poetics Markdown")
    p.add_argument("--scoped-poetics-envelope-ref", help="project-relative provenance envelope for the scoped Project Poetics")
    p.add_argument("--scope-arc")
    p.add_argument("--scope-chapter")
    p.add_argument("--scope-scene")
    p.add_argument("--scope-task")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    authorized = {str(x) for x in args.authorized_shift}
    provenance = None
    poetics_supplied = any([args.scoped_poetics_ref, args.scoped_poetics_envelope_ref, args.project_root])
    if authorized and not (args.project_root and args.scoped_poetics_ref and args.scoped_poetics_envelope_ref):
        p.error("--authorized-shift requires --project-root, --scoped-poetics-ref, and --scoped-poetics-envelope-ref")
    if poetics_supplied:
        if not (args.project_root and args.scoped_poetics_ref and args.scoped_poetics_envelope_ref):
            p.error("scoped Project Poetics provenance requires --project-root, --scoped-poetics-ref, and --scoped-poetics-envelope-ref together")
        provenance, provenance_errors = verify_envelope(
            root=args.project_root.resolve(),
            content_ref=args.scoped_poetics_ref,
            envelope_ref=args.scoped_poetics_envelope_ref,
            project_manifest_ref=args.project_manifest,
            scope_context={
                "arc": args.scope_arc,
                "chapter": args.scope_chapter,
                "scene": args.scope_scene,
                "task": args.scope_task,
            },
        )
        if provenance_errors:
            for msg in provenance_errors:
                print(f"ERROR: scoped Project Poetics provenance: {msg}", file=sys.stderr)
            return 2

    rows = load_rows(Path(args.input))
    chars = defaultdict(list)
    for row in rows:
        chars[str(row.get("character", "?"))].append(row)

    report = []
    for character, items in sorted(chars.items()):
        base = [x for x in items if isinstance(x.get("chapter"), (int, float)) and float(x["chapter"]) <= args.baseline_through]
        recent = [x for x in items if isinstance(x.get("chapter"), (int, float)) and float(x["chapter"]) >= args.recent_from]
        bf, rf = feats(base), feats(recent)
        if len(base) < args.min_lines or len(recent) < args.min_lines:
            report.append({"character": character, "status": "insufficient-data", "baseline_lines": len(base), "recent_lines": len(recent)})
            continue
        d = distance(bf, rf)
        status = "authorized-variation" if character in authorized else ("review" if d >= 0.22 else "stable-looking")
        report.append({
            "character": character,
            "status": status,
            "drift_indicator": round(d, 4),
            "baseline": bf,
            "recent": rf,
            "authorized_by_scoped_poetics": character in authorized,
            "scoped_poetics_envelope_ref": args.scoped_poetics_envelope_ref if character in authorized else None,
            "scoped_poetics_content_sha256": (
                provenance.get("hash", {}).get("content_sha256")
                if character in authorized and isinstance(provenance, dict)
                else None
            ),
            "note": (
                "Advisory only: review character development, audience, stress, register, and scoped Project Poetics before treating drift as error. "
                "An authorized variation is reported, not normalized."
            ),
        })

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for r in report:
            print(" | ".join(f"{k}={v}" for k, v in r.items() if k not in {"baseline", "recent"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
