#!/usr/bin/env python3
"""Report exact long-paragraph duplication and documentation growth in this Skill.

Maintenance diagnostic only. Repeated cross-cutting laws can be legitimate, so the
script does not fail by default and never rewrites references automatically.
"""
from __future__ import annotations
import argparse, json, re
from collections import defaultdict
from pathlib import Path


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold()


def prose_paragraphs(path: Path) -> list[tuple[int, str]]:
    lines=path.read_text(encoding='utf-8').splitlines()
    rows=[]; buf=[]; start=1; in_code=False
    def flush():
        nonlocal buf,start
        if buf:
            text=' '.join(x.strip() for x in buf).strip()
            if len(text)>=160 and not text.startswith(('#','- ','* ','|','>','```')):
                rows.append((start,text))
            buf=[]
    for i,line in enumerate(lines,1):
        if line.strip().startswith('```'):
            flush(); in_code=not in_code; continue
        if in_code:
            continue
        if not line.strip():
            flush(); start=i+1; continue
        if not buf: start=i
        buf.append(line)
    flush(); return rows


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--json', action='store_true')
    p.add_argument('--strict', action='store_true', help='exit 1 when exact long-paragraph duplication exists')
    args=p.parse_args(); root=args.root.resolve(); refs=sorted((root/'references').glob('*.md'))
    groups=defaultdict(list); total_lines=0
    for f in refs:
        total_lines += len(f.read_text(encoding='utf-8').splitlines())
        for line,text in prose_paragraphs(f):
            groups[normalize(text)].append({'file':str(f.relative_to(root)),'line':line,'preview':text[:140]})
    dups=[v for v in groups.values() if len({x['file'] for x in v})>1]
    dups.sort(key=lambda x:(-len(x),x[0]['file']))
    skill_text=(root/'SKILL.md').read_text(encoding='utf-8')
    capability_markers=(
        'polyphony', 'hidden-process depth', 'hidden causal network', 'material embodiment',
        'outer structure should converge', 'compress non-change',
    )
    universal_capability_mentions=[m for m in capability_markers if m.casefold() in skill_text.casefold()]
    result={
        'reference_count':len(refs),
        'reference_lines':total_lines,
        'skill_lines':len((root/'SKILL.md').read_text(encoding='utf-8').splitlines()),
        'duplicate_long_paragraph_groups':dups,
        'duplicate_group_count':len(dups),
        'universal_capability_mentions':universal_capability_mentions,
        'note':'Exact duplication is a maintenance signal, not proof that a repeated law is wrong.'
    }
    if args.json: print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print(f"references: {result['reference_count']} files / {total_lines} lines")
        print(f"SKILL.md: {result['skill_lines']} lines")
        print(f"exact long-paragraph duplicate groups: {len(dups)}")
        print(f"possible capability-as-universal mentions in SKILL.md: {len(universal_capability_mentions)}")
        for marker in universal_capability_mentions: print(f"- review universal capability marker: {marker}")
        for group in dups[:20]:
            locs=', '.join(f"{x['file']}:{x['line']}" for x in group)
            print(f"- {locs} :: {group[0]['preview']}")
    return 1 if args.strict and dups else 0
if __name__=='__main__': raise SystemExit(main())
