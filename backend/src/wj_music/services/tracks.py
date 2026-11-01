"""Track and lyrics use cases. Talks to the library only through the TrackReader contract."""

from wj_music.domain.library import LyricsHit, Page, TrackInfo
from wj_music.domain.repositories import TrackReader


class TrackService:
    def __init__(self, reader: TrackReader) -> None:
        self._reader = reader

    def get_track(self, track_id: int) -> TrackInfo | None:
        return self._reader.get_track(track_id)

    def search_lyrics(self, query: str, *, limit: int, offset: int) -> Page[LyricsHit]:
        text = query.strip()
        if not text:
            return Page(items=[], total=0)
        return self._reader.search_lyrics(text, limit=limit, offset=offset)
