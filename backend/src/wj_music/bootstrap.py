"""Composition root: wires settings to the storage, scanner and cover cache."""

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI

from wj_music.api.app import create_app
from wj_music.config import Settings
from wj_music.domain.models import LibraryTotals
from wj_music.scanner.scan import ScanReport, scan_library
from wj_music.services.facts import FactsService
from wj_music.services.library import LibraryService
from wj_music.services.similar import SimilarService
from wj_music.services.stats import StatsService
from wj_music.services.tracks import TrackService
from wj_music.storage.covers import FileCoverStore
from wj_music.storage.database import create_db_engine
from wj_music.storage.facts_reader import SqlFactsReader
from wj_music.storage.library_reader import SqlLibraryReader
from wj_music.storage.migrate import upgrade_database
from wj_music.storage.repositories import SqlScannedFileRepository, SqlTrackRepository
from wj_music.storage.similar_reader import SqlSimilarReader
from wj_music.storage.stats_reader import SqlStatsReader
from wj_music.storage.totals import count_library
from wj_music.storage.track_reader import SqlTrackReader

DATABASE_NAME = "library.db"
COVERS_DIR_NAME = "covers"


class MusicPathNotConfiguredError(Exception):
    """No music folder is set in the config file or WJ_MUSIC_PATH."""


@dataclass(frozen=True)
class ScanOutcome:
    music_path: Path
    report: ScanReport
    totals: LibraryTotals


def database_path(settings: Settings) -> Path:
    return settings.data_dir / DATABASE_NAME


def run_scan(settings: Settings) -> ScanOutcome:
    if settings.music_path is None:
        raise MusicPathNotConfiguredError
    db_path = database_path(settings)
    upgrade_database(db_path)
    engine = create_db_engine(db_path)
    try:
        report = scan_library(
            settings.music_path,
            scanned=SqlScannedFileRepository(engine),
            tracks=SqlTrackRepository(engine),
            covers=FileCoverStore(settings.data_dir / COVERS_DIR_NAME),
        )
        return ScanOutcome(settings.music_path, report, count_library(engine))
    finally:
        engine.dispose()


def build_app(settings: Settings) -> FastAPI:
    """The web application over the library database, created empty if no scan has run yet."""
    db_path = database_path(settings)
    upgrade_database(db_path)
    engine = create_db_engine(db_path)
    library_reader = SqlLibraryReader(engine)
    return create_app(
        library=LibraryService(library_reader),
        tracks=TrackService(SqlTrackReader(engine)),
        stats=StatsService(SqlStatsReader(engine)),
        facts=FactsService(SqlFactsReader(engine)),
        similar=SimilarService(SqlSimilarReader(engine), library_reader),
        covers_dir=settings.data_dir / COVERS_DIR_NAME,
    )
