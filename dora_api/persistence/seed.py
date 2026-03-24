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

    _FreddoCake = Product(
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

    _CupcakeMix = Product(
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
    _Repository.add(_FreddoCake)
    _Repository.add(_OfferTwo)
    _Repository.add(_CupcakeMix)

    # ---------------- USER ---------------- #
    _UserOne = User(
        email = "ben.talese@gmail.com",
        send_deals_on_day = 6,
        username = "The Coolest Guy",
    )
    _Repository.add(_UserOne)

    # ---------------- STOCK LOCATION ---------------- #
    _Pantry = StockLocation(name = "Pantry")
    _Freezer = StockLocation(name = "Freezer")
    _Fridge = StockLocation(name = "Fridge")
    _Repository.add(_Pantry)
    _Repository.add(_Freezer)
    _Repository.add(_Fridge)

    # ---------------- STOCK LEVEL ---------------- #
    _WellStocked = StockLevel(name = "Well-Stocked", sequence = 0)
    _Sufficient = StockLevel(name = "Sufficient Stock", sequence = 1)
    _Low = StockLevel(name = "Low Stock", sequence = 2)
    _OutOfStock = StockLevel(name = "Out of Stock", sequence = 3)

    _Repository.add(_WellStocked)
    _Repository.add(_Sufficient)
    _Repository.add(_Low)
    _Repository.add(_OutOfStock)

    # ---------------- STOCK ITEM ---------------- #
    _Mangoes = StockItem(
        days_until_stocktake_alert = 3,
        image = None,
        name = "Kensington Pride Mangoes",
        notes = None,
        stock_group = None,
        stock_level_last_updated = datetime.now(UTC),
        stock_level = _WellStocked,
        stock_location = _Pantry,
        stocktake_alerts_are_enabled = False
    )

    _Pizza = StockItem(
        days_until_stocktake_alert=2,
        image = None,
        name = "Super Awesome Pizza",
        notes = None,
        stock_group = None,
        stock_level_last_updated=datetime.now(UTC),
        stock_level=_Sufficient,
        stock_location = _Pantry,
        stocktake_alerts_are_enabled=False
    )

    _Chips = StockItem(
        days_until_stocktake_alert=5,
        image = None,
        name = "Hot Crispy Chippies",
        notes = None,
        stock_group = None,
        stock_level_last_updated=datetime.now(UTC),
        stock_level=_Low,
        stock_location = None,
        stocktake_alerts_are_enabled=True
    )

    _BrazilNuts = StockItem(
        days_until_stocktake_alert = 3,
        image = None,
        name = "Brazil Nuts",
        notes = None,
        stock_group = None,
        stock_level =_Low,
        stock_level_last_updated = datetime.now(UTC),
        stock_location = _Pantry,
        stocktake_alerts_are_enabled = True,
    )

    _IceCream = StockItem(
        days_until_stocktake_alert = 7,
        image = None,
        name = "Vanilla Ice Cream",
        notes = None,
        stock_group = None,
        stock_level = _Low,
        stock_level_last_updated = datetime.now(UTC),
        stock_location = _Freezer,
        stocktake_alerts_are_enabled = True,
    )

    _Pasta = StockItem(
        days_until_stocktake_alert = 14,
        image = None,
        name = "Barilla Pasta",
        notes = None,
        stock_group = None,
        stock_level = _WellStocked,
        stock_level_last_updated = datetime.now(UTC),
        stock_location = _Pantry,
        stocktake_alerts_are_enabled = False,
    )

    _Repository.add(_BrazilNuts)
    _Repository.add(_Mangoes)
    _Repository.add(_Pasta)
    _Repository.add(_Pizza)
    _Repository.add(_Chips)
    _Repository.add(_IceCream)

    # ---------------- SHOPPING LIST ---------------- #
    _ShoppingListOne = ShoppingList(items = [_BrazilNuts, _Pizza])
    _ShoppingListTwo = ShoppingList(items = [_Chips, _IceCream])
    _ShoppingListThree = ShoppingList(items = [_BrazilNuts, _Pasta])

    _Repository.add(_ShoppingListOne)
    _Repository.add(_ShoppingListTwo)
    _Repository.add(_ShoppingListThree)

    _Repository.save_changes()
