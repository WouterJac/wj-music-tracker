import random
from datetime import UTC, datetime, timedelta

from wj_music.domain.library import AlbumSummary
from wj_music.domain.rediscover import album_key, pick_rediscover

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


def album(album_id: int, title: str, artist: str | None = "Artist") -> AlbumSummary:
    return AlbumSummary(
        id=album_id,
        title=title,
        artist_id=None,
        artist_name=artist,
        year=None,
        track_count=1,
        has_cover=False,
    )


def test_key_ignores_case_and_edge_spaces() -> None:
    assert album_key(" Low ", "David Bowie") == album_key("low", " david bowie")


def test_key_treats_a_missing_artist_as_empty() -> None:
    assert album_key("Loose", None) == album_key("Loose", "  ")


def test_albums_never_viewed_come_before_viewed_ones() -> None:
    albums = [album(1, "Seen"), album(2, "Unseen")]
    viewed = {album_key("Seen", "Artist"): NOW}

    picked = pick_rediscover(albums, viewed, count=2, rng=random.Random(1))

    assert [a.title for a in picked] == ["Unseen", "Seen"]


def test_viewed_albums_are_ordered_by_the_longest_time_since_a_view() -> None:
    albums = [album(1, "Recent"), album(2, "Old"), album(3, "Middle")]
    viewed = {
        album_key("Recent", "Artist"): NOW - timedelta(days=1),
        album_key("Old", "Artist"): NOW - timedelta(days=90),
        album_key("Middle", "Artist"): NOW - timedelta(days=10),
    }

    picked = pick_rediscover(albums, viewed, count=3, rng=random.Random(1))

    assert [a.title for a in picked] == ["Old", "Middle", "Recent"]


def test_stops_at_the_requested_count() -> None:
    albums = [album(i, f"Album {i}") for i in range(1, 9)]

    assert len(pick_rediscover(albums, {}, count=3, rng=random.Random(1))) == 3


def test_unviewed_albums_are_shuffled_by_the_given_random_source() -> None:
    albums = [album(i, f"Album {i}") for i in range(1, 9)]

    first = pick_rediscover(albums, {}, count=8, rng=random.Random(1))
    again = pick_rediscover(albums, {}, count=8, rng=random.Random(1))
    other = pick_rediscover(albums, {}, count=8, rng=random.Random(2))

    assert first == again
    assert first != other
    assert sorted(a.id for a in first) == list(range(1, 9))


def test_an_empty_library_has_nothing_to_rediscover() -> None:
    assert pick_rediscover([], {}, count=6, rng=random.Random(1)) == []
