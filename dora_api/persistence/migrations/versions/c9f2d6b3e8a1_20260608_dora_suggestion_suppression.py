"""20260608_dora_suggestion_suppression

P2-04 — table for users' negative decisions on Dora suggestions
(dismissed / snoozed). Generators recompute suggestions fresh each call,
then filter against this table; we deliberately don't persist the
suggestions themselves so they always reflect current pantry state.

Revision ID: c9f2d6b3e8a1
Revises: b8d4e1c7a2f3
Create Date: 2026-06-08 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'c9f2d6b3e8a1'
down_revision = 'b8d4e1c7a2f3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'DoraSuggestionSuppression',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('kind', sa.String(length=64), nullable=False),
        sa.Column('dedup_key', sa.String(length=255), nullable=False),
        sa.Column('decision', sa.String(length=16), nullable=False),
        sa.Column('snoozed_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    # The hot query is "is (kind, dedup_key) suppressed right now?" —
    # a composite index keeps the generator's filter step cheap even as
    # the table grows.
    op.create_index(
        'ix_dora_suggestion_suppression_kind_key',
        'DoraSuggestionSuppression',
        ['kind', 'dedup_key'],
    )


def downgrade():
    op.drop_index('ix_dora_suggestion_suppression_kind_key', table_name='DoraSuggestionSuppression')
    op.drop_table('DoraSuggestionSuppression')
