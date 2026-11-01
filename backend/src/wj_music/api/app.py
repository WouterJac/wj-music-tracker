"""HTTP application factory and routes."""

from fastapi import FastAPI

from wj_music import __version__
from wj_music.api.schemas import HealthResponse


def create_app() -> FastAPI:
    app = FastAPI(title="WJ Music Tracker", version=__version__)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    return app
