# Test Plan Inventory — Dashy Dora

**Assembled 2026-10-23** from the twenty chunk files (track **Tests** = each chunk's §D). Stance (owner, 2026-07-20): lean, manual-first — a test is listed only where it pins a stable, low-churn contract that is expensive to re-check by hand; backend pytest and Vitest only; Playwright stays the 3-spec smoke layer. Baseline at analysis time: pytest 2429 passed / 2 order-dependent flakes; vitest 747 / 66.

## Must-write-before-ship (roll-up)

| Chunk | # | Test | Layer | Priority | Trigger |
|---|---|---|---|---|---|
| Chunk 01 — Cookbook | `test__vocabulary_crud_factory__categories_cuisines_tools_identical_contract` | pytest e2e (parametrised over the three routers) | **must-write-before-ship** (if 01-R5 lands) | A generic factory needs one contract test; the three existing router tests then become the parametrised cases. |
| Chunk 01 — Cookbook | `ingredientDisplayName.spec.ts` | vitest | **must-write-before-ship** | 01-R1 — the label precedence is a contract three surfaces now share and it has already drifted once. |
| Chunk 02 — Meal Plans | `test__sweep_receipt_ids__round_trip_through_orm` | pytest e2e | **must-write-before-ship** | 02-R1 — pins that both receipt writers store the same id type; the only automated way to see it. |
| Chunk 03 — Shopping Lists | `test__snapshot_template__skips_product_only_lines_and_uses_display_name` | pytest e2e | **must-write-before-ship** | 03-R2 — pins the 500 → skip behaviour and the "Template from None" fix. |
| Chunk 03 — Shopping Lists | `test__move_unticked__product_only_lines_move` | pytest e2e | **must-write-before-ship** | 03-R3 — the anchor-key dedupe; the finish dialog's "move to new list" relies on it. |
| Chunk 04 — Cook Mode | `useCookTimer.spec.ts` (deadline-based remaining; pause/resume; fake timers advanced past a throttle) | vitest | **must-write-before-ship** | 04-R8 — the only way to pin "backgrounding doesn't slow the timer". |
| Chunk 04 — Cook Mode | `cookSteps.spec.ts` (flattener: top/sub ordering, section inheritance, structured-with-empty-steps fallback, numbered-line stripping) | vitest | **must-write-before-ship** | 04-R20 first extraction — the step model is the surface's core and has never had a test. |
| Chunk 05 — Stock Overview + Stocktake | `test__stock_item_name__case_insensitive_unique` (create + rename) | pytest e2e | **must-write-before-ship** | 05-R30 — pins the rule the comment already claims. |
| Chunk 05 — Stock Overview + Stocktake | `test__push_expiry__from_max_household_today_or_current` | pytest unit (pure) + e2e | **must-write-before-ship** | 05-R2 — moves FU-123's rule server-side; the client spec retires. |
| Chunk 06 — Stock-Item Detail | `test__level_history__carries_sequence_for_restock_inference` | pytest e2e (`test_stock_item_history_feeds.py`) | **must-write-before-ship** | 06-R3 — pins the DTO field the timeline now keys on. |
| Chunk 06 — Stock-Item Detail | `test__detail_dto__drops_unread_fields` (contract snapshot of top-level keys) | pytest e2e (`test_stock_item_router.py`) | **must-write-before-ship** | 06-R24/R25 — the removal is the contract. |
| Chunk 07 — Zero-Input Pantry (P8-07) | `test__gather__dates_bucket_in_household_zone__not_utc` (level changed 22:00 UTC = 08:00 AEST next day → `days_since_hard == 0`, *Updated today*) | pytest unit (gather with a stub repo) or e2e via `/beliefs` with `timezone=Australia/Sydney` | **must-write-before-ship** | 07-R1 — the FU-525 shape, for belief. |
| Chunk 07 — Zero-Input Pantry (P8-07) | `test__belief_envelope__out_is_never_high_confidence` (property over the constants) | pytest unit (hypothesis or a grid) | **must-write-before-ship** | pins impl-plan §1.3's guarantee that every overlay gate relies on; guards 07-R10 either way. |
| Chunk 08 — Dashboard | `test__restock_radar__item_without_level__is_skipped_not_500` | pytest e2e (`test_dashboard_insight_cards.py`) | **must-write-before-ship** | 08-R1. |
| Chunk 08 — Dashboard | `dashboardLayout.spec.ts` — `parseLayout` inserts an unseen card at its registry position; retired ids dropped; `defaultHidden` inherited | vitest | **must-write-before-ship** | 08-R7 / 08-R18 — the comment promised it and nothing held it. |
| Chunk 09 — Alerts + Suggestions | `test__suggestions__no_string_carries_a_currency_symbol` | pytest e2e (`test_suggestions_router.py`) | **must-write-before-ship** | 09-R1 — the verdict's precedent, for the other inbox. |
| Chunk 13 — Settings shell | `PATCH /app-settings {nutrition_mode:'bogus'}` → 400 with `detail` naming the options | pytest | must-write-before-ship | 13-R1 fix |
| Chunk 13 — Settings shell | Admin PATCH `/users/<id>` with malformed / duplicate email → 422/400; valid email sets `email_verified` | pytest | must-write-before-ship | 13-R2 |
| Chunk 13 — Settings shell | Deactivate admin B, delete admin A → 400 "last admin" | pytest | must-write-before-ship | 13-R3 |
| Chunk 14 — Onboarding | `seed-demo` on a week that already has a `MealPlan` → entry appended to it, plan count unchanged | pytest | must-write-before-ship | 14-R1 |
| Chunk 14 — Onboarding | `seed-demo` after `seed-items` with the three pack names → `items_created == 0` | pytest | must-write-before-ship | 14-R2 |
| Chunk 15 — Auth shell | With `DORA_TRUSTED_PROXY_HOPS=1`, `X-Forwarded-For: 10.0.0.9` → `remote_addr == 10.0.0.9`; with 0 (default) the header is ignored | pytest | must-write-before-ship | 15-R1 |
| Chunk 15 — Auth shell | DEBUG request logging never includes a `password`/`token` value (capture the log handler, POST `/auth/login`) | pytest | must-write-before-ship | 15-R2 |
| Chunk 16 — Ingestion API + companion seam | D1 | `test__ingest__expired_idempotency_key_is_reprocessed_not_500` — insert an `IdempotencyKey` with `expires_at` in the past (direct repo write inside `app.app_context()` as `test_ingest_batch.py:296–303` does), re-push with that key → 200, records accepted, row refreshed, exactly one row for `(source, key)` | pytest | **must-write-before-ship** | with 16-R2 |
| Chunk 16 — Ingestion API + companion seam | D3 | `test__ingest__is_available_round_trips` (false on create, unchanged on a push without it) | pytest | must-write **when** 16-R5 lands | with the FU |
| Chunk 16 — Ingestion API + companion seam | D5 | `test__link_status__never_resolves_a_custom_product` — create a custom product via `POST /products` at the seeded store, look it up by `(store, name)` → `product_not_found`; then push the same name via ingest → the ingested id (not the custom one) | pytest | **must-write-before-ship** | with 16-R8 |
| Chunk 16 — Ingestion API + companion seam | D6 | `test__ingest__validation_errors_are_structured` — replaces the text assertion in `test__ingest__rejects_price_observations_field:353–354` | pytest | must-write (adjust) | with 16-R34/R9 |
| Chunk 17 — Offline / PWA / native | D1 | `usePushSubscription.ensureRegistration` uses the existing registration (`serviceWorker.ready`) and never calls `register()` when one exists; falls back to registering `/push-sw.js` only when `getRegistration()` is null | vitest (mock `navigator.serviceWorker`) | **must-write-before-ship** | with 17-R1 |
| Chunk 18 — Backup & restore + Import | D1 | `test__restore_backup__partial_mode__restores_selected_rows_and_pulls_in_parents` — back up, delete one stock item + its location, restore `mode=partial` with `selection={"stock_items":[id]}` → 200, item back, location pulled in, no KeyError | pytest | **must-write-before-ship** | with 18-R1 |
| Chunk 18 — Backup & restore + Import | D2 | `test__backup_sections__catalogue_matches_SECTIONS` — `GET /data/backup/sections` keys == `[s.backup_key for s in SECTIONS]`, `default_on` matches; plus a Vitest that the page builds its groups from the response (no local list) | pytest + vitest | **must-write-before-ship** | with 18-R3 (replaces the comment "keep this in sync") |
| Chunk 18 — Backup & restore + Import | D6 | `test__restore_backup__stale_required_fk_entries_absent` — `REQUIRED_FKS`/`HARD_FK_PULL_IN` keys ⊆ `SECTIONS` keys and columns exist on the table (module-load assertion like `_validate_import_templates`, so the next rework can't leave a dead key) | pytest | **must-write-before-ship** | with 18-R1 — pins the class, not the instance |
| Chunk 19 — Ops / self-host | D1 | Build-time assertion in `Dockerfile`: `RUN test -f dist/spa/sw.js && test -f dist/spa/manifest.json` after the SPA build | Docker build step | **must-write-before-ship** | with 19-R1 (not a pytest; it is the only place the image's build mode is observable) |
| Chunk 19 — Ops / self-host | D4 | `test__version_check__repo_slug_matches_support_channel` (both import the one constant) | pytest unit | **must-write-before-ship** | with 19-R3 |
| Chunk 20 — Cross-cutting concerns | D1 | `useDateFormat.spec.ts` — `formatDate('2026-09-03')` renders 3 Sept in `America/New_York`; `formatDateTime` medium+short; `formatRelativeDay` Today/Tomorrow/weekday/short; locale switch re-keys the formatter cache | vitest (fake timers + `Intl` locale) | **must-write-before-ship** | the D-006 authority has zero tests and is the kind of stable contract the owner's test stance wants pinned |
| Chunk 20 — Cross-cutting concerns | D3 | `test__units_table_generated_is_current` — regenerate via `scripts/dump_units.py` into a temp path and diff against `web_app/src/generated/units_table.ts` (pins 20-R3/R4's single source) | pytest | **must-write-before-ship** | with 20-R3 (check whether one exists first — `grep dump_units tests/`) |

Everything else below is *nice-to-have*, to be written only when the matching Stage-2 change lands.

---

## Chunk 01 — Cookbook
*Source: [`CHUNK_01_cookbook.md`](../05_investigations/finalisation/CHUNK_01_cookbook.md) · analysed 2026-10-23*

### D. Test plan — Cookbook

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__recipe_write_error_response__maps_every_response_flag` | pytest (unit) | nice-to-have | Only if 01-R12 lands — pins the shared error chain once, instead of 2×9 route tests. |
| `test__vocabulary_crud_factory__categories_cuisines_tools_identical_contract` | pytest e2e (parametrised over the three routers) | **must-write-before-ship** (if 01-R5 lands) | A generic factory needs one contract test; the three existing router tests then become the parametrised cases. |
| `test__recipe_link_access__tags_and_tools_share_one_implementation` | pytest unit | nice-to-have | 01-R6 — pins validate/resolve/find for both link tables with one parametrised test. |
| `test__data_url_response__decodes_and_404s_on_garbage` | pytest unit | nice-to-have | 01-R7 — the five image routes today each rely on their own e2e test. |
| `ingredientDisplayName.spec.ts` | vitest | **must-write-before-ship** | 01-R1 — the label precedence is a contract three surfaces now share and it has already drifted once. |
| `useFilterRegistry.spec.ts` | vitest | nice-to-have | 01-R22 — count/clear/hasAny derive from one list. |
| `test__recipe_dto_cache__invalidated_by_flags` | pytest e2e | nice-to-have | **FU-901** (existing ask). |

Explicitly **not** proposed: Playwright flows for the recipe page (owner stance); component tests for the 2,700-line page (drive it once after 01-R36).

---

## Chunk 02 — Meal Plans
*Source: [`CHUNK_02_meal_plans.md`](../05_investigations/finalisation/CHUNK_02_meal_plans.md) · analysed 2026-10-23*

### D. Test plan — Meal Plans

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__sweep_receipt_ids__round_trip_through_orm` | pytest e2e | **must-write-before-ship** | 02-R1 — pins that both receipt writers store the same id type; the only automated way to see it. |
| `nextWeekCommands.spec.ts` (pure helper extracted from `useMealPlanner`) | vitest | nice-to-have | 02-R2 — a duplicated week keeps `cook_key` + `cook_fresh`. |
| `test__receipt_rows__queue_log_count_agree` | pytest e2e | nice-to-have | 02-R9 — after the five raw queries collapse to one builder, pin queue ⊆ log and counts match pages. |
| `test__entry_writes__create_and_update_share_validation` | pytest unit | nice-to-have | 02-R7 — one parametrised test over the shared validators replaces duplicated cases. |
| `useMealEntryPresentation.spec.ts` | vitest | nice-to-have | 02-R19b — the seven computeds, parametrised over batch/fresh/linked/consumed. |
| `appShellStyleFn.spec.ts` | vitest | nice-to-have | 02-R27 — trivial, but six pages depend on the two branches. |
| `test__meal_slot_counts__group_by` | pytest e2e | nice-to-have | 02-R30 — usage counts after the aggregate rewrite. |

Not proposed: Playwright flows (owner stance); component tests for the 1,100-line builder — drive it once per breakpoint after the token sweep.

---

## Chunk 03 — Shopping Lists
*Source: [`CHUNK_03_shopping_lists.md`](../05_investigations/finalisation/CHUNK_03_shopping_lists.md) · analysed 2026-10-23*

### D. Test plan — Shopping Lists

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__snapshot_template__skips_product_only_lines_and_uses_display_name` | pytest e2e | **must-write-before-ship** | 03-R2 — pins the 500 → skip behaviour and the "Template from None" fix. |
| `test__move_unticked__product_only_lines_move` | pytest e2e | **must-write-before-ship** | 03-R3 — the anchor-key dedupe; the finish dialog's "move to new list" relies on it. |
| `test__membership__ignores_product_only_lines_and_done_lists` | pytest e2e | nice-to-have | 03-R4. |
| `test__quick_add__delegates_to_add_line_dedupe` | pytest e2e | nice-to-have | 03-R5 — nested product line must not count as "already on list". |
| `test__frequently_added__returns_ranked_ids` | pytest e2e | nice-to-have | 03-R6/R14 — replaces the field-shape assertions. |
| `test__instantiate_template__merge_into_list` | pytest e2e | nice-to-have | 03-R33 — new server path. |
| `test__bulk_add__single_commit` | pytest unit | nice-to-have | 03-R34 — count `save_changes` calls on a spy repository. |
| `useShoppingListExport.spec.ts` | vitest | nice-to-have | R-045 fix — mirror `useRecipeExport.spec.ts`. |
| `test__historic_rung__latest_done_purchase_wins` | pytest e2e | nice-to-have | FU-725 — pin before 03-R48 is attempted. |

Not proposed: component tests for the 3,279-line page (drive the three faces once after Stage 2); Playwright flows (owner stance).

---

## Chunk 04 — Cook Mode
*Source: [`CHUNK_04_cook_mode.md`](../05_investigations/finalisation/CHUNK_04_cook_mode.md) · analysed 2026-10-23*

### D. Test plan — Cook Mode

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `useCookTimer.spec.ts` (deadline-based remaining; pause/resume; fake timers advanced past a throttle) | vitest | **must-write-before-ship** | 04-R8 — the only way to pin "backgrounding doesn't slow the timer". |
| `cookSteps.spec.ts` (flattener: top/sub ordering, section inheritance, structured-with-empty-steps fallback, numbered-line stripping) | vitest | **must-write-before-ship** | 04-R20 first extraction — the step model is the surface's core and has never had a test. |
| `cookVoiceCommands.spec.ts` (dispatcher: "stop" precedence, "exit" vs "stop", timer verbs, ignored noise) | vitest | nice-to-have | 04-R20 — owner-specified semantics (2026-09-03) worth pinning. |
| `test__cook_recipe__zero_meals_stamps_last_made_only` + `__positive_meals_bumps_pool_and_writes_event` | pytest e2e | nice-to-have | 04-R19 — pins the response shape and the CookEvent rule. |
| `test__csp__has_media_src` | pytest e2e | nice-to-have | 04-R2 — one-line assertion on the header. |
| `stockLevelStore.spec.ts` (`nameOf`/`sequenceOf`) | vitest | nice-to-have | 04-R11. |

Not proposed: tests for `useSpeechOutput`/`useVoiceInput` (browser APIs; verify by driving on Android Chrome per FU-722/FU-723); Playwright.

---

## Chunk 05 — Stock Overview + Stocktake
*Source: [`CHUNK_05_stock_overview_stocktake.md`](../05_investigations/finalisation/CHUNK_05_stock_overview_stocktake.md) · analysed 2026-10-23*

### D. Test plan — Stock Overview + Stocktake

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

---

## Chunk 06 — Stock-Item Detail
*Source: [`CHUNK_06_stock_item_detail.md`](../05_investigations/finalisation/CHUNK_06_stock_item_detail.md) · analysed 2026-10-23*

### D. Test plan — Stock-Item Detail

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

---

## Chunk 07 — Zero-Input Pantry (P8-07)
*Source: [`CHUNK_07_zero_input_pantry.md`](../05_investigations/finalisation/CHUNK_07_zero_input_pantry.md) · analysed 2026-10-23*

### D. Test plan — Zero-Input Pantry

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__gather__dates_bucket_in_household_zone__not_utc` (level changed 22:00 UTC = 08:00 AEST next day → `days_since_hard == 0`, *Updated today*) | pytest unit (gather with a stub repo) or e2e via `/beliefs` with `timezone=Australia/Sydney` | **must-write-before-ship** | 07-R1 — the FU-525 shape, for belief. |
| `test__belief_envelope__out_is_never_high_confidence` (property over the constants) | pytest unit (hypothesis or a grid) | **must-write-before-ship** | pins impl-plan §1.3's guarantee that every overlay gate relies on; guards 07-R10 either way. |
| `test__recipes__inference_hint__with_no_relationship_include` | pytest e2e | nice-to-have | 07-R2 — proves the FK path hydrates the hint. |
| `test__beliefs_dto__renders_five_fields_only` | pytest e2e (`test_pantry_beliefs_endpoint.py`) | housekeeping | 07-R12. |
| `inferenceHint.spec.ts` | vitest | housekeeping | 07-R5. |

Not proposed: e2e for the shopping / planner hints (drive once with the dense seed); anything for the settings toggles beyond the existing `test__beliefs__per_user_opt_out__gates_and_persists`.

---

## Chunk 08 — Dashboard
*Source: [`CHUNK_08_dashboard.md`](../05_investigations/finalisation/CHUNK_08_dashboard.md) · analysed 2026-10-23*

### D. Test plan — Dashboard

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__restock_radar__item_without_level__is_skipped_not_500` | pytest e2e (`test_dashboard_insight_cards.py`) | **must-write-before-ship** | 08-R1. |
| `dashboardLayout.spec.ts` — `parseLayout` inserts an unseen card at its registry position; retired ids dropped; `defaultHidden` inherited | vitest | **must-write-before-ship** | 08-R7 / 08-R18 — the comment promised it and nothing held it. |
| `test__dora_score__freshness_as_of_household_today` | pytest e2e | nice-to-have | 08-R3 — a +10 h household at 23:00 local. |
| `test__dashboard_summary__shape__no_recipe_or_list_totals` (update the shape test) | pytest e2e | housekeeping | 08-R2. |
| `test__usage_stats__total_spend_matches_spend_by_store_total` | pytest e2e | nice-to-have | 08-R6 — one rule, two readers. |
| `dashboardCalendar.spec.ts` | vitest | housekeeping | 08-R14. |

Not proposed: anything for the card bodies (drive once per `DORA_VERIFY.md` Dashboard rows), the DnD reorder, or the money-off renders (FU-868 is a verify pairing).

---

## Chunk 09 — Alerts + Suggestions
*Source: [`CHUNK_09_alerts_suggestions.md`](../05_investigations/finalisation/CHUNK_09_alerts_suggestions.md) · analysed 2026-10-23*

### D. Test plan — Alerts + Suggestions

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__suggestions__no_string_carries_a_currency_symbol` | pytest e2e (`test_suggestions_router.py`) | **must-write-before-ship** | 09-R1 — the verdict's precedent, for the other inbox. |
| `test__likely_due__uses_cadence_math` (same inputs → same gap as `mean_gap_days`) | pytest unit | nice-to-have | 09-R2. |
| `test__alert_prefs__available_follows_the_evaluator_gates` (money off → `price_drop.available is False`) | pytest e2e | nice-to-have | 09-R13. |
| `attentionRulesCheatSheet.spec.ts` — derived rows equal the former hand table | vitest | housekeeping | 09-R10. |
| `alertStore.spec.ts` — drop `low_count`/`fyi_count` from `EMPTY` | vitest | housekeeping | 09-R15. |

Not proposed: anything for push delivery beyond the existing eight (`test_alerts_push.py`), the brief hour gate (covered in `test_daily_brief*.py`, Chunk 2), or the bell polling (drive once).

---

## Chunk 10 — Products / Price History / Deals
*Source: [`CHUNK_10_products_history_deals.md`](../05_investigations/finalisation/CHUNK_10_products_history_deals.md) · analysed 2026-10-23*

### D. Test plan — Products / History / Deals

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

## Chunk 11 — Assistant (Dora)
*Source: [`CHUNK_11_assistant.md`](../05_investigations/finalisation/CHUNK_11_assistant.md) · analysed 2026-10-23*

### D. Test plan — Assistant

**Existing (keep):** pytest `test_assistant_tool_registry.py` (9: schema↔dispatch integrity, data/action disjoint, mutation gate refuses action tools via `run_tool`, every action tool has a proposer, `nav_for` never offers nav for an action tool, no-model → unavailable), `test_assistant_hardening.py` (8: `_safe_current_path`, `_sanitize_tool_output`), `test_recipe_tools_derivation.py` (5 — recipe *tools* derivation, chunk 1 territory despite the name); vitest `doraIntents.spec` (intent routing corpus, add-to-list parsing, greeting name), `doraModeSlider.spec` (12 incl. axe), `voicePicker.spec` (8).

**Proposed (lean — stable contracts only):**
| # | Pins | Layer | Why |
|---|---|---|---|
| T1 | Every `confirm_actions.PROPOSERS` entry, called with `{}` and with a plausible `item_name`/`recipe_name` against an empty DB, returns a dict with `status` and never raises | pytest (extend the registry test) | 11-R1 — "has a proposer" passed while three proposers crashed |
| T2 | Every `_TOOL_NAV` path is in an allow-list of live SPA route prefixes kept beside the test | pytest | 11-R3 |
| T3 | Every `_TOOLS` entry, called with `{}` against an empty DB, returns a list and never raises | pytest | 11-R2 — catches import/NameError-class faults in any tool |
| T4 | `GET /assistant/capabilities` names == `TOOL_SCHEMAS` names, and every action schema has a proposer + committer; each schema carries ≥1 example | pytest | 11-R8 / 11-R26 |
| T5 | `runIntent('where_is')` names the location when the snapshot has one; "(no location)" only when null | vitest (extend `doraIntents.spec`) | 11-R4 |
| T6 | 11th probe in a minute → 429 with `Retry-After` | pytest | 11-R15 |
| — | Slider height, help-page rendering, voice paths, chat layout | — | **no automated test** — drive once and delete the DORA_VERIFY line |

**DORA_VERIFY additions (Stage 2 close):** AI "cross off bread" produces a confirm card; "what am I wasting" answers; every "See it" button under an AI answer opens a real page; Basic "where's the X" names the location; chat text scales with Settings → Appearance font size (DB1); launcher hover no longer flashes (DB4); slider tap target on a phone (FU-663).

---

## Chunk 12 — Reports / Memory (P8-09), Waste, Budget
*Source: [`CHUNK_12_reports_memory.md`](../05_investigations/finalisation/CHUNK_12_reports_memory.md) · analysed 2026-10-23*

### D. Test plan — Reports / Waste / Budget

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

## Chunk 13 — Settings shell
*Source: [`CHUNK_13_settings_shell.md`](../05_investigations/finalisation/CHUNK_13_settings_shell.md) · analysed 2026-10-23*

### D. Test plan — Settings shell

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `PATCH /app-settings {nutrition_mode:'bogus'}` → 400 with `detail` naming the options | pytest | must-write-before-ship | 13-R1 fix |
| Admin PATCH `/users/<id>` with malformed / duplicate email → 422/400; valid email sets `email_verified` | pytest | must-write-before-ship | 13-R2 |
| Deactivate admin B, delete admin A → 400 "last admin" | pytest | must-write-before-ship | 13-R3 |
| `/health` emits `products_policy.search_url` (or chosen key) and never drops existing keys | pytest | nice-to-have | 13-R4 |
| `familyAndModeOf(normaliseLegacyTheme('pesto-noir'))` → pesto/dark | vitest | nice-to-have | 13-R6 |
| `useAppSettingField` reverts the draft and toasts on a rejected save | vitest | nice-to-have | 13-R9 |
| Admin user list requests > 50 rows (`limit` param present) | vitest (service) | nice-to-have | 13-R5 |
| `HealthInfo`/`AppSettings` TS types compile against a fixture of the real DTO keys (`designTokensDeclared.spec.ts` style contract check) | vitest | nice-to-have | 13-R16 |

Existing coverage is good on the admin/auth boundary (17 app-settings, 7 users-admin, 17 user-router, 7 operational-config). No Playwright.

---

## Chunk 14 — Onboarding
*Source: [`CHUNK_14_onboarding.md`](../05_investigations/finalisation/CHUNK_14_onboarding.md) · analysed 2026-10-23*

### D. Test plan — Onboarding

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `seed-demo` on a week that already has a `MealPlan` → entry appended to it, plan count unchanged | pytest | must-write-before-ship | 14-R1 |
| `seed-demo` after `seed-items` with the three pack names → `items_created == 0` | pytest | must-write-before-ship | 14-R2 |
| `GET /onboarding/state` → `{first_user}` only; `/complete` then `/auth/me.onboarding_completed_at` non-null; `/restart` → null | pytest | nice-to-have | 14-R12 (contract pin) |
| `SeedRequest.extra_group_names` / `extra_location_names` created in the same transaction, deduped by name | pytest (unit, `_FakeRepo`) | nice-to-have | 14-R19 |
| Wizard `THEME_OPTIONS` values equal `themeKeyFor(mode, pesto)` | vitest | nice-to-have | 14-R5 |
| `normaliseHeadcount` bounds (null / 0 / 1.7 / 150) | vitest | nice-to-have | 14-R9 |

Existing coverage is strong on the seed handlers (17 unit + 13 e2e); none on the wizard itself and that stays so (lean stance — one manual walk of A2 per release).

---

## Chunk 15 — Auth shell
*Source: [`CHUNK_15_auth_shell.md`](../05_investigations/finalisation/CHUNK_15_auth_shell.md) · analysed 2026-10-23*

### D. Test plan — Auth shell

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| With `DORA_TRUSTED_PROXY_HOPS=1`, `X-Forwarded-For: 10.0.0.9` → `remote_addr == 10.0.0.9`; with 0 (default) the header is ignored | pytest | must-write-before-ship | 15-R1 |
| DEBUG request logging never includes a `password`/`token` value (capture the log handler, POST `/auth/login`) | pytest | must-write-before-ship | 15-R2 |
| `POST /auth/logout` clears the session (`/me` → 401) and emits `auth.logout`; `Set-Cookie` deletes `dora_csrf` | pytest | nice-to-have | 15-R4 (no logout test exists) |
| Session staleness: login on client A, change password on client B → A's `/me` → 401 | pytest | nice-to-have | pins `get_me:50–61` (untested today) |
| Deactivated user's live cookie → `/me` 401 with the deactivated message | pytest | nice-to-have | pins `get_me:40–48` (untested) |
| `api_response.too_many_requests` sets `Retry-After ≥ 1` and problem+json | pytest (unit) | nice-to-have | 15-R7 |
| `PasswordField` shows the `MIN_PASSWORD_LENGTH` rule from `models/password.ts` | vitest | nice-to-have | 15-R8 |
| `find_active_token` equality lookup still rejects a hash-collision-shaped wrong token | pytest | nice-to-have | 15-R23 |

Existing: 28 + 6 pytest, 17 vitest, 3 Playwright (smoke layer — unchanged). No new Playwright.

---

## Chunk 16 — Ingestion API + companion seam
*Source: [`CHUNK_16_ingestion_api.md`](../05_investigations/finalisation/CHUNK_16_ingestion_api.md) · analysed 2026-10-23*

### D. Test plan — Ingestion API

| # | Test | Layer | Priority | Trigger to write it |
|---|---|---|---|---|
| D1 | `test__ingest__expired_idempotency_key_is_reprocessed_not_500` — insert an `IdempotencyKey` with `expires_at` in the past (direct repo write inside `app.app_context()` as `test_ingest_batch.py:296–303` does), re-push with that key → 200, records accepted, row refreshed, exactly one row for `(source, key)` | pytest | **must-write-before-ship** | with 16-R2 |
| D2 | `test__ingest__stamping_a_key_purges_expired_rows` | pytest | nice-to-have | with 16-R3 |
| D3 | `test__ingest__is_available_round_trips` (false on create, unchanged on a push without it) | pytest | must-write **when** 16-R5 lands | with the FU |
| D4 | `test__ingest_stores__stamps_last_used_at` | pytest | nice-to-have | with 16-R4 |
| D5 | `test__link_status__never_resolves_a_custom_product` — create a custom product via `POST /products` at the seeded store, look it up by `(store, name)` → `product_not_found`; then push the same name via ingest → the ingested id (not the custom one) | pytest | **must-write-before-ship** | with 16-R8 |
| D6 | `test__ingest__validation_errors_are_structured` — replaces the text assertion in `test__ingest__rejects_price_observations_field:353–354` | pytest | must-write (adjust) | with 16-R34/R9 |
| D7 | `test__ingest_store_image__serves_an_uploaded_logo` (200 path; today only the 404 path is pinned, and it `return`s when no bare store exists) | pytest | nice-to-have | opportunistic |
| — | Vitest for `ApiAccessSettings.vue` | — | **no** | thin page over the API; G1–G16 by hand once |

Existing coverage is strong (45 tests pin auth, dedupe, quarantine, `store_id`, paging, PF-8, image round-trip, admin sweep). No Playwright.

---

## Chunk 17 — Offline / PWA / native
*Source: [`CHUNK_17_offline_pwa_native.md`](../05_investigations/finalisation/CHUNK_17_offline_pwa_native.md) · analysed 2026-10-23*

### D. Test plan — Offline / PWA / native

| # | Test | Layer | Priority | Trigger to write it |
|---|---|---|---|---|
| D1 | `usePushSubscription.ensureRegistration` uses the existing registration (`serviceWorker.ready`) and never calls `register()` when one exists; falls back to registering `/push-sw.js` only when `getRegistration()` is null | vitest (mock `navigator.serviceWorker`) | **must-write-before-ship** | with 17-R1 |
| D2 | `usePwaLifecycle`: `controllerchange` with no controller at boot → no update; with a controller → `updateAvailable`; `dismissUpdate` hides; `installUnavailableReason` → `insecure-context` when `isSecureContext === false` | vitest | nice-to-have | with 17-R1 (pins the guard the fix relies on) |
| D3 | `clearApiResponseCache` deletes `dora-api*` and `dora-stock-images*`, leaves `dora-merchant-images*`, never throws when `caches` is undefined | vitest (mock `caches`) | nice-to-have | with 17-R7 |
| D4 | `backendUrl.normaliseUrl` — scheme default, `/api` suffix, trailing-slash trim (and whatever 15-R16/`BackendSetupPage` decides about `http://` LAN defaults) | vitest | nice-to-have | when the scheme rule is next touched |
| D5 | Build check: `npm run build` emits `sw.js` containing `importScripts("push-sw.js")` and no `offline.html` reference | script / CI (`grep` on `dist/spa/sw.js`) | nice-to-have | with 17-R1/R2 — a one-line check in the build script, not a test suite |
| — | `useNetworkStatus` | — | **no** (FU-539 stance) | manual G5–G7 |

No Playwright. Device walk (`DORA_VERIFY` P8-10 + PWA sections) remains the real proof.

---

## Chunk 18 — Backup & restore + Import
*Source: [`CHUNK_18_backup_restore_import.md`](../05_investigations/finalisation/CHUNK_18_backup_restore_import.md) · analysed 2026-10-23*

### D. Test plan — Backup & restore + Import

| # | Test | Layer | Priority | Trigger to write it |
|---|---|---|---|---|
| D1 | `test__restore_backup__partial_mode__restores_selected_rows_and_pulls_in_parents` — back up, delete one stock item + its location, restore `mode=partial` with `selection={"stock_items":[id]}` → 200, item back, location pulled in, no KeyError | pytest | **must-write-before-ship** | with 18-R1 |
| D2 | `test__backup_sections__catalogue_matches_SECTIONS` — `GET /data/backup/sections` keys == `[s.backup_key for s in SECTIONS]`, `default_on` matches; plus a Vitest that the page builds its groups from the response (no local list) | pytest + vitest | **must-write-before-ship** | with 18-R3 (replaces the comment "keep this in sync") |
| D3 | `test__download_backup__sha256_mismatch__is_409` | pytest | nice-to-have | with 18-R14 |
| D4 | `test__spreadsheet_import__level_last_updated_is_utc_aware` (assert `tzinfo` or ISO `+00:00` on the created item) | pytest | nice-to-have | with 18-R4 |
| D5 | `test__spreadsheet_import__slash_dates_follow_install_locale` (`03/04/2027` → 3 Apr on `en-AU`, 4 Mar on `en-US`) | pytest | nice-to-have | with 18-R12 |
| D6 | `test__restore_backup__stale_required_fk_entries_absent` — `REQUIRED_FKS`/`HARD_FK_PULL_IN` keys ⊆ `SECTIONS` keys and columns exist on the table (module-load assertion like `_validate_import_templates`, so the next rework can't leave a dead key) | pytest | **must-write-before-ship** | with 18-R1 — pins the class, not the instance |
| D7 | `test__restore_backup__round_trips_recipe_steps_and_vocab` — backup with default UI sections → wipe recipe tables → restore → steps/tools/tags/cuisine present (closes the three VERIFY bullets by automation since it is a stable contract) | pytest | nice-to-have | with 18-R3 |
| — | Vitest for the two pages | — | **no** | thin over the API after 18-R7; manual G1–G17 |

---

## Chunk 19 — Ops / self-host
*Source: [`CHUNK_19_ops_self_host.md`](../05_investigations/finalisation/CHUNK_19_ops_self_host.md) · analysed 2026-10-23*

### D. Test plan — Ops / self-host

| # | Test | Layer | Priority | Trigger to write it |
|---|---|---|---|---|
| D1 | Build-time assertion in `Dockerfile`: `RUN test -f dist/spa/sw.js && test -f dist/spa/manifest.json` after the SPA build | Docker build step | **must-write-before-ship** | with 19-R1 (not a pytest; it is the only place the image's build mode is observable) |
| D2 | `test__log_level__resolves_env_then_json_then_profile` + `__unknown_value_warns_and_falls_back` | pytest (unit, `DoraConfig` with a temp config path) | nice-to-have | with 19-R5 |
| D3 | `test__profile__production_gate_lists_every_missing_var` / `__skip_flag_bypasses` (SystemExit captured) | pytest unit | nice-to-have | opportunistic — `profile.py` has zero tests |
| D4 | `test__version_check__repo_slug_matches_support_channel` (both import the one constant) | pytest unit | **must-write-before-ship** | with 19-R3 |
| D5 | `test__health__profile_reports_canonical_name` (`DORA_ENV=prod` → `"production"`) | pytest e2e | nice-to-have | with 19-R9 |
| D6 | Extend `test_compose_env_coverage` scan dirs to `gunicorn.conf.py` + `startup.sh` so `DORA_WEB_*`/`DORA_API_SERVER` are **read-side** verified, not just omit-listed | pytest unit | nice-to-have | with 19-R17 |
| D7 | `test__dockerignore_excludes_frontend_env` (string check on `.dockerignore`) | pytest unit | nice-to-have | with 19-R2 — cheap structural pin, same spirit as `test_compose_env_coverage` |
| — | Desktop bundle, compose boot, migrations on a real old DB | manual (A2) | — | release walk |

---

## Chunk 20 — Cross-cutting concerns
*Source: [`CHUNK_20_cross_cutting.md`](../05_investigations/finalisation/CHUNK_20_cross_cutting.md) · analysed 2026-10-23*

### D. Test plan — cross-cutting

| # | Test | Layer | Priority | Trigger to write it |
|---|---|---|---|---|
| D1 | `useDateFormat.spec.ts` — `formatDate('2026-09-03')` renders 3 Sept in `America/New_York`; `formatDateTime` medium+short; `formatRelativeDay` Today/Tomorrow/weekday/short; locale switch re-keys the formatter cache | vitest (fake timers + `Intl` locale) | **must-write-before-ship** | the D-006 authority has zero tests and is the kind of stable contract the owner's test stance wants pinned |
| D2 | `useMoney.spec.ts` — `formatMoney` null → `–`, 2 decimals, `currencySymbol` for AUD/USD/EUR under `en-AU`; `refreshMoneyPolicy` rebuilds the formatter | vitest | nice-to-have | with 20-R25 |
| D3 | `test__units_table_generated_is_current` — regenerate via `scripts/dump_units.py` into a temp path and diff against `web_app/src/generated/units_table.ts` (pins 20-R3/R4's single source) | pytest | **must-write-before-ship** | with 20-R3 (check whether one exists first — `grep dump_units tests/`) |
| D4 | `useConfirm.spec.ts` — resolves true on OK / false on cancel+dismiss; never passes `html`; destructive adds the suffix and `negative` colour | vitest | nice-to-have | with 20-R11 |
| D5 | `useShortcut.spec.ts` — typing-target guard, sequence timeout, newest-first precedence, Escape closes the cheatsheet | vitest | nice-to-have | opportunistic (139 lines, no tests) |
| D6 | `test__client_logs__bucket_keys_are_evicted` | pytest | nice-to-have | with 20-R9 |
| D7 | Structural: `grep` guard that no `.vue` sets `position:` on `Notify.create` except an allow-list of system toasts | vitest (fs scan, like `test_compose_env_coverage`) | nice-to-have | with 20-R10 — cheap drift pin |
| — | Visual contrast checks (FU-671/674) | manual, per theme | — | owner's FU-010 walk |

---
