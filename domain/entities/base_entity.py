from abc import ABC
from collections import namedtuple
from dataclasses import dataclass

EntityID = namedtuple("id", "value")

@dataclass
class BaseEntity(ABC):
    id: EntityID = None

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.id.value == other.id.value
        return False
