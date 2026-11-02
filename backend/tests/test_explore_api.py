from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Library
from explore_helpers import GENRES, tag_tracks
from wj_music.api.app import create_app
from wj_music.services.library import LibraryService
from wj_music.storage.library_reader import SqlLibraryReader


@pytest.fixture
def client(library: Library) -> TestClient:
    tag_tracks(library.engine, GENRES)
    return TestClient(create_app(library=LibraryService(SqlLibraryReader(library.engine))))


def get_json(client: TestClient, url: str) -> Any:
    response = client.get(url)
    assert response.status_code == 200, response.text
    return response.json()


def test_genres_endpoint(client: TestClient) -> None:
    assert get_json(client, "/api/genres") == [
        {"name": "Ambient", "album_count": 2},
        {"name": "Rock", "album_count": 2},
        {"name": "Art Rock", "album_count": 1},
    ]


def test_albums_can_be_filtered_by_genre_and_decade(client: TestClient) -> None:
    body = get_json(client, "/api/albums?genre=Rock&decade=1970")

    assert body["total"] == 2
    assert {a["title"] for a in body["items"]} == {"Low", '"Heroes"'}


def test_decade_must_be_a_multiple_of_ten(client: TestClient) -> None:
    assert client.get("/api/albums?decade=1975").status_code == 422


class TestRandom:
    def test_returns_albums_with_the_usual_shape(self, client: TestClient) -> None:
        albums = get_json(client, "/api/albums/random?count=2")

        assert len(albums) == 2
        assert set(albums[0]) == {
            "id",
            "title",
            "artist_id",
            "artist_name",
            "year",
            "track_count",
            "cover_url",
        }

    def test_defaults_to_one_album(self, client: TestClient) -> None:
        assert len(get_json(client, "/api/albums/random")) == 1

    def test_respects_filters(self, client: TestClient) -> None:
        albums = get_json(client, "/api/albums/random?count=12&genre=ambient")

        assert {a["title"] for a in albums} == {"Another Green World", "Discreet Music"}

    @pytest.mark.parametrize("count", [0, 13, "x"])
    def test_count_is_limited_to_1_through_12(self, client: TestClient, count: object) -> None:
        assert client.get(f"/api/albums/random?count={count}").status_code == 422

    def test_is_not_mistaken_for_an_album_id(self, client: TestClient) -> None:
        assert client.get("/api/albums/random").status_code == 200
