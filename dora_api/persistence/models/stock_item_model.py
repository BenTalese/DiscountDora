from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (Boolean, DateTime, ForeignKey, Integer, LargeBinary,
                        String)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import UUIDType

from dora_api.app import db
from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.persistence.models.stock_group_model import StockGroupModel
from dora_api.persistence.models.stock_level_model import StockLevelModel
from dora_api.persistence.models.stock_location_model import StockLocationModel


# TODO: for all models figure out "required", "min value", "relationship existence constraint" etc...
class StockItemModel(db.Model):
    __entity__ = StockItem
    __tablename__ = StockItem.__name__

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid4
    )

    days_until_stocktake_alert: Mapped[int] = mapped_column(Integer)

    image: Mapped[bytes | None] = mapped_column(LargeBinary)

    name: Mapped[str] = mapped_column(String(255))

    notes: Mapped[str | None] = mapped_column(String(255))

    shopping_lists = relationship(
        'ShoppingListModel',  # string to avoid circular import
        secondary = 'ShoppingListStockItem',
        back_populates = 'items',
        lazy = "noload"
    )

    stock_group: Mapped[StockGroupModel | None] = relationship(
        lazy="noload"
    )

    stock_group_id: Mapped[UUID | None] = mapped_column(
        UUIDType,
        ForeignKey(StockGroup.__name__ + ".id"),
        nullable = True
    )

    stock_level: Mapped[StockLevelModel] = relationship(
        lazy="noload"
    )

    stock_level_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey(StockLevel.__name__ + ".id"),
        nullable = True
    )

    stock_level_last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

    stock_location: Mapped[StockLocationModel | None] = relationship(
        lazy="noload"
    )

    stock_location_id: Mapped[UUID | None] = mapped_column(
        UUIDType,
        ForeignKey(StockLocation.__name__ + ".id"),
        nullable = True
    )

    stocktake_alerts_are_enabled: Mapped[bool] = mapped_column(Boolean)

    def to_entity(self) -> StockItem:
        _Entity = StockItem(
            days_until_stocktake_alert = self.days_until_stocktake_alert,
            image = self.image,
            name = self.name,
            notes = self.notes,
            stock_group = self.stock_group.to_entity() if self.stock_group else None,
            stock_level = self.stock_level.to_entity() if self.stock_level else None,  # type: ignore
            stock_level_last_updated = self.stock_level_last_updated,
            stock_location = self.stock_location.to_entity() if self.stock_location else None,
            stocktake_alerts_are_enabled = self.stocktake_alerts_are_enabled
        )
        _Entity.id = EntityID(self.id)
        return _Entity

    @classmethod
    def from_entity(cls, stock_item: StockItem) -> 'StockItemModel':
        _Model = cls()
        _Model.id = stock_item.id.value
        _Model.days_until_stocktake_alert = stock_item.days_until_stocktake_alert
        _Model.image = stock_item.image
        _Model.name = stock_item.name
        _Model.notes = stock_item.notes
        _Model.stock_group = StockGroupModel.from_entity(stock_item.stock_group) if stock_item.stock_group else None
        _Model.stock_level = StockLevelModel.from_entity(stock_item.stock_level) if stock_item.stock_level else None  # type: ignore
        _Model.stock_level_last_updated = stock_item.stock_level_last_updated
        _Model.stock_location = StockLocationModel.from_entity(stock_item.stock_location) if stock_item.stock_location else None
        _Model.stocktake_alerts_are_enabled = stock_item.stocktake_alerts_are_enabled
        return _Model
