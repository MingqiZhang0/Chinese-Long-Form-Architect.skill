# Reality Grounding Research and Evidence Dossiers

Use this reference when fiction materially depends on real-world facts, places, objects, animals, customs, professions, institutions, law, history, ecology, science, technology, infrastructure, or daily-life practice. It owns **external evidence, provenance, triangulation, scope control, and fact-to-fiction translation**.

## Contents

- Core rule
- Research Layer
- Evidence roles
- Provenance and triangulation
- Dossier workflow
- Fact-to-fiction translation
- Scope and staleness
- Research stopping rule
- Live maintenance
- Failure modes
- Research and Project Poetics

## 1. Core rule

Research reality before locking any consequential detail whose plausibility depends on the real world.

Prefer direct or primary evidence when it actually answers the claim, but do not treat the label **primary** as a guarantee of truth. A witness can misremember, an official procedure can differ from lived practice, and a manufacturer manual describes intended operation rather than every real use. Match the evidence type to the claim, preserve provenance, and triangulate consequential facts when no uniquely authoritative source exists.

If verification is unavailable, do one of four things:

- mark the claim **unverified**;
- generalize it;
- fictionalize it explicitly;
- leave it open.

Do not invent specificity merely because it sounds realistic.

## 2. Research Layer

For a serious new long-form project, create a reality-research index whenever the premise has material real-world dependencies. The research layer precedes or runs alongside **Base Readiness and whichever optional planning artifacts are activated by causal risk or Project Poetics** in `prewriting-readiness.md`. Research need must not force unrelated planning bureaucracy.

Recommended workspace:

```text
research/
  00-reality-research-index.md
  source-ledger.md
  locations/
  objects/
  animals-ecology/
  customs-culture/
  professions-institutions/
  history-daily-life/
  science-technology/
```

Create only the folders and dossiers the project actually needs. Use the reusable templates in `assets/research-templates/` instead of rebuilding dossier schemas in every project.

The research index should track:

- research ID and question;
- why the story needs it;
- affected arcs / chapters / scenes;
- status: `open / sufficient / contested / stale / superseded`;
- dossier path;
- important uncertainty;
- recheck trigger.

## 3. Evidence roles

Use a **claim-specific evidence hierarchy**.

### Direct material or documentary evidence

Best for what existed, looked like, measured, sounded like, was recorded, or was physically used.

Examples: original maps, plans, schedules, catalogs, inventories, photographs, recordings, letters, diaries, logs, court records, museum objects, field notes, specimen records, contemporaneous statistics, engineering drawings.

Typical limitation: narrow viewpoint, missing context, selection bias, creator motive, local exception.

### Operational primary or authoritative sources

Best for formal specification, jurisdiction, official process, intended operation, naming, and current or dated administrative facts.

Examples: statutes, regulations, agency procedures, manuals, service documents, technical standards, official maps/GIS, institutional protocols.

Typical limitation: formal rule may differ from practice; current material may not fit the story date.

### First-person / participant evidence

Best for lived experience, tacit practice, workarounds, rhythm, slang, embarrassment, habit, and social meaning.

Examples: interviews, oral histories, memoirs, diaries, practitioner accounts, ethnographic field notes.

Typical limitation: memory, self-presentation, individual variation, retrospective interpretation.

### Scholarly secondary evidence

Best for context, comparison, disagreement, historical change, causal interpretation, and variation across cases.

Typical limitation: may abstract away exactly the material details fiction needs.

### Reputable tertiary / discovery sources

Use for vocabulary, dates, spellings, candidate sources, and search leads. Do not let snippets, anonymous reposts, SEO summaries, or model-generated text become the sole evidence for consequential claims when stronger sources are available.

## 4. Provenance and triangulation

Use `assets/research-templates/source-ledger-template.md`. This is a **project-specific evidence ledger** for facts that constrain one fiction project; it is separate from the Skill-maintenance bibliography in `external-research-ledger.md`. Do not merge project historical/scientific sources into the Skill-wide research registry unless they independently become evidence for Skill architecture or evaluation methodology.

For every source that materially supports architecture or prose, preserve enough information to recover and reassess it:

- source ID;
- creator / institution;
- source type and evidence role;
- original date and publication/upload date when different;
- place / community / jurisdiction;
- stable locator;
- access date when web-based;
- exact claim supported;
- scope limits and likely bias;
- confidence;
- lineage and conflicts with other sources.

For consequential facts, prefer at least one **independent** cross-check unless the record is uniquely authoritative for the claim. Ten sites repeating one original account are one evidential lineage, not ten confirmations.

When sources disagree, first test whether they actually describe different:

- dates;
- places;
- communities;
- models / versions;
- seasons;
- institutions;
- social positions;
- formal rules versus lived practice.

Preserve real variation instead of averaging it away.

## 5. Dossier workflow

Every dossier should answer a story question rather than collect links.

Use the matching file in `assets/research-templates/`:

- `assets/research-templates/location-dossier-template.md`;
- `assets/research-templates/object-dossier-template.md`;
- `assets/research-templates/animal-dossier-template.md`;
- `assets/research-templates/custom-dossier-template.md`;
- `assets/research-templates/profession-institution-dossier-template.md`;
- `assets/research-templates/theme-domain-dossier-template.md`;
- `assets/research-templates/topic-dossier-template.md` for anything else.

Regardless of category, every useful dossier should separate:

1. **story need**;
2. **research questions**;
3. **source evidence**;
4. **established facts**;
5. **variation / uncertainty**;
6. **material or lived observations**;
7. **affordances / constraints**;
8. **common misconceptions**;
9. **story consequences**;
10. **intentional fictional deviations**;
11. **canon adoption**;
12. **recheck triggers**.

Do not paste long source excerpts. Summarize evidence and keep locators.

## 6. Fact-to-fiction translation

Keep four layers distinct:

1. **Evidence layer** - what the sources actually support.
2. **Project fact layer** - what the fictional world adopts, composites, or deliberately changes.
3. **Scene relevance layer** - what matters to this specific action, place, season, person, or problem.
4. **Prose layer** - what the focalizer would actually notice, know, name, or care about.

Research density must exceed prose density.

A dossier may establish fifty facts so that the scene can safely use two. Do not reward research effort by dumping it into the chapter.

When the project intentionally departs from reality:

- label the deviation;
- state why it exists;
- propagate the altered rule consistently;
- stop citing the real constraint as if the fictional version still obeyed it.

## 7. Scope and staleness

Every factual claim that can vary should carry the smallest useful scope:

- date / period;
- place / jurisdiction;
- community / population;
- model / version;
- season / weather regime;
- role / rank / institution;
- source perspective.

Do not silently generalize one village, family, sect, cohort, office, model year, or personal account into a universal rule.

A dossier becomes **stale** when a changed story assumption falls outside its scope. Common recheck triggers include:

- story date changes;
- season or time-of-day changes;
- location or route changes;
- model / generation / equipment changes;
- law or institutional regime changes;
- different community or social group;
- different species population or ecological condition;
- evidence conflict discovered later.

Scene Packets should record material research dependencies whose scope can invalidate action or description. `spatiotemporal-scene-state.md` owns packet state; this file owns the evidence behind the dependency.

## 8. Research stopping rule

Stop when further research is unlikely to change any material:

- action possibility;
- timing;
- location / access;
- sensory or material behavior;
- institutional procedure;
- cultural credibility;
- character behavior;
- plot constraint;
- scene description.

Do not research an entire country, century, profession, species family, or technology stack because one remote detail may someday appear.

Research **the causal cone**.

## 9. Live maintenance

Research dossiers are live documents.

When drafting or revision introduces a new material dependency:

1. add it to the research index;
2. create or extend the relevant dossier;
3. verify scope before dependent prose is locked;
4. record any adopted project fact or deliberate deviation;
5. mark downstream scenes that depend on it;
6. recheck when a trigger fires.

Do not overwrite historical source findings simply because the project later chooses a fictional deviation. Preserve evidence and project choice separately.

## 10. Failure modes

Watch especially for:

- realism-flavored invention with no recoverable evidence;
- one-source certainty;
- false triangulation through copied sources;
- present-day facts leaking into historical settings;
- official rule treated as complete lived practice;
- local custom generalized to an entire culture;
- researched specifications dumped into prose;
- silent fictional deviation;
- stale dossier scope reused after date/place/model/community changes;
- research that delays drafting without protecting any near-term causal decision.

Use `regression-tests.md` for the compact diagnostic catalog.

## 11. Research and Project Poetics

Research can constrain what is factually possible without dictating one literary realization. Keep three records distinct:

- **evidence** - what external sources support;
- **fictional adoption/deviation** - what the project makes true;
- **poetic use** - how much of that material receives attention, explanation, sensory presence, ambiguity, or background status.

Do not infer that a well-researched object, institution, place, or practice deserves foreground prose merely because research effort was spent on it. Conversely, a Project Poetics that foregrounds material/social life may legitimately make researched ordinary practice a primary salience source rather than plot setup.

## 12. Historical applicability and experience boundary

A true external fact is not automatically applicable to the story period, adopted fictional canon, actor knowledge or firsthand memory. Before consequential adoption, record the fact in the existing project research dependency/source ledger with `fact_id`/`id`, `source_scope: REAL_WORLD`, `valid_from`, optional inclusive `valid_to`, `story_window`, `precision`, provenance, and experience eligibility when used as direct memory. New consequential entries marked `temporal_epistemic_version: 1.0.0` require identity, scope, precision, provenance and decidable applicability. The Skill-wide methodological bibliography is separate and unchanged.

`applies_to_story_window` is a claim cross-checked against dates; it is not an override. `research_freshness.py` derives APPLICABLE only for full containment, INAPPLICABLE for disjoint periods, and UNKNOWN for missing validity, incompatible axes or partial overlap. Narrow a broad window to the relevant scene when necessary. Manual historical/regional reasoning must preserve provenance and cannot override a computable date conflict. Unknown consequential applicability needs review before Writer use.

Current project `story_window` overrides the old query window for freshness. A change marks `story-window-changed`, and a now-disjoint period adds `story-window-inapplicable`; do not reuse old permission. This is research applicability only, not general derived-artifact DAG invalidation. `research_ledger.py validate-project STATE --json` is a read-only query over project `research_dependencies`, never an import into the Skill bibliography.

Legacy research remains readable with UNKNOWN applicability warnings. Missing validity or a legacy true boolean never supplies permission for new consequential use. Without any temporal window, the legacy age-based freshness API remains compatible; binding a historical window exposes unknown applicability for review. No mass migration or historical evidence rewrite.

Example: infrastructure valid from 2004 cannot appear as an operating system in 1993–1995. A historical event after an actor left a city cannot be firsthand memory; a newspaper/letter/phone/record can legitimately inform that actor later. Earlier public debate during presence remains available as direct experience. Knowledge Topology owns that acquisition/experience distinction; Kernel shares the mechanical gate.
