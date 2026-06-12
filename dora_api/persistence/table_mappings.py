from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Table
from sqlalchemy.orm import deferred, registry as SARegistry, relationship
from sqlalchemy_utils import UUIDType

from dora_api.domain.entities.app_setting import AppSetting
from dora_api.domain.entities.audit_event import AuditEvent
from dora_api.domain.entities.auth_token import AuthToken
from dora_api.domain.entities.category import Category
from dora_api.domain.entities.cuisine import Cuisine
from dora_api.domain.entities.dietary_tag import DietaryTag
from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.price_alert import PriceAlert
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_barcode import ProductBarcode
from dora_api.domain.entities.product_historic_offer import ProductHistoricOffer
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.recipe_section import RecipeSection
from dora_api.domain.entities.recipe_step import RecipeStep
from dora_api.domain.entities.shopping_list import ShoppingList, ShoppingListLine
from dora_api.domain.entities.shopping_list_template import (
    ShoppingListTemplate, ShoppingListTemplateLine,
)
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.tool import Tool
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.dora_suggestion_suppression import \
    DoraSuggestionSuppression
from dora_api.domain.entities.stock_item_waste_event import StockItemWasteEvent
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_level_change import StockLevelChange
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.entities.user import User

_mapper_registry = SARegistry()
_mappings_configured = False


def configure_mappings(db: SQLAlchemy):
    global _mappings_configured
    if _mappings_configured:
        return

    metadata = db.metadata

    # ── Tables ────────────────────────────────────────────────────────────────

    merchant_table = Table(
        "Merchant", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255)),
    )

    app_setting_table = Table(
        "AppSetting", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("llm_enabled", Boolean, nullable=False),
        Column("llm_base_url", String(500), nullable=False),
        Column("llm_model", String(255), nullable=False),
        Column("scanning_enabled", Boolean, nullable=False, server_default="0"),
        # C-cross Chunk 1 — install-wide feature flags (proposal §2.6).
        Column("meal_planning_enabled", Boolean, nullable=False, server_default="1"),
        Column("money_enabled", Boolean, nullable=False, server_default="0"),
        Column("nutrition_enabled", Boolean, nullable=False, server_default="0"),
        Column("companion_ingestion_enabled", Boolean, nullable=False, server_default="0"),
        Column("deals_email_enabled", Boolean, nullable=False, server_default="0"),
        # C-cross Chunk 3 — reserved seam for nutrition complex-mode.
        Column("nutrition_db_source", String(255), nullable=False, server_default=""),
    )

    product_offer_table = Table(
        "ProductOffer", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("offered_on", DateTime(timezone=True)),
        Column("price_now", Float),
        Column("price_was", Float),
        Column("product_id", UUIDType, ForeignKey("Product.id", ondelete="CASCADE"), nullable=False),
    )

    product_historic_offer_table = Table(
        "ProductHistoricOffer", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("offered_on", DateTime(timezone=True)),
        Column("price_now", Float),
        Column("price_was", Float),
        Column("product_id", UUIDType, ForeignKey("Product.id", ondelete="CASCADE"), nullable=False),
    )

    product_table = Table(
        "Product", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("brand", String(255), nullable=True),
        Column("image", LargeBinary, nullable=True),
        Column("is_active", Boolean, nullable=False),
        Column("is_available", Boolean, nullable=False),
        Column("merchant_id", UUIDType, ForeignKey("Merchant.id", ondelete="RESTRICT"), nullable=False),
        Column("merchant_stockcode", String(255), nullable=True),
        Column("name", String(255), nullable=False),
        Column("size", String(255)),
        Column("size_unit", String(255)),
        Column("size_value", Float),
        Column("web_url", String(255), nullable=True),
    )

    stock_group_table = Table(
        "StockGroup", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255)),
    )

    stock_level_table = Table(
        "StockLevel", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255)),
        Column("sequence", Integer),
    )

    stock_location_table = Table(
        "StockLocation", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("kind", String(20), nullable=False, server_default="zone"),
        Column("parent_id", UUIDType, ForeignKey("StockLocation.id", ondelete="CASCADE"), nullable=True),
        Column("sequence", Integer, nullable=False, server_default="0"),
    )

    stock_item_table = Table(
        "StockItem", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("days_until_stocktake_alert", Integer),
        Column("expiry_date", Date, nullable=True),
        Column("image", LargeBinary, nullable=True),
        Column("is_flagged", Boolean, nullable=False, server_default="0"),
        Column("is_open", Boolean, nullable=False, server_default="0"),
        Column("opened_on", Date, nullable=True),
        Column("auto_add_when_low", Boolean, nullable=False, server_default="0"),
        Column("name", String(255)),
        Column("notes", String(255), nullable=True),
        Column("stock_group_id", UUIDType, ForeignKey("StockGroup.id", ondelete="SET NULL"), nullable=True),
        Column("stock_level_id", UUIDType, ForeignKey("StockLevel.id", ondelete="SET NULL"), nullable=True),
        Column("stock_level_last_updated", DateTime(timezone=True)),
        Column("stock_location_id", UUIDType, ForeignKey("StockLocation.id", ondelete="SET NULL"), nullable=True),
        Column("stocktake_alerts_are_enabled", Boolean),
        Column("preferred_product_id", UUIDType, ForeignKey("Product.id", ondelete="SET NULL"), nullable=True),
        Column("last_checked_at", DateTime(timezone=True), nullable=True),
    )

    product_barcode_table = Table(
        "ProductBarcode", metadata,
        Column("id", UUIDType, primary_key=True),
        Column(
            "product_id", UUIDType,
            ForeignKey("Product.id", ondelete="CASCADE"),
            nullable=False,
        ),
        Column("barcode", String(255), nullable=False, unique=True),
    )

    price_alert_table = Table(
        "PriceAlert", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("user_id", UUIDType, ForeignKey("User.id", ondelete="CASCADE"), nullable=False),
        Column("product_id", UUIDType, ForeignKey("Product.id", ondelete="CASCADE"), nullable=False),
        Column("threshold_unit_price", Float, nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("last_fired_at", DateTime(timezone=True), nullable=True),
    )

    audit_event_table = Table(
        "AuditEvent", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("occurred_at", DateTime(timezone=True), nullable=False),
        Column("source", String(16), nullable=False),
        Column("actor_user_id", UUIDType, nullable=True),
        Column("actor_ip", String(64), nullable=True),
        Column("action", String(128), nullable=False),
        Column("entity_type", String(64), nullable=True),
        Column("entity_id", UUIDType, nullable=True),
        Column("request_id", String(64), nullable=True),
        Column("payload", String, nullable=True),
        Column("severity", String(16), nullable=False),
    )

    shopping_list_table = Table(
        "ShoppingList", metadata,
        Column("id", UUIDType, primary_key=True),
        # NULL = no custom name; the API serves a date-derived display_name
        # (UX-v2 — custom name is clearable, lists self-label from dates).
        Column("name", String(255), nullable=True),
        # P6-01 lifecycle status (draft/shopping/done) — replaces the old
        # is_archived / is_in_progress flag pair. "Primary" is inferred from
        # DRAFT-count at read time (Chunk 2), not stored.
        Column("status", String(16), nullable=False, server_default="draft"),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("completed_at", DateTime(timezone=True), nullable=True),
        # JSON snapshot of what /finish changed, for server-owned Reopen.
        Column("finish_snapshot", String, nullable=True),
        # P6-01 Chunk 7. Optional shop day the user is planning this list
        # for. Nullable because most lists don't have one — null reads as
        # "no shop day set", not "today".
        Column("planned_shop_date", Date, nullable=True),
    )

    shopping_list_line_table = Table(
        "ShoppingListLine", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("shopping_list_id", UUIDType, ForeignKey("ShoppingList.id", ondelete="CASCADE"), nullable=False),
        # C-7 Chunk 3 — a line is anchored by `stock_item_id` OR
        # `product_id` (or both, when a product is nested under a
        # stock item). Both columns are nullable individually; a
        # CHECK enforces that at least one is set.
        Column("stock_item_id", UUIDType, ForeignKey("StockItem.id", ondelete="CASCADE"), nullable=True),
        Column("product_id", UUIDType, ForeignKey("Product.id", ondelete="CASCADE"), nullable=True),
        CheckConstraint(
            "stock_item_id IS NOT NULL OR product_id IS NOT NULL",
            name="ck_shopping_list_line_anchor",
        ),
        Column("quantity", Integer, nullable=True),
        Column("is_ticked", Boolean, nullable=False, server_default="0"),
        Column("selected_product_id", UUIDType, ForeignKey("Product.id", ondelete="SET NULL"), nullable=True),
        Column("sequence", Integer, nullable=False, server_default="0"),
        Column("added_via", String(32), nullable=False, server_default="manual"),
        Column("added_at", DateTime(timezone=True), nullable=True),
        Column("picked_offer_price", Float, nullable=True),
        Column("list_price_at_pick", Float, nullable=True),
        # P2-02 purchase memory — what the shopper actually paid / where
        # they bought it. NULL when the user didn't override the planned
        # offer; reports & the assistant fall back to picked_offer_price.
        Column("actual_unit_price", Float, nullable=True),
        Column(
            "purchased_merchant_id", UUIDType,
            ForeignKey("Merchant.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    shopping_list_template_table = Table(
        "ShoppingListTemplate", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("updated_at", DateTime(timezone=True), nullable=False),
    )

    shopping_list_template_line_table = Table(
        "ShoppingListTemplateLine", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("template_id", UUIDType, ForeignKey("ShoppingListTemplate.id", ondelete="CASCADE"), nullable=False),
        Column("stock_item_id", UUIDType, ForeignKey("StockItem.id", ondelete="CASCADE"), nullable=False),
        Column("quantity", Integer, nullable=True),
        Column("sequence", Integer, nullable=False, server_default="0"),
    )

    stock_item_product_table = Table(
        "StockItemProduct", metadata,
        Column("stock_item_id", UUIDType, ForeignKey("StockItem.id", ondelete="CASCADE"), primary_key=True),
        Column("product_id", UUIDType, ForeignKey("Product.id", ondelete="CASCADE"), primary_key=True),
    )

    # Self-referential m2m: a stock item's substitutes. Undirected — pairs
    # are stored in canonical order (a_id < b_id) so each unordered pair has
    # exactly one row. Callers must canonicalise via `canonical_pair()` from
    # dora_api.features.substitutes.canonical before insert/delete/query.
    # CASCADE both FKs so deleting an item cleans up its pairs.
    stock_item_substitute_table = Table(
        "StockItemSubstitute", metadata,
        Column("stock_item_a_id", UUIDType, ForeignKey("StockItem.id", ondelete="CASCADE"), primary_key=True),
        Column("stock_item_b_id", UUIDType, ForeignKey("StockItem.id", ondelete="CASCADE"), primary_key=True),
        Column("notes", String, nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False),
        CheckConstraint("stock_item_a_id < stock_item_b_id", name="ck_substitute_canonical"),
    )

    stock_level_change_table = Table(
        "StockLevelChange", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("stock_item_id", UUIDType, ForeignKey("StockItem.id", ondelete="CASCADE"), nullable=False),
        Column("stock_level_id", UUIDType, ForeignKey("StockLevel.id", ondelete="SET NULL"), nullable=True),
        Column("stock_level_name", String(255), nullable=True),
        Column("changed_at", DateTime(timezone=True), nullable=False),
    )

    # P2-04 — user's negative decisions on Dora suggestions. One row per
    # (kind, dedup_key) the user has dismissed or snoozed. The generator
    # filters proposed suggestions against this table on every call.
    dora_suggestion_suppression_table = Table(
        "DoraSuggestionSuppression", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("kind", String(64), nullable=False),
        Column("dedup_key", String(255), nullable=False),
        Column("decision", String(16), nullable=False),
        Column("snoozed_until", DateTime(timezone=True), nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False),
    )

    # P2-06 — append-only log of discarded food. FK is SET NULL (not
    # CASCADE) so deleting a stock item doesn't wipe waste history; the
    # denormalised name on the row keeps insights readable.
    stock_item_waste_event_table = Table(
        "StockItemWasteEvent", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("stock_item_id", UUIDType, ForeignKey("StockItem.id", ondelete="SET NULL"), nullable=True),
        Column("stock_item_name", String(255), nullable=False),
        Column("reason", String(32), nullable=False),
        Column("quantity", Integer, nullable=True),
        Column("estimated_value", Float, nullable=True),
        Column("note", String, nullable=True),
        Column("occurred_at", DateTime(timezone=True), nullable=False),
    )

    recipe_collection_table = Table(
        "RecipeCollection", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255), nullable=False),
    )

    # C-4 Chunk 2 — user-configurable recipe vocabularies (cuisine, category,
    # dietary tags). Each is a simple {id, name, sequence} lookup edited in
    # settings; recipes link to them by FK (cuisine/category single-select,
    # dietary tags many-to-many).
    cuisine_table = Table(
        "Cuisine", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("sequence", Integer, nullable=False, server_default="0"),
    )

    category_table = Table(
        "Category", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("sequence", Integer, nullable=False, server_default="0"),
    )

    dietary_tag_table = Table(
        "DietaryTag", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("category", String(255), nullable=False),
        Column("sequence", Integer, nullable=False, server_default="0"),
    )

    # C-4 Chunk 5 — user-configurable kitchen-tool vocabulary.
    tool_table = Table(
        "Tool", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("sequence", Integer, nullable=False, server_default="0"),
    )

    recipe_table = Table(
        "Recipe", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("available_meals", Integer, nullable=False, server_default="0"),
        Column("category_id", UUIDType, ForeignKey("Category.id", ondelete="SET NULL"), nullable=True),
        Column("cook_time_minutes", Integer, nullable=True),
        Column("cuisine_id", UUIDType, ForeignKey("Cuisine.id", ondelete="SET NULL"), nullable=True),
        Column("difficulty", String(50), nullable=True),
        Column("image", LargeBinary, nullable=True),
        Column("instructions", String, nullable=True),
        Column("is_favourite", Boolean, nullable=False),
        Column("last_made_on", DateTime(timezone=True), nullable=True),
        Column("name", String(255), nullable=False),
        Column("nutrition", String, nullable=True),
        Column("prep_time_minutes", Integer, nullable=True),
        Column("recipe_collection_id", UUIDType, ForeignKey("RecipeCollection.id", ondelete="SET NULL"), nullable=True),
        Column("servings", Integer, nullable=True),
        # C-4 Chunk 7 — origin URL for imported recipes.
        Column("source", String(2048), nullable=True),
        Column("time_of_day", String(50), nullable=True),
        # C-4 Chunk 8 — version sibling grouping (DEC-2). NULL = singleton.
        # Indexed because every detail load asks "who else has this id?".
        Column("version_group_id", UUIDType, nullable=True, index=True),
        # C-4 Chunk 9 — simple nutrition (kcal). NULL when unset.
        Column("kcal", Integer, nullable=True),
    )

    # C-4 Chunk 2 — recipe → dietary-tag association. The tag vocabulary is
    # now the `DietaryTag` entity (was an in-code catalogue); this table pins
    # which tag(s) belong to a recipe. No standalone mapping is registered
    # (matching the StockItemProduct/StockItemSubstitute pattern); handlers
    # read/write rows via the recipe_tag_access helpers.
    recipe_tag_table = Table(
        "RecipeTag", metadata,
        Column("recipe_id", UUIDType, ForeignKey("Recipe.id", ondelete="CASCADE"), primary_key=True),
        Column("dietary_tag_id", UUIDType, ForeignKey("DietaryTag.id", ondelete="CASCADE"), primary_key=True),
    )

    # C-4 Chunk 5 — recipe → tool association (pure link, no standalone
    # mapping; accessed via recipe_tool_access helpers).
    recipe_tool_table = Table(
        "RecipeTool", metadata,
        Column("recipe_id", UUIDType, ForeignKey("Recipe.id", ondelete="CASCADE"), primary_key=True),
        Column("tool_id", UUIDType, ForeignKey("Tool.id", ondelete="CASCADE"), primary_key=True),
    )

    # C-4 Chunk 10 — named groups within a recipe (DEC-3 option A). Optional;
    # ingredients/steps with NULL section_id are the implicit "main" group.
    recipe_section_table = Table(
        "RecipeSection", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("recipe_id", UUIDType, ForeignKey("Recipe.id", ondelete="CASCADE"), nullable=False),
        Column("sequence", Integer, nullable=False, server_default="0"),
        Column("name", String(255), nullable=False),
    )

    recipe_ingredient_table = Table(
        "RecipeIngredient", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("notes", String(255), nullable=True),
        Column("quantity", Float, nullable=True),
        Column("recipe_id", UUIDType, ForeignKey("Recipe.id", ondelete="CASCADE"), nullable=False),
        Column("stock_item_id", UUIDType, ForeignKey("StockItem.id", ondelete="RESTRICT"), nullable=False),
        Column("unit", String(50), nullable=True),
        # C-4 Chunk 10 — nullable section grouping (ON DELETE SET NULL so
        # removing a section keeps its ingredients, just unsectioned).
        Column("section_id", UUIDType, ForeignKey("RecipeSection.id", ondelete="SET NULL"), nullable=True),
    )

    # C-4 Chunk 6 — structured recipe steps. Self-referential `parent_step_id`
    # enables one level of sub-steps (a sub-step's parent must itself be a
    # top-level step; depth>1 is rejected in the access helper). Two link
    # tables: which of the recipe's own ingredients this step uses, and which
    # tools (from the Chunk 5 vocabulary). Both are pure (step_id, x_id) pairs
    # accessed via the `recipe_step_access` helpers — no standalone mapping.
    recipe_step_table = Table(
        "RecipeStep", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("recipe_id", UUIDType, ForeignKey("Recipe.id", ondelete="CASCADE"), nullable=False),
        Column("parent_step_id", UUIDType, ForeignKey("RecipeStep.id", ondelete="CASCADE"), nullable=True),
        Column("sequence", Integer, nullable=False, server_default="0"),
        Column("text", String, nullable=False),
        Column("hint", String, nullable=True),
        # C-4 Chunk 10 — nullable section grouping. Top-level steps may
        # belong to a section; sub-steps inherit visually but the FK is
        # stored per-row to keep reads flat.
        Column("section_id", UUIDType, ForeignKey("RecipeSection.id", ondelete="SET NULL"), nullable=True),
    )

    recipe_step_ingredient_table = Table(
        "RecipeStepIngredient", metadata,
        Column("step_id", UUIDType, ForeignKey("RecipeStep.id", ondelete="CASCADE"), primary_key=True),
        Column("recipe_ingredient_id", UUIDType, ForeignKey("RecipeIngredient.id", ondelete="CASCADE"), primary_key=True),
    )

    recipe_step_tool_table = Table(
        "RecipeStepTool", metadata,
        Column("step_id", UUIDType, ForeignKey("RecipeStep.id", ondelete="CASCADE"), primary_key=True),
        Column("tool_id", UUIDType, ForeignKey("Tool.id", ondelete="CASCADE"), primary_key=True),
    )

    meal_plan_table = Table(
        "MealPlan", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("start_date", Date, nullable=False),
    )

    meal_plan_entry_table = Table(
        "MealPlanEntry", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("recipe_id", UUIDType, ForeignKey("Recipe.id", ondelete="CASCADE"), nullable=False),
        Column("meal_plan_id", UUIDType, ForeignKey("MealPlan.id", ondelete="CASCADE"), nullable=False),
        Column("scheduled_for", Date, nullable=False),
        Column("servings", Integer, nullable=False, server_default="1"),
        Column("slot", String(50), nullable=False),
        Column("consumed_at", DateTime(timezone=True), nullable=True),
    )

    user_table = Table(
        "User", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("email", String(255), nullable=True),
        Column("password_hash", String(255), nullable=True),
        Column("send_deals_on_day", Integer),
        Column("username", String(255), nullable=False, unique=True),
        Column("is_admin", Boolean, nullable=False, default=False, server_default="0"),
        Column("deals_email_enabled", Boolean, nullable=False, server_default="1"),
        Column("deals_email_compact", Boolean, nullable=False, server_default="0"),
        Column("theme", String(20), nullable=False, server_default="system"),
        Column("font_family", String(20), nullable=False, server_default="default"),
        Column("font_size", String(2), nullable=False, server_default="md"),
        Column("onboarding_completed_at", DateTime, nullable=True),
        Column("last_backup_at", DateTime(timezone=True), nullable=True),
        Column("email_verified", Boolean, nullable=False, server_default="0"),
        Column("password_changed_at", DateTime(timezone=True), nullable=True),
        # P2-05 — grocery budget. NULL amount = feature off.
        Column("budget_amount", Float, nullable=True),
        Column("budget_period", String(16), nullable=False, server_default="weekly"),
        # P2-13 — voice opt-ins. Off by default; SPA seeds the in-page
        # toggles from these and the user can override per session.
        Column("voice_input_enabled", Boolean, nullable=False, server_default="0"),
        Column("voice_output_enabled", Boolean, nullable=False, server_default="0"),
        # C-cross Chunk 2 — per-user money opt-in (proposal §2.2).
        Column("money_features_enabled", Boolean, nullable=False, server_default="0"),
        # C-cross Chunk 3 — per-user nutrition mode (proposal §2.3).
        Column("nutrition_mode", String(16), nullable=False, server_default="off"),
        # C-cross Chunk 5 — per-user image-display opt-ins (proposal §2.8).
        # Default True (visual richness on by default; users opt out).
        Column("show_recipe_images", Boolean, nullable=False, server_default="1"),
        Column("show_stock_images", Boolean, nullable=False, server_default="1"),
    )

    auth_token_table = Table(
        "AuthToken", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("user_id", UUIDType, ForeignKey("User.id", ondelete="CASCADE"), nullable=False),
        Column("token_hash", String(64), nullable=False, unique=True),
        Column("purpose", String(32), nullable=False),
        Column("payload", String(255), nullable=True),
        Column("expires_at", DateTime(timezone=True), nullable=False),
        Column("consumed_at", DateTime(timezone=True), nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False),
    )

    # ── Mappings ──────────────────────────────────────────────────────────────

    _mapper_registry.map_imperatively(Merchant, merchant_table, properties={
        "_id_col": merchant_table.c.id,
        "id": merchant_table.c.id,
    })

    _mapper_registry.map_imperatively(StockGroup, stock_group_table, properties={
        "_id_col": stock_group_table.c.id,
        "id": stock_group_table.c.id,
    })

    _mapper_registry.map_imperatively(AppSetting, app_setting_table, properties={
        "_id_col": app_setting_table.c.id,
        "id": app_setting_table.c.id,
    })

    _mapper_registry.map_imperatively(StockLevel, stock_level_table, properties={
        "_id_col": stock_level_table.c.id,
        "id": stock_level_table.c.id,
    })

    # Children are loaded manually by repository queries (matching the rest
    # of the codebase's noload+manual fetch pattern). Cascade-delete is
    # handled at the FK level via ondelete="CASCADE" on parent_id.
    _mapper_registry.map_imperatively(StockLocation, stock_location_table, properties={
        "_id_col": stock_location_table.c.id,
        "id": stock_location_table.c.id,
    })

    _mapper_registry.map_imperatively(User, user_table, properties={
        "_id_col": user_table.c.id,
        "id": user_table.c.id,
    })

    _mapper_registry.map_imperatively(ProductOffer, product_offer_table, properties={
        "_id_col": product_offer_table.c.id,
        "_product_id": product_offer_table.c.product_id,
        "id": product_offer_table.c.id,
    })

    _mapper_registry.map_imperatively(ProductHistoricOffer, product_historic_offer_table, properties={
        "_id_col": product_historic_offer_table.c.id,
        "_product_id": product_historic_offer_table.c.product_id,
        "id": product_historic_offer_table.c.id,
    })

    _mapper_registry.map_imperatively(Product, product_table, properties={
        "_id_col": product_table.c.id,
        "_merchant_id": product_table.c.merchant_id,
        "id": product_table.c.id,
        # FU-014 — defer the image blob so list endpoints (get_products,
        # best-deals) never pull megabytes per row. The dedicated
        # `/products/<id>/image` route triggers the load on attribute
        # access; `has_image` on ProductDto is derived from a separate
        # `IS NOT NULL` check. Mirrors the stock-item / recipe pattern.
        "image": deferred(product_table.c.image),
        "merchant": relationship(Merchant, lazy="noload"),
        "current_offer": relationship(ProductOffer, lazy="noload", uselist=False),
        "historic_offers": relationship(ProductHistoricOffer, lazy="noload"),
    })

    _mapper_registry.map_imperatively(StockItem, stock_item_table, properties={
        "_id_col": stock_item_table.c.id,
        "_stock_group_id": stock_item_table.c.stock_group_id,
        "_stock_level_id": stock_item_table.c.stock_level_id,
        "_stock_location_id": stock_item_table.c.stock_location_id,
        "id": stock_item_table.c.id,
        # C-1 Chunk 6 / FU-033 — defer the image blob so the list endpoint
        # never pulls megabytes per row just to set `has_image`. The
        # dedicated `/stock-items/<id>/image` route triggers the load on
        # attribute access; `has_image` is hydrated via a separate SELECT
        # (mirrors the recipe-image pattern from Cookbook Chunk 5 / FU-090).
        "image": deferred(stock_item_table.c.image),
        "stock_group": relationship(StockGroup, lazy="noload"),
        "stock_level": relationship(StockLevel, lazy="noload"),
        "stock_location": relationship(StockLocation, lazy="noload"),
        "products": relationship(Product, secondary=stock_item_product_table, lazy="noload"),
        # preferred_product_id auto-maps from the column of the same name.
        # Substitutes (StockItemSubstitute) are a self-referential m2m accessed
        # via the association table directly — no relationship is mapped because
        # the generic query builder can't self-join StockItem to itself.
    })

    _mapper_registry.map_imperatively(StockLevelChange, stock_level_change_table, properties={
        "_id_col": stock_level_change_table.c.id,
        "id": stock_level_change_table.c.id,
    })

    _mapper_registry.map_imperatively(StockItemWasteEvent, stock_item_waste_event_table, properties={
        "_id_col": stock_item_waste_event_table.c.id,
        "id": stock_item_waste_event_table.c.id,
    })

    _mapper_registry.map_imperatively(DoraSuggestionSuppression, dora_suggestion_suppression_table, properties={
        "_id_col": dora_suggestion_suppression_table.c.id,
        "id": dora_suggestion_suppression_table.c.id,
    })

    _mapper_registry.map_imperatively(ProductBarcode, product_barcode_table, properties={
        "_id_col": product_barcode_table.c.id,
        "id": product_barcode_table.c.id,
    })

    _mapper_registry.map_imperatively(AuditEvent, audit_event_table, properties={
        "_id_col": audit_event_table.c.id,
        "id": audit_event_table.c.id,
    })

    _mapper_registry.map_imperatively(AuthToken, auth_token_table, properties={
        "_id_col": auth_token_table.c.id,
        "id": auth_token_table.c.id,
    })

    _mapper_registry.map_imperatively(PriceAlert, price_alert_table, properties={
        "_id_col": price_alert_table.c.id,
        "id": price_alert_table.c.id,
    })

    _mapper_registry.map_imperatively(RecipeCollection, recipe_collection_table, properties={
        "_id_col": recipe_collection_table.c.id,
        "id": recipe_collection_table.c.id,
    })

    _mapper_registry.map_imperatively(RecipeIngredient, recipe_ingredient_table, properties={
        "_id_col": recipe_ingredient_table.c.id,
        # FK columns are bound to underscore-prefixed properties so they're
        # ignored by verify_mappings (which compares the entity's dataclass
        # fields against publicly-mapped properties).
        "_recipe_id": recipe_ingredient_table.c.recipe_id,
        "_stock_item_id": recipe_ingredient_table.c.stock_item_id,
        "id": recipe_ingredient_table.c.id,
        # C-4 Chunk 10 — section_id is a real domain attribute (nullable),
        # mapped publicly so it round-trips through `from_entity`.
        "section_id": recipe_ingredient_table.c.section_id,
        "stock_item": relationship(StockItem, lazy="noload"),
    })

    # C-4 Chunk 10 — recipe sections (named groups). No relationship from
    # Recipe; sections are loaded directly by the access helper (matches
    # the RecipeStep pattern).
    _mapper_registry.map_imperatively(RecipeSection, recipe_section_table, properties={
        "_id_col": recipe_section_table.c.id,
        "id": recipe_section_table.c.id,
        "recipe_id": recipe_section_table.c.recipe_id,
        "sequence": recipe_section_table.c.sequence,
        "name": recipe_section_table.c.name,
    })

    # C-4 Chunk 6 — structured step rows. Ingredient + tool links are not
    # mapped as SQLAlchemy relationships; the access helper queries the link
    # tables directly when hydrating the DTO (matches the dietary-tag/tool
    # pattern). All entity fields are publicly mapped (recipe_id/
    # parent_step_id are real domain attributes, not internal FKs).
    _mapper_registry.map_imperatively(RecipeStep, recipe_step_table, properties={
        "_id_col": recipe_step_table.c.id,
        "id": recipe_step_table.c.id,
        "recipe_id": recipe_step_table.c.recipe_id,
        "parent_step_id": recipe_step_table.c.parent_step_id,
        "sequence": recipe_step_table.c.sequence,
        "text": recipe_step_table.c.text,
        "hint": recipe_step_table.c.hint,
        # C-4 Chunk 10 — nullable section grouping for top-level steps.
        "section_id": recipe_step_table.c.section_id,
    })

    _mapper_registry.map_imperatively(Cuisine, cuisine_table, properties={
        "_id_col": cuisine_table.c.id,
        "id": cuisine_table.c.id,
    })

    _mapper_registry.map_imperatively(Category, category_table, properties={
        "_id_col": category_table.c.id,
        "id": category_table.c.id,
    })

    _mapper_registry.map_imperatively(DietaryTag, dietary_tag_table, properties={
        "_id_col": dietary_tag_table.c.id,
        "id": dietary_tag_table.c.id,
    })

    _mapper_registry.map_imperatively(Tool, tool_table, properties={
        "_id_col": tool_table.c.id,
        "id": tool_table.c.id,
    })

    _mapper_registry.map_imperatively(Recipe, recipe_table, properties={
        "_id_col": recipe_table.c.id,
        "_recipe_collection_id": recipe_table.c.recipe_collection_id,
        "_cuisine_id": recipe_table.c.cuisine_id,
        "_category_id": recipe_table.c.category_id,
        "id": recipe_table.c.id,
        # C-cross Chunk 5 / FU-090 — defer the image blob so the list
        # endpoint doesn't load every recipe's image bytes into memory
        # just to compute `has_image`. The detail endpoint (and the
        # dedicated `/recipes/<id>/image` route) trigger the load
        # on-demand via attribute access; everywhere else gets the
        # `has_image: bool` DTO field from a separate SELECT.
        "image": deferred(recipe_table.c.image),
        "recipe_collection": relationship(RecipeCollection, lazy="noload"),
        # selectin (not noload): cuisine + category are tiny, always-wanted
        # lookups, so every recipe read carries them without each call site
        # needing an explicit .include() (keeps the assistant / search /
        # export consumers simple).
        "cuisine": relationship(Cuisine, lazy="selectin"),
        "category": relationship(Category, lazy="selectin"),
        "ingredients": relationship(
            RecipeIngredient,
            lazy="noload",
            cascade="all, delete-orphan",
            foreign_keys=[recipe_ingredient_table.c.recipe_id],
        ),
    })

    _mapper_registry.map_imperatively(MealPlanEntry, meal_plan_entry_table, properties={
        "_id_col": meal_plan_entry_table.c.id,
        "_recipe_id": meal_plan_entry_table.c.recipe_id,
        # See RecipeIngredient above — FK columns hidden from verify_mappings.
        "_meal_plan_id": meal_plan_entry_table.c.meal_plan_id,
        "id": meal_plan_entry_table.c.id,
        "recipe": relationship(Recipe, lazy="noload"),
    })

    _mapper_registry.map_imperatively(MealPlan, meal_plan_table, properties={
        "_id_col": meal_plan_table.c.id,
        "id": meal_plan_table.c.id,
        "entries": relationship(
            MealPlanEntry,
            lazy="noload",
            cascade="all, delete-orphan",
            foreign_keys=[meal_plan_entry_table.c.meal_plan_id],
        ),
    })

    # ShoppingListLine exposes its FK columns directly as `shopping_list_id`,
    # `stock_item_id`, and `selected_product_id` on the dataclass (raw UUIDs,
    # not relationship objects). They auto-map from the table columns of the
    # same name, so we only need to explicitly map `id` for the verify check.
    _mapper_registry.map_imperatively(ShoppingListLine, shopping_list_line_table, properties={
        "_id_col": shopping_list_line_table.c.id,
        "id": shopping_list_line_table.c.id,
    })

    _mapper_registry.map_imperatively(ShoppingList, shopping_list_table, properties={
        "_id_col": shopping_list_table.c.id,
        "id": shopping_list_table.c.id,
        # Lines are added directly via `repo.add(line)` rather than appended
        # through `list.lines`. Using `delete-orphan` would implicitly require
        # `single_parent=True` and complain about lines added outside the
        # collection. Plain "all" cascade is enough — the DB-level FK has
        # ON DELETE CASCADE so a deleted list takes its lines with it.
        "lines": relationship(
            ShoppingListLine,
            primaryjoin=shopping_list_table.c.id == shopping_list_line_table.c.shopping_list_id,
            cascade="all",
            lazy="noload",
        ),
    })

    # Template line — same pattern as ShoppingListLine. FK columns map by
    # name (template_id, stock_item_id); only `id` needs the explicit alias.
    _mapper_registry.map_imperatively(
        ShoppingListTemplateLine, shopping_list_template_line_table, properties={
            "_id_col": shopping_list_template_line_table.c.id,
            "id": shopping_list_template_line_table.c.id,
        }
    )

    _mapper_registry.map_imperatively(
        ShoppingListTemplate, shopping_list_template_table, properties={
            "_id_col": shopping_list_template_table.c.id,
            "id": shopping_list_template_table.c.id,
            "lines": relationship(
                ShoppingListTemplateLine,
                primaryjoin=(
                    shopping_list_template_table.c.id
                    == shopping_list_template_line_table.c.template_id
                ),
                cascade="all",
                lazy="noload",
            ),
        }
    )

    verify_mappings()
    _mappings_configured = True


def verify_mappings():
    from dataclasses import fields as dc_fields
    from dora_api.domain.exceptions import PersistenceError

    for mapper in _mapper_registry.mappers:
        entity_class = mapper.class_
        mapped_attrs = {
            prop.key for prop in mapper.iterate_properties
            if not prop.key.startswith("_")
        }
        entity_fields = {f.name for f in dc_fields(entity_class)}

        unmapped = entity_fields - mapped_attrs
        if unmapped:
            raise PersistenceError(f"{entity_class.__name__} has fields not mapped to persistence: {unmapped}")

        extra = mapped_attrs - entity_fields
        if extra:
            raise PersistenceError(f"{entity_class.__name__} has mapped attributes not present on entity: {extra}")
