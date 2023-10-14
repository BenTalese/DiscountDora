from typing import TypeVar

from domain.entities.base_entity import BaseEntity

TEntity = TypeVar("TEntity", bound=BaseEntity)
