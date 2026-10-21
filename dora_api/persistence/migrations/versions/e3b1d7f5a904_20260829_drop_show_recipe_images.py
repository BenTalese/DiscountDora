"""20260829_drop_show_recipe_images

Owner, on Settings → Appearance: *"I'm thoroughly confused about the recipe
photos toggle in appearance settings. What is this even for??"*

Fair question, and the answer was "almost nothing". `User.show_recipe_images`
arrived in C-cross Chunk 5 as one half of a pair of per-user opt-ins whose
stated purpose (PROPOSAL_CONFIG_AND_OPTINS §2.8) was that a user could *"run a
text-dense, fast, low-bandwidth UI without losing the underlying data"* — the
flag was to govern recipe cards, the detail header, the edit preview, cook mode
and print/export, written from an inline button on the cookbook toolbar, with
explicitly no Settings entry.

Every part of that was dismantled around it:
  * FU-508 dropped the `show_stock_images` companion column outright.
  * The cookbook stopped honouring it on 2026-08-18, when the cards/compact
    view switch took photos over there (a card IS the with-photos shape).
  * Cook mode, print/export and the meal-planner rail never honoured it — they
    request recipe images unconditionally.

What was left governed the recipe page's hero image and the recipe cards on the
stock-item detail page, and it could not even deliver the density it promised:
the photo tile is a fixed grid column, so switching photos off painted a
same-sized "Photo hidden" box in the space the picture had occupied.

So the column is dropped rather than rewired. Photo density on the cookbook is
the cards/compact switch; there is no second control, and the app renders recipe
photos unconditionally everywhere else. See ADR-062.

Destructive by design — the column is a display preference, not data. Nothing
derives from it, no other table references it, and every recipe photo it could
suppress is untouched (the bytes live on `Recipe.image`). The downgrade restores
the column with its original `server_default='1'`, which is also the value every
row would have carried on the way out for anyone who never found the toggle.

Revision ID: e3b1d7f5a904
Revises: b2d9f4a7c3e1
Create Date: 2026-08-29 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e3b1d7f5a904'
down_revision = 'b2d9f4a7c3e1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('show_recipe_images')


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column(
            'show_recipe_images', sa.Boolean(), nullable=False, server_default='1',
        ))
