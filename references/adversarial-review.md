# Adversarial Review and Pressure Testing

Use this reference after the first serious world-model pass and before locking major turns, climaxes, reveals, strategic victories, mystery solutions, political outcomes, or rule changes with many dependencies.

## Contents

- Core principle
- Review roles
- Attack workflow
- Actor and strategy tests
- System and scale tests
- Information and fairness tests
- Rule and branch tests
- Robustness perturbations
- Severity and patching
- Preserve texture
- Red-team report

## Core principle

Temporarily stop helping the intended story happen.

Attack the design from the standpoint of actors, institutions, logistics, readers, world rules, and consequences. The story should survive because constraints, uncertainty, cost, timing, and character make alternatives insufficient - not because the author quietly removes them.

Adversarial review tests credibility, not mathematical optimality. A character may be proud, frightened, misinformed, habitual, culturally constrained, bureaucratic, or simply wrong.

## 1. Review roles

Adopt only the roles relevant to the sequence.

### Intelligent opponent

Ask how the antagonist can escape, delay, mislead, negotiate, audit, change targets, split information, exploit law, attack assumptions, or choose a cheaper objective.

### Minor character

Ask what this person would do if they did not know they were supporting cast.

### Ordinary resident

Ask how major events alter work, prices, transport, family, rumor, fear, opportunity, and routine.

### Institution

Ask what procedure, jurisdiction, precedent, records, inertia, faction, liability, and reporting distortion do to the intended outcome.

### Skeptical first-time reader

Ask what feels planted, convenient, withheld, over-signaled, or under-supported.

### Reread reader

Ask which earlier scenes gain new meaning and which become retroactively false.

### Serial reader with imperfect memory

Assume partial forgetting. Ask whether orientation and clue reactivation are sufficient.

### Logistics auditor

Check time, travel, recovery, money, supply, communication, custody, staffing, physical geometry, and administrative delay.

## 2. Attack workflow

For a major sequence:

1. state the intended outcome;
2. list the minimum conditions required for it;
3. identify who could notice, refuse, delay, expose, exploit, or misunderstand each condition;
4. search for cheaper, safer, earlier, or institutionally easier alternatives;
5. remove protagonist privilege and test what continues;
6. perturb one assumption at a time;
7. inspect downstream consequences and update speeds;
8. classify failures by severity;
9. patch the highest causal layer rather than hiding the problem in prose;
10. rerun the relevant tests.

## 3. Actor and strategy tests

### Rational-actor test

For an important rule, resource, loophole, or technology ask:

- How would a poor but clever person exploit it?
- How would a wealthy actor scale it?
- How would organized crime monetize it?
- How would soldiers weaponize it?
- How would employers, schools, lenders, insurers, hospitals, or families adapt?
- How would an old expert use it differently from a gifted novice?

If obvious use would reshape society, reflect that reshaping.

### Incumbent test

When the protagonist discovers a powerful technique, business model, strategy, or loophole, ask why earlier actors did not already exploit it.

Credible answers include:

- missing complementary technology;
- inaccessible information;
- new political conditions;
- prohibitive prior cost;
- coordination failure;
- enforceable taboo;
- newly created resource;
- rare skill combination;
- failed predecessors whose failure matters.

"Everyone else was stupid" is not enough.

### Countermeasure test

For every strong capability ask what a competent opponent does after seeing it once.

If no meaningful countermeasure exists, explain how that fact reshapes doctrine, institutions, and power distribution.

### Character-intelligence test

At every major reversal record privately:

- what the losing side knew;
- what they reasonably believed;
- what options they considered;
- why the chosen option made sense then;
- what information or constraint enabled the winning move.

If the reversal works only because the loser ignores an obvious action, redesign it.

### Villain-escape / plot-adversarial test

Temporarily advocate for the opposition.

Ask:

- What is the earliest point they could notice something?
- What verification can they perform?
- Can they flee, delay, expose, bribe, arrest, litigate, audit, negotiate, kill, escalate, or refuse the intended game?
- What institutional ally would they call?
- What happens if they act one step earlier than the protagonist expects?
- Is there an obviously cheaper route to the real objective?

If a better move exists, use it or establish why it is unseen, unavailable, too costly, illegitimate, culturally unacceptable, or inconsistent with the actor's actual objective.

### Adaptive-opposition test

After the protagonist blocks, predicts, exposes, or repeatedly intercepts an opponent, ask:

- What anomaly does the opponent observe?
- What competing explanations arise first?
- What evidence could distinguish them?
- What behavior changes before the full truth is known?
- What old plan becomes too risky?
- What fallback, deception, compartmentalization, delay, or probe becomes rational?
- What does the opponent remember next time?

A competent opponent may be wrong, but should not repeatedly return to a disproven model.

## 4. System and scale tests

### Scale test

Check whether a mechanism that works for one person still works for:

- household;
- neighborhood;
- city;
- army;
- nation.

Costs, communication, coordination, enforcement, and logistics should change with scale.

### Legal and bureaucratic test

Trace the boring consequences of dramatic events:

- reports;
- records;
- jurisdiction;
- cleanup;
- investigation;
- insurance;
- permits;
- chain of command;
- family notification;
- replacement of damaged resources;
- administrative blame.

Not all deserve page time. They still exist.

### Power-politics test

Ask who can:

- appoint;
- fire;
- delay;
- veto;
- audit;
- define procedure;
- deny access;
- control budget;
- command force;
- certify identity or truth;
- grant immunity;
- mobilize legitimacy;
- impose hidden costs.

Distinguish prestigious titles from actual mechanisms.

### Timeline and logistics test

Check:

- travel time;
- communication delay;
- healing and training duration;
- administrative response;
- investigation speed;
- sleep and fatigue;
- weather and season;
- work schedules;
- simultaneous events;
- supply and staffing.

Do not compress time beyond world rules merely to reach a desired scene.

### Daily-life / public-consequence test

After major events ask what changes for ordinary routines and what surprisingly does not.

Possible effects include:

- transport;
- prices;
- curfews;
- staffing;
- queues;
- school attendance;
- rent;
- supply;
- neighborhood behavior;
- workplace policy;
- rumor and reputation.

Do not insert slice-of-life scenes by quota. Preserve downstream social state whether or not it reaches the page.

### Consequence-persistence test

Ask what survives into later chapters:

- injuries;
- evidence;
- debt;
- grief;
- infrastructure damage;
- reputation;
- legal exposure;
- scarcity;
- political opportunity;
- changed security procedures;
- copycat behavior;
- fear or trust.

Consequences should decay according to causes and inertia, not disappear because the chapter ended.

Use `state-inertia.md` for update rates and residue.

## 5. Information and fairness tests

### Information test

For every secret or surprise ask:

- Who knows?
- Who has evidence?
- Who benefits from leaking or suppressing it?
- How fast can it spread?
- How can it be authenticated?
- What false explanation competes with the truth?
- What would a suspicious but rational observer infer?

Do not preserve a secret by decree.

### Camera-cheat test

Enforce established focalization. If suspense or explanation collapses because the narrator depended on inaccessible knowledge or artificial thought-withholding, redesign.

Use `focalization-narrator.md` for camera permission.

### Foreshadowing and reread-fairness audit

For each major reveal ask:

- Which prior facts support it?
- Are there multiple independent supports for a major conclusion?
- Were clues natural under the first-read interpretation?
- Does the reveal deepen earlier scenes rather than make the narrator retroactively dishonest?
- If the twist vanished, would the supporting world detail still make sense?

Use `knowledge-topology.md`, `reader-model.md`, and `hidden-causal-networks.md` for detailed reveal design.

### Premature-solution test

Can an attentive reader solve the mystery far earlier than intended from one over-specific clue?

If yes, rebalance interpretation and competing hypotheses rather than simply hiding evidence.

### Information-friction test

Assume reports are delayed, distorted, doubted, suppressed, compartmentalized, or politically inconvenient. Does organizational behavior still make sense?

Use `organizational-learning.md` and `social-transmission-reputation.md` where appropriate.

### Information-power side-channel test

For prophecy, prediction, mind reading, surveillance, divination, remote viewing, or similar advantages ask:

- What does querying cost?
- Can observation leave a trace?
- Can the target notice a trace without knowing its source or content?
- Does precision, range, complexity, repetition, or temporal proximity change cost or detectability?
- Can false inputs poison the result?
- Can targets adapt once they suspect the capability?
- Does self-reference create a special failure mode?
- What institutions, professions, or taboos would arise around the capability?

If the power removes uncertainty without creating new strategic consequences, redesign the rule.

### Camouflaged-probing test

When an antagonist is secretly testing a capability, ask:

- Would the visible action remain rational if the hidden experiment were removed?
- Does it have first-order tactical, political, economic, or security value?
- Is the tested variable hidden inside normal operational variation?
- Would a first-time reader reasonably interpret it as ordinary strategy?
- Can a later reveal reconstruct the diagnostic purpose from details already present?

Do not make the opponent conduct a conspicuous laboratory test merely so the reader can see that testing exists.

## 6. Rule and branch tests

### Progression-consistency test

For every new level or ability ask:

- Was its possibility implied by old principles?
- Does it preserve costs or explain why costs change?
- Does it obsolete earlier tools or institutions?
- Can lower-level actors still matter through specialization, numbers, information, terrain, equipment, or organization?
- Why is access possible now?
- What new vulnerabilities appear?

### Change-propagation test

After modifying a rule or hidden truth ask:

- Which old scenes relied on the prior assumption?
- Which clues change meaning?
- Which choices become irrational?
- Which institutions should behave differently?
- Which payoffs break?
- Which ordinary-life facts change?

If impact cannot be migrated coherently, reject the change or use explicit change control.

### Counterfactual-branch test

For loops, resets, prophecy-driven interventions, repeated scenarios, or alternate branches ask:

- What variable actually changed?
- What important facts stayed invariant?
- Which outcome changed because of intervention rather than coincidence?
- Which hidden actor noticed and adapted?
- What hypothesis became more plausible?
- What hypothesis was falsified?
- Did the branch expose causal structure or merely replay spectacle?
- If disaster disappeared, what underlying objective, actor, capability, or pressure remains?

Each substantial branch should buy causal knowledge at a real cost.

### Narrative-operability test

Before drafting a rule-heavy or politically dense setup, ask whether the rules create playable decisions rather than only lore.

A strong rule should change at least one of:

- what actors can attempt;
- what they can verify;
- what they risk;
- what institutions control;
- what evidence means;
- what alternatives remain.

If a rule only adds explanation and no decision consequences, simplify it.

## 7. Robustness perturbations

### Remove-the-protagonist test

Remove the protagonist for a meaningful interval.

Ask which conflicts continue, relationships change, institutions act, people leave or age, threats worsen, and problems solve themselves.

If everyone waits, world autonomy is too low.

### Coincidence-removal test

Remove the lucky accident. Does the climax still resolve through character and system response?

Chance may trigger or complicate; it should rarely be the only solution.

### Noncooperation test

Assume a key ally refuses for ordinary self-interested reasons. Does the plan have fallback structure?

### Alternative-objective test

Could a major actor achieve the real objective through a less spectacular route? If yes, the spectacular plan needs independent utility, constraint, ideology, misbelief, or hidden purpose.

### Perturb-one-assumption test

Change one supporting assumption at a time - a report arrives late, a witness refuses, a vehicle breaks, a vote changes, a side character leaves, a rumor spreads incorrectly.

If the entire design collapses under a small ordinary perturbation, the sequence may be over-scripted.

## 8. Severity and patching

Classify findings:

- **fatal** - breaks canon, causality, central fairness, or world rules;
- **major** - requires implausible stupidity, luck, information leakage, or institutional absence;
- **moderate** - weakens motivation, timing, reader comprehension, consequence, or pressure;
- **minor** - local friction, wording, or presentation issue.

Patch in this order:

1. objective and rule;
2. knowledge and incentive;
3. institutional/logistical constraint;
4. sequence and scene choice;
5. exposition;
6. prose.

Do not sentence-polish a fatal causal problem.

## 9. Preserve texture

Red teaming can over-optimize fiction into sterile rationalism.

Do not remove:

- ordinary mistakes consistent with character;
- bounded chance;
- emotion-driven choices;
- cultural taboo;
- pride;
- incomplete information;
- bureaucracy;
- irrational but stable habits;
- quiet scenes;
- unresolved life.

The question is not whether every actor makes the mathematically best move. The question is whether the move is credible from that actor's world model and constraints.

## 10. Red-team report

For major architecture work, a compact internal report may contain:

- sequence under review;
- strongest exploit found;
- strongest camera/fairness risk;
- strongest logistics/institutional risk;
- reader-comprehension risk;
- downstream consequence missing;
- severity;
- minimal structural patch;
- regression tests to rerun.

Keep the report backstage unless the user asks for diagnosis.

## Wrong-poetics attacks

Add a distinct adversarial family: **helpful overcorrection**. Ask whether the reviewer is trying to repair the work by importing another poetics' virtues.

Attack candidates include:

- adding conflict/hook/payoff to a scene whose authorized function is ordinary inhabitation, waiting, or perception;
- adding explicit introspection because a character is psychologically opaque;
- standardizing sentence length or chapter voice despite an authorized formal override;
- expanding offscreen world autonomy in a deliberately obsession-centered or highly focalized work;
- pruning recurrence because it does not add new information even though recurrence is licensed as ritual, familiarity, evidence, or temporal form;
- forcing competing thematic positions where theme is realized perceptually, symbolically, ritually, or through one consciousness;
- adding explanation because the reviewer mistakes low explanatory density for incoherence.

Classify findings as hard-integrity failure, Project-Poetics violation, unauthorized drift, or merely the absence of another poetics' virtue before proposing a fix.
