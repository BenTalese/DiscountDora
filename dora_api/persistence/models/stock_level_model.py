from uuid import UUID, uuid4

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import UUIDType

from dora_api.app import db
from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.stock_level import StockLevel


class StockLevelModel(db.Model):
    __entity__ = StockLevel
    __tablename__ = StockLevel.__name__

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid4
    )

    name: Mapped[str] = mapped_column(String(255))

    sequence: Mapped[int] = mapped_column(Integer)

    def to_entity(self) -> StockLevel:
        _Entity = StockLevel(
            name = self.name,
            sequence = self.sequence
        )
        _Entity.id = EntityID(self.id)
        return _Entity

    @classmethod
    def from_entity(cls, stock_level: StockLevel) -> 'StockLevelModel':
        _Model = cls()
        _Model.id = stock_level.id.value
        _Model.name = stock_level.name
        _Model.sequence = stock_level.sequence
        return _Model
