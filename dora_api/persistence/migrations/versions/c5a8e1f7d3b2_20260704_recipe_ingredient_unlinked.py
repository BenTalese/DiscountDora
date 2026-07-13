"""20260704_recipe_ingredient_unlinked

IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — make RecipeIngredient support
persistable "unlinked" rows so a paste-based recipe import can save
even when the parser's fuzzy-match couldn't find a matching StockItem.
The user resolves the linking later (bulk-linker in Chunk 6).

Schema changes:
1. ``RecipeIngredient.stock_item_id`` → nullable. FK still ondelete
   RESTRICT for LINKED rows (deleting a StockItem in-use still blocks);
   unlinked rows are unaffected.
2. New column ``RecipeIngredient.raw_text: String(500), nullable``.
   Preserves the ingredient label — "1 pound ground turkey" — even
   after the linked StockItem is renamed / deleted, and drives the
   Class-B parser's "here's what the user pasted" round-trip.
3. Backfill: for every existing row, set ``raw_text`` to the joined
   ``StockItem.name``. Preserves the ingredient label at the moment of
   the migration; future edits can update either / both fields.
4. CHECK constraint ``stock_item_id IS NOT NULL OR raw_text IS NOT NULL``
   named ``ck_recipe_ingredient_anchor`` — at least one anchor per row.

Cookability rule shift (server-side, wired outside this migration):
if any ingredient on a recipe has ``stock_item_id IS NULL``, the
recipe's cookability is ``None`` (unknown) rather than True/False. On
ship, no existing recipes have unlinked ingredients, so no user-visible
change until Chunk 5 activates the paste importer.

Revision ID: c5a8e1f7d3b2
Revises: d7e3b9f4a1c2
Create Date: 2026-07-04 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'c5a8e1f7d3b2'
down_revision = 'd7e3b9f4a1c2'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Add ``raw_text`` nullable so we can backfill before the CHECK.
    with op.batch_alter_table('RecipeIngredient') as batch:
        batch.add_column(sa.Column('raw_text', sa.String(500), nullable=True))

    # 2) Backfill raw_text from the joined StockItem.name so existing
    #    rows preserve their label even if the StockItem is later
    #    renamed or deleted. Portable across SQLite and Postgres.
    op.execute(
        'UPDATE "RecipeIngredient" '
        'SET raw_text = ("StockItem"."name") '
        'FROM "StockItem" '
        'WHERE "RecipeIngredient".stock_item_id = "StockItem".id '
        '  AND "RecipeIngredient".raw_text IS NULL'
    )

    # 3) Relax stock_item_id to nullable. FK stays ondelete=RESTRICT so a
    #    StockItem that's referenced by a still-linked ingredient can't
    #    be deleted; unlinked rows have NULL and don't touch the FK.
    with op.batch_alter_table('RecipeIngredient') as batch:
        batch.alter_column('stock_item_id', nullable=True)

    # 4) At-least-one anchor: either a linked stock_item or a raw_text
    #    label. The `ck_recipe_ingredient_anchor` name matches the
    #    NAMING_CONVENTION in dora_api/app.py so batch_alter_table can
    #    reproduce it on the SQLite rebuild path.
    with op.batch_alter_table('RecipeIngredient') as batch:
        batch.create_check_constraint(
            'recipe_ingredient_anchor',
            'stock_item_id IS NOT NULL OR raw_text IS NOT NULL',
        )


def downgrade():
    # Reverse: any unlinked rows cannot be resurrected as linked, so
    # downgrade fails loudly if any exist. That matches the migration
    # policy for "you cannot go back from a schema loosening".
    _unlinked_count = op.get_bind().execute(
        sa.text('SELECT COUNT(*) FROM "RecipeIngredient" WHERE stock_item_id IS NULL')
    ).scalar_one()
    if _unlinked_count:
        raise RuntimeError(
            f'{_unlinked_count} RecipeIngredient rows have stock_item_id IS NULL; '
            f'downgrade would violate the NOT NULL restore. Link or delete them '
            f'before downgrading.'
        )
    # NOTE (FU-553): this is the intended downgrade, but it does NOT run under
    # SQLite batch mode today — dropping the named CHECK
    # (`ck_RecipeIngredient_recipe_ingredient_anchor`) fails because Alembic
    # batch + this metadata's naming convention double-render the reflected
    # constraint name on the table rebuild, so `drop_constraint` can't match it
    # (and leaving it undropped fails when `raw_text`, which the CHECK
    # references, is dropped). This is downgrade-only — production only ever
    # runs `upgrade` — and is likely fine on Postgres (native DROP CONSTRAINT, no
    # batch rebuild). Tracked as FU-553; `test__migrations__down_up_roundtrip_is_clean`
    # is strict-xfailed on it. See FU-549 for the from-empty *upgrade* fix.
    with op.batch_alter_table('RecipeIngredient') as batch:
        batch.drop_constraint('recipe_ingredient_anchor', type_='check')
    with op.batch_alter_table('RecipeIngredient') as batch:
        batch.alter_column('stock_item_id', nullable=False)
        batch.drop_column('raw_text')
