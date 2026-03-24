from dataclasses import dataclass
from uuid import UUID


@dataclass
class UserModel:
    email: str
    send_deals_on_day: int
    username: str
    user_id: UUID
