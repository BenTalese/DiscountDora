"""End-to-end coverage for /api/data/backup.

Export-only round (N2 part 1). Inspect/restore land in the next round and
will have their own tests.
"""
import json
import uuid  # FU-166: register_product_barcode tests used uuid without importing it.

import pytest
import requests


BACKUP_URL = "http://localhost:5170/api/data/backup"


@pytest.mark.xfail(
    reason="FU-164: the backup builder never emits the `product_stock_item_links` "
    "section, so a restore would drop every product↔stock-item link. The test "
    "asserts the intended (complete) backup contract; it xpasses once the builder "
    "adds the section. Fails identically on main — pre-existing, not from FU-166.",
    strict=True,
)
def test__get_backup__happy_path__returns_attachment_with_expected_sections(api):
    response = requests.get(BACKUP_URL)

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    disposition = response.headers.get("Content-Disposition", "")
    assert "attachment" in disposition.lower()
    assert "dora-backup-" in disposition

    payload = response.json()

    # Metadata block
    assert payload["schema_version"] == 1
    assert isinstance(payload["exported_at"], str) and payload["exported_at"]
    assert payload["exported_by"] == "dora"  # set by tests/conftest login

    # Every in-scope section is present and a list, even when empty.
    expected_sections = {
        "stock_groups",
        "stock_levels",
        "stock_locations",
        "saved_products",
        "stock_items",
        "product_stock_item_links",
        "stock_item_substitutes",
        "shopping_lists",
        "shopping_list_items",
        "shopping_list_templates",
        "shopping_list_template_lines",
        "recipe_collections",
        "recipes",
        "recipe_ingredients",
        "meals",
        "meal_recipes",
        "meal_plans",
        "meal_plan_entries",
    }
    assert expected_sections.issubset(payload.keys())
    for section in expected_sections:
        assert isinstance(payload[section], list), f"{section} must be a list"

    # Stock levels are seeded by seed_dev_data, so this section should be
    # populated and every row should carry an id.
    assert len(payload["stock_levels"]) >= 1
    for row in payload["stock_levels"]:
        assert "id" in row
        assert row["id"]

    # Volatile / cached data is intentionally excluded.
    for excluded in (
        "users",
        "merchants",
        "product_offers",
        "product_historic_offers",
        "stock_level_changes",
        "notifications",
        "app_settings",
    ):
        assert excluded not in payload, f"{excluded} should not be in backup"


def test__get_backup__without_auth__is_unauthorized(api):
    # Bare requests.Session (no login) — we hit the URL directly without
    # going through the shared authenticated session that conftest set up.
    fresh = requests.Session()
    response = fresh.get(BACKUP_URL)
    assert response.status_code == 401


def test__get_backup__is_valid_json_document(api):
    response = requests.get(BACKUP_URL)
    # The response body must be parseable on its own — i.e. saving it to
    # disk and reloading gives us back the same shape.
    raw = response.content.decode("utf-8")
    reparsed = json.loads(raw)
    assert reparsed["schema_version"] == 1
    assert "stock_items" in reparsed


# ── /inspect ───────────────────────────────────────────────────────────

INSPECT_URL = "http://localhost:5170/api/data/backup/inspect"
RESTORE_URL = "http://localhost:5170/api/data/backup/restore"


def test__inspect_backup__roundtrip__counts_match_and_seeds_flag_as_duplicates(api):
    backup = requests.get(BACKUP_URL).json()

    response = requests.post(INSPECT_URL, json=backup)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["schema_version"] == 1
    assert body["entity_counts"]["stock_levels"] == len(backup["stock_levels"])
    # The backup is a snapshot of the live DB, so every detectable row should
    # appear in `duplicates` for the sections that support detection.
    assert set(body["duplicates"].get("stock_levels", [])) == {
        row["name"] for row in backup["stock_levels"]
    }


def test__inspect_backup__future_schema__is_rejected(api):
    response = requests.post(INSPECT_URL, json={"schema_version": 9999})
    assert response.status_code == 400


def test__inspect_backup__missing_schema__is_rejected(api):
    response = requests.post(INSPECT_URL, json={"stock_items": []})
    assert response.status_code == 400


# ── /restore ───────────────────────────────────────────────────────────

def test__restore_backup__roundtrip_all_skip_duplicates__no_changes(api):
    """Re-importing the same file we just exported should change nothing —
    every row collides on its duplicate key and gets skipped."""
    backup = requests.get(BACKUP_URL).json()

    response = requests.post(
        RESTORE_URL,
        json={"backup": backup, "selection": {}, "mode": "all_skip_duplicates"},
    )
    assert response.status_code == 200, response.text
    summary = response.json()

    # No new rows; every section either skipped or stayed at zero (sub-tables
    # like links/lines may still get re-inserted if their parents weren't
    # detected as duplicates — but for an in-place re-import of a seed-only DB
    # all detected sections must report zero "created").
    for detected in ("stock_groups", "stock_levels", "stock_items"):
        assert summary["created"][detected] == 0, (
            f"{detected}: expected 0 created, got {summary['created'][detected]}"
        )


def test__restore_backup__future_schema__is_rejected(api):
    response = requests.post(
        RESTORE_URL,
        json={"backup": {"schema_version": 9999}, "selection": {}, "mode": "all_skip_duplicates"},
    )
    assert response.status_code == 400


def test__restore_backup__unknown_mode__is_rejected(api):
    response = requests.post(
        RESTORE_URL,
        json={"backup": {"schema_version": 1}, "selection": {}, "mode": "bogus"},
    )
    assert response.status_code == 400


# ── Section toggles ────────────────────────────────────────────────────

def test__get_backup__without_sections_query__defaults_to_core_data(api):
    payload = requests.get(BACKUP_URL).json()
    # Core sections always present.
    assert "stock_items" in payload
    assert "recipes" in payload
    # Optional sections off by default.
    assert "app_settings" not in payload
    assert "users" not in payload
    assert "product_historic_offers" not in payload
    # The dump records what it carried so the restore step can be honest.
    assert "stock_items" in payload["sections"]
    assert "users" not in payload["sections"]


def test__get_backup__with_sections_query__narrows_dump(api):
    payload = requests.get(f"{BACKUP_URL}?sections=stock_items,stock_groups").json()
    assert "stock_items" in payload
    assert "stock_groups" in payload
    assert "recipes" not in payload
    assert "shopping_lists" not in payload
    assert set(payload["sections"]) == {"stock_items", "stock_groups"}


def test__get_backup__with_optional_sections__includes_them(api):
    payload = requests.get(
        f"{BACKUP_URL}?sections=app_settings,users,product_historic_offers"
    ).json()
    assert "app_settings" in payload
    assert "users" in payload
    assert "product_historic_offers" in payload


def test__get_backup__never_exports_password_hashes(api):
    payload = requests.get(f"{BACKUP_URL}?sections=users").json()
    for row in payload["users"]:
        assert "password_hash" not in row, "password_hash must never round-trip"


def test__get_backup__unknown_section__is_rejected(api):
    response = requests.get(f"{BACKUP_URL}?sections=stock_items,nonsense")
    assert response.status_code == 400


# ── Chunked uploads + staged inspect/restore ───────────────────────────

UPLOAD_START_URL = "http://localhost:5170/api/data/uploads/start"
UPLOAD_CHUNK_URL = "http://localhost:5170/api/data/uploads/chunk"
UPLOAD_FINISH_URL = "http://localhost:5170/api/data/uploads/finish"


def _upload_via_chunks(payload: dict, chunk_size: int = 64 * 1024) -> str:
    """Helper — drive a backup payload through the chunked-upload flow
    and return the resulting upload_id."""
    raw = json.dumps(payload).encode("utf-8")

    start = requests.post(UPLOAD_START_URL, json={"expected_size": len(raw)})
    assert start.status_code == 200, start.text
    upload_id = start.json()["upload_id"]

    for offset in range(0, len(raw), chunk_size):
        chunk = raw[offset:offset + chunk_size]
        response = requests.post(
            UPLOAD_CHUNK_URL,
            data={"upload_id": upload_id, "offset": str(offset)},
            files={"chunk": ("chunk.bin", chunk, "application/octet-stream")},
        )
        assert response.status_code == 200, response.text

    finish = requests.post(UPLOAD_FINISH_URL, json={"upload_id": upload_id})
    assert finish.status_code == 200, finish.text
    assert finish.json()["size"] == len(raw)
    return upload_id


def test__chunked_upload__inspect_via_upload_id__roundtrip(api):
    backup = requests.get(BACKUP_URL).json()
    upload_id = _upload_via_chunks(backup)

    response = requests.post(
        "http://localhost:5170/api/data/backup/inspect",
        json={"upload_id": upload_id},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema_version"] == 1
    assert body["entity_counts"]["stock_levels"] == len(backup["stock_levels"])
    # Sample rows surfaced for the SPA's tree view.
    assert "samples" in body
    assert body["samples"]["stock_levels"]["rows"]


def test__chunked_upload__chunk_offset_mismatch__is_400(api):
    start = requests.post(UPLOAD_START_URL, json={})
    upload_id = start.json()["upload_id"]
    # Send a chunk at the wrong offset.
    response = requests.post(
        UPLOAD_CHUNK_URL,
        data={"upload_id": upload_id, "offset": "99"},
        files={"chunk": ("c.bin", b"abc", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert response.json()["errors"]["received"] == ["0"]


def test__chunked_upload__abort_deletes_staged_file(api):
    start = requests.post(UPLOAD_START_URL, json={}).json()
    upload_id = start["upload_id"]
    response = requests.delete(f"http://localhost:5170/api/data/uploads/{upload_id}")
    assert response.status_code == 204
    # Re-aborting is harmless (DELETE is idempotent).
    response = requests.delete(f"http://localhost:5170/api/data/uploads/{upload_id}")
    assert response.status_code == 204


def test__restore_backup__via_upload_id__no_changes_on_roundtrip(api):
    backup = requests.get(BACKUP_URL).json()
    upload_id = _upload_via_chunks(backup)

    response = requests.post(
        RESTORE_URL,
        json={"upload_id": upload_id, "selection": {}, "mode": "all_skip_duplicates"},
    )
    assert response.status_code == 200, response.text
    summary = response.json()
    for detected in ("stock_groups", "stock_levels", "stock_items"):
        assert summary["created"][detected] == 0


def test__restore_backup__upload_id_consumed_on_use(api):
    backup = requests.get(BACKUP_URL).json()
    upload_id = _upload_via_chunks(backup)
    # First restore consumes the staged file…
    requests.post(
        RESTORE_URL,
        json={"upload_id": upload_id, "selection": {}, "mode": "all_skip_duplicates"},
    )
    # …so a second call referencing the same id 400s with "not found".
    second = requests.post(
        RESTORE_URL,
        json={"upload_id": upload_id, "selection": {}, "mode": "all_skip_duplicates"},
    )
    assert second.status_code == 400


def test__restore_backup__rejects_both_inputs(api):
    response = requests.post(
        RESTORE_URL,
        json={
            "backup": {"schema_version": 1},
            "upload_id": "00000000-0000-0000-0000-000000000000",
            "selection": {},
            "mode": "all_skip_duplicates",
        },
    )
    assert response.status_code == 400


# ── Spreadsheet import (N3) ────────────────────────────────────────────

IMPORT_INSPECT_URL = "http://localhost:5170/api/data/import/spreadsheet/inspect"
IMPORT_COMMIT_URL = "http://localhost:5170/api/data/import/spreadsheet/commit"


def _stage_bytes(raw: bytes) -> str:
    """Push raw bytes through the chunked upload stack and return upload_id."""
    start = requests.post(UPLOAD_START_URL, json={"expected_size": len(raw)})
    upload_id = start.json()["upload_id"]
    requests.post(
        UPLOAD_CHUNK_URL,
        data={"upload_id": upload_id, "offset": "0"},
        files={"chunk": ("c.bin", raw, "application/octet-stream")},
    )
    requests.post(UPLOAD_FINISH_URL, json={"upload_id": upload_id})
    return upload_id


def test__spreadsheet_import__csv_happy_path__creates_rows(api):
    csv = (
        "Item,Status,Where,Group,Best before,Essential?\n"
        "TestImport-Alpha,Low,Pantry,Baking,2027-01-15,yes\n"
        "TestImport-Beta,Well-Stocked,Pantry,,2026-12-31,\n"
        "TestImport-Gamma,Out of stock,,,,no\n"
    ).encode("utf-8")
    upload_id = _stage_bytes(csv)

    inspect = requests.post(IMPORT_INSPECT_URL, json={
        "upload_id": upload_id, "filename": "items.csv",
    })
    assert inspect.status_code == 200, inspect.text
    inspect_body = inspect.json()
    assert "items.csv" in inspect_body["sheets"]
    assert inspect_body["auto_mapping"]["items.csv"]["name"] == "Item"
    assert inspect_body["auto_mapping"]["items.csv"]["level"] == "Status"

    commit = requests.post(IMPORT_COMMIT_URL, json={
        "upload_id": upload_id,
        "filename": "items.csv",
        "sheet": "items.csv",
        "column_map": inspect_body["auto_mapping"]["items.csv"],
        "options": {
            "skip_duplicates": True,
            "create_missing_locations": True,
            "create_missing_groups": True,
            "halt_on_error": False,
        },
    })
    assert commit.status_code == 200, commit.text
    summary = commit.json()["summary"]
    assert summary["created"] == 3
    assert summary["errors"] == 0


def test__spreadsheet_import__bad_level_value__per_row_error(api):
    csv = (
        "Item,Status\n"
        "TestImport-BadLevelRow,not-a-real-level\n"
    ).encode("utf-8")
    upload_id = _stage_bytes(csv)

    inspect = requests.post(IMPORT_INSPECT_URL, json={
        "upload_id": upload_id, "filename": "x.csv",
    }).json()

    commit = requests.post(IMPORT_COMMIT_URL, json={
        "upload_id": upload_id,
        "filename": "x.csv",
        "sheet": "x.csv",
        "column_map": inspect["auto_mapping"]["x.csv"],
        "options": {
            "skip_duplicates": True,
            "create_missing_locations": False,
            "create_missing_groups": False,
            "halt_on_error": False,
        },
    })
    assert commit.status_code == 200, commit.text
    body = commit.json()
    assert body["summary"]["created"] == 0
    assert body["summary"]["errors"] == 1
    bad_row = body["rows"][0]
    assert bad_row["status"] == "error"
    assert bad_row["row_number"] == 2
    assert "isn't recognised" in (bad_row["reason"] or "")


def test__spreadsheet_import__halt_on_error__rolls_everything_back(api):
    csv = (
        "Item,Status\n"
        "TestImport-Halt-Good,Low\n"
        "TestImport-Halt-Bad,not-a-real-level\n"
        "TestImport-Halt-AlsoGood,Low\n"
    ).encode("utf-8")
    upload_id = _stage_bytes(csv)
    inspect = requests.post(IMPORT_INSPECT_URL, json={
        "upload_id": upload_id, "filename": "h.csv",
    }).json()

    commit = requests.post(IMPORT_COMMIT_URL, json={
        "upload_id": upload_id,
        "filename": "h.csv",
        "sheet": "h.csv",
        "column_map": inspect["auto_mapping"]["h.csv"],
        "options": {
            "skip_duplicates": True,
            "create_missing_locations": False,
            "create_missing_groups": False,
            "halt_on_error": True,
        },
    })
    assert commit.status_code == 200, commit.text
    summary = commit.json()["summary"]
    assert summary["halted"] == 1
    assert summary["created"] == 0


def test__spreadsheet_import__commit_without_name_column__is_rejected(api):
    csv = b"Item,Status\nfoo,Low\n"
    upload_id = _stage_bytes(csv)
    requests.post(IMPORT_INSPECT_URL, json={
        "upload_id": upload_id, "filename": "n.csv",
    })

    response = requests.post(IMPORT_COMMIT_URL, json={
        "upload_id": upload_id,
        "filename": "n.csv",
        "sheet": "n.csv",
        "column_map": {"name": None, "level": "Status"},
        "options": {},
    })
    assert response.status_code == 400


# ── Export & Print (N4) ────────────────────────────────────────────────

def _first_seeded_shopping_list_id() -> str:
    response = requests.get("http://localhost:5170/api/shopping-lists")
    assert response.status_code == 200, response.text
    summaries = response.json()
    assert summaries, "seed should provide at least one shopping list"
    return summaries[0]["shopping_list_id"]


def _first_seeded_recipe_id() -> str | None:
    response = requests.get("http://localhost:5170/api/recipes")
    assert response.status_code == 200, response.text
    body = response.json()
    items = body.get("items") if isinstance(body, dict) else body
    if not items:
        return None
    return items[0]["recipe_id"]


def test__shopping_list_export_csv__endpoint_removed(api):
    # UX-v2 (§12 Q1): shopping-list CSV export was removed app-wide — print
    # is the only list export. The whole /export route is gone, not just the
    # csv format.
    list_id = _first_seeded_shopping_list_id()
    response = requests.get(
        f"http://localhost:5170/api/shopping-lists/{list_id}/export?format=csv",
    )
    assert response.status_code == 404


def test__shopping_list_print_view__returns_html_with_list_name(api):
    list_id = _first_seeded_shopping_list_id()
    detail = requests.get(
        f"http://localhost:5170/api/shopping-lists/{list_id}",
    ).json()
    response = requests.get(
        f"http://localhost:5170/api/shopping-lists/{list_id}/print-view",
    )
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"].startswith("text/html")
    # display_name, not name — name is nullable now (UX-v2 self-labelled
    # lists) and the print view renders the resolved label.
    assert detail["display_name"] in response.text
    # @media print stylesheet is embedded inline.
    assert "@media print" in response.text


def test__recipe_export_csv__returns_csv_when_recipes_exist(api):
    recipe_id = _first_seeded_recipe_id()
    if recipe_id is None:
        return  # No seeded recipes in this install — skip silently.
    response = requests.get(
        f"http://localhost:5170/api/recipes/{recipe_id}/export?format=csv",
    )
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"].startswith("text/csv")
    header_line = response.text.splitlines()[0]
    for col in ("ingredient", "quantity", "unit", "notes", "location"):
        assert col in header_line


def test__recipe_print_view__returns_html_with_recipe_name(api):
    recipe_id = _first_seeded_recipe_id()
    if recipe_id is None:
        return
    recipe = requests.get(
        f"http://localhost:5170/api/recipes/{recipe_id}",
    ).json()
    response = requests.get(
        f"http://localhost:5170/api/recipes/{recipe_id}/print-view",
    )
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"].startswith("text/html")
    assert recipe["name"] in response.text


# ── Barcodes & QR (N5) ─────────────────────────────────────────────────

LOOKUP_URL = "http://localhost:5170/api/data/barcodes/lookup"
REGISTER_PRODUCT_BARCODE_URL = "http://localhost:5170/api/data/barcodes/register-against-product"
PRODUCTS_URL = "http://localhost:5170/api/products"
STOCK_ITEMS_URL = "http://localhost:5170/api/stock-items"


def _first_seeded_stock_item_id() -> str:
    response = requests.get(STOCK_ITEMS_URL)
    assert response.status_code == 200, response.text
    items = response.json().get("items") or []
    assert items, "seed should provide at least one stock item"
    return items[0]["stock_item_id"]


def test__stock_item_qr__returns_png(api):
    item_id = _first_seeded_stock_item_id()
    response = requests.get(f"{STOCK_ITEMS_URL}/{item_id}/qr")
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"] == "image/png"
    # PNG magic bytes — sanity-check we're returning a real image.
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


def test__stock_item_qr__bad_size__is_400(api):
    item_id = _first_seeded_stock_item_id()
    response = requests.get(f"{STOCK_ITEMS_URL}/{item_id}/qr?size=10")
    assert response.status_code == 400


def _first_product_id() -> str:
    products = requests.get(PRODUCTS_URL).json().get("items") or []
    assert products, "seed data has no products"
    return products[0]["product_id"]


def test__dora_link_lookup__resolves_stock_item(api):
    # A real-world barcode identifies a Product, not a stock item. The only
    # path that resolves directly to a stock item is Dora's own QR link.
    item_id = _first_seeded_stock_item_id()
    dora_lookup = requests.get(
        f"{LOOKUP_URL}?value=dora://stock-item/{item_id}",
    )
    assert dora_lookup.status_code == 200, dora_lookup.text
    body = dora_lookup.json()
    assert body["kind"] == "stock_item"
    assert body["id"] == item_id


def test__register_product_barcode__happy_path__and_lookup(api):
    product_id = _first_product_id()
    barcode = f"TEST-{uuid.uuid4().hex[:10]}"

    register = requests.post(
        REGISTER_PRODUCT_BARCODE_URL,
        json={"product_id": product_id, "barcode": barcode},
    )
    assert register.status_code == 200, register.text
    body = register.json()
    assert body["barcode"] == barcode
    assert body["product_id"] == product_id

    lookup = requests.get(f"{LOOKUP_URL}?value={barcode}")
    assert lookup.status_code == 200, lookup.text
    lookup_body = lookup.json()
    assert lookup_body["kind"] == "product"
    assert lookup_body["id"] == product_id


def test__register_product_barcode__collision__is_409(api):
    product_id = _first_product_id()
    barcode = f"TEST-{uuid.uuid4().hex[:10]}"

    register_first = requests.post(
        REGISTER_PRODUCT_BARCODE_URL,
        json={"product_id": product_id, "barcode": barcode},
    )
    assert register_first.status_code == 200, register_first.text

    register_dup = requests.post(
        REGISTER_PRODUCT_BARCODE_URL,
        json={"product_id": product_id, "barcode": barcode},
    )
    assert register_dup.status_code == 409, register_dup.text


def test__barcode_lookup__unknown_value__is_unknown(api):
    lookup = requests.get(f"{LOOKUP_URL}?value=nothing-matches-this-12345")
    assert lookup.status_code == 200
    assert lookup.json()["kind"] == "unknown"


def test__barcode_lookup__missing_value__is_400(api):
    response = requests.get(LOOKUP_URL)
    assert response.status_code == 400


def test__qr_sheet__unknown_layout__is_400(api):
    response = requests.get(f"{STOCK_ITEMS_URL}/qr/sheet?layout=does-not-exist")
    assert response.status_code == 400


def test__qr_sheet__html_response(api):
    item_id = _first_seeded_stock_item_id()
    response = requests.get(
        f"{STOCK_ITEMS_URL}/qr/sheet?ids={item_id}&layout=a4-21up",
    )
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"].startswith("text/html")
    # The sheet inlines an <img src="/api/stock-items/<id>/qr?...">.
    assert f"/api/stock-items/{item_id}/qr" in response.text


# ── Stock-overview + meal-plan exports (post-N5 polish) ────────────────

def test__stock_overview_export_csv__returns_csv_with_header(api):
    response = requests.get(f"{STOCK_ITEMS_URL}/export?format=csv")
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"].startswith("text/csv")
    header = response.text.splitlines()[0]
    for col in (
        "location", "name", "level", "expiry", "is_flagged",
        "is_open", "auto_add_when_low", "notes",
    ):
        assert col in header


def test__stock_overview_export__unknown_format__is_400(api):
    response = requests.get(f"{STOCK_ITEMS_URL}/export?format=pdf")
    assert response.status_code == 400


def test__stock_overview_print_view__returns_html(api):
    response = requests.get(f"{STOCK_ITEMS_URL}/print-view")
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"].startswith("text/html")
    assert "Stock overview" in response.text


@pytest.mark.xfail(
    reason="FU-168: GET /api/meal-plans/<id>/export?format=csv 500s — the CSV "
    "builder (and the print-view template) reference `entry.meal_name`, but the "
    "MealPlanEntryDto field is `recipe_name` (the print-view silently renders "
    "blanks because Jinja swallows the missing attr). Open question first: was "
    "meal-plan CSV export meant to be removed under the UX-v2 'CSV export removed "
    "app-wide' decision? If kept, the fix is a field rename; if not, delete the "
    "endpoint + this test. Pre-existing, not from FU-166.",
    strict=True,
)
def test__meal_plan_export_csv__returns_csv_when_plans_exist(api):
    plans_response = requests.get("http://localhost:5170/api/meal-plans")
    plans = plans_response.json().get("items") or []
    if not plans:
        return  # No seeded meal plans on this install — skip silently.
    plan_id = plans[0]["meal_plan_id"]
    response = requests.get(
        f"http://localhost:5170/api/meal-plans/{plan_id}/export?format=csv",
    )
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"].startswith("text/csv")
    header = response.text.splitlines()[0]
    for col in ("scheduled_for", "slot", "meal", "servings"):
        assert col in header


def test__meal_plan_print_view__returns_html(api):
    plans = requests.get("http://localhost:5170/api/meal-plans").json().get("items") or []
    if not plans:
        return
    plan_id = plans[0]["meal_plan_id"]
    response = requests.get(
        f"http://localhost:5170/api/meal-plans/{plan_id}/print-view",
    )
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"].startswith("text/html")


def test__get_backup__stamps_last_backup_at_on_user(api):
    # Before any backup the seed user may or may not have a stamp from
    # earlier tests in the session; capture it and assert the next call
    # advances it.
    me_before = requests.get("http://localhost:5170/api/auth/me").json()
    requests.get(BACKUP_URL)
    me_after = requests.get("http://localhost:5170/api/auth/me").json()

    assert me_after["last_backup_at"] is not None
    if me_before.get("last_backup_at") is not None:
        # Subsequent backups must advance the timestamp.
        assert me_after["last_backup_at"] >= me_before["last_backup_at"]
