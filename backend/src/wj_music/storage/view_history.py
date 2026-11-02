"""Album view history. Lives in its own database because, unlike the library cache, it cannot be
rebuilt by scanning, so a rescan or a cache reset must never touch it."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Engine, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from wj_music.domain.rediscover import AlbumKey


class HistoryBase(DeclarativeBase):
    pass


class AlbumViewRow(HistoryBase):
    __tablename__ = "album_views"

    title: Mapped[str] = mapped_column(String, primary_key=True)
    artist: Mapped[str] = mapped_column(String, primary_key=True)
    last_viewed: Mapped[datetime] = mapped_column(DateTime)


class SqlViewHistory:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        HistoryBase.metadata.create_all(engine)

    def record(self, key: AlbumKey, when: datetime) -> None:
        title, artist = key
        with Session(self._engine) as session:
            session.merge(AlbumViewRow(title=title, artist=artist, last_viewed=_naive(when)))
            session.commit()

    def last_viewed(self) -> dict[AlbumKey, datetime]:
        with Session(self._engine) as session:
            rows = session.execute(select(AlbumViewRow)).scalars()
            return {(row.title, row.artist): row.last_viewed.replace(tzinfo=UTC) for row in rows}


def _naive(when: datetime) -> datetime:
    """SQLite stores no time zone, so times are kept as UTC."""
    return when.astimezone(UTC).replace(tzinfo=None)
