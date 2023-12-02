from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from application.dtos.user_dto import UserDto


@dataclass
class UserViewModel:
    email: str
    send_deals_on_day: datetime
    username: str
    user_id: UUID

def get_user_view_model(user: UserDto) -> UserViewModel:
    return UserViewModel(
        email = user.email,
        send_deals_on_day = user.send_deals_on_day,
        username = user.username,
        user_id = user.user_id.value
    )
