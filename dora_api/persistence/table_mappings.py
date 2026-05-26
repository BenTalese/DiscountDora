from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Table
from sqlalchemy.orm import registry as SARegistry, relationship
from sqlalchemy_utils import UUIDType

from dora_api.domain.entities.app_setting import AppSetting
from dora_api.domain.entities.audit_event import AuditEvent
from dora_api.domain.entities.auth_token import AuthToken
from dora_api.domain.entities.meal import Meal
from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.price_alert import PriceAlert
from dora_api.domain.entities.stock_map import StockMap
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_barcode import ProductBarcode
from dora_api.domain.entities.product_historic_offer import ProductHistoricOffer
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.shopping_list import ShoppingList, ShoppingListLine
from dora_api.domain.entities.shopping_list_template import (
    ShoppingListTemplate, ShoppingListTemplateLine,
)
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
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
        Column("barcode", String(255), nullable=True, unique=True),
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

    stock_map_table = Table(
        "StockMap", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("layout", String, nullable=False),
        Column("updated_at", DateTime(timezone=True), nullable=False),
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
        Column("name", String(255), nullable=False),
        Column("is_primary", Boolean, nullable=False, server_default="0"),
        Column("is_archived", Boolean, nullable=False, server_default="0"),
        Column("is_in_progress", Boolean, nullable=False, server_default="0"),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("completed_at", DateTime(timezone=True), nullable=True),
    )

    shopping_list_line_table = Table(
        "ShoppingListLine", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("shopping_list_id", UUIDType, ForeignKey("ShoppingList.id", ondelete="CASCADE"), nullable=False),
        Column("stock_item_id", UUIDType, ForeignKey("StockItem.id", ondelete="CASCADE"), nullable=False),
        Column("quantity", Integer, nullable=True),
        Column("is_ticked", Boolean, nullable=False, server_default="0"),
        Column("selected_product_id", UUIDType, ForeignKey("Product.id", ondelete="SET NULL"), nullable=True),
        Column("sequence", Integer, nullable=False, server_default="0"),
        Column("added_via", String(32), nullable=False, server_default="manual"),
        Column("added_at", DateTime(timezone=True), nullable=True),
        Column("picked_offer_price", Float, nullable=True),
        Column("list_price_at_pick", Float, nullable=True),
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

    recipe_collection_table = Table(
        "RecipeCollection", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255), nullable=False),
    )

    recipe_table = Table(
        "Recipe", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("category", String(255), nullable=True),
        Column("cook_time_minutes", Integer, nullable=True),
        Column("cuisine", String(255), nullable=True),
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
        Column("time_of_day", String(50), nullable=True),
    )

    recipe_ingredient_table = Table(
        "RecipeIngredient", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("notes", String(255), nullable=True),
        Column("quantity", Float, nullable=True),
        Column("recipe_id", UUIDType, ForeignKey("Recipe.id", ondelete="CASCADE"), nullable=False),
        Column("stock_item_id", UUIDType, ForeignKey("StockItem.id", ondelete="RESTRICT"), nullable=False),
        Column("unit", String(50), nullable=True),
    )

    meal_table = Table(
        "Meal", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("quantity_in_stock", Integer, nullable=False),
    )

    meal_recipe_table = Table(
        "MealRecipe", metadata,
        Column("meal_id", UUIDType, ForeignKey("Meal.id", ondelete="CASCADE"), primary_key=True),
        Column("recipe_id", UUIDType, ForeignKey("Recipe.id", ondelete="CASCADE"), primary_key=True),
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
        Column("meal_id", UUIDType, ForeignKey("Meal.id", ondelete="CASCADE"), nullable=False),
        Column("meal_plan_id", UUIDType, ForeignKey("MealPlan.id", ondelete="CASCADE"), nullable=False),
        Column("scheduled_for", Date, nullable=False),
        Column("servings", Integer, nullable=False),
        Column("slot", String(50), nullable=False),
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

    _mapper_registry.map_imperatively(StockMap, stock_map_table, properties={
        "_id_col": stock_map_table.c.id,
        "id": stock_map_table.c.id,
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
        "stock_item": relationship(StockItem, lazy="noload"),
    })

    _mapper_registry.map_imperatively(Recipe, recipe_table, properties={
        "_id_col": recipe_table.c.id,
        "_recipe_collection_id": recipe_table.c.recipe_collection_id,
        "id": recipe_table.c.id,
        "recipe_collection": relationship(RecipeCollection, lazy="noload"),
        "ingredients": relationship(
            RecipeIngredient,
            lazy="noload",
            cascade="all, delete-orphan",
            foreign_keys=[recipe_ingredient_table.c.recipe_id],
        ),
    })

    _mapper_registry.map_imperatively(Meal, meal_table, properties={
        "_id_col": meal_table.c.id,
        "id": meal_table.c.id,
        "recipes": relationship(Recipe, secondary=meal_recipe_table, lazy="noload"),
    })

    _mapper_registry.map_imperatively(MealPlanEntry, meal_plan_entry_table, properties={
        "_id_col": meal_plan_entry_table.c.id,
        "_meal_id": meal_plan_entry_table.c.meal_id,
        # See RecipeIngredient above — FK columns hidden from verify_mappings.
        "_meal_plan_id": meal_plan_entry_table.c.meal_plan_id,
        "id": meal_plan_entry_table.c.id,
        "meal": relationship(Meal, lazy="noload"),
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
