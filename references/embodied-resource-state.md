# Embodied, Resource, and Logistics State

Use this reference when bodies, supplies, money, capacity, transport, energy, labor, recovery, or other finite material constraints can change what actors are able to do. It owns **operational bodily continuity and resource/logistics accounting**. Activate it at the resolution justified by causal risk or current Project Poetics; material embodiment is a capability, not a universal demand for maximal logistical detail. It does not provide medical diagnosis or replace real-world research.

## Contents

- Core principle
- Embodied state
- Recovery and residue
- Resource state
- Logistics and capacity
- Conservation discipline
- Evidence and precision
- Scene integration
- Institutions and populations
- Runtime integration
- Failure modes

## 1. Core principle

Characters do not act from beliefs alone. They act through bodies and finite material systems.

Ask:

> Given the current body, inventory, money, access, capacity, time, infrastructure, and support network, what is actually feasible now?

Do not make resources appear because the plot needs them, and do not make a body reset because the scene changed.

## 2. Embodied state

Track only bodily variables that can constrain later action. Depending on genre, this may include:

- sleep / sleep debt;
- fatigue / exertion;
- hunger / food access;
- thirst / hydration access;
- pain;
- injury and mobility;
- illness symptoms;
- medication/treatment timing;
- intoxication or withdrawal when relevant;
- temperature/weather exposure;
- sensory impairment;
- pregnancy/menstrual or other physiological states when materially relevant and appropriately researched;
- rehabilitation / recovery stage;
- chronic limitation when established by the story.

Prefer qualitative or coarse states unless reliable evidence and plot need justify numbers.

For projects that need a machine-readable starter ledger, use `assets/state-templates/embodied-resource-ledger-template.json`; delete irrelevant example fields rather than adopting them as universal story state.

Good:

- `sleep: severely-deprived`;
- `left_arm: limited-load`;
- `pain: worsening-under-movement`.

Use exact blood loss, drug half-life, calorie expenditure, etc. only when the story truly depends on them and research supports the model.

## 3. Recovery and residue

Recovery is a process, not a boolean switch.

For important injuries/conditions track:

- onset event;
- immediate functional loss;
- treatment received;
- expected course/range, if grounded;
- restrictions;
- flare/reinjury conditions;
- psychological/social residue if separately relevant;
- last evidence-based update.

A healed state may still leave scars, reduced confidence, altered tactics, cost, or reputation.

## 4. Resource state

Possible finite resources include:

- money / credit / debt;
- food / water;
- fuel / battery / power;
- ammunition;
- medicine / medical supplies;
- tools / spare parts;
- data/storage/bandwidth when fictionally relevant;
- vehicles / seats / beds / rooms;
- documents / permits / credentials;
- labor hours / staff availability;
- political capital / favors only when operationally defined, not as fake precise points.

Track:

- current quantity or qualitative availability;
- owner/custodian;
- location;
- accessibility;
- reservation/commitment;
- consumption rate where relevant;
- replenishment source and delay;
- expiration/degradation;
- competing claims.

## 5. Logistics and capacity

Many failures are throughput failures, not inventory failures.

Track when important:

- transport capacity;
- route capacity;
- loading/unloading time;
- communication latency;
- manufacturing/repair time;
- staff shifts;
- queue/backlog;
- bureaucratic processing time;
- storage limits;
- bottlenecks;
- last-mile constraints.

Example:

> Having 10,000 meals in a depot does not feed a cut-off village if the road carries only one truck per day.

## 6. Conservation discipline

When a resource is quantitative enough to matter, use explicit events:

- produced/acquired;
- transferred;
- consumed;
- lost/destroyed;
- reserved/released;
- replenished;
- capacity increased/decreased.

A tracked resource should not increase without a source event unless the model explicitly represents background regeneration/income.

Use `narrative-invariants.md` for nonnegative/conservation rules.

## 7. Evidence and precision

Real physiology, medicine, vehicles, weapons, infrastructure, historical prices, supply chains, and institutional capacity require Reality Grounding when consequential.

Separate:

- evidence-supported range;
- project simplification;
- fictional deviation.

Do not turn an uncertain real system into a crisp game stat merely because structured state feels tidy.

## 8. Scene integration

Before a demanding scene, ask:

- what bodily state enters the scene?;
- what resources are physically present?;
- what has already been spent/reserved?;
- what capacity bottleneck matters?;
- what does the POV character actually notice about their own condition?;
- what changes by exit?

After the scene, commit only durable deltas.

## 9. Institutions and populations

At larger scale, use aggregate resource/capacity state rather than pretending to track every individual unit.

Examples:

- hospital beds: `strained / saturated / recovering`;
- fuel reserve: numeric if known, otherwise bounded range;
- police staffing: shifts and response capacity;
- food distribution: inventory + throughput + route access.

`world-model.md` owns macroeconomic/institutional design. This reference owns continuity of the finite operational resources once they matter to current causality.

## 10. Runtime integration

Recommended projection families:

- `bodies.<character_id>.*`;
- `resources.<resource_id>.*`;
- `capacities.<system_id>.*`.

Recommended semantic events:

- `Rested`;
- `Injured`;
- `Treated`;
- `ConditionWorsened`;
- `ResourceAcquired`;
- `ResourceTransferred`;
- `ResourceConsumed`;
- `ResourceLost`;
- `CapacityChanged`;
- `ReservationCreated` / `ReservationReleased`.

Use event names that fit the project domain; these are examples, not a mandatory ontology.

## 11. Failure modes

### RPG stat creep

Tracking ten numeric meters for every character usually creates fake precision and context waste.

### Scene reset

Fatigue, pain, ammunition, money, and damaged gear do not reset at chapter boundaries.

### Infinite warehouse

An organization repeatedly spends resources without procurement, production, or depletion.

### Inventory-only logistics

Supplies exist but cannot physically reach the people who need them.

### Medical certainty without evidence

If exact recovery or drug effects matter, research them. Otherwise keep a defensible range and uncertainty.
