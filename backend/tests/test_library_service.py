from typing import Any

from wj_music.domain.library import Page
from wj_music.services.library import LibraryService


class RecordingReader:
    """Stands in for the database and remembers how it was called."""

    def __init__(self) -> None:
        self.album_calls: list[dict[str, Any]] = []
        self.artist_calls: list[dict[str, Any]] = []

    def list_albums(self, **kwargs: Any) -> Page[Any]:
        self.album_calls.append(kwargs)
        return Page(items=[], total=0)

    def list_artists(self, **kwargs: Any) -> Page[Any]:
        self.artist_calls.append(kwargs)
        return Page(items=[], total=0)


def test_blank_search_means_no_search() -> None:
    reader = RecordingReader()
    service = LibraryService(reader)  # type: ignore[arg-type]

    service.list_albums(query="   ", artist_id=None, year=None, limit=10, offset=0)
    service.list_artists(query="", limit=10, offset=0)

    assert reader.album_calls[0]["query"] is None
    assert reader.artist_calls[0]["query"] is None


def test_search_text_is_trimmed() -> None:
    reader = RecordingReader()
    service = LibraryService(reader)  # type: ignore[arg-type]

    service.list_albums(query="  low  ", artist_id=3, year=1977, limit=10, offset=5)

    assert reader.album_calls == [
        {
            "query": "low",
            "artist_id": 3,
            "year": 1977,
            "decade": None,
            "genre": None,
            "limit": 10,
            "offset": 5,
        }
    ]


def test_genre_text_is_trimmed_and_blank_means_no_filter() -> None:
    reader = RecordingReader()
    service = LibraryService(reader)  # type: ignore[arg-type]

    service.list_albums(query=None, artist_id=None, year=None, genre="  Rock ", limit=1, offset=0)
    service.list_albums(query=None, artist_id=None, year=None, genre="  ", limit=1, offset=0)

    assert [call["genre"] for call in reader.album_calls] == ["Rock", None]
