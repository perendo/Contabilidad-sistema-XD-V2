"""migrate existing data to a default company

Revision ID: b3c4d5e6f7a8
Revises: f3a9c1d2e4b7
Create Date: 2026-11-06 00:00:00.000000

"""
from typing import Sequence, Union

from sqlalchemy.orm import Session

from alembic import op
import sqlalchemy as sa

from app.company_migration import migrate_existing_to_default_company


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "f3a9c1d2e4b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("companies"):
        return
    session = Session(bind=bind)
    try:
        migrate_existing_to_default_company(session)
    finally:
        session.close()


def downgrade() -> None:
    # El backfill no se revierte automáticamente para no perder la asociación.
    pass