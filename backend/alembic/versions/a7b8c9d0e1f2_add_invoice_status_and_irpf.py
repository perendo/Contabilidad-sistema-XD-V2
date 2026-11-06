"""add invoice status and irpf columns

Revision ID: a7b8c9d0e1f2
Revises: c4d5e6f7a8b9
Create Date: 2026-11-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = ('invoices', 'received_invoices')


def upgrade() -> None:
    for table in TABLES:
        inspector = sa.inspect(op.get_bind())
        if not inspector.has_table(table):
            continue
        columns = {column['name'] for column in inspector.get_columns(table)}

        if 'irpf_rate' not in columns:
            op.add_column(
                table, sa.Column('irpf_rate', sa.Numeric(precision=5, scale=2), nullable=True)
            )
        if 'irpf_amount' not in columns:
            op.add_column(
                table,
                sa.Column('irpf_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            )
        if 'status' not in columns:
            op.add_column(
                table, sa.Column('status', sa.String(length=20), nullable=True)
            )
            op.execute(sa.text(f"UPDATE {table} SET status = 'pendiente' WHERE status IS NULL"))
            op.alter_column(
                table,
                'status',
                existing_type=sa.String(length=20),
                nullable=False,
            )


def downgrade() -> None:
    for table in TABLES:
        inspector = sa.inspect(op.get_bind())
        if not inspector.has_table(table):
            continue
        columns = {column['name'] for column in inspector.get_columns(table)}
        if 'status' in columns:
            op.drop_column(table, 'status')
        if 'irpf_amount' in columns:
            op.drop_column(table, 'irpf_amount')
        if 'irpf_rate' in columns:
            op.drop_column(table, 'irpf_rate')
