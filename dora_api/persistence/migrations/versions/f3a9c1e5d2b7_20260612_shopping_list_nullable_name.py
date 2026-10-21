"""20260612_shopping_list_nullable_name

Shopping-list UX v2. `ShoppingList.name` becomes nullable: NULL means "no
custom name" and the API serves a date-derived `display_name` (custom name >
planned shop date > creation date) instead of baking a date string into the
row at create time.

Backfill: rows whose name exactly matches the auto-generated creation-date
label ("%a %d %b" of created_at) were never user-chosen names, so they are
set to NULL and pick up the new fallback (which also tracks a later-set
planned shop date). Real custom names are untouched. Done row-by-row in
Python so the date formatting is identical on Postgres and SQLite (R-005 —
no dialect-specific strftime SQL).

Batch mode for SQLite portability (R-005).

Revision ID: f3a9c1e5d2b7
Revises: e2c5a8f1d7b3
Create Date: 2026-06-12 12:00:00.000000

"""
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = 'f3a9c1e5d2b7'
down_revision = 'e2c5a8f1d7b3'
branch_labels = None
depends_on = None


def _as_datetime(value) -> datetime | None:
    # Postgres hands back datetime; SQLite hands back the stored ISO string.
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def upgrade():
    with op.batch_alter_table('ShoppingList') as batch:
        batch.alter_column('name', existing_type=sa.String(255), nullable=True)

    bind = op.get_bind()
    rows = bind.execute(
        sa.text('SELECT id, name, created_at FROM "ShoppingList"')
    ).fetchall()
    for row in rows:
        created = _as_datetime(row.created_at)
        if created is None or not row.name:
            continue
        # Match both the year-less label and the with-year variant so labels
        # created in earlier years are caught too.
        auto_labels = {
            created.strftime("%a %d %b"),
            created.strftime("%a %d %b %Y"),
        }
        if row.name in auto_labels:
            bind.execute(
                sa.text('UPDATE "ShoppingList" SET name = NULL WHERE id = :id'),
                {"id": row.id},
            )


def downgrade():
    # Re-materialise a name for NULL rows before restoring NOT NULL.
    bind = op.get_bind()
    rows = bind.execute(
        sa.text('SELECT id, name, created_at FROM "ShoppingList" WHERE name IS NULL')
    ).fetchall()
    for row in rows:
        created = _as_datetime(row.created_at)
        label = created.strftime("%a %d %b") if created else "Shopping list"
        bind.execute(
            sa.text('UPDATE "ShoppingList" SET name = :name WHERE id = :id'),
            {"name": label, "id": row.id},
        )
    with op.batch_alter_table('ShoppingList') as batch:
        batch.alter_column('name', existing_type=sa.String(255), nullable=False)
