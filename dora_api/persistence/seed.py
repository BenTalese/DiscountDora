from datetime import UTC, datetime

from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.shopping_list import ShoppingList
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.entities.user import User
from dora_api.infrastructure.utils import get_container
from dora_api.services.irepository import IRepository


def seed_dev_data():
    _Container = get_container()
    _MerchantRepository = _Container.inject(IRepository[Merchant])
    _ProductRepository = _Container.inject(IRepository[Product])
    _ProductOfferRepository = _Container.inject(IRepository[ProductOffer])
    _StockItemRepository = _Container.inject(IRepository[StockItem])
    _StockLocationRepository = _Container.inject(IRepository[StockLocation])
    _StockLevelRepository = _Container.inject(IRepository[StockLevel])
    _ShoppingListRepository = _Container.inject(IRepository[ShoppingList])
    _UserRepository = _Container.inject(IRepository[User])

    # ---------------- MERCHANT ---------------- #
    _MerchantOne = Merchant(name = "Woolworths")
    _MerchantTwo = Merchant(name = "Coles")
    _MerchantRepository.add(_MerchantOne)
    _MerchantRepository.add(_MerchantTwo)
    _MerchantRepository.save_changes()

    # ---------------- PRODUCT ---------------- #
    _ProductOne = Product(
        brand = "Cadbury",
        current_offer = ProductOffer(
            offered_on=datetime.now(UTC),
            price_now = 2.82,
            price_was = 3.52
        ),
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

    _ProductTwo = Product(
        brand = "Cadbury",
        current_offer = ProductOffer(
            offered_on=datetime.now(UTC),
            price_now = 22.15,
            price_was = 32.16
        ),
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

    _ProductRepository.add(_ProductOne)
    _ProductRepository.add(_ProductTwo)
    _ProductOfferRepository.add(_ProductOne.current_offer)
    _ProductOfferRepository.add(_ProductTwo.current_offer)
    _ProductRepository.save_changes()
    _ProductOfferRepository.save_changes()
    # TODO: Is this necessary? Can't it save the related data?...

    # ---------------- USER ---------------- #
    _UserOne = User(
        email = "ben.talese@gmail.com",
        send_deals_on_day = 6,
        username = "The Coolest Guy",
    )
    _UserRepository.add(_UserOne)
    _UserRepository.save_changes()

    # ---------------- STOCK LOCATION ---------------- #
    _StockLocationOne = StockLocation(name = "Pantry")
    _StockLocationRepository.add(_StockLocationOne)
    _StockLocationRepository.save_changes()

    # ---------------- STOCK LEVEL ---------------- #
    _StockLevelOne = StockLevel(name = "Well-Stocked", sequence = 0)
    _StockLevelTwo = StockLevel(name = "Sufficient Stock", sequence = 1)
    _StockLevelThree = StockLevel(name = "Low Stock", sequence = 2)
    _StockLevelFour = StockLevel(name = "Out of Stock", sequence = 3)

    _StockLevelRepository.add(_StockLevelOne)
    _StockLevelRepository.add(_StockLevelTwo)
    _StockLevelRepository.add(_StockLevelThree)
    _StockLevelRepository.add(_StockLevelFour)
    _StockLevelRepository.save_changes()

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

    _StockItemRepository.add(_StockItemOne)
    _StockItemRepository.add(_StockItemTwo)
    _StockItemRepository.add(_StockItemThree)
    _StockItemRepository.save_changes()

    # ---------------- SHOPPING LIST ---------------- #
    _ShoppingListOne = ShoppingList(items = [_StockItemOne, _StockItemTwo])

    _ShoppingListRepository.add(_ShoppingListOne)
    _ShoppingListRepository.save_changes()
