<div align="center">

# Chinese Long-Form Architect

**A persistent-world Agent Skill for serious Chinese-language long-form fiction.**

*The world continues beyond the page.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.13+](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)](#requirements)
[![Release status: Public preview](https://img.shields.io/badge/Status-Public%20Preview-orange.svg)](PUBLIC_RELEASE_NOTES.md)

**English** · [简体中文](README.zh-CN.md)

[Why it exists](#why-it-exists) · [Quick start](#quick-start) · [How it works](#how-it-works) · [Architecture](#architecture) · [Development](#development)

</div>

---

Chinese Long-Form Architect helps AI writing agents **plan, continue, diagnose, and revise Chinese-language novels without treating each chapter as an isolated prompt**. It maintains an explicit account of story facts, character knowledge, causal dependencies, and revision consequences. Project-specific literary choices remain with the author.

This is a **Skill plus deterministic validation tooling**, not a language model, a hosted novel-writing service, or a finished desktop application. The current distribution is a **public-source preview**; long-horizon literary performance has not been established by a complete public evaluation.

## Why it exists

Long-running fiction has a different failure mode from single-prompt generation. A plausible scene can still contradict an earlier chapter, give a character information they never acquired, erase the consequences of an event, or quietly invalidate a later reveal.

| Common long-form failure | What this project provides |
| --- | --- |
| Established facts change between chapters | **Canon and Story State** to record consequential facts and check declared invariants |
| Characters know things they could not have learned | **Knowledge Topology** to separate world truth, individual knowledge, source evidence, and disclosure |
| Mysteries rely on retroactive convenience | **Hidden Causal Networks** to track mechanisms, preconditions, and bounded causal claims |
| Supporting characters stop existing offscreen | **Living World** guidance for selective offscreen activity and state persistence |
| A revision silently breaks later material | **Revision-impact analysis** and dependency-aware invalidation |
| Context windows leak spoilers or lose crucial facts | **Role-scoped context compilation** for scene and writing handoffs |
| Writing rules flatten every novel into the same formula | **Project Poetics** to keep aesthetic choices explicit, contextual, and author-controlled |

These are mechanisms and workflows, **not guarantees**. Automated checks can only reason about facts and constraints that have been properly represented and supplied.

## Quick start

### 1. Install the Agent Skill

Use an agent environment that supports directory-based Skills. Obtain the separate installable **`skill.zip`** from the project's [Releases](https://github.com/MingqiZhang0/Chinese-Long-Form-Architect.skill/releases) once published, and extract it into your host's Skills directory.

The installed folder must have this entry point:

```text
<your-agent-skills-directory>/
└── literary-webnovel-architect/
    ├── SKILL.md
    ├── agents/
    ├── references/
    ├── scripts/
    └── assets/
```

The **installation package** is intentionally smaller than the development repository. Consult your agent host's own installation instructions for the correct Skills directory. The technical identifier is `literary-webnovel-architect` and should not be renamed casually.

### 2. Start with your story, not with configuration

In an agent session with the Skill installed, try:

> I'm developing a long-form Chinese mystery novel. Before drafting prose, help me establish the smallest useful project state. Separate established events, what each character knows, and what readers have seen. Do not invent irreversible plot decisions or start Chapter 1 without asking me.

The Skill chooses a workflow based on the **task and project state**. A new novel, a continuation, a local prose edit, and a causal revision do not need the same amount of machinery.

### 3. Explore the deterministic tools (optional)

For CLI-based project management, clone the **source repository** and run the following commands from its root:

```bash
git clone https://github.com/MingqiZhang0/Chinese-Long-Form-Architect.skill.git
cd Chinese-Long-Form-Architect.skill
python -m pip install -r requirements.txt

# Discover the available commands and the recommended new-project workflow.
python -B scripts/storyctl.py catalog
python -B scripts/storyctl.py route new-project

# Create a minimal project and validate its manifest.
python -B scripts/storyctl.py project init ./example-novel --project-id example-novel
python -B scripts/storyctl.py project verify ./example-novel/project-manifest.json --root ./example-novel
```

Expected result of the final command:

```text
OK: project manifest and canonical pointers are consistent
```

The command creates **project metadata, not a completed manuscript**. For continuation or diagnosis, discover the relevant workflow with `route resume-project`, `route continue-chapter`, or `route diagnose-project`.

## How it works

A story is more than a text file. The Skill distinguishes several kinds of information that an ordinary chat history can blur together:

- **Story truth:** what has actually happened in the fictional world.
- **Character knowledge and belief:** what a particular person could know or infer at a particular time.
- **Narrative access:** what a viewpoint character, narrator, or writing pass is allowed to disclose.
- **Authorial authority:** which creative decisions are confirmed, provisional, or still open.
- **Historical consequences:** what must be reconsidered when a prior decision or event changes.

A typical chapter workflow is:

```text
Author intent + Project Poetics
              |
              v
    Canon / Story State / evidence
              |
              v
    Planning and readiness checks
              |
              v
      Role-scoped context
              |
              v
         Draft / revise
              |
              v
      Review and reconciliation
              |
              v
    Updated state for the next chapter
```

**Example:** A character hears a rumor in Chapter 3, but never witnesses the event. In Chapter 8, the draft has them describe it as firsthand experience. If the relevant acquisition and assertion have been recorded, the system can flag a mismatch in knowledge basis. It does **not** independently discover every such mistake by reading raw prose.

The system favors **selective formalization**: record what protects continuity and causality; do not turn every atmospheric detail or stylistic choice into a database requirement. Read the [Skill contract](SKILL.md), [Project Poetics](references/project-poetics.md), and [Knowledge Topology](references/knowledge-topology.md) for the underlying rules.

## Architecture

The project has three distinct responsibilities:

| Layer | Responsibility | Main locations |
| --- | --- | --- |
| **Agent Skill** | Choose the appropriate workflow, preserve author control, select relevant context, and guide writing/review | [`SKILL.md`](SKILL.md), [`references/`](references/) |
| **Deterministic tooling** | Validate declared state, provenance, temporal/knowledge constraints, runtime events, readiness, and revision impact | [`scripts/`](scripts/), [`assets/`](assets/) |
| **Experimental Workbench** | Explore a read-only visual interface to selected project state and evidence | [`experiments/workbench-spike/`](experiments/workbench-spike/) |

The Workbench is a **technical spike**, not a supported production application. The Skill does not depend on it. Protocol fixtures required to reproduce the spike are included under [`docs/workbench/contracts/`](docs/workbench/contracts/).

## Scope and limitations

| Area | Current position |
| --- | --- |
| Primary writing language | **Chinese**, with current prose-quality evidence centered on simplified Chinese (`zh-CN`) |
| Types of work | New projects, continuation, substantial revision, continuity diagnosis, and appropriately scoped local/discovery work |
| Literary style | Defined by each project's **Project Poetics**, not a universal plotting formula |
| Reliability | Deterministic checks for **recorded** constraints; no proof of perfect narrative continuity |
| Writing quality | No demonstrated guarantee of high-quality output over 50, 100, or 300 chapters |
| User interface | Skill instructions and CLI; Workbench remains experimental |
| Data security | Local files are not a strong sandbox; do not assume protection against a hostile agent or untrusted plugin |

The public source intentionally excludes private manuscript fixtures, raw model transcripts, and internal experiment logs. As a result, the original extended **Core / Full / Soak** regression program is **not fully reproducible** from this checkout. See [Public Release Notes](PUBLIC_RELEASE_NOTES.md) and [Public Data Policy](PUBLIC_DATA_POLICY.md) for exact boundaries.

## Requirements

- A host that can load file-based Agent Skills and provide the model/runtime capabilities needed for your workflow.
- **Python 3.13+** for the deterministic scripts.
- `jsonschema>=4.18,<5` for the documented runtime checks (`requirements.txt`).
- Additional .NET / Python dependencies **only** if working on the experimental Workbench; see its [README](experiments/workbench-spike/README.md).

Reading the Skill's instructions does not require running Python. Project verification, transactions, context compilation, and the formal readiness gates do require the supported tooling and project evidence.

## Development

This repository is the **privacy-curated source tree**. The installable `skill.zip` contains the production Skill surface without development tests or Workbench experiments. Do not treat the source tree and installation bundle as byte-identical artifacts.

Run the public checks from the repository root:

```bash
python -B scripts/audit_skill_structure.py .
python -B scripts/test_public_release.py
python -B scripts/test_public_fast.py

# Optional: verify that Workbench protocol-generated definitions are in sync.
python -B experiments/workbench-spike/generate_contract.py --check
```

The curated public Fast suite previously passed **12/12** checks in the release audit, but that result does **not** imply the withheld historical Core / Full / Soak suite passed. Actual CI status should be judged from [GitHub Actions](https://github.com/MingqiZhang0/Chinese-Long-Form-Architect.skill/actions) after the repository is published.

**Repository guide:** [`SKILL.md`](SKILL.md) · [`references/`](references/) · [`scripts/`](scripts/) · [`assets/`](assets/) · [`PUBLIC_RELEASE_NOTES.md`](PUBLIC_RELEASE_NOTES.md) · [`SECURITY.md`](SECURITY.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Contributing and security

Issues and pull requests are welcome. Changes to authorial authority, knowledge constraints, evidence/provenance, or revision behavior should include reproducible **synthetic** tests. See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution process.

Do not submit real manuscripts, hidden plot plans, model transcripts, access tokens, or machine-specific logs. The public Git history is not an appropriate place to store private writing projects. For security reports, follow [SECURITY.md](SECURITY.md).

## License

Licensed under the [MIT License](LICENSE) for original code and documentation in this distribution. Third-party components and reference material, where applicable, remain subject to their own terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
