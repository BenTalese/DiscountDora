from uuid import uuid4
from sqlalchemy import Column, Integer, String
from sqlalchemy_utils import UUIDType

from domain.entities.base_entity import EntityID
from domain.entities.stock_location import StockLocation
from domain.entities.user import User
from framework.persistence.infrastructure.persistence_context import db


class UserModel(db.Model):
    __entity__ = User
    __tablename__ = User.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid4)

    email = Column(String(255))

    send_deals_on_day = Column(Integer)

    username = Column(String(255))

    def to_entity(self) -> User:
        return User(
            id = EntityID(self.id),
            email = self.email,
            send_deals_on_day = self.send_deals_on_day,
            username = self.username)

    def get_key(self):
        return self.id
