from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event


def create_db_engine(path: Path) -> Engine:
    engine = create_engine(f"sqlite:///{path.as_posix()}")

    @event.listens_for(engine, "connect")
    def configure_connection(dbapi_connection: Any, _record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        # The database is a rebuildable cache, so a scan does not need a full fsync per commit.
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    return engine
