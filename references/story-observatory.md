# Story Observatory and Long-Run Drift Monitoring

Use this reference for large projects whose state has become too complex to inspect manually. It owns read-only dashboards, drift indicators, dependency hot spots, branch visibility, and maintenance signals. It does not decide canon or rewrite prose.

## Contents

- Observatory principle
- Dashboard families
- Reader-profile simulation
- Voice drift
- Theme/idea genealogy
- Irreversibility view
- Dependency hot spots
- Branch health
- Research freshness
- Project health / Narrative Debt
- Why Trace
- Garbage-collection report
- Tooling and limits

## 1. Observatory principle

A complex story needs observability, not just correctness.

The Observatory answers:

- what is active now;
- what has been dormant too long;
- what changed recently;
- what depends on a fragile assumption;
- which branches diverged most;
- what the reader may have forgotten;
- whether a character voice has drifted;
- which research claims are stale;
- which interpretive ideas recur across the manuscript;
- which generated artifacts are safe to archive.

All Observatory outputs are **read-only projections**.

## 2. Dashboard families

Useful views include:

- character presence and absence timeline;
- relationship-state map;
- object custody timeline;
- location/route graph;
- hidden-thread activity timeline;
- setup/clue lifecycle;
- knowledge propagation graph;
- institutional hypothesis map;
- reader-question heat map;
- research freshness table;
- humanities finding genealogy;
- dependency impact hot spots;
- canon branch tree;
- irreversibility/residue register;
- voice-drift report;
- schema/runtime compatibility status;
- invariant failures and transaction conflicts;
- Narrative Debt by severity/interest/deadline;
- blocking multi-agent objections.

Do not generate every dashboard for every chapter. Produce the smallest useful set for the current maintenance question.

## 3. Reader-profile simulation

`reader-model.md` remains the canonical owner of reader-state reasoning.

The Observatory may maintain several **heuristic reader profiles** to stress-test serialized recall. `assets/observatory-templates/reader-profiles-template.json` provides a starter registry:

- `binge` - recent chapters remain strongly activated;
- `weekly` - moderate decay between installments;
- `casual` - retains major relationships/outcomes more reliably than labels and minor clues;
- `puzzle` - actively tracks anomalies, clue wording, and competing hypotheses;
- `rereader` - knows later outcomes and tests retrospective fairness.

These are design heuristics, not psychological predictions of actual people.

For each important fact/question, track when useful:

- last activation chapter;
- salience;
- repetitions/reactivations;
- causal/emotional distinctiveness;
- current relevance.

Flag a **recall risk** when a planned payoff relies on a low-activation fact under the target profile.

Do not solve recall risk by mechanically repeating exposition. Use the reactivation ladder in `reader-model.md`.

## 4. Voice drift

`voice-architecture.md` and `dialogue-character-voice.md` own voice design. The Observatory only measures drift indicators.

For recurring speakers, compare a baseline window with a recent window using features such as:

- mean/median utterance length;
- sentence count per utterance;
- question/exclamation frequency;
- interruption/fragment tendency when available;
- directness markers when explicitly tagged;
- recurring lexical markers;
- negative-space markers (things the character almost never says);
- audience/register context.

A numerical drift flag is not proof of a writing error.

Before correcting drift, ask whether it is explained by:

- character development;
- changed relationship/power position;
- stress/fatigue;
- public vs private register;
- different focalization/transcription context.

## 5. Theme and idea genealogy

`chapter-humanities-analysis.md` owns interpretive findings.

The Observatory may connect approved or merely analyzed findings across chapters:

```text
PHI-FREEWILL
  Ch.12 -> prediction creates responsibility
  Ch.31 -> refusing to act is itself a choice
  Ch.57 -> prediction constrains perceived freedom
  Ch.102 -> character rejects access to prediction
```

Keep these distinct:

- **analysis lineage** - recurring interpretations in sidecars;
- **approved development lineage** - findings the user chose to deepen;
- **narrative canon** - what later prose actually embodies.

A recurring analysis pattern is not automatically the novel's official theme.

## 6. Irreversibility view

Summarize low-reversibility events and their remaining residue:

- deaths/permanent injury;
- public disclosures;
- destroyed infrastructure;
- legal/institutional commitments;
- irreversible knowledge transfer;
- relationship breaches with persistent residue;
- irreversible resource expenditure.

Flag suspicious resets when later state appears to erase a low-reversibility event without sufficient compensating cause.

## 7. Dependency hot spots

A node with many downstream dependents is a **high-blast-radius assumption**.

Examples:

- one power-system rule used by 40 scenes;
- a historical date controlling multiple ages and routes;
- a research claim supporting a whole institution;
- an antagonist identity supporting many clues.

Do not forbid changing such nodes. Require stronger impact review before doing so.

## 8. Branch health

For active branches show:

- parent/fork point;
- events since fork;
- entities changed relative to parent;
- conflicting projection paths;
- unresolved branch-specific discoveries;
- stale research or Scene Packets;
- mergeability status: `clean-looking / semantic-review-needed / high-conflict`.

Never call a branch safe to merge solely because no file paths conflict.

## 9. Research freshness

Reuse research scope/recheck triggers from `reality-grounding-research.md`. For machine-readable project state, use the same `scripts/research_freshness.py` evaluator as `story_ops stale-research`; the Observatory must not downgrade age-based staleness into a manual `status=stale`-only view.

Surface:

- stale dossiers;
- changed date/season/model/community assumptions;
- scenes depending on stale evidence;
- source-confidence changes;
- project facts that still cite retired/obsolete evidence.

## 10. Project health and Narrative Debt

A Project Health report is a **triage view**, not a literary score. Prefer discrete counts/statuses over fake composite percentages.

Useful signals:

- runtime/schema compatibility: `OK / migration-needed / unsupported`;
- hard invariant failures;
- unresolved transaction conflicts;
- invalidated Scene Packets;
- stale research dependencies;
- blocking multi-agent objections;
- open Narrative Debt, grouped by severity and `resolve_before`;
- debt whose **interest** is increasing because more downstream work now depends on it;
- cold but critical setups/clues;
- `must_resolve` OpenIssues approaching a decision horizon;
- `preserve_open` Issues whose multiplicity is being accidentally collapsed;
- legacy open records still awaiting semantic classification;
- unresolved semantic revision reports;
- unresolved merge plans;
- dependency hot spots;
- voice drift warnings.

Do not collapse these into a single "story health score." A project with one fatal continuity contradiction and otherwise clean metrics is not "93% healthy."

`project-state.md` owns the Narrative Debt register; the Observatory only surfaces it.

## 11. Why Trace and provenance

When the user asks "why is this true now?", "why did this scene become invalid?", or "what depends on this assumption?", produce a **Why Trace** rather than a generic explanation.

Walk provenance/dependency links upstream and downstream, for example:

```text
Current relationship distrust
<- EV-0032 evidence concealed
<- EV-0038 contradiction discovered
<- SC-017 failed confrontation
```

or:

```text
EV-021 changed
-> K-014 invalidated
-> D-031 loses its informational basis
-> SC-037 mission becomes stale
```

Distinguish:

- derivation/provenance: why an artifact/state exists;
- dependency: what would be affected if it changed;
- revision: which prior artifact/version it replaced;
- interpretation: a human/agent explanation not encoded as canonical causation.

Use `scripts/narrative_runtime.py why` when Runtime Mode has explicit dependency data. Why Trace explains recorded structure; it must not invent missing causal history.

## 12. Garbage-collection report

Garbage collection means reducing working clutter without deleting audit history.

Candidate classes:

- generated context packs older than their target draft;
- invalidated projections with newer rebuilds;
- abandoned temporary exports;
- stale local caches;
- unpromoted discovery notes marked REJECTED/RETIRED;
- archived branch scratch files after durable lineage is preserved.

Never garbage-collect:

- committed events;
- user decisions;
- published-version records;
- migrations/retcons;
- branch lineage;
- research provenance needed to justify a current project fact.

## 13. Tooling and limits

Use `scripts/story_observatory.py` for a compact read-only report from structured project state/runtime files. When `project-manifest.json` exists, prefer `--project-manifest` so canonical Story State, Runtime manifest, branch/dependency files, Narrative Debt, and revision directory are resolved from one project-level entrypoint instead of retyped by hand. It recognizes the canonical Reader Model key `reader_state.foreground_questions` (plus legacy aliases). For `--revision-reports`, a directory is searched recursively and only JSON objects matching the semantic revision-impact shape are counted; provenance registries, diff files, and unrelated JSON are ignored. If the project maintains a generated-artifact registry, `assets/observatory-templates/artifact-registry-template.json` can feed a **report-only** garbage-collection candidate section; the tool never deletes files.

Use `scripts/voice_drift.py` when attributed dialogue data is available; `assets/observatory-templates/dialogue-lines-template.jsonl` shows the expected row shape.

Tool outputs are indicators. They must not automatically:

- rewrite dialogue;
- reactivate a clue;
- deepen a theme;
- merge a branch;
- delete project files;
- change canon.

## Project Poetics observability

The Observatory may report, read-only:

- canonical project-poetics pointer and status;
- active scoped override chain;
- currently activated poetics capabilities;
- do-not-optimize constraints in the current Writer mission;
- recent approved poetics changes and downstream invalidations;
- suspected unauthorized drift or cross-project convergence.

It must not infer a new Project Poetics, score literary quality, or mutate poetics from prose statistics alone. A deviation may be authorized experiment, discovery candidate, or drift; preserve that distinction.
