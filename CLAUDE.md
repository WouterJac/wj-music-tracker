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

## Current status
Phases 0 to 4 are built: foundation, library scanner, library browsing, lyrics, statistics dashboard. Nothing past phase 4 exists yet. The next phase is the next open epic in Jira (SCRUM-5 to SCRUM-16). Ask the user before starting it.

**Git state (check with `git log` and `gh pr list` first, this may be stale).** PRs #7 to #14 were merged into their parent branches instead of `main`, so `main` only had #6. PR #16 (branch `SCRUM-34-stats-ui`, base `main`) carries phases 2 to 4 and is waiting for the user to review and merge it. Until it is merged, start new branches from `SCRUM-34-stats-ui`. After it is merged, branch from `main`. One branch per story. Never merge or approve PRs yourself: the user reviews and merges.

**What exists**
- Backend (`backend/src/wj_music/`): `domain`, `scanner`, `storage` (SQLite, Alembic migrations 0001 to 0003), `services`, `api`, composition root `bootstrap.py`, Typer CLI `wj-music scan|serve`.
- API: `/health`, `/api/albums`, `/api/albums/{id}`, `/api/albums/{id}/cover`, `/api/artists`, `/api/artists/{id}`, `/api/years`, `/api/tracks/{id}`, `/api/lyrics/search`, `/api/stats`.
- Frontend (`frontend/src/`): pages Albums, Artists, album/artist/track detail, Lyrics search, Statistics (`/stats`). Shared pieces: `QueryState` (loading/error/empty/not-found), `Skeleton`, `Pagination`, `SearchBox`, `BarChart`.
- Last verified: backend 279 tests, frontend 113 tests, ruff, mypy strict, eslint, tsc, prettier, build all clean.

**Run it (Windows PowerShell)**
- Backend: `cd backend`, then `.venv\Scripts\wj-music scan`, then `.venv\Scripts\wj-music serve` (port 8000).
- Frontend: `cd frontend`, then `npm.cmd run dev` (port 5173; `npm` itself is blocked by the execution policy, so use `npm.cmd`).
- Checks: `ruff check`, `ruff format --check`, `mypy src tests`, `pytest` in `backend`; `npx eslint .`, `npx tsc -b`, `npx prettier --check src`, `npx vitest run`, `npm run build` in `frontend`.

**Gotchas**
- The user's real `config.local.toml` has an invalid unescaped Windows path. It is the user's file: do not edit it. For browser checks use a scratch config outside the repo with `serve --config <file>` and forward slashes. A bad config file wins over `WJ_MUSIC_PATH`.
- The cache DB lives in `%LOCALAPPDATA%\WJMusicTracker`. Migration 0003 clears it, so rescan after upgrading. The real library scans in about 14 s (198 tracks, 16 albums, 4 artists).
- Working-tree files are CRLF. Python edit scripts must normalise `\r\n` to `\n` before multi-line replaces and assert the old text is present. The bash tool mangles large heredocs and backslashes: write files with the Write tool and keep scripts in a file.
- `tsc -b` creates `frontend/tsconfig.tsbuildinfo`. Do not commit it.
- Dev servers started for browser checks must be stopped afterwards (ports 5173 and 8000).

**Workflow**
- Test-first. Commit messages start `SCRUM-<n>: ` and end with the Co-Authored-By trailer. PR bodies end with the Claude Code line. Move Jira stories to In Progress when started and Done when acceptance criteria and tests pass; create child stories under the epic first.
- Check the UI in the browser at 390px and desktop, light and dark, with 44px touch targets, before calling UI work done.

**Known gaps**
- No Playwright end-to-end tests yet (planned in TECH-STACK.md). Screenshots are not attached to Jira.
- Artists only appear if they have at least one album. Lyrics search is ASCII case-insensitive and a phrase must sit within one line. 11 `.lrc` files in the real library have no matching FLAC and are ignored.
