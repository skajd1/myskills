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
   - Keep `AGENTS.md` in sync with current personal skills when skill inventory changes.
   - Keep `.gitignore` aligned with the repository's role as a local skill store.
   - Exclude system-provided skills, temporary files, generated previews, logs, caches, superpowers planning artifacts, and unrelated worktree changes.
   - If the worktree contains unrelated user changes, leave them untouched.

3. Validate the skill when a validator is available.
   - Prefer the skill creator validator when available: `quick_validate.py <path-to-skill-folder>`.
   - If validation cannot run, report why and continue only if the files are simple enough to inspect manually.
   - Check that `SKILL.md` has valid YAML frontmatter with only `name` and `description`.

4. Stage only the intended files.
   - Use explicit paths with `git add`.
   - Re-run `git status --short` and confirm that only intended files are staged.

5. Commit the repository update.
   - Use a concise message such as `Add <skill-name> skill`, `Update <skill-name> skill`, `Rename <old-name> skill to <new-name>`, or `Update skill repository metadata`.
   - Do not amend or rewrite existing commits unless the user explicitly asks.

6. Push to GitHub.
   - Push the current branch to the configured GitHub remote.
   - If the branch has no upstream, set the upstream during push.
   - If authentication or remote configuration fails, report the exact blocker and the next command the user should approve or run.

## Safety Rules

- Never stage the entire repository with `git add .` when unrelated files are present.
- Never delete, revert, or overwrite user changes to make the worktree clean.
- Never commit temporary artifacts unless the user explicitly asks.
- Never commit `.system/`, `docs/superpowers/`, caches, generated previews, logs, or local scratch output.
- Never create PowerShell, shell, Python, or other helper scripts for this skill unless requested.
- Prefer exact file paths in every Git command.

## Completion Report

When finished, report:

- The skill path changed.
- Whether validation passed or why it was skipped.
- The commit hash and message, if committed.
- The pushed branch and remote, if pushed.
