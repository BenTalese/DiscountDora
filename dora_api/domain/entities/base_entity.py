from abc import ABC
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class EntityID:
    value: UUID = UUID(int=0)

    def __composite_values__(self):
        return (self.value,)

    # SQLAlchemy calls EntityID(raw_uuid) positionally when reconstructing
    # but our field is keyword-only via dataclass, so we need __new__
    def __new__(cls, value: UUID = UUID(int=0)):
        obj = object.__new__(cls)
        object.__setattr__(obj, "value", value)
        return obj


@dataclass(eq=False, kw_only=True)
class BaseEntity(ABC):
    id: EntityID = EntityID()

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash((type(self), self.id))
