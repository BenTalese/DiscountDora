"""P2-08 — canonical recipe-tag vocabulary.

We keep these in code rather than a `RecipeTagType` table for two reasons:
  1. The set is small and rarely changes — extending the list is a Python
     change, not a data migration.
  2. A curated vocabulary prevents drift ("gluten-free" vs "Gluten Free"
     vs "GF") that would make filtering unreliable.

The frontend pulls this list via `GET /api/recipes/tags` so the SPA's
tag picker stays in sync without copying the constants. Tags stored on
the `RecipeTag` association table are validated against
`ALLOWED_RECIPE_TAGS` on create/update.

Honest framing: these are a planning aid the user (or recipe-importer)
opts into per recipe. Dora and the recipe filter both surface tags
verbatim. They are NOT a substitute for reading the ingredient list when
food safety matters — the UI and assistant tools both say so explicitly.
"""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecipeTagDefinition:
    """One row in the curated catalogue. `category` groups tags in the
    SPA picker; `label` is the human-friendly display name.
    """
    value: str
    label: str
    category: str


# Order within each category drives the SPA's chip order. Categories
# themselves are surfaced in a fixed order on the frontend.
RECIPE_TAG_CATALOGUE: tuple[RecipeTagDefinition, ...] = (
    # Dietary patterns — broad lifestyle choices.
    RecipeTagDefinition("vegetarian",    "Vegetarian",     "Dietary pattern"),
    RecipeTagDefinition("vegan",         "Vegan",          "Dietary pattern"),
    RecipeTagDefinition("pescatarian",   "Pescatarian",    "Dietary pattern"),

    # Allergen-free — narrows by ingredient exclusion, not a positive claim.
    RecipeTagDefinition("gluten-free",   "Gluten-free",    "Allergen-free"),
    RecipeTagDefinition("dairy-free",    "Dairy-free",     "Allergen-free"),
    RecipeTagDefinition("nut-free",      "Nut-free",       "Allergen-free"),
    RecipeTagDefinition("egg-free",      "Egg-free",       "Allergen-free"),
    RecipeTagDefinition("soy-free",      "Soy-free",       "Allergen-free"),
    RecipeTagDefinition("shellfish-free","Shellfish-free", "Allergen-free"),

    # Nutritional posture — "lower than typical" rather than absolute claims.
    RecipeTagDefinition("low-carb",      "Low-carb",       "Nutritional"),
    RecipeTagDefinition("low-fat",       "Low-fat",        "Nutritional"),
    RecipeTagDefinition("low-sugar",     "Low-sugar",      "Nutritional"),
    RecipeTagDefinition("low-sodium",    "Low-sodium",     "Nutritional"),

    # Diet patterns — specific named diets people search by name.
    RecipeTagDefinition("keto",          "Keto",           "Diet pattern"),
    RecipeTagDefinition("paleo",         "Paleo",          "Diet pattern"),
    RecipeTagDefinition("whole-30",      "Whole30",        "Diet pattern"),

    # Religious.
    RecipeTagDefinition("halal",         "Halal",          "Religious"),
    RecipeTagDefinition("kosher",        "Kosher",         "Religious"),
)

ALLOWED_RECIPE_TAGS: frozenset[str] = frozenset(t.value for t in RECIPE_TAG_CATALOGUE)


# A short, plain-English disclaimer the SPA and assistant can surface
# alongside any tag-based filter. Kept here so the wording stays in one
# place — if we tighten or loosen the framing later, it only changes here.
RECIPE_TAG_DISCLAIMER = (
    "Tags reflect what the recipe was tagged with — a planning aid, not "
    "a substitute for reading the ingredient list when food safety matters."
)
