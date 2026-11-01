"""Statistics use case. Talks to the library only through the StatsReader contract."""

from wj_music.domain.repositories import StatsReader
from wj_music.domain.stats import LibraryStats


class StatsService:
    def __init__(self, reader: StatsReader) -> None:
        self._reader = reader

    def library_stats(self) -> LibraryStats:
        return self._reader.library_stats()
