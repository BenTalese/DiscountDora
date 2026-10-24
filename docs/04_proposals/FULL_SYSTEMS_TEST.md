# Full Systems Test — Dashy Dora

**Assembled 2026-10-23** from the twenty finalisation chunk files (`docs/05_investigations/finalisation/CHUNK_NN_*.md`, track **FST** = each chunk's §A). Governing plan: [`docs/01_charter/FINALISATION_PLAN.md`](../01_charter/FINALISATION_PLAN.md) §3.1; register: [`FINALISATION_COVERAGE.md`](../01_charter/FINALISATION_COVERAGE.md).

**How to walk it.** Each chunk gives preconditions (A1), a numbered golden path with expectations (A2), edge cases (A3), the personas it covers (A4), the platform/network/theme conditions that are load-bearing for that surface (A5) and the 1–4 rows that belong on the launch tollgate (A6). Walk a chunk end to end on a near-final build; tick rows in your own copy; anything that fails goes to `DORA_FOLLOWUPS.md`. Rows marked *today:* describe behaviour at analysis time that Stage 2 is expected to change — re-read the matching `NN-Rk` finding in `FINALISATION_REVIEW.md` before judging a failure.

**Personas** (PLAN §4): Fresh install · Dense household · Minimal · Power user · Admin · Multi-user · Self-host operator · Managed instance.

---

## Release-gate roll-up (every chunk's A6)

**Chunk 01 — Cookbook**

- Create → edit all three regions → save → reload shows every change (incl. step links and section membership).
- Cookbook list of ≥ 100 recipes loads in one page set with query count pinned (`test_recipes_query_count`).
- Import a real pasted recipe end-to-end and bulk-link one unlinked group.
- Cost + nutrition both on: card chip, detail cell, breakdown dialog and nutrition panel agree on coverage counts.

**Chunk 02 — Meal Plans**

- Batch household: plan a 3-day cook, reconcile its cook day as "Didn't cook" in manual mode, and confirm the pool, the chef-hat glyphs and the shortfall all agree.
- Build my week with budget cap on a week projected over budget → the review step's two money figures match the planner's "Cost this week" after save.
- Apply a rotating set over 4 weeks across a month boundary; calendar follows; each week's provenance (`source_template_set_id`, `rotation_index`) is set.
- Phone: add → link cook days → add to list → reconcile, all from the mobile tree.

**Chunk 03 — Shopping Lists**

- Money on + products on: pick an offer → tick → enter a different price at the till → finish → the receipt shows the entered price, "You saved" uses the offer's RRP, and `/budget/status` spent equals the receipt total.
- Finish early with leftovers → "Move to a new list" → the new list carries exactly the unticked lines, the receipt's "Didn't buy" is empty.
- Amend a receipt price → `/stock-items/<id>/detail` "Your prices" reflects the correction (observation rewritten, `observed_at` unchanged).
- Phone: new list from a meal plan → shop → finish, all from the picker.

**Chunk 04 — Cook Mode**

- Structured recipe with a sub-step, a declared timer and a swapped substitute: finish → the substitute's level changes (not the original's), a `cook` consumption event per changed row, pool +N (Batch), `last_made_on` = household today, Stock-item history shows "Used in <recipe>".
- Photo recipe end-to-end on a phone including Finish.
- Sous Chef + mic on Android Chrome: "next" heard while Dora is mid-sentence; narration not clipped at the start (FU-722 candidate fixes).
- Navigate between two cook routes without a reload → the second recipe renders (after 04-R1).

**Chunk 05 — Stock Overview + Stocktake**

- Admin sets expiring window to 3 days → rows, the bell and the "Expiring soon" chip agree (one rule, `stock_attention.py`).
- Full stocktake with all three phases on a phone; after Done, `/stock` reflects every level change and deletion **without a reload** (05-R5).
- Bulk: select 40 → Add to list → one request; Restock → one request, 40 `StockLevelChange` rows, auto-add fires at most once per item; Log waste → Undo restores every expiry.
- Scan loop "Set to Out of Stock" over 5 items → 5 level writes, markers update, no navigation.

**Chunk 06 — Stock-Item Detail**

- Open an item in the peek, swap to a second item, confirm name / level / verdict / QR / substitutes all belong to the second item.
- Rename an item to its own name → no error; to another's name (different case) → 422 (depends on 05-R30).
- Opened toggle → Cancel → confirm no PATCH in the network log.
- Unlink a product that a shopping-list line and a recipe ingredient had selected → both selections cleared; detail read still 200.
- Delete an item used by a recipe → 422 with the recipe names, item still present.

**Chunk 07 — Zero-Input Pantry (P8-07)**

- In an AEST household, change a level at 08:00 local → picker header reads *Updated today* and the ring is gone.
- Toggle *Stock overview hints* off → `/stock-items/beliefs` → `{enabled:false, beliefs:{}}` and no row is dashed.
- Cookbook hints on + the dense seed's at-risk recipe → *May be short* chip names the right ingredient; `missing_count` unchanged.
- Cook-mode finish marking an item down → one `ConsumptionEvent` row, `source='cook'`, `from_sequence < to_sequence`.

**Chunk 08 — Dashboard**

- Default install, 1280px: seven cards, zero dead regions; 375px: one column, Cook/Cards icon-only, no horizontal scroll.
- Money off: no Budget card, no Budget row in Kitchen health, no money hint in a week of reloads (`dashboardMessages.spec` covers the pool; the card gate needs eyes — FU-868).
- Change the budget period in Settings, return within five minutes → Kitchen health's Budget row reflects the new window.
- Reorder two cards, reload, second device → same order.

**Chunk 09 — Alerts + Suggestions**

- Badge count = number of high+medium cards in the panel (feedback L438: "6 vs 10" — pinned by `test__alerts__actionable_count_equals_high_plus_medium_in_items` and `alertStore.spec`).
- Disable `expiring_soon` for user A → A's rows lose their outline, user B's don't.
- Dismiss an expiry alert, change the expiry → a fresh alert.
- With VAPID configured: subscribe, fire an alert, receive the push, tap → panel open.
- 19:00 household-local brief arrives once; 19:20 restart does not resend.

**Chunk 10 — Products / Price History / Deals**

- [ ] Weekly deals mail "See all deals" opens My Products (after 10-R1).
- [ ] My Products shows the whole catalogue on an install with > 50 products (after 10-R9).
- [ ] Store logos render in the Capacitor shell / split host (after 10-R35).
- [ ] Price watch set from My Products fires as a `price_drop` alert on the next lower offer and never twice for the same offer.
- [ ] Deleting a product leaves finished-list lines named.

**Chunk 11 — Assistant (Dora)**

- [ ] Every `PROPOSERS` entry executes against an empty database without raising (after 11-R1).
- [ ] Every data tool executes with `{}` against an empty database without raising (after 11-R2).
- [ ] Every `_TOOL_NAV` path is a live SPA route (after 11-R3).
- [ ] Basic-mode "where is X" names the location (after 11-R4).
- [ ] 21st `/ask` in a minute → 429 + `Retry-After`; probe rate limit → 429 too (after 11-R15).
- [ ] A product name carrying an instruction does not steer the model (manual, one prompt).

**Chunk 12 — Reports / Memory (P8-09), Waste, Budget**

- [ ] A shop finished at 08:00 local on the first day of a period counts toward that period (after 12-R2).
- [ ] Spend-by-store total == spend-by-category total == savings `total_spent` on one fixture (after 12-R10).
- [ ] "Bought most" counts ticked lines only (after 12-R4).
- [ ] Window label dates match the household date near midnight (after 12-R3).
- [ ] `getStockValueAsync` / `GET /reports/stock-value-over-time` gone (after 12-R1) or fixed and consumed.

**Chunk 13 — Settings shell**

- [ ] Invalid `nutrition_mode` → 400, not 500 (13-R1).
- [ ] Admin email edit validates + dedupes like self-serve (13-R2).
- [ ] Deleting the last **active** admin is refused (13-R3).
- [ ] A member sees the Product Search nav entry when a URL is set (13-R4).

**Chunk 14 — Onboarding**

- [ ] Finish with the demo recipe on a week that already has a plan reuses that plan (after 14-R1).
- [ ] Demo ingredients reuse "Pasta" / "Garlic" / "Olive oil" from the packs (after 14-R2).
- [ ] Skip → dashboard banner → Continue → wizard restores the draft (today ✓; keep).
- [ ] A first user who leaves Timezone untouched ends with the **device** zone saved, not UTC (today ✓ — closes FU-632 #48's timezone half).

**Chunk 15 — Auth shell**

- [ ] Behind a reverse proxy, two clients get independent login rate limits and distinct audit IPs (after 15-R1).
- [ ] No request body from `/auth/*` reaches any log at any level (after 15-R2).
- [ ] Register with an email → "Check your inbox" toast (after 15-R3).
- [ ] Fullscreen 404 renders through `AuthShell` (after 15-R6) — one palette, one mascot animation.

**Chunk 16 — Ingestion API + companion seam**

1. Mint → copy → push → counters → revoke → 401 round-trip (G2–G3, G14–G16) on the release build.
2. Idempotent replay is a no-op, and a replay after the TTL does **not** 500 (G7 + 16-R2 fix).
3. `link-status` never reports a custom product (16-R8 fix) — the companion's "unsave" deletes by that id.
4. The power-user guide's sample `curl` body is accepted verbatim by the release build (16-R1).

**Chunk 17 — Offline / PWA / native**

1. G5–G7 on a phone: offline banner copy, no "queued" promise anywhere (incl. `offline.html` — 17-R2), Retry corrects `navigator.onLine`.
2. G8 after a real redeploy: exactly one update banner; **no** banner from visiting Settings → Notifications (17-R1).
3. G9 two-user cache eviction on one device.
4. G11 APK first-run → LAN `http://` backend reachable (17-R10 confirm).

**Chunk 18 — Backup & restore + Import**

1. G2–G3 **New backup with defaults succeeds** (18-R2) and the file round-trips through G8–G10 on a fresh install, including recipe steps/tools/tags (VERIFY cookbook 6/7/8 bullets).
2. G9 **Restore selection** works (18-R1).
3. G12–G16 template → import → error CSV loop.
4. Credential exclusion spot-check on a downloaded file (G5).

**Chunk 19 — Ops / self-host**

1. G2 image ships **PWA mode** (`sw.js` + `manifest.json` present in `/app/web_app/dist/spa`) — 19-R1.
2. G3 from a second machine with `web_app/.env` present on the build host — 19-R2.
3. G4 fresh boot: `schema_version == schema_version_db`, no drift banner, 156 migrations, single head.
4. G9 version check resolves against the real repo — 19-R3.
5. `pytest tests/test_migrations.py tests/test_compose_env_coverage.py` green on SQLite **and** Postgres (G13).

**Chunk 20 — Cross-cutting concerns**

1. G1 + G2 on every theme at `xl` text, phone width — no clipped labels, no h-scroll, focus ring visible and brand-matched.
2. G3 locale flip — no `$`/`toFixed`/US-date leaks (20-R6, R7 fixed).
3. G6–G8 error path end-to-end with a `ref:` id that matches a server log line.
4. Contrast spot-check of `warning`/`negative` chips and segmented active labels in pesto, blueberry, midnight (FU-671/674).

---

## Chunk 01 — Cookbook
*Source: [`CHUNK_01_cookbook.md`](../05_investigations/finalisation/CHUNK_01_cookbook.md) · analysed 2026-10-23*

### A. Full Systems Test — Cookbook

#### A1. Preconditions
- Seeded install (`dora`/`dora` e2e seed) with ≥ 12 recipes, at least one each of: structured steps, free-text, image steps; one with sections; one with an unlinked ingredient; one in a version group.
- Money and nutrition feature flags are the two conditions that change this surface; run the golden path once with both **off** (default) and once with money on + nutrition **complex** with a dataset imported.

#### A2. Golden path
Persona: **Fresh install → Dense user** (the surface is identical; density is what the dense run tests).
1. Stock → Cookbook (`/cookbook`) → page renders cards; toolbar shows New recipe · Import · Compact/Cards · filter toggle · search → expected: footer counts "Shown / Cookable now / Favourites".
2. Toggle Compact → rows; reload → mode remembered (localStorage).
3. Open filters → set Cuisine + a dietary tag include → list narrows, badge count 2, Clear filters resets → expected: panel opens itself whenever a filter is active after navigation.
4. Tick "Uses expiring ingredients" → list re-sorts soonest-expiry first, each card wears "Uses N expiring"; open a result → its ingredient rows carry "Use soon"/"Expired" chips → back → chip still on and list still narrowed (FU fixed 09-09).
5. New recipe → stub dialog (Name / Cuisine / Category / Collection) → Create & open → lands on `/cookbook/<id>` with empty rail.
6. Pencil on masthead → edit serves/prep/cook/difficulty/when → Done → Save bar "Saved"; facts update; Total shown only when prep+cook > 0.
7. Pencil on Ingredients → Add ingredient → row editor opens immediately → type an unknown name → "Use …" → dialog "Add to pantry? / Keep as free text" → both paths close the picker; Done → row renders (Free text chip when unlinked).
8. Add section → name it → move an ingredient into it via the row editor → section renders as a card; Move section up/down; Remove section → rows fall back to main.
9. Pencil on Method → switch Structured → Add step → link ingredients via the link icon → Done → tap a step → its ingredients light; tap an ingredient → steps light.
10. Save → Cook mode button is primary; status strip reads "Everything in stock" or "N missing" with "Add N to a list" → picker (shared AddToListDialog) → confirm → cart button state flips.
11. Favourite toggles from card, row and page; New version → navigates to `(v2)`; Version information lists siblings with created dates.
12. Import → paste a recipe page's text + URL → preview toast "N matched · M unlinked" → recipe opens; Settings → Unlinked ingredients shows the groups; bulk-link one → recipe's cookable flips from unknown.
13. Delete → confirm → back on `/cookbook`.

#### A3. Edge cases
- Save with a half-built ingredient row → "Not saved: 1 ingredient has no item or text yet", row wears "Needs an item" chip.
- Save with an empty structured step → blocked, step field turns red only after the attempt.
- Rename a recipe to an existing name → 422 business-rule toast; rename to its own name → saves (FU-528 family).
- Delete the cuisine a recipe uses (Settings) → recipe shows "Any cuisine", still saves (slot vocabulary: a recipe whose `time_of_day` slot was deleted still saves — 09-01 fix).
- Leave with unsaved changes → "Stay / Leave without saving" dialog; browser reload → native prompt.
- Nutrition complex with no dataset → panel reads "Nothing to add up yet", gaps list "No food linked" with Find a food.
- Money off → no cost cell, no Cost sort axis, no cost chip (server sends nothing).
- Batch cook-style off → no Meals prepared chip/filter/sort; a persisted `meal_count` sort snaps back to Name.
- Share-target landing (`/cookbook?share_text=…`) → import dialog pre-filled; query stripped after.
- Deep links: `?usesStockItem=<id>`, `?cookable=true`, `?expiring=true`.
- Offline (read-only, R-052): cookbook renders cached list; Save fails with a toast, dirty pill stays.

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ | ✓ (perf: 300+ recipes, list query count) | ✓ (money/nutrition off) | ✓ (both on, shortcuts `g r`, `n`) | – | ✓ (favourites are per-recipe, not per-user — see C8-1) | – | – |

#### A5. Load-bearing conditions
- **360×640**: masthead stacks, facts and actions scroll sideways (D-011), method heading wraps the three-way switch to its own line, row buttons lift to 44px.
- **1920+**: filter row wraps to two lines (`wide-wraps`); rail is sticky with inner scroll.
- **All themes × light/dark**: lit-row tint, severity edge stripes, Nutri-Score grade colours (hard-coded hex — C11), rating pill (FU-772).
- **Offline/bad network**: expiring filter fetch failure flips the chip off with a toast.
- **Reduced motion**: FadeTransition on list swap; `q-slide-transition` on rating working.

#### A6. Release-gate rows
- Create → edit all three regions → save → reload shows every change (incl. step links and section membership).
- Cookbook list of ≥ 100 recipes loads in one page set with query count pinned (`test_recipes_query_count`).
- Import a real pasted recipe end-to-end and bulk-link one unlinked group.
- Cost + nutrition both on: card chip, detail cell, breakdown dialog and nutrition panel agree on coverage counts.

---

## Chunk 02 — Meal Plans
*Source: [`CHUNK_02_meal_plans.md`](../05_investigations/finalisation/CHUNK_02_meal_plans.md) · analysed 2026-10-23*

### A. Full Systems Test — Meal Plans

#### A1. Preconditions
- Seeded install with ≥ 20 recipes (some favourites, some never cooked, some with expiring stock) and the household meal slots at their defaults.
- Run twice: **cook-style Fresh** (default) and **cook-style Batch** (`/settings/admin/system/cooking`), because the pool, cook batches, fresh marks, the chef-hat/fridge glyphs and the shortfall all exist only in Batch.
- Money on for the cost/budget rows; nutrition complex for the lighter-swap menu item.

#### A2. Golden path
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

#### A3. Edge cases
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

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (first-run card → Cookbook) | ✓ | ✓ (fresh style, money off) | ✓ (batch + money + nutrition, keyboard nav) | ✓ (cook style / reconcile mode / slots are install-wide) | ✓ (one shared plan per week — see 02-D3) | – | – |

#### A5. Load-bearing conditions
- **360×640 / phone**: the entire mobile branch is a separate component tree (`MealPlanMobileFocus`), so every flow above must be walked twice.
- **1024–1180px**: toolbar compacts labels; rail 340px + context 300px leave the week pane narrow — check nothing wraps to a third line (§3.2 acceptance).
- **Reduced motion**: week carousel and calendar paging drop their transitions; the settle pulse must not loop.
- **Themes × dark**: the lit slot (`--q-primary` 14 % mix), focused day chip (`white` text — 02-R37), leftover grey trim, warning glyph ink; pesto dark had invisible low-alpha washes elsewhere (09-08).
- **Offline**: read-only; every mutation toasts "Could not update the plan." and leaves the week as fetched.

#### A6. Release-gate rows
- Batch household: plan a 3-day cook, reconcile its cook day as "Didn't cook" in manual mode, and confirm the pool, the chef-hat glyphs and the shortfall all agree.
- Build my week with budget cap on a week projected over budget → the review step's two money figures match the planner's "Cost this week" after save.
- Apply a rotating set over 4 weeks across a month boundary; calendar follows; each week's provenance (`source_template_set_id`, `rotation_index`) is set.
- Phone: add → link cook days → add to list → reconcile, all from the mobile tree.

---

## Chunk 03 — Shopping Lists
*Source: [`CHUNK_03_shopping_lists.md`](../05_investigations/finalisation/CHUNK_03_shopping_lists.md) · analysed 2026-10-23*

### A. Full Systems Test — Shopping Lists

#### A1. Preconditions
- Seeded install with ≥ 2 stores (one with a logo), ≥ 30 stock items (some with `usual_store_id`, some with linked products + offers, some essentials, some low/out), ≥ 2 finished lists in history (so the money ladder's historic rung and "frequently added" have data).
- Run three times: **money off** (default install), **money on, products off** (preferred buys), **money on + products on** (offers). The row's "which one" picker, the price chips, the store breakdown title and the trim banner all change shape per tier.
- Budget set under `/settings/budget` for the trim-to-budget and projection rows.

#### A2. Golden path
Persona: **Dense user**, desktop then phone.
1. `/shopping-lists` with lists → route guard lands on the next-up list (live shop > first pending after last completed > earliest pending > latest done); with no lists → empty state + "New list".
2. Rail (desktop) / picker (phone): drafts + shopping + 5 most recent done, newest first; "See older (N)" opens a searchable dialog; "New list" pinned at the top.
3. New list → Start from Empty / Template / Recipe / Meal plan; auto-fill low-or-out (essentials only), all essentials, frequently added; target new (name + shop day) or merge into an existing list → toast with counts; unlinked recipe ingredients named (FU-505).
4. Plan face: overview card (estimated cost or item count · shop day · items; group-by Store/None; **Shop**), toolbar (Add item · Shop day calendar popup · Templates · Print · Save as template).
5. Add item → QuickAddSheet: frequently-added first, then low/out; items already on the target list hidden; one tap = one line, sheet stays open.
6. Row: quantity tile (hover stepper / tap-to-type), name = "which one" picker (offers or preferred buys), Dora's auto-added mark, buy-verdict badge, planned-store caption menu ("Any store" + every store, "(usual)" marked), `~$` estimate, reorder arrows (ungrouped only), delete. Drag to reorder (desktop, ungrouped).
7. Pick an offer → line moves to that store, estimate = offer price; un-pick → historic figure returns. Set planned store → row re-sections under Store.
8. Dora's suggestions strip (inference opted in) → chip adds a line.
9. Over budget → trim banner → "Show what would be cut" → Keep one → Apply → Deferred-to-fit section with reason + Add back.
10. **Shop** → run face: progress bar, "Left to spend", sections with `picked/total`, cleared sections collapse to one line, Collected drawer with trolley total; tap row = picked (toast with Undo); price button → bottom sheet (price each · offers "Seen at" chips · quantity stepper · bought-from); Log price (money) for off-list items; Draft (back to draft, unticks all).
11. **Finish** → dialog lists ticked items (nested lines collapse to the parent); unticked leftovers force a choice: move to existing / move to new / discard; → done, ticked items restocked to Stocked, observations harvested, names snapshotted.
12. Receipt face: card (Shopped date · items bought · You saved), sheet with multiplier · name · leader · amount, "Didn't buy" chips, Total + "N not priced"; Amend → stepper + "Set price" per line; corrections rewrite the observation; Put away checklist.
13. Receipts section (shopping/done): take photo / choose → thumb strip → zoom → delete.
14. Templates page: Use (one tap) / preview / Edit items (picker-based "which one", quantities) / rename inline / delete; Save as template from a list (name + include ticked?).
15. Cart button elsewhere (stock rows, recipe ingredients, product rows): none → add (1 draft silent, 2+ → radio, 0 → "create a list first"); on list → remove; on several → popover.
16. PWA "Shop now" shortcut → `/shopping-lists/shop-now` → the single shopping list, else the single draft, else the overview.

#### A3. Edge cases
- Rename to blank → list self-labels from shop day / created date; `display_name` tracks a later shop-day change.
- Deleting the list you're viewing → bounce to `/shopping-lists`.
- Product-only line (no stock item) → sunken row, bag glyph, removal prompts "also remove the stock item?"; **03-R1/R3/R4**: copying, moving or snapshotting such a line is broken (see §C1).
- Deleting a stock item on a draft → its line vanishes; on a done list → the line survives with the frozen name.
- Finish with zero ticked → "nothing is restocked"; finish with everything ticked → plain confirm, no leftovers section.
- Done list: PATCH `status=done` is refused (400); start / back-to-draft on done → 400.
- Template whose items were deleted → instantiate skips them, list still created (possibly empty).
- Quick-add while 2 drafts exist → "which list" radio, pick remembered for the tab.
- Reorder while grouped → arrows/drag hidden; stored group preference pointing at an empty field → falls back to None with a reason in the menu.
- Money off → no price column, card leads with counts, store breakdown says "Where you'll shop", receipt leader hidden.
- Offline → mutations toast "Could not …" and the optimistic flip is reverted.
- Trim with nothing cuttable → "Trimmed everything safe. Still $X over."
- Two lists both planned for today → next-up picks the earlier-created one.

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (empty state → New list) | ✓ | ✓ (money off tier) | ✓ (products + budget + keyboard `n`/space/`u`/arrows) | ✓ (money / products flags) | ✓ (lists are shared; quick-add target is per-tab) | – | – |

#### A5. Load-bearing conditions
- **375px phone**: the two-line plan row grid, the picker + rename segment, the run row's 60px target, the bottom price sheet with the keyboard up, the finish dialog at 34vh scroll.
- **1280px**: toolbar scrolls sideways rather than wrapping; rail 300px with ellipsised names (FU-578 #40 family).
- **Themes × dark**: status pills (soft bg + full ink), `.sl-panel--warn` soft wash, gradient band on plan/run vs flat receipt, the `hsla(0,0%,100%,.55)` progress track over the gradient (R-002 carve-out — verify on pesto dark).
- **Reduced motion**: progress bar fill, reveal-on-approach transitions.
- **Touch**: no stepper, arrows always visible, 44px action track.

#### A6. Release-gate rows
- Money on + products on: pick an offer → tick → enter a different price at the till → finish → the receipt shows the entered price, "You saved" uses the offer's RRP, and `/budget/status` spent equals the receipt total.
- Finish early with leftovers → "Move to a new list" → the new list carries exactly the unticked lines, the receipt's "Didn't buy" is empty.
- Amend a receipt price → `/stock-items/<id>/detail` "Your prices" reflects the correction (observation rewritten, `observed_at` unchanged).
- Phone: new list from a meal plan → shop → finish, all from the picker.

---

## Chunk 04 — Cook Mode
*Source: [`CHUNK_04_cook_mode.md`](../05_investigations/finalisation/CHUNK_04_cook_mode.md) · analysed 2026-10-23*

### A. Full Systems Test — Cook Mode

#### A1. Preconditions
- Three recipes: **free-text** (numbered lines, one with "simmer 20 minutes"), **structured** (sections, one sub-step, per-step ingredients + tools, one `timer_minutes`, a hint, notes), **photo** (`steps_mode='image'`, ≥ 3 images). (FU-754: the dense seed lacks structured/image fixtures — seed them first.)
- One ingredient low/out **with** a recorded substitute carrying a ratio + note (FU-793: the dense seed lacks this — add).
- Household headcount set (`/settings/admin/system/cooking`); run twice: cook-style **Fresh** and **Batch** (the "Extra servings" stepper and the "You saved N meals" toast exist only in Batch).
- Sous Chef: once with Piper configured, once browser-voice only, once on Firefox (no `SpeechRecognition` → no mic button).

#### A2. Golden path
Persona: **Dense user**, tablet in the kitchen, then phone.
1. Recipe → **Cook** → header: back · name (ellipsised) · Sous Chef (labelled on desktop, icon on phone) · mic (if supported) · `(?)` commands popover (only once Sous Chef or the mic is on) · "Cooking for N" pill seeded from the headcount (or `?for=N` from the planner).
2. Step card: section chip, Sub-step chip, step text at display size, hint band; progress badge + segmented track (≤ 14 steps; segments are jump buttons) → Previous / Repeat / Next one row on a phone.
3. Change "Cooking for" → ingredient quantities rescale (countables to whole numbers ≥ 1, continuous to ½ ⅓ ¼ … or one decimal).
4. Ingredients grouped by recipe section, else by base location, "No location" last; the current step's ingredients and tools highlighted, neighbours dimmed (tools only); optional rows dimmed; notes italic behind a glyph.
5. Low/out ingredient shows the swap button → picker lists substitutes with ratio + note → pick → row shows the substitute chip, "instead of X", the hint line, and an undo.
6. Timer band: declared minutes ("from this step's wording" when sniffed) → Start → MM:SS + bar emptying → Pause / Reset → at zero: toast + chime + "Timer finished" (Sous Chef on).
7. Sous Chef on → step 1 is read on arrival, each step on change, Repeat re-reads; mic on → "next" / "back" / "repeat" / "ingredients" / "tools" / "start timer" / "stop" / "exit" work hands-free; "stop" silences Dora first, pauses the timer second, never exits.
8. All steps panel: numbered circles (shared with the recipe page), current row highlighted, tap to jump.
9. Last step → **Finish** → "Finished cooking?": one row per linked ingredient (substitute replaces the original) with the level swatch picker preselected at the current level + level name + cart button; Batch: "Extra servings for later" stepper at 0 → **Done** → changed levels written as `cook` consumption events, pool bumped, `last_made_on` stamped, celebratory toast, back to the recipe page.
10. Photo recipe: one photo at a time with the same Previous/Next pair, zoom dialog (fit ↔ 2.5× pan, paging inside), last Next = Finish → same dialog.
11. Screen stays awake for the whole cook (where the Wake Lock API exists).

#### A3. Edge cases
- `/cookbook/A/cook` → `/cookbook/B/cook` without leaving → **04-R1** (FU-765): recipe A stays on screen until fixed.
- Structured mode with an empty `steps[]` → falls back to the free-text split (honest, documented).
- Free-text step "1 hour 30 minutes" → sniff reads **30** (minutes matched first) — note, not a bug worth fixing (04-R9).
- Unlinked ingredient → plain raw text, no swap, excluded from the finish rows.
- Finish with nothing changed → no writes, no consumption events, pool bump 0 → `204`.
- Timer running → Next → timer **resets** (04-D2: product gap — long timers don't survive a step change).
- Phone backgrounded mid-timer → the 1 s interval is throttled → the countdown runs slow (04-R8).
- Space / arrows while the finish dialog or swap picker is open → still step the recipe underneath (04-R7).
- iOS / WKWebView: the silent-WAV primer is **blocked by CSP** (04-R2) → first Piper utterance after an await may be muted.
- Firefox: no mic button (R-078 copy in Settings explains); browser voice falls back to Piper when configured.
- Exit mid-sentence → narration stops (composable `onBeforeUnmount`); mic indicator clears.
- Reduced motion: progress segment transitions off.

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (free-text recipe, no headcount → recipe servings) | ✓ | ✓ (Fresh style: no servings stepper) | ✓ (structured + voice + Batch) | ✓ (headcount / cook-style / Piper install) | ✓ (`cooked_by_user_id` on the event; voice prefs per user) | ✓ (Piper present in Docker/desktop) | – |

#### A5. Load-bearing conditions
- **375px phone**: header two bands (headcount wraps), nav row three buttons at `md`, step text `text-h4` (FU-763 — owner's call), finish dialog rows one line.
- **Hands-free**: barge-in over narration (FU-723 defer-restart), "stop" semantics, timer chime after a long silence (autoplay gate — toast is load-bearing).
- **Themes × dark**: timer band (`dora-bg-sunken`), highlight tint + accent rule, progress badge `color-mix` washes, `text-color="white"` chips (04-R22).
- **Audio**: Piper vs browser voice vs none; CSP `media-src` (04-R2).
- **Wake lock**: Chromium / Safari 16.4+ / Firefox 126+; silent no-op elsewhere.

#### A6. Release-gate rows
- Structured recipe with a sub-step, a declared timer and a swapped substitute: finish → the substitute's level changes (not the original's), a `cook` consumption event per changed row, pool +N (Batch), `last_made_on` = household today, Stock-item history shows "Used in <recipe>".
- Photo recipe end-to-end on a phone including Finish.
- Sous Chef + mic on Android Chrome: "next" heard while Dora is mid-sentence; narration not clipped at the start (FU-722 candidate fixes).
- Navigate between two cook routes without a reload → the second recipe renders (after 04-R1).

---

## Chunk 05 — Stock Overview + Stocktake
*Source: [`CHUNK_05_stock_overview_stocktake.md`](../05_investigations/finalisation/CHUNK_05_stock_overview_stocktake.md) · analysed 2026-10-23*

### A. Full Systems Test — Stock Overview + Stocktake

#### A1. Preconditions
- Seeded install ≥ 60 items (crosses the 50-row virtual-scroll threshold), a 3-level location tree, ≥ 4 stock groups, essentials, items expired / expiring / low / out, some with linked products, some with usual stores.
- Install flags toggled across runs: **money** (per-row Log price, toolbar Log price), **scanning** (Scan button + action menu, Print QRs), **stocktake** (toolbar button, dashed markers, `/stocktake`), **stock inference** (Dora-thinks header on the level picker; Review phase).
- Admin settings: expiring-soon window ≠ 7, auto-add mode `essential_only`, stocktake default band, auto-tuning on, new-items opt-in.
- A user with `stocktake_last_session_at` set (so the Sweep phase can appear) and ≥ 3 logged purchases on one item (so Review has a confident row).

#### A2. Golden path
Persona: **Dense user**, desktop then phone.
1. `/stock` → toolbar (New item · Scan · Stocktake [N badge, glows only when an essential is overdue] · Bulk select · Log price · Export) · filter toggle · search; filter panel open iff a filter is active.
2. Rows: essential stripe · level square (dashed ring when Dora disagrees or a count is due; the popover says which) · name · zone (click → location filter) · Log price · expiry button (date picker when unset; +1/+7/+14/Clear/Log waste when set) · open/sealed · cart. Attention outline on expired/expiring/essential-low; dimmed on non-essential out.
3. Default sort "Needs attention" → outlined band first ordered expired → essential-out → expiring → essential-low, then soonest expiry, then name.
4. Filters: Needs attention · Expiring soon · Essential · Open; level / sort+direction / location / group; cart and recipe chips from deep links; footer counts (Shown · Needs attention · per level · Essential · On a list) reflect the filtered set.
5. Row click → splitter peek at 58 % (desktop) / `/stock/:id` (phone); long-press on a phone enters bulk select with that row ticked.
6. Bulk bar: Select visible · Deselect all · Add to list… (radio) · Remove from list… (lists the selection is on) · Move location · Restock · Log waste… (one reason, Undo restores expiries) · Print QRs. Deselecting the last row leaves bulk mode.
7. New item: name · level (dot) · location (path search) · group · usual store (logo) · Essential · Stocktake toggle (install default) → row appears sorted; from a scan: OFF suggestion banner, barcode registered on save.
8. Scan → "Action: Open stock item" ↔ "Set to <level>" from inside the overlay; a known item opens / sets; an unknown EAN opens New item prefilled.
9. Export → CSV / Print of the **filtered** set.
10. Stocktake → **Review** ("Dora's fairly sure about these", pre-ticked, "That's right for N items" / "Check them all myself") → **Walk** (card: name, full breadcrumb, "Checked every fortnight · N days overdue", Dora-thinks reason; Still correct / level button / Skip / Push 3 days / Mute) → **Sweep** ("Dora's stopped tracking these": I still keep this… → level picker · Mute · Delete · Leave them be) → summary (checked / changed / skipped / pushed / muted) → "N went Low or Out → Add to a list…" via the shared picker → Done.
11. Back on `/stock` the changed levels show (**05-R5** — currently they don't until reload).

#### A3. Edge cases
- Stocktake switched off → toolbar button, markers and queue fetch gone; `/stocktake` shows "turned off".
- Inference off → no Review phase, no Dora-thinks header; queue ordered most-overdue first; `ranked_by: cadence`.
- Nothing due → "You're all caught up"; first-ever session → Sweep always empty (watermark None).
- Skip is session-only (the item returns next run); Push hides for 3 days without a check; Mute needs confirm and is undone only on the detail page.
- Review row where recorded == believed → no "but is currently" clause.
- Renamed level (e.g. "Out of Stock" → "None left") → legend, picker, footer and scan menu all follow (sequence-keyed); **05-R3**: the runner's Change-level colour breaks (name-keyed).
- Rename an item to a different case of an existing name → accepted (05-R30 — create's comment says the check is case-insensitive; it isn't).
- Delete an item used by a recipe → 422 "Used by N recipes" dialog; delete from the Sweep → lines on draft lists go, done-list lines keep their name.
- Mark open → effective-expiry prompt; Cancel leaves it sealed; Skip opens with no expiry change.
- Expiry +1 on a past date → from today (FU-123 rule — client-side today, 05-R2).
- Auto-add fires on a low/out transition only in `essential_only`/`all` modes and only with exactly one draft → toast names the list.
- ≥ 50 rows → virtual scroll; row heights fixed (64 / 76 phone); no snap.
- Deep links: `?location_id=`, `?attention=1`, `?level_id=`, `?expiring=1`, `?recipe=`, `?create=1`.
- Phone: toolbar icon-only and scrolling, location line and per-row price hidden, 44px row buttons, name wraps two lines.

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (empty state: New item / from recipe / from list) | ✓ | ✓ (flags off: no money/scan/stocktake chrome) | ✓ (keyboard n f / a arrows enter; scan-to-level loop) | ✓ (expiring window, auto-add mode, stocktake cadence/opt-in) | ✓ (per-user disabled alert kinds affect *that* user's outlines; per-user stocktake watermark) | – | – |

#### A5. Load-bearing conditions
- **≥ 500 items**: the server caps a page at 500 and the SPA pages until exhausted; the queue fetch is 500 — pathological beyond.
- **Themes × dark**: attention outline `--q-negative`, selected fill `--q-primary` 14 %, hover `--q-accent` 4 % (05-R22), essential stripe `--brand-secondary-strong`, dashed ring 65 % ink, runner belief wash.
- **Reduced motion**: micro-feedback classes, row transitions.
- **Touch**: 32px level square kept deliberately (R-085 carve-out), 44px cluster buttons, 44px menu rows.
- **Offline**: level flip rolls back with a toast.

#### A6. Release-gate rows
- Admin sets expiring window to 3 days → rows, the bell and the "Expiring soon" chip agree (one rule, `stock_attention.py`).
- Full stocktake with all three phases on a phone; after Done, `/stock` reflects every level change and deletion **without a reload** (05-R5).
- Bulk: select 40 → Add to list → one request; Restock → one request, 40 `StockLevelChange` rows, auto-add fires at most once per item; Log waste → Undo restores every expiry.
- Scan loop "Set to Out of Stock" over 5 items → 5 level writes, markers update, no navigation.

---

## Chunk 06 — Stock-Item Detail
*Source: [`CHUNK_06_stock_item_detail.md`](../05_investigations/finalisation/CHUNK_06_stock_item_detail.md) · analysed 2026-10-23*

### A. Full Systems Test — Stock-Item Detail

#### A1. Preconditions
- Dense persona (seeded showcase): an item with level history, ≥3 finished-list purchases with prices, a waste event, ≥1 linked recipe, ≥1 substitute with a ratio, ≥1 linked product with a current offer, a planned meal in the next 14 days using it.
- Flags: `products` on, `scanning` on, money on, nutrition **complex**, stocktake on (then each flipped off in A3).
- A second draft shopping list exists (so the add-to-list picker fires).

#### A2. Golden path
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

#### A3. Edge cases
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

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (empty states: no recipes / substitutes / barcodes / prices; thin verdict) | ✓ (A2) | ✓ (money + products off → Overview is level/location/expiry/opened/notes only) | ✓ (ratios, QR print, full history) | ✓ (flag flips mid-session) | – (no per-user state on this page except the verdict opt-out) | – | – |

#### A5. Load-bearing conditions
- The detail read is the **de-facto sub-resource API**: cook mode (substitutes), the recipe page (substitutes per ingredient, N reads), the ingredient editor (preferred buys + products), the log-price sheet and the row price button (prefill only) all call `getDetailAsync` and pay for every feed, every lookup and — in complex nutrition — a catalogue match per read (06-R10).
- `_nutrition_is_complex()` **must** run before the entity load (its commit expires the session and the `noload` relationships silently blank) — documented in the handler; any reordering regresses `test_patch_semantics`.
- The verdict's need axis reads the level by FK (`_level_access`), not the relationship — the R-032 trap that once made every verdict `unsure/low`.
- `useBuyVerdict` is a module cache; every mutation site must invalidate it — and today three level-change sites invalidate three *different* sets of caches (06-R4).

#### A6. Release-gate rows
- Open an item in the peek, swap to a second item, confirm name / level / verdict / QR / substitutes all belong to the second item.
- Rename an item to its own name → no error; to another's name (different case) → 422 (depends on 05-R30).
- Opened toggle → Cancel → confirm no PATCH in the network log.
- Unlink a product that a shopping-list line and a recipe ingredient had selected → both selections cleared; detail read still 200.
- Delete an item used by a recipe → 422 with the recipe names, item still present.

---

## Chunk 07 — Zero-Input Pantry (P8-07)
*Source: [`CHUNK_07_zero_input_pantry.md`](../05_investigations/finalisation/CHUNK_07_zero_input_pantry.md) · analysed 2026-10-23*

### A. Full Systems Test — Zero-Input Pantry

#### A1. Preconditions
- Dense seed (it builds beliefs that *disagree* on purpose: ≥4 unique purchase dates on a few items, one cooked-through item, one freshly-checked item; `seed_dense.py:1156–1190`).
- Signed-in user with all four toggles at their defaults (stock **on**, cookbook / shopping / planner **off**); a second user to prove per-user scoping.
- Household timezone set to something far from UTC (AEST) for the R-021 edge.

#### A2. Golden path
1. Stock overview → rows whose belief disagrees with the recorded level wear a **dashed** level box; agreeing rows wear nothing (silence is the default).
2. Open a dashed row's level picker → header *Dora thinks low* + the reason ("Bought 12 days ago, cooked with 2× since; you usually finish in about 14 days.").
3. Pick a level → ring disappears **immediately** (belief now echoes a fresh hard signal: *Updated today*, high confidence, `is_inferred=false`).
4. Open the item → *Dora thinks …* card expanded shows reason, *Confidence: medium*, *This differs / agrees with your recorded level*.
5. Stocktake → the queue is ordered **uncertain → overdue → confident** and Review-phase rows carry *Dora thinks …* in belief's own words; confirm one → belief reads *You confirmed this today*.
6. Cook a recipe to the finish dialog, mark an ingredient down → a `ConsumptionEvent(source='cook')` lands → the item's reason gains ", cooked with 1× since" and its progress advances by 0.34 of a cycle.
7. Settings → Assistant → *Stock overview hints* **off** → every ring, header and card vanishes on the next load; stocktake order becomes pure overdue; `/stock-items/beliefs` answers `{enabled:false}`.
8. *Cookbook hints* **on** → a cookable recipe with a required ingredient Dora believes **out** shows *May be short* (names in the tooltip); a not-cookable recipe whose every missing ingredient is believed back shows *May be cookable*; the cookbook's filters and `missing_count` are unchanged.
9. *Shopping list hints* **on** → an open list gains *Dora thinks you may be out of…* with ≤ N items not already on the list, A–Z; nothing is added for you.
10. *Meal planner hints* **on** → an uncooked planned entry whose recipe is at risk shows the Dora glyph (amber) with "since you planned this"; cooked entries never do.
11. Suggestions (dashboard/alerts surface) → when an in-play item (on an open list, or needed by a meal within 7 days) has a **low**-confidence belief, a *Still have Rice?* quick-check appears, ≤ 3 at a time, least-confident first, deep-linking to the item.
12. Sign in as the second user → their own toggles apply; the first user's choices don't leak.

#### A3. Edge cases
- No purchases, no checks → *Not sure yet. No purchases or checks on record.* (confidence 0.1, never a ring).
- One purchase only → thin-data path: *Based on the last recorded level (last known 9 days ago). Not enough history yet.* — confidence ≤ 0.4, halves every 30 stale days, never differs.
- Belief can never reach **high** on *Out* (ceiling 0.525) — so the overlay never remarks "out" with high confidence; the recipe hint's medium gate still lets it through.
- Level changed **this morning** in AEST → `_as_date` takes the **UTC** date of the timestamp while `today` is household-local → "Updated 1 day ago" / a check made today not pinning (07-R1).
- Recorded level missing (item with no level) → thin path needs `recorded is not None`; falls to *Not sure yet*.
- Duplicate same-day purchases → `mean_gap_days` ignores zero gaps (pinned by `test_cadence_math`).
- Recipe with an **unlinked** required ingredient → no hint ever (honest `None` stays `None`).
- Recipe where one of three missing ingredients is believed back → no *May be cookable* (all-or-nothing).
- Shopping surface on a **done** list → no suggestions; candidates exclude items already on the list.
- Toggle flipped mid-session → the SPA cache holds the old beliefs until the next `loadAsync(force)` — the overview reloads on mount, the detail page refetches on level change only (FU-851 class).
- `GET /beliefs` with no session user (shouldn't happen behind auth) → `{enabled:false}`.
- Pantry of 400 items → still 3 queries for the gather; the shopping surface gathers for **every** item not on the list by design (§6 of the proposal).

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (all *Not sure yet*, no rings) | ✓ (A2) | ✓ (purchases via finished lists only; no cooking → calendar-only decay) | ✓ (all four surfaces on) | – (no install-wide flag; D-12 made it per-user) | ✓ (step 12) | – | – |

#### A5. Load-bearing conditions
- `compute_belief` is pure; every threshold is a module constant; the safety envelope in the impl plan §1.3 is derived from exactly those constants — change one and the "Out can't be high" guarantee may fall (07-R10 proposes a test that pins it).
- `gather_beliefs_for_items` resolves levels by FK (`_level_access`) — but `inference_overlay.divergent_items` reads `item.stock_level` off the relationship (07-R2).
- `_HARD_SIGNAL_FRESH_DAYS = 3` and the "confirmed today" wording both depend on `_as_date` agreeing with `household_today` (07-R1).
- Every consumer gates through `inference_overlay.surface_enabled` / `SURFACE_FLAGS` — the one map from surface to column.

#### A6. Release-gate rows
- In an AEST household, change a level at 08:00 local → picker header reads *Updated today* and the ring is gone.
- Toggle *Stock overview hints* off → `/stock-items/beliefs` → `{enabled:false, beliefs:{}}` and no row is dashed.
- Cookbook hints on + the dense seed's at-risk recipe → *May be short* chip names the right ingredient; `missing_count` unchanged.
- Cook-mode finish marking an item down → one `ConsumptionEvent` row, `source='cook'`, `from_sequence < to_sequence`.

---

## Chunk 08 — Dashboard
*Source: [`CHUNK_08_dashboard.md`](../05_investigations/finalisation/CHUNK_08_dashboard.md) · analysed 2026-10-23*

### A. Full Systems Test — Dashboard

#### A1. Preconditions
- Dense seed; money **on**, products **on**, batch cooking **on**; a budget set with a few finished shops this period; ≥1 item expiring inside the household's `expiring_soon_window_days`; a plan for the next fortnight with a cooked batch covering some days; one item that went Out in the last week and is needed by a planned meal; a tracked product at a new low.
- A second browser profile (or a fresh user) with no saved layout.

#### A2. Golden path
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

#### A3. Edge cases
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

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (positive empties; score null) | ✓ (A2) | ✓ (money/products off → 6 cards, 3-signal score) | ✓ (reorder/drag/opt-in) | – (no install-wide dashboard setting) | ✓ (layout per user) | – | – |

#### A5. Load-bearing conditions
- `cardRendered` is the **one** predicate both the template `v-if` and the grid-parity maths read; a second hide-when-empty condition at a call site re-creates the dead-air bug.
- `DEFAULT_VISIBLE_COUNT = 7` is a resolved decision held by `dashboardCards.spec.ts`; a new card without `defaultHidden` fails the spec on purpose.
- `loadAll` force-refreshes the score (`refreshDoraScore`) because the composable's 5-min stale window hid budget-period changes; the four mutations the composable's header names never invalidated it (FU-896).
- The summary's `_cook_verdicts` reads the planner's pool model (`planned_meals`) — the dashboard, the planner chips and `/shortfall` are three readings of one allocation.
- `resolve_levels_by_item` returns `None` for an unlevelled item and every consumer must guard it — one here doesn't (08-R1).

#### A6. Release-gate rows
- Default install, 1280px: seven cards, zero dead regions; 375px: one column, Cook/Cards icon-only, no horizontal scroll.
- Money off: no Budget card, no Budget row in Kitchen health, no money hint in a week of reloads (`dashboardMessages.spec` covers the pool; the card gate needs eyes — FU-868).
- Change the budget period in Settings, return within five minutes → Kitchen health's Budget row reflects the new window.
- Reorder two cards, reload, second device → same order.

---

## Chunk 09 — Alerts + Suggestions
*Source: [`CHUNK_09_alerts_suggestions.md`](../05_investigations/finalisation/CHUNK_09_alerts_suggestions.md) · analysed 2026-10-23*

### A. Full Systems Test — Alerts + Suggestions

#### A1. Preconditions
- Dense seed with: an expired item, an item inside the household's expiring-soon window, an essential item Out and one Low, a draft list with `planned_shop_date` tomorrow and another dated last week, next week empty on the plan, ≥3 past-day unreconciled meals (auto-drain **off**), a price watch at or above a tracked product's current price; money **on**, products **on**.
- A second user; VAPID keys configured (admin page) in a browser that supports web push; a device without VAPID for the "ask an admin" state.

#### A2. Golden path
1. Header bell: badge = **actionable count** (high + medium) — the FYI nudges are listed but never counted; bell colour red when any high, amber when only medium; tooltip *N things need attention*.
2. Open the panel → *What needs your attention* → cards severity-first: *X has expired* (Push 7 days · Clear expiry · **Log waste**), *X expires soon* (Push 7 days · Clear expiry · **Recipes** → `/cookbook?usesStockItem=`), *Essential X is out of stock* (level picker · cart), *Did you forget your shopping?* (Open list), *Shopping day tomorrow: …*, *No meals planned for next week* (Plan meals), *N past meals need confirming* (Reconcile), *Product hit your price* ($ · cart via linked item · Price history).
3. Tap a card → its surface (item page / list / planner / reconcile / price history); tap an action → *Done.* toast, panel refreshes; **Log waste** → the stock row's reason dialog → expiry cleared → alert gone, Undo brings it back.
4. **Snooze** (7 days) → card moves to *Snoozed (N)*; **Unsnooze** restores; **Dismiss** → gone for this **episode** only: push the item's expiry to a new date → a new alert; **Dismiss all** → active set empty, *Nothing to do right now*.
5. Settings → Notifications → *In-app alerts*: toggle a kind off → its cards, counts **and** stock-row outlines vanish for this user only (second user unchanged); *Discard alerts after 7 days* → alerts whose episode began earlier drop out; *Price watches* list with remove.
6. *Push notifications on this device* → permission prompt → subscribed; within the hour a newly fired actionable alert arrives as a notification; tapping it opens Dora with the bell panel open (`?alerts=open`); FYI nudges never push.
7. *Evening brief* on → at 19:00 household-local a single notification with tomorrow's meals + any shopping day; nothing is sent on an empty evening; a second scheduler tick inside the hour does not double-send.
8. Admin → System → Alert thresholds: set the expiring-soon window to 14 → the evaluator, the rows and the *Use it up* card all move together; Admin → System → Push: paste VAPID keys (private key encrypted at rest) → the user-side toggle enables.
9. Dora bubble shows a suggestion count badge (red when any high); open chat → *Suggestions* cards on top: *Use X soon*, *You're over budget this week*, *You're probably due for X*, *Buy less X?*, *Still have X?* (quick check), *N past meals need confirming* — each with its primary action, **Snooze 1d**, **Dismiss**, **Why?**; ≤ 8 with every firing kind guaranteed one slot.
10. Dismiss a suggestion → it stays gone until the condition changes; snooze → back after 24 h; the nightly 03:30 job prunes elapsed snoozes.

#### A3. Edge cases
- A kind the client doesn't know (backend ahead) → row renders with only snooze/dismiss and a generic bell icon (pinned by `alertRow.spec`).
- Discard window `Never` (null) keeps everything; an unknown value → 400.
- `shopping_day` and `shopping_overdue` are separate keys on the same list: dismissing the reminder does not silence the missed-shop nudge; moving the planned date is a new episode.
- `no_planned_meals` keys on next week's ISO label → clears the moment a meal lands in that week; its detail formats the date range server-side (`%a %d %b`, 09-R14).
- Essential item restocked then run out again → new episode (`essential_out:<level_since>`); an item with `stock_level_last_updated` None keys on today.
- Price watch: current price ≤ threshold → fires once per **offer**; a new observation at or under the line → a new alert; money off → no price alerts and no toggle.
- Alert key longer than 255 chars → silently a no-op (never a Postgres 500).
- Push: browser unsupported / permission denied / VAPID unset → the right notice above a disabled toggle; unsubscribe tears down server-side first; a 404/410 from the push service prunes the subscription mid-fan; dry-run sender when VAPID is missing never stamps the ledger.
- Daily brief with the user opted in but no device → nothing stamped; subscribe later that evening → the brief still fires that evening.
- Bell polls every 60 s **only while the tab is visible**; returning to the tab refreshes immediately; opening the panel refreshes and hydrates the stock store (for the level picker).
- Suggestions: the household-wide suppression table (no `user_id`) means one user's dismiss hides the suggestion for **everyone** (09-D1).
- Over-budget suggestion body carries `$` literals regardless of the install's currency (09-R6).
- `generate_likely_due` skips items with < 3 purchases or a mean gap > 90 days.
- A user with every kind disabled → bell badge 0, *Nothing to do right now*, no row outlines — and the stock page's *Needs attention* chip matches nothing (FU-702).

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (one FYI nudge: *No meals planned*) | ✓ (A2) | ✓ (money/products off → 6 kinds, no price watch toggle, no deals email section) | ✓ (push + brief + discard window) | ✓ (thresholds, VAPID) | ✓ (prefs + interactions per user; suppression **not**, 09-D1) | ✓ (single-worker scheduler note, VAPID keygen) | – |

#### A5. Load-bearing conditions
- One evaluator: `get_alerts.py` emits the three per-item kinds from `stock_attention`'s predicates; `get_stock_items` reads `resolve_attention_map` with the same user's disabled kinds — the bell, the rows and the chip can't disagree.
- Tier is **derived** from severity (`is_actionable`), never stored; `AlertPreference` is an on/off switch only.
- Every alert is one **episode** (key carries the fact that started it); dismiss holds for the episode; `started_on` is what the discard window measures.
- `AlertInteraction.last_pushed_at` is the only delivery dedup; the push job clears it when a key leaves the user's set so a re-fire re-notifies.
- Scheduler runs in exactly one gunicorn worker; two workers would double-send (documented in `startup.py`).

#### A6. Release-gate rows
- Badge count = number of high+medium cards in the panel (feedback L438: "6 vs 10" — pinned by `test__alerts__actionable_count_equals_high_plus_medium_in_items` and `alertStore.spec`).
- Disable `expiring_soon` for user A → A's rows lose their outline, user B's don't.
- Dismiss an expiry alert, change the expiry → a fresh alert.
- With VAPID configured: subscribe, fire an alert, receive the push, tap → panel open.
- 19:00 household-local brief arrives once; 19:20 restart does not resend.

---

## Chunk 10 — Products / Price History / Deals
*Source: [`CHUNK_10_products_history_deals.md`](../05_investigations/finalisation/CHUNK_10_products_history_deals.md) · analysed 2026-10-23*

### A. Full Systems Test — Products / History / Deals

#### A1. Preconditions
- Products overlay has data (`features.products` data-presence flag true → nav shows **My Products**; it hides entirely when the catalogue is empty — R-029). Fastest seed: `POST /api/products` ×3 with one store on special (`price_was > price_now`), or an `/api/ingest` push.
- At least one `Store` exists (Settings → Stores) — `POST /products` refuses unknown store names.
- A user with a **verified** email, `deals_email_enabled`, `send_deals_on_day` = today's weekday, SMTP configured (or drive `send_deals_email(now=…, _send_email=spy)`).
- Money features on (watch thresholds are dollar amounts).

#### A2. Golden path
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

#### A3. Edge cases
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

#### A4. Persona coverage
- **Pantry-only household (no products):** sees nothing from this chunk — nav entry hidden, no deals mail (no products → empty digest → silent), price watches unreachable. Direct URL to `/my-products` shows the empty state. ✅ hide-when-off.
- **Products user who never links:** product-only shopping lines (chunk 3), delete works, deals mail works; "Stock items without products" glows permanently because every stock item is an orphan → 10-D3.
- **Admin:** sets Product Search URL (ingestion page), curates stores, manages who gets the deals mail.
- **Phone shopper logging prices in an aisle:** `PriceEntry` three-across + numeric keypad gaps → FU-704.

#### A5. Load-bearing conditions
- `StockItemProduct.UNIQUE(product_id)` — a product links to at most one stock item (every `linked_stock_item_*` stamp assumes it).
- `is_custom` is load-bearing: excluded from the sync list, never adopted by ingest dedupe.
- `AlertInteraction` ledger key is ISO-week scoped — changing send day mid-week cannot double-mail.
- `GetBestDealsHandler` is live via the email (`DEAL_POOL_SIZE = 40`) even though its HTTP route is orphaned (FU-838).
- `DiscountChip` is the one `% off` renderer (FU-885) — but the *rule* "on special" still has four client copies (10-R23).

#### A6. Release-gate rows
- [ ] Weekly deals mail "See all deals" opens My Products (after 10-R1).
- [ ] My Products shows the whole catalogue on an install with > 50 products (after 10-R9).
- [ ] Store logos render in the Capacitor shell / split host (after 10-R35).
- [ ] Price watch set from My Products fires as a `price_drop` alert on the next lower offer and never twice for the same offer.
- [ ] Deleting a product leaves finished-list lines named.

---

## Chunk 11 — Assistant (Dora)
*Source: [`CHUNK_11_assistant.md`](../05_investigations/finalisation/CHUNK_11_assistant.md) · analysed 2026-10-23*

### A. Full Systems Test — Assistant

#### A1. Preconditions
- A signed-in user with `show_assistant` on (default). Basic mode needs nothing else.
- AI mode: a reachable provider — Ollama at a LAN URL with a tool-capable model, or a paid key with `DORA_SECRET_ENCRYPTION_KEY` set; provider **verified** by a probe before the Mode picker / slider offers it.
- Exactly one draft shopping list (the assistant's "primary" is inferred from draft count).
- Voice: Piper binary + a downloaded voice (server), or a browser with voices; mic permission for voice input (Chrome; Firefox has no `SpeechRecognition`, FU-788).

#### A2. Golden path
| # | Step | Expect |
|---|---|---|
| G1 | Fresh user loads the app | Launcher pops in once (spring entrance), "Hi! I'm Dora" hint appears after 1.5 s, auto-hides at 9 s; X dismisses it **for this user** for good. |
| G2 | Click the launcher | Chat opens with a greeting using the capitalised username, 4 chips (reply-biased), header shows **Basic** on the slider; header hint names the current page. |
| G3 | Basic: "what's low" | Lists low/out items from the loaded stock store with "See Stock" button; mascot mood follows the reply; typewriter reveal + lip-flap. |
| G4 | Basic: "add milk and eggs" | Resolves against the pantry; unambiguous ones added to the one draft list via the shared composable; ambiguous/not-found named, never guessed. |
| G5 | Basic: "where's the flour" | **Today: always "doesn't have a location set yet"** → 11-R4. Expect the location name. |
| G6 | Basic: "1 cup to ml", "substitute for buttermilk", "tell me a joke", "what can I do here" | Each answered locally; conversion reads the generated units table. |
| G7 | Settings → Assistant → Ollama base URL blur → model picked → Test connection | Card turns green "Connected"; Mode picker gains "Ollama"; `User.assistant_ready` true; slider becomes enabled. |
| G8 | Slider → AI | PATCH `llm_enabled`, status probe, header shows **AI**; chips switch to the natural-language pool. |
| G9 | AI: "any specials on cheese" | `find_deals` runs; reply grounded on rows; nav button offered — **today it targets `/product-search`, a retired route** → 11-R3. |
| G10 | AI: "mark eggs as low" | Confirm card ("Set Eggs to Low Stock? (was Stocked)") → Confirm → `/confirm` → level changed, super-excited face. Cancel → "No worries". |
| G11 | AI: "cross off bread on my list" | **Today: 500 — `_primary_list` reads a dropped column** → 11-R1. Expect a tick confirm card. |
| G12 | AI: "what am I wasting often?" | **Today: `NameError: timezone`** → 11-R2. Expect most-wasted list. |
| G13 | AI: "add 3 apples and some milk" | Multi-item card; ambiguous item shows candidate chips; Add commits only when every ambiguity is resolved. |
| G14 | Suggestions badge on launcher → open chat | Suggestion cards at the top with Accept (navigates + 1 h snooze), Snooze 1d, Dismiss, Why?. |
| G15 | Mute/unmute button | Persists `voice_output_enabled`; replies spoken via Piper (or browser voice fallback); mic button push-to-talk fills the draft. |
| G16 | Settings → Assistant → "Show digital assistant chat bubble" off | Launcher gone everywhere (MainLayout `v-if`). |
| G17 | 21 `/ask` calls inside a minute | 429 with `Retry-After`; chat falls back to Basic for that turn. |

#### A3. Edge cases
| # | Case | Expect (and what the code does today) |
|---|---|---|
| E1 | AI on, Ollama down | Red banner "AI mode unavailable. Using basic mode." with reason + Retry + Settings; launcher shows the offline face only if AI was seen working this session ✅. |
| E2 | Provider details saved but never probed | Status "Not tested" (amber); not offered in Mode; slider dimmed-dashed and tapping it routes to Settings ✅. |
| E3 | Paid provider, no `DORA_SECRET_ENCRYPTION_KEY` | Banner inside Providers; saving a key returns 422 with the reason ✅. |
| E4 | Product name contains "ignore your instructions and…" | SECURITY block + control-byte strip; model summarises as data (B.1) — manual eval only. |
| E5 | "push the bread expiry by 5000 days" | `invalid`: "That's more than 10 years…" ✅ (B.3). |
| E6 | Two or zero draft lists | add-to-list / tick / add-recipe say "that only works when you have exactly one" — **after 11-R1** (today two of the three crash). |
| E7 | `current_path` with newline/injection | Sanitised to path-safe chars, capped 200 ✅ (B.4). |
| E8 | Model returns a tool name that isn't registered | `{"error": "unknown tool"}` fed back; no crash ✅. |
| E9 | Firefox | Mic hidden (no API); Piper speaks; browser voice probe reports no voices → Settings explains ✅ (FU-751 verify). |
| E10 | iOS / Android, reply spoken after an LLM round-trip | May fall back to browser voice or stay silent (autoplay gesture credit) — FU-629 open; silent-WAV primer in place. |
| E11 | Model chains 4 tool rounds | `_MAX_TOOL_ROUNDS=3` → "I got a bit tangled up" ✅. |
| E12 | Household in +10, 08:00 local, "what's the plan" in Basic | `getMealPlan` compares against the **UTC** date → yesterday's entry counts as upcoming → 11-R33. |
| E13 | Ask "where's milk cheapest" with no linked products | `no_linked_products` note; nav → `/product-search` (dead) → 11-R3. |
| E14 | Ask about budget with money off | `budget_status` `disabled` note points at "Settings → Kitchen setup → Money" while the schema description says "Settings → Preferences" → 11-R27. |

#### A4. Persona coverage
- **Pantry-only, no LLM (the majority):** Basic mode is the whole product here — greet, data lookups off the stores, one action verb, conversions, substitutes, page help, jokes. Must never look like a failure state ✅ (no banner, no offline face).
- **Self-hoster with Ollama:** probe + model picker from `/api/tags`; LAN URLs allowed (documented SSRF trade-off: rate cap + audit row).
- **Paid-API user:** key encrypted at rest, write-only, `has_api_key` derived; text leaves the box — help should say so (H9).
- **Phone user:** 24 px slider (FU-663), mic push-to-talk, voice autoplay limits (FU-629), 70dvh card.
- **Admin:** nothing admin-only remains on the assistant (per-user since the §7.1 redesign) except `DORA_SECRET_ENCRYPTION_KEY`.

#### A5. Load-bearing conditions
- **The mutation gate**: action tool calls short-circuit into a proposal; `/confirm` re-validates; the model never writes (B.0). Every finding below must preserve it.
- "Primary list" = exactly one draft list (`resolve_quick_add_target`), not a stored flag.
- `UserLlmProvider.verified` is the only thing that makes a provider selectable; any edit clears it.
- `APP_OVERVIEW` is in every AI prompt — its size is a model-quality lever (11-D1).
- Basic mode reads Pinia stores that other pages hydrate; `ensureRecipeData` loads what it needs on demand.

#### A6. Release-gate rows
- [ ] Every `PROPOSERS` entry executes against an empty database without raising (after 11-R1).
- [ ] Every data tool executes with `{}` against an empty database without raising (after 11-R2).
- [ ] Every `_TOOL_NAV` path is a live SPA route (after 11-R3).
- [ ] Basic-mode "where is X" names the location (after 11-R4).
- [ ] 21st `/ask` in a minute → 429 + `Retry-After`; probe rate limit → 429 too (after 11-R15).
- [ ] A product name carrying an instruction does not steer the model (manual, one prompt).

---

## Chunk 12 — Reports / Memory (P8-09), Waste, Budget
*Source: [`CHUNK_12_reports_memory.md`](../05_investigations/finalisation/CHUNK_12_reports_memory.md) · analysed 2026-10-23*

### A. Full Systems Test — Reports / Waste / Budget

#### A1. Preconditions
- Money features on (admin); otherwise only Waste and Kitchen memory render and the money endpoints 403 (R-058).
- At least two **finished** shopping lists with ticked, priced lines (actual or picked-offer price), ideally at two stores and in two stock groups; one list from the prior window for "vs last period".
- Several cook events (`POST /recipes/<id>/cook`), two or more logged prices for the same item (shelf-price or finished-list harvest), a few waste events.
- A household budget set in Settings → Budget (any member can set it).

#### A2. Golden path
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

#### A3. Edge cases
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

#### A4. Persona coverage
- **Pantry-only, money off:** two cards (Waste, Kitchen memory) + the capture flow — the page stays worth a nav slot (review §3.11) ✅.
- **Money on, no products:** Spend by store attributes via the five-rung store ladder (usual store / planned / purchased) — populated without any product (FU-815) ✅; Price changes works from logged prices alone (FU-703 D3) ✅; savings line hidden.
- **Products user:** savings line against shelf price (FU-831 will re-baseline); price drops on the dashboard.
- **Non-admin member:** can set the household budget (kitchen-setup class) ✅; cannot turn money on.
- **Phone:** one-column grid under 1024; reason grid 3-up under 600; 44 px rows ✅.

#### A5. Load-bearing conditions
- "Spent" = **ticked** lines on **finished** lists, priced by the actual→picked ladder, completed inside the window, `deferred_by_budget = false` — the same rule in `period_spent`, history, spend-by-store/category/YoY and savings (12-R10 makes it one function).
- Reports' store attribution goes through `resolve_store_id` with `last_purchase_store_id=None` (a record, not a guess) ✅.
- Repertoire is deliberately not range-scoped (365 days) ✅.
- Money endpoints refuse at the server (R-058); the page gates before asking ✅.
- Waste events are reason-only (D13); the signal survives for the Dora Score ✅.

#### A6. Release-gate rows
- [ ] A shop finished at 08:00 local on the first day of a period counts toward that period (after 12-R2).
- [ ] Spend-by-store total == spend-by-category total == savings `total_spent` on one fixture (after 12-R10).
- [ ] "Bought most" counts ticked lines only (after 12-R4).
- [ ] Window label dates match the household date near midnight (after 12-R3).
- [ ] `getStockValueAsync` / `GET /reports/stock-value-over-time` gone (after 12-R1) or fixed and consumed.

---

## Chunk 13 — Settings shell
*Source: [`CHUNK_13_settings_shell.md`](../05_investigations/finalisation/CHUNK_13_settings_shell.md) · analysed 2026-10-23*

### A. Full Systems Test — Settings shell

#### A1. Preconditions
- Two accounts: one admin, one member; the admin has a profile picture set.
- `DORA_SECRET_ENCRYPTION_KEY` **unset** on one run, set on another (the Email/Push banners differ).
- Money on, scanning off, nutrition `off` (so Budget shows, QR labels and Nutrition matching hide — R-029 nav honesty).

#### A2. Golden path
| # | Step | Expect |
|---|---|---|
| G1 | Avatar button in the header → `/settings/account` | Shell opens on Account; sidebar groups Account · Preferences · Kitchen setup · About; admin sees the Settings/Admin pill toggle, member sees a plain "Settings" h1. |
| G2 | Upload a profile picture (tile click) | Immediate save, "Profile picture updated.", avatar updates in header + Account + Users list (version bump); "Remove photo" appears; "Or pick one of ours" presets save the same way. |
| G3 | Edit username + email, change password, Save changes | One `/auth/me` PATCH with only the changed fields, then `/auth/me/password`; "Changes saved."; Discard resets drafts; leaving mid-edit prompts (R-020 guard). |
| G4 | Appearance → Mode Dark, Theme Blueberry, Font Lexend, Size Large | Four separate saves, each toasts; swatches re-render for dark; theme key saved as `blueberry-dark`; System mode stores `system-blueberry`. |
| G5 | Notifications → discard-after 7 days, toggle a kind off, remove a price watch | Each saves + bell refreshes; Push section shows the right blocker (no VAPID → ChannelSetupNote with admin "Set up push" link; member gets "Ask an admin"); Email section hidden until product data exists. |
| G6 | Voice → enable output, pick a neural voice, preview | One save sets `voice_id` + `voice_engine='piper'`; preview plays; "Device default voice" switches engine to browser and remembers the neural pick. |
| G7 | Kitchen setup → Stock locations: New zone → + Area → + Section → rename → delete | Prompt dialogs; counts roll up server-side; delete warns "N items stored here will become unassigned"; expansion survives reload (R-026 carve-out). |
| G8 | Stock groups / Cuisines / Categories / Tools / Meal slots | Same `VocabListEditor` anatomy; meal slots reorder with ↑↓ and the planner picks up the change (store-routed). |
| G9 | Stores: New store → click logo tile → upload → rename inline → delete | Logo saves immediately; delete toast reports cleared item/line references. |
| G10 | Admin toggle → Users: Add user with a chosen password; Change password (generate); toggle Active off | Chosen password never echoed; generated one shown once with Copy; deactivation confirm → the user's next `/auth/me` 401s with the deactivated message. |
| G11 | Admin → Region: Match this device | Timezone + locale + units saved; currency untouched; HSR/Nutri-Score nudge only in matching regions and only if scheme is `none`. |
| G12 | Admin → Email: set SMTP password without the encryption key | Banner shown first; save refused with the DORA_SECRET_ENCRYPTION_KEY message. With the key: "SMTP password saved.", `smtp_password_configured=true`, Notifications' email channel unlocks. |
| G13 | Admin → Stock: scanning on | Sidebar gains "QR labels" without reload (scanning composable + flags refreshed). |
| G14 | Admin → Audit log: change retention, filter by request id, open a row, Export CSV | Retention saved on blur; detail dialog "Find related" re-filters; CSV downloads the **loaded page** only. |
| G15 | Phone (<1024) | Sidebar replaced by the tab strip; Account/About tabs navigate directly (no one-chip strip); header fits at 320 px with icon-only sign-out. |

#### A3. Edge cases
| # | Case | Expect (and what the code does today) |
|---|---|---|
| E1 | Admin PATCHes `/app-settings` with `nutrition_mode: "bogus"` | **Today: 500** — handler returns a tuple, caller reads `.invalid_reason` → 13-R1. Expect 400 "Invalid settings." |
| E2 | Admin edits another user's email to `not-an-email` or to an address already on another account | **Today: accepted** — admin path has no format/uniqueness check (self-serve path has both) → 13-R2. |
| E3 | Two admins, one deactivated; delete the remaining active admin | **Today: allowed** — delete guard counts `is_admin` only, not active admins → 13-R3. Expect refusal. |
| E4 | Account page: new password of 7 chars | Inline "At least 8 characters" — correct today but from a hardcoded `8`, not `MIN_PASSWORD_LENGTH` → 13-R12 (FU-656). |
| E5 | Member (non-admin) with a Product Search URL configured | Main-nav "Product Search" entry **never appears** for members — the URL is read from the admin-only `/app-settings` → 13-R4 (FU-186 intent was "every user"). |
| E6 | Install with 51+ users opens Admin → Users | **Today: list silently capped at 50** (`DEFAULT_LIMIT`) → 13-R5 (FU-668 class; low likelihood). |
| E7 | Theme row holds a legacy key (`pesto-noir`) | `familyAndModeOf` → null → picker shows System/Pesto while the app renders pesto-dark (themeService maps legacy at apply time, the Preferences decoder doesn't) → 13-R6. |
| E8 | Appearance page unmounts | `matchMedia` change listener never removed → 13-R7 (leak, minor). |
| E9 | Admin deep-links `/settings/admin/...` as a member | Router guard (`index.ts:154`) redirects; the 12 per-page banners are unreachable → 13-R13. |
| E10 | `/health` with the DB down | Flags fall back to conservative defaults; `features` still emits strings for `nutrition_mode`/`nutrition_rating_scheme` under a `Record<string, boolean>` type → 13-R16. |
| E11 | Audit log on a page with more rows than shown | "Export CSV" exports only the loaded rows; the label promises more → 13-R20 (copy). |
| E12 | Sign out from a dirty Account page | Guard suppressed; no false "discard?" prompt ✅. |
| E13 | QR labels reached by URL with scanning off | Banner with link to Admin → Stock ✅. |

#### A4. Persona coverage
- **Member:** Account/Preferences/Notifications/Voice/Kitchen setup/About; sees "Ask an admin" variants; cannot reach admin pages. (E5 bites them.)
- **Admin:** everything above + the three admin groups; self-row toggles disabled with tooltips.
- **Fresh install / self-host op:** Email + Push banners drive the encryption-key setup; Region "Match this device" is the one-click regionalisation; About carries the instance URL only on native.
- **Phone:** tab strip, inline rows keep toggles beside labels, 44 px tabs/chips.

#### A5. Load-bearing conditions
- Install-wide facts reach non-admins only through `/health` (`features`, `locale_policy`, `image_policy`, `cooking_policy`, `budget_policy`, `reconcile_policy`, `stocktake_policy`) — every admin save that changes one must refresh the matching composable cache (all pages do today ✅; the pattern is hand-copied ×10 → 13-R9).
- `get_or_create_app_setting` is memoised per app context (FU-560) — admin PATCH mutates the same identity-map row ✅.
- Password policy is one Python authority (`validate_password`) used by self-serve, admin-create and admin-set ✅; the SPA mirrors the length only.
- Secrets never ride the DTO (`*_configured` bools) ✅ (tested).

#### A6. Release-gate rows
- [ ] Invalid `nutrition_mode` → 400, not 500 (13-R1).
- [ ] Admin email edit validates + dedupes like self-serve (13-R2).
- [ ] Deleting the last **active** admin is refused (13-R3).
- [ ] A member sees the Product Search nav entry when a URL is set (13-R4).

---

## Chunk 14 — Onboarding
*Source: [`CHUNK_14_onboarding.md`](../05_investigations/finalisation/CHUNK_14_onboarding.md) · analysed 2026-10-23*

### A. Full Systems Test — Onboarding

#### A1. Preconditions
- A fresh DB (migrations only — three stock levels, five meal slots, the fixed recipe vocab; **zero** groups/locations/items/users).
- Run A: first admin created on `/setup` (chunk 15) → lands in `/welcome` as **first user** (admin). Run B: a second account registered later → lands in `/welcome` as a **joining user** (two steps only).
- Device: a phone-width and a desktop-width pass; one pass with `prefers-reduced-motion`.

#### A2. Golden path (first user)
| # | Step | Expect |
|---|---|---|
| G1 | Land on `/welcome` | Dark pinned canvas (`WelcomeLayout`), slim top row: mascot · Story/Setup rail · "Skip onboarding". Story scene 1 "The weekly shop is detective work." rises in. |
| G2 | Next ×3 | Scene 2 draws the loop ring then cascades six nodes + Dora; tapping a node swaps the sell line; scene 3 Dora "thinking"; scene 4 switch panel; last CTA "Set up in about a minute". Rail dots jump anywhere, nothing gated. |
| G3 | Setup → Welcome | Hero greets by username; avatar tile (upload or preset) + Undo; theme cards System/Light/Dark painted in their own tokens; Font segmented. Nothing saved yet. |
| G4 | Next → Build your Dora | Household panel: People (blank = per recipe), Timezone (**pre-filled with this device's zone** because the install is still UTC), Units segmented. Six feature cards seeded from `/app-settings` (Stocktakes + Auto-add on; Spend/Nutrition/Batch/Barcodes off); "Loading your install's current settings…" until the GET lands. |
| G5 | Next → Your stock | Three pick panels (locations by zone, groups, items by pack), every default ticked, `N of M` + All/None per panel, "Add your own" row (items also take Group/Location selects of the picked names). Untick Bathroom + Laundry, add "Garage", add "Coffee" in Pantry/Pantry. |
| G6 | Next → You're all set | Confetti (not under reduced motion); recap rows each with Change; Extras → "Add a demo recipe" (first user only); first-steps tiles 1–4 (+ "Watch your prices" only if Spend tracking is on, + "Pick Dora's voice"); tip linking the guides. |
| G7 | Finish | One `PATCH /auth/me` (theme/font/image), one `PATCH /app-settings` (only what changed), `POST /onboarding/seed` (filters sent only when not "all"), own group/location creates, `POST /onboarding/seed-items`, `POST /onboarding/seed-demo` if ticked, `POST /onboarding/complete`, `/auth/me` refresh → `/`. Dashboard shows the seeded items; Settings → System reflects the picks; `/health` flags refreshed in-session. |
| G8 | Re-open `/welcome` by URL | Bounced to `/` (completed). |
| G9 | Skip onboarding (from any step) | `POST /onboarding/complete` only, nothing else applied; dashboard shows the 24-h "finish setting up" banner; Continue → `POST /onboarding/restart` → back in the wizard with the saved draft. |
| G10 | Joining user (Run B) | Welcome → You're all set only; no features/stock steps; no demo toggle; Finish writes theme/font/avatar + complete. |

#### A3. Edge cases
| # | Case | Expect (and what the code does today) |
|---|---|---|
| E1 | First user already created a meal plan for this week (via "Plan the week" tile then Continue-onboarding → Finish with demo ticked) | **Today a second `MealPlan` for the same `start_date` is inserted** (no uniqueness, no reuse) → 14-R1; the planner's duplicate-week hazard from chunk 2 applies. |
| E2 | Picked pack items "Pasta", "Garlic", "Olive oil" + demo recipe | **Today the demo creates "Spaghetti pasta" and "Garlic cloves" alongside them** (only "Olive oil" is reused) → 14-R2. |
| E3 | `POST /onboarding/seed-items` / `seed-demo` on a DB whose level sequences aren't 0-based | Both pick `sorted(levels)[0]` rather than the Stocked role → 14-R6 (works today because migrations seed 0/1/2). |
| E4 | Refresh mid-wizard | Draft (every pick, step, scene, household, features, own entries) restored from `localStorage` per user ✓. |
| E5 | Finish fails at `seed-items` (e.g. server down) | Prefs + settings already written; wizard stays with the error; re-Finish re-sends only the diff and the seeds are idempotent ✓ (documented partial-apply, see 14-D2). |
| E6 | Re-run the wizard with theme `blueberry` saved | No theme card highlighted; Finish leaves theme untouched ✓ (documented). |
| E7 | Install timezone already set to a real zone before the first user finishes | Wizard pre-fills the stored zone, not the device's ✓. |
| E8 | Reduced motion | Ring/nodes shown immediately, no confetti, no scene rise ✓. |
| E9 | Non-admin somehow `first_user` | Features step shown but baseline never loads → cards disabled forever, Finish sends nothing for it ✓ (documented). |
| E10 | `/onboarding/seed` with `groups:false, locations:false` | 200 with zero counts (deliberate) ✓. |
| E11 | User renames the "Dinner" meal slot before Finish | Demo plan entry still written with `slot="Dinner"` / `time_of_day="Dinner"` literals → 14-R7 (orphan slot name). |
| E12 | Story scene 4 switch panel | Shows "AI assistant — on" though AI mode is per-user and off by default → 14-D3 (honesty nit). |

#### A4. Persona coverage
- **Fresh self-host admin:** full track ✓. **Joining household member:** short track ✓. **Dense/Power user:** draft survives, non-linear rail ✓. **Multi-user:** `first_user = users ≤ 1` so a second account never sees install steps ✓. **Managed/demo:** showcase `demo` user has no `onboarding_completed_at` → sees the full wizard every reset (14-D4 — owner: intended showcase or set it complete?). **Phone:** hero stacks, theme cards 3-up, chips 44 px ✓.

#### A5. Load-bearing conditions
- Draft-until-Finish (L35): every advance is side-effect-free; `applyDraft` is the single write path, in dependency order ✓.
- Seeds are idempotent by name; the server resolves group/location **names**, so items can reference catalogue entries that have no ids until Finish (FU-191) ✓.
- Only the features **diff** is sent, so a richer stored value (nutrition `complex`) survives an untouched card ✓.
- Router gate: `onboarding_completed_at === null` ⇒ `/welcome`; the two auth-store refreshes after complete/restart are what stop the bounce loop ✓.

#### A6. Release-gate rows
- [ ] Finish with the demo recipe on a week that already has a plan reuses that plan (after 14-R1).
- [ ] Demo ingredients reuse "Pasta" / "Garlic" / "Olive oil" from the packs (after 14-R2).
- [ ] Skip → dashboard banner → Continue → wizard restores the draft (today ✓; keep).
- [ ] A first user who leaves Timezone untouched ends with the **device** zone saved, not UTC (today ✓ — closes FU-632 #48's timezone half).

---

## Chunk 15 — Auth shell
*Source: [`CHUNK_15_auth_shell.md`](../05_investigations/finalisation/CHUNK_15_auth_shell.md) · analysed 2026-10-23*

### A. Full Systems Test — Auth shell

#### A1. Preconditions
- Fresh DB (no users) for the bootstrap path; a populated DB with `dora`/`dora` + one non-admin for the rest.
- One run with SMTP configured + `DORA_SECRET_ENCRYPTION_KEY` set (email flows live), one without (dry-run → "Forgot password?" hidden).
- Browser cold-load with the API stopped (cannot-connect), then started (retry).
- Native build (Capacitor) for `/setup/backend`; phone width + `prefers-reduced-motion` passes.

#### A2. Golden path
| # | Step | Expect |
|---|---|---|
| G1 | Cold load, API down | `#pre-mount-splash` (midnight `#1f2647`, pulsing logo) → Vue mounts → `SplashScreen` quiet-blob backdrop, cycling flavour text → after the 8 s boot-probe timeout + 1 retry: "Can't reach Dora's brain", Try again; "Change instance URL" only when a runtime URL override is set. |
| G2 | Start the API, Try again | Probe resumes the same loop; splash fades (CSS, paint-independent) and unmounts after 360 ms. |
| G3 | Fresh DB → any URL | `/auth/bootstrap-required` true → `/setup` (one-time badge, username / optional email / password) → `POST /auth/bootstrap-admin` → auto-login, `email_verified=true`, redirect `/` → onboarding (chunk 14). Second visit to `/setup` → `/` or `/login`. |
| G4 | `/login` sign-in | Opaque 401 copy on bad creds; success → `redirect` query honoured; 5 wrong attempts/min → 429 with `Retry-After` and the generic "Sign-in failed" line. |
| G5 | Register from `/login` | Amber "Need an account? Register" flips the card; min 8 chars inline; 422 field errors inline; success → auto-login → `/welcome`; verification email queued if an address was given. |
| G6 | Forgot password (SMTP on) | Ghost "Forgot password?" visible; `/forgot-password` → 204 always → "If that address is registered…"; mail carries `#/reset-password?token=…` (hash deep link). |
| G7 | Reset link | `/reset-password?token` → new + confirm → 200 → "Continue to sign in"; every other device of that user is signed out on its next `/me`. Reused/expired/foreign-purpose token → 400 inline. |
| G8 | Verify link | `/verify-email?token` → "Email verified" → `/login?verified=1` toast; bad token → "Resend verification" dialog (anti-enumeration 204). |
| G9 | Native first launch | `/setup/backend` → URL normalised (`https://` + `/api`), probed via `/auth/me`, rolled back on failure, stored in Capacitor Preferences; web visitors to the route → `/settings/about`. |
| G10 | Typo'd URL | Fullscreen 404 with the same blobs + mascot + glass card as login; "Take me home". |
| G11 | Sign out (Settings) | `POST /auth/logout` audited, session cleared, list state + SW API cache wiped, `/login`. |
| G12 | Silent 401 mid-session | Interceptor clears the user + caches; next navigation lands on `/login?redirect=…`. |

#### A3. Edge cases
| # | Case | Expect (and what the code does today) |
|---|---|---|
| E1 | Install behind nginx/Caddy/Traefik (the normal self-host) | **Today every user shares one `remote_addr`** (the proxy's): the 5/min login limit, 10/min register limit and the audit `actor_ip` are per-install, not per-client → 15-R1. |
| E2 | Dev server with `debug=True`, someone signs in | **Today the plaintext password is written to the log** by `audit_incoming_request` at DEBUG → 15-R2. |
| E3 | Register with an email | **Today no "check your inbox" toast** — the server's `verification_sent` flag has no reader → 15-R3. |
| E4 | Sign out, then inspect cookies | **Today `dora_csrf` survives** (`clear_cookie` is never called); harmless (re-minted, not a credential) but the pairing the docstring promises doesn't exist → 15-R4. |
| E5 | Deactivated user holding a live cookie hits a non-admin route | Passes until the next `/me` (FU-655, tracked; closes with FU-654). |
| E6 | Admin changes their own password on Users page | Session re-stamped, other devices out ✓ (chunk 13). |
| E7 | Backgrounded tab during boot | Splash fade is CSS + timer, never a Vue transition ✓ (DR-8). |
| E8 | Reduced motion | Blobs static, mascot still, card no enter animation, `will-change` released ✓. |
| E9 | Firefox on Android | Thin seam left of the mascot — mitigated with `will-change`/`backface-visibility`, **unconfirmed** (FU-797; stays a verify item). |
| E10 | Reset-password token in the URL | Accepted risk A.7 (single-use, hashed, 1 h) — unchanged. |
| E11 | 10+ registrations from one test client | In-memory buckets 429 the suite; tests drain `_buckets` directly (`test_route_auth_enforcement.py:231–235`) — a test seam, not a product issue. |
| E12 | Non-admin GETs `/api/app-settings/probe` | 403 today; after 13-R19 the route is gone and the pinned list must shrink or the reverse-count test fails → 15-R12. |

#### A4. Persona coverage
- **Fresh self-host op:** G1→G3 in one sitting; `ADMIN_BOOTSTRAP_EMAIL` lock honoured (410 with a generic message). **Member:** G4/G5, no admin surfaces. **Phone:** mascot tucks top-centre at <760, card full-width, 48 px buttons. **Native:** G9 + "Change instance URL" on the error splash. **Managed/demo:** `demo_mode` capability → banner (chunk 19).

#### A5. Load-bearing conditions
- One auth gate (`middleware.require_auth_if_protected`) + one allowlist (`PUBLIC_ENDPOINTS`), both pinned by the anonymous sweep and the allowlist-rot test ✓.
- CSRF double-submit: cookie minted on any `/api` response, header echoed by the one axios client; raw-`fetch` callers must spread `csrfHeader()` (R-047) ✓.
- Password policy is one Python authority (`validate_password`, NIST shape, no admin override) — the TS side mirrors only the length (FU-656).
- Session staleness: `pwd_v` stamped at login/register/bootstrap, compared in `get_me`; every password change bumps `password_changed_at` ✓.
- Deep links to the hash router go through `spa_deep_link` only ✓.

#### A6. Release-gate rows
- [ ] Behind a reverse proxy, two clients get independent login rate limits and distinct audit IPs (after 15-R1).
- [ ] No request body from `/auth/*` reaches any log at any level (after 15-R2).
- [ ] Register with an email → "Check your inbox" toast (after 15-R3).
- [ ] Fullscreen 404 renders through `AuthShell` (after 15-R6) — one palette, one mascot animation.

---

## Chunk 16 — Ingestion API + companion seam
*Source: [`CHUNK_16_ingestion_api.md`](../05_investigations/finalisation/CHUNK_16_ingestion_api.md) · analysed 2026-10-23*

### A. Full Systems Test — Ingestion API + API access

#### A1. Preconditions
- An admin session; at least one Dora store created (Settings → Stores); a terminal with `curl` (or the companion configured with `DORA_INGEST_URL` + `DORA_INGEST_KEY`).
- One run on SQLite, one on Postgres (the idempotency expiry path depends on DateTime(timezone) round-tripping — the code carries a SQLite tz-coercion comment at `submit_ingestion_batch.py:252–258`).
- A second, non-admin user for the permission edges.

#### A2. Golden path (persona: self-host admin wiring an external producer)
| # | Step | Expect |
|---|---|---|
| G1 | Settings → Admin → **API access** | Header "API access — Bearer keys for authenticated sources that push data into Dora"; empty state "No keys yet…"; Refresh + **New key** actions. Page reachable with zero products (never gated on `features.products`). |
| G2 | New key → label "home box" → Create | Reveal-once dialog "Copy this key now"; copy → toast "Key copied"; Done. Row appears: avatar key icon in primary, "Created …", "Never used", "Accepted 0 · Skipped 0 · Failed 0". `GET /ingestion-sources` never carries `key` or `key_hash`. |
| G3 | `curl -H "Authorization: Bearer <key>" POST /api/ingest` with one product using `"store": "ExternalMart"` + one offer | 200 `{accepted: [], skipped: [{kind: product, ref, reason: store_not_mapped}], failed: [{kind: offer, reason: product_unknown}], idempotent_replay: false}`. Row counters: Skipped 1 · Failed 1; "Last used" stamped. |
| G4 | Expand the row | **Store mappings** card lists "ExternalMart" with a `pending` badge, "Awaiting mapping · last pushed …"; the row header shows "1 pending". |
| G5 | Pick a Dora store in the picker | `PUT …/store-mappings` → badge gone, caption "→ <store>". |
| G6 | Re-push the same batch (new `Idempotency-Key`) | `accepted: [product "created (provenance: …)", offer "appended"]`. Product appears under My products at that store with the pushed price (chunk 10). Counters: Accepted +2. |
| G7 | Re-push the identical batch with the **same** `Idempotency-Key` | 200 `idempotent_replay: true`, all three arrays empty, counters unchanged. |
| G8 | Re-push with a new key, same `observed_at` + `price_now` | product `updated`; offer `skipped: duplicate`. New price at a new `observed_at` → `appended` and the product's current price moves. |
| G9 | Push by `store_id` instead of `store` (the companion's path) | Accepted without any mapping row; an unknown id → `skipped: store_unknown`; both fields at once → 400 "Give exactly one of `store` or `store_id`". |
| G10 | `POST /api/ingest/link-status` with the same `(store, merchant_stockcode)` | `product_id` set, `linked_stock_item_*` null. Link the product to a stock item in Dora → repeat → `linked_stock_item_id` + name filled. |
| G11 | `GET /api/ingest/products` | The pushed product listed with `store` = "ExternalMart" (the caller's own name), `store_id`, `merchant_stockcode`. Mark the product inactive in My products → it drops out of the list (PF-8). |
| G12 | `DELETE /api/ingest/products/<id>` | 204; gone from My products; second call 404. |
| G13 | `GET /api/ingest/stores` + `/stores/<id>/image` | Every Dora store with `has_image`; the image route serves the uploaded logo with `Cache-Control: max-age=3600`, 404 when none. |
| G14 | Overflow menu → **Disable** | Badge "disabled", avatar greyed; next push → 401 "Bearer token missing or invalid." Enable → accepted again. |
| G15 | Rename → "garage box" | Header label updates in place. |
| G16 | **Revoke** → confirm | Row removed; push → 401; `GET …/store-mappings` for that id → 404 (mappings cascade-deleted). |

#### A3. Edge cases
- Missing header / `Basic` scheme / empty token / unknown key → 401 on every `/api/ingest*` route (middleware exempts them from the session cookie; auth is entirely in `authenticate_ingestion_request`).
- Non-admin session on `/api/ingestion-sources*` → 403 (pinned by `test_route_auth_enforcement.py:207–214`); anonymous → 401. The SPA route is admin-gated by the shared `admin/*` router guard.
- Malformed JSON / unknown field (`price_observations[]`, `merchant`) → 400 `{detail: "Malformed payload.", errors: "<pydantic text>"}` — the batch is rejected whole, nothing lands (contrast: a bad *record* never fails the batch).
- `pack_count: 0`, `price_now: 0`, `size_value: 0` → 400 (Field `gt=0`); `price_was` absent → stored as `price_now`.
- An image that isn't a `data:image/…;base64,` URL → dropped, product still accepted, previous image kept; > 6,000,000 chars → whole-batch 400 (the companion drops such images client-side before sending).
- Store deleted in Dora while mapped → mapping's `store_id` goes NULL (`ondelete=SET NULL`) → next push for that name quarantines again with `store_not_mapped`; a push by the deleted `store_id` → `store_unknown`.
- Hand-entered (custom) product with the same name at the same store → ingest creates its own row (OD-2) — **but `link-status` reports the custom row as "already in Dora"** (16-R8).
- Product pushed with **no offer** (companion: out-of-stock, `price_now ≤ 0`) → lands as an *available* product at **$0.00** (16-R5).
- Replay of an `Idempotency-Key` **after its 7-day TTL** → 500 (16-R2).
- link-status with 201 items → 400 (`_MAX_ITEMS = 200`); `GET /ingest/products?limit=banana|0`, `offset=-1` → 400; `limit=9999` silently capped at 500.
- Rate limiting: none on the bearer lane (32-byte `token_urlsafe` keys; brute force infeasible — waived, see C9).
- Phone width: the row's three actions collapse into one overflow menu (owner 2026-10-15); mapping rows wrap the picker under the name at < 600 px.

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (page works with zero products) | – | – | ✓ (curl path, guide) | ✓ (owner of the page) | ✓ (members: 403 on API, no nav entry) | ✓ (key lives in the producer's env; proxy/TLS → chunk 19) | ✓ (same artifact; key per instance) |

#### A5. Load-bearing conditions
- **Postgres + SQLite** — idempotency `expires_at` tz round-trip; unique index behaviour on replay (16-R2).
- **360×640** — the API access row + mapping picker wrap (owner-fixed 2026-10-15; keep as a regression check).
- **Bad network** — the companion treats a non-2xx as "Push failed"; the body text is what the user reads (16-R34).
- Themes × light/dark — `text-color="white"` badges on `warning`/`grey` (D-002 floor on Pesto Dark; C11).

#### A6. Release-gate rows
1. Mint → copy → push → counters → revoke → 401 round-trip (G2–G3, G14–G16) on the release build.
2. Idempotent replay is a no-op, and a replay after the TTL does **not** 500 (G7 + 16-R2 fix).
3. `link-status` never reports a custom product (16-R8 fix) — the companion's "unsave" deletes by that id.
4. The power-user guide's sample `curl` body is accepted verbatim by the release build (16-R1).

---

## Chunk 17 — Offline / PWA / native
*Source: [`CHUNK_17_offline_pwa_native.md`](../05_investigations/finalisation/CHUNK_17_offline_pwa_native.md) · analysed 2026-10-23*

### A. Full Systems Test — Offline / PWA / native

#### A1. Preconditions
- A **built** frontend (`npm run build` → `dist/spa` in PWA mode) served over HTTPS or `localhost` (the SW will not register on plain HTTP); a plain-HTTP LAN install too, for the "install needs HTTPS" and camera-warning paths.
- Chrome desktop + Chrome Android (installed from the address-bar prompt), Safari iOS (Add to Home Screen), Firefox desktop (no install prompt).
- The Android APK (`quasar build -m capacitor -T android` → Android Studio) on a real phone; a LAN backend at `http://192.168.x.x:5170`.
- Two user accounts for the cache-eviction check; DevTools → Network → Offline.

#### A2. Golden path (persona: a household member on a phone)
| # | Step | Expect |
|---|---|---|
| G1 | First HTTPS load | DevTools → Application → Service Workers shows `sw.js` active; Manifest shows "Dashy Dora", theme `#f5c462`, standalone, 3 shortcuts (Primary list · Shop now · Add item), share target → `/cookbook`. |
| G2 | Settings → About → **Install as an app** | Chrome: "Install Dora as an app" button → native prompt → accepted → toast "Installing Dora…"; the section then reads "Dora is installed on this device." iOS Safari: the Share → Add to Home Screen banner. Plain HTTP: "Installing needs HTTPS. This Dora is on plain http://". Firefox: "Install isn't available in this browser…". |
| G3 | Launch from the home screen | Standalone window, no browser chrome; `display-mode: standalone` marks it installed so the button never nags. |
| G4 | Long-press the icon (Android) | The three shortcuts; "Shop now" lands on `/shop-now` → the primary list's shop route (or the lists overview). Share a recipe URL from Chrome → Dora appears in the share sheet → `/cookbook` opens the paste-import dialog pre-filled. |
| G5 | Go offline (airplane mode) | Toast "You're offline. You can look around, but not make changes."; red sticky `OfflineBanner` with the same text + Retry; pages already visited render from the `dora-api` cache; a stock-level change fails, rolls back, and is reported — nothing says "queued". |
| G6 | Server stopped, network up | Banner "Can't reach Dora. You can look around, but not make changes."; probe backs off 5 s → 60 s; Retry shows a spinner then "Still can't reach the server." |
| G7 | Reconnect / server back | Within one probe (immediately if the app was backgrounded and comes back — `visibilitychange` re-probes): banner slides away, toast "Back online.", no phantom changes. |
| G8 | Deploy a new frontend build, then navigate | New SW installs with `skipWaiting` + `clientsClaim`; `controllerchange` fires with a controller already in place → accent `UpdateBanner` "A new version of Dora is ready. Reload to pick it up." → Reload → new build. Dismiss hides it for this page load. |
| G9 | Sign out, sign in as another user | `clearApiResponseCache()` ran on logout (and on any 401): no trace of the first user's pantry/lists/recipes from cache. |
| G10 | Cook mode / Shop mode | Screen stays on for the whole session (Wake Lock); re-acquired after the phone is unlocked; released on leaving the page. Unsupported browsers silently skip. |
| G11 | Android APK first launch | `/setup/backend` before anything else; enter the LAN URL → "Connected…" → `/` → login. Second launch skips the gate (Preferences). Settings → About shows the saved URL + Change. |
| G12 | APK: open a dialog with the keyboard up | Dialog stays above the keyboard (`interactive-widget=resizes-content`; iOS uses the `--vv-inset-*` fallback). |

#### A3. Edge cases
- `navigator.onLine` lies (captive portal, half-dropped mobile data): the banner says offline; **Retry forces the probe** and a success flips `online` back (the 2026-08-17 fix) — pin it.
- Slow backend (> 5 s): the SW's `NetworkFirst` timeout serves the **cached** GET while axios still believes it is live → the page shows yesterday's data with no indicator (C8, 17-D2).
- Toggle **Push notifications** on Settings → Notifications: `usePushSubscription` registers `/push-sw.js` at scope `/` — the same scope `sw.js` controls → the registration is *replaced*, the Workbox worker (and all offline caching) is gone until the next load re-registers `sw.js`, and each swap fires `controllerchange` → a spurious **"A new version of Dora is ready"** banner (17-R1).
- Visiting Settings → Notifications at all (not just toggling) runs `refresh()` → `ensureRegistration()` → the same swap (17-R1).
- Plain-HTTP LAN install: no SW, no install prompt, no wake lock (SecurityError swallowed), camera "may not allow" warning; everything else works.
- Capacitor: `caches` may be absent → eviction is a no-op (by design); Push reads "unsupported" (no PushManager in the WebView); the About install section still renders the "Try Chrome on Android…" caption inside the native app (17-R9).
- Native, LAN backend over `http://`: the WebView origin is `https://localhost`, so every API call is mixed content — `allowMixedContent: true` is what makes it work; whether Android 9+'s cleartext policy also needs `usesCleartextTraffic` is **unverified** (17-R10).
- Idle PWA tab for a day: `dora-api` cache entries expire at 24 h / 200 entries; images at 7 / 30 days.
- A user who dismissed the update banner, then opens a second tab: the second tab boots on the new SW → no banner there (correct).
- Backgrounded tab: the health poll stands down (`scheduleNext` on hidden); the bell poll does the same (chunk 9) — both re-probe on `visibilitychange`.

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (install prompt on first visit) | – | – | ✓ (APK, instance URL) | – | ✓ (G9 cache eviction) | ✓ (HTTP vs HTTPS behaviour; `nginx.conf` SW no-cache) | ✓ (HTTPS → full PWA) |

#### A5. Load-bearing conditions
- **Android PWA** (G1–G8), **native Capacitor** (G11–G12), **iOS PWA** (G2 banner; wake lock on Safari 16.4+), **bad network / offline** (G5–G7, A3 first three), **360×640** (banner + Retry wrap), **all themes × light/dark** (`--q-negative` / `--q-accent` banners on `--text-on-primary`), **reduced-motion** (banner transitions use `--motion-*`).

#### A6. Release-gate rows
1. G5–G7 on a phone: offline banner copy, no "queued" promise anywhere (incl. `offline.html` — 17-R2), Retry corrects `navigator.onLine`.
2. G8 after a real redeploy: exactly one update banner; **no** banner from visiting Settings → Notifications (17-R1).
3. G9 two-user cache eviction on one device.
4. G11 APK first-run → LAN `http://` backend reachable (17-R10 confirm).

---

## Chunk 18 — Backup & restore + Import
*Source: [`CHUNK_18_backup_restore_import.md`](../05_investigations/finalisation/CHUNK_18_backup_restore_import.md) · analysed 2026-10-23*

### A. Full Systems Test — Backup & restore + Import

#### A1. Preconditions
- An admin session; a non-admin for the 403 checks; a populated install (recipes **with structured steps**, a meal plan, a shopping list with a product-only line, a custom product, a user with LLM provider settings).
- One run on SQLite, one on Postgres (restore is raw `insert()` per row inside one transaction; FK enforcement differs).
- A second, empty install (or a wiped `data/`) for the "restore onto fresh" path.
- `DORA_DATA_DIR` writable; a second path for the storage-path override; a > 500 MB JSON for the chunked path (optional).

#### A2. Golden path (persona: self-host admin)
| # | Step | Expect |
|---|---|---|
| G1 | Settings → Admin → Data → **Backup & restore** | Header "Backup & restore — Save your install to a JSON file. Passwords are never included."; library "Keeps the most recent 5"; empty state "No backups yet." |
| G2 | **New backup** → dialog | Core data / Optional groups with All/None; Optional (System settings, User accounts, Historic offers) **off**; ticking one shows the amber "This backup will include …" banner. |
| G3 | Generate (defaults) | **Today: 400 "Unknown backup section(s): product_barcodes."** → toast "Couldn't create backup." (18-R2). After the fix: row appears with timestamp · size · "N sections" · "by <admin>"; file at `<data>/backups/dora-backup-<date>-<id8>.json`; sha256 recorded. |
| G4 | Six more backups | Library holds 5; the oldest two are gone from disk and the table (retention). |
| G5 | Row → **Download** | `dora-backup-<date>.json`, `schema_version: 1`, `sections[]` list, excluded columns absent (`password_hash`, `smtp_password_encrypted`, `vapid_private_key_encrypted`). |
| G6 | Row → **Restore this backup** → confirm | One-click `all_skip_duplicates`; toast "Restore complete. No new rows. Everything was a duplicate." on the same install. |
| G7 | Row → **Delete** → confirm | Row gone, file gone; a second delete 404s. |
| G8 | **Restore from a file** → drop G5's file | Chunked upload (progress bar) → inspect → "Backup preview — Exported … by …", per-section tree with counts, duplicates greyed with a `duplicate` chip, "N of M selected · K duplicates skipped". |
| G9 | Tick three stock items → **Restore selection** → confirm | **Today: 500 (KeyError `meal_recipes`) → "Restore failed" (18-R1).** After the fix: report dialog "Restored 3 row(s), skipped 0", per-section rows, warnings expander; **Reload now**. |
| G10 | **Restore all (skip duplicates)** on the fresh install | Every section lands in FK order (vocab before recipes, steps before step links, products before lines); report lists all touched sections (today the report omits the 9 sections the SPA list doesn't know — 18-R3). |
| G11 | **Library settings** → retention 3, storage path `/mnt/backups` → Save | Toast; next create writes there; unwritable path → 500 "Could not write backup file: …" surfaced as the toast caption. |
| G12 | Settings → Admin → Data → **Import** → Download template | `dora-import-stock_items.csv` with BOM, headers `name,level,location,group,expiry,is_essential`, the Rice example row, one `#` comment row. |
| G13 | Fill 10 rows (one bad level, one unknown location) → drop the CSV | Upload → "Reading spreadsheet…" → single-sheet (no picker) → Map columns auto-filled → Preview 5 rows → Options. |
| G14 | **Import** (defaults) → confirm | Result "Imported 8 row(s) — 0 skipped · 2 error(s)"; chips ok/err; **Download error rows (CSV)**; the 8 items exist at Stocked level with `stocktake_alerts_are_enabled` = install default. |
| G15 | Re-import the same file with *Create missing locations* on | 8 `dup`, the location is created as a zone, 1 err (bad level), 1 ok. |
| G16 | *Halt on first error* on → Import | "Import halted — … (rolled back)", nothing landed. |
| G17 | `.xlsx` with two sheets | "Pick a sheet" radio group appears; mapping snaps to that sheet's auto-pick. |

#### A3. Edge cases
- Non-admin → every `/api/data/*` route 403 (admin sweep in `test_route_auth_enforcement`); the SPA routes sit under the `admin/*` guard.
- Backup JSON with `schema_version: 2` → 400 "newer than this server supports"; missing → 400; non-dict body → 400 with the three-shape hint.
- Upload > 2 GB → client refuses before upload; chunk offset mismatch → 400 with `errors.received` → the composable retries up to 3× then surfaces "Chunk offset mismatch".
- Stale staged files are swept on the next `/uploads/start` (1 h TTL); a successful restore/import **consumes** the staged file (second use → 404 "Upload").
- Restore where `saved_products` is unticked but a product-only shopping line is → the Product is pulled in by `HARD_FK_PULL_IN`; a line whose product isn't in the backup is skipped with a warning (REQUIRED_FKS).
- Restore of `users` → accounts land **without** passwords (admin must reset); `app_settings` → skipped as `singleton` duplicate when a row exists; SMTP / VAPID secrets never round-trip.
- Restored `User` rows change the caller's `is_admin` → "Close" refreshes `authStore`; a deleted-self → 401 → login.
- Meal plans on a fresh install restore with `recipe_id` FKs resolved against restored recipes (post-rework); the stale `meal_id` entries in `REQUIRED_FKS` are inert.
- Import: `#`-prefixed rows stripped (template comment row); BOM stripped; blank trailing rows skipped silently; a row with data but no name → "Missing 'name' value."; level "low" matches "Low Stock" by substring; ambiguous → error; `expiry` accepts ISO, `D/M/Y`, `D-M-Y`, then `M/D/Y` **regardless of the install locale** (18-R12); `is_essential` truthy set includes `✓`.
- Import never creates stock **levels**; locations are created as top-level **zones**; groups as bare names.
- Two admins creating backups at once → distinct ids/filenames; retention runs after each.
- `storage_path` pointing at a path that later disappears → download/restore 404 "Backup file"; delete still removes the row.
- Phone width: library rows wrap (icon · text · 3 icon actions); mapping grid reflows to one column; the result dialog's virtual scroll caps at 360 px.

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (G10 restore onto empty) | ✓ (large backup, `PREVIEW_ROW_LIMIT` 500 → "… and N more") | – | ✓ (import templates) | ✓ (owner of both pages) | ✓ (users section, `created_by`) | ✓ (storage path, retention, FU-717 deploy exclude) | ✓ (same; path likely a mounted volume) |

#### A5. Load-bearing conditions
- **SQLite + Postgres** (raw inserts, FK enforcement, `DateTime` round-trip through `fromisoformat`).
- **Bad network** mid-upload (chunk retry + offset resume); **1920+** (mapping grid auto-fill) and **360×640** (library rows).
- **Themes × dark** — `color="warning"` chips with `text-color="dark"` / `"white"` (C11).

#### A6. Release-gate rows
1. G2–G3 **New backup with defaults succeeds** (18-R2) and the file round-trips through G8–G10 on a fresh install, including recipe steps/tools/tags (VERIFY cookbook 6/7/8 bullets).
2. G9 **Restore selection** works (18-R1).
3. G12–G16 template → import → error CSV loop.
4. Credential exclusion spot-check on a downloaded file (G5).

---

## Chunk 19 — Ops / self-host
*Source: [`CHUNK_19_ops_self_host.md`](../05_investigations/finalisation/CHUNK_19_ops_self_host.md) · analysed 2026-10-23*

### A. Full Systems Test — Ops / self-host

#### A1. Preconditions
- A clean Linux box with Docker Compose v2.24+; a second box (or VM) to reach the stack from another host; a reverse proxy with TLS for the HTTPS run.
- A Windows and a Linux machine for the desktop bundle (`build-windows.ps1`, `build-linux.sh --appimage`).
- A copy of a production SQLite DB from an older schema for the migration run; a Postgres 16 for the Postgres run (`compose.dev.yml`).
- `pip-audit` installed for the security script.

#### A2. Golden path (persona: self-host operator, first deploy)
| # | Step | Expect |
|---|---|---|
| G1 | `git clone … && cp .env.example .env` and set `DORA_SECRET_KEY`, `DORA_CORS_ORIGINS`, `ADMIN_BOOTSTRAP_EMAIL`, `DORA_SECRET_ENCRYPTION_KEY` | Boots. Leave one of the three required vars blank → container exits non-zero with the "Refusing to start … Missing:" banner on stderr. |
| G2 | `docker compose up --build` | Image builds (Node 22, Piper, default voice); `startup.sh` picks gunicorn (production); `[startup] dora_api pid=…`; nginx foreground; `docker ps` healthy via `/healthz`. **Today the SPA is built in SPA mode (no `sw.js`) — 19-R1.** |
| G3 | Browse from another machine to `http://<host>:5174` | SPA loads, talks to `http://<host>:5170/api` (hostname fallback). **If `web_app/.env` existed at build time it talks to `localhost:5170` instead — 19-R2.** |
| G4 | First boot | Default compose → stderr WARNING "DORA_ENV=production and DORA_SECURE_COOKIES=false" (every boot, by default — 19-D1); `upgrade()` applies 156 migrations; `alembic_version` = `f2a6c8e1b4d7`; `/api/health` → `schema_version == schema_version_db`, `profile: production`, features block. |
| G5 | `docker compose exec dashy_dora python scripts/mint_ingestion_key.py --label companion` | Prints the raw key only on stdout; a second run revokes the first and mints one. `set_product_search_url.py http://host:5175` sets the nav link. |
| G6 | Redeploy a newer image | Migrations apply; `_warn_on_schema_drift` is silent; SPA caches roll (nginx `index.html` no-cache, hashed assets immutable). With a **stale DB** (old `create_all` file): boot continues and logs `SCHEMA DRIFT DETECTED … Missing columns: …`. |
| G7 | Logs | `/app/logs/dapi.log` rotates at midnight (`dapi.log.YYYY-MM-DD`, 14 kept); every line carries `[req=…] [user=…]`; `docker logs` shows gunicorn access + app stdout. At the default `DORA_LOG_LEVEL=ERROR` a 400 leaves **no trace** (FU-640). |
| G8 | Scheduler | At 03:00 server time the audit prune runs; 03:30 snooze prune; `:30` alerts push, `:45` daily brief, `:15` deals email all self-gate when unconfigured; `DORA_WEB_CONCURRENCY=2` → gunicorn boot warning about duplicated jobs. |
| G9 | Help → About | "Dashy Dora 0.7.0"; update check hits GitHub — **today `BenTalese/DashyDora`** (19-R3) → "Couldn't check for updates (HTTP Error 404…)" unless GitHub redirects. |
| G10 | `DORA_DEMO_MODE=true` | Boot drops + recreates the schema and seeds the showcase (`demo`/`demo`); the "Demo mode. This sample data resets periodically." pill shows on every page; reset every 60 min (`DORA_DEMO_RESET_MINUTES`). |
| G11 | Desktop: `.\packaging\build-windows.ps1 -Clean` → `dist\Dora\Dora.exe` | Per-user dirs under `%LOCALAPPDATA%\Dora\`, `.secret_key` + `.secret_encryption_key` generated, SQLite pinned, production profile with the gate skipped, random localhost port, default browser opens, Ctrl-C quits. Piper bin + voices seeded into `AppSetting` when bundled. |
| G12 | `scripts/security-audit.sh` | `pip-audit --strict` clean; `npm audit` only the accepted low items. |
| G13 | `pytest tests/test_migrations.py` against Postgres (`compose.dev.yml up postgres`) | 7/7 incl. `upgrade_head_runs_on_postgres`. |

#### A3. Edge cases
- `DORA_ENV=prod` alias → profile production; `/health.profile` reports `"prod"` (19-R9).
- `DORA_SKIP_PROD_VALIDATION=true` on a server → gate and cookie warning both silenced (documented "never set this in a server deployment"; compose deliberately doesn't forward it, but `env_file` does — comment says so).
- `DORA_DB_URL` **and** `DORA_DB_PATH` set → URL wins; `DORA_DB_PATH=` (empty) → treated as unset; relative paths resolve against cwd (`/app` in the container).
- Legacy `./data/dora.data.db` + new `DORA_DATA_DIR` → moved once; populated target → warning, legacy left.
- `DORA_LOG_LEVEL=banana` → `getattr(logging, 'BANANA')` is None → falls back to debug/INFO default silently.
- `appsettings.json` `LOG_LEVEL`/`WEB_APP_*` edits → no effect (19-R5).
- Boot with a feature subpackage whose `__init__` fails to import → routes silently missing (FU-719); rsync exclude deleting a package → same (FU-717/720).
- `/api/health` with the DB down → still 200 with conservative defaults (`setting = None`), `schema_version_db: null`, flags false — a monitoring probe cannot tell "DB down" from "nothing configured" (19-D3).
- gunicorn `timeout=120` vs nginx has **no** `/api/` proxy (API exposed directly on 5170) → no proxy timeout mismatch today; the commented single-port block (nginx.conf:75–82) would need `proxy_read_timeout` ≥ 120 and 15-R1's `ProxyFix`.
- Container healthcheck hits nginx only → a wedged Python API keeps the container "healthy" (documented choice).
- Desktop: port 0 race; `/api/health` not answering within 5 s → exit 2 with a log line; closing the terminal kills the daemon thread.
- Demo mode on Postgres → `drop_all/create_all` on the real DB every hour (by design; disposable).

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (G1–G4) | – | – | ✓ (scripts, env) | ✓ (About/version) | – | ✓ (whole chunk) | ✓ (same image; `DORA_DB_URL` Postgres; FU-405 Phase 4) |

#### A5. Load-bearing conditions
- **SQLite + Postgres** (migrations, FK pragma only on SQLite, demo reset); **Docker** (compose defaults, volumes, healthcheck); **desktop installer** Windows + Linux (G11); **bad network** (version check timeout 4 s, cached 30 min); HTTPS behind a proxy (15-R1 knob).

#### A6. Release-gate rows
1. G2 image ships **PWA mode** (`sw.js` + `manifest.json` present in `/app/web_app/dist/spa`) — 19-R1.
2. G3 from a second machine with `web_app/.env` present on the build host — 19-R2.
3. G4 fresh boot: `schema_version == schema_version_db`, no drift banner, 156 migrations, single head.
4. G9 version check resolves against the real repo — 19-R3.
5. `pytest tests/test_migrations.py tests/test_compose_env_coverage.py` green on SQLite **and** Postgres (G13).

---

## Chunk 20 — Cross-cutting concerns
*Source: [`CHUNK_20_cross_cutting.md`](../05_investigations/finalisation/CHUNK_20_cross_cutting.md) · analysed 2026-10-23*

### A. Full Systems Test — cross-cutting

#### A1. Preconditions
- Every theme family × light/dark (14) available from Settings → Preferences; `prefers-reduced-motion` and `prefers-color-scheme: dark` at the OS; text size each of the four steps.
- Install locale set to `en-AU` then `en-US` (Settings → Admin → System → Region), currency `AUD` → `USD` → `JPY`.
- A way to break a page (DevTools: throw in a component) and to make the API return 500 / go away.
- Phone (360×640) + 1920 desktop; a hardware keyboard.

#### A2. Golden path (persona: a household member, any page)
| # | Step | Expect |
|---|---|---|
| G1 | Switch theme in Preferences | Every surface recolours live, including SVG/charts (donut, price chart, Reports) — `useThemePalette` version bump; no reload. Quasar palette (`--q-primary` etc.) follows. |
| G2 | Switch text size Small → Extra large | Root font-size 14 → 16.5 → 20.5 → 23 px; every rem-based text scales; icon-only controls keep 44 px targets; no page gains a horizontal scroll at 360 px. |
| G3 | Change locale to `en-US` and currency to `USD` | Within one health refresh every money render reads `$1,234.56` US-style and every date `7/17/2026`; the Region page preview matches; dates stay the **same calendar day** west of Greenwich (local-midnight parse). |
| G4 | `JPY` | Still renders 2 decimals (`¥1,234.00`) — documented limitation in `useMoney.ts:45–48`. |
| G5 | Press `?` | Cheatsheet lists Global + the current page's scope; `/` focuses search; `g s` navigates; keys are ignored while typing in an input. |
| G6 | Submit a form with a bad field | Inline `error-message` on the field (friendly copy from `error_translation`), `FormErrorSummary` for general errors, toast caption "Couldn't save. Check the highlighted fields. · ref: abcd1234". |
| G7 | Force a render error on a page | `ErrorBoundary` → `PageErrorState` ("Something went wrong on this screen.") with Reload / Go to dashboard / Report this (when a support channel is set); the layout shell + Dora bubble survive; navigating away clears it; one `oopsie` toast; one `POST /api/client-logs` (rate-limited 10/min). |
| G8 | API 500 on a list | Global toast once; the card shows its error state (DR-8), not an empty state. |
| G9 | Any list loading | Skeletons mimic the layout (`AppSkeleton`), never the word "Loading…" or placeholder titles (D-007). |
| G10 | Trigger 5 toasts quickly | They stack bottom-right (the 269-site convention); offline/online and PWA toasts come in at `top` (the 23-site convention) — two conventions visible at once (20-R10). |
| G11 | Tap a `(?)` chip | `HelpHint` deep-links to Help with `?q=<title>` and the matching guide expanded; `InfoTip` shows its tooltip instantly (0 ms). |

#### A3. Edge cases
- Browser locale ≠ install locale → install wins for money and dates; **sorting** still collates with `'en'` (20-R7).
- `/health` unreachable at boot → money renders AUD/en-AU defaults, dates en-AU, flags false → gated cards hide (FU-844's race class).
- Theme set to a dark family + OS light, and vice versa; `system-*` keys follow the OS; signed-out → brand default light (`boot/theme.ts`).
- A toast fired while another theme is applying → `.dora-toast--info` keeps reading tokens (VERIFY 2026-08-28 bullet still open).
- Error in a boot file before `globalErrorHandler` loads → console only (documented).
- `ResizeObserver loop` notice → filtered (no toast, no rollback).
- Shortcut sequence `g` then a pause > 1 s → prefix dropped; `g` then `s` while an input is focused → ignored.
- Focus-visible ring on a button in `sourdough-dark` → ring halo is Pesto-green (20-R8) because `--ring-focus` isn't overridden there.
- `Esc` with the cheatsheet open closes it; with a `persistent: true` confirm open does nothing (5 sites).
- Text at `sm` (14 px root): captions at `--font-size-xs` ratio drop below the 12 px floor? (`0.75 × 14 = 10.5 px` — D-003 check, 20-R12).

#### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (defaults) | ✓ (skeletons, toast stacking) | – | ✓ (shortcuts) | ✓ (Region/locale) | ✓ (per-user theme/text size) | ✓ (support channel → Report this) | ✓ |

#### A5. Load-bearing conditions
- **All 14 themes × light/dark** (G1, FU-674/671 contrast); **reduced-motion** (skeleton pulse off, motion tokens); **360×640** at `xl` text (G2); **1920+**; **bad network** (G8, client-log rate limit); **keyboard** (G5).

#### A6. Release-gate rows
1. G1 + G2 on every theme at `xl` text, phone width — no clipped labels, no h-scroll, focus ring visible and brand-matched.
2. G3 locale flip — no `$`/`toFixed`/US-date leaks (20-R6, R7 fixed).
3. G6–G8 error path end-to-end with a `ref:` id that matches a server log line.
4. Contrast spot-check of `warning`/`negative` chips and segmented active labels in pesto, blueberry, midnight (FU-671/674).

---
