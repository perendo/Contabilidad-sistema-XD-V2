"""add company_id to remaining data tables

Revision ID: f6a7b8c9d0e1
Revises: d4e5f6a7b8c9
Create Date: 2026-11-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = ['third_parties', 'invoices', 'received_invoices', 'bank_iban_accounts', 'bank_import_profiles']
    for table in tables:
        if not inspector.has_table(table):
            continue
        cols = [c['name'] for c in inspector.get_columns(table)]
        if 'company_id' in cols:
            continue
        op.add_column(table, sa.Column('company_id', sa.Integer(), nullable=True))
        op.create_foreign_key(f'fk_{table}_company_id', table, 'companies', ['company_id'], ['id'])
        op.create_index(f'ix_{table}_company_id', table, ['company_id'])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = ['third_parties', 'invoices', 'received_invoices', 'bank_iban_accounts', 'bank_import_profiles']
    for table in tables:
        if not inspector.has_table(table):
            continue
        cols = [c['name'] for c in inspector.get_columns(table)]
        if 'company_id' not in cols:
            continue
        op.drop_index(f'ix_{table}_company_id', table_name=table)
        op.drop_constraint(f'fk_{table}_company_id', table, type_='foreignkey')
        op.drop_column(table, 'company_id')