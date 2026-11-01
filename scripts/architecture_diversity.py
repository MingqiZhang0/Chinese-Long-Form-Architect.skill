#!/usr/bin/env python3
"""Compare manually/LLM-authored architecture fingerprints for convergence risk.

This is a maintenance diagnostic, not a literary score. It reports pairwise token-set
similarity so maintainers can notice when unrelated genres start inheriting the same
structural defaults after a Skill update.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or not isinstance(data.get('features'),dict):
        raise ValueError(f'{path} must contain an object with features')
    return data


def tokens(rec: dict[str, Any]) -> set[str]:
    out: set[str] = set()

    def add_value(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, child in sorted(value.items()):
                add_value(f"{prefix}.{key}" if prefix else str(key), child)
        elif isinstance(value, list):
            for child in value:
                add_value(prefix, child)
        elif value is not None and str(value).strip():
            out.add(f"{prefix}={str(value).strip().lower()}")

    add_value("", rec['features'])
    return out


def jaccard(a:set[str], b:set[str])->float:
    if not a and not b: return 1.0
    return len(a & b)/len(a | b) if (a|b) else 0.0


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('fingerprints', nargs='+', type=Path)
    p.add_argument('--warn-threshold', type=float, default=0.75)
    p.add_argument('--json', action='store_true')
    args=p.parse_args()
    if len(args.fingerprints)<2:
        p.error('provide at least two fingerprints')
    rows=[]
    loaded=[(path,load(path)) for path in args.fingerprints]
    for i,(pa,a) in enumerate(loaded):
        for pb,b in loaded[i+1:]:
            sim=jaccard(tokens(a),tokens(b))
            rows.append({
                'a':a.get('project_id',pa.stem),
                'b':b.get('project_id',pb.stem),
                'similarity':round(sim,4),
                'convergence_warning':sim>=args.warn_threshold,
            })
    out={'threshold':args.warn_threshold,'pairs':rows,'warning_count':sum(1 for r in rows if r['convergence_warning']), 'note':'Diagnostic only; similarity is not literary quality and diverse Project Poetics should not be normalized.'}
    if args.json:
        print(json.dumps(out,ensure_ascii=False,indent=2))
    else:
        for r in rows:
            flag=' WARNING' if r['convergence_warning'] else ''
            print(f"{r['a']} vs {r['b']}: {r['similarity']:.4f}{flag}")
        print(f"warnings: {out['warning_count']} (diagnostic only; not a quality score)")
    return 0
if __name__=='__main__':
    raise SystemExit(main())
