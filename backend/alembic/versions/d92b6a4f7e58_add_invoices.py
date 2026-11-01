"""add invoices

Revision ID: d92b6a4f7e58
Revises: 8c4e5b6a1d23
Create Date: 2026-11-01 18:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd92b6a4f7e58'
down_revision: Union[str, None] = '8c4e5b6a1d23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('invoices'):
        return
    op.create_table('invoices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('number', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('third_party_id', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=False),
    sa.Column('base_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('vat_rate', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('vat_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('entry_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['entry_id'], ['journal_entries.id'], ),
    sa.ForeignKeyConstraint(['third_party_id'], ['third_parties.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('year', 'number', name='uq_invoices_year_number')
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('invoices'):
        op.drop_table('invoices')
