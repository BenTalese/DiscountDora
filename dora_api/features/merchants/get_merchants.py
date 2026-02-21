from dataclasses import dataclass
from typing import List
from uuid import UUID

from domain.entities.merchant import Merchant
from flask import current_app

from dora_api.features.routers import MERCHANT_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.decorators import has_response
from dora_api.infrastructure.dependency_container import DependencyContainer
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
    _Container: DependencyContainer = current_app.container  # type: ignore
    _Handler: GetMerchantsHandler = _Container.inject(GetMerchantsHandler)
    _Result = _Handler.handle()
    return ok(_Result)
