# Public-preview release notes and known limitations

**Status:** release candidate for owner review; *no GitHub publication is implied*.

Source: the October 15 development archive, with a later October 15 production archive used only to cherry-pick verified CLI documentation corrections. Frozen reference inventory and semantic policies are unchanged.

## Confirmed repairs

- Fixed wrong project path examples in default and manifest-scoped `storyctl route resume-project`, `continue-chapter`, and `diagnose-project` (the command requires the manifest file and `--root`, not only a project directory).
- Fixed matching direct CLI examples in `references/tool-surface.md`.
- Excluded developer-local test-result generator with hardcoded machine path.

## Tests and acceptance

The November 1 pre-cleanup source audit recorded a passing Skill structure validator, 12/12 Fast tests, and only 9/61 completed/passing Core steps (the tenth was a 180-second timeout; remaining tests were not run). Six of seven independent sampled Core cases passed and one chapter-rollover case timed out at 180 seconds. The timeout behavior is compatible with repeated subprocess startup cost; it is not proof of a semantic failing assertion. These are **historical observations**, not claims of passing the newly curated public tree.

The original 61-step Core contract refers to a real-user E2E corpus excluded from public source. Running it directly from this public checkout is unsupported without supplying authorized private fixtures. Public CI only runs the public structural and quick-recovery checks, not Core/Full/Soak or real-model longitudinal author evaluation.

## Unsupported claims

No guaranteed 50/100/200/300-chapter quality, autonomous research correctness, secure multi-user hostile isolation, Workbench production readiness, complete macOS/Linux GUI support, or clean-VM packaging certification.

## Pre-publication legal check

The owner should verify rights to code, documentation and all included fixtures, and confirm the license and copyright line before any public push. This does not certify third-party compliance.

In the privacy-curated public tree, the mutation registry contains only retained synthetic cases; public Fast now passes 12/12 executable command steps. Because the historical private-origin cases and integration suite were withheld, this is not evidence that the original private full-test configuration passes. The original test-tier contract is retained for traceability; its Core/Full/Soak execution is unsupported without the private inputs.

## Privacy-hardening after candidate audit

The first public preview candidate was withdrawn prior to GitHub upload because private-project labels and real-project-derived regression fixtures remained. The revised public source removes those labels, the private-derived case family, and the historical integration suite (which embedded protected story context). The public smoke/Fast checks remain runnable; original Core/Full/Soak results are **not** implied by those checks.

## Independent pre-publication review (2026-11-01)

A separate re-audit detected and removed an unneeded historical maintenance-validation result containing a Windows-local interpreter path. The public Workbench technical-spike source previously lacked its three required synthetic protocol fixtures because the full `docs/workbench/` tree had been withheld. Only the validated JSON Schema and two golden-vector files were restored; all other private Workbench archives remain excluded. `scripts/test_public_release.py` now validates the schema/goldens and checks that the generated protocol bindings are in sync. This does **not** establish that the GUI, .NET build, native file watcher, or packaging procedures pass.

The installable production Skill deliberately excludes Workbench and developer-only test files; source and installation bundles are not byte-identical by design. Preserve the production CLI surface, not the developer maintenance commands, when building `skill.zip`.
