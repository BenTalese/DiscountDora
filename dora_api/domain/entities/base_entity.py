from abc import ABC
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class EntityID:
    value: UUID


@dataclass(eq=False, kw_only=True)
class BaseEntity(ABC):
    id: EntityID = EntityID(UUID(int=0))

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash((type(self), self.id))
