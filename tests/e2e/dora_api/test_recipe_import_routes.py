"""Recipe importer route contract — Chunk 5 (DORA_VERIFY L149/L152).

Chunk 4 replaced the URL-fetching importer with a paste-based one:
`POST /api/recipes/import-from-url` is **gone** (SSRF closed by construction —
the server never fetches) and `POST /api/recipes/import-from-content` is the
only import path. It's a **no-persist preview**: it parses pasted text into a
recipe DTO the SPA then feeds into the create endpoint. Unlinked ingredients
come back carrying their original `raw_text` with a null `stock_item_id` (the
free-text round-trip), and the `source_url` is echoed as metadata, never
fetched.

The parse *quality* is unit-pinned in `test_parse_recipe_from_text.py`; this
file pins the HTTP route contract, which had no functional coverage.
"""
import requests

BASE = "http://localhost:5170/api"
IMPORT_CONTENT = f"{BASE}/recipes/import-from-content"
IMPORT_URL_LEGACY = f"{BASE}/recipes/import-from-url"

# A clearly-structured paste with made-up ingredient names that can't match any
# seeded stock item — so any ingredient the parser returns is guaranteed
# unlinked (raw_text preserved, null stock-item id).
_PASTE = """Whatzit Berry Soup

Serves 4

Ingredients
2 cups whatzitberries
1 large blorptato, diced
a pinch of zorbsalt

Method
1. Simmer the whatzitberries until soft.
2. Add the blorptato and cook through.
3. Season with zorbsalt and serve.
"""


def test__import_from_url__route_deleted__returns_404(api):
    # The URL-fetching importer was removed (SSRF closed by construction).
    resp = requests.post(IMPORT_URL_LEGACY, json={"url": "https://example.com/recipe"})
    assert resp.status_code == 404, resp.text


def test__import_from_content__parses_paste_to_preview_dto(api):
    source = "https://example.com/whatzit-soup"
    resp = requests.post(IMPORT_CONTENT, json={"content": _PASTE, "source_url": source})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Preview DTO shape.
    for key in ("name", "ingredients", "steps", "source_url"):
        assert key in body, f"missing {key}: {body}"
    assert isinstance(body["name"], str) and body["name"].strip()
    assert isinstance(body["ingredients"], list)
    # source_url is echoed as metadata, never fetched or rewritten.
    assert body["source_url"] == source

    # Any parsed ingredient here is unlinked (made-up names) → raw_text kept,
    # stock-item id null. Guarded so a lower-shape parse doesn't false-fail.
    for ing in body["ingredients"]:
        assert ing["stock_item_id"] is None, ing
        assert isinstance(ing["raw_text"], str) and ing["raw_text"].strip()


def test__import_from_content__empty_content__rejected(api):
    # `content` is min_length=1 — an empty paste is a malformed request.
    resp = requests.post(IMPORT_CONTENT, json={"content": ""})
    assert resp.status_code == 400, resp.text
