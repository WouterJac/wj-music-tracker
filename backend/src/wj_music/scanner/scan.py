"""Walks the music folder and brings the library database in line with it.

Reads only. Writes go through the repositories and the cover store, never into the music folder.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from wj_music.domain.models import ScannedFile
from wj_music.domain.repositories import CoverStore, ScannedFileRepository, TrackRepository
from wj_music.scanner.errors import InvalidFlacError, MusicFolderNotFoundError
from wj_music.scanner.flac_reader import read_flac
from wj_music.scanner.lyrics_file import sidecar_stat

logger = logging.getLogger(__name__)
FLAC_SUFFIX = ".flac"


@dataclass
class ScanReport:
    added: list[Path] = field(default_factory=list)
    changed: list[Path] = field(default_factory=list)
    removed: list[Path] = field(default_factory=list)
    unchanged: int = 0
    errors: list[tuple[Path, str]] = field(default_factory=list)


def scan_library(
    root: Path,
    *,
    scanned: ScannedFileRepository,
    tracks: TrackRepository,
    covers: CoverStore,
) -> ScanReport:
    if not root.is_dir():
        raise MusicFolderNotFoundError(root)
    report = ScanReport()
    known = {record.path: record for record in scanned.all()}
    found = set(find_flac_files(root))

    for path in sorted(found):
        try:
            stat = path.stat()
        except OSError as exc:
            # The file vanished or became unreadable after the walk. Leave its records alone;
            # the next scan removes them if the file is really gone.
            logger.warning("Could not stat %s: %s", path, exc)
            report.errors.append((path, str(exc)))
            continue
        previous = known.get(path)
        sidecar = sidecar_stat(path)
        if previous is not None and _unchanged(previous, stat, sidecar):
            report.unchanged += 1
            if previous.error is not None:
                report.errors.append((path, previous.error))
            continue

        error = _index(path, stat, sidecar, tracks=tracks, scanned=scanned, covers=covers)
        if error is not None:
            report.errors.append((path, error))
        elif previous is None:
            report.added.append(path)
        else:
            report.changed.append(path)

    for path in sorted(known.keys() - found):
        tracks.delete(path)
        scanned.delete(path)
        report.removed.append(path)
        logger.info("Removed from library: %s", path)

    if report.added or report.changed or report.removed:
        tracks.prune_orphans()
    return report


def find_flac_files(root: Path) -> list[Path]:
    return [
        path for path in root.rglob("*") if path.suffix.lower() == FLAC_SUFFIX and path.is_file()
    ]


def _unchanged(previous: ScannedFile, stat: os.stat_result, sidecar: os.stat_result | None) -> bool:
    sidecar_size = sidecar.st_size if sidecar else None
    sidecar_mtime = sidecar.st_mtime if sidecar else None
    return (
        previous.size_bytes == stat.st_size
        and previous.mtime == stat.st_mtime
        and previous.lyrics_size_bytes == sidecar_size
        and previous.lyrics_mtime == sidecar_mtime
    )


def _index(
    path: Path,
    stat: os.stat_result,
    sidecar: os.stat_result | None,
    *,
    tracks: TrackRepository,
    scanned: ScannedFileRepository,
    covers: CoverStore,
) -> str | None:
    """Store one file. Returns the error message when the file cannot be read, else None."""
    try:
        flac = read_flac(path)
    except (InvalidFlacError, OSError) as exc:
        # One bad file must not stop the scan. The error is kept so the next scan can report it.
        logger.warning("Could not read %s: %s", path, exc)
        error = str(exc)
        tracks.delete(path)
        scanned.save(_record(path, stat, sidecar, error))
        return error

    cover_file = covers.store(flac.picture) if flac.picture is not None else None
    tracks.save(flac, cover_file=cover_file)
    scanned.save(_record(path, stat, sidecar))
    return None


def _record(
    path: Path, stat: os.stat_result, sidecar: os.stat_result | None, error: str | None = None
) -> ScannedFile:
    return ScannedFile(
        path,
        stat.st_size,
        stat.st_mtime,
        error=error,
        lyrics_size_bytes=sidecar.st_size if sidecar else None,
        lyrics_mtime=sidecar.st_mtime if sidecar else None,
    )
