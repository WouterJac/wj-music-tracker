import json
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, select

from conftest import Library
from wj_music.api.app import create_app
from wj_music.services.library import LibraryService
from wj_music.services.tracks import TrackService
from wj_music.storage.library_reader import SqlLibraryReader
from wj_music.storage.models import TrackRow
from wj_music.storage.track_reader import SqlTrackReader

TRACK_KEYS = {
    "id",
    "title",
    "disc",
    "number",
    "duration_seconds",
    "sample_rate",
    "bit_depth",
    "channels",
    "album_id",
    "album_title",
    "artist_id",
    "artist_name",
    "cover_url",
    "lyrics",
}
HIT_KEYS = {"track_id", "title", "album_id", "album_title", "artist_id", "artist_name", "snippet"}


def make_client(engine: Engine, library: Library | None = None) -> TestClient:
    return TestClient(
        create_app(
            library=LibraryService(SqlLibraryReader(engine)),
            tracks=TrackService(SqlTrackReader(engine)),
            covers_dir=library.covers_dir if library else None,
        )
    )


@pytest.fixture
def client(library: Library) -> TestClient:
    return make_client(library.engine, library)


def get_json(client: TestClient, url: str) -> Any:
    response = client.get(url)
    assert response.status_code == 200, response.text
    return response.json()


def track_id(client: TestClient, title: str) -> int:
    for album in get_json(client, "/api/albums?limit=100")["items"]:
        for track in get_json(client, f"/api/albums/{album['id']}")["tracks"]:
            if track["title"] == title:
                return int(track["id"])
    raise AssertionError(f"no track titled {title}")


class TestTrackDetail:
    def test_has_album_artist_links_and_audio_details(self, client: TestClient) -> None:
        body = get_json(client, f"/api/tracks/{track_id(client, 'Breaking Glass')}")

        assert set(body) == TRACK_KEYS
        assert body["title"] == "Breaking Glass"
        assert body["album_title"] == "Low"
        assert body["artist_name"] == "David Bowie"
        assert body["cover_url"] == f"/api/albums/{body['album_id']}/cover"
        assert body["sample_rate"] == 44100

    def test_synced_lyrics_come_as_timed_lines(self, client: TestClient) -> None:
        body = get_json(client, f"/api/tracks/{track_id(client, 'Breaking Glass')}")

        assert set(body["lyrics"]) == {"plain", "synced_lines"}
        assert body["lyrics"]["plain"] == "Baby, I'm not special\nBreaking glass"
        assert body["lyrics"]["synced_lines"] == [
            {"time_seconds": 1.0, "text": "Baby, I'm not special"},
            {"time_seconds": 6.5, "text": "Breaking glass"},
        ]

    def test_unsynced_lyrics_have_no_timed_lines(self, client: TestClient) -> None:
        body = get_json(client, f"/api/tracks/{track_id(client, 'Sky Saw')}")

        assert body["lyrics"] == {
            "plain": "Wind in the sky\nand the moon is high",
            "synced_lines": None,
        }

    def test_track_without_lyrics_has_null_lyrics(self, client: TestClient) -> None:
        body = get_json(client, f"/api/tracks/{track_id(client, 'Speed of Life')}")

        assert body["lyrics"] is None

    def test_track_without_album_has_null_links_and_cover(
        self, client: TestClient, library: Library
    ) -> None:
        with library.engine.connect() as conn:
            loose_id = conn.execute(
                select(TrackRow.id).where(TrackRow.title == "Loose track")
            ).scalar_one()

        body = get_json(client, f"/api/tracks/{loose_id}")

        assert body["album_id"] is None
        assert body["album_title"] is None
        assert body["artist_id"] is None
        assert body["cover_url"] is None

    def test_unknown_track_is_404(self, client: TestClient) -> None:
        response = client.get("/api/tracks/9999")

        assert response.status_code == 404
        assert response.json() == {"detail": "Track not found"}

    def test_non_numeric_id_is_422(self, client: TestClient) -> None:
        assert client.get("/api/tracks/abc").status_code == 422


class TestLyricsSearch:
    def test_returns_a_page_of_hits_with_snippets(self, client: TestClient) -> None:
        body = get_json(client, "/api/lyrics/search?q=heroes")

        assert set(body) == {"items", "total", "limit", "offset"}
        assert body["total"] == 1
        assert set(body["items"][0]) == HIT_KEYS
        assert body["items"][0]["title"] == "Beauty and the Beast"
        assert "heroes" in body["items"][0]["snippet"].lower()

    def test_hit_links_to_its_track(self, client: TestClient) -> None:
        hit = get_json(client, "/api/lyrics/search?q=heroes")["items"][0]

        assert hit["track_id"] == track_id(client, "Beauty and the Beast")

    def test_paging(self, client: TestClient) -> None:
        body = get_json(client, "/api/lyrics/search?q=in&limit=2&offset=1")

        assert [i["title"] for i in body["items"]] == ["Breaking Glass", "Sky Saw"]
        assert body["total"] == 3
        assert (body["limit"], body["offset"]) == (2, 1)

    @pytest.mark.parametrize(
        "query",
        ["", "q=", "q=a", "q=in&limit=0", "q=in&limit=101", "q=in&offset=-1", f"q={'x' * 101}"],
    )
    def test_invalid_requests_are_422(self, client: TestClient, query: str) -> None:
        assert client.get(f"/api/lyrics/search?{query}").status_code == 422

    def test_blank_search_finds_nothing(self, client: TestClient) -> None:
        body = get_json(client, "/api/lyrics/search?q=%20%20%20")

        assert body["items"] == []
        assert body["total"] == 0

    def test_wildcards_are_literal(self, client: TestClient) -> None:
        assert get_json(client, "/api/lyrics/search?q=%25%25")["total"] == 0


class TestAlbumTracksLinkToLyrics:
    def test_album_detail_tracks_say_whether_they_have_lyrics(self, client: TestClient) -> None:
        low = next(a for a in get_json(client, "/api/albums")["items"] if a["title"] == "Low")

        tracks = get_json(client, f"/api/albums/{low['id']}")["tracks"]

        assert {t["title"]: t["has_lyrics"] for t in tracks} == {
            "Breaking Glass": True,
            "Speed of Life": False,
        }


def test_responses_never_expose_file_system_paths(client: TestClient, library: Library) -> None:
    urls = [
        f"/api/tracks/{track_id(client, 'Breaking Glass')}",
        f"/api/tracks/{track_id(client, 'Sky Saw')}",
        "/api/lyrics/search?q=in",
    ]

    for url in urls:
        text = json.dumps(get_json(client, url))
        assert str(library.music) not in text
        assert str(library.covers_dir) not in text
        assert ".flac" not in text
        assert "file_path" not in text


def test_without_a_track_service_the_routes_are_absent(engine: Engine) -> None:
    bare = TestClient(create_app(library=LibraryService(SqlLibraryReader(engine))))

    assert bare.get("/api/tracks/1").status_code == 404
    assert bare.get("/api/lyrics/search?q=in").status_code == 404
