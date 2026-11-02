from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wj_music.api.app import create_app
from wj_music.bootstrap import build_app
from wj_music.config import Settings
from wj_music.domain.auth import FailureLimiter
from wj_music.services.auth import AuthService
from wj_music.services.scan import ScanService, ScanSummary
from wj_music.storage.auth_files import FilePairingCodes

START = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
TOKEN = "t" * 40
SUMMARY = ScanSummary(
    added=0, changed=0, removed=0, unchanged=1, errors=0, tracks=1, albums=1, artists=1
)


class Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def auth(tmp_path: Path, clock: Clock) -> AuthService:
    return AuthService(
        TOKEN,
        FilePairingCodes(tmp_path / "pairing.json"),
        FailureLimiter(max_failures=3, window=timedelta(seconds=60)),
        clock=clock,
    )


@pytest.fixture
def client(auth: AuthService) -> TestClient:
    return TestClient(create_app(scan=ScanService(lambda: SUMMARY), auth=auth))


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_stays_open(client: TestClient) -> None:
    assert client.get("/health").status_code == 200


def test_api_without_a_token_is_unauthorized(client: TestClient) -> None:
    response = client.post("/api/scan")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_api_with_the_token_is_allowed(client: TestClient) -> None:
    assert client.post("/api/scan", headers=bearer(TOKEN)).status_code == 200


@pytest.mark.parametrize("header", ["Bearer wrong", "Basic " + TOKEN, TOKEN, "Bearer", "Bearer  "])
def test_api_with_a_bad_authorization_header_is_unauthorized(
    client: TestClient, header: str
) -> None:
    assert client.post("/api/scan", headers={"Authorization": header}).status_code == 401


def test_requests_without_a_token_are_never_rate_limited(client: TestClient) -> None:
    # A page that has not paired yet fires many requests; they must not lock the phone out.
    for _ in range(10):
        assert client.post("/api/scan").status_code == 401

    assert client.post("/api/scan", headers=bearer(TOKEN)).status_code == 200


def test_repeated_wrong_tokens_are_rate_limited(client: TestClient) -> None:
    for _ in range(3):
        assert client.post("/api/scan", headers=bearer("wrong")).status_code == 401

    assert client.post("/api/scan", headers=bearer("wrong")).status_code == 429
    # Even the right token waits, so a guess cannot be confirmed while blocked.
    assert client.post("/api/scan", headers=bearer(TOKEN)).status_code == 429


def test_the_block_lifts_after_the_window(client: TestClient, clock: Clock) -> None:
    for _ in range(3):
        client.post("/api/scan", headers=bearer("wrong"))
    clock.now += timedelta(seconds=61)

    assert client.post("/api/scan", headers=bearer(TOKEN)).status_code == 200


def test_pairing_with_a_valid_code_returns_the_token_once(
    client: TestClient, auth: AuthService
) -> None:
    code, _ = auth.issue_pairing_code()

    first = client.post("/api/pair", json={"code": code})
    second = client.post("/api/pair", json={"code": code})

    assert first.status_code == 200
    assert first.json() == {"token": TOKEN}
    assert second.status_code == 401


def test_pairing_accepts_the_code_as_displayed(client: TestClient, auth: AuthService) -> None:
    code, _ = auth.issue_pairing_code()
    typed = f" {code[:4].lower()}-{code[4:].lower()} "

    assert client.post("/api/pair", json={"code": typed}).status_code == 200


def test_pairing_with_a_wrong_code_is_unauthorized(client: TestClient, auth: AuthService) -> None:
    auth.issue_pairing_code()

    response = client.post("/api/pair", json={"code": "WRONG999"})

    assert response.status_code == 401
    assert TOKEN not in response.text


def test_pairing_with_an_expired_code_is_unauthorized(
    client: TestClient, auth: AuthService, clock: Clock
) -> None:
    code, expires_at = auth.issue_pairing_code()
    assert expires_at == START + timedelta(minutes=5)
    clock.now += timedelta(minutes=5, seconds=1)

    assert client.post("/api/pair", json={"code": code}).status_code == 401


def test_repeated_wrong_codes_are_rate_limited_even_for_the_right_code(
    client: TestClient, auth: AuthService
) -> None:
    code, _ = auth.issue_pairing_code()
    for _ in range(3):
        assert client.post("/api/pair", json={"code": "WRONG999"}).status_code == 401

    assert client.post("/api/pair", json={"code": code}).status_code == 429


def test_a_missing_code_is_a_validation_error(client: TestClient) -> None:
    assert client.post("/api/pair", json={}).status_code == 422


def test_without_auth_the_app_stays_open_and_has_no_pairing_route() -> None:
    client = TestClient(create_app(scan=ScanService(lambda: SUMMARY)))

    assert client.post("/api/scan").status_code == 200
    assert client.post("/api/pair", json={"code": "ABCD2345"}).status_code == 404


def settings_for(tmp_path: Path, *, allow_remote: bool) -> Settings:
    music = tmp_path / "music"
    music.mkdir(exist_ok=True)
    return Settings(
        music_path=music,
        data_dir=tmp_path / "data",
        host="127.0.0.1",
        port=8000,
        allow_remote=allow_remote,
    )


def test_the_built_app_stays_open_when_remote_access_is_off(tmp_path: Path) -> None:
    client = TestClient(build_app(settings_for(tmp_path, allow_remote=False)))

    assert client.get("/api/albums").status_code == 200
    assert not (tmp_path / "data" / "auth_token").exists()


def test_the_built_app_requires_the_stored_token_when_remote_access_is_on(
    tmp_path: Path,
) -> None:
    client = TestClient(build_app(settings_for(tmp_path, allow_remote=True)))
    token = (tmp_path / "data" / "auth_token").read_text(encoding="utf-8").strip()

    assert client.get("/api/albums").status_code == 401
    assert client.get("/api/albums", headers=bearer(token)).status_code == 200
    assert client.get("/health").status_code == 200
