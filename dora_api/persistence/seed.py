from datetime import UTC, date, datetime, timedelta

from werkzeug.security import generate_password_hash

from dora_api.domain.entities.meal import Meal
from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.shopping_list import ShoppingList, ShoppingListLine
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import (
    LOCATION_KIND_AREA, LOCATION_KIND_SECTION, LOCATION_KIND_ZONE,
    StockLocation)
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
    # Default dev user. Username `dora`, password `dora`. Override either by
    # editing this file or by registering a new account through the UI.
    _UserOne = User(
        email = "ben.talese@gmail.com",
        password_hash = generate_password_hash("dora"),
        send_deals_on_day = 6,
        username = "dora",
        is_admin = True,
    )
    _Repository.add(_UserOne)

    # ---------------- STOCK LOCATION HIERARCHY ---------------- #
    # Top-level zones.
    _Pantry = StockLocation(name = "Pantry", kind = LOCATION_KIND_ZONE, sequence = 0)
    _Fridge = StockLocation(name = "Fridge", kind = LOCATION_KIND_ZONE, sequence = 1)
    _Freezer = StockLocation(name = "Freezer", kind = LOCATION_KIND_ZONE, sequence = 2)
    _Repository.add(_Pantry)
    _Repository.add(_Fridge)
    _Repository.add(_Freezer)
    _Repository.save_changes()  # need ids before children can FK

    # Pantry areas + sections (demonstrates the 3-level case).
    _TopShelf = StockLocation(
        name = "Top shelf", kind = LOCATION_KIND_AREA,
        parent_id = _Pantry.id, sequence = 0
    )
    _MiddleShelf = StockLocation(
        name = "Middle shelf", kind = LOCATION_KIND_AREA,
        parent_id = _Pantry.id, sequence = 1
    )
    _Repository.add(_TopShelf)
    _Repository.add(_MiddleShelf)
    _Repository.save_changes()

    _MiddleLeft = StockLocation(
        name = "Left side", kind = LOCATION_KIND_SECTION,
        parent_id = _MiddleShelf.id, sequence = 0
    )
    _MiddleRight = StockLocation(
        name = "Right side", kind = LOCATION_KIND_SECTION,
        parent_id = _MiddleShelf.id, sequence = 1
    )
    _Repository.add(_MiddleLeft)
    _Repository.add(_MiddleRight)

    # Fridge gets a single child area (demonstrates 2-level).
    _CrisperDrawer = StockLocation(
        name = "Crisper drawer", kind = LOCATION_KIND_AREA,
        parent_id = _Fridge.id, sequence = 0
    )
    _Repository.add(_CrisperDrawer)

    # ---------------- STOCK LEVEL ---------------- #
    _WellStocked = StockLevel(name = "Well-Stocked", sequence = 0)
    _Sufficient = StockLevel(name = "Sufficient Stock", sequence = 1)
    _Low = StockLevel(name = "Low Stock", sequence = 2)
    _OutOfStock = StockLevel(name = "Out of Stock", sequence = 3)

    _Repository.add(_WellStocked)
    _Repository.add(_Sufficient)
    _Repository.add(_Low)
    _Repository.add(_OutOfStock)

    # ---------------- STOCK GROUPS ---------------- #
    # Pre-defined groups give users a sensible starting taxonomy out of
    # the box. They're plain rows — fully editable / deletable through the
    # settings page.
    _GroupFruit = StockGroup(name = "Fruit & Veg")
    _GroupDairy = StockGroup(name = "Dairy")
    _GroupPantry = StockGroup(name = "Pantry staples")
    _GroupFrozen = StockGroup(name = "Frozen")
    _GroupSnacks = StockGroup(name = "Snacks & treats")
    for _Group in (_GroupFruit, _GroupDairy, _GroupPantry, _GroupFrozen, _GroupSnacks):
        _Repository.add(_Group)

    # ---------------- STOCK ITEM ---------------- #
    _Today = date.today()
    _Mangoes = StockItem(
        days_until_stocktake_alert = 3,
        image = None,
        name = "Kensington Pride Mangoes",
        notes = None,
        stock_group = _GroupFruit,
        stock_level_last_updated = datetime.now(UTC),
        stock_level = _WellStocked,
        stock_location = _CrisperDrawer,
        stocktake_alerts_are_enabled = False,
        expiry_date = _Today + timedelta(days = 4),
    )

    _Pizza = StockItem(
        days_until_stocktake_alert=2,
        image = None,
        name = "Super Awesome Pizza",
        notes = None,
        stock_group = _GroupFrozen,
        stock_level_last_updated=datetime.now(UTC),
        stock_level=_Sufficient,
        stock_location = _Freezer,
        stocktake_alerts_are_enabled=False,
    )

    _Chips = StockItem(
        days_until_stocktake_alert=5,
        image = None,
        name = "Hot Crispy Chippies",
        notes = None,
        stock_group = _GroupSnacks,
        stock_level_last_updated=datetime.now(UTC),
        stock_level=_Low,
        stock_location = None,
        stocktake_alerts_are_enabled=True,
    )

    _BrazilNuts = StockItem(
        days_until_stocktake_alert = 3,
        image = None,
        name = "Brazil Nuts",
        notes = None,
        stock_group = _GroupSnacks,
        stock_level =_Low,
        stock_level_last_updated = datetime.now(UTC),
        stock_location = _MiddleLeft,
        stocktake_alerts_are_enabled = True,
        is_flagged = True,
    )

    _IceCream = StockItem(
        days_until_stocktake_alert = 7,
        image = None,
        name = "Vanilla Ice Cream",
        notes = None,
        stock_group = _GroupFrozen,
        stock_level = _Low,
        stock_level_last_updated = datetime.now(UTC),
        stock_location = _Freezer,
        stocktake_alerts_are_enabled = True,
        # Already-expired sample so the heatmap has something red to chew on.
        expiry_date = _Today - timedelta(days = 3),
    )

    _Pasta = StockItem(
        days_until_stocktake_alert = 14,
        image = None,
        name = "Barilla Pasta",
        notes = None,
        stock_group = _GroupPantry,
        stock_level = _WellStocked,
        stock_level_last_updated = datetime.now(UTC),
        stock_location = _TopShelf,
        stocktake_alerts_are_enabled = False,
    )

    _Repository.add(_BrazilNuts)
    _Repository.add(_Mangoes)
    _Repository.add(_Pasta)
    _Repository.add(_Pizza)
    _Repository.add(_Chips)
    _Repository.add(_IceCream)

    # ---------------- SHOPPING LIST ---------------- #
    # Lines need a persisted shopping_list_id, so we save the lists first
    # then add lines pointing to them.
    _Today = datetime.now(UTC)
    _PrimaryList = ShoppingList(
        name = "This week",
        created_at = _Today,
        is_primary = True,
    )
    _OldList = ShoppingList(
        name = "Last week",
        created_at = _Today - timedelta(days = 7),
        completed_at = _Today - timedelta(days = 5),
        is_archived = True,
    )
    _Repository.add(_PrimaryList)
    _Repository.add(_OldList)
    _Repository.save_changes()

    for _StockItem in (_BrazilNuts, _Chips, _IceCream):
        _Repository.add(ShoppingListLine(
            shopping_list_id = _PrimaryList.id,
            stock_item_id = _StockItem.id,
            quantity = 1,
        ))
    for _StockItem in (_Pasta, _Pizza):
        _Repository.add(ShoppingListLine(
            shopping_list_id = _OldList.id,
            stock_item_id = _StockItem.id,
            quantity = 1,
            is_ticked = True,
        ))

    # ---------------- RECIPE COLLECTION ---------------- #
    _Weeknight = RecipeCollection(name = "Weeknight Dinners")
    _ToTry = RecipeCollection(name = "To Try")
    _Repository.add(_Weeknight)
    _Repository.add(_ToTry)

    # ---------------- RECIPE ---------------- #
    _PastaIngredient = RecipeIngredient(
        notes = None,
        quantity = 250.0,
        stock_item = _Pasta,
        unit = "g",
    )
    _IceCreamIngredient = RecipeIngredient(
        notes = "for serving",
        quantity = 2.0,
        stock_item = _IceCream,
        unit = "scoops",
    )
    _Repository.add(_PastaIngredient)
    _Repository.add(_IceCreamIngredient)

    _SimplePasta = Recipe(
        category = "Pasta",
        cook_time_minutes = 15,
        cuisine = "Italian",
        difficulty = "Easy",
        image = None,
        ingredients = [_PastaIngredient],
        instructions = "1. Boil water.\n2. Cook pasta until al dente.\n3. Drain and serve.",
        is_favourite = True,
        last_made_on = None,
        name = "Simple Pasta",
        nutrition = None,
        prep_time_minutes = 5,
        recipe_collection = _Weeknight,
        servings = 2,
        time_of_day = "Dinner",
    )

    _IceCreamDessert = Recipe(
        category = "Dessert",
        cook_time_minutes = 0,
        cuisine = None,
        difficulty = "Easy",
        image = None,
        ingredients = [_IceCreamIngredient],
        instructions = "1. Scoop ice cream into bowl.\n2. Enjoy.",
        is_favourite = False,
        last_made_on = None,
        name = "Vanilla Ice Cream Bowl",
        nutrition = None,
        prep_time_minutes = 2,
        recipe_collection = _ToTry,
        servings = 1,
        time_of_day = "Dessert",
    )

    _Repository.add(_SimplePasta)
    _Repository.add(_IceCreamDessert)

    # ---------------- MEAL ---------------- #
    _PastaMeal = Meal(name = "Pasta Night", quantity_in_stock = 3, recipes = [_SimplePasta])
    _DessertMeal = Meal(
        name = "Pasta with Dessert",
        quantity_in_stock = 1,
        recipes = [_SimplePasta, _IceCreamDessert],
    )
    _Repository.add(_PastaMeal)
    _Repository.add(_DessertMeal)

    # ---------------- MEAL PLAN ---------------- #
    _Today = date.today()
    # Start the week on the most recent Monday so "this week" looks reasonable.
    _MondayThisWeek = _Today - timedelta(days = _Today.weekday())

    _Monday = MealPlanEntry(
        meal = _PastaMeal,
        scheduled_for = _MondayThisWeek,
        servings = 2,
        slot = "Dinner",
    )
    _Tuesday = MealPlanEntry(
        meal = _DessertMeal,
        scheduled_for = _MondayThisWeek + timedelta(days = 1),
        servings = 2,
        slot = "Dinner",
    )
    _Repository.add(_Monday)
    _Repository.add(_Tuesday)

    _WeekPlan = MealPlan(
        name = "This Week",
        start_date = _MondayThisWeek,
        entries = [_Monday, _Tuesday],
    )
    _Repository.add(_WeekPlan)

    _Repository.save_changes()
