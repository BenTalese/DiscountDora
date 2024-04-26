
from flask import Blueprint, jsonify

from framework.merchant_api.domain.enumerations.supported_merchant import \
    SupportedMerchant

MERCHANT_ROUTER = Blueprint("MERCHANT_ROUTER", __name__, url_prefix="/api/merchants")

@MERCHANT_ROUTER.route("")
async def get_merchants_async():
    return jsonify([{"name": merchant.value } for merchant in SupportedMerchant])
