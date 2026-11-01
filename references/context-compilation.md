# Context Compilation and Leakage Control

Use this reference when a project is large enough that the Writer, Planner, Auditor, or Analyst should not ingest the entire project state at once.

## Contents

- Core principle
- Roles and information boundaries
- Context index
- Context request
- Selection order
- Future-leak control
- Compression and omission
- Writer contract
- Deterministic compiler
- Audit

## 1. Core principle

Treat context selection as a compilation problem, not as "read everything that may be relevant."

A project may contain far more state than a drafting agent should see. Compile the smallest sufficient context for the current role, chapter, scene, and risk. When Runtime Mode is active, compile from the **active canon branch projection** and branch-scoped planning artifacts; never mix sibling-branch facts unless the task explicitly compares branches.

Use:

```text
project state + scoped Project Poetics + target task + role permissions + token budget
    -> relevance filtering
    -> future-leak filtering
    -> required-state check
    -> compression
    -> context pack
```

The context pack is a temporary working artifact. It is not canon and must not become a second state store. This module implements role visibility, taint propagation, and declassification metadata; `narrative-semantics-kernel.md` owns their cross-layer information-flow laws, including transitive taint closure and the rule that declassification changes permission without erasing provenance.

## 2. Roles and information boundaries

Different roles may receive different views of the same project.

- **Director / Orchestrator** may inspect the broad architecture and future plan needed to route work.
- **Research Grounder** receives research questions and adopted project facts, not hidden prose intentions unless necessary.
- **World-State Simulator** receives current world state, offscreen processes, logistics, and causal constraints.
- **Causal Architect / Planner** may inspect future architecture necessary for planning.
- **Writer** receives only a **sanitized Writer Mission**, a **Writer-safe scoped Project Poetics derivative**, permitted POV knowledge, any causally required Scene Packet, relevant character/location/object state, a Writer Reader Brief when needed, active capability references, active threads, Writer-safe OpenIssue commitment boundaries, and explicitly authorized future hints. Raw authorial positions/working hypotheses and the full Reader Model are not Writer inputs by default.
- **Auditor / Red Team** may inspect broader state than the Writer so it can find contradictions.
- **Reader Simulator** receives only reader-visible prose/recaps available by the target point plus a heuristic reader profile. Hidden canon, dependency graphs, intended answers, and future architecture are forbidden except in explicit rereader mode.
- **Revision Analyst** receives before/after chapter text, mechanical alignment, active branch, and only the local authoritative state needed to classify possible semantic impact; it does not receive write authority.
- **Humanities Analyst** receives the written chapter and enough context to avoid obvious misreading, but must not receive hidden future answers merely to make its interpretation look clever.
- **Committer / Updater** receives the written result plus authoritative state needed to reconcile deltas.

Do not give the Writer raw long-horizon spoilers or OpenIssue candidate answers merely because they exist. Distill any future dependency the Writer genuinely needs into a Writer-safe derivative, commitment boundary, or authorized hint. **Negative spoilers are still spoilers**: `do not reveal X` is unsafe when `X` is a hidden answer/candidate the Writer should not know.

For governed authorial openness, raw `open-issue-candidates` / `authorial-possibility-space` entries are backend/planner material and are deterministically blocked from Writer compilation. Give the Writer `open-issue-boundary` derivatives containing authoritative constraints, observable handling permission, and escalation boundaries without enumerating hidden positions. Use `assets/tooling-templates/open-issue-writer-boundary-template.md`; `open-issue-semantics.md` owns the semantic contract.

For drafting, derive safe artifacts when needed:

- **Writer Mission** from the author/planner Chapter Mission;
- **Writer Reader Brief** from the full Reader Model;
- **Scoped Project Poetics derivative** from authoritative project/arc/chapter/scene poetics, containing only active salience/progression/form/do-not-optimize commitments and capability names required now. Pair it with the thin provenance envelope defined by `project-poetics.md`; never compile a bare derivative path.

Use `assets/prewriting-templates/chapter-writer-mission-template.md` and `assets/prewriting-templates/writer-reader-brief-template.md`. Keep literal withheld answers in author/planner/backend artifacts only.

## 3. Context index

For deterministic packing, maintain an optional `context-index.json` with entries such as:

```json
{
  "entries": [
    {
      "id": "chapter-12-writer-mission",
      "path": "context/chapter-12-writer-mission.md",
      "kind": "mission",
      "priority": 100,
      "required": false,
      "roles": ["writer"],
      "visibility": "writer-visible",
      "available_from_chapter": 12,
      "available_to_chapter": 12,
      "chapter": 12,
      "characters": ["lin"],
      "locations": ["north-station"],
      "threads": ["T-07"]
    }
  ]
}
```

Useful metadata:

- `id` - stable identifier;
- `path` - project-relative file path;
- `kind` - mission, poetics, poetics-capability, scene-packet, knowledge, character, location, object, thread, research, style, recent-prose, reader-state, world-state, etc.;
- `priority` - project-specific tie-breaker;
- `required` - whether omission makes the task unsafe **while the entry is eligible for this role/chapter**; prefer request-scoped `required_ids` for chapter-local Mission/Scene Packet artifacts instead of leaving them permanently hard-required in the index;
- `roles` - which roles may receive the entry;
- `visibility` - use `reader-visible` for blind Reader material, `writer-visible` for safe drafting material, and role-scoped `role-internal` only with explicit `roles`; reserve `author-only`, `backend-hidden`, or `future-answer` for protected backend material;
- `branch` / `branches` - which canon branch projections may receive the entry when Runtime Mode is active;
- `available_from_chapter` / `available_to_chapter` - epistemic availability window; chapter-local Writer Mission/Reader Brief/Scene Packet entries should normally set both bounds to the target chapter so they retire automatically on rollover;
- `chapter` - chapter most directly associated with the artifact;
- relevance tags such as `characters`, `locations`, `threads`, `research`, `scenes`, and `poetics_capabilities`;
- optional `summary` and `token_estimate`;
- `tainted_by` - opaque semantic secret IDs directly informing this artifact;
- `derived_from` - **context-entry IDs, never file paths**, from which this artifact was derived, so secret taint can propagate even after paraphrase; a path-looking value that is not an entry ID leaves provenance open and must block required Writer material;
- `declassified_for` / `declassification` - explicit reviewed release of an otherwise tainted artifact to named roles. Prefer structured `declassification` with `roles`, `status`, and explicit `secret_ids`; use `all_taints: true` only when every inherited secret is genuinely released. Never declassify merely to make a compile pass.

Do not encode hidden future truth into a Writer-visible summary, mission, reader brief, disclosure warning, or negative instruction. A literal answer remains leaked even inside “do not reveal ...”.

## 4. Context request

A context request should declare:

- optional `project_manifest` path so project branch/context-generation/secret-registry defaults can be resolved from the project-level entrypoint;
- active canon branch when Runtime Mode is enabled;
- target chapter;
- optional target scene;
- role;
- token budget;
- POV character;
- active characters;
- locations;
- active threads;
- research dependencies;
- `scenes` as relevance hints and `required_scene_ids` for causally mandatory Scene Packet coverage;
- active poetics capability IDs/names when capability-specific references should be selected;
- any explicitly required entry IDs for the **current** task;
- optional backend-only `secret_registry` path plus `blocked_secret_ids` for semantic information-flow control;
- optional backend-only `forbidden_terms` containing literal secrets that must not appear anywhere in the compiled pack;
- optional `forbidden_case_sensitive` (default false) and `deduplicate_content` (default true);
- `strict_visibility: true` when blindness or clean-room isolation matters;
- the selected `execution_profile` for orchestration provenance, but only after capability probing/profile selection; leave it null/absent when no profile has been established and never treat a template default as a capability claim.

Use `assets/tooling-templates/context-request-template.json`.

## 5. Selection order

Pack in this order unless the task requires another:

1. hard-required target mission / fixed local canon / scoped Project Poetics derivative;
2. causally required Scene Packet and POV knowledge / active cast state;
3. local object / route / access state;
4. active causal threads and immediate offscreen pressure;
5. reader-state constraints relevant to the reveal;
6. research facts actually constraining the scene;
7. active poetics-capability / project voice / prose rules needed for this task;
8. recent prose or summaries for local continuity;
9. lower-priority background.

Prefer a compact canonical summary over raw archival material when both are trustworthy.

## 6. Future-leak control

For role-scoped context, exclude an entry when:

- the role is not allowed;
- its branch scope does not match the active request branch;
- `available_from_chapter` is later than the target chapter;
- it is marked future-sensitive and belongs to a later chapter;
- it contains an answer the current Writer/Analyst is not authorized to know, including an unresolved authorial-answer choice;
- it has been retired or invalidated.

The Writer may receive a future-facing instruction only when it is phrased in terms of **observable handling or abstract disclosure class**, for example “let the locked cabinet register visually; do not invent an unseen authorization or historical cause.” Do not write “do not reveal that the cabinet contains X” when `X` itself is protected.

Use two distinct leak defenses:

1. **semantic taint** - assign opaque `SECRET-*` IDs to protected backend truths, mark direct sources with `tainted_by`, and connect summaries/derivatives with `derived_from`. The compiler propagates taint transitively and blocks a role from receiving any artifact derived from a secret it is not authorized to know, even when the wording is completely different. Use `assets/tooling-templates/secret-registry-template.json`.
2. **literal tripwire** - when protected terms are known, store them in the backend secret registry's `literal_terms` or the request's `forbidden_terms`. The compiler scans selected text and fails if one appears; diagnostics expose only hashes, not secret text.

Semantic taint is provenance, not automatic semantic inference. If a Writer-safe derivative was produced from hidden material, record that derivation honestly. Declassify only after the story/user has genuinely released that information to the role.

Do not solve leakage by asking the Writer to "pretend not to know" a spoiler it was unnecessarily given. If the same model context has already seen that spoiler, Context Compiler can still narrow task focus but cannot retroactively erase model-visible history; use `single-agent-isolation.md` to label the pass honestly.

## 7. Compression and omission

When the budget is tight:

- never drop request-required state silently; index-level `required` applies only while an entry is otherwise eligible for the current role/chapter;
- use approved summaries before dropping medium-priority entries;
- prefer current state over obsolete history;
- prefer direct dependencies over thematic adjacency;
- prefer one authoritative source over duplicated restatements; the compiler deduplicates identical source slices and, by default, identical content hashes;
- report what was omitted.

If required material cannot fit, fail compilation and enlarge the budget or reduce task scope. Do not silently draft with missing causal state.

## 8. Writer contract

The Writer should draft from the compiled pack, not roam the whole project unless explicitly escalated. The Writer must not infer missing Project Poetics from generic notions of "good fiction"; if the pack lacks a consequential literary commitment, surface a planning blocker or follow the explicitly delegated discretion boundary.

For a declared scoped Project Poetics derivative, Context Compiler must verify before inclusion: canonical `authority_ref` against the Project Manifest, exact derivative and parent hashes, active status, non-expiry, and declared scope against the request. These are provenance checks only. Do not parse the Markdown into aesthetic schema fields. Snapshot the verified envelope into the context manifest so later orchestration can audit what authority was actually consumed.

If the pack lacks a fact required to make a consequential choice, the Writer should surface a blocker rather than invent canon. An OpenIssue boundary means the missing answer is **not a blank to fill**; write only consequences authorized by the boundary, or escalate if the scene cannot remain robust.

The Writer may invent low-stakes texture only when it does not alter protected state, research truth, future constraints, or the effective compatibility envelope of a governed OpenIssue.

## 9. Deterministic compiler

Use `scripts/compile_context.py` with:

- a context index JSON;
- a request JSON;
- an output Markdown path;
- optionally a manifest JSON path.

Keep scoped-poetics request metadata grouped: `project_manifest`; the paired `scoped_project_poetics_ref` + `scoped_project_poetics_envelope_ref`; the applicable `target_arc` / `target_chapter` / `target_scene` / `task_id` scope selectors; and `active_capabilities`. These fields describe provenance and routing, not the literary contents of the Markdown.

The compiler:

- filters by role, explicit visibility, branch, and chapter availability;
- requires `visibility: reader-visible` for Reader Simulator packs and blocks explicitly protected backend material from Writer/Humanities packs;
- supports `strict_visibility` so unmarked entries fail closed for blind/clean-room passes;
- emits source-content hashes, request hash, and final pack hash for pass-envelope verification;
- blocks role/branch/future leakage, propagates semantic secret taint through `derived_from`, and enforces literal tripwires without echoing secret literals;
- treats request `required_ids` as the hard requirement for the current task and allows expired index-required chapter-local entries to retire normally;
- deduplicates identical source slices and, by default, identical source content;
- scores tag relevance, including optional overlap between request `active_capabilities` and entry `poetics_capabilities`;
- packs eligible required entries first;
- uses summaries when configured and full text will not fit;
- emits included and excluded entries with reasons;
- estimates token load conservatively.

The compiler selects evidence. It does not decide creative meaning.

When a Writer request explicitly supplies `active_capabilities` (including an empty list), `poetics-capability` entries without any matching activation are excluded as `inactive-poetics-capability`. An explicit request-required inactive entry blocks compilation; it cannot override the activation decision. Requests predating the activation field retain legacy eligibility. This operates only on declared routing metadata, never on prose keywords or genre inference.

Compile the organizing decision into the existing Writer-safe poetics and Mission text: current contribution/progression target, reader activity, scene-worthiness rationale, mediation/voice, closure/explanation posture and do-not-optimize constraints. Scope overrides can change these independently without mutating project authority. The current compiler already carries this natural-language content with hashes and selective capabilities; no literary engine field or keyword classifier is needed. Keep solutions and raw OpenIssue positions out of the derivative, even inside negative instructions.

## 10. Audit

Before drafting from a context pack, ask:

- Did every request-required local fact survive packing?
- Did any literal hidden answer leak through a mission, reader brief, summary, or “do not reveal X” instruction?
- Did any paraphrased Writer-visible artifact inherit blocked semantic taint from an author-only source without explicit declassification?
- Did any later-chapter or sibling-branch answer leak into the Writer or Humanities Analyst context?
- Did prior-chapter Mission/Scene Packet entries actually expire at rollover?
- Is the pack mostly canonical state rather than duplicated commentary?
- Is old state being preferred over the current committed state?
- Are research dependencies still in scope?
- Does the pack contain the current scoped Project Poetics derivative **and its verified provenance envelope** when literary choices depend on it?
- Are inactive poetics capabilities excluded instead of loaded because they exist?
- Is the pack small enough that the active craft stack remains intelligible?
- If this is a blind Writer/Reader pass, is the underlying model context actually fresh rather than merely reprompted?
- Does the context manifest/hash still match the pack recorded in the pass envelope?

## Live pack identity and provenance closure

Manifest `1.1.0` adds canonical Context Index and full provenance-source byte fingerprints plus Secret Registry bytes; included sources carry both representation and raw-file hashes. The request digest already binds effective project defaults. Formal readiness recompiles and compares the entire deterministic manifest and pack bytes, covering unchanged Markdown under changed requests/roles/visibility/provenance/taint/required IDs/source bytes/poetics/mission. Old manifests remain readable but must be regenerated for formal drafting. The CLI writes exactly the UTF-8 LF bytes it hashes.

All entry IDs must be nonempty and unique. Missing provenance parents propagate transitively; known taint labels require registry membership or explicit blocked_secret_ids, so an empty registry cannot authorize undeclared secrets. The scoped-poetics injection preserves any indexed derivative's provenance instead of generating an untainted alias. Keep future author-only truths in registered opaque secret nodes with honest source/derivation edges and role visibility; literal tripwires complement semantic taint. An unannotated secret cannot be inferred mechanically: author review must establish the true graph before freezing.

## Structured temporal and epistemic handoff (P0-3)

A selected Writer entry marked with a consequential/secret/temporal/research/plot/identity risk flag must contain structured `fact_uses` linked to canonical Story State facts. Each use names `fact_id`, actor (or request `pov_actor`), use time (or request `story_time`), epistemic mode, and expression/refinement provenance when precision matters. The canonical source supplies risk and actor-relative semantics; consumer metadata cannot lower them. Normal unformalized texture remains exempt.

Compiler loads `canonical_paths.story_state` from the request manifest or root manifest and calls Kernel K21/K22 after role/taint selection. It never accepts request-supplied acquisition records. Current-actor `writer_visible_facts` and catalog declarations remain coverage obligations even if the matching context use rows are deleted. Other POV declarations are isolated; author-only/tainted sources retain existing exclusion and negative-spoiler protections. Selected use metadata cannot disguise itself as author-only or writer_visible=false.

Invalid consequential acquisition, temporal applicability, firsthand memory or expression precision fails closed with empty Writer text. Diagnostics identify laws without echoing hidden values, fact IDs or channels. Director/backend analysis can still inspect future or author-only facts under existing permissions. Deterministic coverage applies to declared consequential material; arbitrary unannotated prose is outside this enforcement.

## Mandatory predecessor freshness (P0-6)

Before an activated Chapter N+1 Writer compile, Project State resolves the explicit canonical final Chapter N and the existing state/reconciliation owners verify its selected freeze. The request supplies `previous_chapter` containing `previous_final_chapter_id`, `previous_final_prose_sha256`, `state_snapshot_id` and `reconciliation_id`. The compiler checks their joint closure, not four independent ID-existence tests. Chapter 1 has no tuple; a legacy unactivated project remains readable but is never labelled verified fresh rollover.

This gate lives in `compile_pack` and the direct CLI. Omitting storyctl, project_manifest or one tuple field cannot bypass an active root manifest. An alternate project manifest, wrong current target/branch, old-copy path, manual post-freeze edit, stale receipt/snapshot or updated hash with old reconciliation fails closed. Compilation is read-only with respect to prose/state/requests and cannot auto-heal provenance.

The active Writer compiler requires equality with the registered canonical Context Index when the live predecessor rollover is FRESH. Selected predecessor entries (chapter number matching N, recent-prose/previous-chapter-summary/context-summary/writer-pack kinds, declared rollover binding, canonical final path or existing derived_from lineage) require current reviewed provenance. A direct uncompressed canonical final file proves its byte source directly. Other entries carry `rollover` metadata from the explicit Project State artifact-binding operation: tuple, whole-file hash, optional inline-summary hash, review reference and fingerprint. Child derivatives require their own reviewed binding; a fresh parent cannot launder an old child. Unknown natural-language dependencies are not inferred. Register consequential source relationships honestly.

P0-6-H: Previous-chapter freshness constraints apply only when a predecessor rollover exists and is applicable to the current chapter. Authoritative NOT_APPLICABLE (Chapter 1, no canonical predecessor) skips only predecessor-specific index equality; ordinary Writer visibility, taint, authorization, required context, budget and context-integrity checks remain mandatory. FRESH retains canonical index binding; STALE fails closed before index selection. An active malformed registry resolves to STALE, never an exemption; UNVERIFIED is reserved for legacy unactivated projects. Caller status claims cannot override live resolution.

A fresh request cannot launder a stale summary. Selected stale optional entries also block rather than silently enter a partly refreshed pack. Purely unrelated notes/drafts do not invalidate predecessor state. Historical packs/receipts are retained, with live status making stale evidence unusable as current. This is a bounded predecessor rollover contract, not P1-11 general derived freshness or P1-10 dependency cones.

A successful active manifest records the exact request tuple in `previous_chapter` plus the live rollover verification view; it contains opaque IDs/hashes, not private prose or hidden state. Recheck canonical final/state/receipt, request/index, representations and output identity immediately before publication. Active failures preserve prior pack and manifest bytes. Local output replacement is atomic per file with failure rollback; no distributed transaction is claimed. Existing role/taint, epistemic and commit-before-dependency checks remain mandatory and independent.



### P0-6-J: Writer-Pack Publication Is Byte-Semantic, Not API-Shape-Semantic

Writer-Pack publication must preserve the exact UTF-8 byte sequence produced from the compiled pack, without platform newline translation, encoding drift or BOM injection. Qualification verifies actual output bytes and hashes, successful replacement, and source-recheck failure preservation of prior pack/manifest bytes (or their absence), with local staging cleanup. It does not require a particular source-level API spelling. This is a deterministic local publication boundary, not a distributed transaction or crash-consistency proof.
