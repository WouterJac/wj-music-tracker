import os
import shutil
from pathlib import Path

import pytest
from sqlalchemy import Engine, func, select

from flac_builder import build_flac
from wj_music.domain.models import ScannedFile
from wj_music.scanner.errors import MusicFolderNotFoundError
from wj_music.scanner.scan import ScanReport, scan_library
from wj_music.storage.covers import FileCoverStore
from wj_music.storage.models import AlbumRow, ArtistRow, ScannedFileRow, TrackRow
from wj_music.storage.repositories import SqlScannedFileRepository, SqlTrackRepository


@pytest.fixture
def music(tmp_path: Path) -> Path:
    folder = tmp_path / "music"
    folder.mkdir()
    return folder


@pytest.fixture
def covers(tmp_path: Path) -> FileCoverStore:
    return FileCoverStore(tmp_path / "covers")


def write_track(folder: Path, name: str, **tags: list[str]) -> Path:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_flac(tags=tags))
    return path


def scan(engine: Engine, music: Path, covers: FileCoverStore) -> ScanReport:
    return scan_library(
        music,
        scanned=SqlScannedFileRepository(engine),
        tracks=SqlTrackRepository(engine),
        covers=covers,
    )


def row_count(engine: Engine, table: type[AlbumRow | ArtistRow | TrackRow | ScannedFileRow]) -> int:
    with engine.connect() as conn:
        return conn.execute(select(func.count()).select_from(table.__table__)).scalar_one()


def track_titles(engine: Engine) -> list[str | None]:
    with engine.connect() as conn:
        return list(conn.execute(select(TrackRow.title).order_by(TrackRow.title)).scalars())


class TestAddingFiles:
    def test_new_files_are_added_with_their_album_and_artist(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        write_track(music, "01.flac", TITLE=["Warszawa"], ARTIST=["David Bowie"], ALBUM=["Low"])
        write_track(
            music, "02.flac", TITLE=["Speed of Life"], ARTIST=["David Bowie"], ALBUM=["Low"]
        )

        report = scan(engine, music, covers)

        assert len(report.added) == 2
        assert row_count(engine, TrackRow) == 2
        assert row_count(engine, AlbumRow) == 1
        assert row_count(engine, ArtistRow) == 1
        assert row_count(engine, ScannedFileRow) == 2

    def test_files_in_subfolders_are_found(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        write_track(music, "Bowie/Low/01.flac", TITLE=["Always Crashing"])

        report = scan(engine, music, covers)

        assert len(report.added) == 1
        assert track_titles(engine) == ["Always Crashing"]

    def test_extension_matching_ignores_case(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        (music / "LOUD.FLAC").write_bytes(build_flac(tags={"TITLE": ["Loud"]}))

        report = scan(engine, music, covers)

        assert len(report.added) == 1

    def test_non_flac_files_are_ignored(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        (music / "cover.jpg").write_bytes(b"\xff\xd8 not a flac")
        (music / "notes.txt").write_text("liner notes")

        report = scan(engine, music, covers)

        assert report.added == []
        assert row_count(engine, ScannedFileRow) == 0


class TestIncrementalRescan:
    def test_unchanged_file_is_skipped(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        write_track(music, "01.flac", TITLE=["Stable"])
        scan(engine, music, covers)

        report = scan(engine, music, covers)

        assert report.added == []
        assert report.changed == []
        assert report.unchanged == 1

    def test_file_with_new_size_is_read_again(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        path = write_track(music, "01.flac", TITLE=["Before"])
        scan(engine, music, covers)
        write_track(music, "01.flac", TITLE=["A much longer title after retagging"])

        report = scan(engine, music, covers)

        assert report.changed == [path]
        assert track_titles(engine) == ["A much longer title after retagging"]

    def test_file_with_new_mtime_is_read_again(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        path = write_track(music, "01.flac", TITLE=["Touched"])
        scan(engine, music, covers)
        stat = path.stat()
        os.utime(path, (stat.st_atime, stat.st_mtime + 60))

        report = scan(engine, music, covers)

        assert report.changed == [path]
        assert report.unchanged == 0

    def test_deleted_file_is_removed_from_the_library(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        path = write_track(music, "01.flac", TITLE=["Gone"], ARTIST=["Band"], ALBUM=["Only Album"])
        scan(engine, music, covers)
        path.unlink()

        report = scan(engine, music, covers)

        assert report.removed == [path]
        assert row_count(engine, TrackRow) == 0
        assert row_count(engine, ScannedFileRow) == 0

    def test_album_and_artist_left_without_tracks_are_pruned(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        path = write_track(music, "01.flac", TITLE=["Gone"], ARTIST=["Band"], ALBUM=["Only Album"])
        scan(engine, music, covers)
        path.unlink()

        scan(engine, music, covers)

        assert row_count(engine, AlbumRow) == 0
        assert row_count(engine, ArtistRow) == 0

    def test_album_still_used_by_another_track_is_kept(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        gone = write_track(music, "01.flac", TITLE=["One"], ARTIST=["Band"], ALBUM=["Album"])
        write_track(music, "02.flac", TITLE=["Two"], ARTIST=["Band"], ALBUM=["Album"])
        scan(engine, music, covers)
        gone.unlink()

        scan(engine, music, covers)

        assert row_count(engine, AlbumRow) == 1
        assert row_count(engine, ArtistRow) == 1


class TestMalformedFiles:
    def test_malformed_file_is_recorded_and_the_scan_continues(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        broken = music / "broken.flac"
        broken.write_bytes(b"this is not audio at all")
        write_track(music, "02.flac", TITLE=["Fine"])

        report = scan(engine, music, covers)

        assert [path for path, _ in report.errors] == [broken]
        assert track_titles(engine) == ["Fine"]
        with engine.connect() as conn:
            error = conn.execute(
                select(ScannedFileRow.error).where(ScannedFileRow.path == str(broken))
            ).scalar_one()
        assert error is not None

    def test_malformed_file_error_is_reported_again_on_next_scan(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        broken = music / "broken.flac"
        broken.write_bytes(b"junk")
        scan(engine, music, covers)

        report = scan(engine, music, covers)

        assert [path for path, _ in report.errors] == [broken]
        assert report.unchanged == 1

    def test_file_that_becomes_malformed_loses_its_track(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        path = write_track(music, "01.flac", TITLE=["Was fine"])
        scan(engine, music, covers)
        path.write_bytes(b"corrupted during copy")

        report = scan(engine, music, covers)

        assert [p for p, _ in report.errors] == [path]
        assert row_count(engine, TrackRow) == 0


class TestCoverArt:
    def test_embedded_cover_is_cached_in_the_covers_folder(
        self, engine: Engine, music: Path, covers: FileCoverStore, tmp_path: Path
    ) -> None:
        cover = b"\xff\xd8\xff cover bytes"
        (music / "01.flac").write_bytes(build_flac(tags={"TITLE": ["Art"]}, picture=cover))

        scan(engine, music, covers)

        cached = list((tmp_path / "covers").iterdir())
        assert len(cached) == 1
        assert cached[0].read_bytes() == cover
        assert cached[0].suffix == ".jpg"
        with engine.connect() as conn:
            stored = conn.execute(select(TrackRow.cover_file)).scalar_one()
        assert stored == cached[0].name

    def test_identical_covers_share_one_cache_file(
        self, engine: Engine, music: Path, covers: FileCoverStore, tmp_path: Path
    ) -> None:
        cover = b"\x89PNG same picture"
        for name in ["01.flac", "02.flac"]:
            (music / name).write_bytes(
                build_flac(tags={"TITLE": [name]}, picture=cover, picture_mime_type="image/png")
            )

        scan(engine, music, covers)

        cached = list((tmp_path / "covers").iterdir())
        assert len(cached) == 1
        assert cached[0].suffix == ".png"

    def test_track_without_cover_has_no_cover_file(
        self, engine: Engine, music: Path, covers: FileCoverStore, tmp_path: Path
    ) -> None:
        write_track(music, "01.flac", TITLE=["Bare"])

        scan(engine, music, covers)

        assert not (tmp_path / "covers").exists()
        with engine.connect() as conn:
            assert conn.execute(select(TrackRow.cover_file)).scalar_one() is None


class TestMusicFolderIsReadOnly:
    def test_scan_leaves_every_file_in_the_music_folder_untouched(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        write_track(music, "Band/Album/01.flac", TITLE=["One"], ARTIST=["Band"], ALBUM=["Album"])
        (music / "broken.flac").write_bytes(b"junk")
        before = {p: p.read_bytes() for p in music.rglob("*") if p.is_file()}

        scan(engine, music, covers)
        scan(engine, music, covers)

        after = {p: p.read_bytes() for p in music.rglob("*") if p.is_file()}
        assert after == before


def test_scan_records_each_file_in_the_scanned_files_table(
    engine: Engine, music: Path, covers: FileCoverStore
) -> None:
    path = write_track(music, "01.flac", TITLE=["Recorded"])

    scan(engine, music, covers)

    records = SqlScannedFileRepository(engine).all()
    assert [r.path for r in records] == [path]
    assert isinstance(records[0], ScannedFile)
    assert records[0].error is None


class TestUnavailableMusicFolder:
    def test_missing_folder_raises_and_keeps_the_library(
        self, engine: Engine, music: Path, covers: FileCoverStore
    ) -> None:
        write_track(music, "01.flac", TITLE=["Keep me"])
        scan(engine, music, covers)
        shutil.rmtree(music)

        with pytest.raises(MusicFolderNotFoundError, match="music"):
            scan(engine, music, covers)

        assert row_count(engine, TrackRow) == 1
        assert row_count(engine, ScannedFileRow) == 1

    def test_path_that_is_a_file_is_rejected(
        self, engine: Engine, tmp_path: Path, covers: FileCoverStore
    ) -> None:
        not_a_folder = tmp_path / "library.txt"
        not_a_folder.write_text("x")

        with pytest.raises(MusicFolderNotFoundError):
            scan(engine, not_a_folder, covers)


def test_file_that_vanishes_during_the_walk_is_reported_and_the_scan_continues(
    engine: Engine, music: Path, covers: FileCoverStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = write_track(music, "01.flac", TITLE=["Real"])
    ghost = music / "ghost.flac"
    monkeypatch.setattr("wj_music.scanner.scan.find_flac_files", lambda _root: [ghost, real])

    report = scan(engine, music, covers)

    assert [path for path, _ in report.errors] == [ghost]
    assert report.added == [real]
