# Chunk 08 — Dashboard

**Analysed:** 2026-10-23 · **Analyst session:** finalisation overnight run (solo, no subagents)
**Scope (from PLAN §4):** the home page — hero (greeting · message of the day · hint callout · Cards menu), the skip-wizard reminder, the eight registered cards (Kitchen health · Next to cook · Use it up · What's coming · Restock radar · My stock · My budget · Price drops), the per-user layout (order + hidden, server-persisted), and the dashboard router (`/summary`, `/dora-score`, `/restock-radar`, `/use-it-up`, `/usage-stats`) plus the `dora_score` domain core.
**Boundaries:** `/alerts/upcoming` (the calendar's feed) and the bell are Chunk 9; `/reports/price-drops` and `ProductThumb` are Chunk 10; `/budget/status` is Chunk 12/13 (read here only as a consumer); the About page's usage block is Chunk 13 (its endpoint lives under this router and is reviewed here); `AddToListButton` / `StockLevelDot` are Chunk 3/5 components; the onboarding restart call is Chunk 14.

## 0. Reading list + files walked

**Planning docs consulted:** `IMPL_PLAN_DASHBOARD_REBUILD.md` (§2 decisions, §3 phases — all DONE, §5 coverage table, §6 DoD) · `DASHBOARD_PAGE_REVIEW.md` (§3 questions, §4 design pass, §6 engineering findings 1–28, §7 sequencing) · feedback `[06-Jun-2026]` § DASHBOARD (L48–61) + L176, L272, L480 · `DORA_VERIFY.md` Dashboard sections (L187, L740 — not pre-scanned; opened because the owner batches are the surface's recent history) · open FUs: FU-899, 898, 896, 871, 870, 868, 837, 836, 832, 844, 700, 654, 671, 908.

**Files walked (every file opened, with line count):**

| File | Lines | Role |
|---|---|---|
| `dora_api/features/dashboard/get_dashboard_summary.py` | 330 | one-round-trip payload (stock counts · upcoming meals + cook verdicts) |
| `dora_api/features/dashboard/get_dora_score.py` | 220 | P8-08 gather + endpoint |
| `dora_api/domain/dora_score.py` | 372 | pure score core (4 components, trend) |
| `dora_api/features/dashboard/get_restock_radar.py` | 206 | recently low/out, `is_planned` |
| `dora_api/features/dashboard/get_use_it_up.py` | 187 | near-expiry ⨝ recipes |
| `dora_api/features/dashboard/get_usage_stats.py` | 129 | About page cumulative counts |
| `dora_api/features/meal_plans/daily_brief.py::slot_order_map`, `domain/stock_status.level_for_status` | — | shared helpers the summary reads |
| `web_app/src/pages/DashboardPage.vue` | 1687 | hero · layout machinery · slot loaders · calendar cells |
| `web_app/src/components/dashboard/DashboardCard.vue` | 139 | shared shell (also Reports') |
| `web_app/src/components/dashboard/CardLoadError.vue` | 101 | per-card failure state |
| `web_app/src/components/dashboard/DoraScoreCard.vue` | 411 | ring + per-signal boxes |
| `web_app/src/components/dashboard/BudgetCard.vue` | 185 | spend vs period |
| `web_app/src/components/dashboard/NextToCookCard.vue` | 175 | next meals + Cook |
| `web_app/src/components/dashboard/PantryDonutCard.vue` | 262 | SVG donut + legend |
| `web_app/src/components/dashboard/PriceDropsCard.vue` | 154 | new-low rows |
| `web_app/src/components/dashboard/RestockRadarCard.vue` | 201 | dot · name · Planned · when · cart |
| `web_app/src/components/dashboard/UseItUpCard.vue` | 237 | items + recipes |
| `web_app/src/components/dashboard/WhatsComingCard.vue` | 394 | 14-day grid + day panel |
| `web_app/src/composables/useDoraScore.ts` | 76 | singleton cache |
| `web_app/src/helpers/dashboardCards.ts` | 174 | card registry + `DEFAULT_VISIBLE_COUNT` |
| `web_app/src/helpers/dashboardGrid.ts` | 102 | run-parity column classes |
| `web_app/src/helpers/dashboardMessages.ts` | 215 | welcome + hint pools, gated |
| `web_app/src/css/dashboardCards.scss` | ~160 | shared card-body primitives |
| `web_app/src/models/dashboard.ts` (76), `models/doraScore.ts` (44), `services/api/dashboardApiService.ts` (118) | — | types + client |
| `web_app/src/pages/settings/AboutSettings.vue` L296–320 | — | usage-stats consumer |
| tests: `test_dashboard_router.py` (12), `test_dashboard_insight_cards.py` (9), `test_dora_score.py` (9 classes), vitest `dashboardCards.spec.ts`, `dashboardGrid.spec.ts`, `dashboardMessages.spec.ts`, `cardLoadError.spec.ts` | — | coverage inventory |

## A. Full Systems Test — Dashboard

### A1. Preconditions
- Dense seed; money **on**, products **on**, batch cooking **on**; a budget set with a few finished shops this period; ≥1 item expiring inside the household's `expiring_soon_window_days`; a plan for the next fortnight with a cooked batch covering some days; one item that went Out in the last week and is needed by a planned meal; a tracked product at a new low.
- A second browser profile (or a fresh user) with no saved layout.

### A2. Golden path
1. Sign in → `/` → hero: mascot · *Good afternoon, Ben* (capitalised username) · a weekday-flavoured message that is the same all day and different tomorrow · an info callout with a hint that never mentions money/products on an install with them off · *Cards* button (icon-only on a phone).
2. Grid loads from a content-shaped skeleton; **seven** cards render by default in registry order (Kitchen health first), *Price drops* is opt-in; no card ever sits beside dead air (odd runs widen their last card).
3. **Kitchen health**: ring + number, *last 30 days*, a ± trend chip only when |delta| ≥ 2; four boxes (Waste · Budget · Freshness · Plan coverage), a dormant one reads *not counted* with a dashed edge; money off → three boxes, no Budget row at all.
4. **Next to cook** (batch household): only meals the pool is short of or marked fresh, deduped by recipe, ≤3, each *Today/Tomorrow/Wednesday* with a *Missing N* / *N to link* badge only when there's work to do; **Cook** opens cook mode at the batch's yield; all covered → *Nothing to cook. You have ready servings…*.
5. **Use it up**: ≤5 items expired-first with *expired 2 days ago / today / 3 days left*; *Recipes using these* ≤3 ranked by how many they clear, *uses 2 expiring*; **See more** → `/cookbook?expiring=1`.
6. **What's coming**: legend (meals · expiry · shopping), 14 cells with weekday + day number + up to three dots, today outlined, selected filled; tapping a day shows its meals (slot chip), expiring items and shopping lists as tappable rows.
7. **Restock radar**: ≤6 rows, most recent band change first, `StockLevelDot` + name + *Planned* chip (tooltip) + *3 days ago* + the stock row's own cart button; an item low since March is absent and the empty copy names the 30-day window.
8. **My stock**: donut grows with the card (132–220px), centre total, legend; low/out legend rows and segments deep-link to `/stock?level_id=…`; switch theme → the donut recolours without a reload.
9. **My budget**: *$X of $Y this week* · *$Z left/over* · progress bar · a tinted *$N still to buy on your open lists* row; no budget target → *$X spent this week*.
10. **Cards** menu → toggle a card off (grid repacks, count line updates), move one up/down (tap) or drag it (desktop), reload → the order persists; sign in as the second user → defaults.
11. Turn *Price drops* on → the card appears (products on) with thumb · store logo · linked item link · price/was · *N% off*.
12. Kill the API, retry a slot → the card shows *I couldn't load …* with **Try again**, never its empty state; summary failure → page banner with its own *Try again*.

### A3. Edge cases
- Money off → `my_budget` vanishes from the grid **and** the Cards menu; Kitchen health scores on three signals; hint pool drops the budget hint; products off → `price_drops` gone likewise.
- Cold load / PWA start → gated loaders re-fire when the health flags land (FU-586 watches); a flag that lands late must not leave Budget blank.
- Brand-new install → Kitchen health *appears once you've tracked a few stock items* (composite null), every other card in its positive empty state; the hero's hint rotates over the ungated pool.
- Saved layout naming retired ids (`attention`, `savings`, …) → filtered on read; a **new** default-on card is appended at the **end** for existing users although the comment promises its registry slot (08-R7).
- All cards hidden → the *All cards are hidden* banner with the Cards icon inline.
- `trend_delta` is None on an install younger than 37 days → no chip; `plan_coverage` never moves the arrow (FU-870, accepted).
- Household east of UTC at 23:30 local → Kitchen health's freshness "as of" is the **UTC** date (08-R3); the calendar's *today* ring is the **browser's** date while the cells start at the household's (08-R8).
- A stock item with no level (level deleted) → `/dashboard/restock-radar` **500s** (08-R1).
- Restock radar: two items levelled in the same write keep A–Z order between loads (two-pass sort, pinned).
- Use it up with `expiring_soon_window_days = 30` → the card says *30 days* nowhere — the window is only used for the query; copy is fine ("about to go off").
- Skip-wizard reminder: shows for 24 h after *Skip everything*, *Hide* is per tab, *Continue* restarts onboarding (`POST /onboarding/restart` + auth refresh) and routes to `/welcome`.
- Offline: eight parallel requests fail → eight in-card errors, one banner; no toast pile-up (by design).

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (positive empties; score null) | ✓ (A2) | ✓ (money/products off → 6 cards, 3-signal score) | ✓ (reorder/drag/opt-in) | – (no install-wide dashboard setting) | ✓ (layout per user) | – | – |

### A5. Load-bearing conditions
- `cardRendered` is the **one** predicate both the template `v-if` and the grid-parity maths read; a second hide-when-empty condition at a call site re-creates the dead-air bug.
- `DEFAULT_VISIBLE_COUNT = 7` is a resolved decision held by `dashboardCards.spec.ts`; a new card without `defaultHidden` fails the spec on purpose.
- `loadAll` force-refreshes the score (`refreshDoraScore`) because the composable's 5-min stale window hid budget-period changes; the four mutations the composable's header names never invalidated it (FU-896).
- The summary's `_cook_verdicts` reads the planner's pool model (`planned_meals`) — the dashboard, the planner chips and `/shortfall` are three readings of one allocation.
- `resolve_levels_by_item` returns `None` for an unlevelled item and every consumer must guard it — one here doesn't (08-R1).

### A6. Release-gate rows
- Default install, 1280px: seven cards, zero dead regions; 375px: one column, Cook/Cards icon-only, no horizontal scroll.
- Money off: no Budget card, no Budget row in Kitchen health, no money hint in a week of reloads (`dashboardMessages.spec` covers the pool; the card gate needs eyes — FU-868).
- Change the budget period in Settings, return within five minutes → Kitchen health's Budget row reflects the new window.
- Reorder two cards, reload, second device → same order.

## B. Help content — Dashboard

### B1. Current help audit
HelpPage has **no Dashboard group**; the only mention is inside a meals entry ("the dashboard shows the next entry on the home page" — stale: the "Next up" callout is gone). The hero hint pool (21 hints, fact-checked 2026-09-04) is the surface's de-facto help and is good; it should stay the *rotating* channel while the guide carries the full explanations. DoraBot's corpus (L14–15) still describes "quick stats, items needing attention" — both cards were cut on 2026-09-04.

### B2. Help entries
New group **Dashboard** (icon `ICONS.dashboard`), `path: '/'`:

1. **Your dashboard** — "The home page is a set of cards you own: **Cards** (top right) shows, hides and reorders them, and the layout is saved to your account, so it follows you between devices and each person in the household has their own. A card whose feature is off for the install — My budget without money features, Price drops without products — is hidden from the grid and the menu rather than shown empty. Everything refreshes each time you come back to the page; there is no refresh button because there is nothing it would add."
2. **Kitchen health** — "One number for how the kitchen is doing, from four signals over the last 30 days: **Waste** (every logged waste event costs ten points), **Budget** (how far over this period's target you are; skipped without a target, absent entirely when money features are off), **Freshness** (the share of expiry-tracked items that are past their date) and **Plan coverage** (how many of the next week's planned meals you could cook right now). A signal with nothing to score says *not counted* and is left out of the average rather than scored zero. The small arrow compares today's number with the same number a week ago; plan coverage looks forward, so it never moves the arrow."
3. **Next to cook** — "The next meals somebody actually has to cook. In a fresh-cooking household that is simply the next planned meals, in day then meal-slot order. With batch cooking on, meals the frozen pool already covers are left out, so the card shows only what the pool is short of plus meals you marked *cook fresh*. A badge appears only when there is work to do first — *Missing 2* or *3 to link*. **Cook** opens cook mode at the batch's yield, the same figure the planner uses."
4. **Use it up** — "What's about to go off, expired first, inside the *expiring soon* window set under Settings → Alerts — and the recipes that would use it, ranked by how many of those items each one clears. *See more* opens the cookbook filtered to recipes using expiring ingredients. Only required ingredients count; an optional one is not a reason to cook something."
5. **What's coming** — "A fortnight at a glance. Each day carries up to three dots: green for planned meals, red for items expiring that day, blue for a shopping list dated that day. Tap a day for the list. It reads the same feed as the bell's upcoming events, so the two never disagree."
6. **Restock radar** — "Items that went **low or out in the last 30 days**, most recent first, with the app's level dot, how long ago it changed, and the same cart button the stock rows have. *Planned* means a meal in the next fortnight still needs it. Something that has been out for months is not shown here — it is on the Stock page filtered by level, which is where everything you're out of lives."
7. **My budget** — "What you've spent this period against the household budget, with what's left or how far over you are, and underneath, the total still to buy on your open lists — a forward-looking figure, not spend. Spend counts ticked lines on finished shopping lists with a price. Set the budget and its period under Settings → Money."
8. **Price drops** (opt-in, products) — "Tracked products at a genuine new low — lower than any price Dora has seen for them — with the store and the stock item they're linked to. It only ever claims a drop against its own history, never against a retailer's ticket price."
9. **The message of the day** — "The line beside Dora is a weekday-flavoured greeting that stays the same all day, and the callout under it is a tip about something in the app that is easy to miss. Tips about money or products are not shown on an install that has those features off."

Also: fix the stale meals sentence at `HelpPage.vue:459` ("the dashboard shows the next entry on the home page" → "Next to cook on the dashboard lists the next ones to cook").

### B3. DoraBot corpus delta
Replace `app_knowledge.py` L14–15 with: *"Dashboard (home): Kitchen health score (waste, budget, freshness, plan coverage over 30 days), Next to cook (batch-aware), Use it up (expiring items + recipes that use them), What's coming (14-day calendar of meals, expiries, shopping), Restock radar (recently low/out, 'Planned' when a meal needs it), My stock (level donut), My budget (money on) and opt-in Price drops (products on). Users show, hide and reorder cards from the Cards menu; the layout is per user."*

## C. Senior review — Dashboard

Verdict key: **execute** · **FU** · **waive** · **conditional**. Sizes S/M/L.

### C1. Bugs (verified or high-confidence latent)
- **08-R1** · `get_restock_radar.py:149–151` builds `recorded_by_item = {item_id: level.sequence for item_id, level in levels.items()}` — `resolve_levels_by_item` returns `None` for an item with no level (its docstring says so; `get_planned_demand.py:39–42` and `get_buy_verdict.py:823–827` both guard `if level is not None`), so one unlevelled item 500s the whole card. Latent today because create requires a level, but a deleted level nulls the FK. · **Exact change:** add `if level is not None`. · S · guard: `test__restock_radar__item_without_level__is_skipped_not_500`. · **execute**.
- **08-R2** · `/dashboard/summary` still ships two sub-objects nothing reads: `recipes.total` (the TS comment says the hero's "recipe book's empty" nudge reads it — that line was cut 2026-09-04; AboutSettings reads `/usage-stats` now — grep `summary.*recipes|recipes\.total|shopping_lists\.total` in `web_app/src` → `models/dashboard.ts` only) and `shopping_lists.total`. Two `count()` queries per load for nobody — the FU-826 class, second round. · **Exact change:** drop `RecipeSummary`/`ShoppingListSummary` + their TS types; delete `test__dashboard_summary__CreatingRecipe__RecipeTotalIncreases`; update the shape test. · S · **execute**.
- **08-R3** · R-021 — `get_dora_score.py:62 now = datetime.now(timezone.utc)` and `L169 as_of = end.date()`: freshness grades "expired as of **UTC** today" while every other dashboard date is household-local; late evening east of UTC an item expiring today isn't expired yet, and the lagged window's day boundary drifts the same way. · **Exact change:** `as_of = household_today(repo)` for the current window and `household_today - 7` for the lagged one (keep the UTC instant for the event-count windows). · S · **execute**.
- **08-R4** · `get_dora_score._gather_inputs` (L170–175) loads **every** `StockItem` into memory to count two things, and runs twice per request (review finding 25 — still open). · **Exact change:** `repository.get(StockItem).count(EXPIRY_DATE.is_not_null())` and `.count(EXPIRY_DATE.lte(as_of))`; drop the list. The handler's `is_expired_on` inline duplicate goes with it (use the domain helper or delete it — `dora_score.is_expired_on` has no production caller; grep at execution). · S · **execute**.
- **08-R5** · `GetDoraScoreHandler.handle(user_id)` → `_gather_inputs(user_id, …)`: `user_id` is never read (the score is household-wide); the route's `_current_user_id()` (L197–204) is another FU-654 copy that exists only to feed an unused parameter and a log line. · **Exact change:** drop the parameter; log via 02-R12's `current_user_id()`. · S · **execute**.
- **08-R6** · `get_usage_stats.py` bypasses the repository with raw `db.metadata.tables` + `db.session` for six plain counts that `repository.get(X).count()` already does (R-005 repository-routed access; the summary two files over does it the portable way), and its `_total_spend` re-states `/reports/spend-by-store`'s rule as a second SQL copy with a docstring promising they match (R-003). · **Exact change:** counts through the repo; extract `lifetime_spend(repo)` into `shopping_lists/_line_price.py` (beside `line_paid_unit_price`) and call it from both this handler and spend-by-store's total. · S/M · **execute**.
- **08-R7** · R-019 (comment ≠ code), review finding 21 — `DashboardPage.vue:758–760`: "Append any card missing from the stored order … **at its CARD_DEFS position**" but the loop `order.push(def.id)` appends at the **end**. Every user with a saved layout got Kitchen health **last**, not first, when it shipped — the opposite of the 2026-09-08 ordering decision. · **Exact change:** insert at the registry index (`order.splice(idx, 0, def.id)` where `idx` is the position after the nearest preceding known card), and pin it in a spec. · S · **execute**.
- **08-R8** · R-021 — `DashboardPage.vue:1262 todayIso = isoOf(new Date())` (browser) decides the calendar's *today* ring while the cells start at `/alerts/upcoming`'s household-local `start`; `greeting` likewise uses the browser hour (acceptable — the greeting is about the reader's clock). · **Exact change:** `/alerts/upcoming` already carries `start`; mark `isToday` from a server `today` field (add it to the DTO, Chunk 9) rather than the browser. · S · **execute (with Chunk 9's `/alerts/upcoming` pass)**.

### C2. Redundancy / DRY (R-001, R-003)
- **08-R9** · Three relative-day formatters: `RestockRadarCard.whenLabel` (L128–136: today/yesterday/N days ago/last week/N weeks ago), `helpers/relativeTime.ts` (Nm/Nh/Nd/Nw ago), and `UseItUpCard.whenLabel` (days left — a different sentence, keep). · **Exact change:** `relativeTime(iso, { style: 'coarse' })` in the shared helper; the radar card calls it. · S · **execute**.
- **08-R10** · `useDoraScore.ts` is the third hand-rolled module cache (with `usePantryBeliefs`, `usePlannedDemand` — 07-R6); same `fetchedAt`/`inflight`/`STALE_AFTER_MS`/`refresh` shape, singleton flavour. · **Exact change:** instantiate from 07-R6's `createOverlayCache` (single-value variant) — and delete `invalidateDoraScore` (FU-896: never had a caller; the header describes behaviour that doesn't exist). · S · **execute (resolves FU-896)**.
- **08-R11** · `DashboardCard.to` prop, `.dora-card-clickable` rules and `:deep(.dora-card-action)` — zero consumers app-wide (FU-899; grep `to=` on `DashboardCard` in `pages/` + `components/reports/` → none; `.dora-card-action` → none). · **Exact change:** drop the prop, the `<component :is>` root (plain `<article>`), and the three rule blocks; keep `#action`. · S · **execute (resolves FU-899)**.
- **08-R12** · Hard-coded English weekday labels `DOW_LABELS = ['Sun', …]` (`L1257`) beside `formatRelativeDay`, which is locale-aware (R-056 one regional convention). · **Exact change:** `weekdayShort(date)` from `useDateFormat` (Intl `weekday: 'short'`). · S · **execute**.
- **08-R13** · `BudgetCard.periodWord = period.replace('ly', '')` — string surgery on a closed set (`BudgetPeriod`) that happens to work for weekly/monthly/fortnightly. · **Exact change:** a `Record<BudgetPeriod, string>` map. · S · **execute**.
- **08-R14** · `calendarCells` (L1258–1298) is a pure 40-line transform of the upcoming DTO living in the page. · **Exact change:** `helpers/dashboardCalendar.ts` `buildCalendarCells(upcoming, today, days)` with a vitest (the parity helper already set the precedent). · S · **execute**.

### C3. Dead code / unused fields / unread endpoints
- **08-R15** · `models/dashboard.ts:1–12, 26–29` comments still say AboutSettings reads the summary and the hero reads `recipes.total` — both false (08-R2). · S · **execute with 08-R2**.
- **08-R16** · `get_dashboard_summary.py:235–241` comment: "Still needed: each upcoming meal-plan entry below carries a per-recipe `missing_count`" is right, but the function computes cookability for the **whole cookbook** to grade ≤7 entries (FU-908 is the identical finding on the plan endpoint). · **Exact change:** when `load_recipe_cookability` gains a `recipe_ids` filter under FU-908, pass the upcoming entries' recipe ids here and in `get_dora_score` (two more callers). · S (given FU-908) · **execute via FU-908**.
- **08-R17** · `dashboardCards.ts` carries ~45 lines of "cards deleted in the 2026-09-04 / 09-08 batches" prose. Valuable once; now it is what `DORA_WORKLOG`/`CHANGELOG` hold. The retired-id list that `dashboardCards.spec.ts` asserts must stay (it is the mechanism). · **Exact change:** keep `RETIRED_CARD_IDS` as an exported constant with one line per id; move the narrative to the worklog. · S · **execute**.

### C4. Componentisation opportunities (R-001)
- **08-R18** · FU-832 (decided, not started): extract `useCardLayout()` from `DashboardPage.vue:727–943` — `parseLayout`, order/hidden refs, `persistLayout`, `cardAvailable`/`isCardVisible`/`cardRendered`, `moveCard`, the DnD config, `menuCards`, `cardColClasses`/`cardCssOrder` — and the flat card catalogue both the dashboard and Reports read. The page drops to ~900 lines (hero + slot loaders + cells). · M · **execute (it is the FU's own plan; 08-R7 lands inside it so the layout gets a spec)**.
- **08-R19** · The Cards menu block (L55–118) is a self-contained `CardsMenu.vue` (list, drag handle, up/down, toggle) once 08-R18 exposes the composable. · S · **execute with 08-R18**.
- **08-R20** · The hero (L20–146) is the page's only remaining markup after the cards were extracted; a `DashboardHero.vue` is optional. · **waive** (one consumer; the page is the natural owner).

### C5. Placement / standards (R-002, R-005, R-008, D-rules)
- **08-R21** · D-010 motion literals: `DashboardCard.vue:60–63` (`0.18s ease` ×3), `.dora-cards` `0.4s ease-out`, `.fade-*` `0.25s` (page L1537, L1620), `PantryDonutCard.vue:165` (`0.6s`, `0.15s`), `WhatsComingCard.vue:219` (`0.15s`), `CardLoadError` retry timer `1200` ms — the `--motion-*` tokens exist and the two verdict components use them. · **Exact change:** `var(--motion-fast|--motion-base|--motion-slow)` + `var(--motion-ease)`; the JS timeout reads the same via `getMotionMs('fast')` if a helper exists, else leave. · S · **execute (02-R38 / 06-R37 class)**.
- **08-R22** · FU-671 — `PriceDropsCard.vue:44 text-color="white"` on a `negative` badge. · **Exact change:** `dora-chip--tint-negative`. · S · **execute**.
- **08-R23** · R-069 — `PriceDropsCard.vue:32 class="text-primary"` on the linked-item router-link (brand fill as text) while every other accent string on the page is `--accent-ink`. · **Exact change:** `dora-link-accent` (or the existing accent-ink utility). · S · **execute**.
- **08-R24** · Inline `style="min-width: 300px"` on the Cards menu list (`L56`). · S · **execute** (06-R36 class).
- **08-R25** · R-008 — loggers: `get_dashboard_summary`, `get_restock_radar`, `get_use_it_up`, `get_usage_stats` build `_Logger` per request; `get_dora_score` has a module `_LOGGER`. `get_use_it_up.py:96 date.fromordinal(today.toordinal() + window)` → `today + timedelta(days=window)`. `get_usage_stats._count/_total_spend` import inside methods. · S · **execute** (06-R41 class).
- **08-R26** · `get_dashboard_summary._cook_verdicts` imports `get_or_create_app_setting` + `upcoming_planned_meals` inside the method (L181–182) with no cycle reason stated. · **Exact change:** module-level imports (or a one-line "cycle:" comment if there is one). · S · **execute**.
- **08-R27** · `DoraScoreCard.barClass` bands the server's number at 80/50 client-side. Presentation banding on a server-owned score (A1 names positive = "good scores", warning = "fair") — the "already clean, do not relocate" class. · **waive** (recorded so it isn't re-raised).

### C6. Naming & idiom
- **08-R28** · `PantryDonutCard.vue` — the file and the `stock_items` card are "My stock" since 2026-09-04; the component name still says Pantry (the comment at L9–12 even explains why "pantry" is the wrong noun). · **Exact change:** rename to `StockDonutCard.vue` (one importer). · S · **execute**.
- **08-R29** · `get_dashboard_summary.py` mixes `_Today`/`_Window`/`_SlotOrder` CapWords locals with `cook_batches`/`upcoming_entries_dto` snake_case in one method. · S · **execute with 08-R2**.

### C7. Efficiency
- **08-R30** · Per dashboard load the server runs `load_recipe_cookability` **twice** (summary + score) and `upcoming_planned_meals` **twice** (summary `_cook_verdicts` + restock radar via `gather_planned_demand`), and the SPA fires 7–8 requests. Acceptable at household scale; 08-R16 trims the cookability half. · **waive** (note).
- **08-R31** · `get_restock_radar` loads every item + `gather_planned_demand` on each load to mark ≤6 rows *Planned*. · **waive** (≤500 items).

### C8. Design-level findings — out of Stage-2 scope
- **08-D1** · FU-837 — a short card stretches to its tall row-mate (align-items: stretch + `height: 100%`); design call, three options recorded there.
- **08-D2** · FU-870 — plan coverage cancels out of the trend; accepted trade.
- **08-D3** · FU-868 — money-off / products-off renders never observed; `DORA_VERIFY.md` Dashboard rows cover it.
- **08-D4** · FU-897 — the "already on a list" filter dropped with *Before you shop*; the cart button shows the state instead. Owner call.
- **08-D5** · Feedback D6 (alert-card redesign) was built (Phase 3) and then **cut** on 2026-09-04 with the attention card; the bell + Alerts page carry it. Recorded as superseded, not missing.
- **08-D6** · Feedback L480 (cross-app undo for a dashboard push-expiry) — the dashboard no longer has an expiry action; superseded.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| SVG donut + ring (`PantryDonutCard`, `DoraScoreCard`) | charts | ECharts (removed, FU-833) | **keep** | — | `stroke-dasharray` on r=15.915 is the idiom; a11y labels present. |
| `useDragDropList` + tap up/down | reorder | SortableJS / vuedraggable | **keep** | — | Native DnD with a tap fallback is the C13 mandate. |
| `zoneColClasses` parity | layout | CSS grid `auto-fit` | **keep** | — | Order is dynamic and persisted; CSS can't widen "the last of an odd run". Tested. |
| `dashboardMessages` pools + `epochDay` | rotation | — | **keep** | — | Deterministic, gated, tested. |
| three module caches | cache | one factory (07-R6) | **wrap** | S | 08-R10. |
| `parseLayout` JSON narrowing | validation | zod | **keep** | — | Six lines; a schema lib for one field is creep. |

### C10. Standards drift (R-0NN)
- **R-003** · 08-R6 (spend rule ×2), 08-R9, 08-R10, 08-R12 — fix.
- **R-005** · 08-R6 (raw Core counts) — fix.
- **R-008** · 08-R25, 08-R26, 08-R29 — fix.
- **R-019** · 08-R7 — fix (and the §6 finding 21 that was marked for Chunk 1 and survived).
- **R-021** · 08-R3, 08-R8 — fix.
- **R-032** · all four handlers resolve levels by FK or count by `_stock_level_id` — clean; 08-R1 is the None-guard, not a relationship read.
- **R-056** · 08-R12 — fix.
- **R-057** · 08-R2 (summary fields), 08-R11 (`to` prop) — the inventory the rule asks for, executed.
- **R-002 / D-010** · 08-R21 — fix; **FU-671** 08-R22; **R-069** 08-R23.
- **R-060** · no undeclared tokens found on this surface (the DoraScoreCard sweep landed; `--semantic-info`, `--hero-gradient`, `--elevation-card(-hover)`, `--radius-pill` all defined).
- **FU-654** · 08-R5 — one more copy removed.
- **FU-844** · the `watch(moneyEnabled)` / `watch(productsEnabled)` re-fire guards (L1379–1390) stay until the composable owns it — tracked.

### C11. Ride-along signals for FU-010 / FU-224
- The hero uses `--brand-primary-soft` fill + `--brand-primary` rule + `--accent-ink` text — the page's cleanest statement of the R-069 split; a reference for FU-224.
- `.dora-cal-cell.is-today` = `--accent-mark` hairline, `.is-selected` = `--brand-primary-soft` fill — two accent families on adjacent cells; check in the dark themes.
- Calendar dots: positive / negative / **info** as a categorical trio (owner fix 2026-09-04) — note the only `--semantic-info` use on the surface.

## D. Test plan — Dashboard

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__restock_radar__item_without_level__is_skipped_not_500` | pytest e2e (`test_dashboard_insight_cards.py`) | **must-write-before-ship** | 08-R1. |
| `dashboardLayout.spec.ts` — `parseLayout` inserts an unseen card at its registry position; retired ids dropped; `defaultHidden` inherited | vitest | **must-write-before-ship** | 08-R7 / 08-R18 — the comment promised it and nothing held it. |
| `test__dora_score__freshness_as_of_household_today` | pytest e2e | nice-to-have | 08-R3 — a +10 h household at 23:00 local. |
| `test__dashboard_summary__shape__no_recipe_or_list_totals` (update the shape test) | pytest e2e | housekeeping | 08-R2. |
| `test__usage_stats__total_spend_matches_spend_by_store_total` | pytest e2e | nice-to-have | 08-R6 — one rule, two readers. |
| `dashboardCalendar.spec.ts` | vitest | housekeeping | 08-R14. |

Not proposed: anything for the card bodies (drive once per `DORA_VERIFY.md` Dashboard rows), the DnD reorder, or the money-off renders (FU-868 is a verify pairing).

## E. Proposed follow-ups (orchestrator allocates ids)

- **Execute existing deferred jobs:** **FU-832** (08-R18/19 — `useCardLayout` + catalogue), **FU-896** (08-R10 — delete `invalidateDoraScore`), **FU-899** (08-R11 — drop the consumer-less `to` path).
- Existing FUs this chunk executes against: **FU-654 / 02-R12** (08-R5), **FU-671** (08-R22), **FU-908** (08-R16 — two more callers for the `recipe_ids` filter), **07-R6** (08-R10), **02-R38 / 06-R37** (08-R21), **06-R41** (08-R25).
- Existing FUs referenced, unchanged: FU-837, 870, 868, 897, 898, 871 (08-R7 does **not** rewrite stored JSON; the migration stays optional), 844, 836 (handled).
- No new FUs: every finding here is executable or already tracked.

## F. Summary for the register

- FST rows: 12 golden + 13 edge + 4 gate · Help entries: 9 new (a new **Dashboard** group — none existed) + 1 stale sentence fixed + DoraBot paragraph rewritten · Review findings: 31 (execute 24 / waive 4 / design-record 6 / fold 1) · Tests: 6 (must-write 2) · Bugs: 8 (restock radar 500s on an unlevelled item; two dead summary sub-objects still queried per load; score freshness dated in UTC; whole-pantry scan ×2 per score; unused `user_id` + a FU-654 copy; usage stats bypass the repo and re-state the spend rule; `parseLayout` appends where its comment says it inserts — Kitchen health landed last for every existing user; calendar "today" from the browser)
- One-line: after three owner batches this is the app's most-reviewed page and it shows — eight honest cards, one predicate for visibility, a tested parity grid, in-card failure states — and what's left is small and mechanical: a `None` guard the other level consumers have, two payload fields nobody reads, three UTC-vs-household dates, and the layout composable FU-832 already decided to extract.

### Feedback coverage — `# DASHBOARD` (L48–61) + strays

| # | Feedback bullet | Where it lives now | State |
|---|---|---|---|
| D1a | Skip-wizard *Continue* does nothing | `onContinueOnboarding` (restart + auth refresh + `/welcome`) | ✅ done |
| D1b | Skip banner buttons inline | `.dora-welcome-actions` | ✅ done |
| D1c | Welcome message when onboarding complete | hero message line | ✅ done |
| D1d | Cycled welcome: 5/day × 7 + hints pool | `dashboardMessages.ts` (35 + 21, gated, tested) | ✅ done |
| D1e | Replace bottom-right bubble, keep the "Dora says" look | hero + callout (band merged 2026-09-04) | ✅ done (evolved) |
| D2 | Dark mode not working | R-060 token sweep (`DoraScoreCard` fallbacks) | ✅ done |
| D3 | Remove refresh if nav refreshes | removed; `loadAll` on mount | ✅ done |
| D4 | Reorder cards via draggable rows | drag + tap up/down, server-persisted | ✅ done |
| D5 | Alerts nav 404 → alerts control page | `/alerts` page (Chunk 9) | ➡ Chunk 9 |
| D6 | Alert card redesign (summary + peek + see all) | built (Phase 3) then cut 2026-09-04 with the attention card | 📦 superseded (08-D5) |
| D7 | "This fortnight" calendar with dots, tap a date | *What's coming* (merged with the week strip, 14 days, FU-818) | ✅ done |
| L176 | Mascot not centred | 2px optical pad carve-out, documented | ✅ done |
| L272 | "Next up to cook" by plan + stock, ready/missing | *Next to cook*, batch-aware | ✅ done |
| L480 | Cross-app undo (dashboard push-expiry) | the dashboard has no expiry action any more | 📦 superseded (08-D6) |
