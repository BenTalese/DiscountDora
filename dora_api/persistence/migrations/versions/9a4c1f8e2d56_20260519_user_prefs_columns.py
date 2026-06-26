"""20260519_user_prefs_columns

Adds the per-user preference columns introduced by the "User & Global
Options" pass: deals-email opt-out + compact mode, theme (system/light/dark),
font family, font size.

Revision ID: 9a4c1f8e2d56
Revises: 8d3f1e5a9c40
Create Date: 2026-05-19 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '9a4c1f8e2d56'
down_revision = '8d3f1e5a9c40'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column(
            'deals_email_enabled', sa.Boolean(), nullable=False, server_default=sa.true()
        ))
        batch.add_column(sa.Column(
            'deals_email_compact', sa.Boolean(), nullable=False, server_default=sa.false()
        ))
        batch.add_column(sa.Column(
            'theme', sa.String(length=20), nullable=False, server_default='system'
        ))
        batch.add_column(sa.Column(
            'font_family', sa.String(length=20), nullable=False, server_default='default'
        ))
        batch.add_column(sa.Column(
            'font_size', sa.String(length=2), nullable=False, server_default='md'
        ))


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.drop_column('font_size')
        batch.drop_column('font_family')
        batch.drop_column('theme')
        batch.drop_column('deals_email_compact')
        batch.drop_column('deals_email_enabled')
