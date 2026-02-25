from typing import Any, Dict, List, get_args, get_origin, get_type_hints

from dora_api.domain.types import AttributeChangeTracker


class ValidationResult:
    errors: Dict[str, List[str]] = {}
    summary: str

    def add_error(self, property_name: str, error_message: str):
        self.errors.setdefault(property_name, []).append(error_message)

    def has_errors(self) -> bool:
        return bool(self.errors)

    def __repr__(self) -> str:
        return f"ValidationResult(errors={self.errors}, summary={self.summary})"


def validate_inputs(request: Any) -> ValidationResult | None:
    """
    Unified validator that checks for:
    1. Required attributes (all annotated fields must exist)
    2. Type matching (matching Python type hints)

    Returns:
        ValidationResult if errors are found, else None
    """
    type_hints = get_type_hints(type(request))
    result = ValidationResult()

    for attr_name, type_hint in type_hints.items():
        # -------------------- Check presence --------------------
        if not hasattr(request, attr_name):
            result.add_error(attr_name, f"'{attr_name}' must have a value.")
            continue

        # -------------------- Check type --------------------
        value = getattr(request, attr_name)

        # Unwrap AttributeChangeTracker safely
        if isinstance(value, AttributeChangeTracker):
            value = value.value

        if value is None:
            continue  # presence already checked, allow None if annotated type allows?

        error_message = _validate_type(attr_name, value, type_hint)
        if error_message:
            result.add_error(attr_name, error_message)

    if result.has_errors():
        result.summary = "Input validation failed: missing or incorrectly typed values."
        return result

    return None


def _validate_type(name: str, value: Any, type_hint: Any) -> str | None:
    """Validate a single attribute against its type hint."""
    origin = get_origin(type_hint)
    args = get_args(type_hint)

    # Simple non-generic type
    if origin is None:
        if not isinstance(value, type_hint):
            return f"'{name}' must be of type '{type_hint.__name__}'."
        return None

    # Generic types (list, tuple, set, etc)
    if not isinstance(value, origin):
        return f"'{name}' must be of type '{origin.__name__}'."

    if origin in (list, tuple, set) and args:
        for item in value:
            if item is None:
                continue
            if not any(isinstance(item, arg) for arg in args):
                arg_names = ", ".join(a.__name__ for a in args)
                return f"Items in '{name}' must be of type(s): {arg_names}."
    return None
