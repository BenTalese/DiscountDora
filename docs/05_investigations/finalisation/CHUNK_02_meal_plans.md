# Chunk 02 — Meal Plans

**Analysed:** 2026-10-23 · **Analyst session:** finalisation overnight run (single session, no sub-agents)
**Scope (from PLAN §4):** board / calendar / templates / template sets, meal slots, pool decrement + shortfall, planned demand, meal reconcile (runner, log, auto mode), rail suggestions, rail + shopping summary + cost, auto builder / budget cap / lighter swaps / budget-defence swaps.
**Boundaries:** recipes → Chunk 1; shopping-list side of "start a list from a plan" → Chunk 3; `AdminSystemMealReconcileSettings.vue`, `RecipeMealSlotsSettings.vue` → Chunk 13; dashboard "next to cook" → Chunk 8; daily-brief *delivery* (`alerts/send_daily_brief.py`) → Chunk 9; `StocktakeRunner.vue` (shares the runner shell) → Chunk 5.

## 0. Reading list + files walked

**Planning docs consulted:** `PROPOSAL_MEAL_PLANS.md`, `PROPOSAL_MEAL_PLANS_PART_2.md` (§1–§16), `IMPL_PLAN_MEAL_PLANS_REBUILD.md`, `BRIEF_MEAL_PLANNER_RAIL_AND_SHELL.md` (§0–§10), `PROPOSAL_MEAL_RECONCILE.md` / `IMPL_PLAN_MEAL_RECONCILE.md` (via FU-317 chunk citations), `PROPOSAL_BUDGET_DEFENSE_SWAPS.md`, `MAGIC_BEHAVIOUR_AUDIT.md` F5/F18, feedback `# MEAL PLANS` (61 bullets), open FUs: FU-920, 908, 907, 898, 879, 863, 862, 851, 849, 802, 757, 682, 654, 630, 759, 624, 675, 674.

**Files walked (every file opened, with line count):**

| File | Lines | Role |
|---|---|---|
| `dora_api/features/meal_plans/get_meal_plans.py` | 778 | DTOs + six hydrations |
| `dora_api/features/meal_plans/update_meal_plan.py` | 285 | PATCH (match-and-update) |
| `dora_api/features/meal_plans/create_meal_plan.py` | 176 | POST |
| `dora_api/features/meal_plans/delete_meal_plan.py` | 44 | DELETE |
| `dora_api/features/meal_plans/get_today.py` | 21 | household today |
| `dora_api/features/meal_plans/get_shortfall.py` | 63 | shortfall report |
| `dora_api/features/meal_plans/cook_batch_grouping.py` | 59 | cook_key grouping + validation |
| `dora_api/features/meal_plans/build_week.py` | 781 | auto builder + rail suggestions |
| `dora_api/features/meal_plans/reconcile.py` | 806 | reconcile queue/log + verbs |
| `dora_api/features/meal_plans/reconcile_consumed_meals.py` | 163 | daily sweep |
| `dora_api/features/meal_plans/planned_meals.py` | 262 | pool allocation model |
| `dora_api/features/meal_plans/daily_brief.py` | 217 | brief content |
| `dora_api/features/meal_plans/get_meal_plan_ingredients.py` | 313 | aggregate + preview |
| `dora_api/features/meal_plans/swap_suggestions.py` | 693 | budget + lighter swaps, apply/undo |
| `dora_api/features/meal_plan_templates/manage_templates.py` | 596 | templates CRUD + apply + recurring |
| `dora_api/features/meal_plan_template_sets/manage_sets.py` | 306 | sets CRUD |
| `dora_api/features/meal_slots/manage_meal_slots.py`, `slot_validation.py` | 301 | slot vocab |
| `dora_api/domain/entities/{meal_plan,meal_plan_entry,cook_batch,meal_plan_reconcile_receipt,meal_plan_swap_ledger,meal_plan_template}.py` | 278 | entities |
| `web_app/src/pages/MealPlansOverview.vue` | 1338 | planner page |
| `web_app/src/pages/MealPlanTemplatesPage.vue` | 355 | templates + sets management |
| `web_app/src/pages/MealReconcileRunner.vue`, `MealReconcileLog.vue`, `MealReconcilePage.vue` | 801 | reconcile surfaces |
| `web_app/src/composables/useMealPlanner.ts` | 1239 | planner core |
| `web_app/src/composables/{useReconcileQueue,useReconcilePolicy,usePlannedDemand,useMealPlanExport}.ts` | ~330 | composables |
| `web_app/src/components/MealPlanBuilderDialog.vue` | 1143 | auto builder |
| `web_app/src/components/{MealPlanWeekDayCard,MealPlanRichCard,MealPlanEntryChip,MealPlanEntryMenu,MealPlanMobileFocus}.vue` | 2089 | week + meal cards |
| `web_app/src/components/{MealPlanRecipePicker,MealPlanRecipeRow,MealPlanPickerSheet,MealPlanRailFilterChips,MealPlanRailDisclosure,MealPlanRailCount}.vue` | 1305 | the rail |
| `web_app/src/components/{MealPlanShoppingSummary,MealPlanIngredientRow,MealPlanCalendar,MealPlanDayPips,MealPlanApplyTemplateDialog,MealPlanLighterDialog,MealPlanFirstRun,MealPlanSkeleton}.vue` | 1821 | right pane, calendar, dialogs |
| `web_app/src/helpers/{recipeRailFilters,weekDates,mealPlanDayPips,mealPlanEntryStatus,mealPlanEntryKey,mealPlanSuggestionCopy}.ts` | ~570 | helpers |
| `web_app/src/stores/{mealPlanStore,mealPlanTemplateStore,mealPlanTemplateSetStore,mealSlotStore}.ts` | 293 | stores |
| `web_app/src/services/api/mealPlanApiService.ts` | 300 | API client + types |
| Tests inventoried: `tests/test_build_week.py` (330), `test_planned_demand.py` (274), `test_trim_to_budget.py` (323), `test_lighter_swaps.py` (134), `test_meal_plan_ingredient_aggregate.py` (155), `test_swap_suggestions.py` (176); e2e `test_meal_plan_router.py`, `test_meal_plan_template_router.py`, `test_meal_plan_template_set_router.py`, `test_meal_slot_router.py`, `test_cook_batches.py`, `test_meal_plan_cost.py`, `test_meal_plan_nutrition.py`, `test_meal_plan_preview.py`, `test_meal_plan_today.py`, `test_reconcile_receipts.py`, `test_reconcile_signal.py`, `test_reconcile_verbs.py`, `test_planned_demand_endpoint.py`, `test_lighter_alternatives.py`, `test_recipe_is_planned.py`, `test_budget_router.py`; vitest `mealPlanDayPips/EntryKey/EntryStatus.spec.ts`, `recipeRailFilters.spec.ts`, `useMealPlanExport.spec.ts`, `weekDates.spec.ts` | | |

## A. Full Systems Test — Meal Plans

### A1. Preconditions
- Seeded install with ≥ 20 recipes (some favourites, some never cooked, some with expiring stock) and the household meal slots at their defaults.
- Run twice: **cook-style Fresh** (default) and **cook-style Batch** (`/settings/admin/system/cooking`), because the pool, cook batches, fresh marks, the chef-hat/fridge glyphs and the shortfall all exist only in Batch.
- Money on for the cost/budget rows; nutrition complex for the lighter-swap menu item.

### A2. Golden path
Persona: **Dense user (Batch household)**, desktop then phone.
1. Open `/meal-plans` → skeleton, then the three-pane shell: collapsed "Recipes" strip · week toolbar + seven day cards (past days folded when the week contains today) · calendar + "Missing this week"/"All ingredients".
2. Click a slot row on Wednesday → the card takes an accent border, the slot says "← pick a recipe", the rail opens and focus lands in its search → click a recipe → "Added to plan" toast, chip appears with ×1, rail stays open.
3. Click the same recipe again on the same slot → servings increment, no duplicate chip.
4. Open the chip menu → Servings stepper (menu stays open across taps); type a number; View recipe; Cook now (guard dialog if not cookable, lands in cook mode at the batch yield).
5. Menu → "Cook once for more days…" → tick Thu + Fri → one chip reads "Cook day · 9 servings", the others "Leftovers"; calendar pips update; "Change cook days…" un-ticking Friday removes Friday's meal; "Separate this cook" leaves three standalone meals.
6. Menu → "Cook fresh on the day" on a standalone meal → Fresh chip, no fridge glyph; toggle back.
7. Right rail → "Missing this week" shows low/out badges → "Add N to a list" → shared picker → confirm → counts drop to "all on a list"; hover an ingredient → the meals using it highlight.
8. Toolbar → All slots toggle (remembered per device); ← → weeks (URL `?week=` follows, ↑/↓ keys, swipe on phone); calendar day click scrolls the week pane to that card with a one-shot settle.
9. Build my week → Setup (days / meals / same-every-day / emphasis / servings seeded from household headcount / budget cap when money on) → Review (reshuffle changes the set, swap by clicking a name, add a meal, "What you'll need" with low·out counts and the two money figures) → Save plan → Done → "Add to a shopping list".
10. Week menu → Save week as template → Templates page → rename inline, build a rotating set → back on the planner → Apply template → pick the set → range → "Planned N weeks".
11. Duplicate to next week → confirm → focused week moves to next week with the copies.
12. Clear week → confirm → plan deleted, rail resets.
13. Move the clock past a planned day (or use a seeded past plan): **Auto** mode → `/meal-plans/reconcile` shows the Meal log; **Manual** mode → the runner: Cooked / Different portions / Cooked later / Didn't cook / Skip, pool moves per verb, the nudge above the planner counts down.
14. Over budget (money on, small budget) → the swap panel appears above the week cards on both breakpoints; apply a swap; undo it.
15. Phone (375): day strip with pips, slot-grouped cards, "Build my week" + "Apply template" side by side, week menu with all six actions, the shopping summary below.

### A3. Edge cases
- Pick a recipe with no slot armed → nothing happens, no toast (owner 09-01).
- Past day slot → "Past days are read-only"; past entries are never resent on PATCH (FU-595).
- Deleting a meal slot in Settings → existing entries keep the label under "Other"; the plan still saves (slot validation allows stored labels).
- A one-day "batch" → client dissolves the orphan `cook_key` so the server never 400s.
- Cook-batch straddling today → the preserved batch is reused, no phantom second cook (09-03).
- Templates: applying skips past days and reports it; a set with a deleted template renders "(deleted template)".
- Reconcile: same verb twice is a 200 no-op; Skip is pool-neutral; `cook_fresh` entries are pool-neutral under every verb; 61st verb in a minute → 429 with Retry-After.
- Timezone: household timezone ≠ browser → "today" comes from the server; the first paint may use the browser's day and then flip.
- Negative-UTC-offset device (America/*) → **see 02-R34**: the phone day strip's date numbers are off by one until fixed.
- Money off → no cost chips, no budget line, builder has no cap toggle, server sends no figures.
- Fresh household → no pool controls on rail rows, no fridge glyphs, no batch menu items, builder spans 1.

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (first-run card → Cookbook) | ✓ | ✓ (fresh style, money off) | ✓ (batch + money + nutrition, keyboard nav) | ✓ (cook style / reconcile mode / slots are install-wide) | ✓ (one shared plan per week — see 02-D3) | – | – |

### A5. Load-bearing conditions
- **360×640 / phone**: the entire mobile branch is a separate component tree (`MealPlanMobileFocus`), so every flow above must be walked twice.
- **1024–1180px**: toolbar compacts labels; rail 340px + context 300px leave the week pane narrow — check nothing wraps to a third line (§3.2 acceptance).
- **Reduced motion**: week carousel and calendar paging drop their transitions; the settle pulse must not loop.
- **Themes × dark**: the lit slot (`--q-primary` 14 % mix), focused day chip (`white` text — 02-R37), leftover grey trim, warning glyph ink; pesto dark had invisible low-alpha washes elsewhere (09-08).
- **Offline**: read-only; every mutation toasts "Could not update the plan." and leaves the week as fetched.

### A6. Release-gate rows
- Batch household: plan a 3-day cook, reconcile its cook day as "Didn't cook" in manual mode, and confirm the pool, the chef-hat glyphs and the shortfall all agree.
- Build my week with budget cap on a week projected over budget → the review step's two money figures match the planner's "Cost this week" after save.
- Apply a rotating set over 4 weeks across a month boundary; calendar follows; each week's provenance (`source_template_set_id`, `rotation_index`) is set.
- Phone: add → link cook days → add to list → reconcile, all from the mobile tree.

## B. Help content — Meal Plans

### B1. Current help audit
- `HelpPage.vue` GUIDES has one entry for this whole surface — *Build a meal plan* under "Recipes & meals": "Group recipes into meals (e.g. roast + sides). Then schedule meals onto a meal plan; the dashboard shows the next entry on the home page." This describes a model that **no longer exists** (there are no "meals" grouping recipes; the planner is a week of slot rows). Stale and misleading.
- The reconcile **runner** and **log** each open a `(?)` modal (`MealReconcileRunner.vue:210–240`, `MealReconcileLog.vue:536–563`) holding the only real help text for reconcile. Owner directive 2026-08-27: *"Info button should take you to help and guides, not open a modal"* — the stocktake runner was converted; these two were not (02-R40).
- `app_knowledge.py` `APP_OVERVIEW` "Meal Plans" paragraph (L25–30) is half-right: it mentions pool decrement on past days and the shortfall, but not cook batches, fresh meals, the auto builder, templates/sets, reconcile modes, the rail's suggestions, cost/budget, or lighter swaps.
- Good inline help that already exists and should be *linked from* guides rather than repeated: the builder's emphasis/servings/budget captions, the apply-template explainer, the `InfoTip` on cookable-now (cookbook).

### B2. Help entries (one per feature / auto-behaviour)

#### Plan a week
- **Group:** Meal plans (new group; move *Build a meal plan* out of "Recipes & meals" and delete it)
- **What it does:** A plan is one week, Monday to Sunday, with the household's meal slots on each day. Tap a slot, then a recipe in the rail (or the picker on a phone) to put it there; tap the same recipe again to add a serving.
- **When it fires / how to trigger it:** `/meal-plans`. The first add to an unplanned week creates the plan; past days are read-only.
- **What controls it:** Slots: `/settings/kitchen-setup/meal-slots`. "All slots" toggle on the toolbar shows empty slots too (remembered per device).
- **What it costs / might get wrong:** Deleting a slot keeps meals already planned under it (they show under "Other"). The week shown on arrival is the household's current week (server timezone).
- **Related:** Build my week · Cook once for several days · Reconcile past meals
- **Chip:** `MealPlansOverview.vue:187` beside the "Recipes" rail heading → `<HelpHint topic="Plan a week">`.
- **Source:** `useMealPlanner.ts`, `update_meal_plan.py`.

#### Build my week
- **Group:** Meal plans
- **What it does:** Dora proposes a week from light guidance — which days, which meals, an emphasis (use up stock / variety / favourites / surprise), servings per meal, and optionally "keep under budget". You edit the proposal (swap, move, re-serve, remove, add) before saving.
- **When it fires / how to trigger it:** Toolbar → Build my week (both breakpoints). Reshuffle picks again from the near-best candidates.
- **What controls it:** Servings seed from `/settings/admin/system/cooking` (people you cook for); the budget cap exists only with money on (`/settings/admin/system/money`); in a Batch household the builder proposes cook batches of up to three days.
- **What it costs / might get wrong:** Each meal uses a distinct recipe, so a small cookbook leaves days empty — the review step says how many. "Under budget" counts the **full cost of the meals**, pantry or not; the to-buy figure is shown beside it. Recipes already planned that week are never proposed.
- **Related:** Plan a week · What a recipe costs (Cookbook)
- **Chip:** `MealPlanBuilderDialog.vue:30` (Setup caption) → HelpHint.
- **Source:** `build_week.py`, FU-596/FU-611/FU-907.

#### Dora suggests (the rail)
- **Group:** Meal plans
- **What it does:** The "Dora suggests" chip ranks your cookbook for the week you're looking at — expiring stock, cookable now, not had lately, favourites — and says why beside each row. The other chips are plain filters (All · Cookable now · Favourites · Not lately · Regulars); search and the time-of-day/difficulty fields narrow whatever the chip produced.
- **What controls it:** Always on. The ranking is the same engine as Build my week's "use up stock" emphasis.
- **What it costs / might get wrong:** It excludes recipes already planned that week; it is recomputed per week.
- **Source:** `build_week.week_suggestions`, `recipeRailFilters.ts`.

#### Cook once for several days (cook batches)
- **Group:** Meal plans (Batch households)
- **What it does:** Link the same recipe across several days in one slot: the earliest day is the **cook day** and carries the whole yield ("Cook day · 9 servings"); the later days are **leftovers** and never need cooking. Cost is counted once, on the cook day.
- **When it fires / how to trigger it:** A meal's menu → "Cook once for more days…" (tick the days) · "Change cook days…" · "Separate this cook".
- **What controls it:** Only with cook-style **Batch** (`/settings/admin/system/cooking`).
- **What it costs / might get wrong:** Un-ticking a day in "Change cook days" removes that day's meal; "Separate" keeps every day as its own meal. A batch and a fresh mark can't be combined. Duplicating a week currently loses the links (02-R2 — fixed in Stage 2).
- **Related:** Meals prepared (Cookbook) · Reconcile past meals
- **Chip:** on the `MealPlanEntryMenu` link item? No — menu items don't carry chips; place on the `MealPlanShoppingSummary`? No. Place in the help page only, linked from "Plan a week".
- **Source:** PROPOSAL_MEAL_PLANS_PART_2, `cook_batch_grouping.py`, `planned_meals.allocate_pool`.

#### Cooked fresh on the day
- **Group:** Meal plans (Batch households)
- **What it does:** Marks a meal as cooked on its day, outside the pool of cooked servings: it never takes a ready serving and never asks you to batch-cook one. Shows a "Fresh" chip.
- **When it fires / how to trigger it:** A meal's menu → "Cook fresh on the day" (Batch only).
- **What it costs / might get wrong:** Reconciling a fresh meal never touches the pool.
- **Source:** `MealPlanEntry.cook_fresh`, owner 2026-09-04.

#### What the meal glyphs mean
- **Group:** Meal plans
- **What it does:** Each planned meal carries up to two glyphs: the **chef hat** (can you make it — green yes, amber missing ingredients) and the **fridge** (is a cooked serving ready — green yes, amber still to cook; Batch only). The card's left edge rolls them up: green fine, amber needs you, grey nothing to do (leftovers, cooked). Dora's voice glyph is a hunch about stock, never a verdict.
- **What controls it:** Cookability from your stock levels; readiness from the cooked pool; both server-decided.
- **Related:** Can I cook this? (Cookbook) · The "Dora thinks…" hint (Stock)
- **Source:** `helpers/mealPlanEntryStatus.ts`, owner assessment 2026-09-12.

#### Templates and rotating sets
- **Group:** Meal plans
- **What it does:** Save a planned week as a template (meals by weekday and slot); apply it to the week you're viewing or across a run of weeks (up to 26). A rotating **set** is an ordered list of templates applied week-by-week in turn.
- **When it fires / how to trigger it:** Week menu → Save week as template; toolbar → Apply template; manage (rename, delete, build sets) at `/meal-plans/templates`.
- **What it costs / might get wrong:** Applying replaces the week's future meals (it asks first) and skips past days. Editing or deleting a template never changes weeks already planned from it. Templates don't carry cook batches (02-D1).
- **Source:** `manage_templates.py`, `manage_sets.py`, Decision 1/2.

#### Reconcile past meals
- **Group:** Meal plans
- **What it does:** When a planned day passes, Dora records what happened to each meal. In **auto** mode (default) she assumes you cooked it, takes the servings from the pool and writes it to the **Meal log** — you can correct any row. In **manual** mode nothing moves until you confirm each meal in the runner: Cooked · Different portions · Cooked later · Didn't cook · Skip for now.
- **When it fires / how to trigger it:** The daily sweep (overnight, household timezone); `/meal-plans/reconcile`; the nudge above the planner and the dashboard chip count what's pending (manual mode only).
- **What controls it:** `/settings/admin/system/meal-reconciliation` (auto vs manual).
- **What it costs / might get wrong:** Every decision is a new receipt — nothing is overwritten, and "Skip" changes nothing. Three or more unresolved meals four days old raise an alert.
- **Related:** Meals prepared (Cookbook) · Alerts
- **Chip:** replaces the runner's and log's `(?)` modals (`MealReconcileRunner.vue:29–35`, `MealReconcileLog.vue:457–463`) with `<HelpHint topic="Reconcile past meals">` (02-R40).
- **Source:** `reconcile_consumed_meals.py`, `reconcile.py`, MAGIC F5.

#### Missing this week and the shopping hand-off
- **Group:** Meal plans
- **What it does:** The right rail (or the card under the phone's week) totals the week's ingredients at the planned servings, splits them into out / low / stocked, lists free-text ingredients that can't be shopped for, and hands the missing ones to the same add-to-list picker the recipe page uses. Hovering an ingredient highlights the meals that need it.
- **What controls it:** Always on. "Already on a list" comes from your open lists.
- **What it costs / might get wrong:** Quantities are summed per stock item across recipes with the same unit; different units aren't converted here.
- **Source:** `get_meal_plan_ingredients.py`, `MealPlanShoppingSummary.vue`.

#### Cost this week and the budget
- **Group:** Meal plans (money)
- **What it does:** Each meal's price chip is its recipe's per-serving estimate × servings (a cook day prices the whole cook); the week's total sits under the rail with its coverage; the budget line compares the week against what is left of the household budget period the week falls in. When the week is projected over budget, Dora offers cheaper recipe swaps with undo.
- **What controls it:** `/settings/admin/system/money` + `/settings/budget`.
- **What it costs / might get wrong:** Estimates follow the recipe cost rules (see Cookbook). Swaps only ever suggest recipes you can cook now, that are similar, or that you've cooked before.
- **Source:** `get_meal_plans._hydrate_cost`, `swap_suggestions.py`, FU-451.

#### Find a lighter option
- **Group:** Meal plans (nutrition)
- **What it does:** From a meal's menu, lists recipes with fewer kcal per serving than it, with the saving and why it's plausible. Never volunteered — Dora holds no calorie target.
- **What controls it:** Nutrition mode on and a reliable figure for the meal (`/settings/admin/system/nutrition`).
- **Source:** FU-637, `rank_lighter_swaps`.

#### Tomorrow at a glance (the daily brief)
- **Group:** Meal plans / Alerts
- **What it does:** One evening notification naming tomorrow's planned meals in slot order (or "Nothing planned for tomorrow yet" when the week has meals elsewhere), plus any shopping day due. Silent when it has nothing to say.
- **What controls it:** Push + the brief hour under `/settings/notifications` (verify in Chunk 9).
- **Source:** `daily_brief.py`.

### B3. DoraBot corpus delta
Replace `app_knowledge.py` L25–30 with:
```
- Meal Plans: a week at a time, Monday to Sunday, with the household's meal
  slots on each day. Tap a slot then a recipe to plan it, or let "Build my
  week" propose a week (use up stock, variety, favourites, surprise; servings
  per meal; optionally keep under budget) and edit it before saving. Batch
  households can link one cook across several days (cook day + leftovers),
  mark a meal as cooked fresh, and see which meals still need cooking from
  the cooked-servings pool. Weeks can be saved as templates and re-applied,
  singly or as a rotating set across weeks. As days pass Dora records what
  happened to each meal (auto: assumed cooked and logged; manual: confirmed
  one by one). The right rail totals the week's ingredients, shows what's
  missing, and hands them to a shopping list; with money on it shows the
  week's cost against the budget and offers cheaper swaps.
```

## C. Senior review — Meal Plans

### C1. Bugs (verified or high-confidence latent)

- **02-R1** · latent, medium-high · `dora_api/features/meal_plans/reconcile_consumed_meals.py:157` · the daily sweep inserts `MealPlanReconcileReceipt.id` as `str(uuid.uuid4())` through raw `text()`, while `reconcile.py:748` inserts the same column as `_id_bytes(...)` (16 raw bytes on SQLite). On SQLite the receipt table therefore holds a **mix of TEXT and BLOB ids** in a `UUIDType` BINARY(16) column. Nothing reads receipts through the ORM today (grep `get(MealPlanReconcileReceipt)` → none), which is the only reason it is latent; the `ORDER BY created_at DESC, id DESC` tie-break (FU-529) also compares TEXT against BLOB, which SQLite orders by storage class rather than value. · **Exact change:** bind the id the same way the verb path does — the shared UUID bind helper from 01-R8 (`persistence/uuid_key.py` gains `uuid_bind(value, dialect_name)`), passing `dialect_name=_Conn.dialect.name` in `_insert_receipt` for both `id` and `entry_id`. Add `test__sweep_receipt_ids__round_trip_through_orm` (load receipts via `repository.get(MealPlanReconcileReceipt).all()` after a sweep). · S · guard: `test_reconcile_receipts.py`, `test_reconcile_verbs.py` · **execute**.
- **02-R2** · latent, high-confidence · `web_app/src/composables/useMealPlanner.ts:1059–1068` `nextWeekCommands` maps only `recipe_id/scheduled_for/servings/slot`, dropping `cook_key` and `cook_fresh`; "Duplicate to next week" turns a cook batch into N standalone meals and un-marks fresh meals, silently. · **Exact change:** build from `toCommand(e)` (drop `meal_plan_entry_id`, shift `scheduled_for` by 7). · S · guard: add a vitest once the mapping is a pure helper (§D) · **execute**.
- **02-R3** · bug (locale) · `web_app/src/components/MealPlanBuilderDialog.vue:696–698` `money(n) = `$${n.toFixed(2)}`` hard-codes the dollar sign and two decimals, bypassing `formatMoney` (R-056; FU-043). · **Exact change:** `import { formatMoney } from 'src/composables/useMoney'`; delete `money`; replace the three call sites (L273, L344, L347). · S · **execute**.
- **02-R34** · bug (R-021, negative-UTC-offset devices) · `web_app/src/components/MealPlanMobileFocus.vue:387` `dayOfMonth(iso) { return new Date(iso).getDate(); }` — a date-only ISO parses as UTC midnight, so west of Greenwich the phone's day strip shows yesterday's number under every chip. `helpers/weekDates.ts:40–47` documents this exact trap and ships `parseLocalIso`. · **Exact change:** `Number(iso.slice(8, 10))` (the calendar already does this at `MealPlanCalendar.vue:861`). · S · guard: `weekDates.spec.ts` style unit test · **execute**.
- **02-R35** · bug (R-021) · `web_app/src/pages/MealReconcileRunner.vue:304` `todayIso = new Date().toISOString().slice(0, 10)` — UTC "today", used as the `:max` of the "Cooked later" date input; east of UTC in the evening it is yesterday, so today's date is un-pickable. · **Exact change:** read `mealPlanStore.today` (server household date) with `localTodayIso()` as the pre-load fallback, as the planner does. · S · **execute**.
- **02-R36** · R-045 violation (the exact signal FU-682 names) · `web_app/src/composables/useMealPlanExport.ts:762–764` `window.open(`${baseUrl}/meal-plans/${id}/print-view`)` — the same unauthenticated-navigation defect `useRecipeExport.openPrintView` was fixed for (Capacitor shell / cross-site SPA → 401 in a new tab). · **Exact change:** mirror `useRecipeExport.openPrintView`: `void openHtmlDocumentAsync(`/meal-plans/${id}/print-view`, 'Meal plan').catch(...)`, sync entry (R-046). Update `useMealPlanExport.spec.ts`. · S · **execute** (tracked FU-682 — this is one of its three).

### C2. Redundancy / DRY (R-001, R-003)

- **02-R4** · `get_meal_plans.py` `_hydrate_nutrition` (L385–390), `_hydrate_cost` (L475–480), `_hydrate_inference` (L590–596) each re-load the plan's distinct recipes with ingredients; `_hydrate_cookability` (L734) loads the whole cookbook again. Tracked **FU-879** (two loads) — it is three plus one. · **Exact change:** a per-call `_recipes_with_ingredients(recipe_ids)` memo on the handler (`include(STOCK_ITEM).then_include(STOCK_LEVEL)` once), consumed by all three; cookability from the same entities via `missing_count_for(r.ingredients, resolve_levels_by_item(...))`. · M · guard: `test_meal_plan_router.py`, `test_meal_plan_nutrition.py`, `test_meal_plan_cost.py` · **execute** (closes FU-879; part of FU-908).
- **02-R5** · `get_meal_plans.py:168–204` `_CostIngredient`/`_CostInput` adapt entities for `estimate_costs_for`; `recipe_rollup.input_from_entity` already produces a shape the pricing ladder duck-types. · **Exact change:** delete the two dataclasses; `estimate_costs_for(self.repository, [input_from_entity(r) for r in recipes])`. · S · guard: `test_meal_plan_cost.py` · **execute**.
- **02-R6** · `get_meal_plans.py:315–351` `_hydrate_entry_has_image` duplicates `get_recipes._hydrate_has_image`. · **Exact change:** `features/recipes/image_flags.py::recipe_ids_with_image(ids) -> set[UUID]`; both call it. · S · **execute** (pairs with Chunk 1).
- **02-R7** · `create_meal_plan.py:66–132` and `update_meal_plan.py:66–248` repeat: slot validation, `validate_cook_groups`, past-date guard, recipe-resolution loop, `CookBatch` minting, `MealPlanEntry(...)` construction, and the error→HTTP chain. · **Exact change:** `meal_plans/_entry_writes.py` with `resolve_recipes(repository, reqs) -> (by_id, missing)`, `has_past_entry(reqs, today)`, `mint_batches(repository, plan_id, reqs, preserved_by_key=None)`, `new_entry(req, recipe, batch)`, `meal_plan_write_error_response(response, request)`; both handlers shrink to orchestration. · M · guard: `test_meal_plan_router.py`, `test_cook_batches.py` · **execute**.
- **02-R8** · `CreateMealPlanEntryRequest` vs `UpdateMealPlanEntryRequest` differ only by `meal_plan_entry_id`. · **Exact change:** `MealPlanEntryRequest` base in `_entry_writes.py`. · S · **execute**.
- **02-R9** · `reconcile.py` carries the latest-receipt `NOT EXISTS (… r2.created_at > r.created_at OR (… AND r2.id > r.id))` predicate **five times** (L239–255, L325–345, L366–380, L400–418, L434–446). · **Exact change:** constants `_LATEST_RECEIPT_FILTER`, `_ENTRY_RECEIPT_SELECT`; one `_receipt_rows(today, *, pending_states, cursor, limit, newest_first)` + `_receipt_count(today, pending_states=None)`; the four fetch/count functions become one-liners; `reconcile_overdue_signal` reuses the filter. · M · guard: `test_reconcile_receipts.py`, `test_reconcile_verbs.py`, `test_reconcile_signal.py` · **execute**.
- **02-R10** · `reconcile.py:523–536` `_id_bytes` and `:300–305` `_stringify_entry_id` duplicate `pool.bump_pool`'s bind normaliser and `recipe_cost._key`. · Folded into **01-R8**. · **execute**.
- **02-R11** · `_too_many_requests(retry_after)` × 5 — `reconcile.py:159`, `assistant/ask_assistant.py:72`, `auth/bootstrap_admin.py:73`, `auth/email_flows.py:47`, `auth/register_user.py:351`. · **Exact change:** `api_response.too_many_requests(retry_after)`; delete the five. · S · guard: `test_auth_flows.py`, `test_reconcile_verbs.py`, assistant rate-limit tests · **execute** (owned here; Chunks 15/11 tick their call sites).
- **02-R12** · `_current_user_id()` × 15 modules. Tracked **FU-654**. · **Exact change:** `infrastructure/auth_helpers.current_user_id()`; sweep. · S · **execute (FU-654)**.
- **02-R13** · hand-rolled install-wide money/budget reads: `build_week.py:438–473`, `swap_suggestions.py:637–640, 698–708` (`repository.get(AppSetting).all()[0]`) while `app_settings/access.py` exports `money_features_enabled`/`get_or_create_app_setting`. Tracked **FU-759**. · **Exact change:** `features/budget/budget.py::household_budget(repository) -> HouseholdBudget(amount, period)` + `budget_remaining(repository, today)`; both modules use them. · S · guard: `test_build_week.py`, `test_swap_suggestions.py`, `test_budget_router.py` · **execute**.
- **02-R14** · `_all_recipe_dtos(repository)` duplicated in `build_week.py:512` and `swap_suggestions.py:651`. · **Exact change:** one `features/recipes/all_recipes.load_all_recipe_dtos(repository)` (see 02-R29). · S · **execute**.
- **02-R15** · `build_week.compute_auto_build:577` calls `GetMealSlotsHandler.handle()` for slot *names*, which loads every MealPlanEntry and Recipe (02-R30). · **Exact change:** `slot_validation.ordered_slot_names(repository)`. · S · **execute**.
- **02-R16** · `useMealPlanner.ts:159–161` and `MealPlanRecipePicker.vue:297–299` repeat the `mealSlotNames.length ? … : [...DEFAULT_MEAL_SLOTS]` fallback (copies 3 and 4 of 01-R15); `MealPlanRecipePicker.vue:300` `[...DIFFICULTY_VALUES]` is copy 3 of 01-R16. · Folded into **01-R15 / 01-R16**. · **execute**.
- **02-R17** · `MealPlansOverview.vue` renders `MealPlanShoppingSummary` twice (L107–120, L541–556) with the same twelve props. · **Exact change:** `shoppingSummaryProps` computed + `v-bind`. · S · **execute**.
- **02-R18** · the same eight `entry-*` handlers are wired at `MealPlansOverview.vue:56–72` (mobile) and `:498–506` (week card), and each of `MealPlanWeekDayCard.vue:85–92, 115–122`, `MealPlanMobileFocus.vue:745–752`, `MealPlanEntryChip.vue:111–118`, `MealPlanRichCard.vue:544–551` re-emits them again (six copies of the same eight lines). · **Exact change:** page: `const entryHandlers = {...}` + `v-on="entryHandlers"`; cards: forward the menu with `v-on="$attrs"`-style passthrough or an `entryListeners(entry)` helper returning the object. · S · **execute** (with 02-R17 and 02-R19b).
- **02-R19b** · `MealPlanRichCard.vue` (phone) and `MealPlanEntryChip.vue` (desktop) scripts are ~90 % identical: `inferenceTooltip`, `linked`, `fresh`, `cookMarkerLabel`, `status`, `priceLabel`, `accessibleLabel`, plus the same glyph run in both templates (chip L60–102, card L490–527). · **Exact change:** `composables/useMealEntryPresentation.ts` (`entry, shortfall` → those seven computeds) and a `MealEntryGlyphs.vue` for the Dora-hunch/price/check/chef-hat/fridge run; both hosts keep only layout. · M · guard: `mealPlanEntryStatus.spec.ts` + a new spec for the composable · **execute**.

### C3. Dead code / unused fields / unread endpoints

- **02-R19** · `useMealPlanner.ts` returns **13 members nothing reads** (grep `planner.<name>` → 0 each): `dayCost` (L182–186), `cookByLabel` (207–213), `freshEntries` (204–206), `needsCookingEntries` (197–199), `needToBuyOnList` (729–731), `slideDir`, `prefersReducedMotion`, `recurringSourceOptions` (internal), `slotNameSet` (internal), `mealPlans`, `today`, `suggestionsLoading`, `onKeydown`. · **Exact change:** delete the first five outright; drop the other eight from the return object. · S · guard: vue-tsc · **execute**.
- **02-R20** · `MealPlansOverview.vue:1295–1307` `.planner-toolbar__statusrow` / `.planner-toolbar__status` — status row deleted 2026-09-12. · **Exact change:** delete both rules. · S · **execute**.
- **02-R21** · `mealPlanStore.getShortfallAsync` + `shortfall` ref (L54–89), `mealPlanApiService.getShortfallAsync` (L66–67), `models/mealPlan.ts:158` `Shortfall` type — no client consumer (**FU-862**). · **Exact change:** delete all three (endpoint stays for the assistant). · S · **execute (FU-862)**.
- **02-R22** · `MealPlan.name` / `MealPlanDto.name` — instances nameless since C-2.E. · **Exact change:** grep `plan.name`/`.name` readers of `MealPlan` in `web_app/src`; if none, drop from the DTO (column stays, R-095). · S · **execute (conditional)**.
- **02-R23** · `MealPlanRecipePicker.vue` multi-select mode — `selectionMode`, `selectedIds`, `isMultiSelect`, `isSelected`, `toggleSelection`, the `update:selectedIds` emit and both `q-checkbox` branches (L150–154, 175–179, 253–255, 405–415) — no host passes `selection-mode` (grep → only `MyProductsPage`'s unrelated `selectedIds`). The "pick myself" builder path that used it was removed 2026-09-03. · **Exact change:** delete; `onRowPick` becomes `emit('recipePick', id)`. · S · **execute**.
- **02-R24** · `helpers/recipeRailFilters.ts:367` `axisFiltersActive` — exported, zero importers. · **Exact change:** delete. · S · **execute**.
- **02-R25** · `MealPlanSkeleton.vue` `grid` variant (L819–834, styles L863–875) — Direction B was retired 2026-07-07 (FU-304); the page passes only `'mobile' | 'list'`. · **Exact change:** delete the variant and its CSS. · S · **execute**.
- **02-R26** · `mealPlanTemplateStore.cloneAsync` (L1017–1020) — grep `cloneAsync(` in `web_app/src`: confirm at execution; the templates page has no Clone action since the 09-13 redesign. If unused, delete the store method, `mealPlanTemplateApiService.cloneAsync` and consider the server `POST /meal-plan-templates/<id>/clone` (test `test_clone_meal_plan_template_unit_of_work.py` pins it → **FU**, same shape as 01-R27). · S · **execute (client) / FU (server)**.

### C4. Componentisation opportunities (R-001)

- **02-R27** · `function pageStyleFn(offset, height)` is copied verbatim in **six pages**: `MealPlansOverview.vue:810`, `MealReconcileRunner.vue:266`, `MealReconcileLog.vue:588`, `SettingsShell.vue`, `StockOverview.vue`, `StocktakeRunner.vue`. · **Exact change:** `helpers/appShell.ts` `export function appShellStyleFn(offset: number, height: number)`; six imports. · S · guard: vue-tsc; drive one shell page · **execute**.
- **02-R28** · `.runner-shell` / `.runner-topbar` / `.runner-card-wrap` / `.runner-card` + the close-X · progress · (?) strip are copied across `MealReconcileRunner.vue`, `MealReconcileLog.vue` and `StocktakeRunner.vue` (the runner's own comment says "same shape as StocktakeRunner"). · **Exact change:** `components/RunnerShell.vue` (props: `closeTo`, `progress?`, `progressLabel?`, `helpTopic`; slots default/`topbar-extra`) hosting the shell CSS once; the three pages become content. · M · guard: none automated — drive the three once · **execute** (coordinate with Chunk 5; the `(?)` becomes a `HelpHint` per 02-R40).
- **02-R29** · lean candidate loader for `build_week` / `week_suggestions` / `swap_suggestions` / `lighter-alternatives` — all run the full `GetRecipesHandler` pipeline (tags, expiring, images, pool, nutrition rollup, inference, cost) over ≤ 10,000 recipes to read ten fields; `swap_suggestions` additionally runs the six-hydration `GetMealPlansHandler.handle_by_id` just for entries. · **Exact change:** `features/recipes/candidates.py::load_recipe_candidates(repository) -> list[RecipeCandidate]` built from `_base_query` + `load_recipe_cookability` + `count_expiring_ingredients_per_recipe` + `estimate_costs_for` + the unallocated/plan-count aggregate; a plain entries read for swaps. · M · guard: `test_build_week.py`, `test_meal_plan_router.py`, `test_swap_suggestions.py`, `test_lighter_alternatives.py` · **FU** (new; sequence after 02-R4).

### C5. Placement / layering (R-003, R-005)

- **02-R30** · `manage_meal_slots.GetMealSlotsHandler.handle` (L47–63) loads **all** `MealPlanEntry` and **all** `Recipe` rows into Python to count slot usage. · **Exact change:** two `select(col, func.count()).group_by(col)` statements. · S · guard: `test_meal_slot_router.py` · **execute**.
- **02-R31** · `get_meal_plan_ingredients.aggregate_meal_plan_ingredients` (L96–103) issues one `.one()` query per recipe; the preview endpoint runs it on every servings tick in the builder. · **Exact change:** one `.all(in_(ids))` with the same includes. · S · guard: `test_meal_plan_ingredient_aggregate.py`, `test_meal_plan_preview.py` · **execute**.
- **02-R32** · `MealPlanBuilderDialog.vue:641–646` `defaultSlots` picks slots by regex `/breakfast|lunch|dinner/i`; `slotFor` (L814) falls back to the literal `'Dinner'`; `build_week.place_entries:353` and `place_entries_batched:378` fall back to `["Dinner"]` — four hard-codings of names in a user-editable vocabulary (R-003). · **Exact change:** client defaults `selectedSlots` to **all** household slots and `slotFor` to `pool[0]`; server falls back to `household_slots[0]`. · S · guard: `test_build_week.py` · **execute** (behaviour default change — note in CHANGELOG).
- **02-R33** · `useMealPlanner.recipeNameById` linear `find` per aggregate row (L842–844). · **Exact change:** `Map` computed. · S · **execute**.
- **02-R37** · raw Quasar palette vars and literal `white` in planner components: `var(--q-primary)` / `var(--q-warning)` / `var(--q-accent)` at `MealPlanWeekDayCard.vue:367, 376, 377, 380, 421, 422`, `MealPlanRichCard.vue:684, 693`, `MealPlanEntryChip.vue:270, 273`, `MealPlanMobileFocus.vue:1023–1037` (+ `color: white` ×3), `MealReconcileLog.vue:761–764`; the rest of these files use `--brand-primary` / `--semantic-warning` / `--text-on-primary`. Two token families in one surface (R-002 / R-060 / D-rules). · **Exact change:** `--q-primary` → `--brand-primary`, `--q-warning` → `--semantic-warning`, `--q-accent` → `--brand-secondary` (check the accent's intent), `white` → `--text-on-primary` (FU-674 governs that token's contrast). · S · **execute**.
- **02-R38** · literal transition durations (D-010) ×8: `MealPlanWeekDayCard.vue:349, 416`, `MealPlanRichCard.vue:667`, `MealPlanEntryChip.vue:260`, `MealPlanMobileFocus.vue:1011, 1102`, `MealPlansOverview.vue:1332`, `MealPlanBuilderDialog` none. · **Exact change:** `var(--motion-fast) var(--motion-ease)`. · S · **execute**.
- **02-R39** · raw px where tokens exist (`gap: 8px`, `padding: 6px 8px`, `border-radius: 8px`, `6px`, `999px`, `margin-bottom: 4px` …) throughout `MealPlanWeekDayCard.vue`, `MealPlanEntryChip.vue`, `MealPlanRichCard.vue`, `MealPlanMobileFocus.vue`, `MealPlanBuilderDialog.vue`, `MealReconcile*.vue` (rem literals) — against `--space-*`, `--radius-*`, `--radius-pill`. Same numeric values exist as tokens, so this is substitution only. · S (mechanical, many lines) · **execute** — do it as one sweep with 02-R37/02-R38 and drive both breakpoints once after.
- **02-R40** · owner directive 2026-08-27 (*"Info button should take you to help and guides, not open a modal"*) not applied to `MealReconcileRunner.vue:210–240` and `MealReconcileLog.vue:536–563` `(?)` dialogs. · **Exact change:** move both texts into the HelpPage entry *Reconcile past meals* (§B2) and replace the two buttons with `<HelpHint topic="Reconcile past meals">`; delete `helpOpen` refs and the dialogs. · S · **execute** (Help track deliverable).

### C6. Naming & idiom

- **02-R41** · `get_meal_plans.py` local imports inside every hydration (R-008). · **Exact change:** hoist. · S · **execute**.
- **02-R42** · `helpers/mealPlanEntryKey.ts:1624–1630` docstring says PATCH "deletes the future entries and inserts new rows … an entry's database id changes every time anything in the week is saved" — false since FU-878 (match-and-update keeps ids). The content-identity key is still right (the batch rebuild re-mints ids). · **Exact change:** reword to the current contract. · S · **execute**.
- **02-R43** · `useMealPlanner.ts:276–290` and `:819–822`, `:792–795` carry retired-feature epitaphs (drag-to-add, `logPaletteCook`, `goToManageTemplates`); `MealPlansOverview.vue:933–938` likewise. These are history the worklog holds. · **Exact change:** trim each to one line pointing at the worklog date. · S · **waive** (comment hygiene only; do opportunistically with 02-R19).

### C7. Efficiency
- 02-R4, 02-R29, 02-R30, 02-R31, 02-R33 above.
- **02-R44** · `MealPlanWeekDayCard.vue:227–229` `collapsedSummary` flat-maps every slot's entries per render; trivial at 7×5. · **waive**.

### C8. Design-level findings — out of Stage-2 scope
- **02-D1** · Templates carry no cook-batch / cook-fresh information (`MealPlanTemplateEntry` is day offset, slot, servings), so applying one to a batch household yields standalone meals. Owner decides whether templates should snapshot batches.
- **02-D2** · `get_shortfall` is assistant-only; the planner reads `needs_cooking` per entry. Two readings of one model, documented — noted so nobody re-unifies them.
- **02-D3** · One plan per week per install (`MealPlan.start_date` is the lookup key, `_fork_template_onto_week` finds by `start_date`); there is no per-user plan. Record for `MULTI_USER_READINESS.md`.
- **02-D4** · `useMealPlanner` is 1,239 lines carrying navigation, mutations, templates, add-to-list, suggestions and budget. It is coherent and documented; splitting (`useMealPlanWeek`, `useMealPlanTemplates`, `useMealPlanShopping`) would be a design-level restructure. **FU** (bundle with 01-R36's page-split follow-up).

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `reconcile.py` raw-SQL cursor pagination + latest-receipt `NOT EXISTS` | keyset paging | SQLAlchemy Core `select()` with window functions | **keep** (as refactored by 02-R9) | — | SQLite < 3.25 has no window functions; the comment says so. |
| `reconcile_consumed_meals.py` connection-level sweep | daily job body | — | **keep** | — | Decoupled transaction is the point. |
| `build_week.select_recipes` greedy ranker + `random.Random` sampling | week generator | an optimiser (OR-tools) | **keep** | — | Anti-creep; fixture-tested. |
| `weekDates.ts` (`shiftDays`, `mondayOf`, `parseLocalIso`) | date arithmetic | `date-fns` / `dayjs` | **keep** | — | Six small pure functions with a spec; a date library would be the app's only one. |
| `useMealPlanner` touch swipe (`onTouchStart/End`, 60px threshold) | gesture | Quasar `TouchSwipe` directive (already in the framework) | **wrap** | S | `v-touch-swipe.vertical` replaces 10 lines and gains velocity handling; execute with 02-R19. |
| `MealPlanCalendar` roving-tabindex grid | a11y grid | — | **keep** | — | Correct and measured. |

### C10. Standards drift (R-0NN)
- **R-021** · 02-R34, 02-R35 (fix).
- **R-045/R-046** · 02-R36 (fix; FU-682).
- **R-056 / FU-043** · 02-R3 (fix).
- **R-003** · 02-R32 (hard-coded slot names) — fix.
- **R-008** · 02-R41 — fix.
- **R-002 / R-060 / D-010 / D-rules tokens** · 02-R37, 02-R38, 02-R39 — fix as one sweep.
- **R-039** · `$q.dialog` calls in `useMealPlanner.ts` and `MealPlansOverview.vue` carry `noCaps` — clean. `MealPlanTemplatesPage.vue:253–257` `cancel: true` without `noCaps` on `confirmDeleteTemplate`. · **Exact change:** `cancel: { label: 'Cancel', flat: true, noCaps: true }`. · S · **execute**.
- **FU-624 / FU-675** · raw `$q.notify` ×17, raw `q-select` ×3 (`MealPlanBuilderDialog.vue:277–293`, `MealPlanTemplatesPage.vue:160–167`) — tracked.
- **Owner directive 2026-08-27 (help modals)** · 02-R40 — fix.

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- Mixed `--q-*` vs `--brand-*`/`--semantic-*` families across the planner (02-R37) — the surface the owner tuned most by eye in September, so re-check pesto dark after the sweep.
- `MealPlanMobileFocus` focused day chip: `--q-primary` fill with `white` ink and `white` pips — FU-674 (`--text-on-primary` contrast) applies.
- `MealPlanRailFilterChips`: `active-color="secondary"` for every chip but Suggests — FU-621/FU-652 (secondary colour) shortlist.
- `MealReconcileLog` pills: four `color-mix(--q-<semantic> 30%)` borders over `--semantic-*-soft` fills — same low-alpha-wash class as the 09-08 cost bars; check in dark themes.
- `MealPlanWeekDayCard` `.day-card--past { opacity: 0.6 }` and `.rich-card--consumed { opacity: 0.55 }` — opacity-dimming on top of muted ink can fall under the D-002 floor in light themes.

## D. Test plan — Meal Plans

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__sweep_receipt_ids__round_trip_through_orm` | pytest e2e | **must-write-before-ship** | 02-R1 — pins that both receipt writers store the same id type; the only automated way to see it. |
| `nextWeekCommands.spec.ts` (pure helper extracted from `useMealPlanner`) | vitest | nice-to-have | 02-R2 — a duplicated week keeps `cook_key` + `cook_fresh`. |
| `test__receipt_rows__queue_log_count_agree` | pytest e2e | nice-to-have | 02-R9 — after the five raw queries collapse to one builder, pin queue ⊆ log and counts match pages. |
| `test__entry_writes__create_and_update_share_validation` | pytest unit | nice-to-have | 02-R7 — one parametrised test over the shared validators replaces duplicated cases. |
| `useMealEntryPresentation.spec.ts` | vitest | nice-to-have | 02-R19b — the seven computeds, parametrised over batch/fresh/linked/consumed. |
| `appShellStyleFn.spec.ts` | vitest | nice-to-have | 02-R27 — trivial, but six pages depend on the two branches. |
| `test__meal_slot_counts__group_by` | pytest e2e | nice-to-have | 02-R30 — usage counts after the aggregate rewrite. |

Not proposed: Playwright flows (owner stance); component tests for the 1,100-line builder — drive it once per breakpoint after the token sweep.

## E. Proposed follow-ups (orchestrator allocates ids)

- **urgent** · type=finding · *Reconcile sweep stores receipt ids as TEXT on SQLite while the verb path stores BLOB* (02-R1) — resolved in Stage 2 if executed this run; otherwise open as urgent.
- type=follow-up · *Lean recipe-candidate loader for the week builder, rail suggestions, swap and lighter endpoints* (02-R29) — why deferred: medium blast radius across four endpoints; sequence after 02-R4.
- type=follow-up · *Server `POST /meal-plan-templates/<id>/clone` has no client caller* (02-R26, conditional) — owner call: drop the endpoint + its unit-of-work test, or keep as API-only.
- type=finding · *Templates don't snapshot cook batches / fresh marks* (02-D1) — owner decision.
- type=finding · *Meal plans are per-install, not per-user* (02-D3) — link `MULTI_USER_READINESS.md`.
- type=follow-up · *Split `useMealPlanner` into week / templates / shopping composables* (02-D4) — bundle with 01-R36.
- type=finding · *Rail row chrome is the third copy of the list-row surface* — already **FU-802/FU-791**; no new entry.

## F. Summary for the register

- FST rows: 15 golden + 13 edge + 4 gate · Help entries: 12 new (1 stale entry deleted; 2 runner modals → guides; DoraBot paragraph rewritten) · Review findings: 46 (execute 38 / FU 3 / waive 3 / conditional 2) · Tests: 7 (must-write 1) · Bugs: 6 (1 latent data-type mix, 1 silent data loss on duplicate, 1 locale, 2 timezone, 1 R-045 auth)
- One-line: the planner's domain model (pool allocation, cook batches, reconcile receipts) is sound and server-owned, but the surface accreted fast in September and left behind 13 dead composable exports, six copies of the page-shell function, two near-identical meal cards, five copies of one raw SQL predicate, four hydrations that each reload the same recipes, and a cluster of small R-021/R-045/R-056 slips that only show on a non-Australian device.
