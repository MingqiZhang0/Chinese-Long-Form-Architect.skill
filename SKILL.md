---
name: literary-webnovel-architect
description: Architect, continue, diagnose, and revise serious Chinese-language long-form fiction when the task materially depends on persistent multi-chapter state, durable canon, causal or knowledge continuity, long-horizon structure, downstream revision impact, or project-specific literary poetics. Use for new novel architecture, established continuation, arc/volume planning, state-sensitive chapter work, continuity repair, mystery/prophecy/counterfactual structures, and rewrites that can alter downstream canon or Project Poetics. Multilingual sources or code-switching may appear inside a Chinese-language project, but non-Chinese target-language prose parity is not claimed. Do not trigger for ordinary local prose polishing, sentence/paragraph beautification, translation, or short fiction that can be completed without persistent project state, even when the excerpt comes from a long novel. Project origin alone is not an activation signal.
---

# Chinese Long-Form Architect

## Scope and identity

The product scope is **serious Chinese-language long-form fiction**. Generic semantic/runtime infrastructure may be language-agnostic, but the packaged prose-quality rules and behavioral promotion evidence are Chinese-specific, with the current empirical baseline centered on `zh-CN`. Multilingual research, quotations, names, or code-switching may be used inside a Chinese-language project; do not claim equal native-prose support for a non-Chinese target-language novel.

Keep the technical slug `literary-webnovel-architect` as a compatibility identifier for now. Do not silently rename the directory, frontmatter name, schema IDs, or installed identity. Read `skill-scope-identity.md` for the canonical product-scope decision, the deferred `chinese-long-form-architect` migration candidate, and controlled migration/successor rules.

## Core contract

Treat a serious long-form work as a persistent project with memory. Protect **hard integrity** without forcing every project into one literary model.

Hard Core protects:

1. fixed canon and explicit user authority;
2. causal/world truth, valid-time relations, and evidence/provenance;
3. actor knowledge, belief, access, capability, authority, and risk;
4. persistent state, revision propagation, and consequence residue;
5. focalization/camera legality and information-flow boundaries;
6. authorial openness, representation migration, and traceability.

Project-specific literary choices live in **Project Poetics**, not in Hard Core. Form, rhythm, voice, selection, atmosphere, world breadth, hidden processes, polyphony, character transformation, explanation density, and suspense may be central in one project and deliberately weak or absent in another.

Maintain these invariants:

- **claim-action consistency** - consequential operational claims must not exceed authoritative execution evidence: `PLANNED -> RUNNING -> DONE -> VERIFIED`, or `FAILED` with a reason. Completion is not verification; a subagent report supports only a reported claim. Use `storyctl status PROJECT_ROOT --json` for the aggregated machine view, and the existing orchestration/checkpoint and [Auditability Contract](docs/auditability-contract.md) for evidence requirements. P0-1 decision legality remains separate from operational execution truth.

- **temporal and epistemic integrity** - truth does not imply historical applicability, actor acquisition, firsthand experience or Writer permission. Consequential Writer facts require legal acquisition coverage (K21); expression precision/basis cannot exceed source support without acquired refinement evidence (K22). Preserve legal exact evidence and qualified inference. Use `knowledge-topology.md` and `reality-grounding-research.md`; do not formalize ordinary texture or claim automatic prose extraction.

- **causal sufficiency** - high-risk hidden responsibility requires an action or deliberate omission, supported preconditions, mechanism, counterfactual role and bounded contingency matching claim strength; graph connectivity alone is insufficient. Use `hidden-causal-networks.md` and State Validation.

- **state continuity/inertia** - consequential state persists until causally changed;
- **actor credibility** - action follows information, incentives, habits, relations, authority, capability, and risk;
- **reader/camera integrity** - distinguish world truth, actor belief, reader exposure/retrievability, and narrator/focalizer permission;
- **evidence integrity** - verify real-world dependencies before they harden into architecture or prose;
- **role isolation** - research, simulation, planning, prose, audit, interpretation, and state mutation remain distinct when complexity warrants it;
- **interpretive consent** - humanities analysis is nonbinding until explicitly adopted;
- **historical traceability** - large projects preserve how canon/planning became authoritative through events, revisions, branches, provenance, and dependency-aware invalidation;
- **formalization restraint** - represent only what protects continuity, causality, access, recovery, revision impact, or an explicitly adopted project contract.
- **commit before dependency** - before research, world/chronology/case mechanics, long-horizon architecture, or Writer-safe context uses a consequential decision, resolve it under known authority and persist its value, resolver, provenance, and semantic identity in canonical Project Brief/state. Agent proposals and temporary assumptions are not committed dependencies. Resolve delegated/discretion choices autonomously, then commit before use; block only actual dependent work. See `front-loaded-adaptive-intake.md` and `project-state.md`.

Read `literary-meta-core.md` whenever diagnosis risks turning one successful technique into a universal quality rule. Read `project-poetics.md` whenever deciding what this particular project should foreground, leave backgrounded, explain, repeat, vary, or refuse to optimize.

## Mode router

Use the smallest workflow that protects the actual risk. Route by **project state + task type** first; then apply the current Project Poetics. A mode chooses workflow/governance only: it never activates a literary capability or supplies a universal aesthetic.

### New / foundational
- For a new project or foundational rebuild, resolve only still-open author intent, establish/verify the manifest, and converge the smallest risk-justified readiness set.
- Establish provisional Project Poetics without filling unchosen literary commitments. For substantial Chapter 1, formal prose requires the evidence-backed permission owned by `prewriting-readiness.md`. Optional artifacts remain conditional.

### Continue
- For an established project, load the manifest and latest canonical state; after a long hiatus or state uncertainty, regenerate the Director-facing resume before planning new prose.
- Derive the next mission from current state plus scoped Project Poetics. Do not restart architecture or re-ask settled choices unless new canon, revision impact, or explicit author intent requires it.

### Revise / diagnose
- Classify the revision axis first: prose-only, hard-semantic, Project-Poetics-affecting, or mixed. Repair the highest failing layer before polishing lower layers and propagate only the affected dependency closure.
- Treat a mere absence of another poetics' virtue as non-failure; do not use revision as a back door for aesthetic normalization.

### Micro / local
- For a contained scene, paragraph, dialogue, continuity check, or other local task, load the smallest sufficient state and active craft stack; keep full-project machinery backstage unless authority or persistent-state risk genuinely crosses the local boundary.
- Preserve known canon and current scoped Project Poetics without bootstrapping new project-wide commitments.

### Discovery
- Use Discovery Drafting only for explicitly exploratory/pantsing work or a bounded experimental branch. Preserve Fixed canon and keep discoveries provisional or typed as OpenIssues until reconciliation.
- Do not promote a discovery into canon or Project Poetics merely because it appeared in prose; route adoption through the proper canonical owner and return to the normal project workflow once the branch is accepted, rejected, or retired.

### Reasoning intensity

When `Low / Medium / High / XHigh / Max` is selected, load `reasoning-intensity.md`. Intensity allocates search/verification work; it is never canon authority, literary complexity, prose length, or an aesthetic score.

## Progressive loading

Load only references controlling the current risk. Persistent state may be broad; the active craft/poetics stack should remain selective. Roughly **4-7 active craft references** is a useful ceiling for a normal chapter, not a quota.

### Literary meta / project poetics

- Cross-poetics distinctions and anti-overcorrection: `literary-meta-core.md`.
- Project-specific salience, progression, reader activity, explanatory threshold, form visibility, do-not-optimize rules, capability activation, and scoped overrides: `project-poetics.md`.
- Non-plot-dominant work, confession, social strategy, obsession, associative memory, atmospheric relations, metaphysical openness, or episodic fair-clue series: use the organizing vocabulary and four-axis compilation in `project-poetics.md`, then load only the specialist owners it activates.

### Prose / scene craft

- Base prose/voice: `voice-architecture.md`, `prose-standard.md`; add `chinese-grammar-idiom.md` for Chinese grammar/idiom risk and `figurative-language.md` only when image/metaphor work is active.
- Paragraph/rhythm/restraint: `paragraph-architecture.md`, `rhythm-propulsion.md`, `restraint-negative-space.md`.
- Scene/selection/time: `scene-architecture.md`, `narrative-selection.md`, `narrative-time-duration.md`.
- POV/dialogue/place: `focalization-narrator.md`, `dialogue-character-voice.md`, `environment-description.md`.
- Motion/kinetics: `dynamic-vividness.md`; load `dynamic-vividness-patterns.md` only when a structural example helps.
- Institutional high-stakes negotiation: `institutional-negotiation.md` only when activated by project/chapter needs.

### Project / state / causality

- Intake/readiness/research/state: `front-loaded-adaptive-intake.md`, `prewriting-readiness.md`, `reality-grounding-research.md`, `project-state.md`, `project-operability.md`.
- Semantic/runtime correctness: `narrative-semantics-kernel.md`, `narrative-runtime.md`, `runtime-schema-migration.md`, `narrative-invariants.md`, `state-validation.md`, `formalization-boundary.md`.
- Revision/branches/open truth: `semantic-revision.md`, `prose-state-reconciliation.md`, `change-control.md`, `discovery-drafting.md`, `open-issue-semantics.md`.
- Embodied/spatiotemporal state: `embodied-resource-state.md`, `spatiotemporal-scene-state.md`, `state-inertia.md` when causally relevant.
- World/knowledge/reader: `world-model.md`, `knowledge-topology.md`, `reader-model.md` at the resolution justified by risk/poetics.
- Selectable complex-causality/social capabilities: `hidden-causal-networks.md`, `world-evolution-social-ecology.md`, `organizational-learning.md`, `social-transmission-reputation.md`, `contingency-noise.md`.
- Long-form/character/theme/endings: `long-horizon-architecture.md`, `character-dynamics.md`, `thematic-polyphony.md`, `complexity-pruning.md`, `endings-closure-aftertaste.md` only to the extent activated by Project Poetics.
- Review/observability: `adversarial-review.md`, `regression-tests.md`, `story-observatory.md`.
- Roles/context/intensity: `multi-agent-orchestration.md`, `single-agent-isolation.md`, `context-compilation.md`, `reasoning-intensity.md`.
- Optional humanities interpretation: `chapter-humanities-analysis.md`.

### Maintenance / evaluation only

Load only while maintaining/evaluating the Skill or running instrumented evidence collection:

- `test-tier-contract.md` - Fast/Core/Full/Soak;
- `external-research-ledger.md` - research provenance/status;
- `evaluation-benchmark.md`, `evaluation-corpus.md` - version evaluation and multi-poetics coverage;
- `failure-corpus-mutation-testing.md` - durable failures/mutation;
- `metamorphic-adversarial-benchmark.md` - semantic/poetics-preserving transformations;
- `chinese-narrative-behavioral-evaluation.md` - Chinese narrative behavior evidence;
- `live-campaign-longitudinal-evaluation.md` - real longitudinal campaigns;
- `intensity-longitudinal-benchmark.md` - synthetic longitudinal calibration;
- `tool-surface.md` - deterministic CLI ownership;
- `system-map.md` - complete canonical ownership map.
- `skill-scope-identity.md` - canonical Chinese-language product scope, public display identity, compatibility slug, and controlled future migration policy.

Keep private evaluation holdouts outside the packaged Skill and never expose gold answers to generation context.

## Operating workflow

### 1. Establish author intent, openness, evidence, and provisional poetics

For a substantial new project/rebuild, complete foreseeable author-level intake up front. Do not force a theme, ending, character arc, hidden network, or genre formula when the user has not chosen one.

Keep source/provenance uncertainty separate from fictional uncertainty. Use typed OpenIssues when consequential possibilities must remain authoritative.

Compile a **provisional Project Poetics** from available intent: long-form organizing principle(s), intended reading experience, legitimate salience sources, progression modes, mind/explanation policy, form visibility, active capabilities, and do-not-optimize constraints. Theme may be `none`.

Research only the causal cone that constrains architecture/prose. Evidence can constrain facts; it does not choose the project's poetics.

### 2. Activate only the planning artifacts the project needs

Use `prewriting-readiness.md`. Require a small Base Readiness set, then activate additional artifacts by **causal risk** and **Project Poetics**. For substantial Chapter 1 work, record the activation decision for every readiness risk family and run the deterministic readiness gate before claiming the project is ready. Distinguish `REVIEW_READY` from `DRAFT_READY`. Before prose, run `storyctl readiness ... --require-draft-permission`; Project Doctor health is insufficient. Freeze and present the review snapshot, then bind a fresh explicit author approval. The first early-writing request requires refusal; only a later independent insistence can waive remote volume depth, with all current safety gates retained. See the owner for the executable contract.

Do not require a Hidden Causal Network, complex Timeline, full Knowledge Topology, detailed World Model, or polyphonic theme map merely because templates exist. Equally, do not leave a causally material artifact inactive merely because the opening can be improvised without immediately crashing.

### 3. Maintain live causal state

Track consequential time/place; actors and knowledge/beliefs; bodies/resources/obligations/relationships/reputation; important objects/custody; routes/access; active offscreen processes when present; narrative debt; reader-relevant state; staleable research dependencies.

In Runtime Mode, use expected-revision transactions, enforce only active hard invariants, append semantic committed events before refreshing materialized projections, and never rewrite projection truth while leaving event history unchanged.

### 4. Simulate only what the project requires; select page time by poetics

Advance causally relevant offscreen state. Some projects require rich autonomous worlds or adaptive hidden processes; others intentionally narrow the world to a focal consciousness, ritual, place, family, perception, or form. Do not add simulation breadth for prestige.

Choose the next narrative unit from the **current scoped poetics**. Decide scene vs summary vs ellipsis/pause, POV/focalizer, reader activity, expected contribution/progression mode, descriptive/dynamic resolution, and research/spatial dependencies.

A full scene need not create a durable world delta. It may justify page time through experiential completion, relation inhabitation, perception, recurrence, waiting, formal movement, or deliberate stasis when authorized by Project Poetics.

Instantiate a Scene Packet when spatial/custody/time/access continuity is causally material. Do not use packet bureaucracy as a literary-worth test.

### 5. Compile safe working context

For large projects, compile the smallest role-appropriate context containing the mission, relevant state, reader constraints, research dependencies, and a **Writer-safe scoped Project Poetics derivative**.

The Writer derivative may contain active salience sources, progression mode, reader activity, mind/explanation threshold, form/voice commitments, licensed recurrence, do-not-optimize constraints, authorized deviations, and only the active capability references needed now.

For activated chapter rollover, explicitly register final approval, reconcile/freeze the canonical final bytes and refresh predecessor-derived context before compiling the next chapter; require the current final hash + reconciliation + state snapshot tuple. See `project-state.md`, `prose-state-reconciliation.md` and `context-compilation.md`. P0-7 contradiction scanning is not implied.

Never encode a hidden answer as `do not reveal X`. Preserve semantic secret taint and authorial OpenIssue boundaries. Use `context-compilation.md`.

### 6. Draft from inside this project's world and poetics

Let prose arise from current bodies/limits, social position, relation history, actual attention/focalization, relevant material affordances, uncertainty, and partial understanding **as filtered by the current Project Poetics**.

Do not automatically add plot, explanation, symbolism, introspection, atmosphere, world breadth, or stylistic uniformity merely because those are available capabilities.

### 7. Commit causal state; propose poetic discoveries separately

After a full scene, derive actual durable exit-state changes from prose and reconcile only those changes that belong in state. `No durable world delta` is legal.

For consequential Chinese prose, read the whole stable text before inspecting proposed exit deltas; distinguish asserted facts, speech/lie, conjecture, metaphor, counterfactual and mistaken belief. Reconcile both omitted durable changes and state claims with no established basis using `prose-state-reconciliation.md`. On semantic revision, inspect actual downstream prose as well as indexed dependencies, preserve independently supported conclusions, and return cited affected premises with repair alternatives through `semantic-revision.md`.

Update affected knowledge, relationships, debts, setups, reader state, research dependencies, and active capability state only when relevant.

If repeated drafting reveals a possible new formal/poetic pattern, record it as a **discovery proposal**. Do not silently promote it to project-level poetics. Route reviewed changes through `project-poetics.md`, `discovery-drafting.md`, and change control.

### 8. Keep interpretation separate from authority

Humanities analysis remains optional/milestone/diagnostic. Its philosophical, historical, psychological, or critical claims do not rewrite canon or Project Poetics automatically. Approved developments route through their canonical owners.

When prose changes, use `semantic-revision.md` to distinguish text-only, hard-semantic, and poetics-affecting changes before propagation.

### 9. Review at the highest failing layer

Classify failures before fixing them:

1. hard integrity violation;
2. project-poetics violation;
3. unauthorized drift;
4. mere absence of another poetics' virtue.

Fix 1-3. Do not "repair" 4.

Use `adversarial-review.md` and `regression-tests.md`. During Skill maintenance, use mutation/metamorphic and multi-poetics adversarial fixtures rather than ad hoc aesthetic judgments. For anti-flattening promotion evidence, run the executable Multi-Poetics Behavioural Oracle described in `evaluation-benchmark.md`; static architecture diversity alone is insufficient.

## Cross-cutting laws

- **Hard correctness is not a universal aesthetic.** Protect truth/access/state while allowing different literary aims.
- **Technique is conditional.** A capability is available knowledge, not a requirement to activate it.
- **Do not collapse distinctions.** Use `literary-meta-core.md` before converting a diagnosis into a universal rule.
- **Project Poetics owns literary priorities.** Craft modules consume those priorities; they do not invent them independently.
- **Theme is optional and non-sovereign.** A project may begin from voice, relation, world, problem, image, perception, or form; theme need not become a debate matrix.
- **Progression has multiple forms.** Event escalation is one form among many; stasis/recurrence may be intentionally experienced.
- **Consistency does not require invariance.** Authorized formal heterogeneity is not drift.
- **Backstage explicitness does not require textual explicitness.** Canonical truth may remain unstated or interpretively open on the page.
- **Reader state is lossy and inferential.** What was once shown is not automatically what a reader can actively retrieve.
- **Formalize only operationally useful state.** Do not turn literary meaning into a complete ontology or aesthetic score.
- **Use semantic paragraphing.** Let paragraph boundaries follow discourse/narrative continuity and deliberate emphasis; avoid default one-sentence-per-line fragmentation.
- **Benchmark the Skill, not a genre.** Promotion requires both hard-continuity strength and multi-poetics non-coercion.
- **Phase 0 architecture freeze is active.** Extend current owners first. Do not add a new reference or major literary subsystem unless a concrete failure family is semantically unrepresentable by existing owners; follow `system-map.md` and record any approved owner-gap exception in `assets/architecture-freeze.json`.
