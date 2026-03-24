class PersistenceError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class DependencyConstructionError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class DuplicateServiceError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
