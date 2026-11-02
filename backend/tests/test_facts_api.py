from fastapi.testclient import TestClient

from conftest import Library
from wj_music.api.app import create_app
from wj_music.services.facts import FactsService
from wj_music.storage.facts_reader import SqlFactsReader


def make_client(library: Library) -> TestClient:
    return TestClient(create_app(facts=FactsService(SqlFactsReader(library.engine))))


def test_facts_endpoint_lists_facts_with_links(library: Library) -> None:
    response = make_client(library).get("/api/facts")

    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0].keys() == {"key", "title", "text", "link"}
    assert items[0]["key"] == "longest_album"
    assert set(items[0]["link"]) == {"kind", "id"}
    assert {item["link"]["kind"] for item in items} == {"album", "track"}


def test_facts_never_expose_file_system_paths(library: Library) -> None:
    text = make_client(library).get("/api/facts").text

    assert str(library.music) not in text
    assert ".flac" not in text


def test_facts_endpoint_is_absent_without_a_service() -> None:
    assert TestClient(create_app()).get("/api/facts").status_code == 404
