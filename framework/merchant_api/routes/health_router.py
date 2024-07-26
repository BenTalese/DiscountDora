from flask import Blueprint, jsonify

from framework.merchant_api.infrastructure.merchant_data_providers import get_merchant_data_providers

HEALTH_ROUTER = Blueprint("HEALTH_ROUTER", __name__, url_prefix="/api/health")


@HEALTH_ROUTER.route("")
async def health_check_async():
    return jsonify(True), 200


@HEALTH_ROUTER.route("data-providers")
async def data_providers_health_check_async():
    _DataProviders = get_merchant_data_providers()

    return jsonify([{
        "base_url": _Provider.base_url,
        "is_healthy": _Provider.is_healthy
    } for _Provider in _DataProviders]), 200
