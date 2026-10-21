from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class Store(BaseEntity):
    """A user-curated retail store (FU-189). Replaces the former `Merchant`
    entity post-Phase-E. Users curate the list themselves — Dora ships zero
    prefilled stores and never auto-creates one (no-auto-create rule, see
    FU-190). Stores optionally carry a user-uploaded logo (`image`); the SPA
    falls back to a hash-swatch + initial when none is set.

    `brand_colour` is the logo's majority colour as `#rrggbb`, derived once at
    upload time by `features/stores/_logo_colour.py`. It is what the shopping
    list's store breakdown paints with, so a Woolworths bucket reads green and
    a Coles one red. NULL whenever there's no logo, the logo can't be read, or
    the logo is greyscale — all of which fall back to the hash swatch."""
    name: str
    image: bytes | None = None
    brand_colour: str | None = None

    class Fields(BaseEntity.Fields):
        NAME = "name"
        IMAGE = "image"
        BRAND_COLOUR = "brand_colour"
