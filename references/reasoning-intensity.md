# Reasoning Intensity and Semantic Work Scheduling

Use this reference when the user chooses **Low / Medium / High / XHigh / Max**, when a project stores a default reasoning-intensity policy, or when a substantial task needs explicit control over semantic search, alternatives, verification, and cost. This reference owns the **Intensity Contract**, Semantic Work Proposal/Result/Trace contracts, Reasoning Epoch, scheduler invariants, calibration boundary, and longitudinal intensity strategies. It does not own governance, canon authority, context permissions, or literary evaluation.

## Contents

- Core laws
- Orthogonal axes
- Mandatory Closure
- Five user-facing levels
- Semantic Work contracts
- Work graph and Reasoning Epoch
- Scheduling laws
- Calibration
- Strategies and overrides
- Portability and degradation
- v0.1 scope boundary
- Maintenance checks

## 1. Core laws

Treat intensity as a **resource-allocation and search policy**, not a quality label and not a token slider.

Preserve these laws:

1. **Intensity controls search, not authority.** More compute never grants canon, secret, OpenIssue, Writer, or authorial permission.
2. **Intensity controls semantic surplus, not the correctness floor.** Required governance/invariant checks remain required at Low.
3. **More compute does not require more context.** Compile the smallest sufficient role-safe context even at Max.
4. **More reasoning does not require more formalization or more predetermined future.** A Max pass may conclude that ambiguity should remain unformalized or OpenIssue should remain open.
5. **More internal reasoning does not require longer prose or more story complexity.** Search complexity and page-time complexity are separate.
6. **Higher tiers widen optional permission monotonically; actual execution need not be monotonic.** Max may prune more, reuse more, or stop earlier than a lower tier on a simple task.
7. **Future capabilities enter through Semantic Work contracts.** Do not redefine the five levels merely because a new module exists.
8. **Termination is mandatory.** No intensity permits unbounded proposal spawning, verifier loops, or circular deliberation.

Do not market Max as “best.” Low can be the correct economical policy for a stable local chapter. Max means the lowest justified stopping threshold inside the current capability set, not unlimited computation.

## 2. Orthogonal axes

Keep three axes separate:

- **Governance** (`lean / persistent / forensic`) — which durability, recovery, audit, reconciliation, and invariant protections the project requires. Owned by `project-operability.md`.
- **Reasoning Intensity** (`low / medium / high / xhigh / max`) — how aggressively the current task explores optional semantic work and verification.
- **Strategy** — the longitudinal schedule of intensity across kickoff, ordinary chapters, reveals, retcons, or architecture rebuilds.

Examples:

- `forensic + low` — strict durable protection with economical local reasoning;
- `lean + max` — deep analysis without forcing heavy persistent infrastructure;
- `max-bootstrap-low-incremental` — Max for foundational architecture, Low for ordinary chapter work, with event-triggered refreshes.

Do not infer one axis from another.

## 3. Mandatory Closure

Before optional expansion, close every directly applicable requirement whose omission could make the result unsafe or semantically false. Typical Mandatory Closure includes:

- fixed canon and explicit user locks;
- actor knowledge / POV legality;
- secret and role visibility boundaries;
- OpenIssue preservation and resolution authority;
- directly relevant spatiotemporal state and travel feasibility;
- directly relevant finite-resource conservation;
- active governance invariants and required commit gates;
- indispensable causal premises of the current task.

A capability may submit a `necessity_claim`; it may not grant itself mandatory status. Admission into Mandatory Closure must be justified by a canonical law, hard invariant, active governance requirement, or indispensable current-task premise.

If the required assurance cannot be executed in the available runtime, report `ASSURANCE_UNAVAILABLE` or degrade the requested operation. Do not silently delete the check and call the Low result safe.

## 4. Five user-facing levels

These are behavioral anchors. Do not encode fixed token counts, fixed chain counts, fixed module lists, or platform-native reasoning knobs into the contract.

### Low — reliable local completion

Ask: **What is required to complete the current task reliably?**

After Mandatory Closure, prefer the highest-value local/direct reasoning. Follow a deep chain when it is necessary to the task; do not proactively fan out into broad long-horizon systems merely because they are imaginable. Use Low for ordinary stable continuation when economy matters.

### Medium — persistent residue

Ask: **What nearby consequence will remain after this task?**

Add relationship residue, recent reader consequences, nearby future feasibility, and other persistent effects likely to matter soon. Use limited alternative checking without broad proactive cross-layer search.

### High — cross-layer search

Ask: **Which deeper systems are materially connected to this change?**

Proactively search for consequential cross-layer links such as event -> knowledge -> organization -> public version -> reader model, or scene choice -> relationship residue -> institutional incentive -> future feasibility. High increases useful-edge recall rather than prose density.

### XHigh — interaction search

Ask: **How do the important deep chains change one another?**

Study feedback among consequential chains, materially distinct alternatives, and loops such as organization response -> public clue -> rumor -> hidden-actor adaptation -> revised organization response. Do not force interaction where evidence does not justify it.

### Max — adaptive convergence

Ask: **After exploration, comparison, verification, pruning, and reallocation, what remains the most robust account?**

Run an adaptive loop when the task warrants it:

`explore -> compare -> verify -> prune -> reallocate -> stop`.

Spend substantial extra effort on verification and counterfactual rejection, not endless brainstorming. Stop when further rounds merely rephrase, reconfirm, or add low-value detail. Preserve legitimate plurality/nonconvergence instead of manufacturing consensus.

## 5. Semantic Work contracts

The five levels do not own modules. Each semantic owner may propose work through a small interoperable contract.

Use `assets/intensity-schemas/work-proposal.schema.json` for proposals. Core fields include:

- stable identity and capability/operation;
- epoch and target references;
- a **necessity claim**, never self-granted mandatory authority;
- semantic scope tags such as local, persistence, cross-layer, interaction, alternative, or verification;
- coarse cost hint and value/risk signals;
- capability requirements;
- authority ceiling;
- basis: branch, epoch revision, semantic dependency fingerprint, and security domain;
- namespaced extensions for future capability-specific metadata.

Use `assets/intensity-schemas/work-result.schema.json` for results. Results must carry:

- proposal/epoch identity;
- basis/provenance and dependency references;
- typed result kind;
- noncanonical authority class;
- freshness/reusability metadata;
- a semantic digest when useful for deduplication or oscillation detection.

There is intentionally **no direct-canon result authority**. New capabilities may produce observations, analyses, validation results, context derivatives, or candidate deltas. Canon mutation remains behind the existing canonical owner and transaction/commit gates.

### Authority conservation

A computation may lower its result authority but may not raise it above the caller/proposal/capability ceiling. More compute never promotes hypothesis to fact, working interpretation to canon, or privileged Planner information into Writer-safe information.

### Security-domain separation

Compute identity and information-flow identity are separate. Do not reuse a privileged cached result directly in a lower-clearance role merely because the operation/target are otherwise identical. Derive a sanitized result through the existing visibility/context boundary.

## 6. Work graph and Reasoning Epoch

Keep the **Narrative Dependency Graph** separate from the temporary **Semantic Work Graph**.

The Work Graph may grow dynamically during a task. Use only these scheduling dependency meanings unless a later contract version proves another is necessary:

- `requires` — hard blocking prerequisite;
- `informs` — useful but nonblocking information;
- `refines` — bounded iterative feedback is permitted.

Do not require the Work Graph to be acyclic. Classify strongly connected components:

- hard `requires` cycles -> restructure, joint-solve, or block; never spin;
- validated refining feedback groups -> bounded delta iteration;
- nonmonotone/unknown cycles -> bounded deliberation, synthesis, or explicit nonconvergence.

Default new capabilities to conservative nonmonotone/unknown behavior until tested.

### Reasoning Epoch

Run substantial analysis against a frozen semantic basis/branch head `R`:

1. freeze the epoch at `R`;
2. propose/admit/schedule read-only semantic work;
3. produce typed results and candidate deltas;
4. synthesize the task output;
5. pass any durable state change through the existing canonical owner/transaction gate;
6. if the branch head changed, rebase/revalidate rather than allowing last-writer-wins.

Do not let optional analysis mutate canon mid-epoch and then use its own mutation as evidence.

## 7. Scheduling laws

### Assurance reservation

Reserve required assurance before optional exploration. Optional work may consume released unused assurance only after required checks are satisfied; optional exploration must never starve the correctness floor.

### Budget conservation

Work may discover new questions; it may not create new compute entitlement. Child proposals re-enter the existing frontier and compete inside the current run budget. Proposal generation itself has cost.

### Demand-driven liveness

Optional work remains live only while it is a selected root or required by another live work item. Reclaim orphaned work after all consumers disappear.

### Priority inheritance

Propagate urgency only along hard `requires` dependencies. Do not inherit urgency through `informs` or `refines`; otherwise low-value optional analysis can borrow the importance of a critical parent.

### Deduplication and reuse

Coalesce semantically identical work using a Work Key derived from capability, operation, target, semantic dependency fingerprint, and security domain. Bind semantic freshness to the inputs actually read, not to the entire project revision.

Distinguish:

- `epoch-stale` — branch head changed; authoritative commit requires revalidation/rebase;
- `semantic-stale` — a dependency fingerprint changed; recomputation is required;
- `reusable` — the epoch changed but relevant semantic dependencies did not.

### Stop conditions

Permit at least three honest stops:

- **solved** — task is sufficiently resolved;
- **economic** — additional optional reasoning has too little expected value for its cost;
- **plurality/nonconvergence** — further iteration oscillates among legitimate alternatives without a justified winner.

A hard liveness ceiling remains a runtime safety guard at every level; its numeric value belongs to calibration/runtime adapters, not this contract.

## 8. Calibration

The contract defines what each tier means; calibration defines how the current Skill/model/runtime realizes it.

Version separately:

- `intensity_contract_version`;
- `scheduler_version`;
- `calibration_version`;
- `benchmark_version`.

Use `assets/intensity-calibration/default-v0.1.json` only as the packaged transparent starting calibration. It contains behavioral postures, not permanent token budgets.

Calibrate levels as distinct **quality/reliability-cost operating regions**, not five absolute budgets. On an appropriate workload the tiers should be empirically distinguishable in behavior and average resource use, while individual simple tasks may stop early and violate strict per-run cost monotonicity.

Do not optimize calibration against one benchmark track. Use development/calibration/holdout splits, cross-track generalization, Pareto inspection, and live longitudinal evidence. If two adjacent tiers collapse behaviorally, adjust calibration rather than redefining the contract unless the behavioral anchor itself is genuinely wrong.

## 9. Strategies and overrides

A project may store a default intensity, while a task may override it. Never let an override change governance, authority, or visibility.

Useful strategies include:

- `steady-low`, `steady-medium`, etc.;
- `max-bootstrap-low-incremental`;
- `event-triggered-refresh` — Low/Medium ordinary work with High/XHigh/Max on major reveal, high-blast revision, OpenIssue horizon, hidden-process collision, institution doctrine change, irreversible relationship shift, or dependency hot spot.

Treat these as strategy presets, not tier definitions. Benchmark them against alternatives rather than blessing one universally.

## 10. Portability and degradation

Reasoning Intensity is runtime-independent. An adapter may realize High/Max through more model reasoning, tool queries, subagents, isolated passes, stronger models, or better retrieval. Native platform reasoning-effort controls are optional implementation mechanisms.

If a proposal requires an unavailable capability, mark it `UNSUPPORTED` or use an explicit degraded fallback. Never pretend a blind/isolated/parallel check ran when the runtime could not provide it.

A future Skill may make tomorrow's Low stronger than today's Max. Intensity is a relative allocation policy inside a recorded system configuration, not an absolute intelligence score.

## 11. v0.1 scope boundary

### MUST now

- stable five-level behavioral contract;
- Mandatory Closure and authority/assurance/security laws;
- Work Proposal/Result/Trace contracts;
- Reasoning Epoch and dynamic work-graph rules;
- transparent calibration boundary;
- user/project/task intensity selection;
- longitudinal benchmark specification and deterministic STC v0.1 semantic-conformance kernel.

### SHOULD now

- record compact Intensity Trace metadata when evaluating/calibrating;
- use semantic dependency fingerprints for reuse when the runtime can provide them;
- exercise extension/mutation/metamorphic cases in maintenance.

### LATER

- learned scheduler/ranker;
- uncertain/stochastic environment control;
- cross-platform universal compute units;
- full automatic 100+ chapter LLM experiment runner;
- adaptive benchmark item selection after a fixed paired bank is established.

### DO NOT BUILD

- fixed tokens/chains per tier as contract;
- “High modules” or “Max modules”;
- Max = load all references/context;
- a general planning/PDDL operating system for the novel;
- a single Intensity quality score;
- automatic formalization because a tier is high;
- direct canon write authority for future capabilities.

## 12. Maintenance checks

Use `scripts/intensity_runtime.py` to validate configs, proposals, results, and trace events. Use `intensity-longitudinal-benchmark.md` for STC and calibration evidence.

When changing this contract, test at minimum:

- duplicate proposal coalescing;
- hard-cycle rejection and bounded feedback termination;
- priority inheritance only along `requires`;
- no child-created budget entitlement;
- authority conservation;
- cross-security-domain cache isolation;
- incremental invalidation by semantic dependency rather than unrelated project change;
- future unknown capability degradation;
- Max early-stop and legitimate nonconvergence;
- intensity placebo / no-op-adapter behavior in benchmark maintenance.
