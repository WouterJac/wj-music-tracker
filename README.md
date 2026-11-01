# WJ Music Tracker

A local web app to explore and analyse a FLAC music collection: albums, artists, statistics, metadata, lyrics and interesting facts. Recommendations follow in later phases.

**Status:** Phase 0 (foundation). Planning and tracking live in Jira (project SCRUM).

## Principles
- Your music stays on your machine. The app only reads your FLAC files.
- Offline first. Online enrichment is optional and comes later.

## Setup
Requirements: Python 3.11+, Node.js 20+.

1. Copy `config.example.toml` to `config.local.toml` and set `music_path` to your FLAC folder. You can also set the `WJ_MUSIC_PATH` environment variable.
2. Backend: `cd backend`, `python -m venv .venv`, `.venv\Scriptsctivate`, `pip install -e ".[dev]"`, then `uvicorn wj_music.api.app:create_app --factory --port 8000`.
3. Frontend: `cd frontend`, `npm install`, then `npm run dev` and open http://127.0.0.1:5173.
4. Tests: `cd backend && pytest`, and `cd frontend && npm test`.

## Documentation
- [CLAUDE.md](CLAUDE.md): master instructions for contributors and tools
- [ARCHITECTURE.md](ARCHITECTURE.md), [TECH-STACK.md](TECH-STACK.md), [DEVELOPMENT.md](DEVELOPMENT.md)
- [FRONTEND.md](FRONTEND.md), [API-AUTH.md](API-AUTH.md), [TESTING.md](TESTING.md), [GIT-WORKFLOW.md](GIT-WORKFLOW.md)

## License
To be decided (MIT proposed).
