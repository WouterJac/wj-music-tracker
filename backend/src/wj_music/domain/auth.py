"""Rules for remote access: pairing codes and limiting repeated failures. No I/O."""

import secrets
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta

# Without 0, 1, O, I and L, so a code read off a screen cannot be mistyped.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8


def new_pairing_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def format_code(code: str) -> str:
    half = len(code) // 2
    return f"{code[:half]}-{code[half:]}"


def normalise_code(text: str) -> str:
    """The code as typed by hand: any case, with spaces or a dash between the groups."""
    return "".join(ch for ch in text.upper() if ch not in " -")


class FailureLimiter:
    """Blocks a client that fails too often within a time window."""

    def __init__(self, max_failures: int, window: timedelta) -> None:
        self._max_failures = max_failures
        self._window = window
        self._failures: defaultdict[str, deque[datetime]] = defaultdict(deque)
        self._lock = threading.Lock()

    def is_blocked(self, key: str, now: datetime) -> bool:
        with self._lock:
            return self._prune(key, now) >= self._max_failures

    def record_failure(self, key: str, now: datetime) -> None:
        with self._lock:
            self._prune(key, now)
            self._failures[key].append(now)

    def _prune(self, key: str, now: datetime) -> int:
        """Forgets failures older than the window and returns how many are left."""
        failures = self._failures.get(key)
        if failures is None:
            return 0
        while failures and now - failures[0] > self._window:
            failures.popleft()
        if not failures:
            # Keeps the table from growing with every address that ever failed once.
            del self._failures[key]
        return len(failures)
