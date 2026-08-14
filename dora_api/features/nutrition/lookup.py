"""Unified food lookup — one search across every enabled nutrition source.

The owner's ask: "slick lookup functionality that tells you what source items
in the list come from, possibility to start typing barcodes and it matches on
that." So:

- **Every result carries its source**, because three catalogues can disagree
  about a banana and hiding which one answered would be dishonest (P3). The
  picker badges each row.
- **Digits are treated as a barcode.** A typed EAN matches the local catalogue
  first, then Open Food Facts — exact matches always outrank text hits.
- **Sources that fail are reported, not swallowed.** A search that quietly
  returned half its sources because OFF timed out would look like "no result"
  and send the user off to type a number by hand.

Local (imported USDA datasets) is searched first and always answers offline.
Live sources are best-effort with short timeouts; the response says which ones
were asked and which failed.

Nothing here writes. A live result is a *suggestion* with no database row until
the user picks it — `resolve_food` is the explicit, human-confirmed step that
persists one (P12 No-invent: a fuzzy name match is never a saved link).
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from urllib.error import URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from dora_api.domain.entities.nutrition_food import (
    NUTRITION_SOURCE_LABELS,
    NUTRITION_SOURCE_OFF,
    NUTRITION_SOURCE_USDA_API,
    NutritionFood,
)
from dora_api.domain.entities.nutrition_portion import NutritionPortion
from dora_api.features.help.version_info import CURRENT_VERSION
from dora_api.persistence.bool_operation import Or
from dora_api.persistence.field import EntityField as Field

_LOG = logging.getLogger(__name__)

_OFF_PRODUCT_URL = (
    "https://world.openfoodfacts.org/api/v2/product/{ean}.json"
    "?fields=code,product_name,generic_name,brands,nutriments"
)
_OFF_SEARCH_URL = (
    "https://world.openfoodfacts.org/cgi/search.pl"
    "?search_simple=1&action=process&json=1&page_size=10"
    "&fields=code,product_name,generic_name,brands,nutriments&search_terms={terms}"
)
_USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# Live sources get a short leash. A pantry app's food picker is a
# type-and-see-results interaction; a 10s stall to reach a web service is worse
# than saying "that source didn't answer".
_LIVE_TIMEOUT_SECONDS = 6
_MAX_RESULTS = 40
_MAX_LOCAL_RESULTS = 25

# Real EANs/UPCs. Anything else that's all digits is treated as text — "500"
# is a search for something weighing 500g, not a barcode.
_BARCODE_LENGTHS = (8, 12, 13, 14)


def _user_agent(purpose: str) -> str:
    # OFF asks callers to identify themselves with name/version + purpose;
    # same convention as `features/data/off_lookup.py` and the importer.
    return f"DashyDora/{CURRENT_VERSION} ({purpose}; +https://openfoodfacts.org)"


@dataclass
class FoodResult:
    """One candidate. `id` is set only for rows that already exist locally;
    live suggestions carry None until the user picks one."""
    source: str
    source_ref: str
    name: str
    id: Optional[str] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None
    kcal_per_100g: Optional[float] = None
    protein_g_per_100g: Optional[float] = None
    carbs_g_per_100g: Optional[float] = None
    fat_g_per_100g: Optional[float] = None
    portions: List[dict] = field(default_factory=list)
    # Why this row is where it is in the list. Also lets the UI mark an exact
    # barcode hit differently from a name guess.
    match: str = "name"          # barcode | name
    exact: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "source_label": NUTRITION_SOURCE_LABELS.get(self.source, self.source),
            "source_ref": self.source_ref,
            "name": self.name,
            "brand": self.brand,
            "barcode": self.barcode,
            "kcal_per_100g": self.kcal_per_100g,
            "protein_g_per_100g": self.protein_g_per_100g,
            "carbs_g_per_100g": self.carbs_g_per_100g,
            "fat_g_per_100g": self.fat_g_per_100g,
            "portions": self.portions,
            "match": self.match,
            "exact": self.exact,
        }


def looks_like_barcode(query: str) -> bool:
    text = query.strip()
    return text.isdigit() and len(text) in _BARCODE_LENGTHS


def search_foods(repository, setting, query: str) -> dict:  # noqa: ANN001
    """Fan out across every enabled source and merge. Local first (always
    answers, even offline), then live sources best-effort."""
    text = (query or "").strip()
    if len(text) < 2:
        return {
            "query": text, "is_barcode": False, "results": [],
            "sources_queried": [], "sources_failed": [],
        }

    is_barcode = looks_like_barcode(text)
    results: List[FoodResult] = []
    queried: List[str] = []
    failed: List[dict] = []

    local = _search_local(repository, text, is_barcode)
    results.extend(local)
    # Which local datasets actually hold rows is what `sources_queried` should
    # report — an empty dataset wasn't meaningfully "asked".
    queried.extend(sorted({r.source for r in local}))

    if is_barcode and bool(getattr(setting, "nutrition_off_lookup_enabled", True)):
        # Don't re-ask OFF for a barcode already cached locally — the local row
        # is the same product and answers instantly.
        if not any(r.match == "barcode" and r.source == NUTRITION_SOURCE_OFF for r in results):
            queried.append(NUTRITION_SOURCE_OFF)
            try:
                off = _off_by_barcode(text)
                if off:
                    results.append(off)
            except Exception as exc:  # noqa: BLE001
                failed.append({"source": NUTRITION_SOURCE_OFF, "error": str(exc)})

    if not is_barcode and bool(getattr(setting, "nutrition_off_lookup_enabled", True)):
        queried.append(NUTRITION_SOURCE_OFF)
        try:
            results.extend(_off_by_text(text))
        except Exception as exc:  # noqa: BLE001
            failed.append({"source": NUTRITION_SOURCE_OFF, "error": str(exc)})

    api_key = (getattr(setting, "nutrition_usda_api_key", "") or "").strip()
    if api_key and not is_barcode:
        queried.append(NUTRITION_SOURCE_USDA_API)
        try:
            results.extend(_usda_api_search(text, api_key))
        except Exception as exc:  # noqa: BLE001
            failed.append({"source": NUTRITION_SOURCE_USDA_API, "error": str(exc)})

    return {
        "query": text,
        "is_barcode": is_barcode,
        "results": [r.to_dict() for r in _rank(results, text)[:_MAX_RESULTS]],
        "sources_queried": queried,
        "sources_failed": failed,
    }


def _rank(results: List[FoodResult], query: str) -> List[FoodResult]:
    """Exact barcode hits, then local name matches (whole-word/prefix beats
    mid-string), then everything else. A food with no kcal can't contribute to
    a rollup, so it sinks."""
    needle = query.strip().lower()

    def key(result: FoodResult):
        name = (result.name or "").lower()
        return (
            0 if result.match == "barcode" else 1,
            0 if result.id else 1,               # already-local beats live
            0 if name.startswith(needle) else 1,
            0 if result.kcal_per_100g is not None else 1,
            len(name),                            # shorter = less qualified = usually the generic one
            name,
        )

    return sorted(results, key=key)


def _search_local(repository, text: str, is_barcode: bool) -> List[FoodResult]:  # noqa: ANN001
    name_field = Field(NutritionFood, NutritionFood.Fields.NAME)
    barcode_field = Field(NutritionFood, NutritionFood.Fields.BARCODE)

    condition = (
        barcode_field.eq(text) if is_barcode
        else Or(name_field.contains(text), barcode_field.eq(text))
    )
    foods = repository.get(NutritionFood).where(condition).all()[:_MAX_LOCAL_RESULTS]
    if not foods:
        return []

    portions_by_food = _portions_for(repository, [f.id for f in foods])
    results = []
    for food in foods:
        matched_barcode = bool(food.barcode) and food.barcode == text
        results.append(FoodResult(
            id = str(food.id),
            source = food.source,
            source_ref = food.source_ref,
            name = food.name,
            brand = food.brand,
            barcode = food.barcode,
            kcal_per_100g = food.kcal_per_100g,
            protein_g_per_100g = food.protein_g_per_100g,
            carbs_g_per_100g = food.carbs_g_per_100g,
            fat_g_per_100g = food.fat_g_per_100g,
            portions = portions_by_food.get(food.id, []),
            match = "barcode" if matched_barcode else "name",
            exact = matched_barcode or food.name.strip().lower() == text.lower(),
        ))
    return results


def _portions_for(repository, food_ids) -> dict:  # noqa: ANN001
    """Batch-load portions for the whole result page — one query, not one per
    row (the mapping deliberately has no relationship object; R-032)."""
    if not food_ids:
        return {}
    rows = repository.get(NutritionPortion).where(
        Field(NutritionPortion, NutritionPortion.Fields.NUTRITION_FOOD_ID).in_(list(food_ids))
    ).all()
    grouped: dict = {}
    for row in rows:
        grouped.setdefault(row.nutrition_food_id, []).append({
            "amount": row.amount,
            "measure": row.measure,
            "gram_weight": row.gram_weight,
        })
    return grouped


def _fetch_json(url: str, purpose: str) -> dict:
    request = Request(url, headers={
        "User-Agent": _user_agent(purpose),
        "Accept": "application/json",
    })
    try:
        with urlopen(request, timeout=_LIVE_TIMEOUT_SECONDS) as response:  # noqa: S310
            raw = response.read().decode("utf-8", errors="replace")
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"couldn't reach the service ({exc})") from exc
    body = json.loads(raw)
    if not isinstance(body, dict):
        raise RuntimeError("unexpected response shape")
    return body


def _to_float(raw) -> Optional[float]:  # noqa: ANN001
    try:
        return float(raw) if raw not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _off_result(product: dict) -> Optional[FoodResult]:
    name = (
        (product.get("product_name") or "").strip()
        or (product.get("generic_name") or "").strip()
    )
    if not name:
        return None
    nutriments = product.get("nutriments") or {}
    kcal = _to_float(nutriments.get("energy-kcal_100g"))
    return FoodResult(
        source = NUTRITION_SOURCE_OFF,
        source_ref = (product.get("code") or "").strip(),
        name = name,
        brand = (product.get("brands") or "").strip() or None,
        barcode = (product.get("code") or "").strip() or None,
        kcal_per_100g = kcal,
        protein_g_per_100g = _to_float(nutriments.get("proteins_100g")),
        carbs_g_per_100g = _to_float(nutriments.get("carbohydrates_100g")),
        fat_g_per_100g = _to_float(nutriments.get("fat_100g")),
    )


def _off_by_barcode(ean: str) -> Optional[FoodResult]:
    body = _fetch_json(_OFF_PRODUCT_URL.format(ean=quote(ean)), "nutrition lookup")
    if body.get("status") != 1:
        return None
    result = _off_result(body.get("product") or {})
    if result is not None:
        result.match = "barcode"
        result.exact = True
    return result


def _off_by_text(text: str) -> List[FoodResult]:
    body = _fetch_json(_OFF_SEARCH_URL.format(terms=quote(text)), "nutrition lookup")
    results = []
    for product in (body.get("products") or []):
        parsed = _off_result(product)
        # Text search over OFF returns plenty of products with no energy value
        # at all; those can't feed a rollup, so they're not offered.
        if parsed is not None and parsed.kcal_per_100g is not None:
            results.append(parsed)
    return results


def _usda_api_search(text: str, api_key: str) -> List[FoodResult]:
    query = urlencode({
        "query": text,
        "pageSize": 15,
        # Generic foods only — Branded is what OFF already covers by barcode,
        # and mixing it in floods the list with near-duplicate supermarket SKUs.
        "dataType": "Foundation,SR Legacy",
        "api_key": api_key,
    })
    return _parse_usda_foods(_fetch_json(f"{_USDA_SEARCH_URL}?{query}", "nutrition lookup"))


def resolve_food(repository, setting, source: str, source_ref: str) -> Optional[NutritionFood]:  # noqa: ANN001
    """Turn a picked suggestion into a persisted row, and return it.

    Called when the user *confirms* a link, not while they browse. The payload
    is deliberately re-fetched from the source rather than trusted from the
    client: the client sends only (source, source_ref), so a tampered request
    can't write arbitrary nutrition numbers into the catalogue.
    """
    existing = repository.get(NutritionFood).where(
        Field(NutritionFood, NutritionFood.Fields.SOURCE).eq(source)
        & Field(NutritionFood, NutritionFood.Fields.SOURCE_REF).eq(source_ref)
    ).all()
    if existing:
        return existing[0]

    result: Optional[FoodResult] = None
    if source == NUTRITION_SOURCE_OFF:
        if not bool(getattr(setting, "nutrition_off_lookup_enabled", True)):
            return None
        result = _off_by_barcode(source_ref)
    elif source == NUTRITION_SOURCE_USDA_API:
        api_key = (getattr(setting, "nutrition_usda_api_key", "") or "").strip()
        if not api_key:
            return None
        result = _usda_api_food(source_ref, api_key)

    if result is None or result.kcal_per_100g is None:
        return None

    food = NutritionFood(
        id = uuid4(),
        source = result.source,
        source_ref = result.source_ref or source_ref,
        name = result.name,
        brand = result.brand,
        barcode = result.barcode,
        kcal_per_100g = result.kcal_per_100g,
        protein_g_per_100g = result.protein_g_per_100g,
        carbs_g_per_100g = result.carbs_g_per_100g,
        fat_g_per_100g = result.fat_g_per_100g,
        imported_at = datetime.now(timezone.utc),
    )
    repository.add(food)
    repository.save_changes()
    return food


def _usda_api_food(fdc_id: str, api_key: str) -> Optional[FoodResult]:
    body = _fetch_json(
        f"{_USDA_SEARCH_URL}?{urlencode({'query': fdc_id, 'pageSize': 5, 'api_key': api_key})}",
        "nutrition lookup",
    )
    for food in (body.get("foods") or []):
        if str(food.get("fdcId")) == str(fdc_id):
            return next(iter(_parse_usda_foods({"foods": [food]})), None)
    return None


def _parse_usda_foods(body: dict) -> List[FoodResult]:
    """Shared parse for both the search and single-food paths. Matches
    nutrients on (name, unit) exactly as the bulk importer does — "Energy"
    comes back as both kcal and kJ, so the unit is load-bearing, not
    decoration."""
    results = []
    for food in (body.get("foods") or []):
        description = (food.get("description") or "").strip()
        fdc_id = food.get("fdcId")
        if not description or fdc_id is None:
            continue
        values = {}
        for nutrient in (food.get("foodNutrients") or []):
            name = (nutrient.get("nutrientName") or "").strip().lower()
            unit = (nutrient.get("unitName") or "").strip().lower()
            amount = _to_float(nutrient.get("value"))
            if amount is None:
                continue
            if name == "energy" and unit == "kcal":
                values["kcal_per_100g"] = amount
            elif name == "protein" and unit == "g":
                values["protein_g_per_100g"] = amount
            elif name == "total lipid (fat)" and unit == "g":
                values["fat_g_per_100g"] = amount
            elif name == "carbohydrate, by difference" and unit == "g":
                values["carbs_g_per_100g"] = amount
        if "kcal_per_100g" not in values:
            continue
        results.append(FoodResult(
            source = NUTRITION_SOURCE_USDA_API,
            source_ref = str(fdc_id),
            name = description,
            brand = (food.get("brandOwner") or "").strip() or None,
            **values,
        ))
    return results
