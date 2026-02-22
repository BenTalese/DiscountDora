from typing import Generic, Optional, Type, cast

from dora_api.domain.generics import TTrackedType


class _UnsetType:
    def __repr__(self):
        return "UNSET"


UNSET = _UnsetType()


class AttributeChangeTracker(Generic[TTrackedType]):
    __origin__ = Type['AttributeChangeTracker']
    __slots__ = ("_value", "_has_been_set")

    def __init__(self, value = UNSET, has_been_set: Optional[bool] = False):
        self._value = value
        self._has_been_set = has_been_set or (value is not UNSET)

    @property
    def has_been_set(self) -> bool:
        return self._has_been_set

    @property
    def value(self) -> TTrackedType:
        if self._value is UNSET:
            raise ValueError("Value was not set")
        return cast(TTrackedType, self._value)

    def value_or(self, default: TTrackedType) -> TTrackedType:
        if self._value is UNSET:
            return default
        return cast(TTrackedType, self._value)

    def __repr__(self):
        if self._value is UNSET:
            return "<UNSET>"
        return repr(self._value)
