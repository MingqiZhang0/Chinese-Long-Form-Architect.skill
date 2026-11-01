# Skill Scope and Identity

This reference is the canonical owner of the Skill's product scope, public display identity, compatibility slug policy, and any future scope/slug migration decision. It does not define literary poetics.

## 1. Canonical product decision

- **Product identity:** `Chinese Long-Form Architect`.
- **Primary target:** serious Chinese-language long-form fiction.
- **Current empirical prose-evaluation baseline:** `zh-CN`.
- **Cross-language parity:** **not claimed**.
- Language-neutral Hard Core, Runtime, Project State, Project Poetics infrastructure, and other generic mechanisms do not by themselves justify a multilingual product claim.
- Multilingual research sources, names, quotations, code-switching, translation evidence, or foreign-language dialogue may appear inside a Chinese-language project when the work requires them. This is not equivalent to native long-form prose/evaluation parity in those languages.
- For a novel whose primary target prose is non-Chinese, do not auto-position this Skill as a native-language prose authority. A user may still explicitly reuse its language-neutral architecture, but any native-language prose-quality claim must come from a separately evidenced language layer.

## 2. Why the product remains Chinese-specific

The package contains Chinese-specific grammar/idiom rules, Chinese prose-integration constraints, and a dedicated Chinese narrative behavioral evaluation corpus. There is no equivalent promoted grammar/idiom plus behavioral-evaluation stack for English, Japanese, Korean, or another target language. Product scope follows demonstrated end-to-end capability, not the most language-neutral subsystem.

Do not broaden the public identity to generic `Long-Form Architect` merely because semantic/runtime layers are reusable across languages.

## 3. Technical slug policy

- **Current compatibility slug:** `literary-webnovel-architect`.
- The current directory name, SKILL frontmatter `name`, installed identity, script/module references, and existing schema `$id` namespaces may continue to use that slug.
- Treat the slug as a historical technical identifier, not as the product's literary scope. In particular, `webnovel` in the slug does not limit the product to commercial web fiction.
- **Candidate future slug:** `chinese-long-form-architect`.
- **Migration status:** deferred; no in-place rename in ordinary maintenance releases.

## 4. Controlled slug migration gate

A future slug migration may occur only in a dedicated compatibility/breaking release after all of the following are true:

1. inventory every slug-coupled surface: directory/package identity, SKILL frontmatter, agent metadata, schema `$id` values, scripts, tests, fixtures, documentation, saved project references, and any external installation/update path;
2. decide and test whether the platform provides alias/redirect/update continuity; if it does not, keep the legacy slug rather than silently creating a second identity;
3. define schema-ID compatibility separately from display-name migration; do not rewrite historical schema namespaces without an explicit migration contract;
4. provide an explicit old->new migration note and regression test proving existing projects/packages remain discoverable and interpretable;
5. package the renamed Skill as an intentional migration artifact, never as a side effect of an unrelated maintenance patch.

If these conditions cannot be satisfied, keep `literary-webnovel-architect` indefinitely while continuing to present `Chinese Long-Form Architect` as the product name.

## 5. Multilingual successor policy

Do not silently evolve this product into a generic multilingual Long-Form Architect. If true multilingual parity becomes a goal, prefer a separate successor or explicitly versioned redesign. A multilingual claim requires promoted, language-specific prose/idiom guidance and behavioral evaluation for each claimed target language, plus cross-language/code-switching regressions. Reusing the Chinese Skill's Hard Core is useful infrastructure, not evidence of native prose parity.

## 6. Maintenance rule

When product scope, display name, slug policy, or multilingual claims change, update this owner first, then synchronize `SKILL.md`, `agents/openai.yaml`, the system map, and the scope/identity regression contract. Do not infer a scope change from a UI rename alone.
