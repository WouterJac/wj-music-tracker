"""The access token and the pending pairing code, kept as small files in the data directory."""

import contextlib
import hashlib
import hmac
import json
import os
import secrets
import threading
from datetime import datetime
from pathlib import Path


def load_or_create_token(path: Path) -> str:
    """The access token, generated on first use. Never printed or logged."""
    if path.is_file():
        token = path.read_text(encoding="utf-8").strip()
        if token:
            return token
    path.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    path.write_text(token + "\n", encoding="utf-8")
    # Not every file system has permissions; the data directory is the user's own anyway.
    with contextlib.suppress(OSError):
        os.chmod(path, 0o600)
    return token


def _digest(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


class FilePairingCodes:
    """At most one pending code. Only its hash is stored, and redeeming it uses it up.

    The code is issued by `wj-music pair` and redeemed by the server, which are different
    processes, so it lives in a file.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()

    def issue(self, code: str, expires_at: datetime) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        record = {"hash": _digest(code), "expires_at": expires_at.isoformat()}
        self._path.write_text(json.dumps(record), encoding="utf-8")

    def redeem(self, code: str, now: datetime) -> bool:
        with self._lock:
            record = self._read()
            if record is None:
                return False
            digest, expires_at = record
            if now > expires_at:
                self._path.unlink(missing_ok=True)
                return False
            if not hmac.compare_digest(digest, _digest(code)):
                return False
            self._path.unlink(missing_ok=True)
            return True

    def _read(self) -> tuple[str, datetime] | None:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            return str(raw["hash"]), datetime.fromisoformat(raw["expires_at"])
        except (OSError, ValueError, KeyError, TypeError):
            return None
