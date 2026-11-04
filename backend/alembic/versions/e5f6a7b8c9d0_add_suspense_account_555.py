"""add suspense account 555

Revision ID: e5f6a7b8c9d0
Revises: c1a2b3d4e5f6
Create Date: 2026-11-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'c1a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Solo aplica a instalaciones existentes. En una BD vacia el seed del PGC
    # creara la cuenta a partir de data/pg_sample.json.
    parent_id = bind.execute(
        sa.text("SELECT id FROM accounts WHERE code = '5'")
    ).scalar()
    if parent_id is None:
        return

    group_id = bind.execute(
        sa.text("SELECT id FROM accounts WHERE code = '55'")
    ).scalar()
    if group_id is None:
        group_id = bind.execute(
            sa.text(
                "INSERT INTO accounts (code, name, type, level, is_detail, parent_id) "
                "VALUES ('55', 'Otras cuentas no bancarias', 'Activo', 2, false, :parent_id) "
                "RETURNING id"
            ),
            {"parent_id": parent_id},
        ).scalar()

    exists_555 = bind.execute(
        sa.text("SELECT id FROM accounts WHERE code = '555'")
    ).scalar()
    if exists_555 is None:
        bind.execute(
            sa.text(
                "INSERT INTO accounts (code, name, type, level, is_detail, parent_id) "
                "VALUES ('555', 'Partidas pendientes de aplicación', 'Activo', 3, true, :parent_id)"
            ),
            {"parent_id": group_id},
        )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DELETE FROM accounts "
            "WHERE code = '555' "
            "AND NOT EXISTS (SELECT 1 FROM journal_lines WHERE account_id = accounts.id)"
        )
    )
    bind.execute(
        sa.text(
            "DELETE FROM accounts "
            "WHERE code = '55' "
            "AND NOT EXISTS (SELECT 1 FROM accounts child WHERE child.parent_id = accounts.id)"
        )
    )
