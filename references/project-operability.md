# Project Operability, Governance Profiles, and Resume

Use this reference when a long-form project must survive many chats, model contexts, Skill upgrades, or long periods of inactivity. It owns the **project-level manifest**, governance intensity, Resume Capsule, and whole-project representation migration. It sits above Narrative Runtime: Lean projects may use it without Runtime Mode. Literary poetics are an orthogonal planning axis owned by `project-poetics.md`; governance profile never decides what kind of novel the project should become.

## Contents

- Project-level contract
- Project Manifest
- Governance profiles
- Resume Capsule
- Doctor / verification
- Whole-project format migration
- Upgrade and downgrade rules
- Failure modes
- Tooling

## 1. Project-level contract

A novel may outlive any single context window and any single Skill version. Do not make project recovery depend on remembering where files happen to live.

Maintain one authoritative `project-manifest.json` for substantial persistent projects. It identifies the project and points to canonical artifacts; it does **not** duplicate their contents and it does not become fictional canon.

Keep three layers distinct:

1. **Project Manifest** - project identity, current branch/chapter, governance profile, canonical artifact pointers, context generation, project-format migration history.
2. **Story State / Runtime** - fictional state and, when active, committed narrative event history.
3. **Author/planning state** - Project Brief, Project Poetics, long-horizon plans, optional planning artifacts, and approved scoped overrides.
4. **Working artifacts** - chapter missions, Scene Packets, compiled contexts, analysis, temporary plans, reports.

A Resume Capsule is generated from the first two layers. It is a recovery artifact, not a new source of truth.

## 2. Project Manifest

Use `assets/project-schemas/project-manifest.schema.json` and `assets/project-templates/project-manifest-template.json`.
The reusable manifest template starts at **Lean** governance, matching `project_ops.py init`; add Persistent/Forensic subsystems only after the project's actual failure modes justify them.
A fresh Lean `init` creates neutral state, chapter/scene directories and prewriting skeletons for Cast, optional World, volume architecture/chapter evidence, readiness, missions, context request/index, scene plans and campaign assessment. It preserves every existing file and verifies the project before writing the manifest. Skeletons start OPEN/BLOCKED/unassessed, contain no identities or literary facts, and never activate World or declare maturity. Persistent/Forensic initialization must already have their required artifacts or should start Lean and escalate later. Legacy migration never scaffolds or rewrites story data.

Core fields:

- `project_format_version` - version of the overall project representation, distinct from Runtime schema version;
- `project_id` - stable project identity; reuse the Runtime `project_id` when Runtime Mode already exists;
- `governance_profile` - `lean`, `persistent`, or `forensic`;
- `current_branch`;
- `current_chapter`;
- `last_committed_event` when Runtime Mode exists;
- `context_generation` - monotonic generation marker for resumable context governance; bump it when canonical context-selection/security inputs materially change so old packs can be recognized as stale;
- `enabled_subsystems`;
- `optional_artifacts` - active/provisional/inactive planning artifacts that are not universal requirements;
- `poetics_override_refs` - project-relative references to approved arc/chapter/scene poetics overrides;
- `humanities_analysis_policy` - optional scheduling policy for nonbinding humanities sidecars; absent means `opt_in`, so ordinary chapters do not run analysis; modes are `opt_in`, `milestone`, `diagnostic`, or `custom`;
- `canonical_paths` - pointers to live canonical artifacts/directories, including optional `project_poetics`; an optional `reasoning_intensity_config` may point to the project-level execution-policy sidecar without making it story canon;
- `migration_history`.

Do not put hidden story answers, character dossiers, summaries of canon, or prose inside the manifest. Keep paths project-relative and reject path traversal.

The manifest should make these questions answerable without project archaeology:

- What project is this?
- Where is its current state?
- Which branch/chapter is live?
- Is Runtime Mode enabled?
- Which context index and secret registry are authoritative?
- Which governance rules are intentionally active?
- Where is the current Project Poetics artifact, if persistent?
- Which optional planning artifacts and scoped poetics overrides are active?
- What representation migrations have occurred?

## 3. Governance profiles

Use the smallest profile that preserves the project's real risks. Governance is a reliability tool, not a badge of seriousness.

The machine-readable defaults, subsystem dependencies, and canonical-path requirements live in `assets/project-templates/governance-profiles.json`.

### Lean

Use for mostly linear, relationship-driven, or otherwise low-branch long fiction where explicit continuity matters but full event sourcing would add more friction than reliability.

Required baseline:

- Project State;
- Chapter Mission;
- scene-local state / Scene Packet as needed.

Do **not** activate Runtime, branches, invariants, secret registries, or Observatory merely because the project is long.

### Persistent

Use when continuity must survive many chapters and contexts, especially with meaningful research dependencies, reader-state management, hidden processes, or planning invalidation.

Add as the durable baseline:

- Reader Model;
- Context Compiler;
- Narrative Runtime;
- dependency graph.

Enable Reality Grounding / research freshness only when the project actually has external evidence whose scope can go stale. Enable Observatory when read-only drift/health views materially reduce maintenance risk; it is useful but not a tax every Persistent project must pay.

### Forensic

Use when semantic mistakes are unusually expensive: time loops, counterfactual branches, mystery-heavy architecture, multiple canon branches, high-impact retcons, strict role isolation, or audit-sensitive collaborative workflows.

Add:

- Observatory;
- Semantic Revision;
- project-specific invariants;
- role isolation;
- branches;
- prose-state reconciliation;
- explicit provenance.

Research remains conditional even here: a Forensic fantasy with no external evidence dependency does not need a fake research-freshness subsystem.

### Profile law

Escalate when complexity actually appears. Do not auto-downgrade an established project because doing so may silently remove protections the author relied on. A user/Director may deliberately simplify after reviewing what will be lost.

A higher profile does not require every optional subsystem to be active in every chapter. In particular, enabling `humanities-sidecar` does not imply per-chapter execution: scheduling is governed separately by `humanities_analysis_policy`, whose default/absence is `opt_in`. It also does not require more of the novel's meaning to be formalized. Governance intensity, semantic formalization, and literary poetics are separate axes. A quiet domestic project may need Forensic state protection, while an action-heavy project may remain Lean. Use `formalization-boundary.md` to preserve productive ambiguity even under Forensic provenance and `project-poetics.md` to determine literary priorities.

Reasoning Intensity is a third, orthogonal axis. `Low / Medium / High / XHigh / Max` controls optional semantic search/verification for the current task; it does not upgrade/downgrade `lean / persistent / forensic`, and lower reasoning intensity never disables protections required by the active governance profile. See `reasoning-intensity.md`.

## 4. Resume Capsule

Generate a fresh Resume Capsule at the start of a new context, after a long hiatus, after a project-format migration, or when canonical pointers may have changed.

The capsule should contain only recovery information:

- project identity/version/profile;
- current branch/chapter;
- Runtime head when present;
- canonical pointers;
- active story pressures;
- reader foreground questions;
- open authorial unknowns;
- stale research count;
- Project Poetics path/status and active scoped override refs;
- optional planning artifacts currently active/provisional.

Do not copy the capsule directly into a blind Writer context. It is Director-facing and may reference author-level state. Resume the Director from the capsule, then compile the Writer's least-privilege context normally.

Do not manually maintain a prose recap that can drift from state. Regenerate the capsule from canonical artifacts.

## 5. Doctor / verification

Before resuming a long-idle project or after moving files, verify:

- manifest schema;
- canonical paths exist and remain inside project root;
- manifest chapter agrees with Story State;
- project ID / branch agree with Runtime Manifest when Runtime is enabled;
- profile-required subsystems are actually enabled;
- context index exists when context compilation is enabled;
- recorded Runtime head is not stale.

Warnings may describe optional artifacts that have not been created yet. An optional artifact becomes an error only when the manifest/project explicitly marks it active and a downstream operation requires it. Identity or chapter/branch disagreement is not a harmless warning: fix it before drafting.

Project Doctor proves project identity/recovery consistency; it does **not** prove Chapter 1 readiness. Use the separate prewriting readiness gate for activation coverage, opening anchors, long-horizon chapter/volume convergence, Scene Packet handoff, and actual Writer-pack provenance/taint compilation. A Doctor `0 errors / 0 warnings` result must never be paraphrased as `DRAFT_READY`.

## 6. Whole-project format migration

Project-format migration changes **representation**, not story meaning.

Keep it separate from:

- Runtime artifact migration (`runtime-schema-migration.md`);
- fictional retcon / canon migration (`change-control.md`);
- prose revision (`semantic-revision.md`).

The initial supported migration is:

`legacy-unversioned -> project-format 1.0.0`

It creates `project-manifest.json` around an existing project without rewriting prose, Story State, committed Runtime history, or inventing Project Poetics. If the legacy project has no existing Project Poetics artifact at the project-level canonical location, the migrated manifest intentionally leaves `canonical_paths.project_poetics` absent and Project Doctor emits an advisory warning.

Establish Project Poetics only through the explicit neutral bootstrap:

```bash
python scripts/project_ops.py ensure-poetics PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT --reason "legacy project adopting Project Poetics owner"
```

`ensure-poetics` is a representation migration, not an aesthetic inference pass. It creates the canonical artifact from the blank provisional template, records structured `project_poetics_provenance` plus a migration-history entry, increments context generation so pre-bootstrap compiled packs cannot masquerade as current, and records `inference_performed=false`. It must not fill theme, progression, voice, active capabilities, do-not-optimize rules, or any other literary commitment. Re-running it after the canonical artifact exists is idempotent and must not rewrite author/planner content. If an unowned file already occupies the target path, the command refuses silent adoption; review that file explicitly before making it authoritative.

For future versions:

1. inspect source version;
2. generate a migration plan;
3. preserve original artifacts until verification passes;
4. migrate one representation hop at a time;
5. run Project Doctor plus the relevant Runtime/state/context validators;
6. prove that no fictional fact was fabricated merely to satisfy a new schema;
7. record migration provenance.

If migration requires deciding what happened in the story, stop: that is change control, not format migration.

## 7. Upgrade and downgrade rules

Profile escalation may be suggested when one or more risks become material:

- repeated context overflow or secret leakage risk;
- branch/counterfactual work;
- costly continuity failures;
- stale research across long real-world timelines;
- many downstream dependencies;
- repeated semantic revisions;
- collaborative role separation.

Do not infer that a genre requires a profile. A quiet relationship novel may remain Lean for hundreds of chapters; a ten-chapter time-loop mystery may justify Forensic.

Do not automatically downgrade. If simplification is user-approved, list which guarantees will disappear before editing the manifest.

## 8. Failure modes

### Manifest-as-wiki

The manifest grows into another world bible. Repair: replace duplicated content with canonical paths.

### Runtime monopoly

Every project is forced to enable event sourcing because Runtime has a manifest. Repair: keep Project Manifest above Runtime and let Lean projects omit Runtime entirely.

### Resume recap drift

A hand-maintained recap disagrees with live state. Repair: regenerate the Resume Capsule from canonical artifacts.

### Governance theater

A simple project carries Forensic machinery that nobody uses. Repair: choose the smallest profile justified by actual failure cost.

### Silent representation migration

A Skill upgrade changes field meanings without a migration record. Repair: version the project format and verify migration before drafting.

## 9. Tooling

For ordinary Agent discovery, enter through `scripts/storyctl.py project`; it delegates to the canonical backend below without duplicating project logic. Use `scripts/project_ops.py` directly for backend-specific debugging or documentation:

```bash
# Wrap an existing unversioned project without rewriting story data
python scripts/project_ops.py migrate-legacy PROJECT_ROOT --profile persistent

# Explicitly establish a blank/provisional Project Poetics owner after legacy migration
# when the legacy project did not already have one. This does not infer poetics.
python scripts/project_ops.py ensure-poetics PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT

# Verify identity, paths, chapter/branch agreement, and profile contract
python scripts/project_ops.py verify PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT

# Verify prewriting readiness separately from Project Doctor
python scripts/storyctl.py readiness PROJECT_ROOT/project-manifest.json PROJECT_ROOT/planning/prewriting-readiness.json --root PROJECT_ROOT --json

# Generate a Director-facing recovery capsule
python scripts/project_ops.py resume PROJECT_ROOT/project-manifest.json --root PROJECT_ROOT --out PROJECT_ROOT/resume-capsule.md

# Inspect compact identity data
python scripts/project_ops.py inspect PROJECT_ROOT/project-manifest.json

# Initialize a new project at the Lean baseline
python scripts/project_ops.py init PROJECT_ROOT --project-id PROJECT-ID

# Raise governance intensity after the required protection artifacts exist
python scripts/project_ops.py set-profile PROJECT_ROOT/project-manifest.json forensic

# Configure optional humanities analysis; ordinary chapters default to opt-in only
python scripts/project_ops.py set-humanities-policy PROJECT_ROOT/project-manifest.json milestone --milestone arc-end --milestone volume-end

# Invalidate old context-pack generations after canonical context/security inputs change
python scripts/project_ops.py bump-context PROJECT_ROOT/project-manifest.json --reason "secret registry updated"

# Check whether a representation migration is needed
python scripts/project_ops.py plan-migration PROJECT_ROOT/project-manifest.json
```

When a Runtime Manifest already exists, `migrate-legacy` reuses its `project_id` and refuses an explicitly supplied conflicting ID. `set-profile` is transactional: it validates the candidate manifest before writing it, refuses a profile escalation whose required artifacts are not actually present, refuses a downgrade unless `--allow-downgrade` is explicit, and even then preserves already-enabled subsystems rather than silently deleting protections.
