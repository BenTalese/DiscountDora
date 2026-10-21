"""20260820_stocktake_last_session

Chunk 6 / **D-4** of `docs/04_proposals/IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md`
— the stocktake runner's third phase (**Sweep**) shows items that dropped out of
rotation *since the user's last session*, not the full excluded set. That needs a
watermark, and the plan called it out as "small new state that doesn't exist yet".

`User.stocktake_last_session_at`, nullable:

* **Per-user, not household.** A stocktake is a shared activity, but "what
  changed since *I* last looked" is a personal question. Household scoping would
  have two people sharing a pantry blanking each other's Sweep phase.
* **NULL = never finished a session.** The Sweep phase reads that as "show
  nothing", not "show everything ever excluded" — the whole point of the phase is
  that newly-excluded is an *event*. Existing users therefore get an empty Sweep
  on their first session after this migration and a real one from then on, which
  is the correct behaviour rather than a gap to backfill.

Additive and nullable, so `downgrade` is a clean drop with nothing to preserve.

Revision ID: f2a6d4b8c917
Revises: e4b1c7a95d20
Create Date: 2026-08-20 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

revision = 'f2a6d4b8c917'
down_revision = 'e4b1c7a95d20'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.add_column(
            sa.Column('stocktake_last_session_at', sa.DateTime(timezone=True),
                      nullable=True)
        )


def downgrade():
    with op.batch_alter_table('User') as batch_op:
        batch_op.drop_column('stocktake_last_session_at')
