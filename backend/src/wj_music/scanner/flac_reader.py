"""Reads Vorbis comments and stream info from a FLAC file. Never writes."""

from pathlib import Path
from typing import Any, cast

from mutagen import MutagenError
from mutagen.flac import FLAC, VCFLACDict

from wj_music.domain.lyrics import resolve_lyrics
from wj_music.domain.models import AudioInfo, FlacFile, Picture, TrackTags
from wj_music.scanner.errors import InvalidFlacError
from wj_music.scanner.lyrics_file import read_sidecar

FRONT_COVER_TYPE = 3


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
    lyrics = resolve_lyrics(
        lyrics=tags.lyrics,
        unsynced=tag("unsyncedlyrics"),
        synced=tag("syncedlyrics"),
        sidecar=read_sidecar(path),
    )
    return FlacFile(
        path=path, tags=tags, audio=audio, picture=_front_cover(flac.pictures), lyrics=lyrics
    )


def _front_cover(pictures: list[Any]) -> Picture | None:
    # Prefer the front cover; fall back to the first embedded picture of any kind.
    if not pictures:
        return None
    chosen = next((p for p in pictures if p.type == FRONT_COVER_TYPE), pictures[0])
    return Picture(data=chosen.data, mime_type=chosen.mime)
