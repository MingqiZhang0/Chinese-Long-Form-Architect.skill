# Narrative Time and Duration

Use this reference when the story feels uniformly paced, repeats routine in real time, skips consequences that needed experience, or confuses urgency with narrative speed.

## Contents

- Core principle
- Four basic duration modes
- Urgency is not narrative speed
- Narrative resolution ladder
- Temporal span versus paragraph span
- Repetition and recurrence
- Time compression must preserve causal accumulation
- Ellipsis and fairness
- Pause and descriptive time
- Time jumps
- Multi-scale pacing
- Audit
- Narrative carrier lifecycle time


## Core principle

Narrative duration controls **experienced time**, not merely the amount of objective change. Choose scene, summary, ellipsis, pause, recurrence, or dilation according to the current Project Poetics and the reader activity the interval must support.

A period of waiting, labor, habit, recovery, seasonality, perception, or formal repetition may deserve expansion despite little durable state change. A major event may be compressed when direct experience is not the point.

## 1. Four basic duration modes

### Scene
Narration approaches the duration of lived action.

Use when readers need to experience choices, uncertainty, relationship movement, physical causality, or a decisive interpretation directly.

### Summary
Compress a stretch of story time while preserving meaningful changes.

A good summary still carries state transition: habits form, pressure accumulates, training changes capability, rumors spread, relationships cool, or a routine becomes normal.

### Ellipsis
Skip story time whose internal steps can be safely inferred or do not deserve page time.

Do not ellide a causal link whose absence makes a later outcome magical, unfair, or emotionally unearned.

### Pause / dilation
Page time expands while story time barely advances.

Use for perception, inspection, memory, thought, spatial orientation, emotional aftershock, or a detail whose meaning depends on sustained attention.

Do not make pause the default whenever prose wants to sound literary.

## 2. Urgency is not narrative speed

A high-pressure situation may be narrated slowly when:

- a tiny decision matters;
- spatial causality must remain legible;
- perception narrows;
- time subjectively dilates;
- the reader must track a chain of micro-causes.

A low-pressure month may be narrated rapidly if only the accumulated result matters.

Do not automatically use short sentences and rapid cuts merely because characters are in danger.

## 3. Narrative resolution ladder

Choose the smallest resolution that preserves the intended effect.

- **omit** - nothing the reader needs happens here;
- **mention** - register passage of time or one change;
- **summary** - show a pattern and its accumulated delta;
- **selected scene** - dramatize one representative or turning instance;
- **full scene** - direct experience matters;
- **dilation** - a narrow interval deserves unusually high attention.

The same recurring event may move down this ladder as it becomes familiar, then move up again when the pattern breaks.


## 3A. Temporal span does not determine paragraph span

A semantic paragraph may cover seconds or decades. Keep it unified when one state transition, causal explanation, conceptual move, or memory task still governs the passage. Conversely, a few seconds may require several paragraphs when action programs, social control, or event models change rapidly.

Use `paragraph-architecture.md` to decide semantic boundaries; this module decides how much page time the story interval receives.

## 4. Repetition and recurrence

Repetition need not justify itself by escalating or changing every iteration. It can establish normality, habit, ritual, social familiarity, evidence, seasonal structure, memory, or formal pattern. Diagnose redundancy only after identifying what recurrence is doing in this project.

Do not dramatize every recurrence of a repeated routine, anomaly, training cycle, work shift, meeting, or argument.

Use iterative compression when several similar events establish a pattern. Return to scene when:

- the pattern first becomes legible;
- a meaningful variation appears;
- adaptation changes behavior;
- the routine itself gains emotional weight;
- a break in the pattern matters.

Repeated scene-level treatment is inert only when it supplies neither new accumulation nor a project-authorized experience. Do not require a world delta.

### Associative memory architecture

Distinguish objective chronology, reconstructed story chronology, presentation order, experienced duration, remembered time and narrating-present time. The distinction between story, discourse and narrating time is research-informed [research:lhn-time-2014]; the following memory planning procedure is Skill synthesis.

Memory need not be an informational flashback. A present sound, texture, gesture or name may activate one memory, a social association, another memory, reinterpretation, then return to a present now perceived differently. Privately retain the sensory, emotional, relational, conceptual or formal link at each transition. Do not normalize this sequence into years merely for clarity.

Repeated recollection can preserve the same fact while changing its weight under later knowledge, narrating age or relation. Separate selective reconstruction from changed fictional fact and from deliberate lying; memory alone does not establish unreliability. Chapter progression may be the organization of the past. Require enough present/past orientation for this project's reader task, without a chronology lesson or compulsory plot payoff for each memory.

## 5. Time compression must preserve causal accumulation

When summarizing days, weeks, or years, track what accumulates:

- fatigue;
- competence;
- money;
- trust;
- resentment;
- habit;
- institutional delay;
- seasonal change;
- public reputation;
- maintenance debt;
- physical recovery or decay.

Compression should not make process disappear.

## 6. Ellipsis and fairness

Safe ellipsis lets the reader infer the bridge.

Unsafe ellipsis hides:

- the decisive choice;
- the only evidence for a reveal;
- the moment a relationship fundamentally changes;
- the resource acquisition that makes a later victory possible;
- the action that would expose a contradiction.

When omitting a critical step for suspense, ensure the current focalization honestly lacks access and later evidence makes the omission fair.

## 7. Pause and descriptive time

Pair with `environment-description.md` when description slows story time.

Pause can serve:

- orientation;
- awe;
- horror;
- inspection;
- waiting;
- aftermath;
- comparison with a remembered earlier state.

Do not pause for exhaustive inventory. Attention still follows focalization, task, and meaning.

## 8. Time jumps

A time jump should alter more than the calendar.

Before and after a meaningful jump, ask:

- what changed gradually;
- what happened offscreen;
- what did not change despite pressure;
- what people now take for granted;
- what relationships or places aged independently of the protagonist;
- what old state left residue.

Use `world-evolution-social-ecology.md` and `state-inertia.md` for substantial jumps.

## 9. Multi-scale pacing

A long novel should vary duration across levels:

- a paragraph can summarize a week;
- a chapter can contain one hour;
- a volume can cover a year;
- a major five-second event can become the most detailed sequence in the book.

Do not let chapter length become a proxy for in-world time.

## Audit

- Why is this interval getting this much page time?
- What would be lost if it were summarized?
- What would be gained if it were omitted?
- Am I replaying routine without new change?
- Did compression preserve accumulated consequence?
- Did ellipsis hide something readers needed for fairness?
- Am I slowing because the moment matters, or because the prose likes itself?

## 10. Narrative carrier lifecycle time

A consequential letter, notebook, recording or digital message is a constrained temporal object as well as narrated text. The object owner is `spatiotemporal-scene-state.md`; `state-validation.md` owns deterministic checks. Creation, inscription intervals, sealing/reopening, sending, receipt and recipient opening form a **type-sensitive partial order**, not a universal letter-shaped state machine. Diaries can receive repeated entries while custody continues; recordings can have explicit later sessions; sent email instances remain distinct from editable drafts.

Use the existing P0-3 `research_freshness.temporal_order` / `temporal_bounds`: numeric common-unit times or ISO calendar dates/months/years. Month/year precision remains an uncertainty interval. Never compare incompatible axes, invent a day, or choose an order inside overlapping intervals. A consequential unresolved relation is `artifact.time_needs_review` and blocks the existing Story State / Readiness seam pending enrichment; legacy unactivated carriers only warn.

Check creation before every internal inscription interval, ordered interval endpoints, original interval end before each applicable control boundary, sending before delivery, and delivery before `opened_at` (defined here as recipient first opening). Author reopening before sending is represented by a `REOPEN` event, not recipient `opened_at`. Control boundaries include explicit `author_control_until`, sending/mailing, declared finalization and canonical author-custody cessation; `sealed_at` is deliberately absent from that list. Recovered control supports separate provenance-bearing layers, never retroactively changes the original layer.

Original recorded segments must fit the recording interval. Later recording/edit mechanisms retain separate layer identity and lawful custody/access. Narration about a later fate of the carrier uses `FRAME_EXTERNAL`, so narrative telling time does not become inscription time. Lifecycle time never creates knowledge acquisition or asserts content truth.

For an active physical carrier, recipient `opened_at` also requires a canonical custody interval covering that point; exact outgoing ends are excluded and an incoming interval beginning at that point supports access. Shared custody remains valid when its canonical row covers the opening. Digital opening uses the existing `delivered_at` → `opened_at` relation only as limited logical support; it does not claim recipient authentication or full digital forensics. Where physical seal state is explicitly represented, `sealed_at`/valid `SEAL` derive `SEALED`, supported opening/valid `REOPEN` derive `OPEN`, and a later ordered seal derives `SEALED` again. These milestones feed effective snapshots and Scene assertions, while unknown ordering stays under `artifact.time_needs_review` and sealing remains separate from author-control loss.
