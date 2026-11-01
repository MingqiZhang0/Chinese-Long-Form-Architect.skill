# Contributing

Please open an issue describing the defect and its reproducible case before broad architectural changes. This project has canonical reference owners and a frozen reference inventory; do not add new owners, alter author-controlled writing policies, weaken readiness, or rewrite Runtime history without an approved change process.

For a patch, update the smallest owning script/reference, add deterministic regression coverage, and run `python -B scripts/audit_skill_structure.py .`, `python -B scripts/test_public_release.py`, and the Fast tier. Describe any test that is not run, especially private-fixture dependent Core tests. Never add model interaction transcripts, unreleased fiction, user paths, credentials, private research notes, or copyrighted source text without distribution rights.

The Workbench is an experimental, read-only prototype; please do not file release regressions solely because it is not a complete cross-platform product.
