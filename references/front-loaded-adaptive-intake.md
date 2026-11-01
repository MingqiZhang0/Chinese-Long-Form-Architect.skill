# Front-Loaded Adaptive Intake

Use this reference when a new fiction project, major rebuild, or other substantial narrative task begins and unresolved user-level choices could materially change architecture. It owns **pre-work prompt parsing, unresolved-slot selection, one-batch freeform intake, delegation/absence semantics, Project Brief creation, and post-kickoff interruption policy**. It does not own later canon state, story-world uncertainty, or ordinary creative implementation details.

## Contents

- Core contract
- Slot states and authority
- Semantic delegation and absence semantics
- Parse-first resolution pass
- Which unknowns deserve a question
- Default author-level field families
- Freeform intake format
- One-batch completion and repair
- Project Brief and provenance
- Post-kickoff zero-interruption default
- Late ambiguity and blocker handling
- Mode scaling
- Interaction with authorial unknowns
- Anti-patterns
- Worked examples
- Project Poetics handoff

## 1. Core contract

Front-load author-level uncertainty before substantial execution.

Use this sequence:

`parse existing user intent -> resolve known slots -> suppress resolved questions -> identify consequential author-level unknowns -> ask them once in one grouped freeform intake -> normalize the answers -> emit a concise Project Brief -> begin autonomous execution`

Do not make the user repeatedly supervise routine creative choices after work has started.

The intake is **adaptive**, not a static questionnaire. A field exists in the catalog only as a candidate question. If the user's initial request, prior conversation, attached canon, or explicit project brief already resolves it, do not ask it again.

Prefer one larger pre-start interaction over a stream of later interruptions when the unresolved choices are foreseeable and materially affect the project.

## 2. Slot states and authority

Normalize relevant author-level fields into one of these states:

- **USER_LOCKED** - explicitly supplied by the user or unambiguously established by prior user-approved project material. Preserve it unless the user later changes it.
- **DELEGATED** - the user clearly transfers decision authority for this field or stated scope to the Agent; the Agent may choose a positive value later without asking again.
- **ABSENT** - the user explicitly indicates that the element, preference, or predeclared design constraint should not exist.
- **USER_RESERVED** - the user explicitly keeps a future author-level decision for themselves and, when useful, identifies the gate at which it may be revisited.
- **AGENT_DISCRETION** - a low-impact implementation detail was intentionally not asked because it belongs to normal Agent craft authority.
- **UNRESOLVED** - a consequential author-level variable is still unknown.
- **CONFLICT** - two locked user requirements cannot both be honored as currently understood.

Do not treat `UNRESOLVED` as a synonym for `DELEGATED`.

Do not treat `ABSENT` as a weak preference.

Do not turn every unasked implementation detail into an authorial unknown. Most local creative choices belong to `AGENT_DISCRETION`.

### Authority is separate from resolution

Keep the existing `status` vocabulary as the authority/intent classification. `DELEGATED` grants permission to decide; a value such as “你来定” records permission, not a resolved transport system. `AGENT_DISCRETION` similarly permits autonomous choice only inside the existing craft/Project-Poetics scope. Neither state requires another user confirmation.

Distinguish a user decision, an Agent proposal, a delegated unresolved choice, a discretion unresolved choice, a temporary assumption, and a canonical committed decision. Store proposals/temporary assumptions outside the resolved fields; they may support explicitly conditional exploration, never an active settled dependency. **Proposal does not gain authority merely because downstream reasoning has started.**

For a consequential decision actually needed by research, world model, chronology, case mechanics, long-horizon architecture, or Writer-safe compilation, use:

`proposal -> authorized resolution -> semantic commit -> dependency`

User decisions can resolve immediately. Delegated/discretion decisions are resolved by the Agent without re-asking. Persist the resolved value, authority, resolution, resolver, provenance, and semantic identity through the existing Project Brief/user-intent register before dependent work starts; `project-state.md` owns the machine contract. Convenience defaults and unresolved candidates cannot fill that contract. Semantic commit is durable state acceptance, not a Git commit.

An unrelated unresolved detail does not block independent work. In normalized JSON mark a truly low-impact unresolved slot `consequential: false`; when a consumer later needs it, its actual dependency edge still requires a resolved semantic commit. Do not classify missing foundational intake as low-impact to evade intake completion.

## 3. Semantic delegation and absence semantics

### Semantic delegation

Treat delegation as a **meaning-and-scope decision**, not an exact-token match. Normalize a field or stated scope to **DELEGATED** when the user clearly communicates that the Agent should decide it and no conflicting lock/reservation makes that interpretation unsafe.

High-confidence examples include:

- `自动` / `由你决定`;
- field-scoped replies such as `你看着办`, `你定`, `随你`, `按你觉得合适的来`, or `都行` when the active question makes the referenced field unambiguous;
- blanket but explicitly scoped instructions such as `其他你决定`, `剩下的你看着办`, or `没提到的按你认为合适的来`.

Determine scope from the structured field, the immediately preceding single-field question, or explicit language such as `其他/剩下的/没提到的`. A scoped delegation may cover multiple remaining ordinary author-level fields, but it does not silently override an existing USER_LOCKED, ABSENT, or USER_RESERVED commitment outside that scope. A later user instruction may supersede earlier intent only when the change itself is clear.

Do **not** equate semantic delegation with mere vagueness. Examples such as a bare `都行` after a multi-field batch, an isolated `随便` with no recoverable referent, or `不限` where the natural meaning is “no restriction” rather than “you choose for me” remain context-sensitive. If materially different authority scopes are plausible, keep the field `UNRESOLVED` and repair only that ambiguity.

Never ask the user to repeat a clear scoped delegation merely because they did not use a canonical token. Store the original phrase/provenance when useful, then normalize the slot to DELEGATED.

### Absence / exclusion semantics

Expressions such as these normally map to **ABSENT** when the field can logically be absent:

- `无`
- `没有`
- `不要`
- `不需要`
- `不包含`
- `禁止`
- other clear negative formulations

Examples:

- `爱情线：无` -> do not add a romance line merely because the Agent thinks one would help.
- `预设主题：无` -> do not choose and lock a governing thematic thesis/question on the user's behalf; themes may still emerge from the fiction.
- `明确禁项：无` -> there are no additional user-specified prohibitions in that field.

If a field is structurally mandatory, explain that `无` is invalid for that field **in the original intake prompt** and tell the user they may explicitly delegate the choice (for example `自动`, `由你决定`, or another clear scoped instruction) if they do not want to choose it. Example: a prose project cannot literally have no narrative access regime; `叙事视角` may therefore mark `不可填“无”` when the current workflow requires a resolved regime.

## 4. Parse-first resolution pass

Before asking anything, extract all usable intent from:

1. the current user request;
2. earlier conversation that still clearly applies;
3. attached/source canon or an existing Project Brief;
4. explicit user corrections that supersede older intent.

For each candidate slot, record internally:

- normalized field ID;
- current state;
- value if any;
- source/provenance;
- confidence that the meaning is unambiguous;
- whether the field was known before intake;
- whether it is consequential enough to ask if unresolved.

Treat a field as already resolved when the user's meaning is explicit or logically unambiguous. Do not re-ask it merely to fit a template.

If the wording admits materially different interpretations, keep the field unresolved instead of inventing certainty.

### Example

User request:

`帮我写一篇长篇现实主义小说，主题是身份是否由记忆决定，背景是1990年代东北。`

Already resolved:

- scale: long-form;
- category: realism;
- theme: identity and memory;
- era/region: 1990s Northeast China.

Do **not** ask those fields again.

## 5. Which unknowns deserve a question

Ask a field only when all of the following are true:

1. it is unresolved or genuinely conflicting;
2. it is relevant to the requested task;
3. it is an **author-level** choice rather than an implementation detail;
4. different answers would materially change architecture, reader experience, research scope, or user satisfaction;
5. the choice can usefully be resolved before work starts.

Typical reasons **not** to ask:

- the user already answered it;
- the user delegated it;
- the user explicitly excluded it;
- it is a local craft decision the Agent is expected to make;
- it concerns remote lore that need not be fixed yet;
- its answer would not materially alter the current task;
- asking would merely shift normal creative labor back to the user.

Use a conservative relevance test. The goal is not maximum questionnaire completeness; it is maximum **pre-start decision clarity per unit of user effort**.

## 6. Default author-level field families

For a serious new long-form project, consider the families below. Ask only unresolved, relevant, consequential fields.

### A. Project identity

Possible fields:

- category / genre identity;
- core premise or governing story problem;
- predeclared theme or thematic question;
- intended scale / length / volume scope;
- target readership or publication/platform context when it materially affects form.

### B. World and reality contract

Possible fields:

- era / geography / setting;
- real-world vs speculative / alternate-world relation;
- realism level and tolerated invention;
- research / factual-fidelity expectation;
- major world-rule boundaries the user already cares about.

### C. Character and relationship direction

Possible fields:

- protagonist or central cast conception;
- desired ensemble scale;
- core relationship emphasis when author-level rather than emergent;
- central conflict/pressure if the user wants to own it;
- required or excluded relationship lines.

### D. Narrative form

Possible fields:

- narrative perspective / focalization regime;
- overall voice / tonal direction;
- linear, multi-line, multi-generational, fragmented, or other structural preference;
- time handling / pacing preference when materially important;
- desired degree of formal or modernist experimentation.

### E. Outcome and content authority

Possible fields:

- ending tendency or closure preference;
- required elements;
- explicit exclusions / prohibitions;
- topics or devices the user strongly wants avoided;
- author-level decisions the user explicitly reserves for themselves.

Do not ask low-level questions such as a minor character's surname, exact weather in a future scene, furniture placement, or the chapter number of a routine reveal unless the user explicitly wants that degree of control.

## 7. Freeform intake format

Do not present multiple-choice menus by default. Use `assets/intake-templates/project-intake-template.md` as a removable-field scaffold when helpful.

Each unresolved field should be a freeform blank with a short example that clarifies the kind of answer expected without constraining the answer space.

Use a compact header once:

- `如果希望我决定，可以直接写“自动 / 由你决定 / 你看着办”等；只要授权对象明确，我会按语义归一为委托。`
- `“无/没有/不要/不需要”等 = 明确表示该元素或预设不存在；不是授权我替你选择。`
- `示例仅用于说明字段含义，不是备选菜单。`

Then use fields such as:

`类别：`  
`示例：现实主义、科幻×悬疑、历史、无明确类型等。`

`主题：`  
`示例：身份与记忆、制度与个人、死亡、自由意志；若不希望预先锁定主题可填“无”。`

`叙事视角：`  
`示例：第一人称、第三人称限知、多视角；如希望我决定，可写“自动”“由你决定”“你看着办”等明确授权表达。`

Never convert examples into an implied menu.

## 8. One-batch completion and repair

Group all foreseeable unresolved author-level questions into **one initial batch** whenever practical.

Do not ask three questions, begin research, then discover four more obvious questions that could have been asked at the start.

After the user replies:

1. parse all answers together;
2. normalize delegation, absence, locks, and reservations;
3. detect blank/invalid/contradictory required fields;
4. if necessary, issue **one compact pre-start repair message** containing only those unresolved blockers;
5. otherwise emit the Project Brief and start work.

A blank answer is not automatically `DELEGATED`. If a blank field remains materially necessary, repair it before kickoff. If the field turns out not to matter, drop it from the active intake rather than inventing a requirement.

Do not ask for a second ceremonial confirmation after the answers are already clear. A concise readback is sufficient.

## 9. Project Brief and provenance

Once intake is complete, create a concise **Project Brief** that records at least:

- task / project type;
- USER_LOCKED author-level constraints;
- DELEGATED fields;
- ABSENT / prohibited elements;
- USER_RESERVED decisions and any declared gates;
- relevant research/fidelity requirements;
- any resolved conflict or interpretation note;
- source/provenance of each high-impact user constraint when useful;
- kickoff status.

Use `assets/intake-templates/project-brief-template.md` when a persistent file is useful.

The Project Brief becomes the upstream source of **explicit user intent** for prewriting and later project state. `project-state.md` owns its durable persistence and later updates once the project is running.

If normalized intake state is persisted as JSON, use `assets/intake-templates/intake-state-template.json` as a starting shape and `scripts/validate_intake_state.py` to check interaction mechanics and declared decision dependencies. The validator does not infer intent or judge literary quality. Register its canonical path as `canonical_paths.intake_state` in the existing Project Manifest when machine-readable consequential dependencies are used; it is the serialization of this same Project Brief, not a second decision registry.

If the user later changes a locked preference, the latest explicit instruction wins; record the change and propagate affected architecture instead of treating the first brief as immutable canon.

## 10. Post-kickoff zero-interruption default

After the Project Brief is complete and substantive execution begins, use a default **nonessential interruption budget of zero**.

Do not return to the user for ordinary creative choices such as:

- which minor character speaks first;
- exact scene weather;
- whether a clue appears in Chapter 17 or 18;
- minor naming;
- routine scene order;
- local pacing adjustments;
- ordinary worldbuilding details that fit established constraints.

Resolve these through existing canon, project rules, research, causal simulation, reader needs, and Agent craft judgment.

A field that was never asked because it was low-impact is not a deferred questionnaire item. It is normal Agent discretion unless later user intent makes it consequential.

The purpose of intake is to transfer routine responsibility **to** the Agent, not to create a queue of future questions.

## 11. Late ambiguity and blocker handling

After kickoff, ask the user only when the work genuinely cannot proceed honestly without their authority or information.

Valid interruption classes are narrow:

1. **locked-constraint conflict** - two explicit user requirements are mutually incompatible and no faithful interpretation can preserve both;
2. **user-only missing fact** - a required personal/source fact cannot be researched, inferred, or safely invented;
3. **declared USER_RESERVED gate** - the user explicitly kept this decision and the predeclared gate has been reached;
4. **explicit approval contract** - another Skill rule already requires user approval, such as optional humanities development.

When a late question becomes unavoidable:

- batch all currently known blockers into one message;
- explain the minimum reason each needs the user;
- do not mix blockers with optional curiosity questions;
- preserve a durable checkpoint so completed work is not reconstructed from memory.

If a decision can remain branch-compatible or authorially unknown without blocking current causality, keep working instead of interrupting.

## 12. Mode scaling

### Serious new long-form project

Run the full adaptive intake before Reality Grounding and the **Base Readiness + activated-artifact** loop in `prewriting-readiness.md`. Compile a provisional Project Poetics record from already supplied theme/question, intended reading experience, form/voice aims, genre/tradition, explicit exclusions, and source-text evidence. Do not ask the user to fill a new aesthetic questionnaire merely because the compiler can represent those choices. `theme: none` remains fully legal.

### Major foundational rebuild

Ask only author-level choices whose status is changed or newly relevant to the rebuild. Preserve unaffected prior intent.

### Established-project continuation

Load the existing Project Brief and current user instruction. Do not replay the original intake. Ask only a genuinely new consequential author-level constraint that must be resolved before the requested continuation.

### Diagnosis / revision

Intake should focus on revision goals, protected material, and user-owned constraints. Do not ask genre/theme/world questions already evident from the text.

### Local scene / micro-task

Usually skip full intake. If a missing choice genuinely blocks the scene, ask all such blockers in one compact batch before drafting.

### Explicit immediate-draft request

If the user explicitly says to draft now and not ask questions, honor that instruction. Preserve their known constraints and use Agent discretion for ordinary gaps unless a true blocker makes the request impossible to execute honestly.

## 13. Interaction with authorial unknowns

Do not confuse **missing intake information** with an **authorial unknown**.

- Intake unknown: a user-preference variable that should usually be resolved or delegated before work begins.
- Authorial unknown: a story-world truth intentionally left undecided during creative development.

If the user does not reserve a story truth for themselves, the Agent may keep it open or resolve it later when causally necessary under `discovery-drafting.md`.

If the user explicitly marks a future decision as USER_RESERVED, preserve compatible branches/constraints and ask only at the declared gate when necessary.

## 14. Anti-patterns

Reject these behaviors:

- asking a static full questionnaire regardless of the initial prompt;
- re-asking a theme, category, era, protagonist, or other field the user already specified;
- presenting A/B/C menus as if the examples exhaust the user's creative options;
- mapping `无` to Agent delegation;
- requiring canonical delegation tokens after the user has already given a clear scoped semantic delegation, or conversely expanding an ambiguous phrase into broader authority than its recoverable scope;
- silently filling an ABSENT element because it seems commercially useful;
- asking implementation details that the Agent should own;
- beginning substantial work before obvious high-impact questions are asked, then drip-feeding questions mid-run;
- treating every unasked detail as future user debt;
- forcing a redundant confirmation after a clear Project Brief readback;
- using intake completeness as an excuse for exhaustive worldbuilding or remote-detail planning.

## 15. Worked examples

### Example A - known theme is suppressed

Initial request:

`帮我写一部长篇小说，主题是记忆是否构成人的身份。`

Do not ask `主题` again.

Ask only the still-relevant author-level fields whose answers would materially change the project, such as category/world contract, protagonist direction, narrative form, or ending tendency if they remain unknown and consequential.

### Example B - absence and delegation are different

User response:

`爱情线：无`  
`叙事视角：自动`

Normalize:

- romance line -> ABSENT;
- POV -> DELEGATED.

The Agent may choose POV. It may not later add a romance line as though `无` meant freedom.

### Example C - no predeclared theme

User response:

`主题：无`

Do not manufacture a formal thematic thesis/question and mark it user-approved. Let thematic patterns emerge from characters, institutions, consequences, and later analysis without retroactively claiming the user selected them.

### Example D - semantic delegation

Field-scoped response:

`叙事视角：你看着办。`

Normalize POV to DELEGATED. Do not ask the user to restate `自动` or `由你决定`.

Blanket request:

`写一部发生在近未来上海的长篇科幻小说，剩下的按你认为合适的来。`

Lock setting and broad category. Treat remaining eligible ordinary author-level fields in that stated scope as DELEGATED. Do not display a questionnaire just to obtain permission already granted.

By contrast, if a multi-field intake receives only `都行` and its target scope cannot be recovered, repair that scope ambiguity instead of assuming blanket authority.

### Example E - one compact repair before kickoff

The intake asks for a mandatory narrative-access regime and explicitly says `不可填“无”`. The user replies `叙事视角：无`.

Before work starts, repair only that field:

`叙事视角这一项无法实际为空；如果你不想指定，可以直接说“你来定”“你看着办”或其他明确授权表达。`

Do not begin planning and ask again several steps later.

## 16. Project Poetics handoff

Intake owns **user intent**, not literary doctrine. After the Project Brief is stable enough to begin planning:

1. route explicit and delegated project-level choices to `project-poetics.md`;
2. preserve `none`, `open`, and provisional values instead of inventing a thematic thesis;
3. distinguish user-locked formal commitments from Agent proposals;
4. record explicit **do-not-optimize** instructions such as "do not accelerate this domestic novel" or "do not normalize chapter voices";
5. let later textual discoveries propose poetics updates through `discovery-drafting.md` rather than silently rewriting project intent.

Do not map theme labels directly to style presets. Theme/question is one input among intended experience, organizing principle, focalization, genre/history, formal ambition, explicit exclusions, and already-written evidence.
