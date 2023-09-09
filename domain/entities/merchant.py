import uuid


class Merchant:
    def __init__(
            self,
            id: uuid,
            name: str,
            url: str):
        self.id = id
        self.name = name
        self.url = url