import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from dora_api.domain.entities.merchant import Merchant
from dora_api.features.routers import MERCHANT_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.decorators import has_response
from dora_api.infrastructure.utils import get_container
from dora_api.services.irepository import IRepository


@dataclass(frozen=True, slots=True)
class MerchantDto:
    merchant_id: UUID
    name: str

    @classmethod
    def from_entity(cls, merchant: Merchant) -> 'MerchantDto':
        return MerchantDto(
            merchant_id = merchant.id.value,
            name = merchant.name,
        )


class GetMerchantsHandler:
    def __init__(self, repository: IRepository[Merchant]):
        self.repository = repository

    def handle(self) -> List[MerchantDto]:
        return self.repository.get().project(MerchantDto.from_entity)


@MERCHANT_ROUTER.route("")
@MERCHANT_ROUTER.route("<query>")
@has_response(MerchantDto)
def get_merchants(query: str | None = None):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to get merchants.")
    _Handler = get_container().inject(GetMerchantsHandler)
    _Result = _Handler.handle()
    _Logger.info(f"Successfully retrieved {len(_Result)} merchants.")
    return ok(_Result)
