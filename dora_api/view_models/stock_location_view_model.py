from dataclasses import dataclass
from uuid import UUID

from domain.entities.stock_location import StockLocation


@dataclass
class StockLocationViewModel:
    name: str
    stock_location_id: UUID


def get_stock_location_view_model(stock_location: StockLocation) -> StockLocationViewModel:
    return StockLocationViewModel(
        name = stock_location.name,
        stock_location_id = stock_location.id.value
    )
