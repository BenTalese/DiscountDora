# dora_api/persistence/mappings.py
from dataclasses import fields

from sqlalchemy.orm import composite, registry, relationship

from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_historic_offer import \
    ProductHistoricOffer
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.shopping_list import ShoppingList
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.entities.user import User
from dora_api.domain.exceptions import PersistenceError
from dora_api.persistence.tables import (MerchantTable,
                                         ProductHistoricOfferTable,
                                         ProductOfferTable, ProductTable,
                                         ShoppingListStockItemTable,
                                         ShoppingListTable, StockGroupTable,
                                         StockItemTable, StockLevelTable,
                                         StockLocationTable, UserTable)

_mapper_registry = registry()
_mappings_configured = False


def verify_mappings(mapper_registry: registry):
    INTERNAL = {"_id_col"}   # private persistence-only mapped names
    for mapper in mapper_registry.mappers:
        entity_class = mapper.class_
        mapped_attributes = mapped_attributes = {
            prop.key for prop in mapper.iterate_properties
            if not prop.key.startswith("_")   # ignore all private persistence internals
        } - INTERNAL
        entity_fields = {f.name for f in fields(entity_class)}

        unmapped = entity_fields - mapped_attributes
        if unmapped:
            raise PersistenceError(
                f"{entity_class.__name__} has fields not mapped to persistence: {unmapped}"
            )

        extra = mapped_attributes - entity_fields - {"id"}  # id handled by composite
        if extra:
            raise PersistenceError(
                f"{entity_class.__name__} has mapped attributes not present on entity: {extra}"
            )


def configure_mappings():
    global _mappings_configured
    if _mappings_configured:
        return

    # Leaf entities first (no relationships to other domain entities)
    _mapper_registry.map_imperatively(Merchant, MerchantTable, properties={
        "_id_col": MerchantTable.c.id,
        "id": composite(EntityID, MerchantTable.c.id),
    })

    _mapper_registry.map_imperatively(StockGroup, StockGroupTable, properties={
        "_id_col": StockGroupTable.c.id,
        "id": composite(EntityID, StockGroupTable.c.id),
    })

    _mapper_registry.map_imperatively(StockLevel, StockLevelTable, properties={
        "_id_col": StockLevelTable.c.id,
        "id": composite(EntityID, StockLevelTable.c.id),
    })

    _mapper_registry.map_imperatively(StockLocation, StockLocationTable, properties={
        "_id_col": StockLocationTable.c.id,
        "id": composite(EntityID, StockLocationTable.c.id),
    })

    _mapper_registry.map_imperatively(User, UserTable, properties={
        "_id_col": UserTable.c.id,
        "id": composite(EntityID, UserTable.c.id),
    })

    _mapper_registry.map_imperatively(ProductOffer, ProductOfferTable, properties={
        "_id_col": ProductOfferTable.c.id,
        "_product_id": ProductOfferTable.c.product_id,
        "id": composite(EntityID, ProductOfferTable.c.id),
    })

    _mapper_registry.map_imperatively(ProductHistoricOffer, ProductHistoricOfferTable, properties={
        "_id_col": ProductHistoricOfferTable.c.id,
        "_product_id": ProductHistoricOfferTable.c.product_id,
        "id": composite(EntityID, ProductHistoricOfferTable.c.id),
    })

    # Entities with relationships
    _mapper_registry.map_imperatively(Product, ProductTable, properties={
        "_id_col": ProductTable.c.id,
        "id": composite(EntityID, ProductTable.c.id),
        "_merchant_id": ProductTable.c.merchant_id,
        "merchant": relationship(Merchant, lazy="noload"),
        "current_offer": relationship(ProductOffer, lazy="noload", uselist=False),
        "historic_offers": relationship(ProductHistoricOffer, lazy="noload"),
    })

    _mapper_registry.map_imperatively(StockItem, StockItemTable, properties={
        "_id_col": StockItemTable.c.id,
        "_stock_group_id": StockItemTable.c.stock_group_id,
        "_stock_level_id": StockItemTable.c.stock_level_id,
        "_stock_location_id": StockItemTable.c.stock_location_id,
        "id": composite(EntityID, StockItemTable.c.id),
        "stock_group": relationship(StockGroup, lazy="noload"),
        "stock_level": relationship(StockLevel, lazy="noload"),
        "stock_location": relationship(StockLocation, lazy="noload"),
        # "shopping_lists": relationship(
        #     ShoppingList,
        #     secondary=ShoppingListStockItemTable,
        #     back_populates="items",
        #     lazy="noload",
        # ),
    })

    _mapper_registry.map_imperatively(ShoppingList, ShoppingListTable, properties={
        "_id_col": ShoppingListTable.c.id,
        "id": composite(EntityID, ShoppingListTable.c.id),
        "items": relationship(
            StockItem,
            secondary=ShoppingListStockItemTable,
            # back_populates="shopping_lists",
            lazy="noload",
        ),
    })

    verify_mappings(_mapper_registry)
    _mappings_configured = True
