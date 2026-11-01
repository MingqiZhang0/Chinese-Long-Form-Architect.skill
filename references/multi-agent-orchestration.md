# Multi-Agent Orchestration and Role Isolation

Use this reference when the platform supports subagents or when a large project benefits from strict role-separated passes.

## Contents

- Core principle
- Role map
- Director contract
- Handoff protocol
- Stage pipelines
- Write permissions
- Fallback without subagents
- Failure handling
- Objection / override protocol
- Audit

## 1. Core principle

Separate **coordination**, **creative generation**, **state mutation**, and **critique** whenever project complexity justifies it.

The Director coordinates and verifies. It should not become the default prose writer.

When native subagents are available, use them. When they are not, simulate the same architecture as serial role-isolated passes and preserve the same handoff boundaries.

Never expose hidden chain-of-thought. Handoffs contain conclusions, evidence, blockers, and required state only.

## 2. Role map

### Director / Orchestrator

Owns stage routing, user checkpoints, task boundaries, and acceptance criteria. Does not write final prose by default.

### Research Grounder

Owns external evidence gathering under `reality-grounding-research.md`. May propose project facts but cannot silently make them canon.

### World-State Simulator

Advances current world, organizations, offscreen actors, logistics, inertia, rumors, and environment under existing canon. Does not choose page-time presentation.

### Causal Architect

Designs or audits hidden causal processes, branches, antagonist adaptation, and long-range dependencies. Does not write finished prose.

### Chapter / Scene Planner

Builds chapter missions, selects scenes, establishes dramatic deltas, and instantiates Scene Packets from live state.

### Writer

Writes prose only from the authorized context pack and current mission. It cannot silently retcon protected canon or rewrite state ledgers.

### Continuity Auditor / Red Team

Runs deterministic checks first, then adversarial review. It diagnoses; it does not silently rewrite the chapter.

### Reader Simulator

Receives only reader-visible prose/context for a selected profile and reports comprehension, memory, hypotheses, confusion, and perceived fairness. It must not see hidden canon or "correct answers" except in explicit rereader mode.

### Revision Analyst

Compares before/after prose, classifies semantic impact, proposes candidate state/dependency deltas, and never commits them. Mechanical alignment comes from `scripts/revision_diff.py`; semantic classification remains an interpretive pass.

### Humanities Analyst

Performs philosophy/history/psychology and adjacent-domain extraction only when an explicit request or configured milestone/diagnostic/custom trigger fires. Do not schedule this role after every ordinary chapter. Its reports are nonbinding until user approval.

### Committer / Updater

Reconciles prose against Scene Packets and project state, performs atomic commits, propagates invalidations, and records approved user decisions. It does not invent missing narrative events.

## 3. Director contract

The Director should:

1. determine the current lifecycle stage;
2. choose the minimum required roles;
3. compile or request role-appropriate context;
4. issue a bounded task order;
5. verify expected artifacts exist;
6. run deterministic checks before subjective review where possible;
7. surface blockers to the user when a user decision is genuinely required;
8. advance only after acceptance criteria are satisfied.

Do not let the Director "help" by doing the Writer's work inside the dispatch step.

## 4. Handoff protocol

Every significant cross-role handoff should state:

- `task_id`;
- `stage`;
- `role`;
- `goal`;
- authoritative inputs;
- allowed reads;
- allowed writes;
- forbidden mutations;
- required outputs;
- acceptance criteria;
- blockers / unresolved decisions;
- status: `PENDING`, `RUNNING`, `BLOCKED`, `DONE`, `REJECTED`.

Use `assets/orchestration/task-order-template.json` for automated workflows or `assets/orchestration/task-order-template.md` for human-readable handoffs. Their execution profile is intentionally unset until capability probing/profile selection; task isolation requirements express desired guarantees, not proof those guarantees are available. Validate JSON orders with `scripts/validate_task_order.py`.

Reusable role cards live under `assets/orchestration/role-cards/`; load only the assigned role card. The canonical role-to-clearance registry is `assets/orchestration/role-clearance.json`; bundled tools read this registry rather than maintaining private copies.

The next role should consume the handoff artifact, not reconstruct the prior role's hidden reasoning.

## 5. Stage pipelines

### New-project pipeline

```text
Director
  -> Research Grounder
  -> World-State Simulator / Causal Architect
  -> Planner
  -> readiness review
  -> Context Compiler
  -> Writer
  -> Continuity Auditor
  -> Committer
  -> Humanities Analyst
  -> user thematic decision
```

Roles may loop backward when acceptance fails.

### Normal chapter pipeline

```text
Director
  -> Simulator
  -> Planner
  -> Context Compiler
  -> Writer
  -> Auditor
  -> Committer
  -> Humanities Analyst
```

Do not invoke every specialist when the chapter does not need them.

### Revision pipeline

Use: mechanical revision alignment -> Revision Analyst semantic-impact report -> Continuity Auditor -> Director/user approval when canon changes -> Committer -> dependency propagation. Do not let a prose rewriter silently serve as its own migration authority.

Route the diagnosed layer to the owner first. For example, a spatial contradiction should not begin with a line editor.

## 6. Write permissions

Use least privilege.

- Research Grounder: research files only.
- Simulator: state proposals / simulation notes, not final prose.
- Planner: missions / Scene Packets / plans.
- Writer: chapter or scene prose draft only.
- Auditor: findings / reports only.
- Humanities Analyst: sidecar analysis reports only.
- Committer: canonical state and approved status transitions.
- Director: order/status files and orchestration metadata.

If the platform cannot enforce filesystem permissions, enforce them procedurally and audit changed files before commit; `scripts/audit_workspace_changes.py` can compare before/after content hashes against allowed path prefixes.

## 7. Fallback without subagents

Use `single-agent-isolation.md` as the canonical owner of no-subagent fallback.

Do not equate prompt-level role switching with fresh-context isolation. Select and record an execution profile (`native-multi-agent`, `clean-room-serial`, `soft-serial`, or `minimal-local`), preserve Task Orders and pass artifacts, and downgrade blindness/independence claims when the runtime cannot provide them.

Role isolation is more important than pretending multiple agents exist.

## 8. Failure handling

- If deterministic validation fails, return to Planner/Committer before prose polishing.
- If Writer needs unavailable canon, mark `BLOCKED`; do not improvise a high-impact answer.
- If Auditor finds a causal flaw, send the finding to Director with the smallest repair layer.
- If Humanities Analyst finds an interesting philosophical or psychological line, do not route it to Writer until the user approves expansion.
- If two roles disagree, preserve both findings and let Director resolve using canon priority or ask the user when it changes creative intent.

## 9. Objection / override protocol

Specialist agents may raise a formal **OBJECTION** instead of forcing an invalid task through. Typical grounds:

- Writer: requested behavior conflicts with current character state/knowledge;
- Research Grounder: evidence is insufficient or scope-mismatched;
- Simulator: logistics/resources make the planned event impossible;
- Causal Architect: an actor has a materially better available strategy;
- Auditor: continuity or camera integrity fails;
- Committer: the prose does not establish the state change it is being asked to record.

An objection should contain:

- objection ID;
- task ID / role;
- violated constraint;
- supporting evidence;
- severity: `advisory / blocking`;
- smallest safe alternatives.

A blocking objection prevents `DONE` until the Director either resolves it or records an explicit override with rationale. Overrides are project decisions and must be visible to later audit; they are not permission to hide contradictions.

The Director should prefer repair over override when a higher-priority canon/causal rule is involved.

## 10. Audit

### Operational reports and evidence

For consequential work, use the versioned operation extension of the existing
pass/checkpoint; see `docs/auditability-contract.md`. `subagent-reported PLANNED`,
`RUNNING`, `DONE`, or `FAILED` describes the report, not verified world state.
The Director must inspect artifacts/canonical state or run the owner's validator
before claiming VERIFIED. Completion is not verification. A conflicting report
cannot override a fresh canonical review snapshot or other authoritative source;
retain the conflict and consult `storyctl status PROJECT_ROOT --json`.
Do not announce dispatch before a real invocation exists. Do not design trust
scores or a delegated verification framework here; P1-14 remains deferred.

The older PENDING/BLOCKED/REJECTED handoff labels are scheduling/disposition
metadata. New operational claims use PLANNED/RUNNING/DONE/VERIFIED/FAILED and
receipt-backed transitions; task disposition never supplies execution evidence.

Check:

- Did the Director write prose it should only dispatch?
- Did the Writer mutate canon ledgers?
- Did the Auditor quietly rewrite instead of diagnose?
- Did the Reader Simulator receive backend answers a real reader could not access?
- Did the Revision Analyst classify a change and then commit it without approval?
- Did the Humanities Analyst smuggle commentary into future prose without approval?
- Did the Committer invent an unshown transfer/event to make state line up?
- Was the context pack role-appropriate and spoiler-safe?
- Were deterministic checks run before subjective judgment where applicable?

## Project Poetics ownership and handoff

The Director/Planner owns compilation and proposed evolution of Project Poetics. The Writer receives only the **approved scoped derivative** required for the current task.

- Do not ask the Writer to reconstruct project poetics from generic craft lore.
- Do not expose raw rejected alternatives or hidden future answers merely to explain a do-not-optimize rule.
- A Planner may propose a poetics update discovered from draft behavior, but promotion follows `discovery-drafting.md` / user authority.
- Auditor findings must distinguish hard-integrity errors, scoped-poetics violations, unauthorized drift, and harmless absence of another poetics' virtue.
- Committer may update world state without altering Project Poetics, and vice versa, unless the approved change genuinely affects both.
