# Formalization Boundary and Productive Ambiguity

Use this reference when the system is tempted to encode every meaningful detail as state, promise, debt, invariant, reader question, dependency, or hidden cause. It owns the boundary between **durable operational state** and material that should remain provisional, interpretive, local, or deliberately unformalized.

## Contents

- Core law
- What requires formalization
- What usually should remain unformalized
- Four representation statuses
- Progressive formalization
- Authorial unknowns versus unformalized material
- Reconciliation boundary
- Reader-model boundary
- Forensic governance without ontology hunger
- Validation rules
- Failure modes
- Review questions

## Core law

Project Poetics may be durable planning state, but do not convert aesthetics into fake numeric weights, exhaustive ontologies, or mechanically decidable "literary quality" fields. Formalize only commitments whose durable representation changes execution/revision safety.

Formalize only when representation materially protects future correctness, access control, causality, recovery, or revision impact.

The absence of a structured field is not automatically a defect.

A novel is allowed to contain:

- ambiguity;
- unstable interpretation;
- mixed motives;
- unnamed attraction or resentment;
- images whose significance is not settled;
- contradictory self-understanding;
- future possibilities the author has not chosen;
- local impressions that never become durable state;
- ordinary details that remain ordinary.

Do not turn the story into a complete ontology of itself.

## 1. What requires formalization

Prefer durable representation when forgetting or confusing the fact could create a real downstream contradiction or information leak.

Strong candidates include:

- canon branch and project identity;
- consequential time / location / route constraints;
- object custody or access when later scenes depend on it;
- injury, resource, capacity, or irreversible material change;
- knowledge acquisition, false belief, access restriction, or secret clearance when later behavior depends on it;
- explicit commitments, contracts, promises, debts, or setups that create future obligations;
- active hidden processes whose offscreen evolution changes future possibilities;
- project rules or invariants that are mechanically falsifiable;
- dependency edges needed for revision propagation;
- external research dependencies whose freshness/scope constrains factual claims;
- state changes whose provenance must survive session/model/version boundaries.

Even here, formalize the **minimum useful claim**. Do not add precision the prose or world does not support.

Bad:

- `trust = 63.4` because a relationship changed.

Better:

- `trust_state = damaged-but-functional` when that distinction affects later choices;
- or leave the relation qualitative if no later mechanism requires a state label.

## 2. What usually should remain unformalized

Do not automatically encode:

- the definitive reason a character looked away;
- the single true emotion behind an ambiguous gesture;
- what an image or recurring object "means";
- whether attraction, envy, shame, or grief is primary when the text intentionally leaves them entangled;
- every conversational implication;
- every minor promise-like phrase;
- every reader curiosity as a formal question;
- every thematic echo as a causal dependency;
- every possible future plot direction;
- local sensory details with no durable consequence;
- author interpretations that are useful today but not canon;
- symbolic readings that should remain available to multiple interpretations.

If formalization would answer a question the fiction benefits from keeping open, do not formalize it merely because a field exists.

## 3. Four representation statuses

Use these as reasoning categories. They do not require a new registry for every project.

### A. Durable formalized

The project commits to a structured representation because later correctness depends on it.

Examples:

- character A possesses the only key;
- character B learned fact X in chapter 18;
- branch `main` contains event E;
- an institution has already filed a public notice.

### B. Provisional / author-level working hypothesis

Useful for planning, but not committed as story truth. When the hypothesis belongs to a consequential governed question, model it as an OpenIssue position with `planning_stance=working_hypothesis`; otherwise ordinary planning notes are enough.

Examples:

- "Perhaps she avoids him because she is ashamed.";
- "The old photograph may eventually connect to the mother.";
- "This relationship might harden into rivalry."

Keep such material in planning/discovery notes if needed. Do not let it masquerade as canon.

### C. Governed OpenIssue

The project intentionally tracks a question because the **decision horizon, compatibility envelope, working assumptions, or preserve-open policy itself** matters. For new structured records use `open-issue-semantics.md`; legacy `AUTHORIAL_UNKNOWN / DELIBERATELY_UNRESOLVED` records remain readable but do not define new semantics.

Do not turn the absence of an answer into a mandatory record. Create an OpenIssue only when later correctness depends on preserving the shape of the open space.

### D. Deliberately unformalized

No structured record is required. The meaning remains in prose, local context, or author intuition until and unless later causality makes representation useful.

This is a legitimate steady state, not unfinished bookkeeping.

Do not create a dedicated unformalized-item registry merely to prove that something is unformalized.

## 4. Progressive formalization

Let structure follow causal activation.

A detail may move through:

`local prose -> recurring pattern -> causally relevant -> durable state`

without being formalized at every earlier stage.

Example:

1. A character repeatedly checks a window. Initially this may be texture.
2. Later the behavior becomes a recognizable anxiety pattern. It may still remain prose-level characterization.
3. If the window-checking becomes a known tell that another character uses strategically, the knowledge relation may deserve representation.
4. If it becomes evidence in a mystery, the clue/access path may enter Knowledge Topology.

Do not retroactively claim the earlier detail was a formal setup unless the story actually commits to that interpretation.

## 5. OpenIssues versus unformalized material

These are different.

An **OpenIssue** is tracked because the project must preserve a consequential compatibility envelope, decision authority/horizon, conditional hypothesis dependency, or deliberate non-resolution policy.

An **unformalized element** needs no such governance. `unmentioned` does not automatically mean `unknown`, and missing data does not create an OpenIssue by itself.

Do not inflate every uncertainty into structured state. The OpenIssue mechanism protects consequential openness; it is not an inventory of everything the author has not decided.

## 6. Reconciliation boundary

`prose-state-reconciliation.md` should reconcile **durable operational consequences**, not every meaning in the text.

Candidate durable facts may include:

- custody transfer;
- knowledge change;
- injury/resource/access change;
- explicit commitment;
- durable institutional action;
- consequential public version;
- branch/canon-relevant event.

Do not require reconciliation candidates for:

- subtext;
- metaphor;
- mood;
- ambiguous motive;
- symbolic association;
- transient sensory perception;
- a thought the character may later reject;
- a reader interpretation.

A strict reconciliation gate verifies the project's chosen durable deltas. It must not force the prose to become fully machine-readable.

## 7. Reader-model boundary

`reader-model.md` is a design model, not a claim that every reader state can be measured exactly.

Track foreground/warm/dormant questions when doing so helps delayed payoff, orientation, or fairness. Do not encode every possible interpretation or curiosity.

A reader may hold contradictory hypotheses. The model may preserve a bounded set or simply mark uncertainty.

Never modify prose solely to make the Reader Model easier to serialize.

## 8. Forensic governance without ontology hunger

Forensic governance increases **provenance and protection**, not semantic totalization.

A Forensic project may still leave these unformalized:

- the deepest motive behind a betrayal;
- whether a recurring image is symbolic or incidental;
- the exact emotional ratio inside a mixed reaction;
- a future branch the author has not chosen to instantiate;
- thematic meaning readers are meant to construct themselves.

Use Forensic machinery for expensive mistakes:

- branch contamination;
- secret leakage;
- knowledge impossibility;
- contradictory event history;
- unsupported canon revision;
- high-cost continuity failure.

Do not use it to manufacture certainty about human meaning.

## 9. Validation rules

Validators may require a representation only when a governing contract already says that representation must exist.

Examples:

- A Forensic project that declares Runtime must have a valid Runtime artifact.
- A committed prose-based delta in a strict reconciliation report must have evidence.
- A secret-tainted Writer entry must obey declassification rules.

Validators must **not** infer:

- "this gesture looks important, therefore it needs a state field";
- "this chapter contains uncertainty, therefore it needs a reader question";
- "this recurring object exists, therefore it is a setup";
- "this character behaved inconsistently, therefore one motive must be selected."

Mechanical checks protect declared contracts. They do not decide what the novel means.

## 10. Failure modes

### Ontology hunger

Every recurring detail becomes a field, edge, debt, promise, or invariant.

Repair: ask what future error the representation actually prevents. If no material failure is identified, leave it unformalized.

### Premature motive lock

A planning hypothesis becomes canonical motivation before the character/story has earned or authorized it.

Repair: demote it to provisional planning or an OpenIssue working hypothesis where durable governance is justified; preserve contradictory evidence.

### Promise inflation

Every repeated image or unusual sentence is registered as setup/payoff debt.

Repair: only formalize a promise when the narrative has created a real reader/causal obligation.

### Ambiguity laundering

A nuanced passage is summarized into one clean state label, then later scenes treat the label as more authoritative than the prose.

Repair: narrow or remove the state field. When durable author-level non-resolution matters, route to `open-issue-semantics.md`; when only actor/reader interpretation is uncertain, keep it in S3/S4 rather than manufacturing an authorial unknown.

### Validator coercion

The project changes fiction to satisfy a schema that should have been optional.

Repair: change the contract or disable the subsystem. Never invent story facts to make validation green.

### Forensic maximalism

Forensic profile is interpreted as "encode everything."

Repair: remember that Forensic governs failure cost and provenance. It does not erase artistic indeterminacy.

## 11. Review questions

Before adding a new durable field, ledger, dependency, or invariant, ask:

- What concrete future failure would this representation prevent?
- Does the text/world actually support this level of precision?
- Could the representation prematurely decide a motive, symbol, theme, or future outcome?
- Is this durable state, a planning hypothesis, an authorial unknown, or merely prose-local meaning?
- Would leaving it unformalized make the novel less correct, or only make the system less complete-looking?
- Can this remain ambiguous without breaking continuity?
- If we formalize it now, can later prose legitimately contradict or reinterpret it?

Prefer a smaller truthful model over a complete-looking false one.
