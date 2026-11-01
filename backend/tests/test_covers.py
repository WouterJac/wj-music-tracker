from pathlib import Path

import pytest

from wj_music.domain.models import Picture
from wj_music.storage.covers import FileCoverStore


def test_store_returns_the_cached_name_and_writes_the_bytes(tmp_path: Path) -> None:
    store = FileCoverStore(tmp_path / "covers")

    name = store.store(Picture(data=b"jpeg bytes", mime_type="image/jpeg"))

    assert name.endswith(".jpg")
    assert (tmp_path / "covers" / name).read_bytes() == b"jpeg bytes"


def test_unknown_mime_type_gets_a_fallback_extension(tmp_path: Path) -> None:
    store = FileCoverStore(tmp_path / "covers")

    name = store.store(Picture(data=b"odd", mime_type="image/x-weird"))

    assert name.endswith(".bin")


def test_failed_write_leaves_no_partial_file_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    covers = tmp_path / "covers"
    store = FileCoverStore(covers)

    def broken_replace(_src: object, _dst: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("wj_music.storage.covers.os.replace", broken_replace)

    with pytest.raises(OSError, match="disk full"):
        store.store(Picture(data=b"jpeg bytes", mime_type="image/jpeg"))

    assert list(covers.iterdir()) == []
