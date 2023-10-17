from dataclasses import dataclass


class AttributeChangeTracker:
    def __init__(self, cls):
        self._cls = cls

        # Override the setattr method for the class
        def custom_setattr(instance, attr, value):
            # Track the attribute change
            print(f"Attribute '{attr}' changed to {value}")
            instance.__dict__[attr] = value

        self._cls.__setattr__ = custom_setattr

# Define a class without any knowledge of the tracker
@dataclass
class MyClass:
    a: int = None
    b: int = None

# Create an instance of the class
obj = MyClass(1, 2)
obj2 = MyClass(3, 4)

# Attach the attribute change tracker to the class at runtime
tracker = AttributeChangeTracker(MyClass)


# Change attributes, and the tracker will work without the class knowing
obj.a = 42
obj.b = 99

obj2.a = 5
