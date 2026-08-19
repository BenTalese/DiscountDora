"""Server-owned recipe cost estimation (R-003 — one definition of "what a
recipe costs", never duplicated on the client or across features).

Extracted from `get_recipes._compute_estimated_cost` (C-4 Chunk 9 / DEC-5) so
both the recipe-detail endpoint and the FU-451 budget-defense swap ranker
price recipes the same way. The single-recipe path preserves the original
behaviour exactly; the batch path prices many recipes in **two queries total**
(one offer lookup, one observation fallback) rather than 2×N — important for
the swap ranker, which costs the whole candidate pool at once.

Pricing ladder per ingredient (PROPOSAL §3.2):
  1. cheapest linked-product current offer → unit price (price_now / size_value)
  2. else the stock item's price-observation unit cost (FU-216 substrate)
  3. else unpriced (contributes nothing; surfaced via the priced/total ratio)

**Unit reconciliation (feedback 2026-08-19).** It used to be pass-through —
the ingredient quantity was multiplied by the unit price whatever the two
units were. That is not a rough heuristic, it's a category error: a price of
"$4.20 per bottle" times "200 ml" produced $840, and the seed's two-ingredient
Juice Bowl reported **$1590**. Every price now carries the unit it is per, the
ingredient quantity is converted into that unit, and an ingredient whose units
can't bridge (200 ml of a thing priced per bottle — we don't know the bottle's
size) is reported **unpriced** rather than guessed at. Unpriced ingredients
already have a home in the UI: the "N of M priced" ratio. An honest gap beats
a confident wrong number.
"""
from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from dora_api.domain import units
from dora_api.domain.entities.stock_item_price_observation import \
    StockItemPriceObservation
from dora_api.domain.stock_status import \
    get_stock_item_unit_cost_with_unit_at
from dora_api.persistence.field import EntityField

# Why an ingredient contributed nothing — surfaced per line in the recipe
# page's expandable cost breakdown, so "why is this estimate low?" is
# answerable without reading the code.
UNPRICED_NO_LINK = "no_link"            # ingredient isn't linked to a stock item
UNPRICED_NO_PRICE = "no_price"          # linked, but no offer and no observation
UNPRICED_UNIT_MISMATCH = "unit_mismatch"  # priced, but the units can't bridge


@dataclass(frozen=True, slots=True)
class UnitPrice:
    """A price and the unit it is *per*. The unit is the half that used to be
    dropped on the floor.

    `pack_amount` is the price of one whole item where that's known — a 400 g
    tin at $1.20 has `amount=0.003 per g` **and** `pack_amount=1.20`. Recipes
    are written both ways ("400 g of tomatoes", "2 tins of tomatoes") and only
    one of the two prices can answer each.
    """
    amount: float
    unit: str
    pack_amount: float | None = None


@dataclass(frozen=True, slots=True)
class CostLine:
    """One ingredient's contribution, for the breakdown UI. `line_cost` is
    None exactly when `reason` is set."""
    name: str
    quantity: float | None
    unit: str | None
    unit_price: float | None
    priced_unit: str | None
    line_cost: float | None
    reason: str | None


@dataclass(frozen=True, slots=True)
class CostEstimate:
    """Per-recipe result. `estimated_cost` is None when nothing priced."""
    estimated_cost: float | None
    priced_count: int
    total_count: int
    lines: tuple[CostLine, ...] = ()


def _key(v) -> str:
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, bytes):
        return str(UUID(bytes=v))
    return str(v)


def _unit_price_map(repository, stock_item_ids: list) -> tuple[dict, dict]:
    """(offer_unit_price_by_item, observation_unit_cost_by_item) keyed by the
    stringified stock-item id. One offer query + one observation query."""
    from sqlalchemy import func, select
    from dora_api.app import db

    if not stock_item_ids:
        return {}, {}

    link_table = db.metadata.tables["StockItemProduct"]
    product_table = db.metadata.tables["Product"]
    offer_table = db.metadata.tables["ProductOffer"]

    stmt = (
        select(
            link_table.c.stock_item_id,
            product_table.c.size_value,
            product_table.c.size_unit,
            func.min(offer_table.c.price_now).label("price_now"),
        )
        .select_from(
            link_table
            .join(product_table, product_table.c.id == link_table.c.product_id)
            .join(offer_table, offer_table.c.product_id == product_table.c.id)
        )
        .where(
            link_table.c.stock_item_id.in_(stock_item_ids),
            product_table.c.is_active.is_(True),
            offer_table.c.price_now.isnot(None),
        )
        .group_by(
            link_table.c.stock_item_id,
            product_table.c.size_value,
            product_table.c.size_unit,
        )
    )
    offer_by_item: dict[str, UnitPrice] = {}
    for sid, size_value, size_unit, price in db.session.execute(stmt).all():
        if price is None:
            continue
        # A sized product prices per its own size unit ("$5 / 1000 g" → $/g);
        # a sizeless one prices per item, which is a count of "ea". Either
        # way the offer price itself is what one of them costs on the shelf,
        # so it's always the pack price.
        if size_value and float(size_value) > 0 and size_unit:
            unit_price = UnitPrice(
                float(price) / float(size_value), str(size_unit), float(price),
            )
        else:
            unit_price = UnitPrice(float(price), "ea", float(price))
        prev = offer_by_item.get(_key(sid))
        if prev is None or _cheaper(unit_price, prev):
            offer_by_item[_key(sid)] = unit_price

    # Observation fallback: one query, grouped per item, delegated to the
    # server-owned per-unit cost helper (R-003).
    obs_by_item: dict[str, list] = {}
    for obs in repository.get(StockItemPriceObservation).all(
        EntityField(StockItemPriceObservation, "stock_item_id").in_(stock_item_ids)
    ):
        obs_by_item.setdefault(_key(obs.stock_item_id), []).append(obs)
    obs_cost_by_item: dict[str, UnitPrice] = {}
    for sid_key, obs_list in obs_by_item.items():
        cost = get_stock_item_unit_cost_with_unit_at(obs_list)
        if cost is None:
            continue
        # A count observation ("$9 for 3 punnets") already *is* a per-item
        # price. A measure observation ("$6 for 4 L") spans an unknown number
        # of packs, so it can't yield one.
        found = units.find_unit(cost.unit)
        pack = cost.amount if found is not None and found.dimension == units.COUNT else None
        obs_cost_by_item[sid_key] = UnitPrice(cost.amount, cost.unit, pack)

    return offer_by_item, obs_cost_by_item


def _cheaper(candidate: UnitPrice, incumbent: UnitPrice) -> bool:
    """Is *candidate* the better price? Only comparable within one dimension —
    "$0.004 per g" and "$2.50 per ea" are not two numbers on the same scale, so
    when the dimensions differ (or a unit is unrecognised) the incumbent stands
    and the choice stays deterministic rather than arbitrary."""
    src = units.find_unit(candidate.unit)
    dst = units.find_unit(incumbent.unit)
    if src is None or dst is None or src.dimension != dst.dimension:
        return False
    # Normalise both to the dimension's base unit before comparing.
    return (candidate.amount / src.factor) < (incumbent.amount / dst.factor)


def _line_cost(ingredient, price: UnitPrice) -> float | None:
    """What this ingredient contributes, or None when it can't be priced.

    Recipes measure ingredients two different ways and each needs a different
    half of the price:

    * **By measure** — "400 g of tomatoes", "2 cups of juice". Convert the
      quantity into the unit the price is per, then multiply. A conversion
      that can't bridge dimensions (200 ml of a thing priced per bottle: we
      don't know the bottle's size) is **unpriced**. Guessing here is what
      produced the $1590 Juice Bowl.
    * **By the item** — "2 tins", "1 onion", or a bare "2". Multiply by the
      price of one whole item. Deliberately permissive about the unit itself:
      "tins" and "cloves" aren't units we know, and don't need to be, because
      the count is all the arithmetic needs.
    """
    qty = float(ingredient.quantity) if ingredient.quantity is not None else 1.0
    ing_unit = (getattr(ingredient, "unit", None) or "").strip()
    ing_def = units.find_unit(ing_unit) if ing_unit else None

    measured = ing_def is not None and ing_def.dimension != units.COUNT
    if measured:
        if units.normalise_unit(ing_unit) == units.normalise_unit(price.unit):
            return qty * price.amount
        converted = units.convert(qty, ing_unit, price.unit)
        return None if converted is None else converted * price.amount

    # Counted (no unit, an unrecognised unit, or an explicit count unit).
    if ing_def is not None and ing_def.dimension == units.COUNT:
        qty *= ing_def.factor          # "1 dozen" is twelve items
    return None if price.pack_amount is None else qty * price.pack_amount


def _line_name(ingredient) -> str:
    """Display name for the breakdown. The batch path is fed entities that
    may not carry the joined stock-item name; the detail path is fed DTOs
    that always do."""
    return getattr(ingredient, "stock_item_name", None) or "Ingredient"


def _unpriced_line(ingredient, reason: str, price: UnitPrice | None) -> CostLine:
    return CostLine(
        name=_line_name(ingredient),
        quantity=float(ingredient.quantity) if ingredient.quantity is not None else None,
        unit=getattr(ingredient, "unit", None),
        unit_price=price.amount if price is not None else None,
        priced_unit=price.unit if price is not None else None,
        line_cost=None,
        reason=reason,
    )


def _cost_one(ingredients, offer_by_item: dict, obs_cost_by_item: dict) -> CostEstimate:
    total = 0.0
    priced = 0
    lines: list[CostLine] = []
    for ing in ingredients:
        if ing.stock_item_id is None:
            lines.append(_unpriced_line(ing, UNPRICED_NO_LINK, None))
            continue
        sid = _key(ing.stock_item_id)
        unit_price = offer_by_item.get(sid) or obs_cost_by_item.get(sid)
        if unit_price is None:
            lines.append(_unpriced_line(ing, UNPRICED_NO_PRICE, None))
            continue
        line_cost = _line_cost(ing, unit_price)
        if line_cost is None:
            lines.append(_unpriced_line(ing, UNPRICED_UNIT_MISMATCH, unit_price))
            continue
        total += line_cost
        priced += 1
        lines.append(CostLine(
            name=_line_name(ing),
            quantity=float(ing.quantity) if ing.quantity is not None else None,
            unit=getattr(ing, "unit", None),
            unit_price=unit_price.amount,
            priced_unit=unit_price.unit,
            line_cost=round(line_cost, 2),
            reason=None,
        ))

    linked_count = sum(1 for i in ingredients if i.stock_item_id is not None)
    return CostEstimate(
        estimated_cost=round(total, 2) if priced > 0 else None,
        priced_count=priced,
        total_count=linked_count,
        lines=tuple(lines),
    )


def estimate_costs_for(repository, recipes: Iterable) -> dict:
    """Batch: `recipe_id (UUID) → CostEstimate` for every recipe passed. Each
    recipe must expose `.recipe_id` and `.ingredients` (each ingredient with
    `.stock_item_id` and `.quantity`). Two queries total."""
    recipes = list(recipes)
    all_ids: list = []
    for r in recipes:
        for ing in (r.ingredients or []):
            if ing.stock_item_id is not None:
                all_ids.append(ing.stock_item_id)
    offer_by_item, obs_cost_by_item = _unit_price_map(repository, all_ids)
    return {
        r.recipe_id: _cost_one(r.ingredients or [], offer_by_item, obs_cost_by_item)
        for r in recipes
    }


def estimate_cost_for_ingredients(repository, ingredients) -> CostEstimate:
    """Single-recipe path used by the recipe-detail endpoint. `ingredients`
    is a list with `.stock_item_id` + `.quantity`."""
    ingredients = list(ingredients)
    ids = [i.stock_item_id for i in ingredients if i.stock_item_id is not None]
    offer_by_item, obs_cost_by_item = _unit_price_map(repository, ids)
    # total_count preserves the original behaviour: it counted *all* dto
    # ingredients (the detail endpoint only ever passes linked-or-null rows and
    # reported len(ingredients)); keep that contract for the caller.
    est = _cost_one(ingredients, offer_by_item, obs_cost_by_item)
    return CostEstimate(
        estimated_cost=est.estimated_cost,
        priced_count=est.priced_count,
        total_count=len(ingredients),
        lines=est.lines,
    )
