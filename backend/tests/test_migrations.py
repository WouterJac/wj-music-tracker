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


def column_names(db_path: Path, table: str) -> set[str]:
    engine = create_engine(f"sqlite:///{db_path}")
    try:
        return {column["name"] for column in inspect(engine).get_columns(table)}
    finally:
        engine.dispose()


def test_head_adds_cover_file_to_tracks(db_path: Path) -> None:
    upgrade_database(db_path)

    assert "cover_file" in column_names(db_path, "tracks")


def test_downgrade_to_first_revision_drops_cover_file_but_keeps_tracks(db_path: Path) -> None:
    upgrade_database(db_path)

    downgrade_database(db_path, "0001")

    columns = column_names(db_path, "tracks")
    assert "cover_file" not in columns
    assert "file_path" in columns
