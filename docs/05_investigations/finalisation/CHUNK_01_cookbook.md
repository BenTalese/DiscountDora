# Chunk 01 — Cookbook

**Analysed:** 2026-10-23 · **Analyst session:** finalisation overnight run (single session, no sub-agents)
**Scope (from PLAN §4):** Recipes CRUD, import (paste + share target), Recipe Detail, tags/vocab, favourites, cookability, meals-worth/pool, cost estimate, plus the nutrition backend the recipe handlers call into (rollup, HSR/Nutri-Score, lookup/matching, dataset import).
**Boundaries:** Cook Mode (`RecipeCookMode.vue`, tts) → Chunk 4. Meal plans → Chunk 2. The vocab/nutrition *settings pages* (`pages/settings/Recipe*Settings.vue`, `NutritionMatchingSettings.vue`, `AdminSystemNutritionSettings.vue`) → Chunk 13. Stock-item food picker (`NutritionFoodPicker.vue`) → Chunk 6. `domain/units.py` → Chunk 20 (read here only as a consumer).

## 0. Reading list + files walked

**Planning docs consulted:** `PROPOSAL_COOKBOOK.md` (§2.1–2.13, §7 coverage), `IMPL_PLAN_COOKBOOK.md` (chunks 1–10), `IMPL_PLAN_RECIPE_IMPORTER.md` (chunks 4–6 as cited in code), `PROPOSAL_RECIPE_IMAGE_STEPS.md`, `RECIPE_PRICE_UNIT_MISMATCH.md`, `MAGIC_BEHAVIOUR_AUDIT.md` F8/F9/F10, feedback `# RECIPES OVERVIEW` + `# RECIPE DETAIL`, open FUs grep'd for recipe/nutrition/ingredient (list in §C).

**Files walked (every file opened, with line count):**

| File | Lines | Role |
|---|---|---|
| `dora_api/features/recipes/get_recipes.py` | 1910 | DTOs, filters, list/detail handler, hydration pipeline, image bytes routes, tag catalogue |
| `dora_api/features/recipes/create_recipe.py` | 506 | POST handler + request models |
| `dora_api/features/recipes/update_recipe.py` | 561 | PATCH handler + request models |
| `dora_api/features/recipes/new_recipe_version.py` | 296 | clone into version group |
| `dora_api/features/recipes/cook_recipe.py` | 96 | pool bump + CookEvent |
| `dora_api/features/recipes/pool.py` | 90 | `bump_pool` authority |
| `dora_api/features/recipes/adjust_recipe_meals.py` | 60 | pool delta |
| `dora_api/features/recipes/delete_recipe.py` | 51 | DELETE |
| `dora_api/features/recipes/ingredient_choice.py` | 69 | label / preferred buy / product validation |
| `dora_api/features/recipes/recipe_cost.py` | 487 | pricing ladder, batch + single |
| `dora_api/features/recipes/import_recipe_from_content.py` | 171 | paste importer + fuzzy match |
| `dora_api/features/recipes/imported_recipe_dtos.py` | 79 | importer wire shapes |
| `dora_api/features/recipes/_parse_recipe_from_text.py` | 1201 | parser (outline only — pure text heuristics, corpus-tested) |
| `dora_api/features/recipes/unlinked_ingredients.py` | 223 | bulk-linker endpoints |
| `dora_api/features/recipes/recipe_tag_access.py` | 178 | RecipeTag link table helpers |
| `dora_api/features/recipes/recipe_tool_access.py` | 183 | RecipeTool link table helpers + step derivation |
| `dora_api/features/recipes/recipe_step_access.py` | 285 | RecipeStep + links |
| `dora_api/features/recipes/recipe_step_image_access.py` | 123 | RecipeStepImage |
| `dora_api/features/recipes/recipe_section_access.py` | 111 | RecipeSection |
| `dora_api/features/recipe_collections/*.py` (4 files) | 240 | collection CRUD |
| `dora_api/features/categories/manage_categories.py` | 194 | vocab CRUD (diffed against cuisines) |
| `dora_api/features/cuisines/manage_cuisines.py` | 197 | vocab CRUD |
| `dora_api/features/nutrition/recipe_rollup.py` | 473 | rollup + ratings |
| `dora_api/features/nutrition/household_measures.py` | 191 | grams resolution |
| `dora_api/features/nutrition/sources.py` | 116 | source availability |
| `dora_api/features/nutrition/nutrition_endpoints.py` | 292 | sources/lookup/resolve/unmatched/accept-all/import |
| `dora_api/features/nutrition/lookup.py` | 484 | multi-source food search |
| `dora_api/features/nutrition/suggestions.py` | 277 | name matcher |
| `dora_api/features/nutrition/nutrients.py` | 280 | nutrient table + display rows |
| `dora_api/features/nutrition/text_matching.py` | 51 | tokeniser |
| `dora_api/features/nutrition/food_categories.py` | 105 | fvnl / fvl sets |
| `dora_api/features/nutrition/dataset_import.py` | 521 | outline + header (USDA zip import) |
| `dora_api/domain/recipe_cookability.py` | 124 | tri-state cookability |
| `dora_api/domain/recipe_tags.py` | 17 | disclaimer |
| `dora_api/domain/entities/recipe.py`, `recipe_ingredient.py` | 125 | entities |
| `dora_api/domain/health_star_rating.py`, `nutri_score.py` | 576 | outline (rating tables) |
| `dora_api/persistence/table_mappings.py` L1680–1860 | — | recipe/meal-plan relationship mappings |
| `dora_api/features/data/export_recipe.py` | — | routes only (CSV + print-view) |
| `web_app/src/pages/RecipesOverview.vue` | 1747 | cookbook list |
| `web_app/src/pages/RecipeDetailPage.vue` | 2727 | recipe page |
| `web_app/src/components/RecipeCard.vue` | 320 | card |
| `web_app/src/components/recipes/RecipeRow.vue` | 314 | compact row |
| `web_app/src/components/RecipeEditDialog.vue` | 195 | stub-creator |
| `web_app/src/components/recipes/RecipeStructuredMethod.vue` | 731 | steps, both faces |
| `web_app/src/components/recipes/RecipeIngredientRowEditor.vue` | 596 | row editor |
| `web_app/src/components/recipes/RecipeNutritionCard.vue` | 605 | nutrition panel |
| `web_app/src/components/recipes/RecipeCostDialog.vue` | 334 | cost breakdown |
| `web_app/src/components/recipes/{RecipeImportDialog,RecipeRatingChip,RecipeHealthStars,RecipeNutriScore,ExpiringChip,RecipeMissingIngredientChip,RecipeBeliefChip,MealStepper,RecipeInfoCard,RecipeStepImagesEditor,RecipeStepImagesViewer,RecipeStepLinksDialog,CookModeGuardDialog}.vue` | ~1700 | script blocks read |
| `web_app/src/composables/useRecipeDisplay.ts` | 239 | shared presentation model |
| `web_app/src/composables/useRecipeEditor.ts` | 264 | form model / PATCH build |
| `web_app/src/composables/useRecipeExport.ts` | 78 | CSV + print |
| `web_app/src/composables/useNutritionRating.ts` | 177 | scheme-aware rating |
| `web_app/src/helpers/{recipeCostSort,recipeVocabulary,formatQuantity,scaleQuantity,cookModeGuard,addToListRows}.ts` | 438 | helpers |
| `web_app/src/stores/recipeStore.ts`, `recipeVocabStore.ts` | 248 | stores |
| `web_app/src/services/api/recipeApiService.ts` | 405 | API client |
| `web_app/src/models/recipe.ts` | 465 | types (outline) |
| `web_app/src/pages/HelpPage.vue` GUIDES, `components/help/HelpHint.vue`, `dora_api/features/assistant/app_knowledge.py` | — | current help |
| Tests: `tests/test_recipe_*.py`, `test_nutrition_*.py`, `test_health_star_rating.py`, `test_nutri_score.py`, `test_parse_recipe_from_text.py`, `tests/e2e/dora_api/test_recipe_router.py` (783), `test_recipes_query_count.py` (128), `test_recipe_import_routes.py` (70), `test_nutrition_router.py` (370), `test_category/cuisine/tool/dietary_tag_router.py`, vitest `web_app/test/unit/recipe*.spec.ts`, `useNutritionRating.spec.ts`, `formatQuantity.spec.ts`, `scaleQuantity.spec.ts`, `cookModeGuard.spec.ts`, `addToListRows.spec.ts` | — | inventoried for §D |

## A. Full Systems Test — Cookbook

### A1. Preconditions
- Seeded install (`dora`/`dora` e2e seed) with ≥ 12 recipes, at least one each of: structured steps, free-text, image steps; one with sections; one with an unlinked ingredient; one in a version group.
- Money and nutrition feature flags are the two conditions that change this surface; run the golden path once with both **off** (default) and once with money on + nutrition **complex** with a dataset imported.

### A2. Golden path
Persona: **Fresh install → Dense user** (the surface is identical; density is what the dense run tests).
1. Stock → Cookbook (`/cookbook`) → page renders cards; toolbar shows New recipe · Import · Compact/Cards · filter toggle · search → expected: footer counts "Shown / Cookable now / Favourites".
2. Toggle Compact → rows; reload → mode remembered (localStorage).
3. Open filters → set Cuisine + a dietary tag include → list narrows, badge count 2, Clear filters resets → expected: panel opens itself whenever a filter is active after navigation.
4. Tick "Uses expiring ingredients" → list re-sorts soonest-expiry first, each card wears "Uses N expiring"; open a result → its ingredient rows carry "Use soon"/"Expired" chips → back → chip still on and list still narrowed (FU fixed 09-09).
5. New recipe → stub dialog (Name / Cuisine / Category / Collection) → Create & open → lands on `/cookbook/<id>` with empty rail.
6. Pencil on masthead → edit serves/prep/cook/difficulty/when → Done → Save bar "Saved"; facts update; Total shown only when prep+cook > 0.
7. Pencil on Ingredients → Add ingredient → row editor opens immediately → type an unknown name → "Use …" → dialog "Add to pantry? / Keep as free text" → both paths close the picker; Done → row renders (Free text chip when unlinked).
8. Add section → name it → move an ingredient into it via the row editor → section renders as a card; Move section up/down; Remove section → rows fall back to main.
9. Pencil on Method → switch Structured → Add step → link ingredients via the link icon → Done → tap a step → its ingredients light; tap an ingredient → steps light.
10. Save → Cook mode button is primary; status strip reads "Everything in stock" or "N missing" with "Add N to a list" → picker (shared AddToListDialog) → confirm → cart button state flips.
11. Favourite toggles from card, row and page; New version → navigates to `(v2)`; Version information lists siblings with created dates.
12. Import → paste a recipe page's text + URL → preview toast "N matched · M unlinked" → recipe opens; Settings → Unlinked ingredients shows the groups; bulk-link one → recipe's cookable flips from unknown.
13. Delete → confirm → back on `/cookbook`.

### A3. Edge cases
- Save with a half-built ingredient row → "Not saved: 1 ingredient has no item or text yet", row wears "Needs an item" chip.
- Save with an empty structured step → blocked, step field turns red only after the attempt.
- Rename a recipe to an existing name → 422 business-rule toast; rename to its own name → saves (FU-528 family).
- Delete the cuisine a recipe uses (Settings) → recipe shows "Any cuisine", still saves (slot vocabulary: a recipe whose `time_of_day` slot was deleted still saves — 09-01 fix).
- Leave with unsaved changes → "Stay / Leave without saving" dialog; browser reload → native prompt.
- Nutrition complex with no dataset → panel reads "Nothing to add up yet", gaps list "No food linked" with Find a food.
- Money off → no cost cell, no Cost sort axis, no cost chip (server sends nothing).
- Batch cook-style off → no Meals prepared chip/filter/sort; a persisted `meal_count` sort snaps back to Name.
- Share-target landing (`/cookbook?share_text=…`) → import dialog pre-filled; query stripped after.
- Deep links: `?usesStockItem=<id>`, `?cookable=true`, `?expiring=true`.
- Offline (read-only, R-052): cookbook renders cached list; Save fails with a toast, dirty pill stays.

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ | ✓ (perf: 300+ recipes, list query count) | ✓ (money/nutrition off) | ✓ (both on, shortcuts `g r`, `n`) | – | ✓ (favourites are per-recipe, not per-user — see C8-1) | – | – |

### A5. Load-bearing conditions
- **360×640**: masthead stacks, facts and actions scroll sideways (D-011), method heading wraps the three-way switch to its own line, row buttons lift to 44px.
- **1920+**: filter row wraps to two lines (`wide-wraps`); rail is sticky with inner scroll.
- **All themes × light/dark**: lit-row tint, severity edge stripes, Nutri-Score grade colours (hard-coded hex — C11), rating pill (FU-772).
- **Offline/bad network**: expiring filter fetch failure flips the chip off with a toast.
- **Reduced motion**: FadeTransition on list swap; `q-slide-transition` on rating working.

### A6. Release-gate rows
- Create → edit all three regions → save → reload shows every change (incl. step links and section membership).
- Cookbook list of ≥ 100 recipes loads in one page set with query count pinned (`test_recipes_query_count`).
- Import a real pasted recipe end-to-end and bulk-link one unlinked group.
- Cost + nutrition both on: card chip, detail cell, breakdown dialog and nutrition panel agree on coverage counts.

## B. Help content — Cookbook

### B1. Current help audit
- `HelpPage.vue` GUIDES group **"Recipes & meals"** has exactly two entries: *Cook mode* (summary only, `path: '/cookbook'`) and *Build a meal plan*. **Nothing** on: importing, versions, sections, structured/free-text/photo methods, step links/highlight, tools derivation, dietary tags disclaimer, cookability tri-state, the cost estimate, nutrition modes/ratings, favourites, the pool, the bulk-linker, the share target. The cookbook is the least-documented major surface in the app.
- No `HelpHint` chip exists on any recipe surface (the three live chips are all on `StockItemDetailPage.vue`).
- `app_knowledge.py` `APP_OVERVIEW` "Recipes" paragraph (L18–24) is stale: says "cook time, difficulty, cuisine, category, and a step-by-step Cook mode … Favourite recipes are surfaced first in suggestions" — omits versions, sections, three method modes, tools, dietary tags, import, cost, nutrition, the Cookbook name, and "Mark made" wording is gone. Also "Recipes:" should read "Cookbook:" (feedback L230, PROPOSAL_COOKBOOK §2.1).
- `InfoTip` on the "Cookable now" chip (`RecipesOverview.vue:134`) is correct. `RecipeNutritionCard` InfoTip "Nutrition basis" is correct.

### B2. Help entries (one per feature / auto-behaviour)

#### Add and edit a recipe
- **Group:** Recipes & meals (rename group to **"Cookbook"** to match the nav)
- **What it does:** A recipe is a name plus ingredients, a method and a few facts (serves, prep, cook, difficulty, when, cuisine, category, collection).
- **When it fires / how to trigger it:** Cookbook → New recipe makes a stub and opens its page. On the page, each block (details · ingredients · method) has its own pencil; edits mark the page unsaved and Save commits all of them at once.
- **What controls it:** Always on — no setting. Which vocabularies appear (cuisines, categories, dietary tags, tools, meal slots) is set under `/settings/kitchen-setup/…`.
- **What it costs / might get wrong:** Nothing is saved until you press Save or Done; leaving the page asks first. A row with no pantry item and no text blocks the save and says which row.
- **Related:** Ingredients and the pantry · Three ways to write a method · Sections
- **Chip:** `RecipeDetailPage.vue:76` beside the masthead pencil → `<HelpHint topic="Add and edit a recipe">`.
- **Source:** `RecipeDetailPage.vue`, `useRecipeEditor.ts`, PROPOSAL_COOKBOOK §2.13.

#### Ingredients and the pantry
- **Group:** Cookbook
- **What it does:** An ingredient usually points at a pantry item, so Dora can say whether you have it. It can instead be plain text (no pantry link), and a linked one can name *which one* you mean ("tasty cheddar" under Cheese) by picking a preferred buy or product.
- **When it fires / how to trigger it:** Edit ingredients → tap a row → the editor. Typing a name the pantry doesn't have offers "Use …" and asks whether to add it to the pantry or keep it as text.
- **What controls it:** Always on. Products are offered as the "which one" list only when Products is on (`/settings/admin/system/features`).
- **What it costs / might get wrong:** Free-text rows can't be checked for stock, so a recipe with one reads as "to link" rather than cookable or not. Optional rows never affect cookability.
- **Related:** Can I cook this? · Fix unlinked ingredients in bulk
- **Chip:** `RecipeDetailPage.vue:406` (Ingredients heading) → `<HelpHint topic="Ingredients and the pantry">`.
- **Source:** `ingredient_choice.py`, `RecipeIngredientRowEditor.vue`, cookbook §1.9.

#### Can I cook this?
- **Group:** Cookbook
- **What it does:** Each recipe shows whether every required ingredient is in stock. Three answers: yes, no (lists what's missing), or unknown (some rows aren't linked to the pantry).
- **When it fires / how to trigger it:** Automatically, from your recorded stock levels. The "Cookable now" filter and the dashboard's cookable count read the same rule.
- **What controls it:** Always on. "Missing" means **out of stock** — a low item still counts as cookable.
- **What it costs / might get wrong:** It trusts your recorded levels. If Dora's stock inference disagrees, the card says so as a remark ("Dora thinks…") without changing the verdict. Entering cook mode on a non-cookable recipe asks first.
- **Related:** Substitutes (Stock) · The "Dora thinks…" hint (Stock)
- **Chip:** none (InfoTip on the chip already covers it).
- **Source:** `domain/recipe_cookability.py`, `useRecipeDisplay.ts`, `cookModeGuard.ts`.

#### Three ways to write a method
- **Group:** Cookbook
- **What it does:** Free text (one block, each line becomes a numbered step), Structured (steps and sub-steps that can link to ingredients, tools and a section, with optional hints and timers), or Photos (an ordered set of step images).
- **When it fires / how to trigger it:** Edit method → the Structured / Free text / Photos switch. Switching never deletes the other mode's content.
- **What controls it:** Always on. New recipes start as free text.
- **What it costs / might get wrong:** Only Structured can highlight which ingredients a step uses (tap a step or an ingredient). In Structured mode the recipe's **tools are derived** from its steps and can't be edited separately; in the other two modes the Tools field is inside the method.
- **Related:** Cook mode · Add and edit a recipe
- **Chip:** `RecipeDetailPage.vue:701` (Method heading).
- **Source:** `recipe_step_access.py`, `sync_recipe_tools_from_steps`, `RecipeStructuredMethod.vue`, PROPOSAL_RECIPE_IMAGE_STEPS.

#### Sections
- **Group:** Cookbook
- **What it does:** Named groups inside one recipe ("For the sauce", "To serve") that hold ingredients and top-level steps.
- **When it fires / how to trigger it:** Edit ingredients → Add section. Move a row into a section from its editor; Remove section sends its rows back to the main list.
- **What controls it:** Always on.
- **What it costs / might get wrong:** Sub-steps follow their parent's section.
- **Related:** Three ways to write a method
- **Chip:** none (tooltip on Add section covers it).
- **Source:** `recipe_section_access.py`.

#### Import a recipe by pasting it
- **Group:** Cookbook
- **What it does:** Paste a recipe page's text (Ctrl+A, Ctrl+C on the site, Ctrl+V here) and Dora picks out the name, times, servings, ingredients and steps. Ingredients are matched to your pantry by name; unmatched ones are kept as text.
- **When it fires / how to trigger it:** Cookbook → Import. On Android, sharing a page to Dora opens the same dialog pre-filled.
- **What controls it:** Always on. The URL you type is kept as the recipe's Source and is never fetched by the server.
- **What it costs / might get wrong:** Sites vary; when fewer than three ingredients are found you get the page text in Instructions to tidy by hand. Matching is fuzzy (score ≥ 70) and can pick the wrong pantry item — check the rows.
- **Related:** Fix unlinked ingredients in bulk
- **Chip:** `RecipesOverview.vue:35` (Import button tooltip could link) — optional.
- **Source:** `import_recipe_from_content.py`, `_parse_recipe_from_text.py`, MAGIC F8.

#### Fix unlinked ingredients in bulk
- **Group:** Cookbook
- **What it does:** Every ingredient that isn't linked to a pantry item, grouped by its text across all recipes, so "1 onion" in nine recipes is linked once.
- **When it fires / how to trigger it:** `/settings/kitchen-setup/unlinked-ingredients` (verify exact path in Chunk 13).
- **What controls it:** Always on.
- **What it costs / might get wrong:** Linking is by exact (whitespace/case-insensitive) text match; "onion, diced" and "onion" are two groups.
- **Related:** Import a recipe by pasting it · Can I cook this?
- **Chip:** on that settings page heading (Chunk 13).
- **Source:** `unlinked_ingredients.py`.

#### Versions of a recipe
- **Group:** Cookbook
- **What it does:** New version copies the whole recipe (ingredients, sections, steps, photos, tags, tools) into a sibling named "(vN)". Versions are equal peers — no "current" one — and each keeps its own meal pool and favourite flag.
- **When it fires / how to trigger it:** Recipe page → New version (action row or Version information panel).
- **What controls it:** Always on.
- **What it costs / might get wrong:** The copy starts unfavourited and with an empty meal pool; meal plans pick a specific version.
- **Related:** Add and edit a recipe
- **Chip:** `RecipeDetailPage.vue:975` (Versions sub-heading).
- **Source:** `new_recipe_version.py` (DEC-2), FU-741.

#### Meals prepared (the pool)
- **Group:** Cookbook
- **What it does:** How many portions of a recipe are already cooked and waiting (freezer, fridge). Cook mode asks how many you made and adds them; past meal-plan days take them away; the planner shows a shortfall when the plan wants more than exist.
- **When it fires / how to trigger it:** Finishing cook mode, the ± stepper on the recipe page's Last cooked cell, and the meal plan's daily reconcile.
- **What controls it:** `/settings/admin/system/cooking` — cook style **Batch** shows the pool everywhere; **Fresh** hides it (the filter, sort axis and stepper disappear).
- **What it costs / might get wrong:** Never goes below zero. "N free · M planned" explains why adding one can still read 0 free.
- **Related:** Build a meal plan · Cook mode
- **Chip:** `RecipeDetailPage.vue:372` beside the stepper.
- **Source:** `pool.py`, `cook_recipe.py`, MAGIC F10, FU-317.

#### What a recipe costs
- **Group:** Cookbook (money)
- **What it does:** An estimate from your own prices: each ingredient is priced from the cheapest linked product offer, else the item's logged prices; the amount is converted into the price's unit, and anything that can't be bridged is reported unpriced rather than guessed. Cards show cost per serving; the page shows the total, "N of M priced", and a breakdown of who dominates the bill and why rows are unpriced.
- **When it fires / how to trigger it:** Automatically on every recipe when money is on.
- **What controls it:** `/settings/admin/system/money` (money features) — off by default; with it off nothing is computed or shown.
- **What it costs / might get wrong:** It's an estimate, not a quote. A pack sold by weight can't price "3 of them" unless the product records how many are in the pack; a cup of something needs a density or a measured portion.
- **Related:** Prices on a stock item (Stock) · Budget
- **Chip:** `RecipeDetailPage.vue:344` (Estimated cost cell label).
- **Source:** `recipe_cost.py`, `RecipeCostDialog.vue`, R-076/ADR-073, FU-874/904/905.

#### Nutrition: off, simple, complex
- **Group:** Cookbook (nutrition)
- **What it does:** Off hides everything. Simple lets you type kcal per serving on a recipe and filter/sort on it. Complex links pantry items to foods in a nutrition catalogue and adds up each recipe's energy and nutrients per serving, always with its coverage ("From 7 of 9 ingredients"), and can show a Health Star Rating or Nutri-Score.
- **When it fires / how to trigger it:** Automatically on recipe cards and pages.
- **What controls it:** `/settings/admin/system/nutrition` (mode, rating scheme, datasets, Open Food Facts / USDA API); per-item food links under the item's page or the matching page.
- **What it costs / might get wrong:** Ratings are estimates from raw ingredient weight. A missing figure (e.g. sugars unknown for a food) flatters the rating — the panel names which figures were thin. The "≤ N kcal" filter judges the figure shown, even when coverage is partial (marked with *).
- **Related:** Link a food to a stock item (Stock) · What a recipe costs
- **Chip:** `RecipeDetailPage.vue:904` (Nutrition heading).
- **Source:** `recipe_rollup.py`, `nutrients.py`, `useNutritionRating.ts`.

#### Dietary tags are a planning aid
- **Group:** Cookbook
- **What it does:** Tags you put on a recipe (vegan, gluten-free…) drive the include/exclude filter. The disclaimer "Tags are a planning aid. Check the ingredient list when food safety matters." is shown whenever a tag filter is on.
- **What controls it:** `/settings/kitchen-setup/dietary-tags` edits the vocabulary.
- **Source:** `domain/recipe_tags.py`, `get_recipe_tag_catalogue`.

#### Mark cooked without cook mode
- **Group:** Cookbook
- **What it does:** Cooking a recipe stamps "Last cooked" today and (in batch style) adds to the pool; it also writes a cook event the stock item's History tab shows as "Used in <recipe>".
- **Source:** `cook_recipe.py` (MAGIC F10 verdict: keep silent). Owner feedback: "Mark made" → "Mark Cooked" wording — confirm the live label in cook mode (Chunk 4).

### B3. DoraBot corpus delta
Replace `app_knowledge.py` L18–24 with:
```
- Cookbook: the household's recipes. Each has ingredients (linked to pantry
  items so Dora knows whether you have them, or plain text), a method written
  as free text, structured steps or step photos, and facts like serves,
  prep/cook time, difficulty, cuisine, category, collection, dietary tags and
  tools. Filters cover all of those plus "cookable now", "uses expiring
  ingredients", "planned", kcal and cost (when those features are on).
  Recipes can be imported by pasting a page's text, copied as versions, and
  each tracks "meals prepared" — cooked-ahead portions in the pool that cook
  mode adds to and meal plans draw down. With money on, Dora estimates what a
  recipe costs from the user's own prices; with nutrition on, it adds up
  kcal per serving (and a Health Star Rating / Nutri-Score in complex mode).
```

## C. Senior review — Cookbook

Open FUs on this surface, cross-referenced rather than restated: FU-895, 902, 901, 900, 879, 876, 863, 858, 855, 793, 786, 772, 771, 770, 765, 761, 760, 757, 753, 750, 748, 746, 744, 742, 741, 736, 735, 734, 732, 730, 712, 691, 680, 670, 669, 646, 657, 645, 643, 638, 575, 624 (toast wrapper), 623 (dialog wrapper), 675 (BaseSelect sweep), 777.

### C1. Bugs (verified or high-confidence latent)

- **01-R1** · class bug (latent, high-confidence) · `web_app/src/helpers/cookModeGuard.ts:567` · `ingredientLabel` precedence is `stock_item_name ?? raw_text`, ignoring the ingredient `label` ("tasty cheddar") that `RecipeDetailPage.ingredientLabel` (L1591) shows first; the guard dialog and the detail page therefore name the same missing row differently once a label is set (shipped 2026-10-21). · **Exact change:** add `web_app/src/helpers/recipeIngredientLabel.ts` exporting `ingredientDisplayName(ing: {label?, stock_item_name, raw_text}): string` = `label || stock_item_name || raw_text || 'Unnamed ingredient'`; use it in `cookModeGuard.ts:567`, `addToListRows.ts:675` (`name:`), `useRecipeDisplay`? (no — it doesn't name rows), and have `RecipeDetailPage.ingredientLabel` delegate to it (keeping its store lookup for the item name). · blast S · test guard: `cookModeGuard.spec.ts`, `addToListRows.spec.ts` (extend with a labelled row) · **execute**.
- **01-R2** · class bug (latent) · `web_app/src/components/recipes/RecipeIngredientRowEditor.vue:527` · after `createStockItemAsync`, the new item is found by `stockItems.value.find((s) => s.name === name)` although the store call returns the created entity; a name that differs after server trimming/normalisation leaves `created` undefined and the row silently stays unanchored. · **Exact change:** `const created = await stockItemStore.createStockItemAsync({...});` then use `created.stock_item_id` / `created.name` directly; delete L527. · S · test guard: none (dialog) — manual: create an item with trailing space · **execute**.
- **01-R3** · class bug (latent, ordering) · `dora_api/features/recipes/get_recipes.py:1627–1716` · `handle_by_id` builds `RecipeDto.from_entity(entity)` *before* the hydrations but computes `_compute_estimated_cost` and `_compute_nutrition` **after** `_hydrate_inference` — fine — however `_hydrate_unallocated` runs on `[_WithAssoc]` whose `available_meals` came from `from_entity`, while `cook_recipe` notes the entity attribute is stale after `bump_pool` in the *same* request. Not reachable today (detail is a separate GET). · **Verdict:** waive — record only; no change.
- **01-R4** · class bug (stale contract comment, misleads maintainers) · `get_recipes.py:1631–1637` and `:1786–1792` · comments say the detail route "has no `uuid:` converter" and that "the old filter-by-id path on the list endpoint still works as the cookbook overview's primary call"; the route is `/<uuid:recipe_id>` (L1794) and the SPA uses `GET /recipes/<id>` (`recipeApiService.getAsync`). · **Exact change:** delete L1631–1637 comment; rewrite L1786–1792 to "Detail endpoint — the SPA's `getAsync`; the list endpoint's filter-by-id form is unused by the SPA." · S · **execute**.

### C2. Redundancy / DRY (R-001, R-003)

- **01-R5** · `dora_api/features/categories/manage_categories.py` (194) vs `cuisines/manage_cuisines.py` (197), `tools/manage_tools.py` (194), `dietary_tags/manage_dietary_tags.py` (209), plus `stock_groups/manage_stock_groups.py` (223), `meal_slots/manage_meal_slots.py` (246) · `diff` of categories vs cuisines after name substitution shows **only** the entity/router names differ: list-with-recipe-counts, create-with-dedupe-and-next-sequence, rename-with-dedupe, delete-with-affected-count. ~800 lines encoding one vocabulary manager four to six times. · **Exact change:** add `dora_api/features/_vocab/vocabulary_feature.py` with `register_vocabulary_crud(router, entity_cls, dto_name, id_field, recipe_fk_field, recipe_include_field, extra_fields=())` that defines the four handlers + routes; `manage_categories.py`/`manage_cuisines.py`/`manage_tools.py` become 10-line registrations. Dietary tags carry `category`; meal slots and stock groups have extra behaviour — keep them separate unless the factory's `extra_fields` hook covers them cleanly (decide at execution; start with the three identical ones). · M · test guard: `tests/e2e/dora_api/test_category_router.py`, `test_cuisine_router.py`, `test_tool_router.py` · **execute** (three identical modules first; dietary tags/meal slots/stock groups → follow-on if the factory fits).
- **01-R6** · `recipe_tag_access.py` vs `recipe_tool_access.py` · `_coerce_uuid`, `_all_*_ids`, `_name_to_id`, `validate_*_ids`, `resolve_*_filter_values`, `get_*_ids_for_recipes`, `set_*_ids_for_recipe`, `find_recipe_ids_with_all_*`, `find_recipe_ids_with_any_*` are the same nine functions over `(link_table, vocab_table, link_fk_name, vocab_noun)`. · **Exact change:** new `dora_api/features/recipes/_recipe_link_access.py` with `class RecipeLinkAccess(link_table_name, vocab_table_name, fk_column, noun, catalogue_hint)` exposing those nine methods; `recipe_tag_access.py` = `TAGS = RecipeLinkAccess("RecipeTag","DietaryTag","dietary_tag_id","dietary tag","See /api/recipes/tags…")` + thin module-level aliases preserving the current names (so 7 import sites don't change); `recipe_tool_access.py` keeps only `get_tool_ids_from_steps` + `sync_recipe_tools_from_steps` + aliases. Keep `get_tag_names_for_recipes` (tags-only). · M · test guard: `test_recipe_router.py` (tag/tool filters), `test_recipe_tools_derivation.py` · **execute**.
- **01-R7** · data-URL decoding × 5 · `get_recipes.py:1839–1861` and `:1870–1894` (inline, twice), `products/get_product_image.py:25`, `stores/manage_stores.py:327`, `users/get_user_image.py:30` (`_decode_data_url`) · the same regex + b64decode + `Response(mimetype, Cache-Control: no-cache)` five times. · **Exact change:** `dora_api/infrastructure/data_url.py` with `decode_data_url(blob: bytes|None) -> tuple[str, bytes] | None` and `data_url_response(blob, on_missing: Callable[[], Response]) -> Response`; replace the two recipe routes' bodies with `return data_url_response(recipe.image, lambda: not_found(...))` / same for step image; the other three features import the shared decoder (their chunks tick Applied when touched; do them here in one sweep since the change is mechanical). · S · test guard: `test_recipe_router.py` image tests, `test_product_router.py`, `test_store_router.py`, `test_user*` image tests (confirm names at execution) · **execute**.
- **01-R8** · `recipe_cost.py:147` `_key(v)` and `get_recipes.py:1562–1567` `_key(v)` · identical UUID/bytes/str → str normaliser. · **Exact change:** move to `dora_api/persistence/uuid_key.py` as `uuid_key(v) -> str`; import in both; delete both local defs. · S · guard: `test_recipe_line_cost.py`, `test_recipe_router.py` · **execute**.
- **01-R9** · `health_star_rating.py:198` and `nutri_score.py:222` `_points_for(value, table)` · identical table-threshold lookup; `nutri_score` also imports `kcal_to_kj` from the HSR module (FU-761). · **Exact change:** `dora_api/domain/rating_tables.py` with `points_for(value, table)` and `kcal_to_kj(kcal)`; both modules import from it; `nutri_score.py` drops its HSR import. · S · guard: `test_health_star_rating.py`, `test_nutri_score.py` · **execute** · tracked: FU-761 (closes).
- **01-R10** · `lookup.py:629` `_to_float` and `dataset_import.py:469` `_to_float` · identical. · **Exact change:** move to `nutrients.py` as `to_float(raw) -> float | None` (the module both already import), delete both locals; `nutrients.off_values` can then drop its injected `to_float` parameter (keep the param for one release if tests pass it — check `test_nutrition_lookup.py`). · S · guard: `test_nutrition_lookup.py`, `test_nutrition_dataset_import.py`, `test_off_lookup.py` · **execute**.
- **01-R11** · `lookup.py:556` `_portions_for` vs `household_measures.py:626` `portions_by_food` · same query, different shape (dicts vs rows). · **Exact change:** `_portions_for` becomes `{fid: [{"amount": p.amount, "measure": p.measure, "gram_weight": p.gram_weight} for p in rows] for fid, rows in portions_by_food(repository, food_ids).items()}`. · S · guard: `test_nutrition_lookup.py` · **execute**.
- **01-R12** · create/update response→HTTP mapping · `create_recipe.py:442–496` and `update_recipe.py:494–558` · the same nine-branch `if _Response.x: log; return y` chain. · **Exact change:** `dora_api/features/recipes/_recipe_errors.py` `def recipe_write_error_response(response, request, request_cls, logger) -> Response | None` covering `recipe_already_exists`, the three vocab not-found cases (guarded by `model_fields_set` membership, which is harmless on the create model), `missing_stock_item_ids`, `invalid_tag/step/section/choice/vocabulary_message`; both routes become `err = recipe_write_error_response(...); if err: return err`. · S/M · guard: `test_recipe_router.py` (422/400 cases) · **execute**.
- **01-R13** · `update_recipe.py:409–413` tool validation errors land in `invalid_tag_message` and log "Invalid recipe tag". · **Exact change:** add `invalid_tool_message` to both response dataclasses and both error chains (folded into 01-R12). · S · **execute**.
- **01-R14** · SPA option mappers · `RecipesOverview.vue:830–845`, `RecipeDetailPage.vue:1549–1554`, `RecipeEditDialog.vue:723–731` each map cuisines/categories/collections/dietary tags/tools to `{label, value}`. · **Exact change:** add getters to `recipeVocabStore.ts`: `cuisineOptions`, `categoryOptions`, `dietaryTagOptions` (with `category`), `toolOptions`; add `collectionOptions` to `recipeStore.ts`; the three consumers destructure them. · S · guard: vue-tsc; `recipeRailFilters.spec.ts` unaffected · **execute**.
- **01-R15** · `timeOfDayOptions` fallback · `RecipesOverview.vue:749–751`, `RecipeDetailPage.vue:1558–1559` · `mealSlotNames.length > 0 ? mealSlotNames : [...DEFAULT_MEAL_SLOTS]`. · **Exact change:** `mealSlotStore.ts` getter `slotNamesOrDefault`; both pages read it (also check `RecipeCookMode`/meal-plan consumers in Chunks 2/4). · S · **execute**.
- **01-R16** · `DIFFICULTY_OPTIONS = [...DIFFICULTY_VALUES]` · `RecipesOverview.vue:754`, `RecipeDetailPage.vue:1224` · **Exact change:** export `DIFFICULTY_OPTIONS` from `helpers/recipeVocabulary.ts`. · S · **execute**.
- **01-R17** · `newClientId()` × 4 · `useRecipeEditor.ts:88` (exported), `RecipesOverview.vue:1510`, `RecipeStepImagesEditor.vue:108`, `RecipeStructuredMethod.vue:401` · **Exact change:** delete the three local copies and import the exported one. · S · guard: vue-tsc, `recipeApiPaging.spec.ts` n/a · **execute**.
- **01-R18** · total time × 3 · `useRecipeDisplay.ts:67–72`, `RecipesOverview.vue:851–856`, `RecipeDetailPage.vue:1561–1565` (the page's variant treats 0+0 as null, the others treat null+null as null — a 0-minute recipe already reads differently). · **Exact change:** `helpers/recipeTime.ts` `totalMinutes(prep, cook): number | null` (null when both null; the page adopts this rule); all three call it. · S · guard: `recipeMetaLine.spec.ts` · **execute**.
- **01-R19** · favourite/cook/add-to-list action cluster · `RecipeCard.vue:148–184` and `RecipeRow.vue:438–475` · identical three buttons + rating chip + belief chip with the same props/emits. · **Exact change:** `components/recipes/RecipeActions.vue` (props: `recipe`, `labelledBelief`, `showFilterByIngredients`; emits the five events); both hosts render it. · S/M · guard: `recipeRowLayout.spec.ts`, `recipeRatingChip.spec.ts` · **execute**.
- **01-R20** · `getAllPagesAsync` · `recipeApiService.ts:481` and `stockItemApiService.ts:70` (comment admits the copy) · **Exact change:** `services/api/paging.ts` `fetchAllPages<T>(fetchPage: (page, limit) => Promise<Page<T>>, limit = 500): Promise<T[]>`; both services delegate. · S · guard: `recipeApiPaging.spec.ts` · **execute**.
- **01-R21** · Create-response shape hack · `recipeStore.ts:85–88` (`'recipe_id' in resource ? … : getAsync`), `RecipesOverview.vue:1470–1472`, `RecipeDetailPage.vue:2102–2103` (`(created as Record<string, unknown>).recipe_id ?? created.id`), same pattern in `stockItemStore.ts:103–106` · the server's `created()` always returns the full DTO body for recipes (`create_recipe.py:501`, `new_recipe_version.py:291`). · **Exact change:** type `createAsync`/`createNewVersionAsync` as `Promise<Recipe>`; `recipeStore.createRecipeAsync` pushes the result directly; delete the two page-level casts and use `created.recipe_id`. (Stock item store: Chunk 5/6.) · S · guard: vue-tsc, `test_recipe_router.py` already pins the 201 body · **execute**.
- **01-R22** · filter-state triple enumeration · `RecipesOverview.vue` `hasAnyFilter` (1218–1242), `activeFilterCount` (1247–1271), `clearFilters` (1365–1388) each list the same 22 fields; adding a filter means three edits (and `StockOverview.vue` has the same shape — Chunk 5). · **Exact change:** declare `const FILTERS: Array<{ ref: Ref<unknown>; isActive: () => boolean; reset: () => void }>` once (built from the `useListState` objects); derive `activeFilterCount = FILTERS.filter(f => f.isActive()).length`, `hasAnyFilter = activeFilterCount > 0 || searchText !== ''`, `clearFilters = () => FILTERS.forEach(f => f.reset())`. Consider promoting to `composables/useFilterRegistry.ts` shared with StockOverview at Chunk 5. · M · guard: `useListState.spec.ts`; add a vitest for the registry · **execute**.
- **01-R23** · `addToListRows.ts:640` `roundQuantity` · `formatQuantity` now rounds to 2 decimals itself (R-079, 2026-09-03). · **Exact change:** delete `roundQuantity`, pass `quantity` straight to `formatQuantity`. · S · guard: `addToListRows.spec.ts`, `formatQuantity.spec.ts` · **execute**.
- **01-R24** · `RecipeCostDialog.vue:738–741` recomputes per-serving as `total / servings` while the DTO carries server-owned `estimated_cost_per_serving` (R-003). · **Exact change:** replace the `servings` prop with `perServing: number | null`; `RecipeDetailPage.vue:1066` passes `recipe.estimated_cost_per_serving`. · S · **execute**.
- **01-R25** · `create_recipe.py:357–370` back-fills `section_id` with a Core `UPDATE` on rows the ORM just inserted, importing `db` locally. · **Exact change:** since `RecipeIngredient` maps `section_id` as a plain column (`update_recipe.py:350` sets it in the constructor), assign `ing_ent.section_id = real` on the pending entities instead and drop the Core update + local import. · S · guard: `test_recipe_router.py` section tests, `test_create_recipe_unit_of_work.py` · **execute**.
- **01-R26** · duplicate `nutrition_endpoints.py:31` imports `_require_admin` from `users/update_user_as_admin.py` while `auth/admin_gate.py:31` exports `require_admin` (8 callers vs 9 callers of the private one). · Cross-chunk — **Chunk 15** owns the admin-gate consolidation; recorded here because nutrition is one caller. · S · **execute (in Chunk 15's sweep)**.

### C3. Dead code / unused fields / unread endpoints

- **01-R27** · `web_app/src/composables/useRecipeExport.ts:79–101` `downloadCsv` · grep `downloadCsv|useRecipeExport` across `web_app/src`: only `RecipeDetailPage.vue:1196/1292` imports the composable and calls **only** `openPrintView` (L2092); the stock overview has its own `downloadCsv`. Owner feedback (RECIPE DETAIL): "Export to csv feels weird, remove feature here." · **Exact change:** delete `downloadCsv` + its `fetch`/`parseFilename`/`triggerSave` imports (client side — nothing calls it). The server route `GET /recipes/<id>/export` (`dora_api/features/data/export_recipe.py:117–137`, `_build_csv` L30) then has **no caller in the SPA**, but two tests pin it (`tests/e2e/dora_api/test_api_fuzz.py:204`, `test_data_router.py:764`), so removing it is a deliberate API cut, not a tidy — **FU** for the owner ("drop the recipe CSV export endpoint + its two test references, or keep it as an API-only export?"). · S · guard: vue-tsc · **execute (client)** / **FU (server route)**.
- **01-R28** · `RecipeDetailPage.vue` scoped CSS with zero template uses (grep'd within the file): `.rn__edit` (2325–2340), `.rn__link` (2412–2418), `.rn__hintblock` (2587), `.rn__editor` (2588), `.rn__secrow` (2656–2661), `.rn__order`, `.rn__ordername`, `.rn__ordersec` (2669–2686). Leftovers from the popup-edit era. · **Exact change:** delete those rules. · S · **execute**.
- **01-R29** · `RecipesOverview.vue:1708–1710` `.full-height` — no template use. · **Exact change:** delete. · S · **execute**.
- **01-R30** · `get_recipes.py:1799` `from dora_api.domain.entities.recipe import Recipe as _Recipe` inside `get_recipe` while `Recipe` is imported at L15. · **Exact change:** delete the local import; use `Recipe.__name__`. · S · **execute**.
- **01-R31** · `create_recipe.py:499` local `from …get_recipes import GetRecipesHandler` and `new_recipe_version.py:287–289` local import of `GetRecipesHandler, get_recipes` · `create_recipe.py` already imports `get_recipes` at L22, so there is no cycle to avoid. · **Exact change:** hoist both to module imports. · S · **execute**.
- **01-R32** · `RecipeCostDialog.vue:185` comment references a `costLineReason` on "the page" — nothing by that name exists (grep). · **Exact change:** reword to "the server ships reason ids; this map is the only copy of their wording". · S · **execute**.
- **01-R33** · `RecipesOverview.vue:883–886` comment "Tag (cuisine + category) options — we synthesise tags from the cuisine and category columns" sits above `collectionOptionsWithNone` and describes a design retired by L235. · **Exact change:** replace with "Collection filter options, plus the '(Uncategorised)' sentinel." · S · **execute**.
- **01-R34** · `recipe_cookability.is_cookable` (`domain/recipe_cookability.py:84`) · docstring says "new code should call `cookability_state`"; grep callers at execution (`grep -rn "is_cookable(" dora_api tests`) — if only tests call it, delete it and update those tests to `cookability_state(...) is True`. · S · **execute (conditional on grep)**.
- **01-R35** · `RecipeDto` fields `has_structured_steps` (L469) and `has_step_images` (L527) — list-only existence flags; detail sets them from the loaded lists. Check SPA readers: `grep -rn "has_structured_steps\|has_step_images" web_app/src`. If unread (the SPA reads `steps_mode`), drop the two hydrations `_hydrate_structured_steps_flag`/`_hydrate_has_step_images` (two bulk queries per list page) and the fields. · S · guard: `test_recipes_query_count.py` (count goes down — adjust the pin) · **execute (conditional on grep)**.

### C4. Componentisation opportunities (R-001)

- **01-R36** · `RecipeDetailPage.vue` is 2,727 lines (the doc-comment at L1118 says the *deleted* page was 2,727 lines — this one has grown to the same size). Extraction plan, each a self-contained block with its own state already localised: (a) `RecipeMasthead.vue` ← L25–216 + `.rn__masthead…rn__factv` styles (props: form, recipe, editing, options; emits dirty/toggle-edit/pick-photo); (b) `RecipeStatusStrip.vue` ← L304–391 (props: recipe, missing/atRisk/cost facts, batchEnabled; emits add-missing, adjust, open-cost); (c) `RecipeIngredientRail.vue` ← L395–683 + ingredient/section mutation functions L1913–2034 + styles `.rn__group…rn__add` (owns `ingredientsEditing`, emits dirty + save requests; the row editor moves with it); (d) `RecipeDetailsDrawers.vue` ← L856–1026 (additional details, nutrition, kcal, versions). The page keeps load/save/dirty/guards (~600 lines). · L · guard: none automated beyond vue-tsc; drive the page once after · **FU** (new follow-up: "Split RecipeDetailPage per 01-R36"; sequence after the S/M items land — the owner is happy with the page, so do it in one PR with a live walk).
- **01-R37** · `RecipesOverview.vue` filter panel (L105–399) is 300 lines of template; a `CookbookFilterPanel.vue` taking the registry from 01-R22 would make the page ~1,000 lines. · M · **FU** (bundle with 01-R36).
- **01-R38** · `RecipeNutritionCard.vue:45–156` the HSR and Nutri-Score blocks are the same template twice (row + working toggle + ledger + three notes); the author's comment argues for separation because copy differs. The *copy* can stay separate while the chrome is shared: `RatingWorking.vue` (props: badge slot, caption, ledger rows, notes[]) · S · **waive** — recorded; owner-happy surface and the duplication is bounded to one file.

### C5. Placement / layering (R-003, R-005)

- **01-R39** · `get_recipes.py` reaches `db.session.execute` with `db.metadata.tables["MealPlanEntry"]` (L1540–1558) and `select(Recipe.id, Recipe.image.is_not(None))` (L1320) — bypasses the repository port (R-005). Both are documented carve-outs (UUID binding on SQLite). · **Exact change (placement only):** move `_hydrate_unallocated`'s two aggregate statements into `dora_api/features/meal_plans/commitment_access.py` as `committed_servings_by_recipe(recipe_ids, today)` and `plan_counts_by_recipe(recipe_ids)` — meal-plan commitment math belongs to the meal-plans feature, and Chunk 2 (FU-908/879) wants the same numbers. · S · guard: `test_recipe_is_planned.py`, `test_recipe_router.py` · **execute**.
- **01-R40** · `RecipeDetailPage.vue:1742–1746` `isMissingItem` derives "missing" from the stock store's `is_out_of_stock` while every ingredient already carries the server's `is_missing`; the page uses the store version because substitutes (not on the DTO) need it. Two sources of the same verdict on one page. · **Exact change:** for ingredient rows read `ing.is_missing` from `recipe.value` (map by `recipe_ingredient_id`); keep the store lookup only inside `loadSubstitutes` for the substitute candidates. · S · **execute**.
- **01-R41** · `RecipesOverview.vue:723` `EXPIRING_FILTER_HORIZON_DAYS = 14` mirrors `get_recipes.EXPIRING_HORIZON_DAYS` (R-003 two languages) · tracked **FU-669**; the R-089 codegen (`web_app/src/generated/units_table.ts` from `scripts/dump_units.py`) is the established mechanism. · **FU-669** (verdict: execute there by making the server default the horizon when the param is `?expiring=1`).
- **01-R42** · `helpers/recipeVocabulary.ts:359` `DIFFICULTY_VALUES` mirrors `ALLOWED_DIFFICULTY_VALUES`; `scaleQuantity.ts:446` `COUNTABLE_UNITS` mirrors the server's count dimension / `SUB_ITEM_UNITS` (R-003/R-089). · **Exact change:** extend `scripts/dump_units.py` to emit `ALLOWED_DIFFICULTY_VALUES`, `ALLOWED_STEPS_MODES` and `SUB_ITEM_UNITS` into `generated/`; `recipeVocabulary.ts` re-exports; `scaleQuantity.isCountableUnit` reads the generated count-dimension + sub-item sets. · S/M · guard: `scaleQuantity.spec.ts`, `test_units.py` · **execute** (Chunk 20 owns the generator; do the recipe consumers here).
- **01-R43** · `import_recipe_from_content.py` fuzzy-matching with RapidFuzz over `all_names` per request while `nutrition/suggestions.py` has a hand-rolled token matcher and the assistant has its own fuzzy helpers — three matching strategies for "which pantry item is this?". · **C9** verdict below; no relocation.

### C6. Naming & idiom

- **01-R44** · `get_recipes.py` has **15** `import dataclasses` inside methods plus local imports of `money_features_enabled`, `estimate_costs_for`, `nutrition_mode`, `household_today`, `select`/`db` (R-008, R-019). None guards a cycle (`recipe_cost.py` and `recipe_rollup.py` don't import `get_recipes`). · **Exact change:** hoist to module imports; drop every in-method `import dataclasses`. · S · guard: pytest import; `test_recipe_router.py` · **execute**.
- **01-R45** · `get_recipes.py:143–149, 608` defensive `getattr(ingredient, "section_id", None)` etc. on attributes the entity always has (R-010/R-019); `recipe_cost.py:309/312/391/433` same `getattr(ingredient, "unit", None)` — there because the batch path once took entities; both callers now pass DTOs with the attributes. · **Exact change:** plain attribute access; keep `getattr` only in `recipe_cookability._required` (documented duck-typing for fixtures). · S · guard: `test_recipe_line_cost.py`, `test_recipe_item_price.py` · **execute**.
- **01-R46** · Pydantic request models: `Create*`/`Update*` Ingredient/Step/Section request classes are field-identical pairs (`create_recipe.py:52–125` vs `update_recipe.py:50–113`). · **Exact change:** define once in `recipe_requests.py` as `RecipeIngredientRequest`, `RecipeStepRequest`, `RecipeSectionRequest`; both handlers import; keep the two top-level `CreateRecipeRequest`/`UpdateRecipeRequest` (their optionality genuinely differs). · S · guard: `test_recipe_router.py`, `test_dto_contracts.py` (if it snapshots names — check) · **execute**.
- **01-R47** · `RecipeCard.vue:152` / `RecipeRow.vue:452` `:color="recipe.is_favourite ? 'red' : undefined"` — raw Quasar palette name where the page uses `text-negative` (R-002, D-020). · **Exact change:** `'negative'` (folds into 01-R19). · S · **execute**.
- **01-R48** · `recipeStore.getRecipesAsync` sorts with `Intl.Collator('en')` while the cookbook sorts again client-side; harmless but misleading (“store order”). · **waive**.
- **01-R49** · `suggestions.ignored_item_count` (`nutrition/suggestions.py:255`) uses `len(…all())` where the repository exposes `.count()` (used by `manage_categories.py:171`). · **Exact change:** `.count()`. · S · **execute**.

### C7. Efficiency

- **01-R50** · `RecipeDetailPage.vue` does `stockItems.value.find(...)` per ingredient row per render in `stockItemName`, `isMissingItem`, `atRiskHeadline`, `substitutableNames` (O(rows × pantry)). · **Exact change:** `stockItemStore` getter `byId: ComputedRef<Map<string, StockItem>>`; the page reads it. (Also useful to Chunks 2/3/5.) · S · **execute**.
- **01-R51** · `_hydrate_expiring_ingredients` (`get_recipes.py:1439`) runs `load_expiring_stock_item_ids` on **every** list page even when no filter asked; it is one cheap query and the chips depend on it — **waive** (by design, documented).
- **01-R52** · `load_recipe_cookability` loads the whole cookbook for `?cookable` — tracked **FU-908**.
- **01-R53** · `_restrict_query` loads `all_recipes` just to seed `allowed` ids (L956) — a `select(Recipe.id)` would avoid hydrating entities; at household scale negligible. · **waive**.

### C8. Design-level findings — out of Stage-2 scope

- **01-D1** · `is_favourite` is a recipe column, not per-user — in a two-account household one person's favourite is everyone's. Record for the multi-user readiness track (`MULTI_USER_READINESS.md`); no change.
- **01-D2** · Recipe name uniqueness is case-sensitive and application-level (FU-575) — tracked.
- **01-D3** · The stub-creator `RecipeEditDialog` still exists as an "Edit" path from the overview although the card has no edit button (feedback: "Edit button feels useless here") — `@updated` path is only reachable if some caller passes `recipe`; `RecipesOverview` only ever opens it with `editingRecipe = null`. The edit branch (`props.recipe` truthy) is therefore unreachable from the SPA: confirm at execution with `grep -rn "RecipeEditDialog" web_app/src` and, if the only host is the overview, simplify to a pure creator (drop `updated` emit + the update branch). · S · **execute (conditional on grep)**.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `_parse_recipe_from_text.py` (1,201 lines of regex heuristics) | paste-text recipe parser | `recipe-scrapers` (needs HTML + network, which FU-104/199 ruled out), `ingredient-parser-nlp` | **keep** | — | Operating on pasted plain text is the legal posture; corpus tests pin it. |
| `import_recipe_from_content.py` RapidFuzz `extractOne` | ingredient→pantry name match | already a library | **keep** | — | — |
| `nutrition/suggestions.py` token-recall scorer | item→food name match | RapidFuzz `token_set_ratio` | **keep** | — | Explainability (R-019) is the stated reason; threshold calibration documented. |
| `nutrition/lookup.py` `urlopen` + retry | OFF/USDA HTTP | `requests` (already a dependency: `requests_cache` in requirements) | **wrap-thin-adapter** | S | One `http_get_json(url, ua, timeout)` in `infrastructure/` shared with `dataset_import._download`; keeps retry policy in one place. **execute**. |
| `dataset_import.py` daemon thread + in-memory state | background import | APScheduler job / RQ | **keep** | — | Same shape as Piper voice download; a queue is anti-creep. |
| `pool.bump_pool` raw `text()` UPDATE … RETURNING | atomic floor-at-zero | ORM `update().returning()` | **keep** | — | Portability note documented; ORM form would need the same dialect split for bytes binding. |
| `recipeApiService.encodeFilterQueryString` | query-string build | `URLSearchParams` (used) vs `queryStringBuilder.createQueryString` | **wrap** | S | Fold the repeated-param encoding into `queryStringBuilder` so there is one encoder (Chunk 20 decides the shape). |
| `useDragDropList` in `RecipeStructuredMethod` | DnD | vuedraggable (`recipeStepImageEditorTypes.ts:13` comment still mentions it) | **keep** (R-022) | — | Fix the stale comment at execution. |

### C10. Standards drift (R-0NN)

- **R-008/R-019** · local imports in `get_recipes.py` (01-R44) — fix.
- **R-010/R-019** · defensive `getattr` on known attributes (01-R45) — fix.
- **R-039** · `RecipeDetailPage.vue:1504–1509` (`onDiscard`) and `:2121–2126` (`onDelete`) `$q.dialog` buttons lack `noCaps` (the route-leave dialog at 2225 has it). · **Exact change:** add `noCaps: true` to `ok` and a `cancel: { label: 'Cancel', flat: true, noCaps: true }`. · S · **execute** · tracked FU-623 (wrapper) stays open.
- **R-002** · `RecipeNutriScore.vue:13–19` hard-coded hex grade colours — these are the published Nutri-Score brand palette (an external standard, R-059). · **explain in place**: add `// R-002 carve-out: Nutri-Score's published grade colours (Santé publique France); not themeable by definition.` and declare them as `--nutri-a…--nutri-e` tokens in `tokens.scss` so R-060 lint sees them. · S · **execute**.
- **R-002** · `RecipeCard.vue:307` `rgba(255,255,255,0.92)` initial glyph over a hashed hue — **explain in place** (`/* R-002 carve-out: ink over a per-recipe hashed hue, no theme token applies */`). · **execute**.
- **R-002/D-020** · `ExpiringChip.vue` `grey-7`/`white` palette classes — tracked **FU-777**.
- **R-047** · `useRecipeExport.downloadCsv` raw `fetch` — removed by 01-R27 (FU-647 covers the stock-overview sibling).
- **R-003** · 01-R24, 01-R40, 01-R41, 01-R42 above.
- **R-035/D-rules** · `RecipeRow.vue` raw px chrome mirrors `StockItemRow` — tracked **FU-791/FU-693**.

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- `RecipeCard`/`RecipeRow` favourite uses palette `red` (→ `negative`).
- `RecipeNutriScore` fixed hex grades — fine as a standard, but no dark-theme contrast check has been done on the E/D letters over the pill.
- `RecipeRatingChip`/`RecipeHealthStars` partial state dims via opacity — FU-772 (rating pill tint, no dark pass).
- `RecipeStructuredMethod` timer pill uses `color-mix` on `--brand-primary` (12 %/35 %) — same class of low-alpha wash the owner found invisible on the cost share bars (09-08); check in pesto dark.
- `TriStateFilterChip` include/exclude use `info`/`warning` semantic colours for Planned/Not planned — a semantic colour carrying a non-semantic meaning (FU-224 shortlist).

## D. Test plan — Cookbook

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__recipe_write_error_response__maps_every_response_flag` | pytest (unit) | nice-to-have | Only if 01-R12 lands — pins the shared error chain once, instead of 2×9 route tests. |
| `test__vocabulary_crud_factory__categories_cuisines_tools_identical_contract` | pytest e2e (parametrised over the three routers) | **must-write-before-ship** (if 01-R5 lands) | A generic factory needs one contract test; the three existing router tests then become the parametrised cases. |
| `test__recipe_link_access__tags_and_tools_share_one_implementation` | pytest unit | nice-to-have | 01-R6 — pins validate/resolve/find for both link tables with one parametrised test. |
| `test__data_url_response__decodes_and_404s_on_garbage` | pytest unit | nice-to-have | 01-R7 — the five image routes today each rely on their own e2e test. |
| `ingredientDisplayName.spec.ts` | vitest | **must-write-before-ship** | 01-R1 — the label precedence is a contract three surfaces now share and it has already drifted once. |
| `useFilterRegistry.spec.ts` | vitest | nice-to-have | 01-R22 — count/clear/hasAny derive from one list. |
| `test__recipe_dto_cache__invalidated_by_flags` | pytest e2e | nice-to-have | **FU-901** (existing ask). |

Explicitly **not** proposed: Playwright flows for the recipe page (owner stance); component tests for the 2,700-line page (drive it once after 01-R36).

## E. Proposed follow-ups (orchestrator allocates ids)

- **urgent? no** · type=finding · *Guard dialog and recipe page name a labelled ingredient differently* (01-R1) — fix in Stage 2; no FU needed if executed this run.
- type=follow-up · *Split `RecipeDetailPage.vue` into masthead / status strip / ingredient rail / details drawers* (01-R36, plus 01-R37) — why deferred: large blast radius, owner is happy with the page, needs a live walk after. Recommended: after this run's S/M findings land, one PR.
- type=follow-up · *Vocabulary CRUD factory: extend to dietary tags, meal slots, stock groups* (01-R5 phase 2) — why deferred: those three carry extra fields/behaviour; do after the three identical ones prove the factory. Recommended: opportunistic.
- type=finding · *Per-user favourites* (01-D1) — recommended: when multi-user readiness is next picked up; link `MULTI_USER_READINESS.md`.
- type=finding · *`stockItemStore.createStockItemAsync` callers that re-find by name* (01-R2 pattern — grep other callers at execution) — recommended: now (Stage 2 of this chunk).

## F. Summary for the register

- FST rows: 13 golden + 11 edge + 4 gate · Help entries: 12 new (0 reworded; group rename "Recipes & meals" → "Cookbook"; DoraBot paragraph rewritten) · Review findings: 53 (execute 40 / FU 4 / waive 6 / conditional-execute 3) · Tests: 7 (must-write 2, both conditional on the refactors they pin) · Bugs: 2 latent (01-R1, 01-R2) + 1 stale-contract comment
- One-line: the cookbook's domain logic is cleanly server-owned and well-commented, but the surface has **no help at all**, the backend repeats one vocabulary manager four times and one link-table helper twice, and the SPA repeats small helpers (client ids, total time, option mappers, action clusters) across pages that the plan's north-star says should each exist once.
