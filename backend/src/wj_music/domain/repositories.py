"""Repository contracts the services depend on. Implementations live in storage."""

from pathlib import Path
from typing import Protocol

from wj_music.domain.library import (
    AlbumDetail,
    AlbumSummary,
    ArtistDetail,
    ArtistSummary,
    Page,
)
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


class LibraryReader(Protocol):
    def list_albums(
        self,
        *,
        query: str | None = None,
        artist_id: int | None = None,
        year: int | None = None,
        limit: int,
        offset: int = 0,
    ) -> Page[AlbumSummary]: ...

    def get_album(self, album_id: int) -> AlbumDetail | None: ...

    def list_artists(
        self, *, query: str | None = None, limit: int, offset: int = 0
    ) -> Page[ArtistSummary]: ...

    def get_artist(self, artist_id: int) -> ArtistDetail | None: ...

    def list_years(self) -> list[int]: ...

    def album_cover_file(self, album_id: int) -> str | None: ...
