"""Reads per-track facts for the statistics. The maths lives in domain.stats."""

from sqlalchemy import Engine, select

from wj_music.domain.stats import LibraryStats, TrackFacts, build_stats
from wj_music.storage.models import AlbumRow, ArtistRow, TrackRow


class SqlStatsReader:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def library_stats(self) -> LibraryStats:
        statement = (
            select(
                TrackRow.album_id,
                AlbumRow.date,
                TrackRow.artist_id,
                ArtistRow.name,
                TrackRow.genre,
                TrackRow.duration_seconds,
                TrackRow.sample_rate,
                TrackRow.bit_depth,
                TrackRow.channels,
            )
            .select_from(TrackRow)
            .outerjoin(AlbumRow, TrackRow.album_id == AlbumRow.id)
            .outerjoin(ArtistRow, TrackRow.artist_id == ArtistRow.id)
        )
        with self._engine.connect() as conn:
            return build_stats(TrackFacts(*row) for row in conn.execute(statement))
