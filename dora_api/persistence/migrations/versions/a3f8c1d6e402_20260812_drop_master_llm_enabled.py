"""20260812_drop_master_llm_enabled

Remove the install-wide AI master kill-switch (`AppSetting.master_llm_enabled`).

AI mode is a purely per-user concern now — each account configures its own
provider/URL/model/API key on Settings → Assistant and opts in via
`User.llm_enabled`. The admin-facing master toggle (and its "System → AI
assistant" page) was removed (owner call 2026-08-12 — "allow users to use AI
if they wish"): a household member wanting AI shouldn't be blocked by an
install-wide switch that made no sense for this app.

**Pre-release hard change — no data preserved:** the column is dropped
outright (any stored value discarded). SQLite runs in batch mode.

Revision ID: a3f8c1d6e402
Revises: c7e1a4b93f52
Create Date: 2026-08-12 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op


revision = 'a3f8c1d6e402'
down_revision = 'c7e1a4b93f52'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.drop_column('master_llm_enabled')


def downgrade():
    with op.batch_alter_table('AppSetting') as batch_op:
        batch_op.add_column(sa.Column(
            'master_llm_enabled', sa.Boolean(),
            nullable=False, server_default=sa.true(),
        ))
