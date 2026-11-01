# API and authentication

## Current state (phases 0 to 9)
- The app is local only. The server binds to `127.0.0.1` by default, so only this PC can reach it.
- No authentication. The API is not reachable from other machines.
- The server must refuse to bind to `0.0.0.0` unless a future phase explicitly enables it.

## Planned for phone access (phase 10, SCRUM-15)
Decision recorded now so it is not made under pressure later.
- Access over the home network or Tailscale. Never the public internet directly.
- Single-user token auth: a long random token generated on first run and stored in the data directory. Sent as `Authorization: Bearer <token>`.
- Token is never placed in URLs, logs or the repo.
- Tokens compared with a constant-time comparison.
- The phone stores the token in secure browser storage after a one-time pairing step (for example scanning a QR code shown on the PC).
- Rate limit failed auth attempts.

## Rules for every endpoint
- Responses never include file system paths outside the library's own relative paths.
- Responses never include the cover cache path or DB path.
- Input is validated by Pydantic models. Query parameters for paging have upper bounds.
