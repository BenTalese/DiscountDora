# Cookbook card revision — FU-088 redesign

**Status:** design-only (no code). Sequel to `PROPOSAL_COOKBOOK.md §2.10`
("Card redesign") and `IMPL_PLAN_COOKBOOK.md Chunk 3`, written off FU-088
browser-verification feedback (2026-06-13).

**Why a new proposal, not an amend of §2.10:** Chunk 3 shipped and was
browser-tested; the user came back with ten distinct findings, several of
which are cross-cutting (cooked-pool relocation, optional ingredients,
cookable-via-button-colour) and cannot be folded into §2.10 as one-line
tweaks. This document captures the next coherent step.

This proposal sits **on top of** the existing FU-088 verification list — that
list still applies for the bits already implemented; this document
**supersedes §2.10** for everything redesigned below.

---

## 0. Verify-state-first

Audited 2026-06-13:
- `web_app/src/components/RecipeCard.vue` — current Chunk 3 card.
- `web_app/src/components/recipes/MealStepper.vue` — `±` stepper, reused
  on detail page + stock-item page.
- `web_app/src/pages/RecipesOverview.vue` — emits handlers; passes
  `highlightStockItemIds` from `?usesStockItem=` deeplink.
- `web_app/src/models/recipe.ts` — DTO carries `time_of_day`,
  `available_meals`, `committed_meals`, `unallocated_meals`,
  `cookable`, `ingredients[*].is_missing`, `is_low_stock`,
  `is_optional` **(does not yet exist — new field, §3.6)**.
- `docs/04_proposals/PROPOSAL_MEAL_PLANS.md §3.1` already designs a
  per-recipe `(unallocated / pool)` row chip on the planner with a
  `+1 cooked / -1 cooked / log cook…` menu — the move-to-planner ask
  in FU-088 is already half-designed there.

Charter checks: `R-001` (componentisation — modal extracts to a reusable
ingredient-picker dialog), `R-003` (state ownership — cookability stays
server-derived; optional-ingredients flag is a server domain fact, not a
client toggle), `R-005` (Postgres/SQLite portability — migration for the
new `is_optional` column must be batch-safe), `R-011` (framework-idiomatic
patterns — Quasar `q-btn` colour for cookable state, not a sibling chip).

---

## 1. What's in (10 items, FU-088 verbatim → designed)

Numbered to match the user's bullets in FU-088, in that order.

### 1.1 Image hide/show is broken (defect, not a redesign)

Cause hypothesis (from `RecipeCard.vue:15`): `useImagePrefs()` reads from a
user-prefs store; if the store wasn't bootstrapped on the Cookbook route
the ref is `undefined` and the `v-if` flips to "always show initial". Fix
during implementation, not a design item — call out so it isn't lost.

### 1.2 New card layout & meta-line swap

Current top order (`RecipeCard.vue:39-90`):
1. Name
2. Cuisine · Category (caption muted)
3. Chips row: time, serves, difficulty, parts

Proposed:
1. Name (heart moves out — see §1.5, now in the footer)
2. Chips row: time, serves, difficulty, parts
3. **`[Cuisine] · [Category] · [Time of day]`** caption muted

Reasoning: the time/servings/difficulty row is the more actionable info
("can I eat this in the window I have?"), so it deserves the slot directly
below the title. The taxonomy line is identity, not filter input — it sinks.

- `time_of_day` already on the DTO (`recipe.ts:61`). When null, drop only
  that segment, keep separators tight (no leading `·`).
- `time_of_day` is now a **single value from a fixed vocabulary** (see
  §1.12) — no multi-valued joining, no overflow rule. One word per recipe.

### 1.3 Drop the "Add to meal plan" kebab item

`RecipeCard.vue:182-190`. The card has no kebab after §1.4, so this falls
out for free. The action remains in the recipe **detail** page.

### 1.4 Footer-bar add-to-list button + new ingredient-picker modal

Kill the `q-card-actions` overflow menu (`RecipeCard.vue:161-193`)
entirely. Footer becomes a single row:

```
[♥]   [👨‍🍳]                        [icon-only add-to-list]
```

- **Heart** (§1.5) is the **first** control in the footer, far-left,
  icon-only `flat`/`round`/`dense` `q-btn`. Mirrors `recipe.is_favourite`
  (filled red vs `favorite_border`).
- **Cook** is **icon-only** (`mdi-chef-hat`), no `Cook` label. Tooltip
  carries the verb. Same `unelevated` style as before; the colour now
  doubles as the cookable indicator (§1.6). When **FU-170** (app-wide
  button display preference: icon-only / icon+text / mixed) lands, this
  button is one of the buttons that *gets a label back* under
  icon+text mode and stays icon-only under mixed mode.
- The add-to-list trigger becomes a `flat`/`round` `q-btn` with
  `ICONS.add_shopping_cart` and a tooltip. No label.
- Same button serves both states (cookable / not cookable) — see §1.6 for
  the colour/icon swap.

**New component:** `RecipeIngredientPickerDialog.vue` (extracted as a
reusable; promoted by `R-001`). Opens both from the card's add-to-list
button **and** from the existing "Add missing" warning chip flow on the
detail page.

Shape:

```
┌─ Add ingredients to a list ──────────────────────────┐
│  Choose ingredients · target list: [List picker ▾]   │
│                                                       │
│  [✓] •  Carrots          out of stock                │
│  [✓] •  Onions           low                         │
│  [ ] •  Olive oil        sufficient                  │
│  [ ] •  Salt             well stocked                │
│  [ ] •  Pasta            sufficient                  │
│                                                       │
│  ───── Optional ─────                                │
│  [ ] •  Parsley (optional)   sufficient              │
│                                                       │
│  [Select all] [Select missing]    [Cancel] [Add]     │
└───────────────────────────────────────────────────────┘
```

- Per-row: stock-level dot (reuse `StockLevelDot.vue`), name, status word.
- Default check state:
  - `is_missing` → checked.
  - `is_low_stock` → checked.
  - `sufficient` / `well_stocked` → unchecked.
  - **Optional ingredients (§1.9)** → unchecked regardless of stock level
    (you only buy spares for an optional thing if you say so).
- Footer: list-picker (existing list selector component) +
  `[Select all] / [Select missing]` quick-action chips + Cancel/Add.
- Empty list → button is disabled on the card with a tooltip ("No
  ingredients").

### 1.5 Heart to the footer (first control)

Move from `recipe-card__fav` (absolute-positioned over the image,
`RecipeCard.vue:22-36`) to the **leftmost slot of the footer action row**
(`q-card-actions`), before the Cook button:

```vue
<q-card-actions class="row items-center no-wrap">
    <q-btn flat round dense
           :icon="recipe.is_favourite ? 'favorite' : 'favorite_border'"
           :color="recipe.is_favourite ? 'red' : undefined"
           @click.stop="emit('toggle-favourite', recipe.recipe_id)" />
    <q-btn unelevated round dense :icon="ICONS.chef_hat"
           :color="cookButtonColour"
           @click.stop="emit('cook', recipe.recipe_id)">
        <q-tooltip>Cook</q-tooltip>
    </q-btn>
    <q-space />
    <q-btn flat round dense :icon="addToListIcon"
           :color="addToListColour"
           @click.stop="openIngredientPicker" />
</q-card-actions>
```

Knock-on:
- The image overlay (`background: rgba(0,0,0,0.28)`) goes away — image is
  cleaner; nothing floats on it.
- All three card actions (favourite, cook, add-to-list) live in one
  predictable strip — easier to scan, easier to thumb on mobile.
- No competition with the title for horizontal space; long names get the
  full width back.

### 1.6 "Cookable now" merges into the Cook button + add-to-list mirrors it

Two-state cook button, no separate chip:

| State        | Cook button                        | Add-to-list button                       |
|--------------|------------------------------------|------------------------------------------|
| Cookable     | `color="primary"`, icon `mdi-chef-hat`, **no label** | `color=undefined` (neutral), icon `add_shopping_cart` |
| Not cookable | `color="warning"`, same icon/no label | `color="warning"`, icon `remove_shopping_cart` |

Tooltip on the Cook button explains state ("Cook this recipe" vs
"Missing N ingredients — open to log a substitute or cook anyway"). Click
behaviour is unchanged in both states; the colour conveys readiness, not
permission. Clicking the warning-coloured add-to-list opens the same
picker (§1.4) with `Select missing` pre-applied (default check states
already give this).

Remove the `Cookable now` / `Missing N` chip section
(`RecipeCard.vue:90-122`). The "X low" chip dies with it (§1.8).

### 1.7 Filter & sort by **difficulty**

`RecipesOverview` currently sorts by name / total_time / last_made /
servings. Add a `difficulty` axis (ordinal: easy < medium < hard, with
nulls sorting last regardless of direction — same null-sentinel rule as
`last_made`).

Filter: chip-row multiselect (FilterBar A4 pattern) with the three values.
Default = all selected = no filter. Per `R-003`, the ordering vocabulary
lives server-side: add a `difficulty_rank` derived field to the DTO (or a
`SortKey` enum the server understands), so the client doesn't redefine
"easy < medium < hard".

### 1.8 Drop the "X low" chip; enlarge dietary chips

Section `RecipeCard.vue:112-121` is removed (it's already going via §1.6).
The dietary tag chips (`recipe-card-tag`, `RecipeCard.vue:77-86`) get
`size="md"` instead of `sm` and `dense` removed. Acceptance: readable at
mobile zoom without zooming; visual diff in a Chromatic-style screenshot
test if/when we add one.

### 1.9 Optional ingredients (cross-cutting — design before code)

The biggest item. Touches: domain, migration, DTOs, cookability rule,
importer, recipe edit dialog, RecipeCard, cook mode, shopping-list flow.

**Domain change:**
- `RecipeIngredient` gains `is_optional: bool` (default `false`,
  not-nullable).
- Migration: batch-mode `add_column` on SQLite + plain on Postgres, no
  data backfill needed (`R-005`).

**Cookability rule (server-owned, `R-003`):**
- `recipe.cookable` = "no **required** ingredient is missing". **Optional
  ingredients are ignored entirely for cookability** — they never block,
  never warn, never produce a hint. A recipe with three missing optional
  items is just `cookable: true`, full stop.
- No `cookable_with_optional` field, no second cookability value.
- `RecipeIngredientDTO.is_missing` / `is_low_stock` stay per-row; the
  picker uses them. The server still computes these for optional rows so
  the picker can show the dot — they're just excluded from the recipe-
  level `cookable` rollup.

**Recipe edit dialog:**
- Each ingredient row gets a small "Optional" checkbox (existing
  `RecipeIngredientEditor` component — extend, don't fork).
- Importer: no auto-detection in v1 (parsing "or to taste" / parens is
  fragile). Importer just creates rows; user marks optional after import.

**RecipeCard:**
- "Missing N ingredients" counts **required ingredients only**. Optional
  missing items are not surfaced on the card.
- No hint line, no "(M optional)" suffix — optional ingredients are
  invisible on the overview. They only appear inside the picker modal
  (under the `─── Optional ───` separator) and on the detail/edit page.

**Cook mode:**
- Optional rows render with an `(optional)` suffix and a slightly dimmed
  row. No behaviour change to step grouping.

**Shopping-list flow:**
- Per §1.4: optional ingredients render under an `─── Optional ───`
  separator in the picker, unchecked by default, regardless of stock.

**Out of scope (defer):**
- Substitutes for optional ingredients (already handled by the existing
  substitutes feature; no extra wiring needed).
- Per-serving scaling of optional quantities — same as required.

### 1.10 "Allocated badge" never appears + remove from overview

Two bugs in one bullet:
- **Couldn't get it to appear**: requires `committed_meals > 0`
  (`RecipeCard.vue:136`). That value is server-derived from
  `MealPlanEntry` rows with `scheduled_for >= today` and `consumed_at IS
  NULL`. FU-088 step 3 says to test by scheduling a meal on a future day —
  if it still doesn't appear after that, the DTO field is missing or
  zero. Investigate the API path during implementation, not redesign.
- **Don't want it on overview anyway**: remove the entire allocated-box
  block (`RecipeCard.vue:135-147`). The information now lives on the
  meal-plans page row chip (`PROPOSAL_MEAL_PLANS.md §3.1`), which is where
  the user actually plans, not browses.

This also kills the `committed_meals` / `unallocated_meals` requirement
**for the cookbook** — those fields stay on the DTO for the meal-plans
page; just don't render them here.

### 1.11 Move "Meals cooked" stepper into the meal planner

Sub-thread of the same FU-088 bullet. Two halves:

**Remove from cookbook card** (`RecipeCard.vue:126-148`):
- Drop the entire meals box (stepper + label + allocated badge).
- The stepper still lives on the recipe **detail page** and on the
  **stock-item** page (per FU-088 verify step 2 and `R-001`). Those
  surfaces are kept — only the overview card loses it.

**Surface in the planner — note only, no edit now:**
- The FU-088 ask is *"easily adjust the number of meals available from
  that screen"*. `PROPOSAL_MEAL_PLANS.md §3.1` already designs a row chip
  `(unallocated / pool)` with a `+1 cooked / -1 cooked / log cook…` menu
  — close enough to the ask that we don't need to redesign here.
- **Scope of this proposal:** just remove the stepper from the card.
  Append a one-line note in `PROPOSAL_MEAL_PLANS.md §3.1` recording
  FU-088's stronger preference (inline stepper vs menu) so whoever
  implements the planner picks it up. **Do not edit the planner
  implementation now** — that proposal is unimplemented and any concrete
  redesign of §3.1 belongs in its own change.

### 1.12 `Recipe.time_of_day` → fixed vocabulary

Today: free-text `String(50)` nullable column
(`dora_api/persistence/table_mappings.py:375`,
`dora_api/domain/entities/recipe.py:38`,
`dora_api/features/recipes/create_recipe.py:100`,
`web_app/src/components/RecipeEditDialog.vue:57`). The edit dialog uses a
free-text input and the overview filter already assumes single-valued
(`pages/RecipesOverview.vue:749`).

Switch to a **fixed vocabulary** (same shape as stock-level names):
`Breakfast`, `Lunch`, `Dinner`, `Snack`, `Dessert` (defaults).

**Aligns with `PROPOSAL_MEAL_PLANS.md §4`** which already designs a
user-scoped, configurable meal-slot vocabulary (`Breakfast` / `Lunch` /
`Dinner` / `Snack`). The two are conceptually the same vocabulary
(`Recipe.time_of_day` says "this is a breakfast dish" as a suggestion;
`MealPlanEntry.slot` says "I'm having this for breakfast"). **Use the
single vocabulary defined by meal-plans §4 for both** — don't ship two
overlapping lists.

**Domain change:**
- `Recipe.time_of_day` stays `String` (no FK churn, matches the §4 stance
  for `MealPlanEntry.slot`) but the frontend always picks from the user's
  meal-slot list. Off-vocabulary historical strings (e.g. the seed's
  `"Dessert"` if the user removes that slot) render verbatim — no data
  loss, no destructive migration.
- One small ripple: `Dessert` is a current seed value but not in the
  meal-plans §4 default list. Add `Dessert` to the seeded defaults so
  parity is clean (this is a §4 amend, not a §1.12-only change — note
  below).

**UI change:**
- `RecipeEditDialog.vue` time-of-day input becomes a `q-select` over
  the user's slot vocabulary (with `clearable`).
- `RecipeDetailPage.vue` mirrors.
- `RecipesOverview.vue` already has the `timeOfDayFilter` from FU-148 —
  swap its option source from a hardcoded list (if any) to the slot
  vocabulary; single-select stays.

**Sequencing:**
- Sits naturally in **Chunk B** (alongside difficulty axis — both are
  "fix the filter to a real vocabulary" changes).
- Coupling with meal-plans §4: §4 hasn't shipped, so we can't depend on
  its user-settings page yet. **Bridge:** Chunk B introduces a tiny
  shared constant (`DEFAULT_MEAL_SLOTS = ['Breakfast','Lunch','Dinner',
  'Snack','Dessert']`) read by both surfaces. When §4 ships and adds
  the user-scoped configurable list, both surfaces switch to reading
  from that. Until then, the constant is the source of truth.

**Meal-plans proposal amend (in this same proposal's PR):**
- Append a note to `PROPOSAL_MEAL_PLANS.md §4` adding `Dessert` to the
  default list and recording that `Recipe.time_of_day` now consumes the
  same vocabulary.

---

## 2. Chunked plan (each chunk = one reviewable PR)

### Chunk A — Card visual redesign (no schema change) ★ FIRST

Pure-frontend on existing fields. No optional-ingredients yet.

- §1.1 image-toggle defect fix (small).
- §1.2 meta-line swap + new order.
- §1.3 kebab gone (falls out of §1.4).
- §1.4 footer-bar add-to-list **button only** (new modal lands in
  Chunk B alongside its checkbox semantics).
- §1.5 heart inline.
- §1.6 cookable absorbed into Cook colour + add-to-list mirror.
- §1.8 drop "X low"; enlarge dietary chips.
- §1.10 remove allocated badge from the card.
- §1.11 remove MealStepper from the card; **detail page + stock-item page
  keep theirs**.

Card simplifies dramatically; nothing schema-side moves yet.

Verify: full Cookbook browser pass on a seed account; covers FU-088 items
1, 2, 3, 5, 6, 8, 10, plus the cookbook half of 11.

### Chunk B — Ingredient-picker modal + difficulty axis

- §1.4 new `RecipeIngredientPickerDialog.vue` component (replaces the
  current straight-to-list flow). Wired to the card and to the detail
  page's "Add missing" entry point.
- §1.7 difficulty filter + sort axis (server vocabulary + client UI).
- §1.12 `Recipe.time_of_day` → fixed vocabulary (shared constant with
  meal-plans §4); edit-dialog input becomes a `q-select`.

No optional-ingredients yet — picker uses current ingredient list,
defaults check states by stock-level only.

Verify: FU-088 items 4, 7.

### Chunk C — Optional ingredients (cross-cutting)

The biggest piece; lands after A+B so its delta is isolated.

- Domain + migration (`is_optional`).
- DTO + cookability rule (`cookable` vs `cookable_with_optional`).
- Recipe-edit dialog UI (optional checkbox per row).
- RecipeCard hint copy ("Missing N (M optional)" + the muted cookable-
  with-optional line).
- Cook-mode row styling.
- Picker modal — optional rows render under the `─── Optional ───`
  separator, default unchecked.

Verify: FU-088 item 9; regression-check every place a recipe's "missing"
state is rendered (dashboard "next up to cook", planner shortfall banner,
stock-item recipe cards, assistant). Coverage gap list in the FU.

### Chunk D — *(folded into Chunk A)*

Removed. The card-side removal already lives in Chunk A (§1.11). The
planner-side change is **not** implemented in this proposal — instead, a
one-line note is appended to `PROPOSAL_MEAL_PLANS.md §3.1` recording the
FU-088 ask (inline stepper, not menu), to be actioned when the planner
proposal itself is implemented.

---

## 3. Risks & open decisions

- **Optional-ingredients ripples wider than the card.** The cookability
  rule is read by: dashboard "next up to cook", planner shortfall banner,
  assistant `search_recipes`/`suggest_recipes`, RecipeCard, stock-item
  recipe cards. Even though the rule's *definition* doesn't change
  (required-only, as today), every site that computes "missing
  ingredients" needs to filter out optional rows from its count.
  Chunk C must regression-check all five surfaces; logging any "missed
  call site" as a FU is mandatory.
- **Footer with three controls (heart / Cook / add-to-list) needs to
  breathe.** Layout is `[♥] [Cook] <q-space/> [add-to-list]` — heart
  hugs Cook on the left, add-to-list sits flush right. If review finds
  the heart-Cook pairing too cramped, insert a small `q-gutter-xs` or a
  vertical divider; if the right-side icon looks orphaned, give it a
  subtle outline (`q-btn--outline`).
- *(resolved 2026-06-13)* — `time_of_day` is now a fixed-vocabulary
  single value (§1.12); no overflow/truncation policy needed.

---

## 4. Cross-references to keep in sync

- `PROPOSAL_COOKBOOK.md §2.10` — supersede on merge; add a "see
  `PROPOSAL_COOKBOOK_CARD_REVISION.md`" pointer at the top.
- `PROPOSAL_MEAL_PLANS.md §3.1` — already amended with a one-line note
  recording the FU-088 preference (inline stepper over the menu). No
  implementation here; picked up when the planner proposal itself
  is built.
- `PROPOSAL_MEAL_PLANS.md §4` — to be amended (Chunk B PR) adding
  `Dessert` to the default meal-slot list and noting that
  `Recipe.time_of_day` shares the same vocabulary (§1.12).
- `IMPL_PLAN_COOKBOOK.md Chunk 3` — mark superseded for the card; new
  chunks A–D land in `IMPL_PLAN_COOKBOOK.md` (appended, not in-place
  rewritten) when each is queued.
- `DORA_FOLLOWUPS.md` FU-088 — flip recommended resolution from
  "browser-verify" to "implement card revision (this proposal); reverify
  after Chunk A".

---

## 5. Open decisions (for co-design)

*(All resolved 2026-06-13.)*

1. **Difficulty vocabulary** — **Resolved:** easy / medium / hard (three
   values).
2. **Chunk B vs C ordering** — **Resolved (recommended):** ship Chunk B
   first; Chunk C adds the optional-rendering rules as a small additive
   change.

---

## 6. From the original spec (historical — `docs/00_original_spec/`)

Skim of the original Recipe Feature Notes (`docs/00_original_spec/feature_notes/`):
- The original spec mentioned a **per-ingredient "optional" flag**
  explicitly (`recipe_ingredient_optional.md` or equivalent — confirm
  filename when implementing). **Keep** — this proposal lands the long-
  intended feature.
- Original spec had a "recipe complexity" score (server-computed) rather
  than a free-text difficulty field. **Consider** post-Chunk-B — if the
  free-text difficulty axis feels brittle, swap to a derived score
  (ingredients × steps × time). Out of scope for this proposal.
- No "merge cookable into Cook button" precedent — the original spec had
  a separate "Ready to cook" badge. **Superseded** by §1.6 here.

(If a sweep of `docs/00_original_spec/` turns up nothing to pull in for
the picker modal or the meta-line redesign, that's fine — they're newer
UX shapes than the original spec considered.)

---

## 7. Feedback coverage

Mapping FU-088 bullets → sections in this proposal. (Source: FU-088 text
itself, since this proposal is a follow-up to a verification finding, not
a new-surface design. The original `02_feedback/Feedback _ Fixes - as of
[06-Jun-2026].md` bullets that motivated Chunk 3 are tracked in
`PROPOSAL_COOKBOOK.md §7` and not duplicated here.)

| FU-088 bullet | Treatment | Section |
|---|---|---|
| Hide/show recipe images doesn't work | Defect; investigate in Chunk A | §1.1 |
| Rethink card design / dietary chips too small | Full visual redesign | §1.2, §1.5, §1.6, §1.8 |
| Meals cooked → move to meal planner | Remove from card (Chunk A); planner side noted in `PROPOSAL_MEAL_PLANS.md §3.1`, deferred to that proposal's implementation | §1.11 |
| New meta line `[Cuisine] · [Category] · [Time of day]` + swap with chip row | Card section reorder | §1.2 |
| Remove "Add to meal plan" button | Kebab gone; action stays in detail | §1.3 |
| Add-to-list → icon-only footer button | Footer redesign + new picker modal | §1.4, §2 Chunk B |
| Modal: per-ingredient checkboxes with stock dots, low/out auto-on | New `RecipeIngredientPickerDialog.vue` | §1.4 |
| Heart moves down to be in-line with the name | Reinterpreted as "out of the image overlay, into the footer action row as the first control" — same intent (one predictable strip for actions), avoids competing with long titles for width | §1.5 |
| Cookable chip → Cook button colour; mirror on add-to-list | State-via-colour | §1.6 |
| Filter/sort by difficulty | New axis + server vocab | §1.7, §2 Chunk B |
| Drop "X low" chip; enlarge dietary chips | Card section delete + chip resize | §1.8 |
| Optional ingredients (cross-cutting) | New domain field + cookability rule + UI ripples | §1.9, §2 Chunk C |
| Allocated badge never appeared + remove from overview | Investigate DTO path; remove from card regardless | §1.10 |
