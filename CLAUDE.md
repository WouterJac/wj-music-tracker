# CLAUDE.md: WJ Music Tracker

Master instructions. Read this at the start of every session.

## What this is
A local web app that analyses a FLAC music collection: browse albums and artists, statistics, metadata, lyrics, interesting facts, and later recommendations. Runs on the owner's PC. Phone access comes later.

## Hard rules
1. **The music folder is read-only.** The app never writes into the music folder. Set the path in `config.local.toml` or with `WJ_MUSIC_PATH`. The repo never contains a personal path. Write-back is a later opt-in feature (SCRUM-16) and is not allowed without that work.
2. **Public repository.** Never commit audio files (`*.flac` and others), databases, cover caches, `config.local.toml`, or personal paths. Check `git status` before every commit. Tests use generated FLAC data only.
3. **Everything is tracked in Jira** (project SCRUM, "WJ Music Tracker" on walterjacobs.atlassian.net). Move a story to In Progress when started and Done when its acceptance criteria and tests pass.
4. **Derived data is rebuildable.** The SQLite DB is a cache built from scanning. Never add something that only exists in the DB without a plan to keep it on rebuild.
5. **Offline first.** No calls to internet services until phase 8 (SCRUM-13) is started and approved.

## Read next
- [ARCHITECTURE.md](ARCHITECTURE.md): layers, data flow, data directory.
- [TECH-STACK.md](TECH-STACK.md): what we use and why.
- [DEVELOPMENT.md](DEVELOPMENT.md): coding standards.
- [FRONTEND.md](FRONTEND.md): UI patterns and responsive rules.
- [API-AUTH.md](API-AUTH.md): authentication (none while local-only).
- [TESTING.md](TESTING.md): how we verify work.
- [GIT-WORKFLOW.md](GIT-WORKFLOW.md): branches, commits, shipping.

## Current phase
Phases 0 to 2 are built (foundation, library scanner, library browsing). Next is phase 3 (lyrics, SCRUM-8). See the epics in Jira SCRUM-5 to SCRUM-16.
