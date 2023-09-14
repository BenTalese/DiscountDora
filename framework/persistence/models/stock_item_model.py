import uuid

from persistence.infrastructure.persistence_context import db
from sqlalchemy import func
from sqlalchemy_utils import UUIDType


class StockItemModel(db.Model):
    __tablename__ = 'StockItem'

    id = db.Column(
        UUIDType(binary=False, native=False),
        primary_key=True,
        default=uuid.uuid4)

    # location_id = db.Column(
    #     db.String(36),
    #     db.ForeignKey('location.id'))

    name = db.Column(
        db.String(255))

    # stock_level_id = db.Column(
    #     db.String(36),
    #     db.ForeignKey('stock_level.id'))

    stock_level_last_updated_on_utc = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now())
