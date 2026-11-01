"""SQLAlchemy implementations of the repository contracts in domain.repositories."""

from pathlib import Path

from sqlalchemy import Engine, delete, select
from sqlalchemy.orm import Session

from wj_music.domain.models import FlacFile, ScannedFile
from wj_music.storage.models import AlbumRow, ArtistRow, ScannedFileRow, TrackRow


class SqlScannedFileRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def all(self) -> list[ScannedFile]:
        with Session(self._engine) as session:
            rows = session.scalars(select(ScannedFileRow).order_by(ScannedFileRow.path))
            return [
                ScannedFile(
                    path=Path(row.path),
                    size_bytes=row.size_bytes,
                    mtime=row.mtime,
                    error=row.error,
                )
                for row in rows
            ]

    def save(self, scanned: ScannedFile) -> None:
        with Session(self._engine) as session, session.begin():
            row = session.scalar(
                select(ScannedFileRow).where(ScannedFileRow.path == str(scanned.path))
            )
            if row is None:
                row = ScannedFileRow(path=str(scanned.path))
                session.add(row)
            row.size_bytes = scanned.size_bytes
            row.mtime = scanned.mtime
            row.error = scanned.error

    def delete(self, path: Path) -> None:
        with Session(self._engine) as session, session.begin():
            session.execute(delete(ScannedFileRow).where(ScannedFileRow.path == str(path)))


class SqlTrackRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(self, flac: FlacFile, cover_file: str | None = None) -> None:
        tags = flac.tags
        with Session(self._engine) as session, session.begin():
            album_artist_id = _artist_id(session, tags.albumartist or tags.artist)
            track_artist_id = _artist_id(session, tags.artist)
            album_id = (
                _album_id(session, tags.album, album_artist_id, tags.date) if tags.album else None
            )

            row = session.scalar(select(TrackRow).where(TrackRow.file_path == str(flac.path)))
            if row is None:
                row = TrackRow(file_path=str(flac.path))
                session.add(row)
            row.album_id = album_id
            row.artist_id = track_artist_id
            row.title = tags.title
            row.track_number = tags.tracknumber
            row.disc_number = tags.discnumber
            row.date = tags.date
            row.genre = tags.genre
            row.composer = tags.composer
            row.label = tags.label
            row.lyrics = tags.lyrics
            row.duration_seconds = flac.audio.duration_seconds
            row.sample_rate = flac.audio.sample_rate
            row.bit_depth = flac.audio.bit_depth
            row.channels = flac.audio.channels
            row.cover_file = cover_file

    def delete(self, path: Path) -> None:
        with Session(self._engine) as session, session.begin():
            session.execute(delete(TrackRow).where(TrackRow.file_path == str(path)))

    def prune_orphans(self) -> None:
        # Albums and artists are derived from tags, so a rebuild must not keep ones no track uses.
        with Session(self._engine) as session, session.begin():
            used_albums = select(TrackRow.album_id).where(TrackRow.album_id.is_not(None))
            session.execute(delete(AlbumRow).where(AlbumRow.id.not_in(used_albums)))
            used_by_tracks = select(TrackRow.artist_id).where(TrackRow.artist_id.is_not(None))
            used_by_albums = select(AlbumRow.artist_id).where(AlbumRow.artist_id.is_not(None))
            session.execute(
                delete(ArtistRow).where(
                    ArtistRow.id.not_in(used_by_tracks), ArtistRow.id.not_in(used_by_albums)
                )
            )


def _artist_id(session: Session, name: str | None) -> int | None:
    if not name:
        return None
    row = session.scalar(select(ArtistRow).where(ArtistRow.name == name))
    if row is None:
        row = ArtistRow(name=name)
        session.add(row)
        session.flush()
    return row.id


def _album_id(session: Session, title: str, artist_id: int | None, date: str | None) -> int:
    row = session.scalar(
        select(AlbumRow).where(
            AlbumRow.title == title,
            AlbumRow.artist_id.is_(None) if artist_id is None else AlbumRow.artist_id == artist_id,
        )
    )
    if row is None:
        row = AlbumRow(title=title, artist_id=artist_id, date=date)
        session.add(row)
        session.flush()
    return row.id
