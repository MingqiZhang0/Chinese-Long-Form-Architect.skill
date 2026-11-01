# Spatiotemporal Scene State and Scene Packets

Use this reference when a persistent project must keep people, objects, locations, routes, access, visibility, travel, and local geometry synchronized across scenes **and those facts are causally material**. It owns the **Global Spatiotemporal World Graph**, the five-sheet **Scene Packet**, reference frames, time-indexed spatial truth, and atomic scene synchronization.

## Contents

- Core rule
- Two-layer state model
- Scene Packet contract
- Global Spatiotemporal World Graph
- Reference frames and relations
- Time-indexed truth
- Entry snapshot and exit reconciliation
- Atomic scene commit
- Propagation and invalidation
- Travel and reachability
- Precision discipline
- File layout
- Audit
- Narrative carrier integrity

## 1. Core rule

A Scene Packet is a mechanical-continuity protection, not a literary-worth gate. Scenes may legitimately have `no durable world delta`; reconcile only actual state changes.

Spatial facts are story state when later causality can depend on them.

Track only the lowest sufficient precision needed to protect:

- action;
- access;
- visibility / occlusion;
- custody;
- travel;
- evidence;
- timing;
- continuity.

Do not turn the novel into CAD. Do not leave causally important geometry to improvisation.

## 2. Two-layer state model

### Global Spatiotemporal World Graph

Owns durable or reusable facts between locations and across scenes:

- containment / parent locations;
- route and connection edges;
- distance or range when relevant;
- directional relations;
- travel modes and minimum/normal travel time;
- access conditions;
- passability;
- time windows;
- moving-platform location when needed;
- changes such as bridge collapse, road closure, new checkpoint, blocked corridor, seasonal route, damaged elevator.

Use `assets/story-state-templates/global-spatial-graph-template.md`.

### Per-scene Scene Packet

Owns the local entry state, scene-relevant people/objects/geometry, and synchronized exit state for one full scene.

A Scene Packet is **not** a prose outline. It is a local state transaction.

## 3. Scene Packet contract

Every full scene whose time/place/access/custody/geometry is causally material should have five logical sheets. Other scenes may use a compact/no-packet path when the project governance and causal risk permit it. Use the templates in `assets/story-state-templates/`.

1. `assets/story-state-templates/00-scene-construction-template.md`
2. `assets/story-state-templates/01-scene-characters-template.md`
3. `assets/story-state-templates/02-scene-objects-template.md`
4. `assets/story-state-templates/03-scene-space-template.md`
5. `assets/story-state-templates/04-scene-delta-commit-template.md`

A compact equivalent is enough for genuinely local or disposable tasks where no persistent state is at risk.

### Pre-draft transaction closure

When a planned scene is causally central and the Packet is activated before drafting, distinguish a **real packet** from a placeholder. A packet is not pre-draft ready while its central trigger, entry state, reset/transfer/custody semantics, or causally relevant actor/object differences are still deferred to “choose while writing.” This is especially important for first demonstrations of time rewind, branch divergence, evidence placement, access constraints, or custody changes.

For Writer handoff, register a Writer-safe packet/derivative in the Context Index with the Scene ID in `scenes`, and list that entry in `required_ids`. Put the Scene ID in `required_scene_ids` when omission would make drafting mechanically unsafe. `scenes` without `required_scene_ids` remains only a relevance/scoring hint.

### Construction sheet

Record only what the scene needs to establish its transaction boundary:

- scene / chapter ID;
- start and expected end time;
- global and local location;
- focalizer / camera permission;
- current pressure or objective;
- active participants and hidden processes;
- reader question;
- material research dependencies;
- possible durable delta, or explicit `none` when the scene is experiential/relational/perceptual/formal without world-state change;
- exit condition;
- downstream dependencies.

`scene-architecture.md` owns whether the scene deserves page time and what contribution/completion it should produce. A Packet must never force a fake delta to justify the scene.

### Character sheet

Snapshot scene-local state, not the character's entire biography:

- entry zone / orientation;
- body / injury / mobility;
- carried objects and usable resources;
- objective;
- relevant knowledge / belief;
- perceptual and physical reach;
- local social role;
- exit zone, carried items, and durable delta.

The canonical long-term character record remains in `project-state.md` / `character-dynamics.md`.

### Object sheet

Track causally relevant objects only:

- holder / container;
- zone;
- condition;
- orientation when it matters;
- accessibility / visibility / movability;
- stateful flags;
- scene interaction;
- exit holder, location, and residue.

Do not inventory decorative objects simply because they are visible.

### Spatial sheet

Represent enough local geometry to protect the action:

- anchors;
- containment;
- relative position;
- distance/range when needed;
- access;
- visibility / occlusion;
- barriers;
- routes;
- time validity;
- reference frame.

### Delta / commit sheet

Record the actual exit state derived from the finished prose:

- actual exit time;
- character state changes;
- object custody/location/condition changes;
- spatial/access/visibility changes;
- evidence or residue created;
- global graph updates;
- timeline and other ledger updates;
- downstream packets invalidated or revised;
- commit status.

Do not mark a scene `COMMITTED` until synchronization is complete.

## 4. Global Spatiotemporal World Graph

### Location nodes

A node may represent any level needed by the story:

```text
country
  -> city
    -> campus
      -> building
        -> floor
          -> room
            -> workbench
              -> drawer
```

Useful node fields:

- stable ID;
- parent;
- type;
- coordinate / structural frame if used;
- access state;
- condition;
- validity interval;
- last update.

### Connection edges

Useful edge fields:

- endpoints;
- distance / range;
- directional relation;
- movement mode;
- minimum and normal travel time;
- passability;
- access requirement;
- valid-from / valid-to;
- source of change.

Travel time and access are state, not eternal constants.

## 5. Reference frames and relations

Directional claims require a meaningful frame.

Use one of these when needed:

- **geographic** - north/south/east/west;
- **structural** - entrance side, stage left, corridor end, upstream/downstream;
- **actor-relative** - the character's left/right/front/back;
- **camera-relative** - useful for perception, not a durable objective world fact unless the camera position is fixed;
- **moving-platform** - bow/stern, train front/rear, vehicle left/right.

Never store durable `left/right/front/behind` without a declared frame.

Common relations include:

- inside / contains;
- adjacent_to;
- above / below;
- north/south/east/west_of;
- in_front_of / behind;
- near / far;
- between;
- touching / supported_by;
- blocked_by;
- visible_from / occluded_from;
- reachable_from;
- connected_to.

Do not use relations merely because the schema allows them. Record only what can protect later causality.

## 6. Time-indexed spatial truth

A spatial fact may be true only during an interval.

Examples:

- a bridge is passable until Chapter 18 and destroyed afterward;
- a train is at Station A at 08:10 and Station B at 08:42;
- a door is locked before the guard arrives and open afterward;
- winter snow closes a mountain road for two months;
- a room layout changes after renovation.

Prefer `valid_from` / `valid_to` or an equivalent project time index over overwriting history.

When a new state supersedes an old one, preserve the old fact if past scenes may still need auditability.

## 7. Entry snapshot and exit reconciliation

### Entry snapshot

Before drafting a full scene:

1. derive the current time and place from canonical state;
2. verify actor arrival, travel, access, injuries, and custody;
3. load the applicable spatial graph interval;
4. load only scene-relevant objects and relations;
5. verify material research dependencies are in scope;
6. instantiate the Scene Packet.

Do not copy a planned packet forward after upstream state changed.

### Exit reconciliation

After drafting:

1. read the prose as the authoritative description of what actually happened, unless it itself violates higher-priority canon;
2. derive the true exit state;
3. reconcile prose and packet;
4. repair prose or state if they disagree;
5. only then commit.

A planned delta that did not occur in prose is not canon.

## 8. Atomic scene commit

A scene is committed only when all causally dependent state has been synchronized. When Runtime Mode is active, the atomic logical order is **validated delta -> committed semantic event(s) -> refreshed projections -> downstream invalidation -> COMMITTED**. Do not directly patch projections and leave event history behind.

Examples:

- a key changes hands -> object custody + character inventory + location state + downstream packets;
- a bridge collapses -> global edge state + travel feasibility + affected timelines + future packets;
- a character breaks a leg -> body state + movement limits + travel estimates + later scene tactics;
- a door is forced open -> access state + physical residue + evidence + later visibility/security assumptions;
- a witness sees an event -> knowledge topology + witness location/visibility + possible social transmission.

`project-state.md` owns global ledger governance. This file owns the spatial/local part of the transaction.

## 9. Propagation and invalidation

Upstream change invalidates every downstream snapshot that depended on the old state.

At minimum, check dependencies from:

- character location / mobility;
- object holder / location;
- route passability / travel time;
- door / barrier / access state;
- moving platform position;
- visibility / occlusion;
- research scope that constrains the physical situation.

Do not patch one future scene manually while leaving later packets stale.

## 10. Travel and reachability

A transition can be omitted from prose while remaining required in state.

Before allowing an actor or object to appear elsewhere, verify:

- departure time;
- arrival time;
- active route;
- minimum travel time;
- access requirements;
- actor mobility / injury;
- transport availability;
- any weather, congestion, security, or institutional constraint that materially changes the route.

Use `scripts/validate_story_state.py` for mechanical checks when the project maintains the JSON state described in `state-validation.md`.

## 11. Precision discipline

Use the lowest sufficient precision.

### Low precision

Good for scenes where only broad continuity matters:

- `inside kitchen`;
- `near the door`;
- `across town, ~30 min by train`.

### Medium precision

Use when action, sightline, or evidence depends on layout:

- named zones;
- approximate distances;
- doorway / corridor / furniture relations;
- travel windows.

### High precision

Use only when exact geometry or timing drives the plot:

- locked-room mystery;
- ballistic / sightline logic;
- tightly timed pursuit;
- mechanical failure;
- collision sequence;
- synchronized transport.

False precision creates brittle maintenance without increasing realism.

## 12. File layout

A persistent project may use:

```text
state/
  global-spatial-graph.md
  scenes/
    S001/
      construction.md
      characters.md
      objects.md
      space.md
      delta-commit.md
```

Equivalent structured formats are fine. The logical separation matters more than filenames.

## 13. Audit

Before locking a scene, ask:

- Is the entry snapshot current?
- Can every participant plausibly be here now?
- Are important objects where prior state says they are?
- Are directional claims tied to a frame?
- Are access and visibility compatible with geometry?
- Are travel and timing feasible?
- Is precision no finer than the causal problem needs?
- Did any real-world dependency go stale?

After the scene, ask:

- Did prose and exit packet converge?
- Were all spatial/custody/travel deltas propagated?
- Were affected future packets invalidated or regenerated?
- Is `sync_complete` true before `COMMITTED`?

## Structured pre-draft evidence

For a required high-risk packet, bind a JSON `evidence_ref` carrying `scene_id`, `target_chapter`, `entry_state`, `trigger`, `local_transition`, `rollback_or_branch`, `retained_state`, `reverted_state`, `exit_state`, `persistent_effects`, closed `open_items`, and `transaction_status: "PLANNED" | "COMMITTED"`. Irrelevant semantics may explain NOT_APPLICABLE; they may not remain choose-later gaps. Readiness snapshots both packet and evidence bytes and requires a real eligible `scene-packet` Writer entry.

Use the manifest's `canonical_paths.scene_plan_registry` for pre-draft registration (neutral scaffold: `state/scene-plans.json`). Its `scene_transactions` rows bind `scene_id`, status and exact `evidence_sha256`. A PLANNED transition is not a committed Story State/Runtime effect. COMMITTED additionally requires an existing Runtime `event_id`; reconcile prose, append/commit real effects and refresh projections through the Runtime/Story State owners before changing that status. The formal permission check remains owned by `prewriting-readiness.md`.

## 14. Narrative carrier integrity

**P0-5-A/I:** Important narrative carriers are both content and world objects; ordinary disposable objects remain lightweight. Activate durable tracking when later reading, evidence, custody, sealing/sending, physical extent or repeated inspection matters. A background letter with only a holder/location stays readable; enrich it before consequential use, without fabricating past dates.

Story State's optional `narrative_artifacts` is a selective view of the existing object owner, not another inventory. Its `id` is the canonical object/custody `item` and Scene Packet object `id`. `type` is an extensible string; `medium` selects paper/audio/video/digital/other semantics. Copies, transcripts, photographs, forwarded messages and sent instances have distinct IDs (optional `source_artifact_ref`); text equality never merges carriers. An editable local draft cannot mutate its sent instance.

**P0-5-B/C/D:** `created_at`, `lifecycle`, `inscriptions` and provenance-bearing `events` describe content on this carrier. Creation does not imply inscription. Original layers belong to the declared original author and must precede all applicable control boundaries. Sealing alone is not loss of control. Reopening while still holding the carrier permits a separate later addition. After transfer, regain/access must be supported by canonical custody and a structured reopening/addition event; it cannot relabel a later addition as original text. A second author, annotation, later recording/edit or postscript retains its own layer, author and time. `FRAME_EXTERNAL` belongs to the surrounding narration, never the carrier's internal text.

`custody` remains canonical (`id`, `item`, `holder`, `start`, `end`, existing half-open interval). Add IDs to consequential rows only when references are needed. Inscription/access must be covered for its entire interval, not just its first instant. Structured event provenance identifies the world mechanism, not proof of real authorship or authenticity. A label such as “postscript” cannot grant access or override mailing/finalization. Use `state-validation.md` for the executable subset and `narrative-time-duration.md` for partial ordering.

**P0-5-E/F:** Causally relevant `physical_extent` distinguishes **available**, **written**, and explicitly **blank** surfaces. Paper surfaces use stable `(sheet, side)` identities; three sheets can have six available surfaces but five written surfaces. Counts validate the canonical set, never manufacture missing identities. Audio/video instead use duration and segment identity. Do not infer pages from word count, simulate handwriting capacity or require irrelevant media fields.

**P0-5-G:** `world_state` and optional chapter `snapshots` preserve material holder/location/condition/seal/extent/content-layer identity. Explicit `changes` carry a mechanism, time, actor, custody reference, provenance and matching before/after values; they update the existing object's contract. Scene sheets reference `artifact_ref` and the same object ID, snapshot only relevant fields, and reconcile actual exit deltas through the existing scene commit. A snapshot cannot declare a new identity or extent just because it appears in a later chapter. This is current structured continuity checking, not previous-chapter hash freshness.

**P0-5-H:** Delivery, possession, opening and visibility do not establish reading, knowledge, belief, authenticity or truth. P0-3 retains knowledge ownership; P0-4 retains causal responsibility. Preserve backend visibility for private carrier contents when preparing Writer context.

**P0-5-J — Explicit Scene State Cannot Be Silently Dropped:** A Scene Packet's explicit tracked artifact field is checked even when the canonical base lacks that key. Entry holder/location and supported tracked fields resolve against custody or the existing object replay; exit fields resolve at scene end. Partial Scene Packets remain legal, ordinary objects remain lightweight, and unrelated JSON fields do not acquire semantics. Missing authority is reported for review rather than treated as a match.

**P0-5-K — Access-Dependent Milestones Need Canonical Support:** A consequential physical `opened_at` must fall inside canonical custody. Custody remains half-open, so an outgoing holder is excluded at the exact end and an incoming holder is included at its exact start. Shared custody supports any named holder actually covered by a shared row. Digital artifacts use the existing delivery/opening order as limited logical support; it does not prove recipient identity or digital forensics. Opening does not create knowledge.

**P0-5-L — Lifecycle and Physical State Reconcile:** For physical carriers where seal state is represented, `sealed_at`/valid `SEAL` transitions derive `SEALED`; access-supported `opened_at`, valid `REOPEN`, or a valid `OPEN` world change derive `OPEN`; a later ordered seal derives `SEALED` again. These transitions advance the `world_state` replay seed and are compared with snapshots and Scene claims. Uncertain temporal order requires review, and sealing alone does not end author control. This is a partial-order coherence check, not a universal artifact state machine.


**P0-5-M — Holder Authority Is Single-Sourced Through Canonical Custody:** For a tracked narrative artifact, holder/access truth is owned by canonical custody. World-state, durable-snapshot, Scene-Packet, and transfer-related holder fields are claims or projections that must reconcile with custody; they are not independent holder authorities. The existing change replay starts at `created_at`, so an active `world_state.holder` asserts membership in custody at that origin. It is not replayed into future holder truth. A partial snapshot or Scene need not declare holder; an explicit holder is checked directly against custody at its observation time. Shared rows support membership, not exclusive ownership. Unknown temporal support requires review; absent holder fields remain legal.

TRANSFER `before.holder` must be supported by custody at the change point or by the uniquely referenced outgoing actor's row ending at an exact handover point. `after.holder` must be covered by incoming custody at that point. Neither field creates custody; later canonical custody supersedes the transfer projection. No epsilon, invented date, second ledger, or possession-to-knowledge inference is introduced. Legacy unactivated carriers retain warning/unknown compatibility; active claims without verifiable authority fail closed.
