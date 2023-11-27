from dataclasses import dataclass
from datetime import datetime

from domain.entities.base_entity import EntityID
from domain.entities.user import User


@dataclass
class UserDto:
    email: str = None
    send_deals_on_day: datetime = None
    username: str = None
    user_id: EntityID

def get_user_dto(user: User) -> UserDto:
    return UserDto(
        email = user.email,
        send_deals_on_day = user.send_deals_on_day,
        username = user.username,
        user_id = user.id
    )
