# Auditability contract 1.0.0

This contract governs deterministic Python owners, including Lean projects. It does
not add Workbench features or infer missing history/evidence.

| Invariant | Owner / validator | Regression | Failure mode |
| --- | --- | --- | --- |
| Untimed state SHALL NOT be silently projected into historical KNOWLEDGE. | `story_ops.knowledge_at` | A1 | `unknown`, PARTIAL, MISSING_TEMPORAL_PROVENANCE |
| Retired state SHALL NOT be resurrected through legacy fallback. | `story_ops.knowledge_at` | A2 | canonical absence remains absence |
| Reader-information queries SHALL respect presentation-time boundaries. | `reader_state.query_reader_state` | A3 | PARTIAL with missing/unsupported chronology |
| Complete Why Trace SHALL preserve all relevant support edges. | `narrative_runtime.why_trace`, `trace_query` | A4 | PARTIAL with terminal/cycle/closure gaps |
| Dependency traversals SHALL share one explicit edge-activity semantic. | `dependency_activity.is_edge_active`, `active_edges` | A5 | unsupported position fails closed |
| Canonical events SHALL NOT be audit-closed without traceable provenance. | `event_provenance`, runtime validation, schema project validation, transaction preflight | A6 | UNRESOLVED_PROVENANCE; legacy load warns |
| Idempotent transaction retry SHALL require both identity and semantic payload equivalence. | `runtime_tx.transaction_match_state`, preflight | A7 | typed TxError.code=IDEMPOTENCY_CONFLICT |

Permanent executable tests: `python -B scripts/storyctl.py auditability-core`.
Use `--smoke` for seven minimal oracles, `--mutations` for seven isolated source
mutations. Fast includes smoke; Core includes the complete suite and mutations.

## Consequential operational claims (P0-2)

An Agent may claim no stronger operational state than authoritative execution
evidence supports. **Completion is not verification.** This applies to research,
freeze, compile, Kernel/readiness checks, context builds, chapter validation,
migration, delegated work and campaigns. Ordinary reads and trivial file writes
need no ceremonial ledger; an operation's owner may accept DONE when no semantic
verification is required. The ledger never grants decision authority under P0-1.

| State / permitted claim | Required evidence |
| --- | --- |
| PLANNED / preparing | Registered intent only; no invocation/completion claim |
| RUNNING / actually started | Content-bound executor invocation receipt |
| DONE / executed or generated; not yet verified | Successful completion receipt bound to invocation plus hashed expected artifacts/tool results |
| VERIFIED / verified, confirmed correct, passed validation | DONE plus separate completion-bound inspection receipt, method, verifier and PASS result |
| FAILED / failed or aborted | Invocation and failure/error receipt, reason and retryable boolean |

The existing pass/checkpoint record carries additive `operational_version=1.0.0`,
`operation_id`, `operation_type`, `status`, `transitions`, `started_evidence`,
`completion_evidence`, `verification_evidence`, `verified_by`, and failure fields.
Evidence pointers are project-root-relative `{ref, sha256}`. Invocation JSON has
`kind=invocation`, operation_id, invocation_id, executor. Completion JSON has
`kind=completion`, the same operation/invocation IDs, `outcome=success`, and
nonempty `outputs` pointers. A tool result is a permissible output, not necessarily
a generated prose file. Verification JSON has `kind=verification`, operation_id,
completion_sha256, `method=deterministic-check|main-agent-inspection`, verifier,
`result=PASS`, and `basis=artifact-inspection`. Its verifier matches verified_by.
This is an inspection separate from execution, not a second human approval.
Failure JSON binds the same invocation and operation, `kind=failure`, and reason;
the record preserves failure_reason and boolean retryable. FAILED is terminal:
a retry receives a new operation ID and receipts, preserving failed history.

The legal sequence starts PLANNED, then RUNNING, then DONE, then VERIFIED.
RUNNING or DONE may enter FAILED. Checkpoint writes require adjacent transitions
and preserve prior evidence identities. No implicit atomic-operation exception,
timestamp-only completion, string flag promotion, or plan-as-result is accepted.
`validate_orchestration_run.py` checks evidence, output bytes, transition history,
declared status, failure reason and report conflict. It requires --root for evidence
inspection. Hashes/receipt kinds establish identity and contract structure, not
cryptographic authentication of an executor or the semantic truth of research.
Agents must record actual tool/executor receipts, never manufacture attestations.

Subagent reports live in `reports: [{reported_by, status}]`; optional reported_by
on an operation identifies the producer. Reports do not supply underlying-world
verification. A report alone allows only “subagent-reported DONE”, never VERIFIED.
Main Agent inspection or the current owner's deterministic validator may verify
the underlying artifacts. Conflicting and stale reports remain visible as warnings,
and cannot upgrade or downgrade evidence-backed state. This minimum rule does not
implement P1-14 authorization delegation, verifier qualification or trust voting.

Every consequential claim must answer: what action, whether invoked, completion
artifact/result, whether verification is required, verifier/method/evidence, and
the authoritative machine-readable source. Natural-language narration need not be
logged wholesale. Legacy records remain immutable and readable as
LEGACY_UNKNOWN_VERIFICATION; legacy DONE never implies VERIFIED. New checkpoint
claims cannot use the legacy format to bypass evidence checks.

`storyctl status PROJECT_ROOT --json` is a read-only aggregator in project_ops,
not a new semantic owner. Project manifest owns chapter/branch and canonical
pointers; readiness owns gate, frozen `review_snapshot` (not a guessed top-level
snapshot field), approval and handoff checks; live Kernel owns its result; the
registered checkpoint owns operations. Use canonical_paths.prewriting_readiness,
or the existing bootstrap path planning/prewriting-readiness.json; register the
one active run at manifest orchestration.active_run_checkpoint. This operational
pointer is outside canonical_paths so changing report bytes does not become a
semantic source of the frozen review fingerprint. No run pointer yields
null, never RUNNING. Missing data yields null/unavailable. Saved handoff PASSED
flags do not override live readiness recompilation. A fresh review fingerprint
establishes the current snapshot; stale reports never override it. Stale artifacts
listed here are those detected by existing readiness/research owners, not a new
general freshness engine. Overall run status prioritizes FAILED, RUNNING, PLANNED,
DONE, VERIFIED across operations; invalid evidence is explicit INVALID, with the
strongest supported per-operation state retained for diagnosis. Queue status is
scheduling metadata, not operational truth. Domain freeze truth is the current
validated snapshot; an old run report cannot delete an existing snapshot.

Executable P0-2 regression: `python -B scripts/integration_selftest.py --only claim-action-consistency`.

## Temporal and legacy authority

Knowledge uses numeric story-valid intervals `[valid_from/acquired_at, valid_until/
valid_to/retired_at)`. `acquired` remains an acquisition alias. An acquisition-event
reference supplies time only when the referenced registered event has CLOSED
provenance and numeric story_time. Missing start does not imply minus infinity.
Current queries (`at=None`) are explicitly current-state reads. Historical results
are stably sorted; the presence of `knowledge_state`, even empty, disables the
lower-authority `knowledge_uses` fallback. Legacy timed uses remain PARTIAL.
Row completeness is PARTIAL for either temporal or provenance gaps;
provenance_status is independently UNRESOLVED unless its owner establishes closure.
An empty row set alone
is not a certified negative fact and carries no FULL assertion.

Reader `NarrativePosition(axis="presentation", domain="chapter", value=N)` is the
formal history input. The integer adapter explicitly maps chapters to presentation.
Story-valid, revision, unsupported domains and nonfinite positions fail closed.
Dictionary collections and list snapshots share the recursive time filter.
`from_chapter` is required for historical entries; timed parent snapshots supply
bounds to nested contents. Existing reader `to_chapter` remains **inclusive**.
Repeated fact/id presentations choose the latest eligible entry. Untimed current
strings remain readable only without a historical position. Flashback story_time
never changes exposure order. Supersession/misdirection must have recorded exposure
bounds; a current label alone does not fabricate its historical transition.
All callers of reader_state_at inherit this filter when they supply a position.
Observatory and resume deliberately use current state. Reader effects in supplied
runtime events reconstruct exposure by chapter then sequence, including set/delete
and replacement transitions. Missing event chapters/sequence, uncommitted rows and
unsupported branch histories are explicit gaps. Replay/import preserve recorded
bounds; they do not manufacture chronology for unbounded current dicts.

Dependencies use active_at (default) or explicit historical_all. No position means
the recorded current lifecycle status. Numeric `--at` is a **revision sequence**
adapter; typed positions must match the edge's declared axis/domain (default
revision/sequence). At a position, retired/invalidated/superseded edges require
explicit start/end and use half-open bounds. Missing historical lifecycle bounds
do not revive inactive edges. Impact, propagation, Why Trace, revision retrieval
and Observatory use the shared owner. Replay preserves lifecycle rows; traversal
of replayed dependency projections uses the same iterator. historical_all exposes
registered history, including invalidated rows; it is not an active-impact claim.

## Trace and provenance closure

why_trace is the compatible graph-only library primitive. It expands a node once
but emits every registered incoming edge, retaining edge IDs and contradictions.
trace_query and the runtime `why` CLI expose mode, completeness, gap_reasons and
provenance_status. FULL means complete **registered** upstream graph with closed
terminal provenance and no unterminated support component. It does not prove that
an unregistered literary inference has been discovered. Minimal is always PARTIAL.

Event provenance is an optional **versioned extension** (`provenance.version=1.0.0`),
not a rewrite of runtime schema 3.0.0. It contains authority, class, origin_ref and
temporal_scope (axis/domain/from/optional until). Catalogs are supplied explicitly
to owners (`--provenance` or manifest `paths.provenance`); never fabricated.

| Class | Required registered closure |
| --- | --- |
| manuscript | evidence origin_ref → anchor_ref → source_revision_ref; valid anchor span and fingerprint; revision and source digest |
| planning / imported / migration | sources origin_ref with matching kind, revision and SHA-256 content identity |
| user_confirmed | confirmations origin_ref with confirmed=true, confirmed_by, canon_ref |
| derived | rules origin_ref with matching rule_version and deterministic=true; nonempty derived_from events recursively CLOSED |

Catalog tables are ID→record dictionaries: sources, source_revisions, evidence,
anchors, confirmations, rules. Missing provenance is UNRESOLVED (LEGACY_UNCLOSED);
missing required fields are PARTIAL; dangling references, invalid source status or
cycles are BROKEN. Complete verified structure is CLOSED. This checks registered
source identities and structural evidence closure; it does not interpret source
meaning or attest an untrusted catalog's authorship.

`committed` alone still does not assert objective canon. Explicit `authority=
canonical` or `audit_closed=true` is promotion and requires closure in runtime
validation and schema project validation. Production transaction preflight requires
closure for **every newly appended event**, including requests omitting the marker;
legacy compatibility cannot be used to write new unclosed rows. Legacy events without
promotion markers load with warnings and remain UNRESOLVED. Strict audit rejects
all unclosed events. No old event bytes are rewritten; normalize_legacy_event does
not add evidence, authority, closure or transaction hashes.

## Transaction identity and recovery

Identity version 1.0.0 uses UTF-8 canonical JSON (sorted keys, compact separators,
finite numbers) → SHA-256. Event list/effect order stays significant. Schema/event
version and committed event status defaults are normalized; branch and sequence
inside proposed events are writer-owned. At request level, missing branch,
expected_effective_revision and blocking_objections normalize to main/null/[];
all other request controls and unknown fields participate in identity.

Excluded request fields: transaction_id, status, committed_event_ids, diagnostics,
retry_metadata, correlation_id, timestamp, committed_at. Event payload fields,
including story_time and source/provenance, remain semantic. Whitespace and object
key order do not participate. JSON integer/float representations are preserved.

Every atomically appended event stores transaction_identity_version and
transaction_payload_sha256. Same ID requires matching event IDs/count and every
stored digest. Older logs without hashes fail closed as unverifiable conflicts;
they remain replayable, and are never silently upgraded to safe retry. A new ID is
a new request and still obeys event collision/concurrency checks. Original receipt
is reconstructed through the committed transaction head, including after later
commits, process restart or a crash between log append and transaction-file update.
