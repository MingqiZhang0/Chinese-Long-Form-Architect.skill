# Chinese prose, state and revision seeds

This fixture extends existing reconciliation, semantic revision and Chinese behavioral evaluation. It is not a novel project, a second state ledger, or an automatic Chinese semantic parser.

`cases.jsonl` contains 16 original raw-prose tasks and provisional author-created oracles. Use `storyctl chinese-eval build-state-blind` to separate generation inputs from gold; never expose this combined corpus or the key to the evaluated model. Exact target paraphrases require recorded independent alignment. `score-state` reports grounded claim, state-finding and revision-impact precision/recall/F1 separately. Seed/oracle roundtrips test the harness only.

`letter-revision/` is an executable Chapter 8 → 23/24 example. The old text explicitly reads the letter; the new text only hears of its existence. Existing graph retrieval identifies the content/action dependencies, retains Chapter 17's independent handwriting support, and the complete prose scan discovers Chapter 24's unindexed missing-character dependency. `packet.json` binds the graph, chapter inventory, branch and both source revisions. `impact.json` records reviewed findings with exact evidence and repair alternatives. Its approval label exists to test approval validation; no real project commit or repair is authorized by this fixture.

Registered integration tests cover semantic coverage/state inventory omissions, stale provenance, cross-layer and cross-branch laundering, false-belief representation, independent supports, unindexed chapters, missing repairs, and blind-evaluation negative controls. They do not prove a model understands arbitrary Chinese novels.
