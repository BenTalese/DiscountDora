from dataclasses import dataclass

from domain.entities.base_entity import EntityID
from domain.entities.stock_group import StockGroup


@dataclass
class StockGroupDto:
    name: str
    stock_group_id: EntityID

def get_stock_group_dto(stock_group: StockGroup) -> StockGroupDto:
    return StockGroupDto(
        name = stock_group.name,
        stock_group_id = stock_group.id
    )
