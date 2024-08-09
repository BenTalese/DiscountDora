from pathlib import Path
from typing import List

from clapy import IServiceProvider
from flask import current_app

from application.infrastructure.utils import get_classes_ending_with
from framework.merchant_api.services.imerchant_data_provider import \
    IMerchantDataProvider


def get_merchant_data_providers() -> List[IMerchantDataProvider]:
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _DataProviders: List[IMerchantDataProvider] = [
        _ServiceProvider.get_service(_Provider)
        for _Provider
        in get_classes_ending_with('provider', Path() / 'framework' / 'merchant_api' / 'infrastructure' / 'merchant_data_providers')
        if type(_Provider) is not IMerchantDataProvider
    ]

    _DataProviders.sort(key = lambda mdp: mdp.priority)

    return _DataProviders


def get_healthy_merchant_data_providers() -> List[IMerchantDataProvider]:
    return [
        _Provider
        for _Provider
        in get_merchant_data_providers()
        if _Provider.is_healthy
    ]
