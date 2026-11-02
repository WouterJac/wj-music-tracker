from wj_music.domain.facts import Fact, FactTrack, build_facts


def track(
    track_id: int,
    *,
    title: str = "Song",
    album_id: int | None = 1,
    album_title: str | None = "Low",
    album_date: str | None = "1977",
    artist_id: int | None = 1,
    artist_name: str | None = "David Bowie",
    disc: int | None = None,
    genre: str | None = None,
    seconds: float = 180,
) -> FactTrack:
    return FactTrack(
        track_id=track_id,
        title=title,
        album_id=album_id,
        album_title=album_title,
        album_date=album_date,
        artist_id=artist_id,
        artist_name=artist_name,
        disc=disc,
        genre=genre,
        duration_seconds=seconds,
    )


def by_key(facts: list[Fact]) -> dict[str, Fact]:
    return {fact.key: fact for fact in facts}


def two_albums() -> list[FactTrack]:
    return [
        track(1, album_id=1, album_title="Low", album_date="1977", seconds=1800),
        track(2, album_id=1, album_title="Low", album_date="1977", seconds=1800),
        track(
            3,
            album_id=2,
            album_title="Another Green World",
            album_date="1975",
            artist_id=2,
            artist_name="Brian Eno",
            seconds=4500,
        ),
    ]


class TestEmptyAndTiny:
    def test_empty_library_has_no_facts(self) -> None:
        assert build_facts([]) == []

    def test_one_album_gives_no_comparisons(self) -> None:
        facts = by_key(build_facts([track(1), track(2)]))

        for key in ("longest_album", "shortest_album", "oldest_release", "newest_release"):
            assert key not in facts

    def test_tracks_without_an_album_are_ignored_for_album_facts(self) -> None:
        facts = build_facts([track(1, album_id=None, album_title=None)])

        assert facts == []


class TestAlbumLengthAndSize:
    def test_longest_and_shortest_album_link_to_the_album(self) -> None:
        facts = by_key(build_facts(two_albums()))

        longest = facts["longest_album"]
        assert longest.text == "Another Green World by Brian Eno runs 1 h 15 min."
        assert (longest.link.kind, longest.link.id) == ("album", 2)
        shortest = facts["shortest_album"]
        assert shortest.text == "Low by David Bowie runs 1 h."
        assert shortest.link.id == 1

    def test_album_with_most_tracks(self) -> None:
        facts = by_key(build_facts(two_albums()))

        assert facts["most_tracks"].text == "Low by David Bowie has 2 tracks."
        assert facts["most_tracks"].link.id == 1

    def test_ties_go_to_the_album_that_sorts_first(self) -> None:
        tied = [
            track(1, album_id=1, album_title="Zebra", seconds=600),
            track(2, album_id=2, album_title="Apple", seconds=600),
        ]

        assert by_key(build_facts(tied))["longest_album"].link.id == 2


class TestReleaseDates:
    def test_oldest_and_newest_release(self) -> None:
        facts = by_key(build_facts(two_albums()))

        assert facts["oldest_release"].text == "Another Green World by Brian Eno came out in 1975."
        assert facts["newest_release"].text == "Low by David Bowie came out in 1977."

    def test_skipped_when_every_album_has_the_same_year_or_none(self) -> None:
        same = [
            track(1, album_id=1, album_title="A", album_date="1977"),
            track(2, album_id=2, album_title="B", album_date="1977-05-01"),
            track(3, album_id=3, album_title="C", album_date=None),
        ]

        facts = by_key(build_facts(same))

        assert "oldest_release" not in facts
        assert "newest_release" not in facts


class TestLongestTrack:
    def test_names_the_track_and_its_album(self) -> None:
        tracks = [*two_albums(), track(4, title="Sky Saw", seconds=9000)]

        fact = by_key(build_facts(tracks))["longest_track"]

        assert fact.text == "“Sky Saw” on Low lasts 2 h 30 min."
        assert (fact.link.kind, fact.link.id) == ("track", 4)

    def test_needs_more_than_one_track(self) -> None:
        assert "longest_track" not in by_key(build_facts([track(1)]))


class TestMultiDisc:
    def test_counts_albums_with_more_than_one_disc(self) -> None:
        tracks = [
            track(1, album_id=1, album_title="Big Box", disc=1),
            track(2, album_id=1, album_title="Big Box", disc=2),
            track(3, album_id=1, album_title="Big Box", disc=3),
            track(4, album_id=2, album_title="Double", disc=1),
            track(5, album_id=2, album_title="Double", disc=2),
            track(6, album_id=3, album_title="Single", disc=1),
        ]

        fact = by_key(build_facts(tracks))["multi_disc"]

        assert fact.text == "2 albums span more than one disc. Big Box by David Bowie has 3."
        assert fact.link.id == 1

    def test_absent_without_multi_disc_albums(self) -> None:
        assert "multi_disc" not in by_key(build_facts(two_albums()))

    def test_single_multi_disc_album_reads_naturally(self) -> None:
        tracks = [track(1, disc=1), track(2, disc=2)]

        assert by_key(build_facts(tracks))["multi_disc"].text == "Low by David Bowie spans 2 discs."


class TestGenreSpread:
    def test_album_with_the_most_distinct_genres(self) -> None:
        tracks = [
            track(1, genre="Rock"),
            track(2, genre=" Rock "),
            track(3, genre="Ambient"),
            track(4, genre="Pop"),
            track(5, album_id=2, album_title="Plain", genre="Rock"),
        ]

        fact = by_key(build_facts(tracks))["genre_spread"]

        assert fact.text == "Low by David Bowie mixes 3 genres: Ambient, Pop and Rock."
        assert fact.link.id == 1

    def test_absent_when_no_album_has_two_genres(self) -> None:
        assert "genre_spread" not in by_key(build_facts([track(1, genre="Rock")]))


class TestCompilations:
    def test_album_with_the_most_different_artists(self) -> None:
        tracks = [
            track(1, album_id=7, album_title="Now 99", artist_id=1, artist_name="A"),
            track(2, album_id=7, album_title="Now 99", artist_id=2, artist_name="B"),
            track(3, album_id=7, album_title="Now 99", artist_id=3, artist_name="C"),
            track(4, album_id=8, album_title="Solo", artist_id=1, artist_name="A"),
        ]

        fact = by_key(build_facts(tracks))["most_artists"]

        assert fact.text == "Now 99 features 3 different artists."
        assert fact.link.id == 7

    def test_two_artists_is_not_a_compilation(self) -> None:
        tracks = [track(1, artist_id=1), track(2, artist_id=2)]

        assert "most_artists" not in by_key(build_facts(tracks))
