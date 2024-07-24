from clapy import IServiceProvider
from flask import Blueprint, current_app, jsonify

from framework.merchant_api.services.iconfiguration_manager import IConfigurationManager

MERCHANT_ROUTER = Blueprint("MERCHANT_ROUTER", __name__, url_prefix="/api/merchants")


@MERCHANT_ROUTER.route("")
async def get_merchants_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)
    return jsonify([{"name": merchant.name.name} for merchant in _ConfigurationManager.get_enabled_merchants()])
