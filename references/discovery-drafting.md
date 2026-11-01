# Discovery Drafting and Deliberate Unknowns

Use this reference when the user wants to discover the story through drafting rather than fully converging architecture first. It owns exploratory prose, discovery sidecars, and promotion/reconciliation of draft-emergent possibilities. For consequential truths intentionally left unsettled, use `open-issue-semantics.md`; this file does not own the OpenIssue ontology. It does not replace continuity, the event runtime, or the normal readiness gate by default.

## Contents

- Two drafting modes
- Discovery safety gate
- Discovery sidecar
- Promotion to canon
- Reconciliation loop
- Discovery versus OpenIssue
- OpenIssue handoff
- Branch use
- Failure modes

## 0. Poetics discovery boundary

Discovery may reveal an emergent poetic pattern as well as story facts. Record it as a **poetics hypothesis** with textual evidence; do not silently promote it to project-level Project Poetics. Repeated success still requires review/authorization before it can invalidate downstream strategy.

## 1. Two drafting modes

### Architected Drafting

Default for serious new long-form projects.

Use the full `prewriting-readiness.md` convergence loop before Chapter 1 and normal chapter/scene planning thereafter.

### Discovery Drafting

Use only when:

- the user explicitly asks to pants/discovery-write/explore;
- a mature project intentionally opens an exploratory branch;
- the story needs a bounded improvisational scene to discover character behavior;
- a remote-volume waiver has passed the two-message protocol in `prewriting-readiness.md` for a substantial opening; the first request alone is insufficient.

Discovery Drafting is not permission to forget canon. For substantial Chapter 1, a discovery label or `discovery_mode=true` never disables the formal current-cone safety/authorization gate owned by `prewriting-readiness.md`. Bounded local experiments still use the minimum constraints below.

## 2. Discovery safety gate

Before exploratory prose, establish the minimum constraints that must not be violated:

- active canon branch;
- current time/place;
- POV/camera permission;
- Fixed facts and hard world rules;
- current character state and knowledge;
- consequential objects/access;
- immediate scene pressure;
- explicit forbidden contradictions;
- known research constraints if real-world facts materially matter.

If these cannot be established, the draft is too unconstrained to be safely reconciled.

## 3. Discovery sidecar

New facts invented during exploratory prose do **not** immediately enter canon.

Record them in a discovery sidecar with fields such as. Use `assets/discovery-templates/discovery-entry-template.json` when a structured form helps:

- discovery ID;
- source chapter/scene/draft version;
- observed textual claim;
- inferred implication;
- affected entities;
- conflicts or dependencies;
- status;
- recommended action.

Allowed statuses:

- `OBSERVED_IN_DRAFT`;
- `NEEDS_RECONCILIATION`;
- `PROVISIONAL_DISCOVERY`;
- `APPROVED_FOR_CANON`;
- `PROMOTED_TO_CANON`;
- `REJECTED`;
- `RETIRED`.

The Writer may surface a discovery; the Writer may not silently promote it.

## 4. Promotion to canon

To promote a discovery:

1. compare it against Fixed/Implied canon;
2. inspect dependency impact;
3. decide whether it enriches or merely simplifies the story;
4. check whether it creates accidental retroactive knowledge;
5. check real-world evidence if applicable;
6. obtain Director/user approval when consequential;
7. emit the appropriate committed event(s) if Runtime Mode is enabled;
8. update projections/ledgers;
9. invalidate dependent plans when needed.

Promotion should preserve the **discovery**, not necessarily its first rough wording.

## 5. Reconciliation loop

After a discovery-drafted chapter:

```text
Draft
 -> extract discoveries
 -> continuity check
 -> dependency impact
 -> classify each discovery
 -> approve/reject/revise
 -> commit approved state
 -> update future plans
```

Do not rewrite the draft just because a discovered fact is provisional unless it actually conflicts or the user wants revision.

## 6. Discovery versus OpenIssue

A **discovery** is something the draft surfaced that may or may not be promoted. An **OpenIssue** is a consequential author-level question whose non-resolution itself needs durable governance. They may interact but they are not the same object.

Examples:

- "The character unexpectedly avoids eye contact" -> discovery sidecar first;
- "Why did she leave, and which future chapters must remain compatible with several answers?" -> OpenIssue;
- "For now, explore the father-debt explanation without choosing it" -> OpenIssue working hypothesis plus conditional discovery/planning;
- "This gesture may mean shame or fear, but nothing later depends on deciding" -> usually leave unformalized.

Do not inflate every discovery into an OpenIssue. Do not let a discovery sidecar bypass OpenIssue resolution authority.

## 7. OpenIssue handoff

When a discovery exposes or materially changes a consequential open authorial question, hand governance to `open-issue-semantics.md`.

Use `assets/discovery-templates/open-issue-template.json` for new structured records. The old `assets/discovery-templates/authorial-unknown-template.json` is a legacy compatibility asset and must not define new v2 semantics.

Key rules:

- a working hypothesis remains conditional;
- listed positions are non-exhaustive unless explicitly declared exhaustive;
- planning stance is separate from truth viability;
- mainline prose may not commit hypothesis-dependent facts while the Issue remains open;
- an Issue may be retired without an answer when the narrative dependency disappears;
- `DELIBERATELY_UNRESOLVED` legacy records require semantic classification before stronger v2 meaning is inferred.

The Agent must not answer an OpenIssue merely because one continuation is easier to write.

## 8. Compatibility during discovery

When discovery work touches an OpenIssue, classify the resulting artifact as robust, conditional, narrowing, resolving, conflicting, or review-required under `open-issue-semantics.md`.

If a scene is only valid under a working hypothesis:

- keep it in the discovery sidecar / conditional plan;
- or instantiate an explicit branch;
- or obtain an authorized authorial decision before mainline commit.

Do not plant apparently objective clues that are only fair under an answer the author has not selected.

## 9. Branch use

Use a canon branch when exploration changes high-impact assumptions.

Use a discovery sidecar when exploration is local and can be reconciled without a new world line.

Examples suited to a branch:

- major character lives instead of dies;
- antagonist identity changes;
- prophecy mechanism changes;
- an institution chooses a different strategy;
- alternate ending.

Examples suited to a discovery sidecar:

- character unexpectedly avoids eye contact;
- a room detail becomes useful;
- a minor relationship acquires warmth;
- a recurring gesture emerges.

## 10. Failure modes

Reject:

- discovery mode silently replacing the user's architected workflow;
- every improvised sentence becoming canon;
- later planning depending on an unpromoted discovery;
- the Agent resolving an OpenIssue without authorized A-level commitment;
- a working hypothesis laundering into canon or compatibility constraints;
- a non-exhaustive position list being treated as exhaustive;
- fake ambiguity where committed facts actually eliminate every intended alternative;
- endless discovery used to avoid committing to decisions that near-term causality requires;
- reconciliation that erases all surprise and makes the exploratory draft conform mechanically to the old plan.
