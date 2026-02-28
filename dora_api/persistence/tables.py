from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, LargeBinary, MetaData, String, Table
from sqlalchemy_utils import UUIDType

metadata = MetaData()

MerchantTable = Table(
    "Merchant", metadata,
    Column("id", UUIDType, primary_key=True),
    Column("name", String(255)),
)

ProductOfferTable = Table(
    "ProductOffer", metadata,
    Column("id", UUIDType, primary_key=True),
    Column("offered_on", DateTime(timezone=True)),
    Column("price_now", Float),
    Column("price_was", Float),
    Column("product_id", UUIDType, ForeignKey("Product.id"), nullable=False),
)

ProductHistoricOfferTable = Table(
    "ProductHistoricOffer", metadata,
    Column("id", UUIDType, primary_key=True),
    Column("offered_on", DateTime(timezone=True)),
    Column("price_now", Float),
    Column("price_was", Float),
    Column("product_id", UUIDType, ForeignKey("Product.id"), nullable=False),
)

ProductTable = Table(
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

StockGroupTable = Table(
    "StockGroup", metadata,
    Column("id", UUIDType, primary_key=True),
    Column("name", String(255)),
)

StockLevelTable = Table(
    "StockLevel", metadata,
    Column("id", UUIDType, primary_key=True),
    Column("name", String(255)),
    Column("sequence", Integer),
)

StockLocationTable = Table(
    "StockLocation", metadata,
    Column("id", UUIDType, primary_key=True),
    Column("name", String(255)),
)

StockItemTable = Table(
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

ShoppingListTable = Table(
    "ShoppingList", metadata,
    Column("id", UUIDType, primary_key=True),
)

ShoppingListStockItemTable = Table(
    "ShoppingListStockItem", metadata,
    Column("shopping_list_id", UUIDType, ForeignKey("ShoppingList.id"), primary_key=True),
    Column("stock_item_id", UUIDType, ForeignKey("StockItem.id"), primary_key=True),
)

UserTable = Table(
    "User", metadata,
    Column("id", UUIDType, primary_key=True),
    Column("email", String(255), nullable=True),
    Column("send_deals_on_day", Integer),
    Column("username", String(255)),
)
