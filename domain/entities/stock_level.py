import uuid


class StockLevel:
    def __init__(
            self,
            id: uuid,
            description: str):
        self.id = id
        self.description = description