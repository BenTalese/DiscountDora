# Meal Plans — redesign proposal (Wave C-2)

**Status:** proposal · changes **no code** · revised after a full
cross-check against `docs/Feedback _ Fixes - as of [06-Jun-2026].md §MEAL PLANS`.
**Reads from:** `MealPlansOverview.vue`, `MealPlanEditDialog.vue`,
`mealPlanStore`, `dora_api/features/meal_plans/*`,
`dora_api/features/recipes/{cook_recipe,adjust_recipe_meals,get_recipes}.py`,
`reconcile_consumed_meals`.

Brief: `docs/prompts/C_big_rock_design_briefs.md §C-2`.
Governing principles: Dashy Dora Decision Charter — every section is
checked against **Effortless** (sensible defaults, no input where
context is enough) and **Anti-creep** (one good model, reuse Wave A,
don't invent surface the brief didn't ask for).

---

## 1. Re-grounding (verified against live code)

- **Meals→recipes merge complete.** `Recipe.available_meals: int` is
  the on-hand pool. `cook_recipe` adds, `adjust_recipe_meals` ±deltas,
  `reconcile_consumed_meals()` runs each request — marks past-due
  entries `consumed_at` and decrements the pool.
- **B6 allocation already works.** `_hydrate_unallocated`
  (`get_recipes.py`) returns
  `unallocated_meals = max(available_meals - sum(future un-consumed servings), 0)`
  via one GROUP BY. Palette renders this directly. Logged
  [FU-032](DORA_FOLLOWUPS.md) for browser confirm per the CLAUDE.md
  rule.
- **Shortfall surface exists** (`GET /meal-plans/shortfall`); banner +
  per-entry warning icon.
- **`MealPlanEntry.slot`** is free-text `str(50)`. No vocabulary.
- **Past-day handling.** Backend refuses `scheduled_for < today` on
  create+update. Existing past entries are preserved during a future
  replace.
- **Frontend gap that bit us:** `isPastDay(iso)` on the canvas uses a
  drift-prone local-date string while the backend uses server-local
  `date.today()`. Around 8am AEST today shows as "still yesterday" to
  one and "today" to the other — drop on Wed at 8am Thu → 400. Fix
  spec in §13.
- **No templates, no recurring, no carousel, no left vertical list, no
  custom calendar widget, no rotating sets exist today.**

---

## 2. Decisions resolved with the user

These are locked. The rest of the doc is shaped around them.

1. **Templates × editing:** plan is **forked** from the template at
   apply-time. Editing the plan never touches the template; editing
   the template only affects future applications. Plan carries
   `source_template_id: UUID | null` for provenance / a "re-apply"
   affordance.
2. **Past days when applying a template:** **skip entirely** — never
   stamp past slots; matches backend's existing refusal.
3. **Shortfall banner:** **dropped from page top.** Keep the per-entry
   warning, plus a single sidebar summary line.
4. **Rotating template sets (A→B→C→D→repeat):** **in scope.** A
   `MealPlanTemplateSet` is an ordered list of templates that
   rotates by week. New "recurring apply" uses a set (or a single
   template) and forks the right one per week.
5. **Trays placement** ("Favourites" / "Haven't had in a while"):
   **inside the left column**, above the all-recipes list. Keeps the
   page from going horizontally heavy.
6. **"Generate shopping list" target choice:** **single button → choice
   modal.** Pick existing list (defaults to primary), or create new.
7. **Cookable cues on the planner:** **dropped entirely.** No
   green-check, no "in-stock only" filter, no "Suggest meals I can
   cook now" CTA on this page. Cookable lives on Cookbook (C-4).

---

## 3. The redesign — surface map

Three columns on desktop, stacked on mobile. **No** page-level title
("Week of…" disappears — the carousel is the title). **No** page-level
shortfall banner. The page's primary nav header is just the page name
+ a small `Plan step-by-step` CTA (sequential builder, §6).

```
┌────────────────────┬───────────────────────────────────────────────┬────────────────────┐
│ Recipe list (left) │ Week carousel (main)                          │ Calendar (right)   │
│                    │   ▲ prev week                                 │ ────────────────── │
│ Search · filters   │  ┌─────────────────────────────────────────┐  │ Month banner       │
│                    │  │ Mon  Tue  Wed  Thu  Fri  Sat  Sun       │  │ ────────────────── │
│ ▾ Favourites       │  │ (slot rows per day)                     │  │ ░░░░ ▓▓▓▓ ░░░░     │
│ ▾ Haven't had in   │  └─────────────────────────────────────────┘  │ ░░░░ ▓▓▓▓ ░░░░     │
│   a while          │   ▼ next week                                 │ rounded squares    │
│                    │                                               │ + status underlines│
│ ▾ All recipes      │                                               │                    │
│   (virtualised)    │                                               │ ────────────────── │
│                    │                                               │ Shopping summary   │
│ Tap to add → cell  │                                               │ ─ 3 to buy         │
│ Drag desktop only  │                                               │ ─ 2 to cook by Fri │
│                    │                                               │ ─ Add to / Gen ▾   │
│                    │                                               │ ────────────────── │
│                    │                                               │ Templates ▾        │
└────────────────────┴───────────────────────────────────────────────┴────────────────────┘
```

### 3.1 Left column — recipe list

- **Three collapsible sections (top → bottom)**:
  - **Favourites** — recipes with `is_favourite`, pinned.
  - **Haven't had in a while** — `last_made_on IS NULL OR < today − 21d`,
    oldest-first, capped at 10.
  - **All recipes** — virtualised (`q-virtual-scroll`); identical row
    shape to `RecipesOverview` so users don't relearn.
- **FilterBar** (A4) at the top:
  - free-text search;
  - `planned within next N weeks` (default 1; expandable);
  - tag filters — land here when C-4 ships the tag overhaul.
  - **No** cookable / in-stock filter (Decision 7).
- **Row shape**: recipe name + a single small `(unallocated / pool)`
  count chip at the row's right edge — the chip's *number* is the
  emphasised element; **no green-check, no colour swap based on
  cookability.** Tap row body → focus the cell-target (see §3.2); tap
  the count chip → menu (`+1 cooked` / `−1 cooked` / `log cook…`).
- **Drag** desktop pointer only (`@pointerdown` checks
  `event.pointerType === 'mouse'`); touch users get tap-to-add.
- **FU-088 (2026-06-13) note — cooked-pool stepper relocates here.** The
  cookbook overview card removed its `MealStepper` (see
  `PROPOSAL_COOKBOOK_CARD_REVISION.md §1.11`). User's stronger preference
  is *inline `[ − N + ]` on the row* rather than the
  `+1 cooked / -1 cooked / log cook…` menu specified above — pick this
  up when this proposal is implemented. Pool adjustment must be
  reachable from the planner; the menu form is acceptable as a fallback
  if the inline form crowds the row.

### 3.2 Main column — week carousel

- **Vertical carousel.** Up-arrow ABOVE the area = previous week;
  down-arrow BELOW = next week. Up/down keyboard, swipe (mobile).
  Smooth slide animation (Quasar `slide-up`/`slide-down` transition,
  respect `prefers-reduced-motion`).
- **No "Week of…" title.** The calendar widget on the right is the
  source of truth for which week is in view; the carousel's edge
  arrows and the calendar's highlight stay in sync.
- **Slot rows per day.** Each day is a vertical stack of named slot
  rows (Breakfast / Lunch / Dinner / Snack — see §4). Empty slot row
  is its own tap/drop target; the slot value is **auto-derived from
  the cell tapped** — no slot picker on add. Today's "always Dinner"
  bug goes away by construction.
- **Past days** render dimmed at `opacity: 0.6`; no add target.
  Consumed entries show a check chip.
- **Entry chip** redesign (fixes the "icons/text overflow card" bug):
  - **Two horizontal regions** inside the chip:
    - left = recipe name (wraps to 2 lines if needed);
    - right = a small *numeric pill* showing `×{servings}`, **its own
      colour separated from the chip** (rounded box,
      `--surface-elevated` bg, larger numeric weight). The on-hand
      count is gone from the chip itself; it lives in the recipe-list
      row (where it actually belongs — planner shows demand, list
      shows supply).
  - The chip wraps to a second line on narrow days, doesn't truncate
    icons. No icon stack > 1 at a time (shortfall icon ONLY when
    shortfall; check ONLY when consumed; never both).
- **Same recipe → same (day, slot)** increments servings on the
  existing entry rather than creating a duplicate.
- **Same recipe → same day, different slot** stays two entries (matches
  current `MealPlanEntry` shape).
- **Per-entry menu** — view recipe / cook now / `Servings: ± n` inline
  adjuster / remove. **No** "Edit entries" button; servings and slot
  are editable directly on the canvas, so the modal is removed.

### 3.3 Right column — calendar, shopping summary, templates

#### Custom calendar widget

- ≈ 6 weeks at a time, vertical stack of week-rows. **Replaces** the
  current "Active plan" dropdown — this widget is how you pick which
  week is in view.
- **Month banner** at the top (e.g. `JUNE`), updates as the focus
  week's month changes.
- Each week-row: 7 small rounded squares (Mon-Sun). **Only the first
  square in each row carries text** — the date as `DD` (e.g. "25").
  The other six are silent rounded blocks. Minimalist.
- **Status underlines** under each square — A1 tokens:
  - empty (no entries) — no underline;
  - planned (≥1 entry, not short) — solid `--semantic-positive`;
  - short (any entry on that day is in shortfall) — solid
    `--semantic-warning`;
  - all consumed — dotted `--text-muted`.
- **Focused week** outlined with `--brand-primary` (the border, not a
  fill — keeps the squares legible).
- **Today's square** carries a small accent dot.
- Clicking a week-row → focus that week in the carousel (smooth-scroll).

#### Shopping summary

- One-line headline: **3 to buy** (counts `needToBuy.length`).
- One-line **2 to cook by Fri** (the moved shortfall summary;
  earliest `earliest_needed` as the deadline word; **icon = chef's
  hat**, not the warning triangle).
- Per-stock-item list under the headline now includes the **shopping-list
  status** of each item (already on list X / not yet). Two affordances:
  - per-row plus icon → add only that item (opens the choice modal
    below if multiple lists);
  - bottom CTA **`Add to / Generate list`** (a single button) →
    **choice modal**: pick an existing list (default = primary), or
    create a new one. Adds everything not already on the chosen list;
    won't double-add.
- **Hover-to-highlight** (desktop only): hovering a stock-item row
  highlights the day cells whose recipes used it. Lost feature on
  touch; mobile keeps the list, just no hover.

#### Templates

- `Save this week as a template` (visible when focused week has
  entries).
- `Apply a template…` dropdown opening a chooser. Two tabs:
  - **One week** — pick a template → "Will replace 3 future entries
    in this week. Continue?" warning when current week is non-empty.
  - **Recurring** — pick a single template OR a **template set** →
    date-range picker (whole weeks) → applies. Per-week fork.

### 3.4 Creating a new plan

- **No** date picker, **no** modal. Replaced by the calendar widget
  in the right column.
- Each empty week-row in the widget is implicitly "new plan here" — the
  first tap-to-add on a day for an unplanned week silently creates
  the `MealPlan` for that week and adds the entry.
- "I want to apply a template to a brand-new week" is covered by
  `Apply a template…` → pick week from the calendar widget.

### 3.5 No `MealPlan.name` for instances

- `MealPlan.name` is **dropped from instances.** Display is always
  "Week starting `<date>`" (computed). Existing rows keep their
  stored name as a hidden field for migration / log readability but
  the UI never surfaces it.
- **Templates** keep `name` (it's the only thing the user types).
- Migration: column stays nullable; new instances written by the
  planner leave it null; the GET handler ignores it. (Aligns with
  Anti-creep — no migration to remove a column we're already
  ignoring.)
- "Delete plan" is renamed **"Clear week"** — clears the focused
  week's entries; if it was the last weeks's entries on a recurring
  template-set's window, the plan row itself is deleted.

### 3.6 Page chrome — removed

- **Page-level shortfall banner.** Moved into per-entry chip + sidebar
  summary line.
- **"Suggest meals I can cook now" CTA + modal.** Cookable belongs on
  Cookbook (Decision 7).
- **"Week of <date>" subtitle.** Carousel is the title.
- **"Edit entries" button.** Servings/slot edit inline.
- **CSV export button.** Use Print or the data-management Export tab.
- **"Active plan" dropdown.** Calendar widget replaces it.
- **`generateListForWeek` standalone CTA.** Merged into the new "Add
  to / Generate" choice modal in the sidebar.

### 3.7 Page icon

Swap the calendar icon for the **chef-hat** (`ICONS.chef_hat` if it
exists in the MD set; otherwise `mdi-pot-mix`). The brief's request
("the one that was for meals page" — pre-merge) and the chef-hat motif
for shortfall give us a coherent identity.

---

## 4. Slots — configurable times-of-day

Today: `MealPlanEntry.slot` is free-text `str(50)`; unconstrained.

Proposed:

- New **settings → preferences → meal slots** vocabulary, user-scoped.
  Defaults shipped: `Breakfast`, `Lunch`, `Dinner`, `Snack`, `Dessert`
  (`Dessert` added 2026-06-13 to align with the cookbook revision —
  `Recipe.time_of_day` shares this vocabulary, see below). User can
  reorder (drag), rename, add (max ~8), remove (with a confirm when
  any entry uses the slot).
- **`Recipe.time_of_day` consumes the same vocabulary** (cookbook
  revision §1.12). Until this proposal ships its user-settings page,
  the cookbook surfaces read from a shared frontend constant
  `DEFAULT_MEAL_SLOTS` mirroring the server's
  `dora_api/domain/entities/recipe.py::DEFAULT_MEAL_SLOTS`. When the
  user-scoped list lands here, both surfaces switch to reading from
  that list (the constant becomes the seeded default).
- `MealPlanEntry.slot` stays a `str` (no FK churn). Frontend always
  picks from the user's list; off-vocabulary historical strings are
  preserved verbatim and rendered in a "Other" row at the bottom of
  the day's slot stack. A one-shot "remap to current vocabulary"
  action in settings can clean these up.
- Tap-add on a Breakfast row produces `slot = "Breakfast"`. No
  picker. Single biggest behavioural change vs the always-"Dinner"
  bug.
- Ripple to C-5 (onboarding) — seed default list there.
- Ripple to settings; this is the only addition to a deferred area in
  scope. One new sub-page row in `settings → preferences`; not a
  redesign.

---

## 5. Templates & template sets

### Template data model

```
MealPlanTemplate
├─ id
├─ name                     e.g. "Weekday batch + Friday fresh"
├─ description?             free text, optional
└─ entries[]                List[MealPlanTemplateEntry]
                              ├─ recipe_id
                              ├─ offset_from_monday  0..6
                              ├─ slot                str (validated
                              │                       against user's slot
                              │                       list at save-time;
                              │                       legacy preserved)
                              └─ servings
```

### Template-set data model (rotating)

```
MealPlanTemplateSet
├─ id
├─ name                     e.g. "Monthly batch rotation"
├─ description?             free text, optional
└─ ordered_templates[]      List[{ template_id, position }]
                            (position = 0..n; rotation cycles modulo length)
```

### `MealPlan` provenance

```
MealPlan
├─ … existing fields
├─ source_template_id      UUID | null    (set on single-template fork)
└─ source_template_set_id  UUID | null    (set on rotating apply;
                                            plus rotation_index for
                                            "which template in the set
                                            applied to this week")
```

### API additions

| Verb | Route | Purpose |
|---|---|---|
| `POST` | `/meal-plan-templates` | Save the focused week as a template. |
| `GET`  | `/meal-plan-templates` | List user's templates. Paginated. |
| `PATCH`| `/meal-plan-templates/{id}` | Edit template (does not propagate to existing plans — Decision 1). |
| `DELETE`| `/meal-plan-templates/{id}` | Delete. |
| `POST` | `/meal-plan-template-sets` | Create a rotating set. |
| `GET`  | `/meal-plan-template-sets` | List. |
| `PATCH`| `/meal-plan-template-sets/{id}` | Reorder / rename. |
| `DELETE`| `/meal-plan-template-sets/{id}` | Delete. |
| `POST` | `/meal-plans/from-template` | Body: `{ template_id, monday_of_week }`. Server: fork a `MealPlan`; compute `scheduled_for = monday + offset`; **skip any offset whose date < today** (Decision 2). |
| `POST` | `/meal-plans/from-template/recurring` | Body: `{ template_id` *or* `template_set_id, start_monday, end_monday }` (whole weeks). Server: per-week fork; for sets, rotates `position` through the ordered list modulo length. |

### UI

- **Save** — right column, modal asking for name (prefilled `Week of
  <date>`) and optional description.
- **Apply one week** — right column, modal with a list of templates;
  the warning copy when the current week has entries names the count
  ("Will replace 3 future entries…").
- **Apply recurring (template or set)** — same dropdown, switches to
  "Recurring" tab. Range picker (whole weeks; default end = +4 weeks;
  hard cap = 26 weeks).
- **Manage templates + sets** — a separate `Templates…` page reached
  from a button in the right column. Lists templates and sets, edit /
  delete / clone. Out of the planner's primary surface so it doesn't
  clutter.

---

## 6. Sequential builder (alt path for fresh-cookers)

Three-step modal, triggered from a small `Plan step-by-step` CTA in
the page header. Modal-only; doesn't replace the canvas.

1. **Pick meals** — recipe list (same shape as left column) with a
   selection counter (default target = user's `meals_per_week` if
   set, else 7).
2. **Required stock** — derived view of (recipe → ingredients), in-
   stock vs need-to-buy, item-by-item. User can deselect recipes
   here without going back a step.
3. **Build & finish** — single click writes the plan entries AND
   either generates a new shopping list or adds-to-existing (the
   same choice modal as the sidebar CTA in §3.3). Last screen offers
   **email** (existing email infra) and **print**
   (`useMealPlanExport.openPrintView`).

Cancel = no writes (nothing is committed before step 3).

---

## 7. Two-persona walk-through (batch vs fresh)

### Batch-cooker

- Opens Meal Plans → calendar widget shows their planned weeks.
- Cooks 8 servings of Lentil Dahl Sunday → `+8` from the recipe-list
  count menu.
- Taps a Tuesday Dinner slot, then taps `Lentil Dahl` in the left
  column → entry added with `servings=1`. Tap again → increments to
  2. (Drag works too on desktop.)
- Right column shopping summary recomputes; nothing to buy.
- Never opens the sequential builder.

### Fresh-cooker

- Opens Meal Plans → `Plan step-by-step`.
- Picks 5 recipes; sees "3 to buy"; clicks `Build & finish`; picks
  the primary list in the choice modal; optionally emails it.
- Closes the modal, goes shopping; opens cook mode each day via the
  per-entry `Cook now` menu.

Both flows live on the same page, neither in the other's way.

---

## 8. Wave A primitive reuse

- **A1 tokens** everywhere. Calendar widget + entry chip use
  `--brand-primary`, `--semantic-positive/warning`, `--text-muted`,
  `--surface-elevated`. No raw colour. **Sidebar `stockStatusColour`
  unifies with the rest of the app** (was using a one-off palette;
  the proposal lifts the stock-level → token mapping from the
  central `getStockLevelColour` helper that StockItem rows use).
- **A2 BaseButton** for every action.
- **A3 BaseDialog** for save-template, apply-template, the choice
  modal, sequential-builder steps.
- **A4 FilterBar** for the left-column filter strip.
- **A5 skeleton** for the carousel cells while a week's entries load.
- **A6 text scale** respected; calendar squares scale with `em`.

---

## 9. Ripple notes (not redesigned here)

- **C-1 Stock Overview:** the per-row "# recipes" chip should become
  **"# upcoming planned meals"** (feedback line 89). Drives the
  `cookable_count` server contract noted in `IMPL_PLAN_STATE_OWNERSHIP.md`.
- **C-3 Cook Mode:** the in-cook framing should read
  **"how many meals did you save?"** for batch-cookers (feedback line
  371). The planner side just keeps the existing `Cook now` entry-menu
  passthrough.
- **C-4 Cookbook:** the **Favourites** and **Haven't had in a while**
  trays should also exist on the cookbook (different metric — "last
  made"). Picture the same component, parameterised. Tag filters land
  in the left-column FilterBar when C-4 ships its tag overhaul.
- **C-7 Cart button:** the new per-item "add to a specific list"
  affordance in the sidebar shopping summary is a single use of the
  cart-button decision tree (C-7). Reuse, don't re-implement.
- **Dora assistant:** the brief mentions "I should be able to ask
  Dorabot to assist with meal planning. Examples: 'I want an Italian
  week', 'Tuesday should be healthy', 'low calorie plan'." These are
  Dora-tool prompts that should call `from-template` /
  `from-template/recurring` once a "plan synthesis" Dora skill exists.
  Out of scope here; logged for the SLM assistant work.
- **Dashboard (deferred):** "next up to cook" card (feedback line 272)
  would read `unallocated_meals` + nearest `scheduled_for`. Note,
  don't build.
- **Settings (deferred):** the slot-vocabulary page is the only new
  row; not a redesign.
- **Onboarding (C-5):** seed slot vocabulary.

---

## 10. Verification asks (per CLAUDE.md MANDATORY rule)

Three "static says fine" items the user should eyeball in browser
before they get marked done:

- **B6 allocation works end-to-end** ([FU-032](DORA_FOLLOWUPS.md)).
- **"Needs x" of a stock item in the shopping summary adds up
  correctly** for multi-recipe weeks where the same ingredient appears
  with different units / quantities. Quick math walk-through is in
  `get_meal_plan_ingredients` (scaling by `entry.servings /
  recipe.servings`). Will log as a new FU once approved.
- **Past-day drop** that 400s on the backend — the user gave us a
  concrete repro (Thu 8am AEST, dropped on Wed). Frontend
  `isPastDay` is the culprit (see §1 / §13). Will log as new FU; the
  fix specced below.

---

## 11. Smaller secondary open decisions

The big ones are locked in §2. Remaining smaller calls:

1. **Recurring window cap** — currently proposing 26 weeks. Pick a
   number.
2. **Number of trays max** — 2 (Favourites + Haven't-had-in-a-while)
   shipping, but the brief leaves room for "frequently-picked on
   plans" as a third future tray.
3. **Templates page route** — `/cookbook/templates` (under cookbook —
   they ARE recipe groupings), or `/meal-plans/templates` (under
   planner — that's where they're applied)? **Recommend
   `/meal-plans/templates`** because they live in the meal-plan
   mental model.
4. **Slot remap UI** — a one-shot "remap legacy entries to current
   vocabulary" button in settings; build now or defer?
5. **Set rotation start anchor** — when applying a set from
   `start_monday`, position 0 = the first week. Alternatively,
   "always start from position 0 of the set on the calendar-year
   start" gives a fixed cycle even if the user pauses. Default to
   apply-time anchor (simpler).

---

## 12. Sequencing (if approved)

| Phase | Reviewable chunk | Risk |
|---|---|---|
| C-2.A | **Slot vocabulary** (settings entry + tap-add slot derivation) | Low |
| C-2.B | **Page chrome cleanup** — drop "Suggest", "Edit entries", CSV, "Week of…" title, page-shortfall banner, "Active plan" dropdown; rename "Delete plan" → "Clear week"; swap icon; new entry-chip layout | Low (removals only) |
| C-2.C | **Vertical carousel + slot rows + cell-targeted tap-add**, drag-mouse-only | Med (interaction surface) |
| C-2.D | **Custom calendar widget + month banner + status underlines**; replaces active-plan dropdown | Med (new component, but no backend impact) |
| C-2.E | **Drop `MealPlan.name` from UI** + "Week starting X" label | Low |
| C-2.F | **Templates (single)**: save + apply-one-week + warning copy | Med (new entity + migration) |
| C-2.G | **Template sets + recurring + `source_template_*` provenance** | Med |
| C-2.H | **Sidebar redesign** — shopping list status per item, individual add, Add-to/Generate choice modal, hover-to-highlight | Med (composes C-7) |
| C-2.I | **Trays** (Favourites + Haven't had in a while) in left column | Low |
| C-2.J | **Sequential builder** modal | Low |
| C-2.K | **Past-day drop bug fix** — frontend uses backend-aligned local date | Low |

Each phase ships in isolation; the canvas keeps working through every
phase.

---

## 13. Concrete fixes folded in (cross-checked against feedback)

A flat checklist of every meal-plan feedback bullet and where the
proposal covers it.

| # | Feedback | Covered |
|---|---|---|
| F1 | Sequential builder (pick → stock → list → email/print) | §6 |
| F2 | Templates, rotating, auto-add tie-in | §5, §3.3 (Add to / Generate choice modal IS the auto-add tie-in) |
| F3 | Page icon (meals icon, not calendar) | §3.7 |
| F4 | Shortfall = chef's hat, not warning triangle | §3.3 |
| F5 | Allocation broken | §1 — already works; FU-032 confirms |
| F6 | "I'm a notification!" placeholder | B7 — already fixed |
| F7 | Full ingredient demand colour consistency | §8 (unifies with stock-level token mapping) |
| F8 | Drag/drop disabled on mobile | §3.1, §3.2 |
| F9 | Tap/click anywhere drag/drop exists | §3.1, §3.2 |
| F10 | Plan instance name useless | §3.5 — dropped |
| F11 | Date picker for new plan wrong | §3.4 — gone |
| F12 | Template management (save/create-from/toolbar button) | §5 + Manage page |
| F13 | Calendar widget design (month banner, DD only on first square, rounded squares, status underlines) | §3.3 |
| F14 | Widget right above shopping info | §3.3 layout |
| F15 | Current day marked | §3.3 (accent dot) |
| F16 | Vertical carousel (up/down arrows + smooth animation) | §3.2 |
| F17 | Calendar changes with carousel | §3.3 |
| F18 | Trays "Favourites" + "Haven't had in a while" + can drag | §3.1 (left column per Decision 5) |
| F19 | Reusable on cookbook (different metric) | §9 ripple |
| F20 | Main working area centring | §3 layout |
| F21 | All-recipes filterable, vertical, on left | §3.1 |
| F22 | Method to add without drag | §3.2 tap-add |
| F23 | Dora assistant: "Italian week", etc. | §9 ripple |
| F24 | Recurring; historical not stuffed; once week passes, read-only | Decision 1 + §1 backend rules |
| F25 | Recurring × editing coexistence | Decision 1 |
| F26 | Batch vs fresh personas | §7 |
| F27 | Meal cards don't fit | §3.2 entry-chip redesign |
| F28 | Refresh resumes on focused week | §3.2 (URL carries `monday=YYYY-MM-DD`) |
| F29 | Past-day drop 400 bug (Thu 8am, Wed) | §1, §10, §12 C-2.K |
| F30 | Hover stock item → highlight day cells | §3.3 |
| F31 | Shopping list status per stock item | §3.3 |
| F32 | Individual add | §3.3 |
| F33 | "Generate" → "Add or generate" / existing or new | §3.3 choice modal |
| F34 | "Needs x" math correctness | §10 verification ask |
| F35 | Slot always "Dinner" bug | §3.2 (auto-derives from cell) |
| F36 | "Edit entries" button shows gap | §3.6 removed |
| F37 | "Delete plan" → "Clear week" | §3.5 |
| F38 | Theme-aware page elements | §8 (A1) |
| F39 | Remove CSV button | §3.6 |
| F40 | Remove "Week of…" title | §3.6 |
| F41 | Colour/icon overload | §3.2 entry chip + §8 token unification |
| F42 | On-hand display in palette better | §3.1 row chip + §3.2 entry pill |
| F43 | Drop "cookable now" cues / "Suggest meals" CTA | Decision 7, §3.6 |
| F44 | Page concern: squishing horizontally | Resolved by Decisions 5 + 7 keeping the right column light; carousel breathes more |
| F45 | Shortfall banner redundant | Decision 3 + §3.3 sidebar line |
| F46 | Time of day as rows | §3.2 |
| F47 | Same recipe same slot → increment | §3.2 |
| F48 | Don't drag one by one | §3.2 + per-entry `Servings: ±n` |
| F49 | Slots configurable + defaults | §4 |
