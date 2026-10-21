"""20260715_fk_covering_indexes

FU-563 (from the FU-393 data-model sanity sweep, Finding 2) — add a covering
index on every foreign-key column that lacked one. Neither SQLite nor Postgres
auto-indexes FK columns, so an unindexed FK means a parent-row delete
full-scans the child table (for CASCADE/SET NULL) and every join on that key is
unindexed. 43 FK columns were uncovered in the production schema; this adds a
plain single-column index to each. Purely additive — no table rewrites, no data
change — so it applies cleanly on both SQLite and Postgres (R-005/R-006).

The matching `Index(...)` declarations were mirrored into the ORM model
(`table_mappings.py`), which now also carries the 32 previously
migration-only indexes/uniques, so `create_all()` (dev/test) finally matches
the migrated schema. `test_migrations.py` compares column + nullability + index
colsets to keep them in lockstep.

Revision ID: b9d4f2a7c3e1
Revises: a1b7f3e9c2d4
Create Date: 2026-07-15 00:00:00.000000
"""
from alembic import op


revision = 'b9d4f2a7c3e1'
down_revision = 'a1b7f3e9c2d4'
branch_labels = None
depends_on = None


# (index_name, table, column) for every FK column that had no covering index.
_FK_INDEXES = [
    ("ix_Backup_created_by_user_id", "Backup", "created_by_user_id"),
    ("ix_Barcode_stock_item_id", "Barcode", "stock_item_id"),
    ("ix_ConsumptionEvent_recipe_id", "ConsumptionEvent", "recipe_id"),
    ("ix_CookEvent_cooked_by_user_id", "CookEvent", "cooked_by_user_id"),
    ("ix_IngestionStoreMapping_store_id", "IngestionStoreMapping", "store_id"),
    ("ix_MealPlanEntry_meal_plan_id", "MealPlanEntry", "meal_plan_id"),
    ("ix_MealPlanEntry_recipe_id", "MealPlanEntry", "recipe_id"),
    ("ix_MealPlanReconcileReceipt_meal_plan_entry_id", "MealPlanReconcileReceipt", "meal_plan_entry_id"),
    ("ix_MealPlanReconcileReceipt_resolved_by_user_id", "MealPlanReconcileReceipt", "resolved_by_user_id"),
    ("ix_MealPlanSwapLedger_applied_by_user_id", "MealPlanSwapLedger", "applied_by_user_id"),
    ("ix_MealPlanSwapLedger_meal_plan_id", "MealPlanSwapLedger", "meal_plan_id"),
    ("ix_MealPlanTemplateEntry_recipe_id", "MealPlanTemplateEntry", "recipe_id"),
    ("ix_MealPlanTemplateEntry_template_id", "MealPlanTemplateEntry", "template_id"),
    ("ix_MealPlanTemplateSetItem_set_id", "MealPlanTemplateSetItem", "set_id"),
    ("ix_PreferredBuy_stock_item_id", "PreferredBuy", "stock_item_id"),
    ("ix_Product_store_id", "Product", "store_id"),
    ("ix_ProductHistoricOffer_product_id", "ProductHistoricOffer", "product_id"),
    ("ix_ProductOffer_product_id", "ProductOffer", "product_id"),
    ("ix_Recipe_category_id", "Recipe", "category_id"),
    ("ix_Recipe_cuisine_id", "Recipe", "cuisine_id"),
    ("ix_Recipe_recipe_collection_id", "Recipe", "recipe_collection_id"),
    ("ix_RecipeIngredient_recipe_id", "RecipeIngredient", "recipe_id"),
    ("ix_RecipeIngredient_section_id", "RecipeIngredient", "section_id"),
    ("ix_RecipeIngredient_stock_item_id", "RecipeIngredient", "stock_item_id"),
    ("ix_RecipeStep_section_id", "RecipeStep", "section_id"),
    ("ix_ShoppingListLine_product_id", "ShoppingListLine", "product_id"),
    ("ix_ShoppingListLine_purchased_store_id", "ShoppingListLine", "purchased_store_id"),
    ("ix_ShoppingListLine_selected_product_id", "ShoppingListLine", "selected_product_id"),
    ("ix_ShoppingListLine_shopping_list_id", "ShoppingListLine", "shopping_list_id"),
    ("ix_ShoppingListLine_stock_item_id", "ShoppingListLine", "stock_item_id"),
    ("ix_ShoppingListTemplateLine_stock_item_id", "ShoppingListTemplateLine", "stock_item_id"),
    ("ix_ShoppingListTemplateLine_template_id", "ShoppingListTemplateLine", "template_id"),
    ("ix_StockItem_stock_group_id", "StockItem", "stock_group_id"),
    ("ix_StockItem_stock_level_id", "StockItem", "stock_level_id"),
    ("ix_StockItem_stock_location_id", "StockItem", "stock_location_id"),
    ("ix_StockItem_usual_store_id", "StockItem", "usual_store_id"),
    ("ix_StockItemPriceObservation_stock_item_id", "StockItemPriceObservation", "stock_item_id"),
    ("ix_StockItemPriceObservation_store_id", "StockItemPriceObservation", "store_id"),
    ("ix_StockItemSubstitute_stock_item_b_id", "StockItemSubstitute", "stock_item_b_id"),
    ("ix_StockItemWasteEvent_stock_item_id", "StockItemWasteEvent", "stock_item_id"),
    ("ix_StockLevelChange_stock_item_id", "StockLevelChange", "stock_item_id"),
    ("ix_StockLevelChange_stock_level_id", "StockLevelChange", "stock_level_id"),
    ("ix_StockLocation_parent_id", "StockLocation", "parent_id"),
]


def upgrade():
    for name, table, column in _FK_INDEXES:
        op.create_index(name, table, [column], unique=False)


def downgrade():
    for name, table, column in reversed(_FK_INDEXES):
        op.drop_index(name, table_name=table)
