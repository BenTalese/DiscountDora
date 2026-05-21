import logging
from dataclasses import dataclass
from uuid import UUID

from flask import request

from dora_api.domain.entities.merchant import Merchant
from dora_api.features.routers import MERCHANT_ROUTER
from dora_api.infrastructure.api_response import bad_request, paginated
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class MerchantDto:
    merchant_id: UUID
    name: str

    @classmethod
    def from_entity(cls, merchant: Merchant) -> 'MerchantDto':
        return MerchantDto(
            merchant_id = merchant.id,
            name = merchant.name,
        )


_FIELD_MAP: dict[str, EntityField] = {
    "merchant_id": EntityField(Merchant, "id"),
}


class GetMerchantsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, options) -> Page[MerchantDto]:
        return self.repository.get(Merchant).paginate(
            options, MerchantDto.from_entity, field_map=_FIELD_MAP
        )


@MERCHANT_ROUTER.route("")
def get_merchants():
    _Logger = logging.getLogger(__name__)
    try:
        _Options = parse_query_options(request.args)
        _Page = get_container().inject(GetMerchantsHandler).handle(_Options)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Logger.info(f"Retrieved {len(_Page.items)} of {_Page.total} merchants.")
    return paginated(_Page.items, _Page.total, _Page.page, _Page.limit)
