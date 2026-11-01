"""Reads Vorbis comments and stream info from a FLAC file. Never writes."""

from pathlib import Path
from typing import cast

from mutagen import MutagenError
from mutagen.flac import FLAC, VCFLACDict

from wj_music.domain.models import AudioInfo, FlacFile, TrackTags
from wj_music.scanner.errors import InvalidFlacError


def read_flac(path: Path) -> FlacFile:
    with path.open("rb") as handle:
        try:
            flac = FLAC(handle)  # type: ignore[no-untyped-call]  # mutagen's constructor is untyped
        except MutagenError as exc:
            raise InvalidFlacError(path) from exc

    comments: dict[str, list[str]] = {}
    if isinstance(flac.tags, VCFLACDict):
        # mutagen's VCFLACDict holds a list of strings per key but has no type stubs.
        comments = cast("dict[str, list[str]]", flac.tags)

    def tag(key: str) -> str | None:
        values = comments.get(key)
        return values[0] if values else None

    tags = TrackTags(
        title=tag("title"),
        artist=tag("artist"),
        albumartist=tag("albumartist"),
        album=tag("album"),
        tracknumber=tag("tracknumber"),
        discnumber=tag("discnumber"),
        date=tag("date"),
        genre=tag("genre"),
        composer=tag("composer"),
        label=tag("label"),
        lyrics=tag("lyrics"),
    )
    audio = AudioInfo(
        duration_seconds=flac.info.length,
        sample_rate=flac.info.sample_rate,
        bit_depth=flac.info.bits_per_sample,
        channels=flac.info.channels,
        file_size_bytes=path.stat().st_size,
    )
    return FlacFile(path=path, tags=tags, audio=audio)
