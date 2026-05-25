from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class ProductBarcode(BaseEntity):
    """A barcode registered against a merchant Product.

    Distinct from StockItem.barcode (which is the user's own QR for a
    pantry item). One ProductBarcode → one Product; many ProductBarcode
    rows can point at the same product if it ships under multiple SKUs.
    """
    product_id: UUID
    barcode: str

    class Fields(BaseEntity.Fields):
        PRODUCT_ID = "product_id"
        BARCODE = "barcode"
