from dataclasses import dataclass

from domain.entities.base_entity import EntityID
from domain.entities.merchant import Merchant


@dataclass
class MerchantDto:
    id: EntityID
    name: str

def get_merchant_dto(merchant: Merchant) -> MerchantDto:
    return MerchantDto(
        id = merchant.id,
        name = merchant.name
    )
