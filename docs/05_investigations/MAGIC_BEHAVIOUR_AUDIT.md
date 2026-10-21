# Magic-behaviour audit (FU-092)

**Status:** **complete; verdicts gathered 2026-06-28.** Follow-up
work spun off as `FU-315..FU-319` (see § Verdicts below).
**Date / task:** 2026-06-28 (FU-092 — "audit ALL implicit/automatic 'magic'
behaviour"). Output specified by the FU: one entry per behaviour, verdict
chosen from the framework below, location pointer.

## Verdict framework

| Code | Meaning                                                        |
|------|----------------------------------------------------------------|
| (a)  | **Keep silent** — genuinely effortless, low-surprise, easy to undo. |
| (b)  | **Make visible / explainable** — surface what happened (toast, "why" hint, undo). Logic unchanged. |
| (c)  | **Make opt-in** — off by default; user enables per-install / per-item. |
| (d)  | **Drop it** — force an explicit choice every time.             |

Bias: silent is fine when reversible + obvious; needs surfacing when it
changes money, data, or list contents in a non-obvious way (FU-092 raise
note).

## Findings

Each row: **what** · **where** · **current surface** · **surprise risk**
· **recommendation**. Numbered for cross-ref in the verdict back-and-forth.

### F1. Auto-add stock item to a list on Low/Out transition

- **What:** When a stocktake update transitions a `StockItem` from "ok" to
  Low or Out *and* the per-item `auto_add_when_low` flag is on, the API
  silently appends a new line to the user's single draft list. Skipped
  silently when there's no draft, 2+ drafts, or the item is already on
  any non-done list.
- **Where:** [update_stock_item.py:217](dora_api/features/stock_items/update_stock_item.py:217)
  (`_try_auto_add`).
- **Current surface:** PATCH response carries `auto_added_line_id` +
  `auto_added_to_list_id`; the SPA can toast off that. The flag is per-item.
- **Surprise risk:** Medium. The flag is opt-in per item (off by default
  on the entity) so the user has agreed in principle, but the *moment* of
  add is silent — fine as long as the SPA actually toasts.
- **Recommendation:** **(b) make visible.** Keep the auto-add (the user
  asked for it via the flag), but verify the SPA renders a toast or a
  "we added X to <list>" affordance every time. Already half-built.

### F2. Quick-add lands silently on the lone draft list (1-draft case)

- **What:** When the user clicks "Add to list" and there's exactly one
  draft list, the item lands on it with no picker, no prompt.
- **Where:** [primary_target_resolver.py:43](dora_api/features/shopping_lists/primary_target_resolver.py:43),
  [`useQuickAddTargetPick`](web_app/src/composables/useQuickAddTargetPick.ts).
- **Current surface:** A "✓ Added to <list>" toast (via
  `useShoppingListActions`). The cart icon flips state on the row.
- **Surprise risk:** Low. There's only one possible target; the picker
  would just confirm what's obvious. Cart icon + toast cover the "what
  happened" question.
- **Recommendation:** **(a) keep silent.** Genuinely effortless; the
  surface state already explains it.

### F3. Quick-add: sessionStorage remembers the pick for the 2+-drafts case

- **What:** When the user has 2+ draft lists, the first quick-add prompts
  for a target. The chosen list is saved in `sessionStorage`
  (`dora.quick_add_target_list_id`) and reused silently for subsequent
  quick-adds in the same tab session.
- **Where:** [useQuickAddTargetPick.ts](web_app/src/composables/useQuickAddTargetPick.ts);
  consumed by `AddToListButton.onBulkAdd` and the single-item flow.
- **Current surface:** Tab-scoped (a fresh tab re-prompts). No visible
  "remembered" indicator after the first prompt.
- **Surprise risk:** Medium. A user expecting the picker every time will
  wonder why the second item went somewhere "automatically".
- **Recommendation:** **(b) make visible.** Keep the remember (the
  shopping mid-flight friction it removes is real), but the toast that
  fires per-add should name the list ("Added to *Sunday shop*") so the
  user can't be surprised silently. Quick check that this is already the
  case; if not, fix it.

### F4. Cart Axis B: "create a list first" on 0 drafts (NOT a silent create)

- **What:** Originally listed by FU-092 as "0 drafts → silently create one";
  the audit shows the current behaviour is the opposite — the inline-product
  variant toasts "No draft list yet. Create one first" and the cart button's
  primary path also routes through the picker. No silent list-create.
- **Where:** [AddToListButton.vue:355](web_app/src/components/AddToListButton.vue:355).
- **Current surface:** Info toast prompting the user to create.
- **Surprise risk:** None.
- **Recommendation:** **(a) keep silent → already the right shape.** No
  action; note this finding closes the FU's specific worry on this point.

### F5. Past-day meal-plan auto-drain (`reconcile_consumed_meals`)

- **What:** Any past-day `MealPlanEntry` with `consumed_at IS NULL` is
  silently marked consumed (`consumed_at = now()`) and the corresponding
  `Recipe.available_meals` pool is decremented by the entry's `servings`,
  floored at 0. Idempotent.
- **Where:** [reconcile_consumed_meals.py](dora_api/features/meal_plans/reconcile_consumed_meals.py);
  fired as a `before_request` hook on dashboard / meal-plan / recipe
  routers ([startup.py:140](dora_api/startup.py:140)).
- **Current surface:** None. The user sees lower pool counts after a day
  rolls; they don't see a "we marked X consumed" record.
- **Surprise risk:** **High.** This is the heaviest-touch implicit
  behaviour in the app — changes data on every page load, with no
  receipt and no undo. A user who didn't eat a planned meal still has it
  drained from their pool.
- **Recommendation:** **(b) make visible.** Keep the reconciliation (the
  rolling-day model depends on it), but: (1) log a per-day "auto-consumed"
  receipt the user can see and reverse from a small "Did you actually
  cook these?" surface (planning chip on the dashboard? cookbook recent-
  cooked list?); (2) consider (c) — gate it behind a per-user "auto-drain
  past-day plans" setting, default on, so a user who wants to confirm
  each cook can flip it. Worth a small proposal before changing.

### F6. Lazy reconcile is a `before_request` hook (silent on every read)

- **What:** Same reconciliation as F5, but flagged separately because the
  *triggering shape* is also magic: the user reads any recipe/meal-plan/
  dashboard endpoint and a sweep mutation runs first.
- **Where:** [startup.py:150-162](dora_api/startup.py:150).
- **Surprise risk:** Low for the read endpoints (idempotent, fast); but
  it adds "silent writes on read" to the mental model.
- **Recommendation:** **(a) keep silent.** This is a pure implementation
  detail of F5 — it's the *what* of F5 that needs the receipt, not the
  *when*. If F5 grows a receipt surface, F6 needs no change.

### F7. Auto-pick the cheapest offer when the user hasn't selected a product

- **What:** Server sorts a line's `offers[]` cheapest-first; the
  client's `chosenOfferFor(line)` returns `offers[0]` when no
  `selected_product_id` is set. Effectively: "no explicit pick → use
  cheapest for line price + savings math".
- **Where:** [get_shopping_list_detail.py:327](dora_api/features/shopping_lists/get_shopping_list_detail.py:327)
  (sort), [models/shoppingList.ts:172](web_app/src/models/shoppingList.ts:172)
  (chosenOfferFor fallback).
- **Current surface:** The line shows the price + store of whichever offer
  ranks first. No "cheapest pick" badge.
- **Surprise risk:** Medium. Money. A user who thinks they picked
  Woolworths-brand and sees Coles pricing displayed (because Coles is
  cheaper this week and they never explicitly set a product) is mildly
  blindsided.
- **Recommendation:** **(b) make visible.** Render a small "cheapest"
  hint chip on lines where the display offer is the auto-pick (no
  `selected_product_id`). One-line code change; removes the only "why is
  this number what it is" surprise on the list.

### F8. URL importer auto-resolves scraped cuisine/category against existing vocab

- **What:** When importing a recipe from a URL, scraped `recipeCuisine` /
  `recipeCategory` names are case-insensitively matched against existing
  `Cuisine` / `Category` rows; matches pre-fill the editor as already-set
  ids. No vocab rows are ever created by the importer.
- **Where:** [import_recipe_from_url.py:351](dora_api/features/recipes/import_recipe_from_url.py:351)
  (`_match_vocab`).
- **Current surface:** The editor lands with the cuisine/category select
  populated (no banner). The user sees the pick and can change it.
- **Surprise risk:** Low. The user is on the editor before save; nothing
  has hit the DB yet.
- **Recommendation:** **(a) keep silent.** Save-deferred + reversible +
  the editor shows the result.

### F9. Inline-create a stock item from the recipe ingredient picker

- **What:** The recipe ingredient `q-select` offers "Create '<typed>'"
  when no match exists; clicking it fires a POST to create the stock
  item inline before the recipe is saved. The new stock item exists in
  the user's pantry regardless of whether the recipe save succeeds.
- **Where:** [RecipeDetailPage.vue:395](web_app/src/pages/RecipeDetailPage.vue:395).
- **Current surface:** The user clicks the explicit "Create" item; no
  hidden trigger.
- **Surprise risk:** Low (it was an explicit click), but the
  asymmetry — the new stock item survives a recipe cancel — is a small
  surprise.
- **Recommendation:** **(a) keep silent** *or* **(b) toast "Added <name>
  to your pantry"**. Either is fine; lean (a) since the click is
  intentional and the StockOverview reveals it on the next visit.

### F10. `cook_recipe` bumps `last_made_on = now()` and adds to the pool

- **What:** `POST /recipes/<id>/cook` with `meals_cooked: N` stamps
  `last_made_on` at server now and increments `available_meals` by N.
- **Where:** [cook_recipe.py:38](dora_api/features/recipes/cook_recipe.py:38).
- **Current surface:** Explicit user action via the cook button; response
  carries the new pool count.
- **Surprise risk:** None.
- **Recommendation:** **(a) keep silent — not magic.** Explicit endpoint
  with a single clear effect; listed for completeness.

### F11. Dora suggestions surface (`/api/suggestions`)

- **What:** A worker scans the household for nudge candidates (waste
  risk, low pool, etc.) and surfaces up to 8 suggestions on the
  dashboard / chat. Accepting routes through the underlying domain
  endpoint; dismiss / snooze persist per-(kind, dedup_key).
- **Where:** [suggestions.py](dora_api/features/suggestions/suggestions.py).
  Notes upfront: "the endpoint deliberately doesn't expose an 'accept'
  action: accepting runs an existing domain endpoint" — i.e. no
  hidden-mutation path.
- **Current surface:** Always visible as a suggestion card the user
  acts on.
- **Surprise risk:** None — suggestion, not action.
- **Recommendation:** **(a) keep silent — not magic.** This is the
  poster child for "visible, dismissable, never hidden". Listed for
  completeness.

### F12. Onboarding seed import (groups / locations / stores)

- **What:** `POST /api/onboarding/seed` reads bundled JSON catalogues and
  bulk-inserts default `StockGroup` / `StockLocation` / `Store` rows.
  Idempotent on name.
- **Where:** [onboarding.py:6](dora_api/features/onboarding/onboarding.py:6).
- **Current surface:** Explicit step in the wizard; the user clicks
  "Use these defaults?" / "Skip".
- **Surprise risk:** None — explicit click, opt-out is visible.
- **Recommendation:** **(a) keep silent — not magic.**

### F13. `is_open = true` silently stamps `opened_on = today`

- **What:** Toggling the `is_open` flag on a stock item to True silently
  sets `opened_on = today`; toggling to False clears it.
- **Where:** [update_stock_item.py:205](dora_api/features/stock_items/update_stock_item.py:205).
- **Current surface:** None directly. The SPA may render the opened
  date afterwards in the detail view.
- **Surprise risk:** Low. It's the obviously-correct default. Edge case:
  the user opens a jar today but only logs it tomorrow and wants the
  date to be yesterday — they have to edit `opened_on` separately.
- **Recommendation:** **(a) keep silent.** Net positive convenience;
  the user can override `opened_on` in the same PATCH (the comment in
  the code calls this case out as supported).

### F14. Auto-flip an `auto_*` line back to `manual` on user edit

- **What:** When the user edits a line's quantity or selected_product,
  `added_via` flips to `manual` to signal "user has taken ownership of
  this line". Tick alone doesn't count.
- **Where:** [manage_shopping_list_lines.py:230](dora_api/features/shopping_lists/manage_shopping_list_lines.py:230).
- **Current surface:** The "added via" chip on the line disappears /
  changes.
- **Surprise risk:** Very low — the visual chip is the receipt.
- **Recommendation:** **(a) keep silent.** The chip *is* the surface.

### F15. Offer price snapshot at tick / add / select-change

- **What:** A line's `picked_offer_price` is auto-captured at three
  moments (creation, first tick if missing, selected-product change) so
  reports have a stable "planning-moment price" to read.
- **Where:** [manage_shopping_list_lines.py:167](dora_api/features/shopping_lists/manage_shopping_list_lines.py:167)
  (`snapshot_offer_price`), called from create / update / tick paths.
- **Current surface:** None — used only for reports. The user's
  `actual_unit_price` override (if set) wins in price displays.
- **Surprise risk:** None.
- **Recommendation:** **(a) keep silent.** Pure reporting plumbing; the
  user-facing override is explicit.

### F16. Finish-shopping defaults every ticked line to "Well-Stocked"

- **What:** `POST /shopping-lists/<id>/finish` flips every ticked line's
  linked stock item back to Well-Stocked unless the user overrode that
  per-item via the modal.
- **Where:** [manage_shopping_list.py:253](dora_api/features/shopping_lists/manage_shopping_list.py:253).
- **Current surface:** The finish modal (UX-v2 M12) reveals all ticked
  items + their default-level pick so the user can override before
  confirming.
- **Surprise risk:** None — the modal *is* the surface.
- **Recommendation:** **(a) keep silent — not magic.** The bulk default
  + per-item override is the textbook shape this audit's framework asks
  for. Listed for completeness.

### F17. Stock alerts fire automatically (per-item conditions)

- **What:** `/api/alerts` generates alerts on read for: `expired`,
  `expiring_soon`, `out_of_stock`, `low_stock`, `essential_low`,
  `essential_out`, `stocktake_overdue`. Per-item, per-condition, with
  dedup keys; user can dismiss / snooze.
- **Where:** [get_alerts.py:155-276](dora_api/features/alerts/get_alerts.py:155).
- **Current surface:** Bell badge + alerts page.
- **Surprise risk:** None — alerts are surfaces, not mutations.
- **Recommendation:** **(a) keep silent — not magic.** Visible by
  design.

### F18. Forward-looking alerts (`no_planned_meals` / `shopping_day`)

- **What:** Same shape as F17 but household-level: "no meals planned
  this week", "shopping day is today/tomorrow/overdue".
- **Where:** [get_alerts.py:365](dora_api/features/alerts/get_alerts.py:365),
  [get_alerts.py:391](dora_api/features/alerts/get_alerts.py:391).
- **Current surface:** Same bell + alerts page.
- **Surprise risk:** None.
- **Recommendation:** **(a) keep silent — not magic.**

## Inventory summary

Of the 18 behaviours audited:

- **9 are already in the right shape** (F4, F8, F10–F12, F14–F18). They
  surfaced in the FU's catalogue as "magic to check", but are either
  surfaces (alerts, suggestions), explicit user actions (cook, onboarding
  seed, inline create), or visible-by-design (finish modal, added_via
  chip).
- **3 want a visible-explainable upgrade** without changing the logic
  (F1 auto-add toast verification, F3 "remembered list" name in toast,
  F7 "cheapest" hint on auto-picked offer lines).
- **1 wants a proper proposal** before changing (F5 past-day auto-drain
  — the heaviest-touch implicit behaviour in the app; deserves the
  audit's most careful pass).
- **2 are pure plumbing details** that ride with their parent (F6, F15).
- **0 obvious "drop it" candidates** so far. F5 might land in (c) "opt-in"
  after the proposal — TBD.

## Verdicts (2026-06-28)

User answered each finding in batched rounds. Follow-ups spun off where
the verdict was (b), (c), or a directive to write a proposal.

| #   | Verdict                                                     | Follow-up |
|-----|-------------------------------------------------------------|-----------|
| F1  | (b) + line-level indicator. Toast must name what landed where; the existing `added_via` chip already labels `auto_low_stock` lines as "auto: low stock", so the indicator is partially present. Verify both in browser. | [[FU-315]] |
| F2  | (a) Keep silent. The single-target case is genuinely effortless. | — |
| F3  | (b) + (c). Default behaviour is the remember (current); add a per-user "always ask which list" setting (default **off**) so a user who wants the confirm-every-time feel can flip it on. Also verify the toast names the destination list. | [[FU-316]] |
| F4  | (a) Already in the right shape. | — |
| F5  | **Plan-first.** User wants (c) opt-in (default on for auto-drain) **paired with a new dedicated manual-reconcile feature** — modelled after stocktake mode, with its own page, alerts, and indication of what *should* have been consumed. Deserves a deeply-thought proposal before any code touches the reconcile path. | [[FU-317]] |
| F6  | (a) Plumbing detail of F5; will be revisited inside the F5 proposal. | (rides FU-317) |
| F7  | (b) Add a small "cheapest" chip on lines using the auto-pick. | [[FU-318]] |
| F8  | (a) Keep silent — save-deferred + visible in the editor. | — |
| F9  | (b) Toast "Added <name> to your pantry" on inline create. | [[FU-319]] |
| F10 | (a) Already in the right shape — explicit endpoint. | — |
| F11 | (a) Already in the right shape — suggestions are a visible surface. | — |
| F12 | (a) Already in the right shape — explicit wizard step. | — |
| F13 | (a) Keep silent — obviously-correct default; user can override `opened_on` in the same PATCH. | — |
| F14 | (a) Keep silent — the `added_via` chip is the receipt. | — |
| F15 | (a) Keep silent — pure reporting plumbing; user-facing override is explicit. | — |
| F16 | (a) Already in the right shape — finish modal is the surface. | — |
| F17 | (a) Already in the right shape — alerts are a visible surface. | — |
| F18 | (a) Already in the right shape — same as F17. | — |

## Outcome

- **13 of 18 verdicts: (a) keep silent / already in the right shape.** No
  code change. FU-092's broad worry resolves into a narrow set of UI
  surfacing tasks plus one deep-thought proposal.
- **4 (b) follow-ups:** FU-315 (F1 toast verify), FU-316 (F3 toast + setting),
  FU-318 (F7 cheapest chip), FU-319 (F9 pantry-add toast).
- **1 plan-first follow-up:** FU-317 — design proposal for a manual
  meal-plan reconcile feature (the heaviest implicit behaviour in the
  app; user wants this thought through before touching the
  `reconcile_consumed_meals` path).

R-019 (no magic) is the standing rule going forward; this audit is the
one-time backlog sweep that ratifies what's already in the right shape
and queues the rest.

---

*Investigation by 2026-06-28 session. Verdicts owned by the user;
recommendations were starting points.*
