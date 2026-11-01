# Runtime Schema, Compatibility, and Migration

Use this reference when the machine-readable **Narrative Runtime** contract changes: event envelopes, branch/dependency files, transaction records, invariant files, snapshots, projections, or other Runtime artifacts. It owns **schema identity, compatibility policy, migration/upcasting discipline, and project-runtime manifests**. It does not own fictional retcons; use `change-control.md` for story-canon change. It also does not own the overall project's file-layout/recovery format; use `project-operability.md` for `project-manifest.json`, governance profiles, Resume Capsules, and whole-project format migration. Every representation-only migration must satisfy the preservation laws in `narrative-semantics-kernel.md`; schema validity alone is insufficient.

Runtime/project/reconciliation schema validation requires `jsonschema>=4.18.0,<5.0.0`, declared in the Skill-root `requirements.txt`. Prefer `scripts/storyctl.py` so the cheap capability probe runs before dependency-sensitive work; for direct diagnosis use `python scripts/storyctl.py capability check runtime`.

## Contents

- Why schema evolution is separate from canon change
- Version layers
- Runtime manifest
- Compatibility policy
- Event versioning and upcasting
- Runtime artifact migrations
- Migration safety protocol
- Unsupported versions
- Tooling and templates
- Failure modes

## 1. Schema change is not canon change

Keep these questions separate:

1. **Did the story change?** -> canon/change control.
2. **Did the stored representation change?** -> schema migration.
3. **Did our interpretation of an old event change?** -> projection/upcaster logic, unless reader-facing canon itself changed.

Renaming `holder` to `custodian_id` in a JSON record is not a retcon. Changing who held the key is.

Do not use migration machinery to hide a story change.

## 2. Version layers

Use explicit versions at four different layers when Runtime Mode is active.

### A. Runtime contract version

The project-wide machine contract used by this Skill/runtime. Store it in `runtime/runtime-manifest.json` as a semantic version such as `3.0.0`.

### B. JSON Schema dialect

Every bundled JSON Schema should declare its JSON Schema dialect with `$schema`, normally Draft 2020-12, and a stable `$id`.

This is **not** the same as the project Runtime contract version.

### C. Artifact schema version

Machine-readable files that persist across runs should identify their artifact schema version when practical, for example:

- branch registry;
- dependency graph;
- snapshots;
- transaction proposals;
- invariant catalogs;
- narrative-debt register;
- semantic-revision impact reports;
- OpenIssue / authorial-open-design records stored in Story State when their representation changes.

### D. Semantic event-type version

Long-lived committed events may outlive the code that produced them. Give each semantic event type an `event_version` when its payload/effect meaning can evolve independently.

Do not conflate:

- runtime contract `3.0.0`;
- event envelope schema `2.0.0`;
- `ObjectTransferred` event version `1.1.0`.

## 3. Runtime manifest

A Runtime project should have one authoritative manifest.

Recommended fields:

- `runtime_schema_version`;
- `schema_dialect`;
- `project_id`;
- `current_branch`;
- `compatibility_policy`;
- supported minimum reader version when relevant;
- file locations for events, branches, dependencies, invariants, debt, and projections;
- migration history;
- last successful validation time/revision when useful.

Do not duplicate branch truth in the manifest. The manifest points to the branch registry; the branch registry owns lineage.

## 4. Compatibility policy

For persistent fiction projects, prefer a **backward-readable** policy:

> the current Runtime should be able to read every supported older project artifact without rewriting committed history first.

Use these categories conceptually:

- **backward-compatible** - current reader can consume older data;
- **forward-compatible** - older reader can consume newer data;
- **full-compatible** - both directions work;
- **breaking** - explicit migration/upcast is required.

For our project runtime, optimize primarily for **backward-transitive reading within the declared support window**. Do not pretend arbitrary future writers/readers will be compatible.

### Version increment guidance

Use semantic-versioning logic for the public Runtime contract:

- **PATCH** - validation/documentation fixes that do not change valid stored data;
- **MINOR** - backward-compatible optional/additive fields or capabilities;
- **MAJOR** - incompatible representation or semantic changes that require migration/upcasting.

A version number communicates compatibility intent; tests and migration code must prove the claim.

## 5. Event versioning and upcasting

Committed history is append-only. Do **not** bulk-edit old events merely because the current handler prefers a new shape.

Prefer this order:

1. tolerate old optional/missing fields directly when safe;
2. normalize old payloads on read;
3. use a small ordered upcaster chain for incompatible structural changes;
4. create a new event type/version when meaning itself changed;
5. rewrite stored history only for exceptional corruption recovery with explicit audit records.

An upcaster transforms an old serialized representation into the current in-memory representation **without changing the original event in the store**.

Keep upcasters:

- deterministic;
- side-effect free;
- ordered;
- individually testable;
- explicit about from-version and to-version;
- unable to invent story facts that were not present or logically forced.

If a migration needs creative interpretation, it is no longer a mere schema upcast. Escalate to the Director/user.

## 6. Runtime artifact migrations

Mutable derived/project artifacts may be migrated in place **only after** preflight and backup because they are not append-only history.

Examples:

- projection files;
- context indexes;
- debt registers;
- reader simulation reports;
- planning artifacts;
- task-order records.

A migration descriptor should state:

- migration ID;
- `from_version`;
- `to_version`;
- artifact kinds;
- compatibility class;
- deterministic transform;
- preconditions;
- post-validation;
- reversibility or restore path;
- whether event upcasting is also required.

Migrate one version hop at a time when possible. Chained small migrations are easier to audit than a single opaque leap.

### OpenIssue migration rule

Treat OpenIssue migration as a two-phase process whenever old records carry weaker/ambiguous semantics:

1. **lossless structural preservation** - keep stable question IDs, original mode/status, listed candidates, constraints, clues, decision owner/horizon, and provenance without inventing a stronger interpretation;
2. **semantic adjudication** - only then classify/upgrade the record to v2 concepts such as resolution policy, domain semantics, position viability, or fictional `preserve_open`.

Legacy `AUTHORIAL_UNKNOWN` candidate lists are **open-ended by default**. Never infer that old `viable_answers` were exhaustive merely because the array is finite.

Legacy `DELIBERATELY_UNRESOLVED` is semantically overloaded. It may mean authorial indecision, fictional incompleteness, reader-facing ambiguity, or interpretive plurality. Do not auto-map it to one v2 meaning. Preserve non-collapse and emit `REVIEW_REQUIRED` until a semantic owner classifies it.

Do not rename/move the Story State serialization key solely for conceptual cleanliness if doing so would create unnecessary project migration risk. New v2 OpenIssue records may continue under the compatibility key `authorial_unknowns`; schema/version fields distinguish the stronger contract.

## 7. Migration safety protocol

Before migration:

1. validate the current project;
2. record current Runtime manifest and branch heads;
3. back up mutable artifacts;
4. confirm no blocking multi-agent transaction is open;
5. dry-run migration and list files/events affected;
6. refuse migration if unknown newer schemas are present.

During migration:

1. acquire the project/runtime write lock;
2. migrate mutable artifacts in dependency order;
3. install/activate event upcasters rather than rewriting old events;
4. update schema/version metadata last;
5. record the migration activity/provenance.

After migration:

1. validate schemas;
2. replay event streams;
3. rebuild disposable projections/snapshots as needed;
4. run narrative invariants;
5. verify the applicable `narrative-semantics-kernel.md` M1-M10 preservation laws—especially event bytes/identity, replay equivalence, branch lineage, epistemic/reader/security state, OpenIssue/authorial-open-design state, provenance, and the three time axes;
6. compare key pre/post projections where no semantic change was intended;
7. release the lock only after success.

If validation fails, restore mutable artifacts and leave the old manifest/version authoritative.

## 8. Unsupported versions

Fail closed when:

- the project uses a newer **major** Runtime version than the current Skill understands;
- an event type/version has no safe reader/upcaster;
- migration history is discontinuous;
- a schema claims compatibility that validation disproves.

Do not guess through an unknown contract.

## 9. Tooling and templates

Bundled resources:

- `assets/runtime-schemas/runtime-manifest.schema.json`
- `assets/runtime-schemas/event.schema.json`
- `assets/runtime-schemas/branches.schema.json`
- `assets/runtime-schemas/dependencies.schema.json`
- `assets/runtime-schemas/snapshot.schema.json`
- `assets/runtime-schemas/transaction.schema.json`
- `assets/runtime-schemas/invariants.schema.json`
- `assets/runtime-schemas/revision-impact.schema.json`
- `assets/runtime-schemas/narrative-debt.schema.json`
- `assets/project-schemas/open-issue.schema.json`
- `assets/discovery-templates/open-issue-template.json`
- `assets/runtime-templates/runtime-manifest-template.json`
- `assets/runtime-templates/transaction-template.json`
- `scripts/runtime_schema.py`

Use `runtime_schema.py validate-project` for a whole project, `validate-artifact` for one structured artifact, and `migrate-legacy` only for the documented legacy Runtime format. `migrate-legacy` must create a neutral empty invariant registry when one is absent; examples are never migrated into canon as default laws. Never invent a migration ad hoc inside prose work.

## 10. Failure modes

### Version-by-date

`2026-09` is useful metadata but poor compatibility semantics. Keep date/build metadata separate from contract version.

### Rewrite-the-past migration

Editing every historical event to look current destroys auditability.

### One global version for everything

Project contract, event envelope, and individual event meaning evolve at different rates.

### Silent default invention

A migration adds a field and fabricates a story fact, exhaustive candidate domain, or resolution policy as its default. Defaults may represent representation defaults, not fictional facts unless the old state logically forces them.

### Openness strengthening by migration

A legacy `DELIBERATELY_UNRESOLVED` record is automatically reinterpreted as fictional indeterminacy or an old finite candidate list is treated as exhaustive. Repair: preserve the weaker legacy meaning and require semantic adjudication.

### False compatibility

A parser can deserialize a file but its meaning changed. Structural readability is not semantic compatibility.

## 11. Project-Poetics compatibility note

`Project Poetics` is author/planning state, not Narrative Runtime world state. Runtime schema migrations must therefore remain semantically neutral about aesthetic choices.

When project manifests gain optional `canonical_paths.project_poetics`, `optional_artifacts`, or `poetics_override_refs` fields:

- older projects without these fields remain readable;
- absence means "not yet represented", not a default poetics;
- migration may add empty optional arrays or pointers but must not infer a theme, active capability, progression model, or style;
- `migrate-legacy` must not create Project Poetics merely because the current Skill supports it; if the owner is absent, use the separate explicit `project_ops.py ensure-poetics` bootstrap;
- `ensure-poetics` may create only the blank provisional template and must record provenance with `inference_performed=false`; it is representation bootstrap, not literary adjudication;
- Runtime replay equivalence must not depend on Project Poetics metadata unless a mechanically decidable formal commitment has separately been promoted to an invariant.
