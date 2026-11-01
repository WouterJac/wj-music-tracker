from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ArtistRow(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)


class AlbumRow(Base):
    __tablename__ = "albums"
    __table_args__ = (UniqueConstraint("title", "artist_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    artist_id: Mapped[int | None] = mapped_column(ForeignKey("artists.id"))
    date: Mapped[str | None] = mapped_column(String)


class TrackRow(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_path: Mapped[str] = mapped_column(String, unique=True)
    album_id: Mapped[int | None] = mapped_column(ForeignKey("albums.id"))
    artist_id: Mapped[int | None] = mapped_column(ForeignKey("artists.id"))
    title: Mapped[str | None] = mapped_column(String)
    track_number: Mapped[str | None] = mapped_column(String)
    disc_number: Mapped[str | None] = mapped_column(String)
    date: Mapped[str | None] = mapped_column(String)
    genre: Mapped[str | None] = mapped_column(String)
    composer: Mapped[str | None] = mapped_column(String)
    label: Mapped[str | None] = mapped_column(String)
    lyrics: Mapped[str | None] = mapped_column(Text)
    duration_seconds: Mapped[float] = mapped_column(Float)
    sample_rate: Mapped[int] = mapped_column(Integer)
    bit_depth: Mapped[int] = mapped_column(Integer)
    channels: Mapped[int] = mapped_column(Integer)
    cover_file: Mapped[str | None] = mapped_column(String)
    synced_lyrics: Mapped[str | None] = mapped_column(Text)


class ScannedFileRow(Base):
    __tablename__ = "scanned_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(String, unique=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    mtime: Mapped[float] = mapped_column(Float)
    error: Mapped[str | None] = mapped_column(Text)
    lyrics_size_bytes: Mapped[int | None] = mapped_column(Integer)
    lyrics_mtime: Mapped[float | None] = mapped_column(Float)
