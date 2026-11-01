# Maintenance Test Tier Contract

Use this reference only while maintaining, validating, promoting, or releasing the Skill. It owns the **Fast / Core / Full / Soak execution contract**. Individual benchmark and failure references still own their semantics; this file only decides when and how much of that evidence to run.

## Contents

- Principle
- Tier contract
- Fast
- Core
- Full
- Soak
- Runner and reporting
- Promotion semantics
- Timeout and failure discipline
- Evidence boundaries
- Maintenance rules

## 1. Principle

Do not treat every maintenance change as a release campaign. Match test cost to the claim being made.

Four named tiers are stable:

`Fast < Core < Full < Soak`

The ordering means **assurance scope and expected cost**, not a single scalar quality score. A higher tier must not weaken a lower tier's protected contracts, but its execution list need not literally rerun every lower-tier command.

Use the machine-readable plan in `assets/test-tier-contract.json` through `scripts/test_tiers.py`. Do not maintain a second ad hoc command list in prose.

## 2. Tier contract

Each tier declares:

- its intended maintenance situation;
- an approximate runtime budget, not a hard performance promise;
- required deterministic steps;
- what a PASS supports;
- what a PASS explicitly does **not** support.

A tier PASS means every required step in that tier passed. It never means the Skill has no unknown bugs.

Do not collapse results into one `test quality` number.

## 3. Fast

Use Fast after routine documentation, routing, template, schema, or narrowly scoped code edits and before handing work off.

Fast intentionally stays small. It covers:

- startup dependency/capability availability;
- structural ownership, Phase 0 architecture-freeze enforcement, packaging hygiene, duplicate numbered-heading lint, and product-scope/display-name/compatibility-slug consistency through `scripts/audit_skill_structure.py`;
- mutation registry validity;
- metamorphic registry validity;
- Chinese narrative evaluation corpus validity;
- trigger activation corpus validity;
- Multi-Poetics Behavioural Oracle fixture/schema validity;
- Reasoning Intensity selftest;
- STC v0.1 semantic-conformance smoke: independent Validator process, arbitrary candidates, diegetic-time/containment semantics, continuation/probe checks, and bounded mutation/differential/metamorphic assurance.

Fast deliberately does **not** run the broad integration suite, mutation execution gate, metamorphic execution gate, long-horizon benchmark, or large fuzzing.

A Fast PASS supports the statement **routine maintenance smoke passed**. It does not support `promotion passed`, `release ready`, or `long-horizon verified`.

## 4. Core

Use Core for normal promotion after a substantive owner, schema, deterministic backend, routing, or cross-module behavior change.

Core adds a curated cross-module integration set that covers the highest-value contracts without executing every historical integration case. Integration cases run as isolated subprocesses so one unexpectedly slow case is visible by name instead of hiding inside an opaque 120-second aggregate timeout.

Core also executes:

- a documentation-numbering negative-control contract so the heading lint itself is regression-tested;
- the Skill scope/identity contract, including Chinese-language product scope, non-multilingual-parity boundaries, and deferred controlled slug migration;
- the trigger-activation precision contract, including blind-packet gold isolation plus injected FP/FN detection, with local polish from a long novel protected as non-activation unless persistent project constraints are material;
- the Phase 0 architecture-freeze negative-control contract, proving that an unapproved new reference fails while a complete approved owner-gap exception is the only authorization path;
- the Multi-Poetics Behavioural Oracle harness selftest, including positive controls, known wrong-poetics mutants, blinded-packet leakage checks, swapped-order judge calibration, and cross-fixture flattening diagnostics;
- the registered Failure Corpus mutation gate;
- the registered metamorphic/adversarial gate;
- a bounded seeded Narrative Runtime fuzz sample.

A Core PASS supports **normal promotion gate passed** for the changed Skill version, subject to change-specific tests. It does not substitute for Full when the release changes broad architecture, Runtime semantics, migration, long-horizon behavior, or evaluation infrastructure.

## 5. Full

Use Full before a release/package intended as a new stable baseline, and after major architectural, Runtime, migration, semantics-kernel, benchmark, or broad orchestration changes.

Full runs:

- the complete deterministic integration suite;
- mutation and metamorphic promotion gates;
- a broader STC semantic-conformance seed sweep through the independent Validator;
- a larger Runtime fuzz sample;
- the deterministic 60-chapter long-horizon benchmark;
- structural/capability checks.

A Full PASS supports **internal deterministic release gate passed**. The official Skill validator and packaging validator still run separately during packaging because they are external release checks, not portable Skill-internal tests.

Full does not establish real longitudinal campaign evidence or literary quality.

## 6. Soak

Use Soak only when the expected value justifies the cost: major Runtime changes, longitudinal/state machinery rewrites, benchmark infrastructure changes, release candidates with elevated continuity risk, or explicit reliability campaigns.

Soak is never the default daily maintenance loop.

It adds:

- a 100-chapter deterministic long-horizon run;
- a 200-seed STC semantic-conformance sweep;
- several large Runtime fuzz runs under independent seeds;
- the complete deterministic integration, mutation, and metamorphic gates.

A Soak PASS supports **high-cost synthetic reliability campaign passed**. It still does not support `real 100-chapter evidence`; only the prospective live-campaign protocol can support that wording.

## 7. Runner and reporting

Public surface:

```bash
python scripts/storyctl.py tests list
python scripts/storyctl.py tests plan fast
python scripts/storyctl.py tests run fast
python scripts/storyctl.py tests run core
python scripts/storyctl.py tests run full
python scripts/storyctl.py tests run soak
```

Use `--json` for machine-readable plan or run reports. Use `--step STEP_ID` only for targeted debugging; a partial run must report `partial: true` and must not be called a tier PASS.

The runner:

- reads the machine contract rather than duplicating tier membership in code;
- runs from the Skill root;
- sets `PYTHONDONTWRITEBYTECODE=1` so maintenance tests do not create package cache artifacts;
- isolates Core integration cases by case name;
- applies per-step timeouts;
- records step duration, status, command, and bounded stdout/stderr tails;
- stops on first failure by default unless `--continue-on-failure` is explicitly requested.

A timeout is a distinct `TIMEOUT` result, not an assertion failure and not a PASS.

## 8. Promotion semantics

Use these default decision rules:

- tiny/local maintenance: Fast;
- substantive normal promotion: Core;
- stable release or major architecture: Full;
- explicit high-cost reliability campaign: Soak.

Escalate when the changed mechanism is outside the current tier's evidence envelope. Do not escalate merely because a higher tier exists.

A change-specific deterministic test may be required in addition to the named tier. The tier contract is a floor, not an excuse to omit a direct reproducer for the defect being fixed.

## 9. Timeout and failure discipline

Never hide a slow group behind one giant opaque command when the runner can isolate it.

If a Core integration case times out:

1. report that exact case as `TIMEOUT`;
2. do not rerun the same aggregate command merely to hope for a different result;
3. inspect or split the responsible case;
4. move genuinely high-cost behavior upward to Full/Soak if the lower-tier claim does not require it.

Do not weaken a timeout solely to make promotion green. Increase a timeout only when the test's semantic scope justifies the cost and the tier contract remains honest.

## 10. Evidence boundaries

Synthetic deterministic tiers test operational contracts. They do not prove:

- human preference;
- literary excellence;
- real reader response;
- real multi-month maintenance burden;
- real 100/300-chapter campaign evidence;
- future runtime/model behavior.

Use `evaluation-benchmark.md` for version comparison, `failure-corpus-mutation-testing.md` for mutation semantics, `metamorphic-adversarial-benchmark.md` for relation semantics, `intensity-longitudinal-benchmark.md` for STC/Intensity calibration, and `live-campaign-longitudinal-evaluation.md` for prospective real longitudinal claims.

## 11. Maintenance rules

- Keep tier names stable; change membership through the machine contract.
- New heavy tests default to Full or Soak until evidence justifies moving them lower.
- New cheap contract/registry checks may enter Fast only if they stay deterministic and do not materially inflate routine latency.
- Core should remain a curated promotion surface rather than gradually becoming `Full with a different name`.
- Soak may grow expensive; that is acceptable only because it is explicit and non-default.
- Report the exact tier, contract version, failed/timed-out step IDs, and whether the run was partial.
- When the machine plan changes materially, update this owner reference, `storyctl` routing, and integration contract tests in the same change.

Core registers seven production-readiness integration cases and three focused prose/state/impact contracts (51 required steps; Full executes all 80 integration cases). The latter protect typed semantic coverage, graph plus unindexed dependency discovery, and a raw-prose blind-scoring harness with omission and grounding mutants. Counts describe this plan revision, not a universal frozen quota. These suites exercise their owners through positive controls and focused fault injections; tests never replace human semantic review, prove model comprehension accuracy, or authenticate local transcript attestations.
