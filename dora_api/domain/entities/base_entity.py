from abc import ABC
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(eq=False, kw_only=True)
class BaseEntity(ABC):
    id: UUID = field(default=UUID(int=0))

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash((type(self), self.id))
