# API and authentication

## Current state
- By default the app is local only. The server binds to `127.0.0.1`, so only this PC can reach it, and there is no authentication.
- The server refuses any non-loopback `server.host` unless `server.allow_remote = true` is set in `config.local.toml`.
- With `allow_remote = true` (phone access, phase 10, SCRUM-15) every `/api` request needs the access token. `/health` and the frontend files stay open.

## Remote access (opt-in)
- Intended for the home network or Tailscale. Never expose the port to the public internet directly.
- Single-user token auth. A long random token is generated on first run and stored in `auth_token` in the data directory. It is sent as `Authorization: Bearer <token>`.
- The token is never placed in URLs, logs or the repo. It is compared in constant time.
- Pairing: `wj-music pair` prints a one-time code (8 characters, valid 5 minutes, works once). The phone sends it to `POST /api/pair` and receives the token in the response, then keeps it in browser storage. Only a hash of the code is stored (`pairing.json` in the data directory).
- Failed attempts are rate limited per client address: 10 wrong tokens or wrong codes within 60 seconds give `429` until the window passes. Requests with no token at all are answered `401` and not counted, so an app that has not paired yet cannot lock itself out.
- Responses carry no token except the one-time pairing response.

## Rules for every endpoint
- Responses never include file system paths outside the library's own relative paths.
- Responses never include the cover cache path or DB path.
- Input is validated by Pydantic models. Query parameters for paging have upper bounds.
