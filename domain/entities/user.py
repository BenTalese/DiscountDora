from dataclasses import dataclass
from datetime import datetime

from domain.entities.base_entity import BaseEntity


@dataclass
class User(BaseEntity):
    email: str = None
    send_deals_on_day: datetime = None
    username: str = None
    # TODO: auth
