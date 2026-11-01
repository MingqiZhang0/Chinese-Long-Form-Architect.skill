# Semantic Revision and Canon Impact

Use this reference when already-written prose is revised and the project must determine whether the change is stylistic, interpretive, or canon-affecting. It owns the **revision-alignment workflow, impact taxonomy, revision provenance, and promotion of approved canon deltas**. It does not own prose craft itself or retcon policy.

## Contents

- Why text diff is insufficient
- Two-layer revision workflow
- Impact taxonomy
- Revision provenance
- Candidate state deltas
- Approval and commit
- Sidecar invalidation
- Branch-aware revision
- Tooling
- Failure modes

## 1. Why text diff is insufficient

A textual change can be large but canon-neutral:

> He opened the window.

becoming a more detailed description may alter style only.

A tiny textual change can alter the world:

> He opened the window.

becoming:

> The window was locked from inside.

may change access, geometry, evidence, tactics, and later causality.

Therefore never equate character-level diff size with story impact.

## 2. Two-layer revision workflow

Use two distinct passes.

### Layer A - deterministic alignment

Mechanically identify:

- unchanged blocks;
- inserted blocks;
- deleted blocks;
- likely modified/aligned blocks;
- movement when reliably detectable;
- before/after hashes and source paths.

This layer reports **where text changed**, not what the change means.

`revision_diff.py` also emits workflow-routing gates. Treat prose/diegetic classification and Project-Poetics classification as separate axes:

| Revision condition | Diegetic classification | Project-Poetics classification | Poetics downstream invalidation review |
|---|---:|---:|---:|
| no prose change, no approved poetics change | no | no | no |
| prose change only | yes | no | no, unless Layer B later finds another dependency impact |
| approved poetics change only | no | **yes** | **yes** |
| prose + approved poetics change | **yes** | **yes** | **yes** |

Therefore a byte-identical or paragraph-identical before/after pair is **not** sufficient to skip revision routing when `--poetics-changed` is declared. Conversely, an ordinary prose diff does not by itself prove that Project Poetics changed.

The legacy aggregate field `semantic_classification_required` remains true whenever **either** axis requires classification. New consumers should prefer `diegetic_classification_required` and `poetics_classification_required`, then use `classification_axes` as the explicit routing list.

### Layer B - semantic impact analysis

An Agent starts with changed/aligned spans and the connected discourse required to interpret them, then examines downstream uses of the changed premises. This layer may be uncertain and must expose its reasoning anchors. Restricting review to changed spans cannot discover consequences in unchanged later prose.

Do not let Layer B directly mutate canon.

## 3. Impact taxonomy

Use one or more labels per change.

- `PROSE_ONLY` - wording/rhythm/image/clarity changed without changing story facts or accessible interpretation.
- `FOCALIZATION_AFFECTING` - camera permission, internal access, or what the reader can legitimately know changed.
- `STATE_AFFECTING` - person/object/place/body/resource state changed.
- `KNOWLEDGE_AFFECTING` - who knows/believes what changed.
- `CAUSAL_AFFECTING` - reasons, enabling conditions, consequences, or feasible alternatives changed.
- `TIMELINE_AFFECTING` - chronology/duration/order/travel assumptions changed.
- `RESEARCH_AFFECTING` - a real-world claim, scope, model, date, or factual dependency changed.
- `PROMISE_AFFECTING` - setup/payoff/reader question or reveal fairness changed.
- `OPEN_ISSUE_AFFECTING` - a revision changes an OpenIssue constraint, position viability, resolution basis, or whether existing prose remains robust to the effective compatibility envelope.
- `THEME_INTERPRETATION_AFFECTING` - humanities analysis may change while canon may remain stable.
- `PROJECT_POETICS_AFFECTING` - an approved Project-Poetics commitment or scoped override changed; classify its planning/form consequences independently from diegetic truth.
- `CANON_CORRECTION` - reader-facing established fact has been intentionally changed; route to `change-control.md`.

A single edit may carry several labels.

## 4. Revision provenance

Treat each stable chapter revision as a new revision entity with provenance.

Record:

- chapter ID;
- old revision/hash;
- new revision/hash;
- author/agent responsible;
- revision purpose;
- changed spans;
- semantic impact labels;
- supporting textual anchors;
- confidence;
- affected state/dependency nodes;
- approval status;
- resulting events, if any.

Preserve the fact that `rev-B` was derived/revised from `rev-A`. Do not overwrite revision lineage merely because only the latest prose is reader-facing.

## 5. Candidate state deltas

For any non-`PROSE_ONLY` edit, produce **candidate deltas**, not direct mutation.

Examples:

- `window.locked: false -> true`;
- `char-li knows FACT-22: false -> true`;
- `scene duration: 3 min -> 20 min`;
- `reader sees culprit face: no -> yes`;
- `research dependency R-17 scope invalidated`.

Then query the dependency graph for affected downstream nodes. If the revision changes an OpenIssue constraint/resolution, also inspect `conditional-on-hypothesis` dependents and Writer-safe commitment boundaries derived from the old envelope.

The semantic analyst may be wrong. Candidate deltas therefore require validation/reconciliation before commit.

### Compare propositions and information paths, not just event names

For each changed proposition, compare old/new truth, polarity, actor holder, acquisition (`seen`/`heard`/`inferred`), content granularity, valid time, narrator permission and reader exposure using reconciliation's semantic distinctions. “看见密信” alone never proves “读过内容”; quote the words establishing actual reading. A downgrade from direct reading to merely hearing that a letter exists may preserve object existence, while removing content knowledge, recognition of missing characters, and decisions relying on the exact message.

Retrieve the existing dependency closure, preserving edge direction/kind, branch, evidence and **alternative upstream supports**. Treat a reachable node as a review candidate; a separate surviving evidence source can preserve a conclusion. Conversely, search the actual later prose even when the graph has no edge. Look for paraphrased recollection, substituted pronouns, decisions, withheld alternatives, and clue interpretation, not merely occurrences of “密信”. Record newly discovered edges as proposals for the existing graph after review, rather than creating a competing graph.

For each downstream proposition/action/clue, return its chapter and exact evidence, old required premise, what the revised source now establishes, the dependency chain, independent support if any, and `affected`, `independent`, or `unresolved`. `independent` requires a real argument, not silence in the graph. Give repair alternatives and tradeoffs for an affected premise: restore/establish the missing information before its use; rewrite the decision as a fallible inference; change the decision/consequence; or retain the old source text. Recheck each selected repair's own access, timeline and reader-clue consequences. Suggestions are not approved canon or executed repairs.

### Existing tooling: graph retrieval plus unindexed prose scan

`revision-diff` optionally emits a version-bound review packet alongside its alignment manifest:

```bash
python scripts/storyctl.py revision-diff PROJECT_ROOT/before/ch8.md PROJECT_ROOT/chapters/ch8.md --chapter-id CH-008 --branch main --out PROJECT_ROOT/revisions/ch8/alignment.json --review-root PROJECT_ROOT --dependencies dependencies.json --changed-node CH8:seen-letter --chapters-dir chapters --review-out PROJECT_ROOT/revisions/ch8/dependency-packet.json
```

Choose seeds only after semantic classification; repeat `--changed-node` for each changed premise. `--chapters-dir` must contain the requested branch's complete applicable Markdown prose. For large projects, review in batches while preserving the whole inventory; a deliberately bounded scan is partial coverage. The packet retains active graph witnesses and all incoming alternative edges, then includes every Markdown chapter even when no dependency is indexed. It retrieves text; it neither labels impacts nor rewrites state. Graph edges lacking a branch are interpreted inside the explicitly scoped project branch. Keep other branches outside that chapter directory. Existing review packets are never overwritten.

Attach `dependency_review` to the **existing impact report**: packet path/hash and one decision for each `review_id`, with status, rationale, exact evidence, and repair alternatives (`description`, `tradeoff`). Affected nodes require evidence and alternatives. A chapter can contain both affected and independently supported propositions: annotate nodes separately and explain the chapter's mixed result. The Kernel K14 verifies packet/input freshness, old/new source identity, branch, complete graph/chapter decision coverage, evidence hashes and unresolved approval blockers. Added or edited chapters, changed dependency edges, or changed source revisions stale the review. Legacy impacts remain readable but do not establish unindexed-discovery coverage.

The executable example is `assets/regression-corpora/prose-state-semantics/letter-revision/impact.json`. Its old Chapter 8 actually reads the letter; the new version only hears that it exists. Chapter 23's content knowledge and gate deployment lose support; Chapter 24's unindexed missing-character claim also loses support. Chapter 23's handwriting identification survives through Chapter 17's independent sample. The report is a reviewed **test fixture**, not an authorization to apply any repair to a real novel.

## 6. Approval and commit

### If all changes are `PROSE_ONLY`

- update chapter revision provenance;
- refresh voice/style fingerprints if needed;
- do not create canon events.

### If canon/state is affected but the revision is consistent with existing canon

1. validate candidate deltas;
2. when the governance profile/failure cost requires it, rebuild `prose-state-reconciliation.md` against the **revised** prose bytes and require reviewed evidence for prose-based deltas;
3. generate semantic event proposals;
4. check expected branch revision and invariants;
5. commit through the normal transaction protocol;
6. invalidate/rebuild affected projections/artifacts.

### If established reader-facing canon changes

Use `change-control.md`. A semantic diff is evidence of change, not permission for a retcon.

### If a previously resolved OpenIssue is reopened

If the old resolution remained only in S0 planning, record an authorized `A`-level reopen and invalidate dependent planning artifacts. If the resolution already caused committed world facts, actor knowledge, reader exposure, or published prose, reopening is a semantic revision/retcon problem: trace downstream consequences and use `change-control.md` where required. Do not erase W/E/X history merely by changing the S0 record.

## 7. Sidecar invalidation

A chapter revision may stale:

- humanities reports;
- reader simulations;
- context summaries and OpenIssue Writer commitment boundaries;
- scene packets;
- voice-drift samples;
- setup/payoff interpretations;
- research adoptions.

Do not regenerate everything. Use dependency impact to invalidate only artifacts whose premises changed.

## 8. Branch-aware revision

Every revision belongs to a branch/revision context.

Do not compare `main` Chapter 20 against an experimental branch Chapter 20 and treat the differences as accidental edits. Branch identity must be part of the revision manifest.

## 9. Tooling

Use:

- `scripts/revision_diff.py` for deterministic paragraph alignment and revision manifest generation;
- `assets/revision-templates/revision-impact-template.json` for the Agent's semantic classification;
- `assets/runtime-schemas/revision-impact.schema.json` for structural validation;
- `scripts/runtime_schema.py validate-artifact` for schema validation when available.

`revision_diff.py` deliberately does **not** claim to know canon impact. It prepares evidence for the semantic pass.

## 10. Failure modes

### Diff-size fallacy

Large rewrite != large canon change.

### Semantic auto-commit

An LLM classification is not a transaction.

### Prose-only complacency

A sentence can sound stylistic while changing spatial, temporal, or epistemic truth. Check verbs, negation, quantities, names, locations, and access claims carefully.

### Lost revision history

Keeping only the latest text makes Why Trace and stale-sidecar diagnosis much harder.

### Revision cascade panic

Do not rebuild the entire novel for every edit. Use dependency edges and impact labels.

### OpenIssue reopen laundering

A resolved answer is reopened in planning while its committed downstream consequences are left untouched as if the old truth had never existed. Repair: separate the S0 authorial reopen from W/E/X revision impact and invalidate only the justified dependency closure.

## 11. Poetics-affecting revision

A revision can leave world canon unchanged while altering **how the project is meant to be read**. Classify this separately from prose-only polish and diegetic semantic change.

Examples include:

- changing a project from stable voice to deliberate chapter-level heterogeneity;
- changing the accepted degree of mind opacity or narrator unreliability;
- changing what counts as progression or legitimate narrative salience;
- authorizing recurrence/stasis that an older strategy treated as compressible;
- adding or removing a do-not-optimize constraint.

For an approved poetics-affecting revision:

1. update the canonical `project-poetics.md` owner or scoped override;
2. require Project-Poetics impact classification even when prose bytes are unchanged;
3. enter downstream invalidation review for Narrative Strategy, Chapter/Writer Missions, context packs, and style/voice diagnostics;
4. invalidate only the affected dependency closure rather than blindly deleting every artifact in those classes;
5. preserve world events and state projections unless the prose edit also changes diegetic truth;
6. distinguish an **authorized formal change** from accidental drift in later audits.

`revision_diff.py --poetics-changed` must surface this route with `poetics_classification_required: true`, `classification_axes` containing `project_poetics`, and `poetics_invalidation_review_required: true`. Its `poetics_invalidation_review_domains` are review domains, not a claim that every listed artifact is stale.

Record the interpretive result in the optional top-level `project_poetics_impact` block of the revision-impact report. This block exists specifically so a poetics-only revision can have `changes: []` while still recording classification status, scope, authority provenance, actual affected artifact classes/nodes, and invalidation-review status. Use `PROJECT_POETICS_AFFECTING` on a textual change when that aligned edit itself participates in the approved poetics change; do not fabricate an alignment merely to represent a poetics-only revision.

Do not event-source Project Poetics as world truth. Preserve its author/planning provenance separately.
