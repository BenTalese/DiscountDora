from flask import Blueprint

HEALTH_ROUTER = Blueprint("HEALTH_ROUTER", __name__, url_prefix="/api/health")
MERCHANT_ROUTER = Blueprint("MERCHANT_ROUTER", __name__, url_prefix="/api/merchants")
STOCK_ITEM_ROUTER = Blueprint("STOCK_ITEM_ROUTER", __name__, url_prefix="/api/stock-items")
STOCK_LEVEL_ROUTER = Blueprint("STOCK_LEVEL_ROUTER", __name__, url_prefix="/api/stock-levels")
USER_ROUTER = Blueprint("USER_ROUTER", __name__, url_prefix="/api/users")
