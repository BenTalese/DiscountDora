from flask import jsonify
from dora_api.features.routers import HEALTH_ROUTER


@HEALTH_ROUTER.route("")
def health_check():
    return jsonify(True), 200
