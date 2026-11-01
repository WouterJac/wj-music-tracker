import sqlite3
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


def test_head_adds_lyrics_columns(db_path: Path) -> None:
    upgrade_database(db_path)

    assert "synced_lyrics" in column_names(db_path, "tracks")
    assert {"lyrics_size_bytes", "lyrics_mtime"} <= column_names(db_path, "scanned_files")


def test_downgrade_to_0002_drops_the_lyrics_columns(db_path: Path) -> None:
    upgrade_database(db_path)

    downgrade_database(db_path, "0002")

    assert "synced_lyrics" not in column_names(db_path, "tracks")
    assert "lyrics_mtime" not in column_names(db_path, "scanned_files")
    assert "cover_file" in column_names(db_path, "tracks")


def test_upgrading_to_0003_clears_the_cache_so_the_next_scan_rebuilds_it(db_path: Path) -> None:
    upgrade_database(db_path, "0002")
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO artists (id, name) VALUES (1, 'Band')")
        conn.execute("INSERT INTO albums (id, title, artist_id) VALUES (1, 'Album', 1)")
        conn.execute(
            "INSERT INTO tracks (file_path, album_id, artist_id, duration_seconds, sample_rate,"
            " bit_depth, channels) VALUES ('a.flac', 1, 1, 1.0, 44100, 16, 2)"
        )
        conn.execute(
            "INSERT INTO scanned_files (path, size_bytes, mtime) VALUES ('a.flac', 1, 1.0)"
        )

    upgrade_database(db_path)

    with sqlite3.connect(db_path) as conn:
        counts = [
            conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("artists", "albums", "tracks", "scanned_files")
        ]
    assert counts == [0, 0, 0, 0]
