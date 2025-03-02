from dataclasses import dataclass
from uuid import UUID

from domain.entities.user import User


@dataclass
class UserViewModel:
    email: str
    send_deals_on_day: int
    username: str
    user_id: UUID


def get_user_view_model(user: User) -> UserViewModel:
    return UserViewModel(
        email = user.email,
        send_deals_on_day = user.send_deals_on_day,
        username = user.username,
        user_id = user.id.value
    )
