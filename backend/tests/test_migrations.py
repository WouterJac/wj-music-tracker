from pathlib import Path

from sqlalchemy import create_engine, inspect

from wj_music.storage.migrate import downgrade_database, upgrade_database

LIBRARY_TABLES = {"artists", "albums", "tracks", "scanned_files"}


def table_names(db_path: Path) -> set[str]:
    engine = create_engine(f"sqlite:///{db_path}")
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_migration_applies_on_empty_database(db_path: Path) -> None:
    assert not db_path.exists()

    upgrade_database(db_path)

    assert table_names(db_path) >= LIBRARY_TABLES


def test_migration_is_idempotent(db_path: Path) -> None:
    upgrade_database(db_path)
    upgrade_database(db_path)

    assert table_names(db_path) >= LIBRARY_TABLES


def test_downgrade_removes_library_tables(db_path: Path) -> None:
    upgrade_database(db_path)

    downgrade_database(db_path)

    assert not LIBRARY_TABLES & table_names(db_path)
