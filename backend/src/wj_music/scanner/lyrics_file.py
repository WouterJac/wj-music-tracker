"""Sidecar lyrics: a .lrc file with the same name next to the FLAC. Read only."""

import os
import stat as stat_module
from pathlib import Path

MAX_SIDECAR_BYTES = 1024 * 1024
SIDECAR_SUFFIX = ".lrc"


def sidecar_path(flac_path: Path) -> Path:
    return flac_path.with_suffix(SIDECAR_SUFFIX)


def sidecar_stat(flac_path: Path) -> os.stat_result | None:
    try:
        result = sidecar_path(flac_path).stat()
    except OSError:
        return None
    return result if stat_module.S_ISREG(result.st_mode) else None


def read_sidecar(flac_path: Path) -> str | None:
    result = sidecar_stat(flac_path)
    if result is None or result.st_size > MAX_SIDECAR_BYTES:
        return None
    try:
        data = sidecar_path(flac_path).read_bytes()
    except OSError:
        return None
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Older .lrc files are often Windows-1252 rather than UTF-8.
        return data.decode("cp1252", errors="replace")
