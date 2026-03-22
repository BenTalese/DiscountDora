from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Table
from sqlalchemy.orm import registry as SARegistry, relationship
from sqlalchemy_utils import UUIDType

from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_historic_offer import ProductHistoricOffer
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.shopping_list import ShoppingList
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
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

    product_offer_table = Table(
        "ProductOffer", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("offered_on", DateTime(timezone=True)),
        Column("price_now", Float),
        Column("price_was", Float),
        Column("product_id", UUIDType, ForeignKey("Product.id"), nullable=False),
    )

    product_historic_offer_table = Table(
        "ProductHistoricOffer", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("offered_on", DateTime(timezone=True)),
        Column("price_now", Float),
        Column("price_was", Float),
        Column("product_id", UUIDType, ForeignKey("Product.id"), nullable=False),
    )

    product_table = Table(
        "Product", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("brand", String(255), nullable=True),
        Column("image", LargeBinary, nullable=True),
        Column("is_active", Boolean, nullable=False),
        Column("is_available", Boolean, nullable=False),
        Column("merchant_id", UUIDType, ForeignKey("Merchant.id"), nullable=False),
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
        Column("name", String(255)),
    )

    stock_item_table = Table(
        "StockItem", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("days_until_stocktake_alert", Integer),
        Column("image", LargeBinary, nullable=True),
        Column("name", String(255)),
        Column("notes", String(255), nullable=True),
        Column("stock_group_id", UUIDType, ForeignKey("StockGroup.id"), nullable=True),
        Column("stock_level_id", UUIDType, ForeignKey("StockLevel.id"), nullable=True),
        Column("stock_level_last_updated", DateTime(timezone=True)),
        Column("stock_location_id", UUIDType, ForeignKey("StockLocation.id"), nullable=True),
        Column("stocktake_alerts_are_enabled", Boolean),
    )

    shopping_list_table = Table(
        "ShoppingList", metadata,
        Column("id", UUIDType, primary_key=True),
    )

    shopping_list_stock_item_table = Table(
        "ShoppingListStockItem", metadata,
        Column("shopping_list_id", UUIDType, ForeignKey("ShoppingList.id"), primary_key=True),
        Column("stock_item_id", UUIDType, ForeignKey("StockItem.id"), primary_key=True),
    )

    user_table = Table(
        "User", metadata,
        Column("id", UUIDType, primary_key=True),
        Column("email", String(255), nullable=True),
        Column("send_deals_on_day", Integer),
        Column("username", String(255)),
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

    _mapper_registry.map_imperatively(StockLevel, stock_level_table, properties={
        "_id_col": stock_level_table.c.id,
        "id": stock_level_table.c.id,
    })

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
    })

    _mapper_registry.map_imperatively(ShoppingList, shopping_list_table, properties={
        "_id_col": shopping_list_table.c.id,
        "id": shopping_list_table.c.id,
        "items": relationship(StockItem, secondary=shopping_list_stock_item_table, lazy="noload"),
    })

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
