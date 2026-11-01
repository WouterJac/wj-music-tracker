"""Initial library schema: artists, albums, tracks and scanned files.

Revision ID: 0001
Revises:
Create Date: 2026-11-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "artists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
    )
    op.create_table(
        "albums",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("artist_id", sa.Integer(), sa.ForeignKey("artists.id"), nullable=True),
        sa.Column("date", sa.String(), nullable=True),
        sa.UniqueConstraint("title", "artist_id"),
    )
    op.create_table(
        "tracks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("file_path", sa.String(), nullable=False, unique=True),
        sa.Column("album_id", sa.Integer(), sa.ForeignKey("albums.id"), nullable=True),
        sa.Column("artist_id", sa.Integer(), sa.ForeignKey("artists.id"), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("track_number", sa.String(), nullable=True),
        sa.Column("disc_number", sa.String(), nullable=True),
        sa.Column("date", sa.String(), nullable=True),
        sa.Column("genre", sa.String(), nullable=True),
        sa.Column("composer", sa.String(), nullable=True),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("lyrics", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("sample_rate", sa.Integer(), nullable=False),
        sa.Column("bit_depth", sa.Integer(), nullable=False),
        sa.Column("channels", sa.Integer(), nullable=False),
    )
    op.create_table(
        "scanned_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("path", sa.String(), nullable=False, unique=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("mtime", sa.Float(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("scanned_files")
    op.drop_table("tracks")
    op.drop_table("albums")
    op.drop_table("artists")
