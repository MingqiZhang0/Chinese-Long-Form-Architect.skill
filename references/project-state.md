# Project State and Continuity Model

Use this reference for any persistent project whose continuity must survive many scenes, chapters, or arcs. It owns the **live Story State Bundle**, canon status, update governance, and state-commit protocol. It also records authoritative references to Project Poetics as author/planning state while keeping poetics separate from fictional world truth. Local spatial transactions belong to `spatiotemporal-scene-state.md`; external evidence belongs to `reality-grounding-research.md`.

## Contents

- State principles
- Canon and provenance
- Project Brief / user-intent register
- Project Poetics register
- Story State Bundle (including embodiment/resources, emotional residue, consequence residue, and Narrative Debt)
- Multi-level commit protocol
- Dependency propagation
- Interpretive sidecar register
- Continuity priority
- Minimal state for short tasks

## 1. State principles

Treat continuity as explicit state, not memory.

Track a fact only when later causality, access, timing, recovery, revision impact, or reader expectation materially depends on it. Use `formalization-boundary.md` before turning ambiguous motive, symbolism, transient impressions, or author interpretation into durable fields.

Every **formalized consequential state** should have, when useful:

- stable ID / label;
- current value or status;
- canon status;
- provenance;
- last meaningful update;
- dependencies;
- time scope or validity when changeable.

All project documents are **live**. Prewriting artifacts, research dossiers, spatial graphs, scene packets, ledgers, and long-horizon plans may evolve as canon changes. Do not preserve a stale document merely because it existed first.

For large projects using Runtime Mode, distinguish **write-side history** from **read-side state**: committed events in `narrative-runtime.md` are the durable history for the semantic strata the project event-sources; the ledgers below are typed materialized projections plus explicit planning state. A replayed Reader Model/humanities status remains reader/analysis state rather than fictional canon. Small projects may use these ledgers directly without Runtime Mode.

At the same time, do not silently rewrite history. Preserve prior truth when auditability matters and use change control for consequential migrations.

## 2. Canon and provenance

### Canon status

- **Fixed** - explicitly established by source material or already delivered/published prose.
- **Implied** - logically forced by Fixed facts.
- **Provisional** - current usable design not yet hardened by reader-facing canon.
- **Open** - deliberately undecided design space whose uncertainty is itself intentional and bounded.
- **Retired** - an intentionally abandoned Provisional choice.

Do not silently demote Fixed facts. `Open` is not a synonym for missing work: if near-term causality depends on the answer, resolve it before drafting.

### Source confidence / provenance flag

Keep source reliability separate from canon status. Mark a claim **source-uncertain** (or use an equivalent confidence field) when memory, transcription, translation, summary, or conflicting evidence makes its origin unreliable. A fact may be Fixed in delivered prose yet still have an uncertain external source history, and an Open design question may rest on excellent evidence.

### Story provenance

- **source** - supplied by the user or source text;
- **derived** - logically inferred from stronger canon;
- **designed** - created during architecture;
- **revealed** - established by drafted prose;
- **migrated** - altered through explicit change control.

Keep this separate from **external evidence provenance**. Research supports a project decision; it does not automatically become fictional canon. Use `reality-grounding-research.md`.

## 3. Story State Bundle

Maintain only the ledgers the project needs.

### A. Canon and change

#### Project Brief / user-intent register

Persist the completed Project Brief from `front-loaded-adaptive-intake.md` when the project is substantial enough to need durable author-intent tracking. Record only author-level constraints that can affect later architecture or interpretation:

- USER_LOCKED choices and provenance;
- DELEGATED fields the Agent may resolve without re-asking;
- ABSENT / prohibited elements;
- USER_RESERVED decisions and declared gates;
- later explicit user updates that supersede older intent.

Do not turn unasked implementation details into future user-question debt. The brief constrains the project; it is not a backlog of missing preferences.

#### Consequential decision semantic commits

Extend this same register; do not create a parallel decision registry. Only decisions actually used by research, world model, chronology, causal/case mechanics, long-horizon architecture, Writer-safe context, or another declared hard dependency need this contract. Ordinary wording, background objects, and incidental clothes remain unformalized unless later consequential.

The normalized Intake JSON retains `schema_version: 1.0.0` and the existing authority `status`; the additive fields below distinguish authorization from resolution. `value` retains the original normalized intent, while `resolved_value` is the actual accepted decision (including valid `false`/`0` values). Canon status remains a separate dimension: a committed S0 planning decision need not be Fixed fictional canon.

```json
{
  "id": "city_transport",
  "status": "delegated",
  "value": "城市交通你来决定",
  "source": "intake_response",
  "resolution": "resolved",
  "resolved_value": "公交 + 中巴体系",
  "resolved_by": "agent",
  "provenance": {
    "authority_ref": "user-message-transport-delegation",
    "resolution_ref": "project-brief#city-transport"
  },
  "semantic_commit": {
    "committed_at": "2026-10-07T09:00:00Z",
    "content_sha256": "<commit_fingerprint(slot)>"
  }
}
```

The remaining interaction fields (`asked`, `known_before_intake`, etc.) stay as before. `USER_LOCKED`/`ABSENT` use `resolved_by: user` with user-intent provenance; `DELEGATED`/`AGENT_DISCRETION` use `resolved_by: agent` with an explicit authority-scope reference and resolution reference. A proposal cannot manufacture a user source. Do not infer resolution from a delegation phrase.

`scripts/validate_intake_state.py:commit_fingerprint` reuses the existing canonical sorted-JSON SHA-256 convention. It binds ID, authority/status, source, resolution, resolved value, resolver, provenance, and acceptance timestamp; it excludes display/interaction metadata. Persist the record with its fingerprint before consumers are activated. This is **semantic commit**, never an instruction to run Git. Runtime event/branch identities remain unchanged; this digest identifies the canonical S0 decision payload rather than introducing another registry or Runtime event identity.

Reuse `source -> target` dependency edges. Outside Runtime, put them in this register's `dependencies.edges`; in Runtime Mode use only the existing Runtime graph and pass it with `--dependencies`. Each consequential decision edge records `kind: decision-dependency`, `dependency_class` (`research / world_model / chronology / case_mechanics / long_horizon / writer_context / consequential`), `status: active`, the captured `source_commit_sha256`, and timezone-bearing `activated_at`. Source is the slot ID; target is the existing consumer/artifact ID. Capture the digest from already persisted state, never fill it in retrospectively. Commit time must strictly precede activation time.

Before independent work, run `python -B scripts/validate_intake_state.py INTAKE.json --consumer CONSUMER-ID --json` (in Runtime Mode also pass the existing graph with `--dependencies`). Without `--consumer`, audit all active decision edges. The checker follows registered active source-to-target edges backward from the requested consumers, including intermediate artifacts; unrelated unresolved fields and unrelated invalid decision edges do not block the selected work. Kernel audits all declared active edges; Context Compiler checks selected entries and `task_id` when the Project Manifest declares a canonical intake path. It uses the request's manifest or the root manifest; omitting the request pointer cannot bypass an opted-in register. Both reuse the validator. Scoped work may proceed independently while another consequential intake slot remains open; full intake completion still rejects unresolved consequential slots.

Missing commit, provenance, resolution, resolver, stale digest, or unproven/reversed acceptance order makes an active dependency invalid. The validator returns `INVALID_REQUIRES_REGENERATION` for missing/stale captured identity/order; it does not mutate research or prose. A later source commit cannot repair an old edge: retain its old activation record, invalidate/retire it, regenerate the dependent artifact, then create a new activation record. Do not rewrite old activation evidence to claim the original artifact was legal.

Legacy `USER_LOCKED + value + source` remains readable as resolved **intent**, with a compatibility warning; it gains no inferred semantic commit. Legacy delegated values remain authority grants. No corpus-wide migration is required. Before a new consequential dependency, review the original provenance, record explicit resolution/resolver and acceptance identity, and regenerate any earlier unsupported consumer. Value-only legacy data never becomes user-authorized automatically. Existing projects without a canonical intake path remain readable; absence is not proof of legality, so new consequential work must register and validate the existing Brief serialization first.

These deterministic checks validate declared provenance and order, not the truth of user-message references or timestamps. Honest canonical records and the operator's pre-work gate are required; no full P1 freshness propagation or inference of undeclared natural-language dependencies is claimed.

#### Project Poetics register

Persist the authoritative Project Poetics reference from `project-poetics.md` when the project uses a durable artifact. This is **author/planning state**, not world truth. Record:

- project-level poetics path/status;
- source/authority and last approval;
- active capability names only when explicitly activated;
- scope override references (arc/volume/chapter/scene);
- do-not-optimize constraints with provenance;
- open/provisional poetics questions;
- superseded poetics versions when auditability matters.

Do not event-source aesthetic interpretation as though it were diegetic fact. Repeated drafting patterns become discovery proposals until reviewed. A poetics change may invalidate Narrative Strategy, missions, context packs, and diagnostics without changing world canon.

#### Canon ledger

Track durable world truths, rules, institutions, terminology, places, and history.

Minimum useful fields:

- ID;
- statement;
- status;
- provenance;
- dependencies;
- first establishment / last update.

#### Change log

For consequential architecture migrations:

- old assumption;
- new assumption;
- reason;
- affected material;
- migration action;
- project stage / date.

`change-control.md` owns retcon and migration procedure.

### B. Time, space, and custody

#### Timeline ledger

Track events and intervals whose timing constrains later action:

- time / date;
- event;
- participants;
- location;
- duration;
- travel / communication / recovery / institutional delay;
- source scene/chapter;
- unresolved temporal constraints.

#### Global spatiotemporal graph register

Register the canonical global graph and its current version / validity range. Do not duplicate detailed spatial schema here. `spatiotemporal-scene-state.md` owns nodes, edges, reference frames, travel, access, and time-indexed geometry.

#### Scene Packet registry

For each scene whose time/place/access/custody continuity is causally material and therefore receives a Scene Packet, record at minimum:

- Scene ID / chapter;
- start/end time;
- global location;
- packet status: `planned / provisional / committed / invalidated`;
- upstream dependencies;
- last synchronization.

The packet contents themselves belong to `spatiotemporal-scene-state.md`.

#### Resource / object custody ledger

Track only objects/resources whose holder, location, condition, ownership, or access can matter later.

Suggested fields:

- object / resource ID;
- current holder / container;
- location;
- condition;
- access restriction;
- last transfer;
- relevant dependencies.

### C. Actors and institutions

#### Character state ledger

Track story-relevant current state. Do not assume every character requires a transformation arc:

- location / body / mobility;
- capability / progression when the project uses it;
- possessions / money / access;
- obligations / debts / legal status;
- active goals;
- relationships / loyalty shifts;
- knowledge / false beliefs;
- reputation;
- unresolved promises;
- self-story / identity claim when behaviorally relevant;
- thresholds / coping / recent pressure when change matters;
- stable patterns, oscillations, relapse, failed change, or deliberate non-change when these are part of the project.

Do not duplicate full craft guidance for focalization or dialogue here. Use `character-dynamics.md`, `focalization-narrator.md`, and `dialogue-character-voice.md`.

#### Embodied / resource / capacity register

When bodies or finite material systems constrain action, maintain the relevant projections for:

- fatigue, sleep, pain, injury, treatment, mobility, exposure, or other consequential bodily state;
- money, food, water, fuel, ammunition, medicine, power, inventory, reserved stock;
- transport, staffing, beds, storage, communication, repair, manufacturing, bureaucratic throughput, or other capacities.

Do not duplicate operational rules here. `embodied-resource-state.md` owns precision, conservation, logistics, and recovery discipline.

#### Relationship / emotional residue ledger

For relationships whose past should constrain present behavior, track durable residue such as:

- trust / distrust;
- fear / safety;
- resentment;
- gratitude / obligation;
- attachment / avoidance;
- humiliation / shame residue;
- unresolved grievance;
- repair attempts and whether they were accepted;
- known triggers or boundary changes;
- context-specific differences (public, private, professional, family).

Prefer qualitative states and evidence-linked history over fake decimal scores. A reconciliation event may change the relationship without erasing accumulated residue. `character-dynamics.md` owns the psychological/relational interpretation; this ledger owns persistent state.

#### Organization state ledger

Track:

- leadership / factions;
- authority / jurisdiction;
- resources;
- public posture / hidden objective where relevant;
- current conflicts;
- procedural constraints;
- information access;
- official and competing theories;
- memory repositories / reporting bottlenecks;
- recent learning or doctrine change.

Use `organizational-learning.md` for adaptation mechanics.

### D. Hidden, offscreen, and branch state

#### Offscreen process ledger

For causally active processes without current page time:

- actor / institution;
- objective;
- last state / action;
- information available;
- current theory;
- interference observed / lesson learned;
- next update condition;
- time/resource dependency;
- interruption conditions;
- reader visibility;
- surfacing consequence.

#### Counterfactual branch ledger

Use only when repeated/alternative scenarios matter to causal inference. If the alternate line becomes a durable editable world line, promote it to a formal canon branch under `narrative-runtime.md`; do not maintain two competing branch systems.

Track:

- branch ID;
- shared initial conditions;
- changed intervention;
- visible outcome;
- hidden response;
- invariants;
- changed facts;
- carried knowledge;
- hypothesis updated;
- cost of comparison.

### E. Narrative and reader state

#### Setup / payoff ledger

Track major narrative promises only:

- setup ID;
- first appearance;
- surface meaning;
- hidden/future causal potential;
- reader visibility and activation: `hot / warm / cool / cold`;
- last natural reactivation;
- possible interpretations;
- payoff horizon;
- status: `open / partial / transformed / resolved / retired-before-promise`.

#### Consequence residue ledger

Track durable aftermath that should keep existing even off-page. This is **story-world residue**, not Narrative Debt in the engineering sense. Examples:

- injury / recovery;
- legal exposure;
- financial debt;
- damaged infrastructure;
- grief;
- scandal;
- missing personnel;
- supply disruption;
- retaliation;
- promises;
- evidence;
- dangerous knowledge now held by someone.

Use `state-inertia.md` for persistence/residue mechanics and `embodied-resource-state.md` when the residue is bodily or materially finite.

#### Narrative Debt register

Track **known weaknesses deliberately left unresolved for now**, not fictional consequences. Examples:

- a motivation is currently thinner than later scenes require;
- a logistics explanation is temporary;
- research is incomplete but the draft must continue;
- an exposition shortcut needs repair before publication;
- a continuity discrepancy is bounded but not yet resolved.

Suggested fields:

- debt ID;
- kind: `continuity / motivation / research / worldbuilding / exposition / logistics / reader-fairness / voice / structure / other`;
- issue;
- temporary justification;
- severity;
- status;
- introduced at;
- resolve-before horizon;
- dependencies;
- **interest** - how leaving the debt open makes later repair more expensive or risky;
- resolution / accepted-debt rationale.

Narrative Debt is visible technical/story debt, not a license to hand-wave. Blocking debt must prevent readiness/commit at the stage where it becomes consequential. Use `assets/state-templates/narrative-debt-template.json` and the schema owned by `runtime-schema-migration.md`.

#### OpenIssue / authorial-open-design register

Use only when preserving a consequential author-level non-resolution matters operationally; ordinary missing work and unformalized meaning do not belong here. For backward compatibility the Story State serialization key remains `authorial_unknowns`, but new records should use OpenIssue v2 semantics from `open-issue-semantics.md`.

Track as needed:

- stable question ID and question text;
- lifecycle state: `open / resolved / retired`;
- resolution policy and criterion;
- decision authority and optional decision horizon;
- domain semantics: open-ended / constraint-defined / explicitly exhaustive;
- authoritative constraints with provenance;
- candidate positions with separate **viability** and **planning stance**;
- resolution or retirement record when applicable;
- clue/provenance references when later compatibility review needs them.

Working hypotheses are conditional planning state, not fictional truth. Reuse the Runtime dependency graph for `conditional-on-hypothesis` provenance where available. Keep this ledger separate from actor knowledge, reader hypotheses, research unknowns, and information-flow restrictions.

Use `assets/discovery-templates/open-issue-template.json` for new records. Legacy `AUTHORIAL_UNKNOWN / DELIBERATELY_UNRESOLVED` records remain readable; do not auto-classify the latter during migration.

#### Reader-state ledger

For dense serials or delayed reveals:

- foreground question;
- warm / dormant questions;
- likely hypothesis;
- known-but-not-understood facts;
- cold facts needed soon;
- last reactivation cue;
- transformed / resolved questions.

Use `reader-model.md` for detailed reasoning.

### F. Change dynamics and social memory

#### Inertia / transition ledger

Use only for states whose resistance to change matters:

- state / relation;
- sustaining forces;
- pressure for change;
- constraints;
- update rates by layer;
- residue;
- lag / rebound risk;
- path-dependent consequence.

Use `state-inertia.md`.

#### Irreversibility ledger

Track only consequential states whose reversal cost matters:

- event/state ID;
- reversibility level;
- reversal cost/required compensating event;
- residue that remains even after reversal;
- people/institutions/evidence that preserve the change.

In Runtime Mode, prefer storing reversibility metadata on the originating semantic event and project only the current high-consequence view here. Keep the event target stratum explicit in reasoning: durability/replay does not by itself make the projected value canon.

#### World-evolution ledger

For recurring places / communities, selectively track:

- protagonist-caused change;
- independently caused change;
- slow background change;
- surprising persistence and its cause.

Use `world-evolution-social-ecology.md`.

#### Social-version ledger

For rumors / reputations / public narratives with causal weight:

- underlying event / uncertainty;
- current circulating version;
- source chain / medium;
- accepting / rejecting / exploiting groups;
- distortions;
- official record versus informal belief;
- behavior caused by the version;
- correction attempts;
- residual reputation.

Use `social-transmission-reputation.md`.

### G. Research and arc registers

#### Research dependency register

Do not duplicate source dossiers. Register only:

- research ID;
- adopted project fact or unresolved dependency;
- scope;
- status;
- affected material;
- recheck trigger.

`reality-grounding-research.md` owns sources and evidence.

#### Arc register

For each active arc:

- central tension;
- actors / stakes;
- unresolved questions;
- dependencies;
- current pressure points;
- exit condition;
- status.


### H. Interpretive sidecar register

When a humanities/human-science report is actually generated by an explicit or configured trigger, it is a durable analysis artifact but **not canon**. Ordinary chapter commits do not require a report. Register only:

- chapter ID and chapter version/hash;
- report path;
- report status;
- finding IDs and their decision statuses;
- any user-approved development targets;
- staleness after chapter revision.

Allowed finding statuses come from `chapter-humanities-analysis.md`. `PENDING_USER_DECISION` and `PARKED` findings must not influence future drafting or planning. Only `APPROVED_FOR_DEVELOPMENT` findings may enter planning, and only actual later narrative material may make the resulting development canon.

## 4. Multi-level commit protocol

Do not use one giant update checklist after every paragraph. Commit at the level where durable state changed.

### Scene commit

For every full persistent scene:

1. derive the actual exit state from prose;
2. reconcile the Scene Packet;
3. validate the proposed durable delta;
4. when the governance profile or failure cost justifies it, reconcile prose-established durable facts against proposed state deltas with `prose-state-reconciliation.md`;
5. in Runtime Mode, append semantic committed event(s) to the active branch; otherwise update the live ledgers directly;
6. synchronize/rebuild character, object, location, access, timeline, and other affected projections;
7. invalidate downstream packets built on stale entry state;
8. mark `COMMITTED` only when synchronization is complete.

`spatiotemporal-scene-state.md` owns the detailed scene transaction. `narrative-runtime.md` owns event append/replay when active.

### Chapter commit

After a substantial chapter, update only durable changes beyond the local scene transaction. In Runtime Mode, represent canon-changing deltas as semantic events before refreshing read-side projections; planning-only state may remain outside the committed event stream until it becomes canon. Under Forensic governance, or for unusually high-risk commits, require an approved prose-state reconciliation report before accepting prose-based durable deltas.

- new canon;
- knowledge / false belief;
- relationship / reputation;
- consequence residue;
- Narrative Debt status/repair deadlines;
- setup/payoff state;
- reader question activation;
- organization learning;
- offscreen process updates;
- world-evolution deltas;
- social versions / rumors;
- research dependencies;
- arc status;
- humanities report/version registration **if** a triggered analysis pass ran, without treating interpretations as canon; no report is required for an ordinary chapter under the default `opt_in` policy.

### Arc / volume commit

At larger boundaries, additionally review:

- accumulated character change;
- institutional / social transformation;
- long-horizon inheritance;
- world-aging effects;
- stale assumptions in later architecture;
- closure or transformed open questions.

Do not update a ledger merely because it exists. Record only durable state.

## 5. Dependency propagation

A change is incomplete until every **dependent** state is reconciled.

When Runtime Mode is active, the unified dependency graph in `narrative-runtime.md` is the canonical propagation structure. This section describes narrative consequences; do not maintain a second incompatible edge direction. `source -> target` always means **target depends on source**.

Examples:

- object transfer -> custody + inventories + scene packets;
- injury -> embodied state + travel + tactics + recovery assumptions + future packet assumptions;
- reveal -> actor knowledge + reader state + offscreen responses;
- route closure -> spatial graph + timeline + logistics + future scenes;
- public accusation -> social-version ledger + reputation + institutional response;
- research correction -> adopted project fact + world/timeline/spatial assumptions + affected scenes;
- rule change -> canon + hidden processes + long-horizon architecture + scenes using the old rule;
- user-approved humanities finding -> relevant thematic/character/world owner + future missions, but never automatic retroactive prose mutation;
- chapter revision -> mark sidecar reports tied to the old chapter version stale and regenerate or preserve as analysis history.

Prefer invalidation + regeneration over silent local patching when many downstream snapshots depend on the old state. Runtime impact tools may mark affected nodes, but they do not choose or apply literary repairs.

## 6. Continuity priority

When a new idea conflicts with state, use:

1. explicit source canon / user instruction;
2. already delivered or published prose;
3. necessary implication;
4. locked architecture;
5. provisional design;
6. new convenience.

Use `change-control.md` when a lower-priority idea must replace stronger state.

## 7. Minimal state for short tasks

Scale bookkeeping to project risk.

For a short continuation, a compact snapshot may be enough:

- current time / place;
- active characters;
- knowledge asymmetries;
- injuries / embodied limits / finite resources;
- relevant objects / access;
- open promises;
- immediate narrative debt;
- active rule constraints.

Do not create giant ledgers for a one-scene disposable task.

## P0-3 fact and acquisition serialization

Keep typed facts, actor acquisitions and uses in this same Story State Bundle. The optional schema subset `assets/project-schemas/temporal-epistemic.schema.json` adds no parallel database or new canon authority. Knowledge Topology owns `facts`/`knowledge_state`/`knowledge_uses`/`writer_visible_facts`; Reality Grounding owns historical `research_dependencies`. New critical records may mark `temporal_epistemic_version: 1.0.0` for explicit identity/provenance/scope/precision requirements. Older records remain readable; absent precision/applicability stays UNKNOWN. Project-format and Runtime authority are unchanged.

## Verified chapter rollover (P0-6)

Project State owns chapter approval and current final selection. No prior executable final/draft selector existed. `project_ops.py finalize-chapter` therefore imports explicit approval of **exact bytes**, never infers authority from filenames, timestamps, an Agent claim or `APPROVED reconciliation`. This is not the future P0-7 contradiction gate.

New `init` manifests emit optional `chapter_rollover: {contract_version: "1.0.0", active: true, chapters: []}`. Legacy manifests and the generic recovery template omit it. The first explicit final registration can activate an existing project. Project format stays 1.0.0; no bulk migration or fabricated old receipts.

P0-6-I — Absence Is Not Malformed Activation: only an absent chapter_rollover field represents legacy/unactivated state (UNVERIFIED). A present value must be an object with contract_version "1.0.0", strict active: true and an array of chapters; explicit null, wrong types, missing/unsupported activation fields and malformed registries fail closed as STALE with stable rollover diagnostics. No automatic deletion, repair or migration occurs. Active applicability also requires the schema-required nonnegative integer current_chapter. NOT_APPLICABLE is positively established only by a valid active empty branch registry and canonical first-chapter state, with request target cross-check; empty records alone are insufficient. Under P0-6-H it skips only predecessor index equality, while ordinary Compiler isolation/integrity checks remain mandatory.

Each chapter record has explicit `chapter_id`, positive `number`, existing `branch`, `finalizations`, `current_finalization_id`, `receipts` and optional `current_rollover`. A finalization binds project/branch/chapter, chosen project-relative prose `path`, exact `final_prose_sha256`, `algorithm: sha256-exact-bytes`, `approved_by`, `approval_ref` and immutable approved-copy evidence. `FINAL-<canonical sorted-JSON SHA-256>` identifies the approval payload. Chapter IDs are opaque; chapter numbers establish order. Within the active branch both number and ID must be unique. The next current target is one greater than the highest explicitly registered chapter number; an empty branch starts at Chapter 1. This order comes from approval records, never a file scan. Existing `current_chapter` retains its legacy state/resume meaning; it does not select final prose.

```bash
python -B scripts/storyctl.py project finalize-chapter PROJECT_ROOT --chapter-id CH-01 --chapter-number 1 --prose chapters/ch1.md --expected-sha256 EXACT_HASH --approved-by user --approval-ref USER_APPROVAL_REFERENCE
```

Caller-supplied approval provenance must reflect actual authority already granted by the author/project. Hashes verify serialization and byte identity; they do not authenticate a human message. A merely proposed draft has no record. Only this explicit registration chooses final prose. The selected file must be inside the registered chapters directory. Historical approved-copy evidence lives under that directory's `.approved`; it cannot independently select the current version. Reapproval retains old records/copies and freezes; it immediately makes old source-dependent tuples stale. Manual changes without reapproval fail live hash verification.

`current_rollover` selects an immutable reconciliation receipt by path, exact file hash and reconciliation ID, with a snapshot ID. Snapshot/receipt files are created and verified before this one Project Manifest pointer changes. Full reconciliation audits the existing canonical Story State (Lean) or active Runtime projection and branch head. Declared durable deltas use JSON-pointer `target` and must already have their exact `after` value in that canonical state. Commit via existing state/Runtime procedures first; reconciliation cannot invent or silently commit facts. Frozen snapshots use the existing Runtime snapshot wire shape; Lean freezes are materialized under the canonical state directory's `rollover-snapshots`, Runtime freezes under its existing snapshots directory. IDs bind the entire snapshot including project/branch and source finalization. They are derived exports of the existing state owner, not a second authority.

A full re-review of substantive changes creates a source-specific snapshot. Verified formatting-only receipts may reuse the previous immutable snapshot. Approval copies and freezes are bounded chapter rollover evidence, not a general document VCS. Historical receipts and their source reports are registered as history; Kernel K13 checks the selected current freeze rather than treating every historical source path as current.

For Chapter N+1, supply the exact tuple returned by a successful freeze under request `previous_chapter`:

```json
{"previous_final_chapter_id":"CH-01","previous_final_prose_sha256":"<exact bytes hash>","state_snapshot_id":"STATE-<snapshot identity>","reconciliation_id":"RECON-<receipt identity>"}
```

No field may be guessed or independently swapped. First chapter requires no predecessor tuple. Requests cannot redirect an active project's standard Project Manifest to an older manifest. Active wrong target/branch, missing final/receipt, stale file/state or mismatched provenance blocks actual compilation. Legacy is readable and reported UNVERIFIED; it never claims verified rollover freshness. To use verified rollover, explicitly register approval, review/reconcile and refresh registered derived context.

After actually regenerating/reviewing a predecessor-derived Context Index entry, explicitly record its source provenance:

```bash
python -B scripts/storyctl.py project bind-rollover-artifact PROJECT_ROOT --entry-id PREDECESSOR_SUMMARY --review-ref REVIEWED_REGENERATION_REFERENCE
```

This captures the live tuple, source-file hash, optional inline-summary hash and review reference with a canonical JSON fingerprint. It does not generate or infer summary text. Do not relabel old content as regenerated. Existing `derived_from` entry links carry the predecessor dependency; no global derived-fact DAG is added.

Optionally register actual current output paths as `canonical_paths.writer_request`, `writer_pack` and `writer_pack_manifest`, alongside `context_index`. If a pack manifest is registered, all three output/request paths are needed for a verified live pack. `storyctl status` and Kernel compare the current request/index, deterministic compiler manifest and actual pack bytes. A stale file remains historical and is not a usable current artifact. Pointer paths need not be deleted to invalidate their evidence.

Status is read-only and reports `previous_chapter_rollover.status`: FRESH, STALE, UNVERIFIED or NOT_APPLICABLE, actual/expected hashes, tuple, opaque codes and stale artifact IDs. Validators never update requests, prose, snapshots, receipts or summaries. A saved fresh flag is irrelevant.

Publication uses local staging, source rechecks and atomic replacement of the current pointer/output. Failed validation does not advance current freeze or publish a new successful pack. No distributed lock or multi-process transaction guarantee is claimed; immutable unselected staged evidence can remain after an I/O failure. Source hashes are rechecked immediately before publication.

