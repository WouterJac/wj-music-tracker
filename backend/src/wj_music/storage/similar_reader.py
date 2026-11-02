"""Gathers the tags that describe each album. The scoring rules live in domain.similar."""

from sqlalchemy import Engine, select

from wj_music.domain.library import year_from_date
from wj_music.domain.similar import AlbumProfile
from wj_music.storage.models import AlbumRow, TrackRow


class SqlSimilarReader:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def album_profiles(self) -> list[AlbumProfile]:
        with self._engine.connect() as conn:
            albums = conn.execute(select(AlbumRow.id, AlbumRow.title, AlbumRow.date)).all()
            tracks = conn.execute(
                select(TrackRow.album_id, TrackRow.genre, TrackRow.label, TrackRow.composer).where(
                    TrackRow.album_id.is_not(None)
                )
            ).all()
        genres: dict[int, set[str]] = {}
        labels: dict[int, set[str]] = {}
        composers: dict[int, set[str]] = {}
        for album_id, genre, label, composer in tracks:
            for tag, found in ((genre, genres), (label, labels), (composer, composers)):
                if album_id is not None and tag and (text := tag.strip()):
                    found.setdefault(album_id, set()).add(text)
        return [
            AlbumProfile(
                album_id=album_id,
                title=title,
                year=year_from_date(date),
                genres=frozenset(genres.get(album_id, ())),
                labels=frozenset(labels.get(album_id, ())),
                composers=frozenset(composers.get(album_id, ())),
            )
            for album_id, title, date in albums
        ]
