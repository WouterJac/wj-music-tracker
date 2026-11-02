import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from flac_builder import build_flac
from wj_music.cli import app
from wj_music.storage.auth_files import FilePairingCodes

runner = CliRunner()


@pytest.fixture
def music(tmp_path: Path) -> Path:
    folder = tmp_path / "music"
    folder.mkdir()
    return folder


@pytest.fixture
def config_file(tmp_path: Path, music: Path) -> Path:
    data_dir = tmp_path / "data"
    path = tmp_path / "config.toml"
    path.write_text(
        f'[library]\nmusic_path = "{music.as_posix()}"\n\n'
        f'[data]\ndirectory = "{data_dir.as_posix()}"\n',
        encoding="utf-8",
    )
    return path


def add_track(folder: Path, name: str, **tags: list[str]) -> Path:
    path = folder / name
    path.write_bytes(build_flac(tags=tags))
    return path


def scan(config_file: Path) -> Any:
    return runner.invoke(app, ["scan", "--config", str(config_file)])


def test_scan_prints_a_summary_of_the_library(music: Path, config_file: Path) -> None:
    add_track(music, "01.flac", TITLE=["One"], ARTIST=["Band"], ALBUM=["Album"])
    add_track(music, "02.flac", TITLE=["Two"], ARTIST=["Band"], ALBUM=["Album"])

    result = scan(config_file)

    assert result.exit_code == 0, result.output
    assert "Added: 2" in result.output
    assert "Changed: 0" in result.output
    assert "Removed: 0" in result.output
    assert "Errors: 0" in result.output
    assert "Library: 2 tracks, 1 album, 1 artist" in result.output


def test_scan_creates_the_database_in_the_data_directory(
    music: Path, config_file: Path, tmp_path: Path
) -> None:
    add_track(music, "01.flac", TITLE=["One"])

    scan(config_file)

    assert (tmp_path / "data" / "library.db").is_file()


def test_second_scan_reports_unchanged_files(music: Path, config_file: Path) -> None:
    add_track(music, "01.flac", TITLE=["One"])
    scan(config_file)

    result = scan(config_file)

    assert "Added: 0" in result.output
    assert "Unchanged: 1" in result.output


def test_scan_lists_changed_and_removed_files(music: Path, config_file: Path) -> None:
    changed = add_track(music, "01.flac", TITLE=["Before"])
    removed = add_track(music, "02.flac", TITLE=["Doomed"])
    scan(config_file)
    add_track(music, "01.flac", TITLE=["A noticeably longer title"])
    removed.unlink()

    result = scan(config_file)

    assert "Changed: 1" in result.output
    assert "Removed: 1" in result.output
    assert changed.name in result.output
    assert removed.name in result.output


def test_scan_lists_unreadable_files_and_still_succeeds(music: Path, config_file: Path) -> None:
    add_track(music, "01.flac", TITLE=["Fine"])
    (music / "broken.flac").write_bytes(b"not audio")

    result = scan(config_file)

    assert result.exit_code == 0, result.output
    assert "Errors: 1" in result.output
    assert "broken.flac" in result.output
    assert "Library: 1 track" in result.output


def test_scan_without_a_music_path_explains_how_to_set_it(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(f'[data]\ndirectory = "{(tmp_path / "data").as_posix()}"\n', encoding="utf-8")

    result = runner.invoke(app, ["scan", "--config", str(config)], env={"WJ_MUSIC_PATH": ""})

    assert result.exit_code == 2
    assert "WJ_MUSIC_PATH" in result.output
    assert "music_path" in result.output


def test_scan_of_a_missing_music_folder_fails_without_touching_the_library(
    music: Path, config_file: Path
) -> None:
    add_track(music, "01.flac", TITLE=["Keep me"])
    scan(config_file)
    (music / "01.flac").unlink()
    music.rmdir()

    result = scan(config_file)

    assert result.exit_code == 1
    assert "not found" in result.output


def test_serve_starts_uvicorn_on_the_configured_loopback_address(
    config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_run(application: object, **kwargs: Any) -> None:
        calls.append({"application": application, **kwargs})

    monkeypatch.setattr("wj_music.cli.uvicorn.run", fake_run)

    result = runner.invoke(app, ["serve", "--config", str(config_file)])

    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["port"] == 8000


def test_invalid_config_file_gives_a_readable_error(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text('[library]\nmusic_path = "D:\\Music"\n', encoding="utf-8")

    result = runner.invoke(app, ["scan", "--config", str(config)])

    assert result.exit_code == 2
    assert "config.toml" in result.output
    assert "Traceback" not in result.output


@pytest.fixture
def remote_config_file(tmp_path: Path, music: Path) -> Path:
    path = tmp_path / "remote.toml"
    path.write_text(
        f'[library]\nmusic_path = "{music.as_posix()}"\n\n'
        f'[data]\ndirectory = "{(tmp_path / "data").as_posix()}"\n\n'
        '[server]\nhost = "0.0.0.0"\nallow_remote = true\n',
        encoding="utf-8",
    )
    return path


def test_pair_prints_a_code_that_the_server_accepts_once(
    remote_config_file: Path, tmp_path: Path
) -> None:
    result = runner.invoke(app, ["pair", "--config", str(remote_config_file)])

    assert result.exit_code == 0, result.output
    match = re.search(r"Pairing code: ([A-Z2-9]{4})-([A-Z2-9]{4})", result.output)
    assert match is not None, result.output
    assert "5 minutes" in result.output
    token = (tmp_path / "data" / "auth_token").read_text(encoding="utf-8").strip()
    assert token not in result.output
    codes = FilePairingCodes(tmp_path / "data" / "pairing.json")
    assert codes.redeem("".join(match.groups()), datetime.now(UTC))
    assert not codes.redeem("".join(match.groups()), datetime.now(UTC))


def test_pair_refuses_when_remote_access_is_off(config_file: Path) -> None:
    result = runner.invoke(app, ["pair", "--config", str(config_file)])

    assert result.exit_code == 2
    assert "allow_remote" in result.output


def test_serve_says_so_when_remote_access_is_on(
    remote_config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("wj_music.cli.uvicorn.run", lambda *args, **kwargs: None)

    result = runner.invoke(app, ["serve", "--config", str(remote_config_file)])

    assert result.exit_code == 0, result.output
    assert "Remote access is on" in result.output
    assert "wj-music pair" in result.output
