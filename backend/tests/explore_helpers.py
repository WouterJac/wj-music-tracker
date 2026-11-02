"""Tag updates for tests that need genres, labels or composers the shared fixture lacks."""

from sqlalchemy import Engine, update

from wj_music.storage.models import TrackRow


def tag_tracks(engine: Engine, values_by_title: dict[str, dict[str, str]]) -> None:
    with engine.begin() as conn:
        for title, values in values_by_title.items():
            conn.execute(update(TrackRow).where(TrackRow.title == title).values(**values))


GENRES = {
    "Breaking Glass": {"genre": "Rock"},
    "Speed of Life": {"genre": "Art Rock"},
    "Beauty and the Beast": {"genre": "Rock"},
    "Sky Saw": {"genre": "Ambient"},
    "First disc": {"genre": "ambient "},
}
