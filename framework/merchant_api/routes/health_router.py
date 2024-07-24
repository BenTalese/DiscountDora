from flask import Blueprint, jsonify

HEALTH_ROUTER = Blueprint("HEALTH_ROUTER", __name__, url_prefix="/api/health")


@HEALTH_ROUTER.route("")
async def health_check_async():
    return jsonify(True), 200


@HEALTH_ROUTER.route("data-providers")
async def data_providers_health_check_async():
    # TODO: Return health from services
    return jsonify(True), 200
