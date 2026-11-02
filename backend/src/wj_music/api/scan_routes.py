"""Scan on request. Routes only call the service and map results to models."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from wj_music.services.scan import ScanAlreadyRunningError, ScanService, ScanUnavailableError


class ScanSummaryOut(BaseModel):
    added: int
    changed: int
    removed: int
    unchanged: int
    errors: int
    tracks: int
    albums: int
    artists: int


def scan_router(service: ScanService) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.post("/scan")
    def scan() -> ScanSummaryOut:
        try:
            summary = service.scan()
        except ScanAlreadyRunningError:
            raise HTTPException(status_code=409, detail="A scan is already running") from None
        except ScanUnavailableError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        return ScanSummaryOut(**vars(summary))

    return router
