import logging

from flask import jsonify

from merchant_api.infrastructure.configuration_manager import CONFIGURATION_MANAGER
from merchant_api.routers import MERCHANT_ROUTER


@MERCHANT_ROUTER.route("")
def get_all_merchants():
    logging.getLogger(__name__).info("Getting all merchants from config.")
    return jsonify([
        {
            "is_enabled": _Merchant.is_enabled,
            "name": _Merchant.name.value
        }
        for _Merchant
        in CONFIGURATION_MANAGER.get_all_merchants()
    ])
