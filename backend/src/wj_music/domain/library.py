"""Read models for browsing the library. Immutable, no I/O."""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):  # noqa: UP046  # PEP 695 syntax needs Python 3.12
    items: list[T]
    total: int


@dataclass(frozen=True)
class ArtistSummary:
    id: int
    name: str
    album_count: int


@dataclass(frozen=True)
class AlbumSummary:
    id: int
    title: str
    artist_id: int | None
    artist_name: str | None
    year: int | None
    track_count: int
    has_cover: bool


@dataclass(frozen=True)
class TrackDetail:
    id: int
    disc: int | None
    number: int | None
    title: str | None
    duration_seconds: float
    sample_rate: int
    bit_depth: int
    channels: int
    has_lyrics: bool = False


@dataclass(frozen=True)
class AlbumDetail:
    summary: AlbumSummary
    tracks: list[TrackDetail]

    @property
    def total_duration_seconds(self) -> float:
        return round(sum(track.duration_seconds for track in self.tracks), 3)


@dataclass(frozen=True)
class TrackInfo:
    id: int
    title: str | None
    disc: int | None
    number: int | None
    duration_seconds: float
    sample_rate: int
    bit_depth: int
    channels: int
    album_id: int | None
    album_title: str | None
    artist_id: int | None
    artist_name: str | None
    album_has_cover: bool
    plain_lyrics: str | None
    synced_lrc: str | None


@dataclass(frozen=True)
class LyricsHit:
    track_id: int
    title: str | None
    album_id: int | None
    album_title: str | None
    artist_id: int | None
    artist_name: str | None
    snippet: str


@dataclass(frozen=True)
class ArtistDetail:
    id: int
    name: str
    albums: list[AlbumSummary]


def year_from_date(date: str | None) -> int | None:
    """Tags hold dates like "1977" or "1977-01-14". The year is the leading four digits."""
    if date is not None and len(date) >= 4 and date[:4].isdigit():
        return int(date[:4])
    return None


def leading_int(text: str | None) -> int | None:
    """Track and disc tags are free text such as "3" or "3/12". Take the leading number."""
    if text is None:
        return None
    digits = ""
    for char in text.strip():
        if not char.isdigit():
            break
        digits += char
    return int(digits) if digits else None
