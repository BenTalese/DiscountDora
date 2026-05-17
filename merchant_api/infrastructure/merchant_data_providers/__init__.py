from pathlib import Path
from typing import List

from dora_api.infrastructure.utils import get_classes_ending_with
from merchant_api.infrastructure.merchant_data_providers.merchant_data_provider import MerchantDataProvider

MERCHANT_DATA_PROVIDERS: list[MerchantDataProvider] = [
    _Provider()
    for _Provider
    in get_classes_ending_with('provider', Path() / 'merchant_api' / 'infrastructure' / 'merchant_data_providers')
    if _Provider != MerchantDataProvider  # Exclude the base class itself
]
MERCHANT_DATA_PROVIDERS.sort(key = lambda mdp: mdp.priority)


def get_healthy_providers() -> List[MerchantDataProvider]:
    return [
        _Provider
        for _Provider
        in MERCHANT_DATA_PROVIDERS
        if _Provider.is_healthy
    ]
