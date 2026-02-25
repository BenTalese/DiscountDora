from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import UUIDType

from dora_api.app import db
from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.stock_location import StockLocation


class StockLocationModel(db.Model):
    __entity__ = StockLocation
    __tablename__ = StockLocation.__name__

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid4
    )

    name: Mapped[str] = mapped_column(String(255))

    def to_entity(self) -> StockLocation:
        _Entity = StockLocation(
            name = self.name
        )
        _Entity.id = EntityID(self.id)
        return _Entity

    @classmethod
    def from_entity(cls, stock_location: StockLocation) -> 'StockLocationModel':
        _Model = cls()
        _Model.id = stock_location.id.value
        _Model.name = stock_location.name
        return _Model
