"""Track cover art: name of the cached cover file in the data directory.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("tracks") as batch:
        batch.add_column(sa.Column("cover_file", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tracks") as batch:
        batch.drop_column("cover_file")
