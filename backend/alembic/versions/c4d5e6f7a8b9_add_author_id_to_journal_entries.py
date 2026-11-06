"""add author_id to journal entries

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-11-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("journal_entries", sa.Column("author_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_journal_entries_author_id_users",
        "journal_entries",
        "users",
        ["author_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_journal_entries_author_id_users", "journal_entries", type_="foreignkey"
    )
    op.drop_column("journal_entries", "author_id")
