# Development standards

## General
- Small, focused modules and functions. Split when a file grows past about 300 lines or a function does more than one job.
- Name things for what they are in the music domain: `Album`, `Track`, `AudioInfo`, not `Item` or `Data`.
- Match the comment density and style of the surrounding code. Comment the *why*, not the *what*.
- No dead code, no commented-out code, no speculative abstractions. Build what the current phase needs.
- Errors: raise typed exceptions from the layer that detects the problem. Never swallow an error silently. Log and record per-file scan errors and continue.
- Logging: use the standard `logging` module, one logger per module (`logging.getLogger(__name__)`).

## Python (backend)
- Python 3.11+ syntax. Type hints on every public function. `mypy --strict` for `domain` and `services`.
- `ruff` for linting and formatting. Config lives in `backend/pyproject.toml`.
- Domain objects are immutable (`dataclass(frozen=True)`), with no I/O imports.
- Services take repository interfaces as constructor arguments. No module-level state.
- FastAPI routes only call services and map results to Pydantic response models.
- Never read the music folder from the API layer. Only the scanner touches files.

## TypeScript (frontend)
- `strict` mode in `tsconfig`. No `any`. Use `unknown` and narrow.
- Functional components with hooks. One component per file for anything non-trivial.
- API types come from the backend OpenAPI schema, not hand-copied where avoidable.
- Server data via TanStack Query. No copying server data into local state.

## Naming
- Python: `snake_case` functions and modules, `PascalCase` classes.
- TypeScript: `camelCase` functions and variables, `PascalCase` components and types.
- Files: `snake_case.py`, `PascalCase.tsx` for components.

## Configuration
- Nothing hard-coded that a user might change: music path, data directory, port.
- Personal values live in `config.local.toml`, which is gitignored. Committed defaults live in `config.example.toml`.
