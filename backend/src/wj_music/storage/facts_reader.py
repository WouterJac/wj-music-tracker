"""Reads per-track data for the facts. The rules live in domain.facts."""

from sqlalchemy import Engine, select

from wj_music.domain.facts import Fact, FactTrack, build_facts
from wj_music.domain.library import leading_int
from wj_music.storage.models import AlbumRow, ArtistRow, TrackRow


class SqlFactsReader:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def facts(self) -> list[Fact]:
        statement = (
            select(
                TrackRow.id,
                TrackRow.title,
                TrackRow.album_id,
                AlbumRow.title,
                AlbumRow.date,
                TrackRow.artist_id,
                ArtistRow.name,
                TrackRow.disc_number,
                TrackRow.genre,
                TrackRow.duration_seconds,
            )
            .select_from(TrackRow)
            .outerjoin(AlbumRow, TrackRow.album_id == AlbumRow.id)
            .outerjoin(ArtistRow, TrackRow.artist_id == ArtistRow.id)
        )
        with self._engine.connect() as conn:
            rows = [
                FactTrack(
                    track_id=track_id,
                    title=title,
                    album_id=album_id,
                    album_title=album_title,
                    album_date=album_date,
                    artist_id=artist_id,
                    artist_name=artist_name,
                    disc=leading_int(disc),
                    genre=genre,
                    duration_seconds=seconds,
                )
                for (
                    track_id,
                    title,
                    album_id,
                    album_title,
                    album_date,
                    artist_id,
                    artist_name,
                    disc,
                    genre,
                    seconds,
                ) in conn.execute(statement)
            ]
        return build_facts(rows)
