from typing import Generic, TypeVar

TAttribute = TypeVar('TAttribute')

class AttributeChangeTracker(Generic[TAttribute]):
    def __init__(self, value: TAttribute = None):
        self._value = value
        self._has_been_set = True if value else False

    def __setattr__(self, name, value):
        if name == '_value':
            super().__setattr__(name, value)
            self._has_been_set = True
        else:
            super().__setattr__(name, value)

    @property
    def value(self) -> TAttribute:
        return self._value

    @property
    def has_been_set(self) -> bool:
        return self._has_been_set

    def __repr__(self) -> str:
        return repr(self._value)

    def __class__(self):
        return type(self._value)


if __name__ == "__main__":
    # Example usage:
    tracker = AttributeChangeTracker[int]()

    print("Initial value:", tracker)  # Outputs: 42
    print("Has been set?", tracker.has_been_set)  # Outputs: False

    tracker._value = 99  # This directly accesses the _value attribute, bypassing the tracker logic.

    print("New value (direct access):", tracker)  # Outputs: 99
    print("Has been set?", tracker.has_been_set)  # Outputs: False

    # Using implicit assignment through the wrapper
    tracker = AttributeChangeTracker(10)

    print("New value (implicit assignment):", tracker)  # Outputs: 10
    print("Has been set?", tracker.has_been_set)  # Outputs: False

    print(tracker.__class__())
