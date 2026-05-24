"""Read-only "lens" tools the assistant can call over Dora's data.

The model never touches the database. It picks a tool name and supplies
arguments; these deterministic Python functions run the actual query through
the repository and return compact, JSON-serialisable rows. That keeps data
access safe and testable while the model only does natural-language
understanding and phrasing.

Round 1 is read-only: stock, products and recipes. Mutating tools (shopping
list, etc.) are intentionally absent.
"""
import functools
import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Callable

from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.persistence.bool_operation import BoolOperation
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

_Logger = logging.getLogger(__name__)

# Cap rows handed back to the model. A small model's context is precious and
# the user doesn't want a wall of text — summaries beat exhaustive dumps.
_MAX_ROWS = 25

# Stock levels are ordered by ascending `sequence`; higher = less stock.
# "Low Stock" = 2, "Out of Stock" = 3 in the seed, so >= 2 means "needs
# restocking". Kept as a named constant so the intent is obvious.
_LOW_STOCK_SEQUENCE = 2

# How many days out counts as "expiring soon".
_EXPIRY_HORIZON_DAYS = 7

# An ingredient counts as "in stock" for recipe suggestions unless its stock
# level is the worst one ("Out of Stock", sequence 3). Low/Sufficient still
# count — you can usually cook with a little of something.
_OUT_OF_STOCK_SEQUENCE = 3

# Don't list every missing ingredient — a few is enough for the user to judge.
_MAX_MISSING = 5


# Native function-calling schemas (OpenAI/Ollama style). Passed to the model so
# it decides — on its own — whether a message needs data (and which tool) or
# can just be answered conversationally. Descriptions matter: they're how the
# model tells "search for products" (a data lookup) apart from "how do I search
# for products" (a how-to question it should answer directly, no tool).
TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_stock",
            "description": (
                "Look up the pantry/stock items the user is currently tracking, "
                "e.g. 'what's low?', 'do I have milk?', 'what's expiring?', "
                "'how many items do I have?'. Call with no arguments to return "
                "everything (for counting or listing). Do NOT use for questions "
                "about how to use the app."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "Specific item name(s) the user mentioned, e.g. 'milk'. Leave empty to return all items."},
                    "low_only": {"type": "boolean", "description": "Only items that are low or out of stock."},
                    "expiring_soon": {"type": "boolean", "description": "Only items expiring within a week."},
                    "flagged_only": {"type": "boolean", "description": "Only flagged/essential items."},
                    "open_only": {"type": "boolean", "description": "Only items currently opened/in use."},
                    "location_name": {"type": "string", "description": "Restrict to a storage location, e.g. 'fridge'."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search merchant products and deals (Coles, Woolworths, IGA, "
                "Aldi), e.g. 'any specials on cheese?'. Do NOT use for 'how do I "
                "search for products' — that's a how-to question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "Product name to search for."},
                    "on_special_only": {"type": "boolean", "description": "Only products currently on special."},
                    "merchant_name": {"type": "string", "description": "Restrict to a merchant, e.g. 'coles'."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_recipes",
            "description": "Find recipes by name or attributes (a direct lookup, not a recommendation).",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string"},
                    "cuisine": {"type": "string"},
                    "difficulty": {"type": "string"},
                    "max_cook_time_minutes": {"type": "integer"},
                    "favourite_only": {"type": "boolean"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_recipes",
            "description": (
                "Recommend what to cook — use for ideas, recommendations, or a "
                "mood/craving ('something spicy', 'something light', 'what can I "
                "make with what I have'). Translate moods into concrete recipe "
                "terms in keywords (e.g. light -> 'salad soup', spicy -> 'curry chilli')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "Concrete recipe terms; translate any mood into these."},
                    "cuisine": {"type": "string"},
                    "difficulty": {"type": "string"},
                    "max_cook_time_minutes": {"type": "integer"},
                    "favourite_only": {"type": "boolean"},
                    "based_on_stock": {"type": "boolean", "description": "True when the user wants ideas from what they already have in stock."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_measurement",
            "description": (
                "Convert kitchen measurements between units (volume, mass, "
                "temperature, and ingredient-aware mass↔volume for common bakers' "
                "staples — flour, sugar, butter, rice). Use when the user asks "
                "'how many ml is a cup' or '200g of flour in cups'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Numeric quantity to convert."},
                    "from_unit": {"type": "string", "description": "Source unit, e.g. 'g', 'cup', 'tbsp', 'oz', 'c', 'f'."},
                    "to_unit": {"type": "string", "description": "Target unit."},
                    "ingredient": {"type": "string", "description": "Ingredient name (only needed for mass↔volume across solids — flour, sugar, butter, rice, etc.). Omit for pure volume↔volume or mass↔mass."},
                },
                "required": ["amount", "from_unit", "to_unit"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_substitution",
            "description": (
                "Suggest ingredient substitutes (e.g. 'what can I use instead of "
                "buttermilk?'). Returns curated swap options for common pantry "
                "items. Use for cooking/recipe substitution questions only."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredient": {"type": "string", "description": "The ingredient the user wants to replace."},
                },
                "required": ["ingredient"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "whats_expiring",
            "description": (
                "List stock items expiring within a horizon (default 7 days). "
                "Use for 'what's about to go off', 'use by today', 'expiring "
                "this week', etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "within_days": {"type": "integer", "description": "Horizon in days. 0 = today only, 7 = this week. Default 7."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_deals",
            "description": (
                "Find currently-on-special merchant products, optionally filtered "
                "by keyword or merchant. Use for 'any specials right now', "
                "'cheap meat this week', 'what's on sale at Coles'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string"},
                    "merchant_name": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pantry_health",
            "description": (
                "High-level snapshot of the user's pantry: counts of total / low "
                "/ out / expiring soon / flagged items. Use for 'pantry status', "
                "'how's my pantry', 'pantry health'."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "meal_plan_for_date",
            "description": (
                "What meals are scheduled for a specific date (or range). Use for "
                "'what's for dinner tomorrow', 'what's the plan for Friday', "
                "'what am I cooking this week'. Pass `date` as ISO yyyy-mm-dd; "
                "omit for today; pass `days_ahead` to widen the window."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Anchor date (yyyy-mm-dd). Defaults to today."},
                    "days_ahead": {"type": "integer", "description": "Include this many days after the anchor. Default 0 (just the anchor day)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recipes_using_item",
            "description": (
                "Find recipes that use a specific stock item — useful for 'what "
                "can I make with these strawberries before they go off'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string", "description": "Name (or partial name) of the stock item."},
                },
                "required": ["item_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_shopping_list",
            "description": "Add one or more items to the user's shopping list, e.g. 'add 3 apples and some milk'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "The items to add.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "quantity": {"type": "integer", "description": "Omit when the user didn't give a number ('some', 'a bit of')."},
                            },
                            "required": ["name"],
                        },
                    },
                },
                "required": ["items"],
            },
        },
    },
]

# Action (mutating) tools are handled outside the read-only path: the model
# proposes them, but a deterministic resolver + an explicit commit step run the
# change. They are deliberately NOT in `_TOOLS`.
ADD_TO_SHOPPING_LIST = "add_to_shopping_list"
_ACTION_TOOLS = frozenset({ADD_TO_SHOPPING_LIST})


def is_action_tool(name: str) -> bool:
    return name in _ACTION_TOOLS


def _combine_and(conditions: list[BoolOperation]) -> BoolOperation | None:
    return functools.reduce(lambda a, b: a & b, conditions) if conditions else None


def _combine_or(conditions: list[BoolOperation]) -> BoolOperation | None:
    return functools.reduce(lambda a, b: a | b, conditions) if conditions else None


def _keyword_condition(entity: type, attribute: str, keywords: str) -> BoolOperation | None:
    tokens = [t for t in str(keywords or "").split() if t]
    if not tokens:
        return None
    return _combine_or([EntityField(entity, attribute).contains(t) for t in tokens])


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes")


def search_stock(args: dict) -> list[dict]:
    repo = SqlAlchemyRepository()
    query = (
        repo.get(StockItem)
        .include(StockItem.Fields.STOCK_LEVEL)
        .include(StockItem.Fields.STOCK_LOCATION)
        .include(StockItem.Fields.STOCK_GROUP)
    )

    conditions: list[BoolOperation] = []
    keyword_condition = _keyword_condition(StockItem, StockItem.Fields.NAME, args.get("keywords", ""))
    if keyword_condition is not None:
        conditions.append(keyword_condition)
    if _truthy(args.get("low_only")):
        conditions.append(EntityField(StockLevel, StockLevel.Fields.SEQUENCE).gte(_LOW_STOCK_SEQUENCE))
    if _truthy(args.get("expiring_soon")):
        horizon = date.today() + timedelta(days=_EXPIRY_HORIZON_DAYS)
        conditions.append(EntityField(StockItem, StockItem.Fields.EXPIRY_DATE).is_not_null())
        conditions.append(EntityField(StockItem, StockItem.Fields.EXPIRY_DATE).lte(horizon))
    if _truthy(args.get("flagged_only")):
        conditions.append(EntityField(StockItem, StockItem.Fields.IS_FLAGGED).eq(True))
    if _truthy(args.get("open_only")):
        conditions.append(EntityField(StockItem, StockItem.Fields.IS_OPEN).eq(True))
    if args.get("location_name"):
        conditions.append(EntityField(StockLocation, StockLocation.Fields.NAME).contains(str(args["location_name"])))

    items: list[StockItem] = query.all(_combine_and(conditions))
    return [
        {
            "name": item.name,
            "stock_level": item.stock_level.name if item.stock_level else None,
            "location": item.stock_location.name if item.stock_location else None,
            "group": item.stock_group.name if item.stock_group else None,
            "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
            "is_flagged": bool(item.is_flagged),
            "is_open": bool(item.is_open),
        }
        for item in items[:_MAX_ROWS]
    ]


def search_products(args: dict) -> list[dict]:
    repo = SqlAlchemyRepository()
    query = (
        repo.get(Product)
        .include(Product.Fields.MERCHANT)
        .include(Product.Fields.CURRENT_OFFER)
    )

    conditions: list[BoolOperation] = [
        EntityField(Product, Product.Fields.IS_ACTIVE).eq(True),
        EntityField(Product, Product.Fields.IS_AVAILABLE).eq(True),
    ]
    keyword_condition = _keyword_condition(Product, Product.Fields.NAME, args.get("keywords", ""))
    if keyword_condition is not None:
        conditions.append(keyword_condition)
    if args.get("merchant_name"):
        conditions.append(EntityField(Merchant, Merchant.Fields.NAME).contains(str(args["merchant_name"])))
    if _truthy(args.get("on_special_only")):
        conditions.append(
            EntityField(ProductOffer, ProductOffer.Fields.PRICE_NOW).lt(
                EntityField(ProductOffer, ProductOffer.Fields.PRICE_WAS)
            )
        )

    products: list[Product] = query.all(_combine_and(conditions))
    return [
        {
            "name": product.name,
            "brand": product.brand,
            "merchant": product.merchant.name if product.merchant else None,
            "size": product.size,
            "price_now": product.current_offer.price_now if product.current_offer else None,
            "price_was": product.current_offer.price_was if product.current_offer else None,
            "web_url": product.web_url,
        }
        for product in products[:_MAX_ROWS]
    ]


def search_recipes(args: dict) -> list[dict]:
    repo = SqlAlchemyRepository()
    query = repo.get(Recipe).include(Recipe.Fields.RECIPE_COLLECTION)

    conditions: list[BoolOperation] = []
    keyword_condition = _keyword_condition(Recipe, Recipe.Fields.NAME, args.get("keywords", ""))
    if keyword_condition is not None:
        conditions.append(keyword_condition)
    if args.get("cuisine"):
        conditions.append(EntityField(Recipe, Recipe.Fields.CUISINE).contains(str(args["cuisine"])))
    if args.get("difficulty"):
        conditions.append(EntityField(Recipe, Recipe.Fields.DIFFICULTY).contains(str(args["difficulty"])))
    if args.get("max_cook_time_minutes"):
        try:
            conditions.append(
                EntityField(Recipe, Recipe.Fields.COOK_TIME_MINUTES).lte(int(args["max_cook_time_minutes"]))
            )
        except (TypeError, ValueError):
            pass
    if _truthy(args.get("favourite_only")):
        conditions.append(EntityField(Recipe, Recipe.Fields.IS_FAVOURITE).eq(True))

    recipes: list[Recipe] = query.all(_combine_and(conditions))
    return [
        {
            "name": recipe.name,
            "cuisine": recipe.cuisine,
            "difficulty": recipe.difficulty,
            "category": recipe.category,
            "cook_time_minutes": recipe.cook_time_minutes,
            "prep_time_minutes": recipe.prep_time_minutes,
            "servings": recipe.servings,
            "is_favourite": bool(recipe.is_favourite),
        }
        for recipe in recipes[:_MAX_ROWS]
    ]


def _recipe_keyword_condition(text: str) -> BoolOperation | None:
    """Match any token against recipe name, category or cuisine — broad on
    purpose so a mood term ('salad', 'curry') surfaces relevant recipes."""
    tokens = [t for t in str(text or "").split() if t]
    if not tokens:
        return None
    clauses: list[BoolOperation] = []
    for token in tokens:
        clauses.append(EntityField(Recipe, Recipe.Fields.NAME).contains(token))
        clauses.append(EntityField(Recipe, Recipe.Fields.CATEGORY).contains(token))
        clauses.append(EntityField(Recipe, Recipe.Fields.CUISINE).contains(token))
    return _combine_or(clauses)


def _stock_coverage(recipe: Recipe) -> tuple[int, int, list[str]]:
    """Return (in_stock_count, total_ingredients, missing_names) for a recipe.
    An ingredient is missing when it has no stock item or its level is the
    worst ("Out of Stock")."""
    total = 0
    in_stock = 0
    missing: list[str] = []
    for ingredient in recipe.ingredients or []:
        total += 1
        item = ingredient.stock_item
        level = item.stock_level if item else None
        if level is not None and level.sequence < _OUT_OF_STOCK_SEQUENCE:
            in_stock += 1
        elif item is not None:
            missing.append(item.name)
    return in_stock, total, missing[:_MAX_MISSING]


def suggest_recipes(args: dict) -> list[dict]:
    repo = SqlAlchemyRepository()
    query = (
        repo.get(Recipe)
        .include(Recipe.Fields.INGREDIENTS)
        .then_include(RecipeIngredient.Fields.STOCK_ITEM)
        .then_include(StockItem.Fields.STOCK_LEVEL)
    )

    conditions: list[BoolOperation] = []
    keyword_condition = _recipe_keyword_condition(args.get("keywords", ""))
    if keyword_condition is not None:
        conditions.append(keyword_condition)
    if args.get("cuisine"):
        conditions.append(EntityField(Recipe, Recipe.Fields.CUISINE).contains(str(args["cuisine"])))
    if args.get("difficulty"):
        conditions.append(EntityField(Recipe, Recipe.Fields.DIFFICULTY).contains(str(args["difficulty"])))
    if args.get("max_cook_time_minutes"):
        try:
            conditions.append(
                EntityField(Recipe, Recipe.Fields.COOK_TIME_MINUTES).lte(int(args["max_cook_time_minutes"]))
            )
        except (TypeError, ValueError):
            pass
    if _truthy(args.get("favourite_only")):
        conditions.append(EntityField(Recipe, Recipe.Fields.IS_FAVOURITE).eq(True))

    recipes: list[Recipe] = query.all(_combine_and(conditions))
    based_on_stock = _truthy(args.get("based_on_stock"))

    rows: list[dict] = []
    for recipe in recipes:
        in_stock, total, missing = _stock_coverage(recipe)
        coverage = (in_stock / total) if total else 0.0
        rows.append({
            "name": recipe.name,
            "cuisine": recipe.cuisine,
            "difficulty": recipe.difficulty,
            "cook_time_minutes": recipe.cook_time_minutes,
            "servings": recipe.servings,
            "is_favourite": bool(recipe.is_favourite),
            "total_ingredients": total,
            "in_stock_count": in_stock,
            "can_make_now": total > 0 and in_stock == total,
            "missing_ingredients": missing,
            "_coverage": coverage,
        })

    if based_on_stock:
        # Best-stocked first, can-make-now ahead of partials, favourites break ties.
        rows.sort(key=lambda r: (r["can_make_now"], r["_coverage"], r["is_favourite"]), reverse=True)
    else:
        rows.sort(key=lambda r: (r["is_favourite"], r["_coverage"]), reverse=True)

    # Drop the internal sort key before handing rows to the model.
    trimmed = rows[:_MAX_ROWS]
    for row in trimmed:
        row.pop("_coverage", None)
    return trimmed


# ─────────────────────────────────────────────────────────────────────────
# Stage 2 tools
# ─────────────────────────────────────────────────────────────────────────

# ── Unit conversion ──────────────────────────────────────────────────────
# Two layers: simple linear conversions within a single dimension (volume /
# mass / temperature), and ingredient-aware mass↔volume for the common
# bakers' staples whose density we know. Reproduces the frontend table for
# parity, with extra ingredient densities the rule engine doesn't have.

# AU-metric defaults (250ml cup, 20ml tbsp) — that's the convention in this app.
_UNIT_TABLE: dict[str, tuple[str, float, float]] = {
    # name → (dimension, to_base, _unused) — to_base converts a value in this
    # unit to the base unit of its dimension. Linear units only (temp handled
    # separately because of the offset).
    "ml": ("volume", 1.0, 0.0), "milliliter": ("volume", 1.0, 0.0), "millilitre": ("volume", 1.0, 0.0),
    "l": ("volume", 1000.0, 0.0), "liter": ("volume", 1000.0, 0.0), "litre": ("volume", 1000.0, 0.0),
    "tsp": ("volume", 5.0, 0.0), "teaspoon": ("volume", 5.0, 0.0),
    "tbsp": ("volume", 20.0, 0.0), "tablespoon": ("volume", 20.0, 0.0),  # AU metric
    "cup": ("volume", 250.0, 0.0), "cups": ("volume", 250.0, 0.0),       # AU metric
    "fl oz": ("volume", 29.5735, 0.0), "floz": ("volume", 29.5735, 0.0),
    "pint": ("volume", 568.261, 0.0), "pt": ("volume", 568.261, 0.0),    # UK
    "quart": ("volume", 946.353, 0.0), "qt": ("volume", 946.353, 0.0),   # US
    "gallon": ("volume", 3785.41, 0.0), "gal": ("volume", 3785.41, 0.0),

    "g": ("mass", 1.0, 0.0), "gram": ("mass", 1.0, 0.0), "grams": ("mass", 1.0, 0.0),
    "kg": ("mass", 1000.0, 0.0), "kilo": ("mass", 1000.0, 0.0), "kilos": ("mass", 1000.0, 0.0), "kilogram": ("mass", 1000.0, 0.0),
    "oz": ("mass", 28.3495, 0.0), "ounce": ("mass", 28.3495, 0.0), "ounces": ("mass", 28.3495, 0.0),
    "lb": ("mass", 453.592, 0.0), "lbs": ("mass", 453.592, 0.0), "pound": ("mass", 453.592, 0.0),
    "stick": ("mass", 113.0, 0.0), "sticks": ("mass", 113.0, 0.0),  # butter
}

# Grams per millilitre. Lets us cross mass↔volume for ingredients whose
# density is well-known. Sourced from common bakers' references.
_INGREDIENT_DENSITY_G_PER_ML: dict[str, float] = {
    "water": 1.00,
    "milk": 1.03,
    "flour": 0.53,
    "plain flour": 0.53, "all-purpose flour": 0.53, "all purpose flour": 0.53,
    "self-raising flour": 0.53, "self raising flour": 0.53,
    "sugar": 0.85, "white sugar": 0.85, "caster sugar": 0.85,
    "brown sugar": 0.93,
    "icing sugar": 0.56, "powdered sugar": 0.56,
    "butter": 0.91,
    "honey": 1.42, "maple syrup": 1.32, "golden syrup": 1.40,
    "rice": 0.78, "white rice": 0.78, "brown rice": 0.76,
    "rolled oats": 0.41, "oats": 0.41,
    "cocoa powder": 0.51, "cocoa": 0.51,
    "salt": 1.20,
    "olive oil": 0.92, "oil": 0.92, "vegetable oil": 0.92,
}


def _normalise_unit(unit: str) -> str:
    return unit.strip().lower().replace("°", "")


def convert_measurement(args: dict) -> list[dict]:
    try:
        amount = float(args.get("amount"))
    except (TypeError, ValueError):
        return [{"error": "amount must be a number"}]
    from_unit = _normalise_unit(str(args.get("from_unit") or ""))
    to_unit = _normalise_unit(str(args.get("to_unit") or ""))
    ingredient = (args.get("ingredient") or "").strip().lower() or None

    # Temperature first — offsets, can't share the linear table.
    temp_units = {"c", "celsius", "celcius", "f", "fahrenheit", "k", "kelvin"}
    if from_unit in temp_units or to_unit in temp_units:
        if from_unit not in temp_units or to_unit not in temp_units:
            return [{"error": f"can't convert {from_unit} to {to_unit} — temperature must convert to temperature"}]
        def to_c(v: float, u: str) -> float:
            if u in ("c", "celsius", "celcius"): return v
            if u in ("f", "fahrenheit"): return (v - 32) * 5 / 9
            return v - 273.15  # kelvin
        def from_c(v: float, u: str) -> float:
            if u in ("c", "celsius", "celcius"): return v
            if u in ("f", "fahrenheit"): return v * 9 / 5 + 32
            return v + 273.15
        result = from_c(to_c(amount, from_unit), to_unit)
        return [{"amount": amount, "from_unit": from_unit, "to_unit": to_unit, "result": round(result, 1)}]

    src = _UNIT_TABLE.get(from_unit)
    dst = _UNIT_TABLE.get(to_unit)
    if not src or not dst:
        return [{"error": f"unknown unit(s): {from_unit!r} or {to_unit!r}"}]
    src_dim, src_factor, _ = src
    dst_dim, dst_factor, _ = dst

    # Same dimension: straight linear conversion.
    if src_dim == dst_dim:
        result = amount * src_factor / dst_factor
        return [{"amount": amount, "from_unit": from_unit, "to_unit": to_unit, "result": round(result, 3)}]

    # Cross-dimension mass↔volume needs an ingredient density.
    if {src_dim, dst_dim} == {"mass", "volume"}:
        density = _INGREDIENT_DENSITY_G_PER_ML.get(ingredient) if ingredient else None
        if density is None:
            return [{
                "error": f"need an ingredient to convert {from_unit} to {to_unit} (mass↔volume depends on density)",
                "known_ingredients": sorted(set(_INGREDIENT_DENSITY_G_PER_ML.keys())),
            }]
        # Convert source to base units of its dimension.
        base = amount * src_factor
        if src_dim == "mass":  # base is grams → convert to ml using density
            ml = base / density
            result = ml / dst_factor
        else:  # source is volume → grams via density
            grams = base * density
            result = grams / dst_factor
        return [{
            "amount": amount, "from_unit": from_unit, "to_unit": to_unit,
            "ingredient": ingredient, "density_g_per_ml": density,
            "result": round(result, 3),
        }]

    return [{"error": f"can't convert {src_dim} to {dst_dim}"}]


# ── Substitution table ───────────────────────────────────────────────────
# Same data the rule-engine fallback uses, plus a few extras the AI can lean
# on. Keyed by canonical lowercase singular name.

_SUBSTITUTES: dict[str, list[str]] = {
    "butter": ["margarine (1:1)", "oil (¾ the amount)", "applesauce (baking, 1:1, reduces fat)", "greek yogurt (baking, 1:1)"],
    "milk": ["oat milk", "almond milk", "soy milk", "evaporated milk diluted 1:1 with water", "powdered milk + water"],
    "egg": ["1 tbsp flaxseed + 3 tbsp water (let it gel)", "1/4 cup mashed banana (sweet bakes)", "1/4 cup applesauce", "1/4 cup silken tofu (blended)"],
    "sour cream": ["greek yogurt (1:1)", "creme fraiche", "cottage cheese (blended)"],
    "buttermilk": ["1 cup milk + 1 tbsp lemon juice or vinegar, sit 5 min", "plain yogurt thinned with milk"],
    "self-raising flour": ["1 cup plain flour + 1.5 tsp baking powder + a pinch of salt"],
    "baking powder": ["1/4 tsp bicarb + 1/2 tsp cream of tartar per 1 tsp"],
    "breadcrumbs": ["crushed cornflakes", "rolled oats (pulsed)", "crushed crackers", "panko"],
    "garlic": ["1/2 tsp garlic powder per clove", "a pinch of asafoetida"],
    "onion": ["1 tbsp dried onion flakes per 1/4 cup fresh", "leek (white part)", "shallots"],
    "cornstarch": ["plain flour (2:1)", "arrowroot (1:1)", "rice flour"],
    "white wine": ["apple juice", "white grape juice", "chicken broth + a splash of white vinegar"],
    "red wine": ["cranberry juice", "beef broth + a splash of balsamic", "pomegranate juice"],
    "lemon juice": ["lime juice (1:1)", "white vinegar (use 1/2 the amount)"],
    "brown sugar": ["1 cup white sugar + 1 tbsp molasses"],
    "honey": ["maple syrup (1:1)", "agave (1:1)", "golden syrup"],
    "vanilla extract": ["maple syrup (1:1, mellower)", "almond extract (1/2 the amount, stronger)"],
    "heavy cream": ["3/4 cup milk + 1/4 cup melted butter", "evaporated milk (won't whip)", "coconut cream"],
    "cream cheese": ["ricotta (smoother spread)", "mascarpone", "greek yogurt + a knob of butter"],
    "yeast": ["1.25x the amount of active dry if you have instant", "sourdough starter (adjust hydration)"],
    "parmesan": ["pecorino", "grana padano", "aged gouda"],
    "soy sauce": ["tamari (gf)", "coconut aminos", "Worcestershire (less salty, sweeter)"],
    "tomato paste": ["3 tbsp tomato sauce reduced", "ketchup (sweeter)"],
    "fish sauce": ["soy sauce + a squeeze of lime", "Worcestershire (different flavour)"],
    "coriander leaves": ["parsley + a pinch of lime zest"],
    "ricotta": ["cottage cheese (blended)", "greek yogurt strained"],
}

_SUBSTITUTE_ALIASES: dict[str, str] = {
    "eggs": "egg", "creme fraiche": "sour cream", "self raising flour": "self-raising flour",
    "sr flour": "self-raising flour", "parm": "parmesan", "parmigiano": "parmesan",
    "spring onion": "onion", "scallion": "onion", "shallot": "onion",
    "cilantro": "coriander leaves", "coriander": "coriander leaves",
    "passata": "tomato paste",
}


def suggest_substitution(args: dict) -> list[dict]:
    raw = str(args.get("ingredient") or "").strip().lower()
    if not raw:
        return [{"error": "ingredient is required"}]
    # Strip filler words and trailing 's' before lookup.
    cleaned = re.sub(r"^(some|any|a|an)\s+", "", raw).rstrip("s")
    if cleaned not in _SUBSTITUTES:
        cleaned_plural = cleaned + "s"
        canonical = _SUBSTITUTE_ALIASES.get(cleaned) or _SUBSTITUTE_ALIASES.get(cleaned_plural) or _SUBSTITUTE_ALIASES.get(raw)
        if canonical:
            cleaned = canonical
    options = _SUBSTITUTES.get(cleaned)
    if not options:
        return [{"ingredient": raw, "options": [], "note": "no curated substitute on file"}]
    return [{"ingredient": cleaned, "options": options}]


# ── Expiring lookup ──────────────────────────────────────────────────────

def whats_expiring(args: dict) -> list[dict]:
    repo = SqlAlchemyRepository()
    try:
        horizon_days = int(args.get("within_days", _EXPIRY_HORIZON_DAYS))
    except (TypeError, ValueError):
        horizon_days = _EXPIRY_HORIZON_DAYS
    cutoff = date.today() + timedelta(days=max(0, horizon_days))
    query = (
        repo.get(StockItem)
        .include(StockItem.Fields.STOCK_LEVEL)
        .include(StockItem.Fields.STOCK_LOCATION)
    )
    conditions = [
        EntityField(StockItem, StockItem.Fields.EXPIRY_DATE).is_not_null(),
        EntityField(StockItem, StockItem.Fields.EXPIRY_DATE).lte(cutoff),
    ]
    items: list[StockItem] = query.all(_combine_and(conditions))
    today = date.today()
    rows = []
    for item in items:
        if not item.expiry_date:
            continue
        days = (item.expiry_date - today).days
        rows.append({
            "name": item.name,
            "expiry_date": item.expiry_date.isoformat(),
            "days_until_expiry": days,
            "is_expired": days < 0,
            "location": item.stock_location.name if item.stock_location else None,
            "stock_level": item.stock_level.name if item.stock_level else None,
        })
    rows.sort(key=lambda r: r["days_until_expiry"])
    return rows[:_MAX_ROWS]


# ── Deals (specials) ─────────────────────────────────────────────────────

def find_deals(args: dict) -> list[dict]:
    repo = SqlAlchemyRepository()
    query = (
        repo.get(Product)
        .include(Product.Fields.MERCHANT)
        .include(Product.Fields.CURRENT_OFFER)
    )
    conditions: list[BoolOperation] = [
        EntityField(Product, Product.Fields.IS_ACTIVE).eq(True),
        EntityField(Product, Product.Fields.IS_AVAILABLE).eq(True),
        # On special = price_now < price_was (existing convention).
        EntityField(ProductOffer, ProductOffer.Fields.PRICE_NOW).lt(
            EntityField(ProductOffer, ProductOffer.Fields.PRICE_WAS)
        ),
    ]
    keyword_condition = _keyword_condition(Product, Product.Fields.NAME, args.get("keywords", ""))
    if keyword_condition is not None:
        conditions.append(keyword_condition)
    if args.get("merchant_name"):
        conditions.append(EntityField(Merchant, Merchant.Fields.NAME).contains(str(args["merchant_name"])))

    products: list[Product] = query.all(_combine_and(conditions))
    rows = []
    for product in products:
        offer = product.current_offer
        if not offer or offer.price_now is None or offer.price_was is None:
            continue
        savings = round(offer.price_was - offer.price_now, 2)
        rows.append({
            "name": product.name,
            "brand": product.brand,
            "merchant": product.merchant.name if product.merchant else None,
            "size": product.size,
            "price_now": offer.price_now,
            "price_was": offer.price_was,
            "savings": savings,
            "savings_percent": round((savings / offer.price_was) * 100, 0) if offer.price_was else 0,
            "web_url": product.web_url,
        })
    # Biggest % discount first — that's what "deals" usually means.
    rows.sort(key=lambda r: r["savings_percent"], reverse=True)
    return rows[:_MAX_ROWS]


# ── Pantry health snapshot ───────────────────────────────────────────────

def pantry_health(_args: dict) -> list[dict]:
    repo = SqlAlchemyRepository()
    items: list[StockItem] = (
        repo.get(StockItem).include(StockItem.Fields.STOCK_LEVEL).all()
    )
    total = len(items)
    low = sum(1 for i in items if i.stock_level and i.stock_level.sequence >= _LOW_STOCK_SEQUENCE)
    out = sum(1 for i in items if i.stock_level and i.stock_level.sequence >= _OUT_OF_STOCK_SEQUENCE)
    flagged = sum(1 for i in items if i.is_flagged)
    open_items = sum(1 for i in items if i.is_open)
    horizon = date.today() + timedelta(days=_EXPIRY_HORIZON_DAYS)
    expiring_soon = sum(
        1 for i in items
        if i.expiry_date and i.expiry_date <= horizon and i.expiry_date >= date.today()
    )
    expired = sum(1 for i in items if i.expiry_date and i.expiry_date < date.today())
    return [{
        "total_items": total,
        "low_count": low,
        "out_count": out,
        "flagged_count": flagged,
        "open_count": open_items,
        "expiring_within_week": expiring_soon,
        "expired_count": expired,
    }]


# ── Meal plan lookup ─────────────────────────────────────────────────────

def meal_plan_for_date(args: dict) -> list[dict]:
    repo = SqlAlchemyRepository()
    anchor_str = (args.get("date") or "").strip()
    try:
        anchor = datetime.strptime(anchor_str, "%Y-%m-%d").date() if anchor_str else date.today()
    except ValueError:
        anchor = date.today()
    try:
        days_ahead = max(0, int(args.get("days_ahead", 0)))
    except (TypeError, ValueError):
        days_ahead = 0
    end = anchor + timedelta(days=days_ahead)

    query = repo.get(MealPlanEntry).include(MealPlanEntry.Fields.MEAL)
    conditions = [
        EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR).gte(anchor),
        EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR).lte(end),
    ]
    entries: list[MealPlanEntry] = query.all(_combine_and(conditions))
    entries.sort(key=lambda e: (e.scheduled_for, e.slot or ""))
    return [
        {
            "date": entry.scheduled_for.isoformat(),
            "slot": entry.slot,
            "meal_name": entry.meal.name if entry.meal else None,
            "servings": entry.servings,
        }
        for entry in entries[:_MAX_ROWS]
    ]


# ── Reverse lookup: recipes using a stock item ───────────────────────────

def recipes_using_item(args: dict) -> list[dict]:
    name = str(args.get("item_name") or "").strip()
    if not name:
        return [{"error": "item_name is required"}]
    repo = SqlAlchemyRepository()
    # Find candidate stock items by name (exact then substring).
    candidates: list[StockItem] = repo.get(StockItem).all(
        EntityField(StockItem, StockItem.Fields.NAME).eq(name)
    )
    if not candidates:
        candidates = repo.get(StockItem).all(
            EntityField(StockItem, StockItem.Fields.NAME).contains(name)
        )
    if not candidates:
        return [{"item_name": name, "recipes": []}]

    item_ids = {str(c.id) for c in candidates}
    # Walk recipes and find any whose ingredients reference one of the candidates.
    recipes: list[Recipe] = (
        repo.get(Recipe)
        .include(Recipe.Fields.INGREDIENTS)
        .then_include(RecipeIngredient.Fields.STOCK_ITEM)
        .all()
    )
    matches: list[dict] = []
    for recipe in recipes:
        used = any(
            ing.stock_item and str(ing.stock_item.id) in item_ids
            for ing in (recipe.ingredients or [])
        )
        if used:
            matches.append({
                "name": recipe.name,
                "cuisine": recipe.cuisine,
                "difficulty": recipe.difficulty,
                "cook_time_minutes": recipe.cook_time_minutes,
                "is_favourite": bool(recipe.is_favourite),
            })
    matches.sort(key=lambda r: (not r["is_favourite"], r["name"]))
    return matches[:_MAX_ROWS]


_TOOLS: dict[str, Callable[[dict], list[dict]]] = {
    "search_stock": search_stock,
    "search_products": search_products,
    "search_recipes": search_recipes,
    "suggest_recipes": suggest_recipes,
    "convert_measurement": convert_measurement,
    "suggest_substitution": suggest_substitution,
    "whats_expiring": whats_expiring,
    "find_deals": find_deals,
    "pantry_health": pantry_health,
    "meal_plan_for_date": meal_plan_for_date,
    "recipes_using_item": recipes_using_item,
}

# Where the UI should offer to navigate after answering, per tool.
_TOOL_NAV: dict[str, dict[str, str]] = {
    "search_stock": {"path": "/stock", "label": "See it on the Stock page"},
    "search_products": {"path": "/product-search", "label": "Open product search"},
    "search_recipes": {"path": "/recipes", "label": "Browse recipes"},
    "suggest_recipes": {"path": "/recipes", "label": "Browse recipes"},
    "whats_expiring": {"path": "/stock", "label": "See it on the Stock page"},
    "find_deals": {"path": "/product-search", "label": "Open product search"},
    "pantry_health": {"path": "/stock", "label": "Open Stock"},
    "meal_plan_for_date": {"path": "/meal-plans", "label": "Open Meal Plans"},
    "recipes_using_item": {"path": "/recipes", "label": "Browse recipes"},
    # convert_measurement / suggest_substitution don't need navigation.
}


def is_data_tool(name: str) -> bool:
    return name in _TOOLS


def run_tool(name: str, args: dict) -> list[dict]:
    """Execute a read-only tool. Raises KeyError for unknown names."""
    _Logger.info("Assistant tool '%s' args=%s", name, args)
    return _TOOLS[name](args or {})


def nav_for(name: str) -> dict[str, str] | None:
    return _TOOL_NAV.get(name)
