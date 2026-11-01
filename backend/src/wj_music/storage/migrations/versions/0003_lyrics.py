"""Lyrics: synced lyrics per track and the sidecar signature per scanned file.

Existing rows were scanned without reading the new lyrics tags or sidecars, and an
unchanged file is skipped, so the library cache is cleared and the next scan rebuilds it.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table in ("tracks", "albums", "artists", "scanned_files"):
        op.execute(f"DELETE FROM {table}")  # noqa: S608  # fixed table names, no user input
    with op.batch_alter_table("tracks") as batch:
        batch.add_column(sa.Column("synced_lyrics", sa.Text(), nullable=True))
    with op.batch_alter_table("scanned_files") as batch:
        batch.add_column(sa.Column("lyrics_size_bytes", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("lyrics_mtime", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("scanned_files") as batch:
        batch.drop_column("lyrics_mtime")
        batch.drop_column("lyrics_size_bytes")
    with op.batch_alter_table("tracks") as batch:
        batch.drop_column("synced_lyrics")
