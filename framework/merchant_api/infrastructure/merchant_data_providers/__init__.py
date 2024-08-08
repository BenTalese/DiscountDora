from pathlib import Path
from typing import List

from clapy import IServiceProvider
from flask import current_app

from application.infrastructure.utils import get_classes_ending_with
from framework.merchant_api.infrastructure.merchant_data_providers.merchant_data_provider import \
    MerchantDataProvider


def get_merchant_data_providers() -> List[MerchantDataProvider]:
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _DataProviders: List[MerchantDataProvider] = [
        _ServiceProvider.get_service(_Provider)
        for _Provider
        in get_classes_ending_with('provider', Path() / 'framework' / 'merchant_api' / 'infrastructure' / 'merchant_data_providers')
    ]

    _DataProviders.sort(key = lambda mdp: mdp.priority)

    return _DataProviders


def get_healthy_merchant_data_providers() -> List[MerchantDataProvider]:
    return [
        _Provider
        for _Provider
        in get_merchant_data_providers()
        if _Provider.is_healthy
    ]
