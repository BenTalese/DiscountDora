from dataclasses import dataclass

from domain.entities.base_entity import BaseEntity


@dataclass
class User(BaseEntity):
    email: str = None
    send_deals_on_day: int = None
    username: str = None
    # TODO: auth
