---
name: skill-manager
description: Manage this personal Codex skill repository at C:\Users\wooch\.codex\skills. Use when the user asks to create, update, rename, remove, validate, commit, or push personal skills; sync local skill changes to GitHub; update AGENTS.md or .gitignore for the skill repo; or says "스킬 관리", "스킬 repo 반영", "스킬 만든 뒤 깃허브에 올려", "개인 스킬을 repo에 반영".
---

# Skill Manager

## Goal

Maintain the user's personal Codex skill collection as both a local skill store and a Git repository.

Use this skill when skill folders under `C:\Users\wooch\.codex\skills` are created, updated, renamed, removed, validated, committed, or pushed. Do not create helper scripts or automation files unless the user explicitly asks for them.

## Workflow

1. Confirm the repository context.
   - Run `git status --short --branch`.
   - Run `git remote -v`.
   - If no GitHub remote is configured, ask the user for the target repository URL before pushing.

2. Identify the skill changes.
   - Include the new, changed, renamed, or removed skill folder and any directly related repository files the user requested.
   - If any personal skill is created, removed, renamed, or its purpose/trigger changes, update `AGENTS.md` in the same change. This is mandatory, not optional.
   - Keep the skill list in `README.md` in sync with current personal skills. Update only the list/summary sections unless the repository usage flow itself changed.
   - Keep `.gitignore` aligned with the repository's role as a local skill store.
   - Exclude system-provided skills, temporary files, generated previews, logs, caches, superpowers planning artifacts, and unrelated worktree changes.
   - If the worktree contains unrelated user changes, leave them untouched.

3. Check repository documentation consistency.
   - Compare top-level personal skill folders with the `AGENTS.md` skill index.
   - Refuse to commit skill inventory changes if `AGENTS.md` is stale.
   - Compare top-level personal skill folders with the `README.md` skill list.
   - Keep `README.md` concise and human-facing; do not duplicate detailed operating rules there.

4. Validate the skill when a validator is available.
   - Prefer the skill creator validator when available: `quick_validate.py <path-to-skill-folder>`.
   - If validation cannot run, report why and continue only if the files are simple enough to inspect manually.
   - Check that `SKILL.md` has valid YAML frontmatter with only `name` and `description`.

5. Stage only the intended files.
   - Use explicit paths with `git add`.
   - Re-run `git status --short` and confirm that only intended files are staged.

6. Commit the repository update.
   - Follow the commit rules below.
   - Do not amend or rewrite existing commits unless the user explicitly asks.

7. Push to GitHub.
   - Push the current branch to the configured GitHub remote.
   - If the branch has no upstream, set the upstream during push.
   - If authentication or remote configuration fails, report the exact blocker and the next command the user should approve or run.

## Safety Rules

- Never stage the entire repository with `git add .` when unrelated files are present.
- Never delete, revert, or overwrite user changes to make the worktree clean.
- Never commit temporary artifacts unless the user explicitly asks.
- Never commit `.system/`, `docs/superpowers/`, caches, generated previews, logs, or local scratch output.
- Never commit a skill creation, deletion, rename, or purpose/trigger change without updating `AGENTS.md`.
- Never commit a skill creation, deletion, or rename without checking the `README.md` skill list.
- Never create PowerShell, shell, Python, or other helper scripts for this skill unless requested.
- Prefer exact file paths in every Git command.

## Commit Rules

- Commit only when the user asks to commit, push, publish, sync to GitHub, or otherwise make the repository changes durable.
- Stage only explicit intended paths. Use `git add <path>...`, never `git add .` or `git add -A` at repository root when unrelated files may exist.
- Before committing, run `git status --short` and inspect the staged set.
- Keep each commit focused on one coherent repository change:
  - Skill inventory or metadata update: `Update skill repository metadata`
  - New skill: `Add <skill-name> skill`
  - Existing skill change: `Update <skill-name> skill`
  - Rename: `Rename <old-name> skill to <new-name>`
  - Removal: `Remove <skill-name> skill`
- If a change touches multiple skills as one intentional repo sync, use `Update personal skill repository`.
- Use imperative, concise commit messages with no trailing period.
- Do not include temporary files, generated previews, logs, cache files, local config, credentials, `.system/`, or `docs/superpowers/`.
- Do not commit a skill inventory change unless `AGENTS.md` is updated and the `README.md` skill list has been checked.
- After committing, push only when the user requested push/sync/publish or clearly wants GitHub updated.
- After push, report the commit hash, message, branch, and remote.

## Completion Report

When finished, report:

- The skill path changed.
- Whether validation passed or why it was skipped.
- The commit hash and message, if committed.
- The pushed branch and remote, if pushed.
