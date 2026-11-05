"""add bank iban accounts

Revision ID: a4b5c6d7e8f9
Revises: f3a9c1d2e4b7
Create Date: 2026-11-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4b5c6d7e8f9'
down_revision: Union[str, None] = 'f3a9c1d2e4b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('bank_iban_accounts'):
        return
    op.create_table(
        'bank_iban_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('iban', sa.String(length=34), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('iban'),
    )
    op.create_index(
        'ix_bank_iban_accounts_iban', 'bank_iban_accounts', ['iban'], unique=False
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('bank_iban_accounts'):
        op.drop_index('ix_bank_iban_accounts_iban', table_name='bank_iban_accounts')
        op.drop_table('bank_iban_accounts')
