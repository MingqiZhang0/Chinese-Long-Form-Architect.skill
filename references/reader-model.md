# Reader Model, Memory, and Information Load

Use this reference for long serials, dense mysteries, large casts, delayed payoffs, time jumps, braided POVs, or any story where reader comprehension can fail even though continuity is technically correct. It owns the heuristic model of a reasonable reader's questions, memory activation, and hypotheses. Reader exposure/model is not world canon and must not mutate objective truth; the cross-layer contract lives in `narrative-semantics-kernel.md`.

## Contents

- Reader state
- Event models, paragraph signals, and boundaries
- Question stack
- Hypothesis management
- Memory activation
- Reactivation methods
- Suspense, curiosity, surprise
- Orientation after cuts
- First-read and reread design
- Blind Reader Agent simulation
- Audit

## Core principle

Model the reader as a **partial, lossy, inferential, history-dependent participant**, not a mirror of canonical state and not only a stack of mystery questions.

Readers may remember gist while losing detail, form familiarity with people/places/routines, learn what dimensions a work rewards attention to, construct imperfect character models, misattribute knowledge, update expectations, and experience rereading differently.

Use reader modeling only at the resolution the current Project Poetics requires.

## 1. Reader state

Track only reader-facing state that can change later writing decisions. Useful dimensions include:

- known facts / observed evidence;
- active questions/hypotheses when relevant;
- likely gist retained vs detail that has gone cognitively cold;
- familiarity with people, places, routines, objects, registers, and recurring structures;
- character models, including plausible misreadings or knowledge misattribution;
- genre/form expectations the text has taught;
- emotional/evaluative orientation;
- currently salient patterns or recurrences;
- rereader-only knowledge when explicitly modeling rereading.

Do not treat `shown once` as `currently retrievable`, and do not treat an intended answer as reader knowledge.

## 2. Event models and boundaries

Event boundaries are one tool for understanding reader updating, not the universal source of narrativity. Quiet/recurrent projects may organize reader state through familiarity, rhythm, place, relation, or formal pattern even when major event boundaries are sparse.

Readers build situation models around characters, goals, time, place, objects, and causality. Large changes in these dimensions behave like event boundaries.

After a strong boundary such as a time jump, location change, POV change, or goal reversal:

- expect some prior details to lose immediate accessibility;
- provide enough anchors for reorientation;
- do not demand instant recall of a low-salience clue from a distant event model;
- use recurring people, objects, phrases, consequences, or procedures as retrieval cues when needed.

Boundaries can also be useful: they allow old material to cool before later reinterpretation.


### Paragraph boundaries as reader-model signals

Treat a semantic paragraph break as a cue that the reader may need to refresh or reorganize a local event model. Do not over-signal weak changes with constant breaks, and do not hide repeated strong resets unless another cohesion mechanism deliberately carries the reader across them.

For dormant material returning after long absence, prefer causally active re-entry cues over encyclopedia recap. Use `paragraph-architecture.md` for re-entry, echo-bearing, and long-memory paragraphs.

## 3. Question stack (conditional)

Use a question stack when inquiry, suspense, curiosity, secrecy, or prediction is an active project mechanism. Do not manufacture foreground questions merely because the template contains them.

Do not run every mystery at full brightness.

Classify questions as:

- **foreground** - the reader should actively think about it now;
- **warm** - recently relevant and easy to reactivate;
- **dormant** - intentionally allowed to leave working attention;
- **reactivating** - being brought back before a turn;
- **resolved** - answered enough that the narrative should not keep pretending it is open;
- **transformed** - the old question was based on a wrong frame and has become a better question.

Dense fiction can maintain many dormant questions, but only a limited number should demand simultaneous active reasoning.

## 4. Hypothesis management

For major mysteries, distinguish:

- evidence available;
- hypothesis the protagonist holds;
- hypothesis the reader is likely to hold;
- hypothesis the antagonist wants others to hold;
- actual mechanism **when authorially fixed**.

If the relevant truth is still an OpenIssue, do not label reader alternatives `correct` or `wrong` merely from authorial indecision. Use `likely / plausible / weak / alternative` until truth is fixed. The author may deliberately bias reader suspicion toward a still-uncommitted position without canonizing it; route the truth boundary through `open-issue-semantics.md`.

When the mechanism is fixed, a fair misdirection should be supported by true observations plus a plausible wrong model. Do not rely on false narration or omitted viewpoint knowledge solely to manufacture surprise.

## 5. Memory activation

For long-horizon setups, track an approximate activation state:

- **hot** - used or mentioned very recently;
- **warm** - likely still accessible with a light cue;
- **cool** - remembered only when context returns;
- **cold** - effectively unavailable without reactivation.

Salience depends on more than chapter count. Emotional intensity, repetition, novelty, causal importance, imagery, and later consequences can keep old information active.

## 6. Reactivation ladder

Before a distant payoff, prefer the lightest reminder that makes the old material usable:

1. repeated visual/material cue;
2. same phrase, name, procedure, symptom, or object behavior;
3. consequence that resembles the earlier event;
4. another character independently encountering the same pattern;
5. brief natural mention;
6. explicit recap only when clarity genuinely requires it.

Do not write reminders that exist only to tell the reader, "remember this clue."

## 7. Suspense, curiosity, and surprise

Use different information arrangements deliberately:

- **suspense** - the reader knows a consequential possibility and waits to learn the outcome;
- **curiosity** - the reader knows an outcome or anomaly and wants the missing cause;
- **surprise** - a turn violates the current model, then becomes intelligible through prior evidence.

A long arc benefits from mixing these rather than treating every chapter as suspense about "what happens next."

## 8. Reader-question movement

A revelation should often change the shape of inquiry.

Examples:

- "Who did it?" -> "Why did they need everyone to think it was them?"
- "Is she the traitor?" -> "What secret was she hiding instead?"
- "Why was the attack prevented?" -> "Why did the enemy choose not to attack?"

Do not merely answer questions; upgrade some of them.

## 9. Orientation after cuts

After a cut, quickly re-establish only what is needed:

- who;
- where;
- when relative to the last relevant event;
- immediate local objective;
- one continuity anchor if the gap is large.

Do not re-explain the whole subplot every time it returns.

## 10. First-read and reread layers

For major reveals, verify two simultaneous readings:

**First read:** the scene is coherent under the reader's current model.

**Reread:** previously ordinary details gain additional causal or psychological meaning without becoming objectively false.

Do not make every scene a puzzle. World remainder and ordinary life protect reread density from becoming mechanical clue-hunting.

## 11. Multi-profile stress test

For very long serials, the same clue may feel obvious to a binge reader and inaccessible to a weekly reader. When useful, inspect several heuristic profiles:

- **binge** - recent details remain highly activated;
- **weekly** - moderate decay between installments;
- **casual** - major outcomes/relationships persist better than labels and minor clues;
- **puzzle** - actively tracks anomalies and competing hypotheses;
- **rereader** - knows later outcomes and tests retrospective fairness.

These are design lenses, not empirical predictions of an actual audience. Use them to identify recall risk, then solve with natural reactivation rather than repetitive exposition. `story-observatory.md` owns dashboard rendering.

## 12. Blind Reader Agent simulation

When a real-readability check matters, run a **blind Reader Agent** on reader-visible material rather than asking a planner who already knows the answer.

Provide only:

- the prose actually available to the target reader by that point;
- any recap/paratext the real reader would genuinely have;
- the selected heuristic profile (`binge`, `weekly`, `casual`, `puzzle`, or `rereader`);
- the questions to answer after reading.

Do **not** provide hidden canon, future architecture, unresolved authorial answers, villain plans, dependency graphs, or explanations of what the scene was intended to achieve. For a rereader stress test, later published prose may be supplied deliberately; mark that mode explicitly.

Ask the blind reader to report, in its own terms:

- what it thinks just happened;
- current goals/conflicts;
- where and when it believes the scene occurs;
- causal links it inferred;
- questions it is actively carrying;
- people/factions/objects it cannot confidently identify;
- hypotheses it currently entertains;
- any moment that felt unfair, confusing, repetitive, or suspiciously author-driven.

Compare these reports against the intended reader-state model. Treat disagreement as diagnostic evidence, not as proof that either the text or reader is wrong. Situation-model dimensions worth checking include **time, space, protagonists/entities, causality, and intentional goals**.

`multi-agent-orchestration.md` owns the Reader Simulator role and `context-compilation.md` owns its leakage-safe context.

## 13. Reader-load audit

Reader success depends on the adopted task: reconstruct a closed case; infer a self-report/behavior mismatch without final diagnosis; learn a social field; accumulate relationship or place familiarity; remember and reinterpret; or hold textually bounded alternatives. None is a universal preference for predicting the next event. Supply the selected task through the existing Writer Reader Brief, without hidden solutions.

Ask:

- How many questions currently demand active memory?
- How many names or factions have been introduced without a durable anchor?
- Which old fact must be usable in the next payoff, and when was it last reactivated?
- Is confusion intentional, local, and recoverable, or simply bookkeeping failure?
- Did a time/POV/place boundary bury information the next scene assumes is still active?
- Is the reader being asked to remember a label when a sensory, relational, or causal cue would work better?

Historical queries use `scripts/reader_state.py` `query_reader_state` with an
explicit `NarrativePosition`; the chapter adapter supports only presentation order.
Untimed accumulated dict contents are not historical evidence. `reader_state_at`
without a position is an explicitly current-state read. Supported snapshots retain
inclusive `to_chapter`; missing history returns PARTIAL with gap reasons. See
`docs/auditability-contract.md` and `scripts/auditability_core_test.py`.
