# Git workflow

## Branches
- `main` is always working: tests pass and the app starts.
- One branch per Jira story: `SCRUM-<n>-<short-slug>`, for example `SCRUM-22-flac-reader`.
- Branches are short-lived. Merge to `main` when the story is Done.

## Commits
- Small commits, each one a coherent change that passes tests.
- Message format: `SCRUM-<n>: <imperative summary>`, then an optional body explaining *why*.
- Example: `SCRUM-22: Read FLAC stream info with mutagen`.

## Before every push (public repository)
1. `git status` shows no audio (`*.flac`, `*.mp3` and others), no database, no covers, no `config.local.toml`.
2. `git diff --cached` contains no personal paths. The default music path appears only in `config.example.toml` or in code as a documented default.
3. Tests and lint pass.

## Jira
- Start a story: move it to In Progress.
- Finish a story: move it to Done, with a comment listing what was verified.
- Link commits or PRs to the story key in the commit message or PR title.

## Pull requests
- Use a PR for each story, even when working alone. It gives a clear place for the checklist and CI results.
- PR description: what changed, how it was verified, and the Jira key.
