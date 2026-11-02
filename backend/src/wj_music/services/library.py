"""Browsing use cases. Talks to the library only through the LibraryReader contract."""

from wj_music.domain.library import (
    AlbumDetail,
    AlbumSummary,
    ArtistDetail,
    ArtistSummary,
    GenreCount,
    Page,
)
from wj_music.domain.repositories import LibraryReader


class LibraryService:
    def __init__(self, reader: LibraryReader) -> None:
        self._reader = reader

    def list_albums(
        self,
        *,
        query: str | None,
        artist_id: int | None,
        year: int | None,
        decade: int | None = None,
        genre: str | None = None,
        limit: int,
        offset: int,
    ) -> Page[AlbumSummary]:
        return self._reader.list_albums(
            query=_clean(query),
            artist_id=artist_id,
            year=year,
            decade=decade,
            genre=_clean(genre),
            limit=limit,
            offset=offset,
        )

    def random_albums(
        self, *, count: int, decade: int | None = None, genre: str | None = None
    ) -> list[AlbumSummary]:
        return self._reader.random_albums(count=count, decade=decade, genre=_clean(genre))

    def list_genres(self) -> list[GenreCount]:
        return self._reader.list_genres()

    def get_album(self, album_id: int) -> AlbumDetail | None:
        return self._reader.get_album(album_id)

    def list_artists(self, *, query: str | None, limit: int, offset: int) -> Page[ArtistSummary]:
        return self._reader.list_artists(query=_clean(query), limit=limit, offset=offset)

    def get_artist(self, artist_id: int) -> ArtistDetail | None:
        return self._reader.get_artist(artist_id)

    def list_years(self) -> list[int]:
        return self._reader.list_years()

    def album_cover_name(self, album_id: int) -> str | None:
        return self._reader.album_cover_file(album_id)


def _clean(query: str | None) -> str | None:
    """Surrounding whitespace is never part of a search, and blank means no search."""
    if query is None:
        return None
    return query.strip() or None
