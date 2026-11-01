# Single-Agent Isolation Runtime

Use this reference when native subagents are unavailable, unreliable, too expensive, or intentionally disabled. It defines the strongest honest fallback from a multi-agent fiction pipeline to serial role-isolated execution.

## Contents

- Core principle
- Capability probe and execution profiles
- Information-clearance model
- Clean-room serial execution
- Soft-serial execution
- Pass envelopes and checkpoints
- Handoff sanitation and taint
- Writer and Reader isolation
- Audit independence
- Crash recovery and resume
- Failure rules
- Audit checklist

## 1. Core principle

Do not pretend that role prompting creates independent agents.

A single model may perform multiple logical roles, but **role separation, context isolation, and evaluator independence are different properties**. Record which property is actually available.

Preserve the architecture as far as the runtime permits:

```text
role contract
    -> authorized inputs
    -> bounded context pack
    -> one pass
    -> explicit output artifact
    -> checkpoint
    -> next pass
```

Never use hidden chain-of-thought as a handoff. Persist conclusions, evidence, blockers, candidate deltas, and artifact references only.

## 2. Capability probe and execution profiles

Before a substantial pipeline, determine whether the environment supports:

- native subagents or agent-as-tool calls;
- whether native agents actually receive isolated LLM-visible contexts rather than a shared message history;
- fresh model contexts / isolated invocations;
- persistent project files;
- deterministic scripts/validators;
- isolated workspaces or filesystem permission enforcement;
- an evaluator that is genuinely independent from the Writer pass.

Use `assets/orchestration/capabilities-template.json` as the capability-probe input shape and run `scripts/select_orchestration_profile.py` to derive the execution profile. The template is deliberately deny-by-default: every capability begins `false` until the environment has actually established it. Do not hand-edit a preselected execution profile to match hoped-for capabilities. Native subagent availability and native context isolation are separate capability flags.

Choose exactly one profile.

### Profile A - `native-multi-agent`

Use distinct agents or agent invocations with explicit role contracts. **Do not assume native multi-agent automatically means context isolation**: some frameworks intentionally share one message history across participants. Blind Writer/Reader claims require isolated agent contexts or a separate fresh invocation. Parallel work is allowed only when writes cannot race or when tasks are read-only.

This is the strongest default when the required isolation capability is actually present.

### Profile B - `clean-room-serial`

Use one orchestration process but start each sensitive role in a **fresh model context**. Persist state only through explicit artifacts and role-scoped context packs.

This can preserve strong information isolation even without simultaneous subagents. It does **not** imply model-family independence: Writer and Auditor may still share model biases if they use the same model.

### Profile C - `soft-serial`

Use the same continuing model context for sequential role passes because a fresh context cannot be created.

This preserves workflow separation and write discipline, but it **cannot erase information already seen by the model**. Therefore:

- do not claim blind Writer or blind Reader evaluation;
- do not claim the Auditor is independent merely because the prompt says "now be the Auditor";
- treat context packs as task focus and provenance controls, not secrecy barriers;
- rely more heavily on deterministic validators, explicit evidence, and human review for high-stakes decisions.

### Profile D - `minimal-local`

Use when persistent files, deterministic validation, or reliable pass artifacts are unavailable. Restrict this profile to contained tasks. Do not claim persistent-runtime, branch-isolation, blindness, or resumability guarantees that the environment cannot provide.

## 3. Information-clearance model

Use a simple clearance ladder for orchestration, not for story truth:

| Clearance | Typical roles | May contain |
| --- | --- | --- |
| 0 | blind Reader Simulator | reader-visible prose only |
| 1 | Writer, chapter-only Humanities Analyst | present/past authorized drafting material; no hidden future answers |
| 2 | Planner, Revision Analyst, Auditor, Research Grounder | current canon, diagnostics, planning-relevant state |
| 3 | Director, Causal Architect, World Simulator, Committer | hidden causal state, future plans, branch/backend state, author-only decisions |

This is a **maximum visibility class**, not a requirement to expose everything at that class.

### No false downgrade

If one model context has already seen clearance 3 information, switching its prompt to a clearance 1 role does not make the context clearance 1 again.

Therefore:

- a lower-clearance role after a higher-clearance role requires a fresh context to claim strong isolation;
- if fresh context is impossible, label the lower-clearance pass `soft` / `nonblind`;
- blind Reader simulation is invalid after backend exposure in the same context;
- a Writer may still draft in soft-serial mode, but future-leak protection becomes an output-audit problem rather than a true information barrier.

## 4. Clean-room serial execution

For each pass:

1. persist the previous role's required outputs;
2. close that role logically;
3. create a fresh model invocation/context;
4. load only the assigned Role Card;
5. load the Task Order;
6. compile a new target-role context pack with strict visibility;
7. run the pass;
8. write only allowed outputs;
9. validate the pass envelope and outputs;
10. checkpoint before starting the next role.

Do **not** copy the full prior conversation into the fresh context. Handoff artifacts replace conversational inheritance.

For Writer and Reader Simulator passes, prefer `strict_visibility: true` in Context Compiler requests. Use `scripts/build_role_pass_bundle.py` to materialize a self-contained role card + Task Order + execution profile + compiled context pack/manifest for a fresh invocation.

## 5. Soft-serial execution

When all roles must share one model context:

1. still issue separate Task Orders;
2. still compile separate role-scoped packs;
3. persist outputs between passes;
4. treat filesystem/write permissions as least-privilege contracts;
5. run deterministic checks before model critique;
6. mark blindness and evaluator independence as unavailable unless supplied externally;
7. where possible, execute lower-clearance diagnostic roles **before** exposing higher-clearance backend information;
8. never use a soft Reader Simulator as evidence that a reveal is fair or surprising;
9. never use same-context Writer self-review as the sole basis for accepting a fragile causal turn.

A soft-serial Writer remains useful. The limitation is epistemic independence, not the ability to write.

## 6. Pass envelopes and checkpoints

Consequential claims obey `claim <= machine-supported state` even in a single
continuing model context. Remembering an intended test is not invocation evidence.
“I ran it” requires actual receipts/results, and “verified” requires the separate
inspection defined in `docs/auditability-contract.md`. Completion is not
verification. Consult `storyctl status PROJECT_ROOT --json`; never reconstruct
execution truth from conversational memory or stale reports.

New checkpoints initialize operations PLANNED. `set-active` requires --root and
--started-evidence pointing to the actual invocation receipt; `complete` requires
--root and a receipt-backed DONE envelope. `record-operation CHECKPOINT RECORD
--root PROJECT_ROOT` registers generic consequential operations and advances
DONE to VERIFIED or records FAILED using the same run, without a parallel ledger.
Legacy scheduling checkpoints remain readable but cannot authorize new operational
completion claims. Start a new run rather than rewrite historical evidence.

Every substantial role pass should emit a pass envelope using `assets/orchestration/pass-envelope-template.json`. The template is deliberately conservative: `execution_profile` is unset and blindness is unclaimed until capability probing/profile selection has actually established them.

Record at least:

- `pass_id` and `task_id`;
- role and execution profile;
- context ID / fresh-context status;
- clearance;
- whether blindness is required or claimed;
- active branch and runtime HEAD/revision read;
- context-pack and manifest paths/hashes;
- input artifact hashes where practical;
- allowed outputs and actual outputs;
- status and blockers;
- source passes / handoff lineage.

Maintain a run checkpoint using `assets/orchestration/run-checkpoint-template.json` so recovery starts from durable artifacts rather than reconstructed conversational memory. Fill its `execution_profile` from the selected profile; the template never preselects one.

Validate the run with `scripts/validate_orchestration_run.py`. Use `scripts/orchestration_checkpoint.py` to initialize, activate, complete, block, and atomically persist serial-run checkpoints. Persist pass-envelope references in canonical checkpoint-relative form when possible; relative/absolute aliases of the same artifact must deduplicate to one durable reference.

## 7. Handoff sanitation and taint

A summary produced by a privileged role is **not automatically safe** for a lower-clearance role.

Treat handoff information as tainted by the highest visibility of its source unless it is deliberately transformed for the target role.

Rules:

- do not pass raw Director/Causal-Architect notes to Writer or Reader Simulator;
- do not assume removing tool-call metadata removes secrets already copied into ordinary prose;
- compile target-role context from authoritative project artifacts, not from the previous model transcript;
- mark intentionally sanitized derivatives as such and retain provenance to the source artifact;
- a sanitizer may remove information, but it cannot invent replacement facts;
- when the target role requires blindness, any uncertain sanitation should fail closed and omit the item.

Context Compiler visibility labels are part of the boundary. They are not a substitute for authorization on write tools.

## 8. Writer and Reader isolation

### Writer

Strong Writer isolation requires either:

- a native isolated agent/context; or
- a clean-room serial fresh context.

The Writer receives only its Role Card, Task Order, mission, Scene Packet, and compiled authorized pack.

In soft-serial mode:

- set blindness claims to false;
- require post-draft leakage/continuity review for high-risk reveals;
- treat consequential novel facts absent from the Writer pack as discoveries or blockers, not silent canon.

### Reader Simulator

A **blind** Reader Simulator is only valid in a fresh context that has not seen backend truth.

If this cannot be arranged:

- do not run a pseudo-blind reader and report it as evidence;
- instead run an ordinary reader-model audit and label it `NONBLIND_DIAGNOSTIC`;
- for real blindness, use a fresh session/model invocation or a human reader.

Rereader mode is different: it may intentionally receive resolved truth, but that must be declared.

## 9. Audit independence

Separate these labels:

- **role-separated** - different instructions/checklist;
- **context-isolated** - evaluator did not receive Writer-only/hidden context;
- **model-independent** - different model/model instance is used as an evaluator;
- **human-independent** - human review is available;
- **externally-verified** - deterministic or external evidence can check the claim.

Do not collapse them into one word such as "independent".

Same-model critique can still be useful for style, completeness, and adversarial prompting, but it is not a substitute for deterministic verification or truly independent review when correctness is mechanically checkable.

For fragile continuity, logistics, branch, transaction, and invariant claims:

1. run deterministic validators first;
2. provide the Auditor explicit evidence and failure locations;
3. then perform interpretive/adversarial review;
4. escalate to a fresh evaluator or human when the decision remains high impact and uncertain.

## 10. Crash recovery and resume

After every completed pass:

- persist outputs;
- persist/refresh the pass envelope;
- update the run checkpoint atomically where possible;
- record the runtime HEAD/revision used and produced when applicable.

On resume:

1. read the run checkpoint;
2. verify hashes / expected output artifacts;
3. verify current branch HEAD against the pass preconditions;
4. resume from the first incomplete or invalidated pass;
5. do not regenerate completed work merely because the conversation transcript is unavailable.

A checkpoint is a recovery aid, not canon.

## 11. Failure rules

Fail or degrade explicitly when:

- a pass claims blindness but reuses a contaminated context;
- a clearance downgrade occurs without a fresh context while strong isolation is claimed;
- a Reader Simulator receives non-reader-visible context;
- the Writer context manifest/hash no longer matches the compiled pack;
- a completed pass lacks its required output artifact;
- the run resumes from an old HEAD after canon advanced;
- a role writes outside its permission boundary;
- a same-model audit is labeled independent without an independent evaluator;
- a privileged handoff is forwarded raw to a lower-clearance role;
- a runtime limitation makes a claimed guarantee impossible.

Prefer an honest weaker profile over a fictitious stronger one.

## 12. Audit checklist

Ask:

- Which execution profile is active, and is it actually supported?
- Did any lower-clearance role inherit a model context that already saw higher-clearance facts?
- Are blind-reader results genuinely blind?
- Did Writer receive only a compiled pack, or did raw backend notes leak through handoff text?
- Are handoff conclusions externalized as artifacts rather than remembered from hidden reasoning?
- Are deterministic checks providing external feedback before same-model self-critique?
- Can the pipeline resume from the checkpoint without reconstructing secret conversational state?
- Are output/write permissions checked after each pass when the platform cannot enforce them natively? Use before/after workspace snapshots where practical.
- Are independence claims labeled precisely?
