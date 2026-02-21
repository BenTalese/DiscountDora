from flask import jsonify
from dora_api.features.routers import HEALTH_ROUTER


@HEALTH_ROUTER.route("")
async def health_check_async():
    return jsonify(True), 200
