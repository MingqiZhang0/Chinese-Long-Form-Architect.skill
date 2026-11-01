# Failure Corpus

This directory is the durable memory of failures discovered while evolving the Skill. It is deliberately different from `references/regression-tests.md`:

- the regression catalog names broad failure **families** in fiction and workflow behavior;
- this corpus records concrete **incidents/reproducers** that actually broke or threatened the Skill;
- automated entries map one incident to a focused fault-injection operator and a named oracle;
- documented entries remain valuable even when no honest deterministic oracle exists yet.

Do not delete a case because the underlying bug was fixed. A fixed bug is exactly what makes the case valuable as regression memory.

Do not inflate the mutation score by counting documented/manual cases, equivalent mutants, invalid baselines, or trivially malformed inputs that bypass the intended semantic layer.

For durable replay, preserve the minimized structured reproducer or deterministic operator. A random seed alone is insufficient because generator/code revisions can change what the seed produces.

Use `scripts/mutation_test.py validate`, `catalog`, `run`, or `reproduce` through `scripts/storyctl.py mutation ...`.

FC-044 through FC-047 record the real prewriting incident family and further maintenance audit findings. Their executable reproducers live in the registered production-readiness integration cases; they are excluded from the existing mutation-score denominator until an independent registered seed/operator/oracle is supplied. No duplicate evidence subsystem or full novel project is bundled.
