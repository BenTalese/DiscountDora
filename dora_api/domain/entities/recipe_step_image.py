from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class RecipeStepImage(BaseEntity):
    """C-4 add-on (image-mode steps) — one ordered photo of a recipe's
    procedural steps. Stored as data-URL bytes mirroring Recipe.image /
    User.image: the row holds the encoded `data:image/...;
    base64,...` UTF-8 bytes and the bytes endpoint at
    `GET /recipes/<recipe_id>/step-images/<image_id>` decodes + serves raw.

    Ingredients stay structured; image-mode only replaces the step content.
    """
    recipe_id: UUID
    sequence: int
    image: bytes

    class Fields(BaseEntity.Fields):
        RECIPE_ID = "recipe_id"
        SEQUENCE = "sequence"
        IMAGE = "image"
