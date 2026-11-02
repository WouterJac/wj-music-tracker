"""Rediscover and view tracking. Routes only call the service and map results to models."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response

from wj_music.api.schemas import AlbumOut, album_out
from wj_music.services.rediscover import RediscoverService

MAX_REDISCOVER_ALBUMS = 12
DEFAULT_REDISCOVER_ALBUMS = 6


def rediscover_router(service: RediscoverService) -> APIRouter:
    router = APIRouter(prefix="/api")

    # Included before the library router, whose /albums/{album_id} would read "rediscover" as an id.
    @router.get("/albums/rediscover")
    def rediscover(
        count: Annotated[int, Query(ge=1, le=MAX_REDISCOVER_ALBUMS)] = DEFAULT_REDISCOVER_ALBUMS,
    ) -> list[AlbumOut]:
        return [album_out(a) for a in service.rediscover(count)]

    @router.post("/albums/{album_id}/view", status_code=204)
    def record_view(album_id: int) -> Response:
        if not service.record_view(album_id):
            raise HTTPException(status_code=404, detail="Album not found")
        return Response(status_code=204)

    return router
