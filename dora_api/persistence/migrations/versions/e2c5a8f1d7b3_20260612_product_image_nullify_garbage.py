"""20260612_product_image_nullify_garbage

FU-014 — clean up Product.image rows corrupted by the old
`Base64Bytes` create path. Pre-fix: the frontend POSTed a base64 string,
Pydantic's `Base64Bytes` decoded it to raw image bytes (PNG/JPEG), the row
stored those raw bytes, and the read path mis-decoded them as UTF-8.

Post-fix the column holds UTF-8 bytes of a `data:image/...;base64,...`
string. Anything that doesn't start with `data:` is leftover garbage from
the old path and renders as broken images. Null those out so the SPA shows
the fallback icon cleanly; the user can re-save the product to get a
correct image.

Revision ID: e2c5a8f1d7b3
Revises: d7c9e4a8c2b1
Create Date: 2026-06-12 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e2c5a8f1d7b3'
down_revision = 'd7c9e4a8c2b1'
branch_labels = None
depends_on = None


def upgrade():
    # `image` is a LargeBinary column. Compare the leading bytes against the
    # ASCII bytes of "data:" to identify well-formed rows; null everything
    # else. SUBSTR + length on bytea/blob works on both Postgres and SQLite.
    bind = op.get_bind()
    bind.execute(
        sa.text(
            'UPDATE "Product" SET image = NULL '
            'WHERE image IS NOT NULL '
            "AND SUBSTR(image, 1, 5) != :prefix"
        ),
        {"prefix": b"data:"},
    )


def downgrade():
    # Irreversible — the garbage bytes were never recoverable as anything
    # useful (they were raw image bytes mis-typed against UTF-8 decoders).
    pass
