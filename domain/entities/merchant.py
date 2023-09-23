from dataclasses import dataclass
import uuid


@dataclass
class Merchant:
    id: uuid = None
    name: str = None
    url: str = None
