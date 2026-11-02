from conftest import Library
from wj_music.storage.facts_reader import SqlFactsReader


def test_facts_for_the_fixture_library(library: Library) -> None:
    facts = {fact.key: fact for fact in SqlFactsReader(library.engine).facts()}

    assert list(facts) == [
        "longest_album",
        "shortest_album",
        "oldest_release",
        "newest_release",
        "most_tracks",
        "longest_track",
        "multi_disc",
    ]
    assert facts["longest_album"].text == "Discreet Music by Brian Eno runs 6 min."
    assert facts["longest_track"].text == "“Breaking Glass” on Low lasts 3 min."
    assert facts["multi_disc"].text == "Discreet Music by Brian Eno spans 2 discs."
    assert facts["oldest_release"].text == "Another Green World by Brian Eno came out in 1975."


def test_empty_database_has_no_facts(engine) -> None:  # type: ignore[no-untyped-def]
    assert SqlFactsReader(engine).facts() == []
