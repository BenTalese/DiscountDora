from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity

# Provenance of a price point. `manual` = the user typed it (stock-item detail
# / quick-add); `shopping_close_out` = captured when finishing a shop;
# `product_offer` = derived from a linked Product offer (only when Products is
# on). The everyday layer carries NO merchant attribution (§2.6) — this is
# "what it cost me", not a cross-store comparison.
PRICE_OBSERVATION_SOURCES = ("manual", "shopping_close_out", "product_offer")


@dataclass
class StockItemPriceObservation(BaseEntity):
    """A single "what this cost me" price point on a stock item (FU-213 /
    PROPOSAL_PRODUCTS_AS_OVERLAY §3.2).

    The everyday price-history substrate: the user records the **total** price
    paid + the quantity/unit; the per-unit cost is derived server-side
    (`get_stock_item_unit_cost_at`) — the client never divides (R-003).
    Gated by the money/spend feature at the surfaces, not by Products.
    """
    stock_item_id: UUID
    price: float          # total paid for `qty` of `unit`
    qty: float
    unit: str
    observed_at: datetime
    source: str
    created_at: datetime

    class Fields(BaseEntity.Fields):
        STOCK_ITEM_ID = "stock_item_id"
        PRICE = "price"
        QTY = "qty"
        UNIT = "unit"
        OBSERVED_AT = "observed_at"
        SOURCE = "source"
        CREATED_AT = "created_at"
