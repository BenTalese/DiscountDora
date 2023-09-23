from dataclasses import dataclass
import uuid


@dataclass
class Merchant:
    id: uuid
    name: str
    url: str
