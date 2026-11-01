from conftest import Library
from wj_music.domain.library import AlbumSummary
from wj_music.storage.library_reader import SqlLibraryReader


def reader(library: Library) -> SqlLibraryReader:
    return SqlLibraryReader(library.engine)


def titles(albums: list[AlbumSummary]) -> list[str]:
    return [album.title for album in albums]


def album_id(library: Library, title: str) -> int:
    page = reader(library).list_albums(limit=100)
    return next(album.id for album in page.items if album.title == title)


class TestListAlbums:
    def test_albums_are_sorted_by_artist_then_year_then_title(self, library: Library) -> None:
        page = reader(library).list_albums(limit=50)

        assert titles(page.items) == ["Another Green World", "Discreet Music", '"Heroes"', "Low"]
        assert page.total == 4

    def test_paging_returns_a_window_and_the_full_total(self, library: Library) -> None:
        page = reader(library).list_albums(limit=2, offset=2)

        assert titles(page.items) == ['"Heroes"', "Low"]
        assert page.total == 4

    def test_offset_past_the_end_is_empty(self, library: Library) -> None:
        page = reader(library).list_albums(limit=10, offset=50)

        assert page.items == []
        assert page.total == 4

    def test_summary_carries_artist_year_track_count_and_cover_flag(self, library: Library) -> None:
        page = reader(library).list_albums(limit=50)
        low = next(a for a in page.items if a.title == "Low")
        heroes = next(a for a in page.items if a.title == '"Heroes"')

        assert low.artist_name == "David Bowie"
        assert low.year == 1977
        assert low.track_count == 2
        assert low.has_cover is True
        assert heroes.has_cover is False

    def test_search_matches_album_title_ignoring_case(self, library: Library) -> None:
        page = reader(library).list_albums(query="lOW", limit=50)

        assert titles(page.items) == ["Low"]
        assert page.total == 1

    def test_search_matches_artist_name(self, library: Library) -> None:
        page = reader(library).list_albums(query="eno", limit=50)

        assert titles(page.items) == ["Another Green World", "Discreet Music"]

    def test_search_treats_percent_and_underscore_literally(self, library: Library) -> None:
        assert reader(library).list_albums(query="%", limit=50).items == []
        assert reader(library).list_albums(query="_", limit=50).items == []

    def test_filter_by_artist(self, library: Library) -> None:
        bowie = reader(library).list_artists(query="bowie", limit=10).items[0]

        page = reader(library).list_albums(artist_id=bowie.id, limit=50)

        assert titles(page.items) == ['"Heroes"', "Low"]

    def test_filter_by_year(self, library: Library) -> None:
        page = reader(library).list_albums(year=1975, limit=50)

        assert titles(page.items) == ["Another Green World", "Discreet Music"]

    def test_filters_combine(self, library: Library) -> None:
        page = reader(library).list_albums(query="green", year=1975, limit=50)

        assert titles(page.items) == ["Another Green World"]

    def test_tracks_without_an_album_are_not_listed(self, library: Library) -> None:
        assert "Loose track" not in titles(reader(library).list_albums(limit=50).items)


class TestAlbumDetail:
    def test_tracks_are_sorted_by_track_number_and_numbers_are_parsed(
        self, library: Library
    ) -> None:
        detail = reader(library).get_album(album_id(library, "Low"))

        assert detail is not None
        assert [t.title for t in detail.tracks] == ["Breaking Glass", "Speed of Life"]
        assert [t.number for t in detail.tracks] == [1, 2]
        assert detail.summary.title == "Low"

    def test_tracks_are_sorted_by_disc_before_track(self, library: Library) -> None:
        detail = reader(library).get_album(album_id(library, "Discreet Music"))

        assert detail is not None
        assert [t.title for t in detail.tracks] == ["First disc", "Second disc"]
        assert [t.disc for t in detail.tracks] == [1, 2]

    def test_technical_info_and_durations_are_included(self, library: Library) -> None:
        detail = reader(library).get_album(album_id(library, "Low"))

        assert detail is not None
        first = detail.tracks[0]
        assert (first.sample_rate, first.bit_depth, first.channels) == (44100, 16, 2)
        assert first.duration_seconds == 200
        assert detail.total_duration_seconds == 350

    def test_unknown_album_is_none(self, library: Library) -> None:
        assert reader(library).get_album(9999) is None


class TestArtists:
    def test_artists_with_albums_are_sorted_by_name_with_album_counts(
        self, library: Library
    ) -> None:
        page = reader(library).list_artists(limit=50)

        assert [(a.name, a.album_count) for a in page.items] == [
            ("Brian Eno", 2),
            ("David Bowie", 2),
        ]
        assert page.total == 2

    def test_search_matches_part_of_the_name(self, library: Library) -> None:
        page = reader(library).list_artists(query="bow", limit=50)

        assert [a.name for a in page.items] == ["David Bowie"]
        assert page.total == 1

    def test_paging(self, library: Library) -> None:
        page = reader(library).list_artists(limit=1, offset=1)

        assert [a.name for a in page.items] == ["David Bowie"]
        assert page.total == 2

    def test_artist_detail_lists_their_albums(self, library: Library) -> None:
        artist = reader(library).list_artists(query="bowie", limit=1).items[0]

        detail = reader(library).get_artist(artist.id)

        assert detail is not None
        assert detail.name == "David Bowie"
        assert titles(detail.albums) == ['"Heroes"', "Low"]

    def test_unknown_artist_is_none(self, library: Library) -> None:
        assert reader(library).get_artist(9999) is None


class TestYearsAndCovers:
    def test_years_are_listed_newest_first(self, library: Library) -> None:
        assert reader(library).list_years() == [1977, 1975]

    def test_album_cover_file_is_the_cached_name(self, library: Library) -> None:
        name = reader(library).album_cover_file(album_id(library, "Low"))

        assert name is not None
        assert (library.covers_dir / name).is_file()

    def test_album_without_cover_has_none(self, library: Library) -> None:
        assert reader(library).album_cover_file(album_id(library, '"Heroes"')) is None

    def test_unknown_album_has_no_cover(self, library: Library) -> None:
        assert reader(library).album_cover_file(9999) is None
