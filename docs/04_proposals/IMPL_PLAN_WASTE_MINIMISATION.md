# Implementation Plan — Waste Minimisation (C-waste impl)

**Status:** Plan for review · **Date:** 2026-06-24 · **No code yet** — chunked plan +
reviewable PRs.
**Source proposal:** `PROPOSAL_WASTE_MINIMISATION.md` (decisions resolved in §2).
**Adjacent surfaces (read before chunk 3):**
- `IMPL_PLAN_STOCK_OVERVIEW.md` (C-1, **done**) — row dropdown patterns and the
  `StockItemRow.vue` expiry-clear control where the new "Mark as wasted" lives.
- `IMPL_PLAN_DASHBOARD_REBUILD.md` (P-dash, **done**) — confirms the `Needs your attention`
  card already covers near-expiry items (or names what to extend).
- `PROPOSAL_ALERTS.md` (C-9) — `EXPIRING_SOON_WINDOW_DAYS = 7` is the existing horizon
  constant; the cookbook filter introduces its own 14-day horizon (see chunk 4).
**Phase:** Master plan **Phase 0/1** — bug-cluster cleanup with a small surface redesign;
no charter pillar work (the Dora Score touches waste explicitly later — see FU-302).

---

## 0. Verify-state-first

Re-check before chunk 1 (lightweight; the proposal was written against current code on
2026-06-24, so drift risk is low):

- `web_app/src/pages/WastePage.vue` still exists and is wired into the router.
- `web_app/src/composables/useStockFilters.ts` still defines `updated_oldest` as
  `Stalest first`.
- `dora_api/domain/entities/stock_item_waste_event.py` still carries
  `quantity / estimated_value / note`.
- `dora_api/features/waste/waste.py` endpoints match the proposal's §3 inventory.
- `web_app/src/helpers/dashboardMessages.ts:86` still contains the "Use soon" tip.

If any of these have shifted, update the chunk that touches them and note the drift in the
worklog before continuing.

---

## 1. Chunked plan

Six PRs, each independently reviewable. Backend goes first so the frontend deletes don't
strand calls. Test additions live with the chunk that introduces the behaviour change.

### Chunk W1 — Backend slim-down + new endpoints

**Goal:** simplify the event schema, drop fields, add the event-delete endpoint backing Undo,
keep the rescue feed + simplified insights working.

**Touches:**
- `dora_api/domain/entities/stock_item_waste_event.py` — remove `quantity`, `estimated_value`,
  `note` from the dataclass + `Fields` inner class.
- New Alembic migration in `dora_api/migrations/versions/` — `DROP COLUMN` on the three
  fields. Pre-release, no idempotent guards (per migrations memory).
- `dora_api/features/waste/waste.py`:
  - `POST` log endpoint: drop the three fields from the request Pydantic model (keep
    `extra=forbid` per R-001-ish forbid-payloads pattern).
  - Insights endpoint: re-shape response to `{most_wasted: [{name, count}], most_recent: [{name, occurred_at}]}`. Drop reason/value aggregations.
  - **New** `DELETE /waste-events/{event_id}` — idempotent (204 even when the event is gone).
    Auth: same as existing waste endpoints.
  - Recipe-match endpoint: defer fate to chunk 4 (cookbook decides whether to consume it
    here or fold into the recipe-list endpoint).
- `dora_api/features/dora_assistant/tools/waste_insights*` — tighten the tool's output
  schema to match the simplified insights response. Drop reason/value rendering in the
  natural-language formatter.
- `dora_api/features/dora_assistant/tools/expiry_rescue*` — verify it still works against
  the rescue feed; no change expected.
- `tests/e2e/dora_api/test_waste*.py` — update fixtures + assertions to the slim schema +
  new endpoint.

**Risk:** any stored fixtures or seed data that populate the dropped fields. Grep
`estimated_value` / `note=` in test setup before merging. Migration verified up/down on
SQLite + Postgres in isolation.

**Reviewable diff:** ~150-250 LOC, mostly deletions.

---

### Chunk W2 — StockOverview sort fix

**Goal:** replace `Stalest first` with `Expires soonest`.

**Touches:**
- `web_app/src/composables/useStockFilters.ts`:
  - Remove `'updated_oldest'` from the `SortKey` union, the `{ value, label }` option entry,
    and the `case 'updated_oldest'` in the sort switch.
  - Add `'expiry_asc'` with label `'Expires soonest'`. Sort comparator:
    1. `expiry_date asc nulls last`
    2. `stock_level_last_updated asc` (tiebreaker for no-expiry items)
    3. `name asc` (final tiebreaker)
  - Update any persisted-sort-key migration code (if the user's last sort was
    `updated_oldest`, fall back to `name_asc` on load).
- Storybook / fixture pages that exercise the sort, if any.

**Tests:** unit-test the comparator with a fixture of (a) mixed-expiry items,
(b) all-without-expiry items (verifies tiebreaker), (c) duplicate expiry dates.

**Risk:** any saved user preference referencing the old key. Pre-release → silently coerce
to `name_asc` on read, no migration UI.

**Reviewable diff:** ~50-80 LOC.

---

### Chunk W3 — StockItemRow "Mark as wasted" + the modal

**Goal:** the row-level capture flow that replaces the deleted page.

**Touches:**
- New component: `web_app/src/components/stock/MarkAsWastedDialog.vue` (or similar). Tile-grid
  modal per `PROPOSAL_WASTE_MINIMISATION.md` §5:
  - `BaseDialog` with `closable`.
  - Header: item name + optional subline (qty + location, if provided).
  - Body: 2-column tile grid for Expired / Spoiled / Didn't like / Bought too much, plus a
    full-width "Other" row. Each tile = `q-btn` (or custom button) with icon + label.
  - Tile tap → emit `submit(reason)` → close.
  - Icons sourced from `src/style/icons.ts`. If no suitable existing icon, add the new icon
    names there (R-002 token discipline — no inline mappings).
- `web_app/src/components/stock/StockItemRow.vue`:
  - In the existing expiry-clear dropdown (the `q-menu` opened from the expiry chip), add a
    new `Mark as wasted` item below `Clear expiry`.
  - Handler: open `MarkAsWastedDialog`. On submit:
    1. `POST` the waste event via the existing API service (chunk W1's slimmed payload).
    2. `DELETE` the expiry on the item (existing endpoint).
    3. Fire the `$q.notify` toast with Undo:
       ```ts
       $q.notify({
         message: 'Logged as wasted',
         actions: [{ label: 'Undo', color: 'white', handler: undoWaste }],
         timeout: 5000,
       });
       ```
    4. `undoWaste`: `DELETE /waste-events/{event_id}` (chunk W1) **and** restore the cleared
       expiry (proposal §13.A — default yes; revert if friction).
- `web_app/src/services/api/wasteApiService.ts`: drop `estimated_value` / `note` / `quantity`
  from the request type; add `deleteEvent(id)`.

**Tests:** component test for the dialog (tile tap submits; close-X dismisses); integration
test for the row flow (submit posts event + clears expiry + fires toast).

**Risk:** the toast handler runs after the modal is gone, so the event id must be captured
into the handler closure before the modal unmounts. Standard Quasar pattern; called out so
no-one re-discovers it.

**Reviewable diff:** ~250-350 LOC (new component dominates).

---

### Chunk W4 — Cookbook "Uses expiring ingredients" filter

**Goal:** the recipe-side rescue surface.

**Touches:**
- Backend: extend the recipe-list endpoint with `?expiring_within_days=14&order_by=expiring_ingredient_count` (or equivalent). The predicate joins through `StockItem.expiry_date` and the recipe's ingredient list. Re-use the predicate from `waste.py`'s recipe-match if it already exists; otherwise lift the logic there.
- After this chunk lands, delete `waste.py`'s standalone recipe-match endpoint **iff** no
  other consumer is found (the page consuming it dies in chunk W6 anyway). Grep across the
  codebase before removing.
- `web_app/src/pages/RecipesOverview.vue`:
  - Add a boolean filter control in the filter row: `Uses expiring ingredients` (14d).
  - When active, force-sort by `expiring_ingredient_count desc` overriding the user's
    current sort; restore on disable.
  - On each card, show a `Uses N expiring` badge — **only when the filter is active**.
    Conditional `v-if` on the filter state.
- `web_app/src/services/api/recipeApiService.ts` (or equivalent): wire the new query params.

**Tests:** backend e2e — recipe-list with `expiring_within_days=14` returns only matching
recipes with the count field populated. Frontend — toggling the filter shows/hides the badge,
and disabling restores the prior sort.

**Risk:** badge field-naming collision — make the count field unambiguous on the DTO
(`expiring_ingredient_count: int | None`) and only present when the filter is on (or always
present and frontend just hides it when filter is off — either is fine, pick whichever
keeps the DTO cleaner).

**Reviewable diff:** ~200-300 LOC across both sides.

---

### Chunk W5 — Dashboard Use-soon cut

**Goal:** remove the dashboard's duplicate near-expiry surface.

**Touches:**
- `web_app/src/pages/DashboardPage.vue`:
  - Remove `'use_soon'` from the card-id union (around line 1108).
  - Remove the `{ id: 'use_soon', ... }` entry from `cardsByZone` (around line 1157).
  - Remove the `Use soon` template block (lines 490+, 498) and any computed/state tied
    to it (rescue feed call, etc.).
  - Remove the CSS class block(s) specific to `use_soon`.
- `web_app/src/helpers/dashboardMessages.ts:86` — delete the tip line referencing
  "Use soon".
- **Verify** the `Needs your attention` card already surfaces near-expiry items. If it
  doesn't, extend it to (this should be a one-line addition to the card's data source — it
  already aggregates alerts, and near-expiry items are an alert kind per
  `EXPIRING_SOON_WINDOW_DAYS = 7` in `stock_status.py`).

**Tests:** dashboard renders without errors with `use_soon` gone; the Cards menu (visibility
toggles) no longer offers a Use-soon row.

**Risk:** other dashboard cards may have implicitly relied on the rescue feed call shared
with Use-soon; verify the call is fully removed (and the fetch retired) only after the card
is.

**Reviewable diff:** ~80-150 LOC, mostly deletions.

---

### Chunk W6 — Delete the page, route, nav, repoint links

**Goal:** the page itself goes; cross-references move.

**Touches:**
- `web_app/src/pages/WastePage.vue` — delete the file.
- Router (`web_app/src/router/routes.ts` or equivalent) — remove the `/waste` route entirely.
  No redirect (D10).
- `web_app/src/layouts/MainLayout.vue` ~line 229 — remove the Waste nav entry. Leave the
  slot empty (D11).
- `dora_api/features/suggestions/suggestions.py` — change the `frequent_waster` suggestion's
  link from `/waste` to `/stock-items/<stock_item_id>` (D8).
- Grep across the codebase for hard-coded `/waste`:
  - settings copy
  - help-page copy
  - assistant prompts
  - any test that navigates to `/waste`
  - `e2e` specs
- For each: re-point to StockOverview (`/stock` with the rescue intent — sort + Needs attention) or to a specific item's detail page (`/stock-items/:id`), whichever fits. Confirm none point to "nowhere".
- Backend: keep `waste.py` but ensure the page-only recipe-match endpoint is removed if
  unused after chunk W4.

**Tests:** navigate to `/waste` → 404 / not-found page. Suggestions that surface
`frequent_waster` → clicking the suggestion lands on StockItemDetail. No broken links in
help/settings copy.

**Risk:** the help page or onboarding might walk a user *through* the waste page in copy.
Grep for "waste" in `pages/HelpPage.vue`, `pages/DoraHelpPage.vue`, onboarding pages — strip
references; if a help section is now empty, delete the section.

**Reviewable diff:** ~100-200 LOC of deletions + targeted edits.

---

### Chunk W7 — Doc & coverage updates (closes the loop)

**Goal:** keep the planning docs honest.

**Touches:**
- `docs/02_feedback/COVERAGE_GAPS.md` line 205: change
  `- REPORTS / WASTE — feedback empty; deferred.`
  to
  `- REPORTS — feedback empty; deferred.`
  and add a separate bullet recording Waste as covered:
  `- WASTE — \`04_proposals/PROPOSAL_WASTE_MINIMISATION.md\` (C-waste; dissolves /waste into a row action + cookbook filter + slimmed Dora tool; signal preserved for the future Dora Score).`
- `docs/03_prompts/00_INDEX.md` line 55: remove `waste` from the deferred list.
- `docs/03_prompts/C_big_rock_design_briefs.md`: add the new `C-waste` brief entry (already
  written in this PR).
- `CHANGELOG.md`: add the user-visible bullets (page removal, new sort, new filter, new
  capture flow).
- `DORA_FOLLOWUPS.md`: add **FU-302** (Dora Score reassessment).

**Reviewable diff:** ~50 LOC of doc edits.

---

## 2. Sequencing

Strict order is W1 → W2/W3/W4/W5 (any order, can parallelise) → W6 → W7. W6 is the
"point of no return" — once the page is gone, the user-visible regression window starts,
so W3 (the replacement capture flow) and W5 (the dashboard cleanup) must land first.

Recommended PR order: **W1, W2, W3, W4, W5, W6, W7** — left-to-right shippable.

---

## 3. Engineering-standards close-gate

For each chunk, before close:

- R-001 (componentisation-first): W3 introduces a *new* dialog component, not inline markup.
- R-002 (theme tokens): all new styling references CSS variables / utility classes; no
  hex values inline.
- R-003 (state ownership): the cookbook filter pushes its predicate to the server
  (W4); no client-side cross-entity expiry recomputation.
- R-007 (scope discipline): `PROPOSAL_WASTE_MINIMISATION.md` §7 ("What we are deliberately
  NOT doing") is the reference list. Any drift toward those items blocks the chunk.
- R-018 (no compat shims pre-release): W6 deletes the route outright; W1's migration is a
  clean `DROP COLUMN`.

No new ADR-worthy decision expected.

---

## 4. Verification checklist (browser walk, post-W6)

The user runs the browser walk. Capture findings as new follow-ups; do not silently fix
during verification.

- [ ] StockOverview: sort menu shows `Expires soonest`, not `Stalest first`. Sorting an
      inventory of mixed-expiry items places the nearest-expiry item first. Items without
      expiry sort last.
- [ ] StockItemRow: open the expiry dropdown → `Mark as wasted` is present. Tap it → modal
      opens. Tile-tap on a reason closes the modal, clears the row's expiry, fires the
      Undo toast.
- [ ] Undo toast: hitting Undo within 5s removes the wasted-event AND restores the expiry
      (verify in the row + in the StockItemDetail History tab).
- [ ] StockItemDetail History tab: a logged event appears with reason + date, no value, no
      note.
- [ ] Cookbook: enable `Uses expiring ingredients` filter → list narrows; cards show
      `Uses N expiring` badge; disable → badge disappears, original sort restores.
- [ ] Dashboard: no `Use soon` card; the Cards menu doesn't offer it. `Needs your attention`
      still includes near-expiry items.
- [ ] Reports: visually unchanged.
- [ ] `/waste` URL: 404 / not-found. No nav entry.
- [ ] Dora assistant: asking "what am I wasting often?" returns a sensible answer from the
      simplified `waste_insights` tool. Asking "what's expiring soon?" returns the rescue
      feed unchanged.
- [ ] Suggestion `frequent_waster` (if currently surfaced): clicking deep-links to the
      relevant StockItemDetail page.

---

## 5. Follow-ups expected to spin off

- **FU-302** (added in W7) — Dora Score reassessment with waste-as-pillar de-emphasis. Deferred to pre-Phase 3.
- Anything that surfaces in the W4 backend predicate (e.g. ingredient-to-stock-item match
  fuzziness) that the cookbook filter needs but isn't worth fixing in this scope.
