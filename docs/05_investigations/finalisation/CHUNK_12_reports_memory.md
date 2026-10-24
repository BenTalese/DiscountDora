# Chunk 12 — Reports / Memory (P8-09), Waste, Budget

**Session:** 2026-10-23 overnight (solo, no subagents) · **Stage:** 1 (analysis only — no code changed)
**Surface:** `/reports` (Summary lede, Spend ×3 axes + savings line, Waste, Kitchen memory, Price changes), the `features/reports` endpoints behind it (incl. the orphaned stock-value report and the dashboard-read price-drops), waste capture + insights (`features/waste`, `MarkAsWastedDialog`, `useLogWaste`, bulk endpoints), and the household budget (`features/budget`, `BudgetSettings.vue`, `useBudgetSettings`). The dashboard's own money/budget cards are chunk 8; the Buy verdict is chunk 6.

---

## 0. Reading list + files walked

**Governing docs read:** `docs/05_investigations/REPORTS_PAGE_REVIEW.md` (§0–§10; the owner's in-session review stands in for the empty feedback section — §3.1–3.11 answers, §6 findings 1–20, §8 D1–D7 all closed/spawned), `docs/04_proposals/PROPOSAL_WASTE_MINIMISATION.md` (§2 D1–D14 locked; §13 A–C impl notes), `PROPOSAL_BUDGET_AWARE_LISTS.md` + `PROPOSAL_BUDGET_DEFENSE_SWAPS.md` (status only), feedback `# REPORTS` / `# WASTE` (both literally `?`), `COVERAGE_GAPS.md:266` (Reports deferred → review). Open FUs in scope: FU-898, 843, 841, 832, 831, 873, 907. Resolved and consulted: FU-703 (D2/D3 put the trend job here), FU-809/810/811/812 (→ 832/831/833), FU-813/814/815/816, FU-845, FU-768, FU-448.

**Backend walked in full (2,744 lines):** `features/reports/reports.py` (1,617 — 10 reports + `range-window`), `features/waste/waste.py` (613), `features/budget/budget.py` (514).

**SPA walked in full (~2,900 lines):** `pages/ReportsPage.vue`, `components/reports/{ReportsLede,SpendCard,WasteCard,KitchenMemoryCard,ItemPriceMoversCard}.vue`, `services/api/{reportsApiService,wasteApiService,budgetApiService}.ts`, `components/stock/MarkAsWastedDialog.vue`, `composables/{useLogWaste,useBudgetSettings}.ts`, `helpers/wasteReasons.ts`, `pages/settings/BudgetSettings.vue`.

**Verification greps run:** `StockItem` relationship laziness (`table_mappings.py:1467–1469` — `stock_level`, `stock_location`, `products` all `lazy="noload"`); every reports/waste/budget client method's consumers (`getStockValueAsync`, `getRescueAsync`, `listEventsAsync` — **none**; `getPriceDropsAsync` — dashboard; `getSavingsCapturedAsync` — Reports only); `GetWasteRescueHandler` callers (assistant tool + a docstring); router mode (`hash` — the cards' `#/stock/…` hrefs are valid); `--text-sm` token (undefined); `DoraSegmented` (9 consumers) vs `BaseSegmented` (13); `household_timezone` helper exists; week-start setting (none); `WASTE_REASON_VALUES` vs the two TS tile lists; `_product_id` private-attr reads across features (18); existing tests (7 pytest files, 0 vitest).

---

## A. Full Systems Test — Reports / Waste / Budget

### A1. Preconditions
- Money features on (admin); otherwise only Waste and Kitchen memory render and the money endpoints 403 (R-058).
- At least two **finished** shopping lists with ticked, priced lines (actual or picked-offer price), ideally at two stores and in two stock groups; one list from the prior window for "vs last period".
- Several cook events (`POST /recipes/<id>/cook`), two or more logged prices for the same item (shelf-price or finished-list harvest), a few waste events.
- A household budget set in Settings → Budget (any member can set it).

### A2. Golden path
| # | Step | Expect |
|---|---|---|
| G1 | Open `/reports` | Summary card leads with "You spent $X across N shops in the last 30 days, Y% more than the 30 days before. Biggest mover: Dairy, up $Z."; range picker 30d default; window label "3 Aug 2026 – 2 Sep 2026" under it. |
| G2 | Spend → By store | `ProportionBar` in store brand colours, "No store set" hatched; legend with spend + list counts; coverage line "N items had no price recorded, so they aren't counted here." |
| G3 | Spend → By group | Same bar keyed by stock group; "Uncategorised" bucket; share %. |
| G4 | Spend → vs last period | Per-group ↑/↓ with %; "new" where the prior window had none; on All time the axis explains it needs a bounded range. |
| G5 | Savings support line | "$X of that was under shelf price." — only when products are on and a saving exists. |
| G6 | Waste card | Total thrown out in the effective window (clamped to 365 days), five reason tiles (zero tiles dimmed), tapping a tile filters the list, "+N more, not shown" past 6 rows. |
| G7 | Kitchen memory | "You cooked 14 times…: 31 meals, 9 different recipes."; repertoire line (always last-365-days); column track with quiet buckets; Cooked most / Bought most lists linking to recipe / item. |
| G8 | Price changes | "N of your items changed price…"; Dearer / Cheaper columns with ↑/↓ and "$2.10 → $2.40/100g"; tap a row → `PriceHistoryChart` with your usual price + store offers as context; "Open <item>" link. |
| G9 | Change range to 1 year | Every card refetches; window label updates; YoY compares year vs the year before; waste caption still says the window it used. |
| G10 | Stock row → expiry menu → Mark as wasted → tap "Spoiled" | Event logged, expiry cleared, 5 s Undo toast; Undo deletes the event and restores the expiry. |
| G11 | Stock bulk bar → Log waste for 20 items | One request each way; toast; Undo restores each previous expiry. |
| G12 | Settings → Budget → $150 weekly | Dashboard budget card shows spent / projected / remaining; `/budget/history` chip "N of last 6 weeks over". |
| G13 | Money off (admin) | `/reports` keeps Waste + Kitchen memory; Summary, Spend and Price changes gone; Settings → Budget shows the "ask an admin" note. |

### A3. Edge cases
| # | Case | Expect (and what the code does today) |
|---|---|---|
| E1 | Shop finished Monday 08:00 in a +10 household | **Today it is counted in last week's budget** (window bounds are UTC midnight of household dates; history buckets by the UTC date) → 12-R2. |
| E2 | Evening user east of UTC reads the window label | **Today the end date can read as tomorrow** (`now.date()` in UTC) → 12-R3. |
| E3 | Item added to five finished lists but ticked on two | **Today "Bought most" counts 5** → 12-R4. Expect 2. |
| E4 | Same reason on the modal and the report | **Today the modal says "Bought too much", the report tile "Overbought"** → 12-R6. |
| E5 | One observation per item | Price changes shows the honest empty line "N of your items have a logged price, but none has two in this range yet" ✅. |
| E6 | Two readings in different dimensions (500 g then 2 L) | Row built from the active dimension only; `items_with_mixed_units` counted ✅. |
| E7 | First price 0; same price twice | Dropped; counted as unchanged, not a mover ✅. |
| E8 | New category this window | `delta_pct: null` → "new", never +∞% ✅. |
| E9 | `/reports/spend-year-over-year?range=all` | 400 with a plain message; SPA never asks ✅. |
| E10 | Waste insights on "All time" | `window_days` clamps to 365 and the caption says so ✅. |
| E11 | One report endpoint 500s | That card shows "I couldn't load …" + Try again; others render ✅ (review finding 8 fixed). |
| E12 | SQLite install, bounded range on Price changes | `_as_utc` coercion; no TypeError (FU-813 class) ✅. |
| E13 | Money gate resolves after mount (cold load) | Gated loaders re-fire when the flag turns on ✅ (duplicated with the dashboard — FU-844). |
| E14 | Stock value endpoint called directly | **Today it under-reports for any item that was never re-levelled and ignores linked-product prices** (noload trap) — and nothing in the SPA calls it → 12-R1. |
| E15 | Undo toast fires twice | Delete is idempotent (204 both times) ✅. |

### A4. Persona coverage
- **Pantry-only, money off:** two cards (Waste, Kitchen memory) + the capture flow — the page stays worth a nav slot (review §3.11) ✅.
- **Money on, no products:** Spend by store attributes via the five-rung store ladder (usual store / planned / purchased) — populated without any product (FU-815) ✅; Price changes works from logged prices alone (FU-703 D3) ✅; savings line hidden.
- **Products user:** savings line against shelf price (FU-831 will re-baseline); price drops on the dashboard.
- **Non-admin member:** can set the household budget (kitchen-setup class) ✅; cannot turn money on.
- **Phone:** one-column grid under 1024; reason grid 3-up under 600; 44 px rows ✅.

### A5. Load-bearing conditions
- "Spent" = **ticked** lines on **finished** lists, priced by the actual→picked ladder, completed inside the window, `deferred_by_budget = false` — the same rule in `period_spent`, history, spend-by-store/category/YoY and savings (12-R10 makes it one function).
- Reports' store attribution goes through `resolve_store_id` with `last_purchase_store_id=None` (a record, not a guess) ✅.
- Repertoire is deliberately not range-scoped (365 days) ✅.
- Money endpoints refuse at the server (R-058); the page gates before asking ✅.
- Waste events are reason-only (D13); the signal survives for the Dora Score ✅.

### A6. Release-gate rows
- [ ] A shop finished at 08:00 local on the first day of a period counts toward that period (after 12-R2).
- [ ] Spend-by-store total == spend-by-category total == savings `total_spent` on one fixture (after 12-R10).
- [ ] "Bought most" counts ticked lines only (after 12-R4).
- [ ] Window label dates match the household date near midnight (after 12-R3).
- [ ] `getStockValueAsync` / `GET /reports/stock-value-over-time` gone (after 12-R1) or fixed and consumed.

---

## B. Help content — Reports / Waste / Budget

### B1. Current help audit
`HelpPage.vue` has **no** entry for Reports, Kitchen memory, Price changes, waste logging or the budget (the only "report" hits are the Report-an-issue button). `app_knowledge.APP_OVERVIEW` names none of them either. The in-page text is good (lede, coverage lines, honest empties) but nothing explains what the figures are built from, which is the first question a money report gets.

### B2. Help entries (one per feature / auto-behaviour)
New group **"Reports, budget & waste"** (icon `ICONS.insights`):

| # | Title | Summary | path |
|---|---|---|---|
| H1 | What Reports is built from | Your own records only: finished shopping lists with prices, cooks logged in cook mode, prices you logged, and waste you marked. Nothing is looked up. A list you never finished, or a line you never ticked, isn't spend. | `/reports` |
| H2 | The range and "All time" | Every card answers for the range you pick; the dates it covers sit under the picker. "All time" starts at your first record. The waste card looks back at most a year and says so. | `/reports` |
| H3 | Where the money went | Spend has three views: by store (in each store's own colour; "No store set" when Dora couldn't tell), by stock group, and against the same-length period before. Items with no price are counted and named, never silently dropped. | `/reports` |
| H4 | "Under shelf price" | The support line under Spend adds up what you paid below the store's listed price on finished lists. It only appears when products are on and there was a saving. | `/reports` |
| H5 | Kitchen memory | Cooks are the times you finished a recipe in cook mode; meals are the portions you said you made; "different recipes" is your repertoire in the range. The line about recipes you haven't cooked always looks at the last year, whatever range you pick. | `/reports` |
| H6 | Bought most | How many finished shops each item was actually bought on in the range. | `/reports` |
| H7 | Price changes | For items you've logged two or more prices for, the first and last price in the range, quoted per the shelf unit (per 100 g, per L, each). Tap an item to see the chart with your usual price and any store offers behind it. Items with one price, or prices in different units, are counted but not shown. | `/reports` |
| H8 | Logging waste | On a stock row, open the expiry menu and choose Mark as wasted, then tap a reason. The expiry clears; Undo within five seconds puts both back. Bulk select logs many at once. The Waste card and Dora's "what am I wasting" answer read these. | `/stock` |
| H9 | Reports with money off | Waste and Kitchen memory stay; Summary, Spend and Price changes go, and their endpoints refuse. | `/reports` |
| H10 | The household budget | Settings → Budget: one amount for the household, weekly (Monday start) or monthly. Spent is what you ticked on finished lists in the period; projected is what's on open lists dated in it; the dashboard card and "N of your last 6 weeks over" read the same numbers. Any member can set it. | `/settings/budget` |

### B3. DoraBot corpus delta
Paragraph for `app_knowledge.py` (lands per 11-D1): *"Reports answers four questions from the household's own records: where the money went (by store, by stock group, or against the previous period), what gets thrown out, what we actually cook and buy, and which of our own items got dearer or cheaper. Everything comes from finished shopping lists with prices, cook-mode cooks, logged prices and marked waste. The budget is one household figure (weekly or monthly) set under Settings → Budget; spent counts only ticked lines on finished lists in the period."*

---

## C. Senior review — Reports / Waste / Budget

Finding ids `12-Rk`. Verdicts: **execute** · **FU** · **waive** · **conditional**.

### C1. Bugs (verified or high-confidence latent)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 12-R1 | `reports.py:236–268` (`StockValueOverTimeHandler`) | Loads `StockItem` with **no includes** and reads `i.stock_level.sequence` and `i.products` — both `lazy="noload"` (`table_mappings.py:1467–1469`), so every item's current rank is 0 and the linked-product price branch never fires (R-032; the FU-873 trap). The figure is level-change history × observation fallback only, which is the §3.3 "systematically undercounted". And it has **no consumer**: the Reports card was cut (chunk 3), the dashboard `pantry_value` card went 2026-09-04, `getStockValueAsync` is unreferenced — the dashboard comment claiming "callers on the reports page" is stale. | Delete the handler, route, `StockValueResponse`/`getStockValueAsync` and `test__stock_value_over_time__…` (R-057). If it is ever revived, `.include(STOCK_LEVEL).include(PRODUCTS)` first. | execute (delete) |
| 12-R2 | `budget.py:95–96, 129–134, 417` | `period_spent` bounds the window at **UTC midnight** of the household dates (`_as_utc_datetime`) and `GetBudgetHistoryHandler` buckets by `completed_at.date()` (UTC) while the anchor is `household_today`. In a +10 household a shop finished Monday 08:00 local counts in **last** week's budget; the status card and the history chip are wrong for the first ~10 h of every period (R-021). The module comment calls this "timezone gymnastics it doesn't deserve". | `datetime.combine(d, time.min, tzinfo=household_timezone(repo))` for the bounds; `completed_at.astimezone(tz).date()` in history; rewrite the comment. Test T1. | execute |
| 12-R3 | `reports.py:117–126, 173–183` | `_parse_range` and `range_window.end` anchor on UTC `now`; the window label can read tomorrow's date in the evening east of UTC, and bounded windows start at a UTC instant (R-021). | Anchor on `household_today` + household midnight; share the helper with 10-R15's `_ranges.py`. | execute |
| 12-R4 | `reports.py:655–660` (`MostBoughtItemsHandler`) | Counts distinct archived lists an item appears on, **ticked or not**; the card says "Bought most". An item added and never bought scores the same as one bought (FU-768's class — "on the list ≠ bought"). | `ShoppingListLine.is_ticked == True`. Test T2. | execute |
| 12-R5 | `waste.py:107–122` | "Value at risk" picks the **last line by `sequence`** over every list the item ever appeared on — `sequence` is per-list, so the pick is arbitrary — while the comment says "cheapest-last-paid-price". `your_prices` already owns an item's baseline. | Use `build_your_prices_for_item(...).baseline`, or drop `estimated_value` (only the assistant tool renders it). | execute |
| 12-R6 | `WasteCard.vue:135–145` vs `helpers/wasteReasons.ts:22–28` | The card declares its own `WASTE_REASON_TILES` ("Overbought") while the helper that calls itself the single source says "Bought too much"; the modal and the report name one reason two ways (R-003). | Import the helper. | execute |
| 12-R7 | `ReportsPage.vue:367–373` | `windowLabel` uses `toLocaleDateString(undefined, …)` — the browser's locale, not the install's (D-006; `useDateFormat.formatDate` exists). | `formatDate(iso, { day:'numeric', month:'short', year:'numeric' })`. | execute |
| 12-R8 | `budgetApiService.ts:4–6` | Doc says settings "live on the User row… go through `AuthApiService.updateMeAsync`" — stale; the same class implements `PATCH /budget/settings` on `AppSetting` (R-019). | Fix the comment. | execute |
| 12-R9 | `waste.py:44–47` | `_DEFAULT_HORIZON_DAYS = 7` "mirrors the assistant's `_EXPIRY_HORIZON_DAYS`" — the assistant reads the admin-configurable `expiring_soon_window_days`; this is a third fixed copy (R-003; the 11-R34 family). | Default from `effective_expiring_soon_window(get_or_create_app_setting(repo))`. | execute |

### C2. Redundancy / DRY (R-001, R-003)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 12-R10 | `SpendByStoreHandler:469–517`, `SavingsCapturedHandler:725–753`, `SpendByCategoryHandler:1162–1191`, `SpendYoYHandler._for_window:1285–1313`, `MostBoughtItemsHandler:643–648`, `budget.period_spent:129–153`, `GetBudgetHistoryHandler:385–425` | "Finished lists in the window → ticked, priced lines → actual→picked ladder" is written **seven** times (five in core SQL, two through the repository), with `deferred_by_budget` honoured only by budget. One rule, one function. | `shopping_lists/_line_price.spend_lines(repo, since, until) -> list[SpendLine]` (list id, completed_at, stock item, product, qty, unit_price, store rungs), used by all seven. Test T3 pins total parity across reports. | execute |
| 12-R11 | `SpendYoYHandler._for_window` ≡ `SpendByCategoryHandler.handle` + `until` | YoY re-implements the category aggregation. | YoY calls the category handler twice over `spend_lines`. | execute (with R10) |
| 12-R12 | `ItemPriceMoversCard:172–179`, `KitchenMemoryCard:195–202`, `ReportsLede:44–61` | `WINDOW_WORDS` ×3 (+ `PRIOR_WORDS`), with one divergence already ("all time" vs "since you started logging prices"). | `helpers/reportRangeWords.ts`. | execute |
| 12-R13 | `ReportsPage.vue:287–298` | `colourFor` hashes into six `paletteToken('--chart-N', '#hex')` fallbacks (R-002 literals; FU-843 collision at six). | `useThemePalette.categoricalColour(key)` as the one ramp (check the dashboard for a twin at Stage 2); FU-843 widens the ramp. | execute |
| 12-R14 | `waste.py:540–544` | `_rank_buckets` compares `occurred_at` by parsing its own ISO string back per event. | Keep datetimes; serialise once at the end. | execute |
| 12-R15 | `waste.py:343–352` | `BulkLogWasteResponse` uses `None` defaults + `__post_init__` to mean "empty list". | `field(default_factory=list)` (R-008). | execute |
| 12-R16 | `budget.py:286, 314–321, 437` | `getattr(offer, "_product_id", None) or getattr(offer, "product_id", None)`; `_current_user_id` (FU-654); `from flask import request` inside a function though imported at module scope. The `_product_id` private-attr read appears **18×** across features (`# noqa: SLF001`). | Local: FU-654 helper, drop the re-import; expose a public mapped `product_id` on the offer entities — cross-cutting (E1). | execute (local) + FU |

### C3. Dead code / unused fields / unread endpoints
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 12-R17 | `waste.py:189–201, 262–282`; `wasteApiService.ts:110–113, 144–147` | `GET /waste/rescue` and `GET /waste/events` have **no HTTP consumer** — the assistant tool calls `GetWasteRescueHandler` directly and the SPA never calls `getRescueAsync`/`listEventsAsync` (`deleteEventAsync` is used by Undo). | Delete the two client methods and the two routes; keep the handler (the tool and `get_recipes`' at-risk rule use it); convert `test__get_waste_rescue__*` to handler tests. | execute (R-057) |
| 12-R18 | `budget.py:239, 338–339, 365, 449–450` | `handle()` is typed `| None` and never returns `None` → two dead `if dto is None: return unauthorized()` branches. | Tighten the types; drop the branches. | execute |
| 12-R19 | `reports.py:789–800`, `reportsApiService.ts:95–102` | `savings-captured.lists[]` is never read by the SPA (`SpendCard` uses the two totals). | Leave until FU-831 (it reshapes savings); then drop or consume. | conditional (FU-831) |
| 12-R20 | `KitchenMemoryCard.vue:313–325`, `WasteCard.vue:198–215` | `.km-skeleton`/`.km-skeleton__col` rules duplicated inside the media query; `.wr-reason` declared twice. | Tidy. | execute |
| 12-R21 | `MarkAsWastedDialog.vue:92–139` | `var(--text-sm, 0.875rem)` — the token is undefined (chunk 5 confirmed) so the fallback always paints; `var(--space-*, Npx)` / `var(--radius-md, 8px)` fallbacks (D-017 no-fallback convention); `outline: none` on `:focus-visible` (FU-841, A6). | Execute FU-841 + tokens (`--font-size-sm`, no fallbacks). | execute |
| 12-R22 | `test_reports_router.py:45` | Goes with 12-R1. | — | execute |

### C4. Componentisation opportunities (R-001)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 12-R23 | `ReportsPage.vue:229–257` vs `DashboardPage` `loadSlot`/`slotErrors` | Per-card failure machinery duplicated (named in-file as FU-844). | `composables/useSlotLoader()`; FU-832's `useCardLayout` can sit beside it. | execute |
| 12-R24 | `reports.py` (1,617 lines, 10 handlers) | Ten reports + their shared range/bucket helpers in one module; the module docstring still says "all six reports". | Split: `features/reports/{_ranges,spend,memory,price_movers,price_drops}.py`; `_ranges.py` is also 10-R15's home. Mechanical; tests re-import. | execute |

### C5. Placement / layering (R-003, R-005)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 12-R25 | `reports.py` (all handlers) | Core `select()` over mapped classes rather than the repository ports — the accepted aggregate-report carve-out (10-R17 treatment), but undeclared. | One `# R-005 carve-out: multi-table aggregates` note at module top (per split module). | execute (comment) |
| 12-R26 | `reports.py:1478–1495` | `ItemPriceMoversHandler` loads every observation for every item and range-filters in Python (documented SQLite-tz reason). | Fine at household scale; the comment already explains it. | waive |
| 12-R27 | `waste.py:142–148` | Rescue loads every recipe with ingredients (11-R41 class). | With 11-R41's ingredient-by-item query. | FU (with 11-R41) |
| 12-R28 | `waste.py:269–280` | `list_waste_events` loads all events then sorts/limits in Python. | Moot after 12-R17; else `order_by`/`limit`. | execute (via R17) |
| 12-R29 | `waste.py:481–483` | `BulkDeleteWasteHandler` calls `save_changes()` inside the loop — N commits (R-031). | One save after the loop (the update handler commits its own restore). | execute |

### C6. Naming & idiom
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 12-R30 | `budget.py:68–72` | "Doesn't deserve timezone gymnastics" two lines above code that already uses `household_today` — and the gymnastics are exactly what 12-R2 needs. | Rewrite with R2. | execute |
| 12-R31 | `reports.py:1–40` | Module docstring lists six endpoints of eleven; the "Conventions" block is right, the inventory isn't (R-019). | Rewrite with R24. | execute |
| 12-R32 | `BudgetSettings.vue:124–128` | `font-size: 0.8125rem`, `margin-top: 4px` raw (D-003/D-017); uses `DoraSegmented` while Reports uses `BaseSegmented` (two segmented controls — chunk 13, 12-D5). | Tokens here; the merge is chunk 13's. | execute (tokens) |

### C7. Efficiency
Covered by 12-R26/27/28/29. The spend reports are O(lines in window) with a handful of bulk lookups — correct shape.

### C8. Design-level findings — out of Stage-2 scope
| Id | Finding | Recommendation |
|---|---|---|
| 12-D1 | Reports has **no owner feedback** (the section is `?`); the in-session review is the only source and the page was rebuilt against it. The "90% happy" statement covers pages the owner walked — confirm Reports was one before Stage 2 touches layout. | Owner: one line, "Reports as it stands is in the 90%". |
| 12-D2 | Savings baseline (FU-831, ADR-068) is decided-not-built; 12-R10 should land first so FU-831 edits one function. | Sequence: R10 → FU-831. |
| 12-D3 | Waste proposal §13: A (Undo restores expiry) built ✅; B (cookbook filter name) and C (sort default) were impl-time picks — chunks 1 and 5 own confirming them. | Record only. |
| 12-D4 | Budget weeks start Monday, fixed; no household first-day setting exists anywhere. Fine for AU; a US household would want Sunday. | One AppSetting if asked; not now. |
| 12-D5 | `DoraSegmented` (settings, 9 uses) and `BaseSegmented` (pages, 13 uses) are two segmented controls (R-001). | Chunk 13 (settings shell) merges; note here because the budget page is the only money surface on the Dora one. |

### C9. Hand-rolled-vs-library verdicts
| Surface | Hand-rolled | Verdict |
|---|---|---|
| Kitchen-memory column track (CSS bars) | Yes | **keep** — review §4.6 chose no chart library; integers as columns, `role="img"` label. |
| `ProportionBar` (spend composition) | Yes (shared) | **keep** — one implementation with the shopping list. |
| `PriceHistoryChart` drill-in | Shared | **keep** (chunk 10 verdict). |
| Range/bucket maths | Yes | **keep**, consolidated in `_ranges.py` (12-R24/10-R15). |

### C10. Standards drift (R-0NN)
| Id | Rule | Where | Verdict |
|---|---|---|---|
| 12-R2 / 12-R3 | R-021 household time | budget bounds + history; reports range anchors | execute |
| 12-R1 | R-032 noload reads | stock-value handler | execute (delete) |
| 12-R6 / 12-R9 / 12-R10 / 12-R11 / 12-R12 / 12-R13 | R-003 one source | reason tiles ×2, expiry horizon ×3, spend-lines ×7, range words ×3, colour ramp | execute |
| 12-R8 / 12-R30 / 12-R31 | R-019 comments ≠ code | budget service doc, period comment, reports docstring | execute |
| 12-R15 / 12-R16 | R-008 idiom | `__post_init__` lists, getattr chain, re-import | execute |
| 12-R1 / 12-R17 / 12-R19 | R-057 contract inventory | stock-value, waste rescue/list, savings lists | execute / conditional |
| 12-R29 | R-031 one commit | bulk delete | execute |
| 12-R7 | D-006 formatting authority | window label | execute |
| 12-R21 | D-017 / A6 / FU-841 | mark-wasted tiles | execute |
| 12-R25 | R-005 (declared carve-out) | reports core SQL | execute (comment) |
| 12-R16 | FU-654 | `budget.py:314` | execute (sweep) |
| 12-R32 | D-003 / D-017 | `BudgetSettings.vue` raw rem/px | execute |

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- Spend legend's unassigned dot: `--border-strong` + hatch (D-001 texture-not-hue) ✅ reference use.
- Categorical ramp `--chart-1..6` with hex fallbacks (12-R13 / FU-843).
- Kitchen-memory bars `--brand-primary`; Price changes uses arrows, no red/green (review §4.5.3) ✅.
- `MarkAsWastedDialog` tiles paint `--border-default`/`--surface-sunken` ✅ after FU-747; focus ring missing (FU-841).

---

## D. Test plan — Reports / Waste / Budget

**Existing (keep):** pytest `test_reports_router.py` (36 — every report incl. money gates, range window, movers' edge rules), `test_reports_memory.py` (23 — range parsing, bucket sizing, YoY maths, stubbed), `test_budget_router.py` (11), `test_budget_spend_excludes_unticked.py` (3), `test_waste_router.py` (14), `test_spend_by_store.py` (1), `test_query_budgets.py` (4 — select-count flatness); no vitest (the cards are presentation over server numbers).

**Proposed (lean):**
| # | Pins | Layer | Why |
|---|---|---|---|
| T1 | A list completed at 08:00 Monday in a +10 household counts in that week's `period_spent` and lands in history row 0; the same instant in UTC terms (Sun 22:00) does not move it | pytest (`test_budget_router`) | 12-R2 — money, silent, periodic |
| T2 | Most-bought counts ticked lines only | pytest | 12-R4 |
| T3 | On one fixture, spend-by-store `total_spend` == spend-by-category `total_spent` == savings `total_spent` == `period_spent` for the matching window | pytest | 12-R10 parity — the contract the extraction exists to pin |
| T4 | `range-window.end` equals the household date (install tz +10, now 23:30 UTC → tomorrow's local date) | pytest | 12-R3 |
| T5 | Waste rescue `estimated_value` equals the item's `your_prices` baseline (or the field is gone) | pytest | 12-R5 |
| — | Card rendering, filter tiles, chart drill-in, window label format | — | **no automated test** — drive once, delete the DORA_VERIFY line |

**DORA_VERIFY additions (Stage 2 close):** budget card after a first-morning shop; window label near midnight; "Bought too much" on both surfaces; `/reports` with money off shows two cards; Undo on a waste log restores the expiry; stock-value endpoint 404s.

---

## E. Proposed follow-ups (orchestrator allocates ids)

| # | Title | Type | Resolution point | Source |
|---|---|---|---|---|
| E1 | Public `product_id` on `ProductOffer`/`ProductHistoricOffer` mappings — retire 18 `_product_id` private-attr reads (`# noqa: SLF001`) | leftover | chunk 20 | 12-R16 |
| E2 | Savings `lists[]` DTO: consume or drop | leftover | with FU-831 | 12-R19 |
| E3 | Merge `DoraSegmented` into `BaseSegmented` | leftover | chunk 13 | 12-D5 |
| E4 | Owner confirms the four-card Reports shape is in the "90%" | decision | now | 12-D1 |
| E5 | Rescue recipe scan via ingredient-by-item query | leftover | with 11-R41 | 12-R27 |

**FUs this chunk advances at Stage 2:** FU-841 (→ resolve), FU-843 (ramp via R13), FU-844 (→ resolve via R23), FU-654 (+1), FU-873 (same trap, different file — reference). FU-831/832/898/907 untouched (decided, their own jobs).

---

## F. Summary for the register

- FST rows: 13 golden + 15 edge + 5 gate · Help entries: **10 new** (a new **Reports, budget & waste** group — none existed) + DoraBot paragraph · Review findings: **32** (`12-R1..R32`) + 5 design (`12-D1..D5`) — **28 execute**, 1 conditional, 1 FU, 1 waive · Tests: 5 proposed (pytest) · FUs: 5 proposed, 4 existing advanced.
- One-line: the rebuilt Reports page is the healthiest surface so far — honest empties, per-card failure, server-owned numbers — and the defects left are all in the plumbing: the household budget is bounded in UTC so early-period shops fall into the previous week, "Bought most" counts things never bought, the spend rule is written seven times, and an endpoint nobody calls is also broken by the noload trap.

### Feedback coverage — `# REPORTS` / `# WASTE` are empty (`?`); the owner's review and the waste proposal stand in

| # | Owner question / decision | Where it lives now | State |
|---|---|---|---|
| RV3.1 | Spend-by-store colouring vs shopping list | `brand_colour` on the row, `storeColour` shared (FU-814) | ✅ done |
| RV3.2 | Dashboard-style opt-in cards on Reports | FU-832 `useCardLayout` decided, not built | 🔵 |
| RV3.3 | Stock value over time — cut | Card cut; endpoint orphaned **and** noload-broken → 12-R1 delete | ➗ |
| RV3.4 | Wastage widget grows too big | 6-row cap + "+N more" | ✅ done |
| RV3.5 | "Keeps running out" / "Mark all essential" | Both cut (2026-09-27) | ✅ done |
| RV3.6 | What spend-by-store is based on | Five-rung ladder via `resolve_store_id`, coverage line (FU-815) | ✅ done |
| RV3.7 | Savings captured — gated? weak metric | Products-gated support line; baseline change = FU-831 | ➗ |
| RV3.8 | Point of "Meals cooked" | Kitchen memory: headline, repertoire, columns | ✅ done |
| RV3.9 | "Category" → "stock group" | "By group" axis; server label unchanged (D5 answered inline) | ✅ done |
| RV3.10 | Price trends broken on SQLite | `_as_utc` everywhere (FU-813); product chart cut from Reports | ✅ done |
| RV3.11 | All setups (money off etc.) | Gates + 403s (FU-816); two cards survive | ✅ done |
| RV6.1–20 | Twenty engineering findings | 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20 closed by the rebuild; **17** (range) moot (card cut) | ✅ done |
| RV8 D1–D7 | Open decisions | All closed/spawned (FU-831/832/833; D5–D7 inline) | ✅ decided |
| WP D1–D4 | Reason-only modal, tile grid, 5 s Undo, five reasons | `MarkAsWastedDialog` + `useLogWaste`; labels diverge on the report → 12-R6 | ➗ |
| WP D5–D7 | Stock sort, cookbook filter, no used/frozen actions | chunks 5/1 own; recorded | ✅ (elsewhere) |
| WP D8 | `frequent_waster` deep link → item detail | chunk 9 (suggestions) | ✅ (elsewhere) |
| WP D9–D11 | Dashboard Use-soon cut; `/waste` route gone, no redirect, no nav slot | `routes.ts:169–173` | ✅ done |
| WP D12 | **No Reports waste card** | **Reversed** — a Waste card exists (owner 2026-09-27 reason tiles). Record the reversal in the proposal. | 📝 doc |
| WP D13 | Slim event schema | `StockItemWasteEvent` reason-only | ✅ done |
| WP D14 | Dora Score reassessment | FU-302 / chunk 8 | — |
| WP §13 A | Undo restores expiry | Single + bulk ✅ | ✅ done |
| Cross | Money switchable off app-wide (feedback L254) | FU-816 gates + 403 | ✅ done |

`docs/02_feedback/COVERAGE_GAPS.md:266` already points Reports at the review; add this chunk file beside it. `PROPOSAL_WASTE_MINIMISATION.md` D12 needs a one-line reversal note.
