from dataclasses import dataclass
from uuid import UUID
from application.dtos.merchant_dto import MerchantDto


@dataclass
class MerchantViewModel:
    merchant_id: UUID
    name: str

def get_merchant_view_model(merchant: MerchantDto) -> MerchantViewModel:
    return MerchantViewModel(
        merchant_id = merchant.merchant_id.value,
        name = merchant.name,
    )
