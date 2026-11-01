# Multi-Poetics Behavioural Oracle assets

This directory is an executable maintenance contract, not a literary-theory module.

Each registered preservation fixture contains:

- `input.md` - the exact rights-clean passage supplied to the target Skill;
- `task.md` - the exact light-revision task;
- `project-poetics.md` - the fixture-specific literary contract;
- `oracle.json` - must-preserve, allowed-intervention, forbidden-intervention, deterministic, and judge contracts;
- `control-preserving.md` - one non-unique positive control used only to calibrate the oracle;
- `wrong-poetics-mutant.md` - a deliberately plausible but poetics-violating repair.

The positive control is **not** a gold style target. A candidate may differ completely and still pass. Deterministic checks are deliberately conservative and cannot establish literary adequacy by themselves. Promotion-grade evidence combines deterministic checks with blinded checklist judging and swapped-order pairwise comparison.

Use `storyctl multi-poetics-oracle --help`.

Long-form qualification uses `qualification_fixtures` in the manifest and `qualification.json` in each selected fixture. The three keys are task stages (planning, chapter, drafting), not narrative types. Pass `--stage` before the subcommand, for example `storyctl multi-poetics-oracle --stage planning build-generation --out /path/to/generation.jsonl`. Each stage has separate input/task/control/mutant paths and uses the existing calibrated blind protocol. The planning input is a brief; chapter/drafting inputs contain mature first-volume contributions. Candidate outputs and judge responses must be imported from an actual campaign. Packaged controls and synthetic selftest responses cannot supply promotion evidence.

Regime compiler metamorphic selftests preserve physical fact bytes while changing a witness, narrating age or object relation. Their result concerns handoff propagation. Whether generated social consequences or interpretations change appropriately remains a model-evaluation obligation.
