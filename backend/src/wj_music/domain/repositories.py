"""Repository contracts the services depend on. Implementations live in storage."""

from datetime import datetime
from pathlib import Path
from typing import Protocol

from wj_music.domain.facts import Fact
from wj_music.domain.library import (
    AlbumDetail,
    AlbumSummary,
    ArtistDetail,
    ArtistSummary,
    GenreCount,
    LyricsHit,
    Page,
    TrackInfo,
)
from wj_music.domain.models import FlacFile, Picture, ScannedFile
from wj_music.domain.rediscover import AlbumKey
from wj_music.domain.similar import AlbumProfile
from wj_music.domain.stats import LibraryStats


class PairingCodes(Protocol):
    def issue(self, code: str, expires_at: datetime) -> None: ...

    def redeem(self, code: str, now: datetime) -> bool:
        """True if the code is the pending one and not expired. It then cannot be used again."""
        ...


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
        decade: int | None = None,
        genre: str | None = None,
        limit: int,
        offset: int = 0,
    ) -> Page[AlbumSummary]: ...

    def random_albums(
        self, *, count: int, decade: int | None = None, genre: str | None = None
    ) -> list[AlbumSummary]: ...

    def list_genres(self) -> list[GenreCount]: ...

    def albums_by_ids(self, album_ids: list[int]) -> list[AlbumSummary]: ...

    def get_album(self, album_id: int) -> AlbumDetail | None: ...

    def list_artists(
        self, *, query: str | None = None, limit: int, offset: int = 0
    ) -> Page[ArtistSummary]: ...

    def get_artist(self, artist_id: int) -> ArtistDetail | None: ...

    def list_years(self) -> list[int]: ...

    def album_cover_file(self, album_id: int) -> str | None: ...


class TrackReader(Protocol):
    def get_track(self, track_id: int) -> TrackInfo | None: ...

    def search_lyrics(self, query: str, *, limit: int, offset: int = 0) -> Page[LyricsHit]: ...


class StatsReader(Protocol):
    def library_stats(self) -> LibraryStats: ...


class FactsReader(Protocol):
    def facts(self) -> list[Fact]: ...


class ViewHistory(Protocol):
    def record(self, key: AlbumKey, when: datetime) -> None: ...

    def last_viewed(self) -> dict[AlbumKey, datetime]: ...


class SimilarReader(Protocol):
    def album_profiles(self) -> list[AlbumProfile]: ...
