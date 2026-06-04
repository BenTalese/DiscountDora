# Dashy Dora (formerly Discount Dora) — Prompt Plan Part 6: Polish

> **Doc library:** see [00_DOCS_INDEX.md](00_DOCS_INDEX.md). The product is **Dashy Dora**; code identifiers still read "DiscountDora" until **P8-01** renames them, so prompts here intentionally reference the current code name. Governance (verify-state-first + the Dora Decision Charter) lives in DASHY_DORA_CHAMPION_PLAN.md Parts II–III.

A focused wave of paste-ready prompts that close the loops Dora already half-built,
rather than adding new surface area. These supersede / refine several Part 2 items
based on later design decisions:

- **Purchase reconciliation is list-first, not receipt-OCR-first** (refines P2-01/02).
- **Barcode scanning is being trimmed to QR-only, opt-in** (refines the Part 1
  barcode work).
- **Price intelligence becomes real** — deal *quality*, not just `now < was`.
- **Proactivity** — the suggestion inbox + deal→list matching + run-out prediction
  (refines P2-03/04/05).
- **Household + in-store** (refines P2-09/11).
- **Feature-wiring** — chain the siloed features into loops: cook→consume→restock,
  deal/expiry-driven meal planning, recipe/week costing, the self-drafting shop, and
  a proactive daily briefing (P6-07 onward).

Each prompt is self-contained and starts with a READ FIRST step so it survives
code drift. Run them in the order below; do not run two in parallel if they touch
the same tables, routes, or stores.

> **REMOVED FEATURES — do not reintroduce.** The substitute graph (stock-item
> substitutes) and the stock map / spatial layout have been **deleted** as low-value.
> The locations feature is now a **simple hierarchical tree** of storage locations
> (a settings-style page), nothing spatial. No prompt below may depend on a
> substitute graph, a stock map, or location routing. If you find lingering
> references to those, treat them as dead code to remove, not capabilities to build on.

---

## Recommended Order

1. **P6-02** — Barcode → QR cleanup (do this first; it *removes* code, shrinking
   surface area the later prompts would otherwise have to reason about).
2. **P6-01** — Purchase reconciliation via the Dora list.
3. **P6-03** — Real price intelligence.
4. **P6-04** — Proactivity: suggestion inbox + deal→list matching + run-out prediction.
5. **P6-05** — Household: shared lists with attribution + realtime.
6. **P6-06** — In-store one-handed shopping mode.

**Feature-wiring tier** (chain the silos — run after the loops above exist):

7. **P6-07** — Cook → consume → restock loop. *(Do first in this tier — it's the
   consumption signal the rest sharpen against.)*
8. **P6-08** — Opportunistic meal suggestions (cook the deals / cook the expiring /
   cook with what I have).
9. **P6-09** — Recipe & weekly-plan costing + budget defense.
10. **P6-10** — The self-drafting weekly shop.
11. **P6-11** — Location-aware grouping (put-away + expiry, via the location tree).
12. **P6-12** — Proactive daily briefing + alerts-as-launchpads.
13. **P6-13** — Confidence-aware suggestions + decision-driven stocktake.

## Cross-Cutting Rules (apply to every prompt)

- **Preview → approve → commit.** No silent writes. Every automatic change is
  previewed, undoable, and announced via the existing notify/undo primitives.
- **Every insight leads to one action.** If Dora says something will run out, cost
  more, or is a fake markdown, give a one-tap next step.
- **Explainable.** The user can always see *why* Dora suggested/ranked/flagged
  something.
- **Do not invent facts.** Use real app data and existing tool calls only.
- **Local-first / opt-in.** Anything external (email parsing, OCR) is opt-in and
  documented. Features default off where they add visible UI most users won't use.
- **Read CHANGELOG.md after each prompt** and adjust the next if code drifted.

---

# P6-02 — Barcode cleanup: QR-only, opt-in, off by default

> Do this first. It deletes the product-barcode subsystem and gates the surviving
> QR feature behind a setting. Smaller surface for everything after it.

```
Trim DiscountDora's barcode feature down to Dora's own per-item QR codes, remove
the real-world product-barcode subsystem entirely, and make the surviving QR
feature an opt-in setting that defaults OFF.

CONTEXT / DECISION:
There are two unrelated "barcode" concepts in the codebase:
  (1) Dora's own QR per stock item — payload "dora://stock-item/<uuid>", generated
      from the item id, printable as label sheets, scannable to jump to the item.
  (2) Real-world packaging barcodes (EAN/UPC) — a ProductBarcode table mapping an
      EAN to a merchant Product, plus a StockItem.barcode column for registering an
      arbitrary real-world code against an item.
Concept (2) only resolves if the EAN→product map is seeded, and it is not — rows
only arrive via a manual register endpoint, so scans mostly return "unknown". We
are REMOVING concept (2) wholesale and KEEPING concept (1), but gating it behind an
off-by-default setting because most users won't print labels.

READ FIRST:
- dora_api/features/data/barcodes.py (all routes: /qr, /qr/sheet, /barcode POST+DELETE,
  /barcodes/lookup, /barcodes/register-against-product).
- dora_api/domain/entities/product_barcode.py and stock_item.py (the `barcode` field
  + Fields.BARCODE).
- dora_api/persistence/migrations/versions/d7f4a2c98e15_20260526_barcodes.py.
- web_app/src/components/ScanOverlay.vue, web_app/src/pages/data/BarcodesQR.vue,
  web_app/src/services/api/barcodeApiService.ts, and every mount/entry point
  (MainLayout.vue scan button, StockOverview.vue, StockItemDetailPage.vue, the
  command-palette 'barcode' tag).
- dora_api/features/app_settings/{get_app_settings.py,update_app_settings.py} and
  web_app/src/pages/settings/PreferencesSettings.vue for how feature settings are
  shaped and surfaced.
- CHANGELOG.md.

REMOVE (concept 2 — real-world barcodes):
- ProductBarcode entity and its table. Add a migration that DROPS the table.
- StockItem.barcode column + Fields.BARCODE. Add the column drop to the same
  migration. (The QR is derived from stock_item.id; no stored barcode is needed.)
- Routes: POST/DELETE /api/stock-items/<id>/barcode, and
  POST /api/barcodes/register-against-product. Delete them.
- The barcodeApiService methods that call those routes.

SIMPLIFY:
- /api/barcodes/lookup now has exactly one job: parse "dora://stock-item/<uuid>"
  and return {kind:"stock_item", id} or {kind:"unknown"}. Drop the StockItem.barcode
  and ProductBarcode branches. PREFERRED: move the dora:// parse into ScanOverlay's
  decode handler client-side and delete the lookup endpoint entirely — only do this
  if no other caller depends on it.
- ScanOverlay must IGNORE anything that isn't a dora:// code: on a non-Dora decode,
  flashBad() + a quiet "Not a Dora QR code" banner. No server round-trip.

KEEP (concept 1 — Dora QR):
- GET /api/stock-items/<id>/qr (PNG) and GET /api/stock-items/qr/sheet (print sheet).
- ScanOverlay.vue and the scan→navigate flow.

RENAME FOR HONESTY (no more "barcode"):
- ScanOverlay status text "Point at a barcode or QR" → "Point at a Dora QR code".
- The manual-entry box label, the BarcodesQR page title/route, button labels, and the
  command-palette tag → "QR" / "QR labels". Grep for user-facing "barcode" strings.

FEATURE FLAG (default OFF):
- Add a boolean app setting `qr_labels_enabled` (default false) via app_settings
  get/update, surfaced in PreferencesSettings.vue under a "QR labels" toggle with a
  one-line explainer ("Print scannable labels for containers, baskets, and shelves").
- Gate behind it: the scan button in MainLayout, the per-item QR + print actions on
  StockOverview/StockItemDetailPage, the BarcodesQR data page route, and the
  command-palette entry. When off, none of these render and the routes 404/redirect.

DONE WHEN:
- ProductBarcode table and StockItem.barcode column are gone; migration applies clean
  up and down on a seeded DB.
- No route, service method, or UI string references product/real-world barcodes.
- With qr_labels_enabled=false (default), there is zero barcode/QR UI anywhere.
- With it on: print a label sheet, scan a printed QR, land on the item; scanning a
  random product barcode shows "Not a Dora QR code" and does nothing.
- CHANGELOG.md updated; no dead imports; lint + typecheck + pytest green.
```

---

# P6-01 — Purchase reconciliation via the Dora list (list = source of truth)

> Refines P2-01/02. The Dora shopping list — ticked in shop mode — IS the receipt.
> Receipt OCR is explicitly demoted to an optional last-resort path.

```
Close the purchase loop in DiscountDora WITHOUT relying on receipt OCR. The
shopping list the user already shops from is the primary source of truth: ticking
items in shop mode tells Dora what was bought, and Dora already knows the scraped
price for linked products. Reconciliation should be the natural byproduct of
finishing a shop, not a separate scanning chore.

READ FIRST:
- web_app/src/pages/ShoppingListShopMode.vue and ShoppingListDetail.vue — the
  tick + finish-shopping flow.
- dora_api/features/shopping_lists/* — especially the review/complete endpoint
  (POST /api/shopping-lists/<id>/review/complete) that already marks ticked items
  Well-Stocked and bumps timestamps.
- dora_api/domain/entities/{stock_item.py,product.py,product_offer.py,
  product_historic_offer.py} and preferred_product_id linkage.
- dora_api/features/price_history/* and dora_api/features/budget/* (budget_status).
- dora_api/features/assistant/tools.py (purchase_price_stats, compare_prices) for
  the existing price-history shape — reuse it, don't reinvent.
- CHANGELOG.md.

PRIMARY PATH — "Finish shop" reconciliation:
1. On finishing a shop (extend the existing review/complete flow), build a
   PurchaseEvent per ticked line:
   - stock_item_id (if the line is linked), product_id (preferred/linked product if
     any), name snapshot, quantity, store, purchased_on.
   - paid_price: default to the current scraped offer price for the linked product;
     if no linked product, leave null. The user can edit inline.
2. Present a single preview screen: "You bought N items at <store> — ~$X.XX".
   Each row: name, qty stepper, price (editable, pre-filled from scraped offer),
   and a "didn't buy" toggle. Untoggled rows commit; "didn't buy" rows are skipped
   AND recorded as skipped (signal for future suggestions).
3. On confirm: write PurchaseEvents, append to price history (actual paid price,
   tagged source="list"), mark items Well-Stocked (existing behaviour), update
   budget spend with the REAL total, and emit one undoable notification.

DATA MODEL:
- purchase_events: id, user_id, household_id (nullable now, used by P6-05),
  stock_item_id (nullable), product_id (nullable), name, quantity, paid_price
  (nullable), store, purchased_on, source ("list" | "email" | "manual" | "ocr"),
  created_at.
- Actual-price history: reuse/extend the existing price-history store so paid_price
  feeds purchase_price_stats and compare_prices. Distinguish scraped vs paid via a
  source tag; do not overwrite scraped offers.

SECONDARY PATH (opt-in) — online-order email import:
- Add a manual "paste order confirmation" import: user pastes the HTML/text of a
  Coles/Woolworths online-order confirmation email; parse structured line items
  (name, qty, price) into the same PurchaseEvent preview screen above.
- Keep the parser provider-shaped (one parser per merchant) so more can be added.
- This is structured data, far more reliable than OCR. Gate behind an opt-in.

LAST-RESORT PATH (optional, behind a setting, default off) — receipt photo OCR:
- Only if cheap to add: a "snap receipt" that runs OCR and produces LOW-CONFIDENCE
  suggested rows into the SAME preview screen. Never a silent write — every OCR row
  is a pre-checked suggestion the user confirms. If OCR is out of scope, stub the
  entry point and note it; do not block the prompt on it.

EXPLAINABILITY:
- Each reconciled price shows its source ("from your list / Woolworths price",
  "from order email", "you entered"). purchase_price_stats should expose paid vs
  scraped so later features can say "you usually pay $X".

DONE WHEN:
- Finishing a shop from a Dora list produces a preview, and confirming it writes
  PurchaseEvents, real price history, real budget spend, and marks items stocked —
  all in one undoable action, zero OCR involved.
- "Didn't buy" lines are recorded as skipped, not just ignored.
- Pasting a sample Coles/Woolies order email yields a correct preview.
- purchase_price_stats returns actual paid prices distinct from scraped offers.
- pytest covers: list reconciliation happy path, skipped-line recording, email parse
  of one fixture per merchant. Lint + typecheck green. CHANGELOG.md updated.
```

---

# P6-03 — Real price intelligence (deal quality, not `now < was`)

```
Make DiscountDora's discount tracking live up to its name. Today "on deal" is just
price_now < price_was (see dora_api/features/assistant/tools.py find_deals, ~line
1432). You already store historic_offers per product — use that history to answer
the question users actually care about: "is this special actually a good price, or
a fake markdown?"

READ FIRST:
- dora_api/domain/entities/{product.py,product_offer.py,product_historic_offer.py}
  — current_offer + append-only historic_offers.
- merchant_api/features/get_product_offers.py and the provider classes under
  merchant_api/infrastructure/merchant_data_providers/* — how/when offers refresh.
- dora_api/features/price_history/* and dora_api/features/assistant/tools.py
  (find_deals, compare_prices, purchase_price_stats).
- dora_api/features/alerts/get_alerts.py — the alert shape to extend.
- After P6-01 lands: paid_price history (real prices beat scraped was-prices).
- CHANGELOG.md.

DEAL-QUALITY SCORING (pure function over a product's offer history):
- Compute, per product, over a configurable window (default 90 days):
  - lowest_price, highest_price, median_price, current_price.
  - is_lowest_in_window (current <= lowest seen).
  - percentile of current price vs history (e.g. "cheaper than 95% of the last 90d").
  - fake_markdown flag: current_offer claims a saving (now < was) BUT current >=
    median of recent actual selling prices — i.e. the "was" price is inflated and the
    "deal" is not actually cheap.
  - deal_score: a single 0–100 (or Poor/Fair/Good/Great) derived from percentile +
    is_lowest_in_window, NOT from the merchant's own claimed saving.
- Prefer the user's real paid_price (P6-01) over scraped was-price when judging
  "good price for you" if available.

SURFACE IT:
- Extend find_deals (assistant tool) and the deals/product-search UI to show
  deal_score and a one-line reason ("Lowest price in 90 days", "Cheaper than usual",
  "Markdown looks inflated — you've paid less recently"). Never just a % off badge.
- A price-history view per product (extend PriceHistoryPage.vue) plotting the offer
  history with the current price marked against the window's low/median.

PRICE-DROP ALERTS:
- Add an alert type "good_deal" in get_alerts.py: fires when a product linked to a
  stock item the user buys (preferred_product_id or in the m2m) hits a Good/Great
  deal_score. Severity scales with how good. Each alert carries a one-tap "add to
  list" action (wire to the shopping-list add already used elsewhere).
- Respect a per-user threshold setting (only alert at "Great", or at "Good+").
- Throttle: don't re-alert the same product+score band within N days.

DONE WHEN:
- A deal_score + reason is computable for any product with >= a few historic offers,
  and degrades gracefully (insufficient-history state) for new products.
- fake_markdown correctly flags a product whose "was" price is above its own recent
  median.
- find_deals and the deals UI show score + plain-English reason, not raw % off.
- A "good_deal" alert appears for a tracked item that hits the threshold, with a
  working one-tap add-to-list, and does not spam on every refresh.
- pytest covers the scoring function (lowest/median/percentile/fake-markdown edge
  cases) with fixture histories. Lint + typecheck green. CHANGELOG.md updated.
```

---

# P6-04 — Proactivity: suggestion inbox + deal→list matching + run-out prediction

> Refines P2-03/04/05. Turns Dora from a reactive ledger into something that tells
> you things you didn't ask. Builds on the existing suggestions feature + list_suggestions tool.

```
Make DiscountDora proactive. There is already a suggestions feature
(dora_api/features/suggestions) and an assistant tool list_suggestions returning
use_soon / over_budget / likely_due / frequent_waster. Promote this into a
first-class, actionable Suggestion Inbox, add deal→list matching, and add run-out
prediction fed by purchase history.

READ FIRST:
- dora_api/features/suggestions/* and assistant tools list_suggestions, find_deals,
  expiry_rescue, budget_status, whats_expiring (tools.py).
- dora_api/features/alerts/get_alerts.py — for severity/throttle patterns and to
  avoid duplicating signals already raised as alerts.
- After P6-01: purchase_events (cadence) and paid_price history.
- After P6-03: deal_score and good_deal alerts.
- web_app: DashboardPage.vue, the alerts UI, and the shopping-list add flow.
- CHANGELOG.md.

A) SUGGESTION INBOX (preview → approve → commit):
- A single inbox surface (component + a section on DashboardPage) listing typed
  suggestions, each with: title, plain-English reason, and a primary one-tap action
  + dismiss. Types: run_out_soon, good_deal_for_you, expiring_rescue,
  over_budget, frequent_waster, restock_due.
- Every suggestion is explainable (show the data behind it) and dismissible;
  dismissals are remembered and feed a "don't suggest this again" signal.
- Accepting performs the action through existing endpoints (add to list, plan meal,
  mark opened, push expiry) and emits an undoable notification.

B) DEAL→LIST MATCHING (the headline feature):
- For each product on a Good/Great deal (P6-03) that maps to a stock item the user
  buys (preferred_product_id or m2m, weighted by purchase_events frequency), create
  a good_deal_for_you suggestion: "The salmon you buy is half-price at Woolies —
  add to list?" with a one-tap add.
- Prioritise items the user is also predicted to run out of soon (combine with C).

C) RUN-OUT PREDICTION:
- From purchase_events cadence (P6-01) estimate a typical repurchase interval per
  stock item (days between purchases, robust to outliers — use median interval).
- predicted_runout = last_purchase + interval, adjusted by current stock_level flag
  (Out/Low accelerates it). Produce a confidence (low until enough history).
- Emit restock_due / run_out_soon suggestions ahead of the predicted date. Never
  present a prediction without its basis ("you usually rebuy ~every 12 days; last
  bought 11 days ago").

NOISE CONTROL:
- A single throttle/budget on how many suggestions surface per day (config, default
  small). Rank by value (great deal on a soon-to-run-out essential > minor deal).
- Do not duplicate something already shown as an alert; cross-reference get_alerts.

DONE WHEN:
- DashboardPage shows an actionable Suggestion Inbox; each item has a reason + one-tap
  action + dismiss, and dismissals persist.
- A tracked item that goes on a Great deal produces a "deal for you" suggestion with a
  working add-to-list.
- Run-out prediction returns a date + confidence + human reason for an item with
  purchase history, and stays quiet (low confidence) without it.
- Daily suggestion volume is capped and ranked; no duplication of existing alerts.
- pytest covers cadence/interval math, deal-match selection, and dedup-vs-alerts.
  Lint + typecheck green. CHANGELOG.md updated.
```

---

# P6-05 — Household: shared lists with attribution + realtime

> Refines P2-09 / A2. The README pitches "so everyone can help grab the milk on
> sale" — but only instance-level user admin exists, no household scoping.

```
Add real household sharing to DiscountDora so members of one household share stock,
lists, and suggestions, with attribution and live updates. Today there is only
instance-level user admin — no household scoping or invites.

READ FIRST:
- dora_api/features/auth/* and dora_api/features/users/* — current user model + admin.
- dora_api/features/{stock_items,shopping_lists,suggestions,budget}/* — what needs a
  household scope.
- dora_api/features/audit/* — attribution/audit patterns to reuse.
- web_app auth/session stores and the shopping-list pages.
- WelcomeWizard (the A2 comment about households) and onboarding.
- CHANGELOG.md.

DATA MODEL + SCOPING:
- households: id, name, created_at. household_members: household_id, user_id, role
  ("owner" | "member"), joined_at. household_invites: token, household_id, email
  (optional), expires_at, accepted_by.
- Add household_id to the entities that are shared: stock_items, shopping_lists (and
  lines), suggestions, budget, purchase_events (from P6-01). Backfill existing rows
  into a default household for the current install.
- Every read/write is scoped to the caller's household. A user belongs to exactly one
  household for now (keep it simple; multi-household is out of scope).
- Invites: owner generates an invite link/token; accepting joins the household. Basic
  roles only (owner can remove members + delete the household).

ATTRIBUTION:
- Stamp who did what on shared mutations (ticked a line, added an item, changed a
  level) using the existing audit infrastructure. Surface lightly in the UI
  ("Sam ticked Milk") on shopping lists and recent activity.

REALTIME:
- Live-sync shared shopping lists and stock-level changes so two members see each
  other's ticks/edits without manual refresh. Prefer the simplest mechanism that fits
  the stack (SSE or WebSocket) — one channel per household. Include last-write-wins
  conflict handling with a visible "updated by Sam" cue; no lost ticks.

DONE WHEN:
- An owner can create a household, invite a second user, and that user joins and sees
  the same stock + lists.
- All shared reads/writes are household-scoped; a user in household A cannot see
  household B's data (covered by a test).
- Existing single-user data is migrated into a default household with the user as owner.
- Two sessions on one shared list see each other's ticks live, with attribution and no
  lost updates.
- pytest covers scoping isolation, invite accept, and attribution stamping. Lint +
  typecheck green. CHANGELOG.md updated.
```

---

# P6-06 — In-store one-handed shopping mode

> Refines P2-11. ShoppingListShopMode.vue exists, but the real usage context is
> one-handed, in a noisy aisle, on a phone. Optimise for that.

```
Upgrade DiscountDora's in-store shopping experience for one-handed, phone-in-aisle
use. A shop mode already exists (web_app/src/pages/ShoppingListShopMode.vue) — make
it genuinely usable while pushing a trolley.

READ FIRST:
- web_app/src/pages/ShoppingListShopMode.vue and ShoppingListDetail.vue.
- The finish-shopping / review-complete flow (and P6-01 reconciliation it feeds into).
- web_app PWA setup (M1) and any existing voice/cook-mode voice code (Part 1 cook mode).
- The QR scan flow (P6-02 ScanOverlay) — reuse it, gated by qr_labels_enabled.
- web_app design tokens / theme and reduced-motion handling.
- CHANGELOG.md.

ONE-HANDED UX:
- Large tap targets, thumb-reachable primary actions, a sticky bottom bar. Ticking an
  item is a single big tap with clear haptic/visual feedback; undo is one tap.
- Items group by store aisle/section if that data exists; otherwise by stock location
  or category. Ticked items collapse to the bottom; outstanding stay on top.
- A running total using current scraped prices (and deal_score badges from P6-03) so
  the user sees spend-so-far vs budget (budget_status) live.
- Keep the screen awake (Wake Lock API) while shop mode is active; release on exit.
- Works offline / flaky signal: queue ticks locally and reconcile on reconnect (lean
  on existing offline/PWA infra). No lost ticks in a dead-zone aisle.

HANDS-FREE ADD:
- A voice "add" affordance: "add milk" appends to the active list (reuse existing
  voice infra if present; otherwise the Web Speech API behind a mic button). Confirm
  visually; never silently add.
- If qr_labels_enabled, a scan button to jump to / tick an item by its Dora QR.

FLOW INTO RECONCILIATION:
- "Finish shop" hands the ticked set straight to the P6-01 reconciliation preview —
  no separate step.

DONE WHEN:
- Shop mode is comfortably operable one-handed: big targets, sticky bottom action bar,
  one-tap tick + undo with feedback.
- Live running total + deal badges + budget remaining are visible while shopping.
- Screen stays awake during shop mode and releases on exit.
- Ticks survive going offline mid-shop and sync on reconnect (tested).
- Voice "add <item>" works behind a confirm; QR scan-to-tick works when enabled.
- Finishing flows directly into P6-01 reconciliation.
- pytest/component tests where practical; manual mobile check noted. Lint + typecheck
  green. CHANGELOG.md updated.
```

---

# Tier: Feature-Wiring — chain the silos

> Dora has the ingredients of an intelligent system but most features live in their
> own page. These prompts add the connections that make the whole worth more than the
> parts. None of them depend on the removed substitute graph or stock map.

---

# P6-07 — Cook → consume → restock loop

> The single most valuable missing wire: cooking a recipe currently does NOT touch
> stock. Wiring it closes the consumption half of run-out prediction (P6-04).

```
Make cooking a recipe in DiscountDora update stock, so consumption stops being
invisible. Today recipes know exactly what they use, but finishing a cook does
nothing to stock levels — so run-out prediction only ever sees purchases, never use.

READ FIRST:
- web_app/src/pages/RecipeCookMode.vue and RecipeDetailPage.vue — the cook flow and
  how a recipe's ingredients map to stock items.
- dora_api/features/recipes/* and dora_api/domain/entities for recipe ingredients ↔
  stock_item linkage.
- dora_api/features/stock_items/* and stock_levels — how a level changes; the
  StockLevel sequence (Well-Stocked → Sufficient → Low → Out).
- dora_api/features/assistant/tools.py — update_stock_level, mark_opened (reuse, do
  not reinvent the level-change path).
- stock_item.auto_add_when_low and the primary-list add flow.
- After P6-04: run-out prediction / cadence store — this prompt feeds it.
- CHANGELOG.md.

NOTE ON THE MODEL: stock levels are coarse flags, not quantities. "Consume" therefore
means stepping a level down (e.g. Well-Stocked → Sufficient, or → Low for a main
ingredient), NOT decrementing a count. Keep it flag-based and ALWAYS user-confirmed.

FLOW:
1. On finishing a recipe in cook mode, build a "what did this use" preview from the
   recipe's linked stock items: each row = item, a suggested new level (heuristic:
   primary/large-quantity ingredients drop further than garnish/pinch ones), and a
   stepper to adjust. Include a "didn't use / had elsewhere" skip per row.
2. Preview → approve → commit (cross-cutting rule). On confirm: apply level changes
   via the existing update_stock_level path, mark relevant items opened where it makes
   sense (mark_opened), trigger auto_add_when_low for anything that drops to Low/Out,
   and emit ONE undoable notification ("Updated 6 items, added 2 to your list").
3. Record a consumption_event per consumed item (item, recipe_id, consumed_on) so
   run-out prediction (P6-04) blends consumption cadence with purchase cadence.

DATA MODEL:
- consumption_events: id, user_id, household_id (nullable; set by P6-05),
  stock_item_id, recipe_id (nullable), consumed_on, created_at.

EXPLAINABILITY:
- The preview states why each level was suggested ("main ingredient", "pinch").
- run-out prediction reasons should later be able to cite "you cooked X twice this
  week" alongside purchase cadence.

DONE WHEN:
- Finishing a cook shows a consumption preview; confirming steps levels down,
  auto-adds anything now Low/Out, and writes consumption_events — one undoable action.
- "Didn't use" rows are respected and not consumed.
- Recipes with unlinked ingredients degrade gracefully (only linked items appear).
- run-out prediction (P6-04) demonstrably shifts when an item is cooked vs only bought.
- pytest covers level-step heuristics, auto-add trigger, and consumption_event writes.
  Lint + typecheck green. CHANGELOG.md updated.
```

---

# P6-08 — Opportunistic meal suggestions (cook the deals / the expiring / what you have)

> Reverses the usual "plan → shop" direction. Starts from what's cheap, what's dying,
> and what's already in stock, and proposes meals. Uses code you already have.

```
Add opportunistic meal suggestions to DiscountDora that start from deals, expiry, and
current stock — not from a blank meal plan. These are the emotional hook: "salmon's at
its 90-day low and your spinach expires Thursday — here's a dinner that uses both."

READ FIRST:
- dora_api/features/assistant/tools.py — suggest_recipes (stock-coverage ranked),
  expiry_rescue (expiring items ranked by recipe coverage), find_deals, recipe_detail,
  whats_expiring, plan_meal_for_date, add_recipe_to_list. REUSE these.
- After P6-03: deal_score on products.
- dora_api/features/{recipes,meals,meal_plans}/* and web_app RecipesOverview.vue,
  MealPlansOverview.vue, RecipeCookMode.vue.
- The Suggestion Inbox from P6-04 — these become inbox items, do not build a new surface.
- CHANGELOG.md.

THREE GENERATORS (all feed the P6-04 Suggestion Inbox as typed suggestions):
1. COOK THE EXPIRING — for items expiring within the horizon, surface the best-covered
   recipe (expiry_rescue), as a suggestion "Use the spinach (expires Thu): <recipe>".
2. COOK THE DEALS — for products on a Good/Great deal (P6-03) that you buy, surface a
   saved/strong-coverage recipe using that ingredient: "Mince is at its 90-day low —
   batch-cook <recipe> and freeze?". For staples bought in bulk, suggest a freeze-ahead
   variant (note the freezer location from the location tree).
3. COOK WHAT I HAVE NOW — a one-tap "what can I make tonight with zero shopping": rank
   recipes by current stock coverage (suggest_recipes), break ties toward using
   soonest-to-expire items. No shopping required.

ACTIONS PER SUGGESTION (one tap each, preview → commit, undoable):
- "Plan it" → plan_meal_for_date (today/this week).
- "Add the rest to my list" → add_recipe_to_list for the missing ingredients only.
- "Cook now" → open RecipeCookMode (which then feeds P6-07).

EXPLAINABILITY:
- Every suggestion shows its trigger ("expires in 2 days", "lowest price in 90 days",
  "you have 9 of 10 ingredients").
- Combine signals when they overlap: an on-deal ingredient that's ALSO soon-to-expire
  ranks highest.

DONE WHEN:
- "What can I make tonight?" returns stock-coverage-ranked recipes, expiry-tie-broken,
  needing no shopping.
- An on-deal ingredient you buy yields a "cook the deal" suggestion with plan / add /
  cook-now actions.
- An expiring item yields a "cook the expiring" suggestion likewise.
- Suggestions flow through the P6-04 inbox (no new surface) and are dismissible.
- pytest covers the three generators and the combined-signal ranking. Lint + typecheck
  green. CHANGELOG.md updated.
```

---

# P6-09 — Recipe & weekly-plan costing + budget defense

> Turns the budget feature from a passive tracker into a negotiator. No substitute
> graph — swaps are cheaper *recipes* or cheaper *products for the same item*.

```
Cost DiscountDora recipes and meal-plan weeks from real prices, tie that to the
budget, and offer concrete money-saving swaps. NOTE: the substitute graph is removed —
swaps come from (a) a cheaper recipe in the plan, or (b) a cheaper / on-special
merchant product for the SAME stock item. Never from a stock-item substitute graph.

READ FIRST:
- dora_api/features/assistant/tools.py — compare_prices (current prices across linked
  products for a stock item), purchase_price_stats, budget_status. REUSE.
- dora_api/features/{recipes,meal_plans,budget,price_history}/* and product/offer
  entities; recipe-ingredient ↔ stock-item ↔ product linkage.
- After P6-03: deal_score (to prefer genuinely-good-price products in swaps).
- After P6-01: paid_price history (prefer real prices over scraped where available).
- web_app RecipeDetailPage.vue, MealPlansOverview.vue, the budget UI.
- CHANGELOG.md.

COSTING:
- cost_per_recipe = sum over ingredients of (best available price for the linked
  product × quantity needed), preferring the user's preferred_product, then paid_price,
  then current scraped offer. Show a per-serving cost too.
- cost_per_week = sum of planned recipes in a meal-plan week. Show it on the meal plan.
- Degrade gracefully: ingredients with no linked product are marked "price unknown"
  and excluded from the total with a visible "N items unpriced" note (no fake totals).

BUDGET DEFENSE (the headline):
- Compare cost_per_week to the grocery budget (budget_status). When over, generate
  ranked swap suggestions, each with the exact saving:
  - PRODUCT swap: "Buy the on-special <brand> for the chicken instead of your usual →
    save $X" (uses compare_prices + deal_score for the same stock item).
  - RECIPE swap: "Swap Thursday's <expensive recipe> for <cheaper saved recipe> →
    save $Y" (a different recipe, not an ingredient substitution).
- Each swap is one-tap apply (re-link preferred product, or swap the planned recipe),
  preview → commit, undoable. State the resulting new weekly total.

DONE WHEN:
- A recipe and a meal-plan week show a real cost (and per-serving), with unpriced
  ingredients flagged rather than guessed.
- When a week is over budget, Dora offers ranked product-swap and recipe-swap
  suggestions with concrete dollar savings and one-tap apply.
- Swaps reference only cheaper products-for-the-same-item or alternative recipes — no
  substitute-graph logic anywhere.
- pytest covers costing math, unpriced-ingredient handling, and swap-saving
  calculations. Lint + typecheck green. CHANGELOG.md updated.
```

---

# P6-10 — The self-drafting weekly shop

```
Make DiscountDora pre-draft next week's shopping list so the user edits rather than
writes it. Combine predicted run-outs, template staples, and current deals into a
single preview to approve.

READ FIRST:
- After P6-04: run-out prediction / restock_due signals and the Suggestion Inbox.
- After P6-03: deal_score (to fold in "things you buy that are on special").
- web_app/src/pages/ShoppingListTemplates.vue and dora_api/features/
  shopping_list_templates/* — staples the user already defined.
- dora_api/features/shopping_lists/* — the primary list and the add flow.
- After P6-01: purchase cadence (drives prediction) and reconciliation.
- CHANGELOG.md.

DRAFT COMPOSITION (a preview, never auto-committed):
- PREDICTED RUN-OUTS: items whose predicted_runout falls within the next shop window
  (P6-04), each tagged with its reason ("usually rebuy ~every 12 days").
- TEMPLATE STAPLES: items from the user's chosen template(s) not already well-stocked.
- DEAL OPPORTUNITIES: products you buy that are currently a Good/Great deal (P6-03),
  marked "on special — optional".
- De-duplicate across the three sources; merge into one ranked draft. Each line shows
  why it's there and is individually removable.

DELIVERY:
- A "Draft my weekly shop" action (and an optional weekly nudge via the existing
  alerts/suggestions cadence) that opens the draft preview. Approve → creates/updates
  the primary list. Nothing is added silently.
- Respect dismissals: items the user repeatedly removes from drafts get down-weighted.

DONE WHEN:
- "Draft my weekly shop" produces a single de-duplicated, reason-tagged list combining
  predicted run-outs + template staples + relevant deals.
- Approving creates/updates the primary list; declining writes nothing.
- Repeatedly-removed items are down-weighted in future drafts.
- pytest covers source-merge/de-dup and the down-weighting signal. Lint + typecheck
  green. CHANGELOG.md updated.
```

---

# P6-11 — Location-aware grouping (put-away + expiry) via the location tree

> The locations feature is now a SIMPLE hierarchical tree (no map, no routing). These
> wires use only that tree — grouping, not spatial navigation.

```
Use DiscountDora's location tree to group two flows by where things live: putting a
shop away, and checking what's expiring. NO map, NO routing, NO spatial layout — the
stock map was removed and must not return. Locations are just a hierarchical tree.

READ FIRST:
- dora_api/features/{locations,stock_locations}/* — the current simple tree model.
- stock_item.stock_location and the location tree UI (the simplified settings-style page).
- dora_api/features/alerts/get_alerts.py — expiry/low alerts to group.
- After P6-01: the finish-shop reconciliation preview (put-away hooks in here).
- CHANGELOG.md.

A) PUT-AWAY GROUPING:
- After a shop is reconciled (P6-01), offer an optional "put away" checklist that
  groups the just-bought items by their stock_location tree node ("Freezer: 3 ·
  Pantry: 2 · Fridge: 4"). Tap to tick each group as stowed. Items with no location
  fall into an "Unsorted" group with a quick-assign. This is a checklist, not a route.

B) EXPIRY-BY-LOCATION:
- In the expiry view / alerts, allow grouping expiring & expired items by location node
  ("Back of freezer: 2 expiring") so the user knows where to physically look. Reuse
  get_alerts data; this is a presentation grouping, not a new alert type.

DONE WHEN:
- After reconciling a shop, a location-grouped put-away checklist is available; ticking
  groups them stowed; unlocated items get a quick-assign.
- Expiring/expired items can be grouped by location tree node.
- No code references a stock map, spatial coordinates, or location routing.
- pytest covers grouping (including the no-location/Unsorted case). Lint + typecheck
  green. CHANGELOG.md updated.
```

---

# P6-12 — Proactive daily briefing + alerts-as-launchpads

```
Give DiscountDora a proactive daily briefing that COMPOSES across features instead of
answering one question at a time, and make every alert/suggestion a launchpad into the
feature that resolves it (never a dead-end notification).

READ FIRST:
- dora_api/features/assistant/* and tools.py — whats_expiring, expiry_rescue,
  find_deals, budget_status, suggest_recipes, pantry_health, get_alerts. The briefing
  COMPOSES these; it must not invent facts outside tool/app data.
- After P6-04: the Suggestion Inbox and run-out prediction.
- After P6-08: opportunistic meal suggestions.
- web_app/src/pages/DashboardPage.vue and the alerts UI.
- CHANGELOG.md.

A) DAILY BRIEFING:
- A once-a-day synthesized summary on DashboardPage that blends the highest-value items
  across features into a short human paragraph + a few one-tap actions, e.g.:
  "Two things expire this week — here's a dinner that clears both. The salmon you buy
  is half-price at Woolies. You're $8 under budget if you want to stock up while mince
  is cheap."
- Built by calling the existing tools and ranking outputs by value (great deal on a
  soon-to-run-out essential > minor deal). Cap length; link each clause to its action
  (plan meal / add to list / view deal). Cache per day; refresh on demand.

B) ALERTS-AS-LAUNCHPADS (cross-cutting, retrofit existing alerts):
- Every alert and suggestion carries a primary cross-feature action:
  - expiring → "cook it" (recipe via expiry_rescue) and/or "plan it".
  - low/out essential → "add to list" AND, if the item is currently a deal (P6-03),
    "it's on special — add now".
  - over budget → "see swaps" (P6-09).
  - restock_due → "add to list" / "draft my shop" (P6-10).
  - stocktake overdue → "quick-check" (P6-13).
- No alert should be a dead end; each links forward to the resolving feature.

DONE WHEN:
- DashboardPage shows a daily briefing composed from real tool outputs (no invented
  facts), value-ranked, length-capped, with working one-tap actions per clause.
- Every alert type exposes at least one cross-feature action that lands the user in the
  resolving flow.
- pytest covers briefing composition (given fixture tool outputs → expected ranked
  clauses) and alert-action wiring. Lint + typecheck green. CHANGELOG.md updated.
```

---

# P6-13 — Confidence-aware suggestions + decision-driven stocktake

```
Make DiscountDora honest about how stale its stock data is, and make stocktake target
the checks that actually matter. Use last_checked_at to attach confidence to
predictions/suggestions, and reorder the stocktake queue by decision impact.

READ FIRST:
- dora_api/features/stocktake/* — the queue (overdue ordering, last_checked_at) and
  check/bulk-check endpoints.
- stock_item.last_checked_at, stock_level_last_updated, days_until_stocktake_alert.
- After P6-04: run-out prediction + Suggestion Inbox.
- After P6-08/P6-09: meal suggestions and weekly-plan costing (the "decisions" that
  depend on stock being correct).
- dora_api/features/alerts/get_alerts.py (stocktake-overdue alert).
- CHANGELOG.md.

A) CONFIDENCE ON PREDICTIONS:
- Attach a confidence/staleness signal to run-out predictions and stock-based
  suggestions derived from last_checked_at (and how long since the level changed).
- Surface it honestly: "I think you're low on rice, but you haven't checked in 40 days
  — confirm?" with a one-tap quick-check that bumps last_checked_at.

B) DECISION-DRIVEN STOCKTAKE QUEUE:
- Re-rank the stocktake queue so items blocking a real decision float to the top:
  ingredients of a planned/suggested recipe, items about to be bought on a deal, or
  items feeding an at-risk budget decision — ahead of merely time-overdue items.
- "Verify you have flour before I suggest this recipe / before you buy it on sale" —
  expose these as inline quick-checks at the decision point, not only in the stocktake
  page.

DONE WHEN:
- Predictions/suggestions display a confidence/staleness cue based on last_checked_at,
  with a one-tap quick-check that updates it.
- The stocktake queue ranks decision-blocking items above purely time-overdue ones.
- Inline quick-checks appear at decision points (recipe suggest, deal add) and bump
  last_checked_at without leaving the flow.
- pytest covers confidence derivation and the decision-driven ranking. Lint + typecheck
  green. CHANGELOG.md updated.
```

---

## Notes & sequencing reminders

- **P6-02 before everything** — removing the product-barcode code first means later
  prompts never have to reason about it.
- **P6-01 before P6-03/P6-04** — real paid prices and purchase cadence are what make
  price intelligence and run-out prediction *real* rather than estimated.
- **P6-05 (household) adds `household_id`** to several tables P6-01/P6-04 also touch.
  If you run P6-05 after them, include those tables in its scoping migration; if
  before, the earlier prompts should add `household_id` as they create their tables.
  Either way — do not run P6-05 in parallel with P6-01/P6-04.
- Keep each feature **explainable and undoable**; that's the throughline that keeps
  Dora trustworthy as it gets smarter.

### Feature-wiring tier (P6-07 → P6-13)

- **P6-07 first.** Cook→consume is the consumption signal P6-04 prediction, P6-08
  meal suggestions, P6-10 self-drafting shop, and P6-13 confidence all sharpen against.
- **P6-08 / P6-09 depend on P6-03** (deal_score) and ideally **P6-01** (paid prices),
  and both feed the **P6-04 Suggestion Inbox** — build the inbox before them so they
  have a home rather than inventing a new surface.
- **P6-10 depends on P6-04** (prediction) + **P6-03** (deals) + templates.
- **P6-12 (briefing) depends on most of the above** — it composes their outputs; build
  it late.
- **No prompt in this tier may depend on the removed substitute graph or stock map.**
  P6-09 swaps are cheaper-product / cheaper-recipe only; P6-11 uses the location tree
  for grouping, never routing. If a prompt drifts toward those, stop and re-scope.
- consumption_events (P6-07) and household_id (P6-05) touch shared tables — don't run
  P6-05 in parallel with P6-07; sequence them and fold household_id into the
  consumption_events migration if P6-05 lands first.
