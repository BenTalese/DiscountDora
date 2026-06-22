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
import statistics
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any, Callable
from uuid import UUID

from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.store import Store
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.shopping_list import (
    SHOPPING_LIST_STATUS_DONE, ShoppingList, ShoppingListLine)
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
# C-9.2 note: the assistant reads the EXPIRING_SOON_WINDOW_DAYS *default* (not
# the admin-configured AppSetting.expiring_soon_window_days that alerts + the
# heatmap now honour). This is the constant-as-default carve-out allowed by
# IMPL_PLAN_ALERTS C-9.2; threading the override through here is deferred
# (DORA_FOLLOWUPS FU-187). It's the one default, not a second literal (R-003).
from dora_api.domain.stock_status import (EXPIRING_SOON_WINDOW_DAYS,
                                          LOW_STOCK_SEQUENCE, is_out_of_stock,
                                          needs_restock)
from dora_api.features.alerts.get_alerts import GetAlertsHandler
from dora_api.features.shopping_lists._line_price import line_paid_unit_price
from dora_api.persistence.bool_operation import BoolOperation
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

_Logger = logging.getLogger(__name__)

# Cap rows handed back to the model. A small model's context is precious and
# the user doesn't want a wall of text — summaries beat exhaustive dumps.
_MAX_ROWS = 25

# When a name lookup finds multiple matches, we don't drown the user (or
# the model) in options. Above this we say "be more specific" rather than
# listing everything. Mirrors the shopping_actions threshold.
_MAX_CANDIDATES = 6

# Stock-status thresholds and predicates are owned by domain/stock_status.py
# (LOW_STOCK_SEQUENCE, is_out_of_stock, needs_restock). An ingredient counts as
# "in stock" for recipe suggestions unless it's out of stock — low/sufficient
# still count, since you can usually cook with a little of something.

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
                    "store_name": {"type": "string", "description": "Restrict to a merchant, e.g. 'coles'."},
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
                "terms in keywords (e.g. light -> 'salad soup', spicy -> 'curry chilli'). "
                "Dietary asks like 'vegan dinner', 'gluten-free pasta', or 'free "
                "from egg' map onto the tag/ingredient filter arguments — not "
                "keywords. Tags reflect what the recipe was tagged with by the "
                "user, not a safety guarantee."
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
                    "tags_include": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Recipe must carry ALL of these dietary tags. The "
                            "vocabulary is user-configurable; defaults include "
                            "Vegetarian, Vegan, Pescatarian, Gluten-free, "
                            "Dairy-free, Nut-free, Egg-free, Soy-free, "
                            "Shellfish-free, Low-carb, Low-fat, Low-sugar, "
                            "Low-sodium, Keto, Paleo, Whole30, Halal, Kosher. "
                            "Match by tag name (case-insensitive)."
                        ),
                    },
                    "tags_exclude": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Recipe must carry NONE of these tags. Same vocabulary as tags_include.",
                    },
                    "ingredient_exclude": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Recipe must not have an ingredient whose stock-item "
                            "name contains any of these substrings (case-"
                            "insensitive). Use for 'free from egg', 'without "
                            "mushrooms', etc."
                        ),
                    },
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
                "Convert kitchen measurements across five dimensions: volume, "
                "mass, temperature, length (cake-pan sizing), and energy "
                "(kJ/kcal). Also ingredient-aware mass↔volume for ~40 bakers' "
                "staples (flour, sugars, butter, rice, oats, chocolate chips, "
                "nuts, etc.). Supports pinch / dash / smidgen, US cup vs AU "
                "cup, °C / °F / K / gas mark, inches / cm, and fraction "
                "amounts like '1/2' or '1 1/2'. Use for any kitchen "
                "conversion question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "string", "description": "Quantity to convert — accepts integers, decimals, fractions ('1/2'), or mixed ('1 1/2')."},
                    "from_unit": {"type": "string", "description": "Source unit. e.g. 'g', 'cup', 'us cup', 'tbsp', 'oz', 'c', 'f', 'gas mark', 'inch', 'cm', 'kj', 'kcal', 'pinch', 'dash'."},
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
                    "store_name": {"type": "string"},
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
            "name": "meals_in_pool",
            "description": (
                "List recipes that have cooked-and-ready meals in the pool, "
                "biggest stash first. Use for 'what's in the freezer', "
                "'what cooked meals do I have', 'what's left from Sunday's "
                "batch cook'. No arguments."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "meals_shortfall",
            "description": (
                "Recipes where planned servings exceed the pool — i.e. what "
                "the user still needs to cook before those days arrive. Use "
                "for 'what do I need to cook', 'what's the week short on', "
                "'what should I batch-cook next'. No arguments."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
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
            "name": "get_alerts",
            "description": (
                "Return the things needing the user's attention right now — "
                "the same data behind the bell icon. Use for 'what needs "
                "attention', 'anything urgent', 'what's wrong'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "description": "Filter by severity: 'high', 'medium', or 'low'. Omit for all."},
                    "kind": {"type": "string", "description": "Filter by kind: 'expired', 'expiring_soon', 'out_of_stock', 'low_stock', 'stocktake_overdue', 'essential_low'. Omit for all."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stock_item_detail",
            "description": (
                "Detailed snapshot of one stock item — level, location, expiry, "
                "flagged/open state, last stocktake, recipes that use it, "
                "whether it's on a shopping list. Use for 'tell me about my "
                "milk', 'how's the cheese looking'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Item name (or partial)."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recipe_detail",
            "description": (
                "Detailed snapshot of one recipe — ingredients with their "
                "in-stock status, cook time, difficulty, an instructions preview. "
                "Use for 'tell me about carbonara', 'how do I make pad thai', "
                "'what's in lasagne'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Recipe name (or partial)."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "shopping_list_contents",
            "description": (
                "List the lines on a shopping list — what's on it, ticked vs "
                "outstanding, with stock-level context. Use for 'what's on my "
                "list', 'what do I still need at woolies'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "List name (or partial). Omit to use the primary list."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "meal_detail",
            "description": (
                "Detailed snapshot of one meal — the constituent recipes and "
                "their cook times. Use for 'what's in the Sunday roast meal', "
                "'tell me about my taco night meal'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Meal name (or partial)."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_location",
            "description": (
                "Look up a storage location and what's in it. Use for 'what's "
                "in the fridge', 'anything urgent in the pantry', 'list the "
                "items in zone 3'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Location name (or partial), e.g. 'fridge', 'pantry', 'zone 3'."},
                    "urgent_only": {"type": "boolean", "description": "Only return items needing attention (low/out/expired/expiring) at this location."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_stock_level",
            "description": (
                "Change the stock level of an item — use when the user reports "
                "consuming, restocking, or otherwise re-evaluating an item's "
                "stock (e.g. 'I just used the last milk', 'mark eggs as low', "
                "'cheese is fully stocked again'). Levels include 'out', 'low', "
                "'sufficient', 'well stocked'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string"},
                    "level": {"type": "string", "description": "'out', 'low', 'sufficient', 'well stocked' (or aliases)."},
                },
                "required": ["item_name", "level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mark_opened",
            "description": (
                "Mark a stock item as opened (start of its in-use countdown). "
                "Set closed=true to mark it closed/unopened again."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string"},
                    "closed": {"type": "boolean", "description": "Set true to mark it closed (unopen) instead."},
                },
                "required": ["item_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "push_expiry",
            "description": (
                "Shift an item's expiry date by a number of days (positive to "
                "push it back, negative to bring it forward). Use for 'push "
                "bread by 3 days', 'add a week to the milk expiry'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string"},
                    "days": {"type": "integer"},
                },
                "required": ["item_name", "days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tick_shopping_line",
            "description": (
                "Tick (mark complete) a line on the primary shopping list. Set "
                "untick=true to un-tick. Use for 'cross off bread', 'I got the "
                "milk', 'I haven't actually got the eggs yet'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string"},
                    "untick": {"type": "boolean", "description": "Set true to un-tick instead of ticking."},
                },
                "required": ["item_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "seasonal_picks",
            "description": (
                "What produce is in season in Australia right now (or for a "
                "named month). Curated table covering common fruit and veg. "
                "Use for 'what's in season', 'what should I be buying this "
                "month', 'seasonal produce'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "Optional month name (e.g. 'march') or number 1-12. Defaults to the current month."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_suggestions",
            "description": (
                "Dora's current proposals for this user — generated from "
                "pantry, budget, purchase cadence, and waste data. Use "
                "for 'what do you suggest?', 'anything I should do?', "
                "'review your suggestions'. Each item has a `kind` "
                "(use_soon / over_budget / likely_due / frequent_waster), "
                "a plain-English reason, and an optional `primary_action` "
                "the SPA can route the user to. Suggestions the user has "
                "dismissed or snoozed are pre-filtered out."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "expiry_rescue",
            "description": (
                "What's about to spoil, and which recipes would use the "
                "most of it. Use for 'what should I use before it goes "
                "off?', 'help me not waste food this week', 'what's a "
                "good recipe for stuff that's expiring?'. Ranks recipes "
                "by how many at-risk items they'd use, so the suggestion "
                "is actionable, not just 'cook anything'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "horizon_days": {"type": "integer", "description": "Days ahead to consider. Default 7."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "waste_insights",
            "description": (
                "How often the user has been throwing food out, by item — "
                "use for 'what am I wasting often?', 'what should I stop "
                "buying?', 'where am I losing money?'. Sourced from "
                "voluntary 'Log as wasted' taps on the Waste page; will "
                "report no data when the user hasn't logged anything."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "window_days": {"type": "integer", "description": "Look-back window in days. Default 90."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "budget_status",
            "description": (
                "Show the user's current grocery budget status across all "
                "their shopping lists — spent this week/month, remaining, "
                "and whether they're tracking over or under. Returns "
                "`enabled=false` when the user hasn't opted in to budget "
                "tracking; the assistant should then point them at "
                "Settings → Preferences. Use for 'what's left in my "
                "budget?', 'how much have I spent this week?', 'am I over "
                "budget?'."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "purchase_price_stats",
            "description": (
                "Purchase history for a stock item across the user's "
                "finished shopping lists — price stats (average / min / "
                "max / last paid, per-merchant breakdown) AND cadence "
                "stats (how often they buy it, usual quantity, usual "
                "merchant, days since last purchase). Use for 'what's the "
                "average price for broccoli?', 'how much do I usually pay "
                "for milk?', 'how often do I buy bread?', 'when did I last "
                "buy eggs?', 'where do I usually shop for cheese?'. "
                "Prefers the user-entered actual price; falls back to the "
                "offer price snapshotted when the line was ticked."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string", "description": "Stock item name (or partial)."},
                },
                "required": ["item_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_prices",
            "description": (
                "Compare prices for a stock item across the merchant products "
                "linked to it. Use for 'where's milk cheapest right now', "
                "'best price on cheese'. Only works for stock items that "
                "have linked products."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string"},
                },
                "required": ["item_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recipe_for_occasion",
            "description": (
                "Suggest recipes that fit an occasion / vibe (kid-friendly, "
                "date night, guests, comfort food, quick weeknight, healthy, "
                "fancy, party). Translates the occasion into concrete recipe "
                "filters and ranks by stock coverage so you get suggestions "
                "you can actually cook."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "occasion": {"type": "string", "description": "Free-form occasion / vibe phrase."},
                },
                "required": ["occasion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_item",
            "description": (
                "Move a stock item to a different storage location. Use for "
                "'move the cheese to the fridge', 'put the rice in the pantry'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string"},
                    "destination": {"type": "string", "description": "Location name (or partial), e.g. 'fridge', 'pantry'."},
                },
                "required": ["item_name", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_primary_list",
            "description": (
                "Make a named shopping list the primary one (the default target "
                "for new additions). Use for 'make Groceries the primary list', "
                "'switch primary to Aldi run'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plan_meal_for_date",
            "description": (
                "Add a meal to the meal plan for a specific date and slot. "
                "Use for 'plan carbonara for Friday dinner', 'put taco night "
                "on Tuesday'. Requires `date` as yyyy-mm-dd."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "meal_name": {"type": "string"},
                    "date": {"type": "string", "description": "yyyy-mm-dd"},
                    "slot": {"type": "string", "description": "'Breakfast', 'Lunch', 'Dinner'. Defaults to Dinner."},
                    "servings": {"type": "integer", "description": "Default 1."},
                },
                "required": ["meal_name", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_recipe_to_list",
            "description": (
                "Add a recipe's ingredients to the primary shopping list. "
                "Defaults to the recipe's MISSING ingredients (anything Out of "
                "Stock or untracked); set missing_only=false to add all "
                "ingredients regardless of stock."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_name": {"type": "string"},
                    "missing_only": {"type": "boolean", "description": "Default true."},
                },
                "required": ["recipe_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cook_recipe",
            "description": (
                "Log that the user has just cooked a recipe — adds the "
                "given number of meals to that recipe's pool. Use for "
                "'I cooked 3 lasagnes', 'just batch-cooked fried rice', "
                "'made two more portions'. Defaults to 1 if the user "
                "doesn't say a number."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_name": {"type": "string"},
                    "meals_cooked": {
                        "type": "integer",
                        "description": "How many portions were cooked. Default 1.",
                    },
                },
                "required": ["recipe_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_recipe_meals",
            "description": (
                "Adjust the cooked-meals pool for a recipe by a signed "
                "delta — positive to add (e.g. 'I found two more in "
                "the freezer'), negative to remove (e.g. 'I ate one', "
                "'the kids finished two'). Don't use for fresh cooks "
                "— that's `cook_recipe`. Floors at 0; never goes "
                "negative."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_name": {"type": "string"},
                    "delta": {
                        "type": "integer",
                        "description": "Signed change. -1 for 'I ate one', +2 for 'found two more'.",
                    },
                },
                "required": ["recipe_name", "delta"],
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
_ACTION_TOOLS = frozenset({
    ADD_TO_SHOPPING_LIST,
    # Tier-2 confirm-style actions — single-decision Confirm/Cancel cards.
    "update_stock_level",
    "mark_opened",
    "push_expiry",
    "tick_shopping_line",
    "move_item",
    "set_primary_list",
    "plan_meal_for_date",
    "add_recipe_to_list",
    "cook_recipe",
    "adjust_recipe_meals",
})


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
        conditions.append(EntityField(StockLevel, StockLevel.Fields.SEQUENCE).gte(LOW_STOCK_SEQUENCE))
    if _truthy(args.get("expiring_soon")):
        horizon = date.today() + timedelta(days=EXPIRING_SOON_WINDOW_DAYS)
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
        .include(Product.Fields.STORE)
        .include(Product.Fields.CURRENT_OFFER)
    )

    conditions: list[BoolOperation] = [
        EntityField(Product, Product.Fields.IS_ACTIVE).eq(True),
        EntityField(Product, Product.Fields.IS_AVAILABLE).eq(True),
    ]
    keyword_condition = _keyword_condition(Product, Product.Fields.NAME, args.get("keywords", ""))
    if keyword_condition is not None:
        conditions.append(keyword_condition)
    if args.get("store_name"):
        conditions.append(EntityField(Store, Store.Fields.NAME).contains(str(args["store_name"])))
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
            "store": product.store.name if product.store else None,
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
    # cuisine is an FK relationship (selectin-loaded), so it's filtered in
    # Python rather than via a SQL `.contains` on a string column.
    cuisine_arg = str(args["cuisine"]).strip().lower() if args.get("cuisine") else None
    if cuisine_arg:
        recipes = [
            r for r in recipes
            if r.cuisine and cuisine_arg in r.cuisine.name.lower()
        ]
    return [
        {
            "name": recipe.name,
            "cuisine": recipe.cuisine.name if recipe.cuisine else None,
            "difficulty": recipe.difficulty,
            "category": recipe.category.name if recipe.category else None,
            "cook_time_minutes": recipe.cook_time_minutes,
            "prep_time_minutes": recipe.prep_time_minutes,
            "servings": recipe.servings,
            "is_favourite": bool(recipe.is_favourite),
        }
        for recipe in recipes[:_MAX_ROWS]
    ]


def _recipe_matches_keywords(recipe: Recipe, text: str) -> bool:
    """True when any keyword token appears in the recipe's name, category, or
    cuisine name. Done in Python (not SQL) because category/cuisine are now FK
    relationships — broad on purpose so a mood term ('salad', 'curry')
    surfaces relevant recipes. Empty/blank text matches everything."""
    tokens = [t.lower() for t in str(text or "").split() if t]
    if not tokens:
        return True
    haystack = " ".join(filter(None, [
        recipe.name or "",
        recipe.category.name if recipe.category else "",
        recipe.cuisine.name if recipe.cuisine else "",
    ])).lower()
    return any(token in haystack for token in tokens)


def _stock_coverage(recipe: Recipe) -> tuple[int, int, list[str]]:
    """Return (in_stock_count, total_required_ingredients, missing_names).

    Cookbook revision §1.9 — **optional ingredients are excluded** so the
    assistant's coverage matches the recipe DTO's `cookable` rule and the
    dashboard's `cookable_count` (R-003 single source). Otherwise: an
    ingredient is missing when it has no stock item or its level is the
    worst ("Out of Stock").
    """
    total = 0
    in_stock = 0
    missing: list[str] = []
    for ingredient in recipe.ingredients or []:
        if getattr(ingredient, "is_optional", False):
            continue
        total += 1
        item = ingredient.stock_item
        level = item.stock_level if item else None
        if level is not None and not is_out_of_stock(level):
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
    # keyword + cuisine are filtered in Python after load (category/cuisine are
    # FK relationships, not string columns). difficulty stays a string column.
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

    # P2-08 — tag / ingredient filters. We compute an allowed recipe-id
    # set up front (when any filter is set) and add it as an `id IN
    # (...)` constraint, which composes naturally with the existing
    # `conditions` list. Empty result short-circuits before the DB hit.
    from dora_api.features.recipes.recipe_tag_access import (
        find_recipe_ids_with_all_tags, find_recipe_ids_with_any_tags,
        get_tag_names_for_recipes,
    )

    def _coerce_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [t.strip() for t in value.split(",") if t.strip()]
        if isinstance(value, (list, tuple)):
            return [str(v).strip() for v in value if str(v).strip()]
        return []

    tags_include = _coerce_list(args.get("tags_include"))
    tags_exclude = _coerce_list(args.get("tags_exclude"))
    ingredient_exclude = [s.lower() for s in _coerce_list(args.get("ingredient_exclude"))]

    if tags_include or tags_exclude or ingredient_exclude:
        allowed: set[UUID] = {r.id for r in repo.get(Recipe).all()}
        if tags_include:
            allowed &= find_recipe_ids_with_all_tags(tags_include)
        if tags_exclude:
            allowed -= find_recipe_ids_with_any_tags(tags_exclude)
        if not allowed:
            return [{
                "status": "no_matches",
                "note": "No recipes match those dietary filters.",
            }]
        conditions.append(EntityField(Recipe, "id").in_(list(allowed)))

    recipes: list[Recipe] = query.all(_combine_and(conditions))
    based_on_stock = _truthy(args.get("based_on_stock"))

    # Python-side keyword + cuisine filtering (FK relationships).
    keywords = args.get("keywords", "")
    recipes = [r for r in recipes if _recipe_matches_keywords(r, keywords)]
    cuisine_arg = str(args["cuisine"]).strip().lower() if args.get("cuisine") else None
    if cuisine_arg:
        recipes = [r for r in recipes if r.cuisine and cuisine_arg in r.cuisine.name.lower()]

    # If the user excluded ingredients, drop recipes that contain any
    # matching ingredient name (case-insensitive substring).
    if ingredient_exclude:
        recipes = [
            r for r in recipes
            if not any(
                term in (ing.stock_item.name or "").lower()
                for ing in (r.ingredients or [])
                if ing.stock_item is not None
                for term in ingredient_exclude
            )
        ]

    # Tag lookup for the response. Bulk-fetch once so each row can
    # surface its tags without N round-trips.
    tag_map = get_tag_names_for_recipes([r.id for r in recipes]) if recipes else {}

    rows: list[dict] = []
    for recipe in recipes:
        in_stock, total, missing = _stock_coverage(recipe)
        coverage = (in_stock / total) if total else 0.0
        rows.append({
            "name": recipe.name,
            "cuisine": recipe.cuisine.name if recipe.cuisine else None,
            "difficulty": recipe.difficulty,
            "cook_time_minutes": recipe.cook_time_minutes,
            "servings": recipe.servings,
            "is_favourite": bool(recipe.is_favourite),
            "total_ingredients": total,
            "in_stock_count": in_stock,
            "can_make_now": total > 0 and in_stock == total,
            "missing_ingredients": missing,
            "tags": tag_map.get(recipe.id, []),
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
# The data tables (unit factors, ingredient densities, gas-mark scale) live
# in dora_api.domain.units — R-003 single source of truth shared with the
# price-entry widget and the harvest path (FU-227 chunk 1). This function
# is the assistant tool-call adapter: same return shape the LLM expects.
from dora_api.domain import units as _units


def convert_measurement(args: dict) -> list[dict]:
    amount = _units.parse_amount(args.get("amount"))
    if amount is None:
        return [{"error": "amount must be a number (decimals and fractions OK)"}]
    from_unit = _units.normalise_unit(str(args.get("from_unit") or ""))
    to_unit = _units.normalise_unit(str(args.get("to_unit") or ""))
    ingredient = (args.get("ingredient") or "").strip().lower() or None

    # Gas mark <-> °C / °F.
    if from_unit in _units.GAS_MARK_ALIASES:
        raw_amount = str(args.get("amount") or "").strip()
        c = _units.GAS_MARK_TO_C.get(raw_amount) or _units.GAS_MARK_TO_C.get(
            f"{int(amount)}" if amount == int(amount) else ""
        )
        if c is None:
            return [{"error": f"gas mark {raw_amount or amount} isn't on the scale (1/4, 1/2, or 1-9)"}]
        if to_unit in ("c", "celsius", "celcius"):
            return [{"amount": amount, "from_unit": "gas mark", "to_unit": to_unit, "result": round(c, 1)}]
        if to_unit in ("f", "fahrenheit"):
            return [{"amount": amount, "from_unit": "gas mark", "to_unit": to_unit, "result": round(c * 9 / 5 + 32, 1)}]
        return [{"error": "gas marks convert to temperature (°C or °F)"}]
    if to_unit in _units.GAS_MARK_ALIASES:
        temp_units = {"c", "celsius", "celcius", "f", "fahrenheit"}
        if from_unit not in temp_units:
            return [{"error": "only temperatures convert to gas marks"}]
        celsius = amount if from_unit in ("c", "celsius", "celcius") else (amount - 32) * 5 / 9
        return [{"amount": amount, "from_unit": from_unit, "to_unit": "gas mark", "result": _units.snap_gas_mark(celsius)}]

    # Temperature — offsets handled by the domain helper.
    temp_units = {"c", "celsius", "celcius", "f", "fahrenheit", "k", "kelvin"}
    if from_unit in temp_units or to_unit in temp_units:
        if from_unit not in temp_units or to_unit not in temp_units:
            return [{"error": f"can't convert {from_unit} to {to_unit} — temperature must convert to temperature"}]
        result = _units.convert_temperature(amount, from_unit, to_unit)
        if result is None:
            return [{"error": f"can't convert {from_unit} to {to_unit}"}]
        return [{"amount": amount, "from_unit": from_unit, "to_unit": to_unit, "result": round(result, 1)}]

    src = _units.find_unit(from_unit)
    dst = _units.find_unit(to_unit)
    if not src or not dst:
        return [{"error": f"unknown unit(s): {from_unit!r} or {to_unit!r}"}]

    # Same dimension: linear conversion via the domain helper.
    if src.dimension == dst.dimension:
        result = _units.convert(amount, from_unit, to_unit)
        if result is None:
            return [{"error": f"can't convert {from_unit} to {to_unit}"}]
        return [{"amount": amount, "from_unit": from_unit, "to_unit": to_unit, "result": round(result, 3)}]

    # Cross-dimension mass↔volume needs an ingredient density.
    if {src.dimension, dst.dimension} == {_units.MASS, _units.VOLUME}:
        density = _units.INGREDIENT_DENSITY_G_PER_ML.get(ingredient) if ingredient else None
        if density is None:
            return [{
                "error": f"need an ingredient to convert {from_unit} to {to_unit} (mass↔volume depends on density)",
                "known_ingredients": sorted(set(_units.INGREDIENT_DENSITY_G_PER_ML.keys())),
            }]
        result = _units.convert(amount, from_unit, to_unit, ingredient=ingredient)
        if result is None:
            return [{"error": f"can't convert {from_unit} to {to_unit}"}]
        return [{
            "amount": amount, "from_unit": from_unit, "to_unit": to_unit,
            "ingredient": ingredient, "density_g_per_ml": density,
            "result": round(result, 3),
        }]

    return [{"error": f"can't convert {src.dimension} to {dst.dimension}"}]



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
        horizon_days = int(args.get("within_days", EXPIRING_SOON_WINDOW_DAYS))
    except (TypeError, ValueError):
        horizon_days = EXPIRING_SOON_WINDOW_DAYS
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
        .include(Product.Fields.STORE)
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
    if args.get("store_name"):
        conditions.append(EntityField(Store, Store.Fields.NAME).contains(str(args["store_name"])))

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
            "store": product.store.name if product.store else None,
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
    low = sum(1 for i in items if needs_restock(i.stock_level))
    out = sum(1 for i in items if is_out_of_stock(i.stock_level))
    flagged = sum(1 for i in items if i.is_flagged)
    open_items = sum(1 for i in items if i.is_open)
    horizon = date.today() + timedelta(days=EXPIRING_SOON_WINDOW_DAYS)
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

    query = repo.get(MealPlanEntry).include(MealPlanEntry.Fields.RECIPE)
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
            "meal_name": entry.recipe.name if entry.recipe else None,
            "servings": entry.servings,
        }
        for entry in entries[:_MAX_ROWS]
    ]


# ── Meal pool: what's cooked & ready, what's running short ──────────────

def meals_in_pool(_args: dict) -> list[dict]:
    """List recipes with cooked-and-ready meals in the pool, descending
    by count. Answers "what's in the freezer", "what cooked meals do I
    have ready", "anything left from Sunday's batch cook"."""
    repo = SqlAlchemyRepository()
    recipes: list[Recipe] = repo.get(Recipe).all(
        EntityField(Recipe, Recipe.Fields.AVAILABLE_MEALS).gt(0)
    )
    recipes.sort(key=lambda r: (-(r.available_meals or 0), r.name.lower()))
    return [
        {
            "recipe_name": r.name,
            "available_meals": r.available_meals or 0,
        }
        for r in recipes[:_MAX_ROWS]
    ]


def meals_shortfall(_args: dict) -> list[dict]:
    """Per-recipe shortfall — recipes whose committed plan servings
    exceed the pool. Answers "what do I need to cook", "what's the week
    short on", "what should I batch-cook next"."""
    from dora_api.features.meal_plans.get_shortfall import GetShortfallHandler
    rows = GetShortfallHandler().handle()
    return [
        {
            "recipe_name": row.recipe_name,
            "available_meals": row.available_meals,
            "committed_meals": row.committed_meals,
            "shortfall": row.shortfall,
            "earliest_needed": (
                row.earliest_needed.isoformat() if row.earliest_needed else None
            ),
        }
        for row in rows[:_MAX_ROWS]
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
                "cuisine": recipe.cuisine.name if recipe.cuisine else None,
                "difficulty": recipe.difficulty,
                "cook_time_minutes": recipe.cook_time_minutes,
                "is_favourite": bool(recipe.is_favourite),
            })
    matches.sort(key=lambda r: (not r["is_favourite"], r["name"]))
    return matches[:_MAX_ROWS]



# ─────────────────────────────────────────────────────────────────────────
# Tier-1 detail / introspection tools
# ─────────────────────────────────────────────────────────────────────────

def get_alerts(args: dict) -> list[dict]:
    """Delegate to the alerts handler that powers the bell icon, then expose
    the rows in a model-friendly shape (with optional severity/kind filters)."""
    handler = GetAlertsHandler()
    payload = handler.handle()
    severity = (args.get("severity") or "").strip().lower() or None
    kind = (args.get("kind") or "").strip().lower() or None
    rows: list[dict] = []
    for alert in payload.items:
        if severity and alert.severity != severity:
            continue
        if kind and alert.kind != kind:
            continue
        rows.append({
            "kind": alert.kind,
            "severity": alert.severity,
            "stock_item_name": alert.stock_item_name,
            "message": alert.message,
            "detail": alert.detail,
            "related_date": alert.related_date,
        })
    # Severity order: high first, then medium, then low.
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    rows.sort(key=lambda r: severity_rank.get(r["severity"], 99))
    return rows[:_MAX_ROWS]


def _find_one_by_name(repo: SqlAlchemyRepository, entity: type, name: str, query_builder=None):
    """Exact name match first (case-insensitive), substring fallback. Returns
    the single best match or None when there are 0 or >1 candidates. The
    caller renders a 'be more specific' message in the >1 case."""
    field = EntityField(entity, "name")
    query = query_builder() if query_builder else repo.get(entity)
    exact = query.all(field.eq(name))
    if len(exact) == 1:
        return exact[0], "exact"
    if len(exact) > 1:
        return None, "ambiguous_exact"
    query = query_builder() if query_builder else repo.get(entity)
    fuzzy = query.all(field.contains(name))
    if len(fuzzy) == 1:
        return fuzzy[0], "fuzzy"
    if len(fuzzy) == 0:
        return None, "not_found"
    return None, "ambiguous_fuzzy", fuzzy


def stock_item_detail(args: dict) -> list[dict]:
    name = str(args.get("name") or "").strip()
    if not name:
        return [{"error": "name is required"}]
    repo = SqlAlchemyRepository()

    def build():
        return (
            repo.get(StockItem)
            .include(StockItem.Fields.STOCK_LEVEL)
            .include(StockItem.Fields.STOCK_LOCATION)
            .include(StockItem.Fields.STOCK_GROUP)
        )

    result = _find_one_by_name(repo, StockItem, name, build)
    status = result[1] if isinstance(result, tuple) else "not_found"
    if status == "not_found":
        return [{"query": name, "status": "not_found"}]
    if status.startswith("ambiguous"):
        candidates = result[2] if len(result) > 2 else []
        return [{
            "query": name,
            "status": "ambiguous",
            "candidates": [{"name": c.name, "location": c.stock_location.name if c.stock_location else None} for c in candidates[:_MAX_CANDIDATES]],
        }]
    item: StockItem = result[0]

    # Recipes that reference this item.
    recipes_using: list[str] = []
    recipes: list[Recipe] = (
        repo.get(Recipe)
        .include(Recipe.Fields.INGREDIENTS)
        .then_include(RecipeIngredient.Fields.STOCK_ITEM)
        .all()
    )
    for recipe in recipes:
        for ing in (recipe.ingredients or []):
            if ing.stock_item and ing.stock_item.id == item.id:
                recipes_using.append(recipe.name)
                break

    # On a shopping list?
    list_lines: list[ShoppingListLine] = repo.get(ShoppingListLine).all(
        EntityField(ShoppingListLine, ShoppingListLine.Fields.STOCK_ITEM_ID).eq(item.id)
    )
    on_lists_count = len(list_lines)

    return [{
        "name": item.name,
        "stock_level": item.stock_level.name if item.stock_level else None,
        "location": item.stock_location.name if item.stock_location else None,
        "group": item.stock_group.name if item.stock_group else None,
        "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
        "is_flagged": bool(item.is_flagged),
        "is_open": bool(item.is_open),
        "opened_on": item.opened_on.isoformat() if getattr(item, "opened_on", None) else None,
        "auto_add_when_low": bool(getattr(item, "auto_add_when_low", False)),
        "stock_level_last_updated": (
            item.stock_level_last_updated.isoformat()
            if getattr(item, "stock_level_last_updated", None) else None
        ),
        "recipes_using_item": recipes_using[:_MAX_ROWS],
        "on_shopping_lists_count": on_lists_count,
    }]


def recipe_detail(args: dict) -> list[dict]:
    name = str(args.get("name") or "").strip()
    if not name:
        return [{"error": "name is required"}]
    repo = SqlAlchemyRepository()

    def build():
        return (
            repo.get(Recipe)
            .include(Recipe.Fields.INGREDIENTS)
            .then_include(RecipeIngredient.Fields.STOCK_ITEM)
            .then_include(StockItem.Fields.STOCK_LEVEL)
        )

    result = _find_one_by_name(repo, Recipe, name, build)
    status = result[1] if isinstance(result, tuple) else "not_found"
    if status == "not_found":
        return [{"query": name, "status": "not_found"}]
    if status.startswith("ambiguous"):
        candidates = result[2] if len(result) > 2 else []
        return [{
            "query": name,
            "status": "ambiguous",
            "candidates": [{"name": c.name, "cuisine": c.cuisine.name if c.cuisine else None} for c in candidates[:_MAX_CANDIDATES]],
        }]
    recipe: Recipe = result[0]

    in_stock, total, missing = _stock_coverage(recipe)

    # Trim instructions preview — small models choke on long blobs and the
    # user can open the recipe page if they want the full thing.
    instructions_preview = None
    if recipe.instructions:
        text = recipe.instructions.strip()
        instructions_preview = text[:400] + ("…" if len(text) > 400 else "")

    return [{
        "name": recipe.name,
        "cuisine": recipe.cuisine.name if recipe.cuisine else None,
        "category": recipe.category.name if recipe.category else None,
        "difficulty": recipe.difficulty,
        "cook_time_minutes": recipe.cook_time_minutes,
        "prep_time_minutes": recipe.prep_time_minutes,
        "servings": recipe.servings,
        "is_favourite": bool(recipe.is_favourite),
        "last_made_on": recipe.last_made_on.isoformat() if recipe.last_made_on else None,
        "total_ingredients": total,
        "in_stock_count": in_stock,
        "can_make_now": total > 0 and in_stock == total,
        "missing_ingredients": missing,
        "ingredients": [
            {
                "name": ing.stock_item.name if ing.stock_item else "(unlinked)",
                "quantity": ing.quantity,
                "unit": ing.unit,
                "notes": ing.notes,
                "in_stock": bool(
                    ing.stock_item
                    and ing.stock_item.stock_level
                    and not is_out_of_stock(ing.stock_item.stock_level)
                ),
            }
            for ing in (recipe.ingredients or [])
        ],
        "instructions_preview": instructions_preview,
    }]


def shopping_list_contents(args: dict) -> list[dict]:
    repo = SqlAlchemyRepository()
    name = str(args.get("name") or "").strip()

    if name:
        lists = repo.get(ShoppingList).all(
            EntityField(ShoppingList, ShoppingList.Fields.STATUS).ne(SHOPPING_LIST_STATUS_DONE)
            & EntityField(ShoppingList, ShoppingList.Fields.NAME).contains(name)
        )
        if not lists:
            return [{"query": name, "status": "not_found"}]
        if len(lists) > 1:
            return [{
                "query": name,
                "status": "ambiguous",
                "candidates": [{"name": l.name, "status": l.status} for l in lists[:_MAX_CANDIDATES]],
            }]
        shopping_list = lists[0]
    else:
        # Default to the inferred quick-add target (only when exactly one draft).
        from dora_api.features.shopping_lists.primary_target_resolver import \
            resolve_primary_target
        active_lists = repo.get(ShoppingList).all(
            EntityField(ShoppingList, ShoppingList.Fields.STATUS).ne(SHOPPING_LIST_STATUS_DONE)
        )
        outcome = resolve_primary_target(active_lists)
        if outcome.kind != "single":
            return [{"status": "no_primary" if outcome.kind == "none" else "ambiguous"}]
        target = next(
            (l for l in active_lists if l.id == outcome.target_list_id), None
        )
        if target is None:
            return [{"status": "no_primary"}]
        shopping_list = target

    lines: list[ShoppingListLine] = repo.get(ShoppingListLine).all(
        EntityField(ShoppingListLine, ShoppingListLine.Fields.SHOPPING_LIST_ID).eq(shopping_list.id)
    )
    if not lines:
        return [{
            "list_name": shopping_list.name,
            "status": shopping_list.status,
            "total_lines": 0,
            "ticked": 0,
            "outstanding": 0,
            "lines": [],
        }]

    # Resolve stock-item names + levels in a second pass so we don't N+1 the lookups.
    item_ids = list({line.stock_item_id for line in lines})
    items: list[StockItem] = (
        repo.get(StockItem)
        .include(StockItem.Fields.STOCK_LEVEL)
        .all(EntityField(StockItem, StockItem.Fields.ID).in_(item_ids))
        if item_ids else []
    )
    item_lookup = {it.id: it for it in items}

    rendered = []
    for line in sorted(lines, key=lambda l: (l.is_ticked, l.sequence)):
        item = item_lookup.get(line.stock_item_id)
        rendered.append({
            "name": item.name if item else "(unknown item)",
            "quantity": line.quantity,
            "is_ticked": line.is_ticked,
            "stock_level": item.stock_level.name if item and item.stock_level else None,
        })

    ticked = sum(1 for l in lines if l.is_ticked)
    return [{
        "list_name": shopping_list.name,
        "status": shopping_list.status,
        "total_lines": len(lines),
        "ticked": ticked,
        "outstanding": len(lines) - ticked,
        "lines": rendered[:_MAX_ROWS],
    }]


def meal_detail(args: dict) -> list[dict]:
    name = str(args.get("name") or "").strip()
    if not name:
        return [{"error": "name is required"}]
    repo = SqlAlchemyRepository()

    def build():
        return repo.get(Recipe)

    result = _find_one_by_name(repo, Recipe, name, build)
    status = result[1] if isinstance(result, tuple) else "not_found"
    if status == "not_found":
        return [{"query": name, "status": "not_found"}]
    if status.startswith("ambiguous"):
        candidates = result[2] if len(result) > 2 else []
        return [{
            "query": name,
            "status": "ambiguous",
            "candidates": [{"name": c.name} for c in candidates[:_MAX_CANDIDATES]],
        }]
    recipe: Recipe = result[0]

    return [{
        "name": recipe.name,
        "available_meals": recipe.available_meals or 0,
        "cuisine": recipe.cuisine.name if recipe.cuisine else None,
        "cook_time_minutes": recipe.cook_time_minutes,
        "difficulty": recipe.difficulty,
        "servings": recipe.servings,
    }]


def find_location(args: dict) -> list[dict]:
    name = str(args.get("name") or "").strip()
    if not name:
        return [{"error": "name is required"}]
    urgent_only = _truthy(args.get("urgent_only"))
    repo = SqlAlchemyRepository()

    locations: list[StockLocation] = repo.get(StockLocation).all(
        EntityField(StockLocation, StockLocation.Fields.NAME).contains(name)
    )
    if not locations:
        return [{"query": name, "status": "not_found"}]
    # Collect items at any of these locations (locations include zones/areas/
    # sections — we match by location_id directly, so a zone match only returns
    # items pinned at the zone level; areas/sections are separate matches).
    location_ids = [l.id for l in locations]
    items: list[StockItem] = (
        repo.get(StockItem)
        .include(StockItem.Fields.STOCK_LEVEL)
        .include(StockItem.Fields.STOCK_LOCATION)
        .all(EntityField(StockItem, StockItem.Fields.STOCK_LOCATION_ID).in_(location_ids))
    )

    today = date.today()
    horizon = today + timedelta(days=EXPIRING_SOON_WINDOW_DAYS)

    def is_urgent(it: StockItem) -> bool:
        level_bad = needs_restock(it.stock_level)
        expiry_bad = it.expiry_date and (it.expiry_date < today or it.expiry_date <= horizon)
        return bool(level_bad or expiry_bad)

    filtered = [it for it in items if is_urgent(it)] if urgent_only else items

    rows = []
    for loc in locations:
        loc_items = [it for it in filtered if it.stock_location and it.stock_location.id == loc.id]
        rows.append({
            "location_name": loc.name,
            "kind": loc.kind,
            "item_count": len(loc_items),
            "items": [
                {
                    "name": it.name,
                    "stock_level": it.stock_level.name if it.stock_level else None,
                    "expiry_date": it.expiry_date.isoformat() if it.expiry_date else None,
                    "is_flagged": bool(it.is_flagged),
                }
                for it in loc_items[:_MAX_ROWS]
            ],
        })
    return rows[:_MAX_ROWS]



# ─────────────────────────────────────────────────────────────────────────
# Tier-3 cognitive / curated tools
# ─────────────────────────────────────────────────────────────────────────

# AU seasonal produce by month. Curated rather than computed — fits a small
# pocket reference better than a date library. Apologies to the southern-
# hemisphere edge cases; this is the rough consensus.
_SEASONAL_AU: dict[int, dict[str, list[str]]] = {
    # month → { "fruit": [...], "veg": [...] }
    1:  {"fruit": ["apricot", "blackberry", "blueberry", "cherry", "fig", "lychee", "mango", "nectarine", "peach", "plum", "raspberry", "watermelon"],
         "veg":   ["basil", "capsicum", "corn", "cucumber", "eggplant", "green bean", "lettuce", "snow pea", "tomato", "zucchini"]},
    2:  {"fruit": ["apple", "blackberry", "fig", "grape", "mango", "nectarine", "passionfruit", "peach", "plum", "raspberry", "watermelon"],
         "veg":   ["basil", "capsicum", "chilli", "corn", "cucumber", "eggplant", "leek", "lettuce", "tomato", "zucchini"]},
    3:  {"fruit": ["apple", "fig", "grape", "kiwifruit", "passionfruit", "pear", "persimmon", "pomegranate", "quince"],
         "veg":   ["beetroot", "broccoli", "cabbage", "cauliflower", "eggplant", "leek", "mushroom", "pumpkin", "silverbeet", "sweet potato"]},
    4:  {"fruit": ["apple", "feijoa", "kiwifruit", "mandarin", "pear", "persimmon", "pomegranate", "quince"],
         "veg":   ["beetroot", "broccoli", "brussels sprout", "cabbage", "cauliflower", "fennel", "leek", "mushroom", "pumpkin", "silverbeet", "sweet potato"]},
    5:  {"fruit": ["apple", "kiwifruit", "lemon", "mandarin", "orange", "pear", "persimmon", "rhubarb"],
         "veg":   ["broccoli", "brussels sprout", "cabbage", "cauliflower", "carrot", "celeriac", "fennel", "kale", "leek", "parsnip", "pumpkin", "swede", "turnip"]},
    6:  {"fruit": ["apple", "kiwifruit", "lemon", "mandarin", "orange", "pear", "rhubarb"],
         "veg":   ["broccoli", "brussels sprout", "cabbage", "cauliflower", "carrot", "celeriac", "fennel", "kale", "leek", "parsnip", "pumpkin", "silverbeet", "swede", "turnip"]},
    7:  {"fruit": ["apple", "grapefruit", "kiwifruit", "lemon", "mandarin", "orange", "pear", "rhubarb"],
         "veg":   ["broccoli", "brussels sprout", "cabbage", "cauliflower", "carrot", "fennel", "kale", "leek", "parsnip", "pumpkin", "silverbeet", "swede", "turnip"]},
    8:  {"fruit": ["apple", "blood orange", "grapefruit", "lemon", "mandarin", "orange", "pear", "rhubarb"],
         "veg":   ["asparagus", "broccoli", "brussels sprout", "cabbage", "cauliflower", "fennel", "kale", "leek", "parsnip", "spinach", "swede"]},
    9:  {"fruit": ["apple", "blood orange", "grapefruit", "lemon", "mandarin", "orange", "pineapple", "strawberry"],
         "veg":   ["artichoke", "asparagus", "broad bean", "broccoli", "cabbage", "fennel", "kale", "leek", "spinach", "spring onion"]},
    10: {"fruit": ["apple", "loquat", "mango", "papaya", "pineapple", "rhubarb", "strawberry"],
         "veg":   ["artichoke", "asparagus", "broad bean", "broccoli", "leek", "lettuce", "rocket", "snow pea", "spinach", "spring onion"]},
    11: {"fruit": ["apricot", "blueberry", "cherry", "mango", "nectarine", "papaya", "peach", "pineapple", "raspberry", "strawberry", "watermelon"],
         "veg":   ["asparagus", "broad bean", "capsicum", "cucumber", "lettuce", "rocket", "snow pea", "spring onion", "tomato", "zucchini"]},
    12: {"fruit": ["apricot", "blueberry", "cherry", "lychee", "mango", "nectarine", "peach", "pineapple", "plum", "raspberry", "strawberry", "watermelon"],
         "veg":   ["basil", "capsicum", "corn", "cucumber", "lettuce", "rocket", "snow pea", "spring onion", "tomato", "zucchini"]},
}

_MONTH_NAMES = ["january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"]


def _resolve_month(raw: str) -> int:
    raw = raw.strip().lower()
    if not raw:
        return date.today().month
    try:
        n = int(raw)
        if 1 <= n <= 12:
            return n
    except ValueError:
        pass
    for i, name in enumerate(_MONTH_NAMES, start=1):
        if raw.startswith(name[:3]):
            return i
    return date.today().month


def seasonal_picks(args: dict) -> list[dict]:
    month_num = _resolve_month(str(args.get("month") or ""))
    table = _SEASONAL_AU.get(month_num, {"fruit": [], "veg": []})
    return [{
        "month": _MONTH_NAMES[month_num - 1].capitalize(),
        "fruit": table["fruit"],
        "veg": table["veg"],
        "note": "Australian seasonal guide — pricing and availability vary by region.",
    }]


# ── Suggestions inbox (P2-04) ───────────────────────────────────────────
# Same handler as GET /api/suggestions. Flattened to plain dicts so the
# model doesn't have to learn the wrapper shape; suppression filtering
# happens server-side, so the model only ever sees live suggestions.

def list_suggestions(_args: dict) -> list[dict]:
    from flask import session
    from dora_api.features.suggestions.suggestions import GetSuggestionsHandler

    raw = session.get("user_id")
    user_id: UUID | None = None
    if raw:
        try:
            user_id = UUID(raw)
        except (ValueError, TypeError):
            user_id = None
    rows = GetSuggestionsHandler().handle(user_id)
    if not rows:
        return [{
            "status": "no_suggestions",
            "note": "Nothing to surface right now — pantry looks settled.",
        }]
    return [{
        "status": "ok",
        "count": len(rows),
        "suggestions": [
            {
                "kind": r.kind,
                "severity": r.severity,
                "title": r.title,
                "body": r.body,
                "reason": r.reason,
                "primary_action": r.primary_action,
                "payload": r.payload,
            }
            for r in rows
        ],
    }]


# ── Expiry rescue + waste insights (P2-06) ──────────────────────────────
# Thin wrappers around the waste handler. They both share the same data
# source so the model can chain "what's expiring?" → "what recipe uses
# them?" → "did I waste a lot of this last month?" without three
# different tool calls.

def expiry_rescue(args: dict) -> list[dict]:
    from dora_api.features.waste.waste import GetWasteRescueHandler

    try:
        horizon = int(args.get("horizon_days", 7))
    except (TypeError, ValueError):
        horizon = 7
    dto = GetWasteRescueHandler().handle(horizon)
    items = [
        {
            "name": i.name,
            "expiry_date": i.expiry_date,
            "days_until_expiry": i.days_until_expiry,
            "is_expired": i.is_expired,
            "stock_level": i.stock_level_name,
            "estimated_value": i.estimated_value,
        }
        for i in dto.items
    ]
    recipes = [
        {
            "name": r.name,
            "cook_time_minutes": r.cook_time_minutes,
            "difficulty": r.difficulty,
            "uses_expiring": r.matching_expiring_items,
            "missing_ingredients": r.missing_ingredients,
            "is_favourite": r.is_favourite,
        }
        for r in dto.recipes
    ]
    if not items:
        return [{
            "horizon_days": dto.horizon_days,
            "status": "nothing_at_risk",
            "note": "No items are within the horizon — your fridge is safe.",
        }]
    return [{
        "horizon_days": dto.horizon_days,
        "status": "ok",
        "items": items,
        "recipes": recipes,
    }]


def waste_insights(args: dict) -> list[dict]:
    # Same DB walk as GET /api/waste/insights but plain dict output so
    # the model doesn't have to learn the wrapper shape.
    try:
        window_days = int(args.get("window_days", 90))
    except (TypeError, ValueError):
        window_days = 90
    window_days = max(7, min(window_days, 365))
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

    from dora_api.domain.entities.stock_item_waste_event import (
        StockItemWasteEvent,
    )
    repo = SqlAlchemyRepository()
    events: list[StockItemWasteEvent] = repo.get(StockItemWasteEvent).all(
        EntityField(
            StockItemWasteEvent, StockItemWasteEvent.Fields.OCCURRED_AT
        ).gte(cutoff)
    )
    if not events:
        return [{
            "window_days": window_days,
            "status": "no_data",
            "note": (
                "No waste events have been logged in this window. The "
                "user logs them via the Waste page when they have to "
                "throw something out."
            ),
        }]

    buckets: dict[tuple, dict] = {}
    total_value = 0.0
    for event in events:
        key = (event.stock_item_id, event.stock_item_name)
        bucket = buckets.setdefault(key, {
            "name": event.stock_item_name,
            "events": 0,
            "estimated_value": 0.0,
            "reasons": {},
        })
        bucket["events"] += 1
        if event.estimated_value:
            bucket["estimated_value"] += float(event.estimated_value)
            total_value += float(event.estimated_value)
        bucket["reasons"][event.reason] = bucket["reasons"].get(event.reason, 0) + 1

    rows = sorted(
        buckets.values(),
        key=lambda b: (-b["events"], -b["estimated_value"], b["name"]),
    )
    for row in rows:
        row["estimated_value"] = round(row["estimated_value"], 2)
    return [{
        "window_days": window_days,
        "status": "ok",
        "total_events": len(events),
        "total_estimated_value": round(total_value, 2),
        "by_item": rows[:_MAX_ROWS],
    }]


# ── Budget status (P2-05) ───────────────────────────────────────────────
# Thin wrapper around the budget handler so Dora can answer "what's left
# in my budget?" without the SPA having to forward the user's query.
# Resolves the current user from the Flask session — same pattern the
# action tools use for shopping-list mutations.

def budget_status(_args: dict) -> list[dict]:
    from flask import session
    from dora_api.features.budget.budget import GetBudgetStatusHandler

    raw = session.get("user_id")
    if not raw:
        return [{"error": "not signed in"}]
    try:
        user_id = UUID(raw)
    except (ValueError, TypeError):
        return [{"error": "not signed in"}]

    dto = GetBudgetStatusHandler().handle(user_id)
    if dto is None:
        return [{"error": "user not found"}]
    if not dto.enabled:
        return [{
            "status": "disabled",
            "note": (
                "The user hasn't opted in to budget tracking. They can "
                "enable it in Settings → Preferences → Grocery budget."
            ),
            "period": dto.period,
            "period_start": dto.period_start,
            "period_end": dto.period_end,
            "spent_this_period": dto.spent,
            "projected_active": dto.projected_active,
        }]
    return [{
        "status": "ok",
        "period": dto.period,
        "period_start": dto.period_start,
        "period_end": dto.period_end,
        "budget_amount": dto.amount,
        "spent": dto.spent,
        "projected_from_active_lists": dto.projected_active,
        "remaining": dto.remaining,
        "over_budget": dto.over_budget,
    }]


# ── Purchase price stats (P2-02) ────────────────────────────────────────
# Pulls historical paid prices out of finished shopping lists. The captured
# price per line is, in priority order:
#   1. actual_unit_price — what the user explicitly entered in shop mode
#      or at finish time (a till-receipt override).
#   2. picked_offer_price — the offer snapshot taken when the line was
#      first ticked (legacy / no-override path).
# Lines without either are skipped: we have nothing trustworthy to report.

def purchase_price_stats(args: dict) -> list[dict]:
    raw_name = str(args.get("item_name") or "").strip()
    if not raw_name:
        return [{"error": "item_name is required"}]
    repo = SqlAlchemyRepository()

    # Resolve the stock item by exact then substring match. Multiple
    # matches → ask the model to disambiguate rather than averaging
    # across distinct items.
    field = EntityField(StockItem, StockItem.Fields.NAME)
    matches: list[StockItem] = repo.get(StockItem).all(field.eq(raw_name))
    if not matches:
        matches = repo.get(StockItem).all(field.contains(raw_name))
    if not matches:
        return [{"query": raw_name, "status": "not_found"}]
    if len(matches) > 1:
        return [{
            "query": raw_name,
            "status": "ambiguous",
            "candidates": [{"name": m.name} for m in matches[:_MAX_CANDIDATES]],
        }]
    item = matches[0]

    # Walk ticked lines on archived lists for this item. We deliberately
    # include unticked lines on archived lists too — the user may have
    # entered a price without ticking — by gating on "has a usable price"
    # instead of is_ticked.
    lines: list[ShoppingListLine] = repo.get(ShoppingListLine).all(
        EntityField(ShoppingListLine, ShoppingListLine.Fields.STOCK_ITEM_ID).eq(item.id)
    )
    if not lines:
        return [{
            "item_name": item.name,
            "status": "no_purchases",
            "note": "No finished shopping lists reference this item yet.",
        }]

    # Restrict to lines whose parent list is archived (= a completed shop).
    list_ids = list({l.shopping_list_id for l in lines})
    archived_ids: set[UUID] = set()
    if list_ids:
        lists = repo.get(ShoppingList).all(
            EntityField(ShoppingList, "id").in_(list_ids)
            & EntityField(ShoppingList, ShoppingList.Fields.STATUS).eq(SHOPPING_LIST_STATUS_DONE)
        )
        archived_ids = {l.id for l in lists}

    # Collect (unit_price, merchant_id_or_None, completed_at) per usable line.
    # Pre-load completed_at + linked merchants in bulk to avoid N+1.
    completed_lookup: dict[UUID, datetime | None] = {}
    if archived_ids:
        for l in repo.get(ShoppingList).all(
            EntityField(ShoppingList, "id").in_(list(archived_ids))
        ):
            completed_lookup[l.id] = l.completed_at

    # Selected-product → merchant lookup, for lines that didn't override
    # `purchased_store_id` but did pick an offer.
    product_store_lookup: dict[UUID, tuple[UUID, str]] = {}
    product_ids = list({
        l.selected_product_id for l in lines
        if l.shopping_list_id in archived_ids and l.selected_product_id
    })
    if product_ids:
        products = (
            repo.get(Product)
            .include(Product.Fields.STORE)
            .all(EntityField(Product, "id").in_(product_ids))
        )
        for p in products:
            if p.store:
                product_store_lookup[p.id] = (p.store.id, p.store.name)

    # Merchant-name lookup for any purchased_store_id overrides on the
    # lines we're about to summarise.
    purchased_store_ids = list({
        l.purchased_store_id for l in lines
        if l.shopping_list_id in archived_ids and l.purchased_store_id
    })
    store_name_lookup: dict[UUID, str] = {}
    if purchased_store_ids:
        for m in repo.get(Store).all(
            EntityField(Store, "id").in_(purchased_store_ids)
        ):
            store_name_lookup[m.id] = m.name

    samples: list[
        tuple[float, UUID | None, str | None, datetime | None, str, int | None]
    ] = []
    for line in lines:
        if line.shopping_list_id not in archived_ids:
            continue
        # actual→picked ladder (K2 shared helper); the source label is still
        # ours since this tool distinguishes user-entered from snapshot.
        price = line_paid_unit_price(line)
        if price is None:
            continue
        source = "actual" if line.actual_unit_price is not None else "offer_snapshot"
        store_id: UUID | None = None
        store_name: str | None = None
        if line.purchased_store_id:
            store_id = line.purchased_store_id
            store_name = store_name_lookup.get(store_id)
        elif line.selected_product_id and line.selected_product_id in product_store_lookup:
            store_id, store_name = product_store_lookup[line.selected_product_id]
        samples.append((
            price, store_id, store_name,
            completed_lookup.get(line.shopping_list_id), source,
            line.quantity,
        ))

    if not samples:
        return [{
            "item_name": item.name,
            "status": "no_purchases",
            "note": "No finished lists for this item have a captured price.",
        }]

    prices = [s[0] for s in samples]
    avg = sum(prices) / len(prices)
    samples_sorted_by_date = sorted(
        samples, key=lambda s: (s[3] or datetime.min), reverse=True,
    )
    last_price, _, last_store_name, last_completed_at, last_source, _ = (
        samples_sorted_by_date[0]
    )

    # Per-store breakdown — only emit a row when we know the store.
    by_store: dict[UUID, dict[str, Any]] = {}
    for price, store_id, store_name, _, _, _ in samples:
        if not store_id:
            continue
        bucket = by_store.setdefault(store_id, {
            "store": store_name,
            "samples": 0,
            "_sum": 0.0,
            "min": price,
            "max": price,
        })
        bucket["samples"] += 1
        bucket["_sum"] += price
        bucket["min"] = min(bucket["min"], price)
        bucket["max"] = max(bucket["max"], price)
    store_rows = []
    for bucket in by_store.values():
        store_rows.append({
            "store": bucket["store"],
            "samples": bucket["samples"],
            "average_price": round(bucket["_sum"] / bucket["samples"], 2),
            "min_price": round(bucket["min"], 2),
            "max_price": round(bucket["max"], 2),
        })
    store_rows.sort(key=lambda r: r["average_price"])

    unknown_store_samples = sum(1 for s in samples if s[1] is None)

    # ── Cadence stats ────────────────────────────────────────────────
    # Same archived-list walk as the price stats; we just look at the
    # *spacing* between completed shops rather than the prices. Multiple
    # purchases on the same shop (which shouldn't happen for one stock
    # item, but be defensive) collapse to one cadence event so a single
    # busy shop doesn't poison the average.
    unique_dates = sorted({
        s[3].date() for s in samples if s[3] is not None
    })
    average_days_between_purchase: float | None = None
    if len(unique_dates) >= 2:
        gaps = [
            (unique_dates[i] - unique_dates[i - 1]).days
            for i in range(1, len(unique_dates))
            if (unique_dates[i] - unique_dates[i - 1]).days > 0
        ]
        if gaps:
            average_days_between_purchase = round(sum(gaps) / len(gaps), 1)

    days_since_last_purchase: int | None = None
    if last_completed_at is not None:
        days_since_last_purchase = max(0, (date.today() - last_completed_at.date()).days)

    quantities = [s[5] for s in samples if s[5] is not None]
    average_quantity: float | None = None
    if quantities:
        average_quantity = round(sum(quantities) / len(quantities), 2)

    # Usual store = the one the user has bought from the most. Tie-
    # broken implicitly by Counter's first-seen order (≈ scan order); on a
    # genuine tie we leave the field as "no clear pattern" via low
    # confidence.
    store_counter: Counter[tuple[UUID, str | None]] = Counter()
    for _, sid, sname, _, _, _ in samples:
        if sid is not None:
            store_counter[(sid, sname)] += 1
    usual_store: str | None = None
    usual_store_share: float | None = None
    if store_counter:
        (_top_id, top_name), top_count = store_counter.most_common(1)[0]
        usual_store = top_name
        usual_store_share = round(top_count / len(samples), 2)

    # Price volatility — stdev when we have ≥2 samples, otherwise None.
    # Spread is a quick sanity-check; stdev is the honest statistic.
    price_stdev: float | None = None
    if len(prices) >= 2:
        price_stdev = round(statistics.stdev(prices), 2)
    price_spread = round(max(prices) - min(prices), 2) if prices else 0

    return [{
        "item_name": item.name,
        "status": "ok",
        "samples": len(samples),
        "average_price": round(avg, 2),
        "min_price": round(min(prices), 2),
        "max_price": round(max(prices), 2),
        "price_stdev": price_stdev,
        "price_spread": price_spread,
        "last_paid_price": round(last_price, 2),
        "last_paid_at": (
            last_completed_at.isoformat() if last_completed_at else None
        ),
        "last_paid_store": last_store_name,
        "last_paid_source": last_source,
        "days_since_last_purchase": days_since_last_purchase,
        "average_days_between_purchase": average_days_between_purchase,
        "average_quantity": average_quantity,
        "usual_store": usual_store,
        "usual_store_share": usual_store_share,
        "by_store": store_rows,
        "unknown_store_samples": unknown_store_samples,
    }]


def compare_prices(args: dict) -> list[dict]:
    name = str(args.get("item_name") or "").strip()
    if not name:
        return [{"error": "item_name is required"}]
    repo = SqlAlchemyRepository()

    # Resolve the stock item with its linked products + offers + merchants.
    def build_query():
        return (
            repo.get(StockItem)
            .include(StockItem.Fields.PRODUCTS)
                .then_include("store")
            .include(StockItem.Fields.PRODUCTS)
                .then_include("current_offer")
        )

    field = EntityField(StockItem, StockItem.Fields.NAME)
    matches = build_query().all(field.eq(name))
    if not matches:
        matches = build_query().all(field.contains(name))
    if not matches:
        return [{"query": name, "status": "not_found"}]
    if len(matches) > 1:
        return [{
            "query": name,
            "status": "ambiguous",
            "candidates": [{"name": m.name} for m in matches[:_MAX_CANDIDATES]],
        }]
    item = matches[0]
    products = item.products or []
    if not products:
        return [{
            "stock_item_name": item.name,
            "status": "no_linked_products",
            "note": "No merchant products are linked to this stock item — link one on the item's detail page.",
            "rows": [],
        }]

    rows = []
    for p in products:
        offer = p.current_offer
        if not offer or offer.price_now is None:
            continue
        savings = (offer.price_was - offer.price_now) if offer.price_was else 0
        rows.append({
            "product_name": p.name,
            "brand": p.brand,
            "store": p.store.name if p.store else None,
            "size": p.size,
            "price_now": offer.price_now,
            "price_was": offer.price_was,
            "on_special": bool(offer.price_was and offer.price_now < offer.price_was),
            "savings": round(savings, 2) if savings else 0,
            "web_url": p.web_url,
        })
    rows.sort(key=lambda r: r["price_now"])
    return [{
        "stock_item_name": item.name,
        "status": "ok",
        "cheapest_store": rows[0]["store"] if rows else None,
        "cheapest_price": rows[0]["price_now"] if rows else None,
        "rows": rows[:_MAX_ROWS],
    }]


# Occasion vocab → search/filter recipe. Each entry is a hint bundle the
# tool wraps around suggest_recipes' existing scorer (which already handles
# stock coverage + favourite tie-breakers).
_OCCASION_PROFILES: dict[str, dict[str, Any]] = {
    "kid": {"keywords": "pasta pizza burger nugget mac cheese sausage", "max_cook_time_minutes": 35, "difficulty": "easy"},
    "kids": {"keywords": "pasta pizza burger nugget mac cheese sausage", "max_cook_time_minutes": 35, "difficulty": "easy"},
    "kid friendly": {"keywords": "pasta pizza burger nugget mac cheese sausage", "max_cook_time_minutes": 35, "difficulty": "easy"},
    "family": {"keywords": "pasta roast casserole curry lasagne", "max_cook_time_minutes": 60},
    "date": {"keywords": "steak risotto pasta seafood salmon", "difficulty": "medium"},
    "date night": {"keywords": "steak risotto pasta seafood salmon", "difficulty": "medium"},
    "romantic": {"keywords": "steak risotto pasta seafood salmon"},
    "guests": {"keywords": "roast risotto lamb seafood tart pavlova", "difficulty": "medium"},
    "dinner party": {"keywords": "roast risotto lamb seafood tart pavlova"},
    "fancy": {"keywords": "duck lamb risotto seafood scallop souffle"},
    "comfort": {"keywords": "stew casserole roast pasta lasagne pie soup"},
    "comfort food": {"keywords": "stew casserole roast pasta lasagne pie soup"},
    "cosy": {"keywords": "stew casserole soup pie risotto"},
    "cozy": {"keywords": "stew casserole soup pie risotto"},
    "quick": {"keywords": "stir fry pasta salad wrap omelette", "max_cook_time_minutes": 20},
    "quick dinner": {"keywords": "stir fry pasta salad wrap omelette", "max_cook_time_minutes": 20},
    "weeknight": {"keywords": "stir fry pasta sheet pan curry rice", "max_cook_time_minutes": 30, "difficulty": "easy"},
    "lazy": {"keywords": "sheet pan one pot pasta toastie", "max_cook_time_minutes": 25},
    "healthy": {"keywords": "salad bowl grilled fish steamed vegetable"},
    "light": {"keywords": "salad soup wrap fish"},
    "spicy": {"keywords": "curry chilli laksa kimchi sichuan"},
    "vegetarian": {"keywords": "vegetable tofu lentil chickpea pasta", "tags_include": "Vegetarian"},
    "vego": {"keywords": "vegetable tofu lentil chickpea pasta", "tags_include": "Vegetarian"},
    "party": {"keywords": "platter dip skewer wing slider"},
    "breakfast": {"keywords": "pancake omelette toastie smoothie porridge"},
    "brunch": {"keywords": "pancake eggs benedict fritter shakshuka avocado"},
    "dessert": {"keywords": "cake pavlova tart pudding crumble brownie"},
    "treat": {"keywords": "cake brownie cookie tart pudding"},
}


def _occasion_profile(occasion: str) -> dict[str, Any] | None:
    key = occasion.strip().lower()
    if key in _OCCASION_PROFILES:
        return _OCCASION_PROFILES[key]
    # Loose match: longest matching alias substring wins.
    best = None
    best_len = 0
    for alias, profile in _OCCASION_PROFILES.items():
        if alias in key and len(alias) > best_len:
            best, best_len = profile, len(alias)
    return best


def recipe_for_occasion(args: dict) -> list[dict]:
    occasion = str(args.get("occasion") or "").strip()
    if not occasion:
        return [{"error": "occasion is required"}]
    profile = _occasion_profile(occasion)
    if not profile:
        return [{
            "occasion": occasion,
            "status": "unknown_occasion",
            "note": "No specific profile for that one — try 'kid-friendly', 'date night', 'comfort', 'quick', 'fancy', 'healthy', 'party', 'dessert'.",
            "rows": [],
        }]
    # Wrap suggest_recipes with the profile's filters plus stock-aware ranking.
    suggest_args = {**profile, "based_on_stock": True}
    rows = suggest_recipes(suggest_args)
    return [{
        "occasion": occasion,
        "matched_profile": profile,
        "status": "ok",
        "rows": rows,
    }]


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
    "meals_in_pool": meals_in_pool,
    "meals_shortfall": meals_shortfall,
    "recipes_using_item": recipes_using_item,
    "get_alerts": get_alerts,
    "stock_item_detail": stock_item_detail,
    "recipe_detail": recipe_detail,
    "shopping_list_contents": shopping_list_contents,
    "meal_detail": meal_detail,
    "find_location": find_location,
    "seasonal_picks": seasonal_picks,
    "compare_prices": compare_prices,
    "purchase_price_stats": purchase_price_stats,
    "budget_status": budget_status,
    "expiry_rescue": expiry_rescue,
    "waste_insights": waste_insights,
    "list_suggestions": list_suggestions,
    "recipe_for_occasion": recipe_for_occasion,
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
    "meals_in_pool": {"path": "/recipes", "label": "Open Recipes"},
    "meals_shortfall": {"path": "/meal-plans", "label": "Open Meal Plans"},
    "recipes_using_item": {"path": "/recipes", "label": "Browse recipes"},
    "get_alerts": {"path": "/stock", "label": "See on Stock"},
    "stock_item_detail": {"path": "/stock", "label": "Open Stock"},
    "recipe_detail": {"path": "/recipes", "label": "Browse recipes"},
    "shopping_list_contents": {"path": "/shopping-lists", "label": "Open Shopping Lists"},
    "meal_detail": {"path": "/recipes", "label": "Open Recipes"},
    "find_location": {"path": "/stock", "label": "See it on the Stock page"},
    "compare_prices": {"path": "/product-search", "label": "Open product search"},
    "purchase_price_stats": {"path": "/reports", "label": "Open Reports"},
    "budget_status": {"path": "/settings/preferences", "label": "Adjust budget"},
    "expiry_rescue": {"path": "/waste", "label": "Open Waste page"},
    "waste_insights": {"path": "/waste", "label": "Open Waste page"},
    # list_suggestions intentionally has no nav target — the SPA reads
    # primary_action off each suggestion and routes from there.
    "recipe_for_occasion": {"path": "/recipes", "label": "Browse recipes"},
    # convert_measurement / suggest_substitution / seasonal_picks need no nav.
}


def is_data_tool(name: str) -> bool:
    return name in _TOOLS


def run_tool(name: str, args: dict) -> list[dict]:
    """Execute a read-only tool. Raises KeyError for unknown names."""
    _Logger.info("Assistant tool '%s' args=%s", name, args)
    return _TOOLS[name](args or {})


def nav_for(name: str) -> dict[str, str] | None:
    return _TOOL_NAV.get(name)
