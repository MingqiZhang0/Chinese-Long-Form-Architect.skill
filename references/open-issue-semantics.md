# Open-Issue Semantics and Authorial Partial Worlds

Use this reference when a consequential story question is intentionally **not yet settled**, when the author wants to explore one possibility without selecting it, when a project must preserve ambiguity across summaries/migrations/branches, or when an Agent is tempted to fill a structured field merely because the schema has room for one.

This file owns the **S0 authorial-open-design contract**. It does not replace fictional canon, Knowledge Topology, Reader Model, Research Grounding, Runtime branches, or interpretive analysis. `narrative-semantics-kernel.md` owns the cross-layer composition laws.

## Contents

- Purpose and non-goals
- Claim versus Issue
- Least Authorial Commitment
- OpenIssue record model
- Issue state and resolution policy
- Domain semantics and non-exhaustive positions
- Viability versus planning stance
- Authorial and effective compatibility envelopes
- Working hypotheses and conditional workspaces
- Robustness classes for mainline work
- Resolution, retirement, and reopening
- Context compilation and Writer-safe boundaries
- Runtime and dependency semantics
- Branch semantics
- Revision and migration
- Conflict versus openness
- Machine validation versus semantic review
- Formalization boundary
- Failure modes

## 1. Purpose

A long-form fiction system must preserve not only what has been decided, but also the **shape of what has not been decided**.

Examples:

- the author knows that a departure may involve the protagonist's father but has not decided the mechanism;
- a motive has several live explanations and the next ten chapters should remain compatible with all of them;
- one explanation is being used as a temporary planning hypothesis without becoming truth;
- the work is intended to preserve a real unresolved question through the ending;
- a prior answer is reopened during revision;
- a character or reader suspects a proposition that the author has not yet made true or false.

Treat such openness as legitimate semantic state. Never force closure merely because a schema, summary, planner, model, or tool prefers a single value.

## 2. Non-goals

Do not turn fiction into a complete-world theorem prover.

This system does not:

- enumerate every possible complete world;
- require an answer for every unmentioned detail;
- formalize every ambiguous motive, image, or interpretation;
- assign fake probabilities to authorial or reader possibilities;
- infer a unique answer from a short candidate list unless that list is explicitly exhaustive;
- let deterministic code decide whether subtle prose is compatible with every interpretation;
- create a second canon database beside Story State / Runtime;
- treat all ambiguity as authorial uncertainty.

Use `formalization-boundary.md` before creating an OpenIssue.

## 3. Claim versus Issue

Keep **claims** and **issues** conceptually distinct.

A **Claim** is a proposition that can be believed, suspected, supported, rejected, or committed.

Example:

> C42: Her departure was materially caused by something involving her father.

An **Issue** is a question whose authorial settlement is still governed.

Example:

> Q17: Why did she leave?

One Issue may have several positions/claims. Positions may overlap and may jointly contribute to the eventual resolution. Do not assume every Issue is an exclusive-choice multiple-choice question.

The same Claim may simultaneously be:

- a viable authorial position in S0;
- a working hypothesis in S0;
- suspected by a character in S3;
- likely in a Reader Model in S4;
- still uncommitted as fictional truth.

Never collapse those stances.

## 4. Least Authorial Commitment

Apply **Least Authorial Commitment**:

> When several semantic states remain compatible with explicit user intent and committed canon, preserve the weakest authorial commitment sufficient for current work.

If the user says:

> "It may have something to do with her father."

record a viable/working position if useful. Do **not** convert it into the constraint `father_related = true`.

If the user later says:

> "It is definitely connected to her father, but I have not decided what happened."

then the father connection may become an authoritative constraint while the mechanism remains open.

Least commitment is not permission for endless deferral. When near-term causality, fair clue design, publication, or a user-reserved decision horizon requires settlement, resolve, branch, or surface the authorized decision gate rather than hiding behind openness.

## 5. OpenIssue record model

For new structured records, prefer `assets/discovery-templates/open-issue-template.json` and validate against `assets/project-schemas/open-issue.schema.json`.

For backward compatibility, projects may continue to store these records under the existing Story State key `authorial_unknowns`. Treat that key as a serialization compatibility surface, not as the full ontology name.

A v2 OpenIssue record minimally owns:

- `question_id` - stable semantic identity;
- `question` - human-readable issue;
- `state` - `open / resolved / retired`;
- `resolution_policy` - `must_resolve / may_resolve / preserve_open`;
- `resolution_criterion` - what information is sufficient to count as resolution;
- `decision_authority` - who is allowed to make the authorial decision;
- `decision_horizon` - optional point by which a decision becomes necessary;
- `domain_semantics` - whether listed positions are open-ended, constraint-defined, or explicitly exhaustive;
- `constraints` - authoritative boundaries with provenance;
- `positions` - named candidate claims/solutions used for planning;
- `resolution` or `retirement` when applicable.

### `planning_owner_ref` compatibility field

`planning_owner_ref` is a **legacy optional planning-routing pointer**, not an ownership or authority field. The name is retained only so existing v2 records remain readable without a destructive migration.

Apply these rules:

- the OpenIssue semantic owner remains **S0 under this Open-Issue contract**;
- authorial decision permission is governed only by `decision_authority` and authorized `A` operations;
- `planning_owner_ref` must never grant truth authority, resolution authority, viability authority, or ownership of the Issue to the referenced planning artifact;
- `planning_owner_ref` must not change the authoritative commitment fingerprint;
- new records should normally set it to `null` (or omit it where the serialization path permits);
- do **not** blanket-default it to the literal project path "planning/project-poetics.md"; Project Poetics owns literary salience/form/capability choices, not authorial-open truth;
- populate a non-null value only when a specific existing planning artifact needs an operational follow-up/routing reference for this particular Issue. Such a pointer remains non-authoritative and may be cleared without changing S0 commitments.

Older records carrying the literal value "planning/project-poetics.md" from the former blanket default remain readable, but treat that value as legacy routing metadata and review whether it should simply be cleared to `null`. Do not infer that Project Poetics owns the Issue.

Do not store Writer-safe summaries as authoritative OpenIssue fields. They are derived artifacts.

## 6. Issue state

Use only three lifecycle states in v2:

### `open`

The Issue has not met its resolution criterion and remains governed by its openness policy.

### `resolved`

An authorized authorial decision has met the Issue's resolution criterion.

Resolved does **not** mean every related detail is now fixed. Create or preserve child Issues for remaining open subquestions.

### `retired`

The Issue no longer requires an answer because the relevant narrative dependency was removed, transformed, or abandoned.

Retirement is not resolution. Do not invent an answer merely to close bookkeeping.

## 7. Resolution policy

### `must_resolve`

The project expects an eventual authorized resolution. Prefer a meaningful decision horizon for consequential cases.

### `may_resolve`

The project permits later resolution but does not currently require it.

### `preserve_open`

The open status is itself part of the design contract. Mainline work should preserve meaningful multiplicity unless the user explicitly changes the policy first.

`preserve_open` is not a synonym for every kind of literary ambiguity. Route separately:

- backend truth fixed but reader denied a unique answer -> Reader Model / disclosure policy;
- facts fixed but interpretation remains plural -> interpretive/prose layer;
- fictional truth itself intentionally left unassigned -> OpenIssue with `preserve_open` when durable governance is required.

## 8. Resolution criterion

An Issue is resolved when its **own resolution criterion** is satisfied, not when the entire fictional world becomes uniquely specified.

Example:

> Q17: Why did she leave?
>
> Resolution criterion: determine the direct trigger and whether the father relationship is causally material; do not require a complete theory of her self-understanding.

The Issue may become resolved while a child Issue such as `Q17.1: What exactly happened to the father?` remains open.

Do not invent percentage-style partial-resolution scores.

## 9. Domain semantics

### `open_ended`

Listed positions are examples/currently considered options. The list is explicitly **not exhaustive**.

A list with one item does not imply only one possible answer remains.

### `constraint_defined`

The admissible space is primarily described by authoritative constraints rather than an enumerated option list.

### `declared_exhaustive`

The author has explicitly declared that the listed positions cover the allowed domain for this Issue.

Only under `declared_exhaustive` may zero/one viable listed positions justify mechanical contradiction/singleton warnings. Even then, the machine must never silently author an A-level resolution event.

## 10. Position semantics

Each position has two orthogonal statuses.

### Viability

`viable` - still compatible with authoritative authorial/canon constraints.

`excluded` - explicitly removed from the authorial possibility space by an authoritative basis.

An excluded position must carry an `exclusion_basis_ref`. Planner dislike, temporary inconvenience, or lack of attention is not enough.

### Planning stance

`candidate` - available but not currently driving planning.

`working_hypothesis` - temporarily used for conditional exploration.

`parked` - still viable but intentionally not being actively explored.

Changing planning stance does not change truth viability.

In particular:

> `working_hypothesis -> parked`

is normally an interpretive/planning update (`I`), not an authorial exclusion (`A`).

## 11. Authorial compatibility envelope

Conceptually, let an Issue have a current authorial completion space `Omega(Q)`.

Do not materialize or enumerate this space. Treat it as a semantic interpretation of:

- active authorial constraints;
- applicable committed canon;
- applicable world rules;
- authoritative exclusions/resolutions.

Do not include working hypotheses merely because they are convenient.

### Authorial Commitment Envelope

The author-level commitments explicitly selected in S0.

### Effective Compatibility Envelope

The subset still compatible with authorial commitments **plus** already committed canon/world rules.

A committed world fact may reduce what remains possible without itself being a new authorial decision.

## 12. Safe/common consequence

When an Issue remains open, mainline work may safely rely on consequences that are compatible with all currently admissible completions.

Use the possible-world formulation only as a reasoning discipline:

- if a consequence holds under every admissible completion -> potentially `ROBUST`;
- if it requires one temporary assumption -> `CONDITIONAL`;
- if it excludes still-authorized completions -> `NARROWING` or `RESOLVING`.

Do not claim deterministic proof for natural-language compatibility unless a project-specific machine invariant genuinely covers it.

## 13. Working hypotheses

A working hypothesis creates a **conditional workspace**. It does not narrow the authoritative OpenIssue.

If H1 is the temporary hypothesis, reason as if working inside `Omega(Q | H1)` while preserving the parent `Omega(Q)`.

Valid operations include:

- propose H1;
- set H1 as the current working hypothesis;
- park H1;
- compare H1 with H2;
- instantiate a counterfactual branch under H1;
- reject H1 as a planning approach without excluding it from authorial viability.

Do not:

- promote H1 into an authoritative constraint merely because several plans use it;
- let summaries rewrite H1 as fact;
- treat branch simulation under H1 as future-canon selection.

## 14. Conditional provenance

Artifacts derived under a working hypothesis must retain their assumption dependency.

Reuse the canonical Runtime dependency graph where available:

```text
H1 --conditional-on-hypothesis--> PLAN-V2
PLAN-V2 --planning--> SCENE-MISSION-32
SCENE-MISSION-32 --derived--> DRAFT-32
```

The canonical edge direction remains `source -> target = target depends on source`.

If H1 becomes authoritatively `excluded`, active downstream conditional artifacts become stale/invalidated/review-required according to their local owner.

Do not auto-canonize those artifacts if H1 is later selected. Selection removes one assumption barrier; normal literary/state review still applies.

This extends provenance closure (`K15`) rather than creating a second dependency system.

## 15. Mainline robustness classes

When prose/planning materially touches an OpenIssue, classify the artifact when the governance profile/risk justifies it:

### `ROBUST`

Compatible with the effective envelope without relying on an unresolved hypothesis.

May proceed through ordinary commit/review.

### `CONDITIONAL`

Depends on one or more still-uncommitted hypotheses.

Keep in a discovery sidecar, conditional planning artifact, or explicit branch. Do not commit to mainline merely because the prose is good.

### `NARROWING`

Would eliminate currently authorized completions without fully resolving the Issue.

Requires authorial Issue-impact review and a legitimate source of narrowing.

### `RESOLVING`

Would satisfy/collapse the Issue's resolution criterion.

Requires an authorized `A`-level authorial decision before mainline commit.

### `CONFLICTING`

Contradicts authoritative constraints/canon.

Block unless handled through revision/change control.

### `REVIEW_REQUIRED`

The system cannot reliably classify the semantic effect.

Do not guess. Human/Agent semantic review is the correct steady state.

## 16. Resolution

A v2 resolution should record:

- the resolved statement;
- optional position IDs that contributed to it;
- a durable basis reference;
- an authority/decision reference.

Resolution is an authorial-design update (`A`). It is not an in-world event merely because Runtime records it.

If the resolution later produces fictional facts, character knowledge, or reader disclosure, those belong to the appropriate `W/E/X` transitions.

## 17. Retirement

Retire an Issue when its narrative dependency disappears without requiring an answer.

Examples:

- the plotline is removed;
- the scene that required the decision is abandoned;
- a larger structural revision makes the question irrelevant.

Record a reason and basis. Do not fabricate a resolution to avoid an open ledger item.

## 18. Reopening

An author may reopen a previously resolved Issue.

If the prior resolution remained only in S0 planning, an `A`-level reopen may be enough.

If the resolution already caused committed world facts, actor knowledge, reader exposure, or many downstream artifacts, reopening requires `semantic-revision.md` / `change-control.md` impact analysis. Changing S0 does not erase consequences already committed elsewhere.

Preserve resolution/reopen history for Why Trace.

## 19. Context compilation

Raw positions/working hypotheses are author/planner material by default.

A Writer normally receives a **sanitized commitment boundary**, not the backend candidate list.

Writer-safe boundary content may include:

- already authoritative constraints;
- observable facts the scene may use;
- what must remain semantically uncommitted;
- what kinds of clue/reaction are permitted;
- what consequential facts the Writer must not invent.

Do not tell the Writer hidden candidate answers merely in the form "do not choose H1/H2". Negative candidate spoilers still contaminate the Writer context.

Use `assets/tooling-templates/open-issue-writer-boundary-template.md` when a durable Writer-safe derivative is useful.

Raw `open-issue-candidates` context entries are forbidden to the Writer by the deterministic Context Compiler. Use `open-issue-boundary` for Writer-facing derivatives.

## 20. Reader-direction exception

The author may intentionally bias readers toward a still-uncommitted hypothesis without selecting it as truth.

Example:

> "Make readers suspect the father more strongly this chapter, but do not decide the actual cause yet."

Represent this as reader-exposure/narrative strategy toward H1, not as authorial truth. Writer guidance should express the authorized observable cue/disclosure target without laundering H1 into canon.

## 21. S0-S7 ownership

- **S0** owns OpenIssue identity, authorial constraints, positions, planning stance, resolution policy, and authorial decisions.
- **S1** may durably record `A`/`I` events when the project event-sources design history.
- **S2** may project current OpenIssue state if S0 events are replayed; replayability does not create fictional truth.
- **S3** owns actor belief/suspicion/knowledge about Claims.
- **S4** owns reader hypotheses/exposure about Claims.
- **S5** owns who may see raw positions, hidden answers, or Writer-safe derivatives.
- **S6** owns provenance, constraint basis, and conditional dependency edges.
- **S7** owns audits such as collapse/conflict/migration review; those findings do not create truth.

Never create separate CharacterUnknown/ReaderUnknown/ResearchUnknown registries merely to mimic OpenIssue.

## 22. Factive epistemic boundary

`knowledge-topology.md` and Kernel K7 remain authoritative:

- `knows(phi)` requires `phi` to be objectively true under project semantics;
- `falsely_believes(phi)` requires `phi` to be objectively false;
- if `phi` is still authorially open, use `believes`, `suspects`, `was_told`, `considers`, etc.

Do not let S3 truth-sensitive labels secretly resolve S0.

Likewise, a Reader Model should not call a hypothesis "wrong" merely because the author has not selected it. Use comparative/defeasible stance language until truth is fixed.

## 23. Runtime event discipline

Do not add a parallel event system.

Use existing semantic operator classes:

### `I` - interpretive/planning update

Examples:

- propose a position;
- promote a viable position to working hypothesis;
- park a working hypothesis;
- change an analyst/reader planning theory.

`I` must not change authoritative authorial viability.

### `A` - authorial decision update

Examples:

- add/relax an authoritative constraint;
- authoritatively exclude a position;
- resolve/retire/reopen an Issue;
- change `preserve_open` policy;
- explicitly delegate/withdraw decision authority.

Only an authorized `A` path may change authorial commitments.

## 24. Branch semantics

A branch can instantiate a concrete history under a hypothesis without selecting that hypothesis for the parent.

- branch under H1 -> conditional exploration;
- successful branch prose -> still conditional until adopted;
- branch merge/adoption -> choose story events explicitly; do not automatically import exploratory assumptions;
- canonizing a branch does not by itself mean every branch-local planning hypothesis became an authorial resolution.

OpenIssue identity is branch-relative only where the project explicitly forks authorial-design state. Otherwise the parent Issue remains open independently of branch experiments.

## 25. Revision and reopening

An OpenIssue's effective envelope may narrow or widen over time.

Widening operations include:

- relaxing/removing an authorial constraint;
- reopening a resolution;
- revising old canon that previously ruled out an option.

Do not assume openness monotonically shrinks.

If a resolution already has downstream committed consequences, perform revision-impact analysis before reopening. Preserve unaffected semantics and invalidate only the dependency closure justified by the change.

## 26. Migration

Migration must preserve openness, not merely field names.

For legacy `AUTHORIAL_UNKNOWN` records:

- preserve question identity;
- treat old `viable_answers` as **open-ended positions by default**, never as automatically exhaustive;
- preserve old compatibility constraints and provenance where available;
- do not invent resolution data.

For legacy `DELIBERATELY_UNRESOLVED` records:

- do not automatically classify them as fictional incompleteness, reader ambiguity, or interpretive plurality;
- preserve the conservative "do not collapse" behavior;
- require semantic classification before upgrading to a stronger v2 meaning.

Prefer two-phase migration:

1. lossless structural preservation;
2. explicit semantic adjudication.

## 27. Conflict versus openness

Distinguish **missing/undecided information** from **conflicting support**.

Examples:

- author has not decided whether father is alive -> OpenIssue;
- one authoritative artifact says alive and another says dead -> representation/continuity conflict;
- backend truth is fixed but Writer lacks access -> information-flow restriction, not unknown;
- external historical fact has an answer but research has not verified it -> research dependency, not authorial unknown;
- a detail is simply not worth modelling -> unformalized, not OpenIssue.

Never repair a contradiction by relabeling it `unknown`.

## 28. Machine validation versus semantic review

Use deterministic tools only for mechanically decidable boundaries.

### Machine-verifiable examples

- record shape and stable ID;
- legal state/policy/domain values;
- open record carrying a resolution;
- `preserve_open` record being resolved without policy change;
- excluded position missing exclusion provenance;
- excluded position simultaneously marked working hypothesis;
- declared-exhaustive open Issue with zero viable positions;
- active dependency on an authoritatively excluded hypothesis;
- Writer context containing a raw `open-issue-candidates` entry;
- legacy records requiring semantic classification.

### Semantic-review examples

- whether prose genuinely remains compatible with all live explanations;
- whether a clue materially narrows the Issue;
- whether two witness completions are genuinely distinct;
- whether a complex motive is fully resolved by a proposed statement;
- whether an old `DELIBERATELY_UNRESOLVED` record means fictional incompleteness or only reader ambiguity.

Use conservative outcomes:

- `VERIFIED` -> deterministic pass;
- `VIOLATION` -> deterministic fail;
- `REVIEW_REQUIRED` -> warning/review gate, never silent inference.

### Deterministic implementation surface

Use `scripts/open_issue.py` as the shared internal validator/fingerprint helper. It is not an authorial-answer solver and is not a separate public workflow. Public maintenance/query surfaces remain:

- `python scripts/storyctl.py semantics verify PROJECT_ROOT --json` for cross-layer K16/K15 checks;
- `python scripts/storyctl.py state-validate STORY_STATE` for story-state structural findings;
- `python scripts/storyctl.py query STORY_STATE open-issues --json` for read-only inspection (`authorial-unknowns` remains a compatibility alias).

The deterministic layer may reject illegal representation/provenance states and mark semantic review required. It must never infer a literary answer merely because the schema is complete.

## 29. Formalization boundary

Create an OpenIssue only when preserving openness matters operationally.

Good reasons:

- future prose must remain compatible with multiple answers;
- clue fairness depends on not collapsing the answer early;
- a working hypothesis has downstream artifacts that need invalidation;
- a decision horizon/owner must be protected;
- the ambiguity itself is a deliberate long-form design commitment.

Do not register every fact the author has not thought about.

`unmentioned` is not automatically `unknown`.

`deliberately unformalized` remains a legitimate steady state.

## 30. Failure modes

### Hypothesis laundering

A working hypothesis is copied into compatibility constraints, summaries, or canon until its provisional origin disappears.

Repair: restore it as a position/planning stance and propagate conditional provenance to downstream artifacts.

### Candidate-list closure

A short list of currently considered positions is treated as exhaustive without an explicit `declared_exhaustive` decision.

Repair: restore `open_ended`/`constraint_defined` domain semantics.

### Planning rejection becomes truth exclusion

A Planner parks H1 and the state silently marks H1 impossible.

Repair: restore `viability=viable`; planning stance and authorial viability are orthogonal.

### Factive side-channel closure

An open Claim is marked `knows(...)`, `false_belief(...)`, or `wrong_reader_hypothesis`, thereby smuggling a truth value in through another stratum.

Repair: downgrade to non-factive stance until truth is fixed.

### Conditional draft canonization

Prose written under H1 is committed to mainline while Q remains open.

Repair: keep it in sidecar/branch or obtain an authorized authorial decision before commit.

### Writer possibility contamination

The Writer receives raw backend candidate answers and prose begins leaning toward one despite nominal instructions to remain open.

Repair: compile only a Writer-safe commitment boundary.

### Unknown laundering

A summary, migration, schema fill, branch experiment, or context pack selects an answer merely to produce a complete record.

Repair: preserve the OpenIssue and mark semantic review when necessary.

### Conflict laundering

Two authoritative sources disagree and the project calls the result "unknown".

Repair: surface a continuity/revision conflict; uncertainty and contradiction are different conditions.

### Openness inflation

Every unspecified texture detail becomes an OpenIssue.

Repair: apply `formalization-boundary.md`; register only consequentially governed openness.
