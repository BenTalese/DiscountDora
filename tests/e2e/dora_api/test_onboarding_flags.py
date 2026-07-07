"""FU-193 — backend behavioural coverage for the Onboarding C-5.3/.4/.5 surfaces.

Covers products data-presence gating (FU-209), the per-user household headcount,
and the starter catalogue + name-resolved item seeding. Migrations themselves are
verified separately (single head + well-formed batch DDL); these tests assert
the runtime round-trips that the wizard relies on.
"""
import uuid

import requests

BASE = "http://localhost:5170/api"
HEALTH = f"{BASE}/health"
APP_SETTINGS = f"{BASE}/app-settings"
ME = f"{BASE}/auth/me"
CATALOG = f"{BASE}/onboarding/catalog"
SEED_ITEMS = f"{BASE}/onboarding/seed-items"
SEED_DEMO = f"{BASE}/onboarding/seed-demo"
STOCK_ITEMS = f"{BASE}/stock-items"
RECIPES = f"{BASE}/recipes"
MEAL_PLANS = f"{BASE}/meal-plans"


# ── products data-presence gate (FU-209) ────────────────────────────


def test__health__products_flag_reflects_data_presence(api):
    # Products is a data-presence overlay (PROPOSAL_PRODUCTS_AS_OVERLAY): the
    # flag is true iff product rows exist — there is no admin/user toggle.
    flags = requests.get(HEALTH).json()["features"]
    body = requests.get(f"{BASE}/products").json()
    items = body["items"] if isinstance(body, dict) and "items" in body else body
    assert flags["products"] is (len(items) > 0)


def test__app_settings__no_longer_carries_products_enabled(api):
    # GET must not expose it, and PATCHing it is
    # rejected by the request model (extra="forbid").
    assert "products_enabled" not in requests.get(APP_SETTINGS).json()
    rejected = requests.patch(APP_SETTINGS, json={"products_enabled": True})
    assert 400 <= rejected.status_code < 500


# ── C-5.4 household headcount ─────────────────────────────────────────


def test__users_me__household_headcount_roundtrips(api):
    original = requests.get(ME).json().get("household_headcount")
    try:
        assert requests.patch(ME, json={"household_headcount": 4}).status_code == 200
        assert requests.get(ME).json()["household_headcount"] == 4
        # null clears it back to "not set" (cook mode then falls back to servings).
        assert requests.patch(ME, json={"household_headcount": None}).status_code == 200
        assert requests.get(ME).json()["household_headcount"] is None
    finally:
        requests.patch(ME, json={"household_headcount": original})


def test__users_me__household_headcount_out_of_range_rejected(api):
    assert requests.patch(ME, json={"household_headcount": 0}).status_code == 400
    assert requests.patch(ME, json={"household_headcount": 100}).status_code == 400


# ── C-5.5 starter catalogue + name-resolved seeding ──────────────────


def test__onboarding_catalog__serialises_groups_locations_packs(api):
    body = requests.get(CATALOG).json()
    assert isinstance(body["groups"], list) and body["groups"]
    assert isinstance(body["locations"], list) and body["locations"]
    # Nested location nodes carry name/kind/children.
    first_zone = body["locations"][0]
    assert {"name", "kind", "children"} <= set(first_zone.keys())
    # 5 starter packs ship in starter_packs.json.
    assert len(body["packs"]) == 5
    pack = body["packs"][0]
    assert {"key", "label", "blurb", "items"} <= set(pack.keys())


def test__onboarding_seed_items__creates_prelocated_and_dedupes(api):
    groups = requests.get(f"{BASE}/stock-groups").json()
    locations = requests.get(f"{BASE}/stock-locations").json()["items"]
    assert groups and locations, "seed DB has groups + locations to resolve against"
    group_name = groups[0]["name"]
    location_name = locations[0]["name"]

    unique_name = f"FU193SeedItem-{uuid.uuid4().hex[:8]}"
    payload = {
        "items": [
            {
                "name": unique_name,
                "group_name": group_name,
                "location_name": location_name,
            }
        ]
    }

    first = requests.post(SEED_ITEMS, json=payload)
    assert first.status_code == 200
    assert first.json() == {"created": 1, "skipped": 0}

    # The item is created pre-located: group + location resolved by name.
    created = requests.get(f"{STOCK_ITEMS}?filter=name:eq:{unique_name}").json()["items"]
    assert len(created) == 1
    item = created[0]
    assert item["stock_group_id"] == groups[0]["stock_group_id"]
    assert item["stock_location_id"] == locations[0]["stock_location_id"]

    # Re-running Finish must not duplicate: same name is skipped.
    second = requests.post(SEED_ITEMS, json=payload)
    assert second.status_code == 200
    assert second.json() == {"created": 0, "skipped": 1}
    still_one = requests.get(f"{STOCK_ITEMS}?filter=name:eq:{unique_name}").json()["items"]
    assert len(still_one) == 1


# ── FU-194 demo dataset toggle ───────────────────────────────────────


def test__onboarding_seed_demo__is_idempotent(api):
    # The dev seed already ships an "Spaghetti Aglio e Olio" recipe, so the
    # first call here lands as a no-op (`seeded: false`) AND a second call
    # behaves identically — that's the contract: never duplicate.
    first = requests.post(SEED_DEMO)
    assert first.status_code == 200
    body_one = first.json()
    assert set(body_one.keys()) == {
        "seeded", "items_created", "recipe_created", "meal_plan_created",
    }
    # On a freshly-seeded DB the recipe already exists, so seeded=False;
    # on a clean DB (no seed) it'd be seeded=True with recipe_created=True.
    # Whichever branch we landed in, a second call must match exactly.
    second = requests.post(SEED_DEMO)
    assert second.status_code == 200
    assert second.json() == body_one
    # Either way, exactly one recipe by that name exists afterward.
    recipes = requests.get(RECIPES).json().get("items", [])
    matches = [r for r in recipes if r.get("name") == "Spaghetti Aglio e Olio"]
    assert len(matches) == 1
