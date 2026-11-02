from datetime import UTC, datetime, timedelta
from pathlib import Path

from wj_music.domain.rediscover import album_key
from wj_music.storage.database import create_db_engine
from wj_music.storage.view_history import SqlViewHistory

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
LOW = album_key("Low", "David Bowie")


def history(path: Path) -> SqlViewHistory:
    return SqlViewHistory(create_db_engine(path))


def test_nothing_is_recorded_at_first(tmp_path: Path) -> None:
    assert history(tmp_path / "user.db").last_viewed() == {}


def test_a_recorded_view_is_returned_with_its_time(tmp_path: Path) -> None:
    views = history(tmp_path / "user.db")

    views.record(LOW, NOW)

    assert views.last_viewed() == {LOW: NOW}


def test_a_new_view_replaces_the_time_of_the_old_one(tmp_path: Path) -> None:
    views = history(tmp_path / "user.db")

    views.record(LOW, NOW)
    views.record(LOW, NOW + timedelta(days=3))

    assert views.last_viewed() == {LOW: NOW + timedelta(days=3)}


def test_views_survive_reopening_the_database(tmp_path: Path) -> None:
    path = tmp_path / "user.db"
    history(path).record(LOW, NOW)

    assert history(path).last_viewed() == {LOW: NOW}
