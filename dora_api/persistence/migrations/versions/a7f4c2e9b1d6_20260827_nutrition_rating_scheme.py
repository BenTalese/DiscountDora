"""20260827_nutrition_rating_scheme

`health_star_rating_enabled` (added earlier the same day, in d1e5b8c3f7a2)
becomes `nutrition_rating_scheme`, a closed-set string.

The boolean could only ever express "the Australian scheme, or nothing", which
is how the settings page ended up telling everyone outside AU/NZ that the
feature was off by default *for them* — reading, fairly, as "not for you". The
rating was never actually region-gated; only its default and its detect-nudge
were. Replacing the flag with a picker (`none` / `health_star` /
`nutri_score`) says the true thing: pick the scheme you recognise, anywhere.

**Existing choices are preserved**, not reset — an install that had the Health
Star Rating switched on comes back with `health_star` selected. That is worth
the three lines: silently returning a household to "no rating" because the
column changed shape would be a regression they'd have to notice and undo.

Only one scheme is active at a time by design — see `RATING_SCHEME_VALUES` in
`domain/entities/app_setting.py` for why two competing verdicts on one recipe
card was rejected.

Revision ID: a7f4c2e9b1d6
Revises: e4c7a2b9f1d3
Create Date: 2026-08-27 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a7f4c2e9b1d6'
down_revision = 'e4c7a2b9f1d3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'nutrition_rating_scheme', sa.String(32),
            nullable=False, server_default='none',
        ))

    # Carry the old boolean across before dropping it. The predicate is the
    # bare column rather than `= 1`: Postgres will not compare a boolean to an
    # integer, and both it and SQLite read a bare boolean column as the
    # condition (§7.5 — the DB layer stays portable both ways).
    op.execute(
        'UPDATE "AppSetting" SET nutrition_rating_scheme = \'health_star\' '
        'WHERE health_star_rating_enabled'
    )

    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('health_star_rating_enabled')


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'health_star_rating_enabled', sa.Boolean(),
            nullable=False, server_default=sa.false(),
        ))

    # Only the Health Star Rating survives the round trip; an install that had
    # chosen Nutri-Score goes back to "no rating", because the old column had
    # nowhere to put it. Losing that on a downgrade is the honest outcome.
    op.execute(
        'UPDATE "AppSetting" SET health_star_rating_enabled = true '
        'WHERE nutrition_rating_scheme = \'health_star\''
    )

    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('nutrition_rating_scheme')
