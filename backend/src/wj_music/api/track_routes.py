"""Track detail and lyrics search. Routes only call the service and map results to models."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from wj_music.api.library_routes import DEFAULT_PAGE_SIZE, Limit, Offset
from wj_music.api.schemas import (
    LyricsHitOut,
    PageOut,
    TrackInfoOut,
    lyrics_page_out,
    track_info_out,
)
from wj_music.services.tracks import TrackService

MIN_SEARCH_LENGTH = 2
MAX_SEARCH_LENGTH = 100

LyricsQuery = Annotated[str, Query(min_length=MIN_SEARCH_LENGTH, max_length=MAX_SEARCH_LENGTH)]


def track_router(service: TrackService) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/tracks/{track_id}")
    def get_track(track_id: int) -> TrackInfoOut:
        info = service.get_track(track_id)
        if info is None:
            raise HTTPException(status_code=404, detail="Track not found")
        return track_info_out(info)

    @router.get("/lyrics/search")
    def search_lyrics(
        q: LyricsQuery, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0
    ) -> PageOut[LyricsHitOut]:
        page = service.search_lyrics(q, limit=limit, offset=offset)
        return lyrics_page_out(page, limit, offset)

    return router
