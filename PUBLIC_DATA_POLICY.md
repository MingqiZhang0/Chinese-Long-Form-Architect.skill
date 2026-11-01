# Public data selection policy

**Allowlist model:** the public repository contains only Skill source, scripts, canonical references, schemas, original synthetic regression fixtures, and a limited workbench source spike. This archive is *not* a complete dump of the development history.

Explicitly excluded from the public tree (and from all Git commits) are raw real-model request/response data, real-user source manuscript and protected plot decisions, locally generated model-evaluation packets, per-machine reports, screenshots, test run logs, full historical development docs, and binary build outputs.

Sensitive originals are retained in the separate private development archive. Missing private test evidence must not be fabricated or silently replaced. The public Fast lane and `scripts/test_public_release.py` are a smoke/release hygiene subset, not a substitution for the original uncompleted Core/Full/Soak gates.

For proposed additions, verify rights, remove personal or account details, ensure fictional examples are synthetic, scan for tokens and absolute paths, and review every newly included directory manually. A passing regex scan is not proof of safe publication. Public Git history is persistent even after files are deleted.

Privacy hardening: the public source also withholds original integration selftests and the real-project-hardening case family because anonymization alone cannot establish authorization to publish proprietary story-derived tests. Avoid adding these back without a provenance and rights review.

Third-audit allowlist exception: `docs/workbench/contracts/workbench-wire.schema.json`, `golden-wire.json`, and `spike-golden-wire.json` are preserved as synthetic protocol definitions/vectors needed to reproduce the Workbench technical spike. Historical machine-local maintenance reports remain withheld.

The public release smoke check includes a positive allowlist of approved synthetic regression roots; adding a new project directory requires review and an explicit allowlist update. An absence of private-looking words in a directory name is not sufficient authorization.
