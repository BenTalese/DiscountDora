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
from datetime import date, timedelta
from typing import Any, Callable

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


_TOOLS: dict[str, Callable[[dict], list[dict]]] = {
    "search_stock": search_stock,
    "search_products": search_products,
    "search_recipes": search_recipes,
    "suggest_recipes": suggest_recipes,
}

# Where the UI should offer to navigate after answering, per tool.
_TOOL_NAV: dict[str, dict[str, str]] = {
    "search_stock": {"path": "/stock", "label": "See it on the Stock page"},
    "search_products": {"path": "/product-search", "label": "Open product search"},
    "search_recipes": {"path": "/recipes", "label": "Browse recipes"},
    "suggest_recipes": {"path": "/recipes", "label": "Browse recipes"},
}


def is_data_tool(name: str) -> bool:
    return name in _TOOLS


def run_tool(name: str, args: dict) -> list[dict]:
    """Execute a read-only tool. Raises KeyError for unknown names."""
    _Logger.info("Assistant tool '%s' args=%s", name, args)
    return _TOOLS[name](args or {})


def nav_for(name: str) -> dict[str, str] | None:
    return _TOOL_NAV.get(name)
