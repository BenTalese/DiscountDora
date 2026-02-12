from dataclasses import dataclass
from uuid import UUID

from domain.entities.merchant import Merchant


@dataclass
class MerchantViewModel:
    merchant_id: UUID
    name: str


def get_merchant_view_model(merchant: Merchant) -> MerchantViewModel:
    return MerchantViewModel(
        merchant_id = merchant.id.value,
        name = merchant.name,
    )
