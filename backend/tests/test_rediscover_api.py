import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Library
from wj_music.api.app import create_app
from wj_music.services.library import LibraryService
from wj_music.services.rediscover import RediscoverService
from wj_music.storage.database import create_db_engine
from wj_music.storage.library_reader import SqlLibraryReader
from wj_music.storage.view_history import SqlViewHistory

START = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


def build_client(library: Library, user_db: Path, clock: Clock) -> TestClient:
    albums = SqlLibraryReader(library.engine)
    rediscover = RediscoverService(
        albums,
        SqlViewHistory(create_db_engine(user_db)),
        clock=clock,
        rng=random.Random(7),
    )
    return TestClient(create_app(library=LibraryService(albums), rediscover=rediscover))


@pytest.fixture
def client(library: Library, tmp_path: Path, clock: Clock) -> TestClient:
    return build_client(library, tmp_path / "user.db", clock)


def album_id(client: TestClient, title: str) -> int:
    for album in client.get("/api/albums?limit=100").json()["items"]:
        if album["title"] == title:
            return int(album["id"])
    raise AssertionError(title)


def view(client: TestClient, title: str) -> None:
    assert client.post(f"/api/albums/{album_id(client, title)}/view").status_code == 204


def rediscover(client: TestClient, count: int | None = None) -> Any:
    response = client.get("/api/albums/rediscover", params={"count": count} if count else None)
    assert response.status_code == 200, response.text
    return response.json()


def titles(albums: Any) -> list[str]:
    return [a["title"] for a in albums]


def test_offers_every_album_when_none_has_been_viewed(client: TestClient) -> None:
    found = rediscover(client, 12)

    assert sorted(titles(found)) == sorted(
        ["Low", '"Heroes"', "Another Green World", "Discreet Music"]
    )
    assert set(found[0]) == {
        "id",
        "title",
        "artist_id",
        "artist_name",
        "year",
        "track_count",
        "cover_url",
    }


def test_viewed_albums_move_to_the_back_oldest_view_first(client: TestClient, clock: Clock) -> None:
    view(client, "Low")
    clock.now += timedelta(days=1)
    view(client, "Another Green World")

    found = titles(rediscover(client, 12))

    assert found[-2:] == ["Low", "Another Green World"]


def test_viewing_again_makes_an_album_the_most_recent(client: TestClient, clock: Clock) -> None:
    view(client, "Low")
    clock.now += timedelta(days=1)
    view(client, "Another Green World")
    clock.now += timedelta(days=1)
    view(client, "Low")

    assert titles(rediscover(client, 12))[-2:] == ["Another Green World", "Low"]


def test_the_count_limits_the_answer(client: TestClient) -> None:
    assert len(rediscover(client, 2)) == 2


def test_the_default_is_six_albums(client: TestClient) -> None:
    assert len(rediscover(client)) == 4  # the test library only has four albums


@pytest.mark.parametrize("count", [0, 13])
def test_a_count_outside_the_limits_is_rejected(client: TestClient, count: int) -> None:
    assert client.get("/api/albums/rediscover", params={"count": count}).status_code == 422


def test_viewing_an_unknown_album_is_not_found(client: TestClient) -> None:
    assert client.post("/api/albums/9999/view").status_code == 404


def test_history_is_kept_when_the_library_is_rebuilt(
    library: Library, tmp_path: Path, clock: Clock
) -> None:
    user_db = tmp_path / "user.db"
    first = build_client(library, user_db, clock)
    view(first, "Low")

    second = build_client(library, user_db, clock)

    assert titles(rediscover(second, 12))[-1] == "Low"
