# Dora Follow-ups Ledger — Open

Stateful backlog of **open follow-ups, deferred jobs, leftovers, and findings**
surfaced while running prompts — the stuff that's easy for the user to miss in a
long session summary. Distinct from the other logs:

- `CHANGELOG.md` = product/code changes that shipped.
- `DORA_WORKLOG.md` = per-session handoff narrative.
- `DORA_FOLLOWUPS.md` (this file) = **open loops** that outlive a single session.
- `DORA_FOLLOWUPS_RESOLVED.md` = the archive of items that have been resolved
  (kept for the trail — never delete).

## How to use this file

- **On session start:** scan for items here. Surface the ones whose *recommended
  resolution point* is "now" or matches the work about to start, and **ask the
  user** whether they want to review/resolve them now or defer.
- **On ending a work unit:** add any new follow-ups/leftovers/findings you
  generated. If you actually resolved an item, **move its entry from this file
  to `DORA_FOLLOWUPS_RESOLVED.md`**, flip the heading from `[OPEN]` to
  `[RESOLVED]`, and add a one-line state note on how. Do not leave resolved
  items in this file, and do not delete them either — the trail matters.
- **Reported defect that "doesn't reproduce" → still log it here** as `[OPEN]`
  type `finding`, resolution "confirm in browser". A static code read is not
  proof a user-reported bug is fixed. Track each reported item individually;
  never bury several as one "all fine" note.
- Keep the newest items at the top.

## Entry template

```
## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
```

---

## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
- **State note:** (filled in when resolved — date + how)
```

---

# Open

## [OPEN] FU-188 — Back-in-stock subscriptions tier (deferred from Alerts C-9.5)
- **Raised:** 2026-06-15 (Alerts C-9.5 — subscriptions tier)
- **Type:** deferred job
- **What:** The proposal/impl plan for the subscriptions tier mentioned a **back-in-stock**
  subscription shape ("notify me when a merchant's product comes back in stock") alongside the
  price-watch (`PriceAlert`) tier that C-9.5 shipped. C-9.5 built **only** the price-watch
  surface (`SubscriptionsPanel.vue`, money-gated, reusing `/price-history/alerts`). Back-in-stock
  was **not** built: there is no data source / entity for it yet — it's companion/ingestion-scope
  (the producer would push availability), and the in-app side would just surface/manage rows like
  price watches do.
- **Why deferred:** anti-creep — no back-in-stock data exists to surface, so a placeholder UI/shape
  now would be speculative (charter: don't pre-build). User confirmed skipping it for C-9.5.
- **Recommended resolution:** **when** the companion/ingestion path (C-10) defines a back-in-stock
  signal — then add a second tier to `SubscriptionsPanel.vue` (same list/manage shape) reading it.

## [OPEN] FU-187 — Assistant ignores the configurable expiring-soon window (uses the constant default)
- **Raised:** 2026-06-15 (Alerts C-9.2 — threshold threading)
- **Type:** finding / consistency gap
- **What:** C-9.2 moved the expiring-soon window onto `AppSetting.expiring_soon_window_days`
  and threaded it through the alerts evaluator (`get_alerts.py`) and the location heatmap
  (`attention.py`, via `get_location_tree` + `get_stock_item_detail`) using one resolver,
  `stock_status.effective_expiring_soon_window`. The **assistant** (`features/assistant/
  tools.py`, ~4 sites near lines 903/1480/1570/2025) still reads the bare
  `EXPIRING_SOON_WINDOW_DAYS` *default* constant, so if an admin changes the household window
  the assistant's "expiring soon" answers won't match the alerts list / heatmap. This is the
  constant-as-default carve-out the impl plan explicitly allowed for C-9.2; flagged inline at
  the `tools.py` import. It's the one default (R-003 — not a second literal), just not
  honouring the override.
- **Why deferred:** threading the `AppSetting` fetch through the 4 assistant tool sites was
  out of C-9.2's tested scope (acceptance named only bell/page/heatmap); low impact (assistant
  expiry answers only drift if an admin retunes the window).
- **Recommended resolution:** opportunistic — when the assistant's expiry tools are next
  touched, or fold into the FU-174 app-wide date/threshold sweep. Pass the resolved window
  (same `effective_expiring_soon_window`) into the 4 sites.

## [OPEN] FU-186 — Decommission in-app live product search / `merchant_api` (scraping-divorce ripple)
- **Raised:** 2026-06-15 (C-10 ingestion API design)
- **Type:** deferred job / decommission
- **What:** With scraping divorced and `/api/ingest` (C-10) as the **only** inbound product path,
  Dora-core must **not scrape live**. The current in-app **product search calls the sibling
  `merchant_api` (port 5172) to live-scrape** — that has to go. Options: (a) repoint in-app
  product search at the **already-ingested local catalogue** (search what your source pushed), or
  (b) move product search entirely to the companion. This **reshapes C-1b's "find & link a
  product"** (it can no longer live-search) and the "Find deals" / best-deals surfaces; `merchant_api`'s
  live-scrape role moves to the private external producer. Folds in **FU-053** (best-deals card
  fetches all products client-side).
- **Why deferred:** a cross-cutting decommission sweep, distinct from building the ingestion seam;
  needs `/ingest` landed first so the catalogue is populated to search against.
- **Recommended resolution:** after **C-10.2** (the ingest path exists); pair with **FU-182**
  (Products-off) since both reshape the product surfaces, and re-confirm C-1b §2.4's "find & link"
  against it. Keep the **invisibility rule** — no scraper references in whatever replaces search.

## [OPEN] FU-185 — Stock Item Detail recipe-tab actions are dead (B8 residue)
- **Raised:** 2026-06-15 (C-1b design — Explore sweep)
- **Type:** finding / bug
- **What:** On `StockItemDetailPage.vue`, `RecipeCard` **emits** `@toggle-favourite` +
  `@add-all-to-list` but the detail page **doesn't listen** to them (only `@open`/`@cook`/
  `@add-missing` are wired). So "remove from favourites does nothing" (feedback L132) and most
  recipe actions beyond Cook (L134) are dead on this surface. Recipe-row navigation IS fixed.
- **Why deferred:** found during the C-1b design sweep; **homed in C-1b.4** (wire the listeners)
  but C-1b isn't built yet. Static read confirms the handlers are missing.
- **Recommended resolution:** fix in **C-1b.4** (Recipes-tab chunk); until then it's a live defect
  — **confirm in browser** that favourite-toggle/add-all are dead, then wire them. Cites B8.

## [OPEN] FU-184 — Reconcile onboarding sell-copy + loop stages against actual app behaviour
- **Raised:** 2026-06-15 (Onboarding C-5 v3 design)
- **Type:** finding / deferred verification (P3 Honest gate)
- **What:** The C-5 onboarding redesign sells "the loop" cinematically (Stock → Plan → List →
  Shop → Restock → Cook, Dora at centre) with one-line claims per stage. These claims + the loop
  stages are **PROVISIONAL** (PROPOSAL_ONBOARDING §6). Before any onboarding copy ships, **walk
  the running app** and confirm each claim is literally true (does finishing a shop really
  auto-restock? does cook mode decrement stock? does price memory + an "inflated price" signal
  actually exist?). Cut/soften anything the app doesn't back.
- **The emerging "Insight / Spend-smarter" stage** (user links products to stock items → Dora
  flags prices that are higher than usual, from their own receipts) is the honest replacement
  for the divorced deal-scraping — but it **isn't a finished feature**. Do NOT promise it in
  onboarding copy until it's real; it's a design placeholder until then. Decide whether to build
  it (it's the spine of the **Spend-tracking** persona).
- **Why deferred:** needs the running app to verify; can't be cleared by a static read (env
  unprovisioned this session, same blocker as FU-183).
- **Recommended resolution:** **close-gate on the onboarding-copy chunks (C-5.1/C-5.2/C-5.6)** —
  validate when building them on a provisioned app. Not optional polish.

## [OPEN] FU-183 — Verify Alerts C-9.1 on a provisioned machine (built static-only)
- **Raised:** 2026-06-15 (Alerts C-9.1 — spine)
- **Type:** finding / deferred verification
- **What:** C-9.1 (generalised alert key + `AlertInteraction` ledger + server-side
  snooze/read/dismiss + the single server-derived "what counts" + 6 new endpoints + the
  server-backed `alertStore`) was **written without running anything** — this machine has
  no Python env (Windows-Store stub only, no venv, deps not importable) and
  `web_app/node_modules` is absent. The user chose "build static-only now" with that
  known. Nothing was executed: no backend e2e, no `migrate up/down` on `f4d2a9c7b3e1`, no
  single-head re-confirm under alembic, no `vue-tsc`, no `eslint`.
- **Must verify (provisioned machine):** (1) `pip install -r requirements.txt` + run
  `tests/e2e/dora_api/test_alerts.py` (7 tests) + the full backend e2e (regression — the
  alert DTO shape changed); (2) migration `f4d2a9c7b3e1` up **and** down in isolation +
  `alembic heads` shows a single head; (3) `npm install` in `web_app` → `vue-tsc` + eslint
  clean (alert model/service/store/bell touched); (4) **browser**: bell badge == actionable
  list count; snooze persists across a reload (server-side); dismiss hides; the existing
  inline actions still work with the new scoped key. Only then flip **FU-042** to resolved.
- **Sub-findings to confirm while there:** (a) assistant `tools.py::get_alerts` passes no
  `user_id`, so it ignores the requesting user's snooze/dismiss overlay — decide whether to
  thread the session user in (minor consistency); (b) no prune sweep for stale
  `AlertInteraction` rows yet (harmless — filtered at read; add to the existing
  `BackgroundScheduler` if it ever matters).
- **Why deferred:** environment not set up on this machine; building static-only was the
  user's explicit choice this session.
- **Update 2026-06-15 (env provisioned — automated verification DONE):** the machine now has
  a working dev env (real Python 3.11.9 + venv + deps; `npm install` done). Verified GREEN:
  (1) `tests/e2e/dora_api/test_alerts.py` 7/7 + full backend e2e **286 passed** (no regression
  from the DTO `tier`/count changes — one unrelated brittle pagination test in
  `test_stock_item_router.py` was hardened to assert pagination mechanics, not specific seeded
  names; not a C-9 bug); (2) migration `f4d2a9c7b3e1` up **and** down verified in isolation +
  `alembic heads` = single head; (3) `vue-tsc` clean + `eslint` shows only the 5 pre-existing
  FU-177 errors (none in alert files). **C-9.2 (per-user prefs + thresholds) was also built +
  test-verified this session** (5 new e2e). Only the in-browser smoke remains.
- **Remaining (browser only):** bell badge == actionable list count; snooze persists across a
  reload; dismiss hides; inline actions still work with the scoped key. **C-9.2 additions:**
  admin System-settings threshold fields save + round-trip; disabling a kind removes it from
  the list + drops the badge; promoting/demoting a kind moves it between badge/FYI.
  **C-9.3 additions:** the Alerts **hub page** (summary tiles + tiered active list + Manage panel
  + collapsible History) renders; the bell is now a slim peek (top rows + bulk-add + "Open
  Alerts"); the shared `AlertRow` act/read actions work from both; History lists past
  dismiss/snooze/read with the stock name resolved; dark-mode clean; no bell/page divergence.
  **C-9.4 additions (forward-looking nudges):** with next week's meal plan empty, a
  `no_planned_meals` FYI row shows and deep-links to `/meal-plans`; planning a meal for next week
  clears it. A `shopping_day` FYI row shows for a list with `planned_shop_date` within 3 days and
  deep-links to that list (`/shopping-lists/<id>`); marking the list done clears it. Both render
  cleanly through the shared `AlertRow` (icon/colour/theme), carry no stock name, and snooze/dismiss
  from the hub + bell.
  **C-9.5 additions (subscriptions / price-watch tier):** with money flag ON and an armed price
  alert, the **Price watch** region renders on the hub listing it (product · merchant · "notify
  below $X" · last-alerted); **View** opens the price-history explorer with that product selected;
  **Remove** deletes it (row disappears + toast); empty-state shows cleanly when nothing is armed;
  the whole region is **hidden when the money flag is off**.
  **C-9.6 additions (Upcoming fortnight timeline) — Phase A is now COMPLETE:** the **Upcoming**
  mini-calendar renders on the hub; days with events show the right per-category dots (warning =
  expiry, primary = shopping, positive = meal); out-of-window cells dimmed, today ringed; clicking
  a day expands its detail list and the links navigate (expiry → `/stock/:id`, shopping →
  `/shopping-lists/:id`, meal → `/cookbook/:recipe_id`); refresh works; empty-state shows when
  nothing is scheduled; dark-mode clean (token dots survive theme switch).
- **Recommended resolution:** **browser-confirm, opportunistic** (next time the app runs) —
  then flip **FU-042** to resolved. Automated verification no longer blocks; only browser
  smoke remains. (Sub-finding (a) — assistant `get_alerts` ignores the user overlay — and the
  new expiring-soon override gap are split out as **FU-187**.)

## [OPEN] FU-190 — Ingestion API must honour "no auto-create stores"
- **Raised:** 2026-06-15 (simple-mode brainstorm round 2)
- **Type:** design constraint / proposal amendment
- **What:** The companion scraper (Phase 2 ingestion API) pushes products +
  offers + price-observations, each referencing a merchant/store. The
  no-auto-create rule for stores (FU-189) must propagate into the ingestion
  API design — it cannot silently materialise stores the user hasn't
  approved. Three viable shapes: (a) hard-reject unknown-store offers; (b)
  quarantine queue ("pending review" until user maps/creates); (c) setup
  mapping step where user maps each companion-side merchant to a Dora store
  once before ingestion goes live. Recommendation in the scratch:
  **(c) happy path + (b) safety net** for never-seen-before stores
  appearing post-setup. Scratch §7 in
  `docs/99_scratch/MINIMAL_USER_PRODUCTS_OFF_FRICTION.md` has the rationale.
- **Why deferred:** PROPOSAL_INGESTION_API.md predates this rule. Fold the
  constraint into the proposal before any ingestion-API code starts.
- **Recommended resolution:** during Phase 2 ingestion-API design — amend
  PROPOSAL_INGESTION_API.md §2 with the "no auto-create stores" constraint
  + the (c)+(b) sequencing, and add a row to its feedback-coverage table
  citing FU-189. Block ingestion implementation until the proposal is
  updated.

## [OPEN] FU-189 — Rename Merchants → Stores, add management page + user-uploaded logos
- **Raised:** 2026-06-15 (simple-mode brainstorm round 2)
- **Type:** refactor + small feature
- **What:** Three coupled changes:
  1. **Entity + UI rename `Merchant` → `Store`** app-wide. Plain-language
     ("Coles is a store, not a merchant"). Pre-release → no compat shims,
     one migration, one mechanical pass. Sanity-check first that no
     existing `Store` symbol in the codebase already means something else
     (Pinia store, etc.); locations is adjacent but unambiguous.
  2. **Single management page in settings.** User-curated list. **No
     prefilled stores** (sidesteps locale-coupling + the legal-logos
     issue). **No auto-create** from any other code path — notably the
     ingestion API must respect this (see FU-190). Edit / disable /
     delete with referential safety against existing offers + shopping
     lines.
  3. **Per-store image upload.** Reuse the existing image-upload infra
     (recipes/stock items already use it from C-cross §2.8). **Dora
     ships zero logos** — legal safety. Fallback when no image: the
     existing hash-swatch + initial pattern from `ProductSearchCard`
     (referenced in ENGINEERING_STANDARDS.md).
  Full rationale in `docs/99_scratch/MINIMAL_USER_PRODUCTS_OFF_FRICTION.md`
  §4. Note: a `StockItem.usual_merchant_id` (rename → `usual_store_id`)
  nullable field also lands here — see FU-182's brainstorm scratch §3 for
  the shopping-list grouping use case.
- **Why deferred:** Cross-cutting refactor + new image-upload consumer +
  ingestion implication. Needs scheduling alongside the simple-mode sweep
  (FU-182) since they share data-model territory.
- **Recommended resolution:** schedule as a dedicated work unit before
  FU-182's per-surface sweep, since simple mode's shopping-list grouping
  depends on `usual_store_id` existing. Earlier still if the C-cross §2.6
  feature-flag panel work picks up first.

## [OPEN] FU-182 — Treat the minimal/Products-off user as a first-class workflow
- **Raised:** 2026-06-14 (talk-time assessment); refined 2026-06-15 (round 2); **promoted to proposal 2026-06-15** — see `docs/04_proposals/PROPOSAL_SIMPLE_MODE.md`. This ledger entry now tracks **co-design + implementation**, not the writing phase.
- **Type:** open decision / design follow-up
- **What:** Audit every surface for the "Products feature off" path and treat
  the minimal user (pantry + recipes + meal plan + checklist shopping list,
  no merchants/offers/price-history/cart) as a first-class workflow — not a
  fallback that empties out around them. **Principle:** minimal users must
  be supported as much as power users — same charter-level care, not a
  degraded fallback.

  Full discussion + model + UX decisions in
  `docs/99_scratch/MINIMAL_USER_PRODUCTS_OFF_FRICTION.md` (initial assessment
  + the 2026-06-15 addendum). Headlines from round-2:
  - **Pricing model reframe** — `StockItem` + `StockItemPriceObservation` is
    the universal substrate; `Product` + `ProductOffer` is an optional
    overlay feeding the same substrate. Unify read paths, never flatten.
    Mode-flips non-destructive both ways (scratch §1).
  - **Shopping-list-as-receipt** with stock-item-level price entry, gated by
    money opt-in (not Products). Log-a-price affordances also outside
    shopping (stock-item detail, quick-add). (Scratch §2.)
  - **Observations carry no merchant** in simple mode — "your paid price
    over time," not cross-merchant comparison. Shopping-list grouping uses
    `StockItem.usual_store_id` (single nullable field) + per-line override.
    (Scratch §3 — depends on FU-189.)
  - **Stock-item-vs-product confusion** is the real UX risk — layered
    mitigations: onboarding explainer copy (milk example, "don't name stock
    items after brands"), glossary entry, in-context micro-copy on stock-
    item-create, empty-state copy on My Products. (Scratch §5; pointer
    notes added to PROPOSAL_ONBOARDING.md §3.3 + PROPOSAL_HELP_OVERLAY.md
    §2.3.)
  - **"Simple mode" as a named identity**, not the absence of Products.
    UI label decoupled from the `products_enabled` flag. (Scratch §6.)
  - **Money + Products are independent layers (2×2).** Open thread for
    onboarding: the C-5 v3 personas bundle products+money; ensure the
    (Products off + money on) combination is reachable via Customise, or
    add a fourth preset. (Scratch §1 tail; flagged in
    PROPOSAL_ONBOARDING.md §3.2.a.)

  **Update 2026-06-15 (C-5 design):** the upstream pieces are now spec'd in
  `IMPL_PLAN_ONBOARDING.md` — **C-5.3** introduces the **`products_enabled`**
  install flag + the **3-persona fork** (Cooking / Savings / Everything) that
  sets it and branches the wizard (Cooking skips the stock-vs-product
  explainer). FU-182's **remaining** scope therefore narrows to the
  **per-surface Products-off sweep**: nav/tabs/columns removed not greyed;
  shopping-list checklist mode; stock-item-detail + recipe-ingredient
  product affordances hidden; settings sections hidden; stock-value report
  + recipe cost estimate rebased on the substrate; "Simple mode" chip in
  settings — i.e. *consume* the flag C-5 ships.
- **Why deferred:** Talk-time scope. Needs promotion to a proper proposal
  (or amendment to PROPOSAL_CONFIG_AND_OPTINS.md §2.6) with a per-surface
  coverage table before any code lands.
- **Recommended resolution:** later during Phase 3 polish — promote the
  scratch into a `04_proposals/` amendment to PROPOSAL_CONFIG_AND_OPTINS.md
  (or a sibling proposal). Sequence after FU-189 (stores rename +
  `usual_store_id`) since the simple-mode shopping-list grouping depends on
  it.

## [OPEN] FU-181 — Wire actual plan-emailing + a `meals_per_week` preference
- **Raised:** 2026-06-14 (C-2.J sequential builder)
- **Type:** follow-up (deferred sub-feature)
- **What:** Two small loose ends from the sequential builder (C-2.J):
  1. **Plan email** — the builder's done-step **Email button is shown disabled**
     ("isn't set up yet", per R-014). Actual emailing of a plan / its shopping
     list isn't built (`useMealPlanExport` only does print). Wire it to the
     existing email infra (INV-4 / `emailer`), SMTP-gated: enable the button
     only when email is configured for the install, otherwise keep it
     disabled-with-a-hint (R-014). The proposal §6 also lists email on the
     recurring/template flows — same backing.
  2. **`meals_per_week` pref** — the builder's target count is hardcoded to 7
     (proposal §6 wanted "user's `meals_per_week` if set, else 7"). No such
     user/household field exists yet. Add it (household-wide, like the slot
     vocab) + have the builder read it. Minor; the 7 default works fine
     meanwhile.
- **Recommended resolution:** opportunistic — pair the email work with the
  broader email/INV-4 effort; the `meals_per_week` pref with the next
  settings/onboarding touch (C-5 seeds it).

## [OPEN] FU-180 — Reassess "preferred product" before commercialise (Phase 4)
- **Raised:** 2026-06-14 (preferred-product removal sweep)
- **Type:** open decision
- **What:** `StockItem.preferred_product_id` was removed end-to-end this
  session — column dropped, two sort orders degraded to `cheapest → name`,
  barcode lookup collapsed to the m2m fallback, stock-value report rebased on
  cheapest most-recent linked-product price. The original concern was your
  own (feedback L131 — "Not sold... fluff vs noise"), and the manual per-item
  annotation never earned its keep at this stage of the build. **Open
  question:** once the rest of the app is built out (and the cart-button
  picker, shop-mode, and stock-value report have real usage data), revisit
  whether a "preferred *product*" or "preferred *merchant*" affordance is
  worth adding back. The original spec wanted preferred *store/merchant*
  (Feature Board L66, Unprocessed-Ideas #48/49/52) — a different shape from
  the per-product field we deleted, and arguably more defensible because one
  merchant choice would travel across all products from that merchant.
- **Why deferred:** the existing design instinct (cart-button proposal open-Q
  2: "always show the picker; preferred only pre-selects") means even a
  rebuilt preferred only changes *order*, not *behaviour* — which cheapest-
  first already does for free. Only worth revisiting if real usage shows
  users wanting to express brand loyalty / size preference / allergen
  avoidance and the current sort isn't getting them there.
- **Recommended resolution:** later — end of app build (Phase 3 polish or
  the first Phase 4 commercialise pass). Inputs to weigh: (a) any signals
  in feedback that users wished they could pin a specific product; (b) the
  cart-button picker's actual UX with cheapest-first sort; (c) whether a
  preferred-*merchant* model (one annotation, app-wide) earns its keep
  better than the per-stock-item preferred-product we just deleted.
- **Update 2026-06-15 (C-5 onboarding design):** the onboarding **preferred-stores**
  capture (feedback L45) was **dropped** and folded into this reconsideration — per the
  user, it's the same uncertain bucket (stock-items-only friction + whether the companion
  app ships, which would otherwise force custom/receipt product entry). So this FU now also
  owns: **does onboarding ever capture preferred stores/merchants, and what would they
  do** — revisit alongside the preferred-product question when the cart/companion surfaces
  make a merchant preference earn its keep. (Merchant currently has only `name`; no
  `is_enabled`/`preferred` field exists.)

## [OPEN] FU-179 — Browser-verify the whole Meal Plans surface (C-2 — all chunks)
- **Raised:** 2026-06-14 (C-2.A…J — full redesign, static-only verified)
- **C-2.J sequential builder:** the planner header's "Plan step-by-step" opens a
  3-step flow (pick meals → buy-vs-have preview → build & generate list) ending
  on a done step with Print (Email shown disabled). Confirm: cancelling writes
  nothing; the preview's buy/in-stock split matches the sidebar; build spreads
  meals across the week's upcoming days + the generate-list choice modal fires;
  Print opens the week's print view.
- **C-2.G sets + recurring + manage page:** the Manage Templates page
  (`/meal-plans/templates`, via the planner's "Manage templates") lists templates
  (rename/clone/delete) + sets (new/edit-with-up-down-reorder/delete); the
  planner's "Apply recurring…" applies a template or a rotating set over a week
  range (≤26 weeks; toast shows weeks/meals/skipped). Confirm a set rotates
  templates week-by-week and the 26-week cap + "pick exactly one source" errors
  surface as toasts.
- **C-2.F templates additions:** right-column Templates card — "Save this week
  as a template" (only when the focused week has meals) → name + description
  dialog; "Apply a template…" lists templates, forks the chosen one onto the
  focused week (past days skipped; toast shows added/skipped counts) and warns
  before replacing existing future meals. Confirm editing/deleting a template
  leaves a week forked from it untouched.
- **C-2.I trays additions:** left column groups into Favourites · Haven't-had
  (oldest/never first) · Frequently-planned · All recipes; curated trays hide
  when empty; searching collapses to a single "Results" tray; rows still
  pick/drag/±/log-cook in every tray. Spot-check the 21-day "haven't had" window
  (a recipe cooked 25 days ago shows; one cooked yesterday doesn't) and that
  "frequently planned" ranks by how often it's been put on plans.
- **C-2.H sidebar additions to the checklist:** each needed-ingredient row shows
  its list status ("on <list>" / "not on a list") + an add-to-list button that
  reflects on-list state and opens the picker on multi-list; hovering a row
  (desktop) outlines the meals that use that ingredient; the per-item stock
  chips now use the **app-wide colours** (intentional change — confirm they read
  sensibly and match Stock/Cookbook). Membership loads on the planner (the
  add-button + status aren't blank).
- **C-2.D calendar additions to the checklist:** the right-column calendar shows
  ~6 weeks; **status underlines** are correct (green planned / amber short /
  dotted-grey all-consumed / none empty); **today** has a dot; the **focused
  week** is outlined; clicking a week jumps the carousel (and vice-versa keeps
  them synced); the month banner + earlier/later arrows page the window;
  reloading with `?monday=YYYY-MM-DD` resumes on that week; the old "Jump to a
  plan" dropdown is gone.
- **Type:** finding (verification gate)
- **What:** C-2.C rebuilt `MealPlansOverview.vue` (3-column carousel) and passed
  vue-tsc + eslint, but the interaction layer needs a human pass. Checklist:
  1. **Carousel nav** — up/down arrows, ↑/↓ keys, and mobile swipe move weeks
     with a slide animation; `prefers-reduced-motion` disables it; `weekRangeLabel`
     updates.
  2. **Tap-add** — tap a day's slot (it highlights + the left banner shows the
     target), tap a recipe → entry lands in **that** slot (NOT always "Dinner",
     F35). Re-adding the same recipe to the same slot **increments servings**.
  3. **Drag** — on desktop, drag a recipe onto a slot adds it; on touch, drag is
     disabled and tap-add works (verify no scroll-jank).
  4. **Implicit create** — first add to an unplanned week silently creates the
     plan; the sidebar switches from "no meals planned" to the shopping summary.
  5. **Inline servings** — the chip menu's ± stepper adjusts servings live and
     removes the entry at 0; view/cook/remove work.
  6. **Past days** dimmed + reject taps/drops; **Today** badge on the right day;
     **the Thu-8am-AEST drop repro** (F29) no longer 400s (ties to C-2.K).
  7. **Left list** — search filters; "N free" + inline ± pool stepper + log-cook
     work; no cookable colour/check.
  8. **Off-vocab** — an entry with a deleted/legacy slot renders under "Other".
  9. **Sidebar/generate** still work bound to the focused week; "Jump to a plan"
     dropdown focuses the chosen week; "Clear this week" empties it.
- **Recommended resolution:** end-of-build browser pass (bundle with FU-032 /
  FU-135 / the timezone verify).

## [OPEN] FU-178 — Full-chain SQLite `flask db upgrade` is broken (batch-mode constraint naming) — prod-SQLite boot blocker
- **Raised:** 2026-06-14 (surfaced by C-2.K's scratch-DB migration check)
- **Type:** finding (pre-existing defect; **blocks fresh SQLite prod boot**)
- **What:** Running the migration chain base→head on a fresh SQLite DB fails at
  **`d7c9e4a8c2b1_20260612_shopping_list_line_product_anchor.py:29`** —
  `with op.batch_alter_table('ShoppingListLine')` raises
  **`ValueError: Constraint must have a name`**. Alembic batch mode on SQLite
  recreates the table and re-adds its constraints; with no `naming_convention`
  configured, an unnamed constraint on `ShoppingListLine` can't be reproduced.
  Likely **several** later batch migrations share the issue (e.g. the
  `recipe_ingredient_optional` b9e5c2a78f31 batch `add_column` on
  `RecipeIngredient`, the FU-163 `drop_finish_snapshot` batch op on
  `ShoppingList`) — the chain just dies at the first one.
- **Why it went unnoticed:** dev + tests use `db.create_all()` (table_mappings),
  never the migrations. Only the **prod, non-debug** path runs `upgrade()`
  (`startup.py:107`). So a fresh **self-host SQLite prod** install fails to boot.
  **Postgres is unaffected** (batch mode is a passthrough there — real ALTER, no
  table recreation), so the standard target (R-005) still boots.
- **Recommended resolution:** **before any SQLite prod release.** Systemic fix:
  add a SQLAlchemy `MetaData(naming_convention=...)` (in `app.py` /
  `configure_mappings`) and pass `render_as_batch=True` + that convention in
  `migrations/env.py`'s `context.configure(...)`, then run a full base→head
  `upgrade` + `downgrade` on a scratch SQLite to confirm every batch migration
  reproduces its constraints. Cross-ref R-005/R-006. (C-2.K's own migration was
  switched to a plain `op.add_column` so it does **not** depend on this fix.)

## [OPEN] FU-177 — Pre-existing ESLint errors block `npm run build`
- **Raised:** 2026-06-14 (surfaced by C-2.A adversarial review)
- **Type:** finding (pre-existing debt)
- **What:** 5 ESLint errors exist on the current tree, **unrelated to C-2.A**
  (verified identical on a stashed clean tree): `useFeatureFlags.ts:31`,
  `useStockFilters.ts:75` + `:92`, `RecipeDetailPage.vue` (~`:1117`),
  `AboutSettings.vue:82`. `npm run build` runs ESLint first and **aborts on
  these before reaching `vue-tsc`**, so a production `quasar build` currently
  fails. `vue-tsc --noEmit` itself is clean.
- **Why deferred:** out of C-2.A scope (R-007); they live in unrelated files.
- **Recommended resolution:** **soon** — a focused cleanup before the
  end-of-build browser-verification pass (a broken `build` blocks shipping the
  polished page). Investigate each (likely `no-unused-vars` /
  `no-explicit-any`-class); fix or justify per the lint config.

## [OPEN] FU-176 — Apply R-014 (reveal-and-disable) app-wide
- **Raised:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS review; new rule R-014 / ADR-009)
- **Type:** follow-up
- **What:** New engineering rule **R-014** says adoptable features that aren't
  yet configured/enabled should be **shown disabled with a "not set up" hint**,
  not hidden — so users discover they exist. The meal-plan builder's Email
  button adopts this in C-2.J. The rest of the app needs a sweep: most notably
  the **scanning button**, which today is *hidden* when `scanning_enabled` is
  off (ADR-002) and per the user should now render **disabled-with-a-hint**
  instead. Audit other gated/`v-if`-hidden adoptable surfaces (LLM/assistant
  affordances, any integration entry points) and convert the *presentation* of
  the off state from hidden → visible-disabled where it makes sense (R-014
  carve-outs: genuinely inapplicable or security-sensitive surfaces stay hidden).
- **Why deferred:** out of the meal-plans scope (R-007); it's a cross-cutting
  presentation change touching the scanning gate + others.
- **Recommended resolution:** opportunistic / a focused small sweep — pair with
  the next touch of each gated surface, and update ADR-002's note to point at
  R-014 for the presentation of the off state.

## [OPEN] FU-175 — Assess a purpose-built "bulk edit the week" meal-plan action
- **Raised:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS review; C-2.E retires MealPlanEditDialog)
- **Type:** follow-up
- **What:** C-2.E deletes `MealPlanEditDialog` — inline servings/slot edit on
  the carousel + implicit create-on-tap cover its jobs. The user wants a
  *purpose-built* bulk-week action assessed separately (it "may not even need a
  modal"): e.g. select multiple entries on the canvas and bump servings /
  reslot / remove in one go, or a compact week-table editor. Assess the real
  need (does inline editing already make this unnecessary?) before building.
- **Why deferred:** the canvas inline-edit (C-2.C) may already satisfy the need;
  building a bulk surface now would be speculative (Anti-creep).
- **Recommended resolution:** after C-2.C/E land and the inline-edit UX has
  been used — assess whether a bulk action earns its place; design a brief if so.

## [OPEN] FU-174 — App-wide datetime / timezone correctness sweep (household tz)
- **Raised:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS review; C-2.K)
- **Type:** deferred job (large)
- **What:** C-2.K introduces `AppSetting.timezone` (household IANA tz) and
  evaluates the meal-plan "today" boundary **in the household timezone**
  (server-owned, exposed to the client) so a household anywhere in the world is
  correct regardless of where the server is hosted — fixing the past-day-drop
  400 (F29) properly rather than with a local patch. The same correctness is
  needed **everywhere dates/date-boundaries matter**: every `date.today()` /
  server-local date use (the reconcile hook, shortfall deadlines, alerts,
  dashboard "next up", any "N days ago/until" logic) and every client-side
  `toISOString()`-derived "today". Datetime is tricky (DST, offsets, storage in
  UTC vs local) — this is a careful, app-wide sweep.
- **Why deferred:** out of the meal-plans scope (R-007); C-2.K lands the
  mechanism for the planner surface only.
- **Recommended resolution:** a focused sweep after C-2.K proves the mechanism.
  **Promote the household-tz date rule into an ADR + a new `R-0NN`** at that
  point (the standard: date-boundary logic evaluates in the household timezone,
  never server-local or client-`toISOString()`). Cross-ref ADR-007 (ISO
  serialisation) — that's the wire format; this is the boundary semantics.

## [OPEN] FU-173 — Slot-vocabulary "remap legacy entries" UI — deferred
- **Raised:** 2026-06-14 (authoring IMPL_PLAN_MEAL_PLANS — C-2.A scope call)
- **Type:** deferred job
- **What:** `PROPOSAL_MEAL_PLANS.md §4 / §11.4` describes a one-shot
  "remap legacy/off-vocabulary `MealPlanEntry.slot` strings to the user's
  current slot list" action in settings. C-2.A deliberately ships the
  per-user vocabulary **without** it (off-vocab strings are preserved verbatim
  and rendered in an "Other" row, C-2.C) — Anti-creep: the cleanup earns its
  place only if real off-vocab data accumulates.
- **Why deferred:** no off-vocab data exists yet (slot is currently picked from
  a fixed 5-value constant); building the remap tool now is speculative.
- **Recommended resolution:** opportunistic — build only if users accumulate
  off-vocabulary slot strings after C-2.A ships the editable list.

## [OPEN] FU-171 — Recipe image hide/show toggle reported broken — no static repro
- **Raised:** 2026-06-13 (FU-088 → Cookbook card revision Chunk A §1.1)
- **Type:** finding (reported defect; didn't reproduce in code)
- **What:** User reported the "Hide/show recipe photos" toggle on the
  Cookbook overview doesn't work (FU-088 bullet 1). Static trace through
  the full chain looked correct end-to-end:
  - `RecipesOverview.vue:21-33` — `BaseButton` with reactive `:icon` and
    `@click="onToggleRecipeImages"`.
  - `onToggleRecipeImages` → `setRecipeImages` → `authStore.updateMeAsync`
    reassigns `currentUser.value` from the PATCH response (`authStore.ts:81-83`).
  - `useImagePrefs.ts:23-25` — `showRecipeImages` computed reads
    `currentUser.value?.show_recipe_images`.
  - `RecipeCard.vue:15` — `v-if="showRecipeImages && recipe.has_image && !imgFailed"`.
  - Backend `update_me.py:162-163` writes the field;
    `register_user.py:112` (DTO) always emits it.
- **Recommended resolution:** **confirm in browser** after Chunk A ships.
  If still broken, capture: (a) does the icon flip on click? (b) does the
  PATCH succeed (network tab)? (c) does the response body include
  `show_recipe_images`? (d) does any card re-render? — that will pinpoint
  which link in the chain breaks at runtime.
- **State note:** open — no code change in Chunk A (no repro to fix). The
  Chunk A card rewrite preserves the same `v-if` gate.

## [OPEN] FU-170 — App-wide button display preference (icon-only / icon+text / mixed)
- **Raised:** 2026-06-13 (FU-088 cookbook card revision — Cook button went icon-only `mdi-chef-hat` per user choice; want this controllable user-wide)
- **Type:** new feature
- **What:** A single user preference (Settings → Appearance, alongside the existing image-display opt-in) controlling how primary action buttons render across the app:
  - **Icon only** — every action button is `flat`/`round` (or `unelevated` for primary) with no label; the verb lives in the tooltip.
  - **Icon + text** — every action button shows both icon and label.
  - **Mixed** (default, recommended) — a curated per-button policy: high-frequency / unambiguous actions (Cook, favourite, add-to-list on the recipe card, ± steppers) go icon-only; less-frequent / verbier actions (Save, Cancel, Create recipe, Delete, Mark cooked, Confirm) keep their labels. The policy is defined once in code, per button, not at the call site.
- **Why:** the cookbook revision (Chunks A–C) introduces the first deliberately icon-only primary button (Cook = chef hat). Without a system-level preference, users who prefer verbose UIs lose the verb entirely, and ad-hoc "should this have a label?" calls drift across the app over time.
- **Shape (sketch — to be designed in a brief):**
  - User-prefs field `button_display: 'icon_only' | 'icon_text' | 'mixed'`, default `'mixed'`.
  - A thin `<AppActionBtn>` wrapper (or a `useButtonDisplay()` composable) that reads the pref + the button's per-instance policy hint (`prefer="icon-only" | "icon-text" | "auto"`) and decides whether to render the label. Existing `q-btn` call sites migrate gradually.
  - Tooltips become mandatory on any button whose policy allows icon-only rendering (accessibility — screen readers still get the verb).
  - Per-button policy lives in a small registry/enum so policy changes are one-line edits, not codebase-wide grep-and-replace.
- **Scope notes:**
  - Footer/toolbar buttons (sticky footer A7, modal action rows A3) are in-scope.
  - Menu items (`q-item`) are out of scope — they need labels for legibility.
  - Settings page itself is out of scope — it uses long-form forms, not action buttons.
- **Recommended resolution:** after the cookbook card revision (Chunks A–C) lands and we have lived with at least one icon-only primary button for a few days. Write a short brief first (charter cross-check: Effortless + Anti-creep — this is a knob, justify it doesn't feel like one), then implement as a small standalone chunk.
- **State note:** open — no brief yet, no code.

## [OPEN] FU-169 — Implement the test-suite improvements proposal
- **Raised:** 2026-06-13 (post-FU-166 proposal)
- **Type:** deferred job
- **What:** `docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md` — phased
  plan to make the suite a trustworthy net: **Phase 1 (P0)** CI runs all tests
  (not just `tests/e2e/dora_api`) + pytest config (`xfail_strict`,
  `filterwarnings`, markers) + `pytest-cov` + shared `assert_problem`/
  `assert_envelope` matchers + one naming convention; **Phase 2** per-test DB
  rollback (isolation → kills order coupling, enables `xdist`) + data
  factories + parametrize; **Phase 3** close the 24 untested API surfaces +
  domain/repository/contract tests; **Phase 4** frontend Vitest +
  `merchant_api`/`emailer` fixture tests + Hypothesis + Postgres CI.
- **Why deferred:** sizeable; needs user prioritisation. Each phase ships
  independently green.
- **Recommended resolution:** start **Phase 1** opportunistically (half-day,
  no-regret); sequence the rest per the proposal. Relates to FU-045 (Postgres
  CI, Phase 4) and FU-161 (Aldi scraper — Phase 4 gives it a net).

## [OPEN] FU-165 — Browser-verify shopping-list UX v2
- **Raised:** 2026-06-12 (UX v2 build session)
- **Type:** finding (verification gate)
- **What:** UX v2 shipped with lint + vue-tsc clean and all 21 shopping e2e
  tests passing, but the visual/interaction layer needs a human pass in the
  running app. Checklist: rail order + auto-scroll + next-up marker; mobile
  dropdown; rename → clear name → list self-labels (and re-labels when the
  shop day changes); shop-day button tones (today/overdue); doughnut +
  totals; Start shopping → sticky footer → restock-review modal (incl. a
  per-item level tweak) → Reopen reverses it; quick-add mid-shop; row
  actions (price button, swap, remove); group-by; bulk select; print view;
  no empty-state flash on load; **drag-reorder lands on the exact row you
  drop on (FU-161)**; dashboard card + Dora-chat add-to-list still work
  (both were touched).
- **Recommended resolution:** now — first browser session after this lands.

## [OPEN] FU-161 — Shopping list drag-and-drop "index off" (feedback L414) — confirm in browser
- **Raised:** 2026-06-12 (shopping-list UX design session; original report L414, 06-Jun feedback)
- **Type:** finding (reported defect, not reproduced in static read)
- **What:** "Drag and drop is an index off somehow (wrong items being swapped)."
  *2026-06-12 update:* a deeper read found the fix **already shipped in P6-01
  Chunk 6** — `onLineDrop` carries a comment explicitly correcting the
  "subtract 1 when dragging down" off-by-one, and UX v2 preserved that logic
  verbatim. Per the reported-defect rule it stays open until verified in the
  running app (now part of the FU-165 checklist).
- **Recommended resolution:** confirm in browser (FU-165).

## [OPEN] FU-161 — Check / upgrade the Aldi scraper (site appears updated)
- **Raised:** 2026-06-12 (user note during Phase 1 wrap-up)
- **Type:** deferred job
- **What:** User flagged that Aldi's website appears to have
  changed; the existing Aldi scraper in the companion / merchant
  scraping module likely needs revisiting. Concrete steps when
  picked up:
  1. Hit a representative Aldi product page in a browser, compare
     the live DOM to what the scraper's selectors expect.
  2. Run the scraper against a known SKU and inspect the result
     (price, size, on-special detection) — note any fields that
     come back null / wrong / missing.
  3. Decide whether it's a selector tweak or a structural
     rewrite. Aldi historically uses a different layout from
     Coles/Woolworths, so changes there can ripple more than a
     simple class rename.
  4. If structural: cross-check the merchant scraping posture
     (`RECONCILED_FINISHING_PLAN.md` Decision 1 — scraper is the
     companion-app-only path; the core repo doesn't ship live
     scrape).
- **Why deferred:** out of scope of the current finishing-pass
  stream; needs live URLs + the companion app to investigate
  properly.
- **Recommended resolution:** opportunistic — when the user
  next needs Aldi pricing data, or as a focused session in the
  companion repo.

## [OPEN] FU-160 — Shopping-list "shopping day" alert (feedback L403)
  *(2026-06-12: now unblocked — the shop-day button + ISO date serialisation
  landed with UX v2; only the alert wiring remains.)*
- **Raised:** 2026-06-12 (re-surfaced during shopping-list buggy-merge audit)
- **Type:** deferred job
- **What:** Feedback L403 asked for an alert when a list's planned shop date
  is *today* / imminent. Depends on FU-159 (planned-shop-date UI) and the
  existing alert pipeline. Not built.
- **Recommended resolution:** opportunistic — bundle with FU-159 once that
  field is surfaced, or queue as a small follow-up once we have a planned
  shop date to fire against. *2026-06-12 update:* fire after FU-162 step 1
  (shop-day button) lands; see `PROPOSAL_SHOPPING_LIST_UX_V2.md` §9.

## [OPEN] FU-154 — Page-local product/stock collections bypass their stores (R-003 smell, likely widespread)
- **Raised:** 2026-06-12 (during FU-014 image-bug investigation)
- **Type:** finding
- **What:** `MyProductsPage.vue` keeps its own local `products = ref<Product[]>([])`
  populated by a direct `productApi.getAllAsync()` in `onMounted` (line 583/1070),
  bypassing `productStore.products` entirely — even though `ProductSearch.vue`'s
  save goes through `productStore.createProductAsync()` which keeps the store
  fresh. Result: a product saved on the search page doesn't appear on My Products
  until the user hard-refreshes the page (confirmed by user, 2026-06-12). This is
  a textbook R-003 (state-ownership / single source of truth) violation — two
  sources of truth for the same domain collection.
- **Why it's likely widespread:** the same pattern (page-local `ref<T[]>` +
  direct API call in `onMounted` for a collection that has a Pinia store) almost
  certainly exists on other pages. Quick suspects to audit:
  - `DashboardPage.vue` (modified in current branch)
  - `StockOverview.vue`, `StockItemDetailPage.vue`
  - `RecipesOverview.vue`, `RecipeDetailPage.vue`
  - `MealPlansOverview.vue`, `WastePage.vue`
  Audit method: grep for `= ref<.*\[\]>\(\[\]\)` + `\.getAllAsync\(\)`
  / `\.get.*Async\(\)` inside `pages/` and cross-reference what Pinia store
  already owns that collection.
- **Confirmed problem area:** `web_app/src/pages/MyProductsPage.vue` (lines
  583, 587–607, 1070). Saved product invisible until refresh.
- **Recommended resolution:** scoped Wave-A-ish prompt — (1) audit all `pages/`
  for the pattern, (2) for each hit, replace the local ref + onMounted-fetch with
  `storeToRefs(theStore)` + `theStore.refresh()`-equivalent, (3) make sure the
  store's create/update/delete methods refresh state so reactivity is automatic.
  Don't relocate fine client-only computeds (per R-003 addendum). Treat
  `MyProductsPage` as the canonical fix to copy.
- **Cross-ref:** ENGINEERING_STANDARDS R-003 (state ownership).

## [OPEN] FU-153 — Assistant LLM config: per-user, reachability probe, multi-provider
- **Raised:** 2026-06-12 (user feedback during FU-085 verify)
- **Type:** design / proposal addition (no code yet)
- **What:** `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md §7` (new
  section, this session) captures four interlocking changes to
  the LLM client + config side, distinct from the §1–6 routing
  refactor:
  1. **§7.1 Per-user LLM config** — drop the singleton
     `AppSetting.llm_*` and move it to `User.llm_*` (+ a
     `master_llm_enabled` install-wide kill switch on
     AppSetting). Households with two desktops each running
     their own LLM stop sharing one URL.
  2. **§7.2 Reachability probe** — new `GET
     /api/assistant/ping` hit **once per chat open** (not per
     message, not on a poll). Visible "AI mode unavailable —
     using basic mode" banner + Retry when the user's
     `llm_enabled` is true but their LLM doesn't answer.
  3. **§7.3 Network-topology constraint** — document that the
     backend (not the device) reaches the LLM URL. Operator
     concern for household / remote-LLM setups; pure
     documentation, no code.
  4. **§7.4 Multi-provider** — abstract `LlmClient` with
     `OllamaClient` (existing, moved) + `OpenAiClient` +
     `AnthropicClient` + `GeminiClient`. Per-user
     `llm_provider` enum + encrypted-at-rest API key column.
     Different tool-call schemas adapt to a shared shape
     before reaching `tools.py`.
- **Sequencing (§7.5):** one migration ships §7.1 + §7.4
  schema columns; provider implementations follow per-PR;
  §7.2 probe lands last (cheap once per-user config is
  available); §7.3 is docs only.
- **Existing DORA-BOT feedback cross-ref (§7.6):** the
  per-user mode toggle / "turn the bot off completely" /
  "disabled if unavailable" items in `Feedback _ Fixes - as
  of [06-Jun-2026].md` lines 452-460 pair directly with §7.1
  + §7.2 — the toggle UI visibly reflects the probe result.
- **Recommended resolution:** treat as the next chunked
  IMPL plan after the FU-152 routing redesign (or before;
  they're orthogonal but the per-user config is a
  pre-requisite for the rules-router-per-user too). Pair
  with the AI-mode design pass.
- **State note 2026-06-12:** **user signed off** on §7.1–§7.4
  as written, with one refinement folded into §7.1: the
  per-user Assistant config lives in
  `PreferencesSettings.vue` next to the existing C-cross
  per-user toggles (`money_features_enabled`, etc.) — not a
  net-new settings page. §7.3 (network-topology docs) was
  explicitly accepted as "same connectivity story as the rest
  of the app, nothing special". Next step: draft an IMPL plan
  from §7 when this work is sequenced.

---

## [RESOLVED-MINIMAL] FU-150 — Assistant chat-mode doesn't recognise dietary/cuisine queries
- **Raised:** 2026-06-12
- **Resolved (step 1, this session):** rule-based first-match-wins
  matcher kept, but the `find_recipe` intent's trigger list now
  catches the bare-noun cases ("i need a recipe", "any breakfast
  ideas", "show me a vegetarian recipe", etc.) — and the handler
  was rewritten to **stop yanking "the bit after a preposition"**
  and instead tokenise the whole message (minus stopwords) and
  substring-match each token against name + cuisine + category +
  timeOfDay + dietaryTagNames. Vocab arrives via the extended
  `RecipeSnapshot` (`dietaryTagNames`, `timeOfDay`) hydrated in
  `DoraChat.vue` from the existing Pinia stores; vocab preload
  was added to `ensureRecipeData()`. Net effect: "i need a
  vegetarian recipe" → routes to find_recipe, filters by the
  'vegetarian' dietary tag, lists the top matches. "Asian
  breakfast recipe" → both 'asian' + 'breakfast' must hit
  (cuisine + timeOfDay). Reply echoes the tokens it filtered on
  so the user sees what was matched.
  **Limitations of step 1 (kept as the structural follow-up FU-152):**
  the matcher is still keyword-list + token-substring, with no
  proper slot extraction or query parser. Stopword list is
  hand-coded; synonyms ("veggie" → "vegetarian") aren't resolved;
  composite phrases ("gluten free" survives because the tag name
  matches, but two-word tags + free-text terms in the same
  message can produce surprising AND-filters). The redesign in
  FU-152 spec's the real fix; this RESOLVED-MINIMAL fixes the
  user-visible "vegetarian"/"asian" failure mode now.

## [OPEN] FU-152 — Chat-mode design: tokenise → slot-extract → filter (structural)
- **Raised:** 2026-06-12 (offshoot of FU-150's minimal fix)
- **Type:** design / structural improvement
- **What:** The current chat is a "first-match-wins keyword
  matcher" with hand-curated `matches[]` per intent + a handler
  that pulls "the noun after a preposition" and substring-searches
  recipe fields. FU-150 step 1 broadened the trigger list +
  switched the handler to whole-message tokenisation, which is
  enough for the dietary/cuisine cases but still scales linearly
  in keyword count and produces brittle behaviour for compound
  queries.
- **Proposed redesign (two axes):**
  1. **Vocab-derived triggers.** Load Cuisine + DietaryTag +
     Tool catalogues at chat init. Each catalogue contributes
     its names to a "term → intent" prior so the matcher knows
     "vegetarian"/"asian"/"slow cooker" all route to
     `find_recipe`. Auto-updates when the user adds new vocab.
  2. **Slot extraction**, separate from intent detection. After
     the intent fires, walk the message once and capture
     `slots: {cuisines[], dietaryTags[], timeOfDay?,
     stockItems[], freeText}`. Handlers consume slots
     declaratively — `filterRecipes({ dietary: ['vegetarian'],
     cuisine: 'asian' })` — instead of doing ad-hoc substring
     searches.
  3. **Intent scoring (optional)**: replace first-match-wins
     with a scoring pass per intent (each contributes keyword
     hits + vocab hits + structural cues). Highest-score intent
     wins, tie → fallback. Catches "i'm hungry, what veggie
     thing can I make?" routing to `whats_for_dinner` with a
     dietary slot, rather than tripping `find_recipe` because
     "recipe"-ish keyword fired first.
  4. **Reply transparency**: show the slots the handler
     applied ("Filtering by: vegetarian + asian"). Already
     present in FU-150 step 1 via `queryDisplay`.
- **Why deferred:** step 1 covers the immediate UX failure; the
  full slot-extraction redesign is a separate, focused work
  unit. Pair with the AI-mode sweep — the slot extractor is the
  same shape of work whether the route resolves into the
  rule-engine handler or the LLM handler.
- **Recommended resolution:** later — pair with AI-mode design.

## [OPEN] FU-151 — Browser-verify FU-085 fixes (FU-147 dietary picker, FU-148/149 filters, FU-150 chat)
- **Raised:** 2026-06-12 (concluding the FU-085 verify pass)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **FU-147** — open the seeded "egg fried rice" recipe → its
     two dietary tags pre-populate the picker; saving with no
     edit doesn't clear them; adding/removing tags + saving
     round-trips (re-open the page shows the new set).
  2. **FU-148** — Cookbook overview "Time of day" dropdown
     filters to Breakfast / Lunch / Dinner / Dessert / Snack /
     Any. Clearable.
  3. **FU-149** — "# ingredients ≤" filter narrows the list;
     "# ingredients" sort axis orders ascending by default
     (fewest first); the direction toggle flips it.
  4. **FU-150** (step 1) — basic chat-mode:
     - "i need a vegetarian recipe" → lists vegetarian recipes,
       header says "Filtering by: vegetarian recipe" (or similar).
     - "i need an asian recipe" → cuisine filter applied.
     - "show me a breakfast recipe" → timeOfDay filter applied.
     - "i need a recipe" with no other terms → prompt asking
       for a name/ingredient/cuisine/tag (no fallback bank).
- **Recommended resolution:** next browser session.

## [OPEN] FU-146 — Sweep external GitHub-issues references — DONE
- **Raised:** 2026-06-12 (user browser verify of FU-085: "should
  remove any mention of github issues as the repo is now private")
- **Type:** finding / hygiene
- **What:** Dora-bot fallback bank, `report_issue` intent + its
  `externalLink`, the `whats_new` "See latest release on GitHub"
  link, `HelpPage` "Report a bug" header button + Help-tab repo
  list + issues list, `AboutSettings` repo + bug-report items,
  and `PageErrorState`'s pre-filled GitHub-issues URL all linked
  to `github.com/BenTalese/DiscountDora` — a now-private repo.
- **Resolved:** 2026-06-12 — replaced the FALLBACK_REPLIES bank +
  `report_issue` intros to drop the GitHub framing; retired the
  externalLink on `fallback` + `report_issue` (Help-nav stays);
  retired the `whats_new` release URL; pulled the four GitHub
  buttons/items from `HelpPage` + `AboutSettings`; retired
  `PageErrorState`'s `reportUrl` + the "Report this" button (the
  `showReport` prop stays so a self-host operator can restore a
  similar surface pointing at their own report sink).
  **Note:** the `report_issue` intent itself stays — it's a
  useful "I found a bug" affordance — but it now navigates to
  Help instead of pointing at an external tracker.

## [OPEN] FU-143 — Backfill `picked_offer_price` for legacy lines
- **Raised:** 2026-06-12 (State Ownership Chunk 6 impl)
- **Type:** deferred job (optional)
- **What:** Chunk 6 moved the offer-price snapshot from
  *tick* to *add* / *select*. Rows created before this change
  with a non-NULL `selected_product_id` but NULL
  `picked_offer_price` (never ticked) won't have a snapshot
  until the user later ticks them (the belt-and-braces hook
  at `manage_shopping_list_lines.py` UpdateLineHandler tick
  path + the finish-list fallback at `manage_shopping_list.
  py:212-215`). A one-off script could snapshot-fill every
  legacy row with `selected_product_id IS NOT NULL AND
  picked_offer_price IS NULL`, picking the current offer for
  the chosen product.
- **Why deferred:** Optional. The belt-and-braces paths drain
  legacy rows organically; nothing breaks if a never-ticked
  legacy row stays unsnapshotted (it just doesn't appear in
  budget / waste aggregates until ticked). At pre-release
  scale this is fine to skip.
- **Recommended resolution:** opportunistic — only worth
  doing if a user later complains "budget number doesn't
  match what's in my old draft lists". Then a small Alembic
  data migration or one-shot script clears the deficit in a
  single pass.

## [OPEN] FU-142 — Browser-verify State Ownership Chunk 6 (snapshot-at-add)
- **Raised:** 2026-06-12 (State Ownership Chunk 6 impl)
- **Type:** finding / verification
- **What:** Exercise the new snapshot timing end-to-end:
  1. **Add line with selected offer** — confirm budget's
     "projected_active" (or post-finish "spent") reflects the
     planning-time price; price the offer up via the
     companion app and confirm the snapshot is the *original*
     value, not the moved price.
  2. **Change `selected_product_id`** via the list detail
     page's offer chip — confirm the snapshot re-captures at
     the new offer's current price.
  3. **Clear selection** — confirm the snapshot clears (the
     line shows as "no priced intent" in any UI that
     surfaces it).
  4. **Tick** an already-snapshotted line — confirm tick
     does NOT overwrite the snapshot.
  5. **Untick** — confirm the snapshot persists (the
     commit-to-offer moment didn't un-happen).
  6. **Tick a legacy line** (one created before this chunk
     with `picked_offer_price` NULL) — confirm the
     belt-and-braces hook fills the snapshot the first time.
- **Why deferred:** static-only impl; needs the running app
  + a live offer to verify price-moved-between-states.
- **Recommended resolution:** confirm in browser — same
  high-priority slot as the other Chunk-N verify items.

## [OPEN] FU-140 — Sweep Cart Button Chunk 3 typing fallout (nullable `stock_item_id`)
- **Raised:** 2026-06-12 (State Ownership Chunk 4 typecheck)
- **Type:** finding / cleanup
- **What:** Cart Button Chunk 3 made `ShoppingListLine.stock_
  item_id` nullable (a product-only line carries `product_id`
  instead). The TS model followed, but at least two consumers
  type-checked only because no other change had triggered them:
  - `NewListDialog.vue:376` — `detail.lines.map(l => l.stock_
    item_id)` previously was `string[]`, now `(string|null)[]`.
    Fixed here with a typed `.filter` to keep the chunk's
    typecheck green.
  - `ShoppingListDetail.vue:2049` — the undo-snapshot path
    passed a possibly-null id to
    `removeByStockItemFromListAsync`. Guarded here so the undo
    only registers when the id is non-null.
  There are likely more call sites in `ShoppingListDetail` and
  the cook-mode finish that haven't been audited because
  TypeScript only flags them when another change exercises the
  expression.
- **Why deferred:** out of Chunk 4's documented scope (this
  is Cart Button Chunk 3 fallout). The two blocking sites
  were fixed inline; the sweep is the open item.
- **Recommended resolution:** opportunistic — fold into the
  next Cart Button or shopping-list touch. Could also be a
  one-shot `grep` sweep for `stock_item_id` reads on
  `ShoppingListLine` and a typed audit.

## [OPEN] FU-139 — Finish migrating `getStockLevelColour(name)` callers to `colourForSequence(seq)`
- **Raised:** 2026-06-12 (State Ownership Chunk 4)
- **Type:** follow-up / cleanup
- **What:** Chunk 4 introduced `colourForSequence(seq)` and
  migrated the *decision-driving* call sites. The legacy
  `getStockLevelColour(name)` was kept as a soft-fallback so
  ~5 surfaces with only a `level_name` (no sequence in scope)
  still compile:
  - `StockItemDetailPage.vue:16, 114, 126` (the q-chip in
    the header, the level-picker dropdown label, and the
    per-level avatar in that dropdown)
  - `RecipesOverview.vue:537` (`stockLevelColourFor`
    helper consumed by ingredient chips)
  - `RecipeDetailPage.vue:1326` (`levelColourFor`)
  - `QuickAddSheet.vue:195`
  - `CreateStockItemDialog.vue:43`
  - `MyProductsPage.vue:1053`
  Each is a small migration (give the helper the level row,
  read `.sequence`, call `colourForSequence`). Once they're
  all migrated, the legacy `getStockLevelColour` + its
  literal-case `switch` in `stockLevelLogic.ts` can be
  deleted, completing the purge.
- **Why deferred:** out of Chunk 4's documented scope (these
  are display-only colour lookups, not decision-driving
  comparisons). R-007 — flag, don't drift.
- **Recommended resolution:** opportunistic, or as a focused
  follow-on session. Each surface migration is mechanical
  (~5 lines). The full sweep closes the literal-fallback hole.

## [OPEN] FU-138 — Query-count test for `GET /recipes` (no N+1)
- **Raised:** 2026-06-12 (State Ownership Chunk 2 close-gate)
- **Type:** deferred job (test infra)
- **What:** The plan's §3 perf risk for Chunks 2–3 calls for an
  integration test that pins the recipe-list endpoint's SQL
  query count, so the set-based cookability / missing-names
  aggregations can't silently regress into N+1 lazy loads.
  `missing_stock_item_names_for` (Chunk 2) is N+1-free by
  construction (pure function over the already-loaded
  ingredient tree), but a runtime guard is still the right
  long-term shape — especially once `?cookable=true` (Chunk 3)
  hits the same query path.
- **Why deferred:** the project has no precedent for query-count
  tests (no SQLAlchemy `before_cursor_execute` harness, no
  baseline numbers). Building that scaffolding belongs with
  the chunk that adds the next hot endpoint, not with a pure
  field-add.
- **Recommended resolution:** **later during State Ownership
  Chunk 3** — fold the harness build into the `?cookable=true`
  end-to-end test so it pays for itself across both chunks.

## [OPEN] FU-135 — Browser-verify Cart Button Chunk 4 (meal-plan generate via Axis B)
- **Raised:** 2026-06-12 (Cart Button Chunk 4 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify the four-state matrix on the meal-plan
  "Generate shopping list for this week" button:
  1. **0 draft lists:** no picker; creates a new list named
     `Meals: <plan>`; success toast says "Shopping list created
     with N items."; routes to the new list.
  2. **1 draft list:** picker opens with that draft preselected +
     a "+ Create new list" row; OK on the draft → backend merges,
     toast says "Added N items to your list.", routes to that
     list.
  3. **2+ draft lists:** picker lists all drafts (first
     preselected) + "+ Create new list"; both an existing pick
     and the create-new pick work.
  4. **Cancel/dismiss:** aborts cleanly — no list created, no
     toast, no navigation.
  Also: `nothing_to_add` path still emits the info toast and
  *doesn't* navigate.
- **Why deferred:** static-only impl; needs a real meal plan +
  varied draft-list state.
- **Recommended resolution:** confirm in browser — same
  high-priority slot as FU-130 / FU-132.

## [OPEN] FU-134 — Audit other `autoGenerate` call sites for Axis-B routing
- **Raised:** 2026-06-12 (Cart Button Chunk 4 impl)
- **Type:** follow-up
- **What:** The meal-plan "Generate shopping list for this week" button
  now offers add-to-existing vs. create-new via Axis B. Three other
  `shoppingListApi.autoGenerateAsync` call sites were left alone:
  - `web_app/src/components/dialogs/NewListDialog.vue:416` — already
    explicitly picks/creates a target list before generating; no change
    needed (already Axis-B-aware by construction).
  - `web_app/src/pages/RecipesOverview.vue:1153` — recipe "add all
    missing to a new list" path. Acceptance candidate for the same
    treatment (the proposal puts recipe bulk-add under variant="bulk"
    via the `AddToListButton`, which is the longer-term home).
  - `web_app/src/layouts/MainLayout.vue:291` — global/keyboard
    shortcut entry. Check whether this should also offer Axis B or
    is intentionally always-new.
- **Why deferred:** out of Chunk 4's documented scope (`PROPOSAL_CART_
  BUTTON.md §5` surface 10 is meal-plan generate only). Scope discipline
  (R-007) — flag, don't drift.
- **Recommended resolution:** opportunistic — re-evaluate when the
  `AddToListButton variant="bulk"` work lands for recipes (FU-131
  vicinity) and again when the global shortcut surface gets touched.

## [OPEN] FU-133 — Promote generate-target picker into a shared `TargetListPicker`
- **Raised:** 2026-06-12 (Cart Button Chunk 4 impl)
- **Type:** follow-up (R-001 carve-out)
- **What:** `pickGenerateTarget` in
  `web_app/src/pages/MealPlansOverview.vue` is a one-shot `$q.dialog`
  radio picker (drafts + "+ Create new"). If a second surface needs
  the same shape (likely candidates: FU-134 audit, future bulk
  add-all-missing flows), extract it as
  `components/dialogs/TargetListPickerDialog.vue` with props
  `{ drafts, allowCreateNew, title?, message? }` and one resolved
  payload type `{ kind: 'existing', id } | { kind: 'new' } | null`.
- **Why deferred:** single consumer today — promoting now would be
  speculative abstraction (R-001 judgement carve-out).
- **Recommended resolution:** when FU-134's audit lands a second
  consumer.

## [OPEN] FU-132 — Browser-verify Cart Button Chunk 3 (standalone-product lines + rules 1–3)
- **Raised:** 2026-06-12 (Cart Button Chunk 3 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Migration applies cleanly** (`d7c9e4a8c2b1`) on both SQLite +
     Postgres; `verify_mappings()` passes for the now-nullable
     `stock_item_id` and the new `product_id` FK.
  2. **Rule 1** — POST `/api/shopping-lists/<id>/lines` with only
     `product_id` (no `stock_item_id`) creates a line; list-detail
     DTO carries `product_id` + null `stock_item_id`. CHECK
     constraint rejects a body with neither anchor (400 from the
     handler before DB).
  3. **Rule 2** — preconditions: a draft list contains a
     product-only line for product P; product P is not yet linked
     to any stock item. POST `/api/stock-items/<S>/products` with
     `product_id=P`. After: the orphan line is upgraded — its
     `stock_item_id` is now S (or it's been folded into an
     existing stock-item line for S, with that line's `product_id`
     set to P).
  4. **Rule 3** — preconditions: a stock-item line for S exists,
     plus a separate product-only line for P (where P is linked to
     S). DELETE the stock-item line by line-id → the nested
     product line is gone too. Same for the cart-button
     remove-by-stock-item path.
  5. **No regressions** on stock-item-only adds (the dominant
     case): existing dedupe by stock_item_id still wins.
  6. **TS compile**: `ShoppingListLine.stock_item_id: string | null`
     no longer breaks consumers (the obvious 3 spots in
     `ShoppingListDetail.vue` were null-guarded this chunk; FU-131
     covers the remaining inline-product surfaces).
- **Why:** schema change + multi-rule wiring + cascade is the
  highest-risk single chunk in the cart-button plan; the rules
  interact with the link-product handler + by-line + by-item delete
  paths.
- **Recommended resolution:** now (next session). Requires a real
  DB to exercise.

## [OPEN] FU-145 — Browser-verify Cart Button Chunk 3 UI (FU-131 follow-on)
- **Raised:** 2026-06-12 (FU-131 impl)
- **Type:** finding / verification
- **What:** Exercise the rule-4 modal + nested display +
  inline-product variant end-to-end:
  1. **Add a product-only line** via the My Products row
     ("Add as product" button) on an unlinked product →
     confirm the line lands with the product chip + tinted
     "product only" background.
  2. **Link the product to a stock item** later via the
     stock-item detail → confirm the parent stock-item line
     appears on the same list (rule 2 backend) AND that the
     product nests visually under it (rule 2 frontend).
  3. **Remove the nested product** → rule-4 modal fires;
     "Yes" removes both, "No" leaves the stock-item parent.
  4. **Remove a product-only line** whose linked stock item
     is NOT on the list → no modal (rule 4 doesn't apply).
  5. **Inline-product Axis B** — exercise with 0 / 1 / 2+
     drafts: 0 → "create a draft first" toast; 1 → silent
     add; 2+ → radio picker, both picks work.
  6. **Existing flows still work** — linked products on the
     My Products row still hit `onAddSingle` (stock-item
     path); ticking/unticking nested children works; bulk
     mode handles parents + children sensibly.
- **Why deferred:** static-only impl; needs a populated
  database + live SPA to exercise the matrix.
- **Recommended resolution:** confirm in browser — folds
  naturally into the broader Cart Button + State Ownership
  browser-verify batch.

## [OPEN] FU-144 — Cart-state awareness for product-anchored adds
- **Raised:** 2026-06-12 (FU-131 impl)
- **Type:** follow-up
- **What:** `AddToListButton variant="inline-product"`
  doesn't show "on a list" state today — `cartStateFor` keys
  on `stock_item_id` and a product-anchored button has none.
  Result: a user can re-click "Add as product" on the same
  product and get a second product-only line (the backend's
  dedupe catches it and the toast reads "Already on your
  list", so it's safe — just not as informative as the
  stock-item variant). A parallel membership index keyed on
  `product_id` would let the button render the same
  on-list / on-multiple states the stock-item variant does.
- **Why deferred:** out of FU-131's documented scope (the
  three named pieces shipped); product-anchored membership
  is a server-side extension that touches the
  `Membership` DTO + how its `items` array is keyed.
- **Recommended resolution:** when a third product-anchored
  consumer of `AddToListButton` shows up, or when a user
  reports the double-add UX as a problem.

## [OPEN] FU-131 (original) — Cart Button Chunk 3 frontend UI (rule 4 modal + inline-product variant + nested display)
- **Raised:** 2026-06-12 (Cart Button Chunk 3 deliberate scope-down)
- **Type:** rollout
- **What:** Backend rules 1–3 + schema + DTO are wired this chunk.
  The UI side of Chunk 3 was deliberately scoped down to keep the
  schema-change PR reviewable. Remaining UI work:
  - **Rule 4 modal**: removing a product-only line should prompt
    "Also remove the stock item from this list?". Hook into the
    existing DeleteLine + RemoveByStockItem paths from the SPA.
  - **`AddToListButton variant="inline-product"`** + a
    `product-id` anchor path (couples with the **My Products**
    page link affordance, L195) — current `AddToListButton` only
    accepts `stockItemId`; this chunk needs a parallel
    `productId` prop.
  - **Nested display on the shopping-list detail page** — render
    a product line that shares a `stock_item_id` with another
    line as a child of that line, not a sibling. Render
    product-only lines with a "product only" badge.
  - **Backup / restore round-trip** — verify the snapshot JSON
    survives the new column (the table is already part of the
    snapshot but the field set changed).
- **Recommended resolution:** opportunistic — pair with the next
  shopping-list-detail polish pass, or do as one focused UI sweep
  before Cart Button Chunk 4.

## [OPEN] FU-130 — Browser-verify Cart Button Chunk 2 (combined modal for 2+ products)
- **Raised:** 2026-06-12 (Cart Button Chunk 2 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **0 linked products** → row cart click adds silently via the
     existing single-item flow (no modal). One toast.
  2. **1 linked product** → same silent add. No modal.
  3. **2+ linked products** → row cart click opens `QuickAddSheet`
     pre-populated with the stock item; target-list dropdown +
     offer radio + quantity editable; Add → one toast.
  4. **2+ products AND 2+ drafts** → still routes through the same
     `QuickAddSheet` (single surface, no stacked modals).
  5. `linked_product_count` shows up on the `/stock-items` JSON
     response (network panel); 0 with no `StockItemProduct` rows;
     count increments as products are linked.
  6. Bulk variant unaffected — still resolves target once + one
     summary toast regardless of per-item product counts.
- **Why:** the modal-routing gate is new code; verify the count
  hydration stays O(1) DB calls per list page (single GROUP BY).
- **Recommended resolution:** now (next session).
- **State note:** 2026-06-14 — user-reported the picker modal is **not
  popping up** when adding to a list with 2+ linked products; AddToListButton
  is going straight to the silent-add path instead of opening QuickAddSheet
  pre-populated. Needs a live repro before root-causing — likely candidates:
  `linked_product_count` not hydrating on the relevant payload,
  `shouldUseCombinedModal.value` evaluating false because of a store
  mismatch, or the new `selected-product-id` short-circuit (FU-128) firing
  on the wrong surface. Revisit when the user can capture which screen +
  which item it fails on.

## [OPEN] FU-124 — Browser-verify Stock Overview Chunk 5 (responsive detail nav + long-press)
- **Raised:** 2026-06-12 (Stock Overview Chunk 5 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Desktop (≥ md breakpoint):** tap a row → splitter peek opens
     with the shared `StockItemDetailPage` embedded; tap again →
     closes. Same behaviour as before.
  2. **Mobile (< md breakpoint):** tap a row → full-page navigation
     to `/stock/<id>`; no drawer/peek. Same `StockItemDetailPage`
     renders in non-`embedded` mode. The back button returns to the
     overview with state preserved.
  3. **Bulk mode (any breakpoint):** tap toggles selection (no nav,
     no peek).
  4. **Long-press a row on mobile:** enters bulk-select mode and
     ticks the held item. Subsequent taps add/remove items. Cancel
     button exits bulk mode.
  5. **Long-press on desktop:** is a no-op (the `<md` guard in
     `onRowLongPress`). Desktop users have the toolbar's Bulk
     select button.
  6. **Resize browser across the md breakpoint** while a peek is
     open — peek stays attached to the row's existing state; future
     row-taps then use the new breakpoint's behaviour.
- **Why:** `v-touch-hold` was newly registered in `quasar.config.ts`
  this chunk; verify it actually fires on touch devices (Chrome
  mobile emulation works). The breakpoint branching uses
  `$q.screen.lt.md` — confirm that `boot/quasarScreen.ts`'s
  `Screen.setDebounce(100)` has the plugin active (it does for
  every other consumer, but a sanity check costs nothing).
- **Recommended resolution:** now (next session).

## [OPEN] FU-123 — Browser-verify Stock Overview Chunk 4 (expiry control)
- **Raised:** 2026-06-12 (Stock Overview Chunk 4 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **No expiry set** → tap the row's expiry button → q-date picker
     appears (popup on desktop, dialog on mobile). Picking a future
     date PATCHes the stock item and the row immediately reflects the
     new date (icon switches to a coloured "ok" / "soon" tone via
     existing logic). Picking past dates is blocked by
     `dateOptionsFuture`.
  2. **Expiry set** → tap the row's expiry button → menu shows
     **+1 day · +7 days · +14 days · Clear** (no +30 anymore).
     +1/+7/+14 each PATCH the right ISO date; Clear nulls it and
     the button reverts to the "no expiry" date-picker state.
  3. **Tone outline still flips correctly**: setting a date <7 days
     in the future triggers `stock-row--warn` (amber); a past date
     should not be settable but if one exists from earlier data,
     `stock-row--alert` (red) still applies.
  4. **No regressions** on the surrounding right-cluster buttons
     (#recipes, open/in-use, cart).
- **Why:** date-picker swap is the highest-risk part; q-date's
  `options` function uses `YYYY/MM/DD` strings while the emitted
  `model-value` uses the configured `mask` — verify both code paths
  actually agree on what "today" means.
- **Recommended resolution:** now (next session).

## [OPEN] FU-122 — Browser-verify Stock Overview Chunk 3 (row rebuild + image toggle)
- **Raised:** 2026-06-12 (Stock Overview Chunk 3 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Row layout** reads left→right: bulk-checkbox (when in bulk mode)
     → coloured level square → name (bold) + zone (inline) → image
     placeholder (if `show_stock_images` is on) → ... → expiry → #recipes
     (when >0) → open/in-use → cart.
  2. **Level button** click opens the picker; selection updates the
     row's colour immediately (optimistic).
  3. **Zone** is clickable and filters the list to that location.
  4. **Status outline:** healthy row has no coloured border; an item
     expiring within 7 days gets an amber border; "Out of Stock" or
     expired items get a red border AND dim. Cross-theme check
     (Pesto light/dark, Cherry Cola dark — colours come from
     `--q-warning` / `--q-negative`).
  5. **Selection fills the row** (light primary tint) when bulk-mode
     selected; the splitter-peek state still draws its own solid
     outline; focus still draws the dashed accent outline.
  6. **Image toggle** at the top right flips between image / image-off
     icon; the row's image slot disappears when off and the row
     becomes visibly denser; reload-survives (server PATCH /me).
  7. **No regressions:** chip-shaped StockItemChip is GONE from rows
     but still renders on shopping-list lines + the stock-item
     detail page. "On N lists" chip is gone. The cart button still
     adds the item to the active draft list (C-7 will replace this
     properly later).
  8. **Virtualised list** still works after the row-size change — the
     `VIRTUAL_SCROLL_ITEM_SIZE = 72` constant in StockOverview.vue
     may need a tweak if rows feel too compact/spacious; q-virtual-
     scroll self-corrects after the first measure but tune the hint
     to match what you see.
- **Why:** static-only impl. Row rebuild is the biggest chunk of the
  plan; cross-theme + cross-state checks are the highest-risk
  verification. The image toggle is the FU-106 surface and needs an
  end-to-end PATCH /me confirmation.
- **Recommended resolution:** now (next session) — confirm and mark
  RESOLVED, or log defects.

## [OPEN] FU-121 — Browser-verify Stock Overview Chunk 2 (top toolbar + filters + footer)
- **Raised:** 2026-06-12 (Stock Overview Chunk 2 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Top toolbar order**: New item · Export · Bulk select · Scan ·
     Stocktake · (spacer) · Search. Bulk select shows "Cancel" once
     bulk-mode is on.
  2. **Filter bar closed by default** on every page that uses
     `FilterBar` (Stock Overview, Cookbook overview, anywhere else
     it appears). Click "Filters" → panel expands; clicking again →
     collapses. Active-filter badge still surfaces while collapsed.
  3. **Level filter** is a single "Any level" dropdown; selecting a
     level filters; clearable. No floating count badges visible.
  4. **"Used in a recipe" filter is gone.**
  5. **Search placeholder** reads "Search" (no parenthesised hint).
  6. **Footer counts** in order: Shown · Well-stocked · Sufficient ·
     Low · Out · Flagged · Auto-add · Needs attention. Counts reflect
     the filtered set; recompute live when filters change.
  7. **No console errors** from the dropped `usedInRecipeOnly` /
     `getStockLevelColour` references.
- **Why:** static-only impl; the FilterBar default flip is a global
  change that touches every consumer, the level dropdown swap touches
  the most-used filter, and the composable's filter set lost one
  field (other callers might still expect it).
- **Recommended resolution:** now (next session). Includes the
  cross-page smoke pass for the FilterBar default flip.

## [OPEN] FU-119 — Browser-verify Cookbook Chunk 10 (multi-part recipes via named sections)
- **Raised:** 2026-06-12 (Chunk 10 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies migration `f6c8e3a9b1d2` on SQLite
     + Postgres; app boots; `verify_mappings()` passes for the new
     `RecipeSection` mapping + the `section_id` column on
     `RecipeIngredient` / `RecipeStep`.
  2. Existing recipes still load and render unchanged (no sections =
     same flat ingredient list, same cook-mode location grouping).
  3. **Create a recipe with two sections** ("Sauce", "Filling"); add
     ingredients, pick a section per row; save; reload → sections +
     section assignments persist; `RecipeCard` shows "2 parts" badge.
  4. **Cook mode:** ingredient panel groups under "Sauce" / "Filling"
     instead of by location; step card shows the section name as a
     chip; "All steps" overview repeats the header at each transition.
  5. **Delete a section** in the editor → its rows fall back to
     "Main" (FK SET NULL), save, reload → no orphans, no FK error.
  6. **Rename a section** in the editor (without touching ingredient
     rows) → server keeps the rows pinned because editor always sends
     `ingredients[]` + `sections[]` together; confirm no rows
     unsectioned themselves.
- **Why:** static-only impl; the section back-fill SQL UPDATE in the
  create handler and the `_resolve_section` UUID-vs-client_id branch
  in the update handler are the highest-risk new code paths and both
  need a real-DB pass.
- **Recommended resolution:** now (next session) — confirm in
  browser, then mark RESOLVED with whatever surfaces.

## [OPEN] FU-118 — Drag-and-drop for moving ingredients between sections
- **Raised:** 2026-06-12 (Chunk 10 deliberate scope-down)
- **Type:** enhancement
- **What:** Right now the only way to move an ingredient between
  sections is the per-row Section picker (`q-select`). The chunk plan
  also mentioned "drag", but the picker is already R-001-friendly
  (reuses the existing select) and ships the feature without net-new
  infra. Add drag-and-drop reorder + section reassignment when the
  same instinct hits the steps editor (see FU-094 for the parallel
  steps DnD work).
- **Why:** Power users with many ingredients in many sections will
  want bulk reassignment; the picker is fine for a few rows.
- **Recommended resolution:** later, opportunistic — pair with
  FU-094 (steps DnD) so we ship one DnD library / pattern.

## [OPEN] FU-117 — `RecipeStepsEditor` should let you pick a step's section
- **Raised:** 2026-06-12 (Chunk 10 deliberate scope-down)
- **Type:** enhancement
- **What:** Chunk 10 wired `section_id` on `RecipeStep` end-to-end
  (entity, table, DTO, cook-mode read path), but the steps editor
  doesn't yet surface a section picker. Hand-entered steps ship with
  `section_id = NULL` until this lands; URL importers can populate
  the field directly if they detect `HowToSection`. Surface should
  be: a small chip / select on each top-level step row in
  `RecipeStepsEditor` mirroring the ingredient row picker; sub-steps
  inherit visually so no picker needed there.
- **Why:** Without it, multi-part recipes still render correctly in
  cook mode if the importer (or a future bulk tool) sets `section_id`
  on steps — but a user editing in the SPA can't move a step into a
  named section.
- **Recommended resolution:** later, when there's another
  cookbook-polish session; small change, isolated to
  `RecipeStepsEditor.vue` + a `sectionOptions` prop.

## [OPEN] FU-116 — Browser-verify Cookbook Chunk 9 (cost + simple nutrition, opt-in)
- **Raised:** 2026-06-11 (Chunk 9 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `e5b9d2c8a4f3` on SQLite +
     Postgres; app boots; `verify_mappings()` passes for the
     reshaped `Recipe`.
  2. **Both flags off (default):** open the recipe detail page →
     the editor has **no** kcal input next to servings; the sidebar
     shows **no** cost card and **no** nutrition card. The
     cookbook overview has **no** Kcal sort option and **no** Kcal ≤
     filter. (Confirms the gates work.)
  3. **Turn on nutrition (Settings → Account → Nutrition → Simple,
     install layer already on):** editor gains the **kcal per
     serving** input. Type a value → save → reload → value persists.
  4. **Nutrition card** appears in the detail sidebar when the
     recipe has a kcal value.
  5. **Cookbook overview Kcal axis + filter:** Sort by → **Kcal**
     option present. Pick it, flip direction → "Highest kcal first"
     / "Lowest kcal first" reads in the tooltip. Recipes without a
     kcal value sink to the bottom in either direction.
  6. **Kcal ≤ filter** input renders in the filter row. Type
     "500" → only recipes with kcal ≤ 500 (and recipes with no
     kcal value at all) survive.
  7. **Turn on money (Settings → Account → Money & budgets, install
     layer already on):** open a recipe whose ingredients link to
     products with current offers → sidebar shows **Estimated cost**
     card with a dollar value, a help-icon tooltip describing the
     math, and "(N / M ingredients priced)" coverage badge.
  8. **Cost math sanity:** pick a simple recipe (3 ingredients, all
     with linked products). Compute expected: for each ingredient,
     `quantity × current offer price ÷ product size_value`. Sum.
     Compare to the card's number — should match to 2 decimal
     places.
  9. **No linked products:** open a recipe whose ingredients aren't
     linked to any product → the Estimated cost card **doesn't
     render** (estimated_cost is null).
  10. **Partial coverage:** open a recipe where some ingredients
      have linked products and others don't → card renders with
      e.g. "(2 / 5 ingredients priced)".
  11. **Old freeform Nutrition expansion gone** from the detail
      page. A recipe with an existing `nutrition` text value still
      saves cleanly (the column round-trips through PATCH).
  12. **Money OFF + Nutrition ON:** cost card hidden, kcal
      input/sort/filter/card all visible.
  13. **Money ON + Nutrition OFF:** cost card visible, no kcal
      surfaces anywhere.
  14. **PATCH wire shape:** changing the kcal value sends
      `{ kcal: <int> }` and nothing else. Clearing it sends
      `{ kcal: null }`.
  15. Cross-theme (Pesto Light + Pesto Dark + Cherry Cola Dark) —
      both new sidebar cards read in all three.
- **Recommended resolution:** now/when env available — closes
  Cookbook Chunk 9.

## [OPEN] FU-115 — Drop the freeform `Recipe.nutrition` text column
- **Raised:** 2026-06-11 (Cookbook Chunk 9 impl)
- **Type:** finding / cleanup
- **What:** Chunk 9 stopped rendering/editing the freeform
  `recipe.nutrition` text column in favour of the structured
  `kcal: int | None` field. The column survives in the DB + on the
  DTO + in the form's hydrate/save plumbing so existing data isn't
  destroyed mid-session. Before dropping, **audit prod-style
  installs** (or any non-seed user data) to confirm no user has
  typed something irreplaceable in there — possibly a recipe note
  on macros / micros that pre-dates Chunk 9. If nothing is found
  worth saving, write a migration that drops the column and clean
  up the four places it's still referenced in the SPA / API.
- **Where it still lives (as of Chunk 9):**
  - `domain/entities/recipe.py` — `nutrition: str | None` field.
  - `persistence/table_mappings.py` — `Column("nutrition", String, ...)`.
  - `features/recipes/get_recipes.py` — RecipeDto carries it.
  - `features/recipes/create_recipe.py` /
    `update_recipe.py` — request models accept it.
  - `web_app/src/models/recipe.ts` — `nutrition: string | null`.
  - `pages/RecipeDetailPage.vue` — `form.nutrition` still round-
    trips on save (hidden from UI, but preserved).
- **Recommended resolution:** later, after Chunk 9 has been in real
  use for a beat and we can confirm no user has typed something
  important there. Dedicated cleanup chunk: migration + audit +
  removal sweep.

## [OPEN] FU-114 — Browser-verify C-cross Chunk 5 (image-display opt-in + deferred image column)
- **Raised:** 2026-06-11 (Chunk 5 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `d4a7c9b3e8f1` on SQLite +
     Postgres; app boots; `verify_mappings()` passes for the
     reshaped `User`.
  2. New user → `show_recipe_images` and `show_stock_images` both
     default **true**. Existing users post-migration are the same
     (server default `'1'`).
  3. Open Cookbook overview. The header now has an **image** icon
     button next to "Import from URL". Tooltip reads "Hide recipe
     photos · saved across sessions".
  4. Recipe cards render their photos as today.
  5. Open a recipe detail page with an image → header preview
     shows the photo.
  6. **Click the toggle.** Icon flips to `image_not_supported`,
     success toast "Recipe photos hidden." appears.
  7. Recipe cards now show the coloured-initial placeholder (no
     photo). **In DevTools Network**, confirm the bytes endpoint
     `GET /api/recipes/<id>/image` is **NOT** called for the
     visible cards (the previous flag-on behaviour would have
     fetched them).
  8. Open a recipe detail page (with an image). The header preview
     shows the placeholder; **the editor's pick/clear buttons
     still work** — pick a new image → preview shows the
     freshly-picked image (the dirty-form branch ignores the
     opt-in, per the IMPL plan's "editor stays usable" carve-out).
     Save → reload → preview hides again (saved image is gated).
  9. **Toggle back on.** Toast "Recipe photos shown." Cards +
     detail show photos again. Saved images survived intact.
  10. **/me payload:** `GET /api/users/me` carries
      `show_recipe_images` + `show_stock_images` on every load.
      The toggle PATCH sends only `{ show_recipe_images: bool }`
      and nothing else.
  11. **Cross-session persistence:** flip the toggle, sign out,
      sign back in — the toggle remains in the chosen position.
      Sign in from a second device → same.
  12. **FU-090 perf fix:** load the cookbook overview with N≥10
      recipes that all have images. The recipe-list response
      payload size is now substantially smaller than before
      (image bytes are no longer included in the rows; only
      `has_image: bool` survives). Backend logs / `sqlalchemy.echo`
      show no `SELECT image FROM Recipe` on the list path.
  13. **Stock-side flag round-trips even though no UI writes it
      yet** (FU-106 will land the inline button in C-1 row
      redesign): `PATCH /me` body `{ show_stock_images: false }`
      survives a reload.
  14. Cross-theme (Pesto Light + Pesto Dark + Cherry Cola Dark) —
      the new icon button reads in all three.
- **Recommended resolution:** now/when env available — closes the
  C-cross pre-consumer foundations.

## [OPEN] FU-113 — Browser-verify C-cross Chunk 4 (location-display policy)
- **Raised:** 2026-06-11 (Chunk 4 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. Open Stock Overview. A stock item assigned to e.g.
     **Pantry → Middle shelf → Left side** now shows **"Pantry"** on
     its location chip (zone-only). Hover the chip → tooltip reads
     *"Pantry › Middle shelf › Left side · Filter to this location"*.
  2. A stock item assigned only to **Pantry** (zone, no sub-area) →
     chip reads *"Pantry"*; tooltip is just *"Filter to this
     location"* (no path prefix because there's no sub-detail to
     reveal).
  3. **Click the chip** — filters the overview to that location.
     Filter still uses the underlying `stock_location_id`, no
     regression.
  4. Open a stock-item detail page. The Location row in the header
     panel reads as the zone (or `—` if unset). Hover → tooltip
     reveals the full breadcrumb when one exists.
  5. Open a shopping-list detail. Each line's `place`-icon location
     reads the zone only. Hover → full breadcrumb tooltip.
  6. **Start shop mode** on a list with lines spread across
     sub-areas under the same zone (e.g. two Fridge lines under
     "Crisper" + one under "Top shelf"). Confirm:
     - The section label above the current item shows the **zone**
       ("Fridge"), not the sub-area.
     - The hover tooltip on the section label shows the full path
       for the current line.
     - The **shop order still splits the two sub-areas apart** —
       crisper items aren't interleaved with top-shelf items just
       because they share the zone (sortKey discipline still uses
       the full breadcrumb).
  7. Open RecipeCookMode. The ingredient group headers continue
     to show zone-only (this hasn't changed) — confirm no
     regression. Per-row location chips don't render in cook
     mode, so there's no chip tooltip to test there.
  8. Cross-theme sanity (Pesto Light + Pesto Dark + Cherry Cola
     Dark) — tooltips read in all three.
- **Recommended resolution:** opportunistic — the policy change is
  small enough that the next time a verifier opens the app, this
  audit takes ~3 minutes.

## [OPEN] FU-112 — Browser-verify C-cross Chunk 3 (per-user nutrition mode + reserved seam)
- **Raised:** 2026-06-11 (Chunk 3 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `c8d3f4a9b2e1` on SQLite +
     Postgres; app boots; `verify_mappings()` passes for the reshaped
     `User` + `AppSetting`.
  2. Open Settings → Account → **Nutrition** card. Three-way toggle
     reads **Off** by default. Captions read sensibly.
  3. **Install OFF, user Off (default):** whole toggle is disabled,
     caption reads "This install has nutrition turned off…".
  4. Admin enables `nutrition_enabled` in System → Features. Return
     to Account → Nutrition. **Off** + **Simple** are now clickable,
     **Complex** is disabled. Caption explains complex needs a source.
  5. Flip to **Simple** → success toast → reload → still on Simple.
  6. Flip back to **Off** → success toast → reload → still off.
  7. **Server rejects complex without seam:** as an admin, send
     `PATCH /api/users/me` with body `{ nutrition_mode: 'complex' }`.
     Get a 400 with the "Complex nutrition mode needs a nutrition
     data source configured…" message.
  8. **Configure the seam:** as an admin, send
     `PATCH /api/app-settings` with body
     `{ nutrition_db_source: 'usda-fdc' }`. `GET /api/health` now
     reports `features.nutrition_complex_available: true`.
  9. Return to Account → Nutrition (refresh page so `useFeatureFlags`
     picks up the change). **Complex** is now clickable. Pick it →
     success toast → reload → still on Complex.
  10. **Re-empty the seam** via PATCH with `nutrition_db_source: ''`.
      Refresh the Settings page. The user remains on Complex
      *server-side* (we don't auto-rewrite), but the toggle's
      Complex option is disabled and the caption reads accordingly.
      The user can switch back to Off / Simple normally.
  11. **PATCH wire shape:** flipping the toggle sends a body with
      `{ nutrition_mode: '<mode>' }` and nothing else. Confirm in
      DevTools Network.
  12. **/me payload** carries `nutrition_mode` on every load.
  13. Cross-theme (Pesto Light + Pesto Dark + Cherry Cola Dark) —
      the new card reads in all three.
- **Recommended resolution:** now/when env available — before C-4
  Chunk 9 (cost + nutrition) lands on top.

## [OPEN] FU-111 — Browser-verify C-cross Chunk 2 (per-user money opt-in)
- **Raised:** 2026-06-11 (Chunk 2 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `b5c1d9a4e3f2` on SQLite + Postgres;
     app boots; `verify_mappings()` passes for the reshaped `User`.
  2. As a regular signed-in user, open Settings → Account. The new
     **Money & budgets** card appears above the Grocery budget card
     with a toggle, currently off (the default).
  3. **Install ON, user OFF (default):** the toggle is enabled, the
     Grocery budget card is **hidden**. Flip the toggle on → success
     toast → Grocery budget card appears → set a budget number + a
     period → reload → toggle still on, budget settings persisted.
  4. **Toggle off again** → success toast → Grocery budget card
     hides → reload → toggle is off, **but the saved budget number
     is still on the server** (verified by flipping back on and
     seeing the same value appear).
  5. **Install OFF (admin disables in System → Features → Money):**
     the per-user toggle is **disabled** with a caption *"This
     install has money features turned off…"*. Grocery budget card
     stays hidden regardless of the per-user value.
  6. **PATCH wire shape:** flipping the toggle sends
     `PATCH /api/users/me` with body `{ money_features_enabled: true|false }`
     (and nothing else). Confirm in DevTools Network.
  7. **/me payload:** `GET /api/users/me` carries
     `money_features_enabled` in its response body.
  8. **Composable layering:** `useMoneyEnabled().moneyEnabled.value` is
     `installEnabled && userEnabled` — confirm via DevTools when one or
     both are flipped.
  9. **Error path:** flip the toggle while the server is reachable but
     the PATCH 500s → the toggle reverts to its previous state +
     negative toast fires.
  10. Cross-theme (Pesto Light + Pesto Dark + Cherry Cola Dark) — the
      new card reads in all three.
- **Recommended resolution:** now/when env available — before C-cross
  Chunk 3 lands on top.

## [OPEN] FU-110 — Browser-verify C-cross Chunk 1 (feature-flag panel + opt-in plumbing)
- **Raised:** 2026-06-11 (Chunk 1 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `a3b8e2f4c1d7` on SQLite + Postgres;
     app boots; `verify_mappings()` passes for the reshaped `AppSetting`.
  2. As an admin user: open Settings → System → **Features** panel.
     Five toggles appear (Meal planning ON, Money / Nutrition /
     Companion ingestion / Weekly deals emailer all OFF). Captions
     read sensibly.
  3. Flip each toggle on → success toast + the saved value persists
     across a reload.
  4. Flip each toggle off → success toast + persists.
  5. As a non-admin user: the panel renders the "no admin
     permissions" banner; the toggles aren't visible.
  6. **Health endpoint contract:** `curl /api/health` JSON carries
     `features.meal_planning` / `features.money` / `features.nutrition`
     / `features.companion_ingestion` / `features.deals_email` keys
     alongside the pre-existing `auth` / `audit` / `scanning` /
     `multi_user` / `email` / `assistant`. Values match what the
     panel shows.
  7. **Composable freshness:** open the panel + open a second tab on
     any page using `useFeatureFlags()` (today there are no
     consumers — verify via DevTools that `flagsLoaded.value` is
     `true` and the named computeds match the panel). Flip a toggle
     in tab 1 → composable cache only refreshes in tab 1 (per-session
     cache; documented as Chunk-1 behaviour; cross-tab refresh is a
     later layer).
  8. **Migration safety on existing installs:** an install that's
     been using meal planning happily should see
     `meal_planning_enabled = True` after the migration (its server
     default). Confirm against a non-empty pre-Chunk-1 row.
  9. **Save error path:** disable network / wait for PATCH to
     500-out → toggle reverts to its previous state; negative toast
     fires with the error caption.
  10. Cross-theme sanity (Pesto Light + Pesto Dark + Cherry Cola
      Dark) — the new panel reads in all three.
- **Recommended resolution:** now/when env available — before
  C-cross Chunk 2 lands on top.

## [OPEN] FU-109 — Decide whether to re-add the RecipeCard "would-be-cookable" dim
- **Raised:** 2026-06-10 (FU-083 follow-up; user wants a real decision
  later)
- **Type:** open product / UX decision
- **What:** FU-083 removed the `RecipeCard --dim` opacity treatment.
  The dim previously fired in **two** places (both used the same
  `highlightStockItemIds` prop):
  1. **`StockItemDetailPage.vue:332`** — "Recipes that use this
     item" tab. A recipe dimmed when restocking *this* item alone
     wouldn't make it cookable (i.e. it was missing other ingredients
     too).
  2. **`RecipesOverview.vue`** — when the user had any ingredient in
     the "Uses ingredients" include list. Same semantics: a recipe
     dimmed when it was missing other ingredients beyond the
     highlighted set.
  Removal landed in both surfaces; the prop is still on `RecipeCard`
  but unused for visual.
- **Why removed:** FU-083 feedback said the dim wasn't immediately
  obvious without a legend, and the card already carries a
  "Missing N ingredients" copy on its face — so the dim doubled up
  the same signal.
- **Why it might come back:** the dim conveys "restocking *just*
  this item wouldn't be enough" without requiring the user to count.
  It's particularly valuable on the **stock-item detail** surface
  (the dim said "go shop for these others too"). On the cookbook
  overview the value is murkier because the filter set is the user's
  own input.
- **What the decision needs:**
  1. **Keep removed everywhere?** (current state) — leaves the card
     copy as the only "this is missing things" signal.
  2. **Re-add only on `StockItemDetailPage`?** — that was the
     surface where the dim was most defensible (single-item context;
     user looking at "what does restocking this unlock?").
  3. **Re-add everywhere, with a legend?** — `q-tooltip` on dimmed
     cards explaining the semantics; same icon/text legend on the
     filter bar so the meaning is discoverable.
- **Recommended resolution:** **user decision required.** When you
  pick a direction, the code path is:
  - Re-add the `dim` computed in `RecipeCard.vue` (was lines 279–283
    pre-removal — see git history).
  - Re-bind `:class="{ 'recipe-card--dim': dim }"` on the root.
  - Re-add the `.recipe-card--dim { opacity: 0.55 }` rule.
  - If overview-only: gate on a prop like `:dim-when-incomplete`
    that the consumer passes (off by default; on for
    `StockItemDetailPage`).

## [OPEN] FU-108 — Reorder Cookbook overview filters by usefulness
- **Raised:** 2026-06-10 (FU-083 follow-up; user, after the bug pass)
- **Type:** finding / UX polish
- **What:** The filter bar in `RecipesOverview.vue` lays controls out
  in the order they were added, not in the order users reach for
  them. The chip cluster (Favourites / Cookable now / Have meals in
  pool / Planned), the numeric inputs, the single-select dropdowns
  (Collection / Cuisine / Category), and the multi-select pickers
  (Uses ingredients / Doesn't use / Dietary / Tools) should be
  ordered by how often users actually flip them — most-used first,
  long-tail later. Pure template reorder, no logic changes.
- **What "useful" means here (open):** the user reads this. A
  reasonable starting cut: **(1) Favourites, Cookable now,
  Planned, Have meals in pool** (the quick-pick chips stay first
  because they're zero-effort); **(2) Cuisine, Category** (single-
  select, common during "what should I cook tonight?"); **(3) Uses
  ingredients / Doesn't use** (when fridge-clearing); **(4) Dietary
  + Tools** (occasional); **(5) Meals ≥ / Missing ingredients ≤**
  (numeric refinement); **(6) Collection** (visual grouping, almost
  set-and-forget). Confirm before moving — the actual answer is the
  user's, not the data's.
- **Recommended resolution:** opportunistic — fold into the next
  pass that touches this template. 10-minute job.

## [OPEN] FU-107 — Standardise API date serialisation on ISO 8601 (drop RFC 2822 default)
- **Raised:** 2026-06-10 (FU-083 "Planned" filter follow-up — RFC vs ISO
  parse bug)
- **Type:** finding / cross-cutting cleanup
- **What:** Flask's default JSON encoder serialises Python `date` /
  `datetime` as **RFC 2822** with a GMT suffix (e.g.
  `"Wed, 10 Jun 2026 00:00:00 GMT"`). That format is an HTTP-Date relic
  — fine for `Last-Modified` headers but actively painful in JSON
  payloads consumed by JS clients, because:
  1. **No timezone semantics** for what's a calendar-only date —
     "Wed, 10 Jun" is parsed by `new Date()` as midnight UTC, which
     becomes "Tue, 09 Jun" in any negative-offset timezone. Every
     consumer either needs to know it's calendar-only and reconstruct
     from UTC parts (the workaround just applied to the "Planned"
     filter), or it gets day-off-by-one bugs.
  2. **Fragile string-based parses** — Chunk 1's first attempt at the
     "Planned" filter sliced `YYYY-MM-DD` from the front of the
     string. That works on ISO; silently fails on RFC 2822
     ("Wed, 10 Ju") and drops every entry.
  3. **Differs from every other modern API** the SPA talks to —
     `created_at` / `expiry_date` etc. all come back RFC, but the
     same data going *out* (PATCH requests) is sent ISO by the SPA.
     Inconsistent.
- **Where it bites today:**
  - `MealPlanEntryDto.scheduled_for` (Date) — caught + worked around.
  - `MealPlanDto.start_date` (Date).
  - `Recipe.last_made_on` (DateTime).
  - `StockItem.expiry_date` (Date or DateTime).
  - Audit events, shopping-list shop-day, alert created_at, etc. —
    anywhere a Python `date` / `datetime` lands in a DTO.
- **Recommended resolution:** override Flask's JSON provider (Flask 2.3+
  ships `app.json_provider_class`) with one that emits ISO 8601 for
  `date` and `datetime`. Either:
  - Calendar-only `date` → `"2026-06-10"`; `datetime` → full ISO with
    offset → `"2026-06-10T15:00:00+00:00"`; **or**
  - Both use ISO with appropriate granularity.
  Tests cover round-trips through every dated DTO + the SPA models that
  read them. Drop the RFC-aware workarounds where they exist (start
  with `plannedRecipeIds` in `RecipesOverview.vue`).
- **Recommended timing:** **later — dedicated `api-date-iso-shift` pass**.
  Not a one-line change because every existing SPA consumer that
  parses these fields needs auditing — some might be relying on
  `new Date(rfc)` happening to work for their use case. Schedule as
  its own focused PR with a tested verification list of every dated
  field.

## [OPEN] FU-105 — Browser-verify Cookbook Chunk 8 (versions + detail-endpoint fix)
- **Raised:** 2026-06-10 (Chunk 8 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies `e1f6a2b4c8d9` on SQLite + Postgres;
     app boots; `verify_mappings()` passes for the reshaped `Recipe`.
  2. **Detail endpoint hydrates:** open a recipe with structured
     steps. Confirm the editor's Structured / Freeform toggle
     populates with the saved steps. (Latent bug from Cookbook
     Chunk 6 / Cook-Mode Chunk 5 — the SPA's `getAsync(id)` used
     to drop them.)
  3. **New version action:** open a recipe → kebab → "New version".
     - Source had no `version_group_id` (singleton): the action
       allocates one + back-fills the source. Both source and copy
       now share the id.
     - Source already had a group: the copy reuses it.
  4. **Sibling card renders:** after "New version", both the source
     and the copy show an "Other versions" card listing the other
     row(s). Singletons (no siblings) hide the card.
  5. **Naming:** first "New version" on a singleton → "(v2)". A
     second click on the source → "(v3)". A click on the copy →
     also lands on the next number (server counts siblings, not
     parent).
  6. **Round-trip carry-through:** the new version inherits
     ingredients, tools, structured steps (with sub-step + ingredient
     refs remapped to the new ingredient ids), tags, cuisine,
     category, collection, source URL, image. The image shows on
     the copy without re-uploading.
  7. **Independent edits:** edit the copy → save → confirm the
     source is unchanged. Same the other way round.
  8. **Sibling delete:** delete one version → the other(s) stay,
     "Other versions" card on the survivor updates.
  9. **Meal plan + cookable:** confirm the meal-plan recipe picker
     and the cookable filter see *both* siblings (DEC-2: users pick
     when allocating). No special version-aware UI.
  10. **Allocations stay per-recipe:** schedule both siblings on a
      meal plan day. Allocated badge on each reads its own
      `available_meals`, not a merged total.
  11. **Backup → restore:** `version_group_id` round-trips through
      backup/restore (it's a column on the Recipe row — no manual
      section change was needed).
- **Recommended resolution:** now/when env available — pairs with
  FU-103 (Chunk 7) and FU-093 (Chunk 6) for a single cookbook
  walkthrough.

## [OPEN] FU-104 — Move the URL recipe importer into the private companion app (legal posture)
- **Raised:** 2026-06-10 (user, during Cookbook Chunk 7 review)
- **Type:** policy / distribution-posture decision (cross-cutting)
- **What:** The URL importer (`features/recipes/import_recipe_from_url.py`
  + the SPA dialogs added in Cookbook Chunk 7) **fetches third-party
  pages and extracts content** — schema.org JSON-LD for the happy path,
  raw `<title>` + body text in the degraded path. That's
  user-initiated, single-page, and modest-scale, but it's still:
  - **automated retrieval of copyrighted content** (recipe text /
    instructions are often editorial copyright, even if individual
    ingredient lists aren't);
  - **likely against most recipe-site ToS** (which boilerplate-ban
    scraping / automated access);
  - **fetched from our server's IP** in the current shape, not the
    user's browser — so the *operator* of a hosted Dora instance is
    the one making the request, not the user. That's the part most
    likely to attract a takedown letter / IP block / CFAA-style
    claim if it ever runs at scale on a public managed instance.
  - **CDN-fingerprintable** at scale via the `_FETCH_HEADERS`
    user-agent.
  The IMPL_PLAN_COOKBOOK shape lets it live anywhere; the master
  `RECONCILED_FINISHING_PLAN.md` Decision 1 already moved the
  **retailer scraper** out of the core app for the same reason (the
  precedent is established).
- **What this FU is asking us to decide:**
  - **Move the importer into the private companion app** (the same
    self-hosted / "personal-use, off-by-default, runs on the user's
    machine, hits sites from the user's own IP" surface that owns the
    retailer scraper). Core Dora keeps the schema (Recipe.source,
    structured steps, the create endpoint that accepts the parsed
    DTO) — the *fetcher* is what relocates.
  - **Or:** keep it in core but switch the architecture so the
    *browser* fetches the URL (CORS-permitting only — recipe sites
    rarely allow CORS, so practical coverage drops to maybe 10%) and
    posts the HTML up to the parser. Lower legal exposure but a much
    worse import experience.
  - **Or:** keep as-is, scope it as a personal-instance feature
    documented as "use only on URLs you have permission to scrape"
    + drop the named-site list in the dialog copy so we're not seen
    as encouraging it.
- **Why discuss now (not later):** the importer just got a more
  visible surface (overview button) in Chunk 7 + a graceful-degrade
  path that *succeeds* even on no-JSON-LD pages, which broadens the
  set of URLs it'll get pointed at. Better to settle the posture
  before users get used to the current shape and the named-site copy.
- **Constraints to honour in the decision:**
  - **Distribution posture (R-005):** core stays SaaS-style /
    self-hostable from one codebase. Moving the importer to the
    companion app means defining a clean "companion sends parsed
    DTO to core" boundary (companion is its own deployable; core
    treats it as an authenticated source of preview DTOs).
  - **Charter principle P10 Anti-creep:** don't bake "scrape any
    URL" into core if the legal answer is uncertain.
  - **Charter principle P1 Effortless:** users still expect the
    feature to work — the answer can't be "we removed it"; it can be
    "you run a companion locally and it stays effortless from your
    perspective".
- **Recommended resolution:** **discuss + design with user before
  next prompt that touches the importer.** Surface to a proposal
  doc (`docs/04_proposals/IMPORTER_DISTRIBUTION_POSTURE.md` or
  similar) once a direction is picked. Likely outcome: move the
  *fetcher* to the companion app (precedent: retailer scraper),
  keep the *parser* + Recipe.source schema in core. Until then, no
  new public-facing surface should advertise the importer (so:
  Chunk 7's overview button + named-site copy is fine for the
  self-hosted single-user case but should be flagged on any
  managed-instance / multi-user deployment as the next prompt
  here.) — see also `RECONCILED_FINISHING_PLAN.md §7.5` for the
  distribution-posture checklist this needs to pass.

## [OPEN] FU-103 — Browser-verify Cookbook Chunk 7 (source + URL importer)
- **Raised:** 2026-06-10 (Chunk 7 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. `alembic upgrade head` applies migration `d0e5f1a3b8c7` on SQLite
     and Postgres; app boots; `verify_mappings()` passes for the
     reshaped `Recipe` (`source` field present).
  2. **Detail-page source field:** open a recipe; the Source URL card
     appears under Instructions / Nutrition. Typed value round-trips
     through save → reload. Clearing the field → save → reload shows
     it empty (explicit null clears server-side).
  3. **Open affordance:** entering an `http(s)://` URL surfaces the
     "Open" ghost button; clicking opens the page in a new tab.
     Non-http values (or blank) hide the button.
  4. **Detail-page importer:** import a recipe from a schema.org-rich
     site (e.g. BBC Good Food). The source URL lands in the
     `source` field (NOT appended to Instructions). Steps/ingredients
     are parsed.
  5. **Degraded fallback:** import a URL that has no schema.org/Recipe
     JSON-LD (any random blog post). Confirm:
     - the importer doesn't 422;
     - the page title + body text land in name/instructions;
     - the warning toast fires: "Couldn't auto-structure that page";
     - `source` is set to the URL.
  6. **Overview Import button:** the new "Import from URL" button sits
     next to "New recipe". Click → dialog opens → paste a URL →
     Import → new recipe appears in the cache → router lands on its
     detail page.
  7. **Unmatched ingredients toast:** import a URL whose ingredients
     mostly don't match your stock items. Confirm the success toast
     counts the unmatched ones ("3 ingredients couldn't be matched —
     add them manually").
  8. **Degraded path from overview:** import a no-JSON-LD URL via the
     overview button. Warning toast fires; new recipe is created with
     the scraped body text in Instructions; detail page opens.
  9. **No "Source: <url>" appendix:** an existing recipe with the old
     in-instructions "Source: …" line still loads fine (no migration
     is attempted) — the user can move the URL into the new field
     manually.
  10. **Backup → restore:** the new `source` column round-trips
      through backup/restore without a manual section change.
- **Recommended resolution:** now/when env available — pairs with
  FU-093 (Chunk 6 structured steps) and FU-091 (Chunk 5 images +
  tools) for a single cookbook end-to-end walkthrough.

## [OPEN] FU-102 — Extract `RecipeImportDialog` shared component (R-001 threshold hit)
- **Raised:** 2026-06-10 (Cookbook Chunk 7 impl)
- **Type:** R-001 cleanup
- **What:** Chunk 7 adds an import-from-URL dialog on
  `RecipesOverview.vue`. The detail page already has one
  (`RecipeDetailPage.vue`); the two now share copy + the URL input
  shape + the importer call + the degraded-vs-success toast branching.
  They diverge on what happens with the preview — detail overwrites
  the current form, overview creates a new recipe and navigates. Two
  surfaces ≈ R-001's "if a pattern recurs (≈2–3 uses)" threshold;
  extract a `RecipeImportDialog.vue` with a `mode: 'overwrite' |
  'create'` prop (or two events: `@preview` for overwrite,
  `@created` for create) once a third caller appears or the duplicated
  copy starts to drift.
- **Recommended resolution:** opportunistic — when the dialog needs
  to change in both places at once (copy tweak, validation rule,
  loading-state UI), do the extraction in the same PR.

## [OPEN] FU-101 — Browser-verify Cook Mode Chunk 6 (cooking-for headcount rescale)
- **Raised:** 2026-06-09 (Chunk 6 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Default seed:** open cook mode on a recipe with `servings = 4`.
     The "Cooking for" input shows 4. Recipe with `servings = null`
     shows 1.
  2. **Rescale up:** bump to 6. Every ingredient quantity rescales by
     1.5×. `200g flour` → `300g` (or `300 g` if continuous-snap
     produces `300`); `2 eggs` → `3 eggs` (round up from 3).
  3. **Rescale down:** drop to 2. `200g` → `100g`; `4 eggs` → `2 eggs`.
  4. **Fraction snap (continuous):** a 4-serving recipe with `1 cup`,
     scaled to 3, gives `¾ cup` (not `0.75`). Scaled to 6, gives
     `1½ cup`.
  5. **Countable rounding:** a 4-serving recipe with `1 egg`, scaled to
     3, gives `1 egg` (rounds 0.75 → 1, floored at 1). Scaled to 6,
     gives `2 eggs` (1.5 → 2).
  6. **Floor at 1:** any countable that would round to 0 stays at 1
     (can't cook with 0 eggs).
  7. **Sub-tolerance fractions:** `0.5 cups`, scaled by 1.0 (no change)
     shows `½ cup` directly.
  8. **Blur clamp:** clear the input → loses focus → re-clamps to 1
     (and quantities don't collapse to zero / NaN mid-cook).
  9. **Min=1:** typing `0` and blurring → re-clamps to 1.
  10. **Session-only:** rescale, exit cook mode, come back. The input
      shows the recipe's original `servings` again. Saved recipe is
      unchanged.
  11. **Gram fraction edge case (note from impl):** a recipe step that
      produces e.g. `7.5g` of an ingredient will render `7½ g`, not
      `8g` as the IMPL plan's example suggested. Watch a few real
      recipes — if gram fractions read weird in practice, flip
      `g/kg/ml/l/mg` to integer rounding in `scaleQuantity.ts`
      (would treat them as countable for rounding purposes while
      leaving the spacing convention via `formatQuantity` intact).
- **Recommended resolution:** now/when env available — pairs with
  FU-093 (Chunk 6 structured steps), FU-096 (Chunks 1–3),
  FU-100 (Chunk 5) for a single end-to-end cook-mode walkthrough.

## [OPEN] FU-100 — Browser-verify Cook Mode Chunk 5 (highlight + tools + hints)
- **Raised:** 2026-06-09 (Chunk 5 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify, in order:
  1. **Structured recipe (Cookbook Chunk 6 editor):** open cook mode on
     a recipe with structured steps that name specific ingredients
     and tools per step. Confirm the highlight tracks:
     - the named ingredient rows tint + get a left accent;
     - the tools panel shows below ingredients (it only appears when
       the recipe lists tools);
     - the step-referenced tools light up; other tools dim.
  2. **Sub-step:** a step nested under a parent shows the "Sub-step"
     chip above its headline.
  3. **Hint:** a step with a hint renders the hint line under the
     headline with the lightbulb icon.
  4. **Unstructured fallback:** open cook mode on a recipe with only
     `instructions` (no structured steps). Confirm the text-matched
     highlight still fires when ingredient names appear in step text.
  5. **No tools panel** when the recipe lists no tools.
  6. **Tick state really gone:** no checkbox on ingredient rows; no
     checkbox in the "All steps" expansion (tap the step text to jump
     there).
  7. **Finish flow** now lists *every* ingredient on the recipe (with
     swaps applied), regardless of any mid-cook interaction.
  8. **Voice:** "Done" command is gone from the Sous Chef help popover.
     "Next" / "Previous" / "Repeat" / timer verbs still work.
  9. **Step navigation** via the "All steps" expansion still jumps to
     the right index; sub-steps render indented in the list.
  10. **Cross-theme** sanity check (Pesto Light + Pesto Dark + Cherry
      Cola Dark) — the highlight tint reads in dark mode.
- **Recommended resolution:** now/when env available — pairs with
  FU-096 (Chunks 1–3 verify) and FU-093 (Chunk 6 verify) for a single
  cook-mode + structured-steps walkthrough.

## [OPEN] FU-099 — Raw backend / Pydantic error strings leak into user-facing toasts → design pass
- **Raised:** 2026-06-09 (user, after the recipe-save Pydantic error)
- **Type:** design discussion needed (cross-cutting UX)
- **What's broken:** When a request fails server-side validation, the
  toast surfaces the **raw Pydantic message** as the caption — e.g.
  *"Input should be a valid integer, unable to parse string as an
  integer"* or *"String should have at least 1 character"*. These are
  developer-facing messages intended for API client implementers; to an
  end user they read as jargon (the recipe-save flow is what surfaced
  the report, but the pattern lives in `describeApiError(err)` and
  affects most pages).
- **Where it leaks today (initial scan, not exhaustive):**
  - `services/errorHandling/apiErrorHandler.ts` — likely concatenates
    the backend's `errors` map values verbatim.
  - Most page-level catch blocks: `caption: describeApiError(err) || ''`
    in recipe save, stock item save, shopping list edits, etc.
- **Status:** **NOT to be implemented yet — prompt the user to design
  this first.** The right answer touches the API error-shape contract,
  the client error-mapping layer, and every form's field-error
  rendering. Before writing code, the next session should walk the
  user through the design choices below and reach decisions.
- **Design questions to put to the user (start of next session on
  this item):**
  1. **Server vs client mapping** — does the backend stay verbatim
     Pydantic and the client translate, or does the backend ship a
     friendlier message per field (and keep the raw code alongside
     for debugging)?
  2. **Inline vs toast** — when a save fails on a field the user can
     see, should the toast disappear in favour of an inline
     `error-message` on the offending q-input? Or both? What about
     forms where the bad field isn't currently rendered (collapsed
     section, off-screen)?
  3. **Generic vs specific copy** — is *"Servings must be a whole
     number"* worth the per-field copy budget, or is *"Couldn't save
     — check the highlighted fields"* + inline enough?
  4. **Network / unknown failures** — what's the fallback caption
     when the failure isn't a validation error (5xx, network down,
     auth expired)? Currently mixed.
  5. **Dev debuggability** — agreed that the raw detail goes to
     `console.warn` for dev visibility, but should there also be a
     keyboard shortcut / hidden affordance for dev users to copy the
     raw error from the toast?
  6. **Scope** — only the most-trafficked forms (recipe / stock item
     / shopping list / edit dialogs) for the first pass, or sweep the
     app?
- **Recommended resolution:** **discuss + design with user first**,
  *then* spin a proposal/IMPL plan. Do not patch toasts piecemeal — the
  fix lives in one shared layer, not in 20 catch blocks.

## [OPEN] FU-098 — Unsaved-changes guard on navigation (app-wide)
- **Raised:** 2026-06-09 (user, after cook-mode batch)
- **Type:** finding / cross-cutting UX gap
- **What:** Navigating away from an editor while it has unsaved edits
  **silently discards** them — there's no confirm prompt. The user noticed
  this on the recipe detail page, but it's likely app-wide: stock item
  detail, shopping-list detail, settings, anywhere there's an `isDirty`
  ref on a form. The recipe detail page already tracks `isDirty.value`
  for the cook-mode guard, so the data is there — what's missing is a
  generic guard that intercepts router navigation (`beforeRouteLeave` /
  `onBeforeRouteLeave`) **and** browser-level navigation (`beforeunload`)
  when any tracked page is dirty.
- **Scope:** every editable surface, not just recipes. Should be a
  shared pattern (a composable `useUnsavedChangesGuard(isDirtyRef)`)
  rather than 10 copies — fits **R-001** (componentise the recurring
  pattern). The confirm copy should match A3 modal standard (Cancel /
  Discard changes / Save & continue — though "Save & continue" requires
  a per-page save function so it's optional).
- **Pages currently lacking the guard (spot list, not exhaustive):**
  - `RecipeDetailPage.vue` — tracks `isDirty`, no guard.
  - `RecipeCookMode.vue` — cook session state not guarded.
  - `StockItemDetailPage.vue` — likely no guard.
  - `ShoppingListDetail.vue` — line edits.
  - Settings pages (theme, vocab, system).
- **Recommended resolution:** **next polish prompt / Wave-A follow-on** —
  ship `useUnsavedChangesGuard` as a single composable wired into every
  editor page via `onBeforeRouteLeave` + a `beforeunload` listener.
  Probably a 1–2 hour pass; do it as one focused PR rather than
  drip-feeding per page.

## [OPEN] FU-097 — Roll out `formatQuantity()` to recipes/shopping-list surfaces
  *(2026-06-12, UX v2: the shopping-list half is **N/A** — list quantities are
  unitless integers in a numeric input, there's no value+unit pair to format.
  Only the recipe surfaces remain.)*
- **Raised:** 2026-06-09 (Cook Mode Chunk 2)
- **Type:** finding / R-001 + R-003 cleanup
- **What:** The new
  `web_app/src/helpers/formatQuantity.ts` centralises DEC-3 unit spacing
  (`ml g kg l mg oz lb floz pt qt` = no-space; everything else spaced) but
  Chunk 2 only swapped the cook-mode ingredient row over. Other surfaces
  still inline the quantity + unit by hand:
  - `RecipeDetailPage.vue` ingredient editor rows
  - `RecipeEditDialog.vue`
  - `RecipeCard.vue`
  - `ShoppingListDetail.vue` + shop-mode card
  - Print/export view (`ExportPrint.vue`)
  - Cookbook overview cards
  Each currently formats independently (some space, some don't, some leave
  the unit blank when null). Switch them to `formatQuantity` so the
  convention can never drift.
- **Recommended resolution:** opportunistic — fold into the next prompt
  that touches each surface; or a focused 30-minute "quantity spacing
  sweep" pass.

## [OPEN] FU-096 — Browser-verify Cook Mode Chunks 1–3
- **Raised:** 2026-06-09 (Cook Mode Chunks 1–3 impl; static-only, no env)
- **Type:** finding / verification (blocks trusting Cook Mode rewrite)
- **What:** Verify, in order:
  1. **Chunk 3 ingredient grouping:** open cook mode for a recipe whose
     ingredients span several locations. Confirm one card per *base*
     location (a sub-area like "Pantry > Spice Rack" collapses to
     "Pantry"). Ingredients with no location land in a final "No
     location" group.
  2. **No mid-cook stock-level chips:** the StockItemChip is gone from
     the ingredient row. Substitutes still render their chip + undo.
  3. **Quantity spacing:** an ingredient with `unit = "g"` reads `"250g"`;
     `unit = "tbsp"` reads `"1 tbsp"`; `unit = null` reads just the qty
     (or empty when both null).
  4. **Chunk 2 Sous Chef rename:** the voice button reads **Sous Chef**
     with a tooltip; the help icon (?) opens a popover listing the 8
     commands.
  5. **Chunk 2 timer:** detect a "10 minutes" step → fill-bar shows below
     MM:SS → bar empties as time runs → at 0 the bar turns negative
     colour, the toast fires, **a short beep plays** (silently no-ops on
     iOS / PWA without a user-gesture activation, that's OK), and the
     reset button works to clear it.
  6. **Chunk 1 finish flow:** mark a few ingredients used, finish →
     dialog shows one row per used ingredient with the current stock
     level chip, action chips (Down one / Out / Unchanged, default Down
     one), override dropdown, and per-row Add-to-list button.
  7. The `meals_cooked` field defaults to **0**. Confirm a Done press
     with 0 toasts *"All eaten — hope it was good."* With N>0 it toasts
     *"You saved N meals — enjoy."* (with proper pluralisation).
  8. **Per-row override > action**: pick an explicit level for one row
     → on Done, that row's stock_level_id flips to the override.
     `Unchanged` rows leave stock alone.
  9. **Fail-soft:** one row pointing at a deleted stock item shouldn't
     stop the others from updating (Promise.allSettled).
  10. **Click-out cancels:** open the finish dialog, click outside →
      dialog closes, **no level / cook calls fired**.
  11. **Session swap interaction:** swap an ingredient to its
      substitute, finish → the *substitute*'s level (not the original
      recipe ingredient) is what updates.
- **Recommended resolution:** now/when env available — before C-3 Chunk 5
  lands on top.

## [OPEN] FU-095 — RecipeEditDialog (quick-create) has no structured-steps surface
- **Raised:** 2026-06-09 (Cookbook Chunk 6 impl)
- **Type:** follow-up
- **What:** The quick "New recipe" dialog (`RecipeEditDialog.vue`) only
  collects the basics — name, ingredients, cuisine/category, tags, tools,
  image. Structured steps were intentionally **not** added to keep the dialog
  lean for the common "create a stub then edit it" workflow. Users add
  structure via the detail page's Structured/Freeform toggle. If a future
  prompt makes the dialog the primary create path (or users complain about
  switching to detail), wire the `RecipeStepsEditor` into the dialog with
  the same `steps_mode` toggle.
- **Recommended resolution:** opportunistic / when next touching the dialog.

## [OPEN] FU-094 — Steps editor: drag-and-drop reorder (replaces up/down)
- **Raised:** 2026-06-09 (Cookbook Chunk 6 impl)
- **Type:** follow-up
- **What:** Per `IMPL_PLAN_COOKBOOK.md §6`, structured steps should reorder
  via the drag-handle pattern already used on shopping-list lines
  (`onLineDrop` off-by-one fix). Chunk 6 ships with **up/down arrow
  buttons** instead — functionally complete but less ergonomic on long
  recipes, especially because nesting (top-step vs sub-step) constrains
  the valid drop zones (siblings only). Replace once the basic editor is
  proven and the nesting drop-zone UX is worked out.
- **Recommended resolution:** later — once Chunk 6 has been browser-verified
  (FU-093) and the editor is in real use.

## [OPEN] FU-093 — Browser-verify Cookbook Chunk 6 (structured recipe steps)
- **Raised:** 2026-06-09 (Chunk 6 impl; static-only, no env)
- **Type:** finding / verification (blocks trusting Chunk 6 + cook-mode Chunk 5)
- **What:** Verify, in order:
  1. `alembic upgrade head` applies migration `c9d4f8e2a5b6` on SQLite **and**
     Postgres; app boots; `verify_mappings()` passes for `RecipeStep`.
  2. On a recipe, switch the new toggle to **Structured**, add a top step
     (text + hint + ingredient + tool), add a sub-step under it, reorder
     via the ↑/↓ buttons, save → reload → the structure round-trips.
  3. Switch the toggle to **Freeform**, save → `steps[]` is wiped server-side
     (re-open → editor shows zero steps); the textarea content remains.
  4. Toggle back to **Structured** and add steps again → save → editor
     reflects the new state.
  5. **URL importer:** import a recipe whose source uses schema.org
     `HowToStep` (e.g. major recipe sites publish JSON-LD) → the editor
     auto-fills Structured with the parsed steps. Import a site that only
     ships `recipeInstructions` as a string → editor stays in Freeform
     with the textarea filled.
  6. **HowToSection** import: a source that groups steps under sections
     produces top-level "section" steps with sub-steps under each.
  7. Delete an ingredient that a step references → the step's ingredient
     chip disappears (cleanup in `removeIngredient`) and save round-trips
     without errors.
  8. Edge: try to save a step with empty text → server returns 400 with
     "Every step must have non-empty text."
  9. **Backup → restore** round-trips RecipeStep / RecipeStepIngredient /
     RecipeStepTool in FK-correct order; structured recipes show the same
     steps after a restore.
- **Recommended resolution:** now/when env available — before cook-mode IMPL
  Chunk 5 lands on top.

## [OPEN] FU-092 — Audit ALL implicit / automatic / "magic" behaviour (hidden-magic risk)
- **Raised:** 2026-06-09 (user, during C-7 cart-button design — started as the
  "preferred product" worry, broadened to every automatic behaviour)
- **Type:** open question / app-wide UX assessment (product-direction call)
- **What:** The user is wary of **background behaviour the app performs without an
  explicit instruction** — anything that makes someone go *"why did the app do
  that? that's annoying."* The trigger was "preferred product/merchant", but the
  concern is general: every silent default, auto-mutation, and inference should be
  audited for whether the convenience is worth the surprise. Effortless (P1) is a
  Charter principle, but so is not blindsiding the user; this audit finds where
  the balance is wrong.
- **Assessment framework — for each automatic behaviour, decide:**
  (a) **keep silent** (genuinely effortless, low-surprise, easily reversible);
  (b) **make it visible/explainable** (a hint/undo/"why" affordance, e.g.
  "pre-selected your preferred — change?" or a toast that names what happened);
  (c) **make it opt-in / a setting** (off by default, or per-item);
  (d) **drop it** for an explicit choice.
  Bias: silent is fine when it's reversible + obvious; needs surfacing when it
  changes money, data, or list contents in a non-obvious way.
- **Catalogue of behaviours to inventory** (confirmed-seen marked ✓; others
  to verify during the audit):
  - ✓ **Preferred product / merchant** auto-pick in add-to-list / cheapest-offer
    paths (`StockItem.preferred_product_id`). *The original trigger.*
  - ✓ **Cart target inference (C-7 Axis B):** 0 draft lists → silently **create**
    one; 1 → silently use it; the **app-wide session "remembered list"** default.
  - ✓ **Auto-add-when-low** (`StockItem.auto_add_when_low`) — items appearing on
    a list without the user adding them.
  - ✓ **Meal-plan reconciliation** — past days auto-draining the recipe pool /
    auto-decrementing `available_meals` when a day rolls past
    (`reconcile_consumed_meals`).
  - ✓ **Auto-generate shopping list** from low/out/essentials.
  - **"Cheapest" auto-selection** of an offer.
  - ✓ **URL importer** auto-resolving scraped cuisine/category → existing vocab ids.
  - ✓ **Inline-create** of a stock item from a recipe ingredient.
  - ✓ **Mark-cooked / cook** auto-bumping last-cooked date + pool.
  - **Dora / dashboard suggestions** that surface or pre-fill actions
    (`suggestionStore`).
  - **Onboarding** auto-seeding groups / locations / vocab defaults.
  - **Substitute behaviour** (note: the old auto-swap-edits-the-recipe was already
    judged wrong in feedback — confirms the instinct).
  - **Expiry / stock alerts** firing automatically; any auto-status changes.
  - …plus anything else found: grep for places the app **mutates or chooses
    without a direct click** (auto-, default, inferred, silently, primary).
- **Output:** a short audit doc (e.g. `05_investigations/MAGIC_BEHAVIOUR_AUDIT.md`)
  listing each behaviour + verdict (a/b/c/d) + where it's surfaced, so the
  individual fixes become their own follow-ups.
- **Recommended resolution:** the **preferred-product slice** before/with **C-7
  Chunk 1** (it hardens product resolution); the **full audit** as its own pass
  (opportunistic, but ideally before more inference is added — e.g. C-2
  allocation, alerts C-9).
- **State note:** open — assessment not started.

## [OPEN] FU-091 — Browser-verify + run Cookbook Chunk 5 (images + tools)
- **Raised:** 2026-06-09 (Chunk 5 implementation; static-only, no env)
- **Type:** finding / verification (blocks trusting Chunk 5)
- **What:** verify, in order:
  1. `alembic upgrade head` applies migration `b8e3f1a6d2c4` (Tool + RecipeTool tables + seed) on SQLite **and** Postgres; app boots; `verify_mappings()` passes for the new `Tool` entity.
  2. `GET /api/tools` returns seeded tools; Settings → "Recipe tags & categories" has a **Tools** editor (create/rename/delete + recipe counts).
  3. Recipe create/update round-trips `tool_ids`; the edit dialog + detail page tools multiselect populate + save.
  4. Overview **Tools** tri-state filter (include/exclude) filters correctly.
  5. **Images:** upload on the detail page (RecipeImageField) → save → image shows on detail + card (via `GET /recipes/<id>/image`); change + remove work; cache-busts after save; oversized file (>4MB) is rejected client-side; create dialog can attach an image.
  6. Backup → restore round-trips Tool/RecipeTool + recipe images.
- **Recommended resolution:** now/when env available — before Chunk 6.
- **State note:** open — nothing executed.

## [OPEN] FU-089 — Browser-verify Cookbook Chunk 4 (detail-page cleanup)
- **Raised:** 2026-06-09 (Chunk 4 implementation; static-only)
- **Type:** follow-up / browser verification
- **What:** On a recipe detail page, confirm:
  1. Sticky top toolbar: Mark cooked (prominent) / Cook mode / Log cook / Print / Save / kebab(Delete); buttons stay at the **top** on a narrow window (don't drop to the bottom). Delete is not adjacent to Mark cooked.
  2. **Mark cooked** bumps the pool +1 and last-cooked; **Log cook…** still logs N; **Print** opens the print view; **no CSV** option anywhere.
  3. Name is an editable labelled field; blanking it blocks save with an inline error.
  4. **Save**: leaving an ingredient row without a stock item blocks the save (prompt) rather than eating the row; saving with an unchanged name succeeds (no "already exists").
  5. Ingredient rows show a single chip (Missing wins) + tinted row when missing; no double chip.
  6. Cookable/missing box readable in dark themes (Pesto Dark / Cherry Cola Dark).
  7. **Cook mode guard**: with unsaved edits OR not-cookable, Cook mode shows a confirm with a working **Cancel**; clicking outside doesn't navigate; "Save & start" only proceeds if the save succeeds.
  8. **Cook mode exit returns to the recipe detail page** (not the overview).
  9. "Available meals" label; meal ± shows no not-allowed cursor flash.
- **Recommended resolution:** now/when next in the app.
- **State note:** open — nothing executed.

## [OPEN] FU-088 — Browser-verify Cookbook Chunk 3 (card redesign + naming)
- **Raised:** 2026-06-09 (Chunk 3 implementation; static-only)
- **Type:** follow-up / browser verification
- **2026-06-13 update:** User did the verification pass and returned ten
  concrete findings (image-toggle broken, allocated badge never
  appears + drop from overview, meals-cooked relocates to planner,
  meta-line swap, optional ingredients, cookable-via-cook-button-colour,
  difficulty filter/sort, picker modal, etc.). Captured as a follow-up
  redesign proposal: `docs/04_proposals/PROPOSAL_COOKBOOK_CARD_REVISION.md`
  (supersedes `PROPOSAL_COOKBOOK.md §2.10`).
- **2026-06-14 update:** Chunks A + B + C all landed (vue-tsc clean,
  299 unit tests passing).
- **New recommended resolution:** browser-verify the revision end-to-end
  using the proposal §7 coverage table as the checklist (image toggle,
  new footer layout `[♥][chef-hat][add-to-list]`, picker modal with
  per-ingredient checkboxes + Optional separator, difficulty filter +
  sort axis, time-of-day vocabulary in edit dialog, per-row Optional
  checkbox in both editors, cook-mode `(optional)` hint + dimmed rows,
  cookability still server-derived). Pairs with FU-171 (the in-browser
  image-toggle confirm). Flip to RESOLVED only after everything's been
  exercised in the running app.
- **What:** Confirm in a running app:
  1. Recipe cards render with the placeholder media tile, emphasised name, chips, dietary chips, and the meals box; equal-height cards in a grid row.
  2. The card ± **MealStepper** adjusts the cooked pool (updates immediately; decrement disabled at 0). Same stepper works on the recipe detail page and on the stock-item detail page's recipe cards.
  3. **Allocated badge**: appears only when `committed_meals > 0`; **red** when `available_meals < committed_meals` (put a recipe on a future meal-plan day with servings exceeding its cooked pool to test), neutral otherwise. Requires the new `committed_meals` DTO field to populate (verify the API returns it).
  4. Card has **only Cook** as a primary button; kebab shows just add-all-to-list + add-to-meal-plan (no Edit/Duplicate/Delete); clicking the card opens detail.
  5. Collection groups are **collapsible rounded boxes** (header toggles; chevron flips).
  6. **Naming**: main-menu reads "Cookbook"; `g r` + command palette "Go to Cookbook"; detail breadcrumb reads "Cookbook".
- **Recommended resolution:** now/when next in the app — pairs with FU-087 (the filter bug blocks seeing the cards under filters, but the cards themselves are independently testable).
- **State note:** open — nothing executed.

## [OPEN] FU-085 — Run + verify Cookbook Chunk 2 (tag taxonomy overhaul) in a real env
- **Raised:** 2026-06-09 (Chunk 2 implementation; nothing was run — no Python venv / node_modules on the Windows dev box)
- **Type:** finding / verification (blocks trusting Chunk 2)
- **What:** Chunk 2 is a large, unrun backend+frontend change (FK-ify cuisine/category, DietaryTag table, 3 CRUD endpoints + settings, tri-state filter). Verify, in order:
  1. `alembic upgrade head` applies cleanly on **SQLite and Postgres** (migration `a7d2f4c9e1b8`: batch-mode Recipe alter dropping cuisine/category strings + adding cuisine_id/category_id FKs, RecipeTag rebuild to dietary_tag_id, vocab seed). Also test `downgrade`.
  2. App boots — `verify_mappings()` passes for Cuisine/Category/DietaryTag + the reshaped Recipe (risk: the `_cuisine_id`/`_category_id` hidden-FK mapping + the selectin relationships).
  3. `repository.get(Recipe).all()` actually selectin-loads `recipe.cuisine`/`.category` (assistant + global_search depend on it; if not, they'll show null cuisine/category).
  4. Recipe create/update/list round-trips `cuisine_id`/`category_id`/`dietary_tag_ids`; `GET /recipes/tags` returns DB-backed tags (value = id) + disclaimer.
  5. Overview: cuisine/category single-selects filter; tri-state DietaryTagFilter cycles +/−/neutral and stays open; RecipeCard shows cuisine/category names + tag chips.
  6. Edit dialog + detail page: cuisine/category selects + dietary multiselect populate from existing recipe + save correctly; URL importer pre-fills matched cuisine/category.
  7. Settings → "Recipe tags & categories": create/rename/delete for all three vocabularies; usage counts + delete warnings; deleting a cuisine/category nulls recipes (SET NULL), deleting a dietary tag removes the links (CASCADE).
  8. Backup → restore round-trips Cuisine/Category/DietaryTag/RecipeTag in FK-correct order.
  9. Dora assistant: search_recipes/suggest_recipes still filter by cuisine + dietary tags (now Python-side / name-resolved).
- **Recommended resolution:** now / first thing once a working env is available — before building Chunk 3+ on top.
- **State note:** 2026-06-09 — first user browser pass: migration applied + app boots + settings CRUD + add-modal dietary tags all **confirmed working** (items 1,2,4,7 effectively ✅). Two gaps found: (a) overview filters unusable → split out as **FU-087**; (b) no dietary-tag editor on the detail page (only the add modal) → **fixed** (added a multiselect to `RecipeDetailPage.vue`, L264). Still to verify: items 3 (selectin), 5 (filters), 6 (detail-page tags), 8 (backup), 9 (assistant).
- **State note:** 2026-06-12 — second user browser pass surfaced
  five concrete findings split out as their own FUs (so FU-085
  doesn't become an umbrella for everything cookbook-shaped):
  - **FU-146** (RESOLVED this session) — GitHub-issues mentions
    swept out (repo private).
  - **FU-147** — detail-page dietary-tag picker doesn't
    pre-populate + chips clear after save (item 6 partial fail).
  - **FU-148** — Cookbook overview missing "time of day" filter.
  - **FU-149** — Cookbook overview missing "# ingredients"
    filter + sort axis.
  - **FU-150** — assistant chat-mode doesn't recognise dietary
    or cuisine queries (item 9 partial fail).
  FU-085 itself stays OPEN until items 3 (selectin), 5 (filters
  end-to-end), 6 (FU-147 fix verified), 8 (backup), 9 (FU-150
  fix verified) are all green.

## [OPEN] FU-084 — Consider an ADR/rule for "selectin for small always-wanted lookups"
- **Raised:** 2026-06-09 (Chunk 2)
- **Type:** finding / engineering-standards
- **What:** Chunk 2 made `Recipe.cuisine`/`.category` relationships `lazy="selectin"` (vs the codebase's noload default) so the ~10 read sites don't each need an `.include()`. If this pattern recurs for other small reference-data relationships, promote it to an `R-0NN` + ADR in `ENGINEERING_STANDARDS.md` (with the caveat: only for tiny, always-wanted lookups — not for large/optional relations where noload + explicit include is correct).
- **Recommended resolution:** opportunistic — when the next selectin-vs-noload call comes up.
- **State note:** open.

## [OPEN] FU-082 — Add `created_at` to Recipe DTO so "Recently added" sort axis can land
- **Raised:** 2026-06-09 (Cookbook Chunk 1; IMPL plan called for the axis)
- **Type:** finding / Phase-2
- **What:** `IMPL_PLAN_COOKBOOK.md` Chunk 1 listed five sort axes including `created-at`. Recipe DTO has no created timestamp today, so Chunk 1 shipped four (`name`, `last_made`, `meal_count`, `total_time`). Adding it is mechanical: a `created_at` column already exists on most domain tables; expose it through `table_mappings.py` and the recipe DTO + SORT_OPTIONS const in `RecipesOverview.vue`.
- **Recommended resolution:** Phase 2 (ingestion API) or when Cookbook Chunk 4 (detail cleanup) is touched — that's the chunk likely to touch the recipe DTO anyway.
- **State note:** open.

## [OPEN] FU-081 — Move "Planned in" filter from client-side to server-derived Recipe.is_planned
- **Raised:** 2026-06-09 (Cookbook Chunk 1)
- **Type:** finding / state-ownership
- **What:** The "Planned in" filter in `RecipesOverview.vue` derives the set of upcoming recipe ids client-side by walking `mealPlanStore.mealPlans[].entries[]` and matching `scheduled_for >= today`. This is a cross-entity rule (recipes × meal plans × today) — R-003 says server-owned. Chunk 1 was constrained to "no model changes" so it shipped client-side; logged here so it gets folded into the right Phase-1 work.
- **Recommended resolution:** when `IMPL_PLAN_STATE_OWNERSHIP.md` lands the server-owned cookability work, add `is_planned: bool` (any future entry exists) to the Recipe DTO and switch `plannedRecipeIds` to read it directly. Cheap to migrate the filter — one ref + one predicate line.
- **State note:** open — current implementation is acceptable but flagged.

## [OPEN] FU-076 — P6-01 Chunk 7 browser smoke
- **Raised:** 2026-06-08 (Chunk 7 impl)
- **Type:** follow-up
- **What:** Run the migration locally (`alembic upgrade head` lands `e1a4c7b2f9d0`), restart the API + web app, then:
  1. Open a list → header chip reads "No shop day" → click → date dialog → save 2026-07-01 → chip updates → refresh → still set.
  2. Clear the date via the dialog's *Clear* button → chip → "No shop day".
  3. Create a list via **New list** dialog with a date → detail loads → chip shows the date.
  4. Set a DRAFT's date to today → navigate to `/shopping-lists` → lands on that draft (priority pick).
  5. With today set: the in-detail banner appears with info-tone "Shopping day is today."
  6. With a past date (e.g. yesterday) set + status still DRAFT: warning-tone banner says "Planned shop day was … — still unfinished."
  7. Selector dropdown: a list with a planned date sorts ahead of unscheduled lists; today's list sits at the top of its band.
  8. Cross-theme: Pesto Light + Pesto Dark + Cherry Cola Dark.
- **Why deferred:** no live API/DB in this session.
- **Recommended resolution:** now (alongside FU-066/068/069/072/073).

## [OPEN] FU-075 — Run the new `test_shopping_list_planned_shop_date` e2e
- **Raised:** 2026-06-08 (Chunk 7 impl)
- **Type:** follow-up
- **What:** Apply migration `e1a4c7b2f9d0` to the test DB, then `pytest tests/e2e/dora_api/test_shopping_list_planned_shop_date.py -v`. Four cases (create-with-date, create-without, PATCH set-and-clear-with-null, PATCH preserves the date when not sent).
- **Why deferred:** no live server in the implementation session; py_compile is not a runtime check.
- **Recommended resolution:** now, with FU-076.

## [OPEN] FU-074 — Wire planned-shop-day into the real alert pipeline (C-9)
- **Raised:** 2026-06-08 (Chunk 7 impl)
- **Type:** finding (deferred-by-design)
- **What:** Chunk 7 surfaces planned-shop-day as a banner on the list detail. The IMPL plan says it "feeds C-9's new alert types" — the actual alert pipeline (alerts bell badge, suggestion-feed insertions, optional push) belongs to the C-9 prompt's surface. When C-9 runs, register a new `shopping_day_today` / `shopping_day_overdue` alert type that fires on the same condition as the banner, and de-dupe so the banner stays the in-page hint while the alerts list / bell badge handle global notification.
- **Why deferred:** alert types + their dedupe semantics live in C-9, not in P6-01 Chunk 7.
- **Recommended resolution:** when C-9 (alerts) executes.

## [OPEN] FU-073 — P6-01 Chunk 6 browser smoke
- **Raised:** 2026-06-08 (Chunk 6 impl)
- **Type:** follow-up
- **What:** Verify the in-store polish behaves in the real browser:
  1. Start shopping → tap *Skip* → next item shows → refresh page → the skipped item is still at the end (persisted).
  2. Tap the centre qty number → dialog opens → type "12" → Save → qty row shows 12; refresh → still 12.
  3. Tap **Peek list** (header) → modal lists ticked + unticked → tap an unticked item → modal closes + that item is now next-up → refresh → still next-up.
  4. Detail page (DRAFT): drag line from position 1 onto position 5 → it lands at index 5 (visual slot of the row it was dropped on). Drag from 5 to 1 → lands at index 1. Off-by-one no longer present (feedback L414).
  5. Detail page header: confirm the old back-arrow is gone (replaced by the list selector).
  6. Cross-theme: open in Pesto Light + Pesto Dark + Cherry Cola Dark.
- **Why deferred:** vue-tsc clean is not a UX test; no dev server in this session.
- **Recommended resolution:** now (alongside FU-066/FU-068/FU-069).

## [OPEN] FU-072 — Chunk 6 audit: pricing-as-you-go + group-by-aisle still respect their contracts
- **Raised:** 2026-06-08 (Chunk 6 impl)
- **Type:** finding
- **What:** Two Chunk 6 line items in the IMPL plan were observed as already-implemented in code (`openPriceEditor` exposed from the shop-mode card; `lineGroups` on the detail page reads `stock_location_breadcrumb` and never writes `sequence`). They need a five-minute browser confirmation that (a) the price editor still opens mid-shop and saves `actual_unit_price`, (b) toggling group-by-location → none → group-by-merchant doesn't quietly mutate the saved order. Once confirmed, flip this to `[RESOLVED]`.
- **Why deferred:** no dev server in the implementation session; pure static read isn't enough proof per CLAUDE.md.
- **Recommended resolution:** confirm in browser (alongside FU-073).

## [OPEN] FU-069 — P6-01 Chunk 5 browser smoke
- **Raised:** 2026-06-08 (Chunk 5 impl)
- **Type:** follow-up
- **What:** Verify the merged surface end-to-end:
  1. `/shopping-lists` with multiple lists → lands on SHOPPING list if any, else newest DRAFT, else newest DONE.
  2. `/shopping-lists` with zero lists → empty-state renders the **New list** button; clicking opens the dialog; submitting routes to the created list.
  3. Detail list-selector: dropdown opens with **Active** group (current highlighted), **Archived** group below the separator, **+ New list** at the top, **Manage templates…** at the bottom.
  4. Active row kebab → Copy unticked / Archive / Delete each behave correctly. Archived row kebab → Copy archived / Delete.
  5. Deleting the currently-open list bounces to the landing and the landing picks the next list.
  6. **+ New list** in the selector opens the dialog; submit routes to the created list.
  7. Switching to a different list via the selector loads its detail (status watcher / shop-mode redirect still works for SHOPPING).
  8. Cross-theme: open in Pesto Light + Pesto Dark + Cherry Cola Dark.
  9. Mobile width: the dropdown is still usable (the proposal eventually wants a dedicated mobile dropdown surface — see FU-071).
- **Why deferred:** vue-tsc clean is not a UX test; no dev server in this session.
- **Recommended resolution:** now (alongside FU-066/FU-068).

## [OPEN] FU-071 — Desktop right-panel + mobile-top-dropdown list selector
- **Raised:** 2026-06-08 (Chunk 5 impl)
- **Type:** finding (UX polish per proposal §2.3 / feedback L405-L406)
- **What:** Proposal calls for a desktop **right panel** (always visible) and a mobile **top dropdown**. Chunk 5 ships a single `q-btn-dropdown` shared across viewports as a viable interim. The dedicated right-panel layout (always visible on >=md, the dropdown collapses below that) is the next step.
- **Why deferred:** would have nearly doubled Chunk 5's edit surface; the dropdown is the same UX *capability* on both viewports, just less ambient on desktop.
- **Recommended resolution:** opportunistic — pair with Chunk 7 (planned shop day + cleanup) or as standalone polish.

## [OPEN] FU-068 — P6-01 Chunk 4 browser smoke
- **Raised:** 2026-06-08 (Chunk 4 impl)
- **Type:** follow-up
- **What:** Verify the unified "New shopping list" dialog handles every old door correctly:
  1. Toolbar *New list* → *Empty + Create new* → produces an empty list, routes into it.
  2. *Empty + auto-fill: low-or-out + new* → equivalent of the old "From all low/out stock".
  3. *Template + new* → uses `instantiateAsync`; lines match the template.
  4. *Recipe + new* → bulk-adds the recipe's ingredient stock items.
  5. *Meal plan + new* → bulk-adds `getIngredientsAsync` results.
  6. *Empty + auto-fill: flagged + essentials-only + merge into existing* → equivalent of old "Top up the primary list".
  7. *Template + merge*: confirm the temp-list-then-delete dance leaves no orphan list in the overview (refresh after).
  8. Empty-state — when no active lists and stock has low/out items, the kickstart "New list" button opens the dialog with *low-or-out* pre-ticked.
  9. Cancel button discards the form (re-open shows defaults again).
  10. Cross-theme: open in Pesto Light + Pesto Dark + Cherry Cola Dark.
- **Why deferred:** vue-tsc clean is not a UX test; no dev server in this session.
- **Recommended resolution:** now (alongside FU-066).

## [OPEN] FU-066 — P6-01 Chunk 3 browser smoke
- **Raised:** 2026-06-08 (Chunk 3 impl)
- **Type:** follow-up
- **What:** Eyeball the lifecycle end-to-end in the running app:
  1. DRAFT detail → *Start shopping* button → confirm router lands on /shop directly.
  2. SHOPPING /shop → tick a few items → kebab *Finish & restock* AND footer button → confirm the dialog lists the ticked items (capped at 8 + "and N more") → confirm restock + archive.
  3. SHOPPING /shop → back-arrow → confirm tooltip reads "Back to editing", confirm status flips to DRAFT, confirm route lands on detail (not bouncing back).
  4. DONE detail → *Reopen* → confirm restock changes reverse and status returns to DRAFT.
  5. PWA "Shop now" — confirm the existing status-driven routing (1 SHOPPING → resume; else 1 DRAFT → open; else overview) still works end-to-end.
  6. Open in Pesto Light + Pesto Dark + Cherry Cola Dark to confirm dialog / primary-button styling still reads.
- **Why deferred:** dev server not run in this session; vue-tsc clean is not a UX test.
- **Recommended resolution:** now (before Chunk 4).

## [OPEN] FU-065 — Ticked-summary string duplicated across both finish dialogs
- **Raised:** 2026-06-08 (Chunk 3 impl)
- **Type:** finding (R-003 lite — same display string built in two places)
- **What:** `ShoppingListDetail.vue` and `ShoppingListShopMode.vue` each build the "N items will be bumped to Well-Stocked: a, b, c, and N more." string for their respective Finish-and-restock dialog. Identical algorithm, two copies. If the wording or cap-count changes, both need editing.
- **Why deferred:** extracting a single helper is one line of value today; both copies are 4-line, Type-C display logic, and the two dialogs *do* differ (Detail has the copy-unticked-to-new-list radio, ShopMode appends a one-line note). Worth a helper only if a third caller appears, or if the wording becomes prose worth localising.
- **Recommended resolution:** opportunistic — when C-locale (FU-043) lands, fold both summaries through one localised builder. Otherwise leave alone.

## [OPEN] FU-060 — Chunk 2 browser smoke: 2+-draft picker, shop-now routing, set-primary removal
- **Raised:** 2026-06-07 (P6-01 Chunk 2 implementation)
- **Type:** finding / browser verification
- **What:** Verify in the running app:
  1. With 2+ drafts, the stock-overview cart click pops the disambiguation
     dialog; the chosen draft persists across cart clicks for the rest of the
     tab session (sessionStorage). Finishing the chosen draft clears the
     stale-hint and the next cart click re-prompts.
  2. With 0 drafts, the cart click shows the "No draft list" dialog → "Open
     lists" lands on the overview.
  3. PWA "Shop now" shortcut: 1 SHOPPING list → goes straight to shop mode; 1
     DRAFT (and no SHOPPING) → goes to that draft's detail; anything else →
     overview.
  4. No "Set as primary" / "Make primary" / "Primary" badge / Primary chip is
     visible anywhere (Shopping lists overview, Shopping list detail,
     ShoppingListTemplates use-as-primary action, ExportPrint primary chip).
  5. Migration `d5e9f3b2a1c8` applies cleanly on a real dev DB (alongside
     FU-057 for the c4d8e1a6f3b9 migration).
- **Recommended resolution:** **confirm in browser** — these are functional
  paths a static type-check can't fully cover; FU-059's line-tick fix
  similarly waits on browser confirmation.

## [OPEN] FU-056 — P6-02 deferred: register-against-product UI + ingestion EAN auto-populate
- **Raised:** 2026-06-07 (P6-02 implementation — "Cleanup now, UI later")
- **Type:** deferred job
- **What:** The backend `POST /api/data/barcodes/register-against-product` route exists and
  is tested, but there is **no UI** to drive it (scan unknown barcode → pick a Product →
  create `ProductBarcode`). Also: ingestion should auto-populate `ProductBarcode` from a
  feed's EAN/UPC field so most barcodes resolve without manual registration.
- **Why deferred:** `Product` has no EAN field today (only `merchant_stockcode`), so a manual
  register UI now would be the only path and low-value. Ingestion is the natural place to
  add an EAN field + auto-fill `ProductBarcode` at scale.
- **Recommended resolution:** later during **Phase 2 (ingestion API)** — design is in
  `docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md` §5–§6.

## [OPEN] FU-052 — Switch cookable surfaces to the server query + optimise the helper
- **Raised:** 2026-06-07 (Phase 1 Chunk 4 — queryable cookability)
- **Type:** follow-up
- **What:** Chunk 4 added the `?cookable` / `?max_missing` API + `cookable_count`,
  but the **shared-store surfaces still fetch all recipes and filter client-side**
  on `r.cookable` (RecipesOverview's cookable toggle / missing-max; the dashboard
  "Cookable tonight" list). Proposal step 4 ("switch the cookable surfaces to
  query") isn't finished. Two parts: (a) make those surfaces *query* the server
  (tricky — the recipes Pinia store is shared and does multi-facet client filtering,
  and the dashboard top-3 needs server-side sort+limit, currently client-sorted by
  favourite/last-made); (b) `load_recipe_cookability` loads **all recipes + full
  ingredient trees** on every dashboard summary and every cookable-filtered query —
  one query (not N+1) and fine at personal scale, but a set-based `COUNT(...) GROUP
  BY recipe` would scale better (watch SQLite/Postgres portability — avoid engine-
  specific `FILTER`).
- **Why deferred:** the store rewire is a real refactor needing browser verification
  (FU-051), and the perf optimisation is premature at current scale (R-007).
- **Recommended resolution:** **later — fold into the Type-B aggregates pass / when
  recipe counts grow.** Backend capability already exists; this is the client
  adoption + optimisation tail.

## [OPEN] FU-051 — Chunks 3–5 client changes not type-checked / browser-verified
- **Raised:** 2026-06-07 (Phase 1 Chunk 3); extended (Chunks 4, 5)
- **Type:** finding
- **What:** The Vue/TS files edited in Chunks 3, 4 **and 5** were verified only by
  manual grep (no dangling references) + reasoning. **They were not run through
  `eslint`/`vue-tsc` or the browser** because `web_app/node_modules` is absent on
  this machine and the local Node is v14.17 (too old for the Quasar toolchain).
  Risk: a type mismatch or template-binding slip could slip through. Likewise the
  Chunk-4/5 **server** additions (cookability filter + `cookable_count`; shopping-list
  `totals`) were unit-tested for their pure logic but **not run against real data**
  (this env's SQLite has no migrated tables — see FU-048), so the DB-backed query
  paths are unproven end-to-end.
- **Why deferred:** no runnable frontend toolchain / migrated DB in this session.
- **Recommended resolution:** **now/next session with a working env** — `npm install`
  then `npm run lint` + `quasar dev`; exercise: Recipes overview (cookable filter +
  footer count + compare dialog), a recipe card chip, recipe detail sidebar + editor
  "Missing" badge, meal-plans palette, dashboard "Cookable tonight" + count, Dora's
  "what's missing" (Chunks 3-4); **and the dashboard primary-list stats + the
  shopping-list detail headline totals (Chunk 5) — confirm $ remaining / savings /
  counts match what the lines imply.** On the server, hit
  `GET /api/recipes?cookable=true|false`, `?max_missing=1`, `/api/dashboard/summary`,
  and `GET /api/shopping-lists/<id>` (check the `totals` block) against seeded data.

## [OPEN] FU-050 — Broader `'Out of Stock'` name-match smell beyond the 7 cookability copies
- **Raised:** 2026-06-07 (Phase 1 Chunk 3)
- **Type:** finding
- **What:** Chunk 3 removed the 7 *recipe-cookability* client copies. A grep
  shows `'Out of Stock'` / `'Low Stock'` name-matching still lives in non-recipe
  surfaces: `MealPlansOverview.vue:484,494` (the meal-plan "need to buy"
  `stockLevelName`/`needToBuy`), `ShoppingListsOverview.vue:489` (restock
  sources), `RecipeCookMode.vue:559` (cook-mode availability), `StockItemChip.vue`,
  `StockItemRow.vue`, `useStockFilters.ts` (stock-page filters). Some are
  legitimately client-side (stock-page filters = state-ownership Type D) or use
  the shared `stockLevelLogic.getStockLevelColour` helper (accepted Type C); but
  `needToBuy`, the restock sources, and cook-mode availability are the same
  cross-entity rule the §8.3 addendum flags as the "wider smell" and could adopt
  the StockItem server booleans (now on the TS model) instead.
- **Why deferred:** out of Chunk-3 scope (R-007 — Chunk 3 is specifically the 7
  cookability copies).
- **Recommended resolution:** **opportunistic / a follow-on state-ownership pass** —
  migrate `needToBuy`, restock sources, and cook-mode availability to read
  `stockItem.is_out_of_stock` / `is_low_stock` / `needs_restock`. Leave the
  stock-page filters (Type D) and the color helper (Type C) per §8.1.

## [OPEN] FU-049 — RecipeDetailPage cookability reflects saved recipe, not live edits
- **Raised:** 2026-06-07 (Phase 1 Chunk 3)
- **Type:** finding
- **What:** The recipe-detail sidebar "Cookable now / Missing N" + in/tracked
  counts now read the *loaded* `recipe.value` server fields rather than the live
  editable `form.ingredients`. So while a user adds/removes ingredients (before
  saving), the sidebar aggregate doesn't update until save (which reloads the
  recipe). The per-ingredient editor "Missing" badge *does* update live (reads
  the stock store's `is_out_of_stock`). Previously the whole sidebar updated live
  off client-recomputed stock joins.
- **Why deferred:** the server can't know unsaved ingredients, and recomputing
  the aggregate client-side is exactly the duplication Chunk 3 removed. The page
  reloads after every save, so the steady-state is correct.
- **Recommended resolution:** **confirm acceptable in browser** (FU-051). If
  live-while-editing is wanted, derive the aggregate from the editor rows'
  `isMissingItem` (already server-boolean-based) instead of `recipe.value` — a
  small, contract-clean change.

## [OPEN] FU-046 — A1 theme chunks D–F regressed since "done"; CHANGELOG over-claims
- **Raised:** 2026-06-06 (A1 STEP 2 Chunk D verify/finish)
- **Type:** finding
- **What:** `CHANGELOG.md` [Unreleased] (committed in `5819fe8 "Begin major rework —
  part A1 A2…"`) claims A1 STEP 2 Chunks **D, G, C, B, E, H, F** all theme-token-
  compliant. They *were* at that commit, but later wave-A/B feature work re-introduced
  Quasar palette literals on several surfaces. Confirmed live offenders on a
  2026-06-06 scan: **Chunk D** — `RecipesOverview`/`RecipeDetailPage`/`RecipeCard`
  (4 literals; **fixed this session**); **Chunk B** — `StockItemRow.vue:274`
  (`colour:'grey-5'`); **Chunk E** — `MealPlansOverview.vue:96-97` (`'grey-4'`/
  `'grey-9'` cookable chip, same pattern as RecipeCard); **Chunk G** —
  `ProviderHealthChip.vue:23` (`'grey-7'`). Broader `grep` flags ~12 surfaces total,
  but several are accepted carve-outs (ScanOverlay DEC-4, ProductSearchCard DEC-8,
  MerchantLogo DEC-9, settings theme swatches DEC-10) — needs a per-file pass to
  separate regressions from carve-outs.
- **Why deferred:** out of scope for "finish Chunk D" — fixing B/E/G/etc. regressions
  is a separate sweep, and the carve-out/regression split needs per-file judgement
  against the DEC list. Logged so the stale "all chunks done" CHANGELOG claim doesn't
  fool the next agent into skipping a needed re-sweep.
- **Recommended resolution:** **opportunistic — run an "A1c regression re-sweep"**
  (re-grep every claimed-done chunk surface for palette literals, fix genuine
  regressions, leave DEC carve-outs) before signing A1 off as complete. The
  cookable-chip `positive/grey` pattern (RecipeCard + MealPlansOverview) is the most
  common regression shape — worth a shared neutral-chip approach.

## [OPEN] FU-045 — Migrate to Postgres as the standard datastore (SQLite kept for lightweight self-host)
- **Raised:** 2026-06-06 (distribution posture — Decision 5 / §7.5)
- **Type:** deferred job
- **What:** Make **Postgres the standard datastore** for dev + hosted; SQLite stays
  supported as the zero-dependency lightweight self-host option (user decision:
  Postgres-default, *not* Postgres-only — retiring SQLite would raise the self-host
  bar). Motivation: SQLite feels too unstable for the long term. Scope when done:
  local Postgres dev setup (docker-compose or similar), confirm Alembic migrations
  run clean on both engines, keep the dev reset flow (`drop_all` /
  `DORA_ALLOW_DESTRUCTIVE` — see memory) working on Postgres, and re-check the
  UUID/`text()` binding sharp edge (Postgres has native UUID, so the raw-`text()`
  workaround likely simplifies — verify both inbound and outbound). Keep the
  ORM/migration layer portable both ways per discipline #2.
- **Why deferred:** posture recorded now; the actual migration is real engineering,
  best done as its own focused unit rather than mid-stream. No urgency — SQLite works
  today.
- **Recommended resolution:** **later — fold into Phase 4 productionize**
  (`RECONCILED_FINISHING_PLAN.md §5`, which already lists "Postgres/gunicorn/Redis"),
  OR opportunistically sooner if the user wants to dev against Postgres before then.
  Not a blocker for Phase 0/1.

## [OPEN] FU-044 — C-help opt-in help-overlay brief written; awaiting approval + per-surface hint rollout
- **Raised:** 2026-06-06 (user-floated idea → `PROPOSAL_HELP_OVERLAY.md`)
- **Type:** deferred job (design brief done; implementation pending approval)
- **What:** A persistent "?" toggle overlaying dismissible per-element "what does
  this do" hints — the opt-in inverse of the forced tour C-5 removed. Net-new
  cross-cutting front-end component (no existing tour/coachmark system). The
  expensive part is **content** (a hint per control, kept from rotting), so the
  brief defers the hint corpus to a per-surface rollout folded into each C-1..C-9
  implementation prompt.
- **Why deferred:** brief-only per the Wave-C ritual; no code until the user
  approves and resolves §4 open decisions (reveal style, content model, mascot,
  discoverability).
- **Recommended resolution:** **when the user approves the brief** — build the
  mechanism + `v-help` directive first (§8.1), then seed hints on the highest-
  confusion surfaces, then roll out per-surface as each C-brief implements. Pair
  the C-5 finish-card mention (§4-4) with C-5 implementation.

## [OPEN] FU-043 — C-locale international-readiness brief written; awaiting approval
- **Raised:** 2026-06-06 (user-floated idea → `PROPOSAL_LOCALE_I18N.md`)
- **Type:** deferred job (design brief done; implementation pending approval)
- **What:** Make Dora usable outside Australia. Companion split solves product
  sourcing; Dora-core still has AU residue — hardcoded `$` currency, `en-AU` voice
  default (`useVoiceInput.ts`), AU merchant branding/copy/seed in core, and a
  **dormant vue-i18n scaffold** (installed in `boot/i18n.ts`, locale hardcoded
  `en-US`, stub messages, zero `$t()`). Brief recommends Layer A (currency/format
  neutrality) + Layer B (de-AU core) now; Layer C (full UI translation) deferred.
- **Why deferred:** brief-only; no code until approval + §3 open decisions
  (currency home, vue-i18n adopt-vs-rip, C-10 currency field, merchant-logo fate).
- **Recommended resolution:** **when the user approves** — fold the currency
  setting + shared money formatter into the C-cross config work (they share the
  config layer); coordinate the C-10 currency field with the ingestion impl;
  de-AU (voice/branding/seed) is independent and low-risk. Layer C stays parked.

## [OPEN] FU-042 — Alerts bell count ≠ list count (badge excludes low + ignores snooze)
- **Raised:** 2026-06-06 (C-9 brief; feedback L438)
- **Type:** finding (reported bug — root cause found statically)
- **What:** The bell badge shows fewer than the dropdown lists ("I see 6, the bell
  shows 10"). Two causes: (1) badge = `high_count + medium_count` (`alertStore:99`)
  — it **excludes low-severity**, but the list shows all severities; (2) the badge
  uses raw backend counts while the list filters **client-snoozed** alerts
  (`alertStore:81`), so snoozing shrinks the list but not the badge.
- **Why open:** real reported bug; fixable independently of the full C-9 page.
- **Recommended resolution:** define ONE "what counts" set (C-9 §2.3) and derive
  the badge, bell list, dashboard card, and page from it — badge number must equal
  the count of items in its tier, and snooze must apply everywhere. Confirm in
  browser after. Can ship ahead of the control-centre page.
- **Update 2026-06-15 (fixed in C-9.1, pending browser):** resolved in code — the server now
  derives ONE canonical count (`get_alerts.py`: `actionable_count` = the active actionable-tier
  list) and the badge reads it directly with no client recompute (R-003); server-side per-user
  snooze/dismiss apply everywhere by construction. The exact invariant
  (`actionable_count == #(actionable items in the list)`) is asserted by a passing e2e
  (`test__alerts__actionable_count_equals_high_plus_medium_in_items`). Kept OPEN only for the
  in-browser confirm, tracked on **FU-183**'s browser checklist — flip both together.

## [OPEN] FU-041 — Onboarding "you already have groups/locations" copy on first-run
- **Raised:** 2026-06-06 (C-5 brief; feedback L32/L33)
- **Type:** finding (reported defect — didn't reproduce statically)
- **What:** User reported the seed step says "You already have some groups set
  up…" / "You already have locations…" during *first-time* setup. Static read
  shows that copy is gated on `has_groups`/`has_locations` (`onboarding.py:94-117`,
  `WelcomeWizard.vue:161-172,195-205`), which are false on a truly-empty DB — so it
  shouldn't render on a clean install. The user likely had dev/seed data or a prior
  seed run. No migration pre-creates *user* groups/locations (confirmed).
- **Why open:** the report came from real usage; a static read isn't proof.
- **Recommended resolution:** **confirm in browser** on a genuinely fresh DB
  (register first user → onboarding) that the "already have" copy does NOT appear
  and the seed checkboxes are enabled. If it DOES appear, find what's seeding user
  groups/locations and fix. Folded into the C-5 §2.6 design either way.

## [OPEN] FU-034 — Wire up `StockItemSubstitute.notes` (substitution notes)
- **Raised:** 2026-06-06 (INV-1)
- **Type:** deferred job
- **What:** `StockItemSubstitute.notes` column exists (added in the
  `c8a1d3b6e9f4` undirected-refactor migration) but was never wired up.
  `add_substitute.py:66` hardcodes `notes=None`; absent from `SubstituteDto`;
  zero frontend references. **Intended feature** (user confirmed): notes should
  capture *how* to substitute, e.g. "X butter → Y amount of olive oil".
- **Why deferred:** wire-up work, not no-regret; best done with the substitute
  surface so the note shows where it's useful (incl. B8 cook-mode swap).
- **Recommended resolution:** later — fold into **INV-8** (substitute
  swap-into-list assessment) or **B8** cook-mode temporary-swap work.

## [OPEN] FU-032 — C-2: allocation count doesn't decrement after planner drop (live repro, root cause TBD)
- **Raised:** 2026-06-06 (C-2 recon); user repro confirmed 2026-06-12
- **Type:** finding (real bug, not yet root-caused)
- **What:** User dragged recipes from the palette onto future days; the
  chip's count next to the recipe name didn't change. Static read of
  the data path looks correct end-to-end:
  - Frontend `MealPlansOverview.onDropOnDay` → `persistEntries` →
    `mealPlanStore.updateMealPlanAsync` awaits the PATCH **and** the
    follow-up `getMealPlansAsync`, then in parallel
    `recipeStore.getRecipesAsync()` runs.
  - Backend `UpdateMealPlanHandler.handle` calls `save_changes()`
    before returning (commit guaranteed).
  - Backend `_hydrate_unallocated` (`get_recipes.py:591`) issues one
    GROUP BY against `MealPlanEntry` filtering
    `consumed_at IS NULL AND scheduled_for >= today AND recipe_id IN :ids`
    and subtracts from `available_meals`.
  - Frontend chip ([MealPlansOverview.vue:101](web_app/src/pages/MealPlansOverview.vue#L101))
    is `(N) = recipe.unallocated_meals` bound through
    `storeToRefs(recipeStore).recipes` — reassigning `recipes.value` in
    `getRecipesAsync` should trigger re-render.
- **Possible runtime causes (none verifiable without devtools):**
  1. **User is reading `available_meals` not `unallocated_meals`.** The
     chip shows `(unallocated_meals)` next to the recipe name; the
     click-menu shows `available_meals` as the big number. Drops only
     decrement `unallocated_meals` (cooked pool unchanged — that only
     moves on Cook / ± adjust). Worth confirming which number the user
     is tracking.
  2. **Reactivity edge case** with `storeToRefs` + sorted array
     reassignment. Unlikely but only visible at runtime.
  3. **`scheduled_for` date comparison** — backend filters
     `scheduled_for >= :today` using `date.today()` (server local).
     Drops on "today" land on the boundary; future drops shouldn't be
     affected. Cross-timezone client/server could in theory miss a
     same-day entry — unlikely with future drops.
- **C-2 redesign cross-ref:** `PROPOSAL_MEAL_PLANS.md §3.1` re-renders
  the same numbers (`(unallocated / pool)` chip — emphasised on the
  recipe row) and `§3.2` reworks the entry chip shape. The C-2 work is
  **design only — no impl plan yet**, so the chip surface in production
  isn't going to change soon. Don't defer the bug fix to "when C-2
  lands."
- **Recommended resolution:** when the user is next at a browser:
  1. Confirm whether the unchanging number is the `(N)` next to the
     recipe name (real bug) or the bigger `{{ available_meals }}` in
     the click-menu card (expected behaviour, not a bug).
  2. If the `(N)` is genuinely stuck, capture the network response from
     `GET /api/recipes` immediately after the drop — does the JSON
     show the new `unallocated_meals`? If yes, it's a frontend
     reactivity bug; if no, it's the backend's SUM not seeing the new
     row (transaction visibility / date filter).
  3. With that one bit of evidence the root cause collapses to either
     a Vue reactivity patch or a backend date / commit-visibility fix.

## [OPEN] FU-025 — A6 text scale: many surfaces still don't respond (likely needs its own sweep)
- **Raised:** 2026-06-05 (A6); user-verified gap 2026-06-12
- **Type:** finding (real, app-wide)
- **What:** Initial A6 in-browser check (2026-06-12) confirmed the scale
  steps themselves are working at the page level, BUT user observed that
  **a lot of secondary text still doesn't change size** when the scale is
  changed — e.g. **button labels, input text, toggle labels**, and likely
  other component-internal text. These almost certainly use Quasar's
  component CSS (`font-size` declared inside `.q-btn__content`,
  `.q-field__native`, `.q-toggle__label`, etc.) which doesn't inherit from
  the page-level rem-scaling tokens A6 set up. Fixing this is broader than
  any single page — likely a Wave-A-style "global pass" prompt that
  overrides the component-internal font-sizes to track the text-scale
  variable (or replaces hard-coded px with the same `rem`/var the body
  text already uses).
- **Why deferred:** out of FU-025's verify scope; needs its own sweep.
- **Recommended resolution:** now-ish — promote into a small Wave-A-shaped
  prompt ("A6b: text-scale follow-through into component-internal text").
  Audit method: grep `font-size` in `web_app/src/css/quasar.variables.scss`
  / overrides, plus a runtime walk through Stock Overview + a form-heavy
  page (Recipe edit, Stock-item detail) at Small vs Extra-large; list each
  surface that doesn't visibly change and convert its `px` to the same
  text-scale var. Deliberately-fixed-px carve-outs (ScanOverlay camera UI,
  PriceHistoryChart SVG labels, Dashboard 3px/7.5px micro-gauge) stay.

## [OPEN] FU-024 — A7 leftovers: dead banner CSS + wider footer adoption
- **Raised:** 2026-06-05 (A7)
- **Type:** leftover
- **What:** (a) Removing StockOverview's summary banner left its scoped
  `.stock-summary-banner` / `.stock-summary-stat` CSS unused (harmless dead
  rules). (b) `PageCountsFooter` is only wired on the 3 prompt pages
  (StockOverview, RecipesOverview, MyProductsPage); other list pages
  (ShoppingLists, MealPlans, etc.) could adopt it for consistency.
- **Why deferred:** dead CSS is harmless; broader adoption was out of A7's
  defined scope (3 pages).
- **Recommended resolution:** opportunistic — delete the dead CSS next time
  StockOverview is touched (or during the Wave-C Stock Overview top-area
  teardown); adopt the footer on other list pages if/when they get polish.

## [OPEN] FU-023 — A5 leftover: spinners not yet migrated on deferred surfaces
- **Raised:** 2026-06-05 (A5)
- **Type:** leftover
- **What:** A5 unified loading on the active app pages, but left raw `q-spinner`
  on the **deferred surfaces** (Reports, Data→Export/Print, Settings sub-pages —
  per the prompt-pack "deferred" list) and on **DoraChat's typing dots** (a
  deliberate `q-spinner-dots` indicator). Also: overview pages got `AppSpinner`
  rather than list-skeletons — fine, but list-skeletons would be a nicer touch.
- **Why deferred:** those pages are flagged "do not design yet"; a spinner swap
  is harmless but low-value there, and DoraChat's dots are an intentional style.
- **Recommended resolution:** opportunistic — migrate the deferred-page spinners
  to `AppSpinner` whenever those pages are next worked on. Decide DoraChat dots
  separately (keep as a typing indicator, or switch to AppSpinner). Consider
  list-skeletons for the big overviews during the FU-010 holistic look pass.

## [OPEN] FU-020 — Recipe-detail substitute swap affordance (cook-mode-only for now?)
- **Raised:** 2026-06-05 (B8)
- **Type:** finding / open question
- **What:** B8 made substitute swapping a temporary **cook-session** action (in
  cook mode only). The recipe-detail "Find substitutes" dialog is now purely
  informational. Open question for the user: do you also want a quick swap
  affordance on the recipe detail page itself, or is cook-mode-only the intended
  model?
- **Why deferred:** cook-mode-only was the chosen scope for B8; adding a second
  swap entry point is a UX decision, not a bug.
- **Recommended resolution:** now-ish — quick user call. If "yes", design where it
  applies (a swap that's still non-destructive to the saved recipe — likely a
  "pre-stage this swap for the next cook" rather than editing the recipe).

## [OPEN] FU-018 — B7: wider sweep for "store mutation + page toast" double-emits
- **Raised:** 2026-06-05 (Wave-B self-audit)
- **Type:** finding
- **What:** B7's "no other double-toast patterns" verdict only walked
  `useShoppingListActions.addItems` callers. Same pattern could exist
  for any store mutation that toasts internally and a page handler that
  toasts on success after. Worth grepping for `$q.notify` and
  `notifyOk` calls inside store/composable methods, then cross-checking
  every caller for a follow-up notify.
- **Why deferred:** out of B7's original scope; opportunistic cleanup.
- **Recommended resolution:** opportunistic — fold into the next polish
  pass.

## [OPEN] FU-016 — Audit other "frontend cache vs backend mutation" guard races
- **Raised:** 2026-06-05 (B5 follow-up)
- **Type:** finding
- **What:** The onboarding "dead button" bug was a stale `authStore.currentUser`
  read by the router guard after `onboardingApi.completeAsync()` updated the
  backend. The same shape could exist for any flow where the backend mutates
  user-scoped state that a guard or computed reads from a frontend cache —
  candidates worth scanning: account changes (email/role/admin flag), data
  import/restore, restart-onboarding. (Stock-item Undo restore was a candidate
  here too; removed with the app-wide undo posture per FU-163.) Look for
  `currentUser?.*` reads in router and layout guards, and pair each with the
  store mutation that should refresh them.
- **Why deferred:** out of B5's bug-fix scope; cross-cutting audit.
- **Recommended resolution:** opportunistic — fold into a Wave-A or polish
  pass once one obvious symptom shows up; not worth a dedicated session.

## [OPEN] FU-012 — FilterBar panel has no visual container
- **Raised:** 2026-06-05 (A4)
- **Type:** finding
- **What:** `FilterBar`'s collapsible panel is a plain div. `ProductSearch`
  previously wrapped its filters in a bordered `q-card`; that border is now gone
  (so all four pages match the borderless inline style the others always used).
- **Why deferred:** consistency was the goal; the other 3 pages never had a card.
  Whether the panel wants subtle containment (border/elevation) is a design call.
- **Recommended resolution:** fold into the FU-010 holistic look review, or a
  quick tweak to `FilterBar.vue` if the panel reads as too bare in the browser.

## [OPEN] FU-011 — AuditLogSettings filtering not standardised
- **Raised:** 2026-06-05 (A4)
- **Type:** finding
- **What:** `settings/AuditLogSettings.vue` has ~9 filter fields with its own
  apply/clear UX. A4 deliberately did not touch it (the prompt scoped A4 to the
  four data-list pages and excluded the deferred/settings pages); its filtering
  is also server-side (sends a query), not the client-predicate pattern FilterBar
  assumes.
- **Why deferred:** out of A4's defined scope; different (server-side) mechanism.
- **Recommended resolution:** later — only if settings/admin gets a dedicated
  polish pass; low priority.

## [OPEN] FU-010 — Late-game holistic theme / colour / overall-look review
- **Raised:** 2026-06-05 (user request)
- **Type:** finding / deferred job
- **What:** A dedicated end-to-end pass over all themes, colours, and the overall
  visual feel of the app — viewed as a whole, in the browser, across the full
  theme set — rather than the per-chunk token work done piecemeal in A1/A1b.
- **Known input — Pesto looks over-dulled:** the user believes Pesto was dulled
  *too far*. Likely cause: the brightness tuning in A1b happened while a theme-logic
  bug was overriding the new values (the `themeService.ts` `THEMES` dict clobbering
  `themes.scss` via `setCssVar` — see the 2026-06-04 A1b round-2 worklog entry and
  the structural fix tracked in [[FU-004]]). So the dulling may have over-corrected
  against values that weren't actually rendering. Now that Pesto/Pesto Dark were
  synced, the *final* dulled value should be re-judged from scratch.
- **Also feed in:** other light themes' `--text-muted` contrast nudge ([[FU-003]]),
  and the structural dual-source collapse ([[FU-004]]) so the review isn't fighting
  a moving target.
- **Why deferred:** look-and-feel polish is best judged late, in one sitting, on a
  near-final app — not litigated token-by-token mid-build.
- **Recommended resolution:** later — a dedicated pass during **Phase 3 (champion
  polish)** or just before **Phase 4 (commercialize)**, once the app is feature-
  complete enough to eyeball holistically. Requires the app actually running
  (deps installed) and ideally a side-by-side across all themes.

## [OPEN] FU-006 — Migrate the remaining ~289 `q-btn` to BaseButton
- **Raised:** 2026-06-04 (A2 Phase 2); rescoped 2026-06-05
- **Type:** deferred job
- **What:** A2 took the app from 399 → ~304 `q-btn`; it currently sits at **~289
  plain `q-btn`** (+ 4 `q-btn-dropdown`, 6 `q-btn-toggle`) across ~40 files. This
  is **NOT part of the standard plan** — A2's prompt was scoped to *toolbar*
  buttons + "New X" placement only, and no other prompt covers the rest. So the
  remainder is a genuine unplanned leftover, captured here on purpose.
- **Breakdown / nuance (don't treat as one uniform job):**
  - **Inline list-row action buttons** — the bulk (recipe cards, stock rows,
    shopping-list lines, settings rows). Low visual impact, the main target.
  - **Products surface** (`MyProductsPage` ~20, `ProductSearch` ~18) — **skip
    these**: that surface is moving to the companion app (master Decision 1), so
    it's intentionally minimal-touch. Migrating them is likely wasted effort.
  - **`q-btn` in `q-input` append slots** (search-clear, copy-to-clipboard) —
    intentionally the minimal pop-out style; leave as-is.
  - **`q-btn-dropdown` / `q-btn-toggle`** — different APIs, out of BaseButton
    scope by design (see FU-005).
  - **`DoraChat` (~14)** — its own component; migrate only if DoraChat is being
    reworked anyway.
- **Why deferred:** out of A2's defined scope; high count, mostly low-impact, and
  a chunk of it (products) shouldn't be migrated at all.
- **Recommended resolution:** later — a dedicated low-priority pass *after* Wave A,
  explicitly excluding the products surface, q-input append buttons, and the
  dropdown/toggle variants. Or purely opportunistic (migrate a page's inline
  buttons whenever that page is open for other work). Not no-regret; not urgent.

## [OPEN] FU-005 — `q-btn-dropdown` / split-button wrapper component
- **Raised:** 2026-06-04 (A2)
- **Type:** deferred job
- **What:** 4 `q-btn-dropdown` + 6 `q-btn-toggle` usages are out of BaseButton's
  scope (different APIs). A wrapper would unify split-buttons if there's appetite.
- **Why deferred:** different component API; not needed for A2.
- **Recommended resolution:** later — only if a design need arises; not no-regret.

## [OPEN] FU-004 — Collapse `themeService.ts` THEMES dict into CSS-var reads
- **Raised:** 2026-06-04 (A1b)
- **Type:** finding
- **What:** 7 themes still have the dual-source coupling between the `THEMES`
  palette dict in `themeService.ts` and `themes.scss`. Their values currently
  match (Pesto / Pesto Dark / Lemon Tart Dark were synced), but it's a latent
  drift hazard.
- **Why deferred:** values match today, so it doesn't block anything.
- **Recommended resolution:** later — a clean-up before commercialise (Phase 4),
  or when a theme bug points back to the dual source.

## [OPEN] FU-003 — Other light themes' `--text-muted` contrast nudge
- **Raised:** 2026-06-04 (A1b)
- **Type:** follow-up
- **What:** only the Pesto family got the `--text-muted` 50→42 lightness bump.
  Other light themes (Lemon Tart, Blueberry, Cherry Cola light, Sourdough light)
  may want the same for AA contrast.
- **Why deferred:** wanted to eyeball Pesto first before touching the whole family.
- **Recommended resolution:** later during a dedicated A1b contrast pass, after the
  user has eyeballed the themes.

## [OPEN] FU-002 — LoginPage `--lp-*` token ladder revisit
- **Raised:** 2026-06-04 (A1)
- **Type:** deferred job
- **What:** `LoginPage.vue`'s private `--lp-*` colour ladder was deliberately left
  untouched (DEC-2 — intentional splash).
- **Why deferred:** it's a one-off intentional design, not theme drift.
- **Recommended resolution:** later during **C19** (shared auth-shell) — revisit
  the whole auth surface together.
