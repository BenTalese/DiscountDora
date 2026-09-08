"""20260907_drop_companion_ingestion_enabled

Owner, 2026-09-07: *"the toggle is redundant, we should remove it."*

Correct — and it is the better answer than the one shipped hours earlier.
`companion_ingestion_enabled` gated nothing at all (FU-866), so it was wired up
to all four `/api/ingest/*` doors that morning. But the control it duplicates
already existed and is strictly better: **ingestion requires a bearer key minted
by an admin**, and every key is an `IngestionSource` row with its own `enabled`
flag. Not wanting ingestion means not minting a key — or revoking/disabling the
one you have, per source, rather than install-wide. Two switches over the same
door, one of them coarser, is worse than one.

So R-078's instruction ("wire it up or drop it") is satisfied by dropping. What
goes: the column, the `features.companion_ingestion` health flag, the admin
toggle, and the gate in `ingestion_auth`. What stays: the shared
`authenticate_ingestion_request()` helper introduced alongside the gate — it
still collapses the same four-line auth block across four routes, which is
worth keeping on its own merits (R-087).

Destructive by design: an install-wide feature switch, not data. Nothing
derives from it. The downgrade restores it with its original
`server_default='0'`.

Follows the `meal_planning_enabled` precedent (`a7c3e5d19f2b`) exactly — the
first instance of this same defect, on the same settings page.

Revision ID: e7a2c4f9b361
Revises: d4f9b2e7a318
Create Date: 2026-09-07 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'e7a2c4f9b361'
down_revision = 'd4f9b2e7a318'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('companion_ingestion_enabled')


def downgrade():
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'companion_ingestion_enabled', sa.Boolean(), nullable=False,
            server_default='0',
        ))
