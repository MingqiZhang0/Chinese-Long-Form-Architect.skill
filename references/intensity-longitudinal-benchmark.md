# Intensity Longitudinal Benchmark and STC v0.1

Use this reference only when maintaining/evaluating Reasoning Intensity or building a deliberately instrumented longitudinal experiment. It owns the **Intensity Benchmark family**, the first **Spatiotemporal Continuity (STC)** track, its latent world/generator/probe contracts, calibration design, and Benchmark Assurance. `evaluation-benchmark.md` still owns general Skill-evaluation principles; `live-campaign-longitudinal-evaluation.md` owns real creative-campaign evidence.

## Contents

- Claims and boundaries
- Experimental tracks
- STC latent world v0.1
- Solution-first generation
- Probe obligations
- Surface conservation
- Observations and metrics
- Intensity experiment matrix
- Calibration and statistics
- Benchmark Assurance
- v0.1 scope boundary

## 1. Claims and boundaries

Keep claims narrower than the evidence.

STC-Core may support claims about mechanical legality inside the modeled spatiotemporal slice: presence, custody/containment, reachability, access, route validity, duration, and temporal constraints. Longitudinal STC may additionally support claims about preserving/updating those facts across narrative distance and later action.

A paired controlled experiment may support claims that different Reasoning Intensity policies caused different STC/repair/cost behavior **within the recorded Skill/model/runtime configuration**.

Synthetic STC does not prove literary quality, general intelligence, or real-fiction usefulness. Those require separate live longitudinal and human/literary evidence.

## 2. Experimental tracks

### Fixed-Trajectory Continuity

Hold latent world history, chapter missions, mandatory deltas, probe schedule, requested output envelope, Skill/model/runtime, and legal information access fixed across intensity arms. Prose may vary, but benchmark-critical event skeleton remains fixed. Use this track for strongest paired intensity comparisons.

### Bounded-Choice Continuity

Offer a finite set of generator-certified legal choices. Each exposed benchmark choice must preserve a non-anticipatory continuation and the required probe-obligation coverage. Different intensities may enter different trajectories; use paired latent seeds but do not overstate causal equivalence after branch divergence.

### Adversarial Intervention

Inject plausible but invalid user/environment requests: impossible travel, stale custody, closed route, missing access, or deadline violation. Measure whether the system refuses/replans instead of silently breaking canon.

Keep free/live creative campaigns separate from all three.

## 3. STC latent world v0.1

Model a **partial closed-world World Slice**, not a complete fictional ontology.

A challenge declares which predicate families are authoritative/complete. Absence outside those families means `UNSPECIFIED`, not false. The Oracle should classify observations as `VALID`, `VIOLATION`, `OUTSIDE_MODELED_SLICE`, or `UNDERSPECIFIED` where appropriate.

v0.1 models only what is needed for deterministic continuity stress:

- actors, objects, locations, containers;
- `AT`, `INSIDE`, `HOLDS`-style location/custody state;
- routes and access requirements;
- route validity intervals and minimum travel times;
- deterministic external events that alter modeled state;
- chapter index separately from diegetic/story time;
- temporal constraints using exact times or interval/difference constraints;
- missions defined by required/forbidden exit predicates plus temporal bounds.

Do not require the tested project to copy the full hidden Oracle. The Skill should persist only the lowest sufficient state needed for future correctness.

### Time

Keep chapter/scene distance distinct from diegetic time. In the executable v0.1.1 conformance harness, chapter numbers are longitudinal/narrative-distance metadata only; route validity, event replay, mission start/deadline, and action legality are evaluated on `story_time`. The challenge also carries explicit difference constraints and an STN-consistency check. A chapter-number translation with unchanged story time is a metamorphic invariant; a story-time boundary change is not.

Prefer relative temporal constraints when exact timestamps are unnecessary. A future implementation may use a dedicated STN solver for larger cases, but v0.1 remains a small deterministic kernel.

### Actions and containment

Keep the action kernel small: move/travel, transfer, wait, and deterministic state update. Validate preconditions, duration, route/access state, and effects. A transition may be omitted from prose while remaining required in latent state.

Containment is executable state, not decoration. `INSIDE(K1,C1)` plus direct custody `HOLDS(P1,C1)` implies effective custody/location of `K1` through `C1`; transferring the container propagates effective custody of its nested contents. Reject containment cycles, simultaneous direct-hold-plus-contained states, and direct transfer of an entity that is still nested inside another container.

## 4. Solution-first generation

Do not randomly generate a world and hope it is solvable.

Use this order:

1. construct a latent scaffold;
2. plant at least one legal witness trajectory or continuation policy;
3. verify baseline solvability with the independent Validator implementation, not Generator helpers;
4. inject state updates;
5. inject near-miss decoys/interference;
6. schedule delayed probe opportunities;
7. reverify solvability/continuation;
8. compute structural difficulty descriptors;
9. render a surface view;
10. validate surface conservation and oracle isolation;
11. freeze/hash the challenge certificate before assigning an intensity arm.

The witness proves existence; it is not the required answer. Unless a challenge explicitly tests optimization, accept any candidate trace satisfying the constraints. v0.1.1 exposes arbitrary candidate validation as a first-class path; the Validator must not compare a candidate for equality with the planted witness.

### Continuation safety

For deterministic bounded-choice v0.1, every exposed controlled choice must lead to a state from which the remaining required benchmark obligations have a legal continuation **without using future hidden information**.

Do not require all branches to preserve the same concrete future Probe Instance. Preserve the required **Probe Type/Obligation**; a different branch may instantiate an equivalent custody/access/route challenge later.

Do not expand an exponential full-story tree when a checkpointed continuation proof to a previously certified safe harbor is sufficient. In executable Bounded-Choice cases, each exposed alternative carries a Continuation Certificate binding the alternative trajectory hash, independently validated legality, elapsed time, and required terminal custody. The certificate is Harness-private and is checked by the independent Validator.

Future uncertain-environment tracks may strengthen this to robust/dynamic controllability. Do not build that into v0.1.

## 5. Probe obligations

Do not create hundreds of named probe types. Compose a Probe Obligation from three orthogonal dimensions plus coverage metadata:

`Semantic Primitive Set x Reasoning Operation x Stress Envelope x Coverage Class`.

### Semantic primitives

Keep the v0.1 primitive registry small:

- presence/location;
- custody/containment;
- reachability/travel;
- temporal constraint;
- access/capability.

### Reasoning operations

Prefer action-oriented probes:

- retrieve current effective state;
- compose several relevant constraints;
- choose a legal action;
- reject/replan an invalid action;
- predict the modeled transition.

### Stress operators

Treat these as difficulty/stress metadata, not new semantic primitives:

- narrative/source-target gap;
- dormancy gap since last relevant activation;
- superseding update count;
- interference from similar entities/facts;
- temporal slack/boundary margin;
- constraint coupling;
- concurrency;
- state-transition gap.

### Lifecycle

A Harness-private obligation may move through:

`UNBOUND -> CANDIDATE -> BOUND -> ARMED -> EXERCISED -> SATISFIED|FAILED`.

The executable v0.1.1 challenge binds concrete obligations before exposure and the independent Validator emits terminal `SATISFIED`, `FAILED`, or non-gating `NOT_EXERCISED` outcomes from the actual candidate trace. Required obligations must terminate `SATISFIED`; a dangling route/entity/mission binding invalidates the challenge rather than silently disappearing from coverage.

A concrete Probe Instance may also be `INVALIDATED` by a legal branch or `CENSORED/NOT_OBSERVED` in ecological/live evidence. Do not count either as pass.

Bind probes to causal opportunities already present in the latent scenario. Synthetic controlled tracks may use interventions, but do not invent a nonsensical plot event during the run merely to repair coverage.

Use suite-level coverage rather than forcing every scenario to contain every primitive/stressor. Prefer diagnostic low-order probes for calibration and separate ecological high-order probes for realistic coupling. Coverage may guide candidate selection; it must not dictate unnatural story construction.

## 6. Surface conservation

A strict surface is a **view of one latent world**, not a separately generated world copy.

Render urban/ancient/science-fiction/neutral variants from the same latent IDs, transitions, constraints, missions, and probe obligations. Surface text may alter names/register/decorative detail but must not alter benchmark-observable transition semantics or leak the witness.

For strict paired surfaces, mechanically verify:

- initial latent state unchanged;
- action mapping total, injective, and unambiguous;
- latent candidate -> surfaced candidate -> latent candidate round-trip is exact;
- the same surfaced trajectory receives the same semantic verdict/signature as its latent form;
- transition/access/duration semantics unchanged;
- observation boundary unchanged;
- mission and probe obligations unchanged;
- latent valid-solution set unchanged.

Surface conservation does not require equal cognitive difficulty. A semantically faithful ancient surface may still expose representation sensitivity; report that separately instead of “fixing” the item until scores match.

Keep v0.1 strict surfaces template/lexicon controlled. Rich naturalistic rewriting belongs to a later ecological track and must not claim strict conservation.

## 7. Observations and metrics

Do not report one STC score.

Track at least three longitudinal outcomes:

- **Native Survival** — no hard violation in the first candidate action/plan;
- **Protected Survival** — no hard violation reaches committed canon after validators/repair;
- **Repair-Free Survival** — no continuity-driven block/repair has yet been required.

Record stages separately:

1. proposed violation;
2. blocked violation;
3. repair success/failure;
4. committed violation.

Distinguish root failure from downstream cascade and record cascade/blast radius.

Track source-to-action distances by chapter/scene/state-transition gap, not only current chapter number. Record old-state update/interference probes separately from simple recall. Prefer action probes over trivia.

Useful supporting curves include repair burden, long-gap action accuracy, obsolete-state rejection, context consumption, persisted-state footprint, reusable-result rate, invalidation precision, total compute, and scheduler overhead.

A persisted-state metric is diagnostic only: Max must not win by copying the entire hidden Oracle into Project State.

## 8. Intensity experiment matrix

For a controlled scenario seed, pair the same latent challenge across all requested levels.

### Natural Intensity

Run each tier with its real calibration. This is the user-facing product condition.

### Equal-Context ablation

Hold the eligible context envelope approximately equal to isolate scheduler/exploration/verification effects from simply reading more.

### Equal-Compute ablation

Hold the overall adapter-specific resource envelope approximately equal to study allocation quality. Preserve raw resource vectors such as input/output tokens, model passes, tool/subagent calls, and wall time; do not pretend they have a universal conversion rate.

### Strategy arms

Compare longitudinal strategies separately, for example:

- Low throughout;
- Max throughout;
- Max bootstrap -> Low incremental;
- Max bootstrap -> Low + event-triggered High refresh.

Do not make one strategy part of a tier definition.

## 9. Calibration and statistics

Calibrate tiers as distinct Pareto operating regions, not fixed budgets. Different benchmark tracks are sensitive to different behavioral anchors; STC need not strictly order XHigh and Max if interaction/alternative search is not material to the challenge.

Use paired latent seeds and randomized/counterbalanced run order. Repeat stochastic model runs. Treat scenario/run as clustered longitudinal units; do not count 100 chapters from one trajectory as 100 independent samples.

Prefer survival/time-to-first-failure plus scenario-level paired effect sizes/uncertainty. Report cost and repair together with integrity. Do not hide failures/crashes from denominators or keep only the best seed.

Keep development, calibration, holdout, and live evidence distinct. When possible use generator-family holdouts and leave-one-track-out calibration to detect benchmark-specific scheduler heuristics.

## 10. Benchmark Assurance

A Benchmark must earn trust independently of the model results.

### Claim discipline and blindness

Freeze/hash the latent challenge before assigning intensity. Scenario generation, strict surface rendering, Probe binding, Core Oracle, and Core scoring must not receive the intensity label. In a bounded-choice run, the same latent state/history/seed must imply the same Harness decision regardless of tier.

Intensity Trace is post-hoc diagnostic evidence; Core verdict must not depend on how much reasoning the model claims to have performed.

### Generator/property validation

Test at minimum:

- every `must-achieve` controlled challenge has a witness;
- an implementation-independent Validator process accepts the witness and non-witness candidates;
- temporal constraints are jointly satisfiable and exact story-time assignments satisfy them;
- controlled choices preserve non-anticipatory continuation and required probe coverage;
- Continuation Certificates match independently observed trajectory hashes/terminal facts;
- containment propagation and nested effective custody are exercised, not merely schema-declared;
- hidden oracle/probe/witness metadata never enters the Agent-visible projection;
- strict surface transformations preserve latent semantics;
- rejected/invalid generation seeds remain visible in generator-validity statistics.

### Harness mutation testing

Inject realistic defects into the Benchmark itself: unsatisfiable mission, false continuation, clairvoyant witness, broken temporal boundary, stale custody, closed-route acceptance, access omission, containment-propagation error, oracle leak, analysis denominator bug, and other known failure mechanisms.

Require an unmutated valid baseline before counting a kill. Report the operator set with mutation results; a perfect registered-set score is not proof of unknown-bug absence.

### Differential checking

For small cases, compare independent algorithmic paths where feasible: optimized route solver vs bounded enumeration, effective projection vs event replay, STN/constraint solver vs naive small-domain enumeration. Shared helpers reduce evidentiary independence; record the scope of differential assurance.

### Metamorphic assurance

Validate the relation itself before using it to judge the Agent. Useful STC relations include ID rename invariance, strict surface invariance, disconnected-subplot isolation, uniform time translation, deadline-boundary directional flips, and capability-preserving route addition.

### Construct validity

Seek convergent evidence by injecting known STC faults and discriminant evidence by changing unrelated prose style/theme while keeping latent traces fixed. Use deliberately broken/state-only/full-runtime baselines to confirm measurement sensitivity. Keep STC-Latent, surface robustness, and prose reconciliation as distinct constructs.

### Intensity placebo tests

Run at least these maintenance controls before trusting tier curves:

- duplicate two identical execution policies under different hidden labels; results should not systematically follow the label;
- map all five labels to the same no-op policy; the Harness must not manufacture an ordered Low->Max curve.

### Prose reconciliation

Keep STC-Core deterministic. If prose must be reconciled back to state, use explicit checklist questions and blinded evaluation where mechanical extraction is insufficient. Do not treat agreement among several LLM judges as ground truth; maintain human anchor cases for subjective/ambiguous prose reconciliation.

### Trust report

Publish an assurance profile rather than a single trust score: generator invariants, differential checking scope, Harness mutation operators/survivors, metamorphic relation coverage, oracle-leak audit, intensity placebo/no-op results, surface conservation, judge calibration when applicable, holdout separation, and live-evidence maturity.

## 11. v0.1 scope boundary

### Build now

The v0.1.1 semantic-conformance implementation now includes:

- deterministic finite latent world slice;
- chapter/story-time separation with all legality evaluated on diegetic `story_time`;
- explicit temporal difference constraints plus consistency checking;
- routes, nested custody/containment, access, deterministic updates, and absolute mission deadlines;
- Generator and independent Validator process separation;
- planted witness **plus arbitrary candidate trajectory validation**;
- executable Bounded-Choice alternatives and Continuation Certificates;
- bound Probe Obligations with terminal lifecycle outcomes;
- strict surface mapping, candidate round-trip, and behavioral conservation;
- challenge certificate/hash;
- semantic mutation, differential, and metamorphic assurance;
- paired intensity protocol and Benchmark Assurance specification.

### Later

- uncertain/stochastic exogenous events and full dynamic controllability;
- reference-frame/visibility geometry beyond topological movement;
- rich naturalistic surface generation;
- automatic long-form prose runner/judge;
- adaptive/IRT item selection;
- learned calibration from accumulated trace data.

### Do not build for STC v0.1

- a complete physical-world simulator;
- a general PDDL planning platform as the canonical representation;
- real-map APIs or external-world travel knowledge;
- one aggregate STC/Trust score;
- a requirement that every scenario contains every probe family;
- a Benchmark path that can see the current Intensity label before the challenge is frozen.

Use `scripts/stc_benchmark.py` for generation and assurance orchestration and `scripts/stc_validator.py` as the independent semantic Validator. Public `storyctl stc` commands continue to route through the generator/harness front end, which delegates semantic acceptance across a process boundary.

Useful maintenance paths include `stc generate`, `stc validate`, `stc candidate`, `stc roundtrip`, `stc mutation-smoke`, `stc assurance`, and `stc selftest`. This deterministic kernel is evidence about the modeled STC slice only; it is not evidence that the full longitudinal LLM Benchmark or real-fiction campaign has already been run.
