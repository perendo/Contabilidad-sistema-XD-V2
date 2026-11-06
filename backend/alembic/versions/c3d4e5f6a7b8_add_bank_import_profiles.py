"""add bank import profiles

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-11-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('bank_import_profiles'):
        return
    op.create_table(
        'bank_import_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('iban', sa.String(length=34), nullable=False),
        sa.Column('date_column', sa.String(length=255), nullable=False),
        sa.Column('concept_column', sa.String(length=255), nullable=False),
        sa.Column('amount_column', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('iban'),
    )
    op.create_index(
        'ix_bank_import_profiles_iban', 'bank_import_profiles', ['iban'], unique=False
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('bank_import_profiles'):
        op.drop_index('ix_bank_import_profiles_iban', table_name='bank_import_profiles')
        op.drop_table('bank_import_profiles')