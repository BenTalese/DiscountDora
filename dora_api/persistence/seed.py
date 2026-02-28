from datetime import UTC, datetime

from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.shopping_list import ShoppingList
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.entities.user import User
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


def seed_dev_data():
    _Repository = SqlAlchemyRepository()

    # ---------------- MERCHANT ---------------- #
    _MerchantOne = Merchant(name = "Woolworths")
    _MerchantTwo = Merchant(name = "Coles")
    _Repository.add(_MerchantOne)
    _Repository.add(_MerchantTwo)

    # ---------------- PRODUCT ---------------- #
    _OfferOne = ProductOffer(
        offered_on=datetime.now(UTC),
        price_now = 2.82,
        price_was = 3.52
    )

    _ProductOne = Product(
        brand = "Cadbury",
        current_offer = _OfferOne,
        historic_offers = [],
        image = None,
        is_active = True,
        is_available = True,
        merchant = _MerchantOne,
        merchant_stockcode = "51741",
        name = "Cadbury Freddo Cake",
        size = "1.5L",
        size_unit = "L",
        size_value = 1.0,
        web_url = "https://www.woolworths.com.au/shop/productdetails/51741"
    )

    _OfferTwo = ProductOffer(
        offered_on=datetime.now(UTC),
        price_now = 22.15,
        price_was = 32.16
    )

    _ProductTwo = Product(
        brand = "Cadbury",
        current_offer = _OfferTwo,
        historic_offers = [],
        image = None,
        is_active = True,
        is_available = True,
        merchant = _MerchantTwo,
        merchant_stockcode = "3056737",
        name = "Betty Crocker Gluten Free Vanilla Cupcake Mix",
        size = "460G",
        size_unit = "G",
        size_value = 460.0,
        web_url = "https://www.coles.com.au/product/3056737"
    )

    _Repository.add(_OfferOne)
    _Repository.add(_ProductOne)
    _Repository.add(_OfferTwo)
    _Repository.add(_ProductTwo)

    # ---------------- USER ---------------- #
    _UserOne = User(
        email = "ben.talese@gmail.com",
        send_deals_on_day = 6,
        username = "The Coolest Guy",
    )
    _Repository.add(_UserOne)

    # ---------------- STOCK LOCATION ---------------- #
    _StockLocationOne = StockLocation(name = "Pantry")
    _Repository.add(_StockLocationOne)

    # ---------------- STOCK LEVEL ---------------- #
    _StockLevelOne = StockLevel(name = "Well-Stocked", sequence = 0)
    _StockLevelTwo = StockLevel(name = "Sufficient Stock", sequence = 1)
    _StockLevelThree = StockLevel(name = "Low Stock", sequence = 2)
    _StockLevelFour = StockLevel(name = "Out of Stock", sequence = 3)

    _Repository.add(_StockLevelOne)
    _Repository.add(_StockLevelTwo)
    _Repository.add(_StockLevelThree)
    _Repository.add(_StockLevelFour)

    # ---------------- STOCK ITEM ---------------- #
    _StockItemOne = StockItem(
        days_until_stocktake_alert=3,
        image = None,
        name = "Kensington Pride Mangoes",
        notes = None,
        stock_group = None,
        stock_level_last_updated=datetime.now(UTC),
        stock_level=_StockLevelOne,
        stock_location = _StockLocationOne,
        stocktake_alerts_are_enabled=False
    )

    _StockItemTwo = StockItem(
        days_until_stocktake_alert=2,
        image = None,
        name = "Super Awesome Pizza",
        notes = None,
        stock_group = None,
        stock_level_last_updated=datetime.now(UTC),
        stock_level=_StockLevelTwo,
        stock_location = _StockLocationOne,
        stocktake_alerts_are_enabled=False
    )

    _StockItemThree = StockItem(
        days_until_stocktake_alert=5,
        image = None,
        name = "Hot Crispy Chippies",
        notes = None,
        stock_group = None,
        stock_level_last_updated=datetime.now(UTC),
        stock_level=_StockLevelThree,
        stock_location = None,
        stocktake_alerts_are_enabled=True
    )

    _Repository.add(_StockItemOne)
    _Repository.add(_StockItemTwo)
    _Repository.add(_StockItemThree)

    # ---------------- SHOPPING LIST ---------------- #
    _ShoppingListOne = ShoppingList(items = [_StockItemOne, _StockItemTwo])
    _Repository.add(_ShoppingListOne)

    _Repository.save_changes()
