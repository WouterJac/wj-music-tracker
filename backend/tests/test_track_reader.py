from sqlalchemy import select

from conftest import Library
from wj_music.domain.library import TrackInfo
from wj_music.storage.library_reader import SqlLibraryReader
from wj_music.storage.models import TrackRow
from wj_music.storage.track_reader import SqlTrackReader


def tracks(library: Library) -> SqlTrackReader:
    return SqlTrackReader(library.engine)


def track_id(library: Library, title: str) -> int:
    albums = SqlLibraryReader(library.engine).list_albums(limit=100).items
    for album in albums:
        detail = SqlLibraryReader(library.engine).get_album(album.id)
        assert detail is not None
        for track in detail.tracks:
            if track.title == title:
                return track.id
    raise AssertionError(f"no track titled {title}")


def get(library: Library, title: str) -> TrackInfo:
    info = tracks(library).get_track(track_id(library, title))
    assert info is not None
    return info


class TestGetTrack:
    def test_includes_album_artist_and_audio_details(self, library: Library) -> None:
        info = get(library, "Breaking Glass")

        assert info.title == "Breaking Glass"
        assert (info.disc, info.number) == (None, 1)
        assert info.album_title == "Low"
        assert info.artist_name == "David Bowie"
        assert info.album_id is not None
        assert info.artist_id is not None
        assert (info.sample_rate, info.bit_depth, info.channels) == (44100, 16, 2)
        assert info.duration_seconds == 200
        assert info.album_has_cover is True

    def test_synced_lyrics_keep_the_raw_lrc_and_a_plain_text(self, library: Library) -> None:
        info = get(library, "Breaking Glass")

        assert info.plain_lyrics == "Baby, I'm not special\nBreaking glass"
        assert info.synced_lrc == (
            "[ar:David Bowie]\n[00:01.00]Baby, I'm not special\n[00:06.50]Breaking glass"
        )

    def test_unsynced_lyrics_have_no_lrc(self, library: Library) -> None:
        info = get(library, "Sky Saw")

        assert info.plain_lyrics == "Wind in the sky\nand the moon is high"
        assert info.synced_lrc is None

    def test_track_without_lyrics(self, library: Library) -> None:
        info = get(library, "Speed of Life")

        assert info.plain_lyrics is None
        assert info.synced_lrc is None

    def test_track_without_album_or_artist(self, library: Library) -> None:
        with library.engine.connect() as conn:
            loose_id = conn.execute(
                select(TrackRow.id).where(TrackRow.title == "Loose track")
            ).scalar_one()
        info = tracks(library).get_track(loose_id)
        assert info is not None

        assert info.album_id is None
        assert info.album_title is None
        assert info.artist_id is None
        assert info.artist_name is None
        assert info.album_has_cover is False

    def test_unknown_track_is_none(self, library: Library) -> None:
        assert tracks(library).get_track(9999) is None


class TestSearchLyrics:
    def test_finds_a_phrase_and_returns_a_snippet(self, library: Library) -> None:
        page = tracks(library).search_lyrics("heroes", limit=10)

        assert page.total == 1
        hit = page.items[0]
        assert hit.title == "Beauty and the Beast"
        assert hit.album_title == '"Heroes"'
        assert hit.artist_name == "David Bowie"
        assert "heroes" in hit.snippet.lower()

    def test_search_ignores_case(self, library: Library) -> None:
        assert tracks(library).search_lyrics("QUEEN", limit=10).total == 1

    def test_synced_only_lyrics_are_searchable_without_timestamps(self, library: Library) -> None:
        page = tracks(library).search_lyrics("breaking glass", limit=10)

        assert [hit.title for hit in page.items] == ["Breaking Glass"]
        assert "[00" not in page.items[0].snippet

    def test_a_phrase_inside_one_line_is_found(self, library: Library) -> None:
        assert tracks(library).search_lyrics("moon is high", limit=10).total == 1

    def test_hits_are_sorted_by_title_and_paged(self, library: Library) -> None:
        reader = tracks(library)

        everything = reader.search_lyrics("in", limit=10)
        window = reader.search_lyrics("in", limit=2, offset=1)

        assert [h.title for h in everything.items] == [
            "Beauty and the Beast",
            "Breaking Glass",
            "Sky Saw",
        ]
        assert [h.title for h in window.items] == ["Breaking Glass", "Sky Saw"]
        assert window.total == 3

    def test_wildcards_match_literally(self, library: Library) -> None:
        assert tracks(library).search_lyrics("%", limit=10).items == []
        assert tracks(library).search_lyrics("_", limit=10).items == []

    def test_no_match_gives_an_empty_page(self, library: Library) -> None:
        page = tracks(library).search_lyrics("zebra", limit=10)

        assert page.items == []
        assert page.total == 0

    def test_tracks_without_lyrics_are_never_hits(self, library: Library) -> None:
        titles = [h.title for h in tracks(library).search_lyrics("e", limit=100).items]

        assert "Speed of Life" not in titles
        assert "Loose track" not in titles
