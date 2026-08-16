"""Nutrition complex-mode — a food with known nutrient values per 100g.

One row per food, from whichever source provided it. Rows are a *cache of
someone else's data*, never user-authored domain truth: the household's own
contribution is the **link** from a StockItem to one of these, which is
always an explicit human confirmation (P12 No-invent — we never auto-match).

Sources differ in what they're good for, which is why the app carries more
than one and badges every search result with where it came from:

- `usda_foundation` / `usda_sr_legacy` — generic whole foods ("Banana, raw",
  "Flour, wheat, all-purpose"). Public domain (CC0), bulk-downloaded, works
  offline. The right answer for recipe ingredients.
- `usda_api` — the same USDA data fetched live via an api.data.gov key, for
  installs that would rather not hold the dataset on disk.
- `off` — Open Food Facts, packaged goods reached by barcode. ODbL: keep the
  attribution, and note that share-alike attaches to a *published* derived
  database (a self-hosted household's own cache is not that).

Per-100g is the storage basis because it's the one basis every source agrees
on; portions ("1 cup, chopped" → 125g) live in `NutritionPortion`.
"""
from dataclasses import dataclass
from datetime import datetime

from dora_api.domain.entities.base_entity import BaseEntity


# R-010 carve-out: closed-set string sentinels rather than a DB enum, matching
# the house convention (SQLite-portable, no CHECK constraint). Validated at the
# import/lookup boundary; every read goes through a named constant.
NUTRITION_SOURCE_USDA_FOUNDATION = "usda_foundation"
NUTRITION_SOURCE_USDA_SR_LEGACY = "usda_sr_legacy"
NUTRITION_SOURCE_USDA_API = "usda_api"
NUTRITION_SOURCE_OFF = "off"
NUTRITION_SOURCE_VALUES = (
    NUTRITION_SOURCE_USDA_FOUNDATION,
    NUTRITION_SOURCE_USDA_SR_LEGACY,
    NUTRITION_SOURCE_USDA_API,
    NUTRITION_SOURCE_OFF,
)

# Human-facing source names. The lookup UI badges every result with one of
# these so "where did this number come from?" is answerable at a glance
# (P3 Honest) — the owner asked for exactly this.
NUTRITION_SOURCE_LABELS = {
    NUTRITION_SOURCE_USDA_FOUNDATION: "USDA Foundation",
    NUTRITION_SOURCE_USDA_SR_LEGACY: "USDA SR Legacy",
    NUTRITION_SOURCE_USDA_API: "USDA (live)",
    NUTRITION_SOURCE_OFF: "Open Food Facts",
}

# Sources that arrive via the bulk-dataset importer (as opposed to a live
# API call). The admin page reports import counts per dataset from this.
NUTRITION_DATASET_SOURCES = (
    NUTRITION_SOURCE_USDA_FOUNDATION,
    NUTRITION_SOURCE_USDA_SR_LEGACY,
)


@dataclass
class NutritionFood(BaseEntity):
    # Which catalogue this row came from — one of NUTRITION_SOURCE_VALUES.
    source: str
    # The source's own identifier: an FDC id for USDA rows, the EAN for OFF.
    # (source, source_ref) is unique, so re-importing a dataset updates rows
    # in place instead of duplicating the catalogue.
    source_ref: str
    name: str
    brand: str | None = None
    # Set for packaged goods (OFF, USDA Branded). Lets the lookup match a
    # typed-in barcode directly against the local cache before any network
    # call. NULL for generic foods, which have no barcode by nature.
    barcode: str | None = None
    # Per 100g. Nullable throughout: a source can know a food's protein but
    # not its fibre, and inventing a 0 would be a lie (P12 No-invent).
    # `kcal_per_100g` is the only one the UI treats as load-bearing.
    #
    # The set is defined once in `features/nutrition/nutrients.py` — that
    # module owns which nutrients exist and how each source names them; these
    # are the columns it fills. Sodium is stored in MILLIgrams (how packs
    # state it); every other value is grams.
    kcal_per_100g: float | None = None
    protein_g_per_100g: float | None = None
    carbs_g_per_100g: float | None = None
    sugars_g_per_100g: float | None = None
    fat_g_per_100g: float | None = None
    saturated_fat_g_per_100g: float | None = None
    fibre_g_per_100g: float | None = None
    sodium_mg_per_100g: float | None = None
    imported_at: datetime | None = None

    class Fields(BaseEntity.Fields):
        SOURCE = "source"
        SOURCE_REF = "source_ref"
        NAME = "name"
        BRAND = "brand"
        BARCODE = "barcode"
        KCAL_PER_100G = "kcal_per_100g"
        PROTEIN_G_PER_100G = "protein_g_per_100g"
        CARBS_G_PER_100G = "carbs_g_per_100g"
        SUGARS_G_PER_100G = "sugars_g_per_100g"
        FAT_G_PER_100G = "fat_g_per_100g"
        SATURATED_FAT_G_PER_100G = "saturated_fat_g_per_100g"
        FIBRE_G_PER_100G = "fibre_g_per_100g"
        SODIUM_MG_PER_100G = "sodium_mg_per_100g"
        IMPORTED_AT = "imported_at"
