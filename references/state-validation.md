# Deterministic Story-State Validation

Use this reference for long projects that maintain machine-readable state and need mechanical checks before high-level creative review.

## Contents

- Core principle
- Suggested state file
- Timeline checks
- Knowledge checks
- Custody checks
- Spatial-edge checks
- Scene-Packet checks
- Inter-scene travel checks
- Object-transfer checks
- Setup dormancy
- Offscreen staleness
- Counterfactual invariants
- Event-sourced runtime validation
- Read-only story operations
- Context compiler
- Runtime schema and migration checks
- Transaction and concurrency checks
- Narrative invariant checks
- Semantic revision reconciliation
- Narrative fuzzing
- Workflow
- Narrative Artifact Lifecycle Checks

## Core principle

Use scripts for contradictions that should be mechanically detectable. Keep creative judgment in the model.

The bundled `scripts/validate_story_state.py` accepts JSON and reports errors/warnings for common temporal, custody, knowledge, spatial, travel, and Scene-Packet contradictions.

Use `spatiotemporal-scene-state.md` for the canonical spatial model. This file documents only the machine-checkable subset.

## Suggested state file

```json
{
  "current_chapter": 240,
  "current_day": 900,
  "timeline": [],
  "knowledge_uses": [],
  "knowledge_state": [],
  "custody": [],
  "spatial_edges": [],
  "scene_packets": [],
  "setups": [],
  "offscreen_processes": [],
  "branches": [],
  "research_dependencies": [],
  "threads": [],
  "reader_state": {},
  "dependencies": [],
  "humanities_reports": []
}
```

All sections are optional.

## Narrative Artifact Lifecycle Checks

`assets/project-schemas/narrative-artifact.schema.json` validates an optional `narrative_artifacts` view under the existing object owner. Absence is legal. A legacy `{ "id": "LETTER-22", "type": "letter" }` warns `artifact.legacy_unknown_lifecycle`; ordinary Scene Packet objects receive no lifecycle requirements. Explicit durability/high risk, `required_for`, or structural lifecycle/inscription/extent/snapshot/change records activate the hard contract even if `durable` is false. No migration or project-version bump is needed.

An active row has `id`, extensible `type`, `medium`, `author`, `created_at`, canonical object custody, and only applicable fields. `required_for` selects consequential inscription timing, custody, physical extent, sealing, sending, delivery, opening or finalization; missing required state blocks. Canonical custody remains top-level `custody`, with uniquely resolved `id` references, matching `item`/`holder`, and half-open `start`/`end` intervals. An absent/null `end` means ongoing custody, not an invented future boundary; contradictory later exclusive holders still fail. A writing interval may finish exactly at handover; a new point inscription cannot start at the outgoing holder's exclusive end. No parallel custody or knowledge database is introduced.

`lifecycle` accepts `sealed_at`, `sent_at`/`mailed_at`, `delivered_at`, recipient `opened_at`, `finalized_at`, `author_control_until`, `recording_start` and `recording_end`. Only present relations are checked. Conservative P0-3 comparison preserves uncertainty; unknown consequential order is an error requiring review, distinct from a proved contradiction.

`inscriptions` rows have stable `id`, `author`, `layer`, `start` (optional `end`), and `provenance`; optional `content` remains backend material. `ORIGINAL_INSCRIPTION` belongs to the original author and fits creation/control/recording bounds. Later layers are `POSTSCRIPT`, `REOPENED_ADDITION`, `SECOND_AUTHOR_ADDITION`, `ANNOTATION`, `LATER_RECORDING`, or `MEDIA_EDIT`, with `event_ref` and `custody_ref`. The uniquely resolved event carries `id`, `kind`, `at`, `actor`, `custody_ref`, `provenance`; its actor/time/access must support the layer. `FRAME_EXTERNAL` is surrounding narration and requires no physical access. Wrong authors, future access, bare exception labels and rewriting an immutable sent instance fail. Sealed writing requires a supported opening, not a claimed exception.

Paper `physical_extent` has `medium: "paper"`, positive `sheets`, and explicit `available_surfaces`/`written_surfaces`, each a list of `{ "sheet": 1, "side": "front" }`. Optional `blank_surfaces` and `written_surface_count` constrain the same identity set. Reject duplicate/out-of-range/unavailable surfaces, missing sheet identities, blank/written overlap and count mismatch. Available surfaces do not count as written. Optional positive `pages` is a declared physical measure, never inferred from words. Audio/video extent uses nonnegative `duration_seconds`, with optional uniquely identified `segments` (`start`, `end` offsets); paper fields are inapplicable.

Optional `world_state` carries material `holder`, `location`, `condition`, `seal_state`. Chapter `snapshots` (`id`, `chapter`, `at`, partial `state`, optional `scene_id`) must match the canonical object version at that time. `content_layer_ids` means completed internal inscriptions at the observation time; future additions and external narration are excluded. Surface ordering and redundant derived count omission do not change identity. Scene Packet objects reference the same `id`/`artifact_ref`. Provenance-bearing `changes` (`id`, `kind`, `at`, `actor`, `custody_ref`, `before`, `after`) preserve matching tracked values; kinds are limited to annotation, sheet removal, opening, transfer, condition change and media edit. A mechanism authorizes only its field family, never identity/authorship replacement. Content layers change through timed inscriptions, not generic object deltas. Register actual world deltas through the existing scene commit; do not hand-edit a later snapshot to hide a contradiction.

Scene Packet artifact assertions are checked only for the tracked state family above plus carrier `medium`. Direct fields and `entry_*`/`exit_*` forms are explicit claims: entry is compared at scene start, exit at scene end. Omitted fields remain optional, and unrelated JSON keys are ignored. A holder claim is resolved from canonical half-open custody; other fields use world state, valid explicit changes, or derived completed content/lifecycle state. A proved mismatch is `artifact.scene_state_conflict`; an absent or temporally indeterminate authority fails closed as `artifact.scene_state_unverified` or a review diagnostic. Scene assertions never create custody, state changes, opening events or knowledge.

For physical carriers with an explicit seal/open lifecycle, `sealed_at` and valid `SEAL` events derive `SEALED`; access-supported recipient `opened_at`, valid `REOPEN` events, and valid `OPEN` changes derive `OPEN`. Later transitions supersede earlier ones only when the existing temporal comparator establishes their order. Ambiguous ordering requires review. These transitions advance the `world_state` replay seed and reconcile partial snapshots and Scene assertions; sealing does not end author control. Physical `opened_at` also needs a custody holder at its time under half-open semantics. Digital opening uses only existing delivery ordering as limited logical support and does not assert authentication or complete forensics.

P0-5-M validates explicit holder assertions through the shared canonical custody query. `world_state.holder` is a redundant claim at the existing `created_at` replay origin and is removed only from the validator's private replay copy, never the input. Snapshot and Scene holder membership is queried at snapshot `at` or Scene start/end; it does not compare against a replayed holder. TRANSFER before claims reconcile with the outgoing referenced row at an exact half-open handover (or custody at the change point), and after claims require covering custody. A supported shared member passes. A proved world/transfer mismatch emits `artifact.holder_custody_conflict`; unavailable authority emits `artifact.holder_state_unverified`; indeterminate temporal support emits `artifact.access_needs_review`. Snapshot mismatch retains `artifact.cross_chapter_contradiction`; Scene mismatch retains its existing conflict categories. All active unresolved claims block the existing Readiness seam. Diagnostics remain opaque codes; legacy unactivated rows warn, and omitted claims remain optional.

Stable opaque diagnostic families are `artifact.schema`, `artifact.lifecycle_order`, `artifact.inscription_after_control_loss`, `artifact.unsupported_exception`, `artifact.layer_author_mismatch`, `artifact.*surface*`, `artifact.written_count_mismatch`, `artifact.cross_chapter_contradiction`, `artifact.duplicate_identity`, and `artifact.*needs_review`. They flow through existing State CLI and Readiness (`readiness.story-state`); no new permission owner is added. Findings do not interpolate private text. Existing Compiler visibility/negative-spoiler controls remain authoritative.

**Coverage is structured-state enforcement only:** no arbitrary Chinese prose extraction, OCR, real postal proof, handwriting capacity, inferred copies, authenticity/truth proof, full document history, digital forensics, derived-fact freshness or chapter rollover.

## Timeline records

```json
{
  "id": "ev-12",
  "actor": "A",
  "location": "north-gate",
  "start": 100,
  "end": 140,
  "allow_overlap": false
}
```

Time values are numeric in a project-defined common unit. The validator flags overlapping events for the same actor at different locations unless overlap is explicitly allowed.

## Knowledge-use records

```json
{
  "actor": "A",
  "fact": "F17",
  "acquired": 120,
  "used": 90
}
```

The validator flags use before acquisition. For false beliefs or inference, give them a distinct fact ID rather than pretending the actor possessed objective truth.

## Custody records

```json
{
  "item": "seal-01",
  "holder": "A",
  "start": 50,
  "end": 80,
  "shared": false
}
```

The validator flags overlapping exclusive custody by different holders.

## Spatial-edge records

```json
{
  "id": "road-A-B-v1",
  "a": "district-A",
  "b": "district-B",
  "distance": 12,
  "direction_a_to_b": "east",
  "direction_b_to_a": "west",
  "min_travel_time": 30,
  "passable": true,
  "valid_from": 0,
  "valid_to": 500,
  "one_way": false
}
```

The validator checks:

- endpoints exist;
- validity intervals are ordered;
- distance and minimum travel time are non-negative;
- simple inverse directions agree when both are supplied;
- overlapping time intervals do not define conflicting states for the same location pair unless explicitly allowed.

Use separate edge versions when distance, access, route condition, or travel time changes over story time.

## Scene-Packet records

A machine-readable mirror of a Scene Packet can use:

```json
{
  "id": "SCN-0042",
  "chapter": 11,
  "start": 300,
  "end": 315,
  "location": "district-A",
  "status": "committed",
  "sync_complete": true,
  "characters": [
    {"id": "A", "entry_zone": "north-door", "exit_zone": "table"}
  ],
  "objects": [
    {
      "id": "key-01",
      "entry_holder": "A",
      "entry_location": "coat-pocket",
      "exit_holder": "A",
      "exit_location": "coat-pocket"
    }
  ],
  "spatial_relations": [
    {
      "subject": "A",
      "relation": "left_of",
      "object": "table",
      "frame": "room-facing-north"
    }
  ]
}
```

The validator requires committed packets to declare `sync_complete: true` and rejects ambiguous left/right/front/behind relations that omit a reference frame.

The Markdown Scene Packet remains the richer authoring document. This JSON form exists only to support mechanical checks.

## Inter-scene travel checks

When the same actor appears in consecutive Scene Packets at different global locations, the validator:

1. reads the previous scene exit time/location;
2. reads the next scene start time/location;
3. searches the currently passable spatial graph for a path;
4. computes the shortest modeled minimum travel time;
5. flags impossible travel when the available gap is shorter.

If no modeled path exists, it warns rather than assuming teleportation. Add the missing route or explicitly set `allow_unmodeled_travel` when the project intentionally leaves that travel outside the modeled graph.

Omitting travel from prose does not remove travel from world state.

## Object-transfer checks

For an object appearing in multiple Scene Packets, the validator compares the prior exit holder/location with the later entry holder/location.

If the object moved between scenes, document the transfer by setting `transition_explained: true` on the relevant object record, or use a project-specific explicit transfer record before the later scene.

An unexplained change is flagged as an object continuity error.

## Setup records

```json
{
  "id": "setup-07",
  "status": "open",
  "salience": "high",
  "last_reactivated_chapter": 80,
  "max_dormancy": 120
}
```

The validator warns when an open setup exceeds its declared dormancy horizon. This is not an automatic plot error; it is a reminder to review reader memory and narrative promises.

## Offscreen-process records

```json
{
  "id": "faction-x",
  "status": "active",
  "importance": "high",
  "last_update_day": 400,
  "max_staleness": 200
}
```

The validator warns when an active process has gone too long without state review.

## Branch records

```json
{
  "id": "loop-3",
  "invariants_expected": {"weather": "rain", "king_alive_at_start": true},
  "invariants_observed": {"weather": "sun", "king_alive_at_start": true},
  "authorized_changes": ["weather"]
}
```

The validator flags invariant drift unless the changed key is explicitly authorized.


## Event-sourced runtime validation

For large projects using Runtime Mode, run `scripts/narrative_runtime.py validate` in addition to the projection-level checks below. Use its `replay`, `snapshot`, `impact`, `branch-create`, and `merge-plan` commands for deterministic runtime operations. Event/runtime validation owns unique event IDs, branch lineage, projection effect syntax, fork validity, and dependency-file structure.

Do not duplicate Runtime replay/lineage checks in `validate_story_state.py`; that validator remains focused on materialized story-state contradictions plus machine-decidable OpenIssue representation guards. OpenIssue literary compatibility itself remains a semantic review task.

## Read-only story operations

Use `scripts/story_ops.py` for deterministic project-state queries that should not depend on creative interpretation. Supported commands include:

- `knowledge` - actor knowledge at a time;
- `travel` - minimum modeled route/time;
- `scene-check` - validator findings involving one Scene Packet;
- `stale-research` - research dependencies due for recheck;
- `thread-status` - current explicit causal-thread state;
- `reader-state` - current or chapter-scoped reader model;
- `propagate` - transitive dependency impact from a changed node;
- `reflection-status` - philosophy/history/psychology sidecar decision state;
- `open-issues` - governed authorial OpenIssue state, positions, policies, and derived commitment fingerprints;
- `authorial-unknowns` - backward-compatible alias for `open-issues`;
- `irreversibility` - active low-reversibility consequence records.

The tool is read-only. `propagate` computes an impact set; it does not rewrite dependent artifacts. In Runtime Mode it prefers the authoritative conventional Runtime dependency artifact beside the project story-state projection; `--dependencies PATH` overrides discovery. Only when no Runtime graph exists does it fall back to embedded `story-state.dependencies`. If no source exists, it warns instead of silently implying an empty graph. Creative repair remains the agent's job.

`scene-check` consumes structured validator issue ownership (`scene_ids`) rather than searching human-readable error text. Cross-scene contradictions such as impossible travel or object transfer must belong to every Scene Packet involved.

`stale-research` and the Story Observatory must share `scripts/research_freshness.py`; do not maintain a second freshness formula in either caller. Explicit stale flags and chapter/day age limits therefore mean the same thing everywhere.

Use `assets/state-templates/story-state-minimal-template.json` as the neutral minimal Story State baseline for a fresh Lean project or validator smoke test. Use `assets/discovery-templates/open-issue-template.json` plus `assets/project-schemas/open-issue.schema.json` for new governed authorial openness. Run `scripts/integration_selftest.py` after changes to Runtime/validation/orchestration seams.

## Context compiler

Use `scripts/compile_context.py` with the schema described in `context-compilation.md`. It deterministically:

- filters entries by role, active branch, and chapter visibility;
- rejects obvious future and sibling-branch leakage;
- scores explicit relevance tags;
- packs required entries before optional context;
- falls back to approved summaries when configured;
- reports included/excluded entries and token estimates.

Use `assets/tooling-templates/context-index-template.json` and `assets/tooling-templates/context-request-template.json`.

It must fail rather than silently omit hard-required causal state.

## Runtime workflow

When Runtime Mode is active:

1. validate event/branch/dependency structure;
2. replay or load the current projection/snapshot;
3. run story-state validation on the materialized projection;
4. run role/context checks;
5. draft/commit;
6. append semantic events;
7. rebuild affected projections;
8. re-run validation.

## Runtime schema and migration checks

When Runtime v3 is enabled, validate representation separately from story truth:

1. validate `runtime/runtime-manifest.json` and registered artifacts with `scripts/runtime_schema.py`;
2. refuse unsupported future major versions rather than guessing;
3. migrate mutable registries through explicit migration tooling;
4. never rewrite committed event history merely to make old events look new;
5. read older event representations through compatibility normalization/upcasters where supported.

Schema validity means "this artifact has a recognized shape," not "the story fact is correct."

## Transaction and concurrency checks

For multi-agent or concurrent work, use `scripts/runtime_tx.py` rather than appending events manually.

A safe commit must:

- declare the branch head/revision it read;
- fail on a changed head instead of last-writer-wins overwriting;
- reject unresolved blocking objections;
- validate the candidate event set before append;
- evaluate hard project invariants when configured;
- append all proposed events or none;
- be idempotent when the same transaction is retried.

## Narrative invariant checks

Use `scripts/validate_invariants.py` for project-specific, mechanically decidable laws. `narrative-invariants.md` owns the DSL and its limits.

Hard invariants may block a commit. Soft/advisory invariants may only surface warnings. Never encode subjective craft preferences such as "this scene is boring" as machine invariants.

## Semantic revision reconciliation

When an already-written chapter changes materially:

1. run `scripts/revision_diff.py` for deterministic paragraph alignment;
2. have a Revision Analyst classify semantic impact under `semantic-revision.md`;
3. validate proposed deltas against current canon/runtime;
4. require approval/change-control for canon-affecting changes;
5. propagate invalidation only after the revision is accepted.

A text diff is evidence of change, not permission to mutate story state.

## Narrative fuzzing

Use `scripts/narrative_fuzz.py` during Skill/runtime maintenance or before trusting major runtime changes. It generates seeded transition sequences and checks properties such as replay equivalence, snapshot-resume equivalence, inherited branch prefixes, and sibling-branch isolation.

Fuzzing validates runtime mechanics. It does not judge literary quality.

## Workflow

1. Maintain only state the project genuinely needs.
2. Mirror causally important spatial routes and Scene Packet state into JSON when scale makes manual continuity fragile.
3. Run the validator before large planning passes, after a major scene/arc commit, or after changing geography/access/timing assumptions.
4. Treat errors as continuity issues to resolve.
5. Treat warnings as prompts for human/model review, not automatic failures.
6. After fixes, run creative audits from the other references.

Do not force centimeter-level geometry into machine-readable state. Validate the lowest precision that protects causality.

## Project Poetics and activated obligations

Mechanical validation follows **activated obligations**, not the full capability library.

- Do not fail a project for lacking a Hidden Causal Network, detailed Timeline, Reader Model, Scene Packet, polyphony map, or other optional artifact unless the current manifest/profile/mission explicitly activates the corresponding dependency.
- A full scene may validly produce no durable world-state delta. Validate continuity claims that actually exist; do not invent a required delta to validate.
- A Project Poetics override is planning metadata. Validate its path/reference integrity when declared, but do not translate aesthetic language into fake mechanical invariants.
- If a Project Poetics explicitly locks a mechanically decidable formal constraint, validate only the typed derivative registered under `narrative-invariants.md`, not free-form literary judgments.

## Temporal, epistemic and precision validation (P0-3)

`validate_story_state.py` delegates to the shared Kernel `temporal_epistemic_issues`; it does not copy a second validator. The optional typed subset is `assets/project-schemas/temporal-epistemic.schema.json`. Existing Story State and project-format versions remain unchanged.

Use `facts`, existing `knowledge_state`, existing `knowledge_uses`, optional `writer_visible_facts` and existing `research_dependencies`. Risk flags are `consequential`, `secret_sensitive`, `temporal_risk`, `research_derived`, `plot_critical`, `identity_critical`. Do not serialize every ordinary fact. Knowledge Topology owns the fields/channels/modes; Reality Grounding owns research validity.

Checks cover missing acquisition (K21 coverage), use before acquisition, uncomparable consequential use, unavailable facts, research applicability conflicts, firsthand experience without original presence/direct acquisition, and unsupported specificity/basis refinement (K22). Issues carry severity, stable code, law and optional scene_ids; existing string-list/CLI callers remain supported. Missing legacy precision is UNKNOWN; missing research validity is UNKNOWN applicability, never automatic true.

Temporal comparisons support finite numeric values in one project axis and ISO `YYYY`, `YYYY-MM`, `YYYY-MM-DD`. Closed date bounds retain the whole year/month uncertainty. Validity ends are inclusive. Missing endpoints are open only when at least one boundary exists. Never compare calendar values with numeric time or treat an unresolved relative label as a date. Overlapping uncertain acquisition/use bounds require review and block critical use. Exact completed acquisition equal to use passes. Existing spatial/travel/custody checks still require numeric units; date presence can support experience checks without converting those other validators into a calendar engine.

Structured use may specify `fact_at` for the historical time being described, separate from current `used_at`; firsthand memory uses `event_at` for fact validity and current acquisition order for access. Temporal source availability still prevents learning a future event. This is not an artifact lifecycle, chapter rollover, causal sufficiency, full prose contradiction scan, or NLP extraction pass.

Uncertain presence endpoints must prove containment using the latest possible arrival and earliest possible departure. Direct event-day memory needs an exact matching direct acquisition; overlapping month bounds alone do not prove experience. Legacy numeric-string acquired/used retains its former numeric interpretation.

## Causal sufficiency validation (P0-4)

Hidden Causal Networks owns the semantics of the optional `causal_events` view; read its P0-4 contract before adding consequential responsibility records. `validate_story_state.py` calls `causal_sufficiency_issues` through the existing structured `validate_issues` seam. String-list callers and the State CLI receive the same errors/warnings. The current Readiness owner already runs that CLI against the canonical Story State, so errors prevent its gate from passing; no second readiness or operational truth owner is added.

The optional typed subset is `assets/project-schemas/causal-event.schema.json`. High-risk versioned/actively used claims are checked for intervention/agent/outcome/mechanism, structured responsibility references, claim-sensitive counterfactual support, conditional omission capability/opportunity/intent/knowledge, supported control/stability, prior plan or acquired adaptive observation and unresolved necessary independent contingencies. Shape errors fail closed without interpreting malformed values. All sections remain optional; absent causal records do not fail ordinary projects. Legacy archived records produce unknown-sufficiency review warnings. Active new primary use requires enrichment, not a project-format bump or historical migration.

`CAUSAL_INSUFFICIENCY` and `MASTERMIND_INFLATION` are deterministic errors on contradictory structured attribution. `causal.counterfactual_review`/`causal.legacy_unknown_sufficiency` are warnings, never fully closed causal certification. A strong unknown-independence or unsupported contingency claim is an error requiring review. Findings preserve optional scene_ids and opaque codes without secret-bearing descriptions. They are backend findings, not Writer directives.

P0-3's existing Kernel helper validates copied backend actor-use declarations against canonical acquisitions; only disclosure metadata is removed from the private validation view. Source truth, validity, temporal order, channel and provenance checks remain shared and unchanged. This grants no Writer permission. P0-1 premise commitment and P0-2 execution evidence still have their existing owners. Do not infer cause from eventual success, require deterministic guarantees, reject all chance or introduce a random-count quota.

Historical internal regression groups for causal sufficiency used private-derived fixtures not distributed here; the public Fast/release checks do not replace that comprehensive coverage. This is structured causal attribution validation, not a full probabilistic engine, post-draft prose scan, chapter rollover, artifact lifecycle, Living World route simulation or revision-scope implementation.


P0-4 surgical hardening derives effective preplanned claim strength centrally; optional intent/mastery deletion cannot disable primary/definite outcome engineering checks. `causal.plan_intent_conflict` rejects contradictory explicit intent while the mastermind audit remains active. A backend-only canonical action index resolves other sufficient causes across causal events after source audits, rejects duplicate IDs, checks actor/outcome binding, noncausal/self/circular references and propagates invalid source evidence. A nonempty string is not proof. All declared other causes are audited even alongside a material-effect argument. Archived legacy warnings remain readable but cannot certify a new high-risk sufficiency reference. Planned branch IDs reserve identity; realized sufficient interventions need an existing causal event/basis. P0-3 acquisition and Writer isolation retain their original owners. See Hidden Causal Networks for P0-4-H and P0-4-I.

P0-4-J adds the centralized `source_supports_sufficient_cause` capability check after canonical resolution and local/recursive source validation. Source role, closed outcome-bound counterfactual and absence of a material-effect-only qualification constrain the incoming sufficient claim. INCIDENTAL/NOT_CAUSALLY_RESPONSIBLE always reject; intent and claimant sufficient flags cannot override them. Missing/unknown roles fail closed (schema, existing local checks and helper policy). The role policy must cover every schema enum, so a new role cannot implicitly gain sufficiency. OVERDETERMINED source support requires its own explicit role/counterfactual and acyclic validated closure; source open closure or limited risk/timing/mechanism/opportunity effect cannot certify sufficiency. Diagnostics are opaque `causal.overdetermination_ineligible_source_role` or `causal.overdetermination_insufficient_source_strength`; existing invalid source diagnostics take precedence for structurally invalid sources. Attribution, P0-3, order independence, circular checks and Writer isolation are unchanged. The role matrix and semantic limits remain owned by Hidden Causal Networks.

P0-4-K removes only the claimant/source actor inequality prohibition from overdetermination reference validation. canonical action.actor must still equal cause.agent; same actor with distinct canonical, independently supported, semantically eligible interventions is allowed. Existing unique action resolution, self/duplicate/circular checks, independent/sufficient/provenance requirements and source-strength validation are unchanged. Different actors do not imply independence; distinct IDs do not establish it alone. Same-event multiple realized actions are outside the existing one-realized-action representation, so no new event identity constraint/schema is added. See Hidden Causal Networks for the semantic contract.
