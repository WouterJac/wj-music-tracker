from pathlib import Path

from alembic import command
from alembic.config import Config

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _config(db_path: Path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    return config


def upgrade_database(db_path: Path, revision: str = "head") -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    command.upgrade(_config(db_path), revision)


def downgrade_database(db_path: Path, revision: str = "base") -> None:
    command.downgrade(_config(db_path), revision)
