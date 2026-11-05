"""add reviewed flag to journal entries

Revision ID: a1b2c3d4e5f6
Revises: f3a9c1d2e4b7
Create Date: 2026-11-05 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f3a9c1d2e4b7"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("journal_entries"):
        return
    columns = {column["name"] for column in inspector.get_columns("journal_entries")}
    if "reviewed" not in columns:
        op.add_column(
            "journal_entries",
            sa.Column("reviewed", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("journal_entries"):
        return
    columns = {column["name"] for column in inspector.get_columns("journal_entries")}
    if "reviewed" in columns:
        op.drop_column("journal_entries", "reviewed")
