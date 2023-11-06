from dataclasses import dataclass

from domain.entities.base_entity import BaseEntity


@dataclass
class User(BaseEntity):
    email: str = None
    name: str = None
