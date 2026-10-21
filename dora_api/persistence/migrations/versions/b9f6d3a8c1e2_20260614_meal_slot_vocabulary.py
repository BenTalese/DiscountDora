"""20260614_meal_slot_vocabulary

C-2.A — household-wide meal-slot vocabulary. Creates the `MealSlot`
{id, name, sequence} lookup and seeds the five DEFAULT_MEAL_SLOTS
(Breakfast, Lunch, Dinner, Snack, Dessert). `MealPlanEntry.slot` /
`Recipe.time_of_day` keep storing the slot *name* as free text (no FK);
this table just pins the vocabulary and is validated against at write-time.

Plain `create_table` is portable across SQLite and Postgres — R-005.
Reversible (downgrade drops the table) — R-006.

Revision ID: b9f6d3a8c1e2
Revises: b9e5c2a78f31
Create Date: 2026-06-14 00:00:00.000000

"""
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'b9f6d3a8c1e2'
down_revision = 'b9e5c2a78f31'
branch_labels = None
depends_on = None


_DEFAULT_MEAL_SLOTS = [
    "Breakfast", "Lunch", "Dinner", "Snack", "Dessert",
]


def upgrade():
    op.create_table(
        'MealSlot',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
    )

    _seed_meal_slots()


def _seed_meal_slots():
    meal_slot_tbl = sa.table(
        'MealSlot',
        sa.column('id', UUIDType()),
        sa.column('name', sa.String),
        sa.column('sequence', sa.Integer),
    )

    op.bulk_insert(meal_slot_tbl, [
        {'id': str(uuid.uuid4()), 'name': name, 'sequence': i}
        for i, name in enumerate(_DEFAULT_MEAL_SLOTS)
    ])


def downgrade():
    op.drop_table('MealSlot')
