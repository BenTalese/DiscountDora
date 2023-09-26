from dataclasses import dataclass
import datetime
import uuid

from application.dtos.stock_item_dto import StockItemDto

@dataclass
class StockItemViewModel:
    viewmodel_name: str
    viewmodel_stock_item_id: uuid
    # stock_level_id: uuid
    # stock_location_id: uuid
    # stock_level_last_updated_on_utc: datetime

@dataclass
class StockItemNextThing:
    nextthing_name: str
    next_thing_other_name: str

def get_stock_item_next_thing(stock_item: StockItemViewModel) -> StockItemNextThing:
    return StockItemNextThing(
        nextthing_name = stock_item.viewmodel_name,
        next_thing_other_name = stock_item.viewmodel_name.capitalize().isdigit()
    )

def get_stock_item_view_model(stock_item: StockItemDto) -> StockItemViewModel:
    return StockItemViewModel(
        viewmodel_name = stock_item.dto_name,
        viewmodel_stock_item_id = stock_item.dto_stock_item_id,
        # stock_level_id = stock_item.stock_level_id,
        # stock_location_id = stock_item.stock_location_id,
        # stock_level_last_updated_on_utc = stock_item.stock_level_last_updated_on_utc
    )
