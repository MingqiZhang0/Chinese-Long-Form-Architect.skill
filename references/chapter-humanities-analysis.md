# Post-Chapter Humanities and Human-Science Analysis

Use this reference when a stable draft/commit has an explicit user request or a configured milestone, diagnostic, or custom humanities-analysis trigger. Ordinary chapters do not run this pass by default.

## Contents

- Core contract
- Scheduling policy
- Scope
- Evidence discipline
- Philosophy
- History and historiography
- Psychology
- Adjacent domains
- Report schema
- User-decision gate
- Expansion protocol
- Staleness and versioning
- Idea genealogy
- Anti-overreach rules
- Audit
- Project Poetics boundary

## 1. Core contract

Treat this analysis as a **sidecar interpretive layer**, not as canon and not as an instruction to rewrite.

Do **not** run this analysis automatically after every substantial chapter. A stable chapter is an eligibility condition, not a trigger.

When a valid trigger fires:

1. close-read the written chapter or milestone span;
2. identify passages, events, choices, institutions, images, or conflicts that genuinely support a humanities/social-science reading;
3. produce a report with evidence anchors, interpretation, confidence, and possible development paths;
4. present or store the report according to the user's workflow;
5. invite development only when the user wants an interpretive decision now; otherwise leave findings nonbinding and continue;
6. until approval, do not inject those interpretations into later prose, plans, dialogue, themes, or character motivation;
7. preserve the report even when no expansion is chosen.

Analysis discovers possibilities. It does not retroactively declare authorial intent.

## 2. Scheduling policy

The project-level default is `opt_in`. If `humanities_analysis_policy` is absent, interpret it as `opt_in` for backward compatibility. Under `opt_in`, ordinary chapter completion does not create a report and does not trigger a recurring "shall I analyze this chapter?" interruption.

A report may run only from one of these trigger classes:

- **explicit request** - the user asks for humanities/human-science analysis of a chapter, scene, arc, or volume; this one-shot request is always sufficient;
- **milestone** - the project policy names a milestone such as arc end, volume end, major reveal, major institutional turn, or another user-defined boundary;
- **diagnostic** - a configured diagnostic owner raises a relevant need, such as interpretation drift, period-context risk, repeated thematic over-explanation, or a disputed character/institution reading;
- **custom** - the user deliberately configures another cadence, including an interval, named milestones, or combined triggers.

Store project-level scheduling in the Project Manifest under `humanities_analysis_policy`; `project-operability.md` owns the manifest contract. The supported modes are `opt_in`, `milestone`, `diagnostic`, and `custom`. Automatic scheduling must never infer a cadence merely because the `humanities-sidecar` subsystem exists.

For `milestone`, `diagnostic`, or `custom`, run only when the configured condition actually fires. Do not retroactively generate missing per-chapter reports merely to fill a sequence. If a diagnostic trigger would interrupt an explicit uninterrupted-drafting request, defer the report unless it protects a user-requested review goal.

## 3. Scope

Always scan for:

- philosophy / ethics / epistemology / metaphysics / political philosophy when materially present;
- history / historiography / memory / period mentality / institutional history when materially present;
- psychology / cognition / motivation / attachment / coping / identity / group psychology when materially present.

Also add only when justified:

- sociology;
- anthropology / ritual / kinship;
- economics;
- law / governance;
- religion / theology;
- media / technology / science studies;
- aesthetics / art theory;
- ecology / environmental humanities.

Do not force every chapter to contain every discipline.

## 4. Evidence discipline

Separate four layers:

1. **Textual observation** - what is explicitly or strongly implied in the chapter.
2. **Interpretation** - one plausible reading of that evidence.
3. **External framework** - a philosophical, historical, psychological, or other concept that may illuminate the reading.
4. **Development option** - how the story could deepen the issue if the user wants it.

Every interpretive item must cite a chapter anchor: scene ID, paragraph label, line range, or short passage description.

Use confidence labels such as `high`, `medium`, `low` for the interpretation, not for the chapter fact itself.

Do not present a plausible reading as the single hidden meaning of the text.

## 5. Philosophy

Look for questions rather than slogans.

Possible lenses include:

- agency and responsibility;
- identity over time;
- knowledge, uncertainty, testimony, and skepticism;
- freedom versus prediction/determination;
- moral luck;
- duty, consequence, virtue, care, loyalty;
- personhood and embodiment;
- memory and selfhood;
- power, legitimacy, authority, justice;
- meaning, absurdity, mortality, sacrifice;
- technology and human ends.

For each philosophical item, identify:

- the concrete narrative tension;
- positions embodied by different characters/institutions;
- what each position protects or sacrifices;
- counterexample already present in the chapter;
- whether the issue is latent, explicit, or already over-explained.

Never turn a philosophical reading into an authorial sermon by default.

## 6. History and historiography

Distinguish:

- **in-world history** - what this fictional society remembers, records, forgets, mythologizes, or disputes;
- **real historical grounding** - verified facts about a real period/place/institution;
- **historical analogy** - a comparison that may illuminate the fiction but is not identity.

When making a real historical claim, verify it when material and cite sources in the research/report workflow.

Avoid presentism: do not judge a past society only by assumptions unavailable to its actors. Reconstruct relevant period institutions, categories, incentives, language, and constraints before interpreting behavior.

For each historical item, ask:

- what period-specific context matters;
- whose record survives and whose does not;
- whether public memory differs from archival truth;
- whether the chapter reproduces a later myth about the past;
- whether an analogy is structural or merely decorative.

## 7. Psychology

Analyze fictional behavior as interpretation, not remote clinical diagnosis.

Useful lenses include:

- goals and appraisal;
- coping and defense;
- habit formation;
- attachment and dependency;
- shame, guilt, resentment, envy, grief;
- trauma responses where textually supported;
- cognitive dissonance;
- motivated reasoning;
- theory of mind and misreading;
- group conformity / obedience / diffusion of responsibility;
- identity threat and self-narrative;
- reinforcement and learned expectations.

Prefer formulations such as:

- "this behavior is consistent with..."
- "one plausible psychological reading is..."
- "the chapter suggests..."

Avoid assigning a psychiatric diagnosis merely from literary behavior. If the story explicitly establishes a diagnosis, treat it as canon and research its portrayal separately.

## 8. Adjacent domains

Use another discipline only when it adds explanatory power.

Examples:

- sociology for class, status, network, bureaucracy, collective behavior;
- anthropology for ritual, taboo, kinship, exchange, local categories;
- economics for incentives, scarcity, market structure, labor, externalities;
- law for procedure, authority, evidence, jurisdiction, rights;
- religion for doctrine, ritual practice, lived belief, institution;
- science/technology studies for expertise, infrastructure, risk, institutional knowledge.

Do not decorate the report with academic vocabulary that has no consequence for reading the chapter.

## 9. Report schema

Create a sidecar report such as:

`analysis/chapter-0012-humanities.md`

Use `assets/analysis-templates/chapter-humanities-report-template.md`.

Each finding gets a stable ID such as:

- `PHI-0012-01`
- `HIS-0012-01`
- `PSY-0012-01`
- `SOC-0012-01`

Recommended fields:

- domain;
- textual anchor;
- observation;
- interpretation;
- external framework / historical parallel if used;
- confidence;
- existing counterevidence;
- potential development paths;
- risk if overdeveloped;
- status.

Allowed statuses:

- `PENDING_USER_DECISION`;
- `PARKED` - preserved but inactive;
- `APPROVED_FOR_DEVELOPMENT`;
- `INTEGRATED`;
- `REJECTED_INTERPRETATION`;
- `STALE_AFTER_REVISION`.

## 10. User-decision gate

After generating the report, expose the findings when the current workflow calls for review. Ask which items should be developed only when an explicit decision is useful now; otherwise leave them `PENDING_USER_DECISION` or `PARKED` and continue.

Do not interpret silence, continued drafting, or a scheduled milestone run as approval.

If the user says "do not expand," mark the relevant findings `PARKED`. Keep them in the report; do not delete them and do not use them as future drafting instructions.

If the user rejects the reading itself, mark `REJECTED_INTERPRETATION` and exclude it from future reasoning unless re-opened.

If the user says to continue writing without deciding, leave findings `PENDING_USER_DECISION` and keep them nonbinding.

## 11. Expansion protocol

When the user approves an item:

1. record the approval in the report and project register;
2. route the item to `thematic-polyphony.md`, `character-dynamics.md`, `world-model.md`, `institutional-negotiation.md`, or another canonical owner as appropriate;
3. decide the smallest narrative carrier: consequence, choice, relationship, institution, motif, recurring situation, counterposition, or world change;
4. integrate prospectively unless the user explicitly requests revision of already-written prose;
5. preserve competing positions and counterexamples;
6. avoid lecture dialogue or narrator explanation unless the form genuinely calls for it;
7. mark `INTEGRATED` only after the idea has entered canon through actual narrative material.

Approval to develop a thought is not permission to make the novel state that thought is true.

## 12. Staleness and versioning

Tie each report to the chapter version/hash/revision ID it analyzed.

If the chapter changes materially:

- mark the old report `STALE_AFTER_REVISION` or regenerate it;
- do not keep treating deleted scenes as evidence;
- preserve the old report for history if useful.

Interpretive reports are append-only analysis history unless the user asks to clean them.

## 13. Idea genealogy

Across chapters, preserve optional lineage between related findings without promoting them to canon. A finding may record:

- parent / related finding IDs;
- recurrence or transformation type;
- whether the user approved development;
- narrative carriers later used;
- counterpositions that emerged;
- whether the idea weakened, inverted, or remained unresolved.

`story-observatory.md` may render these links as an idea genealogy. Keep three layers separate:

1. recurring analysis;
2. user-approved development intent;
3. actual narrative embodiment in canon.

Do not infer layer 3 merely from repeated analytical similarity.

## 14. Anti-overreach rules

Do not:

- find philosophy in every metaphor;
- infer author intent from one ambiguous detail;
- force a real historical analogue onto a fictional structure;
- confuse historical analogy with factual identity;
- diagnose fictional characters casually;
- treat an external theory as more authoritative than the text;
- reward abstract language over precise textual evidence;
- revise prose merely because analysis found an interesting possibility;
- make every approved idea explicit in dialogue.

## 15. Audit

Before delivering the report, ask:

- Did a valid explicit/configured trigger fire? If not, do not generate the report.
- Is every finding anchored in the actual chapter or milestone span?
- Did I separate observation from interpretation?
- Did I distinguish real history from analogy and in-world history?
- Did I avoid casual diagnosis?
- Did I include counterevidence or alternate readings where important?
- Is the report useful even if the user chooses to develop nothing?
- Will the story remain unchanged unless the user explicitly opts in?

## Project Poetics boundary

Humanities analysis may identify a possible pattern in attention, form, theme, temporality, mind opacity, atmosphere, or reader activity. This is **evidence for a proposal**, not authority to rewrite Project Poetics.

- Do not promote an interpretation into a thematic thesis or active poetics capability automatically.
- Do not infer that a critical concept should become a generation target.
- Route user-approved formal/thematic development through `project-poetics.md` and then invalidate affected Narrative Strategy/Missions/context packs as needed.
- Keep scholarly evidence type and project creative choice separate.
