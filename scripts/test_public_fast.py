#!/usr/bin/env python3
"""Privacy-aware public Fast subset; original Fast contract remains unchanged.

This validates and runs the executable Fast command subset without falsely
claiming to enumerate the withheld historical Core/Full/Soak integration suite.
Some private-derived failure-corpus records have been removed from this version.
"""
from __future__ import annotations
import json
import sys
from test_tiers import load_contract, run_step, step_argv

SKIPPED = {}


def main() -> int:
    contract = load_contract()
    errors = []
    if contract.get('schema_version') != '1.0.0':
        errors.append('unsupported tier schema_version')
    tiers = contract.get('tiers', {})
    if not isinstance(tiers, dict) or set(tiers) != {'fast','core','full','soak'}:
        errors.append('tier registry missing required tiers')
    fast = tiers.get('fast', {}) if isinstance(tiers, dict) else {}
    seen = set()
    for step in fast.get('steps', []):
        sid = step.get('id')
        if not isinstance(sid, str) or sid in seen:
            errors.append('invalid or duplicate Fast ID')
        seen.add(sid)
        if step.get('runner') != 'command':
            errors.append(f'{sid} public Fast can only execute command runners')
        if not isinstance(step.get('timeout_seconds'), int) or step['timeout_seconds'] <= 0:
            errors.append(f'{sid} has invalid timeout')
        try:
            from pathlib import Path
            if not Path(step_argv(step)[0]).is_file():
                errors.append(f'{sid} backend is missing')
        except Exception as exc:
            errors.append(f'{sid} invalid command: {exc}')
    if errors:
        print(json.dumps({'passed': False, 'errors': errors}, ensure_ascii=False, indent=2))
        return 1
    steps = list(contract['tiers']['fast']['steps'])
    results = []
    for step in steps:
        sid = str(step['id'])
        if sid in SKIPPED:
            results.append({'id': sid, 'status': 'SKIP_PRIVATE', 'reason': SKIPPED[sid]})
            continue
        results.append(run_step(step))
    passed = all(x['status'] in ('PASS', 'SKIP_PRIVATE') for x in results)
    payload = {'public_fast_passed': passed,
               'full_fast_passed': False,
               'original_fast_steps': len(steps),
               'passed_steps': sum(x['status']=='PASS' for x in results),
               'skipped_private_steps': sum(x['status']=='SKIP_PRIVATE' for x in results),
               'results':results}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 1

if __name__=='__main__':
    sys.exit(main())
