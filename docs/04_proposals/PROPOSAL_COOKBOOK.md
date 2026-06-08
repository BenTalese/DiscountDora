# Proposal — Recipes / Cookbook Redesign (C-4)

**Status:** Draft for discussion · **Date drafted:** 2026-06-06 · **§2.6a Structured steps added 2026-06-08** (closes FU-040; pulled in from C-3 DEC-2) · Changes NO code.  
**Scope:** Redesign the recipe domain (post meals→recipes merge): naming, tags,
images, versions, multi-part recipes, tools, source, cost, nutrition, the card,
filters, and the detail page. **Recipe comparison is CUT per INV-6.** Heavy ripple
to meal plans (C-2), cook mode (C-3), shopping list, and budget.

> **Charter tie-break:** Effortless (P1) + Anti-creep (P10). The recipe domain is
> the loop's hub (pantry → recipes → meals → lists). New power must connect silos,
> not just add fields. Money & nutrition are **opt-in add-ons**, never core.

---

## 1. Current state (from live code)

Recipe entity (`recipe.py`) holds: name, cuisine, category, difficulty,
time_of_day, servings, prep/cook minutes, instructions, nutrition (freeform
string), `available_meals`, `last_made_on`, `is_favourite`, collection, and an
**`image: bytes` field that is never displayed or editable — a dead field**
(parallels `StockItem.image`). Tags are a curated 18-value catalogue
(`recipe_tags.py`) in a `RecipeTag` table, filtered by include/exclude on the
overview. `unallocated_meals` is derived server-side (available − future
un-cooked allocations). **No** cost, **no** versions, **no** multi-part/sections,
**no** tools. URL import (schema.org JSON-LD) exists and dumps the source URL into
the instructions text. Comparison mode (max 3 recipes) lives at
`RecipesOverview.vue:659-692` + the dialog `260-356`.

The feedback (L228-315) is large; the net of it: the domain *works* but is
cluttered, inconsistent with other pages, missing several designed-but-unbuilt
features (images, versions, tools, source, cost), and carries a comparison tool
the user wants gone.

---

## 2. The redesign

### 2.1 Naming — "Cookbook" (L230)
Page is "Cookbook" everywhere (A8 did the route rename + redirect; ensure the
title/labels and the stale "Recipes" command-palette label, **FU-031**, all
follow). "Mark made" → **"Mark cooked"** everywhere, componentised (L245, L303).

### 2.2 Tag system overhaul (L235-238, L255, L260, L283-284) — the big taxonomy fix
Three distinct concepts, currently muddled:

- **Dietary tags** → a **single filter** where clicking a tag cycles
  must-have (green +) → must-not (red −) → neutral (grey), multi-select style that
  **doesn't close the dropdown** (L237). Replaces today's separate include/exclude
  multiselects.
- **Cuisine** and **Category** → **single-select each, NOT lumped together, and
  NOT "tags"** (L235, L255). You're after Italian *or* Asian, not several.
- **All three taxonomies user-configurable in settings** — seed today's defaults,
  let the user add/edit/remove (L238, L283-284). This is **C-cross** (config
  surface); C-4 defines the vocabulary, C-cross builds the settings editor.

> **Open decision (brief):** cuisine-vs-category fate. The user asks "why are they
> separate — was it my original spec?" The original Recipes board only lists
> *cuisine* ("I can categorise recipes by their cuisine"); "category" appears to
> be later drift. **Recommend: keep both but as single-selects, OR collapse to
> cuisine + the configurable category-as-tag** — confirm (§5).

### 2.3 Recipe images (L249)
Display the image on the card and detail; allow upload. The `Recipe.image` column
already exists but is unused (dead) — wire it up (parallels `StockItem.image` /
FU-033; logged as **FU-039**). "People eat with their eyes." Missing-image →
a clean placeholder.

### 2.4 Versions (L247, L312) — replaces "Duplicate"
The original spec is explicit: *"a recipe can have revisions; you want to keep
older versions but not a separate recipe because it's basically the same thing."*
Replace the rarely-used **Duplicate** with **New version / Manage versions**: a
recipe owns an ordered set of versions (dated or numbered); one is "current";
older ones are viewable/restorable. Cook mode and meal plans reference the current
version unless told otherwise.

> **Open decision (brief):** versions UX — full snapshot per version (simple, more
> storage) vs diff/branch; whether meal-plan allocations pin to a version. Proposed:
> **full snapshot, current-pointer, allocations follow current** (simplest mental
> model). Confirm (§5).

### 2.5 Multi-part recipes (L294) — compare two approaches
The user floats two models for "Lasagne = béchamel + napoletana + mince":

| Approach | Pros | Cons |
|---|---|---|
| **A. Sections within one recipe** (named ingredient/step groups) | Simple; one card; no cross-recipe coupling; easy cook-mode grouping | Can't reuse a sub-recipe elsewhere; no independent "available meals" for the sauce |
| **B. Linked sub-recipes** (recipe references other recipes as components) | Reuse béchamel across recipes; each sub-recipe has its own stock/meals/cost | Complex: nested cookability, allocation, cost roll-up; harder UX |

**Recommendation: ship A (sections) first; design B as a later layer.** Sections
cover the dominant "this recipe has a sauce part and a meat part" need with far
less complexity (P10). Linked sub-recipes are powerful but ripple into
cookability/allocation/cost math everywhere — defer until there's demand.
**Open decision (§5):** confirm A-first, or commit to B.

### 2.6 Tools required (L310)
Optional **tools list** per recipe (food processor, 5L pot, …), from a
**configurable catalogue in settings** (like tags — C-cross). Inclusion/exclusion
**filter** on the overview. Cook mode highlights tools per step (C-3 consumes
this).

### 2.6a Structured recipe steps (added 2026-06-08; C-3 dependency, closes FU-040)

Today's `Recipe.instructions` is a freeform text blob split on newlines.
That's the root cause of cook mode's cross-step highlight bug (PROPOSAL_COOK_MODE
§2.4, L327): text-matching breaks when an ingredient appears in steps 1/2/3.
Cook mode's per-step **tools (§2.5)**, **per-step hints (§2.6)**, and **per-step
timers (§2.7)** also have nowhere to attach. C-3 resolved this by promoting
the model change here.

**Model:** `Recipe.steps` becomes an ordered list of structured steps:

```
RecipeStep
  id
  recipe_id
  sequence
  text              # the prose for this step
  sub_steps[]       # optional ordered list (RecipeStep again, one level deep)
  hint              # optional one-line tip rendered as a footer on this step
  ingredient_refs[] # FK→RecipeIngredient ids (which ingredients this step uses)
  tool_refs[]       # FK→RecipeTool ids (which tools this step needs)
```

The freeform `instructions` column stays for backwards compatibility and
**imports**: a recipe with no `steps[]` falls back to splitting `instructions`
on newlines, with text-matched ingredient highlighting — exactly today's
behaviour. **A recipe is "structured" once a user (or importer) populates
`steps[]`**; cook mode then renders the rich per-step behaviour.

**Editor:** in the recipe detail page (§2.13), instructions become a step
list. Each step has its text, an "add hint" affordance, ingredient/tool
multi-select pickers (from the recipe's own ingredient + tool lists), and a
"+ sub-step" affordance.

**Importer:** the URL importer (§2.7) emits structured steps when the source
exposes them in JSON-LD `recipeInstructions` (most schema.org recipe sources
do); otherwise it stores the joined text in `instructions` and leaves
`steps[]` empty.

**Migration:** new tables `RecipeStep` and join tables for the refs. No
data migration of existing recipes — they keep `instructions` and degrade
gracefully. Users opt in by editing.

**Sequencing impact:** in §6 below, **structured-steps lands as its own
chunk** (after detail cleanup §2.13, before C-3's highlight/per-step
features). Without it, C-3 chunks beyond the finish-flow are blocked.

### 2.7 Source field + importer guidance (L295, L296)
- **`source` becomes its own field** (URL or free text) — stop appending it to the
  instructions blob (today's import behaviour).
- The **URL importer names which sites are likely to work** (schema.org/Recipe
  JSON-LD sites) and degrades gracefully otherwise (L296). Offer import **from the
  overview too** (L269), not just detail.

### 2.8 Recipe cost estimate (L254) — opt-in, feeds budgets
Estimate cost from linked-product prices + historic shopping/receipt data;
**flows recipe → meal-plan → shopping-list budget** (the connected loop). **Gated
by the money opt-in (C-cross)** — entirely hidden for users who don't want to know
"how many dollars they're eating." Never affects the core flow.

> Confidence caveat: cost accuracy depends on ingredient quantity→product-size math
> (same hard problem as nutrition §2.9). Ship as a clearly-labelled *estimate*.

### 2.9 Nutrition tiers (L262, L263, L287) — opt-in, less free-form
Replace the freeform nutrition textarea with a **setting: off / simple / complex**:
- **off** — hidden entirely (default).
- **simple** — a single **kcal number** per recipe, typed in; sortable/comparable.
- **complex** — auto-derived from stock-items linked to a nutrition DB
  (configurable in settings). **Heavy; behind the opt-in; may be deferred** if the
  quantity→nutrition conversion proves unreliable — the user explicitly says
  "maybe just off + simple." **Recommend: build off + simple now; complex later.**
  (C-cross owns the nutrition-DB settings.)

### 2.10 Card redesign (L242-248, L274-277)
- **Image** (§2.3), **emphasised name**.
- **Meals box** (L274-275): an **editable in-stock count** (adjust available_meals
  from the card, like the stock overview) **and** an **allocated-meals box that
  only appears when there are allocations** — neutral if available ≥ allocated,
  **red if available < allocated**. Serves both meal-plan users and
  track-only users (who can ignore allocation entirely).
- **Actions on the card, ditch the ⋮** (L248): Cook (primary), and the few real
  actions; **Edit and Duplicate removed** (card click = open/edit; duplicate →
  "new version" in detail) (L243, L246). **Delete moves to detail** (L244).
- **Use the card space better** (L276, L277) — left side for image/meals, bottom
  for more than just "Cook".
- **Fix folder/collection grouping** — currently easy to miss; make the group
  header and count legible (L242).
- Section/grouping backgrounds in rounded boxes (L253).

### 2.11 Filters (L271, L278-279, L239-241) — and consistency
Add useful filters: **planned-in** (in a current/future meal plan, not past)
(L271), **order by last-made** (L279), **meal-count** / **in-stock-only** (L278).
**Stock-item filter → multi-select**, with rows **styled by stock level** (L239,
L240). Make filter shown/hidden/active/clear behaviour **identical to other pages**
(L232, L233) and fix the blank-input-wipes-results bug (L234 → **A4**). Move page
counts to the **sticky footer** (L231 → A7).

### 2.12 Recipe comparison → CUT (INV-6, L250-252)
Per `RECIPE_COMPARISON_ASSESSMENT.md` (INV-6): **remove** compare mode
(`RecipesOverview.vue:659-692` + dialog `260-356` + per-card checkbox). Every
question it tried to answer (time, servings, ingredient count, cookable-now) is
served better by the overview's **sort + filter** axes (§2.11). Fold the removal
into the same chunk that adds those axes, so users land on the overview and find
the answer comparison was meant to give. The theme/formatting complaints (L251,
L252) are moot once cut.

### 2.13 Detail page cleanup (L283-315)
- **Ingredient validation** (L290): block save (or auto-drop with a clear prompt)
  when a row has no stock item — don't silently eat the row.
- **Stock-item picker → filterable dropdown** (up to 100 items) (L285).
- **Editable title consistency** (L289): either give name its own field (like
  stock items) or clearly style the title as editable.
- **Nutrition placement** (L287) follows §2.9; **source** gets its field (§2.7);
  **tools** section (§2.6); **personal recipe notes** field shown in cook mode
  under the steps (L311) — distinct from per-ingredient notes (L293, which stay,
  shown in cook mode).
- **Buttons across the top**, consistent, not relocating to the bottom on mobile
  (L308); **export/print out of the ⋮**, remove ⋮ (L307); **remove CSV export
  here** (L306); **Mark cooked** bigger and not adjacent to Delete (L305); **Log
  cook** folded into the toolbar (L315); fix the not-allowed-cursor flash on
  meal +/- (L314).
- **"Meals on hand" → "available meals"** (L313).
- **Start cook mode**: confirm if not ready-to-cook (L309); block entry if save
  failed (L297); fix the detail→cook→exit→overview nav (L298); the unsaved-changes
  modal gets a Cancel and stops click-out-navigates (L299 → **A3** modal standard).
- **Substitutes:** the temporary cook-mode-only swap is **B8** (already fixed the
  destructive recipe edit, L302); remove the deleted substitutes-graph reference
  (L301 → B8). The "substitutes available as a separate status" idea (L300) is a
  **maybe** — logged as an open decision, lean *don't* (P10, overcomplicates).

---

## 3. Cross-cutting items (covered elsewhere — listed so nothing's lost)

| Feedback | Home |
|---|---|
| Can't-save-unless-name-changes (L286) | **B3** PATCH semantics |
| Modal click-out-to-cancel; unsaved/delete confirmations (L258, L268, L299, L304) | **A3** modal standard |
| Filter blank-input bug + consistency (L234) | **A4** filter system |
| Theme/contrast: comparison chips, cookable box, bright green (L251, L291) | **A1/A1b** |
| Cart button on ingredient rows (L288) | **C-7** |
| "Mark cooked" rename (L245, L303) | **A8** |
| Settings editors for tag/cuisine/category/tools/nutrition-DB taxonomies | **C-cross** (config) + the money/nutrition opt-ins |
| Dashboard "next up to cook" (L272) | Dashboard — deferred; noted |
| Allocation logic "not working" (L273) | **C-2 / B6** (confirm in browser) |

---

## 4. From the original spec (historical — `docs/00_original_spec/`)

| Original note | Verdict | Effect |
|---|---|---|
| *"Recipe revisions/versions (dated or numbered)… keep older versions but not a separate recipe"* | **keep (grounds §2.4)** | Confirms versions intent + rationale; this is the "my original feature notes" L312 cites. |
| *Comparison tool should show time/steps/cuisine/servings/#ingredients/in-stock* | **superseded by INV-6** | The comparison aspiration is exactly what the overview sort/filter now delivers (§2.11/§2.12). Don't revive the tool. |
| *Nutrition "either own object or flatten salt/sugar/fat — maybe?"* | **superseded** | The off/simple/complex tiers (§2.9) are the resolved direction. |
| *Card shows in-stock / low / out summary* | **keep (corroborates §2.10)** | |
| *Ingredients grouped by stock location (so you don't run back and forth)* | **keep → C-3** | Belongs in cook mode's location grouping; cross-ref C-3. |
| *Store recipes as markdown files, point to file in DB / custom location* | **superseded / out of scope** | A major storage-architecture divergence; current design is structured DB rows (needed for cost/nutrition/allocation). Not revisiting absent a strong reason — noted for the record. |

---

## 5. Open decisions (for co-design)

1. **Cuisine vs category fate** — keep both as single-selects, or collapse to
   cuisine + a configurable category? (§2.2)
2. **Versions UX** — full-snapshot + current-pointer + allocations-follow-current
   (proposed), or branch/diff + version-pinned allocations? (§2.4)
3. **Multi-part model** — sections-first (proposed), or commit to linked
   sub-recipes now? (§2.5)
4. **Nutrition scope** — off + simple now, complex later (proposed)? (§2.9)
5. **Cost estimate** — acceptable as a labelled estimate given the quantity→size
   math caveat? (§2.8)
6. **Substitute "status"** (L300) — add an "available substitutes" status, or skip
   as over-complication (proposed skip)? (§2.13)

---

## 6. Suggested sequencing

1. **Comparison cut + filter/sort axes** (§2.11, §2.12) — remove the tool and land
   the sort/filter it was standing in for. Self-contained, high value.
2. **Tag taxonomy overhaul** (§2.2) — the dietary toggle filter + cuisine/category
   single-selects; settings editor is C-cross.
3. **Card redesign** (§2.10) + naming/labels (§2.1).
4. **Detail cleanup** (§2.13) — validation, source field, button layout, log-cook,
   notes.
5. **Images** (§2.3, gated on FU-039) and **tools** (§2.6).
5a. **Structured recipe steps** (§2.6a, added 2026-06-08) — new tables + editor
    swap on the detail page. **Blocker for C-3 highlight/per-step features**;
    independent of versions and multi-part, so it can land in parallel.
6. **Versions** (§2.4) — its own model + UI.
7. **Cost** (§2.8) and **nutrition simple** (§2.9) — behind the money/nutrition
   opt-ins (C-cross).
8. **Multi-part sections** (§2.5) — last; biggest ripple.

---

## 7. Feedback coverage

Maps RECIPES OVERVIEW (L228-279) + RECIPE DETAIL (L281-315).

| Bullet | Summary | Where |
|---|---|---|
| L230 | Rename "Cookbook" | §2.1 (A8) |
| L231 | Page info → sticky footer | §2.11 (A7) |
| L232,233 | Filter offset / consistency | §2.11 (A4) |
| L234 | Filter blank-input bug | §3 → A4 |
| L235 | Cuisine/category not lumped, not tags | §2.2 |
| L236 | "recipe tags" vs "dietary tags" | §2.2 |
| L237 | One dietary filter, +/−/neutral cycle | §2.2 |
| L238 | Settings page for tags | §2.2 → C-cross |
| L239,240 | Stock-item filter multi-select + level-styled | §2.11 |
| L241 | Missing useful filters? | §2.11 |
| L242 | Folder grouping not obvious | §2.10 |
| L243 | Edit button useless on card | §2.10 |
| L244 | Delete → detail | §2.10 |
| L245 | "Mark made" → "Mark cooked" | §2.1 → A8 |
| L246,247 | Duplicate → detail / "new version" | §2.4, §2.10 |
| L248 | Few buttons → card, ditch ⋮ | §2.10 |
| L249 | Recipe image | §2.3 |
| L250 | Comparison useless → remove | §2.12 (INV-6) |
| L251,252 | Comparison theme/format | §2.12 (moot once cut) |
| L253 | Rounded-box section backgrounds | §2.10 |
| L254 | Recipe cost estimate (opt-in) | §2.8 → C-cross money |
| L255,260 | Cuisine/category single-select; why separate | §2.2 (+ open 1) |
| L256-268 | New-recipe modal (crammed, click-out, instructions hint, nutrition, tags, unit hint, ingredient layout) | §2.2/§2.9 + A3 (modal) |
| L269 | Import from overview | §2.7 |
| L270 | Create-button placement consistency | §2.10 |
| L271 | "planned in" filter | §2.11 |
| L272 | Dashboard "next up to cook" | §3 (dashboard deferred) |
| L273 | Allocation not working | §3 → C-2/B6 |
| L274,275 | Cooked-meals clutter; editable in-stock + allocated box | §2.10 |
| L276,277 | Use card space / bottom better | §2.10 |
| L278,279 | Meal-count / in-stock / last-made filters | §2.11 |
| L283,284 | Category/cuisine → configurable dropdowns | §2.2 → C-cross |
| L285 | Stock-item picker filterable dropdown | §2.13 |
| L286 | Can't save (name PATCH) | §3 → B3 |
| L287 | Nutrition placement | §2.9, §2.13 |
| L288 | Cart button componentise | §3 → C-7 |
| L289 | Editable title consistency | §2.13 |
| L290 | No empty-ingredient validation | §2.13 |
| L291 | Cookable box not theme-aware | §3 → A1 |
| L292 | Double out-of-stock/missing chip odd | §2.13 |
| L293 | Ingredient notes value | §2.13 (keep, shown in cook mode) |
| L294 | Multi-part recipes | §2.5 (+ open 3) |
| L295 | Source as its own field | §2.7 |
| L296 | Importer site guidance | §2.7 |
| L297 | No cook mode if save fails | §2.13 |
| L298 | Weird detail→cook→overview nav | §2.13 |
| L299 | Unsaved modal no cancel / click-out | §2.13 → A3 |
| L300 | Substitutes as a separate status | §2.13 (+ open 6) |
| L301,302 | Substitutes-graph ref / destructive swap | §3 → B8 |
| L303 | Mark made → cooked | §2.1 → A8 |
| L304 | Delete confirm click-out | §2.13 → A3 |
| L305 | Mark cooked bigger; delete spacing | §2.13 |
| L306,307 | Remove CSV here; export/print out of ⋮ | §2.13 |
| L308 | Buttons across top, not bottom on mobile | §2.13 |
| L309 | Confirm cook mode if not ready | §2.13 |
| L310 | Tools required (configurable) + filter | §2.6 |
| L311 | Personal recipe notes in cook mode | §2.13 |
| L312 | No way to create versions | §2.4 |
| L313 | "Meals on hand" → "available meals" | §2.13 |
| L314 | Not-allowed cursor flash on meal +/− | §2.13 |
| L315 | Log-cook button → toolbar | §2.13 |
