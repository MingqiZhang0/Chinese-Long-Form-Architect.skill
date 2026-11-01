# Unified Tool Surface

Use this reference when an Agent knows **what it wants to do** but is unsure which deterministic script owns the operation. It owns the public CLI discovery surface. Specialized scripts remain the canonical implementations; `storyctl.py` is a front controller, not a second business-logic layer.

## Contents

- Core rule
- Startup capability preflight
- Front controller
- Common routes
- Public command groups
- Write-boundary discipline
- Backend escape hatch
- Maintenance rules

## Core rule

Default to one entry point:

```bash
python scripts/storyctl.py --help
python scripts/storyctl.py catalog
```

Do not make an Agent memorize the whole `scripts/` directory before it can resume a novel.

The unified CLI exists to answer:

- which tool family owns this task;
- whether the operation is read-only, report-only, or potentially mutating;
- which backend will actually execute it;
- what sequence is normal for common intents.

The facade must never duplicate Runtime, validation, migration, context-selection, revision, or live-campaign evidence logic. The long-horizon benchmark backend is `scripts/long_horizon_benchmark.py`; real longitudinal evidence is owned by `scripts/live_campaign.py`; ordinary discovery still routes through `storyctl.py`.

For source-first Chinese comprehension, `reconcile --prepare` generates pending prose coverage and optional state-leaf audit inventories; `reconcile --strict` checks the reviewed 1.1 contract. `revision-diff --review-root ... --dependencies ... --changed-node ... --review-out ...` retrieves graph witnesses plus complete branch-scoped chapter prose for downstream semantic review. Neither command infers meaning or commits canon. Raw-prose evaluation uses `chinese-eval build-state-blind` / `score-state`; see the reconciliation, semantic-revision and Chinese behavioral-evaluation owners for the full contracts.

## 1. Startup capability preflight

Runtime-facing schema tooling has one declared external Python dependency: `jsonschema>=4.18.0,<5.0.0`, recorded in the Skill-root `requirements.txt`. The canonical probe backend is `scripts/capability_probe.py`. It uses only the standard library so a missing/incompatible dependency can be reported before canonical work begins.

Use:

```bash
python scripts/storyctl.py capability check project
python scripts/storyctl.py capability check runtime
python scripts/storyctl.py capability check intensity
python scripts/storyctl.py capability check stc
python scripts/storyctl.py capability check all --json
```

`storyctl.py` automatically and silently runs the appropriate cheap preflight before dependency-sensitive commands such as `project`, `readiness`, `context`, `poetics-envelope`, `voice-audit`, `task-order-validate`, `runtime`, `transaction`, `schema`, `reconcile`, `intensity`, `stc`, the canonical test-tier runner, the long-horizon benchmark, live campaign checks, and integration selftests. Successful preflight must not contaminate machine-readable backend stdout. Failure is fail-fast with the declared requirement and installation hint. `--help`, `catalog`, and route discovery remain available even if the dependency is missing.

Canonical backends remain directly callable; dependency-sensitive direct backends perform their own early check where necessary. Do not let a mutating command create or change project artifacts before required capabilities are known to be available.

## 2. Front controller

Use:

```bash
python scripts/storyctl.py catalog
python scripts/storyctl.py catalog --json
```

The JSON form is the preferred discovery surface for an Agent that needs machine-readable command metadata.

For common workflows:

```bash
python scripts/storyctl.py route new-project
python scripts/storyctl.py route resume-project
python scripts/storyctl.py route continue-chapter
python scripts/storyctl.py route diagnose-project
python scripts/storyctl.py route revise-canon
python scripts/storyctl.py route maintain-skill
```

Routes are **plans**, not automatic chains of mutations. They show the intended sequence and preserve explicit write boundaries. When a Project Manifest is available, pass `--manifest PROJECT_MANIFEST`; the route then respects enabled subsystems instead of pretending a Lean project needs Runtime or a Forensic project can skip its reconciliation/observability gates.

```bash
python scripts/storyctl.py route continue-chapter --manifest project-manifest.json --json
```

## 3. Common direct commands

Project lifecycle:

```bash
python scripts/storyctl.py project --help
```

Prewriting operational readiness (separate from Project Doctor):

```bash
python scripts/storyctl.py readiness PROJECT_ROOT/project-manifest.json PROJECT_ROOT/planning/prewriting-readiness.json --root PROJECT_ROOT --json
```

`REVIEW_READY` means architecture is ready for author review; `DRAFT_READY` additionally requires current Writer-pack compilation, provenance/taint closure, semantic-kernel verification, required Scene Packet coverage, and current-generation pack evidence.

Story-state and semantic-kernel queries:

```bash
python scripts/storyctl.py query --help
python scripts/storyctl.py state-validate --help
python scripts/storyctl.py semantics laws
python scripts/storyctl.py semantics verify PROJECT_ROOT
```

The canonical semantic verifier backend is `scripts/semantic_kernel.py`; ordinary Agent discovery should still go through `storyctl.py`.

Writer/role context and scoped-poetics provenance:

```bash
python scripts/storyctl.py context --help
python scripts/storyctl.py poetics-envelope --help
```

Runtime and event history:

```bash
python scripts/storyctl.py runtime --help
python scripts/storyctl.py transaction --help
python scripts/storyctl.py schema --help
python scripts/storyctl.py invariants --help
```

Diagnosis and revision:

```bash
python scripts/storyctl.py observatory --help
python scripts/storyctl.py revision-diff --help
python scripts/storyctl.py reconcile --help
```

Prose diagnostics:

```bash
python scripts/storyctl.py prose-audit --help
python scripts/storyctl.py paragraph-audit --help
python scripts/storyctl.py voice-audit --help
```

Reasoning intensity:

```bash
python scripts/storyctl.py intensity --help
```

Orchestration:

```bash
python scripts/storyctl.py orchestration-profile --help
python scripts/storyctl.py orchestration-validate --help
python scripts/storyctl.py role-bundle --help
python scripts/storyctl.py checkpoint --help
```

Maintenance / evidence:

```bash
python scripts/storyctl.py tests list
python scripts/storyctl.py tests plan fast
python scripts/storyctl.py tests run fast
python scripts/storyctl.py tests run core
python scripts/storyctl.py tests plan full
python scripts/storyctl.py tests plan soak
python scripts/storyctl.py research-ledger validate
python scripts/storyctl.py research-ledger coverage
python scripts/storyctl.py research-ledger list
python scripts/storyctl.py chinese-eval validate
python scripts/storyctl.py chinese-eval build-blind --out /tmp/cne-packet.jsonl --key-out /tmp/cne-key.jsonl --seed 17
python scripts/storyctl.py activation-eval validate --json
python scripts/storyctl.py activation-eval build-blind --out /tmp/activation-packet.jsonl --json
python scripts/storyctl.py activation-eval score /tmp/activation-predictions.jsonl --require-critical-pass --json
python scripts/storyctl.py multi-poetics-oracle validate --json
python scripts/storyctl.py multi-poetics-oracle selftest --json
python scripts/storyctl.py mutation validate
python scripts/storyctl.py mutation run
python scripts/storyctl.py metamorphic validate
python scripts/storyctl.py metamorphic run
python scripts/storyctl.py campaign registry
python scripts/storyctl.py campaign session-start CAMPAIGN_DIR --project-root PROJECT_ROOT --session-id SESSION_ID
python scripts/storyctl.py campaign session-end CAMPAIGN_DIR --project-root PROJECT_ROOT --session-id SESSION_ID --outcome completed
python scripts/storyctl.py campaign status CAMPAIGN_DIR --project-root PROJECT_ROOT
python scripts/storyctl.py campaign trajectory CAMPAIGN_DIR --project-root PROJECT_ROOT
python scripts/storyctl.py benchmark run --chapters 60
python scripts/storyctl.py stc selftest
python scripts/storyctl.py stc candidate CHALLENGE.json CANDIDATE.json --json
python scripts/storyctl.py stc roundtrip CHALLENGE.json CANDIDATE.json --surface urban --json
python scripts/storyctl.py stc assurance CHALLENGE.json --json
python scripts/storyctl.py selftest
python scripts/storyctl.py fuzz --help
```

## 4. Public command groups

The front controller currently routes these public families:

- `capability` -> cheap startup dependency/capability checks against declared requirements;
- `project` -> project identity, resume, migration, governance profile;
- `readiness` -> pre-draft activation coverage and operational Chapter 1 readiness;
- `query` -> read-only Story State queries, including `open-issues` (`authorial-unknowns` remains a legacy alias);
- `state-validate` -> mechanical continuity findings;
- `semantics` -> read-only cross-layer Narrative Semantics Kernel laws/verification;
- `context` -> least-privilege context compilation with provenance-verified scoped Project Poetics;
- `poetics-envelope` -> create/verify the thin authority/scope/parent/hash/status/expiry envelope for a scoped Project Poetics derivative;
- `runtime` -> replay, branch, impact, compare, merge planning;
- `transaction` -> optimistic-concurrency commit/status;
- `schema` -> artifact/runtime schema validation and migration;
- `invariants` -> mechanically decidable project laws;
- `observatory` -> read-only health report;
- `revision-diff` -> deterministic revision alignment plus diegetic/Project-Poetics classification and invalidation routing; semantic impact interpretation remains a separate Agent pass;
- `reconcile` -> prose/state evidence validation;
- `prose-audit`, `paragraph-audit`, `voice-audit` -> advisory craft diagnostics;
- `intensity` -> Reasoning Intensity config/proposal/result/trace validation and conservative optional-work screening;
- orchestration commands -> capability/profile, pass bundles, checkpoints, run validation;
- `chinese-eval` -> Chinese narrative contrast-corpus validation, blind-packet/key separation, categorical behavior profiles, and human-annotation aggregation;
- `activation-eval` -> trigger-precision corpus validation, blind activation packets, and observed false-positive/false-negative scoring; it does not simulate the platform trigger model;
- `multi-poetics-oracle` -> ten-fixture anti-flattening tasks, conservative deterministic assertions, blinded pointwise evaluation, swapped-order calibration/pairwise comparison, and uncertainty-preserving aggregation;
- `tests` -> canonical Fast/Core/Full/Soak maintenance plans and execution reports;
- `mutation` -> durable failure-corpus validation, fault injection, survivor materialization, and mutation adequacy;
- `metamorphic` -> valid source/follow-up relation registry, semantic invariance, directional/contrast expectations, and isolation gates;
- `campaign` -> prospectively registered real longitudinal campaigns, hashed session/checkpoint ledgers, observational/intervention/recovery probes, evidence maturity, cold-resume records, and bounded claim gates;
- `stc` -> STC v0.1 semantic-conformance generation plus process-separated validation of diegetic time, containment, arbitrary candidates, bounded-choice continuations, Probe Obligations, strict surface round-trip, and mutation/differential/metamorphic assurance;
- `benchmark`, `selftest`, `fuzz` -> synthetic/deterministic Skill maintenance evidence.

Use `catalog --json` rather than copying this list into another control file.

## 5. Write-boundary discipline

A unified CLI must not make writes less visible.

Keep these distinctions explicit:

- **read-only** - queries, validation, audits, replay, impact analysis;
- **report/output-only** - context packs, observatory reports, revision reports, role bundles;
- **mixed** - commands whose selected subcommand may mutate project state;
- **canonical mutation** - Runtime transaction commit, approved project/profile migration, or other explicitly governed write.

Before a canonical mutation, follow the owner reference for that subsystem. `storyctl.py` does not grant permission merely because it can route the command.

## 6. Backend escape hatch

Specialized backend scripts remain public and documented because:

- debugging may require their exact CLI;
- references may specify a backend-specific contract;
- tests should exercise the canonical implementation directly;
- advanced users may intentionally bypass the facade.

Therefore both of these are valid:

```bash
python scripts/storyctl.py project verify PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT
python scripts/project_ops.py verify PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT
```

The first is the default discovery path. The second is the canonical backend.

Do not fork logic between them.

## 7. Maintenance rules

When adding a new public deterministic tool:

1. give one reference module canonical ownership;
2. add the backend script;
3. add or update its regression test;
4. expose it through `storyctl.py` when it is a reusable Agent-facing operation;
5. include mutation metadata in `catalog`;
6. do not add a second facade for the same operation;
7. keep internal helper libraries out of the public catalog.

When removing or renaming a backend, update `storyctl.py` and structural audit in the same change.

## Project Poetics surface

Maintenance `narrative-regime-qualification` delegates to `scripts/narrative_regime_qualification.py` under `chinese-narrative-behavioral-evaluation.md`; it validates stage contracts and selftests existing oracle/context/readiness mechanics. Actual generation/judging remains the `multi-poetics-oracle` surface, with an optional task-stage selector.

The canonical author/planning owner is `project-poetics.md`. Tooling should expose its **location, scope chain, and activation metadata**, not replace literary judgment with a deterministic style router.

Project-facing commands may:

- explicitly bootstrap a missing legacy owner with `storyctl.py project ensure-poetics PROJECT_MANIFEST`, which creates only the blank provisional template and records non-inference provenance;
- discover `canonical_paths.project_poetics`;
- report `poetics_override_refs` and activated optional artifacts;
- include scoped poetics in compiled context packs;
- validate that declared pointers exist and remain inside the project root.

Do not add commands that compute a universal aesthetic score or map `theme -> style preset`. Any future deterministic validation of a formal commitment must operate on an explicitly typed derivative registered through `narrative-invariants.md`.

## Formal readiness operations

`storyctl readiness` delegates check/refresh/freeze/bind-approval/start-chapter-1 to the existing readiness backend. Enter formal prose through `--require-draft-permission` (alias `--require-draft-ready`); diagnostic `--no-recompile` is incompatible. Evidence lifecycle, author transcript binding, legacy migration, fragmentary protocol and precise arguments are maintained only in `prewriting-readiness.md`. `project verify` remains structural health.

## Public-source preview checks

For privacy-curated public source releases, run `scripts/test_public_release.py` with Python to verify the recommended project routes with a synthetic fixture and reject known excluded private archive paths. This suite is additional maintenance hygiene, not a replacement for Core/Full/Soak.

For a public checkout missing intentionally private E2E fixtures, `scripts/test_public_fast.py` executes the supported Fast checks and explicitly reports any skipped private-seed registry. The original `scripts/test_tiers.py` Fast/Core/Full/Soak contract remains unchanged.
