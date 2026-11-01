# Chinese Narrative Behavioral Evaluation

## Raw prose to state and revision evaluation

Core comprehension uses the existing reconciliation/semantic-revision workflows, not a new writing-rule framework. `assets/regression-corpora/prose-state-semantics/cases.jsonl` contains 16 original, provisional seed tasks: literal reading vs hearsay, known lies vs unverified speech, conjecture, metaphor, counterfactual, misidentification, failed transfer, quiet custody, in-scene reversal, intention, negation scope, seen-object vs read-content, free indirect certainty, and a multi-chapter revision with independent support and an unindexed dependency.

Use the existing Chinese evaluation backend:

```bash
python scripts/storyctl.py chinese-eval build-state-blind --out GENERATOR_PACKET.jsonl --key-out EVALUATOR_KEY.jsonl
python scripts/storyctl.py chinese-eval score-state RESPONSES.jsonl EVALUATOR_KEY.jsonl
```

Send only the generator packet and the active Skill/workflow to the evaluated model. The key contains provisional gold and must remain outside its context. Record model/version/settings, actual raw responses and reviewer paraphrase alignment. Do not silently supply the gold-derived target names, manufacture responses from the key, or report a schema/oracle roundtrip as comprehension performance. A separate reviewer can align synonymous targets before scoring; keep both the raw output and alignment record. The scorer's exact target/value match is deliberately conservative and does not judge free-text semantic equivalence by itself.

Responses contain `case_id` and three arrays: `claims` (salient durable exit-state claims, with the listed semantic fields), `state_findings` (`pointer`, `status`, using `unsupported` or `omitted` for these tasks), and `impacts` (`node`, `status`). Each item supplies `evidence` entries with source name, inclusive 1-based lines and an exact whole-line quote. The revision task requests impacts only; the other tasks request claims and state findings. Claims with no net change or only figurative/hypothetical content need not become durable entries; actual false beliefs may. Use the input's entry-state scope and explain contested annotations independently rather than forcing a match to a disputed oracle.

Report precision/recall/F1 separately for grounded extraction, unsupported/omitted state, and revision impacts. Wrong types count as false positives plus false negatives; correct labels with forged or unrelated evidence do not count as correct; missing hard cases remain in the denominator. Inspect results by semantic category, including empty-delta negative controls, and review repair validity independently. Add user-authorized, rights-cleared longer chapters and externally maintained holdouts before claiming real-world accuracy; these packaged original seeds are not human-consensus or representative long-form evidence. Private holdouts remain external. The deterministic integration test injects missing custody, overlooked unsupported state, missing unindexed impact, forged quotation and unrelated authentic evidence to verify the harness itself.

Use this reference only for Skill maintenance, Chinese-prose evaluation, corpus construction, or deliberately instrumented long-form evaluation. Do not load its gold examples during ordinary drafting.

## Contents

- Mission and non-goals
- Canonical unit: contrast family
- Three evaluation scales
- Orthogonal taxonomy
- Evidence classes
- Test modes
- Contrast construction protocol
- Anti-heuristic reversal protocol
- Context and condition control
- Rights-clean corpus policy
- Annotation and adjudication
- Blindness and leakage control
- Corpus splits and release policy
- Failure-derived corpus growth
- Scoring and reporting
- Longitudinal integration
- Promotion gates
- Deterministic tooling
- Seed-suite status
- Research baseline

## 1. Mission

Build an example-grounded behavioral specification for **native, natural, narratively effective Chinese long-form prose**.

The target is not a collection of admired quotations. The target is a growing set of controlled contrasts that can answer concrete questions such as:

- when a Chinese narrative subject may remain zero and when a competing referent requires reinstatement;
- when `不 + verb` expresses habit, refusal, rule, future/conditional negation, or stance, and when bounded event non-occurrence is more naturally realized with `没/没有 + verb`;
- whether aspect, result, direction, `把/被`, `的/地/得`, idiom slots, sentence-final particles, and discourse connectives fit the intended event and register;
- whether a passage is grammatical yet translation-shaped, over-explicit, over-connected, over-explained, rhythmically fragmented, figuratively generic, or speaker-homogenized;
- whether a local repair preserves meaning, character voice, focalization, and surrounding rhythm;
- whether a model that can recognize a better form also avoids the failure during free generation;
- whether character and narrator voices remain distinct and causally evolving across many chapters rather than flattening toward one model-wide style.

Treat this system as **behavioral evaluation**, not a universal theory of literary quality.

## 2. Non-goals

Do not use this suite to:

- rank authors, genres, dialects, or literary movements by one normative standard;
- declare every marked construction ungrammatical;
- ban a lexical item or syntactic frame merely because models overuse it;
- reduce Chinese prose to frequency thresholds;
- train the drafting Agent to memorize a visible gold answer set;
- convert subjective preference into a fake high-precision literary score;
- copy copyrighted novel sentences into the corpus as benchmark items;
- replace `chinese-grammar-idiom.md`, `dialogue-character-voice.md`, `paragraph-architecture.md`, `figurative-language.md`, or other craft owners.

The suite measures specified behaviors under specified conditions. It must preserve legitimate stylistic variation.

## 3. Canonical unit: contrast family

The canonical unit is a **contrast family**, not an isolated good/bad pair.

A family groups controlled variants that test one underlying mechanism while resisting a simplistic heuristic.

A mature family should usually contain:

1. **anchor** - the target distinction in a representative context;
2. **reversal** - a nearby context in which the apparent shortcut reverses or no longer applies;
3. **boundary** - a marked/register-sensitive case, genuine ambiguity, or edge condition when useful;
4. optional **interference** - add a competing referent, discourse shift, POV change, pressure condition, or other confound;
5. optional **distributional** - repeat or spread the construction across a window to test density rather than one occurrence;
6. optional **longitudinal** - compare separated chapters/checkpoints when the phenomenon is inherently temporal.

Example principle:

- anchor: bounded non-occurrence may prefer `没有解释` over a clipped `不解释` tail;
- reversal: deliberate refusal or standing policy may naturally prefer `不解释`;
- boundary: rhythmic parallelism may license a marked compressed form.

A family therefore specifies a **decision boundary**, not a slogan such as `不 + verb = bad`.

## 4. Three evaluation scales

### 4.1 Local contrast

Typical scope: token, phrase, clause, sentence, or 2-4 sentence micro-context.

Use for:

- reference and zero anaphora;
- aspect/event packaging;
- negation;
- result/directional complements;
- `把/被`;
- `的/地/得`;
- idiom meaning, slot, target, and evaluative color;
- particle and connective function;
- punctuation when it exposes or conceals syntax.

Local tests should minimize uncontrolled changes while preserving enough context for a valid Chinese judgment.

### 4.2 Distributional contrast

Typical scope: paragraph, multi-paragraph window, or dialogue exchange.

Use when the failure is caused by **density, recurrence, symmetry, or interaction**, not one occurrence.

Examples:

- corrective-negation frames become mechanical only after repeated reuse;
- explicit connectives may be individually legal but collectively over-mark discourse relations;
- one metaphor may be apt while one metaphor per emotional beat becomes compulsive;
- sentence-initial pronouns may be locally acceptable but produce translation-shaped reference management at passage scale;
- short paragraphs may be justified locally but become metronomic fragmentation across a scene;
- several characters may each speak plausibly yet converge toward one shared model voice.

Never infer a distributional failure from a single token count alone.

### 4.3 Longitudinal contrast

Typical scope: separated chapters, arc checkpoints, or campaign intervals.

Use for:

- narrator voice drift;
- character-voice convergence;
- flattening of lexical, figurative, syntactic, or interactional variation;
- stable overuse of one connective, contrast, explanation, or metaphor template;
- evolution that should change for story reasons but remains frozen;
- identity traits that should remain stable but drift without causal support.

Integrate these tests with `live-campaign-longitudinal-evaluation.md` and `voice_drift.py`. Longitudinal evaluation must distinguish **earned character change** from accidental model drift; consistency does not mean immobility.

## 5. Orthogonal taxonomy

Do not encode the corpus as one deep tree. Store independent axes so new phenomena can be added without schema migration.

### 5.1 Phenomenon tags

Recommended top-level tags include:

- `referential-economy`
- `zero-anaphora`
- `referent-competition`
- `topic-chain`
- `event-negation`
- `aspect-event-packaging`
- `result-directional-complement`
- `function-word-construction`
- `de-di-de`
- `ba-bei-construction`
- `idiom-construction-fit`
- `information-structure`
- `discourse-linking`
- `sentence-final-particle`
- `native-idiomaticity`
- `translationese`
- `sentence-rhythm`
- `paragraph-architecture`
- `figurative-language`
- `dialogue-voice`
- `register-fit`
- `focalization`
- `explanation-density`
- `formulaic-llm-prose`
- `scene-kinetics`
- `longitudinal-voice-drift`

These tags are extensible. Do not create a schema version solely because a new phenomenon tag is needed.

### 5.2 Scope

Use one of:

- `token`
- `phrase`
- `clause`
- `sentence`
- `micro_context`
- `paragraph`
- `multi_paragraph`
- `multi_speaker`
- `scene_window`
- `longitudinal`

### 5.3 Judgment dimensions

A family may test one or more dimensions:

- `grammaticality`
- `idiomaticity`
- `clarity`
- `narrative_naturalness`
- `register_fit`
- `character_fit`
- `focalization_legality`
- `rhythm`
- `information_structure`
- `preservation`
- `distributional_restraint`
- `longitudinal_coherence`

Do not collapse these into a generic `quality` label.

### 5.4 Provenance class

Use:

- `handcrafted`
- `failure_derived`
- `dynamic_challenge`
- `research_inspired_original`

External literature may motivate a phenomenon. Benchmark wording must remain original unless the source license and project policy explicitly permit inclusion.

## 6. Evidence classes

Every gold judgment has an evidence class.

### `hard_constraint`

Use only for robust grammatical, logical, referential, access, or construction constraints where stylistic preference is not the primary issue.

### `strong_preference`

Use when blinded native annotators show stable preference under the specified context but the losing form is not necessarily ungrammatical.

### `context_conditioned`

Use when the result depends materially on narrator, speaker, register, genre, discourse state, historical setting, or another declared condition.

### `genuine_disagreement`

Use when competent readers remain meaningfully divided after context is clear. Preserve the case as evidence about a stylistic boundary rather than forcing a winner.

Never promote `seed_expert_provisional` material to strong gold merely because it is included in this Skill.

## 7. Test modes

The same family may support several modes. Report them separately.

### Recognition

Show a controlled A/B contrast. Ask which better satisfies the specified criterion under the supplied context.

### Diagnosis

Ask what mechanism distinguishes the candidates. Diagnosis accuracy must not substitute for production behavior.

### Minimal repair

Give the problematic form and require the smallest repair that fixes the target defect while preserving unrelated content.

### Controlled production

Give context, semantic requirements, and constraints without candidate wording. Test whether the model spontaneously realizes the behavior.

### Preservation

Provide an edit request targeting one dimension and test whether the model preserves:

- propositional meaning;
- character voice;
- POV access;
- temporal relation;
- social strategy;
- surrounding rhythm;
- any declared invariant.

A model may recognize a distinction while failing to produce or preserve it. Never merge these modes into one score.

## 8. Contrast construction protocol

For each new family:

1. identify one concrete failure mechanism;
2. state the intended semantic/narrative invariant;
3. choose the smallest context that makes the judgment valid;
4. alter only the target variable where feasible;
5. write an anchor contrast;
6. create at least one reversal or boundary case to defeat a cheap heuristic;
7. add interference or distributional variants when the mechanism depends on referent competition, repetition, pressure, or discourse history;
8. inspect both candidates for accidental lexical-quality differences;
9. verify that candidate length, vividness, specificity, and politeness do not trivially reveal the expected answer unless one of those is the tested variable;
10. record why the expected relation holds **under these conditions**;
11. send the item through blinded native annotation before treating it as promotion-grade evidence.

Prefer minimal changes, but do not sacrifice ecological validity merely to equalize token count.

## 9. Anti-heuristic reversal protocol

A benchmark is unsafe when a model can pass by learning the benchmark's editing habit.

For every recurring rule-like phenomenon, actively search for a countercondition.

Examples:

- `没有 + verb` may fit bounded non-occurrence; `不 + verb` may fit refusal, habit, policy, or future/conditional negation.
- zero subjects may improve a stable topic chain; explicit names/pronouns may become necessary after a competing antecedent or discourse reset.
- removing connectives may reduce over-marking; a genuine contrast, concession, or inferential jump may require one.
- reducing sentence-final particles may remove decorative speechiness; character-specific interactional particles may be essential to stance.
- cutting explanation may improve negative space; a causally obscure action may require explicit grounding.
- combining short sentences may restore flow; panic, impact, or deliberate rhetorical fracture may justify short units.

A family that lacks a plausible anti-heuristic check is incomplete unless the phenomenon is a true hard constraint.

## 10. Context and condition control

Store the conditions needed to make the judgment reproducible.

Relevant fields may include:

- narration mode and person;
- focalizer;
- speaker identity/profile;
- relationship and power asymmetry;
- emotional/physiological pressure;
- genre/register;
- historical period;
- preceding referents;
- discourse topic;
- intended event structure;
- whether marked style is licensed;
- whether the passage is narrator prose, dialogue, embedded text, quotation, note, or intentionally nonstandard writing.

Do not label a construction globally when the real judgment is conditional.

## 11. Rights-clean corpus policy

The preferred benchmark text policy is **original-from-scratch**.

Use external fiction, linguistic studies, dictionaries, learner/native error corpora, and model failures to discover phenomena, not as a source of copied benchmark prose.

For packaged corpus items:

- write fresh micro-scenes and dialogue;
- do not preserve distinctive sentences from copyrighted fiction;
- do not perform near-synonym paraphrase of a source sentence merely to evade copying;
- record provenance class and rights status;
- if an item is failure-derived, remove project-private names/facts and rewrite it into a generic original case;
- keep any source citation in research notes rather than embedding source text;
- require `rights.text_origin = original` for distributable seed/dev assets unless an explicit compatible license is recorded.

Private user prose may generate a failure mechanism, but must not enter a reusable corpus without permission and de-identification.

## 12. Annotation and adjudication

### 12.1 Blind presentation

Randomize A/B order. Do not show:

- expected preference;
- rule name when it gives away the answer;
- rationale;
- source failure;
- Skill implementation notes.

Use `scripts/chinese_narrative_eval.py build-blind` to produce a participant packet and a separate key.

### 12.2 Native annotation

For promotion-grade soft judgments, prefer multiple competent native Chinese readers. Collect:

- choice: `A`, `B`, `tie`, or `context_dependent`;
- strength: `weak`, `moderate`, or `strong` when a directional choice is made;
- judgment dimensions actually used;
- optional concise rationale;
- flags for unclear context, both bad, both good, or suspected confound.

### 12.3 Preserve disagreement

Do not delete low-agreement items automatically.

Route them into one of:

- revise-context;
- genuine-disagreement;
- register-split;
- dialect/era split;
- retire-because-confounded.

Majority vote is not a magic truth function for literary preference.

### 12.4 Adjudication

Adjudication may establish a promotion-grade label only after inspecting:

- raw vote distribution;
- annotator rationales;
- context sufficiency;
- reversal consistency;
- accidental lexical or length cues;
- whether the family is testing the intended mechanism.

Keep raw annotations even after adjudication.

## 13. Blindness and leakage control

Gold answers must not be visible to the generation context being evaluated.

Separate three roles/artifacts:

1. **generator packet** - context/task/candidates only;
2. **key/gold store** - expected relation, rationale, family metadata;
3. **evaluator/aggregator** - reads responses only after generation completes.

If the runtime provides fresh contexts or native subagents, isolate Generator from Gold/Evaluator using `single-agent-isolation.md` and `multi-agent-orchestration.md`.

If true isolation is unavailable:

- build the blind packet before loading gold;
- do not claim evaluator independence;
- label the run `nonblind` or `soft-isolation`;
- do not use that run as sole promotion evidence.

A Skill that has memorized its own visible dev answers is not evidence of generalization.

## 14. Corpus splits and release policy

Use family-level splits so variants from one family cannot leak across development and holdout.

Recommended layers:

- `example` - tiny documentation-only examples;
- `dev` - visible maintenance/regression corpus;
- `challenge` - rotating difficult items, optionally released later;
- `private_holdout` - external to the packaged Skill and never committed under `assets/`.

Do not package private holdout text, keys, hashes that reveal answer identity, or hidden annotations.

When releasing public assets, split by **family**, not individual variant, to prevent anchor/reversal leakage.

## 15. Failure-derived corpus growth

Convert recurring real failures into durable evaluation assets through this pipeline:

```text
real model/Skill failure
    -> mechanism identification
    -> permission/de-identification check
    -> original rewrite
    -> minimalization
    -> anchor contrast
    -> reversal/boundary construction
    -> blind annotation
    -> adjudication
    -> dev/challenge corpus
    -> regression linkage
```

Coordinate with `failure-corpus-mutation-testing.md`:

- the failure corpus owns historical incidents and semantic fault-injection memory;
- this module owns Chinese narrative behavioral contrasts and annotation evidence;
- link records by stable IDs when one incident yields one or more contrast families;
- do not duplicate the original private prose inside both systems.

## 16. Scoring and reporting

Never emit one universal `Chinese Literary Quality` score.

Report profiles by:

- phenomenon;
- scope;
- judgment dimension;
- test mode;
- evidence class;
- provenance class;
- family role (`anchor`, `reversal`, `boundary`, etc.).

Useful measurements include:

- categorical agreement on adjudicated items;
- anchor accuracy;
- reversal accuracy;
- **family-complete success**: all required variants in one family behave correctly;
- recognition-to-production gap;
- repair success with preservation failures reported separately;
- human agreement distribution;
- number of genuine-disagreement cases;
- longitudinal drift/change profiles.

Do not hide a reversal collapse behind high aggregate anchor accuracy.

When comparing Skill versions, preserve the same blind packets where possible and report paired wins/losses plus behavior-profile changes.

## 17. Longitudinal integration

For live long-form projects, local competence and long-term behavior are separate claims.

At registered checkpoints, optionally capture:

- pronoun/name reinstatement profile;
- connective density and function sample;
- corrective-negation frame density;
- paragraph-length distribution;
- figurative source-domain reuse;
- narrator and character voice samples;
- dialogue interactional markers;
- explanation-after-action density;
- character-specific change expected from story events.

Use deterministic tools only as locators or measurements. A count is not itself a prose verdict.

Compare trajectories across checkpoints and record major Skill/tooling changes so apparent improvement is not misattributed to long-term memory.

## 18. Promotion gates

A change to Chinese prose policy should not be promoted merely because it sounds plausible.

For changes that materially affect Chinese prose behavior:

1. run relevant deterministic validators;
2. run the seed/dev contrast families for affected phenomena;
3. inspect anchor and reversal separately;
4. run preservation cases if the change rewrites prose;
5. sample free production, not recognition only;
6. inspect at least one human-reviewed subset for consequential changes;
7. run relevant legacy `evaluation-corpus.md` prompts;
8. if the change came from a real defect, link or add a failure record;
9. do not claim holdout improvement unless an external private holdout was actually used under blind conditions.

A regression that improves one heuristic while breaking its reversal blocks promotion.

### Multi-regime long-form qualification

Use `storyctl narrative-regime-qualification validate|selftest` for schema, control, known-mutant, real scoped-context propagation and conditional-readiness checks. The existing Multi-Poetics Behavioural Oracle supports `--stage planning|chapter|drafting` before its subcommand, with stage-specific inputs/contracts and the same pointwise, calibrated swapped-pairwise, uncertainty-aware aggregation. No stage selector defaults to preservation revision. Planning generators see the brief, not the expected poetics; gold controls and wrong mutants remain outside generation packets. Judges see the project contract and task, never literary prestige labels.

The manifest registers original social-status, associative-memory, atmospheric-relationship, metaphysical-contestation, open-atmospheric, three-case series and procedural reverse-control fixtures; confession, obsession, fair-clue and action reuse existing fixture owners. Planning and chapter controls test explicit volume inheritance; drafting controls are non-unique calibration specimens, not model outputs. `selftest` is harness evidence only. Promotion requires actual generated candidates and independent judges at every stage, with model, reasoning effort, Skill/corpus hashes, judge config and date recorded. Unrun or disputed stages keep the upgrade PROVISIONAL.

## 19. Deterministic tooling

Use `scripts/chinese_narrative_eval.py` through `scripts/storyctl.py chinese-eval`.

Supported operations:

- `validate` - validate corpus structure, family IDs, variant roles, rights/provenance fields, split discipline, and packaged-holdout prohibition;
- `build-blind` - create a generator-visible packet plus a separate answer key, with deterministic A/B swapping;
- `score` - compare model choices against a key and emit a behavior profile rather than a literary total score;
- `aggregate-annotations` - summarize blinded human annotation votes, agreement, and adjudication candidates without overwriting gold automatically.

The script is deterministic infrastructure. It is not a literary judge.

## 20. Seed-suite status

`assets/chinese-narrative-eval/seed-families.jsonl` is an **executable specification and provisional seed**, not a human-consensus benchmark.

Its purposes are to:

- prove the schema and tooling;
- demonstrate anchor/reversal/boundary design;
- provide maintenance smoke tests;
- seed future native-speaker annotation;
- show how to encode distributional and character-sensitive cases.

Do not cite seed accuracy as evidence that one model or Skill version is better at Chinese literature.

Promotion-grade corpus growth requires blind human annotation and, where appropriate, adjudication.

## 21. Research baseline

This protocol adapts several established evaluation ideas conservatively. Canonical bibliographic metadata and publication status live in the Skill-wide External Research Ledger; the links below are stable source IDs, not duplicate citation records.

- [research:zholimp-2026] - controlled Chinese minimal pairs motivate tightly scoped linguistic contrasts and context-sensitive reversal cases.
- [research:contrast-sets-2020] - small meaningful perturbations motivate local decision-boundary and contrast-family testing.
- [research:checklist-2020] - capability-by-test-type behavioral evaluation motivates diagnostic profiles rather than one aggregate prose-quality score.
- [research:native-cgec-2022] - native-speaker error distributions motivate ecologically valid Chinese failure data.
- [research:litbench-2026] - creative-writing judge limitations motivate human calibration and bounded automated literary claims.
- [research:temporal-flattening-2026] - longitudinal drift findings motivate separate long-form trajectory/evolution evaluation.

Do not copy another benchmark's score or ontology wholesale. Translate only methods that preserve the specific target: natural Chinese long-form narrative behavior.
