from typing import TypeVar

from domain.entities.base_entity import BaseEntity

TAttributeValue = TypeVar('TAttributeValue')
TEntity = TypeVar("TEntity", bound=BaseEntity)
TService = TypeVar("TService")
