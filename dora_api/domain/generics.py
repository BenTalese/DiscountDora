from typing import TypeVar

from dora_api.domain.entities.base_entity import BaseEntity

TEntity = TypeVar("TEntity", bound=BaseEntity)
TService = TypeVar("TService")
TTrackedType = TypeVar("TTrackedType")
