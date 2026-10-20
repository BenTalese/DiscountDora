"""FU-872 — `load_recipe_cookability` must not depend on what the request loaded first.

`StockItem.stock_level` is `lazy="noload"`. When the helper relied on an eager
include, a StockItem already in the session came back from the identity map
with the level unset, so every ingredient read as missing. Kitchen health then
said none of the planned meals could be cooked beside a card offering five.
"""
from uuid import UUID, uuid4

import requests

from dora_api.app import app, db
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.recipes.get_recipes import load_recipe_cookability
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from tests.factories import make_stock_item

BASE = "http://localhost:5170/api"


def _level_id(sequence: int) -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l["stock_level_id"] for l in levels if l["sequence"] == sequence)


def _recipe_with(stock_item_id: str) -> UUID:
    resp = requests.post(f"{BASE}/recipes", json={
        "name": f"cookability-{uuid4().hex[:8]}",
        "ingredients": [{"stock_item_id": stock_item_id, "quantity": 1}],
    })
    assert resp.status_code == 201, resp.text
    return UUID(resp.json()["recipe_id"])


def test__cookability__same_answer_after_stock_items_are_in_the_session(api):
    stocked = make_stock_item(stock_level_id=_level_id(0), name=f"In-{uuid4().hex[:6]}")
    out = make_stock_item(stock_level_id=_level_id(2), name=f"Out-{uuid4().hex[:6]}")
    stocked_recipe = _recipe_with(stocked["stock_item_id"])
    out_recipe = _recipe_with(out["stock_item_id"])

    with app.app_context():
        # Start from an empty identity map so the create calls above can't
        # leave hydrated instances behind, then do what the Dora score's
        # Freshness block did: a bare load, which pins `stock_level = None`.
        # The identity map is weak, so the list has to stay referenced.
        db.session.expunge_all()
        repository = SqlAlchemyRepository()
        held = repository.get(StockItem).all()
        cookability = load_recipe_cookability(repository)
        del held

    assert cookability[stocked_recipe] == (0, 1, 0)
    assert cookability[out_recipe] == (1, 1, 0)
