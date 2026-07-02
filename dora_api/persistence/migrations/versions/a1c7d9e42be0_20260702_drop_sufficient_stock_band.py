"""20260702_drop_sufficient_stock_band

Collapse the 4-band StockLevel scheme to 3 bands (Stocked / Low / Out)
to align with P8-07 Zero-Input Pantry's charter-mandated inference
vocabulary. The old "Sufficient Stock" band was semantically dead — no
predicate discriminated it, and the middle band clashed with P8-07's
Out/Low/Stocked belief model.

Steps:
1. Reassign any StockItem currently pointing at the Sufficient row
   (sequence=1) to the Well-Stocked row (sequence=0).
2. Hard-delete any StockLevelChange rows tied to the Sufficient row.
   Pre-release: not worth preserving Sufficient-band history via the
   SET NULL + denormalised name path.
3. Delete the Sufficient row (sequence=1).
4. Reseries: Low (was seq=2) → seq=1, Out (was seq=3) → seq=2. No unique
   constraint on `sequence` so no collision risk during the two-step
   update.
5. Rename the seq=0 row from "Well-Stocked" to "Stocked". Domain enum
   member also renamed WELL_STOCKED → STOCKED in the same commit.

Merges the three open heads (product-unique / drop-nutrition /
buy-verdict-enabled) that were sitting alongside each other on
2026-07-02.

Revision ID: a1c7d9e42be0
Revises: c4a8e2b9d7f5, b7e2d9a4c1f5, e2b9c4a7f5d1
Create Date: 2026-07-02 00:00:00.000000
"""
from alembic import op


revision = 'a1c7d9e42be0'
down_revision = ('c4a8e2b9d7f5', 'b7e2d9a4c1f5', 'e2b9c4a7f5d1')
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Redirect StockItems pointing at Sufficient → Stocked.
    conn.exec_driver_sql("""
        UPDATE "StockItem"
        SET stock_level_id = (
            SELECT id FROM "StockLevel" WHERE sequence = 0
        )
        WHERE stock_level_id = (
            SELECT id FROM "StockLevel" WHERE sequence = 1
        )
    """)

    # 2. Hard-delete Sufficient-band history. Pre-release; not worth
    #    keeping null-FK audit rows around just to render "Sufficient
    #    Stock" in the history rail.
    conn.exec_driver_sql("""
        DELETE FROM "StockLevelChange"
        WHERE stock_level_id = (
            SELECT id FROM "StockLevel" WHERE sequence = 1
        )
    """)

    # 3. Delete the Sufficient StockLevel row itself.
    conn.exec_driver_sql("""
        DELETE FROM "StockLevel" WHERE sequence = 1
    """)

    # 4. Reseries Low (2 → 1) then Out (3 → 2). Rows are disjoint;
    #    no unique constraint on `sequence` so order does not matter
    #    against a collision, but keeping ascending order for readability.
    conn.exec_driver_sql("""
        UPDATE "StockLevel" SET sequence = 1 WHERE sequence = 2
    """)
    conn.exec_driver_sql("""
        UPDATE "StockLevel" SET sequence = 2 WHERE sequence = 3
    """)

    # 5. Rename Well-Stocked → Stocked.
    conn.exec_driver_sql("""
        UPDATE "StockLevel" SET name = 'Stocked' WHERE sequence = 0
    """)


def downgrade():
    conn = op.get_bind()

    # Reverse of upgrade. Recreates the Sufficient row with a fresh id;
    # any StockItem that was collapsed to Stocked stays on Stocked (we
    # cannot know which items were originally Sufficient — that
    # distinction is lost by design). Sufficient-band StockLevelChange
    # rows were hard-deleted on upgrade and are not recreated.
    conn.exec_driver_sql("""
        UPDATE "StockLevel" SET name = 'Well-Stocked' WHERE sequence = 0
    """)
    conn.exec_driver_sql("""
        UPDATE "StockLevel" SET sequence = 3 WHERE sequence = 2
    """)
    conn.exec_driver_sql("""
        UPDATE "StockLevel" SET sequence = 2 WHERE sequence = 1
    """)

    import uuid
    conn.exec_driver_sql(
        f"""
        INSERT INTO "StockLevel" (id, name, sequence)
        VALUES ('{uuid.uuid4()}', 'Sufficient Stock', 1)
        """
    )
