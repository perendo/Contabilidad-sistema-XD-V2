"""add correction_of_entry_id to journal entries

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-05 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("journal_entries"):
        return
    columns = {column["name"] for column in inspector.get_columns("journal_entries")}
    if "correction_of_entry_id" not in columns:
        op.add_column(
            "journal_entries",
            sa.Column(
                "correction_of_entry_id",
                sa.Integer(),
                sa.ForeignKey("journal_entries.id"),
                nullable=True,
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("journal_entries"):
        return
    columns = {column["name"] for column in inspector.get_columns("journal_entries")}
    if "correction_of_entry_id" in columns:
        op.drop_column("journal_entries", "correction_of_entry_id")
