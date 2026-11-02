"""Facts use case. Talks to the library only through the FactsReader contract."""

from wj_music.domain.facts import Fact
from wj_music.domain.repositories import FactsReader


class FactsService:
    def __init__(self, reader: FactsReader) -> None:
        self._reader = reader

    def facts(self) -> list[Fact]:
        return self._reader.facts()
