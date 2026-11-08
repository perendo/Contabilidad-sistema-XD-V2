"""add audit log

Revision ID: a9b8c7d6e5f4
Revises: e49a1b2c3d4f
Create Date: 2026-11-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9b8c7d6e5f4'
down_revision: Union[str, None] = 'e49a1b2c3d4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=100), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('detail', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_audit_logs_company_id'),
        'audit_logs',
        ['company_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_audit_logs_target_id'),
        'audit_logs',
        ['target_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_audit_logs_target_id'),
        table_name='audit_logs',
    )
    op.drop_index(
        op.f('ix_audit_logs_company_id'),
        table_name='audit_logs',
    )
    op.drop_table('audit_logs')
