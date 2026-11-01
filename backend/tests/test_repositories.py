from pathlib import Path

from sqlalchemy import Engine, func, select

from flac_builder import build_flac
from wj_music.domain.models import ScannedFile
from wj_music.scanner.flac_reader import read_flac
from wj_music.storage.models import AlbumRow, ArtistRow, ScannedFileRow, TrackRow
from wj_music.storage.repositories import SqlScannedFileRepository, SqlTrackRepository


def scanned(
    path: Path, *, size: int = 100, mtime: float = 1.0, error: str | None = None
) -> ScannedFile:
    return ScannedFile(path=path, size_bytes=size, mtime=mtime, error=error)


def count(
    engine: Engine,
    row_type: type[ArtistRow] | type[AlbumRow] | type[TrackRow] | type[ScannedFileRow],
) -> int:
    with engine.connect() as conn:
        return conn.execute(select(func.count()).select_from(row_type.__table__)).scalar_one()


def make_flac(tmp_path: Path, name: str, **tags: list[str]) -> Path:
    path = tmp_path / name
    path.write_bytes(build_flac(tags=tags))
    return path


class TestScannedFileRepository:
    def test_saves_and_lists_a_new_file(self, engine: Engine, tmp_path: Path) -> None:
        repo = SqlScannedFileRepository(engine)
        record = scanned(tmp_path / "a.flac", size=2048, mtime=12.5)

        repo.save(record)

        assert repo.all() == [record]

    def test_saving_the_same_path_updates_the_record(self, engine: Engine, tmp_path: Path) -> None:
        repo = SqlScannedFileRepository(engine)
        path = tmp_path / "a.flac"
        repo.save(scanned(path, size=100, mtime=1.0))

        repo.save(scanned(path, size=200, mtime=2.0, error="bad header"))

        assert repo.all() == [scanned(path, size=200, mtime=2.0, error="bad header")]
        assert count(engine, ScannedFileRow) == 1

    def test_delete_removes_the_record(self, engine: Engine, tmp_path: Path) -> None:
        repo = SqlScannedFileRepository(engine)
        repo.save(scanned(tmp_path / "a.flac"))

        repo.delete(tmp_path / "a.flac")

        assert repo.all() == []

    def test_delete_of_an_unknown_path_is_a_no_op(self, engine: Engine, tmp_path: Path) -> None:
        repo = SqlScannedFileRepository(engine)

        repo.delete(tmp_path / "never-saved.flac")

        assert repo.all() == []


class TestTrackRepository:
    def test_saves_track_with_album_and_artist(self, engine: Engine, tmp_path: Path) -> None:
        path = make_flac(
            tmp_path,
            "01.flac",
            TITLE=["Heroes"],
            ARTIST=["David Bowie"],
            ALBUM=['"Heroes"'],
            DATE=["1977"],
            TRACKNUMBER=["1"],
        )
        repo = SqlTrackRepository(engine)

        repo.save(read_flac(path))

        assert count(engine, TrackRow) == 1
        assert count(engine, ArtistRow) == 1
        assert count(engine, AlbumRow) == 1

    def test_saving_the_same_file_twice_does_not_duplicate(
        self, engine: Engine, tmp_path: Path
    ) -> None:
        path = make_flac(tmp_path, "01.flac", TITLE=["Heroes"])
        repo = SqlTrackRepository(engine)

        repo.save(read_flac(path))
        repo.save(read_flac(path))

        assert count(engine, TrackRow) == 1

    def test_artist_and_album_are_shared_between_tracks(
        self, engine: Engine, tmp_path: Path
    ) -> None:
        repo = SqlTrackRepository(engine)
        for name, title in [("01.flac", "Warszawa"), ("02.flac", "Art Decade")]:
            path = make_flac(tmp_path, name, TITLE=[title], ARTIST=["David Bowie"], ALBUM=["Low"])
            repo.save(read_flac(path))

        assert count(engine, TrackRow) == 2
        assert count(engine, ArtistRow) == 1
        assert count(engine, AlbumRow) == 1

    def test_track_without_album_or_artist_tags_is_saved(
        self, engine: Engine, tmp_path: Path
    ) -> None:
        path = make_flac(tmp_path, "loose.flac", TITLE=["Loose track"])
        repo = SqlTrackRepository(engine)

        repo.save(read_flac(path))

        assert count(engine, TrackRow) == 1
        assert count(engine, ArtistRow) == 0
        assert count(engine, AlbumRow) == 0

    def test_delete_by_path_removes_only_that_track(self, engine: Engine, tmp_path: Path) -> None:
        repo = SqlTrackRepository(engine)
        first = make_flac(tmp_path, "01.flac", TITLE=["One"], ARTIST=["Band"], ALBUM=["Album"])
        second = make_flac(tmp_path, "02.flac", TITLE=["Two"], ARTIST=["Band"], ALBUM=["Album"])
        repo.save(read_flac(first))
        repo.save(read_flac(second))

        repo.delete(first)

        assert count(engine, TrackRow) == 1

    def test_stored_audio_info_is_kept(self, engine: Engine, tmp_path: Path) -> None:
        path = tmp_path / "hires.flac"
        path.write_bytes(
            build_flac(
                sample_rate=96000,
                bits_per_sample=24,
                channels=2,
                total_samples=96000 * 3,
                tags={"TITLE": ["Hi-res"]},
            )
        )
        repo = SqlTrackRepository(engine)

        repo.save(read_flac(path))

        with engine.connect() as conn:
            row = conn.execute(select(TrackRow.__table__)).one()
        assert row.sample_rate == 96000
        assert row.bit_depth == 24
        assert row.channels == 2
        assert row.duration_seconds == 3.0
        assert row.file_path == str(path)


class TestLyricsStorage:
    def test_plain_and_synced_lyrics_are_stored(self, engine: Engine, tmp_path: Path) -> None:
        path = make_flac(tmp_path, "01.flac", LYRICS=["[00:01.00]la\n[00:02.00]di"])
        SqlTrackRepository(engine).save(read_flac(path))

        with engine.connect() as conn:
            row = conn.execute(select(TrackRow.lyrics, TrackRow.synced_lyrics)).one()

        assert row.lyrics == "la\ndi"
        assert row.synced_lyrics == "[00:01.00]la\n[00:02.00]di"

    def test_resaving_without_lyrics_clears_them(self, engine: Engine, tmp_path: Path) -> None:
        path = make_flac(tmp_path, "01.flac", LYRICS=["la"])
        repo = SqlTrackRepository(engine)
        repo.save(read_flac(path))
        path.write_bytes(build_flac(tags={"TITLE": ["now empty"]}))

        repo.save(read_flac(path))

        with engine.connect() as conn:
            row = conn.execute(select(TrackRow.lyrics, TrackRow.synced_lyrics)).one()
        assert (row.lyrics, row.synced_lyrics) == (None, None)

    def test_sidecar_signature_is_kept_on_the_scanned_file(
        self, engine: Engine, tmp_path: Path
    ) -> None:
        repo = SqlScannedFileRepository(engine)
        record = ScannedFile(tmp_path / "a.flac", 10, 1.0, lyrics_size_bytes=42, lyrics_mtime=7.5)

        repo.save(record)

        assert repo.all() == [record]
