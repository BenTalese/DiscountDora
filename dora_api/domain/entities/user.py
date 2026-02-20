from dataclasses import dataclass

from domain.entities.base_entity import BaseEntity


@dataclass(slots=True)
class User(BaseEntity):
    email: str | None
    send_deals_on_day: int
    username: str
    # TODO: auth | avoid god object | separate auth from user
