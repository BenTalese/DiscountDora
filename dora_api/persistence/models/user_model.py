from uuid import UUID, uuid4

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import UUIDType

from dora_api.app import db
from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.user import User


class UserModel(db.Model):
    __entity__ = User
    __tablename__ = User.__name__

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid4
    )

    email: Mapped[str | None] = mapped_column(String(255))

    send_deals_on_day: Mapped[int] = mapped_column(Integer)

    username: Mapped[str] = mapped_column(String(255))

    def to_entity(self) -> User:
        _Entity = User(
            email = self.email,
            send_deals_on_day = self.send_deals_on_day,
            username = self.username
        )
        _Entity.id = EntityID(self.id)
        return _Entity

    @classmethod
    def from_entity(cls, user: User) -> 'UserModel':
        _Model = cls()
        _Model.id = user.id.value
        _Model.email = user.email
        _Model.send_deals_on_day = user.send_deals_on_day
        _Model.username = user.username
        return _Model
