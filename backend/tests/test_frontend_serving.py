from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wj_music.api.app import create_app
from wj_music.bootstrap import build_app, default_frontend_dir
from wj_music.config import Settings
from wj_music.services.scan import ScanService, ScanSummary

SUMMARY = ScanSummary(
    added=0, changed=0, removed=0, unchanged=1, errors=0, tracks=1, albums=1, artists=1
)


@pytest.fixture
def dist(tmp_path: Path) -> Path:
    folder = tmp_path / "dist"
    (folder / "assets").mkdir(parents=True)
    (folder / "index.html").write_text("<html>the app</html>", encoding="utf-8")
    (folder / "assets" / "app.js").write_text("console.log('app')", encoding="utf-8")
    (folder / "manifest.webmanifest").write_text('{"name": "WJ"}', encoding="utf-8")
    (tmp_path / "secret.txt").write_text("not for the web", encoding="utf-8")
    return folder


@pytest.fixture
def client(dist: Path) -> TestClient:
    return TestClient(create_app(scan=ScanService(lambda: SUMMARY), frontend_dir=dist))


def test_the_root_serves_the_app(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "the app" in response.text
    assert response.headers["content-type"].startswith("text/html")


@pytest.mark.parametrize("path", ["/albums", "/albums/3", "/explore", "/lyrics/search"])
def test_page_urls_fall_back_to_the_app_so_reloading_works(client: TestClient, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    assert "the app" in response.text


def test_built_files_are_served_as_they_are(client: TestClient) -> None:
    assert client.get("/assets/app.js").text == "console.log('app')"
    assert client.get("/manifest.webmanifest").json() == {"name": "WJ"}


def test_the_app_shell_is_not_cached_but_built_assets_may_be(client: TestClient) -> None:
    assert client.get("/").headers["cache-control"] == "no-cache"
    assert "cache-control" not in client.get("/assets/app.js").headers


def test_unknown_api_paths_stay_json_not_found(client: TestClient) -> None:
    response = client.get("/api/nothing-here")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/json"


def test_api_and_health_are_unaffected(client: TestClient) -> None:
    assert client.get("/health").json()["status"] == "ok"
    assert client.post("/api/scan").status_code == 200


@pytest.mark.parametrize(
    "path", ["/%2e%2e/secret.txt", "/..%2fsecret.txt", "/assets/../../secret.txt"]
)
def test_files_outside_the_build_folder_are_never_served(client: TestClient, path: str) -> None:
    response = client.get(path)

    assert "not for the web" not in response.text


def test_without_a_frontend_folder_nothing_is_served() -> None:
    assert TestClient(create_app()).get("/").status_code == 404


def test_a_folder_without_index_html_is_ignored(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    assert TestClient(create_app(frontend_dir=empty)).get("/").status_code == 404


def settings_for(tmp_path: Path, frontend_dir: Path | None, *, allow_remote: bool) -> Settings:
    return Settings(
        music_path=None,
        data_dir=tmp_path / "data",
        host="127.0.0.1",
        port=8000,
        allow_remote=allow_remote,
        frontend_dir=frontend_dir,
    )


def test_the_built_app_serves_the_configured_frontend_folder(tmp_path: Path, dist: Path) -> None:
    client = TestClient(build_app(settings_for(tmp_path, dist, allow_remote=False)))

    assert "the app" in client.get("/albums/1").text
    assert client.get("/api/albums").status_code == 200


def test_the_frontend_stays_open_when_the_api_needs_a_token(tmp_path: Path, dist: Path) -> None:
    client = TestClient(build_app(settings_for(tmp_path, dist, allow_remote=True)))

    assert client.get("/").status_code == 200
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/api/albums").status_code == 401


def test_a_missing_configured_folder_just_means_no_frontend(tmp_path: Path) -> None:
    client = TestClient(build_app(settings_for(tmp_path, tmp_path / "nope", allow_remote=False)))

    assert client.get("/").status_code == 404
    assert client.get("/api/albums").status_code == 200


def test_the_default_folder_is_the_frontend_build_in_the_repository() -> None:
    folder = default_frontend_dir()

    assert folder.parts[-2:] == ("frontend", "dist")
    assert (folder.parent / "package.json").is_file()
