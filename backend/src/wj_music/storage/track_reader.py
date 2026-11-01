"""SQL queries for single tracks and lyrics search. Read only."""

from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from wj_music.domain.library import LyricsHit, Page, TrackInfo, leading_int
from wj_music.domain.snippet import make_snippet
from wj_music.storage.models import AlbumRow, ArtistRow, TrackRow
from wj_music.storage.search import contains


class SqlTrackReader:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_track(self, track_id: int) -> TrackInfo | None:
        with Session(self._engine) as session:
            row = session.execute(
                select(TrackRow, AlbumRow.title, ArtistRow.name)
                .outerjoin(AlbumRow, TrackRow.album_id == AlbumRow.id)
                .outerjoin(ArtistRow, TrackRow.artist_id == ArtistRow.id)
                .where(TrackRow.id == track_id)
            ).first()
            if row is None:
                return None
            track, album_title, artist_name = row
            has_cover = track.album_id is not None and (
                session.scalar(
                    select(TrackRow.id)
                    .where(TrackRow.album_id == track.album_id, TrackRow.cover_file.is_not(None))
                    .limit(1)
                )
                is not None
            )
            return TrackInfo(
                id=track.id,
                title=track.title,
                disc=leading_int(track.disc_number),
                number=leading_int(track.track_number),
                duration_seconds=track.duration_seconds,
                sample_rate=track.sample_rate,
                bit_depth=track.bit_depth,
                channels=track.channels,
                album_id=track.album_id,
                album_title=album_title,
                artist_id=track.artist_id,
                artist_name=artist_name,
                album_has_cover=has_cover,
                plain_lyrics=track.lyrics,
                synced_lrc=track.synced_lyrics,
            )

    def search_lyrics(self, query: str, *, limit: int, offset: int = 0) -> Page[LyricsHit]:
        match = contains(TrackRow.lyrics, query)
        with Session(self._engine) as session:
            total = session.scalar(select(func.count()).select_from(TrackRow).where(match))
            rows = session.execute(
                select(
                    TrackRow.id,
                    TrackRow.title,
                    TrackRow.album_id,
                    AlbumRow.title,
                    TrackRow.artist_id,
                    ArtistRow.name,
                    TrackRow.lyrics,
                )
                .outerjoin(AlbumRow, TrackRow.album_id == AlbumRow.id)
                .outerjoin(ArtistRow, TrackRow.artist_id == ArtistRow.id)
                .where(match)
                .order_by(func.lower(func.coalesce(TrackRow.title, "")), TrackRow.id)
                .limit(limit)
                .offset(offset)
            )
            hits = [
                LyricsHit(
                    track_id=r[0],
                    title=r[1],
                    album_id=r[2],
                    album_title=r[3],
                    artist_id=r[4],
                    artist_name=r[5],
                    snippet=make_snippet(r[6] or "", query),
                )
                for r in rows
            ]
            return Page(items=hits, total=total or 0)
