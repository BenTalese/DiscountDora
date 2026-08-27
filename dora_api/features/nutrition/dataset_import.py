"""USDA FoodData Central bulk-dataset import.

The "download button" nutrition source: fetch a CSV bundle from USDA, parse it,
and populate `NutritionFood` + `NutritionPortion`. Deliberately the *default*
provider, because it's the only one with no strings attached — FDC data is
public domain (CC0), so it can be redistributed, cached and used offline
without attribution or share-alike obligations, unlike Open Food Facts (ODbL).

Only the two generic-food datasets are offered:

  Foundation  ~3.7MB zipped / 32MB unzipped — current, well-curated
  SR Legacy   ~6.7MB zipped / 54MB unzipped — frozen 2018, far broader

Branded Foods is deliberately *not* offered: at 428MB zipped / 2.9GB unzipped
it dwarfs everything else in the app, and packaged goods are better reached by
barcode through Open Food Facts anyway. Generic foods are what recipe
ingredients actually name ("flour", "banana"), which is what the rollup needs.

Runs on a daemon thread with in-memory status, the same shape as the Piper
voice download (`features/tts/voice_provision.py`) — the user starts it, the
admin page polls. Status is a transient UI hint; the durable truth is simply
how many rows the dataset has, which `sources.py` reads back.
"""
import csv
import io
import logging
import threading
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional, Tuple
from urllib.request import Request, urlopen
from uuid import uuid4

from dora_api.domain.entities.nutrition_food import (
    NUTRITION_SOURCE_USDA_FOUNDATION,
    NUTRITION_SOURCE_USDA_SR_LEGACY,
    NutritionFood,
)
from dora_api.domain.entities.nutrition_portion import NutritionPortion
from dora_api.features.nutrition.food_categories import normalise_category
from dora_api.features.nutrition.nutrients import USDA_NUTRIENT_ATTRS
from dora_api.persistence.field import EntityField as Field

_LOG = logging.getLogger(__name__)

# Release dates are baked into FDC filenames. SR Legacy is frozen ("the final
# release … will not be updated"), so its URL is stable forever; Foundation
# ships a couple of times a year, so *that* URL will eventually 404. Rather
# than add a schema column for it, the start-import endpoint accepts an
# optional `url` override — the admin page exposes it, and a failed download
# says so plainly instead of leaving a dead button.
# Host matters: `www.usda.gov/fdc-datasets/...` is fronted by Akamai and
# answers **403** to programmatic clients regardless of User-Agent (verified
# 2026-08-15 — this is what broke the download button). The FDC origin
# `fdc.nal.usda.gov` serves the same files with no such gate.
_FDC_HOST = "https://fdc.nal.usda.gov/fdc-datasets"
_DEFAULT_URLS = {
    NUTRITION_SOURCE_USDA_FOUNDATION:
        f"{_FDC_HOST}/FoodData_Central_foundation_food_csv_2026-04-30.zip",
    NUTRITION_SOURCE_USDA_SR_LEGACY:
        f"{_FDC_HOST}/FoodData_Central_sr_legacy_food_csv_2018-04.zip",
}

_DATASET_LABELS = {
    NUTRITION_SOURCE_USDA_FOUNDATION: "USDA Foundation Foods",
    NUTRITION_SOURCE_USDA_SR_LEGACY: "USDA SR Legacy",
}

# The nutrients kept, and their USDA names, live in `nutrients.py` (R-002 —
# the live-API path reads the same table). Matched by (name, unit) out of
# `nutrient.csv` rather than by hardcoded FDC nutrient ids: the ids are stable
# in practice but the names are what the file documents, and "Energy" appears
# twice (kcal and kJ), so the unit is load-bearing, not decoration.
_WANTED_NUTRIENTS: Dict[Tuple[str, str], str] = USDA_NUTRIENT_ATTRS

_FETCH_TIMEOUT_SECONDS = 120
# Identify honestly: this call goes to USDA, so pointing the contact URL at
# Open Food Facts (copy-paste from the OFF client) was simply wrong.
_USER_AGENT = "DashyDora (nutrition dataset import; +https://github.com/BenTalese/DiscountDora)"


@dataclass(frozen=True, slots=True)
class ParsedPortion:
    """A portion as the CSV states it, linked by USDA's `fdc_id` rather than by
    a `NutritionFood.id`.

    Deliberately *not* a `NutritionPortion`: `repository.add()` assigns a fresh
    id to every entity it stores (that's the house convention — the repository
    owns identity), so a food's real id doesn't exist until after it's added.
    Building portions against parse-time ids produced 14,449 rows pointing at
    ids that were never stored, and the whole import died on a foreign-key
    violation at the first flush. The link is resolved in `_replace_dataset`,
    after the foods are in.
    """
    fdc_id: str
    amount: float
    measure: str
    gram_weight: float


@dataclass
class ImportState:
    """In-memory progress for one dataset. `phase` drives the admin page's
    wording; `foods` is what actually landed."""
    phase: str = "idle"       # idle | downloading | parsing | saving | done | error
    foods: int = 0
    portions: int = 0
    error: Optional[str] = None


_LOCK = threading.Lock()
_STATE: Dict[str, ImportState] = {}


def dataset_label(source: str) -> str:
    return _DATASET_LABELS.get(source, source)


def default_url(source: str) -> str:
    return _DEFAULT_URLS.get(source, "")


def state_for(source: str) -> ImportState:
    with _LOCK:
        return _STATE.get(source, ImportState())


def is_running(source: str) -> bool:
    with _LOCK:
        state = _STATE.get(source)
        return state is not None and state.phase in ("downloading", "parsing", "saving")


def start_import(source: str, url: str | None = None) -> ImportState:
    """Kick off a background import. Re-entrant: a second call while one is in
    flight just returns the running state rather than starting a second fetch."""
    if source not in _DEFAULT_URLS:
        raise ValueError(f"Unknown nutrition dataset '{source}'.")
    with _LOCK:
        existing = _STATE.get(source)
        if existing is not None and existing.phase in ("downloading", "parsing", "saving"):
            return existing
        _STATE[source] = ImportState(phase="downloading")

    thread = threading.Thread(
        target = _run_import,
        args = (source, (url or "").strip() or _DEFAULT_URLS[source]),
        name = f"nutrition-import-{source}",
        daemon = True,
    )
    thread.start()
    return state_for(source)


def _set(source: str, **fields) -> None:
    with _LOCK:
        state = _STATE.setdefault(source, ImportState())
        for key, value in fields.items():
            setattr(state, key, value)


def _run_import(source: str, url: str) -> None:
    # A worker thread has no Flask app context, so it pushes its own. `app` is
    # a module-level Flask instance (there's no create_app factory here).
    # Imported locally so this module stays importable without the app — the
    # parser is unit-tested standalone.
    from dora_api.app import app
    from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

    try:
        _LOG.info("Importing nutrition dataset '%s' from %s", source, url)
        payload = _download(url)

        _set(source, phase="parsing")
        foods, portions = parse_fdc_csv_zip(payload, source)
        if not foods:
            raise ValueError(
                "The download contained no usable foods — check the URL points "
                "at a FoodData Central *CSV* bundle."
            )

        _set(source, phase="saving", foods=len(foods), portions=len(portions))
        with app.app_context():
            _replace_dataset(SqlAlchemyRepository(), source, foods, portions)

        _set(source, phase="done", error=None)
        _LOG.info(
            "Imported nutrition dataset '%s': %d foods, %d portions",
            source, len(foods), len(portions),
        )
    except Exception as exc:  # noqa: BLE001 — any failure becomes UI state
        _LOG.exception("Nutrition dataset import failed for '%s'", source)
        message = _friendly_error(str(exc) or exc.__class__.__name__)
        _set(source, phase="error", error=message)


# Every failure here reaches the user as a line of text under a dead button,
# so each one has to say what to do next. Raw urllib strings ("HTTP Error 403:
# Forbidden") tell an admin nothing about which of these situations they're in.
def _friendly_error(message: str) -> str:
    if "HTTP Error 404" in message:
        return (
            "That release URL returned 404 — it has probably been superseded. "
            "Grab the current CSV link from fdc.nal.usda.gov/download-datasets "
            "and paste it in as a custom URL."
        )
    if "HTTP Error 403" in message:
        return (
            "The download was refused (403). If you pasted a custom URL, check "
            "it points at fdc.nal.usda.gov — the www.usda.gov mirror blocks "
            "automated downloads."
        )
    if "urlopen error" in message or "timed out" in message.lower():
        return f"Couldn't reach USDA to download the dataset ({message})."
    return message


def _download(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": _USER_AGENT})
    with urlopen(request, timeout=_FETCH_TIMEOUT_SECONDS) as response:  # noqa: S310
        return response.read()


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def _member(archive: zipfile.ZipFile, basename: str) -> Optional[str]:
    """FDC bundles nest their CSVs one directory deep, and the directory name
    carries the release date — so match on basename, not full path."""
    for name in archive.namelist():
        if name.rsplit("/", 1)[-1].lower() == basename:
            return name
    return None


def _rows(archive: zipfile.ZipFile, member: str) -> Iterable[dict]:
    with archive.open(member) as raw:
        # utf-8-sig: FDC ships a BOM, which would otherwise corrupt the first
        # column name and silently break every lookup against it.
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        yield from csv.DictReader(text)


def parse_fdc_csv_zip(payload: bytes, source: str):
    """Pure parse step — bytes in, entities out. Separated from the download
    and the DB write so it can be tested against a small fixture archive."""
    archive = zipfile.ZipFile(io.BytesIO(payload))

    food_member = _member(archive, "food.csv")
    nutrient_member = _member(archive, "nutrient.csv")
    # Optional, unlike the three below: an older or hand-made bundle without it
    # still imports, its foods simply carry no category. Failing the whole
    # import over the Health Star Rating's input would be the wrong trade —
    # the nutrients are what the app is actually for.
    category_member = _member(archive, "food_category.csv")
    food_nutrient_member = _member(archive, "food_nutrient.csv")
    if not (food_member and nutrient_member and food_nutrient_member):
        raise ValueError(
            "Not a FoodData Central CSV bundle — expected food.csv, nutrient.csv "
            "and food_nutrient.csv inside the archive."
        )

    # nutrient id → the NutritionFood attribute it feeds.
    nutrient_attr: Dict[str, str] = {}
    for row in _rows(archive, nutrient_member):
        key = (_norm(row.get("name", "")), _norm(row.get("unit_name", "")))
        attr = _WANTED_NUTRIENTS.get(key)
        if attr:
            nutrient_attr[row["id"]] = attr

    # USDA food-group id → its description. Read for the Health Star Rating's
    # fvnl test and nothing else (see `food_categories.py`); the file has always
    # been in the bundle and was simply never opened.
    categories: Dict[str, str] = {}
    if category_member:
        for row in _rows(archive, category_member):
            description = normalise_category(row.get("description"))
            if row.get("id") and description:
                categories[row["id"]] = description

    imported_at = datetime.now(timezone.utc)
    foods: Dict[str, NutritionFood] = {}
    for row in _rows(archive, food_member):
        fdc_id = row.get("fdc_id")
        description = (row.get("description") or "").strip()
        if not fdc_id or not description:
            continue
        foods[fdc_id] = NutritionFood(
            id = uuid4(),
            source = source,
            source_ref = fdc_id,
            name = description,
            brand = (row.get("brand_owner") or "").strip() or None,
            barcode = (row.get("gtin_upc") or "").strip() or None,
            food_category = categories.get((row.get("food_category_id") or "").strip()),
            imported_at = imported_at,
        )

    for row in _rows(archive, food_nutrient_member):
        attr = nutrient_attr.get(row.get("nutrient_id", ""))
        if not attr:
            continue
        food = foods.get(row.get("fdc_id", ""))
        if food is None:
            continue
        amount = _to_float(row.get("amount"))
        if amount is not None:
            setattr(food, attr, amount)

    portions = _parse_portions(archive, foods)

    # A food with no energy value can't contribute to a rollup and would just
    # be noise in the picker, so it's dropped rather than stored as a row that
    # looks usable and isn't (P12 No-invent). Its portions go with it.
    usable = [f for f in foods.values() if f.kcal_per_100g is not None]
    usable_refs = {f.source_ref for f in usable}
    portions = [p for p in portions if p.fdc_id in usable_refs]
    return usable, portions


def _parse_portions(archive: zipfile.ZipFile, foods: Dict[str, NutritionFood]) -> list:
    """`food_portion.csv` + `measure_unit.csv` → household measures with gram
    weights. This is the half that makes "2 cups flour" convertible; without it
    only mass-unit ingredients could ever be counted."""
    portion_member = _member(archive, "food_portion.csv")
    if not portion_member:
        return []

    unit_names: Dict[str, str] = {}
    unit_member = _member(archive, "measure_unit.csv")
    if unit_member:
        for row in _rows(archive, unit_member):
            name = (row.get("name") or "").strip()
            # FDC uses the literal string "undetermined" for rows whose measure
            # is carried by `modifier` instead.
            if name and name.lower() != "undetermined":
                unit_names[row["id"]] = name

    portions = []
    for row in _rows(archive, portion_member):
        food = foods.get(row.get("fdc_id", ""))
        gram_weight = _to_float(row.get("gram_weight"))
        if food is None or not gram_weight:
            continue
        amount = _to_float(row.get("amount")) or 1.0
        measure = (
            unit_names.get(row.get("measure_unit_id", ""), "")
            or (row.get("portion_description") or "").strip()
            or (row.get("modifier") or "").strip()
        )
        if not measure:
            continue
        portions.append(ParsedPortion(
            fdc_id = food.source_ref,
            amount = amount,
            measure = measure,
            gram_weight = gram_weight,
        ))
    return portions


def _to_float(raw) -> Optional[float]:  # noqa: ANN001
    try:
        text = (raw or "").strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def _replace_dataset(repository, source: str, foods, portions) -> None:  # noqa: ANN001
    """Swap a dataset wholesale: delete this source's rows, insert the new set.

    Whole-replace rather than upsert because a re-import is "take the current
    release", and reconciling ~8k rows one-by-one would be slower and buy
    nothing. StockItem links are `SET NULL` on delete, so a re-import quietly
    unlinks items rather than cascading into the pantry — the honest failure
    mode, and the reason re-import isn't offered casually in the UI.
    """
    existing = repository.get(NutritionFood).where(
        Field(NutritionFood, NutritionFood.Fields.SOURCE).eq(source)
    ).all()
    for food in existing:
        # Portions cascade on the FK; only the foods need removing explicitly.
        repository.remove(food)
    repository.save_changes()

    # Foods are committed **before** portions, and that ordering is load-bearing.
    # `NutritionPortion.nutrition_food_id` is a plain UUID column with no ORM
    # relationship (R-032), so SQLAlchemy's unit of work has no dependency graph
    # to sort by and is free to flush portions first — which it does, and every
    # row then fails the foreign key. The synthetic fixture the parser tests use
    # never caught it because those tests don't touch the database; the real
    # 8k-row SR Legacy import fails on the first flush.
    for food in foods:
        repository.add(food)
    repository.save_changes()

    # Only now do the foods have their real ids — `repository.add()` assigns a
    # fresh one to every entity, discarding whatever it was constructed with.
    # So the parse-time link (USDA's `fdc_id`) is resolved here, against ids
    # that actually exist.
    id_by_fdc_id = {food.source_ref: food.id for food in foods}
    for portion in portions:
        food_id = id_by_fdc_id.get(portion.fdc_id)
        if food_id is None:
            continue
        repository.add(NutritionPortion(
            id = uuid4(),
            nutrition_food_id = food_id,
            amount = portion.amount,
            measure = portion.measure,
            gram_weight = portion.gram_weight,
        ))
    repository.save_changes()
