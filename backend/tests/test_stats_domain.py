from wj_music.domain.stats import TrackFacts, build_stats


def facts(
    *,
    album_id: int | None = 1,
    album_date: str | None = "1977",
    artist_id: int | None = 1,
    artist_name: str | None = "David Bowie",
    genre: str | None = None,
    seconds: float = 180,
    sample_rate: int = 44100,
    bit_depth: int = 16,
    channels: int = 2,
) -> TrackFacts:
    return TrackFacts(
        album_id=album_id,
        album_date=album_date,
        artist_id=artist_id,
        artist_name=artist_name,
        genre=genre,
        duration_seconds=seconds,
        sample_rate=sample_rate,
        bit_depth=bit_depth,
        channels=channels,
    )


def as_pairs(buckets: list) -> list[tuple[str, int]]:  # type: ignore[type-arg]
    return [(b.label, b.count) for b in buckets]


class TestTotals:
    def test_empty_library_is_all_zeros_and_empty_lists(self) -> None:
        stats = build_stats([])

        assert (stats.tracks, stats.albums, stats.artists) == (0, 0, 0)
        assert stats.total_duration_seconds == 0
        assert stats.hires_tracks == 0
        assert stats.albums_by_decade == []
        assert stats.albums_by_year == []
        assert stats.tracks_by_format == []
        assert stats.tracks_by_channels == []
        assert stats.tracks_by_genre == []
        assert stats.albums_by_track_count == []
        assert stats.albums_by_length == []
        assert stats.top_artists == []

    def test_counts_distinct_albums_and_artists_and_sums_duration(self) -> None:
        stats = build_stats(
            [
                facts(album_id=1, seconds=100),
                facts(album_id=1, seconds=50.5),
                facts(album_id=2, artist_id=2, artist_name="Brian Eno", seconds=10),
                facts(album_id=None, artist_id=None, artist_name=None, seconds=1),
            ]
        )

        assert (stats.tracks, stats.albums, stats.artists) == (4, 2, 2)
        assert stats.total_duration_seconds == 161.5


class TestHiRes:
    def test_more_than_16_bit_or_above_48_khz_counts_as_hi_res(self) -> None:
        stats = build_stats(
            [
                facts(),
                facts(bit_depth=24),
                facts(sample_rate=96000),
                facts(sample_rate=48000),
            ]
        )

        assert stats.hires_tracks == 2


class TestAlbumDates:
    def test_albums_are_counted_once_by_decade_and_year(self) -> None:
        stats = build_stats(
            [
                facts(album_id=1, album_date="1977-01-14"),
                facts(album_id=1, album_date="1977-01-14"),
                facts(album_id=2, album_date="1975"),
                facts(album_id=3, album_date="1986"),
                facts(album_id=4, album_date=None),
            ]
        )

        assert as_pairs(stats.albums_by_decade) == [("1970s", 2), ("1980s", 1)]
        assert as_pairs(stats.albums_by_year) == [("1975", 1), ("1977", 1), ("1986", 1)]


class TestTrackDistributions:
    def test_format_label_shows_bit_depth_and_khz_most_common_first(self) -> None:
        stats = build_stats(
            [
                facts(),
                facts(bit_depth=24, sample_rate=96000),
                facts(bit_depth=24, sample_rate=96000),
            ]
            + [facts(sample_rate=44100, bit_depth=24)]
        )

        assert as_pairs(stats.tracks_by_format) == [
            ("24-bit / 96 kHz", 2),
            ("16-bit / 44.1 kHz", 1),
            ("24-bit / 44.1 kHz", 1),
        ]

    def test_channel_labels(self) -> None:
        stats = build_stats(
            [facts(channels=2), facts(channels=2), facts(channels=1), facts(channels=6)]
        )

        assert as_pairs(stats.tracks_by_channels) == [
            ("Stereo", 2),
            ("6 channels", 1),
            ("Mono", 1),
        ]

    def test_genres_are_trimmed_and_blank_ones_skipped(self) -> None:
        stats = build_stats(
            [facts(genre="Rock"), facts(genre=" Rock "), facts(genre="Ambient"), facts(genre="  ")]
        )

        assert as_pairs(stats.tracks_by_genre) == [("Rock", 2), ("Ambient", 1)]


class TestAlbumShape:
    def test_tracks_per_album_buckets_in_natural_order(self) -> None:
        tracks = [facts(album_id=1)] * 3 + [facts(album_id=2)] * 5 + [facts(album_id=3)] * 12
        stats = build_stats(tracks)

        assert as_pairs(stats.albums_by_track_count) == [("1–5 tracks", 2), ("11–15 tracks", 1)]

    def test_album_length_buckets_in_natural_order(self) -> None:
        stats = build_stats(
            [
                facts(album_id=1, seconds=60 * 19),
                facts(album_id=2, seconds=60 * 25),
                facts(album_id=3, seconds=60 * 30),
                facts(album_id=4, seconds=60 * 95),
            ]
        )

        assert as_pairs(stats.albums_by_length) == [
            ("Under 20 min", 1),
            ("20–40 min", 2),
            ("80+ min", 1),
        ]


class TestTopArtists:
    def test_ranked_by_tracks_then_name_and_limited_to_ten(self) -> None:
        tracks = [facts(album_id=1, artist_id=1, artist_name="Zed")] * 2
        tracks += [facts(album_id=2, artist_id=2, artist_name="Abe")] * 2
        tracks += [facts(album_id=3, artist_id=2, artist_name="Abe")]
        tracks += [
            facts(album_id=10 + n, artist_id=10 + n, artist_name=f"Artist {n:02d}")
            for n in range(12)
        ]
        stats = build_stats(tracks)

        top = stats.top_artists
        assert len(top) == 10
        assert [(a.name, a.tracks, a.albums) for a in top[:2]] == [("Abe", 3, 2), ("Zed", 2, 1)]
        assert top[2].name == "Artist 00"
