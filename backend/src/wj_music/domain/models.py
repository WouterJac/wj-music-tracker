from dataclasses import dataclass
from pathlib import Path

from wj_music.domain.lyrics import Lyrics


@dataclass(frozen=True)
class TrackTags:
    title: str | None = None
    artist: str | None = None
    albumartist: str | None = None
    album: str | None = None
    tracknumber: str | None = None
    discnumber: str | None = None
    date: str | None = None
    genre: str | None = None
    composer: str | None = None
    label: str | None = None
    lyrics: str | None = None


@dataclass(frozen=True)
class AudioInfo:
    duration_seconds: float
    sample_rate: int
    bit_depth: int
    channels: int
    file_size_bytes: int


@dataclass(frozen=True)
class Picture:
    data: bytes
    mime_type: str


@dataclass(frozen=True)
class FlacFile:
    path: Path
    tags: TrackTags
    audio: AudioInfo
    picture: Picture | None = None
    lyrics: Lyrics | None = None


@dataclass(frozen=True)
class ScannedFile:
    path: Path
    size_bytes: int
    mtime: float
    error: str | None = None
    # Size and mtime of the sidecar .lrc, so editing it triggers a rescan of an unchanged FLAC.
    lyrics_size_bytes: int | None = None
    lyrics_mtime: float | None = None


@dataclass(frozen=True)
class LibraryTotals:
    tracks: int
    albums: int
    artists: int
