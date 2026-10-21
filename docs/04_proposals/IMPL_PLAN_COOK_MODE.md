# Implementation Plan — Cook Mode (C-impl)

**Status:** Plan for review · **Date:** 2026-06-08 · **No code yet** — phased
plan + first reviewable chunk.
**Source proposal:** `PROPOSAL_COOK_MODE.md` (2026-06-06; decisions resolved
2026-06-08, §5a).
**Adjacent proposal:** `PROPOSAL_COOKBOOK.md` §2.6a (structured recipe steps —
landed here as a co-sequenced C-4 model change that gates C-3's per-step
features).
**Phase:** Master plan **Phase 1 (the loop)** — closes cook→consume, the
restock half of the loop that `IMPL_PLAN_SHOPPING_LISTS.md` opened.

---

## 0. Verify-state-first: no drift

Re-checked 2026-06-08 against `web_app/src/pages/RecipeCookMode.vue` and
`dora_api/domain/entities/recipe.py`. The code matches the proposal's
diagnosis and has **not** moved toward the solution:

- **`Recipe.instructions` is a single `str | None` field** (entity:18). Cook
  mode splits on `\r?\n+` into pseudo-steps and strips leading "1." / "1)"
  prefixes (`RecipeCookMode.vue:356-363`). No `RecipeStep` table exists.
- **Ingredient-step association is text-matched** (`:424-432`-ish) and breaks
  when an ingredient appears across steps 1/2/3 (proposal §2.4, L327).
- **Finish flow is blunt** (`:536-540`, `:562-619`): one boolean toggle
  `finishUpdateLevels` that drops every used item by `nextLowerLevelId` (one
  level), a `finishMealsCooked` defaulting to **1**, a single blanket
  `finishAddRanOut` toggle. No per-item level, no celebration, no
  click-out-to-cancel on the BaseDialog (dialog uses default Quasar
  behaviour).
- **Ticking** is two parallel sets: `usedIds` (ingredients) + `doneSteps`
  (steps), both client-only (`:368-369`).
- **Timer** is `setInterval` + a notify on finish (`:468-469`); no fill-bar,
  no reset surface, no sound, not theme-aware.
- **Voice** is wired but unnamed (`:340-350`); button reads "Enable voice".
- **`Recipe.servings`** exists (entity:26); no live headcount-scaling code.
- **No tools field** on `Recipe` (entity has none; C-4 §2.6 owns that).
- **Substitute session swaps work correctly** (`:386-417`) — keep, no change.

So the work falls into roughly six independent chunks, with **only** the
structured-steps chunk (4) gating the per-step polish chunk (5). Everything
else can land in any order.

---

## 1. Chunked plan (each chunk = one reviewable PR)

### Chunk 1 — Finish-flow rewrite ★ FIRST REVIEWABLE CHUNK
**Closes:** §2.1 + L319 / L334 / L334b / L336 / L337 / L338 + DEC-5.

The highest-value, loop-closing change. Drop the three blanket toggles + flat
toast and ship a per-item finish checklist:

- For each ingredient in `usedIds` (resolved through `sessionSwaps`), render a
  row with its **current stock level** and a level control:
  - **Quick chips** — `↓ one level` (default), `Out`, `Unchanged` (the §5a
    DEC-5 resolution).
  - **Full level dropdown** override (any level the user picked
    deliberately).
- **Per-item add-to-shopping-list** on each row — uses the C-7 cart-button
  component when it exists, falls back to a small `Add to list` text button
  routed through `useStockItemActions.addToList` until C-7 lands. **Removes**
  the blanket `finishAddRanOut` toggle.
- **`meals_cooked` defaults to 0**, not 1; copy reads *"leave at 0 if you
  just ate it"* (L338). Field is optional; cooking still completes.
- **Modal click-out cancels** — set `persistent="false"` (or A3 modal default
  once A3 lands) on the finish dialog (L334b).
- **Celebration on finish** (L337) — small confetti / animation + a
  *"You saved N meals"* line that reads off `meals_cooked` (e.g. *"You saved
  3 meals — enjoy."* / *"All eaten, hope it was good."* when `0`). Replaces
  the flat *"Nice cooking!"* toast. Use the existing `useUndo` /
  `notifyUndoable` chrome if a one-liner is easier than confetti chrome.

**Server change:** none required. `stockItemStore.updateStockLevelAsync` +
`recipeStore.cookAsync` already exist; this chunk only rewires the client.

**Risk:** the per-item loop is a chain of awaits today (`:572-583`); fan-out
or fail-soft so one bad item doesn't kill the rest. Tests: a finish with
0 used / 1 used / 3 used; one row deliberately set to `Unchanged`; one row
set to a specific level via the override; `meals_cooked = 0`; click-out
cancels with no state mutation.

*Acceptance:* the dialog renders one row per used ingredient with
chips+override, a per-row add-to-list button, `meals_cooked` field defaulting
0, and a celebratory close. The three old toggles are gone.

### Chunk 2 — Cook-mode polish
**Closes:** §2.7 (timer) + §2.8 (units) + §2.9 (sous chef) +
L324 / L325 / L326 / L329 + DEC-3.

Independent of every other chunk; can ship in parallel with anything.

- **Timer** — replace the bare MM:SS text with a horizontal fill-bar that
  empties as time passes (`<q-linear-progress :value="…">` styled via theme
  tokens, A1). On finish: change the bar's tone, play a short beep
  (`new Audio()` with a short generated tone or a tiny embedded WAV — keep
  asset weight near zero), keep the existing toast. Add a visible **Reset**
  button (currently the only way is to recreate the timer via "Start timer").
  All colours via tokens (R-002 / A1).
- **Unit attach** — new helper `formatQuantity(quantity, unit)`. Inclusion
  list of no-space units per DEC-3: `ml, g, kg, l, mg, oz, lb, floz, pt,
  qt`. Everything else gets a space. Comprehensive unit tests; this is one
  function that affects every quantity render across recipes, shopping lists,
  and cook mode (callers replaced opportunistically — start with cook mode,
  log a finding for the rest).
- **Sous chef** — rename "Enable voice" → **"Sous Chef"** (with a tiny chef-
  hat icon if one exists in the icon set, else `record_voice_over`). Add a
  popover listing the commands the user can speak (next / previous / repeat
  / start timer / stop). Underlying TTS + recognition (`composables/useVoice`)
  unchanged.

**Risk:** generated audio in PWA / Safari — fall back to silent timer if
audio fails. Theme tokens for the timer bar already exist (A1 §2 token
list).

*Acceptance:* timer is a fill-bar with a visible reset, tones on finish,
respects theme; "Sous Chef" button reads named + has a help popover;
`formatQuantity(2, "ml")` → `"2ml"`; `formatQuantity(2, "scoops")` →
`"2 scoops"`; `formatQuantity(2, "oz")` → `"2oz"`.

### Chunk 3 — Mid-cook ingredients UI
**Closes:** §2.3 + L321 / L323 / L323b / L330 / L334.

Independent of every other chunk.

- **Group ingredients by base stock location** (top-level only — no
  sub-areas; "Pantry > Spice Rack" collapses to "Pantry"). Each group is a
  card; ungrouped ingredients (no location) drop into a labelled "No
  location" group at the end.
- **De-emphasise stock level mid-cook.** Once a recipe is being cooked the
  decision is already made; the missing-ingredient / low-level chips that
  the in-cook panel renders today (`RecipeCookMode.vue` ingredient row) move
  to the **finish** surface (Chunk 1) and stop rendering during cooking.
  Removes the visual noise the user called "horrible" (L323b).
- **Token-driven rebuild** of the ingredient card — apply A1 theme tokens,
  larger / calmer (P1 Effortless). No new componentisation beyond what A1's
  `dora-*` primitives already give us (R-001).

**Risk:** the location breadcrumb already arrives on shopping-list lines but
not yet on `RecipeIngredient`. Need to look up the stock item's location at
render time (already done for the chip lookup via `stockItems.value.find`).
No backend change.

*Acceptance:* ingredient list renders as grouped cards by base location; no
stock-level chips during cooking; styling reads in Pesto Light + Pesto Dark
+ Cherry Cola Dark.

### Chunk 4 — Structured recipe steps (lives in C-4; **blocker for Chunk 5**)
**Closes:** `PROPOSAL_COOKBOOK.md §2.6a` + L323.

This chunk is *part of C-4 implementation* but co-sequenced here because
Chunk 5 can't ship without it. Treat as a hard dependency; do it before
Chunk 5 even if other C-4 chunks are still pending.

- **Backend:**
  - New `RecipeStep` entity: `{ id, recipe_id, sequence, text, hint?,
    parent_step_id? }`. `parent_step_id` makes sub-steps one level deep
    (Recipe → Step → SubStep — the proposal explicitly bounds this).
  - Join tables `RecipeStepIngredient` (step_id, recipe_ingredient_id) and
    `RecipeStepTool` (step_id, recipe_tool_id — the tool table is a C-4 §2.6
    deliverable; co-sequence or stub).
  - Alembic migration. Batch mode for SQLite portability (R-005).
  - `Recipe.instructions` **kept**; a recipe with empty `steps[]` reads as
    "unstructured" and degrades through today's newline-split path
    everywhere.
  - DTOs (recipe summary + detail) expose `steps[]` ordered by sequence.
  - Create + update endpoints accept `steps[]`; the URL importer (C-4 §2.7)
    emits structured steps when the source has them in JSON-LD
    `recipeInstructions`.
- **Frontend (recipe detail editor):**
  - Step list editor replaces the instructions textarea: each step has its
    text, an *add hint* affordance, multi-select pickers for ingredients and
    tools (from the recipe's own lists), a *+ sub-step* affordance.
  - Old `instructions` textarea stays as an *Advanced ▾ Freeform* fallback
    so users with imported recipes can still mass-edit. Saving via the step
    editor writes `steps[]`; the textarea writes `instructions` and leaves
    `steps[]` empty.

**Risk:** existing recipes carry text-blob instructions only; the migration
adds the tables but does **not** parse instructions into steps. Users opt
in by editing. The cook-mode side handles both shapes via §0's fallback
discipline.

*Acceptance:* a recipe saved with structured steps round-trips; a recipe
with empty `steps[]` still renders correctly everywhere; migration applies
cleanly on SQLite + Postgres.

### Chunk 5 — Highlight + per-step features (gated on Chunk 4)
**Closes:** §2.4 + §2.5 + §2.6 hints + §2.7 per-step timers +
L322 / L327 / L328 + DEC-1.

Independent of Chunks 1–3; blocked only on Chunk 4.

- **Drop tick state entirely.** Remove `usedIds` and `doneSteps` and their
  template wiring. *Used* is no longer a thing the user toggles — every
  ingredient on a recipe is *used* by definition, so finish (Chunk 1) ranges
  over `recipe.ingredients`, not over `usedIds`. (Session swaps still apply
  per ingredient.)
- **Per-step highlight.** When the current step has `ingredient_refs`,
  highlight those rows in the ingredient panel + the matching `tool_refs`
  in the tools panel (Chunk 5 also surfaces a tools panel when the recipe
  has tools — §2.5; otherwise hidden). For an unstructured recipe (empty
  `steps[]`) keep today's text-matched highlight as the fallback.
- **Per-step hints.** Render `step.hint` as a small footer line under the
  step text when present.
- **Per-step timers.** Auto-detect minute references in `step.text` (the
  existing `extractMinutes` lives in cook mode); for structured steps, also
  honour any explicit `step.timer_minutes` field if we add one (probably a
  Chunk-4 polish; otherwise text-extract is enough).
- **Removed**: any UI element that depended on tick state (the "Used" tab,
  the per-step done checkbox).

**Risk:** the ingredient-row component has tick-related props and styles
woven in; rip them, don't conditional-on-feature-flag (R-007 anti-creep —
no compat shims). Tests: a structured recipe with overlapping ingredients
across steps highlights the right ones in each; an unstructured recipe
falls back without console errors.

*Acceptance:* no tick boxes anywhere in cook mode; structured recipes
highlight per step correctly; unstructured recipes use text-match fallback.

### Chunk 6 — Serving auto-adjust by headcount
**Closes:** §2.2 + L320 + DEC-4.

Depends on **C-5 onboarding** providing a default `household_headcount`
setting. Stand-alone if C-5 isn't there yet — default to `recipe.servings`
and accept a no-default UI.

- New session-only `cookingFor` ref, defaulting to
  `userSettings.household_headcount ?? recipe.servings ?? 1`.
- A small **"Cooking for ___"** control in the cook-mode header — Quasar
  `q-input type="number"` with `min=1`.
- All quantity renders go through `scaleQuantity(q, recipe.servings,
  cookingFor)`, then through `formatQuantity` (Chunk 2). DEC-4: round
  sensibly — half-quantities snap to `½`, third-quantities to `⅓ / ⅔`,
  quarter-quantities to `¼ / ¾`; otherwise round to the nearest 1 (integer
  countables like eggs) or 0.1 (mass / volume).
- **Session-only.** Never writes back to the saved recipe (same discipline
  as B8 swaps).

**Risk:** the rounding rule needs to handle countables (eggs) vs continuous
(grams) differently. Use a simple heuristic based on the formatted unit: if
the unit is in the "countable" set (`null, "egg", "clove", "scoop",
"slice"…`) round to 1; otherwise round to the most readable fraction. Tests
cover: 1.5 eggs → 2; 0.66 cups → ⅔ cup; 1.333 cups → 1⅓ cup; 7.5g → 8g.

*Acceptance:* changing headcount instantly rescales every visible quantity;
the saved recipe is unchanged after exit; rounding lands on the resolved
DEC-4 buckets.

---

## 2. First reviewable chunk — definition of done

**Chunk 1 (finish-flow rewrite).**

- One row per ingredient that was *used* in the cook session. (Today's
  `usedIds` survives in Chunk 1; Chunk 5 removes the concept entirely by
  treating every recipe ingredient as used.)
- Each row carries `↓ one level / Out / Unchanged` chips **plus** a level
  dropdown override (DEC-5).
- Per-row "Add to list" button (C-7 cart-component proxy if available,
  fallback to a plain button routed through `useStockItemActions.addToList`).
- `meals_cooked` defaults to `0`; label reads "If you batch-cooked, set how
  many meals are in stock — leave at 0 if you just ate it."
- Click-out / Esc cancels the finish dialog with **no state mutation**
  (R-009 preview→approve→commit).
- Celebration on finish: a one-line "You saved N meals" notify, or confetti
  if cheap. Replaces "Nice cooking!".
- Tests: 0 / 1 / 3 used items; one row deliberately `Unchanged`; one row
  full-picker override; `meals_cooked = 0`; cancel = no mutation.
- The three old toggles (`finishUpdateLevels`, `finishAddRanOut`, and the
  "Skip & exit" button) are gone or rewired.

---

## 3. Risks & open decisions

**Risks:**

- **Chunk 4 is the largest and the only blocker.** Treat as its own PR; do
  not bundle it with Chunk 5 (review surface explodes).
- **Chunk 1's per-row level loop runs `updateStockLevelAsync` once per item.**
  For a 12-ingredient recipe that's 12 network calls; consider a server-side
  bulk endpoint if a "lag at finish" complaint surfaces. *Don't pre-build it
  now* (P10 anti-creep) — wait for the signal.
- **Chunk 5 ripples** to every consumer of `usedIds` / `doneSteps` (currently
  only cook mode; verify with a grep before merge).
- **Chunk 6's rounding rule** is the kind of thing every user has an opinion
  on. Ship DEC-4 and adjust if feedback rolls in.

**Open decisions:** none — all 5 closed in `PROPOSAL_COOK_MODE.md §5a`
(2026-06-08). Decisions are now implementation-time invariants; the table
in §5a is the canonical answer.

**Cross-refs:** C-4 §2.6 tools + §2.6a structured steps · C-5 onboarding
headcount · C-7 cart button · A1 theme tokens · A3 modal standard · B8
substitute swaps (kept).

---

## 4. Feedback coverage

Maps COOK MODE (L317-338).

| Bullet (line) | Summary | Where |
|---|---|---|
| L319 | Set stock levels at finish (checklist) + add-to-list after cooking | Chunk 1 |
| L320 | Auto-adjust quantities by headcount (default from onboarding) | Chunk 6 (C-5 dep) |
| L321 | Ingredients grouped by base location | Chunk 3 |
| L322 | Tools section, highlighted per step; hide if none | Chunk 5 (C-4 dep) |
| L323 | Sub-steps: how added/displayed; per-step hints as footer | Chunk 4 (C-4) + Chunk 5 |
| L323b | Ingredients UI looks horrible | Chunk 3 |
| L334 | Stock level not relevant mid-cook | Chunk 3 |
| L324 | Timer not theme-aware; reset not visible | Chunk 2 (A1) |
| L325 | Timer no sound; should restyle + fill-bar | Chunk 2 |
| L326 | "2scoops" — unit inclusion list | Chunk 2 (DEC-3) |
| L327 | Ticking calc odd (ingredient across steps) → highlight | Chunk 5 (DEC-1) |
| L328 | Ticking unnecessary for ingredients & steps → highlight only | Chunk 5 (DEC-1) |
| L329 | Voice button not obvious; "enable voice" unclear; sous chef | Chunk 2 |
| L330 | Page styling boring/basic | Chunk 3 (A1) |
| L334b | Finish modal click-out doesn't cancel | Chunk 1 (→ A3) |
| L337 | Finish feels boring — where's the hooray/congrats | Chunk 1 (celebration) |
| L336 | Mark levels individually; removes "add to list?" toggle; per-item add | Chunk 1 |
| L338 | Meals cooked should start at 0, optional | Chunk 1 |

---

## 5. Suggested run order

Within Phase 1, after `IMPL_PLAN_SHOPPING_LISTS.md` (P6-01) lands:

1. **Chunk 1** (finish flow). Highest value, no dependencies, closes the
   loop visibly for the user.
2. **Chunks 2 + 3** in either order — both pure-frontend polish, no
   dependencies on each other.
3. **Chunk 4** (structured steps, in C-4). Sets up Chunk 5.
4. **Chunk 5** (highlight + per-step). Lights up the rest of the
   per-step ergonomics.
5. **Chunk 6** (headcount). Depends on C-5; can move earlier if C-5
   ships first and you want it in users' hands.
