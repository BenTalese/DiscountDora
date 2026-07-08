"""Structural ports for injectable collaborators.

Each Protocol here describes the *shape* of a collaborator (what
methods it exposes), not a nominal hierarchy — any object that
matches the shape satisfies the type at runtime and at type-check
time. This is Python's idiomatic interface: no ABC inheritance, no
container registration, no `I`-prefix nominal types.

Handlers declare what they need in their `__init__` signature
using these Protocols. Wiring happens explicitly at the router /
app-factory edge (a plain constructor call), not via a container.
See ADR entry for R-0NN in `docs/01_charter/ENGINEERING_STANDARDS.md`.
"""

from typing import Any, Protocol, TypeVar

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.generics import TEntity

TQueryBuilder = TypeVar("TQueryBuilder")


class Repository(Protocol):
    """The persistence surface handlers depend on.

    Modelled on `SqlAlchemyRepository`'s public methods. Any concrete
    that implements these — the real SqlAlchemy-backed one, or a
    fake for tests — satisfies this Protocol.
    """

    @property
    def session(self) -> Any: ...

    def add(self, entity: BaseEntity) -> None: ...

    def get(self, entity_type: type[TEntity]) -> Any: ...

    def reattach_and_save(self, entity: BaseEntity) -> None: ...

    def remove(self, entity: BaseEntity) -> None: ...

    def flush(self) -> None: ...

    def save_changes(self) -> None: ...
