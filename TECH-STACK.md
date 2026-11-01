# Tech stack

| Area | Choice | Why |
|---|---|---|
| Language (backend) | Python 3.11+ | Best audio-metadata tooling. Target version pending decision. |
| FLAC tags | mutagen | Mature library for Vorbis comments, pictures and stream info. |
| Web API | FastAPI + Pydantic v2 | Typed, fast to write, generates OpenAPI for the frontend. |
| Database | SQLite | No server, easy to back up and inspect. Fits a single-user cache. |
| ORM and migrations | SQLAlchemy 2.x, Alembic | Explicit schema, versioned migrations. |
| CLI | Typer | Simple typed commands for `scan` and `serve`. |
| Frontend | React + Vite + TypeScript | Mainstream, good ecosystem, PWA-ready later. |
| Server state | TanStack Query | Caching, loading and error states for API data. |
| Charts (phase 4) | Chosen per dataviz guidance | Accessible, works in both themes. |
| Backend tests | pytest, pytest-cov | Standard, good fixtures. |
| Backend lint and types | ruff, mypy | Fast lint and strict typing on domain and services. |
| Frontend tests | Vitest, Testing Library | Native to Vite, component-level tests. |
| End-to-end tests | Playwright (from phase 2) | Real browser checks, including phone-width viewport. |
| Frontend lint | ESLint, Prettier | Consistent formatting and common errors. |

## Deliberately not used (for now)
- **Docker:** not needed for a single local app. Revisit if phone hosting needs it.
- **Cloud services:** the music never leaves the machine.
- **Heavy frontend frameworks (Next.js, Redux):** the app is a local SPA. Not needed.
