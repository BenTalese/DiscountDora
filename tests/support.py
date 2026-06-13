from datetime import datetime
from uuid import UUID


def is_valid_datetime(value, format=None):
    # FU-166 / ADR-007: the API now serialises datetimes as ISO 8601
    # (`datetime.isoformat()`), which may carry microseconds and/or an offset.
    # With no explicit format, validate via `fromisoformat` (handles those);
    # an explicit `format` still uses strptime for callers that need it.
    try:
        if format is None:
            datetime.fromisoformat(value)
        else:
            datetime.strptime(value, format)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_uuid(value):
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def is_valid_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
