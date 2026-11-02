"""Offline album similarity from the tags already in the library. Pure rules, no database."""

from collections.abc import Iterable
from dataclasses import dataclass

from wj_music.domain.library import AlbumSummary

GENRE_POINTS = 3
LABEL_POINTS = 2
COMPOSER_POINTS = 2
ERA_POINTS = 1
ERA_YEARS = 5
# Era on its own says too little, so at least one real tag match is needed.
MIN_SCORE = 2
DEFAULT_LIMIT = 6


@dataclass(frozen=True)
class AlbumProfile:
    """The tags that describe an album, gathered over its tracks."""

    album_id: int
    title: str
    year: int | None
    genres: frozenset[str]
    labels: frozenset[str]
    composers: frozenset[str]


@dataclass(frozen=True)
class Similar:
    album_id: int
    score: int
    reasons: list[str]


def rank_similar(
    target: AlbumProfile, others: Iterable[AlbumProfile], limit: int = DEFAULT_LIMIT
) -> list[Similar]:
    scored = [
        (other, match)
        for other in others
        if other.album_id != target.album_id
        if (match := _match(target, other)).score >= MIN_SCORE
    ]
    scored.sort(
        key=lambda pair: (
            -pair[1].score,
            _era_distance(target, pair[0]),
            pair[0].title.lower(),
            pair[0].album_id,
        )
    )
    return [match for _, match in scored[:limit]]


def _match(target: AlbumProfile, other: AlbumProfile) -> Similar:
    score = 0
    reasons: list[str] = []

    genres = _shared(target.genres, other.genres)
    if genres:
        score += GENRE_POINTS * len(genres)
        label = "genre" if len(genres) == 1 else "genres"
        reasons.append(f"Shared {label}: {_listed(genres)}")

    labels = _shared(target.labels, other.labels)
    if labels:
        score += LABEL_POINTS
        reasons.append(f"Same label: {_listed(labels)}")

    composers = _shared(target.composers, other.composers)
    if composers:
        score += COMPOSER_POINTS
        reasons.append(f"Same composer: {_listed(composers)}")

    if _era_distance(target, other) <= ERA_YEARS:
        score += ERA_POINTS
        reasons.append(f"Similar era: {other.year}")
    return Similar(album_id=other.album_id, score=score, reasons=reasons)


def _shared(mine: frozenset[str], theirs: frozenset[str]) -> list[str]:
    """What both have, compared without case or edge spaces, spelled the way `mine` has it."""
    theirs_keys = {_key(value) for value in theirs}
    return sorted((value for value in mine if _key(value) in theirs_keys), key=str.lower)


def _key(value: str) -> str:
    return value.strip().lower()


def _listed(values: list[str]) -> str:
    return values[0] if len(values) == 1 else f"{', '.join(values[:-1])} and {values[-1]}"


def _era_distance(target: AlbumProfile, other: AlbumProfile) -> int:
    if target.year is None or other.year is None:
        return 10_000
    return abs(target.year - other.year)


@dataclass(frozen=True)
class SimilarAlbum:
    """A suggested album with why it was suggested."""

    album: AlbumSummary
    score: int
    reasons: list[str]
