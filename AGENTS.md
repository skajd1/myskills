# Repository Instructions

## Personal Skill Completion Workflow

When Codex creates or updates a personal skill in this repository, treat the skill work as incomplete until the skill has been validated and published.

After Codex judges that skill development is complete, and only after validation or manual inspection supports that judgment, automatically use the `after-skill-creation` skill without waiting for a separate user request.

The completion workflow must:

1. Validate the created or updated skill when a validator is available.
2. Inspect `git status --short --branch`.
3. Stage only the intended skill files with explicit paths.
4. Leave unrelated user changes, temporary files, logs, caches, generated previews, and `tmp/` files untouched.
5. Commit the skill update with a concise message.
6. Push the current branch to the configured GitHub remote when possible.

Stop and report instead of committing or pushing when:

- The skill is still in progress.
- Validation fails.
- The intended files are ambiguous.
- Unrelated changes are staged.
- No GitHub remote is configured.
- Authentication, network access, or permissions block the push.

Do not create helper scripts for this workflow unless the user explicitly asks.
