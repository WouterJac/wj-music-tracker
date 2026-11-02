"""Serves the built frontend so the app and its API share one address, which a phone needs."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

ASSETS_DIR = "assets"


def mount_frontend(app: FastAPI, dist: Path) -> None:
    """Serve files from the build folder; any other page URL gets index.html so reloads work.

    Must be called after every other route is added, since it matches any path.
    """
    root = dist.resolve()
    index = root / "index.html"
    if not index.is_file():
        return

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        if path == "health" or path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (root / path).resolve()
        target = candidate if candidate.is_file() and candidate.is_relative_to(root) else index
        # Built assets have hashed names. Everything else (the app shell, the service worker)
        # must be re-checked so an update is picked up.
        in_assets = target.parent == root / ASSETS_DIR
        return FileResponse(target, headers=None if in_assets else {"Cache-Control": "no-cache"})
