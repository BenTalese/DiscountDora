from typing import TypeVar

from dora_api.domain.entities.base_entity import BaseEntity

TEntity = TypeVar("TEntity", bound=BaseEntity)
TTrackedType = TypeVar("TTrackedType")
TValue = TypeVar("TValue")
