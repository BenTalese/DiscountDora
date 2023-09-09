import uuid


class StockLocation:
    def __init__(
            self,
            id: uuid,
            description: str):
        self.id = id
        self.description = description