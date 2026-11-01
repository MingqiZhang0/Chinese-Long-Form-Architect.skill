# Narrative Semantics Kernel

Use this reference whenever two or more of these systems interact: Runtime events/projections, Knowledge Topology, Reader Model, secret taint/context compilation, branches/counterfactuals, semantic revision, prose-state reconciliation, provenance/dependency tracing, or schema/project migration.

This file owns the **cross-layer semantic contract**. It does not replace the specialized modules and does not create another source of truth. Its job is to define what each layer means, how the layers may depend on one another, and which properties must survive replay, branch operations, revisions, and migrations.

## Contents

- Kernel purpose and non-goals
- Semantic strata
- Three independent time axes
- Change operators
- Canonicality and derivation order
- Core semantic laws
- Replay-derivability matrix
- Epistemic semantics
- Reader semantics
- Secret information-flow semantics
- Branch and counterfactual semantics
- Evidence and provenance semantics
- Revision semantics
- Migration-preservation laws
- Query discipline
- Mechanical verification
- Failure modes

## 1. Kernel purpose

The project already has strong local modules. The Kernel prevents locally correct modules from composing into a globally inconsistent story system.

Typical cross-layer errors include:

- a Writer-visible summary inherits a hidden truth semantically but loses its secret label;
- a Reader Model hypothesis is later treated as objective canon;
- an actor's false belief is serialized as a world fact;
- a branch copies current state instead of inheriting a fixed history prefix;
- a revision report silently changes canon without a committed event;
- prose evidence becomes stale after editing while the reconciliation report still looks approved;
- a schema migration changes representation and accidentally resolves an authorial unknown;
- a flashback's story time is confused with event commit order;
- a late reveal is confused with the historical time at which the revealed event occurred.

The Kernel exists to make these category errors explicit.

## 2. Non-goals

Do not turn the Kernel into a theorem prover for literary meaning.

It does not:

- decide motives, themes, symbolism, or emotional truth;
- require every narrative fact to be formalized;
- force all Reader Model judgments to become machine-decidable;
- require a new universal story database;
- duplicate Runtime, Context Compiler, Reconciliation, or Revision logic;
- replace human/Agent judgment when semantic interpretation is genuinely open.

Use `formalization-boundary.md` before expanding the ontology.

## 3. Semantic strata

Treat the project as several typed semantic strata. Never collapse them merely because all happen to be stored as JSON/Markdown.

### S0 - Author intent and open design

Contains:

- user-locked constraints;
- planning choices;
- provisional hypotheses and planning stance;
- governed OpenIssues / authorial unknowns;
- authoritative compatibility constraints;
- deliberately unresolved questions and resolution policies.

This layer may constrain future canon but is not automatically fictional truth. Use `open-issue-semantics.md` when consequential openness must persist across planning, drafting, migration, or revision.

### S1 - Committed semantic history

In Runtime Mode this is the branch-specific effective sequence of **durably accepted semantic events** for the strata the project chooses to event-source.

Commitment means "this transition belongs to the auditable project history." It does **not** mean every committed event is objective fictional canon. A Runtime may durably record, for example:

- a world event (`W`) such as an object transfer;
- an epistemic event (`E`) such as a character learning a fact;
- a reader-exposure event (`X`);
- a policy/declassification event (`P`);
- an authorial/design decision when that project deliberately event-sources S0;
- an interpretive/governance event (`I`) such as an approved analysis status.

The target stratum keeps its own authority. Committing an Observatory or humanities-analysis transition makes that analysis durable; it does not turn the analysis into story-world truth.

The event history is write-side history, not a convenient current-state cache.

### S2 - Deterministic projections

These are replayable views of the event-sourced portions of S1. They may contain several typed subviews, for example:

- current object custody, location/access, body/resource, institution, or hidden-process state;
- committed actor knowledge/belief state when epistemic transitions are event-sourced;
- reader-exposure or Reader Model state when those transitions are deliberately event-sourced;
- policy/declassification state when policy transitions are event-sourced;
- durable analysis/governance status when a project explicitly event-sources that status.

**Replayability does not raise semantic authority.** A replayed Reader Model is still a defeasible reader estimate; a replayed humanities finding is still analysis; a replayed authorial unknown remains S0 design state.

A projection is replaceable. If it disagrees with valid committed history for the stratum it projects, rebuild it.

### S3 - Epistemic states

These describe information relative to an actor/faction:

- knows;
- believes;
- suspects;
- was told;
- has evidence for;
- misremembers;
- cannot access;
- believes that another actor knows/believes something.

Epistemic status is not objective truth. `knowledge-topology.md` owns the local modeling details.

### S4 - Reader exposure and reader model

Separate two things:

1. **reader exposure** - what reader-visible prose has actually made available;
2. **reader model** - a defeasible estimate of what an attentive reader currently remembers, suspects, expects, or emotionally foregrounds.

Exposure can often be evidenced from prose. The Reader Model remains heuristic/profile-dependent and may be revised without changing canon.

### S5 - Information-flow policy

Contains:

- secret IDs;
- taint provenance;
- role clearance;
- declassification decisions;
- context-pack visibility.

This layer governs who may receive information. It does not decide whether that information is true in the story world.

### S6 - Evidence, provenance, and dependency

Contains support/derivation relations such as:

- prose span supports candidate durable delta;
- event produces projection fact;
- artifact derives from another artifact;
- research claim supports world-model claim;
- target depends on source;
- revision derives from earlier revision.

This layer answers **why** a claim/artifact exists and what becomes stale if its support changes.

### S7 - Analysis and governance artifacts

Includes:

- revision-impact reports;
- reconciliation reports;
- observatory reports;
- merge plans;
- context manifests;
- audit findings.

These artifacts can authorize, block, or explain a future commit. They are not fictional canon merely because they are structured and validated.

### 3.1 Four independent status dimensions

Do not use one status word to stand in for four different questions. For any consequential proposition/artifact, distinguish as needed:

1. **durability / commitment** - is this transient, proposed, or durably accepted into project history?
2. **fictional truth / canonicality** - is this Open, Provisional, Implied, Fixed, false-in-world, or outside the category of world truth?
3. **epistemic stance** - who knows, believes, suspects, was told, doubts, or misremembers it?
4. **visibility / exposure** - which role or reader profile may receive it, and at what discourse position?

These dimensions are orthogonal. Examples:

- a Reader Model hypothesis may be durably committed, non-canon, uncertain, and visible to Director only;
- a Fixed backend truth may be canon, unknown to all characters, hidden from Writer, and unrevealed to the reader;
- a character's false belief may be canon as **a fact about that character's belief state** while its propositional content is false in the world;
- a declassified secret may become Writer-visible while its world truth and provenance stay unchanged.

Treat `committed`, `canon`, `known`, and `visible` as different predicates. Never infer one from another.

## 4. Three independent time axes

Never use one timeline to stand in for all temporal meanings.

### 4.1 Story time / valid time

When the represented occurrence or condition holds inside the fictional world.

Use existing `story_time`, scene time, timeline, validity intervals, or equivalent project structures.

A flashback can move backward on this axis without moving backward on commit order.

### 4.2 Semantic commit time / transaction order

When the project durably accepted a semantic event into the committed history. This axis applies to canon-bearing and non-canon event-sourced strata alike.

In Runtime Mode this is primarily branch lineage plus event sequence/order.

A later correction may have a later commit order while describing an earlier story-time fact. A durably committed Reader Model or analysis transition also has a commit position without becoming fictional canon.

### 4.3 Discourse / exposure time

When reader-visible prose makes information available: chapter, scene, paragraph/revision, publication order, or equivalent narrative position.

A fact may:

- occur at story time 3;
- be committed to project history while drafting chapter 20;
- be revealed to the reader in chapter 35.

Those are three different claims.

### Temporal law

Never infer one axis from another unless the project explicitly guarantees the mapping.

In particular:

- event `seq` need not be monotonic in `story_time`;
- chapter order need not equal story chronology;
- late reader exposure does not imply late in-world occurrence;
- a retcon/correction has a new commit position even when it changes a claim about old story time.

## 5. Change operators

Before processing a consequential change, classify what kind of semantic operation it is. One user-visible edit may involve several operators.

### W - World update

The fictional world changes because something happens in-world.

Examples:

- a bridge collapses;
- an object changes hands;
- a character is injured;
- an institution files an order.

This normally belongs in committed events when Runtime Mode is active.

### E - Epistemic update

An actor/faction's information state changes.

Examples:

- learns a fact;
- receives a false report;
- verifies a rumor;
- forgets/misremembers;
- changes belief after evidence.

Do not confuse E with W. Learning that the bridge collapsed does not collapse the bridge.

### X - Reader-exposure update

Reader-visible discourse changes what evidence is available to the reader.

Examples:

- a clue appears on page;
- a reveal becomes explicit;
- a flashback exposes an older event;
- revision removes an earlier clue.

X can change while objective world history remains unchanged.

### P - Policy / visibility update

Who is allowed to receive a protected truth changes.

Examples:

- a secret is declassified to Writer after the reveal;
- a role receives narrower clearance;
- a backend artifact is approved for a Reader Simulator.

P changes authorization, not objective story truth.

### R - Representational revision

The project corrects or revises its representation of already-modelled canon.

Examples:

- prior prose established the wrong room number and is corrected;
- a committed custody fact was recorded incorrectly;
- an earlier chapter is deliberately retconned.

Treat this separately from W. A database correction is not an in-world event unless the fiction itself depicts one.

### I - Interpretive update

An analysis/hypothesis changes without committing a new world fact.

Examples:

- Reader Model likely hypothesis changes;
- humanities interpretation changes;
- a viable authorial position becomes the current working hypothesis or is parked;
- an author planning theory is rejected **as a planning approach** without being authoritatively excluded;
- a previously suspected motive becomes less plausible.

I must not silently become W or A. Changing planning stance does not change authorial viability.

### A - Authorial decision update

The author/user deliberately changes S0 design commitments without depicting an in-world occurrence.

Examples:

- resolves, retires, or reopens an OpenIssue;
- locks, relaxes, or supersedes an authoritative compatibility constraint;
- authoritatively excludes one of several still-open causal positions;
- changes a `preserve_open` policy;
- adopts a researched fact as a worldbuilding constraint before it appears in prose.

A may authorize later W/E/X work, but A is not itself an in-world event. If a project event-sources authorial decisions for auditability, replayability does not convert them into fictional events.

### B - Branch intervention

A counterfactual/sandbox branch changes one or more assumptions after a declared fork.

B creates an alternative history, not a second simultaneous truth on the parent branch.

## 6. Canonicality and derivation order

Use this order when asking which artifact outranks another.

### In Runtime Mode

1. user-locked project constraints govern S0 authorial intent but do not by themselves establish fictional events;
2. committed branch event history is the durable write-side source for every semantic stratum the project deliberately event-sources;
3. **event-log membership proves durability, not fictional canonicality**; determine authority from the event's semantic target/stratum;
4. deterministic projections are derived from the corresponding committed history and inherit that stratum's authority rather than a universal "canon" authority;
5. approved non-event planning state may coexist explicitly but must not contradict replay-derived canon where the same canon-bearing claim is event-sourced;
6. Reader Model, context, revision, reconciliation, Observatory, humanities, and merge artifacts may be durable or even event-sourced while remaining non-canon analysis/governance;
7. no derived/governance artifact may create fictional canon merely by existing, validating, being replayable, or being durably committed.

### Event-domain discipline

A single Runtime stream may carry transitions for several strata. Keep their meanings typed even when they share one append-only log.

- `W` and story-canon-bearing `E/R` transitions can establish or revise fictional canon through the authorized commit path.
- `X` records discourse/reader exposure; replaying X does not make reader exposure an in-world fact.
- `P` records information-flow policy; replaying P changes authorization, not truth.
- `A` records authorial/design decisions; replaying A changes S0 commitments, not what happened in-world.
- `I` records defeasible analysis/governance history; replaying I preserves audit history, not truth status.
- `B` changes branch lineage/assumptions and therefore which history is effective.

Prefer events with one primary semantic target. A multi-stratum event is acceptable when one atomic source action legitimately produces several typed effects—for example a chapter commit may durably record both a world delta and a reader-exposure delta. The shared transaction does not collapse those effects into one semantic type.

Checkpoint/import/migration events may reconstruct several typed projections at once. Treat them as representation/audit operations; they must preserve each imported stratum's prior authority instead of promoting everything in the checkpoint to canon.

### Outside Runtime Mode

`project-state.md` may own durable live ledgers directly. The same layer-separation rules still apply: Reader Model, Context Pack, analysis report, or hypothesis does not become canon automatically.

## 7. Core semantic laws

Treat these as architecture-level invariants.

### K1 - Type separation

Objective truth, actor epistemic state, reader state, visibility policy, provenance, analysis, and authorial design state must remain distinct even when they refer to the same proposition. Durability/replayability is not a shortcut between types.

### K2 - No spontaneous canon

Only an authorized canon commit path may create or revise durable fictional canon. A non-canon semantic event may be durably committed for audit/replay without becoming canon.

A Context Pack, Reader Model update, revision report, reconciliation candidate, Observatory finding, humanities finding, policy event, or merge plan cannot create fictional canon merely by being stored or committed.

Commit-before-dependency extends this same law to consequential S0 decisions: a downstream research/world/chronology/case/long-horizon/Writer-context dependency is legal only if its source was resolved under authorized provenance and semantically committed **before** activation. Agent proposals and temporary assumptions cannot gain authority through repeated use. Delegated/discretion authority permits autonomous resolution, but never removes the need to persist the decision first. `project-state.md` owns the payload/fingerprint and activation record; Intake Validator enforces declared edges, Kernel composes that gate as K2, and Context Compiler gates the selected consumer cone. A later backfilled source commit requires consumer regeneration, not retroactive legality. This does not require unrelated open details to be resolved or all literature to be formalized.

### K3 - Replay determinism

For a fixed normalized event history, branch lineage, reducer semantics, and base snapshot, deterministic replay must produce the same deterministic projection.

If replay is nondeterministic, Runtime has ceased to be auditable.

### K4 - Snapshot transparency

A valid snapshot plus the exact suffix of committed events must be observationally equivalent to replaying the full effective history for the deterministic projection paths the snapshot claims to cover.

A snapshot is an optimization, not a parallel truth.

### K5 - Branch-prefix preservation

A child branch shares the parent's effective history exactly through the declared fork event. Parent history before the fork is neither copied into an independent mutable bundle nor silently rewritten by the child.

### K6 - Branch isolation

Events, secrets, reader state, planning conclusions, and Writer context from one branch do not leak into another branch merely because entity IDs overlap.

Cross-branch adoption requires an explicit merge/adaptation/author decision.

### K7 - Epistemic truthfulness

Use `knows(phi)` only when `phi` is objectively true on that branch/time under the project's knowledge semantics.

False, unverified, or merely possible content belongs under belief/suspicion/report/misremembering/etc.

The converse does not hold: objective truth does not imply that any actor knows it.

### K8 - Epistemic locality

An information event changes only the epistemic states justified by the communication/observation channel.

A public reader reveal does not automatically inform every character. An actor learning a fact does not automatically expose it to the reader.

### K9 - Reader non-authority

Reader exposure and Reader Model estimates may constrain fairness/orientation, but they never define objective truth or actor knowledge.

A likely reader hypothesis may be wrong by design.

### K10 - Taint closure

If artifact/context entry `A` derives from protected source `B`, `A` inherits every still-protected secret taint of `B`, transitively.

Paraphrase, summarization, translation, inference, compression, and reformatting do not erase semantic provenance.

### K11 - Declassification is permission, not amnesia

Declassification changes which roles may receive a protected derivation. It does not erase the artifact's provenance or pretend the artifact was never secret-derived.

Prefer explicit, role-scoped, secret-ID-scoped release over global label removal.

### K12 - Evidence/provenance distinction

A valid evidence hash proves that the cited bytes/range are the bytes/range reviewed. It does not prove the semantic interpretation is correct.

Evidence supports a reviewed delta; it does not replace semantic judgment.

### K13 - Evidence freshness

If the evidence-bearing prose changes, the old evidence link becomes stale even if the durable fact may still be true.

Stale support requires revalidation. It does not automatically erase canon.

### K14 - Minimal semantic disturbance

When revising a representation, preserve unaffected committed semantics. Invalidate/review the dependency closure of the changed source rather than rewriting the whole project.

This is a narrative version of minimal-change belief maintenance.

### K15 - Provenance closure

A consequential derived state should be explainable through a finite Why Trace ending in primitive support such as committed events, reader-visible prose evidence, research evidence, or explicit author/user decisions.

Do not accept unexplained durable nodes that exist only because a summary copied them forward.

### K16 - Open truth preservation

A governed OpenIssue has no secretly selected objective value while its authorial state remains open. Apply Least Authorial Commitment: preserve the weakest authorial commitment supported by explicit decisions and committed canon.

Working hypotheses are conditional planning assumptions, not authoritative constraints. Candidate lists are non-exhaustive unless explicitly declared exhaustive. Migration, summarization, branch simulation, context compilation, factive epistemic labels, and schema completion must not collapse an OpenIssue to one answer.

Mainline prose may rely on robust consequences of the effective compatibility envelope. Material that is only valid under an unresolved working hypothesis remains conditional and must not enter mainline canon merely because it is narratively attractive. Use `open-issue-semantics.md` for the full contract.

### K17 - Representation migration preserves story semantics

Schema/project migration may change representation. It must not silently change story truth, branch lineage, role visibility, authorial unknown status, reader exposure, or provenance meaning.

### K18 - Stable semantic identity

Stable event/entity/branch/question IDs survive representation migration and ordinary wording/name changes unless an explicit identity migration says otherwise.

Human-readable names may change without creating a new semantic entity.

### K19 - Analysis is defeasible

Revision classification, Reader Model hypotheses, impact predictions, and humanities interpretations may be corrected without implying a retcon.

Do not grant analysis artifacts the epistemic status of committed world facts.

### K20 - Formalization restraint

The Kernel governs relationships among formalized material. It does not require all meaningful fiction to become formalized.

### K21 - Epistemic acquisition coverage

A consequential Writer-visible actor fact must trace to a completed authorized acquisition/channel before use; missing records do not erase the coverage obligation. Truth, valid time, historical applicability, acquisition, direct experience and visibility are separate dimensions. Future knowledge is illegal; qualified prediction/belief is not knowledge. Author-only and other POV facts remain isolated. Firsthand memory needs original presence/direct acquisition; later learning cannot create it. Knowledge Topology and Reality Grounding remain the local owners. Kernel shares the law boundary with State Validator and Context Compiler, rather than creating a parallel knowledge store.

### K22 - Precision monotonicity

Downstream expression cannot gain specificity or confirmed evidential basis beyond its authoritative source without available, actor-acquired, same-fact supporting evidence. Compare specificity and basis independently with explicit transition rules; never rank INFERRED numerically or use confidence as precision. Preserve lawful exact-to-exact information and allow legitimate coarser compression. Missing legacy precision remains UNKNOWN. Enforcement concerns declared structured facts/expressions, not automatic interpretation of all prose.

## 8. Replay-derivability matrix

Ask two questions, in order:

1. **which semantic stratum is this value in?**
2. **which event/evidence subset is sufficient to rebuild it?**

"Replayable" is not a truth-status label. A non-canon Reader Model or humanities status may be replayable if the project deliberately event-sources it. Conversely, an objectively true story fact may not be mechanically replayable if the project never formalized the transition.

### Normally replay-derivable from the relevant committed event subset

- branch head/effective revision from branch/event history;
- current object custody/location from `W/R` events that represent those transitions;
- body/resource/capacity and institution/world state from corresponding `W/R` events;
- actor knowledge/belief state from `E/R` events when acquisition/revision/loss is represented;
- active hidden-process state from committed process transitions;
- promise/debt status when explicitly event-sourced;
- reader exposure from `X/R` history when the project event-sources exposure rather than deriving it directly from prose evidence;
- policy/declassification state from `P` history when policy is event-sourced;
- S0 authorial-decision status from `A` history when the project chooses to audit those decisions in Runtime;
- analysis/governance status from `I` history when deliberately event-sourced.

### Not replay-derivable from semantic events alone unless their evidence/decision inputs are also represented

- prose wording and exact textual form;
- camera/focalization choices not represented as durable semantic transitions;
- whether a Reader Model hypothesis is psychologically *correct*;
- stylistic voice quality;
- current context-pack selection unless compilation inputs/request are part of the reproducible build;
- external research freshness at today's date;
- the semantic correctness of a revision-impact interpretation;
- prose evidence validity after file bytes change unless the current bytes are rechecked;
- the truth of an Observatory/humanities interpretation;
- uncommitted planning hypotheses;
- deliberately unformalized meaning.

### Conditionally derivable / dual-source

- **reader exposure**: may be replayed from `X` events or re-derived from reader-visible prose evidence; choose one canonical route for a project and preserve provenance between them;
- **Reader Model**: may have replayable durable history, but its judgments remain defeasible I-layer estimates;
- **actor knowledge**: derivable only if epistemic transitions are committed, never from objective truth alone;
- **authorial unknown status**: derivable only if authorial decisions are event-sourced; otherwise S0 planning state owns it;
- **research-derived canon**: the adopted fictional claim may be event-sourced while external evidence freshness remains outside replay;
- **humanities/Observatory status**: workflow status may be replayable while interpretive validity remains human/Agent-judged.

Do not claim replay guarantees for a layer whose sufficient inputs are absent. Do not infer fictional canonicality from the fact that a layer is replayable.

## 9. Epistemic semantics

Use `knowledge-topology.md` for detailed craft. Kernel constraints:

- knowledge is factive when the project uses the word `knows`;
- belief/suspicion/testimony may be false;
- acquisition, verification, retraction, forgetting, and corruption are different transitions;
- second-order beliefs (`A believes B knows X`) are not flattened into first-order knowledge;
- actor epistemic state is branch- and time-relative;
- an actor cannot use information before the acquisition channel exists;
- retconning the source of information requires downstream epistemic impact review.

For complex mysteries, think in terms of a set of possibilities compatible with an actor's information rather than a single boolean flag. You do not need to serialize a full possible-world model unless the project actually benefits from it.

## 10. Reader semantics

Use `reader-model.md` for memory/load craft. Kernel constraints:

- reader exposure must be grounded in reader-visible text/paratext;
- reader memory/hypothesis is an estimate, not a fact about all readers;
- reader exposure may grow through a reveal while objective history remains unchanged;
- prose revision may contract reader exposure by removing or altering a clue;
- a rereader profile legitimately has a different information state from a first-reader profile;
- hidden backend truth must never be used as evidence that a first-time reader "should know" something.

Reader Model changes are normally I/X operations, not W operations.

## 11. Secret information-flow semantics

Use `context-compilation.md` for implementation details.

Apply these principles:

1. assign opaque secret IDs to protected backend truths;
2. propagate taint through derivation edges transitively;
3. treat lexical forbidden-term checks as a final tripwire, not the semantic model;
4. compile role context under least privilege;
5. declassify explicitly by role and protected semantic source;
6. preserve provenance after declassification;
7. never include a negative spoiler such as "do not mention SECRET-X" in Writer-visible context;
8. never echo protected literal text in leak diagnostics;
9. treat branch identity as part of the visibility boundary when secrets differ by branch.

The target property is narrative noninterference: backend-only truth should not influence an unauthorized role's observable context/output except through an approved release channel.

Perfect formal noninterference cannot be proven for a language model from these files alone; use semantic taint, isolation, blind-role execution when available, and adversarial leak tests as practical enforcement layers.

## 12. Branch and counterfactual semantics

Use `narrative-runtime.md` for mechanics and `hidden-causal-networks.md` for narrative design.

### Four non-equivalent possibility spaces

Do not collapse these just because all can be described as "possible versions of events":

1. **authorial possibility space (S0)** - outcomes the author has intentionally not selected yet;
2. **actor epistemic alternatives (S3)** - worlds compatible with what a character/faction knows or believes;
3. **reader hypothesis space (S4)** - possibilities an attentive reader model may currently consider plausible;
4. **counterfactual branch family (B)** - explicitly instantiated histories used for sandbox/canon divergence analysis.

They can overlap without being identical. In particular:

- simulating a branch under a working hypothesis does not secretly resolve an OpenIssue;
- resolving an OpenIssue does not inform any character or reader;
- a character believing X does not create a branch where X is true;
- a reader strongly suspecting X does not make X canon or authorially selected;
- canonizing one branch does not retroactively mean other branches were "false beliefs"—they remain explicit counterfactual histories.

Treat movement between these spaces as an explicit semantic operation: authorial decision (`A`), canon/world update or revision (`W/R`), epistemic update (`E`), reader exposure/model update (`X/I`), or branch intervention (`B`).

A branch is a **history**, not merely a state snapshot.

For branch `B` forked from `A` at event `F`:

- the past through `F` is shared;
- post-fork events are branch-local;
- state is reconstructed from shared prefix + local suffix;
- branch-local reader/knowledge/context conclusions stay local unless explicitly transferred;
- abandoning a branch does not delete its historical analytical value.

### Cross-branch semantic identity

Stable entity IDs denote semantic identity across the shared prefix unless an explicit identity migration says otherwise. After the fork, **state becomes branch-relative even when the entity ID is the same**.

- the same character ID on two branches is the same trans-branch character identity with potentially divergent knowledge, injuries, relationships, location, or life status;
- a branch-only entity receives a stable ID when introduced on that branch and does not automatically exist on siblings;
- human-readable renaming does not create a new entity;
- equal IDs are not permission to merge divergent branch state; merge/adaptation must choose which branch-relative properties survive.

This is why comparison should be keyed by `(branch, semantic_id, time/checkpoint)` rather than by name alone.

### Minimal-intervention counterfactual rule

When comparing counterfactuals, change the declared intervention first and keep shared world rules/history fixed as far as causality permits.

Additional differences must be:

- downstream consequences of the intervention;
- explicitly declared secondary interventions;
- stochastic/contingent differences allowed by the experiment.

Do not make a branch "work" by silently changing unrelated assumptions.

### OpenIssue versus branch

An OpenIssue governs an authorial question whose effective compatibility envelope still permits more than one completion, or whose resolution is deliberately deferred/preserved. A listed position is not automatically exhaustive.

A branch instantiates a concrete hypothetical history, optionally under one or more declared assumptions.

Do not create branches merely to represent every undecided thought. Do not infer that a simulated branch is secretly the future canon. Adopting branch events does not automatically adopt branch-local exploratory assumptions; authorial selection still requires an explicit `A` operation.

## 13. Evidence and provenance semantics

Use four relations distinctly when possible:

- **supports** - evidence/research/prose gives warrant for a reviewed claim;
- **produces** - an event/reducer deterministically produces a projection fact;
- **derives-from** - an artifact is transformed/summarized from another artifact;
- **depends-on** - target correctness/validity requires source.

Do not flatten all four into a generic "related" edge when the distinction affects invalidation.

### Authority does not flow upward through derivation

Derivation may carry **content, provenance, dependency, and secret taint**. It does not automatically carry a stronger semantic authority.

- a summary derived from Fixed canon is still a derived summary, not a replacement canonical source;
- a Reader Model derived from reader-visible prose remains a defeasible model;
- an analysis report derived from committed events remains analysis;
- a Writer-visible artifact derived from a protected secret inherits taint until explicitly declassified.

Moving a claim into a stronger authority class requires an explicit promotion/commit decision owned by that class. This prevents "summary laundering" and "analysis laundering" in the same way taint closure prevents secret laundering.

### Why Trace termination

For a consequential durable claim, a Why Trace should eventually terminate in one or more primitive bases:

- committed event(s);
- current prose evidence span(s);
- external research/source evidence;
- explicit user/author decision;
- declared project rule/invariant.

A cycle of summaries that only cite one another is not provenance.

## 14. Revision semantics

Use `semantic-revision.md`, `prose-state-reconciliation.md`, and `change-control.md`.

### Prose-only revision

If the semantic analysis is genuinely `PROSE_ONLY`:

- prose revision lineage changes;
- style/voice metrics may change;
- objective canon event history does not change;
- deterministic world projection does not change.

### Meaning/state-affecting revision

A semantic-impact report proposes candidate deltas. It does not commit them.

After review:

- validate prose/state evidence where required;
- compute dependency impact;
- if reader-facing established canon changes, invoke Change Control;
- in Runtime Mode, materialize accepted canonical changes through new committed events and/or an explicit new branch;
- refresh projections after commit.

### Minimal-change rule

When new evidence contradicts an existing representation, remove/revise the smallest justified dependent structure rather than discarding unrelated canon.

The project is closer to a reason-maintenance system than to a mutable summary document.

### World update versus representational revision

Keep these distinct:

- `the bridge collapses on Tuesday` -> W;
- `we discover our previous record wrongly said Monday` -> R;
- `the protagonist learns on Wednesday that it collapsed Tuesday` -> E;
- `the reader is shown the Tuesday collapse in a chapter-20 flashback` -> X.

One chapter may contain all four without them being the same transition.

## 15. Migration-preservation laws

Representation evolution must satisfy semantic preservation, not merely schema validity.

### M1 - Event-history preservation

Committed historical event bytes/IDs/order remain stable unless the migration contract explicitly uses a safe compatibility/upcast layer. Prefer read-time normalization to rewriting committed history.

### M2 - Replay equivalence

For every supported branch/checkpoint, old representation interpreted by the old semantics and migrated representation interpreted by the new semantics should yield observationally equivalent deterministic story projections for the supported query surface.

### M3 - Branch-lineage preservation

Parent/fork relationships and effective shared history do not change because of a schema migration.

### M4 - Epistemic preservation

Migration does not turn belief into knowledge, erase false-belief status, or grant information to actors who did not have it.

### M5 - Reader/exposure preservation

Migration does not invent or delete reader-visible evidence merely because Reader Model representation changed.

### M6 - Security preservation

Migration does not declassify a secret, erase taint ancestry, or widen role access unless that policy change is explicit and separately approved.

### M7 - Open-state preservation

Migration does not resolve OpenIssues, convert working hypotheses into authoritative constraints, treat legacy candidate lists as exhaustive, or convert provisional hypotheses into objective truth. Legacy `DELIBERATELY_UNRESOLVED` records require semantic classification before stronger v2 meaning is inferred.

### M8 - Provenance preservation

Why Trace and evidence lineage remain reconstructable across migration. If IDs change, provide an explicit identity mapping.

### M9 - Time-axis preservation

Story time, commit order, and discourse/exposure position retain their meanings. Do not "clean up" one axis by rewriting it to match another.

### M10 - Unaffected-semantics preservation

A representation migration may alter formatting/defaults/indexing but must not produce new narrative consequences outside the declared migration scope.

## 16. Query discipline

When asking the system a semantic question, specify the axis/layer when ambiguity matters.

Prefer queries like:

- What is objectively true on branch `main` after event `EV-40`?
- What did character A know at story time T?
- What had the reader been shown by the end of Chapter 12?
- What does the weekly-reader heuristic currently keep active?
- Why does the current projection say the key belongs to B?
- Which protected secrets taint this Writer-visible summary?
- Which downstream nodes become stale if Chapter 3 changes?
- Which facts differ between branch A and branch B because of the declared intervention?

Avoid vague queries such as `what is the state?` when several semantic strata are in play.

## 17. Mechanical verification

Use:

```bash
python scripts/storyctl.py semantics verify PROJECT_ROOT
python scripts/storyctl.py semantics laws
```

The verifier is deliberately partial. It can check machine-decidable Kernel laws such as:

- Runtime/branch validity;
- deterministic replay repeatability;
- current branch/head consistency;
- snapshot transparency when snapshots exist;
- context-derivation graph integrity and semantic taint closure metadata;
- approved reconciliation evidence freshness;
- obvious open-authorial-unknown collapse;
- cross-artifact project/branch identity consistency.

It cannot prove:

- that a Reader Model is psychologically correct;
- that a clue is fair;
- that a belief is narratively plausible;
- that a paraphrase contains no conceptual leak under all possible language-model behavior;
- that an interpretation of prose is semantically correct.

Use deterministic verification as a floor, then adversarial review for semantic risks.

## 18. Failure modes

### Projection absolutism

A cached/current-state file is treated as more authoritative than event history.

Repair: replay and rebuild the projection.

### State soup

World truth, actor belief, reader hypothesis, and Writer visibility are placed in one undifferentiated map.

Repair: restore semantic strata.

### Temporal collapse

Story chronology, commit order, and reveal order are treated as one timeline.

Repair: state which time axis each claim uses.

### Epistemic leakage

A reader reveal or backend fact silently becomes actor knowledge.

Repair: require an information channel / epistemic transition.

### Taint laundering

A secret is paraphrased/summarized and therefore considered clean.

Repair: propagate provenance taint by derivation, not lexical overlap.

### Evidence worship

A matching hash is treated as proof a semantic conclusion is true.

Repair: hashes prove evidence identity/freshness only.

### Revision-as-event confusion

A correction to the project's record is narrated as though the fictional world itself changed.

Repair: distinguish R from W and use Change Control when reader-facing canon changes.

### Branch snapshot cloning

A branch is created by duplicating current state and then mutating both copies independently.

Repair: reconstruct from parent prefix + branch-local events.

### Open-state laundering

A migration, summary, context pack, branch experiment, or repeated planning summary quietly selects one answer to an OpenIssue, treats a working hypothesis as a constraint, or assumes a candidate list is exhaustive.

Repair: restore the authoritative compatibility envelope, conditional provenance, and resolution authority defined by `open-issue-semantics.md`.

### Semantic migration drift

A schema migration validates syntactically but changes replay outcome, visibility, branch lineage, or provenance.

Repair: test semantic preservation properties, not only JSON Schema validity.

## 19. Ownership boundary

This file owns cross-layer laws only.

Local owners remain:

- world/event history and branches -> `narrative-runtime.md`;
- actor truth/belief/evidence craft -> `knowledge-topology.md`;
- reader memory/hypothesis -> `reader-model.md`;
- Writer/role visibility and taint implementation -> `context-compilation.md`;
- prose revision classification -> `semantic-revision.md`;
- prose/state evidence -> `prose-state-reconciliation.md`;
- retcon policy -> `change-control.md`;
- governed authorial openness / OpenIssues -> `open-issue-semantics.md`;
- discovery sidecars and promotion from exploratory prose -> `discovery-drafting.md`;
- formalization restraint -> `formalization-boundary.md`;
- representation migration -> `runtime-schema-migration.md` / `project-operability.md`.

When two local owners disagree about composition, the Kernel's type-separation and preservation laws resolve the cross-layer contract. Do not create a second local implementation inside this file.
