"""Walks the music folder and brings the library database in line with it.

Reads only. Writes go through the repositories and the cover store, never into the music folder.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from wj_music.domain.models import ScannedFile
from wj_music.domain.repositories import CoverStore, ScannedFileRepository, TrackRepository
from wj_music.scanner.errors import InvalidFlacError
from wj_music.scanner.flac_reader import read_flac

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
    report = ScanReport()
    known = {record.path: record for record in scanned.all()}
    found = set(find_flac_files(root))

    for path in sorted(found):
        stat = path.stat()
        previous = known.get(path)
        if previous is not None and _unchanged(previous, stat):
            report.unchanged += 1
            if previous.error is not None:
                report.errors.append((path, previous.error))
            continue

        error = _index(path, stat, tracks=tracks, scanned=scanned, covers=covers)
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


def _unchanged(previous: ScannedFile, stat: os.stat_result) -> bool:
    return previous.size_bytes == stat.st_size and previous.mtime == stat.st_mtime


def _index(
    path: Path,
    stat: os.stat_result,
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
        scanned.save(ScannedFile(path, stat.st_size, stat.st_mtime, error=error))
        return error

    cover_file = covers.store(flac.picture) if flac.picture is not None else None
    tracks.save(flac, cover_file=cover_file)
    scanned.save(ScannedFile(path, stat.st_size, stat.st_mtime))
    return None
