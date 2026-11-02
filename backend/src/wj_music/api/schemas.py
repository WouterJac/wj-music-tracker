"""Response models for the HTTP API. Never include file system or cache paths."""

from typing import Generic, TypeVar

from pydantic import BaseModel

from wj_music.domain.facts import Fact
from wj_music.domain.library import (
    AlbumDetail,
    AlbumSummary,
    ArtistDetail,
    ArtistSummary,
    LyricsHit,
    Page,
    TrackDetail,
    TrackInfo,
)
from wj_music.domain.lyrics import parse_lrc
from wj_music.domain.stats import Bucket, LibraryStats

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
    has_lyrics: bool


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
        has_lyrics=track.has_lyrics,
    )


class LyricLineOut(BaseModel):
    time_seconds: float
    text: str


class LyricsOut(BaseModel):
    plain: str | None
    synced_lines: list[LyricLineOut] | None


class TrackInfoOut(BaseModel):
    id: int
    title: str | None
    disc: int | None
    number: int | None
    duration_seconds: float
    sample_rate: int
    bit_depth: int
    channels: int
    album_id: int | None
    album_title: str | None
    artist_id: int | None
    artist_name: str | None
    cover_url: str | None
    lyrics: LyricsOut | None


class LyricsHitOut(BaseModel):
    track_id: int
    title: str | None
    album_id: int | None
    album_title: str | None
    artist_id: int | None
    artist_name: str | None
    snippet: str


def track_info_out(info: TrackInfo) -> TrackInfoOut:
    lyrics = None
    if info.plain_lyrics is not None or info.synced_lrc is not None:
        lines = parse_lrc(info.synced_lrc) if info.synced_lrc else None
        lyrics = LyricsOut(
            plain=info.plain_lyrics,
            synced_lines=[LyricLineOut(time_seconds=x.time_seconds, text=x.text) for x in lines]
            if lines
            else None,
        )
    has_cover = info.album_has_cover and info.album_id is not None
    return TrackInfoOut(
        id=info.id,
        title=info.title,
        disc=info.disc,
        number=info.number,
        duration_seconds=info.duration_seconds,
        sample_rate=info.sample_rate,
        bit_depth=info.bit_depth,
        channels=info.channels,
        album_id=info.album_id,
        album_title=info.album_title,
        artist_id=info.artist_id,
        artist_name=info.artist_name,
        cover_url=f"/api/albums/{info.album_id}/cover" if has_cover else None,
        lyrics=lyrics,
    )


def lyrics_page_out(page: Page[LyricsHit], limit: int, offset: int) -> PageOut[LyricsHitOut]:
    items = [
        LyricsHitOut(
            track_id=h.track_id,
            title=h.title,
            album_id=h.album_id,
            album_title=h.album_title,
            artist_id=h.artist_id,
            artist_name=h.artist_name,
            snippet=h.snippet,
        )
        for h in page.items
    ]
    return PageOut(items=items, total=page.total, limit=limit, offset=offset)


class BucketOut(BaseModel):
    label: str
    count: int


class TopArtistOut(BaseModel):
    id: int
    name: str
    tracks: int
    albums: int


class StatsOut(BaseModel):
    tracks: int
    albums: int
    artists: int
    total_duration_seconds: float
    hires_tracks: int
    albums_by_decade: list[BucketOut]
    albums_by_year: list[BucketOut]
    tracks_by_format: list[BucketOut]
    tracks_by_channels: list[BucketOut]
    tracks_by_genre: list[BucketOut]
    albums_by_track_count: list[BucketOut]
    albums_by_length: list[BucketOut]
    top_artists: list[TopArtistOut]


def stats_out(stats: LibraryStats) -> StatsOut:
    def buckets(items: list[Bucket]) -> list[BucketOut]:
        return [BucketOut(label=b.label, count=b.count) for b in items]

    return StatsOut(
        tracks=stats.tracks,
        albums=stats.albums,
        artists=stats.artists,
        total_duration_seconds=stats.total_duration_seconds,
        hires_tracks=stats.hires_tracks,
        albums_by_decade=buckets(stats.albums_by_decade),
        albums_by_year=buckets(stats.albums_by_year),
        tracks_by_format=buckets(stats.tracks_by_format),
        tracks_by_channels=buckets(stats.tracks_by_channels),
        tracks_by_genre=buckets(stats.tracks_by_genre),
        albums_by_track_count=buckets(stats.albums_by_track_count),
        albums_by_length=buckets(stats.albums_by_length),
        top_artists=[
            TopArtistOut(id=a.id, name=a.name, tracks=a.tracks, albums=a.albums)
            for a in stats.top_artists
        ],
    )


class FactLinkOut(BaseModel):
    kind: str
    id: int


class FactOut(BaseModel):
    key: str
    title: str
    text: str
    link: FactLinkOut


class FactsOut(BaseModel):
    items: list[FactOut]


def facts_out(facts: list[Fact]) -> FactsOut:
    return FactsOut(
        items=[
            FactOut(
                key=f.key,
                title=f.title,
                text=f.text,
                link=FactLinkOut(kind=f.link.kind, id=f.link.id),
            )
            for f in facts
        ]
    )
