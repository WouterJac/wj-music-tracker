"""Scan use case: runs a library scan on request, one at a time."""

import threading
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ScanSummary:
    added: int
    changed: int
    removed: int
    unchanged: int
    errors: int
    tracks: int
    albums: int
    artists: int


class ScanAlreadyRunningError(Exception):
    """A scan was requested while another one is still running."""


class ScanUnavailableError(Exception):
    """The scan cannot run, for example no music folder is set or the folder is not there."""


class ScanService:
    def __init__(self, run: Callable[[], ScanSummary]) -> None:
        self._run = run
        self._lock = threading.Lock()

    def scan(self) -> ScanSummary:
        if not self._lock.acquire(blocking=False):
            raise ScanAlreadyRunningError
        try:
            return self._run()
        finally:
            self._lock.release()
