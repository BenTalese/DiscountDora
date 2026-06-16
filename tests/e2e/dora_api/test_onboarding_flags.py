"""FU-193 — backend behavioural coverage for the Onboarding C-5.3/.4/.5 surfaces.

Covers the install/products flag, the per-user household headcount, and the
starter catalogue + name-resolved item seeding. Migrations themselves are
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
STOCK_ITEMS = f"{BASE}/stock-items"


# ── C-5.3 products flag ──────────────────────────────────────────────


def test__health__products_flag_defaults_true(api):
    flags = requests.get(HEALTH).json()["features"]
    assert flags["products"] is True


def test__app_settings__products_enabled_roundtrips_and_health_reflects(api):
    original = requests.get(APP_SETTINGS).json()["products_enabled"]
    assert original is True, "existing installs default products on"
    try:
        patched = requests.patch(APP_SETTINGS, json={"products_enabled": False})
        assert patched.status_code == 200
        assert patched.json()["products_enabled"] is False
        assert requests.get(APP_SETTINGS).json()["products_enabled"] is False
        # The flag is the single source of truth: /health must agree.
        assert requests.get(HEALTH).json()["features"]["products"] is False
    finally:
        assert requests.patch(
            APP_SETTINGS, json={"products_enabled": original}
        ).status_code == 200
    assert requests.get(HEALTH).json()["features"]["products"] is True


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
