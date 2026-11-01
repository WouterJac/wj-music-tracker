"""Lyrics rules: LRC parsing and choosing between embedded and sidecar sources. No I/O."""

import re
from dataclasses import dataclass

# [mm:ss], [mm:ss.x] up to three fraction digits. Minutes may pass 59 for long tracks.
TIMESTAMP = re.compile(r"\[(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?\]")
METADATA = re.compile(r"^\[([A-Za-z#]+):([^\]]*)\]$")
WORD_TIMING = re.compile(r"<\d{1,3}:\d{2}(?:[.:]\d{1,3})?>")


@dataclass(frozen=True)
class LyricLine:
    time_seconds: float
    text: str


@dataclass(frozen=True)
class Lyrics:
    """plain is always set when a track has lyrics (search uses it); synced_lrc is the raw LRC."""

    plain: str | None
    synced_lrc: str | None


def has_timestamps(text: str) -> bool:
    return TIMESTAMP.search(text) is not None


def parse_lrc(text: str) -> list[LyricLine]:
    offset_seconds = 0.0
    parsed: list[LyricLine] = []
    for raw in text.splitlines():
        line = raw.strip()
        metadata = METADATA.match(line)
        if metadata:
            if metadata.group(1).lower() == "offset":
                offset_seconds = _offset_seconds(metadata.group(2))
            continue
        stamps: list[float] = []
        position = 0
        while match := TIMESTAMP.match(line, position):
            stamps.append(_seconds(match))
            position = match.end()
        if not stamps:
            continue
        lyric = WORD_TIMING.sub("", line[position:]).strip()
        parsed.extend(LyricLine(seconds, lyric) for seconds in stamps)
    # A positive LRC offset means the lyrics should appear earlier.
    shifted = [
        LyricLine(max(0.0, line.time_seconds - offset_seconds), line.text) for line in parsed
    ]
    return sorted(shifted, key=lambda line: line.time_seconds)


def lrc_to_plain(text: str) -> str:
    return "\n".join(line.text for line in parse_lrc(text)).strip()


def resolve_lyrics(
    *,
    lyrics: str | None,
    unsynced: str | None,
    synced: str | None,
    sidecar: str | None,
) -> Lyrics | None:
    """Combine every source. Embedded tags win over the sidecar for each kind of lyrics."""
    cleaned = [_clean(source) for source in (lyrics, unsynced, synced, sidecar)]
    lyrics_tag, unsynced_tag, synced_tag, sidecar_text = cleaned

    synced_lrc = next(
        (t for t in (synced_tag, lyrics_tag, sidecar_text) if t and has_timestamps(t)), None
    )
    plain = next(
        (
            t
            for t in (unsynced_tag, lyrics_tag, sidecar_text, synced_tag)
            if t and not has_timestamps(t)
        ),
        None,
    )
    if plain is None and synced_lrc is not None:
        plain = lrc_to_plain(synced_lrc) or None
    if plain is None and synced_lrc is None:
        return None
    return Lyrics(plain=plain, synced_lrc=synced_lrc)


def _clean(text: str | None) -> str | None:
    if not text:
        return None
    unified = text.replace("\r\n", "\n").replace("\r", "\n")
    return unified.strip() or None


def _seconds(match: re.Match[str]) -> float:
    minutes, seconds, fraction = match.groups()
    return (
        int(minutes) * 60 + int(seconds) + (int(fraction) / 10 ** len(fraction) if fraction else 0)
    )


def _offset_seconds(value: str) -> float:
    try:
        return int(value.strip()) / 1000
    except ValueError:
        return 0.0
