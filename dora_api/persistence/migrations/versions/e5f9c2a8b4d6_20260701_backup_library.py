"""20260701_backup_library

FU-342 — the backup library. Persists each generated backup as a
row + a file on disk, replacing the previous stream-the-file
fast-path (which the same migration retires by dropping
`User.last_backup_at`, whose only writer was that old endpoint).

Two AppSetting columns land in the same migration so retention +
storage-path admin controls arrive with the table itself, not a
subsequent step:
  - `backup_retention_count` (default 5) — oldest-first prune on
    every new library write; disk-conscious default for Pi.
  - `backup_storage_path` (default '' → resolved to
    `$DORA_DATA_DIR/backups/` at runtime by the config helper).

Revision ID: e5f9c2a8b4d6
Revises: d4e8f2b1c9a5
Create Date: 2026-07-01 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = 'e5f9c2a8b4d6'
down_revision = 'd4e8f2b1c9a5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'Backup',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'created_by_user_id', UUIDType,
            sa.ForeignKey('User.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        # JSON-encoded list[str] — the section backup_keys this file
        # carries (mirrors the `sections` field inside the file's
        # own envelope).
        sa.Column('sections', sa.Text(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('trigger_kind', sa.String(length=16), nullable=False),
        sa.Column('storage_path', sa.String(length=1024), nullable=False),
    )
    # List view sorts by created_at DESC; index the column so a
    # library with a year of dailies still pages cheap.
    op.create_index(
        'backup_created_at',
        'Backup', ['created_at'],
    )

    # Retention + storage path AppSettings. The old download-only path
    # never had these because it had nothing to prune / no location
    # decision to persist.
    with op.batch_alter_table('AppSetting') as batch:
        batch.add_column(sa.Column(
            'backup_retention_count', sa.Integer(),
            nullable=False, server_default='5',
        ))
        batch.add_column(sa.Column(
            'backup_storage_path', sa.String(length=1024),
            nullable=False, server_default='',
        ))

    # The old fast-path stamped `User.last_backup_at` on every
    # download. The library owns "when was the last backup" via
    # `SELECT MAX(created_at) FROM Backup`, so the per-user column
    # has no writer left. Drop it; pre-release, no data to
    # preserve.
    with op.batch_alter_table('User') as batch:
        batch.drop_column('last_backup_at')


def downgrade():
    with op.batch_alter_table('User') as batch:
        batch.add_column(sa.Column(
            'last_backup_at', sa.DateTime(timezone=True), nullable=True,
        ))
    with op.batch_alter_table('AppSetting') as batch:
        batch.drop_column('backup_storage_path')
        batch.drop_column('backup_retention_count')
    op.drop_index('backup_created_at', table_name='Backup')
    op.drop_table('Backup')
