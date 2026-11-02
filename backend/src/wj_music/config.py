"""Settings from built-in defaults, an optional TOML file and environment variables."""

import ipaddress
import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MUSIC_PATH_ENV = "WJ_MUSIC_PATH"
CONFIG_ENV = "WJ_CONFIG"
CONFIG_FILE_NAME = "config.local.toml"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DATA_DIR_NAME = "WJMusicTracker"


@dataclass(frozen=True)
class Settings:
    music_path: Path | None
    data_dir: Path
    host: str
    port: int
    allow_remote: bool = False


def default_data_dir(env: Mapping[str, str]) -> Path:
    local_app_data = env.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base / DATA_DIR_NAME


def find_config_file(start: Path, env: Mapping[str, str] | None = None) -> Path | None:
    """Locate the config file: WJ_CONFIG, else config.local.toml in start or a parent folder."""
    environ = os.environ if env is None else env
    explicit = environ.get(CONFIG_ENV)
    if explicit:
        return Path(explicit)
    for folder in (start, *start.parents):
        candidate = folder / CONFIG_FILE_NAME
        if candidate.is_file():
            return candidate
    return None


def load_settings(
    config_file: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> Settings:
    """Build settings from defaults, then the config file, then environment overrides."""
    environ = os.environ if env is None else env
    raw: dict[str, Any] = {}
    if config_file is not None and config_file.exists():
        with config_file.open("rb") as handle:
            try:
                raw = tomllib.load(handle)
            except tomllib.TOMLDecodeError as exc:
                raise ValueError(f"Invalid config file {config_file}: {exc}") from exc

    library = _table(raw, "library")
    data = _table(raw, "data")
    server = _table(raw, "server")

    port = server.get("port", DEFAULT_PORT)
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError(f"server.port must be an integer from 1 to 65535, got {port!r}")

    allow_remote = server.get("allow_remote", False)
    if not isinstance(allow_remote, bool):
        raise ValueError(f"server.allow_remote must be true or false, got {allow_remote!r}")

    host = server.get("host", DEFAULT_HOST)
    remote_host = allow_remote and isinstance(host, str) and host.strip() != ""
    if not _is_loopback(host) and not remote_host:
        raise ValueError(
            "server.host must be a loopback address unless server.allow_remote is true "
            f"(see API-AUTH.md), got {host!r}"
        )

    music_path = environ.get(MUSIC_PATH_ENV) or library.get("music_path", "")
    directory = data.get("directory", "")
    return Settings(
        music_path=Path(music_path) if music_path else None,
        data_dir=Path(directory) if directory else default_data_dir(environ),
        host=host,
        port=port,
        allow_remote=allow_remote,
    )


def _table(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"[{key}] must be a table")
    return value


def _is_loopback(host: object) -> bool:
    if not isinstance(host, str):
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False
