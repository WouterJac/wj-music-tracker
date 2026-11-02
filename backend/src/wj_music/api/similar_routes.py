"""Similar albums. Routes only call the service and map results to models."""

from fastapi import APIRouter, HTTPException

from wj_music.api.schemas import SimilarAlbumOut, similar_out
from wj_music.services.similar import SimilarService


def similar_router(service: SimilarService) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/albums/{album_id}/similar")
    def similar_albums(album_id: int) -> list[SimilarAlbumOut]:
        found = service.similar_to(album_id)
        if found is None:
            raise HTTPException(status_code=404, detail="Album not found")
        return similar_out(found)

    return router
