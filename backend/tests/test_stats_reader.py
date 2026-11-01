from sqlalchemy import update

from conftest import Library
from wj_music.storage.models import TrackRow
from wj_music.storage.stats_reader import SqlStatsReader


class TestSqlStatsReader:
    def test_summarises_the_fixture_library(self, library: Library) -> None:
        stats = SqlStatsReader(library.engine).library_stats()

        assert (stats.tracks, stats.albums, stats.artists) == (7, 4, 2)
        assert stats.total_duration_seconds == 1250
        assert stats.hires_tracks == 0
        assert [(b.label, b.count) for b in stats.albums_by_decade] == [("1970s", 4)]
        assert [(b.label, b.count) for b in stats.albums_by_year] == [("1975", 2), ("1977", 2)]
        assert [(b.label, b.count) for b in stats.tracks_by_format] == [("16-bit / 44.1 kHz", 7)]
        assert [(b.label, b.count) for b in stats.tracks_by_channels] == [("Stereo", 7)]
        assert stats.tracks_by_genre == []
        assert [(a.name, a.tracks, a.albums) for a in stats.top_artists] == [
            ("Brian Eno", 3, 2),
            ("David Bowie", 3, 2),
        ]

    def test_reads_audio_format_and_genre_from_the_tracks(self, library: Library) -> None:
        with library.engine.begin() as conn:
            conn.execute(
                update(TrackRow)
                .where(TrackRow.title == "Sky Saw")
                .values(bit_depth=24, sample_rate=96000, genre="Ambient")
            )

        stats = SqlStatsReader(library.engine).library_stats()

        assert stats.hires_tracks == 1
        assert ("24-bit / 96 kHz", 1) in [(b.label, b.count) for b in stats.tracks_by_format]
        assert [(b.label, b.count) for b in stats.tracks_by_genre] == [("Ambient", 1)]

    def test_empty_database_gives_empty_stats(self, engine) -> None:  # type: ignore[no-untyped-def]
        stats = SqlStatsReader(engine).library_stats()

        assert (stats.tracks, stats.albums, stats.artists) == (0, 0, 0)
        assert stats.top_artists == []
