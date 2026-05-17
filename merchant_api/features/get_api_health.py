import logging

from flask import jsonify

from merchant_api.routers import HEALTH_ROUTER


@HEALTH_ROUTER.route("")
def get_api_health():
    logging.getLogger(__name__).info("API health check requested.")
    return jsonify(True), 200
