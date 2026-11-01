"""Library statistics. Routes only call the service and map the result to a model."""

from fastapi import APIRouter

from wj_music.api.schemas import StatsOut, stats_out
from wj_music.services.stats import StatsService


def stats_router(service: StatsService) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/stats")
    def get_stats() -> StatsOut:
        return stats_out(service.library_stats())

    return router
