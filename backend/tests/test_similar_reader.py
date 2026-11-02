import pytest

from conftest import Library
from explore_helpers import GENRES, merged, tag_tracks
from wj_music.storage.similar_reader import SqlSimilarReader

TAGS = {
    "Breaking Glass": {"label": "RCA", "composer": "David Bowie"},
    "Beauty and the Beast": {"label": " rca "},
    "Sky Saw": {"label": "Island", "composer": "Brian Eno"},
}


@pytest.fixture
def profiles(library: Library):  # type: ignore[no-untyped-def]
    tag_tracks(library.engine, merged(GENRES, TAGS))
    return {p.title: p for p in SqlSimilarReader(library.engine).album_profiles()}


def test_one_profile_per_album_with_a_title_and_year(profiles) -> None:  # type: ignore[no-untyped-def]
    assert sorted(profiles) == ['"Heroes"', "Another Green World", "Discreet Music", "Low"]
    assert profiles["Low"].year == 1977
    assert profiles["Another Green World"].year == 1975


def test_tags_are_gathered_over_the_tracks_and_trimmed(profiles) -> None:  # type: ignore[no-untyped-def]
    assert profiles["Low"].genres == {"Rock", "Art Rock"}
    assert profiles["Low"].labels == {"RCA"}
    assert profiles["Low"].composers == {"David Bowie"}
    assert profiles["Discreet Music"].genres == {"ambient"}
    assert profiles['"Heroes"'].labels == {"rca"}


def test_untagged_albums_have_empty_sets(library: Library) -> None:
    profile = {p.title: p for p in SqlSimilarReader(library.engine).album_profiles()}["Low"]

    assert (profile.genres, profile.labels, profile.composers) == (frozenset(),) * 3


def test_empty_database_has_no_profiles(engine) -> None:  # type: ignore[no-untyped-def]
    assert SqlSimilarReader(engine).album_profiles() == []
