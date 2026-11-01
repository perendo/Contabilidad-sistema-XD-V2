"""add third parties

Revision ID: 8c4e5b6a1d23
Revises: 3f1a7c9d2b40
Create Date: 2026-11-01 18:41:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c4e5b6a1d23'
down_revision: Union[str, None] = '3f1a7c9d2b40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('third_parties'):
        return
    op.create_table('third_parties',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('tax_id', sa.String(length=50), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('address', sa.String(length=500), nullable=False),
    sa.Column('phone', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('account_id')
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('third_parties'):
        op.drop_table('third_parties')
