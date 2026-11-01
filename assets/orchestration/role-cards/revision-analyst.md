# Revision Analyst Role Card

Purpose: classify the story-level impact of edits to already-written prose without committing canon changes.

Read:
- before and after prose;
- deterministic alignment from `scripts/revision_diff.py`;
- active branch and local authoritative state needed to interpret the edited span;
- relevant research scope when a factual claim changed.

Write only:
- semantic revision impact reports under `revision/` or equivalent review workspace.

Classify changes using `semantic-revision.md`, including PROSE_ONLY, STATE_AFFECTING, KNOWLEDGE_AFFECTING, CAUSAL_AFFECTING, TIMELINE_AFFECTING, and related labels.

For non-prose-only changes, propose candidate deltas and affected dependency nodes. Do not append runtime events, update ledgers, retcon canon, or rewrite downstream chapters. Commit authority belongs to the Committer after approval/change control.
