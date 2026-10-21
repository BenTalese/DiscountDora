"""e2e for the nutrition auto-matcher — /api/nutrition/unmatched-items and the
bulk accept.

The unit suite (`tests/test_nutrition_suggestions.py`) pins the scoring in
isolation. What only a real request can prove is the part that has already
broken once on this feature: the **repository query path**. The single-item
suggestion runs `contains` / `Or` against real `NutritionFood` rows, the bulk
path reads the catalogue and filters `StockItem` on a nullable FK plus a new
boolean column, and both feed DTOs that the SPA reads by key. A wrong field
name there fails silently as "no suggestions", which looks exactly like a
correctly-restrained matcher.

The mode gate is pinned too: the whole surface must stay invisible on installs
that never turned complex nutrition on.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import requests

from dora_api.app import app
from dora_api.domain.entities.app_setting import (
    NUTRITION_MODE_COMPLEX, NUTRITION_MODE_SIMPLE,
)
from dora_api.domain.entities.nutrition_food import (
    NUTRITION_SOURCE_USDA_SR_LEGACY, NutritionFood,
)
from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from tests.factories import make_stock_item

BASE = "http://localhost:5170/api"
UNMATCHED = f"{BASE}/nutrition/unmatched-items"
ACCEPT_ALL = f"{BASE}/nutrition/suggestions/accept-all"


def _set_mode(mode: str) -> str:
    """Set the install-wide nutrition mode, returning the previous value.

    The suggestion surface is gated on complex mode, and the setting is
    install-wide — so every test here has to put it back, or it leaks into the
    rest of the suite running against the same server.
    """
    with app.app_context():
        repo = SqlAlchemyRepository()
        setting = get_or_create_app_setting(repo)
        previous = setting.nutrition_mode
        setting.nutrition_mode = mode
        # Keep the live sources out of it — the matcher is local-only by
        # design, but the picker's lookup shares this setting and a stray
        # network call would make the suite flaky.
        setting.nutrition_off_lookup_enabled = False
        setting.nutrition_usda_api_key = ""
        repo.save_changes()
    return previous


@pytest.fixture
def complex_mode():
    previous = _set_mode(NUTRITION_MODE_COMPLEX)
    yield
    _set_mode(previous)


def _seed_food(name: str, kcal: float = 89.0) -> str:
    with app.app_context():
        repo = SqlAlchemyRepository()
        food = NutritionFood(
            id=uuid4(), source=NUTRITION_SOURCE_USDA_SR_LEGACY,
            source_ref=f"s-{uuid4().hex[:8]}", name=name, kcal_per_100g=kcal,
            imported_at=datetime.now(timezone.utc),
        )
        repo.add(food)
        repo.save_changes()
        return str(food.id)


def _suffix() -> int:
    """Stock-item names must be unique, but the suffix must not change what the
    item *is*. A digits-only suffix is invisible to the matcher (`tokens()`
    drops digits by design, so "Milk 2%" and "Milk" meet); a hex one would
    smuggle stray letters into the token set and quietly sink every score.
    """
    return uuid4().int % 1_000_000


def _make_stock_item(name: str) -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return make_stock_item(
        stock_level_id=levels[0]["stock_level_id"], name=name,
    )["stock_item_id"]


def _row_for(payload: dict, item_id: str) -> dict | None:
    return next(
        (row for row in payload["items"] if row["stock_item_id"] == item_id), None,
    )


#region ---------------- the mode gate ----------------


def test__unmatched_items__SimpleMode__AnswersEmptyRatherThanSuggesting(api):
    previous = _set_mode(NUTRITION_MODE_SIMPLE)
    try:
        payload = requests.get(UNMATCHED).json()
        # Empty rather than an error: the SPA hides the nav entry in simple
        # mode, and the API saying the same thing keeps the two gates agreeing.
        assert payload["items"] == []
        assert payload["suggested_count"] == 0
    finally:
        _set_mode(previous)


def test__accept_all__SimpleMode__Refused(api):
    previous = _set_mode(NUTRITION_MODE_SIMPLE)
    try:
        assert requests.post(ACCEPT_ALL, json={}).status_code == 400
    finally:
        _set_mode(previous)

#endregion

#region ---------------- suggesting ----------------


def test__unmatched_items__NameMatchesTheCatalogue__IsSuggestedNotLinked(api, complex_mode):
    food_id = _seed_food("Bananas, raw")
    item_id = _make_stock_item(f"Bananas {_suffix()}")

    row = _row_for(requests.get(UNMATCHED).json(), item_id)
    assert row is not None, "an unlinked item must appear in the queue"
    assert row["suggestion"]["nutrition_food_id"] == food_id
    assert row["suggestion"]["source_label"] == "USDA SR Legacy"

    # The critical half: suggesting wrote nothing. The item is still unlinked
    # until a human accepts (P12 No-invent).
    detail = requests.get(f"{BASE}/stock-items/{item_id}/detail").json()
    assert detail["nutrition_food"] is None
    assert detail["nutrition_suggestion"]["nutrition_food_id"] == food_id


def test__unmatched_items__NonFood__ListedWithNoSuggestion(api, complex_mode):
    _seed_food("Bananas, raw")
    item_id = _make_stock_item(f"Toilet paper {_suffix()}")

    row = _row_for(requests.get(UNMATCHED).json(), item_id)
    # Present but unsuggested — the owner's case. It still needs a row so it
    # can be set aside; it just must not be handed a bogus match.
    assert row is not None
    assert row["suggestion"] is None


def test__detail__LinkedItem__CarriesNoSuggestion(api, complex_mode):
    food_id = _seed_food("Bananas, raw")
    item_id = _make_stock_item(f"Bananas {_suffix()}")
    requests.patch(f"{BASE}/stock-items/{item_id}", json={"nutrition_food_id": food_id})

    detail = requests.get(f"{BASE}/stock-items/{item_id}/detail").json()
    assert detail["nutrition_food"]["nutrition_food_id"] == food_id
    # Nothing left to guess about, and a suggestion beside a real link would
    # read as a competing answer.
    assert detail["nutrition_suggestion"] is None
    assert _row_for(requests.get(UNMATCHED).json(), item_id) is None

#endregion

#region ---------------- accepting ----------------


def test__accept__PatchWithTheSuggestedFood__LinksAndLeavesTheQueue(api, complex_mode):
    food_id = _seed_food("Bananas, raw")
    item_id = _make_stock_item(f"Bananas {_suffix()}")

    # Accepting is the ordinary link PATCH — there's no separate accept verb,
    # because a suggestion is only ever a candidate on screen.
    resp = requests.patch(f"{BASE}/stock-items/{item_id}", json={
        "nutrition_food_id": food_id,
    })
    assert resp.status_code in (200, 204), resp.text
    assert _row_for(requests.get(UNMATCHED).json(), item_id) is None


def test__accept_all__ConfidentMatchesOnly__AreLinkedInOneCall(api, complex_mode):
    confident_food = _seed_food("Bananas, raw")
    _seed_food("Chicken, broilers or fryers, breast, meat only, raw")
    confident_item = _make_stock_item(f"Bananas {_suffix()}")
    judgement_item = _make_stock_item(f"Chicken breast {_suffix()}")

    before = requests.get(UNMATCHED).json()
    assert _row_for(before, confident_item)["suggestion"]["is_strong"] is True
    # A heavily-qualified catalogue row is a judgement call, not a certainty.
    assert _row_for(before, judgement_item)["suggestion"]["is_strong"] is False

    resp = requests.post(ACCEPT_ALL, json={})
    assert resp.status_code == 200, resp.text
    assert resp.json()["linked_count"] >= 1

    linked = requests.get(f"{BASE}/stock-items/{confident_item}/detail").json()
    assert linked["nutrition_food"]["nutrition_food_id"] == confident_food
    # The weak one must survive the sweep still needing a human.
    unlinked = requests.get(f"{BASE}/stock-items/{judgement_item}/detail").json()
    assert unlinked["nutrition_food"] is None

#endregion

#region ---------------- ignoring ----------------


def test__ignore__ItemLeavesTheQueueAndIsCounted(api, complex_mode):
    _seed_food("Bananas, raw")
    item_id = _make_stock_item(f"Bananas {_suffix()}")

    resp = requests.patch(f"{BASE}/stock-items/{item_id}", json={"nutrition_ignored": True})
    assert resp.status_code in (200, 204), resp.text

    payload = requests.get(UNMATCHED).json()
    assert _row_for(payload, item_id) is None
    assert payload["ignored_count"] >= 1

    detail = requests.get(f"{BASE}/stock-items/{item_id}/detail").json()
    assert detail["nutrition_ignored"] is True
    # No suggestion for an item that's been waved off — that's the point.
    assert detail["nutrition_suggestion"] is None


def test__ignore__IsReversible(api, complex_mode):
    _seed_food("Bananas, raw")
    item_id = _make_stock_item(f"Bananas {_suffix()}")
    requests.patch(f"{BASE}/stock-items/{item_id}", json={"nutrition_ignored": True})

    listed = requests.get(f"{UNMATCHED}?include_ignored=1").json()
    assert any(
        row["stock_item_id"] == item_id for row in listed["ignored_items"]
    ), "a set-aside item has to remain reachable, or ignoring is a trap"

    requests.patch(f"{BASE}/stock-items/{item_id}", json={"nutrition_ignored": False})
    assert _row_for(requests.get(UNMATCHED).json(), item_id) is not None


def test__link__ClearsAStaleIgnoreFlag(api, complex_mode):
    food_id = _seed_food("Bananas, raw")
    item_id = _make_stock_item(f"Bananas {_suffix()}")
    requests.patch(f"{BASE}/stock-items/{item_id}", json={"nutrition_ignored": True})

    requests.patch(f"{BASE}/stock-items/{item_id}", json={"nutrition_food_id": food_id})

    detail = requests.get(f"{BASE}/stock-items/{item_id}/detail").json()
    # Linking a food and ignoring the item are contradictory answers to the
    # same question; the explicit link wins and the stale flag goes.
    assert detail["nutrition_food"]["nutrition_food_id"] == food_id
    assert detail["nutrition_ignored"] is False

#endregion


#region ---------------- catalogue-size reporting ----------------

def test__unmatched_items__ReportsCatalogueSize__SoAnEmptyOneIsDistinguishable(
    api, complex_mode,
):
    """The regression this exists to prevent is a *support* one, not a code one.

    The matcher reads the local catalogue and nothing else, so an install with
    no dataset downloaded suggests nothing — which renders identically to "every
    item is already matched" and gets reported as a broken feature. The count
    travels so the page can tell those two apart and say which one it is.
    """
    _seed_food("Bananas, raw")
    payload = requests.get(UNMATCHED).json()

    assert payload["catalogue_size"] >= 1
    # Not merely present — it has to track the catalogue, or the empty-state
    # banner would key off a constant.
    _seed_food(f"Rice, white, long-grain {_suffix()}")
    assert requests.get(UNMATCHED).json()["catalogue_size"] > payload["catalogue_size"]


def test__unmatched_items__SimpleMode__ReportsZeroCatalogue(api):
    previous = _set_mode(NUTRITION_MODE_SIMPLE)
    try:
        # The short-circuit branch has to carry the key too — a missing field
        # reads as `undefined` in the SPA, which is not `=== 0`, so the banner
        # would silently never fire.
        assert requests.get(UNMATCHED).json()["catalogue_size"] == 0
    finally:
        _set_mode(previous)

#endregion
