from dataclasses import dataclass
from pathlib import Path


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
class FlacFile:
    path: Path
    tags: TrackTags
    audio: AudioInfo
