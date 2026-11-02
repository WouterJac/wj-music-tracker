"""Interesting facts. Routes only call the service and map results to models."""

from fastapi import APIRouter

from wj_music.api.schemas import FactsOut, facts_out
from wj_music.services.facts import FactsService


def facts_router(service: FactsService) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/facts")
    def get_facts() -> FactsOut:
        return facts_out(service.facts())

    return router
