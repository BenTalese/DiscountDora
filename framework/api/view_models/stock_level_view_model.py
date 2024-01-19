from dataclasses import dataclass
from uuid import UUID

from application.dtos.stock_level_dto import StockLevelDto


@dataclass
class StockLevelViewModel:
    description: str
    stock_level_id: UUID

def get_stock_level_view_model(stock_level: StockLevelDto) -> StockLevelViewModel:
    return StockLevelViewModel(
        description = stock_level.description,
        stock_level_id = stock_level.stock_level_id.value,
    )
