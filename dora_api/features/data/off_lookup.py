"""P8-02 — Open Food Facts EAN → suggestion.

    GET /api/data/products/off-lookup?value=<ean>

The client calls this only when `/api/data/barcodes/lookup` returned
`kind: unknown` — an EAN that Dora doesn't know yet. The endpoint hits
Open Food Facts server-side (avoids browser CORS + centralises the
User-Agent + cache), and returns a small, confirmable suggestion the SPA
uses to pre-fill a new stock item. Never silently writes; always a
suggestion the user reviews.

Boundary the whole feature defends: this is *add-only*. There is no path
here to look up a live deal, price, or merchant. OFF is open data; we
consume, we don't scrape a retailer.

Charter alignment: P1 Effortless (one scan → one confirm add), P3 Honest
(the SPA labels the suggestion as "from Open Food Facts, review and
confirm"), P9 No-scrape (open data source), P12 No-invent (unknown →
`found=false`, not made-up).
"""
import json
import logging
from dataclasses import dataclass
from time import time
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from dora_api.features.help.version_info import CURRENT_VERSION
from dora_api.features.routers import DATA_ROUTER
from dora_api.infrastructure.api_response import bad_request, ok


_LOGGER = logging.getLogger(__name__)


_OFF_URL_TEMPLATE = (
    "https://world.openfoodfacts.org/api/v2/product/{ean}.json"
    # v2 accepts `fields=` to limit the payload; we only need a handful of
    # keys, so trim the response to keep the round-trip lean and cheap
    # to cache.
    "?fields=product_name,generic_name,brands,image_front_url,image_url,"
    "categories,quantity"
)
_FETCH_TIMEOUT_SECONDS = 5
_CACHE_TTL_SECONDS = 24 * 60 * 60
_CACHE_MAX_ENTRIES = 512


# Cache keyed by the raw scanned value (already digits-only by the time it
# hits us). Value = (fetched_at, response_dict). Bounded to
# _CACHE_MAX_ENTRIES with a FIFO eviction — sufficient for a personal
# pantry app; if the working set genuinely exceeds this, an LRU is a
# one-line swap later.
_CACHE: dict[str, tuple[float, dict]] = {}


@dataclass(frozen=True, slots=True)
class OffSuggestionDto:
    """Small, confirmable suggestion pulled from Open Food Facts. Every
    field is optional so the SPA can render whatever OFF provides without
    the user needing to fill blanks the source didn't have."""
    found: bool
    name: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    categories: Optional[str] = None
    quantity: Optional[str] = None


def _is_plausible_ean(raw: str) -> bool:
    """EAN-8 / UPC-A (12) / EAN-13 / ITF-14 are the codes OFF returns
    data for. 8..14 digits keeps the endpoint honest without pretending
    to be a full checksum validator."""
    return raw.isdigit() and 8 <= len(raw) <= 14


def _cache_get(ean: str) -> Optional[dict]:
    entry = _CACHE.get(ean)
    if entry is None:
        return None
    fetched_at, payload = entry
    if time() - fetched_at > _CACHE_TTL_SECONDS:
        # Stale — drop so the next call refetches. Cheaper than a
        # background sweep.
        _CACHE.pop(ean, None)
        return None
    return payload


def _cache_put(ean: str, payload: dict) -> None:
    if len(_CACHE) >= _CACHE_MAX_ENTRIES:
        # FIFO drop: pop the oldest inserted key. `dict` preserves
        # insertion order (guaranteed since 3.7).
        try:
            oldest = next(iter(_CACHE))
            _CACHE.pop(oldest, None)
        except StopIteration:
            pass
    _CACHE[ean] = (time(), payload)


def _first_non_empty(*candidates: object) -> Optional[str]:
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return None


def _parse_off_response(body: dict) -> dict:
    """Extract the handful of fields the SPA needs from an OFF product
    document. OFF returns `status: 1` for a hit and `status: 0` for a
    miss; we mirror that as `found`."""
    if int(body.get("status") or 0) != 1:
        return {"found": False}
    product = body.get("product") or {}
    name = _first_non_empty(product.get("product_name"), product.get("generic_name"))
    brand = _first_non_empty(product.get("brands"))
    image = _first_non_empty(product.get("image_front_url"), product.get("image_url"))
    # OFF returns comma-separated freeform categories (e.g. "Plant-based
    # foods and beverages, Beverages, Plant-based beverages"). We hand it
    # through unchanged; mapping into a Dora stock group is user-side.
    categories = _first_non_empty(product.get("categories"))
    quantity = _first_non_empty(product.get("quantity"))
    return {
        "found": True,
        "name": name,
        "brand": brand,
        "image_url": image,
        "categories": categories,
        "quantity": quantity,
    }


def _fetch_from_off(ean: str) -> dict:
    """Server-side OFF call. Never raises — a failure returns
    `{found: false}` so the SPA can fall through to the manual-entry
    fallback without a special error branch."""
    url = _OFF_URL_TEMPLATE.format(ean=ean)
    req = Request(url, headers={
        # OFF asks callers to identify themselves with a descriptive UA
        # (name/version + purpose). Matches the pattern used by
        # `get_version.py` and the recipe importer.
        "User-Agent": f"DashyDora/{CURRENT_VERSION} (barcode-to-add; +https://openfoodfacts.org)",
        "Accept": "application/json",
    })
    try:
        with urlopen(req, timeout=_FETCH_TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (URLError, TimeoutError) as exc:
        _LOGGER.info("OFF lookup network failure for %s: %s", ean, exc)
        return {"found": False}
    except Exception as exc:
        _LOGGER.warning("OFF lookup unexpected error for %s: %s", ean, exc)
        return {"found": False}
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        _LOGGER.warning("OFF lookup returned non-JSON for %s: %s", ean, exc)
        return {"found": False}
    if not isinstance(body, dict):
        return {"found": False}
    return _parse_off_response(body)


# The fetch function is exposed for tests via monkeypatching (see
# `test_off_lookup.py` — replace `_fetch_from_off` to avoid a real
# network call).
def _lookup_ean(ean: str) -> dict:
    cached = _cache_get(ean)
    if cached is not None:
        return cached
    payload = _fetch_from_off(ean)
    _cache_put(ean, payload)
    return payload


@DATA_ROUTER.route("/products/off-lookup", methods=["GET"])
def off_lookup():
    """Return an Open Food Facts suggestion for an EAN, or `{found:
    false}` when OFF has no entry (or is unreachable). Callers should
    only hit this when the primary barcode lookup returned `unknown` —
    already-mapped EANs must never re-round-trip through OFF."""
    from flask import request

    raw = (request.args.get("value") or "").strip()
    if not raw:
        return bad_request("value query parameter is required.")
    if not _is_plausible_ean(raw):
        # Not an error worth logging — most non-numeric scans are Dora
        # QR links which the caller should have routed through
        # `/api/data/barcodes/lookup` first.
        return ok(OffSuggestionDto(found=False))

    payload = _lookup_ean(raw)
    return ok(OffSuggestionDto(
        found=bool(payload.get("found")),
        name=payload.get("name"),
        brand=payload.get("brand"),
        image_url=payload.get("image_url"),
        categories=payload.get("categories"),
        quantity=payload.get("quantity"),
    ))
