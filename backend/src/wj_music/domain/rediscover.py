"""Choosing albums to look at again. Pure rules, no I/O."""

import random
from collections.abc import Mapping, Sequence
from datetime import datetime

from wj_music.domain.library import AlbumSummary

AlbumKey = tuple[str, str]


def album_key(title: str, artist_name: str | None) -> AlbumKey:
    """Views are kept by title and artist, since album ids change when the cache is rebuilt."""
    return title.strip().casefold(), (artist_name or "").strip().casefold()


def pick_rediscover(
    albums: Sequence[AlbumSummary],
    last_viewed: Mapping[AlbumKey, datetime],
    *,
    count: int,
    rng: random.Random,
) -> list[AlbumSummary]:
    """Albums never viewed first, in random order, then viewed ones with the oldest view first."""
    unseen = [a for a in albums if album_key(a.title, a.artist_name) not in last_viewed]
    seen = sorted(
        (a for a in albums if album_key(a.title, a.artist_name) in last_viewed),
        key=lambda a: (last_viewed[album_key(a.title, a.artist_name)], a.id),
    )
    rng.shuffle(unseen)
    return [*unseen, *seen][:count]
