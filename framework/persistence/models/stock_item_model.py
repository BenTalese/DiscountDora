import uuid
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation

from framework.startup import db
from sqlalchemy import func
from sqlalchemy_utils import UUIDType

from domain.entities.stock_item import StockItem


class StockItemModel(db.Model):
    __tablename__ = StockItem.__name__

    id = db.Column(
        UUIDType(binary=False, native=False),
        primary_key=True,
        default=uuid.uuid4)

    location_id = db.Column(
        db.String(36),
        db.ForeignKey(StockLocation.__name__ + ".id"))

    name = db.Column(
        db.String(255))

    stock_level_id = db.Column(
        db.String(36),
        db.ForeignKey(StockLevel.__name__ + ".id"))

    stock_level_last_updated_on_utc = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now())
