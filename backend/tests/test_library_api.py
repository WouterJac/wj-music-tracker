import json
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from conftest import COVER_BYTES, Library
from wj_music.api.app import create_app
from wj_music.services.library import LibraryService
from wj_music.storage.library_reader import SqlLibraryReader

ALBUM_KEYS = {"id", "title", "artist_id", "artist_name", "year", "track_count", "cover_url"}
TRACK_KEYS = {
    "id",
    "disc",
    "number",
    "title",
    "duration_seconds",
    "sample_rate",
    "bit_depth",
    "channels",
    "has_lyrics",
}


@pytest.fixture
def client(library: Library) -> TestClient:
    service = LibraryService(SqlLibraryReader(library.engine))
    return TestClient(create_app(library=service, covers_dir=library.covers_dir))


def get_json(client: TestClient, url: str) -> Any:
    response = client.get(url)
    assert response.status_code == 200, response.text
    return response.json()


def album_by_title(client: TestClient, title: str) -> dict[str, Any]:
    items = get_json(client, "/api/albums?limit=100")["items"]
    return next(item for item in items if item["title"] == title)


class TestAlbumList:
    def test_returns_a_page_with_the_expected_shape(self, client: TestClient) -> None:
        body = get_json(client, "/api/albums")

        assert set(body) == {"items", "total", "limit", "offset"}
        assert body["total"] == 4
        assert body["limit"] == 50
        assert body["offset"] == 0
        assert {item["title"] for item in body["items"]} == {
            "Another Green World",
            "Discreet Music",
            '"Heroes"',
            "Low",
        }
        assert set(body["items"][0]) == ALBUM_KEYS

    def test_cover_url_points_at_the_cover_endpoint_or_is_null(self, client: TestClient) -> None:
        low = album_by_title(client, "Low")
        heroes = album_by_title(client, '"Heroes"')

        assert low["cover_url"] == f"/api/albums/{low['id']}/cover"
        assert heroes["cover_url"] is None

    @pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "limit=abc"])
    def test_paging_parameters_are_bounded(self, client: TestClient, query: str) -> None:
        assert client.get(f"/api/albums?{query}").status_code == 422

    def test_largest_allowed_page_is_accepted(self, client: TestClient) -> None:
        assert client.get("/api/albums?limit=100").status_code == 200

    def test_paging_window(self, client: TestClient) -> None:
        body = get_json(client, "/api/albums?limit=1&offset=3")

        assert [item["title"] for item in body["items"]] == ["Low"]
        assert body["total"] == 4
        assert body["limit"] == 1
        assert body["offset"] == 3

    def test_search_filter(self, client: TestClient) -> None:
        body = get_json(client, "/api/albums?q=eno")

        assert body["total"] == 2

    def test_year_filter(self, client: TestClient) -> None:
        body = get_json(client, "/api/albums?year=1977")

        assert [item["title"] for item in body["items"]] == ['"Heroes"', "Low"]

    def test_artist_filter(self, client: TestClient) -> None:
        eno = get_json(client, "/api/artists?q=eno")["items"][0]

        body = get_json(client, f"/api/albums?artist_id={eno['id']}")

        assert body["total"] == 2

    def test_year_must_be_a_number(self, client: TestClient) -> None:
        assert client.get("/api/albums?year=abc").status_code == 422

    def test_empty_library_returns_an_empty_page(self, engine: Engine) -> None:
        service = LibraryService(SqlLibraryReader(engine))
        empty = TestClient(create_app(library=service))

        body = get_json(empty, "/api/albums")

        assert body["items"] == []
        assert body["total"] == 0


class TestAlbumDetail:
    def test_includes_sorted_tracks_with_technical_info(self, client: TestClient) -> None:
        low = album_by_title(client, "Low")

        body = get_json(client, f"/api/albums/{low['id']}")

        assert set(body) == ALBUM_KEYS | {"total_duration_seconds", "tracks"}
        assert body["total_duration_seconds"] == 350
        assert [t["title"] for t in body["tracks"]] == ["Breaking Glass", "Speed of Life"]
        assert set(body["tracks"][0]) == TRACK_KEYS
        assert body["tracks"][0]["number"] == 1
        assert body["tracks"][0]["sample_rate"] == 44100
        assert body["tracks"][0]["bit_depth"] == 16
        assert body["tracks"][0]["channels"] == 2

    def test_unknown_album_is_404(self, client: TestClient) -> None:
        response = client.get("/api/albums/9999")

        assert response.status_code == 404
        assert response.json() == {"detail": "Album not found"}

    def test_non_numeric_id_is_422(self, client: TestClient) -> None:
        assert client.get("/api/albums/abc").status_code == 422


class TestCover:
    def test_serves_the_cached_image(self, client: TestClient) -> None:
        low = album_by_title(client, "Low")

        response = client.get(low["cover_url"])

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert response.content == COVER_BYTES
        assert "max-age" in response.headers["cache-control"]

    def test_album_without_cover_is_404(self, client: TestClient) -> None:
        heroes = album_by_title(client, '"Heroes"')

        assert client.get(f"/api/albums/{heroes['id']}/cover").status_code == 404

    def test_unknown_album_is_404(self, client: TestClient) -> None:
        assert client.get("/api/albums/9999/cover").status_code == 404


class TestArtists:
    def test_list_has_album_counts(self, client: TestClient) -> None:
        body = get_json(client, "/api/artists")

        assert set(body) == {"items", "total", "limit", "offset"}
        assert [(a["name"], a["album_count"]) for a in body["items"]] == [
            ("Brian Eno", 2),
            ("David Bowie", 2),
        ]
        assert set(body["items"][0]) == {"id", "name", "album_count"}

    def test_search(self, client: TestClient) -> None:
        body = get_json(client, "/api/artists?q=bow")

        assert [a["name"] for a in body["items"]] == ["David Bowie"]

    @pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
    def test_paging_parameters_are_bounded(self, client: TestClient, query: str) -> None:
        assert client.get(f"/api/artists?{query}").status_code == 422

    def test_detail_lists_albums(self, client: TestClient) -> None:
        bowie = get_json(client, "/api/artists?q=bowie")["items"][0]

        body = get_json(client, f"/api/artists/{bowie['id']}")

        assert set(body) == {"id", "name", "albums"}
        assert [a["title"] for a in body["albums"]] == ['"Heroes"', "Low"]
        assert set(body["albums"][0]) == ALBUM_KEYS

    def test_unknown_artist_is_404(self, client: TestClient) -> None:
        response = client.get("/api/artists/9999")

        assert response.status_code == 404
        assert response.json() == {"detail": "Artist not found"}


def test_years_are_listed_newest_first(client: TestClient) -> None:
    assert get_json(client, "/api/years") == [1977, 1975]


def test_responses_never_expose_file_system_paths(client: TestClient, library: Library) -> None:
    low = album_by_title(client, "Low")
    bowie = get_json(client, "/api/artists?q=bowie")["items"][0]
    urls = [
        "/api/albums",
        f"/api/albums/{low['id']}",
        "/api/artists",
        f"/api/artists/{bowie['id']}",
        "/api/years",
    ]

    for url in urls:
        text = json.dumps(get_json(client, url))
        assert str(library.music) not in text
        assert str(library.covers_dir) not in text
        assert ".flac" not in text
        assert "file_path" not in text


def test_without_a_library_only_health_is_available() -> None:
    bare = TestClient(create_app())

    assert bare.get("/health").status_code == 200
    assert bare.get("/api/albums").status_code == 404
