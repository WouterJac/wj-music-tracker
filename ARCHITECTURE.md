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
| CLI | `wj_music.cli` | services | `wj-music scan`, `wj-music serve`. |

## Data flow
1. **Scan:** the scanner walks the music folder, reads each `.flac`, and produces domain objects. The library service stores them via repositories.
2. **Incremental:** a scanned file is skipped when its path, size and mtime match the stored record. Deleted files are removed from the DB.
3. **Serve:** the API reads through services only. Services read from the DB, never from the music folder.

## Data directory
Outside the repo and the music folder. Default `%LOCALAPPDATA%\WJMusicTracker\` (configurable):
- `library.db`: SQLite database (rebuildable cache).
- `covers/`: extracted cover art, named by content hash.
- Later: `enrichment/` for cached online data (phase 8).

## Key decisions
Each decision gets an ADR in `docs/` (for example `docs/0001-python-react-stack.md`). Decisions so far:
- Local-only app, no auth, bound to localhost (see [API-AUTH.md](API-AUTH.md)).
- Python backend and React PWA frontend.
- Read-only access to the music folder.
- Rebuildable SQLite cache.
- Offline first. Online enrichment is opt-in and comes later.
