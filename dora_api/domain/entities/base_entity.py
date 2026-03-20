from abc import ABC
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EntityID:
    value: UUID = field(default_factory=uuid4)

    def __composite_values__(self):
        return (self.value,)

    def __new__(cls, value: UUID | None = None):
        obj = object.__new__(cls)
        object.__setattr__(obj, "value", value if value is not None else uuid4())
        return obj


@dataclass(eq=False, kw_only=True)
class BaseEntity(ABC):
    id: EntityID = field(default_factory=EntityID)

    # def __eq__(self, other):
    #     if self is other:
    #         return True
    #     if not isinstance(other, type(self)):
    #         return False
    #     return self.id == other.id

    # def __hash__(self):
    #     return hash((type(self), self.id))
