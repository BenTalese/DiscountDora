from dataclasses import dataclass
from datetime import datetime
from typing import List

from application.dtos.product_dto import ProductDto, get_product_dto
from domain.entities.base_entity import EntityID
from domain.entities.stock_item import StockItem


@dataclass
class StockItemDto:
    name: str
    products: List[ProductDto]
    stock_group_id: EntityID
    stock_item_id: EntityID
    stock_level_id: EntityID
    stock_location_id: EntityID
    stock_level_last_updated: datetime

def get_stock_item_dto(stock_item: StockItem) -> StockItemDto:
    return StockItemDto(
        name = stock_item.name,
        products = [get_product_dto(p) for p in stock_item.products],
        stock_group_id = stock_item.stock_group.id if stock_item.stock_group else None,
        stock_item_id = stock_item.id,
        stock_level_id = stock_item.stock_level.id if stock_item.stock_level else None,
        stock_location_id = stock_item.stock_location.id if stock_item.stock_location else None,
        stock_level_last_updated = stock_item.stock_level_last_updated
    )
