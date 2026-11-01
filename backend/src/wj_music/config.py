"""Settings from built-in defaults, an optional TOML file and environment variables."""

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MUSIC_PATH_ENV = "WJ_MUSIC_PATH"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DATA_DIR_NAME = "WJMusicTracker"


@dataclass(frozen=True)
class Settings:
    music_path: Path | None
    data_dir: Path
    host: str
    port: int


def default_data_dir(env: Mapping[str, str]) -> Path:
    local_app_data = env.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base / DATA_DIR_NAME


def load_settings(
    config_file: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> Settings:
    """Build settings from defaults, then the config file, then environment overrides."""
    environ = os.environ if env is None else env
    raw: dict[str, Any] = {}
    if config_file is not None and config_file.exists():
        with config_file.open("rb") as handle:
            raw = tomllib.load(handle)

    library = _table(raw, "library")
    data = _table(raw, "data")
    server = _table(raw, "server")

    port = server.get("port", DEFAULT_PORT)
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError(f"server.port must be an integer from 1 to 65535, got {port!r}")

    music_path = environ.get(MUSIC_PATH_ENV) or library.get("music_path", "")
    directory = data.get("directory", "")
    return Settings(
        music_path=Path(music_path) if music_path else None,
        data_dir=Path(directory) if directory else default_data_dir(environ),
        host=server.get("host", DEFAULT_HOST),
        port=port,
    )


def _table(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"[{key}] must be a table")
    return value
