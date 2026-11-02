"""SQL queries behind the browsing API. Read only."""

from collections import Counter
from typing import Any

from sqlalchemy import ColumnElement, Engine, Row, Select, distinct, func, or_, select
from sqlalchemy.orm import Session

from wj_music.domain.library import (
    AlbumDetail,
    AlbumSummary,
    ArtistDetail,
    ArtistSummary,
    GenreCount,
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
        decade: int | None = None,
        genre: str | None = None,
        limit: int,
        offset: int = 0,
    ) -> Page[AlbumSummary]:
        conditions = _album_conditions(query, artist_id, year, decade, genre)
        with Session(self._engine) as session:
            total = session.scalar(
                select(func.count())
                .select_from(AlbumRow)
                .outerjoin(ArtistRow, AlbumRow.artist_id == ArtistRow.id)
                .where(*conditions)
            )
            rows = session.execute(_album_summaries(conditions).limit(limit).offset(offset))
            return Page(items=[_album_summary(row) for row in rows], total=total or 0)

    def random_albums(
        self, *, count: int, decade: int | None = None, genre: str | None = None
    ) -> list[AlbumSummary]:
        conditions = _album_conditions(None, None, None, decade, genre)
        statement = _album_summaries(conditions).order_by(None).order_by(func.random()).limit(count)
        with Session(self._engine) as session:
            return [_album_summary(row) for row in session.execute(statement)]

    def albums_by_ids(self, album_ids: list[int]) -> list[AlbumSummary]:
        with Session(self._engine) as session:
            rows = session.execute(_album_summaries([AlbumRow.id.in_(album_ids)]))
            by_id = {summary.id: summary for summary in map(_album_summary, rows)}
        return [by_id[i] for i in album_ids if i in by_id]

    def list_genres(self) -> list[GenreCount]:
        with Session(self._engine) as session:
            rows = session.execute(
                select(TrackRow.album_id, TrackRow.genre).where(
                    TrackRow.album_id.is_not(None), TrackRow.genre.is_not(None)
                )
            )
            albums_by_genre: dict[str, set[int]] = {}
            spellings: dict[str, Counter[str]] = {}
            for album_id, genre in rows:
                if album_id is None or genre is None or not (name := genre.strip()):
                    continue
                key = name.lower()
                albums_by_genre.setdefault(key, set()).add(album_id)
                spellings.setdefault(key, Counter())[name] += 1
        # Tags differ in case and spacing; show the spelling used most, capitals first on a tie.
        names = {
            key: min(counts, key=lambda spelling: (-counts[spelling], spelling))
            for key, counts in spellings.items()
        }
        ranked = sorted(albums_by_genre, key=lambda k: (-len(albums_by_genre[k]), names[k].lower()))
        return [GenreCount(name=names[k], album_count=len(albums_by_genre[k])) for k in ranked]

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
    query: str | None,
    artist_id: int | None,
    year: int | None,
    decade: int | None = None,
    genre: str | None = None,
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if query:
        conditions.append(or_(_contains(AlbumRow.title, query), _contains(ArtistRow.name, query)))
    if artist_id is not None:
        conditions.append(AlbumRow.artist_id == artist_id)
    if year is not None:
        conditions.append(AlbumRow.date.like(f"{year:04d}%"))
    if decade is not None:
        conditions.append(AlbumRow.date.like(f"{decade // 10:03d}%"))
    if genre:
        wanted = genre.strip().lower()
        conditions.append(
            AlbumRow.id.in_(
                select(TrackRow.album_id).where(func.lower(func.trim(TrackRow.genre)) == wanted)
            )
        )
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
