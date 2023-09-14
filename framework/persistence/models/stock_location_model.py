import uuid

from persistence.infrastructure.persistence_context import db
from sqlalchemy_utils import UUIDType

from domain.entities.stock_location import StockLocation


class StockLocationModel(db.Model):
    __tablename__ = StockLocation.__name__

    id = db.Column(
        UUIDType(binary=False, native=False),
        primary_key=True,
        default=uuid.uuid4)

    description = db.Column(
        db.String(255))
