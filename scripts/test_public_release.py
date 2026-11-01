#!/usr/bin/env python3
"""Safe-to-publish smoke checks for the curated public source tree.

This suite intentionally does not replace the private-fixture Core/Full/Soak
contracts or imply any guarantees about actual literary quality.
"""
from __future__ import annotations
import json
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'


def run(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    return subprocess.run([sys.executable, '-B', str(SCRIPTS / 'storyctl.py'), *args],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=40)


def test_route_examples() -> None:
    sample = ROOT / 'assets/regression-corpora/relationship-lean'
    manifest_path = sample / 'project-manifest.json'
    if not manifest_path.exists():
        raise AssertionError('synthetic project fixture not found')
    for intent in ('new-project', 'resume-project', 'continue-chapter', 'diagnose-project'):
        for scoped in (False, True):
            args = ('route', intent, '--json') + (('--manifest', str(manifest_path)) if scoped else ())
            p = run(*args)
            assert p.returncode == 0, (intent, p.stdout, p.stderr)
            steps = json.loads(p.stdout)['steps']
            for row in steps:
                example = row.get('example', '')
                if example.startswith('project verify '):
                    assert example == 'project verify PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT', (intent, example)
    # Act on the real command from the recommendation, not merely a string assertion.
    verify = run('project', 'verify', str(manifest_path), '--root', str(sample), '--json')
    assert verify.returncode == 0, (verify.stdout, verify.stderr)


def test_source_hygiene() -> None:
    assert (ROOT / 'SKILL.md').exists()
    assert (ROOT / 'agents/openai.yaml').exists()
    assert (ROOT / 'LICENSE').is_file()
    assert (ROOT / 'PUBLIC_DATA_POLICY.md').is_file()
    private_paths = [
        'assets/regression-corpora/real-project-hardening',
        'assets/regression-corpora/private-fixture',
        'assets/post-r4-diagnostic',
        'assets/activation-evaluation/runs',
        'docs/model-campaign-results',
        'docs/preview-hardening',
        'experiments/workbench-spike/artifacts',
    ]
    assert all(not (ROOT / name).exists() for name in private_paths)
    markers = [re.compile(rb'-----BEGIN (?:RSA|OPENSSH|EC|DSA|PRIVATE) (?:PRIVATE )?KEY-----'),
               re.compile(rb'gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}'),
               re.compile(rb'sk-(?:proj-)?[A-Za-z0-9_-]{25,}'),
               re.compile(rb'[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/][^\\/\s"<>]+',re.I)]
    offenders=[]
    for p in ROOT.rglob('*'):
        if not p.is_file() or '.git' in p.parts: continue
        b=p.read_bytes()
        if any(rx.search(b) for rx in markers): offenders.append(str(p.relative_to(ROOT)))
    assert not offenders, ('files with potentially sensitive patterns', offenders)
    # Treat all real-user narrative samples as private, even if anonymized.
    # Do not embed private project names in public test code or diagnostics.
    forbidden_fixture_dirs = [x for x in (ROOT / 'assets/regression-corpora').iterdir()
                              if x.is_dir() and (x.name.startswith('real-user-') or x.name.startswith('private-'))]
    assert not forbidden_fixture_dirs, ('private regression roots', [x.name for x in forbidden_fixture_dirs])
    # Every newly introduced regression project must be reviewed before public release.
    allowed_public_regression_roots = {
        'atmospheric-relational-distance',
        'causal-action-control',
        'episodic-investigative-series',
        'fair-clue-detection',
        'formal-heterogeneity',
        'memory-associative-temporality',
        'metaphysical-identity-contestation',
        'minimal-action-omission',
        'obsessive-interiority',
        'open-atmospheric-causality',
        'perceptual-encounter',
        'polyphonic-ideological',
        'prose-state-semantics',
        'quiet-family-seasonal',
        'relationship-lean',
        'retelling-parody',
        'self-misreading-confession',
        'social-ambition-status',
        'structural-irregularity',
        'technical-procedural-clarity',
        'time-loop-forensic',
        'xianxia-growth',
    }
    public_regression_roots = {p.name for p in (ROOT / 'assets/regression-corpora').iterdir() if p.is_dir()}
    assert public_regression_roots <= allowed_public_regression_roots, (
        'unreviewed regression projects must not enter the public distribution',
        sorted(public_regression_roots - allowed_public_regression_roots),
    )
    assert not (ROOT / 'assets/maintenance-validation.json').exists(), 'machine-local maintenance evidence is not distributable'
    corpus_file = ROOT / 'assets/failure-corpus/failure-cases.json'
    if corpus_file.is_file():
        corpus = json.loads(corpus_file.read_text(encoding='utf-8'))
        private_cases = [c.get('id') for c in corpus.get('cases', [])
                         if str(c.get('source', '')).startswith('real-user-')
                         or str(c.get('seed', '')).startswith('assets/regression-corpora/private-')]
        assert not private_cases, ('private-origin corpus cases', private_cases)


def test_workbench_contracts() -> None:
    # The Workbench is an optional technical spike, but its source must not
    # contain broken protocol-schema references in a public checkout.
    from jsonschema import Draft202012Validator
    contract = ROOT / 'docs/workbench/contracts'
    schema_path = contract / 'workbench-wire.schema.json'
    assert schema_path.is_file(), 'Workbench wire schema is missing'
    # Git may store LF even when a Windows checkout used CRLF. The digest is
    # defined over UTF-8 with universal newlines normalized to LF.
    raw = schema_path.read_bytes()
    canonical = schema_path.read_text(encoding='utf-8').encode('utf-8')
    assert canonical == raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n'), 'Unexpected schema byte encoding'
    digest_lf = hashlib.sha256(canonical).hexdigest()
    generated = (ROOT / 'experiments/workbench-spike/desktop/Workbench.Protocol/Generated.cs').read_text(encoding='utf-8')
    assert f'public const string Digest = "sha256:{digest_lf}"' in generated, 'Generated C# schema digest mismatch'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for name in ('golden-wire.json', 'spike-golden-wire.json'):
        path = contract / name
        assert path.is_file(), ('Workbench golden corpus is missing', name)
        cases = json.loads(path.read_text(encoding='utf-8'))
        if name == 'spike-golden-wire.json':
            hello = [row['message']['result'] for row in cases['valid']
                     if row.get('message', {}).get('result', {}).get('kind') == 'Hello']
            assert len(hello) == 1 and hello[0]['schema_digest'] == f'sha256:{digest_lf}', 'Golden Hello schema digest mismatch'
        for group, expected in (('valid', True), ('invalid', False)):
            for row in cases[group]:
                assert validator.is_valid(row['message']) is expected, (name, group, row['name'])
    check = subprocess.run([sys.executable, '-B', str(ROOT / 'experiments/workbench-spike/generate_contract.py'), '--check'],
                           cwd=ROOT, capture_output=True, text=True, timeout=25)
    assert check.returncode == 0, ('Workbench protocol drift', check.stdout, check.stderr)


if __name__ == '__main__':
    test_route_examples()
    test_source_hygiene()
    test_workbench_contracts()
    print('public-release tests PASS (route examples + project verify + privacy allowlist + Workbench protocol goldens)')
