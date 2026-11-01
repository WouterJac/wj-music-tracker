"""Response models for the HTTP API. Never include file system or cache paths."""

from typing import Generic, TypeVar

from pydantic import BaseModel

from wj_music.domain.library import (
    AlbumDetail,
    AlbumSummary,
    ArtistDetail,
    ArtistSummary,
    Page,
    TrackDetail,
)

T = TypeVar("T")


class HealthResponse(BaseModel):
    status: str
    version: str


class PageOut(BaseModel, Generic[T]):  # noqa: UP046  # PEP 695 syntax needs Python 3.12
    items: list[T]
    total: int
    limit: int
    offset: int


class AlbumOut(BaseModel):
    id: int
    title: str
    artist_id: int | None
    artist_name: str | None
    year: int | None
    track_count: int
    cover_url: str | None


class TrackOut(BaseModel):
    id: int
    disc: int | None
    number: int | None
    title: str | None
    duration_seconds: float
    sample_rate: int
    bit_depth: int
    channels: int


class AlbumDetailOut(AlbumOut):
    total_duration_seconds: float
    tracks: list[TrackOut]


class ArtistOut(BaseModel):
    id: int
    name: str
    album_count: int


class ArtistDetailOut(BaseModel):
    id: int
    name: str
    albums: list[AlbumOut]


def album_out(album: AlbumSummary) -> AlbumOut:
    return AlbumOut(
        id=album.id,
        title=album.title,
        artist_id=album.artist_id,
        artist_name=album.artist_name,
        year=album.year,
        track_count=album.track_count,
        cover_url=f"/api/albums/{album.id}/cover" if album.has_cover else None,
    )


def album_detail_out(detail: AlbumDetail) -> AlbumDetailOut:
    return AlbumDetailOut(
        **album_out(detail.summary).model_dump(),
        total_duration_seconds=detail.total_duration_seconds,
        tracks=[_track_out(track) for track in detail.tracks],
    )


def artist_out(artist: ArtistSummary) -> ArtistOut:
    return ArtistOut(id=artist.id, name=artist.name, album_count=artist.album_count)


def artist_detail_out(detail: ArtistDetail) -> ArtistDetailOut:
    return ArtistDetailOut(
        id=detail.id, name=detail.name, albums=[album_out(a) for a in detail.albums]
    )


def album_page_out(page: Page[AlbumSummary], limit: int, offset: int) -> PageOut[AlbumOut]:
    return PageOut(
        items=[album_out(a) for a in page.items], total=page.total, limit=limit, offset=offset
    )


def artist_page_out(page: Page[ArtistSummary], limit: int, offset: int) -> PageOut[ArtistOut]:
    return PageOut(
        items=[artist_out(a) for a in page.items], total=page.total, limit=limit, offset=offset
    )


def _track_out(track: TrackDetail) -> TrackOut:
    return TrackOut(
        id=track.id,
        disc=track.disc,
        number=track.number,
        title=track.title,
        duration_seconds=track.duration_seconds,
        sample_rate=track.sample_rate,
        bit_depth=track.bit_depth,
        channels=track.channels,
    )
