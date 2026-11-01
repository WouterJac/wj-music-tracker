# Testing

## Principles
- A story is Done only when its acceptance criteria are verified by tests or a recorded manual check.
- Tests never use real music from the library. Fixtures are generated in code.
- Tests run offline and without the user's music folder.

## Layers
| Layer | Tool | What it covers |
|---|---|---|
| Unit (domain, services) | pytest | Pure logic: stats, facts, filters. Fast. |
| Integration (scanner, storage) | pytest + temp dirs + in-memory or temp SQLite | Real file reads on generated FLAC files, migrations, repositories. |
| API | pytest + FastAPI TestClient | Each endpoint: status codes, shapes, paging bounds, error responses. |
| Frontend components | Vitest + Testing Library | Rendering of loading, empty, error and success states. |
| End-to-end | Playwright | Main user flows, at desktop and phone widths. |

## Fixtures
- A test helper builds minimal valid FLAC streams in code: a STREAMINFO block (sample rate, bit depth, channels, length) and a VORBIS_COMMENT block (tags). Optionally a PICTURE block for cover art.
- A fixture folder is created in a temp directory per test. Example: two albums, one with a deleted track, one malformed file.
- No binary audio is committed. The generated files are small (a few KB).

## Coverage targets
- Domain and services: 90% or more line coverage.
- Scanner and storage: 85% or more.
- Frontend: component tests for every data view.
Coverage is a guide. The acceptance criteria matter more.

## Before a story is Done
1. Backend: `pytest`, `ruff check`, `ruff format --check`, `mypy` pass.
2. Frontend: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.
3. UI stories: screenshots checked at phone and desktop widths.
4. Manual check where a test cannot cover it (for example a real scan of the library), with the result noted in the Jira story.

## Test-first (TDD)
Required wherever a test can express the behaviour. Skip it only for pure configuration or scaffolding with no behaviour (for example `pyproject.toml`, `tsconfig.json`).
1. Write the failing test first. Run it and confirm it fails for the right reason (a missing function, a wrong value), not a typo or import error that hides the behaviour.
2. Write the smallest code that makes it pass.
3. Run the full checks for the layer. Only then continue with more code.
Do not write feature code unless the relevant tests pass. Refactor only with the tests green.

## Running tests
- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm test`
