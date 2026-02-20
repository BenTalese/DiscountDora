from flask import Blueprint

MERCHANT_ROUTER = Blueprint("MERCHANT_ROUTER", __name__, url_prefix="/api/merchants")
STOCK_ITEM_ROUTER = Blueprint("STOCK_ITEM_ROUTER", __name__, url_prefix="/api/stock-items")
