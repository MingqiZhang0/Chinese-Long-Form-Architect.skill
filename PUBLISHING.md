# Publishing checklist (maintainer action required)

This repository package has been cleaned and tested as a *public-source preview*. It is **not** yet published to GitHub.

## Before publishing

1. Confirm that `MingqiZhang0` is the intended GitHub owner and copyright attribution. Confirm use of the MIT license and that you hold the rights to distribute all files and original synthetic fixture text.
2. Read `PUBLIC_DATA_POLICY.md`, `PUBLIC_RELEASE_NOTES.md` and `SECURITY.md`. Private real-user novel content and raw model evaluation archives must never be added to Git history.
3. Use the already-created, currently empty public GitHub repository named `Chinese-Long-Form-Architect.skill` under `MingqiZhang0`. Do not initialize it with a README, `.gitignore`, or license on GitHub; these already exist in this release source tree.
4. From the extracted root (where `SKILL.md` is):

```bash
python -B scripts/test_public_release.py
python -B scripts/test_public_fast.py
python -B experiments/workbench-spike/generate_contract.py --check
git init -b main
git add -A
git commit -m "Initial public-source preview"
git remote add origin https://github.com/MingqiZhang0/Chinese-Long-Form-Architect.skill.git
git push -u origin main
```

Before committing, check `git config --get user.name` and `git config --get user.email`. Git commit metadata can publicly reveal a personal email address even when the source ZIP contains none. Use your GitHub-provided noreply address if you want to keep that email private. Never commit an archive of the *private full development snapshot* or the *private original real-user fixture*.

## Publishing the installable Skill

Upload the separately supplied `skill.zip` to a **pre-release** named `v0.1.0-public-preview` after source push succeeds. The ZIP should contain a single `literary-webnovel-architect/SKILL.md` skill entry and the corresponding references/scripts/assets. Do not attach the full development archive.

## Release labeling

Do not claim that the full Core/Full/Soak pipeline passed or that the Workbench is production-ready. The published public repo only passes the explicitly scoped public checks. Resolve full regression reproducibility and long-horizon quality evidence before dropping the preview label.
