from pathlib import Path

import pytest

from wj_music.config import DEFAULT_HOST, DEFAULT_PORT, find_config_file, load_settings


def write_config(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_defaults_without_config_file(tmp_path: Path) -> None:
    settings = load_settings(tmp_path / "missing.toml", {"LOCALAPPDATA": str(tmp_path)})

    assert settings.music_path is None
    assert settings.data_dir == tmp_path / "WJMusicTracker"
    assert settings.host == DEFAULT_HOST
    assert settings.port == DEFAULT_PORT


def test_data_dir_falls_back_to_home_when_localappdata_unset() -> None:
    settings = load_settings(env={})

    assert settings.data_dir == Path.home() / "AppData" / "Local" / "WJMusicTracker"


def test_config_file_overrides_defaults(tmp_path: Path) -> None:
    config = write_config(
        tmp_path / "config.local.toml",
        """
[library]
music_path = "E:\\\\Music"

[data]
directory = "F:\\\\data"

[server]
host = "127.0.0.1"
port = 9000
""",
    )

    settings = load_settings(config, {"LOCALAPPDATA": str(tmp_path)})

    assert settings.music_path == Path("E:\\Music")
    assert settings.data_dir == Path("F:\\data")
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000


def test_empty_music_path_in_file_means_unset(tmp_path: Path) -> None:
    config = write_config(tmp_path / "config.local.toml", '[library]\nmusic_path = ""\n')

    settings = load_settings(config, {})

    assert settings.music_path is None


def test_environment_variable_overrides_config_file(tmp_path: Path) -> None:
    config = write_config(tmp_path / "config.local.toml", '[library]\nmusic_path = "E:\\\\Music"\n')

    settings = load_settings(config, {"WJ_MUSIC_PATH": "G:\\Flac"})

    assert settings.music_path == Path("G:\\Flac")


def test_environment_variable_sets_music_path_without_file(tmp_path: Path) -> None:
    settings = load_settings(tmp_path / "missing.toml", {"WJ_MUSIC_PATH": "G:\\Flac"})

    assert settings.music_path == Path("G:\\Flac")


def test_empty_environment_variable_is_ignored(tmp_path: Path) -> None:
    config = write_config(tmp_path / "config.local.toml", '[library]\nmusic_path = "E:\\\\Music"\n')

    settings = load_settings(config, {"WJ_MUSIC_PATH": ""})

    assert settings.music_path == Path("E:\\Music")


def test_partial_config_keeps_other_defaults(tmp_path: Path) -> None:
    config = write_config(tmp_path / "config.local.toml", "[server]\nport = 8123\n")

    settings = load_settings(config, {"LOCALAPPDATA": str(tmp_path)})

    assert settings.port == 8123
    assert settings.music_path is None
    assert settings.data_dir == tmp_path / "WJMusicTracker"


def test_empty_data_directory_uses_default(tmp_path: Path) -> None:
    config = write_config(tmp_path / "config.local.toml", '[data]\ndirectory = ""\n')

    settings = load_settings(config, {"LOCALAPPDATA": str(tmp_path)})

    assert settings.data_dir == tmp_path / "WJMusicTracker"


@pytest.mark.parametrize("port", ["0", "65536", '"8000"'])
def test_invalid_port_is_rejected(tmp_path: Path, port: str) -> None:
    config = write_config(tmp_path / "config.local.toml", f"[server]\nport = {port}\n")

    with pytest.raises(ValueError, match="server.port"):
        load_settings(config, {})


def test_table_section_must_be_a_table(tmp_path: Path) -> None:
    config = write_config(tmp_path / "config.local.toml", 'server = "localhost"\n')

    with pytest.raises(ValueError, match=r"\[server\]"):
        load_settings(config, {})


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.20", "example.com", ""])
def test_non_loopback_host_is_rejected(tmp_path: Path, host: str) -> None:
    config = write_config(tmp_path / "config.local.toml", f'[server]\nhost = "{host}"\n')

    with pytest.raises(ValueError, match="server.host"):
        load_settings(config, {})


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_loopback_host_is_accepted(tmp_path: Path, host: str) -> None:
    config = write_config(tmp_path / "config.local.toml", f'[server]\nhost = "{host}"\n')

    assert load_settings(config, {}).host == host


class TestFindConfigFile:
    def test_finds_config_in_the_start_folder(self, tmp_path: Path) -> None:
        config = write_config(tmp_path / "config.local.toml", "")

        assert find_config_file(tmp_path, {}) == config

    def test_walks_up_to_a_parent_folder(self, tmp_path: Path) -> None:
        config = write_config(tmp_path / "config.local.toml", "")
        nested = tmp_path / "backend" / "src"
        nested.mkdir(parents=True)

        assert find_config_file(nested, {}) == config

    def test_returns_none_when_no_config_exists(self, tmp_path: Path) -> None:
        assert find_config_file(tmp_path, {}) is None

    def test_environment_variable_names_the_file(self, tmp_path: Path) -> None:
        elsewhere = write_config(tmp_path / "elsewhere.toml", "")

        assert find_config_file(tmp_path, {"WJ_CONFIG": str(elsewhere)}) == elsewhere


def test_invalid_toml_names_the_file_and_the_problem(tmp_path: Path) -> None:
    config = write_config(tmp_path / "config.local.toml", '[library]\nmusic_path = "D:\\Music"\n')

    with pytest.raises(ValueError, match=r"config\.local\.toml.*Unescaped"):
        load_settings(config, {})


def test_remote_access_is_off_by_default(tmp_path: Path) -> None:
    assert load_settings(tmp_path / "missing.toml", {}).allow_remote is False


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.20", "100.64.0.7", "pc.tailnet.ts.net"])
def test_non_loopback_host_is_accepted_when_remote_access_is_allowed(
    tmp_path: Path, host: str
) -> None:
    config = write_config(
        tmp_path / "config.local.toml", f'[server]\nhost = "{host}"\nallow_remote = true\n'
    )

    settings = load_settings(config, {})

    assert (settings.host, settings.allow_remote) == (host, True)


def test_an_empty_host_is_rejected_even_when_remote_access_is_allowed(tmp_path: Path) -> None:
    config = write_config(
        tmp_path / "config.local.toml", '[server]\nhost = ""\nallow_remote = true\n'
    )

    with pytest.raises(ValueError, match="server.host"):
        load_settings(config, {})


@pytest.mark.parametrize("value", ['"yes"', "1"])
def test_allow_remote_must_be_a_boolean(tmp_path: Path, value: str) -> None:
    config = write_config(tmp_path / "config.local.toml", f"[server]\nallow_remote = {value}\n")

    with pytest.raises(ValueError, match="server.allow_remote"):
        load_settings(config, {})
