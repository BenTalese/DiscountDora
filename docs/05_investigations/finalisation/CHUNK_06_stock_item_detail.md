# Chunk 06 — Stock-Item Detail

**Analysed:** 2026-10-23 · **Analyst session:** finalisation overnight run (solo, no subagents)
**Scope (from PLAN §4):** the stock-item detail page and everything it hosts — Overview inline editors, Dora's three signal cards (belief · planned meals · buy verdict), preferred buys, "Your prices" + the full-history sheet, Products / Recipes / Substitutes / Scanning / Lists / History tabs, delete — plus the backend group behind them (`get_stock_item_detail`, `get_buy_verdict`, `your_prices`, substitutes, preferred buys, price observations, recently-priced, stock-item price history, link/unlink product, planned demand).
**Boundaries:** the overview row + stocktake runner (Chunk 5) own `StockItemRow`, `useStockItemActions.pushExpiry` (05-R2) and the row's waste logging; the belief *engine* (`pantry_belief.py`) is Chunk 7; product pages, `/price-history`, the camera scanner and `PriceEntry`'s form shape (FU-704) are Chunk 10; nutrition *matching* settings are Chunk 13; `update_stock_item.py` is read here only for the expiry classifier and the rename rule (05-R30 owns uniqueness).

## 0. Reading list + files walked

**Planning docs consulted:** `FINALISATION_PLAN.md` §3–§4, §8 · `_CHUNK_TEMPLATE.md` · `Feedback _ Fixes - as of [06-Jun-2026].md` § STOCK ITEM DETAIL (L110–141) · `PROPOSAL_BUY_VERDICT_ORACLE.md` (via module docstring) · `IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md` D-10/D-11/D-12 (via comments) · `PROPOSAL_PRODUCTS_AS_OVERLAY.md` §3.1–3.3 (via comments) · `ENGINEERING_STANDARDS.md` · `DESIGN_STYLE_GUIDE.md` · `HelpPage.vue` Stock group · `app_knowledge.py` · open FUs on this surface: FU-706, 707, 704, 705, 644, 876, 910, 851, 849, 711, 712, 685, 684, 683, 923, 575, 753, 671, 847, 834, 764, 654, 682.

**Files walked (every file opened, with line count):**

| File | Lines | Role |
|---|---|---|
| `dora_api/features/stock_items/get_stock_item_detail.py` | 1002 | the detail DTO + 9 history/price/nutrition feeds in one `handle()` |
| `dora_api/features/stock_items/get_buy_verdict.py` | 925 | P8-05/06 oracle — pure composer + bulk gather + endpoint |
| `dora_api/features/stock_items/your_prices.py` | 774 | baseline median / display denominator / price series |
| `dora_api/features/stock_items/add_substitute.py` | 142 | POST pair + metadata |
| `dora_api/features/stock_items/remove_substitute.py` | 56 | DELETE pair |
| `dora_api/features/stock_items/update_substitute.py` | 130 | PATCH pair metadata |
| `dora_api/features/stock_items/preferred_buys.py` | 131 | add / rename / delete |
| `dora_api/features/stock_items/price_observations.py` | 133 | add / delete observation |
| `dora_api/features/stock_items/recently_priced.py` | 88 | log-price picker shortlist |
| `dora_api/features/stock_items/stock_item_price_history.py` | 99 | unioned per-unit series endpoint |
| `dora_api/features/stock_items/link_product_to_stock_item.py` | 127 | POST link + orphan-line fold |
| `dora_api/features/stock_items/unlink_product_from_stock_item.py` | 108 | DELETE link + selected-product clears |
| `dora_api/features/stock_items/get_planned_demand.py` | 49 | overlay endpoint |
| `dora_api/features/stock_items/planned_demand.py` | 215 | demand signal + urgency grading |
| `dora_api/features/stock_items/_level_access.py` | 62 | R-032-safe level resolver |
| `dora_api/features/stock_items/update_stock_item.py` | L200–260 | expiry transition emit, rename rule |
| `dora_api/domain/cadence_math.py`, `features/shopping_lists/_line_price.py` (head) | — | chokepoints the verdict reads |
| `web_app/src/pages/StockItemDetailPage.vue` | 2814 | the page (routed + embedded peek) |
| `web_app/src/components/stock/BuyVerdictCard.vue` | 369 | detail-page verdict card |
| `web_app/src/components/stock/BuyVerdictBadge.vue` | 205 | row/line chip + popover |
| `web_app/src/components/stock/BuyVerdictBadgeInline.vue` | 39 | self-fetching badge |
| `web_app/src/components/stock/buyVerdictDisplay.ts` | 32 | shared axis icon + detail line |
| `web_app/src/components/stock/PlannedDemandCard.vue` | 141 | demand card |
| `web_app/src/components/stock/PantryBeliefCard.vue` | ~130 | belief card |
| `web_app/src/components/stock/SubstituteMetadataDialog.vue` | 239 | note + ratio dialog |
| `web_app/src/components/stock/NutritionFactsList.vue` | 91 | per-100g table |
| `web_app/src/components/stock/NutritionFoodPicker.vue` | 294 | search-and-confirm picker |
| `web_app/src/components/dora/YourPricesWidget.vue` | 311 | prices card |
| `web_app/src/components/dora/PriceHistoryBottomSheet.vue` | 146 | full-history sheet |
| `web_app/src/components/PriceHistoryChart.vue` | 566 | SVG chart (FU-833) |
| `web_app/src/composables/useBuyVerdict.ts` | 224 | per-item cache |
| `web_app/src/composables/useBuyVerdictActions.ts` | 114 | mark-stocked / remove-from-lists |
| `web_app/src/composables/useBuyVerdictEnabled.ts` | 49 | money × user gate |
| `web_app/src/composables/usePlannedDemand.ts` | 58 | overlay cache |
| `web_app/src/composables/useLogWaste.ts` | 98 | reason-only waste log + undo |
| `web_app/src/composables/useLogPrice.ts` | 32 | sheet opener |
| `web_app/src/composables/openToggle.ts` | 71 | pure open-toggle patch builder |
| `web_app/src/composables/useStockItemActions.ts` | 260 | cross-feature actions |
| `web_app/src/helpers/expiryIndicator.ts` | 88 | expiry glyph |
| `web_app/src/helpers/substituteRatio.ts`, `wasteReasons.ts`, `relativeTime.ts` (heads) | — | shared formatters |
| `web_app/src/models/stockItemDetail.ts` | 304 | DTO types |
| `web_app/src/models/stockItem.ts` | 42 | list DTO type |
| `web_app/src/services/api/buyVerdictApiService.ts` | 95 | verdict client |
| `web_app/src/services/api/priceHistoryApiService.ts` | 114 | history types |
| `web_app/src/services/api/stockItemApiService.ts` (method list, `UpdateStockItemCommand`) | — | client |
| `web_app/src/stores/stockItemStore.ts` L117–175 | — | update/delete paths |
| `web_app/src/pages/HelpPage.vue` L353–412 | — | existing Stock help entries |
| `dora_api/features/assistant/app_knowledge.py` L14–26 | — | DoraBot corpus |
| tests: `test_substitutes_router.py`, `test_substitute_metadata.py`, `test_preferred_buys.py`, `test_price_observations.py`, `test_your_prices.py`, `test_stock_item_price_history.py`, `test_recently_priced.py`, `test_planned_demand_endpoint.py`, `test_buy_verdict.py`, `test_planned_demand.py`, `test_stock_item_history_feeds.py` / `test_stock_item_router.py` / `test_patch_semantics.py` / `test_delete_integrity.py` (names) · vitest `openToggle.spec.ts`, `useBuyVerdict.spec.ts`, `buyVerdictPrime.spec.ts`, `useBuyVerdictEnabled.spec.ts`, `relativeTime.spec.ts`, `useStockItemActionsPushExpiry.spec.ts` | — | coverage inventory |

## A. Full Systems Test — Stock-Item Detail

### A1. Preconditions
- Dense persona (seeded showcase): an item with level history, ≥3 finished-list purchases with prices, a waste event, ≥1 linked recipe, ≥1 substitute with a ratio, ≥1 linked product with a current offer, a planned meal in the next 14 days using it.
- Flags: `products` on, `scanning` on, money on, nutrition **complex**, stocktake on (then each flipped off in A3).
- A second draft shopping list exists (so the add-to-list picker fires).

### A2. Golden path
1. Stock → click an item (desktop) → **peek opens in the splitter**; on a phone the same click routes to `/stock/:id` → header shows name (ellipsised, never wraps), Delete at top right (icon-only below `sm`).
2. Overview: three cards at the top in order *Dora thinks* → *N planned meals need this* (only when money off) → *Should I buy?* → each collapsed to one line, caret in the same column; expanding the verdict shows data confidence, reasons with the plan reason first, and the "Based on N price samples (last 12 months)" footer.
3. Edit **Name**, blur → saves; rename to its *own* name → no "already exists" error; rename to another item's name → 422 toast.
4. Change **Level** from the picker → chip repaints, "Updated just now", the belief card refreshes, the verdict refetches, the planned-meals grade moves (Low→Out flips watch→blocking).
5. Location (path-labelled, searchable), Stock group, Usual store (store logos) → each saves on change; clearing via the ✕ saves `clear_*` and sticks after reload.
6. Nutrition row (complex): a *Suggested* candidate shows dashed with "matched on the name, not saved yet" → **Use this** links it → kcal + source line → **Details** opens the per-100g table with *Vitamins & minerals (N)* behind a disclosure → ✕ unlinks → **Not a food** on the suggestion → row reads *Ignored*; searching and linking from Ignored un-ignores.
7. Expiry: glyph + date open the picker; +1d/+7d/+14d shift; ✕ clears → History tab gains *Set / Pushed +7 days / Cleared expiry* entries.
8. **Opened** toggle on → *MarkOpenExpiryDialog* → Cancel/Escape → toggle snaps back, **nothing written**; Skip → opened, expiry unchanged; Update → opened + new expiry. Toggle off → no prompt.
9. Essential / Stocktake toggles save immediately; Notes saves on blur; navigating away with unsaved notes → unsaved-changes guard.
10. Preferred buys (products **off**): add → appears A–Z; rename inline (Enter/blur/Esc); remove.
11. **Your prices**: *Log a price* → PriceEntry prefilled "from your last receipt · <date>" → submit → the recent list gains a row with "4 × 125 g" when a pack count was given; the *Usually $X / 100g* figure appears from the 3rd observation; *Paying more than usual* / *About average* pill; *Current shelf prices* sidecar when a linked product has a same-dimension offer; **Full history** → bottom sheet: your observations solid, store offers dashed, baseline dotted, legend, "above usual" chip.
12. Products tab: cheapest card outlined + *Cheapest* chip, sparkline per product, cart button per product (state-aware), external link, Unlink → card disappears and any list/template/recipe selection of that product is cleared server-side; *Link another* → opens the Product Search companion (or Features setup when unset).
13. Recipes tab: cards reflow by column count; open → `/cookbook/:id`; Cook → `/cookbook/:id/cook`; favourite toggles; *Add missing* / *Add all* → primary draft (or the list picker when none is primary); *Filter stock by ingredients* → `/stock?recipe=`.
14. Substitutes tab: *Add substitute* → picker (excludes self + already-linked, 30 cap) → row shows level dot, name, ratio caption, note; ✎ → note + ratio dialog (ratio toggled on/off, units narrowed to the install's system) → Save; viewing the pair from the **other** item shows the ratio inverted; ✂ unlinks; clicking a row in the peek swaps the peek id, routed mode navigates.
15. Scanning tab (flag on): QR renders (lazy, per item, re-fetched on peek swap); Print opens the sheet; *Add barcode* → EAN appears as a direct row; a code from a linked product shows "(from product: …)" and is not removable here.
16. Lists tab: each open list the item sits on, ★ on the quick-add target; *Add to a list* when none.
17. History tab: merged timeline newest-first — level changes read *Restocked →* / *Dropped to*, waste, list adds, *Bought · list · $ · at store*, *Used in <recipe> · N meals*, expiry trail, synthetic *Opened* and *Checked (still correct)*; footer "N older events not shown" when any feed exceeded 50.
18. Delete → confirm → if an ingredient of any recipe: *Still used by recipes* dialog listing them; otherwise the item is gone, the peek closes / route returns to `/stock`, no unsaved-changes prompt.

### A3. Edge cases
- `?section=products` with products **off** (or the admin flips it mid-session) → falls back to Overview; same for `?section=scanning` with scanning off; an unknown section string shows an empty panel (no guard — see 06-R24).
- Money **off** → no verdict card and no "Full history"/"Your prices" (the planned-meals card stands alone); nutrition **simple/off** → Nutrition row absent; stocktake **off** → Stocktake row absent; products **on** → Preferred buys hidden, rows retained (FU-644).
- Thin data → verdict *No strong buy signal* with the single "Not enough history yet" reason (plan reason survives); belief missing → no card; demand with every meal covered → "N planned meals, all covered".
- Item deleted elsewhere while the peek is open → verdict fetch 404 hides the card silently; `loadDetail` shows "Could not load this stock item."
- Peek swaps id while Scanning is open → QR clears and refetches; while Notes has unsaved text → **the draft is replaced by the new item's notes with no prompt** (the guard only fires on route leave — 06-R16).
- Toggle a switch while typing in Notes → the reload re-hydrates `form.notes` and the half-typed text is lost (06-R16).
- +1d on an **expired** item: the detail page shifts from the expired date (still expired); the overview row's +1d shifts from today (05-R2 — two rules, 06-R1).
- Expiry date, `opened_on`, and timeline expiry bodies render raw ISO `YYYY-MM-DD` (06-R2).
- Substitute whose other item has no level → muted dot; substitute row for an item not in the store yet → name from the DTO, no colour (06-R6).
- Linked product with no price → sorts last, no *Cheapest*; all without prices → no chip at all.
- Barcode POST 404 on an old server → "This server has no barcode endpoint…" (FU-710); duplicate EAN → server message verbatim.
- Price observation in `kJ` → 400 with the supported-units sentence; unknown store → 404; negative pack count → 400.
- Delete price observation → immediate, no confirm (FU-706); no edit path (FU-706).
- Offline: every save is a direct API call with no queue; the toast says *Save failed.* and the editor keeps the typed value (R-020 guard still arms).
- `history_older_count` only counts past the 50-per-kind cap — a 49/49/49 item shows 147 rows and no footer (correct; note for the help text).

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (empty states: no recipes / substitutes / barcodes / prices; thin verdict) | ✓ (A2) | ✓ (money + products off → Overview is level/location/expiry/opened/notes only) | ✓ (ratios, QR print, full history) | ✓ (flag flips mid-session) | – (no per-user state on this page except the verdict opt-out) | – | – |

### A5. Load-bearing conditions
- The detail read is the **de-facto sub-resource API**: cook mode (substitutes), the recipe page (substitutes per ingredient, N reads), the ingredient editor (preferred buys + products), the log-price sheet and the row price button (prefill only) all call `getDetailAsync` and pay for every feed, every lookup and — in complex nutrition — a catalogue match per read (06-R10).
- `_nutrition_is_complex()` **must** run before the entity load (its commit expires the session and the `noload` relationships silently blank) — documented in the handler; any reordering regresses `test_patch_semantics`.
- The verdict's need axis reads the level by FK (`_level_access`), not the relationship — the R-032 trap that once made every verdict `unsure/low`.
- `useBuyVerdict` is a module cache; every mutation site must invalidate it — and today three level-change sites invalidate three *different* sets of caches (06-R4).

### A6. Release-gate rows
- Open an item in the peek, swap to a second item, confirm name / level / verdict / QR / substitutes all belong to the second item.
- Rename an item to its own name → no error; to another's name (different case) → 422 (depends on 05-R30).
- Opened toggle → Cancel → confirm no PATCH in the network log.
- Unlink a product that a shopping-list line and a recipe ingredient had selected → both selections cleared; detail read still 200.
- Delete an item used by a recipe → 422 with the recipe names, item still present.

## B. Help content — Stock-Item Detail

### B1. Current help audit
Stock group already carries *Barcodes*, *QR label*, *Substitutes* (all accurate), *The Buy / Wait / Skip ring on the cart button* (describes the row/line badge, not the card), and *Link a product to a stock item* — **stale**: it says "link a product on the detail page", but the detail page's *Find & link* opens the external companion and linking happens from My Products' "Link to stock item…" (the page comment at `StockItemDetailPage.vue:2531–2534` says so). Nothing explains the page itself: which rows save when, what *Updated* means, the three cards, *Your prices* (the "Usually" median, 3-sample floor, the per-100g denominator, receipts vs logs, the dimension rule), the full-history chart's two line styles, preferred buys vs products, nutrition linking, the Lists ★, the History feeds and the truncation footer, or why Delete can be refused. Tooltips on Essential / Opened / Stocktake / Preferred buys are good one-liners and stay.

### B2. Help entries
Group **Stock** (new entries; sentence-case titles; `path: '/stock'`):

1. **The stock item page** — summary: "Open any item for its own page: on a desktop it opens beside the list, on a phone it takes the screen. Every row on the Overview is its own editor — pickers, toggles and dates save the moment you change them; the name and notes save when you leave the field. *Updated 3d ago* under the level is when the level last changed. Products, Recipes, Substitutes, Scanning, Lists and History each have a tab; a tab is hidden when the feature behind it is switched off for the install."
2. **Dora's three cards on an item** — "At the top of an item sit up to three collapsed cards, in the order of the questions they answer: *Dora thinks …* is her inferred level and why (see *How Dora infers your stock*); *N planned meals need this* is what your upcoming plan wants of it, graded by your recorded level (Out blocks a meal, Low is a watch); *Should I buy it?* is the verdict — with money features on the plan reason folds into the verdict instead. Each opens to its reasoning. None of them is an alert; they are commentary beside the level you recorded."
3. **Your prices** — "Dora keeps your own price record for an item from two sources: prices you log here (*Log a price*) and prices harvested from finished shopping lists. *Usually $X / 100 g* is the **median** of the last 12 months, shown once there are three prices, always per the install's shelf denominator (per 100 g / 100 ml, or per kg / L for big packs; per lb / oz on a US install). *Paying more than usual* means the latest price is more than 15 % over that median. The *Current shelf prices* line is what linked products cost right now and never counts toward the median. One rule to know: the headline follows the **unit family of your most recent price** — log one price per piece for an item you usually price by weight and the figure switches to per piece until you log by weight again." (FU-707/FU-876 are the open design calls; the copy states the current rule honestly.)
4. **The price history chart** — "*Full history* on the Your prices card draws your own logged prices as a solid line with dots, store offers for linked products as a faint dashed line in the same colour, and your usual price as a dotted reference. Everything is per the same unit so the lines can share one axis. Hover for exact values; the legend names each line. Where it says *above usual*, the latest price is over your median." 
5. **Preferred buys** — "A free-text reminder of what you actually buy for an item — *Vitasoy Oat Milky 1 L* — listed A–Z under the Overview. It is a note to yourself, not a product: no prices, no store. When the Products feature is on this section hides, because linked products answer the same question with real prices; your preferred buys are kept and come back if Products is turned off."
6. **Nutrition on a stock item** — "With nutrition in *complex* mode an item can be linked to a food in the nutrition catalogue so recipes using it can total their energy. Dora suggests a match from the name — marked *Suggested* or *Possible match* and never saved until you tap *Use this*. Search yourself with the magnifier; *Not a food* stops Dora asking about that item (linking a food later un-ignores it). *Details* shows the per-100 g panel; only the nutrients the source states are shown — a missing one is left out, never shown as zero. In *simple* mode calories are typed on the recipe and this row does not appear."
7. **Expiry, opened, and the +N buttons** — "The calendar glyph and the date both open the picker; the ✕ clears it; +1d / +7d / +14d push it. Marking an item *Opened* asks whether to shorten its expiry — Skip keeps the date, Cancel changes nothing. Every change is kept as a trail on the History tab (*Set*, *Pushed +7 days*, *Cleared*), so an item you keep pushing back shows up for what it is." (Adjust after 06-R1 lands: "+1d counts from today or the current expiry, whichever is later.")
8. **An item's history** — "The History tab merges everything Dora knows about one item into one timeline, newest first: level changes (read as *Restocked* or *Dropped to*), waste you logged, lists it was added to, what you actually *bought* (a ticked line on a finished list, with price and store when captured), recipes you *cooked* that use it, the expiry trail, plus *Opened* and *Checked (still correct)* from its current state. Each kind keeps its latest 50; *N older events not shown* at the bottom is the honest count of what was cut."
9. **Linked products on an item** — rewrite of *Link a product to a stock item*: "With Products on, the Products tab lists the catalogue products linked to this item, cheapest first with the cheapest outlined, each with its current price, a trend sparkline, its own cart button and a link to the store. Linking happens from **My Products** (*Link to stock item…*) or when the Product Search companion pushes a product in; *Find & link* here opens that companion. Unlinking clears any shopping-list line, template line or recipe ingredient that had chosen that product."
10. **Deleting a stock item** — "Delete removes the item and its history, prices, substitute links and barcodes. Dora refuses while the item is an ingredient of any recipe and names them — remove it from those recipes first. Shopping-list lines that pointed at it keep their text."

Also: fold a *"Lists tab: ★ marks the list the cart button adds to"* sentence into the existing shopping-list quick-add entry (Chunk 3's B2) rather than a new entry.

### B3. DoraBot corpus delta
`app_knowledge.py` Stock paragraph (L14–20) names only "adjust stock level, link products, see which recipes use it, set expiry, mark as opened, push expiry". Add one paragraph: *"An item's page also holds: Dora's inferred level and the buy verdict (money on), planned-meal demand from the next fortnight, your own price record (logged + harvested from finished lists, median 'usually' price, full-history chart), preferred-buy notes (hidden when Products is on), a nutrition-catalogue link in complex mode, substitutes with notes and ratios, direct barcodes + a printable QR label (scanning on), the lists it is on, and a merged history timeline."*

## C. Senior review — Stock-Item Detail

Verdict key: **execute** (Stage 2 applies) · **FU** (orchestrator opens) · **waive** (recorded, no change) · **conditional** (execute if the stated check holds). Sizes S/M/L.

### C1. Bugs (verified or high-confidence latent)
- **06-R1** · Two "+N days" rules on one item. `StockItemDetailPage.vue:1827–1835 shiftExpiry` shifts from `expiry_date ?? today(UTC)`; the row's `useStockItemActions.pushExpiry` (L179–202) shifts from `max(today, current)`. +1d on an expired item gives "still expired" here and "tomorrow" there. Also the detail copy uses UTC "today" (`toISOString`) while the row uses browser-local — both wrong under R-021. · **Exact change:** fold into 05-R2's `POST /stock-items/<id>/push-expiry` (server rule, household today); the page calls `actions.pushExpiry(id, days)` and `shiftExpiry` is deleted; pin with 05-R2's test. · S (given 05-R2) · **execute**.
- **06-R2** · D-006 — raw ISO dates on screen: `L499 {{ detail.expiry_date || '–' }}`, `L538 Opened {{ detail.opened_on }}`, timeline `L2460 fmt = (iso) => iso` and `L2479 body = e.new_expiry_date`. The glyph tooltip already goes through `formatDate` (FU-712 fixed that half). · **Exact change:** route all four through `formatDate` from `useDateFormat`. · S · **execute**.
- **06-R3** · R-003 / FU-799 class — the timeline infers *Restocked/Dropped* by regex on the level **name** (`L2375–2376 /^(low|out)/i`), which breaks for renamed levels ("Running out", "Nearly gone") and is the prose-parsed domain fact R-068 forbids. · **Exact change:** `LevelChangeDto` gains `stock_level_sequence: int | None` (resolve via the `_LevelLookup` already built at `get_stock_item_detail.py:496` — extend it to `{id: (name, sequence)}`); client compares sequences with `LOW_STOCK_SEQUENCE` from `helpers/stockStatus`. Drop the unread `stock_level_id` from the same DTO. · S · guard: `test_stock_item_history_feeds.py` + 1 case · **execute**.
- **06-R4** · Three level-change sites, three invalidation sets: `onChangeStockLevel` (L1974–1993) invalidates verdict + belief + planned demand; `useBuyVerdictActions.markStocked` (L61–67) verdict + belief; `useStockItemActions.markRestocked` (L162–167) verdict only. A *mark restocked* from the row leaves the belief chip and the demand grade stale; `markStocked` from the card leaves the demand grade stale. · **Exact change:** move the three invalidations into `stockItemStore.updateStockLevelAsync` (the one write path, R-074) and delete them from the three callers. · S · **execute**.
- **06-R5** · Two "mark restocked" implementations: `useBuyVerdictActions.markStocked` (finds `STOCKED_SEQUENCE`, toasts the level name) and `useStockItemActions.markRestocked` (takes `stockLevels[0]`, toasts "Marked restocked."). Same intent, different lookup, different toast. · **Exact change:** `markRestocked` delegates to the sequence-based lookup (use 04-R11's `stockLevelStore.stockedLevel`) and the two toasts become one; `markStocked` calls `markRestocked`. · S · **execute**.
- **06-R6** · Substitute rows fabricate a `StockItem` (`stockItemFor`, L2132–2142: `stock_level_id: sub.stock_level_id ?? ''`, nulls for location/group) to borrow a level *sequence* from the store, falling back to no colour when the store hasn't got the item. The DTO already carries `stock_level_id` + `stock_level_name`; what the row needs is the sequence. · **Exact change:** `SubstituteDto` gains `stock_level_sequence` (same `_LevelLookup` as 06-R3); delete `stockItemFor` and the `stockItems` dependency for this tab; drop `stock_level_name` from the DTO if cook mode's swap picker doesn't read it (grep at execution). · S · **execute (conditional on the cook-mode grep)**.
- **06-R7** · `get_stock_item_detail.py:601` and `:633` fetch **the same** `ShoppingListLine` set twice (`STOCK_ITEM_ID.eq(id)`) for the list-adds and purchase feeds; the second branch re-loads the parent lists the first already loaded. · **Exact change:** one fetch, one `{list_id: ShoppingList}` lookup shared by both feeds. · S · **execute**.
- **06-R8** · `get_stock_item_detail.py:874 self.repository.get(Barcode).all()` — a full-table scan of every barcode on every detail read, filtered in Python. · **Exact change:** `EntityField(Barcode, STOCK_ITEM_ID).eq(id) | EntityField(Barcode, PRODUCT_ID).in_(linked_ids)` (or two small queries). · S · **execute**.
- **06-R9** · `recently_priced.py:66 for item in self.repository.get(StockItem).all()` loads the whole pantry to hydrate ≤ 50 names. · **Exact change:** `EntityField(StockItem, "id").in_(list(latest))`. · S · **execute**.
- **06-R10** · The detail DTO as a sub-resource API (A5): `RecipeDetailPage.vue:1672` issues **one full detail read per ingredient** for substitutes; `RecipeCookMode.vue:1272`, `RecipeIngredientRowEditor.vue:368`, `LogPriceSheet.vue:190`, `StockItemRowPriceButton.vue:79` each read one slice. Every call runs 9 feeds, ~15 queries, and in complex nutrition a catalogue `suggest_for_name` (L935–937). · **Exact change (Stage 2, M):** add `GET /stock-items/<id>/substitutes` (handler already has the pair query — extract `build_substitutes(session, id, level_lookup)`), `GET /stock-items/<id>/price-entry-prefill` (extract `build_prefill`), and `GET /stock-items/<id>/buy-choices` (preferred buys + linked products); re-point the five callers; keep the detail DTO as is for the page. · M · **execute** (the extraction is also what 06-R11 wants).
- **06-R11** · `GetStockItemDetailHandler.handle` is ~570 lines in one method (`L418–989`); nine feeds, each with its own lookups, inline imports (`L773 Store as _StoreEntity`, `L780 ShoppingListLine as _Line` — both already imported at module top), and `_Lines` reused for two different collections (`L601` vs `L780`). R-001/R-008. · **Exact change:** split into `_linked_recipes`, `_linked_products`, `_substitutes`, `_level_history`, `_history_feeds` (waste / adds / purchases / cooks / expiry sharing one `HistoryTally`), `_prices` (observations + prefill + your-prices), `_barcodes`, `_nutrition`; drop the aliased imports; fix the two stale "Cap at 20" comments (`L698`, `L720`). · M · guard: `test_stock_item_router.py`, `test_stock_item_history_feeds.py`, `test_patch_semantics.py` · **execute**.
- **06-R12** · `link_product_to_stock_item.py:76–98` — per orphan line: `get(ShoppingList).by_id` + a `one()` lookup → N+1 on a product sitting on many lists. · **Exact change:** fetch the parent lists once by `shopping_list_id in_`, and the existing stock-item lines once by `(list_id in_) & stock_item_id`. · S · **execute**.
- **06-R13** · `get_buy_verdict._items_with_fake_markdown` (L870–904) calls `get_deal_quality` per linked product, each loading the product with both offer collections plus the household's paid prices — on the **bulk** path (`get_list_buy_verdicts`) that is one deep walk per product on the list. · **Exact change:** add `gather_deal_quality_for_products(ids)` in `deal_quality.py` (one products+offers include, one lines fetch) and call it here. · M · **FU** (Chunk 10 owns `deal_quality.py`; bundle with FU-683's B6 follow-through).
- **06-R14** · `your_prices.py` — `build_your_prices_for_item` (L126–265) and `build_your_prices_for_product` (L268–395) are the same ~80-line baseline block twice (sort, latest-dimension, window filter, median, strict-greater, display denominator, three identical empty-state constructions). FU-876 will change that rule — twice. · **Exact change:** `_baseline_from_observations(observations, *, repo, now, system) -> YourPrices` used by both; `_EMPTY_YOUR_PRICES` factory; the product variant passes `offers_sidecar=[]`. · M · guard: `test_your_prices.py` (20 cases) · **execute**.
- **06-R15** · `your_prices.py:47–60 measurement_system_from_repo` reads `repo.get(AppSetting).all()[0]` — a second copy of the install-wide setting read beside `app_settings.access.get_or_create_app_setting` (FU-759 class, R-003). · **Exact change:** `return getattr(get_or_create_app_setting(repo), "measurement_system", units.METRIC) or units.METRIC`. (Mind the commit-expiry hazard the detail handler documents: this runs *after* the entity load today — safe only because nothing below it reads a `noload` relationship on `_StockItem`; keep it that way or move the read up.) · S · **execute**.
- **06-R16** · Latent UX bug: `loadDetail → hydrateForm` after **every** save (L1738, L1845) overwrites `form.name`/`form.notes` with the server copy — a toggle flipped while Notes has an unsaved draft discards the draft; a peek id swap does the same without the R-020 guard (which only arms on route leave). · **Exact change:** `hydrateForm` keeps the current `form.notes`/`form.name` when `isDirty` is true and the id is unchanged; on an id change, if dirty, ask via the same guard dialog before swapping. · S · **execute**.
- **06-R17** · **Cross-surface (Chunk 5 file):** `StockOverview.vue:453–454` comment says the peek opens at **50 %** (feedback "open the split-view at 50%") while `L948 watch(peekId, v => splitPct = v ? 58 : 100)` sets **58**. Either the comment or the number is wrong; the feedback asked for 50. · **Exact change:** owner's call — 50 per the feedback, fix the comment either way. · S · **execute** (patch into CHUNK_05 §C1 as 05-R41 at assembly).

### C2. Redundancy / DRY (R-001, R-003)
- **06-R18** · `BuyVerdictBadge.headline` (L107–115) and `BuyVerdictCard.headline` (L210–219) are the same mapping (the card adds strength grading); the "Based on N price sample(s) · N waste event(s) (last 12 months)." footer is written out in both (`Badge L49–62`, `Card L132–151`). · **Exact change:** `headlineFor(verdict)` and `dataUsedLine(dataUsed)` in `buyVerdictDisplay.ts`; both components call them. · S · **execute**.
- **06-R19** · `formatObsMeasure`/`trimZero` (L1920–1931) hand-roll quantity formatting beside `helpers/formatQuantity` (used by `substituteRatio.ts`). · **Exact change:** `obs.pack_count > 1 ? \`${n} × ${formatQuantity(total/n, unit)}\` : formatQuantity(total, unit)`; delete `trimZero`. · S · **execute**.
- **06-R20** · Three sibling cards, one anatomy, three stylesheets: `.belief-card`, `.demand-card`, `.dora-buy-verdict-card` each declare radius 8px / padding 10px 12px / sunken bg / `--border-strong` border / tone variants / 44px summary / icon tint (`PantryBeliefCard.vue:85–131`, `PlannedDemandCard.vue:96–140`, `BuyVerdictCard.vue:250–345`). · **Exact change:** one `.dora-signal-card` + `.is-{neutral,warning,negative,positive}` tone modifiers in `css/components.scss` (R-002 tokens); each card keeps only its own content rules. · S/M · **execute**.
- **06-R21** · `BuyVerdictCard` hand-rolls the disclosure (summary button + caret button, L15–82) that `CollapsibleCard` owns for the two cards above it — the belief card's own comment says CollapsibleCard "owns that shape for every disclosure in the app". · **Exact change:** host on `CollapsibleCard header-toggles` with the action button in a trailing header slot. · M · **conditional** — execute if `CollapsibleCard` exposes (or can trivially gain) a trailing-actions slot; else FU.
- **06-R22** · Preferred buys sorted A–Z on the server (`get_stock_item_detail.py:742–753`) **and** on the client (`L1857–1861`), with a stale client comment ("Backend still stores a position") and a stale TS doc ("ordered by position", `stockItemDetail.ts:231`) — FU-225 removed `position`. R-003: server owns order. · **Exact change:** render `detail.preferred_buys` as given; fix both comments. `RecipeIngredientRowEditor.vue:371–372` has the same client sort → drop. · S · **execute**.
- **06-R23** · `primaryListId = computed(() => quickAddTargetListId ?? null)` (L2303) and `formatDateTime` (L2589–2592) are pass-through wrappers. · **Exact change:** use the store computed and `formatLocaleDateTime` directly. · S · **execute**.

### C3. Dead code / unused fields / unread endpoints
- **06-R24** · Detail-DTO fields with no SPA reader on this page or anywhere: `stock_location_name`, `stock_location_breadcrumb` (costs a `StockLocation.all()` + breadcrumb walk per read, L487–491), `stock_group_name`, `usual_store_name` (a `Store.by_id` per read, L860–863) — the page edits all four through id pickers and never shows the names (grep `detail.stock_location_name|stock_location_breadcrumb|stock_group_name|usual_store_name` in `web_app/src` → the only breadcrumb readers are *other* DTOs: stocktake, put-away, line sections). `LinkedProductDto.brand` / `merchant_stockcode` — unread on this page (`.brand` readers are product components; `merchant_stockcode` only `CustomProductDialog`, a different DTO). `PriceObservationDto.shopping_list_line_id` and `.store_id`, `PurchaseEventDto.store_id` — only the resolved names are read. · **Exact change:** drop the nine fields from the DTOs + `models/stockItemDetail.ts`; delete the breadcrumb + usual-store lookups; update the handler docstring (L7–8 still promises "location name and stock-level name so the page doesn't cross-reference"). · S · guard: `test_stock_item_router.py` · **execute**.
- **06-R25** · `StockItemDetailDto.unit_cost` — no SPA reader (grep → `models/` only); the page shows `your_prices.current` (display denominator) instead, so the DTO carries two "current per-unit cost" numbers in two unit bases (R-003 smell). `test_price_observations.py` ×3 assert `unit_cost`. · **Exact change:** drop `unit_cost` + `get_stock_item_unit_cost_at` call (L811; keep the domain function — reports and recipe cost use its sibling); re-point the three tests at `your_prices.current` (allow for the display factor). · S · **execute**.
- **06-R26** · `models/stockItemDetail.ts:67–73 WasteEvent.quantity / estimated_value / note` — the DTO sends `occurred_at` + `reason` only (C-waste slim); grep `.estimated_value|w.quantity|w.note` → none. · **Exact change:** drop the three members. · S · **execute**.
- **06-R27** · `ICONS` is `as const` with every key defined, so `ICONS.schedule ?? 'schedule'`, `ICONS.help ?? 'help_outline'` (`BuyVerdictBadge.vue:95–97`), `ICONS.event_repeat ?? 'mdi-calendar-refresh'` (`BuyVerdictCard.vue:101`), `ICONS.price_check ?? …`, `ICONS.inventory_2 ?? …`, `ICONS.delete_outline ?? …` (`buyVerdictDisplay.ts:13–16`) are dead fallbacks that also hide a typo forever. · **Exact change:** remove the six `??`. · S · **execute**.
- **06-R28** · `unlink_product_from_stock_item.py:87–94` — the `UUID(str(product_id))` coercion + comment claims Flask hands the param as `str`, but the route is `<uuid:product_id>` (L83) so it is already a `UUID`; dead defensive code from the FU-528 era. `add_substitute.py:58 str(a) == str(b)` is the same reflex while `update_substitute.py:65` compares directly. · **Exact change:** delete the coercion; compare UUIDs directly in both; this is 01-R8's `uuid_bind` family — apply its helper if a real str path remains anywhere. · S · **execute**.
- **06-R29** · `add_substitute.py:11 from dora_api.domain import units` — unused (validation lives in `substitutes.metadata`). · S · **execute**.
- **06-R30** · `stock_item_price_history.py:36,44 canonical_unit` carries the **display** unit (FU-910) — rename to `display_unit` through `StockItemPriceHistoryDto`, `priceHistoryApiService.ts:65`, `stockItemHistoryToChart`. · S · **execute (resolves FU-910)**.
- **06-R31** · Stale comments: `YourPricesWidget.vue:14–17` ("[Full history] disabled until chunk 6"), `stockItemDetail.ts:241–243` ("chunk 3 placeholder"), `get_stock_item_detail.py:698,720` ("Cap at 20" vs the 50 constant), `StockItemDetailPage.vue:751–756` ("Chunk 4 lights up… chunk 6 wires"). · S · **execute**.

### C4. Componentisation opportunities (R-001)
- **06-R32** · `StockItemDetailPage.vue` (2814 lines) is the second-largest page after `ShoppingListDetail` (FU-780). Natural seams, each already a self-contained block: `StockItemOverviewTab.vue` (L83–811 — the inline-edit list + preferred buys + prices), `StockItemSubstitutesTab.vue` (L992–1076 + picker dialog L1337–1366), `StockItemScanningTab.vue` (L1094–1236 + QR state L1520–1578), `StockItemHistoryTab.vue` (L1289–1319 + `lifecycleEvents` L2343–2529 → a pure `helpers/lifecycleTimeline.ts` with a vitest), `StockItemProductsTab.vue` (L821–944 + L2012–2064), `useStockItemDetail(id)` composable owning `detail/loading/busy/saveField/withBusyReload/loadDetail` + the store-sync watcher. · **Exact change:** the split above; page keeps the header, tabs, delete and the dialogs it hosts. · L · **FU** (bundle with the "big page splits" group: FU-780, 01-R36, 02-D4, 04-R20, 05-R33).
- **06-R33** · `NutritionFoodPicker.vue:2–87` hand-rolls `q-dialog` + `q-card` while every other dialog on this surface uses `BaseDialog` (R-001; D-rules on dialogs ride on the base). · **Exact change:** host on `BaseDialog` (`closable`, `title`, `#actions`). · S · **execute**.
- **06-R34** · `openToggle.ts` is a pure helper with no Vue import living in `composables/` (its own header says it is "kept free of Quasar/store imports"). · **Exact change:** move to `helpers/openToggle.ts` with its spec. · S · **execute**.
- **06-R35** · `models/stockItemDetail.ts:295–304 PricePoint / PriceHistory` are the **product** price-history types (`productApi.getPriceHistoryAsync`) parked in the stock-item model. · **Exact change:** move to `models/product.ts` (or the product API service). · S · **execute**.

### C5. Placement / standards (R-002, R-005, R-008, D-rules)
- **06-R36** · Inline `style=` ×21 on the page: eleven `style="max-width:160px"` label cells (L112…635), `style="font-size: 0.75rem"` (L308), `style="min-width: 0; padding-right: 8px"` (L270), `style="width: 256px; height: 256px; max-width: 100%"` (L1128), `style="max-height: 60vh; overflow: auto"` (L1341), plus `style="margin-left: 24px/26px"` ×4 in the two verdict components and `style="max-width: 110px"`/`"min-width: 130px"` ×4 in `SubstituteMetadataDialog`. · **Exact change:** classes (`.dora-inline-edit__label`, `.dora-buy-verdict__detail`, `.sub-ratio-row__qty/__unit`, `.stock-detail__qr`). · S · **execute**.
- **06-R37** · D-003 — px/rem literals off the type scale: 49 across the five card/page files (`0.6875rem`, `0.75rem`, `0.8125rem`, `0.875rem`, `0.9375rem`, `1rem`, `font-size: 10` in the SVG), and `NutritionFoodPicker` ×8. `YourPricesWidget` and `PriceHistoryChart` already use `calc(var(--font-size-*) * 1rem)` — the pattern to follow. · **Exact change:** token sweep (02-R37 / 05-R22 class). · S · **execute**.
- **06-R38** · D-002 / FU-671 — `text-color="white"` on semantic chips: *Cheapest* (`L878–885`) and *above usual* (`PriceHistoryBottomSheet.vue:35–43`). `colourForSequence`'s sibling `TINT_BY_SEQUENCE` shows the house pattern (`dora-chip--tint-positive/-warning`). · **Exact change:** the two tint classes, no `text-color`. · S · **execute (two of FU-671's sites)**.
- **06-R39** · Raw icon strings: `name="circle"` (L1013 — the substitute dot; `StockLevelDot` exists and takes a sequence → use it, which 06-R6 enables) and `icon: 'lock_open'` (L2500). · **Exact change:** `StockLevelDot` + `ICONS.lock_open` (add to the registry). · S · **execute**.
- **06-R40** · R-039 — `confirmDelete` passes `cancel: { noCaps: true }` but its OK button isn't declared, and the *Still used by recipes* dialog builds `html: true` markup by string concatenation (`L2566–2577`; one of 4 `html: true` app-wide). · **Exact change:** `ok: { noCaps: true }`; render the recipe list via a tiny `BlockedByRecipesDialog.vue` (or the FU-623 wrapper when it lands) instead of HTML strings. · S · **execute**.
- **06-R41** · R-008 — logger idiom: `get_stock_item_detail`, `add/remove/update_substitute`, `link/unlink` create `_Logger = logging.getLogger(__name__)` inside the route per request; `get_buy_verdict`, `get_planned_demand` use a module-level `_LOGGER`; `preferred_buys` / `price_observations` call `logging.getLogger(__name__)` inline. · **Exact change:** module-level `_LOGGER` across the group. · S · **execute**.
- **06-R42** · R-008 / E402 — `your_prices.py:25–35 _as_naive_utc` is defined **between** the `from __future__` import and the module imports. · **Exact change:** move below the imports. · S · **execute**.
- **06-R43** · R-005 — `add/remove/update_substitute.py` and the detail handler read/write the `StockItemSubstitute` association via `db.metadata.tables[...]` Core statements because the generic repository cannot self-join `StockItem`. Portable Core; documented. · **waive** (same posture as 03-R37; revisit if the association ever becomes an entity).
- **06-R44** · R-021 — `BuyVerdictCard.waitHintTargetLabel` (L223–238) computes "in ~N days" from the **browser's** today; the server computed `until` from household today. Off by one across the household/browser zone boundary. · **Exact change:** either the server adds `days_until` to `WaitHintDto`, or the client uses `householdToday()` (04-R?/R-021 helper). · S · **execute** (server field — one rule).
- **06-R45** · R-021 — `_AxisInputs.today: date = field(default_factory=date.today)` (`get_buy_verdict.py:253`) is a server-local default; every production path overrides it with `household_today`. · **waive** (test-only default; comment says so).

### C6. Naming & idiom
- **06-R46** · `recipesForDetail` casts `recipes.value.filter(...) as unknown as Recipe[]` (L2072, L2106): the store's `recipes` is typed differently from `models/recipe.Recipe`. · **Exact change:** fix the store type (or `RecipeCard`'s prop) so the double cast goes. · S · **execute**.
- **06-R47** · `NutritionFoodPicker` borrows `useSettingsSave().notifyError` — a settings-page helper used as a generic error toast on a stock surface (and FU-624 wants one notify wrapper). · **Exact change:** `toastCaption` + `$q.notify` like its neighbours until FU-624 lands. · S · **execute**.
- **06-R48** · `onLists` fallback row `{ shopping_list_id: lid, name: lid, status: 'draft' }` (L2297) renders a UUID as a list name if membership and summaries disagree. · **Exact change:** filter the unknowns out (the comment already says they shouldn't exist). · S · **execute**.
- **06-R49** · `_NutritionIsComplex` — the only CapWords local in a handler whose other locals are `_StockItem`-style; fine. `_Purchases_raw` mixes the two conventions. · S · **execute** (rename with 06-R11).

### C7. Efficiency
- **06-R50** · `loadDetail` triggers `shoppingListStore.refreshAsync()` on **every** reload (L2610) — i.e. after each field save, toggle and preferred-buy edit — a membership+summaries round-trip the save didn't need. · **Exact change:** refresh only from the list-affecting actions (`onAddToList`, `onAddMissing/AllToList`, `onUnlink`, `onBuyVerdictAction`). · S · **execute**.
- **06-R51** · `loadPriceHistories` (L2032–2048) fires one `productApi.getPriceHistoryAsync` per linked product for the sparklines; `priceHistoryApiService.seriesAsync(ids)` already batches. · **Exact change:** one `seriesAsync(ids, '90d')` call, map `points → price_now`. · S · **execute**.
- **06-R52** · `watch(storeItem, …, { deep: true })` (L2643–2663) deep-watches a computed that the store replaces wholesale on every mutation (`stockItems.value[idx] = refreshed`); `deep` adds a per-tick traversal for nothing. · **Exact change:** drop `deep`. · S · **execute**.
- **06-R53** · Complex nutrition runs `suggest_for_name` (a catalogue match) on every detail read of every unlinked, un-ignored item — including the five sub-resource callers in 06-R10. · **Exact change:** lands with 06-R10 (the sub-endpoints skip it); for the page itself it is the right place. · — · **execute via 06-R10**.
- **06-R54** · `get_planned_demand` loads every stock item + resolves levels per call to grade urgency; ≤ 500 items, cheap. · **waive**.

### C8. Design-level findings — out of Stage-2 scope
- **06-D1** · Server-formatted dates inside reason prose: `_wait_hint.reason` (`strftime('%b %d')`, L525) and `planned_demand.build_reason` (`'%a' day '%b'`, L131–132) — same class as 03-R8 (`strftime('%a %d %b')`) and R-056 (one regional convention). The client already receives `until` / `earliest_needed` and formats dates through `useDateFormat`. **Recommend** the server drops the date clause from these sentences and the client appends it formatted; needs the owner's nod because the sentences are owner-approved copy. → FU (cross-surface: 02, 03, 06).
- **06-D2** · FU-706 (no edit / no confirm on observations), FU-707 (signal presentation), FU-876 (latest-dimension rule), FU-704 (PriceEntry on a phone), FU-705 (chart touch) — all open design calls on this surface; copy in B2-3 states the current rules honestly. No action here.
- **06-D3** · FU-644 — preferred buys hidden when Products is on, no migration nudge. Still a decision.
- **06-D4** · The item page has no *Log waste* action though waste is the one event the History tab can't otherwise explain; the row has it. Owner ≥ 90 % happy → record only.
- **06-D5** · `?section=<unknown>` renders an empty tab panel; a `tab` guard to `overview` is a two-line fix but changes nothing the user has asked for → fold into 06-R32 when the page splits.
- **06-D6** · FU-711 — "Opened" vs "open / in-use" wording across row / help; copy sweep.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `PriceHistoryChart.vue` inline SVG | charting | ECharts (removed, FU-833) | **keep** | — | Deliberate; a11y text alternative only possible as SVG. |
| `useBuyVerdict` Map cache | per-item cache | Pinia / TanStack Query | **keep** | — | Documented rationale; `primeBuyVerdicts` handles bulk. |
| `relativeTime.ts` | relative time | `Intl.RelativeTimeFormat` / date-fns | **wrap** | S | A 20-line formatter is fine, but it should respect the install locale (R-056) — route through `useDateFormat`'s locale when it gains relative output. |
| `_trimmed_mean`, `statistics.median/pstdev` | stats | numpy | **keep** | — | Stdlib. |
| `q-date` in the expiry dialog | date picker | — | **keep** | — | Framework. |
| `allLocationOptions` tree walk (L1610–1621) | path labels | `helpers/locationDisplay.ts` / 05-R25 `locationStore.pathOptions` | **replace** | S | Same walk as `CreateStockItemDialog` / `PutAwayDialog`; 05-R25 is the one home. |
| `DoraTabs` | tabs | `q-tabs` | **keep** | — | Owner-chosen indicator. |
| `NutritionFoodPicker` search token | race guard | AbortController | **keep** | — | Correct and small. |

### C10. Standards drift (R-0NN)
- **R-003** · 06-R3, 06-R5, 06-R6, 06-R15, 06-R18, 06-R19, 06-R22, 06-R25 — fix.
- **R-001** · 06-R10/R11 (extraction), 06-R20, 06-R33, 06-R34 — fix; 06-R32 → FU.
- **R-002 / D-002 / D-003** · 06-R36, 06-R37, 06-R38, 06-R39 — fix.
- **R-005** · 06-R43 — waived carve-out, documented.
- **R-008** · 06-R41, 06-R42, 06-R46, 06-R49 — fix.
- **R-021** · 06-R1 (with 05-R2), 06-R44 — fix; 06-R45 waived.
- **R-032** · the detail handler reads `_StockItem.stock_level` / `.stock_location` / `.stock_group` off the relationships (L954–960) — safe only because of the include list **and** the `_nutrition_is_complex` ordering rule; `_level_access.resolve_levels_by_item` is the house answer for the level (FU-684 sweep). Recommend using it here when FU-684 executes (Chunk 7); until then the docstring guard stands. → tracked FU-684.
- **R-039** · 06-R40 — fix.
- **R-045** · none on this surface (QR + print already blob-based via `useQrLabels`).
- **R-056 / D-006** · 06-R2 — fix; 06-D1 → FU.
- **R-074** · 06-R4 — fix.
- **FU-764** (undefined tokens) · none found on this surface (`--focus-ring`, `--accent-ink`, `--radius-*`, `--space-*` all defined; `NutritionFoodPicker` fixed its `--text-accent` already).
- **FU-624 / FU-675** · raw `$q.notify` ×9 on the page, raw `q-select` ×5 (Location/Group/Store + 2 unit pickers) — tracked.

### C11. Ride-along signals for FU-010 / FU-224
- Three signal cards use `--semantic-*-soft` fills with `--border-strong` neutrals; the cheapest-product card uses `color-mix(--brand-primary 8%)` — the primary/semantic split FU-224 owns.
- `.dora-buy-verdict-badge.is-unsure` border = `--surface-sunken` on a `--surface-sunken` fill (invisible border by design?) — check in pesto dark.
- `.dora-buy-verdict-popover` hardcodes `box-shadow: 0 6px 18px rgba(0,0,0,.15)` (R-002 — an `--elevation-*` token exists for cards elsewhere).

## D. Test plan — Stock-Item Detail

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__level_history__carries_sequence_for_restock_inference` | pytest e2e (`test_stock_item_history_feeds.py`) | **must-write-before-ship** | 06-R3 — pins the DTO field the timeline now keys on. |
| `test__detail_dto__drops_unread_fields` (contract snapshot of top-level keys) | pytest e2e (`test_stock_item_router.py`) | **must-write-before-ship** | 06-R24/R25 — the removal is the contract. |
| `test__your_prices__item_and_product_variants_share_one_baseline` | pytest e2e | nice-to-have | 06-R14 — same observations → same median from both builders. |
| `test__substitutes_endpoint__matches_detail_substitutes` | pytest e2e | nice-to-have | 06-R10 — the new sub-resource returns what the detail feed does. |
| `lifecycleTimeline.spec.ts` (merge + sort + restock/dropped by sequence) | vitest | nice-to-have | 06-R3 / 06-R32 — once the pure helper exists. |
| `buyVerdictDisplay.spec.ts` (`headlineFor`, `dataUsedLine`) | vitest | housekeeping | 06-R18. |
| `test_price_observations.py` ×3 — re-point `unit_cost` → `your_prices.current` | pytest | housekeeping | 06-R25. |
| `openToggle.spec.ts` — moves with the helper | vitest | housekeeping | 06-R34. |

Not proposed: a vitest for the 06-R4 invalidation set (drive once: mark restocked from the row → belief chip + demand grade repaint) or for 06-R16 (drive once). The 05-R2 test covers 06-R1.

## E. Proposed follow-ups (orchestrator allocates ids)

- type=follow-up · *Split `StockItemDetailPage.vue` into tab components + `useStockItemDetail`* (06-R32) — bundle with the "big page splits" group (FU-780, 01-R36, 02-D4, 04-R20, 05-R33).
- type=finding · *Bulk `deal_quality` gather for the verdict's fake-markdown check* (06-R13) — Chunk 10 surface; cite FU-683 B6.
- type=finding · *Server-formatted dates inside reason prose (wait hint, planned demand, shopping day names)* (06-D1; 03-R8; R-056) — one decision for three sites.
- type=finding · *Peek opens at 58 % while the comment and the feedback say 50 %* (06-R17) — patch into CHUNK_05 at assembly; execute with the owner's number.
- **Resolve:** FU-910 (06-R30 executes it).
- Existing FUs this chunk executes against: **FU-671** (06-R38, two sites), **05-R2 / FU-123** (06-R1), **01-R8** (06-R28), **05-R25** (C9 location walk), **04-R11** (06-R5), **02-R37 / 05-R22** (06-R37).
- Existing FUs referenced, unchanged: FU-706, 707, 704, 705, 876, 644, 851, 849, 711, 712, 685, 684, 683, 923, 575, 753, 847, 624, 675, 780.

## F. Summary for the register

- FST rows: 18 golden + 17 edge + 5 gate · Help entries: 10 new + 1 rewrite (*Link a product*) + 1 fold-in · Review findings: 54 (execute 43 / FU 3 / waive 4 / conditional 2 / cross-surface 1 / design-record 6) · Tests: 8 (must-write 2) · Bugs: 7 (two "+N days" rules on one item; raw ISO dates ×4; restock/dropped inferred by regex on level *names*; three level-change sites with three different cache-invalidation sets; two "mark restocked" implementations; substitute rows fabricate a `StockItem` to borrow a colour; unsaved notes silently overwritten by any other save)
- One-line: the item page is where the app's best server-side work shows — one cadence engine, one baseline chokepoint, one level resolver — and where its **read model is overworked**: a 1000-line detail handler is being used as five different sub-resource APIs (one full read per ingredient on the recipe page), the cache-invalidation story differs by which button you pressed, and the timeline still parses level names to decide what "Restocked" means.

### Feedback coverage — `# STOCK ITEM DETAIL` (L110–141)

| # | Feedback bullet | Where it lives now | State |
|---|---|---|---|
| SD1 | Clear-expiry cross next to the date | `L507–516` ✕ button | ✅ done |
| SD2 | Relationship between expiry and open? | DR-5 `MarkOpenExpiryDialog` prompts on open; tooltip L541–546 | ✅ done · help B2-7 |
| SD3 | No way to set Essential | Overview row L552 | ✅ done |
| SD4 | No way to set stock group / forgotten feature | Overview row L231; Settings → Stock groups; filter chip | ✅ done (value question: owner kept it) |
| SD4a | "What else has a field with no way to set it?" | Chunk 20 cross-cutting | ➡ Chunk 20 |
| SD5 | Split-view opens at 50 % | `StockOverview.vue:948` sets **58** | ⚠ 06-R17 |
| SD6 | Splitter min/max | `[40, 70]` clamp | ✅ done |
| SD7 | Unlink product exception | FU-528 coercion (now dead code, 06-R28) + `test_delete_product.py` | ✅ done |
| SD8 | Tabs theme-aware | `DoraTabs` | ✅ done |
| SD9 | Level shown twice | header chip removed | ✅ done |
| SD10 | Delete placement | header top-right, icon-only on phones | ✅ done |
| SD11 | Remove Restock | removed from the page | ✅ done |
| SD12 | Opened / expiry controls beside their info | Overview rows | ✅ done |
| SD13 | Find deals → Products tab, only when empty | L833–846 CTA + "Link another" | ✅ done |
| SD14 | QR vs barcode — same feature? | Help *Barcodes* / *QR label*; Scanning tab | ✅ done |
| SD15 | Overview single column | `dora-inline-edit` list | ✅ done |
| SD16 | Location updatable inline | row L201 | ✅ done |
| SD17 | Is Notes fluff? | kept, owner-visible | ✅ decided (kept) |
| SD18 | Add product of choice; highlight cheaper | `AddToListButton` per card + *Cheapest* | ✅ done |
| SD19 | Preferred merchant/product — value? | preferred buys kept, hidden when Products on | ✅ decided · FU-644 open |
| SD20 | Remove from favourites does nothing | `onToggleFavourite` | ✅ done |
| SD21 | Clicking a recipe navigates wrong | `/cookbook/:id` | ✅ done |
| SD22 | Recipe actions dead | all five events wired | ✅ done |
| SD23 | Delete → FK IntegrityError | 422 `blocked_by_recipes` + cascade (`test_delete_integrity.py`) | ✅ done · help B2-10 |
| SD24 | Swap-into-list for substitutes weird | removed | ✅ done |
| SD25 | Keep level dot + outline on substitutes | dot L1012 (06-R6 makes it the shared `StockLevelDot`) | ✅ done |
| SD26 | Lists tab lacklustre; dead go-to icon; "(primary)" plain | rows clickable, ★ quick-add target | ✅ done |
| SD27 | History tab unuseful | purchase / cook / expiry feeds + honest footer | ✅ done · help B2-8 |
| SD28 | Can't edit without changing name — PATCH not PUT | partial PATCH; rename-to-own-name fix | ✅ done (case-insensitivity → 05-R30) |
