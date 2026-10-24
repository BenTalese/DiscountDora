# Chunk 10 — Products / Price History / Deals

**Session:** 2026-10-23 overnight (solo, no subagents) · **Stage:** 1 (analysis only — no code changed)
**Surface:** My Products (`/my-products`), Price History explorer (`/price-history`), price watches (`PriceAlert` → `price_drop` alert), the products catalogue API, the weekly deals email, the deal-quality signal, the reports "price drops" query, and the price-logging entry points (`PriceEntry`, `LogPriceSheet`, `StockItemRowPriceButton`) that the Prices assessment grouped with this axis.

---

## 0. Reading list + files walked

**Governing docs read:** `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` (Appendix A status table), `docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md` (Phase F in progress), `docs/05_investigations/PRICES_SURFACE_UX_ASSESSMENT.md` §6–§8 (D1–D4; FU-703 → resolved), `docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` L156–227 (PRODUCT SEARCH ×31, MY PRODUCTS ×22, PRODUCT HISTORY ×10), `ENGINEERING_STANDARDS.md` (R-001/002/003/005/008/019/021/029/045/056/057/058/069/074), `DESIGN_STYLE_GUIDE.md` (D-001/004/005/006/010/017). Open FUs in scope: FU-922, 923, 919, 917, 911, 846, 838, 831, 768, 753, 732, 708, 705, 704, 644, 627. Resolved and consulted: FU-703, FU-214, FU-605, FU-668, FU-671, FU-789, FU-833, FU-856, FU-883, FU-885.

**Backend walked in full:** `features/products/{get_products,create_product,update_product,delete_product,get_price_history,get_product_image,product_links}.py`; `features/price_history/price_history.py`; `features/deals/{deal_quality,deals_digest,send_deals_email}.py`; `features/reports/reports.py` L805–945 (`PriceDropsHandler`); `domain/entities/{product,product_offer,product_historic_offer,price_alert,store}.py`; `domain/product_offer.py`; `alerts/get_alerts.py::_price_drop_alerts` (L494–540, read for the watch contract); `email_templates/weekly_deals.html` (grep only).

**SPA walked in full:** `pages/MyProductsPage.vue` (1223), `pages/PriceHistoryPage.vue` (474), `components/products/{ProductCard,ProductRow,ProductLinkButton,ProductThumb,CustomProductDialog,ProductPackCountDialog,ProductPhotoDialog,ProductPriceWatchDialog}.vue`, `components/dora/PriceEntry.vue`, `components/LogPriceSheet.vue`, `components/stock/StockItemRowPriceButton.vue`, `components/chips/DiscountChip.vue`, `components/TrendSparkline.vue`, `components/StoreLogo.vue`, `composables/{usePriceChartSeries,useProductSearchUrl}.ts`, `services/api/productApiService.ts`, `stores/productStore.ts`, `models/product.ts`, `helpers/{unitPriceDisplay,scrapedProductOfferLogic}.ts`. `PriceHistoryChart.vue` (566) grep-checked for tooltip theming + `seriesColour` sites only (its drawing logic is pinned by `priceHistoryChart.spec.ts`).

**Verification greps run:** routes (`/my-products`, `/price-history` — **no `/products` SPA route**), `spa_deep_link` callers, `DEFAULT_LIMIT`/`MAX_LIMIT`, every `tables["StockItemProduct"]` reader (11), `last_fired_at` writers, `seriesColour(` sites, "on special" rule copies (client 4 + server 3), `productStore`/`productApiService` consumers, `resolveBaseURL()}/` `<img>` sources, raw `text-color="white"` / `Nms ease` / raw icon names in the chunk's components, money/feature gating in the three backend packages (none), `find_unit` casing, `apply_offer_to_product` signature, existing test names (8 pytest files, 4 vitest specs).

---

## A. Full Systems Test — Products / History / Deals

### A1. Preconditions
- Products overlay has data (`features.products` data-presence flag true → nav shows **My Products**; it hides entirely when the catalogue is empty — R-029). Fastest seed: `POST /api/products` ×3 with one store on special (`price_was > price_now`), or an `/api/ingest` push.
- At least one `Store` exists (Settings → Stores) — `POST /products` refuses unknown store names.
- A user with a **verified** email, `deals_email_enabled`, `send_deals_on_day` = today's weekday, SMTP configured (or drive `send_deals_email(now=…, _send_email=spy)`).
- Money features on (watch thresholds are dollar amounts).

### A2. Golden path
| # | Step | Expect |
|---|---|---|
| G1 | Open **My Products** (cards view) | Toolbar: Stock items without products (count, glows only when >0), Add custom, Bulk select, Cards/Compact toggle, Filters, Search. Cards show photo/glyph, green `% off` badge, struck was-price, store logo, link state, Custom chip where hand-entered. Footer: Shown / On deal / Unlinked. |
| G2 | Toggle **Compact** | Same list, one row each; view mode remembered across visits (`useListViewMode('my-products')`). |
| G3 | Click the grey broken-link button on an unlinked product → pick a stock item → Link | Button turns green, chip names the stock item; chip click opens `/stock/<id>`. Unlink via the green button: product stays, chip gone. |
| G4 | Add to list from a **linked** product | Line nests under the stock item with that product selected. From an **unlinked** product → product-only line (chunk 3 contract). |
| G5 | **Add custom**: name, store, price, "1kg", pack count 12, photo | Card appears with Custom chip; `is_custom` true; no `% off` (price_was defaults to price_now); photo served via `/products/<id>/image`. |
| G6 | ⋮ → **Set items in pack** on an ingested product → 6 | Menu item now reads "Items in pack: 6"; recipe costing can price a bare count (chunk 1). Clear → null. |
| G7 | ⋮ → **Alert me on a price drop** → $4.00 → Save | Card shows "Alert at $4.00"; bell refreshes. Re-open: "Change price alert", Stop watching removes it. |
| G8 | Ingest/PATCH the product to `price_now` ≤ 4.00 | Bell gains a `price_drop` alert (medium) with add-to-list via the linked stock item; one episode per offer (`price_drop:<offer.id>`). |
| G9 | ⋮ → **Price history** | `/price-history?product_id=` opens with that product pre-selected, chart drawn, comparison card with current price, `% off`, all-time low, "Your usual" when observations exist. |
| G10 | Pick up to 5 products, switch 30d/90d/1y/All | Each pick refetches (FU-605 fixed); 6th pick → "Up to 5 products at a time." toast. Range changes the plotted window; all-time low unaffected. |
| G11 | **Manage alerts** | Lists the user's watches with store logo + threshold; Remove deletes. |
| G12 | ⋮ → **Delete product** on a product that is on a *finished* list and a *live* list | Confirm names the consequence; product, offers, watch and link go; finished list line survives with the snapshot name; live list line is removed. |
| G13 | Bulk select → Select… → "Low stock, on deal" → Add N on-deal to list | Picker of active lists; adds only linked, on-deal selections. Unlink / Stop tracking / Delete act on the selection; Deselect all empties it. |
| G14 | Weekly deals: `send_deals_email(now=<send day 07:00 household>)` | One mail per opted-in verified user; subject "Up to N% off this week" (≥20) or "N deals this week"; ledger row `deals:weekly_email:YYYY-Www` stamped; second tick same hour → 0 sent. |

### A3. Edge cases
| # | Case | Expect (and what the code does today) |
|---|---|---|
| E1 | Catalogue > 50 products | **Today: My Products, the price-history picker and the shopping-list linked lookup see only the first page of 50** (`getAllAsync` sends no `limit`; `DEFAULT_LIMIT = 50`) and nothing says so → 10-R9. |
| E2 | Weekly email "See all deals" link | **Today it points at `/products`, a route that doesn't exist** → 10-R1. Expect `/my-products`. |
| E3 | Product Search URL unset, non-admin user, empty catalogue | Empty state says "Use Product Search"; the CTA routes a non-admin to an admin settings path → 10-R30. Expect hide-when-off copy. |
| E4 | Custom product with the same (store, name) as a later ingest | Ingest must not adopt it (`test__ingestion_does_not_adopt_a_custom_product_with_the_same_name` ✅). |
| E5 | PATCH `price_now` only | 422 "price_now and price_was must both be set." ✅ |
| E6 | Photo on an ingested product | 422 "Only products you added yourself…" ✅; card hides the menu item for non-custom. |
| E7 | Subscriber with unverified email | Skipped with an info log; Settings → Notifications explains ✅. |
| E8 | Week with nothing on special | No mail **and no ledger stamp**, so a 07:20 ingest still mails on the next tick ✅. |
| E9 | Household timezone changed at runtime | Hourly job re-reads it each tick ✅ (R-021). |
| E10 | Watch threshold is a *pack* price labelled `threshold_unit_price` | Works as pack price end-to-end; naming is wrong → FU-911/FU-917. |
| E11 | Split SPA/API host or Capacitor shell | Product photos load (authed `ProductThumb`); **store logos do not** (`StoreLogo` binds the API URL into `<img src>`) → 10-R35. |
| E12 | Dark mode chart hover | Tooltip uses `--surface-component` / `--text-secondary` on a static read → PH7 still "confirm in browser" (FU-708). |
| E13 | Price-history page on a phone | Chart has no touch interaction (FU-705); alerts button drops its label ✅. |
| E14 | Delete alert belonging to another user | 404 — scoped by `user_id` ✅. |
| E15 | Custom product size "500 ML" / "1 kg " | Parses; unit is upper-cased on save (`'KG'`) while ingested rows carry `kg` → 10-R8. |

### A4. Persona coverage
- **Pantry-only household (no products):** sees nothing from this chunk — nav entry hidden, no deals mail (no products → empty digest → silent), price watches unreachable. Direct URL to `/my-products` shows the empty state. ✅ hide-when-off.
- **Products user who never links:** product-only shopping lines (chunk 3), delete works, deals mail works; "Stock items without products" glows permanently because every stock item is an orphan → 10-D3.
- **Admin:** sets Product Search URL (ingestion page), curates stores, manages who gets the deals mail.
- **Phone shopper logging prices in an aisle:** `PriceEntry` three-across + numeric keypad gaps → FU-704.

### A5. Load-bearing conditions
- `StockItemProduct.UNIQUE(product_id)` — a product links to at most one stock item (every `linked_stock_item_*` stamp assumes it).
- `is_custom` is load-bearing: excluded from the sync list, never adopted by ingest dedupe.
- `AlertInteraction` ledger key is ISO-week scoped — changing send day mid-week cannot double-mail.
- `GetBestDealsHandler` is live via the email (`DEAL_POOL_SIZE = 40`) even though its HTTP route is orphaned (FU-838).
- `DiscountChip` is the one `% off` renderer (FU-885) — but the *rule* "on special" still has four client copies (10-R23).

### A6. Release-gate rows
- [ ] Weekly deals mail "See all deals" opens My Products (after 10-R1).
- [ ] My Products shows the whole catalogue on an install with > 50 products (after 10-R9).
- [ ] Store logos render in the Capacitor shell / split host (after 10-R35).
- [ ] Price watch set from My Products fires as a `price_drop` alert on the next lower offer and never twice for the same offer.
- [ ] Deleting a product leaves finished-list lines named.

---

## B. Help content — Products / History / Deals

### B1. Current help audit
`HelpPage.vue` has two entries touching this surface, both stale:
- **"Link a product to a stock item"** (L401–404, under Stock): says "On the detail page…"; the grey/green `ProductLinkButton` on My Products is now the primary place to link/unlink. Rewrite.
- **"Search for products"** (L469–472, under *Shopping & deals*, `path: '/'`): "opens an admin-configured external search surface… pushes data back into Dora via the ingestion seam" — jargon ("seam"), and `path: '/'` is wrong. Rewrite; point at `/my-products`.
No entry exists for My Products, custom products, pack count, price watches, price history, the weekly deals email, or deal quality. `app_knowledge.py` (DoraBot corpus) has **zero** mentions of My Products / price history / custom products.

### B2. Help entries (one per feature / auto-behaviour)
New group **"Products & prices"** (icon `ICONS.shopping_bag`):

| # | Title | Summary (plain voice, D-copy) | path |
|---|---|---|---|
| H1 | What a product is | A product is one thing at one shop with a price — "Coles brand milk 2L". A stock item is the thing in your kitchen. Link a product to a stock item and its price rides along with your pantry record; you can also use products on their own. | `/my-products` |
| H2 | Finding products | Product Search opens the companion app your admin set up; what you save there lands in My Products. If the menu has no Product Search, ask your admin to set it up under Settings → Admin → Product data. | `/my-products` |
| H3 | Cards or compact rows | Switch with the toolbar button; Dora remembers your choice. Cards show photos and every action; rows show the essentials and the two everyday buttons. | `/my-products` |
| H4 | Link or unlink a product | The grey broken-link button means "not linked" — tap it to pick a stock item. Green means linked — tap it to unlink. The chip beside it names the stock item and opens it. | `/my-products` |
| H5 | Add a product to a shopping list | Linked products add under their stock item with that product chosen. Unlinked ones add as a product-only line, marked as such. | `/my-products` |
| H6 | Custom products | For a shop Dora can't check — a butcher, a market stall. You type the price, size and store; Dora never refreshes it, and marks it **Custom** so you can tell. Only custom products can carry your own photo. | `/my-products` |
| H7 | Items in the pack | A 700 g carton says nothing about how many eggs are in it. Set "items in the pack" on any product so a recipe's "3 eggs" can be priced. | `/my-products` |
| H8 | Tracking prices | "Stop tracking prices" hides a product from deals and the weekly email without deleting it; show it again with the "Show untracked" filter. | `/my-products` |
| H9 | Deleting a product | Gone for good, with its price history and any watch on it. Finished shopping lists keep their record of it; live lists drop the line. | `/my-products` |
| H10 | Bulk select | Select… offers All visible, On deal, Inactive, and the stock-aware helpers (Low stock on deal, Out of stock on deal, Essential + low on deal). Then add the on-deal ones to a list, unlink, stop tracking or delete in one go. | `/my-products` |
| H11 | Stock items without products | The toolbar count is stock items that no tracked product is linked to. It lights up when there are any. | `/my-products` |
| H12 | Watch a price | ⋮ → "Alert me on a price drop", enter the pack price you'd buy at. One watch per product; saving again replaces it. When a new offer lands at or below it, you get a bell alert (and a push if you have them on) — once per offer. | `/my-products` |
| H13 | Price history | Compare up to five products' advertised prices over 30 days, 90 days, a year or all time. Each card shows the current price, discount, the all-time low, and — if you've logged prices yourself — your usual price. A product with no offers shows your own logged prices instead. | `/price-history` |
| H14 | Weekly deals email | Settings → Notifications: pick a day; the mail arrives at 7 am your time with the best specials across your tracked products — compact (up to 20 lines) or expanded (up to 10 with detail). A quiet week sends nothing. Needs a verified email address. | `/settings/notifications` |
| H15 | Is it really a deal? | Dora checks a special against the product's own 90-day history and what you've actually paid. A "special" that's dearer than your usual price is called out, never celebrated. | `/stock` (Buy verdict) |

Rewrites: fold the old "Link a product…" into H4 (delete the Stock-group entry) and replace "Search for products" with H2.

### B3. DoraBot corpus delta
Append a **Products** paragraph to `app_knowledge.py`: *"My Products holds the products you saved from Product Search (an external companion the admin configures) plus any custom products you typed in for shops Dora can't check. A product can be linked to one stock item (grey broken link = unlinked, green = linked) or used on its own. Each product can carry an items-in-pack count, and you can watch a price: one watch per product, which fires as a price-drop alert once per new offer at or below your figure. Price history compares up to five products over a range and shows your own usual price where you've logged one. The weekly deals email goes out at 7 am on the day you pick, only to verified addresses, and only when something is on special. Dora never looks prices up live — everything comes from what was pushed in."*

---

## C. Senior review — Products / History / Deals

Finding ids `10-Rk`. Verdicts: **execute** (Stage 2, test-guarded) · **FU** (needs an owner call or is cross-surface) · **waive** (reasoned) · **conditional**.

### C1. Bugs (verified or high-confidence latent)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 10-R1 | `deals/send_deals_email.py:106` | `spa_deep_link("/products")` — the SPA has no `/products` route (`routes.ts:89–90` define `price-history` and `my-products`). Every weekly mail's "See all deals" button lands on the catch-all. | `spa_deep_link("/my-products")`; pin with a test that renders the HTML and asserts the href. | execute |
| 10-R2 | `pages/PriceHistoryPage.vue:159–166` | "currently N% above [all-time low]" carries an InfoTip explaining *your usual price from prices you've logged* — but the figure is offers-based (`atl_by_product` reads `ProductHistoricOffer`). Already named in FU-708 ("mis-parented tooltip"). | Delete the tip or reword: "the lowest advertised price Dora has seen for this product". | execute (FU-708) |
| 10-R9 | `services/api/productApiService.ts:13`; consumers `MyProductsPage.vue:602`, `PriceHistoryPage.vue:441`, `ShoppingListDetail.vue:2721` | `getAllAsync` hits `/products` with no `limit` → server `DEFAULT_LIMIT = 50`. On an install with 51+ saved products, **My Products silently shows 50**, the footer says "Shown 50", the history picker can't find product 51, and the list's linked lookup misses. FU-668 called this trap for pickers; this is the list page itself. | `getAllAsync` requests `?limit=500` (`MAX_LIMIT`) and the store surfaces `page.total` so the footer can say "Shown N of M"; a real paginated catalogue page is an FU if a household ever exceeds 500. Also retire the dead `slice(0,100)` in `PriceHistoryPage.vue:339,345`. | execute |
| 10-R30 | `MyProductsPage.vue:302–314, 423–428, 1166–1172` | Empty-state and orphans copy say "Use Product Search"; when no URL is configured `openProductSearch` routes **every** user to `/settings/admin/system/ingestion` — an admin path a member can't use. Hide-when-off (R-029). | Read `useProductSearchUrl().configured` + `isAdmin`: configured → CTA; unconfigured admin → "Set up Product Search"; unconfigured member → copy "Ask your admin to set up Product Search" and no button. Empty state also mentions **Add custom**. | execute |
| 10-R35 | `components/StoreLogo.vue:104–111, 12–19` | `imageUrl` = `${resolveBaseURL()}/stores/<id>/image` bound into `<img :src>` — the exact R-045 violation `ProductThumb.vue`'s header documents (unauthenticated by construction; silent broken image on a split `app.`/`api.` host and in the Capacitor shell). No carve-out comment. Renders on My Products, Price history, shopping lists, settings. | Fetch via `AxiosHttpClient.getBlob` + `objectUrlFor`, as `ProductThumb` does — ideally by extracting one `AuthedImage` primitive both use (10-R45). Keep the hash-swatch fallback. | execute |
| 10-R5 | `products/update_product.py:96–110` | The PATCH price path appends a `ProductHistoricOffer` by hand: no `source`, no "did the price actually change" check, no dedupe — while `create_product.py:110` routes the same event through the shared `apply_offer_to_product` (`source="manual"`). Two offer-append rules (R-003); the module FIXME in `product_historic_offer.py` describes the race this path had. | `apply_offer_to_product(repo, product, price_now=…, price_was=…, observed_at=now, source="manual")`; test: one historic row with `source == "manual"`, no row when the price is unchanged. | execute |
| 10-R43 | `deals/deal_quality.py:178–185` | The 90-day horizon is built as **UTC midnight of the household date** (`datetime.combine(today - 90d, min.time(), tzinfo=timezone.utc)`), plus a local `_as_utc` shim for naive rows. Same R-021 slip as 07-R1 / 08-R3. | `tzinfo=household_timezone(repo)` (or compare dates in household-local); drop `_as_utc` once rows are known-aware. | execute |
| 10-R4 | `PriceHistoryPage.vue:435–448` | `onMounted` reassigns `selectedIds` (fires the `watch` → `refreshSeries()`) and then calls `refreshSeries()` again — double fetch on deep-link. | Drop the explicit call (the watch covers it) or make the watch `immediate` and remove both explicit calls. | execute |

### C2. Redundancy / DRY (R-001, R-003)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 10-R6 | `price_history/price_history.py:179–185` | Inline `deal_pct = max(0, int(round((1 - now/was)*100)))` duplicates `domain/product_offer.discount_percent` (and rounds differently at the boundary). | `discount_percent(now, was)`. | execute |
| 10-R12 | `reports/reports.py:905–925`, `deals/deal_quality.py:146–158` | Both re-implement the `StockItemProduct` join read (+ `reports` re-implements `stamp_has_image`) "because no shared DTO". Full count of raw `tables["StockItemProduct"]` readers is **11**: `product_links.py` (the shared one), `get_link_status.py:217` (FU-923), `reports.py:910`, `deal_quality.py:153`, `barcodes.py:447`, `recipe_cost.py:164`, `get_buy_verdict.py:885`, `get_stock_items.py:185`, `your_prices.py:290/536/681`. | Make `stamp_has_image(repo, ids) -> dict[UUID,bool]` and `linked_stock_items` the only two readers in this chunk's packages (reports + deal_quality); widen FU-923 to list the other 7 for the ingestion/stock chunks. Also removes the two function-local `from dora_api.app import db` imports (R-008). | execute (this chunk) + FU-923 widened |
| 10-R15 | `price_history.py:40` vs `reports.py:734` | `_RANGE_DAYS` defined twice (reports' is a superset: adds 2y/5y). | One `features/_ranges.py` (`RANGE_DAYS`, `range_cutoff`), imported by both. | execute |
| 10-R23 | `MyProductsPage.vue:656–660`, `ProductCard.vue:251–255`, `chips/DiscountChip.vue:59–66`, `StockItemDetailPage.vue:898`, `helpers/scrapedProductOfferLogic.ts` (orphan, FU-838) | "On special" = `was > now` is written four times client-side while the one helper that already states it has no consumer. | `helpers/offerLogic.ts` exporting `isOnSpecial(offer)` + `discountPercent(offer)` (rename of the orphan file); `DiscountChip`, `ProductCard.hasDiscount`, `MyProductsPage.onSpecial`, the detail page use it. Server rule stays `domain/product_offer.py` (accepted Type-C display carve-out, now with one client copy instead of five). | execute |
| 10-R20 | `LogPriceSheet.vue:185–196, 212–218`, `StockItemRowPriceButton.vue:70–86, 88–94`, `PriceEntry.vue:155–162` | Both entry points fetch prefill by downloading the **whole** stock-item detail (`getDetailAsync` → `price_entry_prefill`, 06-R10's sub-resource case), both hold a `storesList` computed, and the submit payload type is declared inline three times. | Export `PriceEntrySubmission` from `PriceEntry.vue`; both callers use `GET /stock-items/<id>/price-entry-prefill` (06-R10) and the exported type. | execute (with 06-R10) |
| 10-R22 | `CustomProductDialog.vue:219–224, 237–240` vs `ProductPackCountDialog.vue:85–91` | Pack-count parsing/validation written twice with two different messages. | `helpers/packCount.ts::parsePackCount(raw): number \| null \| undefined` + one message constant. | execute |
| 10-R25 | `create_product.py:88–95` | Loads every `Store` and matches `name.strip().lower()` in Python — the same rule `CreateStoreHandler` uses for duplicate detection. | `features/stores/find_store_by_name(repo, name)` used by both. | execute |
| 10-R41 | `deals/deals_digest.py:56–101` | `format_money` claims to be "the only server-side money formatting in the app" — 09-R1 found `suggestions/generate_over_budget` hard-coding `$` ×5. | Lift `format_money` + `_CURRENCY_SYMBOLS` to `infrastructure/money.py`; 09-R1 consumes it. | execute (cross-chunk with 09-R1) |
| 10-R42 | `send_deals_email.py:226–244` | `_ledger_row` = `.all()` → `rows[0]`; the alerts chunk proposed `alerts/_ledger.py` helpers for exactly this `AlertInteraction` read (09-R12) and the `.one()` idiom (09-R9). | Use the shared ledger helper. | execute (with 09-R12) |
| 10-R40 | `PriceHistoryPage.vue:212–227, 316–319, 402–421` vs `components/products/ProductPriceWatchDialog.vue` | Three ways to manage one watch: the per-card inline `MoneyInput` + "Set alert" (PH3's "squished card"), the "Manage alerts" dialog (list/remove only — FU-708), and the My Products watch dialog (set/change/remove, refreshes the bell). | Reuse `ProductPriceWatchDialog` from the comparison cards (button "Watch this price" / "Change watch") and from the Manage-alerts rows; delete `alertInputs` + `onSetAlert`. Fixes PH3 + the FU-708 "cannot create" half in one move. | execute (FU-708) |
| 10-R21 | `components/dora/PriceEntry.vue:35–43` | Price field is a raw `q-input type="number" :prefix` while `MoneyInput` (symbol prefix, 2dp on blur, `inputmode`) exists and is used by the three product dialogs. | `MoneyInput` — also lands FU-704's keypad point. | execute (FU-704) |

### C3. Dead code / unused fields / unread endpoints
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 10-R19 | `stores/productStore.ts:35–39` | `createProductAsync` / `updateProductAsync` have **no consumers** (grep); `MyProductsPage` mutates through `productApi` directly and then re-runs `loadAll()` — five parallel refetches (products, stock items, levels, lists, watches) after every single toggle, link, photo or delete. | Mutations go through the store (which refreshes `products` only); link/unlink additionally refresh `stockItemStore`; `loadAll` on mount only. Resolves the dead exports by giving them their callers (R-074). | execute |
| 10-R38a | `productApiService.ts:36–37`, `products/get_products.py:187–203` | FU-838: `getBestDealsAsync` + `GET /products/best-deals` have no SPA consumer. **`GetBestDealsHandler` itself is live** (the deals email pool). | Delete the route + client method, keep the handler; `scrapedProductOfferLogic` survives as the renamed shared helper (10-R23). Resolve FU-838. | execute |
| 10-R39 | `price_history.py:270, 292, 312`; `domain/entities/price_alert.py:22` | `last_fired_at` is written only to `None` on re-save and read into a DTO nobody renders (FU-917). | Execute FU-917 as written: drop the column (migration) + DTO field; the episode key does the job. The `threshold_unit_price` → pack-price rename is FU-911's call. | execute (FU-917) |
| 10-R49 | `MyProductsPage.vue:595–596`, `PriceHistoryPage.vue:293–295, 438–440` | Comments claim "a save on the product-search surface (which writes through `productStore.createProductAsync`) is visible here" — there is no in-app search surface (FU-186) and nothing calls that method. | Rewrite to the true reason (one store, lazy hydration) — R-019. | execute |
| 10-R26 | `domain/entities/product_historic_offer.py:7–14`, `product_offer.py:12` | Module FIXME (profanity, a commit hash, "I can't be assed") describing the race 10-R5 fixes; a `TODO: Presentation only…` that is long since done elsewhere. | Replace with a two-line factual note on why historic offers are a separate table; delete the TODO. | execute |
| 10-R37 | `PriceHistoryPage.vue:339,345` | `.slice(0,100)` on a list that is at most 50 rows (10-R9). | Remove with 10-R9. | execute |
| 10-R10 | `ProductCard.vue:59,64`, `ProductRow.vue:67` | `formatMoney(product.price_now ?? 0)` — `price_now` is non-null in the DTO and the type; the guard renders "$0.00" if it ever fired. | Drop `?? 0` (with 10-R7). | execute |
| 10-R46 | `tests/e2e/dora_api/test_product_router.py:268` | `test__create_product__MerchantAlreadyExists__MerchantIsReused` — Merchant was renamed Store in Phase E. | Rename `StoreAlreadyExists__StoreIsReused`. | execute |

### C4. Componentisation opportunities (R-001)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 10-R45 | `ProductThumb.vue`, `StoreLogo.vue` (10-R35), the stock-item / recipe image routes (chunks 5/6/1), the QR-label fetch | Each authed image fetch is hand-rolled per surface; `ProductThumb` is the best copy (in-flight guard, glyph fallback). | One `AuthedImage.vue` (props: `path`, `hasImage`, `alt`, fallback slot) that `ProductThumb`/`StoreLogo` wrap. | FU (cross-surface; execute `StoreLogo` via 10-R35 first) |
| 10-R28 | `ProductRow.vue:126–134` | Row click → `window.open(web_url)` on a `q-card` — not a link: no keyboard/middle-click/status-bar preview (D-005); `ProductCard` already does it properly with a real `<a target=_blank rel=noopener>`. | Wrap the identity block in the same `<a>` the card uses (shared `ProductStoreLink` slot or copy the `topHalfAttrs` computed into a tiny composable). | execute |

### C5. Placement / layering (R-003, R-005)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 10-R17 | `price_history/price_history.py` (whole module) | Every read is raw `db.metadata.tables[…]` + `db.session.execute`, and `delete_price_alert` commits with `db.session.commit()` — the only module in the chunk that bypasses the repository ports and `save_changes` (R-005, R-031). Core-SQL is Postgres-portable, so not a correctness bug; it is the pattern R-005 exists to stop spreading. | Execute the small part: delete via `repo.remove(alert)` + `save_changes()`, create/list via `repo.get(PriceAlert)`. The multi-table series read stays core-SQL with an inline `# R-005 carve-out: aggregate over 4 tables` comment. | execute (small) + comment |
| 10-R16 | `price_history.py:69–76` (+3 call sites) | Local `_current_user_id()` reading `session.get("user_id")` — another FU-654 copy. | `infrastructure/auth_helpers.current_user_id()`. | execute (FU-654 sweep) |
| 10-R3 | `price_history.py` (no gate); `MyProductsPage.vue:615–617` comment | The comment says price watches are "money-gated on the server like every price surface" — **no** `money_features_enabled` check exists in `products/`, `price_history/` or `deals/`. R-058 says a dollar surface refuses at the endpoint. The products overlay is data-presence gated, not money gated, so whether a *pack-price threshold* counts as a money surface is an owner call. | Minimum: correct the comment. Recommended: gate `/price-history/alerts*` on `money_features_enabled` (403 `MONEY_DISABLED_DETAIL`) and hide the watch menu item when money is off. | conditional (owner) — comment fix executes regardless |
| 10-R27 | `products/get_price_history.py` (per-product `/products/<id>/price-history`) | One consumer: `StockItemDetailPage.vue:2037` sparkline loop — N sequential requests, one per linked product, for the same data `/price-history?product_ids=a,b,c` returns in one call (cap 5). | Detail page calls the multi-product endpoint once (≤5 linked products is the realistic case; fall back per-product beyond 5); then retire the per-product route or keep it as the raw-points contract. Belongs with 06-R10's sub-resource rework. | conditional (with chunk 6) |
| 10-R38 | `PriceHistoryPage.vue:374–380` | `aboveLowPct` computed client-side from two server numbers while the sibling `deal_pct` is server-computed. | Display math over two shipped facts — the "already clean, do not relocate" category. Note the asymmetry; leave. | waive |

### C6. Naming & idiom
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 10-R7 | `models/product.ts` vs `ProductDto` | `brand`, `merchant_stockcode`, `web_url` typed `string` but nullable server-side (`str \| None`); `store_id?` optional but always stamped; `pack_count` correct. R-057 contract drift — the templates already guard with `v-if="product.brand"`. | `string \| null` ×3, `store_id: string`. | execute |
| 10-R24 | `get_products.py:66` | `bool(getattr(product, "is_custom", False))` on a declared dataclass field. | `product.is_custom`. | execute |
| 10-R11 | `PriceHistoryPage.vue:316–319` | `alertInputs` declaration sits at column 0 inside an indented `<script setup>` (R-008). Moot once 10-R40 deletes it; otherwise re-indent. | — | execute |
| 10-R8 | `CustomProductDialog.vue:217` | `splitSize` upper-cases the unit (`'KG'`, `'ML'`); server `find_unit` lower-cases so costing resolves, but the stored `size_unit` casing differs from every ingested row (`kg`, `g`, `ml`). | Store the canonical key from `UNIT_TABLE` (lower-case) and validate against it client-side so an unknown unit is rejected at the form. | execute |
| 10-R32 | `MyProductsPage.vue:443` | Raw `name="inventory_2"` — `ICONS.inventory_2` exists (`ProductCard.vue:176`). | Use the registry. | execute |

### C7. Efficiency
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 10-R13 | `get_products.py:150–157` (`GetBestDealsHandler`), `reports.py:837–843` (`PriceDropsHandler`), `deal_quality.py:169–173` | Each loads **every** `Product` with offers into Python to rank/scan — the 06-R9 / 08-R4 shape. Fine at hundreds; wrong shape at thousands. Needs a repo capability to filter/order on a related entity's columns, or a core-SQL ranked query. | Ranked core-SQL query for best-deals (`price_now < price_was`, ordered by `(was-now)/was`) with the entity hydrate on the top-N ids only. | FU (opportunistic — when the repo gains related-field filters, or a household passes ~500 products) |
| 10-R14 | `price_history.py:108–128` | Historic rows fetched twice per request (ranged + all-time for ATL). | One unranged query; derive the ranged series in Python. | execute |
| 10-R31 | `MyProductsPage.vue:1153–1164`, `LogPriceSheet.vue:146–151, 181` | `stockLevels.find` per rendered orphan row (twice) and inside a sort comparator. | `levelsById` Map (the level store likely has one — chunk 5). | execute |
| 10-R47 | `MyProductsPage.vue:881–1019` | Bulk unlink / stop-tracking / delete loop N sequential requests with one catch; partial failure is reported honestly ("Could not delete everything.") and `loadAll` reconciles. | A bulk endpoint is a design call; today's shape is honest. | waive |

### C8. Design-level findings — out of Stage-2 scope
| Id | Finding | Recommendation |
|---|---|---|
| 10-D1 | Product-axis fate (`/price-history` as a page vs sheet from My Products; PH10, assessment D1) — **FU-703 resolved** (RESOLVED ledger L338). Both surfaces kept; `/price-history` still has no nav entry and is reached only via a product's ⋮ menu (PH1 "hidden away"). | Record the FU-703 decision in H13; if "hidden" still bites, the cheapest fix is a "Price history" link in the My Products toolbar. Owner call. |
| 10-D2 | Watch thresholds are pack prices named `threshold_unit_price` and the `unit_price` key on the product series is a pack price (FU-911). Works; the vocabulary lies. | Resolve FU-911 together with FU-917's column drop — one migration. |
| 10-D3 | `stockItemsMissingProducts` (`MyProductsPage.vue:1144–1151`) counts **every** stock item without a tracked linked product, so the attention glow fires permanently on any install that uses products for a few items ("Stock items without products (214)"). The MP-18 glow was asked for; the predicate makes it wallpaper. | Owner call on what deserves attention: essentials only? items with a preferred buy? items added in the last N days? Or drop the glow and keep the count. |
| 10-D4 | "Stop tracking prices" / "Track prices" is offered on **custom** products, which nothing refreshes — `is_active` on a custom product only affects deals ranking/email. | Relabel for custom ("Hide from deals") or hide the item (R-029). Small; owner wording. |
| 10-D5 | Three alert surfaces for one watch (10-R40) is the structural version of PH8's ask for one place; after 10-R40 the page's cards and the bell both point at the same dialog. | None beyond 10-R40. |

### C9. Hand-rolled-vs-library verdicts
| Surface | Hand-rolled | Verdict |
|---|---|---|
| `PriceHistoryChart.vue` (566 lines, SVG, crosshair, legend, baseline) | Yes | **keep** — already the one chart for three callers (FU-833), spec-pinned; a chart library would bring 100 KB for one SVG. Touch support is FU-705. |
| `TrendSparkline.vue` | Yes (40 lines) | **keep** — but read tokens via `var()` in `style`, not `getComputedStyle` (10-R36). |
| `deals_digest.format_money` | Yes (flat symbol table) | **keep** — documented; one email's worth of prices. Lift to `infrastructure/money.py` (10-R41). |
| `CustomProductDialog.splitSize` regex | Yes | **keep** — tiny; validate against `UNIT_TABLE` (10-R8). |
| `StoreLogo` hash-swatch | Yes | **keep** — deterministic, zero logos shipped by design. |

### C10. Standards drift (R-0NN)
| Id | Rule | Where | Verdict |
|---|---|---|---|
| 10-R33 | R-069 / FU-671 `text-color="white"` | `PriceHistoryPage.vue:33,191`, `ProductCard.vue:92`, `DiscountChip.vue:10`; raw `color: white` at `ProductCard.vue:367` | execute (FU-671 sweep: `--text-on-accent`) |
| 10-R34 | D-010 motion tokens; D-017 radii | `ProductCard.vue:292`, `ProductRow.vue:140` `120ms ease`; `ProductRow.vue:139` `var(--radius-sm, 8px)` literal fallback | execute (`var(--motion-fast)`, drop the fallback) |
| 10-R36 | R-002 tokens-only | `TrendSparkline.vue:34–45` reads `--semantic-positive/negative` via `getComputedStyle` with hard-coded `hsl()` fallbacks; SVG accepts `style="stroke: var(--semantic-positive)"` directly | execute |
| 10-R16 | FU-654 `session.get("user_id")` | `price_history.py:70` | execute (sweep) |
| 10-R17 | R-005 / R-031 | `price_history.py` raw session + `commit()` | execute small + carve-out comment |
| 10-R43 | R-021 household timezone | `deal_quality.py:178–185` | execute |
| 10-R12/10-R44 | R-008 (function-local imports "to avoid cycles") | `deal_quality.py:150–151`, `reports.py:905` | execute with 10-R12 |
| 10-R26 | R-019 comments ≠ code / hygiene | `product_historic_offer.py` FIXME | execute |
| 10-R49 | R-019 | stale store comments | execute |
| — | R-045 | `StoreLogo.vue` (10-R35) | execute |
| — | R-056 dates in prose | None in this chunk: `PriceEntry` uses `formatRelativeDay`, the series ships ISO for the chart axis (a chart, not prose), the email formats no dates. | clean |

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- `DiscountChip` green + white text is the one `% off` (FU-885) — white → `--text-on-accent` (10-R33).
- `ProductCard__oos` red banner uses `--semantic-negative` + raw white (10-R33).
- `PriceHistoryPage` "above usual" chip `color="warning" text-color="white"` — amber on white is the D-002 contrast case; `--text-on-accent` and check.
- `product-card--inactive` / `product-row--inactive` = `opacity: 0.6` — fine (D-001 grey = absent/unknown).
- Chart tooltip is token-based on a static read (PH7 stays FU-708 "confirm in browser").

---

## D. Test plan — Products / History / Deals

**Existing (keep):** pytest `test_product_router.py` (43: create/get/update incl. pagination defaults), `test_custom_products.py` (16: is_custom, photo rules, pack count, ingest non-adoption, sync exclusion), `test_delete_product.py` (9: cascade, finished vs live lines, ingest delete auth), `test_price_history.py` (7: 400/404/placeholder, your_prices + observations, alerts CRUD), `test_deals_email.py` (19: pure policy — day/hour/ledger key/money/lines/subject), `test_deal_quality.py` (10), `test_product_offer.py` (3), `test_product_search_url_setting.py` (4); vitest `discountChip.spec` (12), `priceChartSeries.spec` (8), `priceHistoryChart.spec` (9), `unitPriceDisplay.spec` (12).

**Proposed (lean — stable contracts only, per the 2026-07-20 stance):**
| # | Pins | Layer | Why |
|---|---|---|---|
| T1 | `send_deals_email` renders `deals_url` to a route the SPA has (`/my-products`) — assert the href in the rendered HTML via the `_send_email` spy | pytest | 10-R1; a dead link in an unprompted weekly mail is the worst-case regression and is invisible to every other test |
| T2 | PATCH price → exactly one `ProductHistoricOffer` with `source == "manual"`; same price again → no new row | pytest (extend `test__update_product__UpdatingAllAttributes`) | 10-R5 contract |
| T3 | `/price-history` `current.deal_pct` equals `discount_percent(now, was)` for a boundary pair (e.g. 3.995/4.00) | pytest (extend `test_price_history`) | 10-R6 |
| T4 | `get_deal_quality` window edge: an offer at household-local midnight 90 days ago is inside the window in a +10 household | pytest | 10-R43 (R-021) |
| T5 | `deals_url` + unsubscribe present in `_text_body` | pytest | cheap, same seam as T1 |
| T6 | `/price-history/alerts` 403 when money is off (only if 10-R3 is decided "gate") | pytest | R-058 |
| — | `getAllAsync` limit, StoreLogo authed fetch, store-routed mutations | — | **no automated test** — drive once and delete the DORA_VERIFY line (verification stance) |

**DORA_VERIFY additions (Stage 2 close):** open the weekly mail's "See all deals" → My Products; >50 products visible on My Products + history picker; store logo renders in the Capacitor shell; set a watch from My Products, push a lower offer, see the bell + "once per offer"; price-history tooltip in dark mode (PH7).

---

## E. Proposed follow-ups (orchestrator allocates ids)

| # | Title | Type | Resolution point | Source |
|---|---|---|---|---|
| E1 | Widen FU-923 to all 11 raw `StockItemProduct` readers (7 outside this chunk) | leftover | with chunks 5/6/16 Stage 2 | 10-R12 |
| E2 | `AuthedImage` primitive for every authenticated image route (products, stores, stock items, recipes, QR) | leftover | after 10-R35 lands | 10-R45 |
| E3 | Ranked core-SQL for best-deals / price-drops / deal-quality instead of load-all-and-rank | finding | opportunistic — when the repo gains related-field filters or a household nears 500 products | 10-R13 |
| E4 | Decide: are price watches a money surface (R-058 gate on `/price-history/alerts*`)? | decision | now (owner) | 10-R3 |
| E5 | Decide the "Stock items without products" attention predicate (glow fires on every install) | decision | now (owner) | 10-D3 |
| E6 | Relabel/hide "Track prices" for custom products | decision (wording) | now (owner, one line) | 10-D4 |
| E7 | Detail-page sparklines: one multi-product history call instead of N per-product calls; fate of `/products/<id>/price-history` | leftover | with 06-R10 | 10-R27 |
| E8 | True paginated catalogue page if a household exceeds `MAX_LIMIT` (500) | finding | when triggered | 10-R9 |
| E9 | Record the FU-703 decision in help + consider a "Price history" toolbar link on My Products (PH1) | leftover | opportunistic | 10-D1 |

**FUs this chunk resolves or advances at Stage 2:** FU-838 (route + client method deleted; handler kept, helper renamed → resolve), FU-917 (column dropped → resolve), FU-708 (tooltip copy + "cannot create" via 10-R40; PH7 stays "confirm in browser"), FU-704 (`MoneyInput` in `PriceEntry`; responsive layout still to do), FU-923 (two sites executed here, widened), FU-654 (+1 site), FU-671 (+5 sites). FU-911/FU-846/FU-705/FU-922/FU-919/FU-831/FU-768/FU-753/FU-732/FU-644/FU-627 untouched — their resolution points stand.

---

## F. Summary for the register

- FST rows: 14 golden + 15 edge + 5 gate · Help entries: **15 new** (a new **Products & prices** group — none existed) + 2 stale rewrites + DoraBot paragraph (corpus had zero product coverage) · Review findings: **49** (`10-R1..R49` + 5 design `10-D1..D5`) — **37 execute**, 5 FU, 3 conditional, 4 waive · Tests: 6 proposed (pytest), none vitest · FUs: 9 proposed, 7 existing advanced.
- One-line: the products overlay is in good shape where the owner looked (cards/rows, link button, custom products, bulk helpers, delete, deals email policy all land the feedback) and rough where nobody could see — the weekly mail links to a route that doesn't exist, the catalogue is silently capped at 50 everywhere the SPA reads it, store logos are the unauthenticated `<img>` R-045 names, PATCH-price bypasses the shared offer-append rule, and the one chart's price-watch has three UIs.

### Feedback coverage — `# PRODUCT SEARCH` (L156–186), `# MY PRODUCTS` (L188–212), `# PRODUCT HISTORY` (L214–226)

**PRODUCT SEARCH** — the in-app search page was retired (FU-186, Phase D); the page and 25 of its 31 bullets moved to the external companion and are **out of scope here (companion)**. The six that touch Dora:

| # | Feedback bullet | Where it lives now | State |
|---|---|---|---|
| PS1 | Merchant vs data-provider conflation | Stores are user-curated (FU-189); providers = ingestion page | ✅ done |
| PS7 | Plain-English accuracy disclaimer | Companion surface; Dora's equivalent is H2/H14 copy ("Dora never looks prices up live") | companion + B2 |
| PS9–11 | Cannot save / quick-add / link: "Extra inputs are not permitted" | Save is a companion→ingest push; link + add-to-list on My Products work (`test_product_router`, chunk 3 lines) | ✅ done |
| PS27 | Link button as the merchant logo | `StoreLogo` with upload + hash-swatch (Phase E); **logo `<img>` is unauthenticated** → 10-R35 | ➗ |
| PS20 | Page state remembered between navigations — assess per screen | My Products: `useListState('my-products')` + `useListViewMode` (filters + view remembered, deliberately) | ✅ done |
| PS23 | One loading indicator everywhere | `AppSpinner` used | ✅ done |

**MY PRODUCTS**

| # | Feedback bullet | Where it lives now | State |
|---|---|---|---|
| MP1 | Products usable standalone; product-only lines nest when linked; removal modal | `AddToListButton inline-product`, product-only lines (chunk 3 contract); "noted in guides" → H1/H5 | ✅ built · help in B2 |
| MP2 | Add custom products for unsupported stores | `CustomProductDialog` + `is_custom` (OD-2) | ✅ done |
| MP3 | Mark inactive: "Extra inputs not permitted" | PATCH `is_active` works (`test__update_product__UpdatingIsActiveOnly`) | ✅ done |
| MP4 | Fewer ellipses, actions on the card | Two everyday actions on the face + one ⋮ (owner 2026-10-15 two-per-row) | ✅ done |
| MP5 | Grey broken / green linked button; click to link/unlink; still show which item | `ProductLinkButton` + stock-item chip | ✅ done |
| MP6 | Componentise the cart button | `AddToListButton` (5 variants) | ✅ done |
| MP7 | No way to remove a saved product | `DELETE /products/<id>` + confirm naming consequences (FU-883) | ✅ done |
| MP8 | Inactive styling unclear | `opacity .6` + "Show untracked" filter; H8 explains | ✅ done · help B2 |
| MP9 | Filter clear behaviour consistent | `FilterToggleButton` + `FilterBar` shared | ✅ done |
| MP10 | `% off` chip small / use the card space | `DiscountChip` `md` default (FU-885) | ✅ done |
| MP11 | Unlink modal cancel button yellow; componentise | `confirmDestructive` — red OK, flat cancel (D-008) | ✅ done |
| MP12 | Deselect all in bulk mode | Select… → Deselect all | ✅ done |
| MP13 | Bulk bar styling consistent | `dora-subbar` | ✅ done |
| MP14–17 | Select inactive / low-on-deal / out-on-deal / essential-low-on-deal | Select… menu, server-owned stock flags | ✅ done |
| MP18 | Orphans button should grab attention when >0 | `attention` glow — fires on every install with any unlinked item → 10-D3 | ➗ (owner predicate) |
| MP19 | Refresh button — why? | Removed | ✅ done |
| MP20 | Bulk select in the toolbar, drop the learnt-once prose | Done | ✅ done |
| MP21 | Open-stock-item button unnecessary — click the name | Chip is the link | ✅ done |
| MP22 | Page info hidden/tiny — sticky footer like Stock | `PageCountsFooter` (Shown / On deal / Unlinked) — **counts the first 50 only** → 10-R9 | ➗ |
| MP23 | Filters shown by default on desktop, hidden on mobile | `useFilterPanelExpanded` | ✅ done |

**PRODUCT HISTORY**

| # | Feedback bullet | Where it lives now | State |
|---|---|---|---|
| PH1 | Major feature, hidden away | Reached only via ⋮ → Price history; FU-703 resolved keep-both; nav link = 10-D1 / E9 | ➗ |
| PH2 | Select products → no change | FU-605 fixed (reassign, not splice) | ✅ done |
| PH3 | Card squished; notify placeholder cut | `MoneyInput` below the price + full-width button; **replace with the watch dialog** → 10-R40 | ➗ |
| PH4 | Notify input should format as a price | `MoneyInput` | ✅ done |
| PH5 | `% off` and text tiny | `DiscountChip` default size | ✅ done |
| PH6 | `% off` colour inconsistent — componentise | `DiscountChip` green everywhere (FU-885) | ✅ done |
| PH7 | Hover bubble not theme-aware | Tooltip uses `--surface-component`/`--text-secondary` on static read — **confirm in browser** (FU-708) | 🟡 |
| PH8 | Manage alerts here is good; want central granular control | Settings → Notifications per-kind switches (chunk 9); local dialog can list/remove, create via 10-R40 | ➗ |
| PH9 | Graph doesn't reach the box edge | `measureChart` = `clientWidth − 16` + `ResizeObserver` (FU-708 verify) | 🟡 confirm |
| PH10 | Drawer/bottom-sheet from My Products; use My Products as the selector | Bottom sheet built for **stock items** (`PriceHistoryBottomSheet`); product axis kept as a page (FU-703) | ✅ decided |

`docs/02_feedback/COVERAGE_GAPS.md` — no flips needed; the three blocks were already attributed to these surfaces.
