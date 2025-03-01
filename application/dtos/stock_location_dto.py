from dataclasses import dataclass

from domain.entities.base_entity import EntityID
from domain.entities.stock_location import StockLocation


@dataclass
class StockLocationDto:
    name: str
    stock_location_id: EntityID


def get_stock_location_dto(stock_location: StockLocation) -> StockLocationDto:
    return StockLocationDto(
        name = stock_location.name,
        stock_location_id = stock_location.id
    )
