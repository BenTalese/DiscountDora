from clapy import IServiceProvider
from flask import Blueprint, current_app, jsonify

from framework.merchant_api.services.iconfiguration_manager import IConfigurationManager

MERCHANT_ROUTER = Blueprint("MERCHANT_ROUTER", __name__, url_prefix="/api/merchants")


@MERCHANT_ROUTER.route("")
async def get_merchants_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ConfigurationManager: IConfigurationManager = _ServiceProvider.get_service(IConfigurationManager)
    # TODO: This should just get all merchants, and the api service can send a query to
    # filter down the result, or filter it in memory if not bothered to implement filtering middleware here
    return jsonify([{"name": merchant.name.value} for merchant in _ConfigurationManager.get_enabled_merchants()])


@MERCHANT_ROUTER.route("", methods = ["PATCH"])
async def update_merchant_async():
    # TODO: Implement enabling/disabling merchants
    pass
