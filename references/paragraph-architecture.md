# Paragraph Architecture

Use this reference when prose has sentence-by-sentence line breaks, giant undifferentiated blocks, dialogue that loses social ownership, psychological passages that fragment into slogans, mobile formatting that distorts semantic structure, or long-form re-entry/echo passages that fail to restore reader state.

This module owns **semantic paragraph structure, paragraph boundaries, paragraph clusters, and the relation between semantic paragraphs and optional display blocks**. It does not own sentence-level diction (`prose-standard.md`), scene selection (`scene-architecture.md`), temporal resolution (`narrative-time-duration.md`), dialogue strategy (`dialogue-character-voice.md`), descriptive attention (`environment-description.md`), reader-memory state (`reader-model.md`), or macro rhythm (`rhythm-propulsion.md`).

## Contents

- Core model
- Paragraph continuity vector
- Boundary strength and paragraph hysteresis
- Semantic paragraph versus display block
- Paragraph functions and paragraph clusters
- Default grammar by discourse mode
- Realist and psychological long-form grammar
- Multi-generational and ultra-long-form grammar
- Polyphonic and dialogue-heavy grammar
- Stream-of-consciousness and modernist grammar
- Minimalist and omission-heavy grammar
- Compressed/conceptual grammar
- Serial and mobile web-fiction grammar
- Long-form memory paragraphs
- Long-paragraph topologies
- Paragraph endings and whitespace
- Deliberate misalignment protocol
- Paragraph audit
- Deterministic diagnostics
- Routing

## 1. Core model

Treat a paragraph as a **local narrative field**, not a quota of sentences or characters.

A semantic paragraph normally tells the reader one of two things:

1. **continue using the current local world model**; or
2. **update that model here because a meaningful boundary has been crossed**.

Do not ask first, "Is this paragraph too long?" Ask:

- What local narrative state currently dominates?
- Which continuities still bind the next sentence to this state?
- What changed strongly enough that the reader benefits from a reset?
- If a boundary is intentionally hidden or delayed, what other signal preserves coherence?

Do not use paragraph breaks as substitutes for syntax. A sequence of related actions, perceptions, reactions, or thoughts may belong to one paragraph even when several verbs or sentences are involved.

Do not force one topic per paragraph. Require one **dominant narrative job** or a legible bridge among jobs.

## 2. Paragraph continuity vector

Track paragraph cohesion through a small set of dimensions. Not every paragraph needs all of them.

Useful dimensions include:

- **focal actor** - whose embodied or cognitive access organizes the passage;
- **active participants** - who is currently socially or physically relevant;
- **story time** - the local temporal frame;
- **space** - the current spatial model or reference frame;
- **local goal** - what the actor is trying to do now;
- **causal chain** - what event is producing what consequence;
- **attention object** - what perception or object currently organizes noticing;
- **cognitive task** - what question, memory, appraisal, or decision is being processed;
- **social floor** - who currently controls the interaction or forces response;
- **discourse mode** - action, dialogue, reflection, description, summary, argument, re-entry, etc.;
- **anchor/motif** - an object, sound, image, phrase, or external event that can preserve continuity across changes.

A paragraph may survive changes in one dimension when other dimensions remain strongly continuous.

Examples of legitimate compensation:

- time shifts while the same sensory trigger organizes memory;
- focalization shifts while all minds respond to the same explosion or public event;
- space expands while the paragraph continues one explanatory or causal task;
- several objects are noticed while one inspection goal governs attention.

Do not treat any single dimension as an automatic break trigger.

## 3. Boundary strength and paragraph hysteresis

Classify boundaries qualitatively rather than by fixed numeric score.

### Continuous

Keep the paragraph when most governing dimensions remain stable and the new sentence continues the same micro-action, thought process, observation, or causal chain.

### Weak boundary

A small change occurs, but the higher-order task remains stable. Either continuation or a break may work. Let rhythm, emphasis, and readability decide.

Examples:

- attention moves from a door to its lock during the same inspection;
- a speaker pauses, moves a cup, and continues the same social action;
- a memory adds another episode while answering the same present question.

### Normal boundary

Break when a meaningful local reorganization occurs, such as:

- a new actor takes control of the social floor;
- a search becomes an escape;
- observation becomes a consequential decision;
- a completed causal unit becomes the premise of a new unit;
- narration changes from current action to a sustained memory or argument.

### Strong boundary

Use a paragraph break, blank line, section break, or scene break when several core dimensions reset together: actor, time, place, goal, causal chain, or narrative mode.

### Paragraph hysteresis

Do not break on every perturbation. Preserve a paragraph through small fluctuations while its dominant narrative state remains stable.

This prevents:

- one-action-per-line fragmentation;
- one-thought-per-line pseudo-literary cadence;
- catalogue-like observation;
- false emphasis caused only by whitespace.

## 4. Semantic paragraph versus display block

Distinguish two layers.

### Semantic paragraph

Own narrative cognition and discourse structure. A semantic paragraph signals a meaningful local grouping or boundary.

### Display block

Own optional visual breathing on a constrained medium such as a mobile screen.

Default to making them identical. Split a semantic paragraph into multiple display blocks only when the target medium materially benefits and a **display-safe breakpoint** exists.

A display-safe breakpoint should:

- coincide with a genuine weak internal boundary;
- preserve attribution and syntax;
- avoid inventing suspense or emphasis;
- avoid splitting a tightly coupled action-consequence pair;
- avoid turning one psychological process into slogan fragments.

Never infer "mobile-friendly" = "one sentence per paragraph".

Do not let platform formatting silently change semantic paragraph structure in the canonical manuscript unless the user explicitly wants platform-native layout.

## 5. Paragraph functions and paragraph clusters

A paragraph may primarily perform one of these jobs:

- **ACTION** - continuous embodied action or tactical change;
- **PERCEPTION** - a governed attention path;
- **ORIENTATION** - establish/re-establish time, place, participants, or situation;
- **DIALOGUE_TURN** - one speaker's social action plus associated gesture/reaction;
- **REACTION** - register consequence before the next initiative;
- **REFLECTION** - pursue one cognitive/emotional problem;
- **DESCRIPTION** - develop a perceivable field through selective attention;
- **SUMMARY** - compress a state transition across story time;
- **ARGUMENT** - advance a rhetorical move;
- **TRANSITION** - bridge a meaningful change in mode, location, time, or thread;
- **RE_ENTRY** - reactivate a dormant person, place, object, thread, or institution;
- **ECHO** - reactivate earlier meaning through present action, object, image, ritual, or relation;
- **AFTERMATH** - let a changed state settle into body, space, relationship, or institution.

Do not label paragraphs in user-facing prose. Use these categories backstage only when they clarify construction or diagnosis.

### Paragraph cluster

Treat several adjacent paragraphs as a higher local rhythmic unit.

Useful cluster shapes include:

- orientation -> action -> consequence -> reaction;
- narration -> dialogue -> dialogue -> reaction -> silence;
- long setup -> medium escalation -> short decisive turn -> longer aftermath;
- summary -> scene entry -> high-resolution exchange -> compressed exit;
- anchor -> excursion -> return across several paragraphs rather than one.

Judge short or long paragraphs relative to their cluster. A short paragraph has little emphasis if every surrounding paragraph is equally short.

## 6. Default grammar by discourse mode

Do not use one paragraph grammar for all prose.

### Action mode

Prioritize:

- bodily continuity;
- causal continuity;
- geometry;
- local goal.

Keep tightly coupled micro-actions together. Break when the action program, tactical state, causal regime, or controlling actor changes.

### Dialogue mode

Prioritize:

- speaker attribution;
- social turn;
- social floor;
- reaction ownership.

A new speaker usually starts a new paragraph. The same speaker's dialogue, gesture, pause, and continuation may remain together when they form one social action.

### Reflection mode

Prioritize:

- cognitive task;
- emotional appraisal;
- associative anchor.

Do not break for every new thought. Break when the mind changes what problem it is solving, returns decisively to the present, reaches a consequential conclusion, or is interrupted by external reality.

### Description mode

Prioritize:

- perceptual anchor;
- attention path;
- viewpoint task;
- spatial scale.

Keep related details together when they belong to one act of looking. Break when scale, location, perceptual task, or meaning changes enough to require reorientation.

### Summary mode

Prioritize:

- state transition;
- conceptual/causal continuity;
- the before/after relation.

A paragraph may cover hours, years, or generations if one transition remains the governing job. Time span alone does not require a break.

### Argument mode

Prioritize rhetorical moves rather than speaker identity. A single speaker may need multiple paragraphs when moving through claim, evidence, qualification, counterposition, concession, or conclusion.

### Collective-scene mode

Prioritize shared anchors and social-floor shifts. Many focal participants may coexist in one paragraph when one public event binds their attention.

### Stream-of-consciousness mode

Prioritize phenomenological or associative continuity. Objective chronology may break while sensory, emotional, verbal, or motif continuity holds.

## 7. Realist and psychological long-form grammar

For realist, psychological, and socially embedded long-form fiction, default to relatively strong alignment between semantic paragraph boundaries and event-model changes.

Use longer paragraphs freely for:

- sustained social observation;
- one psychological processing task;
- institutional or household pressure fields;
- compressed biography;
- one governed descriptive field;
- one chain of material consequence.

Use shorter paragraphs when:

- dialogue sharpens into turn-by-turn interaction;
- a decision changes the local goal;
- a discovered fact invalidates the previous model;
- a relationship changes social floor or obligation;
- the current paragraph's pressure finally resolves into action.

Do not imitate any named author's syntax or diction. Abstract only structural principles.

## 8. Multi-generational and ultra-long-form grammar

For novels spanning decades, generations, volumes, reincarnations, dynasties, or very large casts, paragraphs must serve **longitudinal memory** as well as local clarity.

Use paragraphs to:

- re-establish an old actor through a current action rather than biography recap;
- show how a familiar place changed since last appearance;
- reactivate an old object through present custody or consequence;
- let old social obligations constrain a current decision;
- carry thematic or symbolic echoes whose meaning has changed;
- compress long periods while preserving the causal bridge into the next scene.

Prefer **recap through causality** over encyclopedic reminder.

Weak:
- explain who a returning person was and what happened many chapters ago.

Stronger:
- let a current habit, injury, debt, object, relationship, title, or institutional role reactivate the old memory because it matters now.

Use `reader-model.md` to decide how much reactivation is needed. Do not assume binge-reader memory for weekly/serial readers.

## 9. Polyphonic and dialogue-heavy grammar

For novels driven by prolonged conversation, ideological conflict, group pressure, family councils, interrogations, salons, committees, or socially dense rooms:

- treat paragraph boundaries as **interactional ownership** signals;
- track who currently controls the topic;
- separate a new speaker when attribution would otherwise blur;
- allow one speaker to occupy several paragraphs when rhetorical moves change;
- give silence its own paragraph only when it functions as a social act;
- let group reaction create a paragraph boundary when it changes the room's pressure or option set;
- avoid converting debate into alternating exposition blocks.

A speaker turn is a strong default boundary, not an absolute law. Shared action, interruption, quoted material, and tightly attached gesture can modify the surface form.

Use `dialogue-character-voice.md` for speech acts and social strategy.

## 10. Stream-of-consciousness and modernist grammar

Do not equate stream of consciousness with random fragmentation or giant unpunctuated blocks.

Permit objective boundaries to be intentionally under-marked when the character's experienced continuity requires it.

Examples of legitimate continuity mechanisms:

- a sensory trigger carries present into memory;
- a repeated phrase or image bridges time layers;
- one emotion reorganizes several memories;
- a public sound or object hands focalization from one mind to another;
- syntax or rhythm preserves surface continuity while chronology shifts.

### Anchor-mediated focal handoff

Allow focalization to move without a hard paragraph break when a strong shared external anchor makes the transfer legible and the project's camera regime permits it.

### Phenomenological continuity

A time jump may stay inside a paragraph when the point is that the character does not experience past and present as cleanly separated.

### Compensatory cohesion

Whenever a major default continuity is broken, require another legible organizing force. If time, actor, space, and goal all change with no compensatory anchor, the result is probably incoherence rather than modernist freedom.

Use `focalization-narrator.md` to validate camera permission. Experimental paragraphing never licenses knowledge leakage.

## 11. Minimalist and omission-heavy grammar

Minimalism should remove explanation, not destroy event structure.

Prefer:

- precise social turns;
- concrete actions with unstated interpretation;
- pauses that belong to a relationship;
- ordinary syntax when ordinary syntax can carry continuity;
- selective omission of interpretation already inferable from action.

Reject pseudo-minimalist fragmentation such as one mundane action per line when no genuine boundary exists.

**Omission is not fragmentation.**

Short paragraphs earn force through contrast, ownership, silence, or changed state. If every sentence is isolated, shortness loses structural meaning.

## 12. Compressed/conceptual grammar

For fable-like, historiographic, speculative, essayistic, archival, mythic, or conceptually compressed narration, conceptual causality may dominate chronology.

A single paragraph may legitimately span:

- years;
- generations;
- several locations;
- multiple incidents;

when all details serve one explanatory, causal, or conceptual move.

Break when the governing proposition changes, a counter-model enters, or the narrative returns from abstraction to a specific scene requiring a new reader model.

Do not force scene-like paragraph density onto summary or conceptual narration.

## 13. Serial and mobile web-fiction grammar

Separate **serial memory management** from **mobile visual formatting**.

For serial long fiction:

- assume some readers return after hours or days;
- reactivate dormant people/threads through present causality;
- use current stakes to recover old facts;
- avoid repetitive encyclopedia recap;
- distinguish binge, weekly, casual, puzzle, and rereader needs through `reader-model.md`.

For mobile presentation:

- allow somewhat more visual breathing when the platform benefits;
- use display-safe weak boundaries rather than arbitrary sentence breaks;
- preserve social ownership and action-causal chains;
- do not manufacture a hook at every screenful;
- do not let platform lineation overwrite the canonical semantic paragraph unless explicitly requested.

A platform-specific display layer may split or reflow semantic paragraphs after drafting. Keep that transformation reversible where practical.

## 14. Long-form memory paragraphs

### Re-entry paragraph

Use when a person, place, institution, object, or thread returns after enough dormancy that reader retrieval may be weak.

Restore only what the present scene needs:

- identity cue;
- changed state;
- old relation now relevant;
- one diagnostic detail;
- current reason for return.

Do not repeat the original introduction.

### Re-entry compression

Prefer one current functional detail that restores several memory links at once.

Examples of useful carriers:

- persistent injury;
- habitual gesture;
- job technique;
- altered title;
- old debt;
- missing object;
- changed architecture;
- familiar phrase used in a changed relationship.

### Echo-bearing paragraph

Let a current event reactivate an earlier pattern, object, ritual, place, or phrase whose meaning has changed.

An echo should work first as present action. Do not halt the story merely to announce the parallel.

### Place-memory paragraph

On return to a known location, emphasize delta: what aged, vanished, was repaired, changed ownership, changed use, or became newly salient.

Use `environment-description.md` and `world-evolution-social-ecology.md` for the underlying change.

## 15. Long-paragraph topologies

A long paragraph should possess internal structure. Useful topologies include:

### Funnel

broad field -> narrower field -> person -> decisive detail.

### Expansion

specific object/event -> memory or implication -> larger social/historical field.

### Spiral

return repeatedly to one question or image, each time with changed understanding.

### Contrast

state A -> state B -> relation between them.

### Accumulation

several aligned observations/effects -> emergent judgment or consequence.

### Anchor -> Excursion -> Return

begin with a present anchor -> range through memory, analogy, argument, or history -> return to the anchor transformed.

Reject **chain drift** when A leads to B leads to C leads to D with no governing task, return structure, or compensatory cohesion.

## 16. Paragraph endings and whitespace

Do not give every paragraph a punchline, hook, reversal, aphorism, ominous hint, or moral landing.

Useful ending types include:

- **completion** - the local task ends;
- **turn** - direction changes and the next paragraph takes over;
- **residue** - action ends but sensation/emotion remains;
- **question** - a genuine unresolved problem becomes active;
- **image** - stop on a concrete perception with earned weight;
- **transfer** - hand attention/control to another actor, place, time, or thread.

Whitespace may encode social silence, hesitation, discontinuity, or relief, but only through the relation between adjacent paragraphs. Blank space has no automatic profundity.

## 17. Deliberate misalignment protocol

Default to aligning paragraph boundaries with meaningful narrative boundaries.

Permit deliberate misalignment only when the text gains something specific from it.

Possible reasons:

- preserve traumatic or associative continuity;
- let memory invade present experience without a clean gate;
- hand focalization through a shared public anchor;
- maintain breathless bodily action across minor state changes;
- sustain one rhetorical or conceptual movement across time/space changes;
- intentionally delay reader re-segmentation.

When deliberately hiding or delaying a boundary, identify the compensating structure:

- motif;
- sensory trigger;
- syntax/rhythm;
- repeated phrase;
- shared object/event;
- stable cognitive task;
- explicit typographic or section-level signal.

If no compensating cohesion exists, restore the missing boundary.

Never use experimental paragraphing to excuse camera cheating, incoherent state, or accidental ambiguity.

## 18. Paragraph audit

For an important prose pass, inspect both false and missing boundaries. Use `assets/paragraph-templates/paragraph-audit-template.md` when the passage is complex enough to justify a written audit artifact.

### False-boundary test

Merge adjacent paragraphs mentally. If nothing meaningful changes at the break and the only effect is artificial emphasis, consider removing it.

Warning signs:

- one mundane action per paragraph;
- one sentence of internal thought per paragraph;
- a continuous visual scan broken into object-by-object blocks;
- every paragraph ending in a mini-hook;
- repeated isolated sentence fragments with no social or cognitive boundary.

### Missing-boundary test

Split a long paragraph mentally at major state changes. If actor, time, place, goal, causal chain, or discourse mode repeatedly resets and no higher continuity binds them, add boundaries.

### Boundary-explanation test

For every conspicuous break, be able to explain its structural job in plain terms. The explanation does not need to be dramatic.

Good reasons include:

- new social owner;
- new local goal;
- completed causal unit;
- cognitive-mode change;
- re-entry;
- scene-resolution change;
- deliberate emphasis after sustained longer paragraphs.

"It looked too long" is not enough unless the task is explicitly display formatting.

### Short-paragraph test

Ask what the shortness gains relative to surrounding paragraphs. If the answer is nothing, merge or rebalance.

### Long-paragraph test

Identify the topology and governing task. If neither can be named, inspect for chain drift or missing boundaries.

### Genre/mode test

Do not condemn a paragraph for violating realist defaults if the passage is intentionally operating in another grammar. Verify that the alternative grammar supplies its own cohesion.

## 19. Deterministic diagnostics

Use `scripts/paragraph_profile.py` only as an advisory structural profile. It may report:

- paragraph count;
- character and sentence-length distributions;
- one-sentence paragraph rate;
- consecutive short-paragraph runs;
- very long local outliers;
- dialogue-looking paragraph share.

Do **not** let these metrics decide paragraph quality. A high one-sentence rate may be correct in rapid dialogue and wrong in reflective narration. A long outlier may be architecturally excellent or badly drifted.

Use the profile to choose passages for human/Agent semantic audit, not to optimize toward a target number.

## 20. Routing

- Sentence diction, explanation echo, and surface AI patterns -> `prose-standard.md`.
- Dialogue ownership, subtext, turn-taking, register -> `dialogue-character-voice.md`.
- Descriptive attention path and spatial re-entry -> `environment-description.md`.
- Story-time compression/expansion -> `narrative-time-duration.md`.
- Chapter/scene dramatic state -> `scene-architecture.md`.
- Expectation pulse and event weight -> `rhythm-propulsion.md`.
- Reader memory and dormant-thread reactivation -> `reader-model.md`.
- POV/camera permission -> `focalization-narrator.md`.
- World/place change during long absences -> `world-evolution-social-ecology.md`.
- Long-horizon recurrence and arc inheritance -> `long-horizon-architecture.md`.

Do not turn these paragraph grammars into named-author imitation. Use them as transferable structural models.
