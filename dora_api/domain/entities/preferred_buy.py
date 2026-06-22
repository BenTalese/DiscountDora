from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class PreferredBuy(BaseEntity):
    """A free-text "what I actually buy" reminder attached to a stock item
    (FU-211 / PROPOSAL_PRODUCTS_AS_OVERLAY §3.1).

    The everyday-user counterpart to the power-user `Product` overlay: a short
    label the user types (e.g. "Vitasoy Oat Milky 1L") to remember a favourite
    buy and surface it as a shopping-list hint. Deliberately **separate** from
    `Product` — no price, SKU, store, or validation, and never gated by the
    products or money features. **Unordered** — the SPA sorts client-side
    case-insensitively by label (FU-225 dropped the manual reorder column).
    """
    stock_item_id: UUID
    label: str
    created_at: datetime

    class Fields(BaseEntity.Fields):
        STOCK_ITEM_ID = "stock_item_id"
        LABEL = "label"
        CREATED_AT = "created_at"
