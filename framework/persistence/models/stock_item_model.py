import uuid

from sqlalchemy import func
from persistence.infrastructure.persistence_context import db


class StockItemModel(db.Model):
    __tablename__ = 'StockItem'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=str(uuid.uuid4()),
        unique=True)

    location_id = db.Column(
        db.String(36),
        db.ForeignKey('location.id'))

    name = db.Column(
        db.String(255))

    stock_level_id = db.Column(
        db.String(36),
        db.ForeignKey('stock_level.id'))

    stock_level_last_updated_on_utc = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now())
