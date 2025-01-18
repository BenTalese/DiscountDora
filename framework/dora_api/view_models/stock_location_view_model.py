from dataclasses import dataclass
from uuid import UUID
from application.dtos.stock_location_dto import StockLocationDto


@dataclass
class StockLocationViewModel:
    name: str
    stock_location_id: UUID

def get_stock_location_view_model(stock_location: StockLocationDto) -> StockLocationViewModel:
    return StockLocationViewModel(
        name = stock_location.name,
        stock_location_id = stock_location.stock_location_id.value
    )
