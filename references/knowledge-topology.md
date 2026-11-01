# Knowledge Topology, Secrets, and Fair Reveals

Use this reference for mysteries, investigations, strategic deception, hidden identity, political intrigue, betrayal, and any reveal where fairness matters. It owns project reasoning about truth, actor knowledge/belief, evidence, deception, and reveal fairness. `narrative-semantics-kernel.md` owns the cross-layer rule that world truth, actor epistemic state, reader exposure, and visibility policy are distinct semantic strata.

## Contents

- Three-layer epistemic model
- Evidence graph
- Fair-play reveal test
- Misdirection
- Secret durability
- Reader inference budget
- Knowledge changes as plot events
- Strategic deception
- Reveal aftermath
- Reinterpretive depth and hidden-process handoff
- Authorial unknowns

## 1. Three-layer epistemic model

Never collapse these layers:

### Objective truth
What is actually true in the world regardless of who knows it.

### Actor knowledge

Actor knowledge includes self-models that may be wrong. A person's stated motive or first-person interpretation is actor-level evidence unless the project separately establishes it as authoritative.
For each relevant character or faction distinguish:

- knows;
- suspects;
- falsely believes;
- has evidence for;
- has heard but cannot verify;
- cannot access;
- has forgotten or misremembered;
- believes another actor knows.

### Reader knowledge

For long serials, distinguish **shown** from **currently retrievable**. A distant fact can remain objectively known while becoming cognitively cold. Use `reader-model.md` when delayed payoff, cast density, time jumps, or braided POV make reactivation important.

Track what the text has actually made available:

- explicit fact;
- strong implication;
- weak clue;
- misleading but honest framing;
- withheld because viewpoint lacks access;
- withheld only by authorial concealment.

The last category is dangerous. Do not let a viewpoint character consciously know decisive information and then unnaturally avoid thinking about it solely to fool the reader.

## 2. Evidence graph

For consequential mysteries, model evidence as a graph rather than a single clue.

Each clue may have:

- source;
- reliability;
- accessibility;
- cost of verification;
- time sensitivity;
- alternative explanations;
- who can combine it with other clues;
- what conclusion it supports alone;
- what conclusion it supports only in combination.

Prefer major reveals supported by multiple independent paths. When evidence travels through testimony, rumor, media, or copied records, verify source independence rather than counting repetitions; use `social-transmission-reputation.md` for transmission chains.

## 3. Fair-play reveal test (activate for epistemic-puzzle projects)

A reveal is fair when:

- the underlying cause existed before the reveal;
- earlier scenes are compatible with it;
- at least one prior foothold exists;
- characters who should have noticed had a reason not to conclude correctly yet;
- the reader can retrospectively reconstruct the reveal from available or naturally inaccessible information;
- the reveal does not depend on a rule invented at reveal time.

Fair does not mean easy to predict.

## 4. Misdirection (conditional capability)

Use misdirection through interpretation, not false authorial fact.

Good sources of misdirection:

- true evidence placed in a misleading context;
- two causes producing similar symptoms;
- a character's plausible but incomplete theory;
- social prejudice or institutional assumption;
- a real secret hiding a deeper secret;
- a clue visible to the wrong person;
- correct conclusion reached for the wrong reason;
- evidence whose meaning changes after a new rule or relationship is understood.

Avoid lying through omniscient narration unless the narrative form explicitly permits an unreliable narrator.

## 5. Secret durability

For every important secret ask:

- who knows;
- who suspects;
- what records exist;
- who benefits from disclosure;
- who benefits from silence;
- what communication channels exist;
- how leaks are detected;
- how claims are authenticated;
- what false public explanation competes with the truth;
- how long the secret can realistically survive.

Do not preserve secrets by authorial decree. Also ask how partial leaks, distorted retellings, and false public versions might exist without exposing the full truth.

## 6. Reader inference budget

Control difficulty by distributing clues across:

- visibility;
- ambiguity;
- time separation;
- domain knowledge required;
- number of clues that must be combined;
- misleading interpretations that remain rational.

Do not make every clue equally obscure. Give attentive readers occasional solvable footholds.

## 7. Knowledge changes as plot events

Treat acquisition, loss, corruption, verification, and sharing of information as real state changes.

A character learning a fact should affect:

- future choices;
- whom they trust;
- what risks they tolerate;
- what they ask;
- what they conceal;
- what they can infer from later evidence.

Do not let characters repeatedly rediscover the same knowledge for exposition.

## 8. Strategic deception

For a deception plan, record privately:

- target belief;
- current target belief;
- evidence the target already has;
- evidence the deceiver can manipulate;
- verification channels the target may use;
- cost if the lie is tested;
- fallback if partial exposure occurs;
- who else may observe the manipulation.

A clever deception survives the target's reasonable checking behavior.

## 9. Reveal aftermath

A revelation is not complete when the reader learns the truth.

Trace:

- who accepts it;
- who denies it;
- what proof is required;
- what institutions can act on it;
- what relationships change;
- what prior events are reinterpreted;
- what new danger follows from knowledge spreading.


## 10. Reinterpretive depth and hidden-process handoff

For major long-form reveals, separate three questions:

1. What did the reader think the earlier event meant?
2. What does it mean after the reveal?
3. What active process still continues after the reveal?

Prefer reveals that add a causal layer without making prior objective facts false.

After revealing a hidden actor or mechanism, hand the thread back to the live world model:

- what does the newly exposed actor do now;
- who learns that the secret is exposed;
- who still believes the old explanation;
- what plan is abandoned or accelerated;
- what evidence becomes dangerous;
- what prior scenes gain new meaning;
- what objective survives the reveal.

A reveal should change the game, not merely close a box.
## 11. Authorial openness

Sometimes objective truth is intentionally not selected yet. Do not fake a settled truth in backstage reasoning.

Keep separate:

- unknown to an actor;
- unknown to the reader;
- authorially open / undecided;
- backend truth fixed but withheld by policy;
- external fact not yet researched;
- interpretive plurality that does not belong in world truth.

For consequential authorial openness, `open-issue-semantics.md` owns the compatibility envelope, positions/working hypotheses, resolution authority, and mainline robustness rules. Until resolution, treat an open Claim as not yet truth-valued for factive epistemic labels.

Therefore an actor may `believe`, `suspect`, or `have_heard` an open Claim, but do not encode `knows(phi)` or `falsely_believes(phi)` until project semantics establish `phi` as objectively true or false. Evidence emitted while truth remains authorially open must stay compatible with the authorized envelope unless the project explicitly branches.


## 12. Temporal acquisition coverage and expression precision

Fact truth, temporal validity, research applicability, actor acquisition, direct experience, Writer visibility and expression precision are independent dimensions. Author research is not character knowledge. Later knowledge never creates earlier firsthand experience. Remove illegal knowledge while preserving legal concrete evidence.

For consequential, secret-sensitive, temporal-risk, research-derived, plot-critical or identity-critical actor facts exposed to Writer, K21 requires a completed authorized channel before use, including facts whose acquisition was never recorded. Use the existing Story State Bundle: `facts` carries project fact values, `knowledge_state` carries acquisitions, and `knowledge_uses` or `writer_visible_facts` carries uses. A `facts` record declaring `writer_visible: true`, `actor` and `used_at` is itself a coverage obligation; deleting use rows is no exemption. These are typed views of the existing Knowledge owner, not another Knowledge Database. Runtime projects keep their existing authorized event/projection discipline.

Acquisition records use `actor`, `fact_id` (legacy `fact` stays readable), `acquired_at` (legacy `acquired`), `acquisition_channel`, `provenance`; optional `completed: false` and `authorized: false` cannot support knowledge. A use has `actor`, `fact_id`, `used_at` (legacy `used`), and `mode`. Acquisition must be completed at or before use. Channel/provenance are canonical evidence declarations to be reviewed, not automatically proven testimony. One actor's acquisition does not authorize another actor.

`PREDICTION`, `SUSPICION`/`SUSPECTS`, `INFERENCE`, `HYPOTHESIS`, `RUMOR`, `FALSE_BELIEF`, `BELIEF`/`BELIEVES`, `MISREMEMBERING`, `PLAN`, `FEELS`, and `HAVE_HEARD` remain nonfactive modes, never shortcuts to confirmed knowledge. Retain their qualifier in structured expression basis. Author-only facts need no actor acquisition and remain outside Writer context; other POV facts remain isolated by the existing role/POV boundary.

Objective observation may use `DIRECT_OBSERVATION` with provenance in `knowledge_state`; ordinary incidental cups need no record. Established ordinary competence/public background may use a provenance-backed canonical `acquisition_policy: PUBLIC | BACKGROUND`; this cannot exempt secret/identity/temporal-risk or research-derived facts. A consumer cannot turn actor knowledge into objective truth by setting `actor_relative: false`; that exemption also requires the authoritative fact to declare it.

For `experience: FIRSTHAND | FIRSTHAND_MEMORY | DIRECT_EXPERIENCE`, require a direct channel at `event_at`, presence in the existing `timeline` at the event's `location`, and no conflicting `direct_experience_eligible: false` or `experience_eligible_for` restriction. `LATER_LEARNED` requires legal acquisition but no original presence. Presence and acquisition do not substitute for each other.

K22 compares `expression` against source `precision`, calendar `specificity`, and independent `basis`. `precision` supports `EXACT`, `BOUNDED`, `APPROXIMATE`, `UNKNOWN`, `INFERRED`; `basis` supports `CONFIRMED`, `INFERRED`, `REPORTED`, `UNVERIFIED`. INFERRED is not ranked between UNKNOWN and EXACT. An exact-looking inference remains inferred. Confidence never supplies precision.

Calendar specificity is `YEAR | MONTH | PART_MONTH | DAY | UNKNOWN`. ISO value granularity cannot be hidden by a coarser declared specificity. Month to middle-month/day is refinement. Exact to exact retains legal precision; exact to a coarser expression can be lawful compression. Do not systematically erase useful exact evidence for style. Legacy absent precision is UNKNOWN, never inferred EXACT.

A `refinement_evidence` list names primitive fact IDs with `supports_fact_id`, provenance and sufficient precision/value. Support must match the same fact/value, be available and acquired by this actor before use, and preserve Writer visibility. A self-reference, unrelated exact date, confidence increase, future evidence, or contradictory month does not establish refinement. Natural-language qualifier/meaning interpretation still needs semantic review.

A prediction label cannot declassify an author-only/backend future fact. Predict from a separate Writer-safe evidence or hypothesis record rather than exposing protected source truth. Inferred acquisition or AUTHOR_RESEARCH/RUMOR channels cannot support confirmed actor knowledge.
