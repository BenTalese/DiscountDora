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

Ingredient-unit vs product-unit reconciliation is pass-through — the documented
rough heuristic; the number is always surfaced to users as an *estimate*.
"""
from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from dora_api.domain.entities.stock_item_price_observation import \
    StockItemPriceObservation
from dora_api.domain.stock_status import get_stock_item_unit_cost_at
from dora_api.persistence.field import EntityField


@dataclass(frozen=True, slots=True)
class CostEstimate:
    """Per-recipe result. `estimated_cost` is None when nothing priced."""
    estimated_cost: float | None
    priced_count: int
    total_count: int


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
        .group_by(link_table.c.stock_item_id, product_table.c.size_value)
    )
    offer_by_item: dict[str, float] = {}
    for sid, size_value, price in db.session.execute(stmt).all():
        if price is None:
            continue
        unit_price = float(price) / float(size_value) if size_value else float(price)
        prev = offer_by_item.get(_key(sid))
        if prev is None or unit_price < prev:
            offer_by_item[_key(sid)] = unit_price

    # Observation fallback: one query, grouped per item, delegated to the
    # server-owned per-unit cost helper (R-003).
    obs_by_item: dict[str, list] = {}
    for obs in repository.get(StockItemPriceObservation).all(
        EntityField(StockItemPriceObservation, "stock_item_id").in_(stock_item_ids)
    ):
        obs_by_item.setdefault(_key(obs.stock_item_id), []).append(obs)
    obs_cost_by_item: dict[str, float] = {}
    for sid_key, obs_list in obs_by_item.items():
        cost = get_stock_item_unit_cost_at(obs_list)
        if cost is not None:
            obs_cost_by_item[sid_key] = cost

    return offer_by_item, obs_cost_by_item


def _cost_one(ingredients, offer_by_item: dict, obs_cost_by_item: dict) -> CostEstimate:
    linked = [i for i in ingredients if i.stock_item_id is not None]
    if not linked:
        return CostEstimate(estimated_cost=None, priced_count=0, total_count=len(ingredients))
    total = 0.0
    priced = 0
    for ing in linked:
        sid = _key(ing.stock_item_id)
        unit_price = offer_by_item.get(sid)
        if unit_price is None:
            unit_price = obs_cost_by_item.get(sid)
        if unit_price is None:
            continue
        qty = float(ing.quantity) if ing.quantity is not None else 1.0
        total += qty * unit_price
        priced += 1
    return CostEstimate(
        estimated_cost=round(total, 2) if priced > 0 else None,
        priced_count=priced,
        total_count=len(linked),
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
    ids = [i.stock_item_id for i in ingredients if i.stock_item_id is not None]
    offer_by_item, obs_cost_by_item = _unit_price_map(repository, ids)
    # total_count preserves the original behaviour: it counted *all* dto
    # ingredients (the detail endpoint only ever passes linked-or-null rows and
    # reported len(ingredients)); keep that contract for the caller.
    est = _cost_one(ingredients, offer_by_item, obs_cost_by_item)
    return CostEstimate(
        estimated_cost=est.estimated_cost,
        priced_count=est.priced_count,
        total_count=len(list(ingredients)),
    )
