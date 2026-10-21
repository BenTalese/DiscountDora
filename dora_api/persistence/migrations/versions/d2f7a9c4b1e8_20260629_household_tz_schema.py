"""20260629_household_tz_schema

FU-174 / R-021 — schema cleanup for the app-wide household-timezone sweep.

Two changes:

1. ``Recipe.last_made_on`` was typed ``DateTime(timezone=True)`` but
   represents a calendar day ("which household day this was last
   cooked"). Switch to ``Date``: drops the (meaningless) time portion,
   makes the boundary semantics explicit. Existing datetime values
   collapse to their date in storage.

2. ``User.onboarding_completed_at`` was typed bare ``DateTime`` while
   every other wall-clock column in the schema sets ``timezone=True``.
   The stored values are already naive UTC (writes go through
   ``datetime.now(UTC)``); flagging the column makes the schema match
   reality and removes the JSON-provider tagging dance for this one
   field.

Also serves as the **merge migration** between the two open heads
(``b7e2d9a4c1f5`` drop_recipe_nutrition + ``c4a8e2b9d7f5``
stock_item_product_unique) — both 2026-06-28 work, both head as of the
FU-174 sweep.

Revision ID: d2f7a9c4b1e8
Revises: b7e2d9a4c1f5, c4a8e2b9d7f5
Create Date: 2026-06-29 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd2f7a9c4b1e8'
down_revision = ('b7e2d9a4c1f5', 'c4a8e2b9d7f5')
branch_labels = None
depends_on = None


def upgrade():
    # ── Recipe.last_made_on : DateTime → Date ──────────────────────────
    # Alembic's batch mode (SQLite-safe) recreates the table from scratch
    # with the new column type; existing datetime values are stringified
    # by SQLite and reparsed as dates. Postgres performs an ALTER COLUMN
    # TYPE with an implicit USING cast (datetime → date drops time).
    with op.batch_alter_table('Recipe') as batch:
        batch.alter_column(
            'last_made_on',
            existing_type=sa.DateTime(timezone=True),
            type_=sa.Date(),
            existing_nullable=True,
        )

    # ── User.onboarding_completed_at : DateTime → DateTime(timezone=True) ──
    # On SQLite this is a no-op at runtime (SQLite ignores `timezone=True`
    # — it stores plain strings either way), but it ensures schema parity
    # on Postgres and aligns the declaration with every other wall-clock
    # column. R-021.
    with op.batch_alter_table('User') as batch:
        batch.alter_column(
            'onboarding_completed_at',
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.alter_column(
            'onboarding_completed_at',
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=True,
        )
    with op.batch_alter_table('Recipe') as batch:
        batch.alter_column(
            'last_made_on',
            existing_type=sa.Date(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
        )
