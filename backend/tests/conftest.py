from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from sqlalchemy import Engine

from flac_builder import build_flac
from wj_music.scanner.scan import scan_library
from wj_music.storage.covers import FileCoverStore
from wj_music.storage.database import create_db_engine
from wj_music.storage.migrate import upgrade_database
from wj_music.storage.repositories import SqlScannedFileRepository, SqlTrackRepository


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "library.db"


@pytest.fixture
def engine(db_path: Path) -> Iterator[Engine]:
    upgrade_database(db_path)
    db = create_db_engine(db_path)
    yield db
    db.dispose()


@dataclass(frozen=True)
class Library:
    """A scanned library built from generated FLAC files."""

    engine: Engine
    covers_dir: Path
    music: Path


COVER_BYTES = b"\xff\xd8\xff the cover of Low"


@pytest.fixture
def library(engine: Engine, tmp_path: Path) -> Library:
    music = tmp_path / "music"
    music.mkdir()
    covers_dir = tmp_path / "covers"

    def track(
        name: str, tags: dict[str, list[str]], *, seconds: int = 180, picture: bytes | None = None
    ) -> None:
        (music / name).write_bytes(
            build_flac(tags=tags, picture=picture, total_samples=44100 * seconds)
        )

    # Written out of order on purpose: the reader must sort by disc, then track number.
    low = {"ARTIST": ["David Bowie"], "ALBUM": ["Low"], "DATE": ["1977-01-14"]}
    track(
        "low2.flac",
        {**low, "TITLE": ["Speed of Life"], "TRACKNUMBER": ["2"]},
        seconds=150,
        picture=COVER_BYTES,
    )
    track(
        "low1.flac",
        {**low, "TITLE": ["Breaking Glass"], "TRACKNUMBER": ["1/11"]},
        seconds=200,
        picture=COVER_BYTES,
    )
    heroes = {"ARTIST": ["David Bowie"], "ALBUM": ['"Heroes"'], "DATE": ["1977"]}
    track("heroes1.flac", {**heroes, "TITLE": ["Beauty and the Beast"], "TRACKNUMBER": ["1"]})
    green = {"ARTIST": ["Brian Eno"], "ALBUM": ["Another Green World"], "DATE": ["1975"]}
    track("green1.flac", {**green, "TITLE": ["Sky Saw"], "TRACKNUMBER": ["1"]})
    disc = {"ARTIST": ["Brian Eno"], "ALBUM": ["Discreet Music"], "DATE": ["1975"]}
    track(
        "disc2.flac", {**disc, "TITLE": ["Second disc"], "DISCNUMBER": ["2"], "TRACKNUMBER": ["1"]}
    )
    track(
        "disc1.flac", {**disc, "TITLE": ["First disc"], "DISCNUMBER": ["1"], "TRACKNUMBER": ["1"]}
    )
    track("loose.flac", {"TITLE": ["Loose track"]})

    scan_library(
        music,
        scanned=SqlScannedFileRepository(engine),
        tracks=SqlTrackRepository(engine),
        covers=FileCoverStore(covers_dir),
    )
    return Library(engine=engine, covers_dir=covers_dir, music=music)
