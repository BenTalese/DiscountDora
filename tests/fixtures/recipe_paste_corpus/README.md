# Recipe paste corpus

Fixtures for `parse_recipe_from_text` — the paste-based recipe importer's
text parser. Each `.txt` file is a **verbatim Ctrl+A / Ctrl+C paste**
from a real recipe website. Ground truth for each fixture lives in
`_expectations.py`.

## Why this exists

The paste importer replaces the URL-fetch importer for legal reasons
(see [IMPL_PLAN_RECIPE_IMPORTER.md](../../../docs/04_proposals/IMPL_PLAN_RECIPE_IMPORTER.md)).
Text input has no JSON-LD to fall back on, so the parser has to handle
"the visible-text shape of a modern recipe page." The corpus is the
fence for "does it work well enough on the sites users actually paste
from?"

## Adding a fixture

1. Open the recipe page in your browser.
2. `Ctrl+A` → `Ctrl+C` → paste into `tests/fixtures/recipe_paste_corpus/<sitename><n>.txt`.
   Don't clean it up — the noise (nav, story, footer, comments) is the
   parser's problem, not yours.
3. Add an entry in `_expectations.py` with **loose** minimum-shape
   assertions. Read `_expectations.py`'s module docstring for field
   semantics; the rule of thumb is:
   - `name_contains`: the substring that must appear in the extracted
     name (guards against nav/related-post-link mis-picks).
   - `servings` / `prep_minutes` / `cook_minutes` / `total_minutes`:
     exact ints, but only assert what the fixture unambiguously
     publishes. Leave others `None`.
   - `min_ingredients` / `min_steps`: lower bounds. Loose so a parser
     tweak that finds one extra never breaks the fence.
   - `first_ingredient_contains`: the strongest "did we find the right
     block?" signal.
   - `notes`: free-form for future readers.
4. `pytest tests/test_parse_recipe_from_text.py -k <sitename>` to run
   just your new fixture.

## Class A vs Class B

- **Class A** — sites with explicit `Ingredients` / `Instructions` /
  `Method` / `Directions` header lines. Anchor-based parser handles
  them (Chunk 2). Most of the corpus.
- **Class B** — sites without headers. Deb Perelman's Smitten Kitchen
  is the canonical shape: `Serves N` line, then unbulleted ingredients,
  then unnumbered prose steps. Grammar-based fallback handles them
  (Chunk 3).

If you're adding a fixture that fails the Class A parser but shouldn't,
tag its `notes` field with `CLASS B` so future readers know why.
