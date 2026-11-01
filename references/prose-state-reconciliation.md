# Prose-State Reconciliation

Use this reference when durable Story State or Runtime events are being derived from newly drafted or revised prose. It owns the **two-way evidence contract** between what the text actually establishes and what the project records as durable state.

## Contents

- Why reconciliation exists
- Two directions
- Candidate extraction
- State-delta evidence
- Non-prose deltas
- Review gate
- Revision behavior
- Tooling
- Failure modes

## 1. Why reconciliation exists

A story can fail even when prose and state are each internally coherent:

- prose establishes a durable transfer, injury, promise, knowledge acquisition, or access change but the state update forgets it;
- state records a consequential fact that the prose never established;
- a later prose edit invalidates evidence supporting an old commit while the state remains unchanged.

Do not solve this by pretending deterministic code can understand fiction perfectly. Use semantic extraction as a **candidate-generation** step, then validate provenance mechanically. `formalization-boundary.md` owns the prior question of whether a meaning belongs in durable state at all.

## 2. Two directions

After a substantial scene/chapter, reconcile both directions.

### Prose -> candidate durable facts

Identify text-established facts that may matter later:

- object transfer / custody;
- knowledge gained, lost, doubted, or falsified;
- injury / treatment / resource expenditure;
- access / route / location change;
- relationship commitment or durable residue;
- institutional record/action;
- promise, debt, setup, public version;
- other persistent causal changes.

Each candidate must be explicitly classified:

- `committed` - mapped to one or more reviewed state deltas;
- `non_durable` - true in the moment but not worth persistent tracking;
- `rejected` - extraction was wrong or not actually established;
- `pending` - unresolved; cannot pass a strict commit gate.

### State delta -> evidence / basis

Every durable delta must explain why it exists.

If `basis = prose`, attach exact evidence spans from the current prose bytes.

If the delta legitimately occurs outside narrated prose, use a non-prose basis such as:

- `offscreen-simulation`;
- `author-decision`;
- `research-correction`;
- `runtime-derived`.

Explain non-prose bases in `basis_note`. Do not forge prose evidence for an offscreen event.

## 3. Candidate extraction

The Writer should not directly mutate canonical state while drafting. A Committer/Continuity pass reads the stable prose and proposes candidates.

Candidate extraction is semantic and may be wrong. Therefore:

- never auto-promote every extracted statement;
- distinguish descriptive transient facts from persistent state;
- do not convert metaphor, hypothetical speech, lies, plans, or focalizer belief into objective canon without the correct state category;
- separate actor belief from world truth;
- prefer omission over tracking trivia that cannot affect later causality;
- do not create candidates merely for subtext, metaphor, symbolic association, ambiguous motive, or local sensory meaning unless a later operational dependency genuinely requires representation.

The reconciliation report records the reviewed decision, not raw model confidence.

### Read prose before seeing the submitted deltas

For a consequential Chinese chapter, perform a **source-first pass** over the entire stable text with the necessary entry state and focalization context, but without the Writer's proposed exit deltas. Only then compare the independently extracted candidates against submitted deltas and the current state. Otherwise the review merely confirms the supplied list and never searches for what it omitted. In single-agent work, freeze the source-first candidate list before loading the exit delta list; do not describe this as independent-agent evidence.

Read connected discourse, not isolated verbs. Resolve the speaker/focalizer, referents (including omitted subjects and pronouns), negation scope, time, modality, quotation boundaries, and later correction or reversal. Enlarge the evidence span until it includes the clause that limits the claim. If the resolution remains uncertain, retain `pending` and explain competing readings. Keywords such as “看见”, “相信”, “一定” or “其实” are prompts to inspect context, never automatic truth labels.

For each causally material proposition, separate:

| Textual situation | What may actually be established | What must not be promoted |
|---|---|---|
| 直接叙述且叙述权限可靠 | The stated world event, limited to what is asserted | Unmentioned properties, completion of an attempt, or reading a merely seen object |
| 言说／转述 | The speech/hearing event; belief only if acceptance is established | Truth of the embedded message, or belief inferred just from hearing |
| 谎言 | A speech act and any resulting belief; falsity only with contrary evidence | “不可靠的人说了” therefore this particular statement is false; deception can use true words |
| 猜测／自由间接引语 | A particular actor's hypothesis or certainty | Focalizer certainty treated as an omniscient narrator's assertion |
| 隐喻 | A figurative comparison; an actual injury needs separate literal evidence | “冷话像刀” converted into a wound, weapon, or attack |
| 反事实／愿望／计划 | The conditional/desire/plan as such when operationally material | Its embedded event treated as actual history or a completed action |
| 误认 | What the actor believed and, if established, the distinct actual identity | Correcting world identity by erasing the actor's false belief and consequent motive |

`semantics.mode` describes the proposition, not the entire sentence. One sentence may need multiple candidates: “门房骗他说信烧了，他信了，信其实还在墙里” establishes an actual speech event, a false actor belief, and an actual letter location. Use `assertion` for the actual speech event, `lie` for the false believed content, and separate their holders/layers. `truth` concerns the embedded proposition; a `refuted` belief can still be a real, durable belief. `polarity=negated` is an explicit negative proposition, not mere absence of evidence. Seeing a folded letter can establish its existence without establishing its text, authenticity, author, or custody.

### Find omissions and unsupported state symmetrically

Review exit state, not just individual sentences: a key offered and refused is not a transfer; a key handed over and returned has no net holder change, though the temporary access/exposure may itself matter. Silent acceptance, changed access, exhausted resources, commitments, discovered doubts, and irreversible reader exposure are easy to omit even without dramatic wording. Preserve a false belief that motivates later action; do not “repair” it into truth. No durable delta remains legal.

Compare the prose-derived list with recorded state and distinguish: already present; missing durable change; supported new change; contradicting state; unsupported state; explicit non-prose basis; unresolved interpretation. “Not narrated here” is not “never established”: search earlier prose, branch history and authorized offscreen/authorial sources before rejecting a historical state fact. Inspect exactly the supplied state snapshot; identify a scoped export as partial rather than claiming the whole project was audited. A negative state assertion also needs evidence; ignorance about a claim is not proof the claim is false.

### Executable semantic review, version 1.1

The existing reconciliation artifact now supports `1.1.0`, without creating a second ledger. It adds typed `prose_candidates[].semantics`, matching delta `layer`/`holder`, and `semantic_review`:

- `coverage`: hash-bound line ranges, referenced candidate IDs, review status and rationale. Every nonblank source line must be covered exactly once; ranges can be combined when the needed context spans several lines. A reviewed range may have no candidates when nothing durable is established, with an actual reason.
- `sources`: whole-file hashes of every cited prose source, including historical chapters used in state checks. A changed narration frame outside a quoted span must stale semantic review too; a matching fragment hash alone is insufficient. The preparer inventories the current chapter; add earlier sources before citing them.
- `state_snapshot` and `state_checks`: snapshot path, whole-file hash and branch, plus each leaf's exact JSON pointer/value, status, evidence and rationale. Use an explicit scoped export if the full state is too broad. `supported` requires textual evidence; `unsupported` and `pending` block strict approval; `non_prose` requires an explanation of the genuine authority/event basis; `non_material` identifies metadata or noncanonical bookkeeping.
- Candidate `semantics`: proposition, mode, layer (`world`, `actor_belief`, `actor_knowledge`, `reader_exposure`), holder when applicable, polarity, truth status, acquisition source, exact evidence and rationale. These map to the existing Kernel strata, not a new truth model.

Strict validation rejects unreviewed/omitted ranges, missing state inventory entries, stale snapshots, cross-branch reviews, mismatched belief/world delta layers, and non-established propositions submitted as world truth or knowledge. Metaphorical/counterfactual/planned embedded events cannot be committed directly: represent an actual belief, plan, or speech act with its own asserted proposition when needed. Low confidence does not mean false; leave a consequential unresolved reading pending.

**These checks enforce the submitted reading's consistency, not its correctness.** A reviewer can still mislabel a sentence as an established assertion or mark a range reviewed despite missing a fact. Raw-prose blind evaluation, quoted rationale, and review of contested cases remain necessary. Version `1.0.0` stays readable and emits a legacy warning: it validates submitted evidence but offers no semantic coverage/state-inventory assurance. New consequential reviews use `1.1.0`.

## 4. State-delta evidence

For each prose-based delta, record:

- `delta_id`;
- human-readable description;
- target state path/identity when useful;
- before / after when meaningful;
- evidence path;
- 1-indexed inclusive line range;
- SHA-256 of the selected line-range text.

Also record SHA-256 of the whole prose file. If prose changes afterward, the report becomes stale even if the cited lines themselves happen to remain unchanged. Re-run semantic review rather than assuming an old commit still matches the revised chapter.

Evidence proves **where the claim came from**. It does not by itself prove the semantic interpretation is correct; that remains the reviewer's job.

## 5. Non-prose deltas

Some durable changes are intentionally not dramatized. For example, an institution completes routine paperwork during an ellipsis or an offscreen actor advances a process between chapters.

Such deltas may enter state when the project architecture allows them, but their basis must be explicit. They still require causal validity and may require Runtime events; they simply do not claim false textual evidence.

Do not use `offscreen-simulation` as an escape hatch for changes that should have been reader-visible.

## 6. Review gate

A reconciliation report moves through:

`DRAFT -> READY_FOR_REVIEW -> APPROVED`

or `REJECTED`.

Before an approved chapter commit in Forensic governance:

- no prose candidate remains `pending`;
- every `committed` candidate references existing deltas;
- every prose-based delta is referenced by at least one committed candidate;
- every prose evidence span still hashes correctly;
- whole-prose hash matches current bytes;
- non-prose deltas explain their basis.

Persistent projects may use this selectively for high-risk chapters. Lean projects should not be forced to generate reconciliation JSON for routine scenes.

## 7. Revision behavior

When existing prose changes:

1. run `revision_diff.py` / `semantic-revision.md` first;
2. if prose-only, existing state may remain unchanged, but any evidence report tied to the old whole-prose hash is technically stale and should be regenerated only when the project requires forensic provenance;
3. if state/knowledge/causal/timeline meaning changes, rebuild reconciliation before accepting new canon deltas;
4. never keep an `APPROVED` report whose `prose_sha256` no longer matches current prose.

## 8. Tooling

Use `assets/reconciliation-templates/prose-state-reconciliation-template.json` and:

Prefer generating the pending source/state inventory rather than filling a static template by hand (report path is an output path; use an absolute path when running outside the project):

```bash
python scripts/storyctl.py reconcile PROJECT_ROOT/reconciliations/ch-008.json --root PROJECT_ROOT --prepare chapters/ch8.md --state state.json --chapter-id CH-008 --branch main
```

The output is DRAFT, with no inferred facts and no approval. Read the prose, fill candidates, review all ranges, reconcile state claims, then validate. Existing reports are never overwritten by `--prepare`.

```bash
python scripts/prose_state_reconcile.py reconciliations/ch-001.json --root PROJECT_ROOT
```

For a final Forensic commit gate:

```bash
python scripts/prose_state_reconcile.py reconciliations/ch-001.json --root PROJECT_ROOT --strict
```

The deterministic validator checks schema, whole-prose freshness, evidence ranges/hashes, cross-references, and unresolved candidates. It does **not** extract story meaning by itself.

For raw-prose extraction/unsupported-state/revision evaluation, use `storyctl chinese-eval build-state-blind` and `score-state` described in `chinese-narrative-behavioral-evaluation.md`. Keep the answer key out of generation context. Do not cite oracle roundtrips as model comprehension accuracy.

## 9. Failure modes

### State-memory gap

Prose establishes a durable change, but no candidate records it. Repair: run the semantic extraction/reconciliation pass before planning downstream scenes.

### Unsupported state invention

A prose-based state delta has no text evidence. Repair: locate real evidence, reclassify the basis, or reject the delta.

### Stale evidence after revision

The chapter changed after approval. Repair: regenerate or review reconciliation; do not trust an old hash.

### Evidence absolutism

A valid hash is treated as proof the interpretation is correct. Repair: remember that hashing proves provenance, not semantics.

### Bureaucratic overreach

Every tiny scene in a low-risk novel gets a full report. Repair: reserve strict reconciliation for the governance profile and failure cost that justify it.

## Source-bound chapter freeze (P0-6)

For an activated verified rollover, resolve chapter/branch through Project State's explicit finalization record. Both `--prepare` and direct report validation reject an alternate draft/backup/old-copy source. An `APPROVED` report approves semantic review; it is not final-prose selection authority. Register actual final approval first. P0-7 hard contradiction scanning remains unimplemented.

Read the entire stable canonical final text, complete the 1.1 report's coverage/candidates/deltas, audit the full canonical Story State or a current replay-verified Runtime snapshot, commit actual durable changes using the existing state owner, then:

```bash
python -B scripts/prose_state_reconcile.py PROJECT_ROOT/reconciliations/review-ch1.json --root PROJECT_ROOT --freeze --json
```

`--freeze` always requires APPROVED full review regardless of a separate `--strict` flag. Scoped or unrelated state exports cannot replace canonical state. In rollover reports, committed delta targets are JSON pointers and must match canonical committed after-values. No arbitrary prose contradiction extraction or automatic semantic commit is performed.

The immutable receipt extends this same reconciliation artifact with `reconciliation_id` and `rollover_receipt`: project/finalization, `input_final_prose_sha256`, verified snapshot path/hash/ID, `verification: VERIFIED`, effect and reviewed source-report identity. `RECON-<canonical sorted-JSON SHA-256>` binds the full payload excluding its own ID. The snapshot ID binds actual snapshot content. Receipt bytes are hash-bound in Project State's selected freeze. Live verification closes project, branch, chapter, canonical path, current raw hash, receipt and canonical state together; existence of an ID is insufficient.

The current freeze pointer changes only after immutable snapshot and receipt outputs validate and source/report/state hashes are rechecked. Missing/stale review, uncommitted delta, wrong snapshot or changed source leaves the prior current pointer intact. Historical receipts/reports remain audit evidence.

After explicit reapproval of a formatting revision, this operation can inherit a previous verified freeze:

```bash
python -B scripts/prose_state_reconcile.py PROJECT_ROOT/reconciliations/unused-output-placeholder.json --root PROJECT_ROOT --freeze --formatting-only --chapter-id CH-01 --json
```

In formatting mode the positional path is not read or published; the registered prior receipt is the only parent. Compare archived prior approved bytes with current approved bytes. The conservative normalization allows a UTF-8 BOM, CRLF/LF conversion and one terminal newline only. Paragraph boundaries, punctuation, emphasis, character substitutions, internal whitespace and ordering are not normalized. Anything else requires full semantic re-review.

A verified formatting receipt stores both raw identities, parent finalization/receipt identities, normalization digest and SAME_BYTES/FORMAT_ONLY classification; effect is `FORMAT_ONLY_NO_STATE_DELTA`. It rechecks the immutable prior snapshot against current canonical state and records a new source-bound receipt while reusing that snapshot. It does not fabricate a fresh semantic line review. Direct strict validation accepts this distinct schema path only through its machine proof and selected current freeze. Same-source retries are idempotent; repeated formatting changes produce new source bindings, not infinite world-state snapshots. Every old raw-hash pack is stale until refreshed.

