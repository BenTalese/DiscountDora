"""USDA food categories, and the one question Dora asks of them.

FoodData Central classifies every food into one of 28 categories
(`food_category.csv`, e.g. "1100 Vegetables and Vegetable Products"). The
importer has always downloaded that file as part of the bundle and thrown it
away; since 2026-08-27 it stores the description on `NutritionFood.
food_category`, for exactly one purpose: deciding whether a food counts as
**fvnl** — fruit, vegetable, nut or legume — for the Health Star Rating.

**This is deliberately not `StockGroup`.** A stock group is the user's own
pantry filing system ("Frozen", "Snacks & treats"): free text, renameable, and
chosen to answer *where do I look for this*. Keying nutrition behaviour off it
would break the same rule `domain/stock_status.py` states for stock levels —
behaviour must never depend on a label a user can rename — and it would be
wrong on the merits anyway, since frozen peas are fvnl and live under "Frozen".
The two are unrelated by design (owner's call, 2026-08-27), which is why this
is its own isolated column that nothing in the UI renders.

The category descriptions below *are* safe to key on: they are USDA's fixed
vocabulary shipped inside the dataset, not something an install can edit.
"""
from __future__ import annotations

from typing import Optional


# The categories that count as fvnl, per the HSR Calculator and Style Guide
# v8.1, Step 5.1: "fruits, vegetables, nuts and legumes (fvnl) including
# coconut, spices, herbs, fungi, seeds and algae".
#
# Spices and Herbs is in the list because the guide names them explicitly, not
# by analogy. Fungi and seeds need no entry of their own — USDA files mushrooms
# under Vegetables and seeds under Nut and Seed Products.
#
# What is *not* here matters as much as what is. The guide excludes "a
# constituent, extract or isolate of a food e.g. peanut oil" and "cereal
# grains": USDA already separates those into Fats and Oils (0400) and Cereal
# Grains and Pasta (2000), so excluding them is simply a matter of not listing
# them. Fruits and Fruit Juices does include juices, which HSR treats with more
# nuance than we can here — a splash of lemon juice in a dish reads as fvnl.
FVNL_CATEGORIES: frozenset[str] = frozenset({
    "spices and herbs",
    "fruits and fruit juices",
    "vegetables and vegetable products",
    "nut and seed products",
    "legumes and legume products",
})


def normalise_category(description: Optional[str]) -> Optional[str]:
    """The stored form. Case and surrounding whitespace are not signal, and
    normalising on the way in means the predicate never has to guess."""
    if description is None:
        return None
    cleaned = " ".join(description.split()).strip()
    return cleaned or None


def is_fvnl_category(description: Optional[str]) -> bool:
    """Whether a food in this category counts toward the HSR fvnl percentage.

    An unknown or missing category is `False` — the conservative answer. It
    costs the recipe fvnl points it might have deserved rather than awarding
    points it didn't, and the caller reports how much of the recipe's weight
    was classified so a thin answer can't pass for a confident one.
    """
    normalised = normalise_category(description)
    return normalised is not None and normalised.lower() in FVNL_CATEGORIES
