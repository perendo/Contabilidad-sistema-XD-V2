"""add received invoice jobs

Revision ID: e49a1b2c3d4f
Revises: da37e7a0b22c
Create Date: 2026-11-07 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e49a1b2c3d4f'
down_revision: Union[str, None] = 'da37e7a0b22c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'received_invoice_jobs',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expense_account_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('error', sa.String(length=500), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['expense_account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_received_invoice_jobs_company_id'),
        'received_invoice_jobs',
        ['company_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_received_invoice_jobs_company_id'),
        table_name='received_invoice_jobs',
    )
    op.drop_table('received_invoice_jobs')
