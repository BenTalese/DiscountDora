"""Recipe dietary-tag framing.

C-4 Chunk 2 moved the tag *vocabulary* out of code into the
user-configurable `DietaryTag` table (seeded with the previous defaults).
What remains here is the plain-English disclaimer the SPA and assistant
surface alongside any tag-based UI — kept in one place so the wording stays
consistent if we tighten or loosen the framing later.

Honest framing: tags are a planning aid the user opts into per recipe. They
are NOT a substitute for reading the ingredient list when food safety
matters — the UI and assistant tools both say so explicitly.
"""

RECIPE_TAG_DISCLAIMER = (
    "Tags reflect what the recipe was tagged with — a planning aid, not "
    "a substitute for reading the ingredient list when food safety matters."
)
