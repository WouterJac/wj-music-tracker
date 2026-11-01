"""Repository contracts the services depend on. Implementations live in storage."""

from pathlib import Path
from typing import Protocol

from wj_music.domain.models import FlacFile, ScannedFile


class ScannedFileRepository(Protocol):
    def all(self) -> list[ScannedFile]: ...

    def save(self, scanned: ScannedFile) -> None: ...

    def delete(self, path: Path) -> None: ...


class TrackRepository(Protocol):
    def save(self, flac: FlacFile) -> None: ...

    def delete(self, path: Path) -> None: ...
