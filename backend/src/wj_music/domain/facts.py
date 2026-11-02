"""Interesting facts about the collection. Pure rules over per-track data, no database."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Literal

from wj_music.domain.library import year_from_date

MIN_COMPILATION_ARTISTS = 3
MIN_GENRES = 2


@dataclass(frozen=True)
class FactTrack:
    """What the facts need to know about one track."""

    track_id: int
    title: str | None
    album_id: int | None
    album_title: str | None
    album_date: str | None
    artist_id: int | None
    artist_name: str | None
    disc: int | None
    genre: str | None
    duration_seconds: float


@dataclass(frozen=True)
class FactLink:
    kind: Literal["album", "artist", "track"]
    id: int


@dataclass(frozen=True)
class Fact:
    key: str
    title: str
    text: str
    link: FactLink


@dataclass
class _Album:
    id: int
    title: str
    date: str | None
    tracks: list[FactTrack] = field(default_factory=list)

    @property
    def seconds(self) -> float:
        return sum(t.duration_seconds for t in self.tracks)

    @property
    def year(self) -> int | None:
        return year_from_date(self.date)

    @property
    def label(self) -> str:
        """The title, with the artist when the whole album is by one."""
        names = {t.artist_name for t in self.tracks if t.artist_name}
        return f"{self.title} by {next(iter(names))}" if len(names) == 1 else self.title

    @property
    def discs(self) -> int:
        return len({t.disc for t in self.tracks if t.disc is not None})

    @property
    def genres(self) -> list[str]:
        return sorted({g for t in self.tracks if t.genre and (g := t.genre.strip())})

    @property
    def artist_count(self) -> int:
        return len({t.artist_id for t in self.tracks if t.artist_id is not None})


def build_facts(tracks: Iterable[FactTrack]) -> list[Fact]:
    rows = list(tracks)
    albums = _group_albums(rows)
    builders: list[Callable[[list[_Album], list[FactTrack]], Fact | None]] = [
        _longest_album,
        _shortest_album,
        _oldest_release,
        _newest_release,
        _most_tracks,
        _longest_track,
        _multi_disc,
        _genre_spread,
        _most_artists,
    ]
    facts = (build(albums, rows) for build in builders)
    return [fact for fact in facts if fact is not None]


def _group_albums(rows: list[FactTrack]) -> list[_Album]:
    grouped: dict[int, _Album] = {}
    for row in rows:
        if row.album_id is None:
            continue
        album = grouped.setdefault(
            row.album_id,
            _Album(row.album_id, row.album_title or "Unknown album", row.album_date),
        )
        album.tracks.append(row)
    return list(grouped.values())


def _album_fact(key: str, title: str, album: _Album, text: str) -> Fact:
    return Fact(key=key, title=title, text=text, link=FactLink("album", album.id))


def _duration(seconds: float) -> str:
    minutes = max(1, round(seconds / 60))
    hours, rest = divmod(minutes, 60)
    if hours == 0:
        return f"{minutes} min"
    return f"{hours} h" if rest == 0 else f"{hours} h {rest} min"


def _longest_album(albums: list[_Album], _rows: list[FactTrack]) -> Fact | None:
    if len(albums) < 2:
        return None
    album = min(albums, key=lambda a: (-a.seconds, a.title))
    return _album_fact(
        "longest_album", "Longest album", album, f"{album.label} runs {_duration(album.seconds)}."
    )


def _shortest_album(albums: list[_Album], _rows: list[FactTrack]) -> Fact | None:
    if len(albums) < 2:
        return None
    album = min(albums, key=lambda a: (a.seconds, a.title))
    return _album_fact(
        "shortest_album",
        "Shortest album",
        album,
        f"{album.label} runs {_duration(album.seconds)}.",
    )


def _dated(albums: list[_Album]) -> list[_Album]:
    return [album for album in albums if album.year is not None]


def _year_span(albums: list[_Album]) -> bool:
    return len({album.year for album in _dated(albums)}) >= 2


def _oldest_release(albums: list[_Album], _rows: list[FactTrack]) -> Fact | None:
    if not _year_span(albums):
        return None
    album = min(_dated(albums), key=lambda a: (a.year or 0, a.title))
    return _album_fact(
        "oldest_release", "Oldest release", album, f"{album.label} came out in {album.year}."
    )


def _newest_release(albums: list[_Album], _rows: list[FactTrack]) -> Fact | None:
    if not _year_span(albums):
        return None
    album = min(_dated(albums), key=lambda a: (-(a.year or 0), a.title))
    return _album_fact(
        "newest_release", "Newest release", album, f"{album.label} came out in {album.year}."
    )


def _most_tracks(albums: list[_Album], _rows: list[FactTrack]) -> Fact | None:
    if len(albums) < 2:
        return None
    album = min(albums, key=lambda a: (-len(a.tracks), a.title))
    return _album_fact(
        "most_tracks", "Most tracks", album, f"{album.label} has {len(album.tracks)} tracks."
    )


def _longest_track(_albums: list[_Album], rows: list[FactTrack]) -> Fact | None:
    if len(rows) < 2:
        return None
    row = min(rows, key=lambda r: (-r.duration_seconds, r.track_id))
    name = f"“{row.title or 'Untitled track'}”"
    place = f" on {row.album_title}" if row.album_title else ""
    return Fact(
        key="longest_track",
        title="Longest track",
        text=f"{name}{place} lasts {_duration(row.duration_seconds)}.",
        link=FactLink("track", row.track_id),
    )


def _multi_disc(albums: list[_Album], _rows: list[FactTrack]) -> Fact | None:
    multi = [album for album in albums if album.discs > 1]
    if not multi:
        return None
    top = min(multi, key=lambda a: (-a.discs, a.title))
    if len(multi) == 1:
        text = f"{top.label} spans {top.discs} discs."
    else:
        text = f"{len(multi)} albums span more than one disc. {top.label} has {top.discs}."
    return _album_fact("multi_disc", "Multi-disc albums", top, text)


def _genre_spread(albums: list[_Album], _rows: list[FactTrack]) -> Fact | None:
    wide = [album for album in albums if len(album.genres) >= MIN_GENRES]
    if not wide:
        return None
    top = min(wide, key=lambda a: (-len(a.genres), a.title))
    names = top.genres
    listed = f"{', '.join(names[:-1])} and {names[-1]}"
    return _album_fact(
        "genre_spread",
        "Widest genre spread",
        top,
        f"{top.label} mixes {len(names)} genres: {listed}.",
    )


def _most_artists(albums: list[_Album], _rows: list[FactTrack]) -> Fact | None:
    crowded = [album for album in albums if album.artist_count >= MIN_COMPILATION_ARTISTS]
    if not crowded:
        return None
    top = min(crowded, key=lambda a: (-a.artist_count, a.title))
    return _album_fact(
        "most_artists",
        "Most artists on one album",
        top,
        f"{top.label} features {top.artist_count} different artists.",
    )
