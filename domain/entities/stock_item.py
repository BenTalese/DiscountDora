from dataclasses import dataclass
from datetime import datetime

from domain.entities.base_entity import BaseEntity
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


@dataclass
class StockItem(BaseEntity):
    name: str = None
    # products: List[Product] = None
    stock_level: StockLevel = None
    stock_level_last_updated: datetime = None
    stock_location: StockLocation = None

    #attribute ideas:
        #is_active
        #description
        #preferred_merchant
        #image
        #stock_group (e.g. )

        #only one can have value:
            #best_before
            #expires_on
