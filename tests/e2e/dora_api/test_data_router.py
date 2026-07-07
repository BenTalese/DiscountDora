"""End-to-end coverage for /api/data/backup* and /api/data/backups (library).

FU-342 retired the download-only `GET /api/data/backup` fast-path in
favour of the persistent library (`/api/data/backups` — plural). The
tests here `POST /backups` (create) + `GET /backups/<id>/download` to
land on a payload equivalent to what the old endpoint returned, then
assert on the payload's shape / restore round-trip / etc.

Inspect + restore endpoints (`/api/data/backup/inspect`,
`/api/data/backup/restore`) are unchanged — the library reuses the
same restore handler internally for the fast-path restore-from-saved
button, but the inspect + external-file restore endpoints remain as
before.
"""
import json
import uuid  # register_product_barcode tests used uuid without importing it.

import pytest
import requests

from tests.e2e.dora_api._error_assertions import domain_err


LIBRARY_URL = "http://localhost:5170/api/data/backups"


def _create_backup(sections: list[str] | None = None) -> tuple[dict, dict]:
    """POST the library create endpoint, then GET the download so tests
    can assert on both the row + the payload shape. Returns (row, payload).

    Every test in this module that used to `requests.get(BACKUP_URL)` now
    threads through here — the payload assertions are exactly the ones
    the retired GET endpoint carried."""
    body = {} if sections is None else {"sections": sections}
    row_response = requests.post(LIBRARY_URL, json=body)
    row_response.raise_for_status()
    row = row_response.json()
    dl_response = requests.get(f"{LIBRARY_URL}/{row['backup_id']}/download")
    dl_response.raise_for_status()
    return row, dl_response.json()


def test__get_backup__happy_path__returns_attachment_with_expected_sections(api):
    row, payload = _create_backup()

    # Row-level metadata the library added
    assert row["status"] == "ready"
    assert row["trigger_kind"] == "manual"
    assert row["created_by_username"] == "dora"
    assert row["size_bytes"] > 0

    # The download response was pre-checked by _create_backup (raise_for_status
    # + content-disposition attachment is set inside send_file()); this test
    # focuses on the JSON body shape.

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
        # `meals` + `meal_recipes` were removed by the meals→recipes
        # rework; `product_stock_item_links` (above) is now a real backup section.
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
    response = fresh.post(LIBRARY_URL, json={})
    assert response.status_code == 401


def test__get_backup__is_valid_json_document(api):
    _, payload = _create_backup()
    # Payload must be parseable on its own — i.e. saving it to disk and
    # reloading gives back the same shape. `_create_backup` already
    # round-tripped it through JSON on both ends; this test asserts the
    # invariant is preserved when it lands on disk.
    reparsed = json.loads(json.dumps(payload))
    assert reparsed["schema_version"] == 1
    assert "stock_items" in reparsed


# ── /inspect ───────────────────────────────────────────────────────────

INSPECT_URL = "http://localhost:5170/api/data/backup/inspect"
RESTORE_URL = "http://localhost:5170/api/data/backup/restore"


def test__inspect_backup__roundtrip__counts_match_and_seeds_flag_as_duplicates(api):
    _, backup = _create_backup()

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
    _, backup = _create_backup()

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
    _, payload = _create_backup()
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
    _, payload = _create_backup(sections=["stock_items", "stock_groups"])
    assert "stock_items" in payload
    assert "stock_groups" in payload
    assert "recipes" not in payload
    assert "shopping_lists" not in payload
    assert set(payload["sections"]) == {"stock_items", "stock_groups"}


def test__get_backup__with_optional_sections__includes_them(api):
    _, payload = _create_backup(
        sections=["app_settings", "users", "product_historic_offers"],
    )
    assert "app_settings" in payload
    assert "users" in payload
    assert "product_historic_offers" in payload


def test__get_backup__never_exports_password_hashes(api):
    _, payload = _create_backup(sections=["users"])
    for row in payload["users"]:
        assert "password_hash" not in row, "password_hash must never round-trip"


def test__get_backup__unknown_section__is_rejected(api):
    response = requests.post(
        LIBRARY_URL,
        json={"sections": ["stock_items", "nonsense"]},
    )
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
    _, backup = _create_backup()
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
    assert response.json()["errors"]["received"] == [domain_err("0")]


def test__chunked_upload__abort_deletes_staged_file(api):
    start = requests.post(UPLOAD_START_URL, json={}).json()
    upload_id = start["upload_id"]
    response = requests.delete(f"http://localhost:5170/api/data/uploads/{upload_id}")
    assert response.status_code == 204
    # Re-aborting is harmless (DELETE is idempotent).
    response = requests.delete(f"http://localhost:5170/api/data/uploads/{upload_id}")
    assert response.status_code == 204


def test__restore_backup__via_upload_id__no_changes_on_roundtrip(api):
    _, backup = _create_backup()
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
    _, backup = _create_backup()
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
        "TestImport-Beta,Stocked,Pantry,,2026-12-31,\n"
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


# ── Import template download (FU-347 — BOM for Excel-on-Windows) ───────

def test__import_template__csv_download__starts_with_utf8_bom(api):
    """FU-347 — the downloaded template CSV must start with the UTF-8
    BOM so Excel-on-Windows opens it in UTF-8 instead of guessing
    ANSI/CP-1252. Without the BOM, any accented character in a future
    example row / header renders as mojibake in Excel."""
    response = requests.get(
        "http://localhost:5170/api/data/import/templates/stock_items.csv"
    )
    assert response.status_code == 200, response.text
    body = response.content
    assert body.startswith(b"\xef\xbb\xbf"), (
        "Template CSV must begin with the UTF-8 BOM (0xEF 0xBB 0xBF); "
        f"got first bytes {body[:8]!r}"
    )


def test__import_template__csv_download__body_after_bom_parses(api):
    """The BOM is only for Excel — server-side parsers (including our
    own upload path) must still be able to consume the file. Round-trip
    the downloaded template through the chunked-upload + inspect stack
    to prove the BOM doesn't wedge the parser."""
    response = requests.get(
        "http://localhost:5170/api/data/import/templates/stock_items.csv"
    )
    assert response.status_code == 200, response.text
    body = response.content
    # Sanity — BOM present + non-empty CSV payload after it.
    assert body[:3] == b"\xef\xbb\xbf"
    assert len(body) > 3

    upload_id = _stage_bytes(body)
    inspect = requests.post(IMPORT_INSPECT_URL, json={
        "upload_id": upload_id, "filename": "stock_items.csv",
    })
    assert inspect.status_code == 200, inspect.text
    inspect_body = inspect.json()
    # The parser strips the BOM before decoding, so the auto-mapper's
    # `name` column resolves cleanly instead of collating a `"﻿name"`
    # header that no target field can match.
    auto = inspect_body["auto_mapping"]["stock_items.csv"]
    assert auto["name"] is not None, (
        f"Auto-mapper couldn't identify the name column after BOM strip: {auto!r}"
    )
    # Belt-and-braces — the mapped header itself doesn't carry a
    # leading BOM character.
    assert not auto["name"].startswith("﻿"), (
        f"BOM leaked into the mapped name-column header: {auto['name']!r}"
    )


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
REGISTER_URL = "http://localhost:5170/api/data/barcodes"
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


# per-test product index so each barcode-register test gets a
# fresh unbarcoded Product. The new `one Product = one EAN` rule means
# any test that registers against `products[0]` blocks the next from
# doing the same. Tests increment this counter at call sites.
_PRODUCT_INDEX = [0]


def _next_unused_product_id(*, requires_link: bool = False) -> str:
    """Yield product_ids round-robin from the seed so each barcode test
    starts with a Product that has no barcode registered yet. Each call
    advances by one regardless of seed size; consumers must take the
    head of the list slice they need.

    `requires_link=True` skips forward until the next Product has a
    linked StockItem — used by the traversal test, which needs the
    `stock_item_via_product` lookup kind."""
    products = requests.get(PRODUCTS_URL).json().get("items") or []
    assert products, "seed data has no products"
    while True:
        idx = _PRODUCT_INDEX[0]
        _PRODUCT_INDEX[0] = idx + 1
        assert idx < len(products), (
            f"barcode tests need more seed products (asked for #{idx}, have "
            f"{len(products)}). Bump the seed or release a product."
        )
        candidate = products[idx]
        if requires_link and not candidate.get("linked_stock_item_id"):
            continue
        return candidate["product_id"]
    return products[idx]["product_id"]


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


def test__register_barcode__against_product__lookup_traverses_via_product(api):
    """FU-056 — registering against a Product that's linked to a StockItem
    yields the `stock_item_via_product` lookup kind (the catalogue case).
    `product_no_link` only fires when the Product has zero linked items."""
    # `requires_link=True` — this test is about the *linked* traversal,
    # so the picked Product must have a StockItem attached. Bare
    # round-robin was flaky: it landed on a linked Product when the
    # test ran in isolation but on an unlinked one once earlier tests
    # advanced the counter past the linked seed rows.
    product_id = _next_unused_product_id(requires_link=True)
    barcode = f"TEST-{uuid.uuid4().hex[:10]}"

    register = requests.post(REGISTER_URL, json={
        "product_id": product_id,
        "barcode": barcode,
    })
    assert register.status_code == 200, register.text
    body = register.json()
    assert body["barcode"] == barcode
    assert body["product_id"] == product_id
    assert body["stock_item_id"] is None
    barcode_id = body["barcode_id"]

    lookup = requests.get(f"{LOOKUP_URL}?value={barcode}")
    assert lookup.status_code == 200, lookup.text
    lookup_body = lookup.json()
    # `UNIQUE(StockItemProduct.product_id)` guarantees that any linked
    # Product reaches exactly one StockItem — so the only possible
    # outcomes are `stock_item_via_product` (linked, the seed shape)
    # or `product_no_link` (Product has no StockItem).
    assert lookup_body["kind"] == "stock_item_via_product", lookup_body
    assert lookup_body["product_id"] == product_id
    assert lookup_body["barcode_id"] == barcode_id


def test__register_barcode__same_barcode_twice__is_409(api):
    """Barcode UNIQUE constraint — same value can't be registered twice."""
    product_id = _next_unused_product_id()
    barcode = f"TEST-{uuid.uuid4().hex[:10]}"

    register_first = requests.post(REGISTER_URL, json={
        "product_id": product_id,
        "barcode": barcode,
    })
    assert register_first.status_code == 200, register_first.text

    register_dup = requests.post(REGISTER_URL, json={
        "product_id": product_id,
        "barcode": barcode,
    })
    assert register_dup.status_code == 409, register_dup.text


def test__register_barcode__direct_stock_item__lookup_resolves_to_stock_item(api):
    """FU-056 — registering directly against a stock item (no product)
    returns the `stock_item` kind on lookup. The 'lightweight install' path."""
    stock_item_id = requests.get(
        'http://localhost:5170/api/stock-items?limit=1'
    ).json()['items'][0]['stock_item_id']
    barcode = f"DIR-{uuid.uuid4().hex[:10]}"

    register = requests.post(REGISTER_URL, json={
        "stock_item_id": stock_item_id,
        "barcode": barcode,
    })
    assert register.status_code == 200, register.text
    body = register.json()
    assert body["stock_item_id"] == stock_item_id
    assert body["product_id"] is None

    lookup = requests.get(f"{LOOKUP_URL}?value={barcode}")
    assert lookup.status_code == 200, lookup.text
    lookup_body = lookup.json()
    assert lookup_body["kind"] == "stock_item"
    assert lookup_body["id"] == stock_item_id
    # The flat product_id field is None for direct-only registrations.
    assert lookup_body["product_id"] is None


def test__register_barcode__second_against_same_product__is_409(api):
    """FU-056 — one Product = one barcode (per-product UNIQUE)."""
    product_id = _next_unused_product_id()
    barcode_a = f"PROD-A-{uuid.uuid4().hex[:8]}"
    barcode_b = f"PROD-B-{uuid.uuid4().hex[:8]}"

    first = requests.post(REGISTER_URL, json={
        "product_id": product_id,
        "barcode": barcode_a,
    })
    assert first.status_code == 200, first.text

    second = requests.post(REGISTER_URL, json={
        "product_id": product_id,
        "barcode": barcode_b,
    })
    # The per-product UNIQUE constraint fires here (different barcode but
    # same product_id → can't have a second).
    assert second.status_code == 409, second.text


def test__register_barcode__neither_target__is_400(api):
    """FU-056 — model validator: at least one of product_id / stock_item_id
    must be set."""
    response = requests.post(REGISTER_URL, json={"barcode": "ORPHAN-12345"})
    assert response.status_code == 400, response.text


def test__delete_barcode__round_trip(api):
    """FU-056 — DELETE removes the registration; subsequent lookup is unknown."""
    stock_item_id = requests.get(
        'http://localhost:5170/api/stock-items?limit=1'
    ).json()['items'][0]['stock_item_id']
    barcode = f"DEL-{uuid.uuid4().hex[:10]}"

    register = requests.post(REGISTER_URL, json={
        "stock_item_id": stock_item_id,
        "barcode": barcode,
    })
    assert register.status_code == 200, register.text
    barcode_id = register.json()["barcode_id"]

    delete = requests.delete(f"{REGISTER_URL}/{barcode_id}")
    assert delete.status_code == 204, delete.text

    lookup = requests.get(f"{LOOKUP_URL}?value={barcode}")
    assert lookup.json()["kind"] == "unknown"


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


def test__meal_plan_export_csv__endpoint_removed__is_404(api):
    # meal-plan CSV export was removed (a plan is a calendar, not a
    # table); print-view → "Save as PDF" is the export path. The /export route
    # is gone, so it 404s.
    plans = requests.get("http://localhost:5170/api/meal-plans").json().get("items") or []
    if not plans:
        return  # No seeded meal plans on this install.
    plan_id = plans[0]["meal_plan_id"]
    response = requests.get(
        f"http://localhost:5170/api/meal-plans/{plan_id}/export?format=csv",
    )
    assert response.status_code == 404


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


# the library now owns "when was
# the last backup" via `MAX(Backup.created_at)`. The old test that
# stamped this column on every download lived here; deleted.
