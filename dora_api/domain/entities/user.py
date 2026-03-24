from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class User(BaseEntity):
    email: str | None
    send_deals_on_day: int
    username: str
    # TODO: auth | avoid god object | separate auth from user
