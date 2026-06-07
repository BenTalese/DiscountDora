"""20260612_shopping_list_status

P6-01 Chunk 1. Collapses the ShoppingList lifecycle flags into a single
`status` column (draft / shopping / done):
    is_archived = true            -> done
    is_in_progress = true (active) -> shopping
    otherwise                     -> draft

Also adds `finish_snapshot` (nullable JSON-as-text) holding what /finish
changed, so Reopen reverses the finish server-side without trusting a
client-supplied snapshot.

The old `is_archived` / `is_in_progress` columns are dropped (pre-release —
no dual-read shim). `is_primary` is intentionally left in place; its removal
is P6-01 Chunk 2.

Batch mode so the column add/drop works on SQLite (table rebuild) as well as
Postgres — R-005 portable data access. The value conversion uses dialect-
neutral boolean literals (sa.true()/sa.false()).

Revision ID: c4d8e1a6f3b9
Revises: a3f1c7d2e9b4
Create Date: 2026-06-12 13:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'c4d8e1a6f3b9'
down_revision = 'a3f1c7d2e9b4'
branch_labels = None
depends_on = None


_shopping_list = sa.table(
    'ShoppingList',
    sa.column('status', sa.String),
    sa.column('is_archived', sa.Boolean),
    sa.column('is_in_progress', sa.Boolean),
)


def upgrade():
    with op.batch_alter_table('ShoppingList') as batch:
        batch.add_column(sa.Column(
            'status', sa.String(16), nullable=False, server_default='draft',
        ))
        batch.add_column(sa.Column('finish_snapshot', sa.String(), nullable=True))

    # Convert the old flag pair into the single status value (rows start
    # 'draft' from the server_default; promote the archived/in-progress ones).
    op.execute(
        _shopping_list.update()
        .where(_shopping_list.c.is_archived == sa.true())
        .values(status='done')
    )
    op.execute(
        _shopping_list.update()
        .where(sa.and_(
            _shopping_list.c.is_archived == sa.false(),
            _shopping_list.c.is_in_progress == sa.true(),
        ))
        .values(status='shopping')
    )

    with op.batch_alter_table('ShoppingList') as batch:
        batch.drop_column('is_in_progress')
        batch.drop_column('is_archived')


def downgrade():
    with op.batch_alter_table('ShoppingList') as batch:
        batch.add_column(sa.Column(
            'is_archived', sa.Boolean(), nullable=False, server_default='0',
        ))
        batch.add_column(sa.Column(
            'is_in_progress', sa.Boolean(), nullable=False, server_default='0',
        ))

    op.execute(
        _shopping_list.update()
        .where(_shopping_list.c.status == 'done')
        .values(is_archived=sa.true())
    )
    op.execute(
        _shopping_list.update()
        .where(_shopping_list.c.status == 'shopping')
        .values(is_in_progress=sa.true())
    )

    with op.batch_alter_table('ShoppingList') as batch:
        batch.drop_column('finish_snapshot')
        batch.drop_column('status')
