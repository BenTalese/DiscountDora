from flask import Blueprint


HEALTH_ROUTER = Blueprint("HEALTH_ROUTER", __name__, url_prefix="/api/health")
PRODUCT_ROUTER = Blueprint("PRODUCT_ROUTER", __name__, url_prefix="/api/products")
MERCHANT_ROUTER = Blueprint("MERCHANT_ROUTER", __name__, url_prefix="/api/merchants")
