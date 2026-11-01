# Metamorphic and Adversarial Narrative Benchmark

Load this reference only when maintaining or evaluating the Skill, designing cross-representation robustness tests, or investigating a failure where the direct expected output is unavailable or too brittle. It owns **metamorphic relations, follow-up transformations, contrast/locality tests, and adversarial semantic-invariance evaluation**. `failure-corpus-mutation-testing.md` owns injected invalid states and known defect mechanisms; this layer starts from valid source cases and asks how behavior should transform under controlled valid follow-ups.

## Contents

- Purpose and boundary
- Relation types
- Relation quality contract
- Narrative transformation families
- Adversarial protocol
- Automated registry and CLI
- Promotion gate
- Failure handoff to the Failure Corpus
- Research basis

## 1. Purpose and boundary

Long-form narrative tooling has an oracle problem. For many operations there is no single correct byte-for-byte output. A Writer Pack may legitimately include extra low-priority context when budget grows; a prose rewrite should invalidate evidence hashes even when its reviewed meaning is unchanged; a declassification should change visibility while leaving truth and provenance intact.

Use a **metamorphic relation (MR)** to specify the expected relation between a valid source execution and a controlled valid follow-up execution. Do not require exact output equality unless exact equality is itself the semantic property under test.

Second-layer mutation testing asks: **if we inject a known defect, does an owner reject it?**

This third layer asks: **if we transform a valid input in a semantics-preserving or deliberately local way, does the system preserve exactly the invariants it should and change exactly the dimensions it should?**

Do not use this layer to manufacture invalid states merely to obtain a failure. Invalid-fault injection belongs to `failure-corpus-mutation-testing.md`.

## 2. Relation types

Use the smallest relation type that states the contract precisely:

- **INV - invariance**: the transformation changes representation but the compared semantic observation must remain equivalent.
- **MONO - monotonic preservation**: the follow-up may add information/capability, but a protected source subset must remain present and unchanged.
- **DIR - directional expectation**: a controlled input change must move one output property in a known direction, such as eligible -> expired or blocked -> admitted.
- **ISO - isolation**: a perturbation in an unrelated component, branch, dependency component, or visibility scope must not affect the protected target.
- **CON - contrast/locality**: a small meaningful semantic change must change the corresponding local decision/output while unrelated semantics remain fixed.
- **ROUNDTRIP - break-and-refresh relation**: a representation-sensitive guard should fail after a valid representation change and recover after the corresponding evidence/metadata refresh, with semantic meaning preserved.

These types parallel established behavioral-testing ideas such as invariance and directional expectation, while adding branch/dependency isolation and evidence round-trips needed by this Skill.

## 3. Relation quality contract

A registered automated MR must satisfy all of the following:

1. **Necessary, not merely plausible.** A relation may enter the promotion gate only if violation is genuinely evidence of a defect or contract break for the scoped operation.
2. **Non-vacuous transformation.** Source and follow-up inputs must differ. A no-op follow-up is INVALID, not PASS.
3. **Explicit semantic observation.** Compare IDs, replay projections, law statuses, provenance, evidence freshness, or another owner-defined semantic view. Avoid whole-file byte equality for semantic equivalence.
4. **Protected vs expected-to-change fields.** State both. A declassification relation, for example, protects truth/provenance but expects Writer visibility to change.
5. **Canonical oracle ownership.** The benchmark may normalize presentation order, but it must call the existing Context Compiler, Runtime, Kernel, Reconciliation validator, or another canonical subsystem rather than reimplementing its business rules.
6. **Source validity first.** The source case must pass its canonical owner before a follow-up is meaningful.
7. **Follow-up validity where required.** A valid-transform MR must not be credited when the transform accidentally creates malformed input.
8. **Locality over broad similarity.** Prefer exact semantic sets/deltas over vague text similarity scores.
9. **No user-intent rewriting.** A transformation may alter representation or a deliberately selected semantic axis; it must not silently change authorial commitments outside that axis.
10. **Stable reproducibility.** Automated relations are deterministic. Model-generated paraphrases may be used to discover new cases, but promoted relations must preserve a fixed reproducer or a validated transformation contract.

A relation count is not a quality score. Metamorphic-testing research shows that MR choice strongly affects fault-detection power; do not inflate coverage with dozens of near-duplicate permutations.

## 4. Narrative transformation families

### Representation-preserving transformations

Examples:

- JSON key/whitespace reserialization;
- Context Index entry permutation;
- permutation of set-valued request fields;
- dependency-edge order permutation;
- Secret Registry record permutation.

These should usually be `INV` relations.

### Semantics-preserving textual transformations

Examples:

- paraphrase secret-derived text while preserving provenance;
- rewrite prose while preserving the reviewed durable delta;
- substitute display names while preserving stable semantic IDs.

Textual equivalence must be grounded in durable IDs/provenance/reviewed deltas, not only embedding similarity.

### Irrelevant-noise transformations

Examples:

- add disconnected dependency components;
- add sibling-branch context with extreme priority;
- add irrelevant low-priority context under spare budget.

These are `ISO` or `MONO` relations. They attack accidental coupling.

### Boundary transformations

Move an input across exactly one contractual boundary:

- chapter N -> N+1 at an availability window;
- blocked -> explicitly declassified;
- pre-fork -> post-fork;
- current evidence hash -> stale hash -> refreshed hash.

These are usually `DIR`, `CON`, or `ROUNDTRIP` relations.

### Contrast transformations

Make the smallest meaningful semantic change and demand a correspondingly local output change. Contrast tests are useful because a system that always returns the same answer can pass invariance tests while being semantically dead.

Examples:

- change one event effect value and require exactly one replay path to differ;
- change only a display label while stable IDs and relationships remain fixed;
- change one visibility permission and require only the relevant context admission decision to change.

## 5. Adversarial protocol

For each automated relation:

1. construct or copy a valid source fixture;
2. run the canonical source oracle and record a normalized semantic observation;
3. apply exactly one registered transform;
4. prove the source and follow-up inputs differ;
5. run the same canonical owner(s) on the follow-up;
6. evaluate the registered relation over normalized observations;
7. report PASS / FAIL / INVALID;
8. preserve a failing pair when the relation exposes a defect.

Adversarial pressure should target likely shortcut behavior:

- lexical rather than provenance-based secret detection;
- ordering dependence in structures documented as sets;
- high-priority irrelevant context stealing budget;
- sibling branch or disconnected graph contamination;
- display-name identity confusion;
- byte-hash evidence being mistaken for semantic truth;
- systems that pass invariance only because they ignore meaningful input changes.

Pair invariance relations with contrast/directional relations. A system that is invariant to everything is wrong.

## 6. Automated registry and CLI

Canonical relation registry:

`assets/metamorphic/metamorphic-relations.json`

Run through the unified surface:

```bash
python scripts/storyctl.py metamorphic validate
python scripts/storyctl.py metamorphic catalog
python scripts/storyctl.py metamorphic run
python scripts/storyctl.py metamorphic run --relation MR-010
```

Direct backend debugging:

```bash
python scripts/metamorphic_benchmark.py run --json
```

The first automated suite covers Context Compiler set/order invariance, semantic secret taint under paraphrase, monotonic irrelevant-context expansion, availability boundaries, declassification locality, Runtime serialization, dependency permutation/noise, sibling branch isolation, stable-ID label locality, prose-evidence round-trip behavior, Kernel representation invariance, branch-scoped context noise, Secret Registry permutation, and local event contrast.

Documented relations remain in the registry when the transformation or oracle still needs human/LLM semantic review. They are visible assets but do not count as automated promotion evidence.

## 7. Promotion gate

A maintenance release passes this layer only when:

- the registry validates;
- every automated relation has a known operator and canonical owner;
- source/follow-up transformations are non-vacuous;
- no automated relation is INVALID;
- every automated relation PASSes;
- the suite contains multiple relation types rather than permutation-only tests;
- the automated suite covers the configured minimum number of Narrative Semantics Kernel strata;
- no relation is waived merely because it is inconvenient.

Report **relation count, relation-type coverage, semantic-stratum coverage, and failures**. Do not compress the result into a single impressive score and treat that as completeness.

## 8. Failure handoff to the Failure Corpus

If an MR fails because the Skill violates a necessary relation:

1. preserve the source/follow-up pair;
2. minimize the pair while retaining the relation failure;
3. repair the canonical owner;
4. add the newly understood defect mechanism to the Failure Corpus;
5. decide whether it also deserves a mutation operator;
6. keep the MR so future releases must satisfy both the relation and the fixed-bug regression.

This creates a deliberate bridge between moat layers: metamorphic/adversarial discovery feeds durable failure memory rather than disappearing after one benchmark run.

## 9. Research basis

This layer adapts several mature testing ideas:

- **Metamorphic Testing** addresses the oracle problem by checking necessary relations across source and follow-up executions rather than requiring a concrete expected output for every individual input.
- **Behavioral NLP testing (CheckList)** distinguishes minimum functionality, invariance, and directional expectation, demonstrating that capability-oriented perturbation tests can reveal failures missed by held-out accuracy.
- **Contrast Sets** make small, meaningful input changes and inspect whether local decisions change appropriately, which guards against systems that appear robust only because they are insensitive.
- **Property-based / generated follow-up testing** can automate source generation, but generated relations still require domain-validity review.
- Research on MR selection repeatedly shows that the usefulness of a metamorphic suite depends on relation quality and source-test diversity, not relation count alone.

The Skill uses these ideas conservatively: deterministic promoted MRs have explicit owners and semantic observations; open-ended literary equivalence remains documented until a trustworthy oracle exists.

### Research anchors for maintainers

Canonical metadata/status live in `external-research-ledger.md`. Use these sources as conceptual anchors rather than prose templates:

- [research:metamorphic-testing-1998] - source/follow-up executions and metamorphic relations as a response to the oracle problem.
- [research:metamorphic-survey-2016] - taxonomy, application evidence, and the importance of identifying/selecting defensible metamorphic relations.
- [research:good-mr-selection-2006] - plausible relations differ in fault-detection value; relation count alone is not adequacy.
- [research:checklist-2020] - minimum-functionality, invariance, and directional-expectation thinking for language systems.
- [research:contrast-sets-2020] - small meaningful perturbations should produce appropriately local decision changes.
- [research:pbt-metamorphic-2022] - property-based generation can automate source/follow-up cases while the metamorphic relation remains the governing property.

Do not import an MR merely because a paper used it in another domain. Translate only relations that are necessary for this Skill's narrative semantics and deterministic owners.

## Project-Poetics metamorphic relations

Automate only relations with a deterministic subsystem oracle. These relations protect **authority, scope, provenance, capability activation, and Hard-Core separation**; they do not pretend that a machine can prove arbitrary literary passages aesthetically equivalent.

The promoted Project-Poetics relations are:

- **MR-022 inactive capability invariance:** an inactive optional capability cannot become universal readiness debt;
- **MR-023 scope override / inheritance locality:** one valid chapter override reaches that target scope, leaves the canonical parent unchanged, does not alter the later chapter pack after the override ends, and is rejected if directly reused out of scope;
- **MR-024 authorized heterogeneity contrast:** with identical dialogue measurements, an unscoped shift remains `review` while the same shift becomes `authorized-variation` only under valid scoped-poetics provenance;
- **MR-025 poetics-preserving surface variation:** character/place surface substitutions must change the task pack but leave the scoped-poetics provenance/capability projection invariant; this is a representation/governance relation, not a claim that arbitrary prose substitutions are aesthetically equivalent;
- **MR-026 Hard-Core invariance across conflicting poetics:** deliberately conflicting valid Project Poetics must yield identical Narrative Semantics Kernel verdicts for the same hard state, and the same injected hard fault must remain a failure under both.

Keep **theme wording invariance** documented until there is a trustworthy deterministic or calibrated behavioural oracle for "same intended experience"; do not operationalize it by keyword matching or a theme-to-style lookup.
