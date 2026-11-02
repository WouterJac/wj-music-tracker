"""SQL queries behind the browsing API. Read only."""

from typing import Any

from sqlalchemy import ColumnElement, Engine, Row, Select, distinct, func, or_, select
from sqlalchemy.orm import Session

from wj_music.domain.library import (
    AlbumDetail,
    AlbumSummary,
    ArtistDetail,
    ArtistSummary,
    Page,
    TrackDetail,
    leading_int,
    year_from_date,
)
from wj_music.storage.models import AlbumRow, ArtistRow, TrackRow
from wj_music.storage.search import contains as _contains


class SqlLibraryReader:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_albums(
        self,
        *,
        query: str | None = None,
        artist_id: int | None = None,
        year: int | None = None,
        limit: int,
        offset: int = 0,
    ) -> Page[AlbumSummary]:
        conditions = _album_conditions(query, artist_id, year)
        with Session(self._engine) as session:
            total = session.scalar(
                select(func.count())
                .select_from(AlbumRow)
                .outerjoin(ArtistRow, AlbumRow.artist_id == ArtistRow.id)
                .where(*conditions)
            )
            rows = session.execute(_album_summaries(conditions).limit(limit).offset(offset))
            return Page(items=[_album_summary(row) for row in rows], total=total or 0)

    def get_album(self, album_id: int) -> AlbumDetail | None:
        with Session(self._engine) as session:
            row = session.execute(_album_summaries([AlbumRow.id == album_id])).first()
            if row is None:
                return None
            tracks = session.scalars(select(TrackRow).where(TrackRow.album_id == album_id)).all()
            # Disc and track tags are free text ("3/12"), so they are ordered here, not in SQL.
            ordered = sorted(
                tracks,
                key=lambda t: (
                    leading_int(t.disc_number) or 0,
                    leading_int(t.track_number) or 0,
                    t.file_path,
                ),
            )
            return AlbumDetail(
                summary=_album_summary(row),
                tracks=[
                    TrackDetail(
                        id=t.id,
                        disc=leading_int(t.disc_number),
                        number=leading_int(t.track_number),
                        title=t.title,
                        duration_seconds=t.duration_seconds,
                        sample_rate=t.sample_rate,
                        bit_depth=t.bit_depth,
                        channels=t.channels,
                        has_lyrics=t.lyrics is not None,
                    )
                    for t in ordered
                ],
            )

    def list_artists(
        self, *, query: str | None = None, limit: int, offset: int = 0
    ) -> Page[ArtistSummary]:
        # Only artists with at least one album are browsable; the join drops the rest.
        conditions = [_contains(ArtistRow.name, query)] if query else []
        with Session(self._engine) as session:
            total = session.scalar(
                select(func.count(distinct(ArtistRow.id)))
                .select_from(ArtistRow)
                .join(AlbumRow, AlbumRow.artist_id == ArtistRow.id)
                .where(*conditions)
            )
            rows = session.execute(
                select(ArtistRow.id, ArtistRow.name, func.count(AlbumRow.id))
                .join(AlbumRow, AlbumRow.artist_id == ArtistRow.id)
                .where(*conditions)
                .group_by(ArtistRow.id)
                .order_by(func.lower(ArtistRow.name), ArtistRow.id)
                .limit(limit)
                .offset(offset)
            )
            items = [ArtistSummary(id=r[0], name=r[1], album_count=r[2]) for r in rows]
            return Page(items=items, total=total or 0)

    def get_artist(self, artist_id: int) -> ArtistDetail | None:
        with Session(self._engine) as session:
            artist = session.get(ArtistRow, artist_id)
            if artist is None:
                return None
            rows = session.execute(_album_summaries([AlbumRow.artist_id == artist_id]))
            return ArtistDetail(
                id=artist.id, name=artist.name, albums=[_album_summary(r) for r in rows]
            )

    def list_years(self) -> list[int]:
        with Session(self._engine) as session:
            dates = session.scalars(select(AlbumRow.date).where(AlbumRow.date.is_not(None)))
            years = {year for date in dates if (year := year_from_date(date)) is not None}
        return sorted(years, reverse=True)

    def album_cover_file(self, album_id: int) -> str | None:
        with Session(self._engine) as session:
            return session.scalar(
                select(TrackRow.cover_file)
                .where(TrackRow.album_id == album_id, TrackRow.cover_file.is_not(None))
                .order_by(TrackRow.id)
                .limit(1)
            )


def _album_conditions(
    query: str | None, artist_id: int | None, year: int | None
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if query:
        conditions.append(or_(_contains(AlbumRow.title, query), _contains(ArtistRow.name, query)))
    if artist_id is not None:
        conditions.append(AlbumRow.artist_id == artist_id)
    if year is not None:
        conditions.append(AlbumRow.date.like(f"{year:04d}%"))
    return conditions


def _album_summaries(conditions: list[ColumnElement[bool]]) -> Select[*tuple[Any, ...]]:
    return (
        select(
            AlbumRow.id,
            AlbumRow.title,
            AlbumRow.artist_id,
            ArtistRow.name,
            AlbumRow.date,
            func.count(TrackRow.id),
            func.max(TrackRow.cover_file.is_not(None)),
        )
        .select_from(AlbumRow)
        .outerjoin(ArtistRow, AlbumRow.artist_id == ArtistRow.id)
        .outerjoin(TrackRow, TrackRow.album_id == AlbumRow.id)
        .where(*conditions)
        .group_by(AlbumRow.id)
        .order_by(
            ArtistRow.name.is_(None),
            func.lower(ArtistRow.name),
            AlbumRow.date,
            func.lower(AlbumRow.title),
            AlbumRow.id,
        )
    )


def _album_summary(row: Row[Any]) -> AlbumSummary:
    album_id, title, artist_id, artist_name, date, track_count, has_cover = tuple(row)
    return AlbumSummary(
        id=album_id,
        title=title,
        artist_id=artist_id,
        artist_name=artist_name,
        year=year_from_date(date),
        track_count=track_count,
        has_cover=bool(has_cover),
    )
