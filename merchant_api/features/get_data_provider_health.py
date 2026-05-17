import logging

from flask import jsonify

from merchant_api.infrastructure.merchant_data_providers import MERCHANT_DATA_PROVIDERS
from merchant_api.routers import HEALTH_ROUTER


@HEALTH_ROUTER.route("data-providers")
def get_data_providers_health():
    logging.getLogger(__name__).info("Data providers health check requested.")
    return jsonify([{
        "base_url": _Provider.base_url,
        "is_healthy": _Provider.is_healthy
    } for _Provider in MERCHANT_DATA_PROVIDERS]), 200
