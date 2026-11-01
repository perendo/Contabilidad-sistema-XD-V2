"""add journal entries and lines

Revision ID: 3f1a7c9d2b40
Revises: 52077e91941c
Create Date: 2026-11-01 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f1a7c9d2b40'
down_revision: Union[str, None] = '52077e91941c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table('journal_entries'):
        op.create_table('journal_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id')
        )
    if not inspector.has_table('journal_lines'):
        op.create_table('journal_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('debit', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('credit', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['entry_id'], ['journal_entries.id'], ),
        sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('journal_lines'):
        op.drop_table('journal_lines')
    if inspector.has_table('journal_entries'):
        op.drop_table('journal_entries')
