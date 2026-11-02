"""Rediscover use cases: remember which albums were viewed and suggest ones not seen lately."""

import random
from collections.abc import Callable
from datetime import UTC, datetime

from wj_music.domain.library import AlbumSummary
from wj_music.domain.rediscover import album_key, pick_rediscover
from wj_music.domain.repositories import LibraryReader, ViewHistory

# The whole library is read to pick from, which stays cheap for a personal collection.
ALL_ALBUMS = 100_000


def _utc_now() -> datetime:
    return datetime.now(UTC)


class RediscoverService:
    def __init__(
        self,
        albums: LibraryReader,
        history: ViewHistory,
        *,
        clock: Callable[[], datetime] = _utc_now,
        rng: random.Random | None = None,
    ) -> None:
        self._albums = albums
        self._history = history
        self._clock = clock
        self._rng = rng or random.Random()

    def record_view(self, album_id: int) -> bool:
        """Remember a view of the album, or return False if there is no such album."""
        detail = self._albums.get_album(album_id)
        if detail is None:
            return False
        summary = detail.summary
        self._history.record(album_key(summary.title, summary.artist_name), self._clock())
        return True

    def rediscover(self, count: int) -> list[AlbumSummary]:
        albums = self._albums.list_albums(limit=ALL_ALBUMS).items
        return pick_rediscover(albums, self._history.last_viewed(), count=count, rng=self._rng)
