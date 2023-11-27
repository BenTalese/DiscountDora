from dataclasses import asdict, dataclass
from domain.entities.base_entity import EntityID

from domain.entities.stock_location import StockLocation


@dataclass
class StockLocationDto:
    description: str
    stock_location_id: EntityID

# TODO: Map explicitly
# def get_stock_location_dto(stock_location: StockLocation) -> StockLocationDto:
#     return StockLocationDto(**asdict(stock_location))
