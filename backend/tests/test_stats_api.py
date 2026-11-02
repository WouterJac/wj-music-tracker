from fastapi.testclient import TestClient

from conftest import Library
from wj_music.api.app import create_app
from wj_music.services.stats import StatsService
from wj_music.storage.stats_reader import SqlStatsReader

KEYS = {
    "tracks",
    "albums",
    "artists",
    "total_duration_seconds",
    "hires_tracks",
    "albums_by_decade",
    "albums_by_year",
    "tracks_by_format",
    "tracks_by_channels",
    "tracks_by_genre",
    "albums_by_track_count",
    "albums_by_length",
    "top_artists",
}


def make_client(library: Library) -> TestClient:
    return TestClient(create_app(stats=StatsService(SqlStatsReader(library.engine))))


def test_stats_endpoint_returns_the_summary(library: Library) -> None:
    response = make_client(library).get("/api/stats")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == KEYS
    assert body["tracks"] == 7
    assert body["albums_by_decade"] == [{"label": "1970s", "count": 4}]
    assert set(body["top_artists"][0]) == {"id", "name", "tracks", "albums"}


def test_stats_never_expose_file_system_paths(library: Library) -> None:
    text = make_client(library).get("/api/stats").text

    assert str(library.music) not in text
    assert ".flac" not in text


def test_stats_endpoint_is_absent_without_a_service() -> None:
    assert TestClient(create_app()).get("/api/stats").status_code == 404
