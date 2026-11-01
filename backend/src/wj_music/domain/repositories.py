"""Repository contracts the services depend on. Implementations live in storage."""

from pathlib import Path
from typing import Protocol

from wj_music.domain.models import FlacFile, Picture, ScannedFile


class ScannedFileRepository(Protocol):
    def all(self) -> list[ScannedFile]: ...

    def save(self, scanned: ScannedFile) -> None: ...

    def delete(self, path: Path) -> None: ...


class TrackRepository(Protocol):
    def save(self, flac: FlacFile, cover_file: str | None = None) -> None: ...

    def delete(self, path: Path) -> None: ...

    def prune_orphans(self) -> None: ...


class CoverStore(Protocol):
    def store(self, picture: Picture) -> str:
        """Keep the picture and return the name it can be found under."""
        ...
