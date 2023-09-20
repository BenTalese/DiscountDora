import datetime
import uuid


class StockItemDto:
    name: str
    stock_item_id: uuid
    stock_level_id: uuid
    stock_location_id: uuid
    stock_level_last_updated_on_utc: datetime
