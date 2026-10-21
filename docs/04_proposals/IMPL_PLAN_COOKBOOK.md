# Implementation Plan — Cookbook / Recipes (C-impl)

**Status:** Plan for review · **Date:** 2026-06-08 · **No code yet** — phased
plan + first reviewable chunk.
**Source proposal:** `PROPOSAL_COOKBOOK.md` (2026-06-06; decisions resolved
§5a 2026-06-08).
**Adjacent IMPL plans:** `IMPL_PLAN_COOK_MODE.md` (C-3 consumes the
structured-steps + tools deliverables here); `IMPL_PLAN_SHOPPING_LISTS.md`
(P6-01 ripples — C-7 cart-button rows on ingredient lists feed into shopping
lists); `IMPL_PLAN_STATE_OWNERSHIP.md` (cookability source-of-truth lands
ahead).
**Phase:** Master plan **Phase 1 (the loop)** — the recipe domain is the
loop's hub (pantry → recipes → meals → lists). Sequenced *alongside* C-3
cook-mode work; **Chunk 6 (structured steps)** is a hard blocker for C-3
Chunk 5 (per-step highlight).

---

## 0. Verify-state-first: no drift

Re-checked 2026-06-08 against the live entities, table_mappings, and the
two big Vue pages. The code matches the proposal's diagnosis and has **not**
moved toward the solution:

- **`Recipe` entity** (`recipe.py`) holds: `available_meals, category,
  cook_time_minutes, cuisine, difficulty, image (bytes, **unused**),
  ingredients, instructions (freeform string), is_favourite, last_made_on,
  name, nutrition (freeform string), prep_time_minutes, recipe_collection,
  servings, time_of_day`. **No** `tools`, `source`, `cost`, `version_group_id`,
  or `sections` field. `image` exists but is never displayed or editable
  (FU-039).
- **`recipe_table`** (`table_mappings.py:297-315`) matches the entity.
- **`RecipeTag`** (`:323-327`) is a `(recipe_id, tag)` association from a
  curated 18-value catalogue in `domain/recipe_tags.py`. No `RecipeCuisine`
  / `RecipeCategory` table — those live as `String(255)` columns on
  `recipe_table` (`:301, :303`).
- **`RecipeCollection`** exists and backs today's "folder" grouping
  (`recipe_collection.py`). Keep.
- **Comparison mode** at `RecipesOverview.vue:659-692` + dialog
  `:260-356` + per-card checkbox — all to be ripped (§2.12).
- **Tags filter** today uses two separate `q-select` multiselects
  (include + exclude) on the overview filter bar — not the
  `+/−/neutral` cycle the proposal asks for.
- **URL importer** (`recipe_url_import.py` or similar in the recipes feature
  folder) appends `Source: <url>` to `instructions`. No `source` column to
  receive it; data ends up in the prose blob (§2.7).
- **Cook mode** still splits `instructions` by newline (cross-reference
  IMPL_PLAN_COOK_MODE §0).

So the work falls into roughly nine chunks, ordered by independence and
risk. The structured-steps chunk (§6 here / §2.6a in the proposal) is the
single dependency-gating one for C-3.

---

## 1. Chunked plan (each chunk = one reviewable PR)

### Chunk 1 — Comparison cut + filter/sort axes ★ FIRST REVIEWABLE CHUNK
**Closes:** §2.11 + §2.12 + L239 / L240 / L241 / L250–252 / L271 / L278 /
L279.

Self-contained, high value, no model changes — the lowest-risk way to
visibly improve the cookbook for users.

- **Rip comparison mode entirely** (per INV-6): `RecipesOverview.vue` lines
  ~`260-356` (the comparison dialog), `659-692` (the trigger + state), the
  per-card checkbox, and any `compareSelection` ref / handlers. Includes
  template, script, and styles. Don't leave a "Compare" menu item behind.
- **Replace it with sort + filter axes** the comparison was standing in
  for:
  - **Order by:** name (default) · last-made · meal-count (available_meals)
    · prep+cook time · created-at.
  - **Stock-item filter → multi-select**, with each row styled by current
    stock-level chip (level-colour token from A1).
  - New filters: **planned-in** (recipe appears in a meal plan whose date
    is ≥ today), **in-stock-only** (available_meals > 0), **meal-count
    range**.
  - Page-count display moves to the **sticky footer** (A7 dep — if A7
    hasn't landed, ship a placeholder div and log a follow-up).
- **Filter-bar consistency** with the rest of the app — adopt A4 once it
  lands; otherwise match the closest A4-compliant page (StockOverview).
- Fix the blank-input-wipes-results bug (L234) at the same time — its root
  cause lives in the shared filter bar (A4).

**Risk:** the comparison teardown touches ~150 lines of template and ~100
lines of script. Read-before-deleting; some sort/filter wiring may share
state. Tests: e2e for the new filters; existing recipe-list e2e still
passes.

*Acceptance:* no "Compare" affordance anywhere; the new filters + sort
axes work; page counts in the footer; blank-input bug gone for the recipes
overview.

### Chunk 2 — Tag taxonomy overhaul
**Closes:** §2.2 + L235 / L236 / L237 / L255 / L260 / L283 / L284.

- **Backend:**
  - `Recipe.cuisine` and `Recipe.category` stay as single-string columns on
    `recipe_table` (no schema change). DEC-1: both kept, both single-select.
  - New **`Cuisine`** and **`Category`** tables (`{id, name, sequence}`) so
    the vocabularies become user-configurable instead of free-form strings.
    Seed with today's curated values. `Recipe.cuisine` / `Recipe.category`
    become FK fields (`UUIDType, ForeignKey(..., ondelete=SET NULL),
    nullable=True`). Migration converts existing string values to FK rows.
  - Dietary tags stay in the existing `RecipeTag` association (no schema
    change there), but the catalogue moves from `domain/recipe_tags.py` to
    a new **`DietaryTag`** table (`{id, name, sequence}`); the association
    column type changes from `String(64)` to `UUIDType` FK. Migration
    creates the table, seeds it from `recipe_tags.py`, and rewrites the
    association.
  - DTOs expose `cuisine_id` / `category_id` / `dietary_tag_ids[]`.
- **Frontend:**
  - **Dietary filter**: one `q-select` (or `q-btn-dropdown`) where each
    option cycles **must-have (green +)** → **must-not (red −)** →
    **neutral (grey)** on click. **Dropdown does not close** on click — only
    on outside-click / Esc (L237). Replaces today's two include/exclude
    selects.
  - **Cuisine / Category filters** become single-select dropdowns sourced
    from the new tables.
  - Recipe edit form: cuisine + category single-select; tags multi-select.
- **C-cross dependency**: the *settings editor* for the three vocabularies
  lives in C-cross (config surface). C-4 ships the *data* with admin-only
  read-only views if C-cross isn't ready; settings editor follows.

**Risk:** the tri-state filter (`+/−/neutral`) is a custom Quasar control
— land it as a small component (R-001) reused for future +/− filters.
Migration must be idempotent (re-runs okay).

*Acceptance:* dietary filter cycles +/−/neutral; cuisine/category are
single-select; the three vocabularies are tables (visible in the DB);
existing recipes preserve their values.

### Chunk 3 — Card redesign + naming
**Closes:** §2.1 + §2.10 + L230 / L242–248 / L253 / L270 / L274–277.

- **Naming sweep** — `RecipesOverview` title + breadcrumbs + sidebar item
  all read "Cookbook". "Mark made" → "Mark cooked" everywhere in the
  surface (A8 may already cover the route rename; this chunk catches stale
  labels — ~~command-palette label~~ (palette retired 2026-06-12);
  remaining FU-031 concerns are tour cards, help text, and any
  other static "Recipes" mentions in SPA copy).
- **Card body redesign:**
  - **Image** (gated on FU-039 — Chunk 5 wires it; for now, render the
    placeholder unconditionally so the layout is right).
  - Emphasised name at the top.
  - **Meals box**: editable `available_meals` count (steppable like the
    stock-overview level chip), plus an **allocated-meals box** that only
    renders when allocations exist. Neutral if `available >= allocated`,
    **red** if `available < allocated`. Reads off existing server-derived
    `unallocated_meals`.
  - **Cook** is the only primary action on the card. **Edit and Duplicate
    removed** — card click opens the detail page (which is also the edit
    surface). **Delete moves to detail** (§2.13 / Chunk 4).
  - **Folder/collection grouping**: prominent header + count
    (`RecipeCollection.name (N)`), rounded box background, collapsible.
- **Section background tokens** (rounded boxes) — uses the A1 surface
  tokens; no new colour decisions.

**Risk:** the meal-stepper on the card duplicates a pattern from
stock-overview — extract to a `dora-meal-stepper` mini-component (R-001 if
it ends up used in 2+ places). Don't write three copies.

*Acceptance:* card layout matches the mockup spirit; only Cook is on the
card; collection groups read clearly; "Cookbook"/"Mark cooked" naming
consistent.

### Chunk 4 — Detail page cleanup
**Closes:** §2.13 + L283 / L285 / L286 / L289 / L290 / L292 / L297 /
L298 / L299 / L304 / L305 / L306 / L307 / L308 / L309 / L313 / L314 /
L315.

This is the big "detail page is a mess" cleanup. Order the work top-to-
bottom inside the chunk; it's all on `RecipeDetailPage.vue`.

- **Ingredient validation** — block save when a row has no `stock_item_id`
  (or auto-drop with an explicit confirm). No silent eaten rows.
- **Stock-item picker → filterable dropdown** (up to ~100 visible at once
  — the stock catalogue isn't huge; Quasar `q-select` with
  `use-input`/`hide-selected`/`fill-input` is fine).
- **Editable title consistency** — match the stock-item pattern (own
  `q-input` field, no pretending the H1 is editable). Or vice versa —
  pick one and apply.
- **Buttons across the top, never the bottom on mobile** — sticky header
  with: **Mark cooked** (large), **Log cook** (folded in), **Cook mode**,
  Export, ⋮ (only for Print / CSV-export / Delete-list — and CSV-export
  here is removed per L306).
- **Mark cooked**: visually larger and **not adjacent to Delete** (L305).
- **"Meals on hand" → "available meals"** (L313).
- **Not-allowed cursor flash** on meal +/− (L314): pre-flight the disabled
  state with a `:disable` rather than catching the click error.
- **Cook mode entry**: confirm if `unsaved` is true (L297); block entry
  when the most recent save errored; fix the detail→cook→exit→overview
  navigation so exit returns to **detail**, not all the way back to
  overview (L298). The unsaved-changes modal gets a real Cancel button and
  clicks-outside no longer navigate (L299, A3 dep).
- **Double "out of stock / missing" chip** (L292): pick one chip per
  ingredient row — "missing" wins over "out of stock" because missing is
  the actionable state.

**Risk:** the detail page is the single biggest Vue file in the recipes
surface; touch it in one chunk and the diff stays auditable. Don't
interleave with §2.13 leftovers in other chunks.

*Acceptance:* every L283-L315 line either lands here or is explicitly
deferred (in §3 of this plan).

### Chunk 5 — Images + tools
**Closes:** §2.3 + §2.6 + L249 / L310 + **closes FU-039**.

- **Images** (FU-039):
  - Wire `Recipe.image` (already a `LargeBinary` column) end-to-end.
  - Upload affordance on the detail page (same shape as `StockItem.image`
    if FU-033 has landed; otherwise pioneer it here and FU-033 follows).
  - Render on the card (Chunk 3 left a placeholder).
  - Missing-image placeholder: simple coloured tile with the recipe name
    initial.
- **Tools:**
  - New **`Tool`** table (`{id, name, sequence}`) — same shape as the new
    Dietary/Cuisine/Category tables.
  - New `RecipeTool` association `(recipe_id, tool_id)`.
  - Recipe edit form: multi-select tools.
  - Overview filter: include/exclude tools (same `+/−/neutral` cycle as
    dietary tags from Chunk 2 — re-use the component).
  - Cook mode reads `recipe.tools[]` for the per-step highlight in C-3
    Chunk 5. (No cook-mode work in this chunk — that's gated on Chunk 6
    structured steps.)

**Risk:** image uploads need a sensible size cap; reuse whatever
`StockItem.image` ends up using (FU-033 should set the precedent).
Logged as a finding if the size-cap pattern is missing.

*Acceptance:* recipes have images on card + detail; tools section
renders + filters work; the new Tool table is editable through C-cross
(when it lands).

### Chunk 6 — Structured recipe steps (★ blocker for C-3 Chunk 5)
**Closes:** §2.6a + `PROPOSAL_COOK_MODE.md §2.4 / §2.5 / §2.6 / §2.7`.

This is the C-4 chunk that gates C-3's per-step highlight + per-step
tools/hints/timers (`IMPL_PLAN_COOK_MODE.md` Chunk 5 sits behind this).
Treat as its own PR; do not bundle with anything else — the migration +
editor surface is already substantial.

- **Backend:**
  - **`RecipeStep`** entity & table:
    ```
    RecipeStep
      id              UUID, PK
      recipe_id       UUID, FK→Recipe.id, NOT NULL, ON DELETE CASCADE
      parent_step_id  UUID, FK→RecipeStep.id, ON DELETE CASCADE, NULL
      sequence        INT, NOT NULL
      text            TEXT, NOT NULL
      hint            TEXT, NULL
    ```
    Self-referential FK gives **one level** of sub-steps (children of a top
    step have its id as `parent_step_id`; sub-steps of a sub-step are
    rejected at the entity level — keep the validator simple).
  - **`RecipeStepIngredient`** association
    `(step_id, recipe_ingredient_id)`.
  - **`RecipeStepTool`** association `(step_id, recipe_tool_id)` — depends
    on the Tool table from Chunk 5.
  - `Recipe.instructions` **stays** as a `String, nullable=True` column.
    A recipe with empty `steps[]` is "unstructured" and falls back to
    today's newline-splitting / text-matched-highlighting path everywhere.
  - DTOs: recipe detail exposes `steps[]` ordered by `(parent_step_id NULLS
    FIRST, sequence)`. Summary keeps a `has_structured_steps: bool` for
    cheap UI decisions.
  - Create + update endpoints accept `steps[]` as a nested write (replace
    semantics: full-list replaces the current set, simpler than diff
    semantics and matches how `ingredients` is already handled).
  - The **URL importer** maps `schema.org/Recipe recipeInstructions` to
    `steps[]` when the source provides structured entries; otherwise
    joins them into `instructions` and leaves `steps[]` empty. JSON-LD
    `HowToStep` items become individual steps; `HowToSection` items become
    a parent step containing the section's children as sub-steps.
- **Frontend (recipe detail editor):**
  - Step list replaces today's instructions `<q-input type="textarea">`.
  - Each step row: text field, *add hint* affordance (toggles a small
    `q-input` for `hint`), ingredient multi-select (from the recipe's own
    `ingredients[]`), tool multi-select (from `tools[]`), *+ sub-step*
    button (disabled on rows already at depth 1).
  - Drag-handle reorder within siblings (re-use the DnD off-by-one-fixed
    pattern from `IMPL_PLAN_SHOPPING_LISTS.md` Chunk 6).
  - **Advanced ▾ Freeform fallback**: still expose a textarea bound to the
    original `instructions` field for users with imported recipes who want
    to mass-edit. Saving via the step list writes `steps[]`; the textarea
    writes `instructions` and clears `steps[]` (the user is explicitly
    opting back to unstructured).
- **No data migration** of existing recipes — they keep `instructions`
  and the cook-mode fallback path handles them. Users opt in by editing.

**Risk:** the editor UX is the bulk of the work. Wire the data round-trip
first; iterate on the form. Tests: round-trip a structured recipe;
round-trip an unstructured one; toggle to freeform and back.

*Acceptance:* structured-step recipes round-trip cleanly; unstructured
recipes work everywhere unchanged; migration applies cleanly on SQLite +
Postgres; the freeform fallback exists.

### Chunk 7 — Source field + URL importer cleanup
**Closes:** §2.7 + L269 / L295 / L296.

Independent of every other chunk except Chunk 6 (importer also writes
`steps[]`).

- **Backend:**
  - New `Recipe.source` column (`String(2048), nullable=True`). The URL
    importer writes here instead of appending to `instructions`.
  - Migration; data migration is *not* attempted (the existing
    `instructions` text might mention a source URL but parsing it back
    out reliably is impractical — leave historical recipes as-is, users
    can clean up on edit).
- **Frontend:**
  - Recipe detail: `source` field (URL input with a small "Open" affordance
    when filled).
  - URL importer dialog:
    - **Named-site hints** — a one-paragraph blurb listing site categories
      that work (recipe sites with schema.org JSON-LD recipe markup) and
      a fallback note for unknown sites. Probably 3–5 example domains to
      anchor user expectations.
    - Reachable **from the overview's New-Recipe surface** as well, not
      only from the detail page (L269).
    - Graceful degradation on JSON-LD-less sites: take what we can scrape
      (title, image-meta-tag) and dump the page text into `instructions`
      with a banner saying "couldn't auto-structure; review and edit".

**Risk:** the importer changes ripple to Chunk 6 (structured steps from
JSON-LD). Co-sequence: land Chunk 6 first, then Chunk 7 to wire the
importer's structured output through.

*Acceptance:* `source` shows on detail; importer writes there; importer
is reachable from the overview; structured imports emit `steps[]` when
the source has it.

### Chunk 8 — Versions (per DEC-2: siblings via version_group_id)
**Closes:** §2.4 + L247 / L312.

**Note:** DEC-2 reshaped this chunk vs the brief. The model is flatter
than the brief implied — no current pointer, no snapshot vs current
distinction.

- **Backend:**
  - New nullable `Recipe.version_group_id: UUIDType` column. Recipes with
    the same `version_group_id` are versions of each other (siblings).
    Recipes with `NULL` are singletons.
  - **"New version" action** (`POST /recipes/<id>/new-version`):
    - If the source recipe's `version_group_id` is `NULL`, assign a new
      UUID to both source and the new copy.
    - Otherwise reuse the source's `version_group_id` for the copy.
    - Returns the new recipe id.
  - Detail DTO exposes `version_siblings[]` (the other recipes with the
    same group id — id, name, last_made_on, available_meals — light
    payload; clicking a sibling navigates to its detail).
  - **Delete behaviour**: existing single-recipe delete works unchanged.
    If deleting leaves a group with zero or one entry, no special handling
    is required (the group is implicit — a lone recipe with a group id is
    fine; it'll absorb future siblings).
  - **Allocations stay per-recipe** — no special version-aware
    allocation logic (per user's framing: "they're all equal, allocations
    are the same for all versions" — read as "user picks a version when
    allocating; the link is discovery only").
- **Frontend:**
  - Replace the **Duplicate** action with **New version** on the detail
    page kebab.
  - New **Versions** card / section on the detail page showing
    `version_siblings[]` with their names + last_made_on. Click → navigate.
  - "New version" copies the source recipe (ingredients, tools, steps,
    cuisine/category/tags, source, image) and routes the user into edit
    mode on the copy with the name pre-filled `<source.name> (v2)` (or
    similar — count siblings + 1).

**Risk:** the meal-plan view + the cookable view will see "Fried Rice"
× N when N > 1 versions exist. That's by design per DEC-2 (the user picks
when allocating). No special UI affordance to "pick a version" — they're
listed in the standard recipe picker like any other recipe.

*Acceptance:* New Version button copies; siblings render on detail;
deleting one leaves the others intact; allocations work per-recipe with
no special handling.

### Chunk 9 — Cost estimate + simple nutrition (opt-in)
**Closes:** §2.8 + §2.9 + L254 / L262 / L263 / L287 + DEC-4 + DEC-5.

Both features are gated by C-cross opt-ins; this chunk lands the recipe-
side wiring + the math.

- **Nutrition (DEC-4):**
  - New `Recipe.kcal: Integer, nullable=True` column. Simple, typed by
    the user.
  - Detail page: input field next to servings/prep/cook time when the
    nutrition opt-in is `simple`; hidden when `off` (default).
  - Sort/filter axes (Chunk 1) gain a "kcal range" option when nutrition
    is enabled.
  - The freeform `nutrition: str | None` column on `recipe_table` is left
    in place for backwards compatibility but no longer rendered or edited
    (logged as a follow-up to drop once we're sure no user has typed
    something irreplaceable in there).
- **Cost estimate (DEC-5):**
  - Server-side computation: for each `RecipeIngredient` with a
    `stock_item_id`, find the linked `Product` (if any) and its most-recent
    `Offer.price_now`. Sum `quantity * price_per_unit` across the recipe.
    Quantity-to-product-size math uses the same rough heuristic as the
    cost-of-pantry views (if any) — pass through ingredient units as-is
    when they match the product unit; otherwise estimate from the linked
    product's pack size.
  - Expose as `Recipe.estimated_cost: float | None` on the detail DTO
    (server-computed, not stored — keep it derived so price drift is
    automatic).
  - Detail page renders the estimate with a **clear "estimate" label**;
    hover/tooltip describes the math.
  - **Money opt-in (C-cross)** gates the render; never affects the core
    flow when off.

**Risk:** the cost math has well-known accuracy limits (the
quantity→product-size ratio). Ship as "estimate" — never as truth. Tests
cover the happy path + a recipe with no linked products (renders `null`
gracefully).

*Acceptance:* simple nutrition + cost estimate both ship behind their
opt-ins; users with both off see no new fields anywhere.

### Chunk 10 — Multi-part sections (last chunk; biggest ripple)
**Closes:** §2.5 + L294 + DEC-3.

Section-based multi-part per DEC-3 (option A). Sub-recipes (option B) are
explicitly deferred — log a fresh follow-up when the section feature has
real-world signal that reuse matters.

- **Backend:**
  - **`RecipeSection`** entity & table: `{id, recipe_id, sequence, name}`.
  - `RecipeIngredient` gains an optional `section_id: UUIDType, FK→
    RecipeSection.id, ON DELETE SET NULL, nullable=True`. Unsectioned
    ingredients (section_id NULL) are the "main" group.
  - `RecipeStep` similarly gains `section_id: UUIDType, FK→
    RecipeSection.id, nullable=True`. Unsectioned steps are "main".
  - Migration: existing recipes have one implicit "main" section with all
    ingredients/steps in it; no data migration needed (NULL section_id
    works as the default).
  - DTOs: recipe detail exposes `sections[]` ordered by sequence; each
    section carries its own ingredient + step lists for client
    convenience.
- **Frontend:**
  - Recipe edit form: an "Add section" button creates a named group;
    ingredients and steps move between sections via drag or a section
    picker per row.
  - Cook mode: sections render as named headers in the ingredient panel
    and the step list (C-3 Chunk 3's grouping by location now coexists
    with sections; sections win as the top-level grouping when present).
  - Card / detail summary: section count badge when > 1.

**Risk:** ripples into cookability math (today's "all ingredients
available?" check is flat; sections don't change the answer but the UI
that displays the per-section breakdown is new). Tests: a recipe with no
sections renders unchanged; a recipe with two sections renders both
headers in cook mode; cookability still works.

*Acceptance:* a recipe can have N named sections; ingredients and steps
attach to sections; cook mode renders the section structure.

---

## 2. First reviewable chunk — definition of done

**Chunk 1 (comparison cut + filter/sort axes).**

- Every line of the comparison feature is gone: dialog, trigger, per-card
  checkbox, state, styles. `grep -r 'compar' web_app/src/pages/Recipes*`
  should return nothing meaningful.
- New filters land: planned-in, in-stock-only, meal-count range,
  stock-item multi-select (level-styled rows).
- New sort axes land: name, last-made, meal-count, prep+cook time,
  created-at. Default is name.
- Page-count display in the sticky footer (A7 dep — placeholder if not
  yet available; log a follow-up).
- Blank-input filter bug is gone for the recipes overview (or A4 lands
  the fix system-wide and this chunk consumes it).
- Tests: e2e covering each new filter; existing tests pass.
- Engineering close-gate (`ENGINEERING_STANDARDS.md`): R-001
  (componentise the multi-select level-styled list if it'll be reused),
  R-007 (no scope creep), R-008 (terse).

---

## 3. Risks & open decisions

**Risks:**

- **Chunk 4 (detail cleanup) is large and many-faceted.** Resist the
  temptation to bundle Chunk 5 (images + tools) into it — the diff
  becomes unreviewable. Land Chunk 4 as detail-only first.
- **Chunk 6 (structured steps) is the longest single change** and the
  only one gating another C-impl plan. Sequence it ahead of C-3 Chunk 5.
- **Chunk 2's catalogue tables** ripple into C-cross. If C-cross isn't
  ready, ship the data + read-only admin views and let C-cross's settings
  editor follow.
- **Chunk 9's cost math** is inherently fuzzy. Communicate this in copy
  (the "estimate" badge); reuse whatever ratio heuristic
  `IMPL_PLAN_STATE_OWNERSHIP.md` ships for pantry-cost views, if any.
- **Chunk 10's section model** changes the shape of three nested
  collections (ingredients, steps, sections); fan-out carefully.

**Open decisions:** none — all 6 closed in `PROPOSAL_COOKBOOK.md §5a`
(2026-06-08). DEC-2 deviated meaningfully from the brief's
"snapshot+pointer" recommendation; the resolved model (siblings via
`version_group_id`) is reflected in Chunk 8.

**Cross-refs:**
- `IMPL_PLAN_COOK_MODE.md` — Chunk 6 here is the blocker for cook-mode
  Chunk 5.
- `IMPL_PLAN_SHOPPING_LISTS.md` — already landed; the ingredient cart-
  button rows on the detail page (L288) consume C-7.
- `IMPL_PLAN_STATE_OWNERSHIP.md` — cookability source-of-truth lands
  ahead; Chunk 3's red-when-overallocated chip reads off the
  server-derived value.
- A1 theme tokens · A3 modal standard · A4 filter system · A7 sticky
  footer · A8 renames · B3 PATCH semantics · B8 substitute swaps · C-7
  cart button · C-cross config surface (vocabularies + opt-ins).

---

## 4. Feedback coverage

Maps RECIPES OVERVIEW (L228-L279) + RECIPE DETAIL (L281-L315).

| Bullet | Summary | Where |
|---|---|---|
| L230 | Rename "Cookbook" | Chunk 3 (A8) |
| L231 | Page info → sticky footer | Chunk 1 (A7) |
| L232,233 | Filter offset / consistency | Chunk 1 (A4) |
| L234 | Filter blank-input bug | Chunk 1 (A4) |
| L235 | Cuisine/category not lumped, not tags | Chunk 2 (DEC-1) |
| L236 | "recipe tags" vs "dietary tags" | Chunk 2 |
| L237 | Dietary filter +/−/neutral cycle | Chunk 2 |
| L238 | Settings page for tags | Chunk 2 → C-cross |
| L239,240 | Stock-item filter multi-select + level-styled | Chunk 1 |
| L241 | Missing useful filters? | Chunk 1 |
| L242 | Folder grouping not obvious | Chunk 3 |
| L243 | Edit button useless on card | Chunk 3 |
| L244 | Delete → detail | Chunk 3 + Chunk 4 |
| L245 | "Mark made" → "Mark cooked" | Chunk 3 (A8) |
| L246,247 | Duplicate → detail / "new version" | Chunk 8 (DEC-2) |
| L248 | Few buttons → card, ditch ⋮ | Chunk 3 |
| L249 | Recipe image | Chunk 5 (FU-039) |
| L250 | Comparison useless → remove | Chunk 1 (INV-6) |
| L251,252 | Comparison theme/format | Chunk 1 (moot) |
| L253 | Rounded-box section backgrounds | Chunk 3 |
| L254 | Recipe cost estimate (opt-in) | Chunk 9 (DEC-5, C-cross money) |
| L255,260 | Cuisine/category single-select; why separate | Chunk 2 (DEC-1) |
| L256-268 | New-recipe modal cleanup | Chunk 2 + Chunk 4 + A3 |
| L269 | Import from overview | Chunk 7 |
| L270 | Create-button placement consistency | Chunk 3 |
| L271 | "planned in" filter | Chunk 1 |
| L272 | Dashboard "next up to cook" | Deferred (dashboard rework) |
| L273 | Allocation not working | C-2 / B6 (confirm in browser) |
| L274,275 | Cooked-meals clutter; editable in-stock + allocated box | Chunk 3 |
| L276,277 | Use card space / bottom better | Chunk 3 |
| L278,279 | Meal-count / in-stock / last-made filters | Chunk 1 |
| L283,284 | Category/cuisine → configurable dropdowns | Chunk 2 → C-cross |
| L285 | Stock-item picker filterable dropdown | Chunk 4 |
| L286 | Can't save (name PATCH) | B3 (already scoped) |
| L287 | Nutrition placement | Chunk 9 |
| L288 | Cart button componentise | C-7 |
| L289 | Editable title consistency | Chunk 4 |
| L290 | No empty-ingredient validation | Chunk 4 |
| L291 | Cookable box not theme-aware | A1 |
| L292 | Double out-of-stock/missing chip | Chunk 4 |
| L293 | Ingredient notes (kept, shown in cook mode) | Chunk 4 + cook mode |
| L294 | Multi-part recipes | Chunk 10 (DEC-3) |
| L295 | Source as its own field | Chunk 7 |
| L296 | Importer site guidance | Chunk 7 |
| L297 | No cook mode if save fails | Chunk 4 |
| L298 | Weird detail→cook→overview nav | Chunk 4 |
| L299 | Unsaved modal no cancel / click-out | Chunk 4 → A3 |
| L300 | Substitutes as a separate status | Skipped (DEC-6) |
| L301,302 | Substitutes-graph ref / destructive swap | B8 (already done) |
| L303 | Mark made → cooked | Chunk 3 (A8) |
| L304 | Delete confirm click-out | Chunk 4 → A3 |
| L305 | Mark cooked bigger; delete spacing | Chunk 4 |
| L306,307 | Remove CSV here; export/print out of ⋮ | Chunk 4 |
| L308 | Buttons across top, not bottom on mobile | Chunk 4 |
| L309 | Confirm cook mode if not ready | Chunk 4 |
| L310 | Tools required (configurable) + filter | Chunk 5 |
| L311 | Personal recipe notes in cook mode | Chunk 4 + cook mode |
| L312 | No way to create versions | Chunk 8 (DEC-2) |
| L313 | "Meals on hand" → "available meals" | Chunk 4 |
| L314 | Not-allowed cursor flash on meal +/− | Chunk 4 |
| L315 | Log-cook button → toolbar | Chunk 4 |

---

## 5. Suggested run order

Within Phase 1, alongside `IMPL_PLAN_COOK_MODE.md`:

1. **Chunk 1** — comparison cut + filter/sort axes. Self-contained,
   visibly improves the overview. No model changes.
2. **Chunk 3** — card redesign + naming. Pure frontend on top of Chunk 1.
3. **Chunk 2** — tag/cuisine/category catalogue tables + filter redesign.
   New schema; co-sequence with C-cross's settings editor.
4. **Chunk 4** — detail page cleanup. Biggest single-file diff; do it
   alone.
5. **Chunk 5** — images + tools (closes FU-039 + adds the Tool table that
   Chunk 6 depends on for `RecipeStepTool`).
6. **Chunk 6** — structured recipe steps. **Blocks C-3 Chunk 5.** Largest
   migration; do its own PR.
7. **Chunk 7** — source field + importer cleanup. Wires JSON-LD through to
   the Chunk 6 step model.
8. **Chunk 8** — versions (siblings via `version_group_id`). Stand-alone;
   can interleave anywhere after Chunk 4.
9. **Chunk 9** — cost + simple nutrition, behind their C-cross opt-ins.
10. **Chunk 10** — multi-part sections. Biggest ripple; last on purpose.

If a second agent is working in parallel, Chunks 1 and 8 are the safest
to take independently (Chunk 1 = no model change; Chunk 8 = single-column
+ self-contained UI).
