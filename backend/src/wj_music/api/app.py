"""HTTP application factory and routes."""

from pathlib import Path

from fastapi import FastAPI

from wj_music import __version__
from wj_music.api.library_routes import library_router
from wj_music.api.schemas import HealthResponse
from wj_music.api.stats_routes import stats_router
from wj_music.api.track_routes import track_router
from wj_music.services.library import LibraryService
from wj_music.services.stats import StatsService
from wj_music.services.tracks import TrackService


def create_app(
    library: LibraryService | None = None,
    tracks: TrackService | None = None,
    covers_dir: Path | None = None,
    stats: StatsService | None = None,
) -> FastAPI:
    app = FastAPI(title="WJ Music Tracker", version=__version__)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    if library is not None:
        app.include_router(library_router(library, covers_dir))
    if tracks is not None:
        app.include_router(track_router(tracks))
    if stats is not None:
        app.include_router(stats_router(stats))

    return app
