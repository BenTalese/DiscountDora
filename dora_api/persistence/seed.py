from datetime import UTC, date, datetime, timedelta

from werkzeug.security import generate_password_hash

from dora_api.app import db
from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.store import Store
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_historic_offer import ProductHistoricOffer
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.category import Category
from dora_api.domain.entities.cuisine import Cuisine
from dora_api.domain.entities.dietary_tag import DietaryTag
from dora_api.domain.entities.meal_slot import MealSlot
from dora_api.domain.entities.tool import Tool
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.shopping_list import (
    SHOPPING_LIST_STATUS_DONE, SHOPPING_LIST_STATUS_SHOPPING,
    ShoppingList, ShoppingListLine)
from dora_api.domain.entities.shopping_list_template import (
    ShoppingListTemplate, ShoppingListTemplateLine)
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_level_change import StockLevelChange
from dora_api.domain.entities.stock_location import (
    LOCATION_KIND_AREA, LOCATION_KIND_SECTION, LOCATION_KIND_ZONE,
    StockLocation)
from dora_api.domain.entities.user import User
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


def seed_dev_data():
    """Populate a rich dev dataset that exercises every screen.

    Covers: multiple stores and products (with current + historic offers
    for sparklines), product↔stock-item links, a deep
    location hierarchy, stock items across all levels / expiry states / flags /
    open markers, substitutes, level-change history, recipes (cookable and
    not) across collections, meals, a full week's meal plan, primary /
    in-progress / archived shopping lists with selected offers, and templates.
    """
    repo = SqlAlchemyRepository()
    now = datetime.now(UTC)
    today = date.today()

    # Build with autoflush off: we add child rows (e.g. RecipeIngredient) before
    # their parent exists to link them, and an autoflush in that gap would try to
    # insert with a null FK. The explicit save_changes() calls below flush with
    # every relationship resolved. Restored before the final commit.
    db.session.autoflush = False

    # ---------------- STORES (dev fixtures only) ---------------- #
    # FU-189 — production ships zero pre-seeded stores; these exist only
    # so the dev seed dataset has products to render.
    woolworths = Store(name="Woolworths")
    coles = Store(name="Coles")
    aldi = Store(name="Aldi")
    iga = Store(name="IGA")
    for s in (woolworths, coles, aldi, iga):
        repo.add(s)

    # ---------------- PRODUCTS ---------------- #
    def make_product(*, store, name, brand, size, size_unit, size_value,
                     stockcode, price_now, price_was, history):
        """history: list of (days_ago, price_now, price_was)."""
        current = ProductOffer(offered_on=now, price_now=price_now, price_was=price_was)
        repo.add(current)
        historic = []
        for days_ago, h_now, h_was in history:
            offer = ProductHistoricOffer(
                offered_on=now - timedelta(days=days_ago),
                price_now=h_now,
                price_was=h_was,
            )
            repo.add(offer)
            historic.append(offer)
        product = Product(
            brand=brand,
            current_offer=current,
            historic_offers=historic,
            image=None,
            is_active=True,
            is_available=True,
            store=store,
            merchant_stockcode=stockcode,
            name=name,
            size=size,
            size_unit=size_unit,
            size_value=size_value,
            web_url=f"https://example.com/p/{stockcode}",
        )
        repo.add(product)
        return product

    milk_woolies = make_product(
        store=woolworths, name="Woolworths Full Cream Milk 2L", brand="Woolworths",
        size="2L", size_unit="L", size_value=2.0, stockcode="W-MILK-2L",
        price_now=3.10, price_was=3.10,
        history=[(28, 3.30, 3.30), (21, 3.30, 3.30), (14, 3.10, 3.30), (7, 3.10, 3.10)],
    )
    milk_coles = make_product(
        store=coles, name="Coles Full Cream Milk 2L", brand="Coles",
        size="2L", size_unit="L", size_value=2.0, stockcode="C-MILK-2L",
        price_now=2.90, price_was=3.30,
        history=[(28, 3.30, 3.30), (14, 3.30, 3.30), (7, 2.90, 3.30)],
    )
    eggs_woolies = make_product(
        store=woolworths, name="Woolworths Free Range Eggs 12pk", brand="Woolworths",
        size="700g", size_unit="g", size_value=700.0, stockcode="W-EGG-12",
        price_now=5.50, price_was=6.20,
        history=[(30, 6.20, 6.20), (15, 5.90, 6.20), (5, 5.50, 6.20)],
    )
    pasta_barilla = make_product(
        store=coles, name="Barilla Spaghetti No.5 500g", brand="Barilla",
        size="500g", size_unit="g", size_value=500.0, stockcode="C-PASTA-500",
        price_now=1.50, price_was=3.00,
        history=[(30, 3.00, 3.00), (20, 2.50, 3.00), (10, 1.50, 3.00), (2, 1.50, 3.00)],
    )
    oil_aldi = make_product(
        store=aldi, name="Aldi Extra Virgin Olive Oil 1L", brand="Vialli",
        size="1L", size_unit="L", size_value=1.0, stockcode="A-OIL-1L",
        price_now=7.99, price_was=9.99,
        history=[(25, 9.99, 9.99), (12, 8.99, 9.99), (3, 7.99, 9.99)],
    )
    parmesan_coles = make_product(
        store=coles, name="Coles Parmesan Wedge 200g", brand="Coles",
        size="200g", size_unit="g", size_value=200.0, stockcode="C-PARM-200",
        price_now=6.00, price_was=6.00, history=[(20, 6.50, 6.50), (8, 6.00, 6.50)],
    )
    coffee_iga = make_product(
        store=iga, name="Vittoria Coffee Beans 1kg", brand="Vittoria",
        size="1kg", size_unit="kg", size_value=1.0, stockcode="I-COFFEE-1KG",
        price_now=28.00, price_was=40.00,
        history=[(40, 40.00, 40.00), (20, 34.00, 40.00), (5, 28.00, 40.00)],
    )
    freddo = make_product(
        store=woolworths, name="Cadbury Freddo Cake", brand="Cadbury",
        size="1.5L", size_unit="L", size_value=1.0, stockcode="51741",
        price_now=2.82, price_was=3.52, history=[(15, 3.52, 3.52), (4, 2.82, 3.52)],
    )
    cupcake = make_product(
        store=coles, name="Betty Crocker Gluten Free Vanilla Cupcake Mix", brand="Betty Crocker",
        size="460g", size_unit="g", size_value=460.0, stockcode="3056737",
        price_now=22.15, price_was=32.16, history=[(18, 32.16, 32.16), (6, 22.15, 32.16)],
    )

    # ---------------- USER ---------------- #
    # Default dev user. Username `dora`, password `dora`.
    repo.add(User(
        email="ben.talese@gmail.com",
        password_hash=generate_password_hash("dora"),
        send_deals_on_day=6,
        username="dora",
        is_admin=True,
    ))

    # ---------------- LOCATION HIERARCHY ---------------- #
    pantry = StockLocation(name="Pantry", kind=LOCATION_KIND_ZONE, sequence=0)
    fridge = StockLocation(name="Fridge", kind=LOCATION_KIND_ZONE, sequence=1)
    freezer = StockLocation(name="Freezer", kind=LOCATION_KIND_ZONE, sequence=2)
    for loc in (pantry, fridge, freezer):
        repo.add(loc)
    repo.save_changes()  # need ids before children FK to them

    top_shelf = StockLocation(name="Top shelf", kind=LOCATION_KIND_AREA, parent_id=pantry.id, sequence=0)
    middle_shelf = StockLocation(name="Middle shelf", kind=LOCATION_KIND_AREA, parent_id=pantry.id, sequence=1)
    for loc in (top_shelf, middle_shelf):
        repo.add(loc)
    repo.save_changes()

    middle_left = StockLocation(name="Left side", kind=LOCATION_KIND_SECTION, parent_id=middle_shelf.id, sequence=0)
    middle_right = StockLocation(name="Right side", kind=LOCATION_KIND_SECTION, parent_id=middle_shelf.id, sequence=1)
    crisper = StockLocation(name="Crisper drawer", kind=LOCATION_KIND_AREA, parent_id=fridge.id, sequence=0)
    for loc in (middle_left, middle_right, crisper):
        repo.add(loc)

    # ---------------- STOCK LEVELS ---------------- #
    well = StockLevel(name="Well-Stocked", sequence=0)
    sufficient = StockLevel(name="Sufficient Stock", sequence=1)
    low = StockLevel(name="Low Stock", sequence=2)
    out = StockLevel(name="Out of Stock", sequence=3)
    for lvl in (well, sufficient, low, out):
        repo.add(lvl)

    # ---------------- STOCK GROUPS ---------------- #
    g_fruit = StockGroup(name="Fruit & Veg")
    g_dairy = StockGroup(name="Dairy")
    g_pantry = StockGroup(name="Pantry staples")
    g_frozen = StockGroup(name="Frozen")
    g_snacks = StockGroup(name="Snacks & treats")
    g_meat = StockGroup(name="Meat & seafood")
    for grp in (g_fruit, g_dairy, g_pantry, g_frozen, g_snacks, g_meat):
        repo.add(grp)

    # ---------------- STOCK ITEMS ---------------- #
    def make_item(*, name, group, level, location, **kw):
        item = StockItem(
            days_until_stocktake_alert=kw.get("stocktake_days", 7),
            image=None,
            name=name,
            notes=kw.get("notes"),
            stock_group=group,
            stock_level_last_updated=now - timedelta(days=kw.get("updated_days_ago", 0)),
            stock_level=level,
            stock_location=location,
            stocktake_alerts_are_enabled=kw.get("stocktake_alerts", False),
            expiry_date=kw.get("expiry"),
            is_flagged=kw.get("flagged", False),
            auto_add_when_low=kw.get("auto_add", False),
            is_open=kw.get("is_open", False),
            opened_on=kw.get("opened_on"),
            products=kw.get("products", []),
        )
        repo.add(item)
        return item

    mangoes = make_item(name="Kensington Pride Mangoes", group=g_fruit, level=well,
                        location=crisper, expiry=today + timedelta(days=4), stocktake_days=3)
    pizza = make_item(name="Super Awesome Pizza", group=g_frozen, level=sufficient, location=freezer)
    chips = make_item(name="Hot Crispy Chippies", group=g_snacks, level=low, location=None,
                      stocktake_alerts=True, stocktake_days=5)
    brazil = make_item(name="Brazil Nuts", group=g_snacks, level=low, location=middle_left,
                       flagged=True, stocktake_alerts=True)
    icecream = make_item(name="Vanilla Ice Cream", group=g_frozen, level=low, location=freezer,
                         stocktake_alerts=True, expiry=today - timedelta(days=3))
    pasta = make_item(name="Barilla Pasta", group=g_pantry, level=well, location=top_shelf,
                      products=[pasta_barilla])
    milk = make_item(name="Full Cream Milk", group=g_dairy, level=low, location=fridge,
                     expiry=today + timedelta(days=2), auto_add=True, is_open=True,
                     opened_on=today - timedelta(days=2), products=[milk_woolies, milk_coles],
                     updated_days_ago=1)
    eggs = make_item(name="Free Range Eggs", group=g_dairy, level=sufficient, location=fridge,
                     flagged=True, products=[eggs_woolies])
    butter = make_item(name="Butter", group=g_dairy, level=well, location=fridge,
                       is_open=True, opened_on=today - timedelta(days=5))
    tomatoes = make_item(name="Canned Tomatoes", group=g_pantry, level=well, location=middle_right)
    onions = make_item(name="Brown Onions", group=g_fruit, level=sufficient, location=pantry)
    garlic = make_item(name="Garlic", group=g_fruit, level=well, location=pantry)
    olive_oil = make_item(name="Olive Oil", group=g_pantry, level=sufficient, location=top_shelf,
                          flagged=True, is_open=True, opened_on=today - timedelta(days=20),
                          products=[oil_aldi])
    parmesan = make_item(name="Parmesan Cheese", group=g_dairy, level=out, location=fridge,
                         auto_add=True, products=[parmesan_coles])
    chicken = make_item(name="Chicken Breast", group=g_meat, level=sufficient, location=freezer)
    rice = make_item(name="Jasmine Rice", group=g_pantry, level=well, location=middle_right)
    soy = make_item(name="Soy Sauce", group=g_pantry, level=sufficient, location=middle_left)
    broccoli = make_item(name="Broccoli", group=g_fruit, level=low, location=crisper,
                         expiry=today + timedelta(days=1), auto_add=True, stocktake_alerts=True)
    bread = make_item(name="Sourdough Bread", group=g_pantry, level=out, location=None,
                      flagged=True, auto_add=True)
    coffee = make_item(name="Coffee Beans", group=g_pantry, level=well, location=top_shelf,
                       flagged=True, is_open=True, opened_on=today - timedelta(days=3),
                       products=[coffee_iga])

    repo.save_changes()  # items need ids before substitutes / history / lines

    # ---------------- SUBSTITUTES (undirected pairs) ---------------- #
    from dora_api.features.substitutes.canonical import canonical_pair
    assoc = db.metadata.tables["StockItemSubstitute"]
    raw_pairs = [
        (olive_oil.id, butter.id, "Cooking fat"),
        (pasta.id, rice.id, "Carb base"),
        (parmesan.id, butter.id, None),
        (milk.id, butter.id, None),
    ]
    now = datetime.now(UTC)
    seen: set[tuple] = set()
    rows: list[dict] = []
    for x, y, notes in raw_pairs:
        a, b = canonical_pair(x, y)
        if (a, b) in seen:
            continue
        seen.add((a, b))
        rows.append({
            "stock_item_a_id": a,
            "stock_item_b_id": b,
            "notes": notes,
            "created_at": now,
        })
    db.session.execute(assoc.insert(), rows)

    # ---------------- STOCK-LEVEL HISTORY ---------------- #
    def level_change(item, level, days_ago):
        repo.add(StockLevelChange(
            stock_item_id=item.id,
            stock_level_id=level.id,
            stock_level_name=level.name,
            changed_at=now - timedelta(days=days_ago),
        ))

    level_change(milk, well, 9)
    level_change(milk, sufficient, 5)
    level_change(milk, low, 1)
    level_change(pasta, sufficient, 12)
    level_change(pasta, well, 3)
    level_change(icecream, sufficient, 8)
    level_change(icecream, low, 2)
    level_change(parmesan, low, 6)
    level_change(parmesan, out, 1)

    # ---------------- PRICE OBSERVATIONS (FU-227 chunk 2) ---------------- #
    # Exercises the full state matrix the "Your prices" widget (chunk 3) will
    # render: ≥3 items with 3+ observations (baseline-ready), ≥1 below
    # MIN_SAMPLES (the empty-state copy), ≥1 with current > 1.15× median
    # (above-usual chip), ≥1 with store_id set + ≥1 without (store chip).
    # These are all *manual* observations (no FK); the chunk-5 harvest below
    # adds FK-provenance ones from finished lists (milk, pasta, pizza, chips,
    # bread).
    from dora_api.domain.entities.stock_item_price_observation import StockItemPriceObservation

    def price_obs(item, *, total_price, total_measure, unit, days_ago, store=None, pack_count=None):
        repo.add(StockItemPriceObservation(
            stock_item_id=item.id,
            total_price=float(total_price),
            total_measure=float(total_measure),
            unit=unit,
            observed_at=now - timedelta(days=days_ago),
            store_id=(store.id if store is not None else None),
            shopping_list_line_id=None,
            created_at=now - timedelta(days=days_ago),
            pack_count=pack_count,
        ))

    # Milk — 4 obs in L, store-tagged, baseline ≈ $2.00/L, latest at baseline.
    price_obs(milk, total_price=4.20, total_measure=2.0, unit="L", days_ago=42, store=woolworths)
    price_obs(milk, total_price=2.00, total_measure=1.0, unit="L", days_ago=21, store=coles)
    price_obs(milk, total_price=4.10, total_measure=2.0, unit="L", days_ago=10, store=woolworths)
    price_obs(milk, total_price=2.00, total_measure=1.0, unit="L", days_ago=2, store=coles)
    # Yoghurt-style multipack observation on butter (FU-227 follow-up:
    # exercises the pack_count column + the obs list's "4 × 125g" render).
    # "$4.20 for 4 × 125g pack of yoghurt" — keeps butter at 3 obs so the
    # widget flips from empty-state to baseline-ready.
    price_obs(butter, total_price=4.20, total_measure=500.0, unit="g",
              days_ago=10, store=woolworths, pack_count=4)

    # Olive oil — 4 obs in ml, no store, latest 30% above median → above-usual chip.
    price_obs(olive_oil, total_price=8.00, total_measure=500.0, unit="ml", days_ago=120)
    price_obs(olive_oil, total_price=9.00, total_measure=500.0, unit="ml", days_ago=80)
    price_obs(olive_oil, total_price=8.50, total_measure=500.0, unit="ml", days_ago=40)
    price_obs(olive_oil, total_price=12.00, total_measure=500.0, unit="ml", days_ago=3)  # spike

    # Eggs — 3 obs in ea (count dim), store-tagged.
    price_obs(eggs, total_price=7.50, total_measure=12.0, unit="ea", days_ago=30, store=woolworths)
    price_obs(eggs, total_price=8.00, total_measure=12.0, unit="ea", days_ago=14, store=coles)
    price_obs(eggs, total_price=7.50, total_measure=12.0, unit="ea", days_ago=5, store=woolworths)

    # Butter — 2 obs (below MIN_SAMPLES — drives the "not enough data" empty state).
    price_obs(butter, total_price=6.50, total_measure=250.0, unit="g", days_ago=18)
    price_obs(butter, total_price=6.80, total_measure=250.0, unit="g", days_ago=4)

    # Coffee — 1 obs (also empty-state side; lets the widget render with a single
    # current-price chip but no baseline).
    price_obs(coffee, total_price=22.00, total_measure=1.0, unit="kg", days_ago=7, store=aldi)

    # ---------------- RECIPE COLLECTIONS ---------------- #
    weeknight = RecipeCollection(name="Weeknight Dinners")
    to_try = RecipeCollection(name="To Try")
    breakfast = RecipeCollection(name="Quick Breakfasts")
    for c in (weeknight, to_try, breakfast):
        repo.add(c)

    # ---------------- RECIPE VOCABULARIES (C-4 Chunk 2) ---------------- #
    # Mirror the migration's default seed so a create_all dev DB matches a
    # migrated prod DB. Only the values the seed recipes reference are bound
    # to locals; the rest still exist so the settings editor shows a full set.
    _cuisine_names = [
        "Italian", "Asian", "Chinese", "Japanese", "Thai", "Indian",
        "Mexican", "Mediterranean", "American", "French", "Middle Eastern",
        "Other",
    ]
    cuisines = {n: Cuisine(name=n, sequence=i) for i, n in enumerate(_cuisine_names)}
    for c in cuisines.values():
        repo.add(c)

    _category_names = [
        "Main", "Pasta", "Rice", "Stir fry", "Soup", "Salad", "Side",
        "Breakfast", "Dessert", "Snack", "Drink", "Sauce",
    ]
    categories = {n: Category(name=n, sequence=i) for i, n in enumerate(_category_names)}
    for c in categories.values():
        repo.add(c)

    _dietary_tags = [
        ("Vegetarian", "Dietary pattern"), ("Vegan", "Dietary pattern"),
        ("Pescatarian", "Dietary pattern"), ("Gluten-free", "Allergen-free"),
        ("Dairy-free", "Allergen-free"), ("Nut-free", "Allergen-free"),
        ("Egg-free", "Allergen-free"), ("Soy-free", "Allergen-free"),
        ("Shellfish-free", "Allergen-free"), ("Low-carb", "Nutritional"),
        ("Low-fat", "Nutritional"), ("Low-sugar", "Nutritional"),
        ("Low-sodium", "Nutritional"), ("Keto", "Diet pattern"),
        ("Paleo", "Diet pattern"), ("Whole30", "Diet pattern"),
        ("Halal", "Religious"), ("Kosher", "Religious"),
    ]
    dietary_tags = {
        name: DietaryTag(name=name, category=cat, sequence=i)
        for i, (name, cat) in enumerate(_dietary_tags)
    }
    for t in dietary_tags.values():
        repo.add(t)

    _tool_names = [
        "Frypan", "Saucepan", "Large pot", "Baking tray", "Oven dish",
        "Mixing bowl", "Food processor", "Blender", "Stand mixer",
        "Hand mixer", "Wok", "Slow cooker", "Air fryer", "Grater",
        "Whisk", "Colander", "Rolling pin", "Knife & board",
    ]
    tools = {n: Tool(name=n, sequence=i) for i, n in enumerate(_tool_names)}
    for t in tools.values():
        repo.add(t)

    # C-2.A — household-wide meal-slot vocabulary. Mirror the migration's
    # default seed so a create_all dev/test DB matches a migrated prod DB.
    _meal_slot_names = ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"]
    for i, n in enumerate(_meal_slot_names):
        repo.add(MealSlot(name=n, sequence=i))

    # ---------------- RECIPES ---------------- #
    def ingredient(item, qty, unit, notes=None):
        ri = RecipeIngredient(notes=notes, quantity=qty, stock_item=item, unit=unit)
        repo.add(ri)
        return ri

    def make_recipe(*, name, collection, ingredients, instructions, **kw):
        recipe = Recipe(
            available_meals=kw.get("available_meals", 0),
            category=categories.get(kw["category"]) if kw.get("category") else None,
            cook_time_minutes=kw.get("cook", 20),
            cuisine=cuisines.get(kw["cuisine"]) if kw.get("cuisine") else None,
            difficulty=kw.get("difficulty", "Easy"),
            image=None,
            ingredients=ingredients,
            instructions=instructions,
            is_favourite=kw.get("favourite", False),
            last_made_on=kw.get("last_made"),
            name=name,
            nutrition=kw.get("nutrition"),
            prep_time_minutes=kw.get("prep", 10),
            recipe_collection=collection,
            servings=kw.get("servings", 2),
            source=kw.get("source"),
            time_of_day=kw.get("time_of_day", "Dinner"),
            version_group_id=None,
            kcal=kw.get("kcal"),
            steps_mode=kw.get("steps_mode", "freeform"),
            # FU-082 — seed recipes get the same now() stamp the real
            # create handlers use; the "Recently added" axis sorts them
            # by name within the same tick.
            created_at=kw.get("created_at", datetime.now(UTC)),
        )
        repo.add(recipe)
        return recipe

    # Cookable now (all ingredients well/sufficient).
    aglio = make_recipe(
        name="Spaghetti Aglio e Olio", collection=weeknight, cuisine="Italian",
        category="Pasta", favourite=True, cook=15, prep=5, servings=2,
        ingredients=[
            ingredient(pasta, 250, "g"),
            ingredient(garlic, 4, "cloves"),
            ingredient(olive_oil, 60, "ml"),
        ],
        instructions=(
            "1. Boil a large pot of salted water and cook the Barilla Pasta until al dente.\n"
            "2. Meanwhile, gently heat the Olive Oil and sliced Garlic until fragrant, about 3 minutes.\n"
            "3. Toss the drained pasta through the garlic oil and serve."
        ),
    )
    # Missing an ingredient (Parmesan is Out).
    simple_pasta = make_recipe(
        name="Tomato Pasta", collection=weeknight, cuisine="Italian", category="Pasta",
        cook=20, prep=10, servings=2, last_made=now - timedelta(days=4),
        ingredients=[
            ingredient(pasta, 250, "g"),
            ingredient(tomatoes, 1, "can"),
            ingredient(garlic, 2, "cloves"),
            ingredient(olive_oil, 30, "ml"),
            ingredient(parmesan, 30, "g", notes="to serve"),
        ],
        instructions=(
            "1. Cook the Barilla Pasta in salted boiling water.\n"
            "2. Soften the Garlic in Olive Oil, then add the Canned Tomatoes and simmer 10 minutes.\n"
            "3. Toss the pasta through the sauce and finish with grated Parmesan Cheese."
        ),
    )
    stir_fry = make_recipe(
        name="Veggie Stir Fry", collection=weeknight, cuisine="Asian", category="Stir fry",
        cook=15, prep=10, servings=3,
        ingredients=[
            ingredient(rice, 300, "g"),
            ingredient(broccoli, 1, "head"),
            ingredient(soy, 30, "ml"),
            ingredient(garlic, 2, "cloves"),
            ingredient(chicken, 400, "g"),
        ],
        instructions=(
            "1. Cook the Jasmine Rice according to packet directions.\n"
            "2. Stir-fry the Chicken Breast until golden, then add Garlic and Broccoli.\n"
            "3. Splash in the Soy Sauce, toss for 2 minutes and serve over rice."
        ),
    )
    fried_rice = make_recipe(
        name="Egg Fried Rice", collection=weeknight, cuisine="Asian", category="Rice",
        cook=15, prep=5, servings=2,
        ingredients=[
            ingredient(rice, 300, "g"),
            ingredient(eggs, 3, "whole"),
            ingredient(soy, 20, "ml"),
            ingredient(onions, 1, "whole"),
        ],
        instructions=(
            "1. Scramble the Free Range Eggs and set aside.\n"
            "2. Fry the Brown Onions, add the Jasmine Rice and Soy Sauce.\n"
            "3. Fold the egg back through and serve hot."
        ),
    )
    # Missing (Bread is Out, Parmesan is Out).
    garlic_bread = make_recipe(
        name="Cheesy Garlic Bread", collection=to_try, cuisine="Italian", category="Side",
        cook=12, prep=8, servings=4,
        ingredients=[
            ingredient(bread, 1, "loaf"),
            ingredient(butter, 50, "g"),
            ingredient(garlic, 3, "cloves"),
            ingredient(parmesan, 40, "g"),
        ],
        instructions=(
            "1. Mash the Butter with crushed Garlic.\n"
            "2. Spread over sliced Sourdough Bread and top with Parmesan Cheese.\n"
            "3. Bake at 200C for 10 minutes until golden."
        ),
    )
    icecream_bowl = make_recipe(
        name="Vanilla Ice Cream Bowl", collection=to_try, category="Dessert",
        difficulty="Easy", cook=0, prep=2, servings=1, time_of_day="Dessert",
        ingredients=[ingredient(icecream, 2, "scoops", notes="for serving")],
        instructions="1. Scoop the Vanilla Ice Cream into a bowl.\n2. Enjoy.",
    )

    # ---------------- MEAL POOL ---------------- #
    # Seed `available_meals` directly on the recipes that the plan will
    # draw from, so the dashboard "meals on hand" card and the planner
    # shortfall panel both have something to show.
    aglio.available_meals = 4
    stir_fry.available_meals = 2
    fried_rice.available_meals = 2

    # ---------------- MEAL PLAN (this week) ---------------- #
    monday = today - timedelta(days=today.weekday())

    def plan_entry(recipe, day_offset, slot, servings=2):
        entry = MealPlanEntry(
            recipe=recipe,
            scheduled_for=monday + timedelta(days=day_offset),
            servings=servings,
            slot=slot,
        )
        repo.add(entry)
        return entry

    entries = [
        plan_entry(aglio, 0, "Dinner"),
        plan_entry(fried_rice, 1, "Dinner"),
        plan_entry(aglio, 2, "Lunch", servings=1),
        # `simple_pasta` and `icecream_bowl` aren't in the pool, so the
        # planner surfaces a shortfall the user has to cook before then.
        plan_entry(simple_pasta, 3, "Dinner", servings=2),
        plan_entry(fried_rice, 4, "Dinner", servings=3),
        plan_entry(aglio, 5, "Dinner", servings=4),
    ]
    repo.add(MealPlan(name="This Week", start_date=monday, entries=entries))

    # ---------------- SHOPPING LISTS ---------------- #
    primary = ShoppingList(name="This week", created_at=now)
    in_progress = ShoppingList(
        name="Saturday shop", created_at=now - timedelta(days=1),
        status=SHOPPING_LIST_STATUS_SHOPPING,
    )
    archived = ShoppingList(
        name="Last week", created_at=now - timedelta(days=7),
        completed_at=now - timedelta(days=5), status=SHOPPING_LIST_STATUS_DONE,
    )
    # FU-227 chunk 5 — a second finished list whose priced ticked lines get
    # harvested into observations (provenance via FK). Its items overlap the
    # draft `primary` list, so those draft lines surface a "from your last
    # receipt" prefill; the rest fall back to the chosen-offer prefill.
    weekend = ShoppingList(
        name="Weekend shop", created_at=now - timedelta(days=4),
        completed_at=now - timedelta(days=3), status=SHOPPING_LIST_STATUS_DONE,
    )
    for sl in (primary, in_progress, archived, weekend):
        repo.add(sl)
    repo.save_changes()  # lines need persisted list ids

    # (line, selected_product, store) for finished priced lines, harvested into
    # observations below exactly as POST /finish would (chunk 5 closed loop).
    _harvest_jobs: list[tuple] = []

    def line(list_id, item, seq, qty=1, ticked=False, selected_product=None,
             actual_unit_price=None, purchased_store=None):
        sl_line = ShoppingListLine(
            shopping_list_id=list_id,
            stock_item_id=item.id,
            quantity=qty,
            is_ticked=ticked,
            sequence=seq,
            selected_product_id=selected_product.id if selected_product else None,
            actual_unit_price=actual_unit_price,
            purchased_store_id=purchased_store.id if purchased_store else None,
        )
        repo.add(sl_line)
        if ticked and actual_unit_price is not None:
            _harvest_jobs.append((sl_line, selected_product, purchased_store))
        return sl_line

    # Primary: a mix of low/out essentials, one with a chosen offer.
    line(primary.id, milk, 0, qty=2, selected_product=milk_coles)
    line(primary.id, parmesan, 1, selected_product=parmesan_coles)
    line(primary.id, bread, 2)
    line(primary.id, brazil, 3)
    line(primary.id, broccoli, 4)

    # In-progress: mid-shop, a couple already ticked.
    line(in_progress.id, eggs, 0, ticked=True, selected_product=eggs_woolies)
    line(in_progress.id, olive_oil, 1, selected_product=oil_aldi)
    line(in_progress.id, coffee, 2, ticked=True, selected_product=coffee_iga)

    # Archived: completed last week — now priced + harvested. A sized product
    # (pasta → measure obs in g) and two sizeless lines (count obs in ea).
    line(archived.id, pasta, 0, ticked=True, selected_product=pasta_barilla,
         actual_unit_price=1.30, purchased_store=coles)
    line(archived.id, pizza, 1, ticked=True, actual_unit_price=6.00, purchased_store=woolworths)
    line(archived.id, chips, 2, ticked=True, actual_unit_price=3.20)

    # Weekend shop: finished 3 days ago. milk is a sized product (→ measure obs
    # in L, sitting alongside its manual observations with FK provenance);
    # bread is sizeless (→ count obs). Both overlap `primary`.
    line(weekend.id, milk, 0, qty=2, ticked=True, selected_product=milk_coles,
         actual_unit_price=4.00, purchased_store=coles)
    line(weekend.id, bread, 1, ticked=True, actual_unit_price=4.40, purchased_store=woolworths)

    repo.save_changes()  # line ids needed for the harvest FK

    # Harvest one observation per finished priced line, via the same shared
    # helper the /finish handler uses (R-017 — seed exercises the new path).
    from dora_api.features.shopping_lists._line_price import (
        harvest_observation_fields, line_paid_unit_price)
    _completed_at = {archived.id: archived.completed_at, weekend.id: weekend.completed_at}
    for sl_line, product, store in _harvest_jobs:
        unit_price = line_paid_unit_price(sl_line)
        if unit_price is None:
            continue
        _tp, _tm, _unit, _pc = harvest_observation_fields(
            unit_price=unit_price,
            quantity=sl_line.quantity,
            size_value=product.size_value if product else None,
            size_unit=product.size_unit if product else None,
            product_pack_count=product.pack_count if product else None,
        )
        _at = _completed_at.get(sl_line.shopping_list_id, now)
        repo.add(StockItemPriceObservation(
            stock_item_id=sl_line.stock_item_id,
            total_price=_tp, total_measure=_tm, unit=_unit,
            observed_at=_at, store_id=(store.id if store else None),
            shopping_list_line_id=sl_line.id, created_at=_at,
            pack_count=_pc,
        ))
    repo.save_changes()

    # ---------------- SHOPPING LIST TEMPLATES ---------------- #
    staples = ShoppingListTemplate(name="Weekly staples", created_at=now, updated_at=now)
    taco = ShoppingListTemplate(name="Pantry restock", created_at=now, updated_at=now)
    repo.add(staples)
    repo.add(taco)
    repo.save_changes()

    def template_line(template_id, item, seq, qty=1):
        repo.add(ShoppingListTemplateLine(
            template_id=template_id, stock_item_id=item.id, quantity=qty, sequence=seq,
        ))

    for seq, item in enumerate((milk, eggs, bread, pasta, butter)):
        template_line(staples.id, item, seq)
    for seq, item in enumerate((rice, soy, olive_oil, garlic, tomatoes)):
        template_line(taco.id, item, seq)

    # ---------------- RECIPE DIETARY TAGS (C-4 Chunk 2) ---------------- #
    # Recipes + dietary tags both have ids by now (saved above). Write the
    # association directly — RecipeTag has no standalone entity.
    repo.save_changes()
    recipe_tag_assoc = db.metadata.tables["RecipeTag"]
    _tag_links = [
        (aglio, "Vegetarian"),
        (stir_fry, "Dairy-free"),
        (fried_rice, "Vegetarian"),
        (fried_rice, "Dairy-free"),
        (garlic_bread, "Vegetarian"),
    ]
    db.session.execute(
        recipe_tag_assoc.insert(),
        [
            {"recipe_id": recipe.id, "dietary_tag_id": dietary_tags[tag].id}
            for recipe, tag in _tag_links
        ],
    )

    # ---------------- RECIPE TOOLS (C-4 Chunk 5) ---------------- #
    recipe_tool_assoc = db.metadata.tables["RecipeTool"]
    _tool_links = [
        (aglio, "Large pot"), (aglio, "Frypan"),
        (stir_fry, "Wok"), (fried_rice, "Wok"),
        (garlic_bread, "Baking tray"), (simple_pasta, "Large pot"),
    ]
    db.session.execute(
        recipe_tool_assoc.insert(),
        [
            {"recipe_id": recipe.id, "tool_id": tools[tool].id}
            for recipe, tool in _tool_links
        ],
    )

    db.session.autoflush = True
    repo.save_changes()
