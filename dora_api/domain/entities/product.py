from dataclasses import dataclass
from typing import List

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.store import Store
from dora_api.domain.entities.product_historic_offer import \
    ProductHistoricOffer
from dora_api.domain.entities.product_offer import ProductOffer


@dataclass
class Product(BaseEntity):
    brand: str | None
    current_offer: ProductOffer
    historic_offers: List[ProductHistoricOffer]
    image: bytes | None
    is_active: bool
    is_available: bool
    store: Store
    # FU-189: `merchant_stockcode` retained — it's the producer's SKU code,
    # not a reference to the renamed entity. Renaming this column was
    # deliberately deferred (PRODUCTS_OVERLAY_RUNBOOK Phase E).
    merchant_stockcode: str | None
    name: str
    size: str
    size_unit: str
    size_value: float
    web_url: str | None
    # Multipack count (FU-227 follow-up). ``size_value`` keeps the existing
    # convention of being the TOTAL measure across the whole bundle (so the
    # per-unit math stays unchanged); ``pack_count`` is informational —
    # captures "this is a 4-pack of 125g" so the obs / row UI can render
    # "$4.20 for 4 × 125g" rather than "500g flat". ``None`` ⇒ single
    # pack / free-weight, the common case.
    pack_count: int | None = None

    class Fields(BaseEntity.Fields):
        BRAND = "brand"
        CURRENT_OFFER = "current_offer"
        HISTORIC_OFFERS = "historic_offers"
        IMAGE = "image"
        IS_ACTIVE = "is_active"
        IS_AVAILABLE = "is_available"
        STORE = "store"
        MERCHANT_STOCKCODE = "merchant_stockcode"
        NAME = "name"
        SIZE = "size"
        SIZE_UNIT = "size_unit"
        SIZE_VALUE = "size_value"
        WEB_URL = "web_url"
        PACK_COUNT = "pack_count"
