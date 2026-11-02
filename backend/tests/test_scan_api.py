import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from flac_builder import build_flac
from wj_music.api.app import create_app
from wj_music.bootstrap import build_app
from wj_music.config import Settings
from wj_music.services.scan import ScanService, ScanSummary, ScanUnavailableError

SUMMARY = ScanSummary(
    added=2, changed=1, removed=3, unchanged=10, errors=1, tracks=12, albums=4, artists=2
)


def client_for(service: ScanService) -> TestClient:
    return TestClient(create_app(scan=service))


def test_scan_returns_the_summary() -> None:
    response = client_for(ScanService(lambda: SUMMARY)).post("/api/scan")

    assert response.status_code == 200
    assert response.json() == {
        "added": 2,
        "changed": 1,
        "removed": 3,
        "unchanged": 10,
        "errors": 1,
        "tracks": 12,
        "albums": 4,
        "artists": 2,
    }


def test_scan_route_is_absent_without_a_service() -> None:
    assert TestClient(create_app()).post("/api/scan").status_code == 404


def test_scan_that_cannot_run_reports_why() -> None:
    def unavailable() -> ScanSummary:
        raise ScanUnavailableError("No music folder set.")

    response = client_for(ScanService(unavailable)).post("/api/scan")

    assert response.status_code == 422
    assert response.json() == {"detail": "No music folder set."}


def test_a_second_scan_while_one_runs_is_refused() -> None:
    started = threading.Event()
    release = threading.Event()

    def slow() -> ScanSummary:
        started.set()
        assert release.wait(timeout=5)
        return SUMMARY

    service = ScanService(slow)
    client = client_for(service)
    first: list[int] = []
    worker = threading.Thread(target=lambda: first.append(client.post("/api/scan").status_code))
    worker.start()
    try:
        assert started.wait(timeout=5)
        second = client.post("/api/scan")
    finally:
        release.set()
        worker.join(timeout=5)

    assert second.status_code == 409
    assert first == [200]


def test_a_scan_can_run_again_after_one_failed() -> None:
    calls = {"count": 0}

    def flaky() -> ScanSummary:
        calls["count"] += 1
        if calls["count"] == 1:
            raise ScanUnavailableError("Music folder not found.")
        return SUMMARY

    client = client_for(ScanService(flaky))

    assert client.post("/api/scan").status_code == 422
    assert client.post("/api/scan").status_code == 200


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    music = tmp_path / "music"
    music.mkdir()
    return Settings(music_path=music, data_dir=tmp_path / "data", host="127.0.0.1", port=8000)


def test_the_built_app_scans_the_music_folder_and_serves_the_result(settings: Settings) -> None:
    assert settings.music_path is not None
    client = TestClient(build_app(settings))
    assert client.get("/api/albums").json()["total"] == 0

    (settings.music_path / "one.flac").write_bytes(
        build_flac(tags={"ARTIST": ["Brian Eno"], "ALBUM": ["Another Green World"]})
    )
    response = client.post("/api/scan")

    assert response.status_code == 200
    body = response.json()
    assert (body["added"], body["tracks"], body["albums"], body["artists"]) == (1, 1, 1, 1)
    assert client.get("/api/albums").json()["total"] == 1


def test_the_built_app_refuses_to_scan_without_a_music_folder(tmp_path: Path) -> None:
    settings = Settings(music_path=None, data_dir=tmp_path / "data", host="127.0.0.1", port=8000)

    response = TestClient(build_app(settings)).post("/api/scan")

    assert response.status_code == 422
    assert "music folder" in response.json()["detail"].lower()


def test_the_built_app_refuses_to_scan_a_missing_music_folder(tmp_path: Path) -> None:
    settings = Settings(
        music_path=tmp_path / "unplugged", data_dir=tmp_path / "data", host="127.0.0.1", port=8000
    )

    response = TestClient(build_app(settings)).post("/api/scan")

    assert response.status_code == 422
    assert "unplugged" in response.json()["detail"]
