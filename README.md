# WJ Music Tracker

A local web app to explore and analyse a FLAC music collection: albums, artists, statistics, metadata, lyrics and interesting facts. Recommendations follow in later phases.

**Status:** Phases 6 (explore) and 7 (offline recommendations) are done, with phase 5 (interesting facts) and phase 4 (statistics) before them: scan your library, then browse albums and artists, read embedded or `.lrc` lyrics, search them, see statistics (decades, formats, hi-res share, top artists), read facts about your collection, shuffle random albums, browse by decade and genre, and see similar albums on each album page. Planning and tracking live in Jira (project SCRUM).

## Principles
- Your music stays on your machine. The app only reads your FLAC files.
- Offline first. Online enrichment is optional and comes later.

## Setup
Requirements: Python 3.11+, Node.js 20+.

1. Copy `config.example.toml` to `config.local.toml` and set `music_path` to your FLAC folder. You can also set the `WJ_MUSIC_PATH` environment variable.
2. Backend: `cd backend`, `python -m venv .venv`, `.venv\Scripts\activate`, `pip install -e ".[dev]"`. Then `wj-music scan` reads your music folder into the library database (re-run it any time, unchanged files are skipped) and `wj-music serve` starts the API on http://127.0.0.1:8000.
3. Frontend: `cd frontend`, `npm install`, then `npm run dev` (with the backend running) and open http://127.0.0.1:5173.
4. Tests: `cd backend && pytest`, and `cd frontend && npm test`.

## Documentation
- [CLAUDE.md](CLAUDE.md): master instructions for contributors and tools
- [ARCHITECTURE.md](ARCHITECTURE.md), [TECH-STACK.md](TECH-STACK.md), [DEVELOPMENT.md](DEVELOPMENT.md)
- [FRONTEND.md](FRONTEND.md), [API-AUTH.md](API-AUTH.md), [TESTING.md](TESTING.md), [GIT-WORKFLOW.md](GIT-WORKFLOW.md)

## License
To be decided (MIT proposed).
