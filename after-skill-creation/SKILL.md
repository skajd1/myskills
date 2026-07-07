---
name: after-skill-creation
description: Use after Codex creates or updates one of the user's personal skills and the user wants local skill changes reflected in their GitHub skill collection repository. Triggers include "after skill creation", "스킬 만든 뒤 깃허브에 올려", "개인 스킬을 repo에 반영", "스킬 모음집 repo에 올려", or any request to validate, commit, and push newly created or modified skill files.
---

# After Skill Creation

## Goal

Publish personal skill changes from the local skill collection repository to GitHub without adding unrelated files.

Use this skill only after the skill content itself has been created or updated. Do not create helper scripts or automation files unless the user explicitly asks for them.

## Workflow

1. Confirm the repository context.
   - Run `git status --short --branch`.
   - Run `git remote -v`.
   - If no GitHub remote is configured, ask the user for the target repository URL before pushing.

2. Identify the skill changes.
   - Include the new or changed skill folder and any directly related files the user requested.
   - Exclude temporary files, generated previews, logs, caches, and unrelated worktree changes.
   - If the worktree contains unrelated user changes, leave them untouched.

3. Validate the skill when a validator is available.
   - Prefer the skill creator validator when available: `quick_validate.py <path-to-skill-folder>`.
   - If validation cannot run, report why and continue only if the files are simple enough to inspect manually.
   - Check that `SKILL.md` has valid YAML frontmatter with only `name` and `description`.

4. Stage only the intended files.
   - Use explicit paths with `git add`.
   - Re-run `git status --short` and confirm that only intended files are staged.

5. Commit the skill update.
   - Use a concise message such as `Add after-skill-creation skill` or `Update <skill-name> skill`.
   - Do not amend or rewrite existing commits unless the user explicitly asks.

6. Push to GitHub.
   - Push the current branch to the configured GitHub remote.
   - If the branch has no upstream, set the upstream during push.
   - If authentication or remote configuration fails, report the exact blocker and the next command the user should approve or run.

## Safety Rules

- Never stage the entire repository with `git add .` when unrelated files are present.
- Never delete, revert, or overwrite user changes to make the worktree clean.
- Never commit temporary artifacts unless the user explicitly asks.
- Never create PowerShell, shell, Python, or other helper scripts for this skill unless requested.
- Prefer exact file paths in every Git command.

## Completion Report

When finished, report:

- The skill path changed.
- Whether validation passed or why it was skipped.
- The commit hash and message, if committed.
- The pushed branch and remote, if pushed.
