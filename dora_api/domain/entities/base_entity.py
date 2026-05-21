from abc import ABC
from dataclasses import dataclass, field
from uuid import UUID

from dora_api.domain.types import EMPTY_UUID


@dataclass(eq=False, kw_only=True)
class BaseEntity(ABC):
    id: UUID = field(default=EMPTY_UUID)

    def __eq__(self, other):
        if self is other:
            return True
        if type(self) is not type(other):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash((type(self), self.id))

    class Fields:
        """String constants for attribute names — replaces runtime-introspecting
        helpers like `varname.nameof(Entity.attr)`. Each entity overrides this
        with its own constants; this base only provides the inherited `ID`.
        """
        ID = "id"
