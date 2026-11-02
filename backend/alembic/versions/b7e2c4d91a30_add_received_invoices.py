"""add received invoices

Revision ID: b7e2c4d91a30
Revises: d92b6a4f7e58
Create Date: 2026-11-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e2c4d91a30'
down_revision: Union[str, None] = 'd92b6a4f7e58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('received_invoices'):
        return
    op.create_table('received_invoices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('third_party_id', sa.Integer(), nullable=False),
    sa.Column('supplier_number', sa.String(length=100), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=False),
    sa.Column('base_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('vat_rate', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('vat_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('expense_account_id', sa.Integer(), nullable=False),
    sa.Column('entry_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['entry_id'], ['journal_entries.id'], ),
    sa.ForeignKeyConstraint(['expense_account_id'], ['accounts.id'], ),
    sa.ForeignKeyConstraint(['third_party_id'], ['third_parties.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('third_party_id', 'supplier_number', name='uq_received_invoices_supplier_number')
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('received_invoices'):
        op.drop_table('received_invoices')
