# External Research Ledger

Use this reference only while maintaining/evaluating the Skill, checking research provenance, or updating an external methodological claim. It owns the **Skill-wide external research registry**. It does not replace a fiction project's Reality Grounding source ledger.

## Contents

- Purpose and boundary
- Canonical artifact
- Required metadata
- Citation discipline
- Publication-status upgrades
- Verification and freshness
- Subsystem views
- Maintenance workflow

## 1. Purpose and boundary

External research that materially informs Skill architecture, benchmark design, evaluation claims, long-horizon memory policy, test methodology, or similar maintenance decisions must have one canonical record in `assets/external-research-ledger.json`.

Keep three ledgers distinct:

1. **Skill Research Ledger** - research used to design or evaluate this Skill; canonical here.
2. **Project Research Source Ledger** - historical/scientific/legal/material evidence used to ground one fiction project; owned by `reality-grounding-research.md` and its project template.
3. **Runtime research dependencies** - project facts that can become stale during an ongoing story; owned by Project State/Runtime freshness logic.

Do not copy project research into the Skill ledger merely because the Skill happened to use a project as a regression fixture.

## 2. Canonical artifact

Canonical machine data:

- `assets/external-research-ledger.json`
- `assets/external-research-ledger.schema.json`

Canonical deterministic backend: `scripts/research_ledger.py`; normal Agent use should go through `storyctl research-ledger`.

Validate/query it with:

```bash
python scripts/storyctl.py research-ledger validate
python scripts/storyctl.py research-ledger coverage
python scripts/storyctl.py research-ledger list
python scripts/storyctl.py research-ledger show SOURCE_ID
```

The JSON ledger is the bibliographic source of truth. Narrative references may retain a short human-readable description, but stable linkage must use `[research:SOURCE_ID]` rather than duplicating mutable publication metadata in multiple files.

## 3. Required metadata

Each source records:

- `id` - stable lowercase Skill identifier;
- `title`;
- `authors` - ordered author list;
- `venue` and `year`;
- `source_type`;
- `publication_status` - `peer-reviewed`, `preprint`, or `other`;
- `doi` when one exists;
- `arxiv` when relevant;
- `canonical_identifier` and HTTPS `canonical_url`;
- `verification_date` and `verification_basis`;
- `claims_used_for` - bounded statements/design decisions this source supports;
- `used_by` - packaged files that consume the source;
- `superseded_by` - another ledger ID when this record should no longer be the active citation;
- optional notes for non-obvious lineage.

`verification_date` means the bibliographic/status metadata was checked against the stated canonical source on that date. It does **not** mean every scientific claim in the paper was independently reproduced.

## 4. Citation discipline

When adding an external research claim to a maintenance/evaluation reference:

1. add or update the canonical ledger entry;
2. verify publication metadata against a primary/canonical venue when practical;
3. cite the claim in the reference with `[research:SOURCE_ID]`;
4. add that reference path to `used_by`;
5. describe only the narrow claim actually used;
6. distinguish source findings from Skill design decisions or extrapolations.

Do not treat an arXiv preprint and its later peer-reviewed publication as independent confirmations. Prefer updating one stable record to the peer-reviewed canonical venue while preserving the arXiv identifier when useful.

## 5. Publication-status upgrades

When a preprint later appears in a peer-reviewed venue:

- keep the same stable ledger ID when it is substantively the same work;
- change `publication_status` to `peer-reviewed`;
- update venue, DOI/canonical identifier, URL, and verification date;
- retain the arXiv ID as lineage metadata;
- use `superseded_by` only when a genuinely distinct later record should replace the current record.

Do not silently describe a preprint as peer-reviewed merely because a project page says it is submitted or accepted. Verify against the actual proceedings/journal when available.

## 6. Verification and freshness

Run `research-ledger validate` in Fast maintenance. The validator checks schema shape, unique IDs/identifiers, `used_by` paths, research markers, subsystem views, and supersession references.

Use `research-ledger coverage` to find:

- reference markers with no ledger entry;
- `used_by` declarations that no longer contain the corresponding marker;
- ledger entries that have no live consumer;
- stale subsystem views.

A verification date becoming old is a reason to review a source when its status or cited claim is freshness-sensitive; it is not an automatic invalidation of stable historical methodology.

## 7. Subsystem views

Subsystems may ship a compact view containing only canonical IDs. For example, Chinese Narrative Evaluation keeps `assets/chinese-narrative-eval/research-ledger.json` as a compatibility/view artifact listing the research IDs that justify that protocol. It must not duplicate titles, authors, venue, DOI, or publication status.

The canonical ledger owns bibliographic metadata; subsystem views own only membership/purpose.

## 8. Maintenance workflow

For research-informed Skill changes:

1. identify the exact external claim being used;
2. verify the source and add/update one canonical entry;
3. add `[research:ID]` to each consuming owner reference;
4. update `used_by` to match actual consumers;
5. run `storyctl research-ledger validate` and `coverage`;
6. run the appropriate Fast/Core test tier;
7. never cite a source merely to decorate an already-made design decision.
