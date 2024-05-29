from dataclasses import dataclass
from uuid import UUID

from application.dtos.stock_level_dto import StockLevelDto


@dataclass
class StockLevelViewModel:
    name: str
    sequence: int
    stock_level_id: UUID

def get_stock_level_view_model(stock_level: StockLevelDto) -> StockLevelViewModel:
    return StockLevelViewModel(
        name = stock_level.name,
        sequence = stock_level.sequence,
        stock_level_id = stock_level.stock_level_id.value,
    )
