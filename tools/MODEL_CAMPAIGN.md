# Real model qualification maintenance interface

This tool stays outside the packaged `scripts/` discovery surface. It does not
change the Skill, canonical fixtures, runtime, Workbench or Auditability Core.
Use Python UTF-8 mode and disable bytecode writes on Windows:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$campaign = 'docs/model-campaign-results/multi-regime-real-model-qualification-20261005-R3'
python -B tools/model_campaign.py verify --campaign $campaign
python -B tools/model_campaign.py dry-run --campaign $campaign
```

The current real execution is **blocked by automatic approval review**, not by
missing authentication. The authenticated CLI answered a single `READY` probe;
that probe is not a qualification result. Do not run external calls until the
user approves sending the frozen synthetic benchmark and Skill to Codex.

After authorization, exact execution commands are:

```powershell
python -B tools/model_campaign.py generate --campaign $campaign
python -B tools/model_campaign.py calibrate --campaign $campaign
python -B tools/model_campaign.py build-judges --campaign $campaign
python -B tools/model_campaign.py pointwise --campaign $campaign
python -B tools/model_campaign.py pairwise --campaign $campaign
python -B tools/model_campaign.py aggregate --campaign $campaign
python -B tools/model_campaign.py rerun --campaign $campaign
python -B tools/model_campaign.py build-judges --campaign $campaign --run-id run_2
python -B tools/model_campaign.py pointwise --campaign $campaign --run-id run_2
python -B tools/model_campaign.py pairwise --campaign $campaign --run-id run_2
python -B tools/model_campaign.py aggregate --campaign $campaign --run-id run_2
python -B tools/model_campaign.py hashes --campaign $campaign
```

Each `generate` call resumes successful immutable records without resampling
them. Technical attempts have an upper bound of three. An exhausted transport
failure stops the loop; semantic quality never triggers a technical retry.
CLI output limits are not exposed, so no output budget is invented. The CLI's
tools, web search and MCP are disabled; any observed tool event invalidates that
request. Its standard system scaffold remains a limitation of this adapter.
All target requests have independent ephemeral contexts and isolated temporary
working directories. CLI model revision is recorded as unknown. Configured
judge availability and calibration remain unverified until actual calls occur.

The frozen `requests/*.jsonl` files are the exact provider-independent target
requests. Model input contains only `messages`, not request IDs, fixture IDs,
oracle hashes or local-defect transport fields. The shared craft context uses
three base references and a small stage-appropriate stack; all references are
frozen. Responses must retain the output text unchanged. Never use oracle
controls as live target outputs.

External/file provider interface:

```powershell
python -B tools/model_campaign.py import-targets --campaign $campaign --input external-targets.jsonl
python -B tools/model_campaign.py build-judges --campaign $campaign
python -B tools/model_campaign.py import-judges --campaign $campaign --input external-calibration.jsonl
python -B tools/model_campaign.py import-judges --campaign $campaign --input external-pointwise.jsonl
python -B tools/model_campaign.py import-judges --campaign $campaign --input external-pairwise.jsonl
python -B tools/model_campaign.py replay --campaign $campaign
```

Target response envelope requires `task_id`, `request_hash`, `model`,
`reasoning_effort`, `started_at`, `status`, `output`, `fresh_context: true`, and
`tool_calls: false`. Hash is SHA-256 of the canonical JSON request (UTF-8,
ensure_ascii=False, sorted keys, separators `(',', ':')`). Optional usage must
be actual exposed usage or null. Optional attempt defaults to 1. Configuration
must match the freeze. Source/provider metadata is externally attested, not
independently verified by the importer; inspect external evidence provenance
before promotion. Raw accepted response records are immutable.

Judge envelope requires `judge_id`, `stage`, `phase` (`calibration`, `pointwise`,
`pairwise`), `model`, `reasoning_effort`, `request_hash`, `fresh_context: true`,
`tool_calls: false`, and `responses`. Compute the request with
`model_campaign.judge_request(packet)` and hash with `model_campaign.digest`.
Calibration packets already exist under `judges/calibration/`. Formal pointwise
and pairwise packets are materialized only from successful actual target
outputs. Private keys must never be supplied to the judge. Response schema is
the existing oracle checklist, with uncertainty/tie preserved. Incorrect
calibration excludes the judge; at least two calibrated judges and the existing
0.67 threshold remain required. The existing target pair is target vs damaging
mutant, with both orientations. No hidden reasoning is requested or retained.

`aggregate`/`replay` perform no model calls. Their results are mechanical evidence
summaries; the promotion decision still requires reviewing the locked policy,
stability runs, individual failure evidence and all reverse controls. Unrun
incidence and agreement remain null. Do not infer zero contamination from an
empty campaign. The report must be updated with actual calibration, case,
runtime, stability and promotion evidence before calling a real run COMPLETE.

Offline regression tests use mocks and authored controls only in temporary
directories; they cannot supply promotion evidence:

```powershell
python -B tools/test_model_campaign.py
```

Manifest structure is versioned in `tools/model-campaign-manifest.schema.json`.
Any frozen file/config/task change invalidates a campaign. Use a new identity
after a repair; never merge old and new target outputs.
