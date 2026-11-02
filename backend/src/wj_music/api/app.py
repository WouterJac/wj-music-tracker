"""HTTP application factory and routes."""

from pathlib import Path

from fastapi import FastAPI

from wj_music import __version__
from wj_music.api.auth_routes import auth_router, install_token_check
from wj_music.api.facts_routes import facts_router
from wj_music.api.frontend_routes import mount_frontend
from wj_music.api.library_routes import library_router
from wj_music.api.rediscover_routes import rediscover_router
from wj_music.api.scan_routes import scan_router
from wj_music.api.schemas import HealthResponse
from wj_music.api.similar_routes import similar_router
from wj_music.api.stats_routes import stats_router
from wj_music.api.track_routes import track_router
from wj_music.services.auth import AuthService
from wj_music.services.facts import FactsService
from wj_music.services.library import LibraryService
from wj_music.services.rediscover import RediscoverService
from wj_music.services.scan import ScanService
from wj_music.services.similar import SimilarService
from wj_music.services.stats import StatsService
from wj_music.services.tracks import TrackService


def create_app(
    library: LibraryService | None = None,
    tracks: TrackService | None = None,
    covers_dir: Path | None = None,
    stats: StatsService | None = None,
    facts: FactsService | None = None,
    similar: SimilarService | None = None,
    rediscover: RediscoverService | None = None,
    scan: ScanService | None = None,
    auth: AuthService | None = None,
    frontend_dir: Path | None = None,
) -> FastAPI:
    app = FastAPI(title="WJ Music Tracker", version=__version__)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    if auth is not None:
        install_token_check(app, auth)
        app.include_router(auth_router(auth))

    # Before the library router, whose /albums/{album_id} would read "rediscover" as an id.
    if rediscover is not None:
        app.include_router(rediscover_router(rediscover))
    if library is not None:
        app.include_router(library_router(library, covers_dir))
    if tracks is not None:
        app.include_router(track_router(tracks))
    if stats is not None:
        app.include_router(stats_router(stats))
    if facts is not None:
        app.include_router(facts_router(facts))
    if similar is not None:
        app.include_router(similar_router(similar))
    if scan is not None:
        app.include_router(scan_router(scan))
    # Last, because it answers any path that no route above took.
    if frontend_dir is not None:
        mount_frontend(app, frontend_dir)

    return app
