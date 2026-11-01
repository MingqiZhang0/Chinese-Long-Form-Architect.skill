# Regression Corpus Retention Policy

These fixtures exist to exercise cross-module behavior. Keep **canonical/source inputs and deliberately adversarial fixtures**; regenerate disposable outputs inside tests.

Retain when a file is needed as:

- canonical project state or prose;
- a stable source input to a regression;
- a deliberately malformed/adversarial input whose bytes matter;
- a compact expected fixture that cannot be reproduced cheaply.

Do not retain routine generated artifacts merely because an earlier manual E2E run produced them, including compiled Writer packs/manifests, Observatory reports, replay caches, transaction proposals, readiness/adversarial-review status reports, paragraph-profile reports, or mechanical revision diffs. Tests should create those in temporary directories and assert their behavior.

If a generated artifact must be retained, document the exact regression that requires its frozen bytes in the corpus README.

## Corpus roles

- A private long-form E2E fixture used during development is intentionally excluded from this public source package. Reproducible public tests use the remaining synthetic fixtures.
- `relationship-lean/` - low-mechanism relationship fiction; proves Lean governance stays lightweight.
- `xianxia-growth/` - research-free Persistent progression fantasy; exercises Runtime/context continuity, injury/resource/logistics shape, and proves research machinery stays conditional.
- `time-loop-forensic/` - Forensic branch/secret/role-isolation fixture with a real invariant, semantic revision, prose-state reconciliation, and replayable checkpoint state.

Story-specific optional protections claimed by a fixture should have durable evidence rather than empty placeholders. Profile-baseline infrastructure may be structurally empty only when emptiness is itself a valid state (for example, a dependency graph with no current edges).

## Generated long-horizon benchmark

The 60-chapter long-horizon continuity project is generated on demand by `scripts/long_horizon_benchmark.py`; do not freeze its disposable project tree under `assets/regression-corpora/`. This keeps the Skill package small while ensuring each maintenance run proves that the current toolchain can still construct, replay, compile, and validate a long chain from scratch.
## Relationship to the failure corpus

These project fixtures are reusable **seeds**. Concrete historical incidents live separately in `assets/failure-corpus/failure-cases.json`. Mutation tests copy a known-good seed to a temporary directory, inject one focused fault, and ask the canonical owner/oracle to detect or contain it. Do not store every mutated project under this directory; materialize survivors only for debugging/minimization.



## Multi-poetics adversarial fixtures

The following compact fixtures are **not author/style imitation targets**. They adversarially test whether maintenance changes preserve sharply different local poetics without weakening hard continuity:

- `quiet-family-seasonal/` - ordinary recurrence, family/social familiarity, seasonal/material accumulation;
- `obsessive-interiority/` - highly concentrated consciousness and object/idea fixation;
- `minimal-action-omission/` - action/body/material resistance with limited explicit introspection;
- `polyphonic-ideological/` - deliberately activated thematic polyphony;
- `structural-irregularity/` - unequal attention and intentionally uneven long-form structure;
- `formal-heterogeneity/` - authorized chapter-scoped formal variation;
- `perceptual-encounter/` - experiential/perceptual completion without mandatory plot delta;
- `fair-clue-detection/` - strict local clue/inference/fairness commitments;
- `retelling-parody/` - inherited-story material as an explicit poetic resource;
- `self-misreading-confession/` - first-person self-model distinct from psychological/world truth.

Use them together. A maintenance change fails the plurality gate if it improves one family by silently importing that family's virtues into incompatible fixtures.
### Behavioural oracle contract

The ten multi-poetics fixtures are executable, not metadata-only. Each fixture carries `input.md`, `task.md`, `oracle.json`, one non-unique `control-preserving.md`, and one deliberate `wrong-poetics-mutant.md`. Run `storyctl multi-poetics-oracle selftest` for harness integrity; for a real Skill/model candidate, use `build-generation`, save one output per fixture, run `check`, then use `build-blind` and `aggregate` with independent judge responses. Deterministic PASS alone never proves literary or poetics adequacy.

