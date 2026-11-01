# Benchmark and Evaluation Protocol

Use this reference only when maintaining, auditing, or substantially revising this skill. Do not run the benchmark for ordinary fiction requests.

## Contents

- Core principle
- Maintenance test tiers
- Evaluation layers
- Fixed benchmark and holdout
- Pairwise comparison first
- Do not trust one judge configuration
- Multi-Poetics Behavioural Oracle
- Separate compliance from vitality
- Failure log
- Version comparison protocol
- Anti-overfitting
- Active craft-stack audit
- Promotion questions
- Chinese narrative behavioral evaluation
- Cross-project structural diversity
- Long-horizon benchmark ladder
- Failure-corpus and mutation adequacy
- Metamorphic / adversarial relation adequacy
- Trigger activation precision


## Core principle

A writing skill can become more rule-compliant while producing worse fiction.

Evaluate changes against stable tasks. Separate mechanical regressions from reader preference, vitality, and long-form usefulness.

Use `evaluation-corpus.md` for the fixed task set. Treat every `B*`/`H*` case ID as a stable traceability identifier, not disposable display numbering: never reuse an existing ID for a different case. The Fast structural audit rejects duplicate case IDs before packaging.

## Maintenance test tiers

Use `test-tier-contract.md` for executable maintenance depth. Fast is routine smoke, Core is the normal promotion gate, Full is the internal deterministic release/major-architecture gate, and Soak is an explicit high-cost reliability campaign. Do not reconstruct those tiers by hand from the individual benchmark sections below.

A test-tier PASS and a quality-evaluation result are different evidence. The tier runner proves only the deterministic/synthetic contracts listed by that tier; pairwise literary evaluation, private holdout evidence, and live longitudinal campaigns remain separate.

## 1. Evaluation layers

Assess at three scales.

### Macro
- long-horizon direction;
- world autonomy;
- causal coherence;
- thread inheritance;
- ending strength;
- thematic depth without author sermon.

### Meso
- chapter/arc propulsion;
- scene selection;
- reader memory load;
- clue reactivation;
- relationship progression;
- institutional and offscreen consequence.

### Micro
- focalization;
- dialogue voice;
- spatial clarity;
- dynamic vividness;
- prose restraint;
- Chinese grammatical/reference naturalness and idiom/register fit when the benchmark language is Chinese;
- paragraph rhythm;
- descriptive resolution.

### Operational
- role isolation and clean handoffs;
- deterministic query/check coverage;
- context-pack relevance and spoiler safety;
- state mutation permissions;
- sidecar analysis remaining nonbinding until user approval;
- Narrative Semantics Kernel layer/type separation, provenance closure, information-flow preservation, and no-spontaneous-canon checks;
- event replay / projection consistency when Runtime Mode is active;
- runtime schema compatibility and replay-equivalent migration;
- optimistic-concurrency conflict detection and idempotent retry;
- project invariants blocking only mechanically decidable contradictions;
- semantic prose revisions requiring reviewed state deltas before commit;
- branch/sandbox isolation and semantic merge gating;
- discovery promotion and authorial-unknown preservation;
- embodied/resource continuity without fake precision;
- blind Reader Simulator isolation from backend truth;
- observatory outputs remaining read-only/advisory;
- seeded runtime fuzzing passing replay/snapshot/branch properties;
- no-subagent fallback preserving task/write discipline while labeling blindness and evaluator independence honestly;
- paragraph architecture preserving semantic boundaries, mode-specific grammar, long-form re-entry, deliberate modernist compensation, and separation of semantic paragraphs from optional display blocks.

A version may improve one scale while degrading another.

## 2. Fixed benchmark and holdout

Maintain:

- a **core set** used regularly during development;
- a **holdout set** used less often to detect overfitting to familiar prompts;
- a **failure log** containing real cases where the skill produced weak or broken fiction.

Do not rewrite benchmark prompts to flatter the newest module.

## 3. Pairwise comparison first

For subjective fiction quality, prefer blinded A/B comparison between versions over self-assigned absolute scores.

Keep constant where possible:

- prompt;
- requested length;
- language;
- source context;
- model/configuration;
- tool access;
- generation count.

Hide version labels and implementation notes from the judge.

Useful questions:

- Which version would you continue reading?
- Which world feels more autonomous?
- Which characters feel more independently alive?
- Which reveal feels fairer on reread?
- Which version is clearer without becoming flatter?
- Which version leaves stronger aftertaste?
- Which version sounds less like a writing system demonstrating its rules?

## 4. Do not trust one judge configuration

LLM judges can show position, verbosity, style, provenance, and self-preference biases.

When model judging matters:

- evaluate both A/B orders;
- treat order-disagreement as uncertainty or tie;
- hide model/version provenance;
- compare outputs of similar requested length;
- use explicit criteria rather than "which is better?" alone;
- inspect a human sample when a change is important;
- prefer multiple judges or one human + model-assisted analysis over one uncalibrated model verdict.

Do not convert a subjective judge into a fake precise score. Position bias is empirically non-random across LLM judges, candidates, and tasks, so swapped order is a required control rather than cosmetic randomization. [research:judge-position-bias-2025]

Direct pairwise comparison can also amplify superficial preferences such as verbosity or authoritative tone. Use independent criterion-level pointwise judgment before pairwise comparison when the evaluation is meant to test a specific behavioural contract rather than general preference. [research:comparative-trap-2025]

Decompose the relevant contract into traceable checks instead of asking for one opaque quality score; checklist-style judging has shown stronger reliability and interpretability across evaluator models. [research:checkeval-2025]

When evaluation results are stored as blinded pairwise JSONL, use `scripts/aggregate_pairwise_eval.py` to collapse swapped-order judgments into consistent wins, ties, incomplete cases, and order-disagreement uncertainty.

## 4.1 Multi-Poetics Behavioural Oracle

Static differences in architecture-fingerprint.json prove only that fixtures are described differently. They do **not** prove the Skill behaves differently when asked to revise prose. Use `scripts/multi_poetics_oracle.py` through `storyctl multi-poetics-oracle` for the ten incompatible-poetics fixtures.

Each fixture must package the exact input.md and task.md, its `project-poetics.md`, an oracle.json with **must-preserve**, **allowed intervention**, and **forbidden intervention** assertions, one non-unique control-preserving.md, and one deliberate wrong-poetics-mutant.md. The control is calibration evidence, not a gold style target.

Run a real target evaluation in this order:

1. storyctl multi-poetics-oracle build-generation --out generation.jsonl to freeze the ten exact target tasks.
2. Run the candidate Skill/model independently and save one passage as <candidate-dir>/<fixture-id>.md. Do not expose controls, mutants, or evaluator keys to the generator.
3. storyctl multi-poetics-oracle check --candidate-dir CANDIDATES --out deterministic.json --json. Mechanical failures are gating, but a mechanical PASS is never literary proof.
4. storyctl multi-poetics-oracle build-blind --candidate-dir CANDIDATES --out judge-packet.jsonl --key-out judge-key.jsonl --seed SEED --json. The visible packet contains the declared poetics/checklist but hides candidate provenance and role labels.
5. Collect independent judge responses. Each fixture receives one pointwise target judgment, a swapped calibration pair (`control` vs `wrong mutant`), and a swapped target-vs-mutant pair. Do not call the same generation context an independent judge.
6. storyctl multi-poetics-oracle aggregate RESPONSES judge-key.jsonl --deterministic-report deterministic.json --min-calibrated-judges 2 --consensus 0.67 --json. A judge that cannot consistently prefer the preserving control over the wrong-poetics mutant after order swapping is excluded for that fixture.
7. Treat order disagreement, ties, too few calibrated judges, or split checklist/pairwise evidence as **uncertain**, not as a forced pass/fail. Inspect cross-fixture repeated intervention tags as flattening signals; they trigger review, while explicit fixture-specific forbidden interventions remain the gating evidence.

The oracle is intentionally asymmetric. `allowed_interventions` are permissions, not requirements. Absence of an allowed technique is never a failure. `forbidden_interventions` describe project-specific coercions. This prevents the evaluator itself from turning one fixture's virtues into universal obligations.

storyctl multi-poetics-oracle selftest --json is a harness test only: it proves that all ten positive controls survive, all ten known wrong-poetics mutants are killed by conservative deterministic checks, blinding hides candidate roles, a synthetic always-left judge is rejected by swapped calibration, and repeated cross-fixture intervention tags are surfaced. It does **not** prove that an unrun target model or Skill preserves plurality. Promotion evidence requires actual candidate outputs plus independent judge responses.

## 5. Separate compliance from vitality

Track at least two classes of outcome.

### Correctness / integrity
- canon consistency;
- knowledge legality;
- causal sufficiency;
- spatial/logistical plausibility;
- no camera cheating;
- no obvious regression-test failure.

### Literary / reading value
- propulsion;
- surprise and reread density;
- character life;
- world surplus;
- emotional force;
- dialogue distinctness;
- scene vividness;
- restraint;
- desire to continue.

If compliance rises while vitality falls, treat the change as suspect.

## 6. Failure log

Record failures by mechanism, not vague labels.

Bad:
- "boring";
- "AI-like";
- "not literary enough".

Better:
- every scene receives equal ceremony;
- side characters wait for protagonist contact;
- opponent never updates after interference;
- explanation follows every strong image;
- long-form opening is strong but final arc compresses consequences;
- dialogue voices differ lexically but not socially;
- benchmark improvement came from making every answer longer.

A new durable failure mechanism may justify a regression test or module update.

## 7. Version comparison protocol

For substantial revisions:

1. freeze the baseline skill version;
2. identify the intended improvement;
3. run a representative subset of core benchmarks;
4. compare old/new blind;
5. log wins, losses, ties, and failure mechanisms;
6. run regression tests relevant to the changed modules;
7. run selected holdouts;
8. validate the durable failure corpus and run the registered semantic mutation suite; surviving non-equivalent mutants or invalid baselines block promotion;
9. run the registered metamorphic/adversarial suite; any failed or invalid automated relation blocks promotion;
10. revert or narrow the change if gains are local but regressions broad;
11. only then promote the new version.

Where feasible, change one major concept at a time or use ablation to identify which addition caused the effect.

## 8. Anti-overfitting

Warning signs:

- outputs begin sharing the same architecture because benchmarks reward it;
- recurring phrasing appears from benchmark examples;
- modules activate whenever a benchmark surface cue appears;
- holdout performance falls while core benchmark performance rises;
- complexity increases because the evaluator mistakes density for quality.

A benchmark measures the skill. It must not become the genre.

## 9. Active craft-stack audit

When a revised skill seems technically stronger but prose becomes stiff, inspect how many modules are active at once.

Persistent story state may be broad. Active craft reasoning should remain selective.

For most substantial chapter tasks, prefer a small stack of dominant modules rather than loading every available reference. Add a module only when it controls a material risk in the current scene or arc.

## 10. Promotion questions

Before accepting a major update, ask:

- Did the targeted failure improve?
- Did any previously strong behavior regress?
- Is the new instruction actually used when relevant?
- Does it activate too often?
- Did the skill become more verbose or mechanical?
- Did the change increase real structural depth or merely instruction count?
- Do world truth, actor epistemic state, reader exposure/model, visibility policy, provenance, and analysis remain distinct semantic strata after the change?
- Can the same canonical state be reconstructed from committed events after the change?
- Can supported legacy project artifacts migrate without rewriting committed history, resolving authorial unknowns, widening secret access, changing branch lineage, collapsing the three time axes, or changing replayed story state?
- Does a stale concurrent transaction fail rather than silently win, and does a retry remain idempotent?
- Do project invariants catch genuine mechanical contradictions without hard-coding subjective taste?
- Do branch/discovery/observatory tools remain subordinate to user and narrative judgment?
- When native subagents are unavailable, does the selected fallback profile match actual context/file/tool capabilities, and are blind/independent claims disabled when unsupported?
- Do paragraph rules adapt to discourse mode without collapsing into fixed length, sentence-count, or named-author imitation?
- Does mobile formatting remain a reversible display concern rather than rewriting semantic paragraph boundaries?
- Does deliberate boundary misalignment identify a compensating cohesion mechanism instead of invoking "experimental style" as a blank check?
- In Chinese prose, does bounded event non-occurrence use natural `没有/没 + verb` rather than clipped comma + `不 + verb` tails, while preserving `不` for genuine habit/refusal/future/general negation?
- Are corrective negative frames (`不是 X，而是 Y`, `没有 X，只是 Y`, etc.) used for real contrast rather than as a repeated default emphasis cadence?
- Does adaptive intake suppress every author-level field already resolved by the user instead of replaying a static questionnaire?
- Are clear scoped semantic delegation expressions normalized to DELEGATED without token policing, while ambiguous scope remains unresolved and `无` / clear negatives remain absence/exclusion rather than hidden permission?
- After kickoff, does the workflow maintain a zero nonessential interruption default and keep ordinary implementation choices with the Agent?
- Does every registered non-equivalent automated failure mutant still get detected or contained, with zero invalid baselines?
- Does a holdout case still surprise the system in a healthy way?
## 11. Chinese narrative behavioral evaluation

When a change materially affects Chinese prose generation or revision, use `chinese-narrative-behavioral-evaluation.md` in addition to the broad prompts in `evaluation-corpus.md`. The Chinese suite is an example-grounded behavioral specification, not a quotation bank and not a universal literary-quality judge.

Required discipline:

- treat the contrast **family**, not an isolated pair, as the unit of evaluation;
- preserve anchor + reversal/boundary coverage so the Skill cannot pass by memorizing a surface editing heuristic;
- separate local, distributional, and longitudinal claims;
- report recognition, diagnosis, repair, production, and preservation behavior separately when those modes are tested;
- keep packaged seed/dev material distinct from promotion-grade human gold;
- keep `private_holdout` material outside the Skill package;
- build generator-visible packets without gold/rationale and evaluate only after generation;
- if true fresh-context isolation is unavailable, label the run nonblind/soft-isolation and do not treat it as sole promotion evidence;
- report behavior profiles by phenomenon/role/scope/evidence class rather than one `Chinese literary quality` score.

Run `python scripts/storyctl.py chinese-eval validate` as a maintenance smoke test. Use `build-blind` before human/model A/B evaluation and preserve the separate evaluator key. The packaged seed suite is provisional executable specification; it must not be cited as native-speaker consensus.

## 12. Cross-project structural diversity

A Skill can regress by making every story more compliant **and more alike**. Treat this as a distinct failure mode.

When comparing versions across multiple genres, inspect architecture fingerprints such as:

- dominant conflict source;
- chapter propulsion mechanism;
- scene-exit pattern;
- secret/mystery density;
- institutional share of causality;
- POV switching pattern;
- ordinary-life share;
- explanation density;
- climax mechanism;
- paragraph/rhythm distribution.

Do not optimize for maximal difference. Ask whether unrelated genres are converging on the same hidden-network, reveal, chapter-delta, or institutional template merely because the Skill likes those structures. A version should preserve causal integrity **without reducing legitimate structural variety**.

The regression corpora under `assets/regression-corpora/` deliberately include a realistic infrastructure mystery, a low-mechanism relationship novel, progression fantasy, and a time-loop/branch project. Use them together; never let one corpus define “good fiction” for the others.

For maintenance experiments, record compact fingerprints with `assets/analysis-templates/architecture-fingerprint-template.json` and compare them using `scripts/architecture_diversity.py`. Treat high similarity as a prompt for human review, never as an automatic failure or a target to game.


## 13. Long-horizon benchmark ladder

Short E2E tests prove that modules can connect. They do not prove that a novel remains operable after dozens of chapters.

Maintain two distinct forms of long-horizon evidence.

### A. Deterministic continuity benchmark

Run:

```bash
python scripts/storyctl.py benchmark run --chapters 60
```

The benchmark generates a temporary 60-chapter Persistent project with:

- 60 prose chapter files and 61 committed Runtime events including initialization;
- a character who leaves for more than thirty chapters and returns with old knowledge intact;
- an object custody transfer that remains open for more than forty chapters before returning;
- a chapter-1 promise that reactivates late and pays off after fifty chapters;
- an injury whose later state preserves residue rather than resetting;
- Reader Model question movement;
- dependency propagation from early chapters into distant chapters;
- chapter-scoped context retirement and token-budget compilation;
- backend secret exclusion plus semantic-taint rejection of a paraphrased Writer-facing leak;
- full Runtime replay and project/schema validation.

This benchmark is intentionally synthetic and deterministic. It demonstrates **operational long-horizon integrity**, not literary quality.

Do not rewrite the benchmark to flatter a new subsystem. If an architectural change breaks it, explain why the benchmark contract itself became invalid before changing the test.

### B. Real longitudinal campaign evidence

Use `live-campaign-longitudinal-evaluation.md` for the canonical protocol. Live checkpoints should preserve artifact hashes plus the active Skill/harness hashes, and `storyctl campaign trajectory` should be used to inspect longitudinal growth without inventing one composite score. The live layer is intentionally stricter than the deterministic benchmark:

- real chapter artifacts and real project history must exist;
- checkpoints are collected across distinct sessions;
- long-term memory must influence later actions, not merely answer trivia;
- cold-resume/interruption recovery is tested;
- update fidelity, interference resistance, reader/permission continuity, and maintenance burden are tracked;
- creative drift / temporal flattening receives human review rather than a fake automatic literary score;
- synthetic `LWA-LONG-HORIZON-*` benchmark projects are explicitly ineligible for live-evidence claims.

Evidence maturity is reported as L0-L6. L4 is the first level allowed to support the wording **real 100-chapter evidence**. The 100 chapters are prospectively observed chapters after campaign registration, so an existing project registered at chapter N uses checkpoint offsets +1/+10/+25/+50/+75/+100 (absolute chapters N+1 ... N+100). L4 also requires session diversity, human-reviewed checkpoints, cold-resume evidence, campaign-origin memory-to-action probe coverage, and no severe integrity blocker at the terminal checkpoint.

Do not block ordinary Skill development merely because no live campaign has yet reached a milestone. Instead, bound the claim: report **operational benchmark passed** for deterministic stress evidence and report the exact live evidence level separately.

## 14. Failure-corpus and mutation adequacy

For maintenance releases, use `failure-corpus-mutation-testing.md` in addition to example regressions. A fixed historical incident should remain reproducible after the code that caused it is gone. Report the automated operator set together with the mutation score; never quote `1.000` without the operator count.

Treat a surviving non-equivalent mutant as evidence of a detector/containment gap. Preserve the survivor, minimize it, repair the canonical owner, and only then rerun promotion. Documented-only failures remain visible even though they are excluded from the mutation-score denominator.

## 15. Metamorphic / adversarial relation adequacy

Use `metamorphic-adversarial-benchmark.md` when a direct one-output oracle would be brittle or incomplete. Report the registered automated/documented relation counts, relation-type coverage, Narrative Semantics Kernel stratum coverage, failures, and invalid relations. Do not summarize this layer as a single robustness score.

A promotion run should include `python scripts/storyctl.py metamorphic validate` and `python scripts/storyctl.py metamorphic run`. Invariance-only suites are insufficient: keep directional, isolation, contrast/locality, monotonic, and evidence round-trip relations so a system that simply ignores input changes cannot appear robust.

When a metamorphic relation exposes a genuine defect, preserve and minimize the source/follow-up pair, repair the canonical owner, and feed the mechanism into the Failure Corpus.

## 16. Reasoning Intensity longitudinal calibration

Use `intensity-longitudinal-benchmark.md` when evaluating Low/Medium/High/XHigh/Max. Keep the five-level behavioral contract separate from calibration parameters and benchmark results. The first synthetic track is STC (Spatiotemporal Continuity), which uses a hidden deterministic latent world, solution-first challenge generation, delayed action probes, paired intensity arms, and separate Native/Protected/Repair-Free observations.

The STC harness must be blind to the intensity label before challenge freeze, must keep legal information access fixed in controlled comparisons, and must validate itself through generator properties, harness mutation, differential/oracle checks, metamorphic relations, surface-conservation checks, and intensity placebo/no-op-adapter controls. Do not report a single STC/Intensity/Benchmark-Trust score. Synthetic STC is operational evidence and never substitutes for `live-campaign-longitudinal-evaluation.md`.

## Project-Poetics construct validity

A benchmark must not reward one poetics by smuggling it into the scoring function. Separate:

1. **hard-integrity performance** - canon, time, access, knowledge, state, provenance, replay;
2. **project-poetics fidelity** - whether the output preserves the declared local literary contract;
3. **unauthorized convergence risk** - whether diverse projects are being normalized toward the Skill's familiar defaults;
4. **reader/quality judgment** - necessarily plural, task-conditioned, and partly interpretive.

For multi-poetics promotion, include adversarial fixtures whose authorized virtues conflict: quiet accumulation vs fair-clue inference; minimalist omission vs explicit polyphonic thought; stable voice vs authorized formal heterogeneity; ordinary recurrence vs event-centered propulsion. A version fails if it improves average checklist compliance by forcing those fixtures toward a common architecture.

Do not assign a single universal aesthetic score. Report failure families and pairwise/task-conditioned judgments instead.
## Trigger activation precision

Treat Skill activation as a separate classification surface from prose quality and long-form correctness. Use `assets/activation-evaluation/cases.json` with `scripts/activation_eval.py` / `storyctl activation-eval`. The corpus is intentionally split into `clear_positive`, `clear_negative`, `boundary`, and `near_miss` cases.

The central routing rule is **task risk over project origin**. A sentence or paragraph taken from a 180-chapter novel still stays outside this heavy Skill when the user asks only for context-free local polish. The same tiny text span becomes activation-positive when the requested edit explicitly depends on durable canon, downstream clue meaning, reader/knowledge state, Project Poetics, or revision invalidation.

Run the evaluation honestly:

1. `activation-eval validate --json` checks corpus shape and sentinel coverage.
2. `activation-eval build-blind --out PACKET.jsonl --json` exports only case ID/prompt; it hides category, gold labels, criticality, and rationale.
3. Record the **actual external/platform activation decision** for each case as `{"id": ..., "activate": true|false}`. Do not replace this step with a keyword classifier that merely restates the description.
4. `activation-eval score PREDICTIONS.jsonl --json` reports TP/TN/FP/FN, precision, recall, FPR/FNR, category breakdown, and the IDs of false positives/negatives. Add `--require-critical-pass` in a promotion run when any critical sentinel error should fail the command.
5. Treat zero errors on critical sentinels as the hard gate. Boundary/near-miss results remain separately visible so a good aggregate score cannot hide a dangerous local-polish false positive or an established-project false negative.

`activation-eval selftest --json` proves only that the evaluation harness catches injected FP/FN errors and that the blind packet hides gold. It does **not** prove the installed ChatGPT trigger has any particular precision until real trigger decisions are supplied.


### Recorded external activation evidence

Store real runtime campaigns under `assets/activation-evaluation/runs/` and bind each record to the exact corpus SHA-256 plus execution environment. Keep model/configuration metadata provenance explicit when it is supplied by the tester rather than independently observable from logs.

The first recorded campaign is preserved in the private historical archive (not distributed with this open-source package): Codex, GPT-6 Luna, Extra High reasoning effort (configuration user-reported), one fresh conversation per case, 32/32 correct decisions with TP=14, TN=18, FP=0, FN=0, and the critical gate passing. Treat this as evidence for that fixed corpus and recorded configuration only; do not generalize it into a universal trigger-accuracy claim.



## 17. Real prewriting-readiness incident

The first live Phase-4 project exposed a pre-draft false-positive that synthetic Core/Full coverage had not surfaced. A real historical time-loop project passed Project Doctor and had extensive planning files, yet the first readiness claim still omitted a causally necessary World Model. After that was repaired, independent review found additional opening-readiness gaps: the focal character remained an abstract “ordinary person” without the livelihood/current-task anchors needed by Chapter 1; Long-Horizon Architecture contained calendar bands but no explicit volume decision or near-term chapter map; the causally central first-rewind Scene Packet still deferred its trigger/reset transaction to drafting; and an early Writer handoff claim preceded a context compile whose `derived_from` provenance used file paths instead of context-entry IDs.

Preserve this mechanism as `prewriting-readiness-real-campaign-regression`. The lesson is not “always create more documents.” The regression requires explicit **activation decisions**, separates Project Doctor from prewriting readiness, separates `REVIEW_READY` from `DRAFT_READY`, and demands operational proof only for protections the project actually activated. It also treats each independent failure as a separate finding so a large green-looking planning bundle cannot hide one blocking seam.

The same campaign also exposed a Windows text-normalization seam: a compiled Writer pack's in-memory LF hash can diverge from CRLF bytes written to disk. `DRAFT_READY` evidence therefore verifies the actual on-disk pack bytes against the stored manifest hash rather than trusting a successful compile message alone.
