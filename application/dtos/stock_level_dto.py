from dataclasses import dataclass

from domain.entities.base_entity import EntityID
from domain.entities.stock_level import StockLevel


@dataclass
class StockLevelDto:
    name: str
    sequence: int
    stock_level_id: EntityID


def get_stock_level_dto(stock_level: StockLevel) -> StockLevelDto:
    return StockLevelDto(
        name = stock_level.name,
        sequence = stock_level.sequence,
        stock_level_id = stock_level.id
    )
