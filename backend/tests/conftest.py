from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine

from wj_music.storage.database import create_db_engine
from wj_music.storage.migrate import upgrade_database


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "library.db"


@pytest.fixture
def engine(db_path: Path) -> Iterator[Engine]:
    upgrade_database(db_path)
    db = create_db_engine(db_path)
    yield db
    db.dispose()
