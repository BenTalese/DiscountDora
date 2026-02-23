from clapy import IServiceProvider
from flask import Blueprint, current_app, jsonify

from merchant_api.services.iconfiguration_manager import IConfigurationManager

MERCHANT_ROUTER = Blueprint("MERCHANT_ROUTER", __name__, url_prefix="/api/merchants")


@MERCHANT_ROUTER.route("")
async def get_all_merchants_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)
    return jsonify([
        {
            "is_enabled": _Merchant.is_enabled,
            "name": _Merchant.name.value
        }
        for _Merchant
        in _ConfigurationManager.get_all_merchants()
    ])


@MERCHANT_ROUTER.route("<merchant_name>", methods = ["PATCH"])
async def update_merchant_async(merchant_name: str):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)
    _ConfigurationManager.toggle_merchant_enabled_state(merchant_name)
    return '', 204
