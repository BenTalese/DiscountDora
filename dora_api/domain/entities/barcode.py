from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class Barcode(BaseEntity):
    """A real-world EAN/UPC barcode registered in Dora (FU-056 hybrid model).

    Either `product_id` or `stock_item_id` (or both) must be set:

    * **Product-tied** (`product_id` set, exclusive of `stock_item_id` or
      with it both set): the barcode is a Product's catalogue EAN. The 1:1
      "one Product = one EAN" rule is enforced via a DB UNIQUE constraint
      on `product_id`. From a stock item's perspective, this barcode
      reaches it via `StockItemProduct` (the user has the Product linked).

    * **Stock-item-direct** (`stock_item_id` set, `product_id` NULL): the
      user registered a raw EAN against a specific stock item without
      bothering with the Products overlay (lightweight install path, or
      a stock item that has no linked Product).

    * **Both set**: the EAN is a real Product's catalogue code *and* the
      user explicitly tied it to their pantry slot. Both linkages
      coexist; the stock_item_id wins for lookup direction (most specific).

    A CHECK constraint forbids the "neither set" row.
    Distinct from `dora://stock-item/<uuid>` QR codes — those are Dora's
    own labels, not real-world barcodes, and bypass this table entirely.
    """
    barcode: str
    product_id: UUID | None
    stock_item_id: UUID | None
    created_at: datetime

    class Fields(BaseEntity.Fields):
        BARCODE = "barcode"
        PRODUCT_ID = "product_id"
        STOCK_ITEM_ID = "stock_item_id"
        CREATED_AT = "created_at"
