"""add company_id to accounts and journal_entries

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-11-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table('accounts'):
        return
    # accounts: add company_id
    if 'company_id' not in [c['name'] for c in inspector.get_columns('accounts')]:
        op.add_column('accounts', sa.Column('company_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_accounts_company_id', 'accounts', 'companies', ['company_id'], ['id'])
        op.create_index('ix_accounts_company_id', 'accounts', ['company_id'])
    # drop old unique index on code, add composite unique (company_id, code)
    try:
        op.drop_index('ix_accounts_code', table_name='accounts')
    except Exception:
        pass
    try:
        op.drop_constraint('accounts_code_key', 'accounts', type_='unique')
    except Exception:
        pass
    try:
        op.create_unique_constraint('uq_accounts_company_code', 'accounts', ['company_id', 'code'])
    except Exception:
        pass
    # journal_entries: add company_id
    if inspector.has_table('journal_entries'):
        if 'company_id' not in [c['name'] for c in inspector.get_columns('journal_entries')]:
            op.add_column('journal_entries', sa.Column('company_id', sa.Integer(), nullable=True))
            op.create_foreign_key('fk_journal_entries_company_id', 'journal_entries', 'companies', ['company_id'], ['id'])
            op.create_index('ix_journal_entries_company_id', 'journal_entries', ['company_id'])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('journal_entries'):
        if 'company_id' in [c['name'] for c in inspector.get_columns('journal_entries')]:
            op.drop_index('ix_journal_entries_company_id', table_name='journal_entries')
            op.drop_constraint('fk_journal_entries_company_id', 'journal_entries', type_='foreignkey')
            op.drop_column('journal_entries', 'company_id')
    if inspector.has_table('accounts'):
        if 'company_id' in [c['name'] for c in inspector.get_columns('accounts')]:
            try:
                op.drop_constraint('uq_accounts_company_code', 'accounts', type_='unique')
            except Exception:
                pass
            try:
                op.create_unique_constraint('accounts_code_key', 'accounts', ['code'])
            except Exception:
                pass
            op.drop_index('ix_accounts_company_id', table_name='accounts')
            op.drop_constraint('fk_accounts_company_id', 'accounts', type_='foreignkey')
            op.drop_column('accounts', 'company_id')