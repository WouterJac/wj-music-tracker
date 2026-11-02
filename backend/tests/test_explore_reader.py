import pytest

from conftest import Library
from explore_helpers import GENRES, tag_tracks
from wj_music.domain.library import AlbumSummary
from wj_music.storage.library_reader import SqlLibraryReader


@pytest.fixture
def reader(library: Library) -> SqlLibraryReader:
    tag_tracks(library.engine, GENRES)
    return SqlLibraryReader(library.engine)


def titles(albums: list[AlbumSummary]) -> list[str]:
    return [album.title for album in albums]


class TestGenres:
    def test_genres_with_album_counts_biggest_first(self, reader: SqlLibraryReader) -> None:
        genres = reader.list_genres()

        assert [(g.name, g.album_count) for g in genres] == [
            ("Ambient", 2),
            ("Rock", 2),
            ("Art Rock", 1),
        ]

    def test_no_genre_tags_means_no_genres(self, library: Library) -> None:
        assert SqlLibraryReader(library.engine).list_genres() == []


class TestFilters:
    def test_decade_filter(self, reader: SqlLibraryReader) -> None:
        page = reader.list_albums(decade=1970, limit=50)

        assert page.total == 4
        assert reader.list_albums(decade=1980, limit=50).items == []

    def test_genre_filter_ignores_case_and_spaces(self, reader: SqlLibraryReader) -> None:
        page = reader.list_albums(genre="AMBIENT", limit=50)

        assert sorted(titles(page.items)) == ["Another Green World", "Discreet Music"]
        assert page.total == 2

    def test_genre_matches_an_album_when_any_track_has_it(self, reader: SqlLibraryReader) -> None:
        assert titles(reader.list_albums(genre="Art Rock", limit=50).items) == ["Low"]

    def test_filters_combine_with_the_existing_ones(self, reader: SqlLibraryReader) -> None:
        page = reader.list_albums(genre="Rock", year=1977, query="low", limit=50)

        assert titles(page.items) == ["Low"]


class TestRandomAlbums:
    def test_returns_the_requested_number_of_distinct_albums(
        self, reader: SqlLibraryReader
    ) -> None:
        albums = reader.random_albums(count=3)

        assert len(albums) == 3
        assert len({a.id for a in albums}) == 3

    def test_never_returns_more_than_exist(self, reader: SqlLibraryReader) -> None:
        assert len(reader.random_albums(count=12)) == 4

    def test_respects_filters(self, reader: SqlLibraryReader) -> None:
        for _ in range(10):
            albums = reader.random_albums(count=4, genre="ambient")
            assert {a.title for a in albums} == {"Another Green World", "Discreet Music"}

    def test_empty_when_nothing_matches(self, reader: SqlLibraryReader) -> None:
        assert reader.random_albums(count=3, decade=1990) == []

    def test_selection_varies(self, reader: SqlLibraryReader) -> None:
        firsts = {reader.random_albums(count=1)[0].id for _ in range(40)}

        assert len(firsts) > 1
