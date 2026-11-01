# Event-Sourced Narrative Runtime

Use this reference for large persistent projects that need historical reconstruction, safe branch experiments, dependency-aware invalidation, or reliable state queries across many chapters. It owns the event stream, materialized projections, snapshots, semantic branches (canon and sandbox), and the unified dependency graph. It does **not** own prose, dramatic design, ordinary short-task continuity, or project-level identity/recovery; `project-operability.md` owns the Project Manifest above Runtime. Cross-layer meaning—how committed history relates to projections, actor/reader knowledge, visibility, evidence, revision, and migration—is governed by `narrative-semantics-kernel.md`.

## Contents

- Activation gate
- Runtime invariants
- Runtime contract and schema evolution
- Committed semantic event model
- Transaction and concurrency protocol
- Projections and snapshots
- Branch semantics
- Counterfactual sandbox
- Semantic merge planning
- Dependency graph and invalidation
- Why Trace and provenance
- Corrections and retcons
- Irreversibility metadata
- Runtime directory contract
- Deterministic tooling
- Garbage collection
- Failure modes

## 1. Activation gate

Do not force event sourcing onto every story. Under `project-operability.md`, Lean governance normally omits Runtime; Persistent and Forensic governance activate it because their recovery/audit guarantees depend on historical reconstruction.

Enable Runtime Mode when one or more of these are true:

- the project is expected to persist across many chapters or volumes;
- many entities change independently and historical queries matter;
- branch experiments or alternate outcomes are frequent;
- revisions regularly invalidate downstream plans;
- exact custody, knowledge, route, institution, or object history matters;
- the author needs to ask what was true at an earlier story time or draft point;
- multiple agents may commit state and need a single auditable write model.

For a short story, isolated scene, or small continuation, the live ledgers in `project-state.md` may remain the authoritative state without a runtime event store.

## 2. Runtime invariants

When Runtime Mode is enabled:

1. committed events are the durable write-side source for the semantic strata the project deliberately event-sources; **commitment/replayability does not by itself mean objective fictional canon**;
2. live ledgers, current-state files, Scene Packet registries, dashboards, and query views are typed projections/read models whose authority remains local to their semantic stratum;
3. snapshots are performance caches, never replacement history;
4. committed events are append-only;
5. correcting committed history uses an explicit compensating/corrective transition or branch/change-control path appropriate to that semantic stratum, never silent mutation of an old event;
6. provisional discoveries stay outside the committed event stream until promoted;
7. dependency invalidation is read-only until a human/Director chooses the repair;
8. branch merge is semantic and approval-gated, never an automatic line merge.

The point is not database purity. The point is reliable narrative history.

## 3. Runtime contract and schema evolution

Runtime data itself evolves. Keep representation change separate from story change. A schema migration must also preserve the semantic-kernel migration laws: event meaning/identity, branch lineage, replay-equivalent projections where no story change was intended, epistemic/reader state, secrecy provenance, OpenIssue/authorial-open-design state, and independent time axes.

- project/runtime contract version -> `runtime-schema-migration.md`;
- event-type payload evolution -> explicit `event_version` plus compatible reader/upcaster;
- mutable projection/planning migration -> deterministic project migration;
- story-canon correction -> `change-control.md`.

The current runtime should prefer backward-readable project artifacts within its declared support window. Do not rewrite old committed events just to make them look current.

Use `runtime/runtime-manifest.json` and the bundled JSON Schemas/templates for persistent Runtime projects.

## 4. Committed semantic event model

A committed event should capture **what semantic transition was durably accepted and why it matters**, not merely the resulting field value. Many Runtime events are canon-bearing world/epistemic events, but the same append-only history may also record reader-exposure, policy, authorial-decision, or analysis/governance transitions. Their target stratum keeps its own authority; event-log membership alone never promotes them to fictional canon.

Recommended fields:

- `schema_version` - event-envelope representation version when Runtime schema validation is active;
- `event_version` - semantic event-type version;
- `event_id` - globally unique stable ID;
- `branch` - semantic-history branch, normally `main`; for canon-bearing events this is the corresponding canon branch;
- `seq` - monotonic sequence within the branch;
- `event_type` - domain meaning such as `ObjectTransferred`, `FactLearned`, `RouteClosed`, `RelationshipChanged`, or typed S0/I events such as `OpenIssueResolved` / `WorkingHypothesisParked`;
- `intent` - short semantic description of the occurrence;
- `story_time` - in-world temporal position when meaningful;
- `chapter` / `scene` - narrative provenance when meaningful;
- `entity_ids` - affected stable entity IDs;
- `effects` - deterministic projection operations;
- `source` - scene commit, chapter commit, migration, user decision, research adoption, etc.;
- `dependencies` - upstream nodes required for this event to remain valid;
- `transaction_id` - atomic commit provenance;
- `correlation_id` / `causation_id` - optional provenance links when useful;
- `compensates` / `supersedes` - optional audit links;
- `reversibility` - optional narrative consequence metadata.

Prefer semantic events:

- `ObjectTransferred` over `holder changed to Li`;
- `WitnessLearnedIdentity` over `knowledge flag = true`;
- `ReaderExposureRecorded` over silently treating a reader hypothesis as world truth;
- `SecretDeclassifiedForWriter` over deleting taint ancestry;
- `OpenIssueResolved` over quietly filling an open answer field;
- `WorkingHypothesisSelectedForPlanning` over rewriting a temporary hypothesis as an authoritative constraint;
- `BridgeCollapsed` over `travel_time changed`.

When one transaction touches several strata, keep the effects conceptually typed. A Chapter commit may atomically record a world delta and reader-exposure delta without making reader state part of objective world truth. Checkpoint/import events may reconstruct several typed projections, but they must preserve the prior authority of each imported value.

`effects` exist so projections can be rebuilt mechanically. `event_type` and `intent` preserve narrative meaning.

## 5. Projection operations

The deterministic runtime may use a small generic operation set:

- `set` - set a nested value;
- `delete` - delete a nested value from the projection;
- `append` - append a value to a list;
- `add_to_set` - add only if absent;
- `remove_from_set` - remove matching list values;
- `increment` - numeric delta.

Keep projection effects boring. Complex literary interpretation belongs to the Agent, not the replay engine.

Example event:

```json
{
  "event_id": "EV-0042",
  "branch": "main",
  "seq": 42,
  "event_type": "ObjectTransferred",
  "intent": "Zhang hands the archive key to Li after the hearing",
  "story_time": 18.4,
  "chapter": 12,
  "scene": "SCN-0012-03",
  "entity_ids": ["obj-archive-key", "char-zhang", "char-li"],
  "effects": [
    {"op": "set", "path": "objects.obj-archive-key.holder", "value": "char-li"},
    {"op": "set", "path": "objects.obj-archive-key.location", "value": "char-li.inventory"}
  ],
  "source": "scene-commit",
  "dependencies": ["SCN-0012-03"]
}
```

## 6. Transaction and concurrency protocol

When multiple agents or passes can propose state changes, do not allow last-writer-wins canon mutation.

A commit transaction should contain:

- stable `transaction_id`;
- active branch;
- `expected_head_event` and optionally expected effective revision;
- purpose / source task;
- read-set or critical dependencies when useful;
- all proposed semantic events for one atomic change-set;
- unresolved blocking objections;
- validation status.

Use this protocol:

1. read branch state at revision/head `R`;
2. plan proposed events without mutating canon;
3. simulate the whole transaction in memory;
4. run runtime validation and `narrative-invariants.md`;
5. acquire the project write lock;
6. re-read the branch head;
7. if head != `R`, reject with a conflict and rebase/replan;
8. otherwise append **all events or none**;
9. make repeated identical `transaction_id` + event-ID sets idempotent; reject reuse of a transaction ID for different events;
10. preserve all pre-existing committed event bytes while appending the new records atomically;
11. if the append succeeded but task/transaction metadata did not update, a retry should reconcile that metadata from the already-committed events;
12. refresh projections and dependency impact only after append succeeds.

This is optimistic concurrency: conflicts are detected at commit rather than prevented by holding long creative locks. It is intentionally conservative for narrative canon.

A conflict is not an error to be hidden. It means another accepted story change invalidated the transaction's assumptions.

Use `scripts/runtime_tx.py`.

## 7. Materialized projections

Do not make normal writing queries replay the whole novel from Chapter 1.

Maintain query-oriented projections such as:

- current character state;
- current object custody;
- current location/access state;
- current knowledge/belief state;
- current institution state;
- embodied/body state and finite resource/capacity state when relevant;
- active hidden-process state;
- reader-state view;
- research dependency status;
- humanities finding status;
- branch-specific current world state.

A projection is disposable: if it disagrees with valid committed history for the stratum it projects, rebuild it. **Replayability does not elevate authority**: a replayed Reader Model remains heuristic analysis, and a replayed humanities status remains non-canon governance state.

`project-state.md` defines what ledgers are useful. In Runtime Mode, those ledgers are projections of the event history plus deliberate planning state that has not yet become canon.

## 8. Snapshots

Long event streams may be expensive to replay. Create snapshots at meaningful checkpoints:

- chapter boundaries;
- arc boundaries;
- volume boundaries;
- after major migrations;
- after a high-density sequence of state changes.

A snapshot should record:

- branch;
- last included event ID / sequence;
- projection schema version;
- materialized state;
- creation provenance.

Never edit history just because a snapshot is stale. Regenerate the snapshot.

## 9. Branch semantics

Use branches for experiments that should not contaminate canonical state.

Examples:

- alternate survival/death outcome;
- experimental reveal timing;
- different antagonist response;
- major Volume 2 rewrite;
- alternate ending;
- counterfactual analysis.

A branch records:

- branch name;
- parent branch;
- fork event;
- purpose;
- status: `active / merged / abandoned / archived`;
- owner / user decision when relevant.

A branch inherits the parent history only through its fork event, then appends its own events.

Do not copy-and-edit the entire state bundle as if both copies were independent truth. Reconstruct branch state from lineage plus branch events.

## 10. Counterfactual sandbox

Use a branch with status `sandbox` for bounded what-if experiments. A sandbox is not canon and must not leak into Writer context for another branch.

Typical workflow:

1. choose a fork event;
2. create two or more sandbox branches for candidate interventions;
3. apply only the changed intervention and justified downstream responses;
4. simulate actors/institutions under the same world rules unless the experiment explicitly changes a rule;
5. compare resulting projections, reader state, costs, hidden-process reactions, and irreversible consequences;
6. present differences to the user/Director without ranking unless the user asks for a non-political creative judgment;
7. archive/discard the sandbox or prepare a semantic merge plan for selected ideas.

A sandbox may alter an invariant only if branch metadata says the experiment is testing that invariant itself. A sandbox may also declare one or more OpenIssue positions as **branch assumptions**. Those assumptions remain conditional to that sandbox and do not narrow the parent Issue merely because the branch is coherent or later contributes adopted events.

Use `narrative_runtime.py compare` for state differences; interpretation remains an Agent task.

## 11. Semantic merge planning

Narrative branches cannot be safely merged like source-code text.

Before any merge:

1. identify the common fork;
2. list source-branch events after the fork;
3. list target-branch events after the fork;
4. compare affected entities and projection paths;
5. detect semantic conflicts even when files do not overlap;
6. classify source changes as `adopt / adapt / reject / needs-redesign`;
7. generate a merge plan;
8. require Director/user approval;
9. materialize approved changes as **new target-branch events**.

Never copy source events blindly into `main` when their assumptions differ. Separate branch-local exploratory assumptions from story events proposed for adoption; importing the latter does not automatically select the former as authorial truth. Any OpenIssue narrowing/resolution still requires an authorized `A` operation.

A merge plan is analysis, not canon.

## 12. Unified dependency graph

Represent consequential dependencies as directed edges:

`source -> target` means **target depends on source**.

Possible node types:

- canon fact;
- event;
- research claim;
- character state;
- knowledge fact;
- object;
- location/route;
- scene packet;
- chapter mission;
- hidden thread;
- reader question;
- OpenIssue position / working hypothesis;
- humanities finding;
- arc/volume plan.

Recommended edge metadata:

- `kind` - causal, epistemic, spatial, research, planning, reveal, object-custody, `conditional-on-hypothesis`, etc.;
- `strength` - hard / soft;
- `status` - active / retired;
- `reason`;
- `created_by`.

A changed source does not automatically rewrite targets. It marks them **affected**, **stale**, or **needs review** according to edge semantics. An authoritatively excluded OpenIssue position must not retain active `conditional-on-hypothesis` edges to live downstream work; invalidate/review that dependency closure. Parking a still-viable hypothesis does not by itself invalidate conditional artifacts.

This is an incremental-build model for narrative state: re-evaluate what depends on a changed input, not the whole project.

## 13. Why Trace and provenance

The dependency graph should support both directions:

- **impact**: what depends on this node?;
- **why trace**: what upstream facts/events/research/decisions does this node depend on?

Use Why Trace when the author asks:

- Why does this character currently distrust someone?
- Why is this scene invalid after the revision?
- Why does the Writer need this context item?
- Which research claim supports this project fact?
- Which user decision caused this branch to exist?

A useful trace preserves provenance categories rather than flattening everything into generic edges. Record, when available:

- source/target IDs;
- edge kind;
- reason;
- producing activity/task;
- responsible Agent/user;
- revision/branch;
- source event intent;
- research/document provenance.

Treat revised artifacts as new revisions derived from earlier artifacts, not as if the earlier version never existed. `semantic-revision.md` owns prose revision lineage; W3C-style entity/activity/derivation thinking is a useful mental model for traceability, not a requirement to serialize full PROV.

Use `narrative_runtime.py why`.

## 14. Corrections, migrations, and retcons

When an already committed event is wrong:

- if the prose/canon was never actually established, prefer a branch or explicit migration before publication;
- if an event must be corrected in the audit history, append a corrective/compensating event;
- if prior reader-facing canon changes, use `change-control.md` and label the retcon honestly;
- if a later revelation changes interpretation but not literal fact, add new events/facts without rewriting old truth.

Do not use event-sourcing vocabulary to disguise a retcon as a twist.

## 15. Irreversibility metadata

Consequences have different reversal costs. Record this only when it matters.

Suggested levels:

- `highly-reversible` - ordinary plan, minor misunderstanding;
- `costly-reversible` - job loss, legal filing, public conflict, damaged trust;
- `low-reversibility` - death, permanent injury, infrastructure destruction, irreversible disclosure;
- `information-irreversible` - a secret has entered another actor/institution/public channel even if later denied.

Optional metadata:

- reversal cost;
- required compensating event;
- residue after reversal;
- who still remembers/possesses evidence;
- institutional/public persistence.

Use this to prevent cheap resets, not to score drama mechanically.

## 16. Runtime directory contract

A large project may use the reusable starter files in `assets/runtime-templates/` and a project-local layout such as:

```text
runtime/
  runtime-manifest.json
  events.jsonl
  branches.json
  dependencies.json
  invariants.json
  narrative-debt.json
  transactions/
  projections/
    current-state.json
  snapshots/
  discovery/
  observatory/
```

These are project files, not bundled Skill state.

The event stream and branch registry are durable. Projections, snapshots, context packs, dashboards, and generated reports can be rebuilt.

## 17. Deterministic tooling

Use `scripts/narrative_runtime.py` for:

- validating event/branch/dependency structure;
- replaying a branch into a materialized state;
- writing a snapshot;
- creating active/sandbox branch records;
- computing dependency impact and upstream Why Trace;
- comparing branch projections;
- generating a merge plan without applying it.

Use `scripts/runtime_tx.py` for expected-head optimistic concurrency, idempotent atomic event append, and invariant-gated commits.

Use `scripts/runtime_schema.py` for Runtime contract validation and representation migration.

Use `scripts/validate_invariants.py` for project-defined hard/soft constraint checks.

Use `scripts/story_ops.py` for higher-level story queries after the relevant state projection exists.

Do not ask the script to decide whether a character choice is good, whether a theme should deepen, or whether a branch should become canon.

## 18. Narrative garbage collection

Event history is not garbage. Do not delete committed events merely to reduce clutter.

Safe candidates for archival/removal include:

- obsolete generated context packs;
- stale projection files that can be rebuilt;
- invalidated Scene Packets after their replacement is committed and provenance remains available;
- abandoned branch working notes after the branch is archived;
- expired caches;
- superseded schema-validation reports or dry-run migration outputs that are reproducible;
- duplicate temporary exports;
- superseded provisional discoveries that never became canon.

Keep:

- committed event streams;
- explicit migrations/retcons;
- branch lineage;
- user decisions;
- evidence/source history needed for audit;
- published-version records.

Prefer **archive** over delete when future forensic value is plausible.

## 19. Failure modes

Reject these patterns:

- current-state files edited directly while the event stream says something else;
- every tiny prose gesture becoming an event;
- projection operations that encode literary interpretation;
- branches copied as whole duplicate universes with unclear lineage;
- automatic merges after a major causal divergence;
- dependency graphs with edges but no direction semantics;
- snapshots treated as canonical history;
- provisional discovery written directly into committed events;
- deleting old events to make a retcon look clean;
- event sourcing used for a one-scene task where a simple state snapshot is sufficient;
- last-writer-wins commits from stale Agent state;
- rewriting old events during schema migration;
- sandbox events leaking into `main` context;
- Why Trace edges with no provenance or reason;
- auto-merging a counterfactual because the state diff looks small.

Auditability correctness is owned by `scripts/dependency_activity.py` (shared edge
activity), `scripts/event_provenance.py` (versioned provenance closure), and the
production runtime/transaction owners. See `docs/auditability-contract.md` for
authority, temporal boundaries, retry identity and legacy handling. Run
the `scripts/auditability_core_test.py` entrypoint for the permanent seven-gap suite;
`--mutations` proves its source-mutation oracles and `--smoke` is in Fast.
