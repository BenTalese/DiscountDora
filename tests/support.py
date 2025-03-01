from datetime import datetime
from uuid import UUID


def is_valid_datetime(value, format='%Y-%m-%dT%H:%M:%S'):
    try:
        datetime.strptime(value, format)
        return True
    except ValueError:
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
