# Narrative Invariants and Constraint DSL

Use this reference when a project has hard story rules that should be checked mechanically across commits, replays, branches, or fuzz tests. It owns the **declarative invariant catalog and its execution boundary**. It does not own literary taste, dramatic quality, or open authorial questions.

## Contents

- What belongs in an invariant
- Hard vs soft constraints
- DSL design principles
- Supported rule families
- Scope and time
- Commit integration
- Branches and authorial unknowns
- Fuzz/property testing
- Tooling
- Failure modes

## 1. What belongs in an invariant

Project Poetics is not automatically an invariant DSL. Only a deliberately locked, mechanically decidable formal commitment should become an invariant; most literary judgments remain human/Agent diagnostics rather than pass/fail laws.

An invariant is a condition the story/runtime promises to preserve whenever its declared scope applies.

Good candidates:

- a unique artifact cannot have two simultaneous holders;
- a dead actor cannot perform ordinary voluntary actions unless a project-specific exception is active;
- resource totals cannot become negative;
- a fact cannot be used by an actor before a knowledge-acquisition event;
- a route-dependent move must fit available time;
- each use of a defined power requires a declared cost event;
- a sealed door cannot be crossed while its access state is closed unless another rule/event changes that state.

Bad candidates:

- every chapter must be exciting;
- the protagonist should be likable;
- prose should feel literary;
- every scene needs a twist;
- a theme should be deep.

Those are judgments, not machine invariants.

## 2. Hard vs soft constraints

Use severities deliberately:

- `error` - commit must stop;
- `warning` - commit may proceed only after explicit review/override;
- `advisory` - health signal only.

Do not turn every preference into an `error` merely because the DSL can express it.

## 3. DSL design principles

The bundled DSL is intentionally small and non-Turing-complete.

Principles:

- declarative rather than procedural;
- explicit rule IDs;
- structured JSON inputs;
- no arbitrary code execution;
- deterministic evaluation;
- bounded operators;
- branch/time scope;
- readable failure messages;
- no automatic repair.

This follows the policy-as-code idea: separate **decision rules** from the code that enforces the decision, while keeping the fiction-specific language much smaller than a general policy language.

## 4. Supported rule families

The validator supports these core families.

### `always`

Assert a condition on current projection state after every committed event or at commit boundaries.

Example uses:

- a numeric resource remains nonnegative;
- a required canonical field is present;
- a project rule remains true.

### `event_guard`

When selected event types occur, assert pre-state and/or post-state conditions.

Example:

- `TeleportUsed` requires `abilities.teleport.enabled == true` before the event;
- `ProphecyInvoked` must leave a nonempty cost/residue field after the event.

Use `{entity}` in a path to apply a guard to event entity IDs.

### `requires_prior_event`

Selected events require a prior event of another type in the effective branch history, optionally sharing an entity.

Example:

- `FactUsed` requires prior `FactLearned` for the same actor/fact identity.

### `forbids_event_when`

Reject selected events when a pre-state condition holds.

Example:

- ordinary `ActorAction` is forbidden when `characters.{entity}.alive == false`.

### `monotonic`

A numeric/categorical quantity may only move in the declared direction unless an allowed reset/reversal event occurs.

Use sparingly. Many human states are not monotonic.

### `conservation`

Check tracked numeric resources against explicit production/consumption/transfer deltas.

Use only where quantities are meaningful and evidence supports the precision.

### `temporal_order`

Require one event/fact class to precede another within the effective branch history.

Do not use this to freeze flexible narrative order when only story chronology matters; distinguish story time from disclosure order.

## 5. Conditions

Keep condition operators bounded:

- `exists` / `not_exists`;
- `eq` / `neq`;
- `in` / `not_in`;
- `gt` / `gte` / `lt` / `lte`;
- `truthy` / `falsy`;
- `contains`;
- `nonempty` / `empty`.

Paths use dot notation into the replayed projection. `{entity}` may substitute the current event entity ID. Avoid a general expression language unless the project genuinely needs it.

## 6. Scope and time

An invariant may declare:

- branches;
- event-type filters;
- entity IDs;
- chapter range;
- story-time interval;
- activation/deactivation event IDs;
- severity.

This matters because story laws can legitimately change.

Example:

> Before the ritual in Chapter 80, resurrection is impossible. After it, resurrection is possible but costs memory.

Do not encode both eras as one timeless invariant.

## 7. Commit integration

In Runtime Mode, use this order:

1. read active branch at expected head;
2. replay/load current projection;
3. evaluate transaction preconditions;
4. simulate proposed events in memory;
5. run invariant catalog against the simulated result and event sequence;
6. if blocking rules pass, perform the atomic append;
7. refresh projections;
8. optionally rerun invariant checks as a postcondition.

A failed invariant produces diagnostics. It does not rewrite the events into compliance.

## 8. Branches and OpenIssues

Invariants are branch-specific when necessary.

A sandbox branch may deliberately disable or alter a project invariant to explore:

> What if magic no longer costs memory?

That experiment must be explicit in branch metadata. Do not silently weaken `main` constraints.

Do not encode an unresolved OpenIssue answer or working hypothesis as an invariant. A deterministic invariant may encode an **already authoritative** compatibility constraint or a mechanically decidable preserve-open guard, but it must not choose among viable positions. Candidate lists are non-exhaustive unless explicitly declared exhaustive.

## 9. Fuzz/property testing

Invariants become much more useful when tested against **sequences**, not isolated examples.

Use stateful fuzzing to generate combinations such as:

- transfer -> branch -> transfer -> replay;
- injury -> travel -> treatment -> revision;
- reveal -> false rumor -> correction;
- resource consume -> replenish -> branch merge plan;
- schema migrate -> replay -> snapshot -> replay.

Run invariant checks after every generated step. The goal is to find a **minimal failing sequence**, not to create random fiction.

`state-validation.md` owns the full fuzz-testing workflow.

## 10. Tooling

Use:

- `assets/runtime-templates/invariants-template.json` - neutral empty registry for new/generic projects;
- `assets/runtime-templates/invariants-examples.json` - opt-in examples only, never implicit project law;
- `assets/runtime-schemas/invariants.schema.json`;
- `scripts/validate_invariants.py`.

Keep the default registry empty. A generic Runtime must not acquire cash, mortality, magic, resource, or other story-specific laws merely because an example exists in the Skill. Adopt each example only after the project's actual projection paths and semantics make that invariant true.

The script validates the catalog and evaluates supported deterministic rules against an event stream/projection. Unsupported literary reasoning must remain with an Agent/Auditor.

## 11. Failure modes

### Constraint inflation

Hundreds of rules turn the story into brittle software. Automate only truths where false positives are less costly than silent contradiction.

### Hidden creative law

A rule such as `hero_must_win` is author coercion disguised as validation.

### False precision

Do not require exact calorie, fatigue, trust, or stress numbers unless the project has evidence and a real reason to model them numerically.

### Auto-repair

The validator should say what broke, not invent the fix.

### Timeless rules for changing worlds

Rules can have eras. Scope them explicitly.
