# Chunk 05 — Stock Overview + Stocktake

**Analysed:** 2026-10-23 · **Analyst session:** finalisation overnight run (single session, no sub-agents)
**Scope (from PLAN §4):** `/stock` (toolbar, filters, sort, rows, bulk bar, splitter peek, scan actions, export, create dialog), the stock-item list/create/update/delete/move/bulk API, the attention rule, stock levels/groups/locations APIs, `/stocktake` (queue, three-phase session, check/snooze/bulk-check, cadence, ranking, sweep).
**Boundaries:** `StockItemDetailPage` + `get_stock_item_detail.py` + substitutes/preferred buys/price observations/buy verdict → Chunk 6; `inference_overlay` / `pantry_belief` / `PantryBelief*` → Chunk 7; `LogPriceSheet`/`PriceEntry` → Chunk 10; `ScanOverlay`, barcode/QR endpoints → Chunk 16/18 (the overview's *use* of them is here); Settings pages for levels/groups/locations/stocktake → Chunk 13; `WelcomeWizard` → Chunk 14; the alerts feed's use of `resolve_overdue_map` / `stock_attention` → Chunk 9.

## 0. Reading list + files walked

**Planning docs consulted:** `PROPOSAL_STOCKTAKE_MODE.md` (§4–§7), `IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md` (Step 0, Chunks 3b/4/5/6, D-1..D-10), `STOCK_OVERVIEW_PERF.md`, C-1 Stock Overview chunks 1–4, feedback `# STOCK OVERVIEW` (L63–109) + `# STOCKTAKE MODE` (L142–155); open FUs: FU-923, 851, 841, 777, 773, 728, 715, 714, 713, 712, 702, 701, 700, 699, 698, 693, 686, 685, 684, 683, 667, 650/642, 633, 631, 579, 575.

**Files walked (every file opened):**

| File | Lines | Role |
|---|---|---|
| `dora_api/features/stock_items/{get_stock_items,update_stock_item,create_stock_item,delete_stock_item,bulk_operations,move_stock_item,_level_access,stock_attention}.py` | 1577 | list/CRUD/bulk/attention |
| `dora_api/features/stocktake/{stocktake,session,cadence,queue_ranking,sweep}.py` | 1443 | queue, session, cadence, ranking, sweep |
| `dora_api/domain/{stock_status,location_breadcrumb}.py`, `domain/entities/{stock_item,stock_level,stock_location,stock_group}.py` | 385 | domain |
| `dora_api/features/stock_levels/get_stock_levels.py`, `stock_locations/{create,update,delete,get}_stock_location.py`, `stock_groups/manage_stock_groups.py` | 545 | vocab APIs |
| `web_app/src/pages/StockOverview.vue` | 1857 | the page |
| `web_app/src/pages/StocktakeRunner.vue` | 1012 | the runner |
| `web_app/src/components/stock/{StockItemRow,StockItemRowPriceButton,StockLevelDot,StockLevelPicker,StockRowLegend,CreateStockItemDialog,BulkMoveLocationDialog,MarkAsWastedDialog,MarkOpenExpiryDialog}.vue`, `createStockItemPrefill.ts` | 2606 | row + dialogs |
| `web_app/src/components/stocktake/{StocktakeReviewPhase,StocktakeSweepPhase}.vue` | 447 | phases |
| `web_app/src/composables/{useStockFilters,useStockItemActions,useStockStatus,useStocktakePolicy,useListViewMode,useStockOverviewExport,useFilterPanelExpanded}.ts` | 1096 | composables |
| `web_app/src/helpers/{stockLevelLogic,stockRowMetrics,stockStatus,scanActions,locationDisplay}.ts` | 261 | helpers |
| `web_app/src/stores/{stockItemStore,stockLevelStore,locationStore,stockLocationStore}.ts`, `services/api/{stockItemApiService,stocktakeApiService,stockLocationApiService}.ts`, `models/stockItem.ts` | 1004 | stores, API, model |
| Tests inventoried: `tests/test_stock_status.py`, `test_stock_attention.py`, `test_stocktake_cadence.py`, `test_stocktake_queue_ranking.py`, `test_stocktake_sweep.py`; e2e `test_stock_item_router.py`, `test_bulk_operations.py`, `test_stocktake_router.py`, `test_stock_level_router.py`, `test_stock_level_collapse.py`, `test_stock_location_router.py` (flat), `test_location_router.py` (tree), `test_stock_group_router.py`, `test_update_stock_item_auto_add.py`, `test_stock_item_history_feeds.py`, `test_confirm_actions_resolve_level.py`; vitest `useStockFilters.spec.ts`, `stockStatus.spec.ts`, `stockLevelDot.spec.ts` (FU-650/642), `stockItemStore.spec.ts`, `locationStore.spec.ts`, `filterLocationTree.spec.ts`, `useStockItemActionsPushExpiry.spec.ts` | | |

## A. Full Systems Test — Stock Overview + Stocktake

### A1. Preconditions
- Seeded install ≥ 60 items (crosses the 50-row virtual-scroll threshold), a 3-level location tree, ≥ 4 stock groups, essentials, items expired / expiring / low / out, some with linked products, some with usual stores.
- Install flags toggled across runs: **money** (per-row Log price, toolbar Log price), **scanning** (Scan button + action menu, Print QRs), **stocktake** (toolbar button, dashed markers, `/stocktake`), **stock inference** (Dora-thinks header on the level picker; Review phase).
- Admin settings: expiring-soon window ≠ 7, auto-add mode `essential_only`, stocktake default band, auto-tuning on, new-items opt-in.
- A user with `stocktake_last_session_at` set (so the Sweep phase can appear) and ≥ 3 logged purchases on one item (so Review has a confident row).

### A2. Golden path
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

### A3. Edge cases
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

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (empty state: New item / from recipe / from list) | ✓ | ✓ (flags off: no money/scan/stocktake chrome) | ✓ (keyboard n f / a arrows enter; scan-to-level loop) | ✓ (expiring window, auto-add mode, stocktake cadence/opt-in) | ✓ (per-user disabled alert kinds affect *that* user's outlines; per-user stocktake watermark) | – | – |

### A5. Load-bearing conditions
- **≥ 500 items**: the server caps a page at 500 and the SPA pages until exhausted; the queue fetch is 500 — pathological beyond.
- **Themes × dark**: attention outline `--q-negative`, selected fill `--q-primary` 14 %, hover `--q-accent` 4 % (05-R22), essential stripe `--brand-secondary-strong`, dashed ring 65 % ink, runner belief wash.
- **Reduced motion**: micro-feedback classes, row transitions.
- **Touch**: 32px level square kept deliberately (R-085 carve-out), 44px cluster buttons, 44px menu rows.
- **Offline**: level flip rolls back with a toast.

### A6. Release-gate rows
- Admin sets expiring window to 3 days → rows, the bell and the "Expiring soon" chip agree (one rule, `stock_attention.py`).
- Full stocktake with all three phases on a phone; after Done, `/stock` reflects every level change and deletion **without a reload** (05-R5).
- Bulk: select 40 → Add to list → one request; Restock → one request, 40 `StockLevelChange` rows, auto-add fires at most once per item; Log waste → Undo restores every expiry.
- Scan loop "Set to Out of Stock" over 5 items → 5 level writes, markers update, no navigation.

## B. Help content — Stock Overview + Stocktake

### B1. Current help audit
- `HelpPage.vue` **Stock** group: *Add a stock item*, *expiry / essentials*, *Dora's hint* (inference), *Scanning*, *Barcodes*, *QR labels*, *Substitutes*, *Link a product* — good coverage of the detail-page features; **nothing** on the overview's own language: the attention outline and its rule, the three-band row ramp, the dashed "might be wrong" ring, filters/sort, bulk select, the expiry button's push shortcuts, open/in-use + effective expiry, auto-add, export of the filtered set. The colour rules live in *What the colours and outlines mean* (`HelpPage.vue:353`) as the page comment says; `StockRowLegend.vue` is the live legend component and should be mounted inside that entry's `details` so the guide can't drift from the rows (R-003) — today the entry is prose only.
- **Stocktake** group: *How stocktake works* with `details` paragraphs (engagement gate, least-certain-first ordering, cadence bands) — accurate and already the `(?)` deep-link target. Missing: the three phases by name (Review / the walk / "Dora's stopped tracking these"), Push vs Skip vs Mute semantics, the Low/Out → list prompt, the per-item toggle and install default, FU-700's "turned off" state.
- `app_knowledge.py:15–19` Stock paragraph: accurate but thin — no attention rule, no stocktake, no bulk, no scan actions.

### B2. Help entries

#### Reading a stock row
- **Group:** Stock (rewrites the existing *What the colours and outlines mean* entry; mount `StockRowLegend` in its `details`)
- **What it does:** The coloured square is the stock level (green stocked · amber low · red out; dashed-edge box = no level set). A **dashed ring** around it means the number might be wrong — either Dora's hunch disagrees or the item is due a stocktake check; open the square to see which. The **row outline** means something needs you: expired, expiring soon, or an essential that's low or out. A **dimmed** row is out of stock but not essential — nothing to do. The coloured left edge marks an essential.
- **What controls it:** The expiring-soon window and per-user alert kinds (`/settings/notifications`) decide the outline; it's the same rule as the bell.
- **Source:** `stock_attention.py`, `StockRowLegend.vue`, D-5/D-7/D-8.

#### Finding things: filters, sort and search
- **Group:** Stock
- **What it does:** Search by name; quick chips for Needs attention · Expiring soon · Essential · Open; dropdowns for level, location (searchable path), group; sort by attention (default: most urgent first), name, level, last updated or expiry, with a direction toggle. The filter panel opens by itself whenever a filter is active and your filters survive leaving and returning (not a reload). The footer counts describe what's shown.
- **What it costs / might get wrong:** Links from elsewhere (an alert, a recipe's "ingredients", a location) arrive as chips you can remove.
- **Source:** `useStockFilters.ts`, `useFilterPanelExpanded`.

#### Quick actions on a row
- **Group:** Stock
- **What it does:** Tap the level square to set a level. The expiry button opens a calendar when none is set; once set it offers +1 / +7 / +14 days (counted from today or the current date, whichever is later), Clear, and Log waste. The seal/open button marks an item in use — opening asks whether its effective expiry changes. The cart adds to (or removes from) your list. Tap the row to open the item; on a phone, hold a row to select several.
- **Related:** Expiry and essentials · Shopping: the cart button
- **Source:** `StockItemRow.vue`, `useStockItemActions`.

#### Doing several at once (bulk select)
- **Group:** Stock
- **What it does:** Bulk select (or hold a row on a phone) lets you pick rows and add them to a list, remove them from one, move them to a location, mark them restocked, log them all as wasted for one reason (with Undo), or print their QR labels. Each is one request. Deselecting the last row ends bulk mode.
- **Source:** `StockOverview.vue` bulk bar, `bulk_operations.py` ×2.

#### Essential items and auto-add
- **Group:** Stock
- **What it does:** Marking an item essential makes Dora chase it as soon as it runs low (the row outlines, the bell says so) instead of waiting until it's gone. With auto-add on, an item dropping to low or out lands on your only draft shopping list by itself, marked with Dora's glyph; you're told in a toast.
- **What controls it:** `/settings/admin/system/stock` auto-add mode: off · essentials only (default) · every item. Nothing is auto-added when you have no draft list or more than one.
- **Source:** `update_stock_item._try_auto_add`, MAGIC F1.

#### Scanning with an action
- **Group:** Stock (extends *Scanning*)
- **What it does:** The Scan button opens the camera on "Open stock item". Switch the action inside the overlay to "Set to <level>" and every item you scan takes that level without closing the camera — a quick way to walk the pantry marking things out. A barcode Dora doesn't know opens New item prefilled (from Open Food Facts where it can).
- **What controls it:** Scanning switch (`/settings/admin/system`).
- **Source:** FU-378, `scanActions.ts`.

#### Exporting your stock
- **Group:** Stock
- **What it does:** Export → CSV or Print / Save as PDF of exactly the rows currently shown (filters and search applied); with nothing filtered, everything.
- **Source:** `useStockOverviewExport`.

#### How stocktake works *(extend the existing entry)*
- Add paragraphs: **Three parts.** *Review* — items Dora is fairly sure about from your shopping and cooking, pre-ticked; agree in one tap or untick to check yourself. *The walk* — the rest, least-certain first: Still correct · set the level · Skip (just for this run) · Push 3 days (no check recorded) · Mute (stops asking; un-mute on the item). *Dora's stopped tracking these* — items that left the rotation since your last stocktake: say you still keep them (set a level), mute, delete, or leave them be. At the end anything you marked low or out can go on a list in one go.
- **What controls it:** `/settings/admin/system/stocktake` (switch, default cadence, auto-tuning, new-item default); per-item Stocktake toggle on create and on the item.
- **What it costs / might get wrong:** With the install switch off nothing is ever due and `/stocktake` says so.

### B3. DoraBot corpus delta
Append to `app_knowledge.py` Stock paragraph:
```
  Rows outline when something needs you (expired, expiring soon, an essential
  that's low or out — one rule shared with the bell), dim when out but not
  essential, and the level square wears a dashed ring when Dora's hunch
  disagrees or a stocktake check is due. Bulk select handles add/remove from a
  list, move, restock, waste and QR labels for many rows at once; Scan can open
  an item or set every scanned item to a level. Stocktake (when switched on)
  runs in three parts — agree with what Dora is sure about, walk the uncertain
  items least-certain first (Still correct / set level / Skip / Push 3 days /
  Mute), then tidy items that dropped out of rotation — and offers to put
  anything that went low or out on a list.
```

## C. Senior review — Stock Overview + Stocktake

### C1. Bugs (verified or high-confidence latent)

- **05-R5** · bug (high-confidence) · `StocktakeRunner.vue` writes levels, mutes and deletes through the raw API (`stockApi.updateAsync` L594/615/694/790, `stockApi.deleteAsync` L823), never through `stockItemStore`. The store is already hydrated from `/stock`, `ensureLoadedAsync` is a no-op once `hydrated`, and nothing invalidates it — so **after a stocktake, `/stock` shows the pre-stocktake levels (and deleted items) until a hard reload**. It also skips the store's recipe-fact invalidation and the auto-add toast (a level set to Low in the runner can fire `_try_auto_add` server-side and the user is never told). · **Exact change:** route level writes through `stockItemStore.updateStockLevelAsync`, mute through `updateStockItemAsync`, delete through `deleteStockItemAsync`. · S · guard: drive once (stocktake → /stock) · **execute**.
- **05-R3** · bug (R-003/FU-050) · `StocktakeRunner.vue:499` `stockLevels.find(l => l.name === c.stock_level_name)` colours the Change-level button by **name**; `SessionItemDto.stock_level_id` is right there. · **Exact change:** `find(l => l.stock_level_id === c.stock_level_id)` (or 04-R11's `stockLevelStore.sequenceOf`). · S · **execute**.
- **05-R7** · dead + rule-bypassing endpoint · `POST /shopping-lists/<id>/review/complete` (`stocktake.py:583–651`) writes `stock_level_id` with a raw `UPDATE` — no `StockLevelChange`, no `ConsumptionEvent`, no auto-add, no `last_checked_at` rule — exactly the bypass `bulk_operations.py`'s docstring refuses; and `stocktakeApiService.reviewCompleteAsync` has **zero callers** (the shopping-list "review mode" was retired in UX-v2). · **Exact change:** delete the route, `ReviewCompleteRequest`, `_stocked_level_id`, the `SHOPPING_LIST_ROUTER` import, `reviewCompleteAsync`, and its e2e cases in `test_stocktake_router.py` / fuzz list. · S · **execute**.
- **05-R30** · comment/behaviour mismatch · `create_stock_item.py:55` says the name check is case-insensitive; both create (L98–103) and update (L207–215) use `eq`, which is case-sensitive on SQLite and Postgres, so "Milk" and "milk" both exist while groups normalise (`manage_stock_groups.py:105`). · **Exact change:** `func.lower(name) == request.name.lower()` via a repository `ieq`/`EntityField.ilike` (check the port), or normalise as groups do; share one `_name_taken(repository, name, exclude_id)` between create and update. · S · guard: `test_stock_item_router.py` new case · **execute** (FU-575 keeps the concurrent-race half).
- **05-R2** · R-003/R-021 · the "+N days from max(today, current expiry)" rule (FU-123) lives in the client (`useStockItemActions.pushExpiry:179–202`) with a browser-local `today`, while every other date stamp (`opened_on`) is household-day server-side. The row menu, the detail page and the bell's "push expiry" all route here. · **Exact change:** `POST /stock-items/<id>/push-expiry {days}` → `{expiry_date}` using `household_today`; client calls it. Keep `useStockItemActionsPushExpiry.spec.ts` as the server unit test's twin or retire it. · M · guard: new pytest unit + e2e · **execute**.
- **05-R11** · duplicate API for one table · the flat `/api/stock-locations` CRUD (`stock_locations/*`, name-only, can't set `kind`/`parent_id`) coexists with the tree `/api/locations` CRUD (`locations/*`). SPA callers of the flat one: `stockLocationStore` ← `StockItemRow.vue:343, 458, 461, 487` (a name fallback that is **dead**: `getStockLocationsAsync` is never called on the overview, so `stockLocations` is always `[]`) and `WelcomeWizard.vue:1405–1544` (onboarding creates zones by name). · **Exact change:** onboarding → `locationStore.createAsync({ name, kind: 'zone' })`; delete `stockLocationStore`, `stockLocationApiService`, the flat router (4 files) and `test_stock_location_router.py` + its fuzz/DTO-contract rows; `StockItemRow` drops the import and fallback. · M · guard: `test_location_router.py`, onboarding e2e (Chunk 14) · **execute** (Chunk 14 ticks the wizard).

**05-R41** · comment ≠ code (cross-filed from 06-R17) · `StockOverview.vue:453–454` says the split-view peek opens at **50 %** (feedback "open the split-view at 50%") while the code sets **58**. · **Exact change:** pick one (the owner asked for 50) and make the comment read the constant. · blast S · guard none · **execute**.

### C2. Redundancy / DRY (R-001, R-003)

- **05-R10** · `stocktake.get_stocktake_queue` (L432–470) and `session.get_stocktake_session` (L138–181) repeat: load items with level+location, `resolve_overdue_map`, gate beliefs on `SURFACE_STOCK`, `gather_beliefs_for_items`, `rank_queue`, `band_by_item`/`days_by_item`. · **Exact change:** `stocktake._ranked_overdue(repo, user, now) -> RankedOverdue(ranked, band_by_item, days_by_item, belief_ranked)`; both endpoints consume it. · S · guard: `test_stocktake_router.py` · **execute**.
- **05-R9** · the SQLite-naive → aware-UTC coercion appears inline at `stocktake.py:242–243, 393–395`, as `sweep._aware`, and again in `reconcile.py` (Chunk 2). · **Exact change:** `persistence/aware.py::as_utc(dt)`; four call sites. · S · **execute**.
- **05-R6** · "the most-stocked level is `stockLevels[0]`" in `StockOverview.bulkRestock:1108` and `useStockItemActions.markRestocked:156`; `findLevelBySequence(levels, STOCKED_SEQUENCE)` exists in `helpers/stockStatus.ts`. · **Exact change:** `stockLevelStore.stockedLevel` computed (via `findLevelBySequence`); both read it. · S · **execute**.
- **05-R13** · stock groups fetched ad hoc in `StockOverview.loadStockGroups`, `CreateStockItemDialog.loadStockGroupsAsync` and the detail page ("there's no store for them"). · **Exact change:** `stores/stockGroupStore.ts` (R-016 lazy, same shape as `stockLevelStore`); three callers. · S · **execute**.
- **05-R25** · the path-labelled location option walker (`"Pantry › Middle shelf"`) is copied in `useStockFilters.allLocationOptions` (L233–244), `CreateStockItemDialog.allLocationOptions` (L303–314) and (per its comment) the detail page. · **Exact change:** `locationStore.pathOptions` computed; `filterLocations` narrowing helper alongside. · S · **execute**.
- **05-R24** · belief band ↔ word/sequence maps: `StocktakeReviewPhase.vue` (`BAND_WORD`, `BAND_SEQUENCE`, `BAND_BY_SEQUENCE`), `StocktakeRunner.vue:505` (`BELIEF_WORD`), `StockItemRow.vue:413` (`BELIEF_BAND_WORD`), + `PantryBeliefChip`/`PantryBeliefCard` (Chunk 7). · **Exact change:** `helpers/beliefBand.ts` (`bandWord`, `sequenceForBand`, `bandForSequence`); five call sites. · S · guard: new `beliefBand.spec.ts` · **execute**.
- **05-R26** · six more `stockLevels.find(l => l.stock_level_id === id)` lookups (`StockOverview.filterLevelSequence`, `CreateStockItemDialog.selectedLevelSequence`, `StocktakeReviewPhase.levelSequence`, `StockItemRow.levelName/levelSequence`, `StockLevelPicker.levelName/levelSequence`, `useStockFilters.levelSequence`) — **04-R11**'s `nameOf/sequenceOf` getters. · **execute (04-R11)**.
- **05-R19** · `StocktakeRunner` Mute confirm dialog duplicated (L683–689, L779–785). · **Exact change:** `confirmMute(name): Promise<boolean>`; both call it. · S · **execute**.
- **05-R16 / 05-R17** · `pageStyleFn` (02-R27) and the `.runner-*` shell (02-R28 `RunnerShell`) — this surface holds copies 5–6 and 3 respectively. · **execute (02-R27 / 02-R28)**.
- **05-R28** · local imports with no cycle to break: `create_stock_item.py:91, 202, 214`, `update_stock_item.py:287, 302, 388–391, 485, 496`, `get_stock_items.py:126, 181–183, 211` (`dataclasses` ×3). Only `_try_auto_add`'s shopping-list imports (L408–431) have a documented cycle. · **Exact change:** hoist the rest. · S · **execute**.

### C3. Dead code / unused fields / unread endpoints

- **05-R14** · `useStockFilters` exports `summaryCounts`, `countByLevel`, `toggleLevelFilter` — zero callers. · **Exact change:** delete (and their spec cases). · S · **execute**.
- **05-R12** · `StockItemRow` `useStockLocationStore` import + flat-name fallback — dead (05-R11). · **execute**.
- **05-R7** · `review/complete` + `reviewCompleteAsync` — dead (above).
- **05-R38** · `useStockItemActions.findSubstitutes` and `seeRecipesUsing` — zero callers (grep: only `openDetail` is used, by `StockItemDetailPage.vue:2282`; the alerts model builds its own `/cookbook?usesStockItem=` URL at `models/alert.ts:155`). · **Exact change:** delete both. · S · **execute**.
- **05-R15** · list-DTO fields with no SPA reader: `stock_level_name` (the TS comment says "print-sheet labels", but the print view is server-rendered), `last_checked_at`, `opened_on` (grep in overview/row/filters → none; the **detail** DTO carries its own copies). · **Exact change:** drop the three from `StockItemDto` + `models/stockItem.ts`; keep `needs_restock` (cook mode reads it). · S · guard: `test_dto_contracts.py` · **execute**.
- **05-R21** · `StockOverview.bulkAddToPrimary` (keyboard `a`, quick-add target) vs `bulkAddToListPrompt` (bar, radio) — two bulk-add flows. Intentional (keyboard = fast path). · **waive** (document in the `a` shortcut description).
- **FU-698** · "Deselect all" ≡ "Cancel bulk select" — the code comment already answers it (kept because on a phone the bar is what's on screen). · **resolve FU-698** with that note.

### C4. Componentisation opportunities (R-001)

- **05-R33** · `StockOverview.vue` (1,857 lines): the scan flow (L1435–1590, ~155 lines + the overlay template) and the bulk bar + its seven handlers (L371–451 + L1021–1399) are self-contained. · **Exact change:** `useStockScan(...)` composable (action, options, decode handlers) and `useStockBulkActions(...)` (selection, the seven actions, `pickActiveListId`); the page keeps filters, list, peek. · M · guard: vue-tsc + drive bulk and scan once · **FU** (same group as FU-780/01-R36/04-R20 — the "big page splits").
- **05-R37** · one `MarkAsWastedDialog` + one expiry `q-menu` **per row** (×50 before virtualisation). Hoist to a single page-level dialog keyed by the active row? Virtual scroll bounds the DOM; · **waive**.

### C5. Placement / standards (R-002, R-005, R-008, D-rules)

- **05-R22** · raw Quasar palette vars in stock components: `StockItemRow.vue:732–733 (--q-accent), 835–836 (--q-negative), 842, 845 (--q-primary)`, `StockRowLegend.vue:178, 206–207`, `StockOverview.vue:1809 (--q-page — intentional, documented)` — 11 sites → `--brand-*` / `--semantic-*` (02-R37 family). Literal transitions `StockOverview.vue:1772 (0.25s ease)`, `MarkAsWastedDialog.vue:123 (120ms ease)` → motion tokens (D-010). `.scan-action-caption` `rgba(255,255,255,.82)` / `rgba(0,0,0,.6)` — R-002 carve-out (camera surface is always dark) → add the carve-out comment. · S · **execute**.
- **05-R23** · `StocktakeRunner.vue:960, 964, 1000` `var(--text-md, 1rem)` / `var(--text-xs, 0.75rem)` and `MarkAsWastedDialog.vue:137` `var(--text-sm, …)` — the type tokens are `--font-size-*`; `--text-md/-xs/-sm` are **undefined** (grep `css/*.scss` → none; FU-764 class) and have always painted their fallbacks. Plus raw px rhythm throughout the runner (`padding: 12px/24px`, `gap: 8px/4px/12px`, `border-radius: 12px`, `margin: 16px auto 0`) and `StockItemRow` (`font-size: 1.05rem / 0.8rem`, `border-radius: 8px/4px`, `padding: 6px 12px`, `gap: 14px/6px`) → `--font-size-*`, `--space-*`, `--radius-*`. · S (mechanical) · **execute** as one sweep with 05-R22; drive both pages after.
- **05-R29** · `StocktakeRunner` `$q.dialog` `ok: { label, color, unelevated }` ×3 (L689, 785, 818) lacks `noCaps` (R-039). · S · **execute**.
- **05-R8** · `stocktake.bulk_check` raw `table.update()` — acceptable (writes only `last_checked_at`/`snoozed_until`, no rule), but it `db.session.commit()`s directly rather than through the repository; and `get_stock_items._hydrate_linked_product_count` + `delete_stock_item` + `_gather_engagement_signals` + `sweep._latest_activity_by_item` use raw Core on mapped tables. All are aggregates/bulk the port can't express — consistent with the 02-R30 precedent. · **Exact change:** add `# R-005 carve-out: aggregate` comments where missing; `bulk_check` → `repo.session.execute(...)` + `repo.save_changes()`. · S · **execute**.
- **05-R31** · `GetStockGroupsHandler` loads every `StockItem` to count per group (L54–63) → `select(_stock_group_id, count()).group_by` (02-R30 shape). · S · **execute**.
- **05-R34** · `useStockOverviewExport.openPrintView` `window.open(baseUrl…)` — **R-045**, the 4th site of FU-682's defect (recipe print fixed; meal plan 02-R36; shopping 03-C10). `downloadCsv` uses raw `fetch(credentials:'include')` rather than the shared download path other exports use. · **Exact change:** `openHtmlDocumentAsync('/stock-items/print-view…')`; CSV via the shared `downloadFileAsync` helper if one exists (Chunk 18 inventories export helpers). · S · **execute (FU-682)**.
- **05-R27** · `GetStockItemsHandler.handle` collects entities via a side-effecting projection closure to feed the attention pass. Works; · **waive** (documented).
- **05-R40** · `/stocktake/queue` loads **every** stock item with level + location on each overview load, filters in Python. Bounded by the 500-item cap; · **waive** (note for FU-667's "client-side filtering over a hydrated collection" audit — this is its server twin).
- **05-R4** · `StocktakeRunner.onPickLevel:623–624` `sequence >= LOW_STOCK_SEQUENCE || sequence === OUT_OF_STOCK_SEQUENCE` (second clause redundant) → `needsRestockSequence(sequence)`; `void levelName` unused param. · S · **execute**.

### C6. Naming & idiom
- **05-R35** · `stockLocationStore` vs `locationStore` — two stores for one concept (resolved by 05-R11).
- **05-R36** · `StockItemDto` vs `StocktakeQueueItemDto` vs `SessionItemDto` — fine; `StocktakeQueueItem` TS type duplicates `StocktakeSessionItem` minus `stock_level_id`/breadcrumb → one `StocktakeItemBase` interface. · S · **execute** (with 05-R10).

### C7. Efficiency
- 05-R13, 05-R31, 05-R40 above. `useStockFilters.filteredStockItems` recomputes `attentionBand`/`outOfStock` per compare — fine at 500.

### C8. Design-level findings — out of Stage-2 scope
- **05-D1** · **FU-728 (stocktake half) answered:** the runner **already** gives each lifecycle phase its own composition (`StocktakeReviewPhase`, the walk card, `StocktakeSweepPhase`) — R-054 is satisfied. Close FU-728 (cook-mode half answered in 04-D1).
- **05-D2** · The flat-vs-tree location API split (05-R11) is a leftover from before the tree existed; nothing in the owner's feedback wants a name-only location. Confirm with the owner that onboarding zones via the tree API is fine (they're zones anyway).
- **05-D3** · `StockLevelPicker` stays 32px on touch (R-085 carve-out, owner 2026-09-09) — recorded; no change.
- **05-D4** · FU-700: dashboard/help copy not gated on the stocktake switch — the help entry above names the switch; the dashboard half → Chunk 8.
- **05-D5** · FU-699 (full backend suite not run for the stocktake switch) — the baseline run at the start of this overnight (2429 passed / 2 order-dependent flakes) covers it → **resolve FU-699**.
- **05-D6** · FU-715 ("Needs attention filter broken" didn't reproduce) — the filter reads `needs_attention` only; stays confirm-in-browser.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `useStockFilters` client filter+sort over the hydrated collection | in-memory filtering | server-side query params (`parse_query_options` already supports `filter=`/`sort=`) | **keep (for now)** | — | FU-667 owns the question; at ≤ 500 items client-side is the right call and the deep-link chips depend on it. |
| `q-virtual-scroll` + fixed row metric | virtualisation | — | **keep** | — | Correct use of the framework. |
| `useDragDropList` (not used here), `v-touch-hold` | gestures | — | **keep** | — | Quasar directive. |
| `cadence.py` band resolver | rules | — | **keep** | — | Pure, tested. |
| `queue_ranking.sort_key` tuple sort | ranking | — | **keep** | — | Deterministic, tested. |
| `sweep._latest_activity_by_item` two aggregates | event dating | an `engagement_events` table | **keep** | — | Documented trade: derive, don't store. |
| `locationStore.breadcrumb` rebuilds parent/name maps per call | tree walk | memoised maps | **wrap** | S | Build the two maps once per tree load (computed); called per row. |

### C10. Standards drift (R-0NN)
- **R-003** · 05-R3, 05-R6, 05-R24, 05-R25, 05-R11 — fix.
- **R-005** · 05-R7 (rule bypass), 05-R8 — fix.
- **R-008** · 05-R28 — fix.
- **R-021** · 05-R2 — fix.
- **R-032** · the attention pass and `_is_engaged` read `item.stock_level` directly; safe only because every caller includes the level — **FU-684** tracks the class; recommend `_level_access.resolve_levels_by_item` there when FU-683/684 execute (Chunk 6/7).
- **R-039** · 05-R29 — fix.
- **R-045** · 05-R34 — fix (FU-682).
- **R-002 / D-003 / D-010** · 05-R22, 05-R23 — fix.
- **R-085/D-004** · level square 32px — documented carve-out, clean.
- **FU-764** (undefined tokens) · 05-R23 `--text-md/-xs/-sm` — fix.
- **FU-624 / FU-675** · raw `$q.notify` ×30+, raw `q-select` ×6 — tracked.

### C11. Ride-along signals for FU-010 / FU-224
- `--q-accent` 4 %/38 % washes on row hover; `--q-primary` 14 % selected fill — the accent-vs-primary question FU-224 owns.
- `.stock-row--dim { opacity: .62 }` + `.stock-row-legend__row-swatch--dim` — opacity dimming (D-002).
- Runner belief wash `--semantic-warning-soft` + warning hairline (measured 2.1:1 before the 09-01 fix; re-check pesto dark).
- `--brand-secondary-strong` essential stripe vs `active-color="secondary"` on the Essential chip — same concept, two tokens.

## D. Test plan — Stock Overview + Stocktake

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__stock_item_name__case_insensitive_unique` (create + rename) | pytest e2e | **must-write-before-ship** | 05-R30 — pins the rule the comment already claims. |
| `test__push_expiry__from_max_household_today_or_current` | pytest unit (pure) + e2e | **must-write-before-ship** | 05-R2 — moves FU-123's rule server-side; the client spec retires. |
| `test__ranked_overdue__queue_and_session_agree` | pytest e2e | nice-to-have | 05-R10 — same items, same order, from both endpoints. |
| `test__stock_groups__item_count_group_by` | pytest e2e | nice-to-have | 05-R31. |
| `beliefBand.spec.ts` | vitest | nice-to-have | 05-R24. |
| `stockLevelStore.spec.ts` (`stockedLevel`, `nameOf`, `sequenceOf`) | vitest | nice-to-have | 05-R6 / 04-R11. |
| `useStockFilters.spec.ts` — drop the dead-export cases | vitest | housekeeping | 05-R14. |
| `test_stock_location_router.py` — delete | pytest | housekeeping | 05-R11. |

Not proposed: a vitest for the runner's store wiring (05-R5) — drive once; Playwright.

## E. Proposed follow-ups (orchestrator allocates ids)

- type=follow-up · *Extract `useStockScan` + `useStockBulkActions` from `StockOverview.vue`* (05-R33) — bundle with the "big page splits" group (FU-780, 01-R36, 02-D4, 04-R20).
- type=finding · *Flat `/api/stock-locations` duplicates the tree API* (05-R11 / 05-D2) — execute this run if the owner is fine with onboarding using the tree API; otherwise FU.
- type=finding · *`review/complete` bypassed every level-change rule* (05-R7) — resolved by deletion this run; record in CHANGELOG.
- **Resolve:** FU-698 (documented, keep), FU-699 (baseline suite run 2026-10-22), FU-728 (both halves answered: 04-D1, 05-D1).
- Existing FUs this chunk executes against: **FU-682** (05-R34), **FU-654** (`get_stock_items._disabled_kinds` literal `"user_id"` — copy 19), **04-R11**, **02-R27/02-R28**, **01-R8** (`_hydrate_linked_product_count._key`).

## F. Summary for the register

- FST rows: 11 golden + 14 edge + 4 gate · Help entries: 7 new + 1 extended (stocktake) · Review findings: 40 (execute 30 / FU 1 / waive 5 / conditional 2 / resolve-FU 3) · Tests: 8 (must-write 2) · Bugs: 6 (stocktake writes bypass the store → stale `/stock` until reload; runner level colour keyed by name; dead `review/complete` endpoint bypassing every level rule; case-insensitive uniqueness claimed but not enforced; client-side expiry-push rule with browser today; a dead flat location API still shipped)
- One-line: the stock surface is the app's most-reviewed and it shows on the server — one attention rule, one cadence engine, one ranking, one sweep — but the **stocktake runner never learned about the store** (its writes vanish from `/stock` until a reload), a retired shopping-list "review mode" left a raw-UPDATE endpoint that bypasses every level-change rule, and two location APIs still serve one table.
