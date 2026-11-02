"""Library statistics. Pure functions over per-track facts, testable without a database."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from wj_music.domain.library import year_from_date

TOP_ARTISTS = 10
HIRES_MIN_BIT_DEPTH = 17
HIRES_MIN_SAMPLE_RATE = 48001

# (upper bound exclusive, label) in natural order; the last label has no bound.
_TRACK_COUNT_BUCKETS = [
    (6, "1–5 tracks"),
    (11, "6–10 tracks"),
    (16, "11–15 tracks"),
    (21, "16–20 tracks"),
]
_TRACK_COUNT_LAST = "21+ tracks"
_LENGTH_BUCKETS = [(20, "Under 20 min"), (40, "20–40 min"), (60, "40–60 min"), (80, "60–80 min")]
_LENGTH_LAST = "80+ min"


@dataclass(frozen=True)
class TrackFacts:
    """What the statistics need to know about one track."""

    album_id: int | None
    album_date: str | None
    artist_id: int | None
    artist_name: str | None
    genre: str | None
    duration_seconds: float
    sample_rate: int
    bit_depth: int
    channels: int


@dataclass(frozen=True)
class Bucket:
    label: str
    count: int


@dataclass(frozen=True)
class ArtistCount:
    id: int
    name: str
    tracks: int
    albums: int


@dataclass(frozen=True)
class LibraryStats:
    tracks: int
    albums: int
    artists: int
    total_duration_seconds: float
    hires_tracks: int
    albums_by_decade: list[Bucket]
    albums_by_year: list[Bucket]
    tracks_by_format: list[Bucket]
    tracks_by_channels: list[Bucket]
    tracks_by_genre: list[Bucket]
    albums_by_track_count: list[Bucket]
    albums_by_length: list[Bucket]
    top_artists: list[ArtistCount]


def build_stats(facts: Iterable[TrackFacts]) -> LibraryStats:
    rows = list(facts)
    album_dates: dict[int, str | None] = {}
    album_tracks: Counter[int] = Counter()
    album_seconds: dict[int, float] = {}
    for row in rows:
        if row.album_id is not None:
            album_dates.setdefault(row.album_id, row.album_date)
            album_tracks[row.album_id] += 1
            album_seconds[row.album_id] = album_seconds.get(row.album_id, 0) + row.duration_seconds

    years = Counter(
        year for date in album_dates.values() if (year := year_from_date(date)) is not None
    )
    return LibraryStats(
        tracks=len(rows),
        albums=len(album_dates),
        artists=len({row.artist_id for row in rows if row.artist_id is not None}),
        total_duration_seconds=round(sum(row.duration_seconds for row in rows), 3),
        hires_tracks=sum(1 for row in rows if _is_hires(row)),
        albums_by_decade=_in_label_order(
            Counter(f"{year // 10 * 10}s" for year in years.elements())
        ),
        albums_by_year=_in_label_order(Counter({str(year): n for year, n in years.items()})),
        tracks_by_format=_most_common(Counter(_format_label(row) for row in rows)),
        tracks_by_channels=_most_common(Counter(_channels_label(row.channels) for row in rows)),
        tracks_by_genre=_most_common(
            Counter(genre for row in rows if (genre := (row.genre or "").strip()))
        ),
        albums_by_track_count=_in_bucket_order(
            album_tracks.values(), _TRACK_COUNT_BUCKETS, _TRACK_COUNT_LAST
        ),
        albums_by_length=_in_bucket_order(
            (seconds / 60 for seconds in album_seconds.values()), _LENGTH_BUCKETS, _LENGTH_LAST
        ),
        top_artists=_top_artists(rows),
    )


def _is_hires(row: TrackFacts) -> bool:
    return row.bit_depth >= HIRES_MIN_BIT_DEPTH or row.sample_rate >= HIRES_MIN_SAMPLE_RATE


def _format_label(row: TrackFacts) -> str:
    return f"{row.bit_depth}-bit / {row.sample_rate / 1000:g} kHz"


def _channels_label(channels: int) -> str:
    return {1: "Mono", 2: "Stereo"}.get(channels, f"{channels} channels")


def _most_common(counts: Counter[str]) -> list[Bucket]:
    """Biggest first; equal counts fall back to the label so the order is stable."""
    return [Bucket(label, n) for label, n in sorted(counts.items(), key=lambda p: (-p[1], p[0]))]


def _in_label_order(counts: Counter[str]) -> list[Bucket]:
    return [Bucket(label, counts[label]) for label in sorted(counts)]


def _in_bucket_order(
    values: Iterable[float], bounds: list[tuple[int, str]], last_label: str
) -> list[Bucket]:
    labels = [label for _, label in bounds] + [last_label]
    counts: Counter[str] = Counter()
    for value in values:
        counts[next((label for bound, label in bounds if value < bound), last_label)] += 1
    return [Bucket(label, counts[label]) for label in labels if counts[label]]


def _top_artists(rows: list[TrackFacts]) -> list[ArtistCount]:
    names: dict[int, str] = {}
    tracks: Counter[int] = Counter()
    albums: dict[int, set[int]] = {}
    for row in rows:
        if row.artist_id is None or row.artist_name is None:
            continue
        names[row.artist_id] = row.artist_name
        tracks[row.artist_id] += 1
        if row.album_id is not None:
            albums.setdefault(row.artist_id, set()).add(row.album_id)
    ranked = sorted(tracks, key=lambda artist_id: (-tracks[artist_id], names[artist_id]))
    return [
        ArtistCount(id=i, name=names[i], tracks=tracks[i], albums=len(albums.get(i, ())))
        for i in ranked[:TOP_ARTISTS]
    ]
