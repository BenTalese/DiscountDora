
from typing import Generic, Optional, Type

from dora_api.domain.generics import TAttributeValue


class AttributeChangeTracker(Generic[TAttributeValue]):
    __origin__ = Type['AttributeChangeTracker']

    def __init__(self, value: Optional[TAttributeValue] = None, has_been_set: Optional[bool] = False):
        self._value = value
        self._has_been_set = has_been_set or (value is not None)

    def __setattr__(self, name, value):
        if name == '_value':
            super().__setattr__(name, value)
            self._has_been_set = True
        else:
            super().__setattr__(name, value)

    @property
    def value(self) -> TAttributeValue | None:
        return self._value

    @property
    def has_been_set(self) -> bool:
        return self._has_been_set

    def __repr__(self) -> str:
        return repr(self._value)

    def __getattr__(self, item):
        return getattr(self._value, item)
