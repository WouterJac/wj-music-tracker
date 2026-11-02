from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Library
from explore_helpers import GENRES, merged, tag_tracks
from wj_music.api.app import create_app
from wj_music.services.library import LibraryService
from wj_music.services.similar import SimilarService
from wj_music.storage.library_reader import SqlLibraryReader
from wj_music.storage.similar_reader import SqlSimilarReader

TAGS = {
    "Breaking Glass": {"label": "RCA", "composer": "David Bowie"},
    "Beauty and the Beast": {"label": "RCA"},
    "Sky Saw": {"label": "Island", "composer": "Brian Eno"},
    "First disc": {"composer": "brian eno"},
}


@pytest.fixture
def client(library: Library) -> TestClient:
    tag_tracks(library.engine, merged(GENRES, TAGS))
    albums = SqlLibraryReader(library.engine)
    return TestClient(
        create_app(
            library=LibraryService(albums),
            similar=SimilarService(SqlSimilarReader(library.engine), albums),
        )
    )


def album_id(client: TestClient, title: str) -> int:
    for album in client.get("/api/albums?limit=100").json()["items"]:
        if album["title"] == title:
            return int(album["id"])
    raise AssertionError(title)


def similar(client: TestClient, title: str) -> Any:
    response = client.get(f"/api/albums/{album_id(client, title)}/similar")
    assert response.status_code == 200, response.text
    return response.json()


def test_suggests_albums_with_the_reasons(client: TestClient) -> None:
    [match] = similar(client, "Low")

    assert match["album"]["title"] == '"Heroes"'
    assert match["reasons"] == ["Shared genre: Rock", "Same label: RCA", "Similar era: 1977"]
    assert match["score"] == 6
    assert set(match["album"]) == {
        "id",
        "title",
        "artist_id",
        "artist_name",
        "year",
        "track_count",
        "cover_url",
    }


def test_composer_and_genre_link_the_eno_albums(client: TestClient) -> None:
    [match] = similar(client, "Another Green World")

    assert match["album"]["title"] == "Discreet Music"
    assert match["reasons"] == [
        "Shared genre: Ambient",
        "Same composer: Brian Eno",
        "Similar era: 1975",
    ]


def test_never_suggests_the_album_itself(client: TestClient) -> None:
    for title in ("Low", '"Heroes"', "Another Green World", "Discreet Music"):
        own = album_id(client, title)
        assert own not in {m["album"]["id"] for m in similar(client, title)}


def test_unknown_album_is_404(client: TestClient) -> None:
    assert client.get("/api/albums/9999/similar").status_code == 404


def test_album_without_matches_gets_an_empty_list(library: Library) -> None:
    albums = SqlLibraryReader(library.engine)
    client = TestClient(
        create_app(
            library=LibraryService(albums),
            similar=SimilarService(SqlSimilarReader(library.engine), albums),
        )
    )

    assert similar(client, "Low") == []


def test_no_file_system_paths_are_exposed(client: TestClient, library: Library) -> None:
    text = client.get(f"/api/albums/{album_id(client, 'Low')}/similar").text

    assert str(library.music) not in text
    assert ".flac" not in text
