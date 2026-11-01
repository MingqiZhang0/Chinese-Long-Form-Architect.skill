# Change Control and Canon Migration

Use this reference whenever later planning suggests changing established **story meaning/canon**: a rule, history, relationship, capability, institution, identity, date, or hidden truth. Representation/schema migrations belong to `runtime-schema-migration.md`; prose revision impact belongs to `semantic-revision.md`. Do not confuse data-format migration with retcon.

## Contents

- Change classes
- Impact analysis
- Migration procedure
- Retcon discipline
- Branch-before-retcon rule
- Rule versioning
- Change budget

## 1. Change classes

### Class A - open-space design
The fact has never been established and no existing scene depends on it.

Change freely, then update project state.

### Class B - provisional migration
The fact exists in architecture but has not become reader-facing canon.

Change it after checking dependencies and the relevant adversarial review tests.

### Class C - interpretive migration
The earlier prose remains literally true, but a later model changes its meaning.

Allowed when the reinterpretation is causally honest and not merely a loophole.

### Class D - locked-canon migration
The earlier prose or source canon would become false.

Do not perform silently. Prefer redesigning the new idea. If the user explicitly accepts a retcon, record it as such and repair all dependencies.

## 2. Impact analysis

Before changing a consequential assumption, inspect:

- world rules;
- progression limits;
- timeline;
- geography and logistics;
- institutional behavior;
- economy and scarcity;
- character decisions;
- actor knowledge;
- reader clues;
- planned reveals;
- setup/payoff promises;
- existing combat outcomes;
- legal or political consequences;
- ordinary-life details that rely on the old rule.

A small rule change can have large second-order effects.

## 3. Migration procedure

For a high-impact experiment whose outcome is uncertain, prefer a canon branch from `narrative-runtime.md` before rewriting `main`. Use direct migration only when the project has actually chosen the new assumption.

1. State the old assumption.
2. State the proposed new assumption.
3. Identify why the change is needed.
4. List affected state entries and scenes.
5. Decide whether each dependency survives, needs reinterpretation, needs rewriting, or makes the change unacceptable.
6. Re-run the relevant adversarial review tests.
7. Update ledgers and change log.
8. Promote the new assumption to the correct status.

## 4. Retcon discipline

Do not call a contradiction a twist.

A twist reveals a truth compatible with prior facts.
A retcon changes prior truth.

Use retcons only when the user knowingly prefers repair over continuity.

## 5. Branch-before-retcon rule

When the proposed change would alter many downstream dependencies and the author is still testing it:

1. fork a branch at the last shared committed event;
2. explore the change there;
3. run continuity/dependency review;
4. compare consequences;
5. either abandon the branch or approve a semantic merge plan.

Do not copy an alternate branch back into canon by file overwrite. Approved adoption becomes new target-branch events/migrations.

## 6. Rule versioning

For complex power or technology systems, keep a simple rule version when useful.

Example:

- Power Model v0.3 - provisional architecture;
- Power Model v0.4 - pressure-test revisions;
- Power Model v1.0 - core rules locked by Chapter 6.

Do not version trivial prose choices.

## 7. Change budget

Early architecture should remain flexible. Later prose should become progressively harder to change.

As the novel grows:

- change open space freely;
- change provisional design carefully;
- reinterpret locked facts only when genuinely supported;
- avoid direct contradiction.

This creates discovery without destroying reader trust.
