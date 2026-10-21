from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class ShoppingListAttachment(BaseEntity):
    """FU-334 — receipt-photo record-keeping. One ordered photo attached to
    a `shopping` or `done` shopping list. Storage shape mirrors
    `RecipeStepImage`: the row holds the encoded
    `data:image/...;base64,...` UTF-8 bytes and the bytes endpoint at
    `GET /shopping-lists/<list_id>/attachments/<attachment_id>` decodes +
    serves raw.

    Pure record-keeping — no OCR, no parsing, no auto-matching to lines.
    """
    shopping_list_id: UUID
    sequence: int
    image: bytes
    created_at: datetime

    class Fields(BaseEntity.Fields):
        SHOPPING_LIST_ID = "shopping_list_id"
        SEQUENCE = "sequence"
        IMAGE = "image"
        CREATED_AT = "created_at"
