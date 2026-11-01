# Failure Corpus and Narrative Mutation Testing

Load this reference when maintaining the Skill, converting a discovered defect into durable regression memory, evaluating detector strength, or deciding whether a new release is robust enough to promote. It owns the concrete failure ledger and fault-injection mutation protocol. `regression-tests.md` still owns broad failure families; `evaluation-benchmark.md` still owns version-to-version quality evaluation; the next-layer metamorphic benchmark owns semantics-preserving input transformations.

## Contents

- Purpose and boundary
- Core entities
- Failure-capture lifecycle
- Mutation operator design
- Oracles and mutation score
- Survivors, invalid mutants, and equivalent mutants
- Counterexample minimization
- Promotion gate
- CLI workflow
- Maintenance rules
- Research basis

## 1. Purpose and boundary

A mature Skill must remember more than its current rules. Preserve the failures that forced those rules to exist.

The durable corpus is `assets/failure-corpus/failure-cases.json`. It contains:

- concrete historical incidents discovered during real E2E, integration, cleanup, or Kernel work;
- the owner module whose contract was actually wrong;
- the mechanism and lesson, rather than only the symptom;
- a deterministic mutation operator and oracle when honest automation is possible;
- a documented-only record when no trustworthy deterministic oracle exists yet.

Do not invent an oracle merely to increase automated coverage. A documented failure with an honest gap is more valuable than a fake test.

This layer uses **semantic/artifact fault injection**. It deliberately corrupts valid project/context/runtime artifacts and asks the canonical owner to reject, detect, or contain the fault. It does not replace source-code mutation testing of Python implementation internals, and it does not replace literary judgment.

## 2. Core entities

Keep these terms distinct:

- **failure family** - broad reusable mechanism in `regression-tests.md`, such as negative spoiler leakage or context alias duplication;
- **failure case** - one concrete incident/reproducer with a stable `FC-*` identity;
- **seed fixture** - known-good project copied before injection;
- **mutation operator** - one focused transformation that injects a representative defect;
- **mutant** - the resulting faulty fixture;
- **oracle** - canonical detector or containment property used to judge the mutant;
- **killed mutant** - the oracle detects/rejects the fault, or the authoritative layer contains it so the wrong state cannot affect the result;
- **surviving mutant** - the injected non-equivalent fault passes through the intended oracle;
- **invalid mutant** - baseline was already broken, the operator changed nothing, or the mutation bypassed the intended semantic contract in a meaningless way;
- **equivalent mutant** - representation changed but the behavior/properties under test are genuinely unchanged. Do not count it as a failure or as score-improving evidence.

## 3. Failure-capture lifecycle

When a real failure is discovered:

1. **Freeze the observation.** Preserve the exact symptom, affected project state, and tool/version context before fixing it when possible.
2. **Find the owner-level mechanism.** Avoid naming the case after a surface error message when the true problem is lifecycle, provenance, authority, identity, or information flow.
3. **Minimize.** Remove unrelated files/fields/steps until the failure still reproduces. Keep the smallest structured counterexample that preserves the same mechanism.
4. **Assign a stable `FC-*` ID.** IDs are append-only compatibility handles; do not recycle them.
5. **Link the broad regression family** when one exists. Multiple incidents may belong to one family.
6. **Choose an oracle.** Prefer the canonical owner validator/Kernel law/compiler behavior over a new ad-hoc checker.
7. **Automate only when honest.** If no deterministic oracle exists, keep the case documented and expose the gap.
8. **Fix the owner contract.** Do not special-case the one fixture inside the mutation runner.
9. **Run the mutant again.** The new detector/containment behavior must kill it.
10. **Keep the case forever** unless it is proven semantically duplicate of another case; if merged, preserve its retired ID in notes.

A bug fix without a durable reproducer is incomplete for this Skill's maintenance layer.

## 4. Mutation operator design

Good narrative mutators are:

- **representative** - modeled on a real failure or a plausible near-neighbor of one;
- **small** - one semantic defect per operator whenever possible;
- **owner-targeted** - they exercise a contract the named owner claims to enforce;
- **nontrivial** - malformed JSON or a missing whole project directory is usually too easy and teaches little;
- **deterministic** - the same Skill version and seed fixture produce the same mutated bytes;
- **auditable** - the runner records touched semantic surfaces and before/after tree hashes;
- **orthogonal enough** - do not add several nearly identical mutants merely to inflate the score.

Current operator families include:

- Runtime identity/order/branch-lineage corruption;
- Context provenance, branch isolation, declassification, literal leakage, and alias pressure;
- open-authorial-unknown collapse;
- stale prose-state evidence;
- Project Manifest guarantee/artifact inconsistency;
- authoritative Runtime dependency graph versus stale embedded projection.

Prefer mutations that are close to competent real maintenance mistakes. Trivial mutants that every parser rejects should not dominate the suite.

## 5. Oracles and mutation score

For every automated case, the runner must first prove that the **unmutated seed passes** the intended oracle. Otherwise classify the case `INVALID_BASELINE`; never call it killed.

Then inject the fault and run the canonical oracle.

The mutation score is:

`killed non-equivalent mutants / (killed + surviving non-equivalent mutants)`

Exclude documented-only cases, invalid baselines, invalid no-op mutants, and explicitly justified equivalent mutants from the denominator.

Do not compare mutation scores across versions if the operator set changed without also reporting which operators were added/removed. The score is evidence about the current corpus, not an absolute measure of narrative quality.

A containment oracle can count as a kill. Example: when Story State carries a stale embedded dependency graph, a correct Runtime-aware query may still return the authoritative Runtime result. The wrong projection was injected, but the system prevented it from taking semantic authority.

## 6. Survivors, invalid mutants, and equivalent mutants

A **survivor is valuable evidence**. Do not hide it to preserve a perfect score.

When a mutant survives:

1. materialize it with `mutation reproduce` or `--keep-survivors`;
2. confirm the mutation is non-equivalent and the seed baseline is valid;
3. identify whether the missing protection belongs in an existing owner, Kernel seam, or genuinely cannot be machine-decided;
4. minimize the reproducer again if possible;
5. repair the owner contract;
6. add/strengthen a deterministic regression that covers the newly discovered combination;
7. rerun the full mutation suite.

If the survivor exposes an oracle problem rather than an implementation problem, fix the oracle contract first. Never teach the runner the expected error string while leaving the semantic hole open.

Equivalent mutants are a known mutation-testing hazard. Require an explicit equivalence rationale before excluding one. "The current tests do not notice" is not equivalence.

## 7. Counterexample minimization

A random seed is not a durable failure artifact by itself. Generator changes can make the same seed produce a different structure.

Prefer to preserve:

- minimized JSON/JSONL objects;
- the smallest event trace that still fails;
- a focused context-index/provenance fragment;
- a minimal prose/evidence pair;
- the exact mutation operator plus a stable seed fixture.

When a raw failure is large, apply delta-debugging/shrinking thinking:

- remove unrelated chapters/events/entries;
- delete unrelated fields;
- shorten lists while preserving referential validity;
- reduce a multi-step failure to the shortest command/event sequence that still triggers the same oracle;
- preserve the semantic preconditions of the bug while shrinking.

The current `reproduce` command creates a deterministic project-level reproducer. Further shrinking remains an explicit maintenance task rather than silently treating the full seed project as minimal.

## 7.1 OpenIssue failure memory

Treat authorial-openness corruption as mutation-testable infrastructure failure when the mechanism is machine-decidable. Current automated operators cover:

- laundering a `working_hypothesis` into an authoritative compatibility constraint;
- leaving an authoritatively excluded position active as a working hypothesis;
- forcing raw `open-issue-candidates` into a Writer request despite the Writer-safe commitment-boundary contract;
- keeping an active `conditional-on-hypothesis` dependency after its source position has been authoritatively excluded.

These cases intentionally test governance seams, not whether deterministic code can decide literary meaning. Candidate-list non-exhaustiveness, prose-level narrowing, and legacy ambiguity classification remain semantic-review cases unless a trustworthy mechanical oracle exists.

## 8. Promotion gate

For a release candidate:

- corpus structure must validate;
- every automated seed baseline must pass;
- every registered non-equivalent automated mutant must be killed/contained;
- no survivor may be waived without a documented classification change;
- documented-only cases remain visible in corpus statistics and should be automated when a trustworthy oracle later appears;
- ordinary integration regressions, long-horizon benchmark, Kernel verification, and Runtime fuzz still run separately.

A `1.000` mutation score means only that the **registered automated mutant set** is currently killed. It does not mean the Skill has no unknown failure modes.

## 9. CLI workflow

Use the unified public surface:

```bash
python scripts/storyctl.py mutation validate
python scripts/storyctl.py mutation catalog
python scripts/storyctl.py mutation stats
python scripts/storyctl.py mutation run
python scripts/storyctl.py mutation run --category context
python scripts/storyctl.py mutation reproduce FC-032 /tmp/fc-032
```

Direct backend access remains available:

```bash
python scripts/mutation_test.py run --json
```

`run` is deterministic and returns failure when any automated mutant survives or any baseline/mutant is invalid. Use `--keep-survivors DIR` to preserve surviving project trees for debugging.

## 10. Maintenance rules

- Failure IDs are stable and append-only.
- Keep historical cases after fixing them.
- Do not count the same seed/operator/oracle signature twice.
- A later automated case may supersede a historical documented incident; link with `automated_by` rather than duplicating it in the score.
- Mutators may prepare faulty inputs; they must not contain special logic that makes the detector pass.
- Oracles should be canonical subsystem behavior, not mutation-runner-only reimplementations.
- Record a newly discovered survivor as a new failure case when it represents a distinct mechanism, even if the original mutant that exposed it already has an ID.
- Keep this layer deterministic. Semantics-preserving transformations and oracle-problem exploration belong to the later metamorphic/adversarial benchmark layer.

## 11. Research basis

The maintenance design adapts several mature testing ideas:

- mutation testing: deliberately seed small faults and measure whether the test suite detects them; treat equivalent mutants and trivial/easy operator sets as threats to meaningful adequacy;
- software fault injection: prefer representative injected faults and use them to assess dependability behavior rather than merely count malformed inputs;
- property-based testing: preserve concrete counterexamples, not only generators;
- shrinking/delta debugging: reduce a large failure-inducing input to the smallest structured reproducer that still exposes the defect;
- metamorphic testing: when a direct one-output oracle is difficult, hand valid source/follow-up transformations to `metamorphic-adversarial-benchmark.md`; if that layer discovers a genuine defect, bring the minimized mechanism back into this Failure Corpus.

## Poetics-overcorrection mutation family

Add mutations that preserve hard canon while deliberately import a wrong literary objective:

- inject an unnecessary hook/reveal into quiet accumulation;
- convert ordinary recurring detail into foreshadowing;
- add explicit motive exposition to an intentionally opaque/self-misreading narrator;
- standardize an authorized chapter-level voice shift;
- add a hidden antagonist process to a project that did not activate one;
- force a stable/oscillating character into a growth beat;
- compress licensed waiting/ritual/stasis because "nothing changed";
- turn a perceptual object into a clue or symbol with payoff;
- force a theme into a position matrix;
- mark an inactive optional planning artifact as missing-required.

The expected detector is a Project-Poetics fidelity or wrong-poetics failure, not a fabricated world-state contradiction.

Production prewriting incidents use the existing failure ledger and minimized live-campaign incident record. Linked integration fault injections provide executable regression without pretending that documented entries count toward the registered mutation score. See the production prewriting family in `regression-tests.md`.
