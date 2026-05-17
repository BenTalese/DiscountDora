import logging

from merchant_api.infrastructure.configuration_manager import CONFIGURATION_MANAGER
from merchant_api.routers import MERCHANT_ROUTER


@MERCHANT_ROUTER.route("<merchant_name>", methods = ["PATCH"])
def update_merchant(merchant_name: str):
    logging.getLogger(__name__).info("Updating merchant enabled state.")
    CONFIGURATION_MANAGER.toggle_merchant_enabled_state(merchant_name)
    return '', 204
