from pathlib import Path

from sqlalchemy import text

from wj_music.storage.database import create_db_engine

SYNCHRONOUS_NORMAL = 1


def test_engine_uses_wal_journal_so_scans_commit_quickly(tmp_path: Path) -> None:
    engine = create_db_engine(tmp_path / "library.db")
    try:
        with engine.connect() as conn:
            assert conn.execute(text("PRAGMA journal_mode")).scalar_one() == "wal"
            assert conn.execute(text("PRAGMA synchronous")).scalar_one() == SYNCHRONOUS_NORMAL
    finally:
        engine.dispose()


def test_engine_enforces_foreign_keys(tmp_path: Path) -> None:
    engine = create_db_engine(tmp_path / "library.db")
    try:
        with engine.connect() as conn:
            assert conn.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    finally:
        engine.dispose()
