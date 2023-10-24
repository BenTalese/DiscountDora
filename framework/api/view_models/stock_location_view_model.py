from dataclasses import dataclass

from application.dtos.stock_location_dto import StockLocationDto


@dataclass
class StockLocationViewModel:
    description: str

def get_stock_location_view_model(stock_location: StockLocationDto) -> StockLocationViewModel:
    return StockLocationViewModel(
        description = stock_location.description
    )
