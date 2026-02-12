class MappingError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class PersistenceError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
