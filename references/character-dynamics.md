# Character Dynamics and Relationship Change

Use this reference when characters must change across long spans without becoming trait-flipping plot instruments.

## Contents

- Character as actor, agent, and author
- Change loop
- Character state record
- Thresholds and path dependence
- Relationship vectors
- Offscreen life
- Contradiction and self-misreading
- Audit

## Core principle

Model characters as path-dependent people whose current behavior inherits body, habit, relation, knowledge, self-story, social role, and prior consequence. **Dynamics do not require a completed transformation arc.**

Legitimate long-form patterns include durable change, partial change, oscillation, relapse, failed change, repeated contradiction, context-dependent behavior, deliberate stability, and changes mainly in how other characters/readers understand the person.

Project Poetics decides whether character transformation is central.

## 1. Dynamics loop

When change is actually occurring, use a path-dependent loop such as:

```text
pressure -> response -> consequence -> revised habit/self-story/relationship -> later response
```

But do not force the loop to produce monotonic growth. It may produce:

- reinforcement of an old pattern;
- temporary deviation then return;
- oscillation;
- relapse;
- increased self-knowledge without behavioral change;
- behavioral change without accurate self-knowledge;
- stable behavior whose meaning changes because context/reader understanding changed.

Track only what later behavior depends on.

## 2. Character dynamics record

For important characters, add only fields that can change future causality:

- current social roles;
- recurring habits and default coping style;
- active goals and projects;
- values and red lines;
- feared losses;
- attachments and dependencies;
- self-concept;
- current life-story explanation of major past events;
- disowned or unacknowledged motive;
- shame, pride, grief, resentment, hope, or obligation with behavioral consequences;
- current threshold under stress;
- recent identity-threatening event;
- latest choice that contradicted the old self;
- change state: resisted / unstable / rehearsed / consolidated / relapsed.

Avoid amateur diagnosis. Track behavior, interpretation, and pressure rather than assigning unsupported disorders.

## 3. Change should be path-dependent

Do not write:

> cowardly -> traumatic event -> brave

Prefer:

- the person protects themselves in the old way;
- that defense fails or becomes costly;
- they reinterpret what the old defense means;
- they attempt a different action under smaller pressure;
- success or failure changes the next threshold;
- under greater pressure they may relapse;
- later they make a choice that would have been impossible earlier.

Relapse does not erase development. Growth can be uneven across contexts.

## 4. Thresholds instead of switches

For beliefs, loyalties, habits, and moral lines, know what pressure would be required to move them.

Examples:

- a loyal officer may disobey for family but not for money;
- a pacifist may use violence to stop immediate harm but refuse revenge;
- a proud rival may ask for help only after a public duty outweighs personal shame.

The threshold itself can move after experience.

## 5. Contradiction without randomness

Allow characters to contain competing commitments.

A person can:

- love someone and distrust them;
- believe in an institution and hate its current leaders;
- want truth and avoid one specific truth;
- be generous in private and cruel when status is threatened;
- condemn a behavior they secretly understand too well.

Contradiction becomes depth when each side has history, incentive, or identity behind it.

## 6. Relationship vectors

Do not compress relationships into one variable such as `trust = high`.

Track relevant dimensions separately:

- affection;
- trust;
- intimacy;
- dependence;
- admiration;
- fear;
- resentment;
- shame;
- jealousy;
- debt/obligation;
- power asymmetry;
- shared secrets;
- shared history;
- public role versus private role;
- mistaken model of the other person;
- expectation not yet spoken aloud.

Relationships can move in different directions at once. An alliance can gain trust while losing affection; love can deepen while dependence becomes intolerable.

Persist consequential trust/distrust, resentment, fear/safety, obligation, attachment, shame residue, repair attempts, and context-specific triggers in the relationship/emotional-residue projection owned by `project-state.md`; keep them qualitative unless the story truly supplies a meaningful scale.

## 7. Relationship change requires interaction history

For major relationship turns, ask:

- What repeated pattern existed before the turn?
- What specific event violated or confirmed that pattern?
- How did each side interpret it differently?
- What changed in behavior afterward?
- What old behavior remains out of habit?
- What would a third party notice before either participant admits the change?

Do not let one speech overwrite years of interaction unless the speech carries decisive new evidence or a long-suppressed commitment finally becomes actionable. Use `state-inertia.md` when knowledge, emotion, habit, trust, and public behavior should update at different speeds.

## 8. Offscreen life

Important characters keep changing when absent from the protagonist.

Track major offscreen updates caused by:

- work;
- family;
- illness or recovery;
- money;
- romance;
- boredom;
- status;
- new friends and enemies;
- changing institutions;
- aging;
- grief;
- success that has nothing to do with the protagonist.

When they return, let changed behavior reveal part of that missing life before exposition explains it.

## 9. Self-story can be wrong

Characters are not authoritative interpreters of themselves.

Distinguish:

- what happened;
- what the person believes happened;
- what they say happened;
- what identity that explanation protects;
- what later evidence could force reinterpretation.

A strong long-form arc may change less through new facts than through a new explanation of old facts.

Social performance can sustain a whole long-form trajectory: inner pressure -> performance -> audience response -> success -> estrangement -> greater dependence on performance. Track only consequential iterations. Ambition may gain access while increasing shame, compromise romance or friendship, and alter risk tolerance; social movement is not a level ladder. An obsessive object may likewise reorganize self-story while remaining a literal material object with access, use and history. Keep behavior and contradiction available without immediate motive resolution or diagnostic labeling.

## 10. Audit

Before a major character turn, ask:

- Is the change visible in choices rather than only narration?
- Did prior pressure create a plausible path?
- Has the person paid a social, emotional, or practical cost for changing?
- Are old habits still present where realistic?
- Does the new behavior generalize too quickly across every context?
- Have relationships changed independently rather than all following the same arc?
- Could this person plausibly continue living if the protagonist vanished?

## Cast identity versus current state

Character Roster / Cast Architecture establishes **who exists**; Character State describes already established people now. Neither substitutes for the other. Before substantial Chapter 1, Cast evidence lists `characters` with unique `id`, `identity`, `social_position`, `life_anchor`, and `state_scope: "long-term" | "scene-local"`; `opening_character_ids` names actual important appearing characters. `narrative_centers[]` names one or multiple real roster entries. Legacy `central_character` remains a compatible single-center form. Centers need no completed transformation arc.

Long-term characters require separately active Character State, whose evidence has actual `states` entries with matching `character_id` and qualitative `current_state`. Current-cone Writer-safe derivatives are bound through `writer_entry_ids`. The readiness owner verifies identity/anchor/evidence hashes and safe handoff; this owner supplies character meaning and never self-authorizes prose from a maturity label.
