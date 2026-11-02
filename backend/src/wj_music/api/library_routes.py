"""Read-only browsing endpoints. Routes only call the service and map results to models."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from wj_music.api.schemas import (
    AlbumDetailOut,
    AlbumOut,
    ArtistDetailOut,
    ArtistOut,
    GenreOut,
    PageOut,
    album_detail_out,
    album_out,
    album_page_out,
    artist_detail_out,
    artist_page_out,
)
from wj_music.services.library import LibraryService

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 50
COVER_CACHE_SECONDS = 3600

Search = Annotated[str | None, Query(max_length=100)]
Limit = Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)]
Offset = Annotated[int, Query(ge=0)]
Decade = Annotated[int | None, Query(ge=1000, le=9990, multiple_of=10)]
Genre = Annotated[str | None, Query(max_length=100)]
MAX_RANDOM_ALBUMS = 12


def library_router(service: LibraryService, covers_dir: Path | None) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/albums")
    def list_albums(
        q: Search = None,
        artist_id: int | None = None,
        year: Annotated[int | None, Query(ge=1000, le=9999)] = None,
        decade: Decade = None,
        genre: Genre = None,
        limit: Limit = DEFAULT_PAGE_SIZE,
        offset: Offset = 0,
    ) -> PageOut[AlbumOut]:
        page = service.list_albums(
            query=q,
            artist_id=artist_id,
            year=year,
            decade=decade,
            genre=genre,
            limit=limit,
            offset=offset,
        )
        return album_page_out(page, limit, offset)

    # Declared before /albums/{album_id}, which would otherwise try to read "random" as an id.
    @router.get("/albums/random")
    def random_albums(
        count: Annotated[int, Query(ge=1, le=MAX_RANDOM_ALBUMS)] = 1,
        decade: Decade = None,
        genre: Genre = None,
    ) -> list[AlbumOut]:
        albums = service.random_albums(count=count, decade=decade, genre=genre)
        return [album_out(a) for a in albums]

    @router.get("/genres")
    def list_genres() -> list[GenreOut]:
        return [GenreOut(name=g.name, album_count=g.album_count) for g in service.list_genres()]

    @router.get("/albums/{album_id}")
    def get_album(album_id: int) -> AlbumDetailOut:
        detail = service.get_album(album_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Album not found")
        return album_detail_out(detail)

    @router.get("/albums/{album_id}/cover")
    def get_cover(album_id: int) -> FileResponse:
        name = service.album_cover_name(album_id)
        if name is None or covers_dir is None or Path(name).name != name:
            raise HTTPException(status_code=404, detail="Cover not found")
        path = covers_dir / name
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Cover not found")
        return FileResponse(
            path, headers={"Cache-Control": f"public, max-age={COVER_CACHE_SECONDS}"}
        )

    @router.get("/artists")
    def list_artists(
        q: Search = None, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0
    ) -> PageOut[ArtistOut]:
        page = service.list_artists(query=q, limit=limit, offset=offset)
        return artist_page_out(page, limit, offset)

    @router.get("/artists/{artist_id}")
    def get_artist(artist_id: int) -> ArtistDetailOut:
        detail = service.get_artist(artist_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Artist not found")
        return artist_detail_out(detail)

    @router.get("/years")
    def list_years() -> list[int]:
        return service.list_years()

    return router
