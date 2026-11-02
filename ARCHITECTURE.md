# Architecture

## Overview
```
FLAC folder (read-only)
      │  scanner (mutagen)
      ▼
SQLite database  ◄── repositories (storage)
      │
      ▼
services (library, stats, facts, explore, recommendations)
      │
      ▼
FastAPI (api)  ── JSON ──►  React PWA (frontend)  ── browser on the PC
```

## Layers and dependency direction
Dependencies point inward only.

| Layer | Package | May depend on | Notes |
|---|---|---|---|
| Domain | `wj_music.domain` | nothing | Pure models and rules. No I/O. |
| Scanner | `wj_music.scanner` | domain | Reads files. Returns domain objects. |
| Storage | `wj_music.storage` | domain | SQLAlchemy models, repositories, migrations. |
| Services | `wj_music.services` | domain, storage interfaces | Business logic. Never imports FastAPI. |
| API | `wj_music.api` | services | Translates HTTP to service calls and back. Thin. |
| CLI | `wj_music.cli` | services, bootstrap | `wj-music scan`, `wj-music serve`. |
| Composition root | `wj_music.bootstrap` | everything | Wires settings to storage, scanner and services. The only place that knows concrete classes. |

## Data flow
1. **Scan:** the scanner walks the music folder, reads each `.flac`, and produces domain objects. `scan_library` stores them through the repository contracts in `domain`.
2. **Incremental:** a scanned file is skipped when its path, size and mtime match the stored record. Deleted files are removed from the DB, and albums or artists left without tracks are pruned. A sidecar `.lrc` next to a FLAC counts as part of that file: adding, editing or removing it rescans the track. A missing music folder aborts the scan, so an unplugged drive never empties the library.
3. **Serve:** the API reads through services only. Services read from the DB, never from the music folder.

## Data directory
Outside the repo and the music folder. Default `%LOCALAPPDATA%\WJMusicTracker\` (configurable):
- `library.db`: SQLite database (rebuildable cache).
- `user.db`: SQLite database with album view history for rediscover. Not a cache: scans and cache resets never touch it.
- `covers/`: extracted cover art, named by content hash.
- Later: `enrichment/` for cached online data (phase 8).

## Key decisions
Each decision gets an ADR in `docs/` (for example `docs/0001-python-react-stack.md`). Decisions so far:
- Local-only by default: bound to localhost with no auth. Phone access is opt-in with token auth (see [API-AUTH.md](API-AUTH.md)).
- Python backend and React PWA frontend.
- Read-only access to the music folder.
- Rebuildable SQLite cache.
- Offline first. Online enrichment is opt-in and comes later.
