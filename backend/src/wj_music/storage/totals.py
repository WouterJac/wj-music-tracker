"""Row counts for the library summary."""

from sqlalchemy import Engine, func, select

from wj_music.domain.models import LibraryTotals
from wj_music.storage.models import AlbumRow, ArtistRow, TrackRow


def count_library(engine: Engine) -> LibraryTotals:
    with engine.connect() as conn:

        def count(row_type: type[AlbumRow | ArtistRow | TrackRow]) -> int:
            return conn.execute(select(func.count()).select_from(row_type)).scalar_one()

        return LibraryTotals(
            tracks=count(TrackRow), albums=count(AlbumRow), artists=count(ArtistRow)
        )
