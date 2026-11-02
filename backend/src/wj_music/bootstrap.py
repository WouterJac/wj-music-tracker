"""Composition root: wires settings to the storage, scanner and cover cache."""

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI

from wj_music.api.app import create_app
from wj_music.config import MUSIC_PATH_ENV, Settings
from wj_music.domain.models import LibraryTotals
from wj_music.scanner.errors import MusicFolderNotFoundError
from wj_music.scanner.scan import ScanReport, scan_library
from wj_music.services.facts import FactsService
from wj_music.services.library import LibraryService
from wj_music.services.rediscover import RediscoverService
from wj_music.services.scan import ScanService, ScanSummary, ScanUnavailableError
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
from wj_music.storage.view_history import SqlViewHistory

DATABASE_NAME = "library.db"
USER_DATABASE_NAME = "user.db"
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


def _scan_summary(settings: Settings) -> ScanSummary:
    """Run a scan for the web app, turning setup problems into a message for the user."""
    try:
        outcome = run_scan(settings)
    except MusicPathNotConfiguredError:
        raise ScanUnavailableError(
            f"No music folder set. Set music_path in config.local.toml or {MUSIC_PATH_ENV}."
        ) from None
    except MusicFolderNotFoundError as exc:
        raise ScanUnavailableError(str(exc)) from None
    report, totals = outcome.report, outcome.totals
    return ScanSummary(
        added=len(report.added),
        changed=len(report.changed),
        removed=len(report.removed),
        unchanged=report.unchanged,
        errors=len(report.errors),
        tracks=totals.tracks,
        albums=totals.albums,
        artists=totals.artists,
    )


def build_app(settings: Settings) -> FastAPI:
    """The web application over the library database, created empty if no scan has run yet."""
    db_path = database_path(settings)
    upgrade_database(db_path)
    engine = create_db_engine(db_path)
    library_reader = SqlLibraryReader(engine)
    # View history is not a cache, so it has its own file that a rescan or reset leaves alone.
    user_engine = create_db_engine(settings.data_dir / USER_DATABASE_NAME)
    return create_app(
        library=LibraryService(library_reader),
        tracks=TrackService(SqlTrackReader(engine)),
        stats=StatsService(SqlStatsReader(engine)),
        facts=FactsService(SqlFactsReader(engine)),
        similar=SimilarService(SqlSimilarReader(engine), library_reader),
        rediscover=RediscoverService(library_reader, SqlViewHistory(user_engine)),
        covers_dir=settings.data_dir / COVERS_DIR_NAME,
        scan=ScanService(lambda: _scan_summary(settings)),
    )
