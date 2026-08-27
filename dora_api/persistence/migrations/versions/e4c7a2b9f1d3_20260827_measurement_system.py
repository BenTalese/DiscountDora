"""20260827_measurement_system

Owner feedback 2026-08-27 — *"Locale and region settings should also include
units config, which then determines what units appear throughout the app."*

Replaces ``AppSetting.unit_pricing_locale VARCHAR(8) NOT NULL DEFAULT 'AU'``
with ``AppSetting.measurement_system VARCHAR(16) NOT NULL DEFAULT 'metric'``.

It is a replacement rather than an addition because the two would have been
two names for one fact (R-003). ``unit_pricing_locale`` only ever answered
"which shelf convention do I quote per-unit prices in?" on an AU/US axis, and
it was never exposed anywhere in the UI. The new setting answers that *and*
"which units do the app's dropdowns offer?", on a three-value axis that can
tell the UK apart from the US — which the old one could not, since both use
pounds and ounces but only one prices by the quart.

Value mapping on the way up::

    'AU' → 'metric'
    'US' → 'us'

and the reverse on the way down, where ``'imperial'`` — a value the old column
had no way to express — collapses to ``'AU'``, since the UK prices in metric.
That is a lossy downgrade and is the honest one: the pricing behaviour is
preserved exactly, only the units-picker nuance is lost.

Postgres and SQLite both handle this through ``batch_alter_table``; the data
migration is a two-row-at-most UPDATE (AppSetting is a singleton).

Revision ID: e4c7a2b9f1d3
Revises: d1e5b8c3f7a2
Create Date: 2026-08-27 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'e4c7a2b9f1d3'
down_revision = 'd1e5b8c3f7a2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(
            sa.Column(
                'measurement_system',
                sa.String(length=16),
                nullable=False,
                server_default='metric',
            ),
        )
    # Carry the existing pricing convention across before the old column goes.
    op.execute(
        "UPDATE \"AppSetting\" SET measurement_system = 'us' "
        "WHERE upper(unit_pricing_locale) = 'US'"
    )
    op.execute(
        "UPDATE \"AppSetting\" SET measurement_system = 'metric' "
        "WHERE upper(unit_pricing_locale) <> 'US' OR unit_pricing_locale IS NULL"
    )
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('unit_pricing_locale')


def downgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(
            sa.Column(
                'unit_pricing_locale',
                sa.String(length=8),
                nullable=False,
                server_default='AU',
            ),
        )
    # 'imperial' folds into 'AU': the UK shelf convention IS the AU one, so
    # nothing about pricing changes — only the picker vocabulary is lost.
    op.execute(
        "UPDATE \"AppSetting\" SET unit_pricing_locale = 'US' "
        "WHERE lower(measurement_system) = 'us'"
    )
    op.execute(
        "UPDATE \"AppSetting\" SET unit_pricing_locale = 'AU' "
        "WHERE lower(measurement_system) <> 'us' OR measurement_system IS NULL"
    )
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('measurement_system')
