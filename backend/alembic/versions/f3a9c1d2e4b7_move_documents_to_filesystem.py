"""move documents to filesystem storage

Revision ID: f3a9c1d2e4b7
Revises: e5f6a7b8c9d0
Create Date: 2026-11-05 10:00:00.000000

"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.document_storage import (
    company_folder_name,
    generated_filename,
    resolve_path,
)


# revision identifiers, used by Alembic.
revision: str = 'f3a9c1d2e4b7'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(table: str) -> set[str]:
    return {column['name'] for column in sa.inspect(op.get_bind()).get_columns(table)}


def _company_name(bind: sa.Connection) -> str | None:
    return bind.execute(
        sa.text('SELECT name FROM companies ORDER BY id LIMIT 1')
    ).scalar()


def _move_content_to_disk(bind: sa.Connection, company_name: str | None) -> None:
    rows = bind.execute(
        sa.text(
            'SELECT d.id, d.filename, d.content_type, d.content, e.date '
            'FROM documents d '
            'JOIN journal_entries e ON e.id = d.entry_id '
            'WHERE d.content IS NOT NULL AND d.file_path IS NULL'
        )
    ).mappings().all()

    for row in rows:
        year = row['date'].year
        relative = (
            Path(company_folder_name(company_name))
            / str(year)
            / generated_filename(row['filename'], row['content_type'])
        )
        path = resolve_path(relative.as_posix())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(row['content'])
        bind.execute(
            sa.text('UPDATE documents SET file_path = :file_path WHERE id = :id'),
            {'file_path': relative.as_posix(), 'id': row['id']},
        )


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table('documents'):
        return

    columns = _column_names('documents')
    if 'file_path' not in columns:
        op.add_column(
            'documents', sa.Column('file_path', sa.String(length=500), nullable=True)
        )

    if 'content' in columns:
        _move_content_to_disk(bind, _company_name(bind))
        op.drop_column('documents', 'content')

    op.alter_column(
        'documents',
        'file_path',
        existing_type=sa.String(length=500),
        nullable=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table('documents'):
        return

    columns = _column_names('documents')
    if 'content' not in columns:
        op.add_column(
            'documents', sa.Column('content', sa.LargeBinary(), nullable=True)
        )

    rows = bind.execute(
        sa.text('SELECT id, file_path FROM documents')
    ).mappings().all()

    for row in rows:
        path = resolve_path(row['file_path'])
        if not path.exists():
            raise RuntimeError(
                f'No se puede revertir: falta el fichero {row["file_path"]!r}'
            )
        bind.execute(
            sa.text('UPDATE documents SET content = :content WHERE id = :id'),
            {'content': path.read_bytes(), 'id': row['id']},
        )

    op.alter_column(
        'documents',
        'content',
        existing_type=sa.LargeBinary(),
        nullable=False,
    )
    op.drop_column('documents', 'file_path')
