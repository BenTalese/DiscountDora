# Dora Follow-ups Ledger — Resolved

Archive of `[RESOLVED]` items moved out of `DORA_FOLLOWUPS.md`. Kept for the
audit trail — never delete entries here.

When you resolve an open item, move its block from `DORA_FOLLOWUPS.md` to this
file, flip the heading from `[OPEN]` to `[RESOLVED]`, and append a one-line
state note describing how it was resolved (date + brief mechanism). New
resolutions go at the **top**.

---

## [RESOLVED] FU-367 — PROPOSAL_HELP_OVERLAY superseded → narrower `(?)` help chips shipped instead
- **Resolved:** 2026-07-07 — this was already superseded on 2026-07-06; the ledger just hadn't caught up. `docs/04_proposals/PROPOSAL_HELP_OVERLAY.md` carries a 📦 **SUPERSEDED (2026-07-06)** banner at the top: the opt-in overlay design (`?` toolbar toggle + `v-help` directive + dismissible per-element overlays + DoraBot fronting + discoverability nudge) was retired when FU-044 was re-scoped mid-session. The narrower ask — targeted `(?)` hover-tooltip chips on ~25 specific confusing controls — shipped instead via `IMPL_PLAN_HELP_CHIPS.md` and [[FU-503]] / [[FU-044]] (both resolved 2026-07-06). Help page + DoraBot assistant remain the deep-help fallback. Proposal file kept as the record of the parked design.

## [RESOLVED] FU-459 — App-wide security headers shipped (CSP / X-Frame-Options / X-Content-Type-Options / Referrer-Policy)
- **Resolved:** 2026-07-07 — added `attach_security_headers` `@after_app_request` hook in `dora_api/infrastructure/middleware.py`. Sets `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer-when-downgrade`, and a permissive-but-honest `Content-Security-Policy` on every response. CSP: `default-src 'self'`; `script-src` allows `'unsafe-inline' 'unsafe-eval'` (Quasar runtime + Vue's HTML-shell inline scripts); `style-src 'unsafe-inline'` (Vue scoped styles + Quasar dynamic theming); `img-src` allows `data: blob: https:` (base64 image blobs, upload previews, external product/store images); `connect-src 'self' https:` (self-hosted → external LLM); `frame-ancestors 'none'` (CSP-native companion to X-Frame-Options); `base-uri 'self'`; `form-action 'self'`. Hand-rolled, no Flask-Talisman dependency. `response.headers.setdefault(...)` so a reverse proxy that already sets any of them wins; `DORA_DISABLE_SECURITY_HEADERS=1` opts out entirely (escape hatch when a proxy/CDN conflicts — not for production). Tightening `script-src` off `'unsafe-inline'/'unsafe-eval'` requires a nonce-per-response scheme or build-time change, deferred as a future FU if warranted.

## [RESOLVED] FU-509 — Logging desktop-vs-dev split → documented in `logging_setup.py`
- **Resolved:** 2026-07-07 — added an explicit `Note on log_dir` block to `configure_logging()` explaining that dev/hosted-web uses `./data/logs/<service>/` and desktop uses `platformdirs.user_log_dir` per-OS; the split is intentional (OS-standard on packaged distributions, tail-friendly on dev runs) and the function itself doesn't care. No behaviour change.

## [RESOLVED] FU-508 — `StockItem.image` feature dropped entirely
- **Resolved:** 2026-07-07 — user chose to drop the feature outright (anti-creep — visual noise, half-built, linked Products carry the visual). Removed column + downstream chain: migration `a4c9e1f2b3d5_20260707_drop_stock_item_image` drops `StockItem.image` + `User.show_stock_images`; deleted `get_stock_item_image.py` endpoint; stripped `has_image` + `_hydrate_has_image` from `get_stock_items.py`; removed `has_image`/`has_own_image` from `get_stock_item_detail.py`; dropped `image` field from `create_stock_item.py` + `update_stock_item.py`; removed `show_stock_images` from `User`/`register_user.py`/`update_me.py`; deleted SPA image slot in `StockItemRow.vue`, image upload field in `StockItemDetailPage.vue`, image-toggle button in `StockOverview.vue`, `stockItemImageUrl` in `stockItemApiService.ts`, `imageVersionOf`/`bumpImageVersion` in `stockItemStore.ts`, and the `showStockImages`/`setStockImages` half of `useImagePrefs.ts`. Companion `show_recipe_images` opt-in stays. Test: e2e `test_stock_item_router.py` DTO shape updated to drop `has_image`.

## [RESOLVED] FU-507 — Expiry-on-open prompt shipped
- **Resolved:** 2026-07-07 — added the FU-415-decided dialog to both the stock-item row (`StockItemRow.vue:onToggleOpen`) and the detail page (`StockItemDetailPage.vue:onToggleOpen`). When `is_open` flips true, a Quasar `$q.dialog({ prompt: { type: 'date' } })` prefilled with the current expiry asks "Update its effective expiry?" — OK sends `expiry_date` + `is_open: true` in one PATCH; Skip sends `is_open: true` only (default-unchanged shape). No new server endpoint — `update_stock_item.py` already accepted `expiry_date`. Toggling to sealed unchanged.

## [RESOLVED] FU-506 — Recipe editor free-text ingredient path shipped
- **Resolved:** 2026-07-07 — added a `Use "<typed>" as free text (no pantry link)` option in the recipe editor's ingredient picker `#after-options` (`RecipeDetailPage.vue`). `useAsRawText(idx, text)` sets `stock_item_id=null` + `raw_text=text` on the row, and an unlinked row now surfaces its `raw_text` as a small italic caption below the picker + label flips to "Free-text ingredient". Save path already sent `raw_text` (Chunk 4 shape); server already accepted `stock_item_id=null + raw_text` (`recipe_ingredient_anchor` CHECK). No server change.

## [RESOLVED] FU-505 — Unlinked-ingredient warning banner on auto-gen
- **Resolved:** 2026-07-07 — user picked the banner shape over adding a `raw_text` column to `ShoppingListLine` (would demand a new line-rendering path + snapshot/tick behaviour for text-only lines). `_UnlinkedSkip` dataclass added; `_collect_recipes` + `_collect_meal_plan_week` in `auto_generate.py` append `(recipe_name, ingredient_name from raw_text)` when they encounter an ingredient with `stock_item is None`; response payload carries the list. SPA `useMealPlanner.generateListForWeek` now renders a `$q.dialog` after the auto-gen success toast listing the skipped ingredients (`• <ingredient> (<recipe>)`) with an "Add these manually" title. `NewListDialog` doesn't invoke recipe sources today so no wiring there; the SDK type includes the field so it's ready when it does.

## [RESOLVED] FU-420 — Recipes: non-linked ingredients still fully accounted for → traced; model + cookability + cook-mode clean; one drop-off + one UI gap spun off
- **Resolved:** 2026-07-07 — parallel Explore agent walked the null-`stock_item_id` path end-to-end. **Model:** nullable + `recipe_ingredient_anchor` CHECK constraint requires `stock_item_id` OR `raw_text` (`dora_api/domain/entities/recipe_ingredient.py`, migration `c5a8e1f7d3b2`). **Cookability:** `recipe_cookability.py:26-94` correctly returns tri-state (`None` when any required ingredient is unlinked). **Cook-mode finish:** `cook_recipe.py:38-72` deducts nothing per-ingredient (only bumps `available_meals`), so unlinked rows are safe. **Drop-off:** `auto_generate.py:321,380` silently skips unlinked ingredients from shopping-list generation — spun off as [[FU-505]]. **UI gap:** no user-facing path to create unlinked ingredients (only URL/paste import populates them) — spun off as [[FU-506]]. The trace itself is complete; the fixes are properly bounded FUs.

## [RESOLVED] FU-417 — MAGIC_BEHAVIOUR_AUDIT verdicts delta-check → all 18 accounted for
- **Resolved:** 2026-07-07 — parallel Explore agent walked all 18 verdicts (F1–F18) in `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` "Verdicts (2026-06-28)" against shipped code. **13 confirmed keep-silent / already-right** (F2, F4, F6, F8, F10–F12, F13–F18). **3 upgrades shipped:** F1→[[FU-315]] (auto-add toast + list-name), F3→[[FU-316]] (remembered-list toast + always-ask setting), F9→[[FU-319]] (inline-create toast reworded). **2 upgrades still outstanding but already tracked:** F5→[[FU-317]] (meal-plan reconcile — awaiting proposal doc; deliberate delay), F7→[[FU-318]] (cheapest-offer chip on line; small + bounded, gated behind FU-320 help-copy work). Every verdict has a home; no new FU needed.

## [RESOLVED] FU-416 — ORPHANED_FIELDS_AUDIT delta-check → 6 of 7 accounted for; one spun off
- **Resolved:** 2026-07-07 — parallel Explore agent cross-referenced every field in `docs/05_investigations/ORPHANED_FIELDS_AUDIT.md` against current schema/code. **Wired up:** `StockItemSubstitute.notes` (accepted in `AddSubstituteRequest`, in `SubstituteDto`). **Removed via migrations:** `StockItem.preferred_product_id` (migration `d2a7f4c9e6b1`, 2026-06-14; report now estimates from cheapest recent product price), `StockItem.barcode` (migration `a3f1c7d2e9b4`, 2026-06-12, P6-02; real barcodes attach to Product, not StockItem). **Backend-only by design (no action):** `ShoppingListLine.picked_offer_price` + `list_price_at_pick` (used only in reports/budget/waste analytics). **Still orphaned:** `StockItem.image` — column exists, `get_stock_items.py:42-47` hydrates a `has_image` flag, but upload UI + DTO field + display chain never built — spun off as [[FU-508]] for keep-or-drop call.

## [RESOLVED] FU-415 — FEATURE_CLARIFICATIONS expiry ↔ open interaction → decided: prompt on open
- **Resolved:** 2026-07-07 — user decision. When `is_open` is flipped to true, the SPA will **prompt the user for an updated effective expiry** (default: unchanged). Chosen over "independent" (loses information about the mostly-real "opened shortens shelf life" pattern) and "fixed % shortening" (universal rule is wrong per item: opened milk vs opened jam). Implementation deferred and tracked as [[FU-507]] — small dialog on the open toggle with a prefilled date picker; server takes an optional `expires_on` in the same PATCH; no new endpoint. Docs implication: `docs/05_investigations/FEATURE_CLARIFICATIONS.md §(c)` should reference this decision on next touch.

## [RESOLVED] FU-414 — LOGGING_AND_DATA_LAYOUT delta-check → 6/7 shipped; one spun off
- **Resolved:** 2026-07-07 — parallel Explore agent walked every recommendation in `docs/05_investigations/LOGGING_AND_DATA_LAYOUT.md`. **Shipped:** time-based rotation (`TimedRotatingFileHandler(when="midnight", backupCount=14)` at `logging_setup.py:88-96` — FU-027), `.YYYY-MM-DD` rotation suffix, 14-day backup count, stdout handler retained for Docker aggregation, `.secret_key` relocation via `config_manager.get_data_dir()` (`app.py:73` — FU-037), `data/` ÷ `cache/` split preserved. **Outstanding:** desktop vs dev log-location split (`platformdirs.user_log_dir` on desktop, `./data/logs/<service>/` on dev) — spun off as [[FU-509]] for the unify-or-document call.

## [RESOLVED] FU-419 — Recipes: healthy/unhealthy rating + filter/sort → dropped
- **Resolved:** 2026-07-07 — decision call: **dropped**. Anti-creep tiebreak from the Charter: a manual 5★ healthiness field is subjective (no clear input signal — who decides 5★?) and adds a field users must maintain forever. Cookbook already has tags + favourites for the "I feel like something light" cue, and if a nutrition-complex mode is ever built it can carry an objective, derived health score (not a manual rating). No code change; original-spec intent recorded as superseded.
- **Raised:** 2026-07-01 (original-spec sweep).
- **Type:** deferred job (dropped intent) — now formally dropped.

## [RESOLVED] FU-425 — Pricing reassessment handoff → fully executed, archived to `06_legacy_prompt_plans/`
- **Resolved:** 2026-07-07 — comprehensive delta-check via an Explore agent walked every §6 (A–K), §6a (A1 deep-dive + two-mode PriceEntry), and §6b (LC-1 through LC-5) decision from `PRICING_SYSTEM_REASSESSMENT_HANDOFF.md` against shipped code. **All shipped, no gaps.** Handoff moved from `docs/99_scratch/` to `docs/06_legacy_prompt_plans/PRICING_SYSTEM_REASSESSMENT_HANDOFF.md` with an archive banner at the top pointing at IMPL_PLAN_YOUR_PRICES.md as the execution vehicle and this FU as the delta-check.
- **Coverage confirmed:** every decision — folded observation shape (A1) · nullable `store_id` (A2) · user-editable `observed_at` (A3) · dropped `source` enum + FK provenance (A4) · count dimension (B1) · extracted units module + SPA codegen mirror (B2) · flat picker, no smart defaults (B3) · per-dimension baseline (B4) · median + 1.15× + min-3 + trailing-12mo (C1-C2) · observation-only baseline (C3, LC-2) · inline widget + bottom-sheet + price-history page (C5) · never-converted offers/observations (D1) · colour-coded chart (D2) · prefill priority ladder (D3) · prefill-and-persist, no bulk copy (E1-E2) · `/finish` as only harvest path (E3) · sizeless-vs-sized harvest (E4) · till total (E5) · product-less lines (E6) · shared `PriceEntry` component (F1) · source-labelled prefill (F2) · row button + `mdi-cash-plus` (G1-G3) · intra-build staging (H1, LC-5) · products-off history (H2) · money-gated "Receipt" relabel (I1) · UI-gated observation endpoints (I3) · removed ingestion→observation path (J1) · non-preserving migration + partial UNIQUE (K1, LC-1) · extracted `line_paid_unit_price` helper (K2). All in code.
- **Bonus shape-changes en route** (additive within FU-227, not reshaping the core):
  - `pack_count` optional informational field added (FU-232 follow-up) — folded shape still intact; count is display-only, math ignores it.
  - Locale display denominators (AU `/100ml` vs US `/fl oz`) via `display_denominator_for()` in `domain/units.py` — FU-228 follow-up, natural consequence of multi-locale support.
  - Chart series helpers (`build_stock_item_price_series`, `build_product_observation_series` in `your_prices.py`) — implementation detail surfaced during chunks 5-6, not a design shift.
- **Raised:** 2026-07-01 (docs audit).
- **Type (original):** finding (verification-only).

## [RESOLVED] FU-424 — Senior review Tier-2 credibility gaps → all four routed to concrete FUs
- **Resolved:** 2026-07-07 — the four Tier-2 items from `docs/99_scratch/SENIOR_REVIEW_2026-06-16.md` are all now either shipped or tracked by concrete FUs. FU-424 was a "confirm status" umbrella; that status is now confirmed.
- **Tier-2 resolution summary:**
  1. **Unreachable Postgres posture** → **CLOSED** via [[FU-045]] (Postgres migration path documented; SQLite still supported for lightweight self-host per §7.5).
  2. **~237 prompt-ID comments in shipped source** → **CLOSED** via [[FU-462]] (2026-07-07: 887 refs stripped across 202 files; R-008 hardened with an explicit close-time grep).
  3. **Half-finished base-component adoption** → **AUDITED THIS SESSION** via an Explore agent. Findings: 54 raw `q-btn` uses across 16 files (mostly straightforward migrations, 3-4 defensible "unelevated coloured icon" outliers waiting on a `BaseButton` variant decision); `q-dialog` / `q-btn-toggle` / `q-btn-dropdown` are all clean (defensible non-modal / wrapper cases). **Real work bounded and opportunistic** — logged as [[FU-504]] rather than left as an unbounded credibility gap.
  4. **Missing request-level transaction safety** → **AUDITED THIS SESSION**. 72 write handlers; 23 have multiple `save_changes()` calls (torn-state risk on mid-flow failure). Worst offenders: `create_recipe.py` (5 saves), `shopping_list_templates/manage_templates.py` (11 saves across bundled handlers), `meal_plan_templates/manage_templates.py` (3 saves in create + 3 in clone), `new_recipe_version.py` (2). **Work already tracked** by [[FU-456]] (unit-of-work refactor starting with `create_recipe.py`). The audit confirms FU-456's shape is right: opportunistic per-touch with the flush-based pattern, not a project-wide sweep. No new FU needed; FU-456's scope is sufficient.
- **Nothing left unrouted** — every Tier-2 item is now either shipped (postgres, prompt-IDs), tracked with bounded scope (FU-504), or tracked with a working impl-plan (FU-456). FU-424 itself has no residual work.
- **Cross-ref:** [[FU-045]] · [[FU-462]] · [[FU-456]] · [[FU-504]] · [[FU-409]] (auth findings re-audit — overlapping but separate, still open).
- **Raised:** 2026-07-01 (docs audit).
- **Type (original):** finding (audit-only).

## [RESOLVED] FU-460 — `SESSION_COOKIE_SECURE` default → kept off, added prod-mode warning (option a)
- **Resolved:** 2026-07-07 — took option (a) per the FU's recommended path. Default stays off (right for desktop / LAN self-host over plain HTTP / local dev), but any install running in `DORA_ENV=production` without an explicit `DORA_SECURE_COOKIES` value now sees a loud stderr banner at boot. Fits §7.5 distribution-posture "same artifact, different config" — the operator sees the warning once, makes an explicit choice either way, and it goes quiet.
- **Cohort caught:** any HTTPS-fronted install (SaaS or self-host behind Let's Encrypt / Cloudflare / LB TLS termination) that forgot the flag. Cohort NOT nagged: desktop app, LAN-only self-host over plain HTTP, dev.
- **What shipped:**
  - `dora_api/infrastructure/profile.py` — new `warn_if_insecure_cookies_in_production()` sibling to `validate_production_requirements`. Warns only when the var is **unset** (empty or missing). An explicit `DORA_SECURE_COOKIES=false` is treated as an intentional operator choice (internal LAN behind VPN, home-lab, no cert) and silenced without complaint. `DORA_SKIP_PROD_VALIDATION=true` also silences (same escape hatch as the sibling validator).
  - `dora_api/startup.py` — called right after `validate_production_requirements()` so the message lands before DI-container / DB / audit setup noise.
  - `tests/test_profile_warnings.py` (new) — 6 tests: silent-in-dev, fires-when-prod-and-unset, silent-when-explicitly-true, silent-when-explicitly-false, silent-when-skip-flag-set, fires-when-whitespace-only.
- **Deliberate design calls:**
  - **Warning, not boot-block.** A prod-mode install intentionally served over plain HTTP (internal LAN behind a VPN) is a legitimate shape; the operator has made a choice and shouldn't be forced to set an override flag. A boot-block would collide with §7.5's "same artifact" rule.
  - **Silent on explicit `false`.** The whole point is to catch operators who forgot the flag; someone who typed `DORA_SECURE_COOKIES=false` did not forget.
  - **Kept the default off** rather than flipping on. Flipping on would break every desktop / LAN install on next launch — the very cohort that has no HTTPS. Option (b) from the FU was cleaner in isolation but hostile to §7.5.
  - **Reused the existing validator's escape hatch** (`DORA_SKIP_PROD_VALIDATION`) so the two prod-mode guards behave consistently.
- **Verification:**
  - `pytest tests/ -q` → **824 passed, 0 failed** (up from 818 with the 6 new tests).
  - R-008 close-gate grep → **0 hits**.
  - Operator-smoke checklist added to `DORA_VERIFY.md` under a new **Operator** heading — 7 checks covering the 5 warning-decision branches plus a browser cookie-inspector round-trip.
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (e) sub-part).
- **Type (original):** finding / policy call.
- **Cross-ref:** [[FU-459]] (app-wide security headers) — separate hardening item still open; would land in the same Phase-4 hardening pass.

## [RESOLVED] FU-503 — Unused `budgetApi` var on ShoppingListDetail.vue → deleted
- **Resolved:** 2026-07-07 — deleted the unused declaration (and its now-orphan `BudgetApiService` import) from [ShoppingListDetail.vue](web_app/src/pages/ShoppingListDetail.vue). Grep confirmed every `trim-to-budget` call in the file goes through the primary `api` (`ShoppingListApiService`), not `budgetApi` — the local `budgetApi` never had a call-site, so no wiring was intended. ESLint clean on the file after the edit.
- **Raised:** 2026-07-07 (FU-452 lint pass).
- **Type (original):** finding / lint noise.

## [RESOLVED] FU-452 — P6-11 location-aware grouping → Surface A (put-away dialog) shipped, Surface B (alerts group-by-location) CUT
- **Resolved:** 2026-07-07 — user's call: ship Surface A only as an on-demand helper dialog off the finished-list toolbar, cut Surface B permanently ("never do B, don't think it's necessary"). Ephemeral state per user preference — the dialog is a physical-world checklist, not a data commitment.
- **Surface A (shipped):** Post-`Finish & restock`, a **Put away** button appears in the list's toolbar next to *Copy to new list*. Clicking opens `PutAwayDialog`, which groups the list's ticked lines by their `stock_location_breadcrumb` — one card per location with a tick-per-group affordance ("Freezer · 3") and a "(No location)" bucket at the bottom for unsorted items. Each unsorted line carries an inline "Assign" button that opens a small location picker (walked tree, same shape as the create-stock-item / stock-filter pickers); on save it calls `PATCH /api/stock-items/<id>` with the new `stock_location_id` and triggers a list-detail reload so the item moves group.
- **Surface B (CUT):** Grouping expiring alerts by location — not built and won't be. User's call: not necessary. No `AlertDto` location enrichment, no `AlertsPage` toggle. If it ever becomes an actual ask, re-open a new FU; the one-liner `.include(StockItem.Fields.STOCK_LOCATION)` in `get_alerts.py` is documented in the FU-452 research report if it ever needs to resurrect.
- **Guardrails respected:**
  - No data-model change — feature runs entirely on existing columns (`ShoppingListLine.stock_location_id`, `StockItem.stock_location`, `StockLocation` tree). Explicit per the FU.
  - No spatial-location / stock-map / location-routing reintroduction (charter Removed-features).
  - No new alert type (Surface B was cut anyway; wouldn't have added one).
  - Ephemeral state — `doneGroups` Set + `assignOpen` refs live in the dialog component and reset on every open. No new column, no localStorage, no session storage.
- **Files touched:**
  - `web_app/src/components/dialogs/PutAwayDialog.vue` (new).
  - `web_app/src/pages/ShoppingListDetail.vue` — added the toolbar button (guarded on `detail.status === 'done'`), the `<PutAwayDialog>` element, the `putAwayOpen` ref, the `onPutAwayAssigned` handler (calls the existing `load()` refresh).
- **Deliberate design calls:**
  - **Button appears on the *done* list, not automatically after finish.** User's explicit direction — "button shows on a done list. if clicked, basically shows what you recommended." Keeps the finish flow's success toast + list-archived state as-is; put-away is opt-in.
  - **Inline mini-dialog for location assign** (not the full stock-item edit sheet). The whole point is a fast one-tap sort — opening the heavy detail-page-picker would break the flow. Same walked-tree picker shape as [`CreateStockItemDialog.vue`](web_app/src/components/stock/CreateStockItemDialog.vue:174-186) so the label rendering is consistent.
  - **Groups keyed by `stock_location_id` with `null` = "(No location)".** Matches the domain: unsorted is a real, queryable state, not an error condition.
  - **Unsorted group pinned to the bottom** so a tidy pantry doesn't hide the "still to sort" items above real groups.
  - **Location picker options refreshed on every open** — `watch(modelValue)` calls `locationStore.ensureLoadedAsync()` so a location the user added elsewhere shows up without a page reload.
- **Verification:**
  - `pytest tests/ -q` → **818 passed, 0 failed** (unchanged; feature is frontend-only).
  - `vue-tsc --noEmit` → 4 pre-existing `@capacitor/*` module-not-found errors as baseline; zero new type errors introduced.
  - `eslint` on the two touched files → clean on the new file; one pre-existing `budgetApi` unused-var on `ShoppingListDetail.vue:1307` from commit `14112c1f` (not caused by this FU) — logged as [[FU-503]].
  - R-008 close-gate grep → **0 hits** (no prompt-ID / FU-NNN refs introduced in the new code).
- **Browser-verify:** entry added to `DORA_VERIFY.md` under Shopping lists.
- **Raised:** 2026-07-02 (P6 legacy-plan cross-check).
- **Type (original):** deferred job (Phase 1 loop item, un-started; fell off the map when spatial locations were retired).
- **Cross-ref:** [[FU-503]] (unused `budgetApi` — spotted during this session's lint pass).

## [RESOLVED] FU-462 — Prompt-ID + FU-NNN comment sweep → 887 refs stripped app-wide, R-008 hardened
- **Resolved:** 2026-07-07 — the sweep landed and R-008 in `ENGINEERING_STANDARDS.md` was strengthened with an explicit close-gate grep so this can't rot back in. Full pytest suite still 818/818 after the sweep; vue-tsc unchanged from baseline (the 4 pre-existing `@capacitor/*` errors are unrelated).
- **Scope discovered vs FU's estimate:** FU-462 estimated ~237 prompt-ID comments. Actual count on 2026-07-07 was **887 references** across 202 files — 793 line-start comments + 72 second-pass comments with looser prefix shapes + 22 hand-fixed residuals. The user opted to include **FU-NNN references** in the same sweep (same category — task/PR refs banned by R-008) rather than leave them for a second FU.
- **How the sweep ran (serial file-by-file, three passes):**
  1. Scripted `scratchpad/strip_prefixes.py` (venv Python) with a strict regex handled the well-formed `# ID — substance` / `<!-- ID — substance -->` shapes — 793 transforms across 191 files. Every transform kept the substance (0 lines dropped) — prompt-ID prefixes were pure noise, not standalone WHY.
  2. A looser second-pass regex swept prefixes with extra descriptor words between the ID and the em-dash (`FU-227 follow-up —`, `FU-333 Buckets B + C —`, `P6-01 lifecycle status —`, etc.) — 72 more transforms across 42 files.
  3. 22 hand-fixed residuals — comments with period-terminated prefixes (`# P6-01 Chunk 7.`), pure-noise breadcrumbs (`<!-- FU-044 chip -->`, `// P8-09 memory` section-markers), inline comments (`import uuid  # FU-166: ...`), and a handful of FU-cross-refs that needed prose reworking to preserve the WHY without the FU IDs.
- **Rule shipped alongside** — `docs/01_charter/ENGINEERING_STANDARDS.md` R-008 gained: (a) explicit "a comment must be useful to a reader who has no memory of how the code got here" framing, (b) the explicit close-time grep `rg -nE '(#|//) +(P[0-9]|C-[0-9]|B[0-9]|INV-[0-9]|FU-[0-9])' dora_api/ tests/ web_app/src/`, (c) keep-substance-drop-prefix as the standard rework (e.g. `# P8-05 — buy-verdict defaults on because ...` → `# Buy-verdict defaults on because ...`), (d) an explicit WHAT-comment definition + delete signal, (e) a narrow carve-out for *currently-open* FU refs that name a live workaround (delete when the FU closes).
- **Verification:**
  - `rg -nE "(#|//|<!--)\s+(P[0-9]|C-[0-9]|B[0-9]|INV-[0-9]|FU-[0-9])" dora_api/ tests/ web_app/src/` → **0 hits**.
  - `rg -nE "\S.*(#|//)\s+(P[0-9]|C-[0-9]|B[0-9]|INV-[0-9]|FU-[0-9])" dora_api/ tests/ web_app/src/` (inline) → **0 hits**.
  - `.venv/Scripts/pytest.exe tests/ -q` → **818 passed, 0 failed** (matches pre-sweep baseline).
  - `web_app$ npx vue-tsc --noEmit` → same 4 pre-existing `@capacitor/*` errors as baseline; no new type errors introduced.
- **Carve-outs left in place** — R-0NN / ADR-0NN references (`# R-003 —`, `# ADR-014 —`) survive intentionally; the close-gate grep excludes them.
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (f) sub-part).
- **Type (original):** deferred job / pre-release polish.
- **Cross-ref:** [[FU-424]] Tier-2 item 1 also closed by this sweep (audit-trail updated in the FU-424 open block).

## [RESOLVED] FU-502 — `dependency_injector==4.41.0` pin has no py3.12 wheel → bumped to 4.49.1
- **Resolved:** 2026-07-07 — bumped the pin in `requirements.txt` to `dependency_injector==4.49.1`, which ships a `cp310-abi3` win-amd64 wheel that installs cleanly on py3.12. Full pytest suite green under the new pin (`818 passed, 0 failed`). The `containers.DeclarativeContainer` / `providers.Factory` / `providers.Singleton` surface Dora uses (`dora_api/infrastructure/dependency_container.py`, `service_wiring.py`) is stable across 4.41 → 4.49, so no downstream code needed touching.
- **Raised:** 2026-07-07 (surfaced during FU-466 env bootstrap).
- **Type (original):** finding / dep hygiene.

## [RESOLVED] FU-466 — Wider pytest drift pool (~41 failures) → suite green (818/818)
- **Resolved:** 2026-07-07 — the suite was in a much better state than the FU expected. 5 of the 6 original clusters were **already at zero failures** on current HEAD (fixed by unrelated work between 2026-07-05 and now); the only survivor was 1 flaky test in `test_data_router.py`. Two new drift items had appeared outside the FU's scope (`test_bucket_c_secrets.py` × 6, `test_recipe_is_planned.py` × 1) — resolved in the same pass.
- **Baseline vs. current, per file:**
  | File | FU-466 expected | Actual on HEAD | Notes |
  |---|---:|---:|---|
  | `test_alerts.py` | 16 | 0 | Resolved by earlier work; no action. |
  | `test_alerts_digest.py` | 5 | 0 | Resolved by earlier work; no action. |
  | `test_alerts_push.py` | 4 | 0 | Resolved by earlier work; no action. |
  | `test_household_tz_boundaries.py` | 2 (500s) | 0 | The suspected real-bug 500 was fixed by earlier work; no action. |
  | `test_stock_item_router.py` | 3 | 0 | Resolved by earlier work; no action. |
  | `test_data_router.py` | 11 | 1 | The register-barcode traversal flake (noted in the FU-297 worklog session) — fixed this session. |
  | `test_bucket_c_secrets.py` (new) | — | 6 | New drift from FU-333 Bucket C; fixed this session. |
  | `test_recipe_is_planned.py` (new) | — | 1 | Test assumption stale; fixed this session. |
- **Fixes shipped this session:**
  - `tests/e2e/dora_api/test_bucket_c_secrets.py` — added the session-scoped `_wrapping_key` fixture the module docstring promised but never had. It writes a fresh `DORA_LLM_KEY_ENCRYPTION_KEY` (Fernet-generated) into the env, clears the `key_encryption._fernet` lru_cache, and restores/rewipes on teardown. Without it, every write-a-secret test hit a 400 "wrapping key isn't configured". Root cause: the fixture was documented but not written when FU-333 Bucket C landed 2026-07-06.
  - `tests/e2e/dora_api/test_recipe_is_planned.py::test__recipes__is_planned_true_when_future_unconsumed_entry_exists` — was picking `?limit=1` (the first seeded recipe) which already had other future meal-plan entries, so deleting the one we added never flipped `is_planned` to false. Rewritten to pick a recipe that currently reports `is_planned: false`, guaranteeing the flip-back is observable.
  - `tests/e2e/dora_api/test_data_router.py` — extended `_next_unused_product_id()` with `requires_link=True` (skips forward until the next Product has a `linked_stock_item_id`) and switched the traversal test to use it. Root cause: the traversal test asserts `stock_item_via_product`, which requires a Product with a StockItem linked — the bare round-robin landed on a linked Product only when this file ran in isolation; once earlier tests advanced the counter past the linked seed rows, it fell onto an unlinked Product and returned `product_no_link`. Matches the FU-297 flake symptom.
- **Verification:** `./.venv/Scripts/pytest.exe tests/ -q` → **818 passed, 0 failed** (up from 810/8 at session start).
- **Follow-on drift caught & noted separately:** requirements pin `dependency_injector==4.41.0`, which has no py3.12 wheel and can't build from sdist on Windows without a C toolchain. Installed 4.49.1 (which has a py3.12 win-amd64 wheel) — tests are green under it, but the pin should be bumped. Not in this FU's scope; logging as FU-047-adjacent in the worklog for follow-up.
- **Raised:** 2026-07-05 (surfaced while closing FU-328).
- **Type (original):** finding (pre-existing drift).
- **Why deferred (original):** each cluster belonged to its own feature area and needed per-area investigation to distinguish stale-assertion drift from real regressions. In practice 5 of 6 clusters healed themselves via unrelated feature work before we got here.
- **Cross-ref:** [[FU-328]] (predecessor; resolved 2026-07-05). The register-barcode traversal flake was first noted in the FU-297 close-out worklog entry.

## [RESOLVED] FU-501 — Seasonal-picks table is AU-only → feature removed
- **Resolved:** 2026-07-07 — user's call: cut the feature rather than localise it. `seasonal_picks` was only ever surfaced as one of ~30 assistant tools — no dashboard tile, no shopping-list suggestion, no page pulled from it. Only path was a user asking Dora "what's in season?" in chat. Low value, and the AU-only data was actively misleading for any non-AU install. Cutting is cheaper than either localising, gating on locale, or admin-uploaded tables.
- **What shipped (removal):**
  - `dora_api/features/assistant/tools.py` — removed the `seasonal_picks` tool schema, the `_SEASONAL_AU` table, `_MONTH_NAMES`, `_resolve_month`, the `seasonal_picks` handler, the `_TOOLS` registry entry, and the `_TOOL_NAV` trailing-comment reference.
  - `dora_api/features/assistant/ask_assistant.py` — dropped the `'what's in season right now' → seasonal_picks` example from the tool-selection prompt.
  - `web_app/src/pages/DoraHelpPage.vue` — removed the `seasonal_picks` help entry.
  - `web_app/src/style/icons.ts` — dropped the now-unused `eco: 'mdi-leaf'` token (only site used it).
- **Verified sweep clean:** `rg "seasonal_picks|SEASONAL_AU|_resolve_month|_MONTH_NAMES"` across code returns nothing outside the follow-ups + worklog audit trail.
- **Raised:** 2026-07-06 (FU-043 close-gate).
- **Type (original):** deferred job (locale data).
- **What (original):** hardcoded AU fruit/veg table with an honest but AU-only "seasonal guide" note; non-AU installs saw AU seasons.

## [RESOLVED] FU-465 — Native push notifications (FCM bridge) not wired → parked until SaaS / Phase 4
- **Resolved:** 2026-07-07 — user's call: not worth doing now. VAPID web push already covers the browser + PWA install path (the realistic install story pre-release); native push only matters if the Capacitor APK becomes the primary distribution or Phase 4 commercialisation wants push parity across install types. Adds a Firebase dependency, which cuts against the self-host posture (§7.5) — every self-hoster would have to provision FCM credentials for a channel most won't use. Parked as a Phase 4 resurrection item; noted alongside [[FU-461]] under Phase 4 in `docs/01_charter/RECONCILED_FINISHING_PLAN.md`.
- **Raised:** 2026-07-04 (P8-10 close-gate).
- **Type:** deferred job.
- **What:** VAPID web push works in the browser + PWA install path but Android's WebView doesn't expose the Push / PushManager / Notification APIs, so the Capacitor build's push toggle reads `unsupported`. To make proactive alerts (deal-for-you, run-out, expiry) work on the native app, wire `@capacitor/push-notifications` + Firebase Cloud Messaging on Android (and APNS on iOS when that platform is built). Server-side: a native-endpoint subscription store parallel to the web-push VAPID one, plus a fan-out in `push_sender.py`. Manifest already declares `POST_NOTIFICATIONS`.
- **Why deferred (original):** user picked "keep VAPID web push" at P8-10 scope-lock — smallest surface, avoids a Firebase dependency, matches self-host posture. Native push is only worth the FCM/Firebase cost once there's actual demand.
- **If resurrected:** Firebase project setup + `google-services.json` + backend fan-out is roughly a half-day of work.

## [RESOLVED] FU-448 — P2-05 tail: budget-aware auto-generated shopping lists (optimizer piece)
- **Resolved:** 2026-07-06 — design brief landed at
  [PROPOSAL_BUDGET_AWARE_LISTS.md](docs/04_proposals/PROPOSAL_BUDGET_AWARE_LISTS.md);
  build followed the same session across all six steps in brief §10.
  - **Step 1** — shared `period_headroom(user, on_date, repository)`
    helper in [budget.py](dora_api/features/budget/budget.py); dashboard
    now reads through the same arithmetic (R-003 state-ownership).
  - **Step 2** — `ShoppingListLine.deferred_by_budget` column +
    migration [e5b4d8f2c3a7](dora_api/persistence/migrations/versions/e5b4d8f2c3a7_20260706_shoppinglistline_deferred_by_budget.py);
    `compute_list_totals` skips deferred lines so projected/ticked
    counts stay honest.
  - **Step 3** — 5-tier trim classifier + `POST /shopping-lists/<id>/trim-to-budget`
    with `mode=preview` in [trim_to_budget.py](dora_api/features/shopping_lists/trim_to_budget.py).
    17 classifier tests in [test_trim_to_budget.py](tests/test_trim_to_budget.py)
    covering each tier + the never-cut set + explicit-exclude.
  - **Step 4** — `mode=apply` mutates lines and freezes the reason chip
    on a new `deferred_reason: str | None` column (**deviation** from brief §7.2,
    which said "re-derive on read" — the deviation is documented in-brief and
    in the worklog with a full rationale). Add-back path lands on
    `PATCH /lines/<id>` with `deferred_by_budget=false`.
  - **Step 5** — SPA banner + Deferred-to-fit-budget section on
    [ShoppingListDetail.vue](web_app/src/pages/ShoppingListDetail.vue).
    Three CTAs (Show what would be cut / Trim to fit / Dismiss), a preview
    card with per-line Keep buttons, applied state that scrolls to the
    Deferred section, and an "Add back" per-line action that flips the
    flag off via PATCH.
  - **Step 6** — assistant confirm-action `trim_list_to_budget` in
    [confirm_actions.py](dora_api/features/assistant/confirm_actions.py)
    + tool spec + action-tool registry in [tools.py](dora_api/features/assistant/tools.py).
    Handles "trim my list to budget" / "cut some things to stay under" —
    self-gates when money features are off or no budget is set, and
    returns a specific summary when nothing safe is cuttable.
- **Verified:** classifier tests 17/17; full targeted suite (budget /
  shopping / assistant / trim) 60/60; full suite 811 passed / 7 failed
  (all pre-existing bucket-c + recipe-is-planned; unchanged). `vue-tsc
  --noEmit` exit 0.
- **Raised:** 2026-07-02.
- **Type:** deferred job (design + build). Now: **shipped**.

## [RESOLVED] FU-461 — Account-deletion endpoint (GDPR) → refocused as admin Add / Delete on the users page
- **Resolved:** 2026-07-06 — user's call: GDPR "right to erasure" is only load-bearing if we go SaaS; single-tenant self-host and desktop don't have that obligation. The load-bearing gap on the users page was the missing Add + Delete affordances (Edit + Reset password already shipped). Fixed that instead. If SaaS ever becomes real, this FU can be re-opened as a self-serve `/settings/account` danger-zone build — the admin-side plumbing shipped here (soft-vs-hard call, cascade behaviour, last-admin guard) will inform it, but the surface is different.
- **What shipped:**
  - **Backend — new `dora_api/features/users/create_user_as_admin.py`.** `POST /api/users` (admin-only). Payload: `{ username, email?, is_admin? }`. Uniqueness checks match `register_user.py` (username case-sensitive, email normalised + case-insensitive). Optional email is validated when present. Server mints a 12-char alphanumeric one-time password (same shape as `reset_user_password.py`), hashes it, stores, returns `{ user_id, new_password }` — admin relays out-of-band. `email_verified=false` (parity with self-register); no verification email dispatch (admin implicitly vouches). Audit event `user.created_by_admin`.
  - **Backend — new `dora_api/features/users/delete_user_as_admin.py`.** `DELETE /api/users/<user_id>` (admin-only). Hard-deletes the User row after two guards: (a) refuses to delete the caller (`403 Forbidden`); (b) refuses to delete the last remaining admin (`400 business_rule_violation`, mirroring the `update_user_as_admin` demote guard). FK-cascaded tables drop automatically (`PriceAlert`, `AuthToken`, per-user LLM config); `RecipeCookEvent.cooked_by_user_id` + `ShoppingList.created_by_user_id` are `ON DELETE SET NULL` so household-shared history survives with a null author. `AlertInteraction`, `AlertPreference`, `PushSubscription` — user-scoped tables that carry a plain `user_id` column with no FK constraint — are cleaned up explicitly in the handler. `AuditEvent.actor_user_id` orphans intentionally so the audit trail preserves what happened. Audit event `user.deleted_by_admin`.
  - **Frontend — `userAdminApiService.ts`**: added `createAsync(command) → { user_id, new_password }` and `deleteAsync(userId)`. Documented the one-time-password contract.
  - **Frontend — `UsersAdminSettings.vue`**: new **Add user** button in the page header (primary variant, `person_add` icon). Create dialog collects `username / email / is_admin` with inline field-error surfacing (server 422 errors map to the picker; username-taken / email-taken 400s land inline on the offending field). On success the existing password-shown-once dialog is reused (shared between create + reset — a `resetResultKind` flag switches the copy). New **Delete** button on each row, disabled with tooltip on the current user's row; confirms via `$q.dialog` with a `Delete` (negative) CTA and honest scope copy ("sessions, alert prefs, push subs removed; household-shared things survive"). Also added `person_add: 'mdi-account-plus'` to `web_app/src/style/icons.ts`.
- **Deliberate design calls:**
  - **Hard delete, not soft-delete.** Soft-delete would need a `User.deleted_at` column + every user-scoped query to filter on it; scope grew beyond what the users page needs today. Hard delete + explicit cleanup of the three FK-less tables + intentional audit-event orphaning is a smaller surface. If SaaS obligations arrive later, an added `deleted_at` + retention window is straightforward and doesn't invalidate the current shape.
  - **No self-delete.** The admin must ask another admin (or use a future self-serve account-close endpoint). Prevents accidental lockouts even beyond the last-admin guard.
  - **One-time password, not verification email.** Same shape as the existing `reset_user_password` flow — no dependency on SMTP being configured, admin relays out-of-band. `email_verified=false` on the created user so a subsequent self-serve verify still works if wanted.
- **Files touched:**
  - Backend: `dora_api/features/users/{create_user_as_admin,delete_user_as_admin}.py` (new).
  - Frontend: `web_app/src/services/api/userAdminApiService.ts`; `web_app/src/pages/settings/UsersAdminSettings.vue`; `web_app/src/style/icons.ts`.
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (e) sub-part).
- **Type:** deferred job / feature (compliance) → refocused as admin CRUD.
- **What (original):** No account-deletion path exists (`DELETE /auth/me` etc.). Needed for GDPR "right to erasure" once the product is user-facing. Design questions: soft-delete (retention window) vs hard-delete, cascade rules (personal data vs household-shared data like recipes/products), auth (password reprompt), audit trail, self-service UI location (Settings → Account danger-zone). Recommend a short brief before building.
- **Browser-verify:** appended to `DORA_VERIFY.md` under Settings.

## [RESOLVED] FU-313 — Designed token ladder for graded severity / heatmap palettes
- **Resolved:** 2026-07-06 — shipped the designed token ladder + categorical alert-kind accents + lifecycle event colours, replaced Quasar's numbered palette across every FU-audited site (plus one extra leak swept in the same pass). All values `light-dark()`-driven so a single declaration in `tokens.scss` covers every theme's light + dark variants; no per-theme repetition. Scope shrank one item when the killed location-heatmap system was verified gone (`models/location.ts` FU pointer was stale).
- **What shipped:**
  - **`web_app/src/css/tokens.scss`** — new "Graded severity + alert taxonomy" section with 15 tokens: severity ladder (`--severity-critical` / `-high` / `-medium` / `-low` / `-attention`), 4 categorical alert-kind accents (`--alert-kind-out-of-stock` / `-stocktake-overdue` / `-no-planned-meals` / `-shopping-day`), 1 alert-history state (`--alert-history-read`; snoozed reuses `--severity-medium`), 3 lifecycle accents (`--lifecycle-bought` / `-expiry-changed` / `-cleared`), 1 generic neutral (`--neutral-muted`). Each unique colour uses `light-dark(lightHSL, darkHSL)` — light values keep the current Quasar-palette hue, dark values are lifted ~15% lightness so they stay legible against `--surface-page` in the 5 dark themes.
  - **`web_app/src/css/colours.scss`** — matching `.bg-<name>` + `.text-<name>` utility classes (30 total) so Quasar's `color` prop keeps working as-is (`<q-avatar :color="severity-critical">` generates `bg-severity-critical` → the utility class → the token). Documented that this is the mechanism.
  - **`models/alert.ts colorFor + colorForKind`** — 3-stop severity ladder + 8 kind accents now return token class-suffixes (`severity-critical`, `alert-kind-out-of-stock`, etc.) instead of `red-6` / `orange-7` / `purple-5` etc. Kinds that semantically overlap the severity ladder alias to it (expired ⇒ critical, expiring_soon ⇒ medium, low_stock ⇒ low, essential_low ⇒ high).
  - **`AlertsPage.vue historyChipColor`** — snoozed reuses `severity-medium`, read maps to the new `alert-history-read` token.
  - **`AddToListButton.vue`** — `on_multiple` (`amber-9`) → `severity-attention`.
  - **`StockItemDetailPage.vue` lifecycle timeline (5 sites)** — bought (teal-8) → `lifecycle-bought`; cooked (deep-orange-6) → `severity-high`; expiry set/pushed (orange-8 × 2) → `lifecycle-expiry-changed`; cleared (grey-7) → `lifecycle-cleared`; opened (amber-9) → `severity-attention`.
  - **`DashboardPage.vue nextToCookBadgeColor`** — extra leak swept in-pass: `grey-6` (unlinked ingredients / no ingredients) → `neutral-muted`.
- **Verified sweep clean:** `rg "return 'red-\d|return 'orange-\d|..."` etc. across `web_app/src` returns only breadcrumb comments in the migrated files. Full audit list preserved in the FU history below.
- **Raised:** 2026-06-26 (FU-046 A1 theme-token regression sweep).
- **Type:** deferred job.
- **What:** four surfaces still ride Quasar's numbered palette because they
  encode a *graded* severity / heatmap, not a binary semantic — a single
  `negative` / `warning` doesn't carry the ordinal signal. Sites:
  - `web_app\src\models\alert.ts:144-169` — alert-severity gradient
    (red → orange → amber → deep-orange → purple → teal → indigo).
  - `web_app\src\models\location.ts:41-45` — location-heatmap palette
    (green → teal → amber → orange → red). **Verified stale 2026-07-06 — the whole location-heatmap feature was killed 2026-07-04 stocktake cleanup; palette pointer removed from scope.**
  - `web_app\src\pages\AlertsPage.vue:422-423` — `historyChipColor`
    state ladder: `'orange-7'` (snoozed), `'blue-grey-5'` (read).
  - `web_app\src\components\AddToListButton.vue:247` and
    `web_app\src\pages\StockItemDetailPage.vue:1635` — `'amber-9'`
    "needs attention" tones (inspect; likely the same shape).
- **Why deferred:** swapping these to a single semantic loses ordinal info, and
  picking N specific palette stops is a design decision, not a sweep. They need
  a designed token ladder — e.g. `--severity-1`..`--severity-5` (and a
  `--heatmap-1..N`) — defined in `web_app/src/style/tokens.scss` +
  `themes.scss` so each step is theme-aware in both light and dark, and a tiny
  `severityClass(level)` helper to map an ordinal to the right token-bound
  class.
- **Recommended resolution:** opportunistic — bundle with the next visual
  pass on alerts/heatmaps, or when an A-wave design brief touches severity UI.

## [RESOLVED] FU-284 — settings mobile nav still horizontal-scroll fallback (Phase 5 owes top tab strip) — SHIPPED IN PASSING
- **Resolved:** 2026-07-06 — stale FU; the "real" implementation the FU said Phase 5 owed has already shipped in [SettingsMobileNav.vue](web_app/src/components/settings/SettingsMobileNav.vue). Whoever did it didn't close the FU at the time. Verified in the current code:
  - **Top tab strip** with Account / Kitchen setup / Admin · global tabs, accent-underline active state.
  - **Chip strip below** reveals the selected group's destinations, horizontally-scrolling, current route highlighted.
  - **Sub-groups flattened** on mobile (Recipe taxonomies + System become flat chips — documented design pick in the component).
  - **Route-aware** — the correct tab auto-opens on deep-link and follows navigation.
  - File's own header comment confirms: "Replaces Phase 3's placeholder horizontal-scroll of the desktop sidebar."
- **Raised:** 2026-06-23 (Settings rebuild Phase 3).
- **Type:** deferred job (shipped in a later Phase-3/5 pass, FU not closed at the time).
- **What:** §6.3 was resolved as **top tab strip** but Phase 3 only ships the
  desktop shell + a `flex-direction: row; overflow-x: auto` fallback on
  `<1024px`. The real implementation (three top tabs → chip strip with the
  selected group's sub-items) is owned by Phase 5.
- **Why deferred:** Phase 3 owns desktop visuals only; mobile is a dedicated
  phase that also revisits SettingsSection row collapse + theme grid + the
  DoraSegmented overflow shape.
- **Note for future:** the FU also mentioned Phase-5 revisits of `SettingsSection` row collapse + theme grid + `DoraSegmented` overflow shape. Those may still be open — but they're separate from the mobile-nav concern this FU's title + body describe. If any turn out to be open, they warrant their own FU rather than sitting under FU-284's title.

## [RESOLVED] FU-220 — Repurpose `OnboardingLoop` in Help + consider menu re-ordering — WON'T DO (no change)
- **Resolved:** 2026-07-06 — discussed and closed with no code change. Three separable sub-questions; verdict on each:
  - **Loop diagram in Help.** Nice-to-have, not must-do. Costs promoting `OnboardingLoop.vue` into a shared `components/dora/AppLoopDiagram.vue` + a compact size mode + a HelpPage slot. Value is a mental-model refresh users could otherwise only get by re-running the wizard; low payoff for the churn. Skipped.
  - **Help section order following the loop.** Current order (Stock → Recipes & meals → Shopping & deals → Settings → Dora) already serves the "plan-first" user reasonably; the "shop-first" alternative order is defensible but not obviously better. Reordering costs muscle memory + doc-link churn; skipped.
  - **Main-menu order following the loop.** The FU itself already flagged the tension — cookbook + recipes are nouns, not loop steps. Nav is a random-access index, not a linear tutorial; loop belongs in onboarding/Help as a mental model, not baked into the nav strip. Skipped.
- **Raised:** 2026-06-17 (FU-210 revisit — user direction)
- **Type:** follow-up (UX + IA) — dropped without action.
- **What:** With the cinematic Story still alive (FU-210 revisit kept the hero loop there) and
  the Finish-step recap dropped, the loop is "a nice reminder of how to use the app." Find a
  durable home for it in **Help** so first-run users can revisit it after onboarding without
  rerunning the wizard. Two open IA questions to chew on at the same time:
  (a) **Help section order.** Should the Help sections be ordered in the loop's flow
      (Stock → Plan → List → Shop → Restock → Cook), so newcomers can read the help in the same
      order they'll actually use the app?
  (b) **Main menu order.** Same question for the left-nav: do the buttons map cleanly to the
      loop today? If not, is reordering worth doing — or is the loop's order aspirational
      and the menu's pragmatic (cookbook + recipes are nouns, not steps)?
- **Note for future:** if you revisit, the cheapest partial win is renaming the Help sections to include the loop stage they cover ("Recipes & meals — plan and cook" / "Shopping — list, shop, restock"). No file structure change, teaches the mental model in situ.

## [RESOLVED] FU-188 — Back-in-stock subscriptions tier (deferred from Alerts C-9.5) — WON'T DO
- **Resolved:** 2026-07-06 — user's call: won't do. The FU was speculative — no back-in-stock data source exists (it was gated on the companion / ingestion path producing an availability signal). If a signal ever ships, the producer will design the in-app surface at the same time; keeping a dangling UI-only follow-up here adds noise without adding memory that the future implementer needs.
- **Raised:** 2026-06-15 (Alerts C-9.5 — subscriptions tier)
- **Type:** deferred job (dropped)
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

## [RESOLVED] FU-184 — Reconcile onboarding sell-copy + loop stages against actual app behaviour
- **Resolved:** 2026-07-06 — honesty pass done. Walked every claim in the onboarding sell-copy against the running feature set; two lines didn't cleanly back and were softened, the rest are truthful to what a user with an empty install sees on day 1. User directive: "the logic of the app is pretty settled, minus the verification pass needed" — the foundations FU-184 was waiting on are now in place.
- **What changed in the copy:**
  - **`WelcomeWizard.vue:69`** — welcome-card blurb: "I keep your pantry, **deals** and meals in one place" → "I keep your pantry, **shopping and cooking** in one place". Scraping was divorced back in P8; "deals" was aspirational.
  - **`onboardingContent.ts` PERSONA_PREVIEWS[cooking].centreSell** — "Watching expiry and stock, and **suggesting** what to cook." → "…and **flagging what you can cook now**." Active suggestion requires the opt-in assistant (off by default at the master flag + per-user provider config); the cookable-now filter + Dora Score card ARE always-on day-1 surfaces, and "flagging what you can cook now" maps cleanly onto them.
  - **`onboardingContent.ts` header docstring + inline `PROVISIONAL` markers** — flipped from "⚠️ PROVISIONAL" to "✅ Honesty pass done" so future readers know the reconciliation ran; kept the guidance that any *new* sell copy must be truthful to a day-1 install.
- **What was verified and kept unchanged:**
  - `LOOP_STAGES.stock` — `StockItem.stock_level` + `Location` tree + `expiry_date` all exist. ✓
  - `LOOP_STAGES.plan` — cookable-now filter ([RecipesOverview.vue:84](web_app/src/pages/RecipesOverview.vue:84)) + meal plans + shortfall (per `useMealPlanWeekStatus`) all real. ✓
  - `LOOP_STAGES.list` — auto-add-when-low (per FU-464 fix) + meal-plan-gaps-onto-lists all real. ✓
  - `LOOP_STAGES.shop` + `restock` — `ShoppingListDetail.vue`'s Finish & restock is real (bumps ticked items back to Stocked). ✓
  - `LOOP_STAGES.cook` — [RecipeCookMode.vue](web_app/src/pages/RecipeCookMode.vue) walks structured steps + `recipeStore.cookAsync` → `dora_api/features/recipes/cook_recipe.py` decrements ingredients. ✓
  - `LOOP_CENTRE.sell` "…watching expiry and stock, and answering when you ask" — alerts feed watches expiry + stock; the assistant answers when queried (opt-in gating is honest because the sell says "when you ask", not "unprompted"). ✓
  - `PERSONA_PREVIEWS.spend` "…and what you've been paying" — YourPricesWidget + price observations (FU-213/FU-216) are shipped; gating on the `money_enabled` install flag is the intended "preview of what turning it on gives you" framing. ✓
  - `NARRATIVE_SCENES` (detective work / one loop / brain doing the remembering / you're in control) — figurative, no literal feature claims. ✓
  - Provisional `LOOP_INSIGHT` node was already removed 2026-06-17 in the FU-210 pass — nothing dimmed-and-"coming" remains.
- **Raised:** 2026-06-15 (Onboarding C-5 v3 design)
- **Type:** finding / deferred verification (P3 Honest gate)
- **Browser-verify:** appended to `DORA_VERIFY.md` under Onboarding — the two edited surfaces plus a spot-check of each `LOOP_STAGES.sell` claim playing out end-to-end.

## [RESOLVED] FU-095 — RecipeEditDialog reshaped: stub-creator only, then navigate to detail
- **Resolved:** 2026-07-06 — reassessed and reshaped rather than "add structured steps to the modal". The dialog now creates a **stub** (Name / Cuisine / Category / Collection), closes, and navigates straight to `/cookbook/<new-id>` so the user can flesh out ingredients, steps, image, tools, dietary tags, times, servings, difficulty, time-of-day, and instructions on the detail page (which has better editors for all of them, including the Structured/Freeform/Image `steps_mode` toggle that FU-095 originally worried about). Same shape when editing from the overview — a quick rename/reclassify shortcut; deeper edits happen on the detail page.
- **What shipped:**
  - **`RecipeEditDialog.vue`** — trimmed to 4 fields (Name, Cuisine, Category, Collection). Dialog width dropped 800px → 480px (single column). Primary button reads "Create & open" on create, "Save" on edit. Emit signature split from a generic `saved` into distinct `created(recipeId)` + `updated`.
  - **`recipeStore.createRecipeAsync`** — now returns the created `Recipe` entity so callers can navigate. Existing signature was `Promise<void>`; no other callers relied on that.
  - **`RecipesOverview.vue`** — `onSaved()` split into `onRecipeCreated(recipeId)` (navigates via `router.push('/cookbook/<id>')`) and `onRecipeUpdated()` (list refresh only, same as before). Import + wiring updated.
- **Removed from the modal (all now detail-page-only):** ingredients repeater, image upload, instructions textarea, dietary tags multi-select, tools multi-select, difficulty, servings, prep time, cook time, time of day. Vocab-store hydration for tools + dietary tag catalogue also gone — the trimmed dialog doesn't consume them.
- **Rationale (from the reassessment):** the modal's job is "quick stub so the recipe exists in the list"; anything that reads as "flesh out this recipe" is friction and belongs on the detail page where the specialised editors live. Name + Cuisine + Category keep the stub from getting lost (they're the primary overview filter axes); Collection is the "where does this live" pick users often think of at create-time.
- **Raised:** 2026-06-09 (Cookbook Chunk 6 impl).
- **Type:** follow-up (reshape, not "add structured steps to the modal").
- **Browser-verify:** appended to `DORA_VERIFY.md` under Cookbook — dialog fields present, "Create & open" navigates, edit-from-overview stays on the list.

## [RESOLVED] FU-056 (partial) — Phase 2 ingestion EAN auto-populate
- **Resolved:** 2026-07-06 — closed as clutter rather than "done". The two remaining pieces are both **call sites for plumbing that's already shipped**, gated behind speculative future work (Phase 2 ingestion API + a Products UI redesign). Neither needs a bookmark to be remembered: anyone building either parent feature will naturally add these in passing.
  - **Ingestion auto-populate** — `POST /api/data/barcodes` + the `Barcode` model with per-Product UNIQUE landed 2026-06-28 (slice 1, hybrid model). When Phase 2 ingestion is built, the feed importer should call the endpoint for each EAN/UPC in the catalogue. Grep-anchor for future work: `POST /api/data/barcodes` with `product_id` set.
  - **Product detail EAN field** — same endpoint. Add a single-EAN row on the Product detail page (gated on `features.products`) when the Products UI is next touched. Products is currently a data-presence overlay (PROPOSAL_PRODUCTS_AS_OVERLAY / FU-209), so this piggy-backs on whatever surface work lands there.
- **Raised:** 2026-06-07 (P6-02); slice 1 closed 2026-06-28 (hybrid model)
- **Type:** deferred job (Phase-2 scoped)
- **What's left after the 2026-06-28 hybrid landing:**
  - **Ingestion auto-populate** — when the ingestion API imports a
    retailer catalogue, it should populate `Barcode` from the feed's
    EAN/UPC field automatically so most barcodes resolve without manual
    registration. Just calls `POST /api/data/barcodes` with
    `product_id` set; logic + endpoint already in place. Blocked on the
    ingestion API itself.
  - **Product detail EAN field** — when the Products UI gets touched,
    add a single-EAN row (gated on `features.products`). Uses the same
    endpoint. Per-Product UNIQUE constraint already enforced
    server-side ("one Product = one EAN").
- **Recommended resolution:** Phase 2 ingestion + the Products UI work,
  whichever lands first.

## [RESOLVED] FU-333 — Env-var sprawl: promote operational config to AppSetting + first-run wizard for desktop
- **Resolved:** 2026-07-06 — Buckets C + D shipped end-to-end; the Bucket-B env-var fallbacks were also dropped in the same unit (pre-release, no operators to preserve → also closes [[FU-467]]). Env-var footprint is now 2 bootstrap keys on server self-host (`DORA_SECRET_KEY` + `DORA_LLM_KEY_ENCRYPTION_KEY`), auto-generated on desktop bundles.
- **What shipped in this unit (2026-07-06):**
  - **Bucket C — encrypted secrets on `AppSetting`.** New columns `smtp_password_encrypted` + `vapid_private_key_encrypted` (Fernet ciphertext wrapped by `DORA_LLM_KEY_ENCRYPTION_KEY`, reusing the FU-153 helper). Migration `a3e7d2c9b5f1`. Write handler accepts plaintext on `smtp_password` / `vapid_private_key` and encrypts on save; empty string is the explicit-clear signal; missing-wrapping-key returns a friendly 400. Read DTO returns `<field>_configured: bool` — ciphertext never leaves the row. Resolver decrypts on demand and degrades to empty (dry-run) on rotated-key / undecodable ciphertext with a warning log rather than crashing install-wide. Admin UI: `AdminSystemEmailSettings.vue` + `AdminSystemPushSettings.vue` flipped from disabled-with-hint placeholders to write-only password inputs with Save/Clear.
  - **Bucket D — desktop first-run key bootstrap.** `desktop_app.py._bootstrap_keys()` auto-generates `DORA_SECRET_KEY` (`secrets.token_hex(32)`) and `DORA_LLM_KEY_ENCRYPTION_KEY` (`Fernet.generate_key()`) into `<DATA_DIR>/.secret_key` + `<DATA_DIR>/.llm_key_encryption_key` on first launch; server self-host still sets both explicitly. Same file also gained `_detect_bundled_piper_paths()` + `_seed_desktop_paths()` — the detected `piper_bin` / `piper_bundled_voice_dir` are written into the `AppSetting` row post-init (rather than exported as env), so the strict Bucket-B resolver has no env fallback path to lose.
  - **Bucket-B env fallbacks dropped.** `operational_config.py` is now a straight `AppSetting` projection (no `_pick_str` / `_pick_int` / `_pick_bool`); all 7 read sites (`health_check`, `audit_retention`, `auth_helpers.public_base_url`, `email_sender`, `push_sender`, `tts_synthesize`, `voice_provision`) either delegate to the resolver or fall through to a dry-run/None. `.env.example` deprecated blocks removed. README VAPID section rewritten; the "env-driven path also still works" language is gone.
  - **Tests.** `tests/e2e/dora_api/test_operational_config_resolver.py` had already been rewritten to the strict-AppSetting shape; added `test_bucket_c_secrets.py` covering the encrypt-on-write path (ciphertext-not-plaintext, `_configured` bool never leaks, clear-via-empty-string, partial-update leaves-unchanged, round-trip decrypt, missing wrapping key → 400, rotated wrapping key → dry-run + warning).
- **Files touched in this unit:**
  - Backend: `dora_api/domain/entities/app_setting.py`; `dora_api/persistence/table_mappings.py`; `dora_api/persistence/migrations/versions/a3e7d2c9b5f1_20260706_appsetting_bucket_c_secrets.py` (new); `dora_api/features/app_settings/{operational_config,get_app_settings,update_app_settings}.py`; `dora_api/infrastructure/{email_sender,push_sender,auth_helpers,audit_retention}.py`; `dora_api/features/tts/{tts_synthesize,voice_provision}.py`; `dora_api/features/health/health_check.py`; `desktop_app.py`.
  - Frontend: `web_app/src/services/api/appSettingsApiService.ts`; `web_app/src/pages/settings/{AdminSystemEmailSettings,AdminSystemPushSettings}.vue`.
  - Tests: `tests/e2e/dora_api/test_bucket_c_secrets.py` (new).
  - Docs: `.env.example`; `README.md`; `CHANGELOG.md`; `docs/04_proposals/IMPL_PLAN_ENV_TO_APPSETTING.md`; `docs/01_charter/ENGINEERING_STANDARDS.md` (new ADR-026 + R-030).
- **Explicit non-goals kept:** `DORA_SECRET_KEY` + `DORA_LLM_KEY_ENCRYPTION_KEY` stay in env (bootstrap-only). Per-user `User.llm_*` (FU-153) unchanged. No "set arbitrary env vars from admin UI" surface — that was the anti-pattern this FU existed to avoid.
- **Engineering-standards close-gate:** clean. R-003 (server-owned operational config), R-005 (portable data access; strict AppSetting is Postgres/SQLite-agnostic), R-007 (Buckets C + D + fallback drop bundled per user directive; no scope creep beyond that), all respected. Promoted a new **R-030 / ADR-026** — "Operational config lives on `AppSetting`, not env" — capturing the recurring "where should this config live?" call.
- **Cross-refs:** [[FU-467]] closed in the same unit (below); [[FU-327]] previously shipped the desktop bundle scripts (2026-07-03), which made Bucket D actionable.

## [RESOLVED] FU-467 — Drop the DORA_* env-var fallbacks after FU-333 Bucket B beds in
- **Resolved:** 2026-07-06 — folded into the FU-333 close-out. User directive: "no need for fallbacks, this is prerelease work. no current users of the app." Resolver + 7 read sites are now strict AppSetting projections; `.env.example` and README purged of the deprecated env vars. See the FU-333 resolved entry above for the full file list.
- **Raised:** 2026-07-05 (FU-333 Bucket B merge).
- **Type:** deferred job (deprecation follow-up).
- **What:** FU-333 Bucket B promoted 12 operational env vars to `AppSetting` and shipped four admin System pages, but kept the env vars as *fallbacks* (resolver in `dora_api/features/app_settings/operational_config.py` prefers the row when set, falls back to the env when the row is empty). The fallback lane is a deprecation-window courtesy so existing operators don't lose their SMTP / VAPID / TTS config on the FU-333 upgrade. One release after Bucket B ships, drop the fallback.
- **Cross-ref:** FU-333 (parent).

## [RESOLVED] FU-032 — C-2: allocation count doesn't decrement after planner drop
- **Resolved:** 2026-07-06 — user confirmed in the browser (with batch-cooking
  toggled on via the new onboarding pref) that dropping a recipe onto a future
  day now decrements the "N free" caption on the recipe row in the palette
  ([MealPlanRecipePicker.vue:59](web_app/src/components/MealPlanRecipePicker.vue:59)).
  Root cause never diagnosed — the meal-plan surface was rebuilt between the
  original repro (2026-06-12 against `MealPlansOverview.vue`) and now (the
  picker lives in `MealPlanRecipePicker.vue`, gated behind
  `batch_features_enabled`), and the rebuild quietly cleared whatever
  reactivity / commit-visibility bug was making the old chip stick. Not worth
  archaeology; the bug is gone from the shipping surface.
- **Raised:** 2026-06-06 (C-2 recon); user repro confirmed 2026-06-12
- **Type:** finding (real bug, not yet root-caused)
- **What:** User dragged recipes from the palette onto future days; the chip's
  count next to the recipe name didn't change. Data path read clean end-to-end
  (frontend `onDropOnDay` → PATCH → refetch recipes; backend `_hydrate_unallocated`
  GROUP BY looked correct; chip bound through `storeToRefs`). Three runtime
  suspects — reading the wrong number (`available_meals` vs `unallocated_meals`),
  `storeToRefs` + sorted-array reactivity edge case, `scheduled_for >= today`
  date boundary. None ever verified; picker rebuild made the question moot.

## [RESOLVED] FU-041 — Onboarding "you already have groups/locations" copy on first-run
- **Resolved:** 2026-07-06 — root cause fixed by design change rather than a
  bug hunt. The user pointed out that a genuine first-time setup (fresh
  self-host, or first user in a new SaaS household) will *always* be against an
  empty DB, so onboarding never needed to defensively handle "already have
  groups/locations". The dev seed data was the only thing that could ever fire
  that branch. Split onboarding into two tracks: first user walks
  welcome → admin → seed → first_item → finish; every subsequent user walks
  welcome → finish only (personal prefs; no household-scoped seeding). Dropped
  `has_locations` / `has_groups` / `has_stock_items` from `OnboardingStateDto`
  ([onboarding.py](dora_api/features/onboarding/onboarding.py)) and the
  matching TS type ([onboarding.ts](web_app/src/models/onboarding.ts)); ripped
  the "You already have…" copy branches out of
  [WelcomeWizard.vue](web_app/src/pages/onboarding/WelcomeWizard.vue). Backend
  onboarding tests green (24 passed).
- **Raised:** 2026-06-06 (C-5 brief; feedback L32/L33)
- **Type:** finding (reported defect — didn't reproduce statically)
- **What:** User reported the seed step said "You already have some groups set
  up…" / "You already have locations…" during first-time setup. Static read
  showed the copy was gated on `has_groups` / `has_locations`, which are false
  on a truly-empty DB — so the branch could only ever fire against
  `seed_dev_data()` output. Rather than chase the dev-seed source, we removed
  the defensive branch and the whole seed step from the subsequent-user track
  (where it doesn't belong).

## [RESOLVED] FU-347 — Import template CSV: no UTF-8 BOM — Excel-on-Windows garbles accented example values
- **Resolved:** 2026-07-06 — [`import_spreadsheet.py::download_import_template`](dora_api/features/data/import_spreadsheet.py) now prepends the UTF-8 BOM (`\xef\xbb\xbf`) to the response body before encoding, with an inline comment explaining why (Excel-on-Windows guesses ANSI/CP-1252 without it). The upload-side sniffer (`_parse_csv` around line 127) already strips a leading BOM, so the round-trip stays symmetric — verified by two new tests in [`test_data_router.py`](tests/e2e/dora_api/test_data_router.py): (1) the downloaded template starts with the BOM byte sequence; (2) staging that exact body back through the chunked-upload + inspect stack auto-maps the `name` column cleanly (proving the BOM didn't leak into a `"﻿name"` header). Full pytest 790/1 pre-existing flake — no regressions.
- **Raised:** 2026-07-01 (post-FU-343 self-review).
- **Type:** finding (latent — only bites when non-ASCII enters the example).
- **What:** The templates endpoint in
  [`import_spreadsheet.py`](dora_api/features/data/import_spreadsheet.py)
  emits UTF-8 without a BOM. Today the example row is all ASCII, so
  nothing renders wrong. If a future example includes an accented
  character (`café`, `crème`, a currency symbol, etc.), Excel on
  Windows will show mojibake unless the user opens via Data → From
  Text and picks UTF-8. The inspect endpoint strips a BOM if
  present, so the round-trip works either way — this is a display-
  only concern for the *download*, not the *upload*.
- **Why deferred:** doesn't bite today (all-ASCII example).
- **Recommended resolution:** prepend `﻿` to the CSV body when
  writing (one line change). Trivial. **Recommended resolution
  point:** now if we ever want to add non-ASCII to an example
  (unlikely for stock_items), else pair with FU-349 if we go for
  option (b) — customer-named locations / groups might contain
  accents.

## [RESOLVED] FU-319 — Toast "Added <name> to your pantry" on inline-create from the recipe ingredient picker (F9)
- **Resolved:** 2026-07-06 — the inline-create path in [RecipeDetailPage.vue:1516](web_app/src/pages/RecipeDetailPage.vue) already fired a positive toast (`Created stock item "<name>".`), but the copy leaned on internal jargon and didn't hint that the new item is now a persistent pantry row the user will see on the next Stock overview visit. Reworded to `Added "<name>" to your pantry.` — matches the FU's exact ask; small inline comment names the FU and the persistence expectation for future readers. `vue-tsc` clean. Negative-path toasts (`No stock levels configured…`, `Could not create stock item.`) left as-is: they're technical error surfaces where "stock item" language matches the error being reported, and rewording is out of FU-319's scope.
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F9 — (b)).
- **Type:** UX / cleanup.
- **What:** The recipe ingredient `q-select` exposes a "Create '<typed>'"
  no-option entry that fires a POST to create a brand-new `StockItem`
  inline. The new item survives even if the user cancels the recipe save
  (verified during the audit). Add a small positive toast "Added <name>
  to your pantry" when that inline-create path fires so the user isn't
  surprised by a new tracked item on the next StockOverview visit.
- **Where:** `web_app/src/pages/RecipeDetailPage.vue:395` (the picker)
  and the create-stock-item handler the inline-create eventually calls.
- **Recommended resolution:** opportunistic — fold into the next cookbook /
  recipe-editor touch. 1–2 lines.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F9.

## [RESOLVED] FU-502 — Coverage tests for FU-043 locale/currency backend
- **Resolved:** 2026-07-06 — new [tests/e2e/dora_api/test_locale_currency.py](tests/e2e/dora_api/test_locale_currency.py), **19 cases, all green**. Covers: (1) PATCH `{currency, locale}` round-trip through `GET /health` `locale_policy`, plus a shipping-default check; (2) currency valid table (`USD`, `EUR`, `aud→AUD` case-normalisation) + invalid table (`US`, `USDX`, `US1`, `""`, `" GBP "` — pydantic length gate catches the whitespace-padded case); (3) locale valid table (`en-AU`, `en-US`, `de-DE`, `en-Latn-US`, `zh-Hant-TW`) + invalid table (`en_AU`, `e`, `english`, `en AU`). Explicit skip of the FU's "migration up/down against in-memory sqlite" line item — the migration is exercised on every test run via the conftest's alembic-managed schema (any regression on the columns would take the whole suite down before this file loads), so a dedicated up/down test would only add ceremony. Fixture resets the row to `AUD`/`en-AU` in `try/finally`. Suite delta: 787 passed / 2 pre-existing flakes (both `register_barcode` and `is_planned_true_when_future_unconsumed_entry_exists` fail on clean HEAD with the same order-dependent state pollution — [[FU-466]]).
- **Raised:** 2026-07-06 (FU-043 close-gate).
- **Type:** deferred job (test coverage).
- **What:** the FU-043 backend (AppSetting `currency`/`locale` columns +
  migration `c4e9a2f7b1d3` + `_is_valid_bcp47` validator in
  `update_app_settings.py` + `_locale_policy()` in `health_check.py`) shipped
  without new tests because the Python test venv wasn't available on the box
  the work ran on. The R-013 close-gate wants these under coverage.
- **What to add:**
  - Round-trip test: `PATCH /app-settings {currency:"USD", locale:"en-US"}`
    then `GET /health` reflects `locale_policy.currency == "USD"` and
    `locale_policy.locale == "en-US"`.
  - Validation table: currency must be 3 uppercase alpha; `"US"`, `"USDX"`,
    `"US1"`, `"usd"` (should upper-cased-in), `""` — expected verdicts.
  - Locale validation table: `"en-AU"`, `"en-Latn-US"`, `"zh-Hant-TW"` accept;
    `"en_AU"` (underscore), `"e"`, `"english"`, `"en AU"` (space) reject.
  - Migration up/down against an in-memory sqlite (matches the existing
    `test_operational_config_resolver.py` shape).
- **Recommended resolution:** opportunistic — next time the pytest env is
  reachable (see [[FU-466]] for the broader suite drift).

## [RESOLVED] FU-503 — Ship the targeted `(?)` help chips per `IMPL_PLAN_HELP_CHIPS.md`
- **Resolved:** 2026-07-06 — executed the impl plan end-to-end. Batched by file across ~15 files, 32 audit targets. **Landed net ~20 new chips**: DoraScoreCard (Kitchen health), DashboardPage (Savings captured), ReportsPage (Year-over-year, Meals-worth), AlertsPage (tier concept + per-kind tier override), shared MealPlanWeekStatus (Shortfall — covers chips 8 & 9 in one edit), RecipeDetailPage (Unallocated meals), RecipesOverview (Cookable now), StockOverview (Essential, Auto-add on low, Open/in-use, Needs check), StocktakeRunner (cadence subline, Push 3 days), ShoppingListDetail (Finish & restock), PriceHistoryPage (currently X% above, Your usual), MyProductsPage (Select on-deal), PriceEntry (multipack disclosure). **Folded (extended existing tooltip)**: RecipeCookMode Sous Chef + hands-free mic, ShoppingListDetail Plan-which-day, NotificationsSettings Compact format help, AssistantSettings tool-able-requests description. **Skipped as already covered**: StockItemDetailPage Essential/Auto-add toggles (existing tooltips), PreferencesSettings three toggles (existing SettingsRow `help` attrs). **Skipped as N/A**: Cookable-tonight dashboard label — card was renamed to "Next to cook" (meal-plan-driven) since the audit; the tooltip copy would misdescribe the current card, and chip 11 covers the "cookable now" term in its actual home. `npx vue-tsc --noEmit` → clean. Overlay mechanism, `v-help` directive, `?` toolbar toggle, DoraBot fronting stay parked as someday.
- **Raised:** 2026-07-06 (FU-044 re-scope).
- **Type:** deferred job (execution — audit + copy are already done).
- **What:** User re-scoped FU-044 mid-session (dropped the opt-in help-
  overlay mechanism from `PROPOSAL_HELP_OVERLAY.md`); the narrowed ask is
  to add a targeted `(?)` hover-tooltip using the existing
  `RecipeDetailPage.vue`-style pattern on 32 genuinely-confusing
  controls. The audit ran this session and the tooltip copy is drafted
  in [IMPL_PLAN_HELP_CHIPS.md](docs/04_proposals/IMPL_PLAN_HELP_CHIPS.md).
- **Why deferred:** user asked to save it for the next session so that
  session can go straight from open → edit → commit without re-
  discovering the audit or drafting copy.
- **Recommended resolution:** **now / next session.** Open the impl plan,
  open each file in its "Batch by file" order, apply the chips, `vue-tsc`
  clean, run the close-gate in the impl plan (CHANGELOG bullet, move
  FU-044 → resolved, retire PROPOSAL_HELP_OVERLAY as superseded, add
  DORA_VERIFY entry, worklog + PROJECT_STATE update). Do NOT re-open the
  overlay-mechanism debate — that decision is locked as parked.

## [RESOLVED] FU-044 — Re-scoped 2026-07-06 → shipped via [[FU-503]]
- **Resolved:** 2026-07-06 — original opt-in help-overlay design retired (parked as someday). Executed the narrowed replacement per `IMPL_PLAN_HELP_CHIPS.md`; see [[FU-503]] for the shipped detail. Help/guides page + assistant remain the deep-help fallback; `PROPOSAL_HELP_OVERLAY.md` stays in the tree as 📦 superseded record.
- **Raised:** 2026-06-06 (user-floated idea → `PROPOSAL_HELP_OVERLAY.md`).
- **Type:** deferred job (design retired; execution pending under a new ID).
- **Status update 2026-07-06:** original opt-in help-overlay design
  (`?` toolbar toggle, dismissible per-element overlays, `v-help`
  directive, DoraBot fronting, discoverability nudge) **retired.** User
  narrowed scope mid-session: instead of a whole mechanism, add
  targeted `(?)` hover-tooltip chips on 32 specific confusing controls
  using the existing `RecipeDetailPage.vue`-style pattern. Audit +
  tooltip copy are drafted in
  [IMPL_PLAN_HELP_CHIPS.md](docs/04_proposals/IMPL_PLAN_HELP_CHIPS.md).
  `PROPOSAL_HELP_OVERLAY.md` stays in the tree as the record of the
  parked overlay design (📦 superseded); Help/guides page + assistant
  remain the deep-help fallback.
- **Recommended resolution:** closes at the same time as [[FU-503]] —
  next session opens the impl plan, applies the chips, runs the
  close-gate.

## [RESOLVED] FU-218 — Browser-verify the new admin "API access" page (C-10 / Phase B)
- **Resolved:** 2026-07-06 — pure browser-verify; the a-g checklist already lives in `DORA_VERIFY.md` under **API access page (C-10 Phase B) — origin FU-218** (lines ~1050-1057). Per the CLAUDE.md rule, pure "walk the app" checks don't warrant an open FU. If any check turns up a real bug, a fresh FU gets opened for the fix.
- **Raised:** 2026-06-17 (Phase B build)
- **Type:** verification
- **What:** New Settings page lives at `/settings/admin/api-access`. Confirm in the browser:
  (a) sidebar entry appears under Admin · global (admin only); (b) `New key` opens dialog → reveals
  raw key once → copy works → list shows the new row with `Never used` + `Accepted 0 / Skipped 0
  / Failed 0`; (c) expanding the row shows "Store mappings" panel; (d) push a record from any
  bearer client against an unknown store → reload → the source row shows a pending badge + the
  mapping appears in the panel marked "pending"; (e) merchant picker assigns it → the badge
  clears; (f) disable / enable / rename / revoke all round-trip; (g) revoked key is rejected by
  `/api/ingest` immediately.
- **Recommended resolution:** opportunistic — bundle with the other Phase 0 browser passes.

## [RESOLVED] FU-190 — Ingestion API must honour "no auto-create stores"
- **Resolved:** 2026-07-06 — code + tests landed 2026-06-17 (quarantine queue end-to-end; `test_ingest_batch.py` + `test_ingestion_store_mappings.py`). Only outstanding piece was "confirm the pending → assign flow in the UI", which is a pure browser-verify — that checklist already lives in `DORA_VERIFY.md` under **Ingestion: quarantine queue — origin FU-190** (lines ~1063-1065) and steps (d)/(e) of the FU-218 API access verify cover the same flow. Nothing left as an open FU.
- **Update 2026-06-17 (Phase B build):** implemented as **(b) quarantine queue** end-to-end (the
  proposal's chosen safety net; the "(c) setup mapping step" is naturally produced by the same
  surface — admins map *before* pushing if they want, but unknown names on first sight quarantine
  instead of being rejected, which is friendlier). On every ingest record the producer's
  `merchant` string is resolved via `IngestionStoreMapping`: known → use the linked Merchant;
  unknown → create a quarantined mapping (`merchant_id IS NULL`), skip the record with reason
  `store_not_mapped`, surface as **pending** on the API access page. Stores themselves are
  **never** created by the endpoint. Admin assigns or clears the merchant via
  `PUT /api/ingestion-sources/<id>/store-mappings`. Covered by `test_ingest_batch.py` (quarantine
  + post-mapping roundtrip) + `test_ingestion_store_mappings.py` (CRUD + invalid merchant rejected).

## [RESOLVED] FU-176 — Apply R-014 (reveal-and-disable) app-wide
- **Resolved:** 2026-07-06 — R-014 / ADR-009 retired (superseded by R-029 / ADR-025). User directive: "if a user has disabled something (either personally or for the household) it should not be in their face." The sweep this FU prescribed is now inverted — hide gated entry points outside their own settings screen, not show-disabled. Tracked as **[[FU-500]]**. Standards doc, ADR log, and `IMPL_PLAN_MEAL_PLANS.md` C-2.J all updated same session.
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

## [RESOLVED] FU-085 — Run + verify Cookbook Chunk 2 (tag taxonomy overhaul) in a real env
- **Resolved:** 2026-07-06 — remaining work (items 3, 5, 6, 8, 9) is all pure browser-verify; the checklist already lives in `DORA_VERIFY.md` under **Cookbook Chunk 2 — tag taxonomy — remaining items — origin FU-085** (and the second-round items under `FU-085 fixes — second-round verify items — origin FU-151`). Per the CLAUDE.md rule, pure browser-verify doesn't warrant an open FU. If any of those checks turn up a real bug, a fresh FU gets opened for the fix.
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
    or cuisine queries (item 9 partial fail). RESOLVED 2026-06-12
    (minimal fix shipped). The structural redesign is folded into
    `docs/04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` §2.2.1
    rather than tracked as its own FU.

## [RESOLVED] FU-043 — C-locale international-readiness (Layers A + B shipped)
- **Resolved:** 2026-07-06 — Layers A + B shipped end-to-end. Layer C (full UI
  translation) stays parked as designed.
- **Decisions taken during approval (2026-07-06):**
  1. Currency + locale live **install-wide** on `AppSetting` (no per-user override).
  2. `vue-i18n` **adopt-lite** — kept installed as the future translation seam,
     but the money formatter is a direct `Intl.NumberFormat` wrapper (`useMoney.ts`)
     rather than `n(v, 'currency')`.
  3. **No** `currency` field on C-10 `price_observation` — single-currency-per-
     install assumption stays. If Dora ever goes multi-tenant SaaS with separate
     households sharing an install, this moves onto whatever household row lands
     then; today, one value each is correct.
  4. AU merchant branding **fully removed** from core assistant copy (no
     `AldiLogo`/`IgaLogo` files existed to remove; StoreLogo is generic and
     stays).
- **What shipped:**
  - **Backend:** `AppSetting.currency` + `AppSetting.locale` fields (entity +
    table mapping + migration `c4e9a2f7b1d3`), extended DTO + PATCH endpoint
    with ISO 4217 + BCP-47 validation (server-side lightweight parser).
    `/api/health` now surfaces `locale_policy: { currency, locale }` alongside
    `image_policy` for every logged-in session to consume.
  - **Frontend money formatter (Layer A):** new
    [useMoney.ts](web_app/src/composables/useMoney.ts) — module-level
    reactive `Intl.NumberFormat`-backed formatter; exports `formatMoney(x)`
    (the primary render helper), `currencySymbol` (for `q-input` prefix),
    `currentMoneyPolicy()` (non-Vue callers), `refreshMoneyPolicy()` (settings
    save re-fetch). Every hardcoded `$` prefix (2 sites) and `${{ x.toFixed(2) }}` /
    template-literal `` `$${x.toFixed(2)}` `` (45 sites across 11 files) now
    routes through it — Dashboard, Reports, ShoppingListDetail, PriceHistory,
    StockItemDetail, RecipeDetail, YourPricesWidget, PriceHistoryChart,
    PriceHistoryBottomSheet, ProductChip, QuickAddSheet, SubscriptionsPanel,
    MyProductsPage, MoneySettings, PriceEntry.
  - **Frontend voice locale (Layer B):** `useVoiceInput.ts` derives its BCP-47
    tag from the install locale (fallback: browser locale, then `en-AU`), no
    longer hardcoded `en-AU`.
  - **Backend assistant copy (Layer B):** `app_knowledge.py` reworded so the
    APP_OVERVIEW doesn't name Australian retailers; `tools.py` two tool
    descriptions genericised (`search_products`, `set_primary_list`). The
    seasonal-picks tool + note remain factually AU-specific — its underlying
    table is AU-curated. Left as-is with the "Australian seasonal guide"
    disclaimer; logged as [[FU-501]] for later per-locale data.
  - **Settings UI:** new
    [AdminSystemLocaleSettings.vue](web_app/src/pages/settings/AdminSystemLocaleSettings.vue)
    at `/settings/admin/system/locale` — currency + locale inputs with a live
    preview + "Use this device" locale-detect, wired via the same
    `AppSettingsApiService.updateAsync({currency,locale})` pattern the timezone
    page uses. Sits alongside Timezone in the System nav.
  - **vue-i18n:** unchanged mechanically; a comment in `boot/i18n.ts` records
    the adopt-lite decision so a future session knows the app doesn't route
    through `n(v, 'currency')`.
- **Coverage tests not written:** the test venv isn't available on this box; the
  new resolver + endpoint validation are logged as [[FU-502]] for a coverage
  pass when the runner is next reachable.
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

---

## [RESOLVED] FU-003 — Other light themes' `--text-muted` contrast nudge
- **Resolved:** 2026-07-06 — user's call was to **undo the Pesto bump** rather than
  propagate it to the other light themes. Reverted `[data-theme="pesto"] --text-muted`
  in `web_app/src/css/themes.scss:66` from `hsl(168 10% 42%)` back to the pre-A1b
  value `hsl(168 8% 50%)`. All light themes (Pesto, Lemon Tart, Blueberry, Cherry
  Cola light, Sourdough light) are now on the same ~50% muted-lightness baseline —
  the whole-app polish pass ([[FU-002]]) will re-judge muted contrast holistically
  from parity, not from a Pesto-only outlier. Pesto Dark was not touched (its 66% was
  independently tuned for dark-page pop, not part of the A1b light-theme bump).
- **Raised:** 2026-06-04 (A1b)
- **Type:** follow-up
- **What:** only the Pesto family got the `--text-muted` 50→42 lightness bump.
  Other light themes (Lemon Tart, Blueberry, Cherry Cola light, Sourdough light)
  may want the same for AA contrast.
- **Why deferred:** wanted to eyeball Pesto first before touching the whole family.
- **Recommended resolution:** later during a dedicated A1b contrast pass, after the
  user has eyeballed the themes.

---

## [RESOLVED] FU-328 — Four pre-existing pytest failures (data_router / household_tz / product / recipe_is_planned)
- **Resolved:** 2026-07-05 — all four cleared. Suite delta on this branch: 44→41 failed, 711→714 passed (net −3, matching the three tests I edited; the fourth self-healed).
  - `test_recipe_is_planned::test__recipes__is_planned_true_when_future_unconsumed_entry_exists` — self-healed since 2026-06-29 (passes on clean HEAD).
  - `test_product_router::test__update_product__PriceNowAtZeroBoundary__IsBadRequest` — FU-099 error-shape drift; the assertion still expected a flat raw string. Fixed by using the `validation_err("greater_than", "Input should be greater than 0")` helper (the pattern every neighbouring test in the file already uses).
  - `test_household_tz_boundaries::test__dashboard__upcoming_window_anchored_on_household_today` — targeting endpoints that don't exist (`POST /meal-plans/<id>/entries`, `GET /dashboard`). Rewrote the test to (a) embed the entry via `POST /meal-plans` (the real composition path), (b) read `GET /dashboard/summary` → `meal_plan.upcoming_entries` (the real DTO shape), (c) tear down the created plan in a `finally`.
  - `test_data_router::test__chunked_upload__chunk_offset_mismatch__is_400` — same FU-099 error-shape drift; added `domain_err` import and updated the assertion to `domain_err("0")`.
- **Follow-on discovery:** the full-suite failure count on clean HEAD is now **44** (not 4), reflecting drift accumulated since FU-328 was raised (suite grew from 540 → 755 tests). Logged as a separate FU for opportunistic per-area cleanup — this FU is closed strictly on its four named items.
- **Raised:** 2026-06-29 (FU-288 resolution — full-suite run uncovered a
  *different* set of failures than FU-288 originally named).
- **Type:** finding (pre-existing drift; confirmed on a clean stash).
- **What:** `./.venv/bin/pytest tests/` shows **4 failures, all pre-existing**,
  unrelated to the three profile-picture tests FU-288 named (those all pass
  now). Confirmed via `git stash` — they fail on clean HEAD too:
  - `tests/e2e/dora_api/test_data_router.py::test__chunked_upload__chunk_offset_mismatch__is_400`
  - `tests/e2e/dora_api/test_household_tz_boundaries.py::test__dashboard__upcoming_window_anchored_on_household_today`
  - `tests/e2e/dora_api/test_product_router.py::test__update_product__PriceNowAtZeroBoundary__IsBadRequest`
  - `tests/e2e/dora_api/test_recipe_is_planned.py::test__recipes__is_planned_true_when_future_unconsumed_entry_exists`
  Suite totals: 4 failed, 536 passed.
- **Why deferred:** out of scope of the FU-288 / FU-285 / FU-289 work unit
  (R-007); each failure belongs to its own feature area (data import,
  household-tz boundaries, product validation, planner-derived `is_planned`).
- **Recommended resolution:** opportunistic per area — when next touching
  data-import / dashboard upcoming-window / product validation / `is_planned`
  derivation, run that test first, see what it expects, and either fix the
  code or update the assertion. Don't bundle as one "fix the 4" job — each
  failure is its own story.

## [RESOLVED] FU-302 — Dora Score reassessment: waste-as-pillar weight
- **Resolved:** 2026-07-05 — reviewed with the user; no change. The current Score model already keeps waste as its own equal-weight pillar over a rolling 30-day window (`DORA_SCORE_WINDOW_DAYS=30`, `_score_waste` in `dora_api/domain/dora_score.py`), with the 7-day-lagged trend arrow tracking week-over-week movement. That matches the intent — waste stays a distinct, time-based signal separate from freshness (freshness = snapshot of expiry-tracked items past date now; waste = 30d event count). C-waste's UI de-emphasis doesn't require Score reweighting; missing components already excluded per P3. Closed without code changes.
- **Raised:** 2026-06-24 (C-waste design — `PROPOSAL_WASTE_MINIMISATION.md`).
- **Type:** finding
- **What:** `DASHY_DORA_CHAMPION_PLAN.md` §§334, 346, 444–447 treat waste as one of four Dora Score pillars ("low waste, on-budget, fresh, few run-outs"). The C-waste design deliberately de-emphasises waste as a UI feature — the `/waste` page is deleted, the capture flow shrinks to a single row dropdown action with no money/note capture, no Reports card. The *signal* is preserved (events still logged + queryable) so the Score can read it. But the de-emphasis is a quiet vote that the Score model itself may want re-weighting — perhaps waste shrinks to a smaller pillar, or merges with another (e.g. "fresh + low-waste" → one freshness pillar). This is a **charter-level** decision, not a UI cleanup, and was explicitly out of scope for C-waste.
- **Why deferred:** the Score isn't designed yet (Phase 3 / champion phase); doing the weighting now would be speculative. Better to revisit when the Score model is being built and the full pillar picture is on the table.
- **Recommended resolution:** later during pre-Phase 3 (when the Dora Score model is actually being designed; the reassessment is an input to that design, not its own deliverable).

## [RESOLVED] FU-295 — Confirm the Alerts page (D5) no longer 404s
- **Resolved:** 2026-07-05 — user verified in the running app that the `/alerts` route loads (no 404). Feedback D5 confirmed fixed; the static read of `routes.ts` → `pages/AlertsPage.vue` matched actual behaviour.
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 3).
- **Type:** finding (reported defect, static-only verification).
- **What:** feedback D5 reported "Alerts navigation is broken (goes to 404)". A
  static read shows the `/alerts` route IS registered (`routes.ts` →
  `pages/AlertsPage.vue`, the C-9 control surface), so it appears fixed — but a
  static read is not proof.
- **Recommended resolution:** the verify itself is tracked in `DORA_VERIFY.md`
  under "Dashboard rebuild" (it's the same click that exercises the Phase-3
  alert card → `/alerts` link). Close this FU once that pass is green.

## [RESOLVED] FU-444 — `test__all_axes_thin__collapses_to_single_not_enough_history` fails on pre-existing composer behaviour (duplicate of FU-455)
- **Resolved:** 2026-07-04 — **duplicate of FU-455**. Both FUs described the same failing pytest (`tests/test_buy_verdict.py::test__all_axes_thin__collapses_to_single_not_enough_history`); FU-444 was raised 2026-07-02 during the Sufficient-band axe close-gate, FU-455 was raised 2026-07-04 during Stocktake Chunk 1's close-gate — same failure, second FU. FU-455's resolution literally implemented FU-444's Option 2 recommendation ("widen the fixture to actually trigger three thin axes — `purchases_12mo=1, waste_events_12mo=1` so the waste axis returns `thin_data` per the `< _MIN_PURCHASES_FOR_WASTE_RATE` branch"). Full pytest suite 303/303 green since. Consolidated for the audit trail so a future reader doesn't see two open FUs for one failure.
- **Raised:** 2026-07-02 (surfaced while running `pytest` for the Sufficient-band axe close-gate).
- **Type:** finding (pre-existing, not introduced this session).
- **What:** `tests/test_buy_verdict.py::test__all_axes_thin__collapses_to_single_not_enough_history` fails on `main`-state because its inputs only produced two thin axes, not three — the composer's `len(thin) == 3` collapse correctly didn't fire.
- **Why deferred:** unrelated to the Sufficient-band axe; pre-existed on `main`.

## [RESOLVED] FU-421 — "Remind me to use this" on opened items (use-by reminder)
- **Resolved:** 2026-07-04 — closed as **already satisfied by the existing expiry surface**, no code change needed. Read + confirmed:
  - **Item detail** ([`StockItemDetailPage.vue:269-298`](web_app/src/pages/StockItemDetailPage.vue)) — Expiry row exposes `+1d` / `+7d` / `+14d` shift chips, a **Set** date-picker, and a **Clear** (×) button.
  - **Stock row** ([`StockItemRow.vue:191-231`](web_app/src/components/stock/StockItemRow.vue)) — expiry button opens a date picker when unset, or a `Push +1d / +7d / +14d` / `Clear` menu when set.
  - **Tooltip on the Open toggle** ([`StockItemDetailPage.vue:312-319`](web_app/src/pages/StockItemDetailPage.vue)) already documents this exact workflow verbatim: *"Opening an item doesn't change its expiry date — but for perishables it's the cue to set or shorten one. Use the expiry row above to do that."* — someone deliberately built the affordance and wrote the in-product hint for it.
  - **Free alerts** — the existing `expired` + `expiring_soon` alert kinds fire off `expiry_date` regardless of whether the date was manufacturer-printed or user-set from an open event. Same rails as everything else.
  - **Free auto-clear on waste** — `StockItemRow.onMarkAsWasted` and the bulk-waste flow (Stock Overview) already clear `expiry_date` when the item is logged wasted.
- **Design decision on reuse vs new field:** user asked "why not just use the expiry feature?" — the honest answer is that a user-set "use by 2 months from open" IS an expiry, semantically identical to a manufacturer-printed one (both mean "use it or bin it"). Reusing avoids a duplicate field (`use_by_reminder_at`), a duplicate alert kind (`use_by_reminder`), duplicate Settings preferences, and the six-plus surfaces that would need to consume the parallel data. The only real gap is *ergonomics for month-scale opened-life* — the shift chips top out at `+14d`, so "remind me in 2 months" hits the raw date picker. Considered adding `+1m` / `+3m` chips (Option B); user explicitly picked "close as-is" (Option A) since he hasn't hit the pain in real use. If it becomes annoying, a ~10-line SPA change extends the chips.
- **Raised:** 2026-07-01 (original-spec sweep).
- **Type:** deferred job (dropped intent).
- **What:** Original spec asked for a "remind me" affordance when an item is opened (e.g. "I opened this Thai curry paste, remind me in 2 months"). Distinct from expiry (expiry is intrinsic to the product; this is user-set per-open event). Not modelled today — `is_open` + `opened_at` exist, no reminder field/UI.
- **Why deferred:** never made it into the finishing plan.
- **Recommended resolution:** when P8-07 Zero-Input Pantry or the alerts refactor next opens — decide keep/cut; if keep, a `use_by_reminder_at` field on `StockItem` + one alert type + a modal on the "opened" toggle covers it.

## [RESOLVED] FU-458 — Rate-limit assistant endpoints
- **Resolved:** 2026-07-04 — extended the existing `rate_limit` / `rate_limit_remaining_seconds` helpers in [`infrastructure/auth_helpers.py`](dora_api/infrastructure/auth_helpers.py) to accept an optional `subject` argument that overrides the per-IP bucket key with a per-identity one (typically `str(session.user_id)`). Backward-compat: omitting the arg keeps the historical per-IP behaviour for pre-auth callers (login/register/verify). Wired the assistant surface: **`/assistant/ask`** at 20/min (LLM round-trip, most expensive), **`/assistant/act`** at 60/min, **`/assistant/confirm`** at 60/min — all bucketed by authenticated `session.user_id`, falling back to IP when unauthenticated (which is defense-in-depth even though ambient auth guards should block those calls). RFC 6585 §4 shaped 429 with `Retry-After`, matching the auth-surface `email_flows._too_many_requests` pattern. Also **fixed a doc/code drift on `/assistant/probe`** — its rate-limit call was per-IP but the code comment claimed per-user; now that the helper supports it, the code matches the comment (per-user for real). New pytest coverage: [`tests/test_rate_limit_subject.py`](tests/test_rate_limit_subject.py) — 5/5 green on subject isolation, scope isolation, retry-after math, IP fallback, and empty-string subject boundary. Full pytest suite **303/303 green** (was 298 → 5 new tests). No SPA change — 429 is a pre-existing shape the axios interceptor already knows how to render.
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (e) sub-part).
- **Type:** deferred job / hardening.
- **What:** `POST /assistant/ask` + `/assistant/act` + `/assistant/confirm` had no rate limit. In multi-tenant (Phase 4) an authenticated user could burn upstream LLM tokens by looping requests. The FU asked for per-user (not per-IP) bucketing because households share IPs.
- **Why deferred:** Tier-2 hardening; Phase 3 is single-user personal-use so the risk was theoretical.
- **Recommended resolution:** before Phase 4 commercialization — user pulled forward.

## [RESOLVED] FU-463 — Sibling `text() + str(uuid) IN :ids` queries silently returning zero rows on SQLite
- **Resolved:** 2026-07-04 — same rewrite as FU-171 (drop raw `text()`, use ORM `select()` with SQLAlchemy Core so UUIDType adapts bindings on both engines). Two sites fixed: [`get_stock_items.py::_hydrate_linked_product_count`](dora_api/features/stock_items/get_stock_items.py) — the "linked products" count on every stock-item DTO was 0 on SQLite regardless of the link table's actual contents; and [`get_recipes.py::_compute_estimated_cost`](dora_api/features/recipes/get_recipes.py) — the three-table join (`StockItemProduct → Product → ProductOffer`) that computes a recipe's cost estimate. Under the old raw-SQL both queries silently returned zero rows on SQLite (`WHERE stock_item_id IN :ids` bind never matched BINARY(16) storage), so `linked_product_count=0` on every DTO and `estimated_cost=None` on every recipe with priced ingredients — both fell back to their empty-state renderings without any error. Postgres deployments were never affected. Ran the rewritten queries against the actual SQLite `dora.test.db` via a REPL under `app.app_context()`: both compile + execute cleanly. Full pytest suite **298/298 green**. `project_sqlite_uuid_text_binding` memory now covers three surfaces (this + FU-171 recipes/meal-plans + the original `get_stock_items._hydrate_has_image`).
- **Raised:** 2026-07-03 (spotted during FU-171 resolution).
- **Type:** finding (latent bug on SQLite deployments; harmless on Postgres).
- **What:** Two remaining call sites used the same broken shape that FU-171 fixed. Under the old raw-SQL bind + string-uuid IN clause, both silently returned zero rows on SQLite — `linked_product_count` was 0 on every stock-item DTO, and `estimated_cost` was `None` on every recipe.
- **Why deferred:** neither was on the surface the user originally reported (FU-171 was strictly the recipe-image toggle); rewrites were less mechanical than the recipe-image one (aggregations across a link table).
- **Recommended resolution:** now-ish — same pattern as FU-171's fix.

## [RESOLVED] FU-464 — Auto-add-when-low threshold is stale after the 3-band collapse (`>= 2` = Out only)
- **Resolved:** 2026-07-04 — replaced the two hardcoded `_NewLevelSeq >= 2` / `_PreviousLevelSeq < 2` sequence-literal comparisons in [`update_stock_item.py`](dora_api/features/stock_items/update_stock_item.py) with the semantic predicate `needs_restock(level)` from `stock_status.py` (R-003 single authority). Also refactored the previous-level capture to keep the loaded `StockLevel` object around (rather than just its sequence) so both the transition check and the level-change history append read the same source. Before: `>= 2` was Out-only under the new 3-band sequences (post-`a1c7d9e42be0`) — Low transitions on `auto_add_when_low`-flagged items silently dropped. After: `needs_restock` returns True for both Low (seq=1) and Out (seq=2) and False for Stocked (0) + None, so the hook fires on the correct Stocked→Low, Stocked→Out, and None→Low/Out transitions (verified via sanity table). `_NewLevelSeq` local dropped (no other reader); `_PreviousLevelSeq` kept for the neighbouring consumption-event branch that still needs the raw int. Full pytest suite **298/298 green**. Fix will be reverified in-browser via the existing auto-add DORA_VERIFY block.
- **Raised:** 2026-07-03 (spotted while wiring P8-07 consumption events into `update_stock_item.py`).
- **Type:** finding (real bug — behaviour drift).
- **What:** [`update_stock_item.py`](dora_api/features/stock_items/update_stock_item.py) auto-add hook fired on `_NewLevelSeq >= 2` with a stale comment `# 2 = Low, 3 = Out (see seed)`. That comment reflected the OLD 4-band sequences (0 Stocked / 1 Sufficient / 2 Low / 3 Out). After the 2026-07-02 Sufficient-band collapse the canonical sequences are **0 Stocked / 1 Low / 2 Out**. So `>= 2` now meant **Out only** — an item transitioning to **Low** no longer auto-added, even with `auto_add_when_low` set. The intent was low-or-out (`needs_restock`, seq ≥ 1).
- **Why not fixed here:** was out of P8-07 scope (R-007); touched the auto-add behaviour which has its own DORA_VERIFY coverage.
- **Recommended resolution:** now/opportunistic — replace the `>= 2` + `< 2` literals with `needs_restock(...)` from `stock_status.py`.

## [RESOLVED] FU-455 — Pre-existing test failure in `test_buy_verdict.py` (all-thin-axes case returns 0 reasons)
- **Resolved:** 2026-07-04 — the test was wrong, not the composer. The `waste_events_12mo=0, purchases_12mo=1` inputs hit the composer's `no_waste_history` branch (a *positive signal* meaning "you've never wasted this"), NOT `thin_data`. So only 2 of 3 axes were actually thin and the `len(thin) == 3` collapse in `compose_verdict` correctly didn't fire. The `no_waste_history` vs `thin_data` distinction is semantically meaningful — one is "we know something", the other is "we don't have enough data" — and merging them would break the verdict's ability to nudge toward buying when the user has a clean waste record. Fix: updated the test's waste inputs to `waste_events_12mo=1, purchases_12mo=1` (waste seen, but too few purchases to compute a rate) so the waste axis genuinely returns `thin_data`. Docstring gained a "waste-axis nuance" note explaining why `waste_events_12mo=0` would miss the collapse. Full pytest suite now **298/298 green** (was 297/298 since Chunk 1's ship). One-line change to the composer would have been wrong — composer's classification was correct all along.
- **Raised:** 2026-07-04 (Stocktake Chunk 1 close-gate — surfaced by running the full test suite after the change).
- **Type:** bug (not a stocktake regression).
- **What:** `tests/test_buy_verdict.py::test__all_axes_thin__collapses_to_single_not_enough_history` failed on main-state (confirmed by `git stash` isolation). The test built a "min viable" input for the buy-verdict composer and asserted `len(verdict.reasons) == 1` (a single "not enough history yet" reason). The composer was returning `reasons=[]` for that shape, which turned out to be correct: the test's inputs only produced two thin axes, not three.
- **Why deferred:** cleanly out of scope for Chunk 1 (backend engine for stocktake). Surfaced only because the chunk's close-gate ran the full pytest suite.
- **Recommended resolution:** now that this session touched the failure, fold the fix in.

## [RESOLVED] FU-226 — Assess the new stocktake-queue rules (history vs. current vs. desired)
- **Resolved:** 2026-07-04 — assessed with the user across four question-waves; every decision locked into `docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md` (status: designed-not-built, decisions-locked). Final design: (1) **Gate** simplified to one question — "do you actually keep this item?" (in stock / opened / adjusted-in-60d / on-a-list-in-60d). Essential + auto-add DROPPED as gate signals; the two history signals gain a **60-day window**. (2) **Essential** = cadence-only, one band faster; the *sole* per-item lever — **no per-item Weekly/Fortnightly/Monthly picker ever**. (3) **Cadence** = Weekly/Fortnightly/Monthly bands; global default **Fortnightly** + **Auto** self-tuning **ON by default** (trailing-90d avg gap between level changes: ≤10d→Weekly, 11–24d→Fortnightly, ≥25d→Monthly; Low/Out in 14d bumps faster). (4) **Never-checked → grace period** (`created_at` baseline, `9999` sentinel dropped). (5) **Verbs:** two primary (Still correct | Change level — the latter shows current level+colour+"(change)") + three secondary (Skip session-only / Push 3-day snooze / Mute w/ confirm). Out-of-stock button + keyboard shortcuts + per-item Add-to-list all dropped; add-to-list becomes a **completion-screen batch**. (6) **No landing page** — straight into the runner + a `(?)` help affordance. (7) New **"Stocktake" settings block** (default cadence + Auto toggle). (8) **Expiry & Waste CUT from stocktake** (retires the 2026-07-02 extension — Overview expiring-filter + log-waste-there is the single surface). (9) Stock Overview gets a **pulsing outline** on overdue rows' stock-level button + a "Needs check" quick-filter. **Merged [[FU-430]]** (the redesign-brief ask). Only impl-level call left: drop-vs-dead-column `days_until_stocktake_alert`. Build is future phase work, not this FU.
- **Raised:** 2026-06-19 (Stock Overview bulk + stocktake feedback round)
- **Type:** finding (UX policy — needs user judgement)
- **What:** Round-18 swapped the stocktake queue's filter from "anything overdue
  surfaces" to a stricter engagement-based rule. The user wants this written down
  so they can sit with it and decide whether it's right, looser, or stricter
  before any more code lands.

### What it WAS (pre-round-18)

  In `dora_api/features/stocktake/stocktake.py::get_stocktake_queue`:

  An item entered the queue when **both** were true:
  1. `stocktake_alerts_are_enabled == True` (per-item manual opt-out).
  2. `_compute_overdue(item) > 0`, where overdue is:
     - **`9999`** if `last_checked_at is None` (never-checked sentinel — items
       always surfaced as "maximally overdue").
     - Otherwise: `max(0, days_since_last_check − days_until_stocktake_alert)`.
       The per-item cadence is `days_until_stocktake_alert` (default 14, set on
       create).

  Ordering: most-overdue first → oldest `last_checked_at` → name.

  Pain point the user reported: a freshly-created stub item ("nachos I don't
  really keep in stock") immediately landed at the top of the queue because
  it'd never been checked → 9999 overdue. Dora pestered the user about every
  item they'd ever typed into the system, including items they'd long ago
  decided not to manage.

### What it IS NOW (round-18, 2026-06-19)

  Same two existing gates (per-item opt-out + `overdue > 0`), PLUS a new
  **engagement gate** that runs before either. An item must show ≥1 sign the
  user actually manages it:

  1. `is_flagged` (Essential) **or** `auto_add_when_low` — explicit "this
     matters" flags.
  2. Currently in stock — `stock_level.sequence < OUT_OF_STOCK_SEQUENCE`.
  3. Ever opened — `opened_on is not None`.
  4. Level was changed at least once — any `StockLevelChange` row exists for
     this stock_item_id. (The history table only grows when a level actually
     moves, so this distinguishes "never touched" from "touched once and back
     to default".)
  5. On any shopping list, ever — any `ShoppingListLine` row references this
     stock_item_id, regardless of list status (active or done).

  Signals 4 + 5 are bulk-fetched in one DISTINCT query each, so the queue
  endpoint stays cheap on big pantries.

  The `9999` never-checked sentinel is **kept**. The intent: engaged-but-
  never-checked items (essential / on a list / in-stock / etc.) still surface
  first; the engagement gate just stops the queue from drowning in unengaged
  stubs.

### Things to weigh when assessing

  - **False negatives** — items the user DOES care about but that fail every
    engagement signal. Likeliest case: an item that's normally well-stocked
    but is genuinely depleted right now, and the user never opened it (not a
    sealed product they "open"), never flagged it essential, never put it on
    a list, never moved the level. Possibly: a recurring seasonal item the
    user wants to be reminded to restock but hasn't engaged with recently.
  - **False positives** — items that pass engagement but shouldn't really
    nag. Likeliest case: items that were on ONE shopping list once five
    months ago and have been ignored since. Signal 5 ("ever on a list") is
    intentionally permissive — should it be "on a recent list" instead?
    (e.g. last 60 days.) Trade-off: DB needs a join on list lifecycle
    timestamps; not free.
  - **Tuning knobs to consider**:
    - Time-bound the "on a list" signal (last N days).
    - Time-bound "level was changed" similarly (only count level changes in
      the last N days as engagement).
    - Add a "snooze for N days" affordance on the queue row so the user can
      mute individual items without flipping the binary `stocktake_alerts_
      are_enabled` flag.
    - Replace the global cadence with a smarter default (e.g. shorter for
      essentials, longer for "in-stock but lots of headroom" items).
    - Promote `stocktake_alerts_are_enabled` from "manual opt-out only" to
      "auto-set false when engagement decays past N days" so the data
      self-cleans.
  - **Candidate rule 4 — expiry as an engagement signal** (added
    2026-07-02, user feedback): the current engagement filter treats
    "opened" as a signal but does NOT treat "near-expiry" as one. Yet
    stocktake is exactly the moment the user walks the pantry and
    reviews expiring items, and near-expiry is arguably a stronger
    version of "in play" — a countdown ends in the discard bin.
    Currently near-expiry items surface via a **separate** flow
    ([`waste/rescue`](dora_api/features/waste/waste.py) endpoint + the
    Dashboard's "Needs your attention" card), so users have to check
    two surfaces for the same walk. Proposal to weigh: add "`expiry_date`
    within N days" (default 7, reusing `EXPIRING_SOON_WINDOW_DAYS`) as
    a sixth engagement signal.
    * **Frequency mismatch worth thinking through:** item-cadence is
      typically weekly-plus, but expiry-driven review wants **daily**
      surfacing. Two options:
      * (a) one queue, but expiring items get a synthetic-overdue score
        that pins them to the top regardless of `last_checked_at`. Simple;
        risks noise on a pantry with lots of dated items.
      * (b) two queue "modes" surfaced from the same page ("Overdue"
        cadence-driven + "Expiring" daily-driven, mode toggle on the
        header). Same list UI, filtered by mode. Cleaner UX; small
        extra API surface (`GET /stocktake/queue?mode=expiring`).
    * **Queue row shape:** whichever way, the queue row needs an
      `entry_reason` so the UI can render *why* it surfaced ("expiring
      in 2 days" vs "10 days overdue for a check"). The user shouldn't
      have to guess.
    * **R-003 check:** `waste/rescue` and the Dashboard expiry card
      stay — they're glance-surfaces (Dashboard) and cook-what-you-can
      rescue (rescue recipes matched to expiring ingredients).
      Stocktake would be the walk-the-pantry-and-decide surface. Shared
      SoT lives on a server-side `get_expiring_items` helper; UI cards
      read from it rather than duplicating expiry logic. Not a
      collision — three verbs (glance / cook / decide) on the same
      underlying data.
  - **Candidate verb 3 — waste as a stocktake resolution + bulk waste
    API** (added 2026-07-02, user feedback): today stocktake has two
    resolutions per item — Check (keep, bumps `last_checked_at`) and
    Set level (adjust). There's no **Waste** verb. If Rule 4 lands and
    expiring items enter the queue, the natural resolution for "past
    date" is bin-it → and the user shouldn't have to leave the
    stocktake flow to log it. Proposal to weigh:
    * Add "Waste" as a per-item resolution that logs a
      [`StockItemWasteEvent`](dora_api/domain/entities/stock_item_waste_event.py)
      AND flips the level to Out AND bumps `last_checked_at`, in one
      action. Charter P2 preserved — waste-capture stays
      reason-only (no quantity, no value, no note per
      `PROPOSAL_WASTE_MINIMISATION §5`).
    * New endpoint `POST /waste/events/bulk` taking a list of
      `{stock_item_id, reason}`. Bulk-select mode gains "Log waste on
      selected" alongside "Bulk check."
    * **Interaction with the check verb:** if an item is
      near-expiry AND the user hits "Check" (level still correct, not
      binning it yet), does it stay on the expiring queue? Probably
      yes — Check bumps `last_checked_at`, but expiry is unchanged.
      Worth surfacing this explicitly so a checked-but-still-close-to-
      expiry item doesn't silently drop off the rescue card.
  - **The combined framing worth naming:** stocktake and waste-rescue
    are two halves of the same walk (open the fridge → eyeball each
    item → resolve it), currently split into two surfaces. The clean
    long-term shape is stocktake as a *review* mode with three
    resolutions per item (Keep / Set level / Waste) and a queue that
    includes both cadence-overdue and expiry-imminent items. That's
    proposal-scope — probably belongs in a proper
    `PROPOSAL_STOCKTAKE_MODE.md` brief (see [[FU-430]]) rather than
    piecemeal, and the expiry+waste angle is a stronger anchor to
    build that brief around than the four remaining SK NO_HOME
    items alone.
  - **No-change cost**: if the round-18 rule turns out to be roughly right,
    the only required follow-on is the browser-verify pass (FU-222 covers
    the SPA side; this rule lives in the backend and wants its own dataset
    walk-through).

- **Why deferred:** the user explicitly wants to sit with this and decide
  later. No code change pending here yet — this entry is the substrate for
  that decision. **Extended 2026-07-02** with two candidate additions
  (expiry as an engagement signal, waste as a stocktake resolution + bulk
  API) surfaced from user feedback; the underlying framing is that
  stocktake and waste-rescue are two halves of the same walk. This
  extension is *for careful consideration*, not a build ask.
- **Recommended resolution:** opportunistic — re-open when the user has
  walked their pantry through the new queue and decided whether the
  engagement rule is too tight, too loose, or right. Coordinate with
  [[FU-430]] when either opens: the expiry+waste extension above is a
  stronger anchor for the missing `PROPOSAL_STOCKTAKE_MODE.md` brief
  than the four remaining SK NO_HOME items alone. Do not action either
  FU in isolation.



## [RESOLVED] FU-335 — Migrate StoresSettings logo upload to ImageSourcePicker
- **Raised:** 2026-06-30 (FU-334 follow-on — image-source-picker rollout)
- **Type:** leftover
- **What:** [`web_app/src/pages/settings/StoresSettings.vue`](web_app/src/pages/settings/StoresSettings.vue) still uses Quasar `q-file` for its store-logo upload. Every other image-upload site now routes through the shared `ImageSourcePicker` primitive (R-0NN), which gives users the **Take photo** vs **Choose image** split. Migrating means dropping `q-file` (loses its drag-drop visual + clearable affordance, gains the consistent UX). The store-logo surface also has its own bespoke chrome (preview + max-file-size hint + reject toast wiring) that needs careful re-housing.
- **Why deferred:** the `q-file` → custom-buttons swap is the only bespoke part of the chrome; the rest (preview + clear) belongs in `ImageUploadField` if we want it. Doing it right is a 30-line refactor with one cross-cutting concern (drag-drop equivalent), not trivial enough to slip into the FU-334 sweep. Charts as a quality follow-on, not a blocker.
- **Recommended resolution:** opportunistic, next time settings is touched OR when a second store-logo bug forces us into that file.
- **State note (2026-07-04):** migrated to `ImageSourcePicker` directly (not `ImageUploadField`) — the store-specific `StoreLogo` preview with fallback swatch is deliberately retained, so the picker-only shape fits better than the generic wrapper. Chrome mapped 1:1: `q-file` → `<ImageSourcePicker accept="image/png,image/jpeg,image/webp" @pick @error>`; local `MAX_BYTES = 6_000_000` + local `ACCEPT` constants dropped in favour of the install-wide image policy that `processImageFile` reads (R-003 single source of truth); `@rejected` toast replaced with an inline `pickError` caption under the picker (same shape ImageUploadField uses on other sites — one visual language for "your file didn't fit"); `imageFile: File | null` ref and the local `FileReader` code both deleted (the picker returns a `ProcessedImage` with a ready `dataUrl` — the resize/re-encode happens in `imageService.processImageFile`). A new `pickerVerb` computed toggles the two button labels between "Add logo" and "Change logo" to match the language ImageUploadField uses elsewhere. The "Remove existing logo" button + `clearImage` flow is unchanged. `vue-tsc --noEmit` clean. Verify item covers the browser check.

## [RESOLVED] FU-426 — Waste-page scratch assessment: confirm fully absorbed by C-waste
- **Raised:** 2026-07-01 (docs audit).
- **Type:** finding (audit trail).
- **What:** `docs/99_scratch/WASTE_PAGE_ASSESSMENT_2026-06-24.md` became `PROPOSAL_WASTE_MINIMISATION.md` + `IMPL_PLAN_WASTE_MINIMISATION.md`. Confirm every keep-item from the scratch note is either in the shipped proposal, a landed FU, or explicitly-dropped-with-rationale. If clean, archive the scratch note.
- **Why deferred:** low risk, just a delta-check.
- **Recommended resolution:** opportunistic; also fold the archive step into it (move to `06_legacy_prompt_plans/` or delete).
- **State note (2026-07-04):** delta check **clean**; scratch note deleted. Every recommendation from the assessment is absorbed with rationale in the shipped proposal:
  - **Rename to "Use soon" / "Rescue"** → superseded by a stronger call: **dissolve `/waste` entirely** (D10 route deleted, D11 no nav-slot replacement). `WastePage.vue` is gone from the tree; capture moved to StockItemRow expiry dropdown `Mark as wasted` (D1/D2 tile-grid + Undo toast).
  - **Push insights into Reports as a card** → explicitly dropped with rationale (D12: no Reports waste card; the cheap most/recently-wasted view lives only inside the simplified `waste_insights` Dora tool).
  - **Decide layered vs duplicated Dashboard "Use soon"** → resolved to *cut* (D9: `Use soon` card removed; `Needs your attention` absorbs).
  - **Don't invest further until Dora Score lands** → charter tie-break of the proposal quotes this directly: "keep the signal, shed the surface." Dora Score subsequently shipped as P8-08 (Kitchen health card).
  - Explicit don'ts from the scratch (no bulk logging, no photo capture, no freezer-zone modelling, no shame UI) all preserved in the proposal (D1/D2 minimalist capture, D7 freezer is "a physical move, not an app state", charter tie-break §"shame-free by design").
  - **One real leftover found + fixed inline:** [DoraScoreCard.vue:143](web_app/src/components/dashboard/DoraScoreCard.vue) linked the waste component-action to `/waste` — a stale route from P8-08 (which was written after the /waste page was deleted). Set to `null` (R-014 reveal-and-disable: the score row still explains the number, just without a dead button). `vue-tsc --noEmit` clean.
  - Scratch note deleted; source-assessment pointer in the proposal updated to name the deletion; PROJECT_STATE doc-register updated (99_scratch count 6 → 5).

## [RESOLVED] FU-434 — Pre-existing `AdminDataImport.vue` `exactOptional` errors
- **Raised:** 2026-07-02 (P8-02 close-gate — spotted via `vue-tsc`).
- **Type:** finding (pre-existing, not touched by P8-02).
- **What:** `vue-tsc --noEmit` reports two errors in [`AdminDataImport.vue:33,35`](web_app/src/pages/settings/AdminDataImport.vue): a `find(...)` result assigned to `ImportTemplate` without narrowing the possible `undefined`. Fires under `exactOptionalPropertyTypes: true`. Confirmed pre-existing (git status was clean at session start; `git diff` empty on the file).
- **Why deferred:** out of scope for P8-02; the file works at runtime (find over a fixed template list that always has entries).
- **Recommended resolution:** opportunistic — next Admin/Data touch, fix with either an assertion or an explicit fallback. Two-line fix.
- **State note (2026-07-04):** already fixed by prior work — investigation on FU-434 pickup found `vue-tsc --noEmit` runs **clean** (0 errors). File now uses `templates[0]!` non-null assertions on lines 33 + 35 (the "two-line fix" the FU suggested); the assertion is honest because the outer `v-if="templates.length === 1"` on line 28 gates the whole block. Landed in an intervening commit (likely `0642548` recipe-importer overhaul which touched the file). Confirmed the shape is stable + reader-obvious (no source comment needed per R-008 — the v-if guard is right there). Closing without code change; the fix is in the tree.

## [RESOLVED] FU-454 — BuyVerdictCard `mark_stocked` + `remove_from_list` one-tap actions unwired
- **Raised:** 2026-07-02 (P8-06 close, spotted while closing FU-437).
- **Type:** deferred job (polish; nice-to-have).
- **What:** the card's one-tap-action button now renders in `StockItemDetailPage.vue` overview tab, and the `add_to_list` variant is fully wired. The other two variants (`mark_stocked` when wastes-often + stocked → "Already stocked"; `remove_from_list` when the item is already on an open list → "Remove from list") emit their `@action` events but the handler in `onBuyVerdictAction` is a no-op nudge — the fact editors immediately below the card *are* the primary way to change level or remove a list line. Tapping the button is silent, which is quietly-broken UX (Charter P3).
- **Why deferred:** wiring these needs the "Well-Stocked" `StockLevel` id lookup (from `stockLevelStore`) + a specific list-line target (find the open list containing this item + drop that line). Neither is difficult; it just wasn't the P8-06 story and the fact editors cover both cases.
- **Recommended resolution:** opportunistic — either wire both handlers properly, OR hide the card's one-tap button for these two `kind` values (reveal-and-disable, R-014) so users don't tap a dead button. Small either way.
- **State note (2026-07-04):** wired end-to-end (option A). New shared composable [useBuyVerdictActions.ts](web_app/src/composables/useBuyVerdictActions.ts) exposes `markStocked(stockItemId)` and `removeFromAllOpenLists(stockItemId)` — same seams the row card + detail card + shopping-list card all now delegate to (R-001 componentisation-first, R-003 single source of truth for mutation paths). `markStocked` reuses `stockItemStore.updateStockLevelAsync` (the same call the row's stock-level dropdown makes) with the "Well-Stocked" band looked up via `STOCKED_SEQUENCE === 0` on `stockLevelStore.stockLevels`; on success invalidates the buy-verdict + refreshes pantry beliefs; toasts positive on success, negative on failure. `removeFromAllOpenLists` fans out via `useShoppingListActions.removeFromAllLists` over every non-`done` list summary — the server's `by-stock-item` DELETE is a safe no-op on lists that don't contain the item, so no per-list membership probe is needed. Three call sites updated: [StockItemDetailPage.vue:1521](web_app/src/pages/StockItemDetailPage.vue) reloads detail after `markStocked` so the level chip repaints; [StockOverview.vue:702](web_app/src/pages/StockOverview.vue) replaces the "use the row controls" nudge toast with real mutations; [ShoppingListDetail.vue:2216](web_app/src/pages/ShoppingListDetail.vue) wires `mark_stocked` (its `remove_from_list` was already correctly line-specific and left as-is). `vue-tsc --noEmit` clean; 41/42 backend buy-verdict tests still green (the pre-existing FU-444 failure is unrelated).

## [RESOLVED] FU-442 — §LOGIN password-policy feedback still uncovered
- **Raised:** 2026-07-02 (C-19 audit — spotted while writing coverage table).
- **Type:** finding.
- **What:** feedback bullet "Password policy feels too restrictive, do minimum of 8 characters, and allow admins to turn the restrictions off." C-19 explicitly left this alone (out of shell-styling scope).
- **Why deferred:** doesn't belong in an auth-shell styling proposal; needs its own decision.
- **Recommended resolution:** later during `PROPOSAL_CONFIG_AND_OPTINS.md` extension, or spin a small standalone prompt. Not blocking C-19.
- **State note (2026-07-04):** shipped as a **NIST SP 800-63B / ISO/IEC 27002:2022 §5.17 aligned** policy in [auth_helpers.py:43-108](dora_api/infrastructure/auth_helpers.py). Changes:
  - `MIN_PASSWORD_LENGTH` **10 → 8** (matches feedback request + NIST minimum).
  - **Composition rules dropped** — no forced letter + digit mix. NIST removed these in 2017 (SP 800-63B §5.1.1.2 rationale: they push users toward predictable substitutions like `Password1!` which reduce real entropy).
  - **Breach-list check added** — a bundled frozenset of the top ~60 known-compromised passwords (`password123`, `qwerty`, `letmein1`, `dashydora`, etc.) is rejected case-insensitively, with a friendly message ("appears on public breach lists — pick something less common").
  - **Admin override deliberately NOT added** — the user's explicit call. An install-wide toggle would defeat the compliance posture; keeping the policy fixed is what makes the ISO/NIST citation truthful.
  - Frontend copy updated on SetupAdminPage, LoginPage, ResetPasswordPage, AccountSettings — hint text now reads "at least 8 characters, a passphrase works well" (no composition-rule language). AccountSettings' stale `>= 4` client rule tightened to `>= 8` to match.
  - **23/23 pytest green** on `tests/test_password_policy.py` covering min-length boundary, no composition rules (letters-only + digits-only pass), breach-list rejection (case-insensitive), and the policy-doc text. `vue-tsc --noEmit` clean.
  - Rationale + full policy documented inline in `auth_helpers.py` as an R-008 header block so a future reader can see the ISO/NIST citation without hunting the changelog.

## [RESOLVED] FU-411 — PLATFORM_BUILDS_AUDIT target-matrix: not acted on
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `docs/05_investigations/PLATFORM_BUILDS_AUDIT.md` recommends a target-matrix (which platforms to prioritise for native builds). Nothing acted on; overlaps with P8-10 native and P5-04 mobile field-test.
- **Why deferred:** Phase 3 flagship-adjacent.
- **Recommended resolution:** roll into the P8-10 native-app brief when Phase 3 opens.
- **State note (2026-07-04, P8-10):** matrix decision landed with the P8-10 build. Prioritised: **Android (Capacitor, buildable on Linux)** + **PWA install (already working)**. Deferred: **iOS** (scaffolded via `cap add ios` but never built — needs a Mac session and $99/yr Apple Developer account when there's a real user). Skipped: Electron (PyInstaller path is better), Cordova, BEX. Full setup and rationale in [packaging/BUILD_NATIVE.md](packaging/BUILD_NATIVE.md).

## [RESOLVED] FU-418 — Distribution Spec §4 open questions
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `docs/05_investigations/Distribution Spec - Desktop App & Mobile Client.md` §4 has explicit open questions for the user. Not answered; overlaps with PLATFORM_BUILDS_AUDIT and P8-10 native.
- **Why deferred:** Phase 3 / commercialization territory.
- **Recommended resolution:** roll into the P8-10 native-app brief when Phase 3 opens; answer the §4 questions inline there.
- **State note (2026-07-04, P8-10):** answered in practice during P8-10 scope-lock. (1) Backend URL is user-configurable at runtime via a first-run screen + Settings → About edit control (@capacitor/preferences persistence). (2) Push notifications on native = **unsupported today**; VAPID web push kept for browser + PWA only, native FCM bridge deferred as [[FU-465]]. (3) Wake-lock via the standard `navigator.wakeLock` Web API in cook + shop mode. (4) Store submission not attempted; draft copy landed in [docs/04_proposals/PLAY_STORE_LISTING.md](docs/04_proposals/PLAY_STORE_LISTING.md).

## [RESOLVED] FU-104 — Move the URL recipe importer into the private companion app (legal posture)
- **Raised:** 2026-06-10 (user, during Cookbook Chunk 7 review)
- **Type:** policy / distribution-posture decision (cross-cutting)
- **Resolved:** 2026-07-04 by IMPL_PLAN_RECIPE_IMPORTER Chunk 5 —
  **legalized in place, no companion split needed**. The URL fetcher
  (`import_recipe_from_url.py`) was deleted outright; the endpoint
  reshaped to `POST /api/recipes/import-from-content` accepting user-
  pasted text. The operator of a hosted Dora instance no longer touches
  third-party sites — the fetch moved to the user's browser via paste.
  Core keeps `Recipe.source` (metadata only; never fetched). Distribution
  posture (R-005) satisfied by construction — no outbound HTTP, no
  ambient IP surface, no user-agent fingerprint.

## [RESOLVED] FU-199 — SSRF in recipe import-from-URL
- **Raised:** 2026-06-16 (senior/tech-lead review).
- **Type:** finding (security, HIGH).
- **Resolved:** 2026-07-04 by IMPL_PLAN_RECIPE_IMPORTER Chunk 5 —
  **closed by construction**. The URL-fetching endpoint
  (`POST /api/recipes/import-from-url`) is deleted; the replacement
  `POST /api/recipes/import-from-content` accepts user-pasted text only.
  There is no `requests.get()`, no host, no redirect, no scheme to
  validate. No allow-list / block-list needed because there is no
  outbound HTTP.

## [RESOLVED] FU-449 — P6-07 cook→consume: `consumption_events` writes never landed
- **Raised:** 2026-07-02 (P6 legacy-plan cross-check).
- **Type:** finding (loop-integrity gap).
- **Resolved:** 2026-07-03, as the foundation leg of P8-07 (the flagship
  depends on cadence quality — champion plan §5). Shipped:
  - New `ConsumptionEvent` entity + `ConsumptionEvent` table + migration
    `f2a9c4d7e1b8` (stock-item-scoped depletion log; distinct from the
    recipe-scoped `CookEvent`). FKs SET NULL, denormalised names, indexed
    on stock_item_id.
  - Written on a cook-driven level **drop** via the existing
    `PATCH /stock-items/<id>` path (new `consumption_source` /
    `consumption_recipe_id` fields; the cook-mode finish dialog tags its
    per-item drops `source='cook'`). Keeping it on the one level-change
    site preserves R-001/R-003.
  - Consumed by the new P8-07 belief service (`pantry_belief.py`):
    `cooks_since_purchase` advances depletion, so the run-out inference
    **demonstrably shifts when cooked vs only bought** (unit-tested in
    `tests/test_pantry_belief.py::test__cooking_shifts_prediction_earlier`),
    and the reason chip reads "cooked with N× since" — the done-when bonus.
- **Scope note:** the separate buy-verdict `_cadence_detail` was left
  purchase-cadence (its "should I buy" purpose); the belief service is the
  canonical run-out inference that blends cooking. Logged in
  `PROPOSAL_ZERO_INPUT_PANTRY.md §4`. Server-env verify (migration + pytest)
  pending a Python box.

## [RESOLVED] FU-300 — Dashboard quick actions: add "Log price"
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 5).
- **Type:** follow-up.
- **Resolved:** 2026-07-03. Shipped a global `LogPriceSheet.vue` +
  `useLogPrice` composable mounted alongside `QuickAddSheet` in
  `MainLayout.vue`. Dashboard quick-action bar now has a third button
  "Log price" (money-gated to match `StockItemRowPriceButton`); it pops a
  bottom sheet with the same shortlist ordering as QuickAddSheet (low/out
  first), then hands off to the shared `PriceEntry` component in shelf mode
  with the item's `price_entry_prefill` seeded lazily. No new API — reuses
  `stockItemApi.addPriceObservationAsync`.

## [RESOLVED] FU-299 — Dashboard stock donut: deep-link buckets to filtered /stock
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 5).
- **Type:** follow-up (enhancement).
- **Resolved:** 2026-07-03. No new query-param needed — `StockOverview.vue`
  already reads `?level_id=<id>` (lines 1081-1088). Dashboard donut now
  computes low/out `stock_level_id`s via `findLevelBySequence` on the
  hydrated `stockLevelStore` and links each of: (a) the donut segment (SVG
  `<circle>` with `role="link"` + keyboard handlers), and (b) the legend
  row (`<router-link>`). The card-level `:to="/stock"` was removed; a
  "View →" action link keeps the unfiltered path. "In stock" is
  intentionally not clickable (no matching filter — it's the residual).

## [RESOLVED] FU-296 — Dashboard "price drops" widget
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 4).
- **Type:** deferred job.
- **Resolved:** 2026-07-03. Server-side verify is user-driven (no Python
  env on this box); code landed:
  - **Server:** new `PriceDropsHandler` + `GET /api/reports/price-drops?limit=N`
    in `reports.py`. Definition of "new low": `current_offer.price_now`
    strictly less than the minimum of that product's
    `ProductHistoricOffer.price_now` values — Honesty (§2.4). Products with
    no history skip (a first-ever price isn't a drop). Ranked by drop
    percent desc; slice done server-side (state-ownership §8.2). Stamps
    `has_image` + `linked_stock_item_*` only against the sliced set to
    avoid touching the deferred image blob for the tail.
  - **Client:** `reportsApiService.getPriceDropsAsync`, new `price_drops`
    card def in `DashboardPage.vue` (zone `'money'`, `gate: 'products'`,
    `defaultHidden: true`), rendered next to Best deals. Empty state:
    "Nothing at a new low right now — I'll flag one when a tracked product
    drops." Added to `DORA_VERIFY.md` under Dashboard.

## [RESOLVED] FU-396 — P7-02 fuzzywuzzy → RapidFuzz (already shipped by FU-196; ledger stale)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (real blocker) — turned out to be a stale duplicate.
- **What:** ledger claimed `fuzzywuzzy==0.18.0` was still in `requirements.txt` and used in `global_search.py` + `import_recipe_from_url.py`; RapidFuzz swap was gated as a Phase 4 kickoff task.
- **Resolved:** 2026-07-04 (discovered during
  `IMPL_PLAN_RECIPE_IMPORTER` Chunk 3). Verified with `grep`:
  * `requirements.txt` line 23 → `rapidfuzz==3.9.6` (no fuzzywuzzy line).
  * `global_search.py` line 22 → `from rapidfuzz import fuzz`.
  * `import_recipe_from_url.py` line 30 → `from rapidfuzz import process as fuzz_process`.
  Every "fuzzywuzzy" mention that remains is in a docstring or an
  inline comment explaining the historical swap (FU-196 shipped it).
  GPL blocker is gone. No commit needed.

## [RESOLVED] FU-171 — Recipe image hide/show toggle + save broken on SQLite — `has_image` always false
- **Raised:** 2026-06-13 (FU-088 → Cookbook card revision Chunk A §1.1)
- **Type:** finding (real backend bug on SQLite deployments)
- **What:** User reported the Cookbook "Hide/show recipe photos" toggle
  didn't work — positive toast fired but cards kept showing images — plus
  recipe-image upload on the detail page appeared to reset immediately
  after Save. Stock overview's image toggle worked, deepening the mystery.
- **Root cause (2026-07-03):** `_hydrate_has_image` in
  `dora_api/features/recipes/get_recipes.py` used raw
  `text('… WHERE id IN :ids')` bound with `[str(uuid), …]`. On SQLite the
  `Recipe.id` column is `sqlalchemy_utils.UUIDType` → stored as
  `BINARY(16)`; the string IN-list never matches a blob, so the query
  returns zero rows and every DTO gets `has_image=False`. Symptoms line
  up perfectly:
    - Cookbook cards always fall back to the coloured-initial tile
      (`v-if="showRecipeImages && recipe.has_image && ..."` short-circuits
      false), so the show/hide toggle is invisible because there are no
      real images to hide.
    - Recipe-detail upload works while the editor is *dirty* (the preview
      reads `form.image` directly), but the post-save `loadRecipe()`
      refetches a DTO with `has_image=false`, so the preview flips to the
      placeholder. Looks like "poof, it's gone" even though the bytes are
      safely in `Recipe.image`.
    - Stock overview worked because `get_stock_items._hydrate_has_image`
      had already been rewritten as an ORM `select()` (see the
      `project_sqlite_uuid_text_binding` memory) — same class of bug,
      caught earlier for that surface.
- **Evidence:** curl round-trip against the live dev server on 2026-07-03:
  1. `PATCH /api/recipes/<id>` with a data-URL image → 204; DB
     `Recipe.image` blob went from NULL to 114 bytes.
  2. `GET /api/recipes/<id>` still returned `"has_image": false`.
  3. Standalone ORM `select(Recipe.id, Recipe.image.is_not(None))
     .where(Recipe.id.in_([uuid]))` from Python REPL returned
     `[(UUID('…'), True)]` under the same SQLite path.
- **Resolved:** 2026-07-03. Two edits:
    - `get_recipes.py` `_hydrate_has_image` — switched to
      `select(Recipe.id, Recipe.image.is_not(None)).where(Recipe.id.in_(ids))`
      so SQLAlchemy's UUIDType adapts the bindings to the column's
      native storage.
    - `get_meal_plans.py` `_hydrate_entry_has_image` — same rewrite;
      identical bug pattern that would have hidden recipe images on the
      meal-plan surface too.
  Two sibling `text() + str(uuid)` queries remain in
  `get_stock_items._hydrate_linked_product_count` and
  `get_recipes._compute_estimated_cost` — logged as [[FU-463]] because
  they're not on the reported surface and the rewrites are non-trivial.
  Backend restart required to pick up the change.

## [RESOLVED] FU-312 — Pre-existing eslint error in `StockItemRow.vue` waste-undo handler
- **Raised:** 2026-06-26 (surfaced during FU-209 verification)
- **Type:** finding (pre-existing lint regression)
- **What:** `web_app/src/components/stock/StockItemRow.vue:635` — the Undo
  action handler on the wasted-item toast was an `async () => { ... }`,
  passed where Quasar's notify action expects a `void`-returning handler.
  eslint flagged `@typescript-eslint/no-misused-promises`.
- **Resolved:** 2026-07-03. Handler already wrapped the awaited work in a
  synchronous `handler: () => { void (async () => { ... })(); }` closure —
  file lints clean. Ledger caught up.

## [RESOLVED] FU-327 — Windows + macOS desktop build scripts for the Piper bundle
- **Raised:** 2026-06-24 (Piper platform audit). Renumbered from
  FU-288 on 2026-06-29 to resolve a ledger numbering collision.
- **Type:** deferred job.
- **Resolved:** 2026-07-03. Shipped both platform build scripts
  mirroring `build-linux.sh`. User has no Windows or macOS dev
  machine at resolve time — cross-platform verify is user-driven,
  16 checkboxes total split across two new sections in
  `DORA_VERIFY.md` under Build/install/desktop.
- **What shipped:**
  - `packaging/build-windows.ps1` — PowerShell script; SPA build →
    Piper fetch (auto-detected `windows_amd64`) → default voice
    fetch → `pyinstaller --noconfirm dora.spec` → smoke-check
    `dist\Dora\Dora.exe`. Flags `-SkipSpa`, `-SkipPyInstaller`,
    `-Clean`.
  - `packaging/build-macos.sh` — bash script; auto-detects arch
    via `uname -m` (arm64 → `macos_aarch64`; x86_64 → `macos_x64`),
    passes explicit `--platform` to `fetch_piper.py` so the right
    tarball lands. Extra `--arch` override for cross-arch scenarios.
    Executable bit set via `git update-index --chmod=+x`. Same
    three flags as Linux.
  - `README.md` — Desktop-bundle section rewritten to cover all
    three platforms with per-platform prereqs and OS-appropriate
    data directories. Notes Linux is the CI-verified path;
    Windows/macOS scripts are checked-in-only pending user verify.
- **Explicitly not shipped in this pass:**
  - **`.exe` installer / `.dmg`** — both platforms produce
    directory-tree bundles; single-file installers stay a follow-on
    aligned with FU-337 (README/copy references
    AppImage/.exe/.dmg as if all three exist; only AppImage does).
  - **CI matrix.** FU flagged this as double-blocked behind FU-169
    (CI intentionally commented out to preserve free-tier
    minutes). Not touching `.github/workflows/*.yml` here.
- **Related:**
  - [[FU-336]] — PWA build mode selection (from the same
    2026-06-30 platform-builds audit); still open.
  - [[FU-337]] — README/copy alignment on installer references;
    still open.
  - Audit doc: `docs/05_investigations/PLATFORM_BUILDS_AUDIT.md`.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry for design notes +
  rules check.

## [RESOLVED] FU-287 — iOS / WKWebView autoplay across an `await` for Piper synth
- **Raised:** 2026-06-24 (Piper platform audit).
- **Type:** finding (real cross-platform constraint, not a regression).
- **Resolved:** 2026-07-03. Shipped the primer fix the FU spec'd.
  `useSpeechOutput.ts` registers a one-shot document listener at
  first mount that plays a 44-byte silent muted `data:audio/wav`
  blob on the first user gesture, claiming the browser's autoplay
  credit for the tab session — subsequent `audio.play()` calls
  (including the Dora chat reply flow that awaits LLM + Piper
  synth before playing) inherit it. Idempotent; no-op on
  Chrome/Firefox/Android. Timer-narration edge case documented
  in-code as best-effort (a timer callback that fires long after
  the last gesture may still be silent; the visible Notify remains
  the load-bearing "timer done" signal).
- **Design choice:** the FU listed two options — primer, or single
  long-lived `<audio>` element. Shipped the primer alone (the FU's
  recommended shape); ships the smaller safe change first. If iOS
  browser-verify shows the primer isn't enough, the reused-element
  refactor stays available as a follow-up.
- **iOS browser-verify pending:** user has no iOS device access
  as of resolve time. Seven-scenario checklist added to
  `DORA_VERIFY.md` under **"iOS / macOS-WKWebView audio-unlock
  primer — origin FU-287"** in the Cross-cutting section
  (chat reply Piper, chat reply browser voice, cook-mode step
  narration, timer-narration edge case, macOS WKWebView, non-iOS
  no-regression, session-scoped reload). Walked when device access
  next arrives.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry for design notes +
  rules check.

## [RESOLVED] FU-208 — My Products → stock-item "Link…" flow is a silent dead-end
- **Raised:** 2026-06-17 (products-as-overlay pivot — code investigation).
- **Type:** finding (bug).
- **Resolved:** 2026-07-03. Code has been fixed since 2026-06-17 and
  re-verified statically 2026-06-29; the FU was sitting OPEN pending
  browser-verify. Under current ledger conventions
  ([[feedback-browser-verify-not-an-fu]]) pure browser-verify belongs
  in `DORA_VERIFY.md`, not gating an FU's resolution. Two unchecked
  verify items already live under **"My Products → stock-item 'Link…'
  — origin FU-208"** in `DORA_VERIFY.md` (L912-914):
  - From My Products, "Link…" → pick stock item → product links and
    shows as linked (no bounce)
  - Error toast on failure
- **What shipped (2026-06-17):** `MyProductsPage.vue` `confirmLink()`
  now links in place via `stockItemApi.linkProductAsync`
  (`POST /stock-items/{id}/products`) + `loadAll()` + a toast, instead
  of the dead `link_product_id` navigation that had no consumer after
  C-1b.3 removed the saved-products picker dialog from
  `StockItemDetailPage.vue`. 2026-06-29 static re-verify confirmed
  `MyProductsPage.vue:1013` still hits the correct path, the endpoint
  exists at `link_product_to_stock_item.py:104`, and grep across the
  repo finds `link_product_id` only in a doc comment at
  `MyProductsPage.vue:984` — no dead navigation remains.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry.

## [RESOLVED] FU-196 — Review's lower-severity hardening batch (umbrella disassembled)
- **Raised:** 2026-06-16 (senior/tech-lead review).
- **Type:** finding (architecture + hardening).
- **Resolved:** 2026-07-03. Umbrella disassembled. The genuinely-safe
  and small items landed in one pass; each remaining item was spun
  off into its own FU so it can be triaged / scheduled / declined on
  its own merits rather than dragged around inside a stale umbrella.
- **Landed this session (easy wins):**
  - **(d1)** `Requests==2.31.0` → **`Requests==2.32.4`** — closes
    CVE-2024-35195 (`requirements.txt`).
  - **(d2)** `fuzzywuzzy==0.18.0` → **`rapidfuzz==3.9.6`** — actively
    maintained, MIT-licensed (fuzzywuzzy is GPL — mild licensing
    hazard), no python-Levenshtein warning noise. Two call sites
    swapped (`features/recipes/import_recipe_from_url.py`,
    `features/search/global_search.py`). rapidfuzz's `process` +
    `fuzz` modules are drop-in compatible with the surface both
    files used.
  - **(f1)** `web_app/src/components/SelectComponent.vue` **deleted**
    — grep confirmed zero non-self callers.
  - **(f2)** `web_app/.npmrc` **deleted** — repo is on npm, the file
    only held pnpm-specific keys (`shamefully-hoist`,
    `strict-peer-dependencies`, `resolution-mode=highest`) that warn
    on every `npm` command.
  - **(b partial)** Global exception handler in `startup.py` now
    calls `db.session.rollback()` before returning 500. Belt-and-
    braces for the multi-commit sites; the full unit-of-work
    refactor stays as FU-456 below.
- **Split off as their own FUs (do not re-umbrella):**
  - **FU-456** — Unit-of-work refactor for multi-commit handlers
    (starting with `create_recipe.py`). *(item b)*
  - **FU-457** — Boot-time resolved-route assertion for
    reflection-based wiring. *(item c)*
  - **FU-458** — Rate-limit assistant endpoints. *(item e1)*
  - **FU-459** — App-wide security headers (CSP / X-Frame-Options /
    X-Content-Type-Options / Referrer-Policy). *(item e2)*
  - **FU-460** — `SESSION_COOKIE_SECURE` default: policy call.
    *(item e3)*
  - **FU-461** — Account-deletion endpoint (GDPR) — design + build.
    *(item e4)*
  - **FU-462** — Sweep the ~237 prompt-ID comments from shipped
    source. *(item f3; duplicates FU-424's Tier-2 sub-item — same
    finding.)*
- **Previously struck (2026-06-29):** original (a) sub-item
  ("Postgres unreachable") — resolved by FU-045.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry for the audit method
  and per-item verdicts.

## [RESOLVED] FU-186 — Decommission in-app live product search / `merchant_api` + standalone `emailer/` (scraping-divorce ripple)
- **Raised:** 2026-06-15 (C-10 ingestion API design); emailer scope added 2026-06-16.
- **Type:** deferred job / decommission.
- **Resolved:** 2026-07-03. Code work has been fully shipped since
  **2026-06-17** (Phase D landed); the FU was sitting under a
  `[RESOLVED?]` heading pending browser-verify. Under current ledger
  conventions ([[feedback-browser-verify-not-an-fu]]) pure
  browser-verify belongs in `DORA_VERIFY.md`, not gating an FU's
  resolution, so moving to RESOLVED now.
- **What shipped (2026-06-17 Phase D — verbatim from the FU update):**
  `merchant_api/` + `emailer/` directories deleted from this repo
  (they live in `../dora-companion`). Backend wiring stripped
  (audit `SOURCE_MAPI` + `SOURCE_EMAILER` retained read-only as
  `*_LEGACY` for historical rows; nothing in `dora_api` writes those
  values any more). FE wiring stripped: `merchantApiService` /
  `merchantManagementApiService` / `MerchantsSettings.vue` /
  `ProductSearch.vue` / `ProductSearchCard.vue` /
  `ProviderHealthChip.vue` / `merchantStore` / `scrapedProductOffer*`
  / `offerSortByOptions` all gone; `axiosHttpClient` no longer
  carries the `'merchant'` `ApiBackend` arm. `useProductSearchUrl()`
  composable added; `useFeatureFlags().products` + the new
  `AppSetting.product_search_url` drive a re-pointed **Product
  Search** nav entry that opens the admin-configured URL in a new
  tab (data-gated; R-014 disabled-with-hint when URL unset). Infra
  cleaned: `desktop_app.py` only spawns dora_api, `compose.yml`
  drops the 5172 port + emailer block, `Dockerfile` + `startup.sh`
  no longer spawn the companion processes, `nginx.conf` drops the
  5172 proxy comment, `dora.spec` drops the merchant_api submodules
  + emailer templates, `.env` / `.env.example` drop `MAPI_*` + the
  `DORA_EMAIL_ENABLED` deals-emailer block (the `DORA_SMTP_*` vars
  stay for the transactional sender), CI drops the `compileall`
  smoke job. Migration `f8b2d4a6c1e3` adds
  `AppSetting.product_search_url`. **Verified at land time:** pytest
  **405/405** (+4 new), `vue-tsc` clean, `npm run lint` clean,
  fresh-SQLite `flask db upgrade` clean.
- **Design context — products-as-overlay pivot (2026-06-17):** the
  search question was settled by
  `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` §4.1 — only the
  Product Search page moves to the companion (its own complete app
  in its own repo, hosting `merchant_api` + the moved search page +
  its own settings). Dora keeps the Product Search nav entry as an
  install-configured URL (data-gated; companion never named — a
  bounded carve-out to the invisibility rule). My Products / Price
  History / the stock-item Products tab **stay in Dora**.
- **Not-in-scope (preserved as-is):**
  `dora_api/infrastructure/email_sender.py` is the transactional
  sender (password-reset etc.) — stays. The legitimate in-app
  "email me stuff" need is the Alerts C-9.7 email digest (per-user
  opt-in, reuses `email_sender.py`) — so removing `emailer/` left
  no in-app gap.
- **Remaining browser-verify (unblocked):** two unchecked items
  under "Decommission scraping (Phase D) — re-pointed nav — origin
  FU-186" in `DORA_VERIFY.md` — Product Search nav opens the
  admin-configured URL in a new tab, and the System Settings input
  for `AppSetting.product_search_url` saves + round-trips. Walked
  on the user's own time; not gating this resolve.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry.

## [RESOLVED] FU-423 — MINIMAL_USER_PRODUCTS_OFF_FRICTION scratch → promote or consolidate
- **Raised:** 2026-07-01 (docs audit).
- **Type:** deferred job.
- **Resolved:** 2026-07-03. Duplicate of an already-resolved FU;
  its "close as duplicate of FU-181" note was a **typo** — the
  scratch doc's own header + IMPL_PLAN_ONBOARDING.md +
  PROPOSAL_ONBOARDING.md all point the scratch at **FU-182**
  (Products-off minimal-user workflow), which was promoted to
  `docs/04_proposals/PROPOSAL_SIMPLE_MODE.md` and resolved.
  Fixing the ledger typo rather than propagating it. The scratch
  doc's header still says "see FU-181" — leaving that alone (it's
  a talk-time doc; the two promotion targets in `04_proposals/`
  cite FU-182 correctly and are authoritative).
- **See:** the resolved FU-182 entry below in this file.

## [RESOLVED] FU-181 — Wire actual plan-emailing + a `meals_per_week` preference
- **Raised:** 2026-06-14 (C-2.J sequential builder).
- **Type:** follow-up (deferred sub-feature).
- **Resolved:** 2026-07-03. Two loose ends resolved differently:
  1. **Loose-end #1 (plan email) — stale, not built.** The disabled
     Email button the FU cited was removed from
     `SequentialBuilderDialog.vue`'s done-step (grep across all
     meal-plan surfaces returns zero email references). Removing
     the button was an implicit product decision — print-view →
     Save-as-PDF is the export path
     (`useMealPlanExport.ts:1-4` also notes FU-168 similarly
     retired CSV). Not re-added. If plan-emailing returns as an
     ask later it's a fresh feature request grounded in current
     email/SMTP infra, not the FU's original disabled-button entry
     point.
  2. **Loose-end #2 (`meals_per_week` pref) — shipped.**
     `BUILDER_TARGET_MEALS = 7` was still hardcoded in
     `useMealPlanner.ts:24`. Added `User.meals_per_week int | null`
     (bounds 1–21, null → SPA fallback of 7), wired through the
     entity + Fields + `AuthenticatedUserDto` + `UpdateMeRequest` +
     handler + table mapping. New `useMealsPerWeek()` composable
     (`web_app/src/composables/useMealsPerWeek.ts`) reads the pref
     reactively; both `MealPlansBoardPage` and `MealPlansOverview`
     consume it. Constant renamed to `BUILDER_TARGET_MEALS_FALLBACK`
     — single source of the fallback, no other file re-hardcodes 7.
     Preferences → Meal planning gains a "Meals per week" number
     input (1–21; blank = default 7). Migration
     `d7e3b9f4a1c2_20260703_user_meals_per_week.py` (chains off
     `c6d2a8e3b9f1` FU-316).
- **Where landed:**
  `dora_api/persistence/migrations/versions/d7e3b9f4a1c2_20260703_user_meals_per_week.py`,
  `dora_api/persistence/table_mappings.py`,
  `dora_api/domain/entities/user.py`,
  `dora_api/features/auth/register_user.py`,
  `dora_api/features/auth/update_me.py`,
  `web_app/src/models/auth.ts`,
  `web_app/src/services/api/authApiService.ts`,
  `web_app/src/composables/useMealPlanner.ts` (rename),
  `web_app/src/composables/useMealsPerWeek.ts` (new),
  `web_app/src/pages/MealPlansBoardPage.vue`,
  `web_app/src/pages/MealPlansOverview.vue`,
  `web_app/src/pages/settings/PreferencesSettings.vue`.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry.

## [RESOLVED] FU-170 — App-wide button display preference (icon-only / icon+text / mixed)
- **Raised:** 2026-06-13 (FU-088 cookbook card revision — Cook button
  went icon-only `mdi-chef-hat`; wanted this controllable user-wide).
- **Type:** new feature.
- **Resolved:** 2026-07-03. Planning-pass verdict: the proposed
  3-way user pref doesn't pay its rent. Not building. User agreed.
  Full reasoning preserved so a future "revisit if a real user
  complaint arrives" is grounded:
  - **Scale checked:** 651 button call sites in the SPA
    (`BaseButton` + raw `q-btn`); 119 use `variant="icon"`.
    Almost all icon-only buttons already carry their verb in a
    `<q-tooltip>` child or `aria-label` — the "per-button policy"
    the FU proposed to formalise is already embedded in each call
    site's shape, just not in a registry.
  - **Neither non-default mode is genuinely usable.**
    `icon_only` would strip labels off Save / Cancel / Delete /
    Confirm — those words *are* the affordance. `icon_text` would
    force labels onto ± steppers, modal-close X's, week-nav arrows,
    hamburger, image-reorder arrows — components explicitly
    designed for icon-density, layouts break.
  - **"Mixed" default is what the code already does implicitly.**
    Formalising it into a Settings knob nobody will meaningfully
    change adds a permanent audit tax on every new button
    ("what's this button's policy?") for zero user-observable
    payoff. Charter P8 Anti-creep concern.
  - **Trigger case is a one-liner.** The FU's raiser trigger — Cook
    button feeling too icon-only on the recipe card — can be
    addressed by just adding a `label` prop to that one button if a
    complaint arrives. Since the button landed, no user complaint
    has surfaced in DORA_FOLLOWUPS or this session's punch-list
    passes.
- **Trigger for a future revisit** (self-surfacing): if a user
  reports a specific icon-only button as unreadable, address that
  button. If a *class* of complaints surfaces (users lost across
  many icon-only surfaces), reopen this FU and consider a narrower
  per-surface fix rather than a global knob.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry.

## [RESOLVED] FU-134 — Audit other `autoGenerate` call sites for Axis-B routing
- **Raised:** 2026-06-12 (Cart Button Chunk 4 impl).
- **Type:** follow-up.
- **Resolved:** 2026-07-03. Audit complete — all three named sites
  resolve without code changes. Grep-verified only three
  `autoGenerateAsync` hits remain in the codebase (the service
  definition, `useMealPlanner.ts` — the Axis-B-aware Chunk-4
  surface, and `NewListDialog.vue`); the two other named sites are
  gone entirely.
  1. **`web_app/src/components/dialogs/NewListDialog.vue:418`** —
     still calls `autoGenerateAsync` with
     `merge_into_list_id: targetListId`, where `targetListId` was
     resolved upstream. Axis-B-aware by construction; FU's original
     verdict on this site was "no change needed" and remains true.
  2. **`web_app/src/pages/RecipesOverview.vue` "add all missing" —
     `autoGenerateAsync` call is gone.** The flow was reworked to
     open a per-ingredient picker (`pickerOpen` at ~L1247-1296) that
     emits `{ stockItemIds, targetListId }`, then `onPickerConfirm`
     calls `addItems(targetListId, ...)`. Axis-B-aware by
     construction — the user picks the list before anything runs.
  3. **`web_app/src/layouts/MainLayout.vue` global shortcut —
     `autoGenerateAsync` call is gone.** The command palette was
     retired 2026-06-12 (comment at ~L183). Remaining global
     shortcuts are pure navigation (`g s`/`g l`/`g r`/`g d`/`g h`,
     `?`, `/`) — no "generate shopping list" entry to route.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry.

## [RESOLVED] FU-144 — Cart-state awareness for product-anchored adds
- **Raised:** 2026-06-12 (FU-131 impl).
- **Type:** follow-up.
- **Resolved:** 2026-07-03. Trigger-not-fired resolve. Verified
  against current code: still one consumer of
  `AddToListButton variant="inline-product"` —
  `web_app/src/pages/MyProductsPage.vue:351`, and only for
  **unlinked** products (linked products fall through to the
  stock-item variant, which already renders full cart-state).
  Backend dedup at
  `dora_api/features/shopping_lists/manage_shopping_list_lines.py:107-113`
  already returns `already_on_list=true` on a repeat product-anchored
  click on the same list, so the *bug* the FU worried about
  (spurious duplicate lines) does not exist — only a
  UX-informativeness gap remains. The FU raiser's deferred bar was
  well-set:
  - **"Third product-anchored consumer of `AddToListButton` shows up"** —
    still one.
  - **"User reports the double-add UX as a problem"** — not reported.
  Doing it now means extending `MembershipDto` with a parallel
  `product_items` array (permanent DTO-payload growth on every
  navigation), generalising `cartStateFor`, and rewiring the ~200
  lines of state logic in `AddToListButton.vue` that today branch on
  `stockItemId`. Not warranted against zero triggers.
- **Trigger for a future revisit** (self-surfacing): if a second
  product-anchored consumer lands (a page adding a product-line
  button somewhere new) or a user reports the double-add UX gap,
  reopen this FU and reuse the analysis above. Unlinked products
  are also a transient state — a product typically gets linked to
  a stock item over time — so the affected surface shrinks
  naturally without code changes.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry.

## [RESOLVED] FU-065 — Ticked-summary string duplicated across both finish dialogs
- **Raised:** 2026-06-08 (Chunk 3 impl).
- **Type:** finding (R-003 lite — same display string built in two places).
- **Resolved:** 2026-07-03. Superseded — the FU's premise is triply
  obsolete against the current code:
  1. **The second location is gone.** `ShoppingListShopMode.vue` no
     longer exists; shop-mode was folded into
     `ShoppingListDetail.vue`. No duplication to extract — only one
     surface builds a Finish-and-restock summary now.
  2. **The specific string is gone.** The Finish-and-restock flow
     was reworked into the M12 restock-review modal (per-item level
     tweaks via `finishReviewOpen` at
     `web_app/src/pages/ShoppingListDetail.vue:1006`), not a bullet
     summary. Grep confirms no "will be bumped" / "and N more"
     string anywhere in the SPA.
  3. **"Well-Stocked" is a retired band.** The 2026-07-02 3-band
     StockLevel collapse dropped the Sufficient middle band and
     relabelled the top band from "Well-Stocked" to "Stocked". Even
     if the summary string reappeared, it would say "Stocked", not
     "Well-Stocked".
  User is also considering redoing the modal — any future
  duplication would be shaped by the new design, not the pre-M12
  one the FU described.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry.

## [RESOLVED] FU-455 — Dashboard prefetches recipeStore but never reads from it
- **Raised:** 2026-07-03 (FU-052 audit — side-finding).
- **Type:** finding / cleanup.
- **Resolved:** 2026-07-03. Removed the dead prefetch from
  `web_app/src/pages/DashboardPage.vue` — deleted
  `recipeStore.ensureLoadedAsync()` from the `loadAll` fan-out plus
  the `const recipeStore = useRecipeStore()` binding and the
  `import { useRecipeStore }` line. Grep-verified no residual
  references. Saves one `GET /recipes` round-trip per dashboard load.
  R-016 lazy hydration means any downstream page still gets the
  store on its own `ensureLoadedAsync` call — nothing else depended
  on the dashboard pre-hydrating for it.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry.

## [RESOLVED] FU-052 — Switch cookable surfaces to the server query + optimise the helper
- **Raised:** 2026-06-07 (Phase 1 Chunk 4 — queryable cookability).
- **Type:** follow-up.
- **Resolved:** 2026-07-03. Audit result — no code change; item is
  fully resolved (point 1 already done, points 2/3 correctly declined
  as premature and drift-creating at current scale). Original scope
  had three sub-items:
  1. ✅ **Dashboard "Cookable tonight" server-side.** Already closed
     by [[FU-298]]: the card at
     `web_app/src/pages/DashboardPage.vue:1619-1641` reads
     `summary.meal_plan.upcoming_entries` (server-computed, capped at
     3). No fetch-all + client-sort remaining.
  2. **RecipesOverview cookable toggle → server-side query — declined
     as architectural incoherence.** The cookbook applies ~20
     client-side filter axes over a hydrated store; moving one axis
     (cookable) server-side while the other ~19 stay client-side
     makes `recipes.value` mean "recipes minus the server-filtered
     axes" — a confusing local invariant. A coherent alternative
     (whole-cookbook server-query rewrite with paginated fetch and
     all axes moved) is a real refactor, not this FU. At
     ~200-recipe personal scale, multi-axis client filter over a
     hydrated cache is the right architecture.
  3. **`load_recipe_cookability` → SQL `COUNT ... GROUP BY` —
     declined as R-003 drift.** Technically cleaner, portable (no
     engine-specific `FILTER`). But at ~200 recipes / ~2000
     ingredient rows the current eager-loaded one-query pass is not
     a measurable hot path, and the SQL would duplicate the
     "is_missing" rule (`level is None OR sequence >= OUT_OF_STOCK_
     SEQUENCE`) that
     `dora_api/domain/recipe_cookability.py` +
     `dora_api/domain/stock_status.py` own as the R-003 single
     source. A SQL copy of that rule is exactly the drift R-003
     exists to prevent.
- **Side-finding spun off:** [[FU-455]] —
  `DashboardPage.vue:1931` calls `recipeStore.ensureLoadedAsync()`
  but grep-confirmed nothing on the dashboard reads `recipes.value`.
  Dead pre-hydration from a pre-FU-298 design; opportunistic cleanup.
- **Trigger for a future revisit** (self-surfacing, no persistent
  loop needed): if `GET /api/recipes/?cookable` or the dashboard-
  summary timing becomes a measurable hot path, or if the cookbook
  grows a paginated "load next page from server" posture — that's
  when the point-2/3 rewrites become coherent. Until then, resolved.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry for the audit method.

## [RESOLVED] FU-016 — Audit other "frontend cache vs backend mutation" guard races
- **Raised:** 2026-06-05 (B5 follow-up).
- **Type:** finding.
- **Resolved:** 2026-07-03. Full audit: grepped router / layout guards
  for `currentUser?.*` reads → three fields (`isAuthenticated`,
  `onboarding_completed_at`, `is_admin`). Paired each with every
  backend mutation that touches user-scoped state. Two real bugs
  found and fixed in this session:
  1. `web_app/src/pages/settings/UsersAdminSettings.vue` —
     `patch()` never refreshed `authStore.currentUser` when the
     admin was editing themselves, so self-demote / rename / email
     change left the router guard + MainLayout + SettingsShell +
     admin pages reading stale state until a hard reload.
  2. `web_app/src/pages/settings/AdminDataBackupRestore.vue` — a
     successful restore that included the users section could
     invalidate `currentUser`; the report dialog's "Reload now"
     button was the only path to sync, and "Close" left the guard
     lying. Close now refreshes `authStore.currentUser` as a
     belt-and-braces safety net (the "Reload now" affordance still
     covers the rest of the stores).
- **All-clear list (verified during the audit — refresh already in place
  or refresh not applicable):**
  - `POST /onboarding/complete` (WelcomeWizard: `onSkipEverything`,
    `complete`) — both call `authStore.refreshAsync()`.
  - `POST /onboarding/restart` (AboutSettings + DashboardPage
    Continue-onboarding) — both refresh.
  - `PATCH /auth/me` — `authStore.updateMeAsync` writes the response
    DTO straight into `currentUser`.
  - `POST /auth/me/email` — deliberate no-op on `currentUser`;
    address flips only after the confirmation link, next `/me`
    probe picks it up.
  - Password change — no cached-field mutation.
  - Session-expired 401 — interceptor clears `currentUser`.
  - `POST /data/import/spreadsheet/commit` — never touches users.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry for the full method +
  findings.

## [RESOLVED] FU-314 — Retire grandfathered `lazy="selectin"` overrides on `Recipe.cuisine` / `.category`
- **Raised:** 2026-06-28 (R-019 / ADR-014 adoption — "no magic" rule).
- **Type:** finding / engineering-standards cleanup.
- **Resolved:** 2026-07-03. Both relationships flipped to `lazy="noload"`
  in `dora_api/persistence/table_mappings.py:1246-1247`; every read site
  that touches `recipe.cuisine` / `recipe.category` after a
  `repository.get(Recipe)` now chains an explicit `.include(...)`.
  Sites updated: `features/recipes/get_recipes.py::_base_query`,
  `features/recipes/new_recipe_version.py`,
  `features/meal_plans/get_meal_plans.py::_base_query` (via sibling
  `then_include` off entry.recipe), `features/search/global_search.py`,
  `features/categories/manage_categories.py`,
  `features/cuisines/manage_cuisines.py`,
  `features/assistant/tools.py` (search_recipes, suggest_recipes,
  recipes_using_item, recipe_detail, meal_detail).
  `create_recipe.py` / `update_recipe.py` / `import_recipe_from_url.py`
  reviewed but not updated — they only write to those relationships or
  reference request-side ids.
  No new N+1 test needed: the FU-138 e2e query-count test
  (`tests/e2e/dora_api/test_recipes_query_count.py`) already asserts
  that adding 10 recipes doesn't add ~10 SELECTs to `GET /recipes`,
  which is precisely the regression the FU warned about.
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry.

## [RESOLVED] FU-315 — Verify auto-add-when-low toast + line indicator (F1)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F1 — (b) + line indicator).
- **Type:** verification / cleanup.
- **Resolved:** 2026-07-03. The verify part found a real bug: the SPA
  typed `stockItemApiService.updateAsync` as `Promise<void>` and threw
  away the server's `{ auto_added: {...} }` payload, so **no toast ever
  fired** on the auto-add-when-low trigger. Fixed by exposing a new
  `UpdateStockItemResponse` type on the API service, returning it
  through both `updateStockLevelAsync` and `updateStockItemAsync` in the
  store, and adding a shared `handleAutoAddedResponse` helper that
  refreshes the shopping-list store and fires a Quasar Notify
  ("Added *<item>* to *<list>*.") whenever the server reports an
  auto-add. The line's `auto: low stock` chip on
  `ShoppingListDetail.vue` `addedViaLabel` was already correctly wired
  (L2299-2316) — the remaining density-check is a browser-verify item.
- **Where landed:**
  `web_app/src/services/api/stockItemApiService.ts` (new
  `UpdateStockItemResponse` type + `updateAsync` return type),
  `web_app/src/stores/stockItemStore.ts` (`handleAutoAddedResponse`
  helper called from both PATCH paths).
- **See:** `DORA_WORKLOG.md` 2026-07-03 entry.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F1;
  FU-320 (help-copy pass) still gates on remaining F-block items.

## [RESOLVED] FU-316 — Quick-add "remembered list": per-add toast names the destination + "always ask" setting (F3)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F3 — combo (b)+(c)).
- **Type:** UX / cleanup + settings.
- **Resolved:** 2026-07-03. Shipped in one slice — see `DORA_WORKLOG.md`
  entry for the same date. Toast now names the destination list
  (`useStockItemActions.addToList` resolves `display_name` off the store
  summaries for all three code paths); new
  `User.always_ask_which_shopping_list` per-user boolean (default False,
  migration `c6d2a8e3b9f1`) surfaced as a **Preferences → Shopping
  lists → Always ask which list** toggle. When on, the picker fires
  every quick-add — the composable still `save()`s the pick during the
  call so the bulk-add caller in `AddToListButton` keeps working, then
  `clear()`s it in `finally` so the next add re-prompts.
- **Where landed:**
  `dora_api/persistence/migrations/versions/c6d2a8e3b9f1_20260703_user_always_ask_list.py`,
  `dora_api/domain/entities/user.py`, `dora_api/persistence/table_mappings.py`,
  `dora_api/features/auth/register_user.py`, `dora_api/features/auth/update_me.py`,
  `web_app/src/models/auth.ts`, `web_app/src/services/api/authApiService.ts`,
  `web_app/src/composables/useStockItemActions.ts`,
  `web_app/src/pages/settings/PreferencesSettings.vue`.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F3;
  `DORA_FOLLOWUPS.md` FU-320 (help-copy pass) still gates on this + the
  other F-block siblings.

## [RESOLVED] FU-438 — P8-06 Wait-or-Buy: `wait_hint` on the buy-verdict endpoint shipped
- **Raised:** 2026-07-02 (P8-05 close, forward-look).
- **Type:** deferred job (champion sequence).
- **What:** the P8-05 verdict had a `wait` outcome ("price is above usual — try later") with no time-boxed advice. P8-06 needed to derive that from cadence + personal price history, extending the *same* endpoint rather than a separate route.
- **State note (2026-07-02):** **Shipped**. New `WaitHintDto(until, reason)` + optional `wait_hint` field on `BuyVerdictDto`. New pure helper `_wait_hint(inputs)` in `dora_api/features/stock_items/get_buy_verdict.py` — low-cadence cycle detection reusing `_CHEAP_BAND_FRACTION` (one definition of "low"), median gap over ≥2 detected lows, CV guard drops the hint on erratic cadence, overdue guard drops it when the predicted next low is already past (all three: Charter P3 honesty). Composer calls it only when the verdict landed on `wait`. Frontend: `BuyVerdictWaitHint` TS type + `wait_hint: BuyVerdictWaitHint | null` on `BuyVerdict`; `BuyVerdictCard.vue` renders a `--semantic-warning-soft` block between header and reasons with a friendly relative-date headline ("Expect a dip in ~14 days (Nov 15)") + the server's reason as sub-caption. 5 new unit tests in `tests/test_buy_verdict.py` cover regular fortnightly cycle, single-low, wildly-varying-gaps, overdue-prediction, and non-wait-verdict cases (all pass). Pre-existing `test__all_axes_thin` failure (FU-444) unchanged.

## [RESOLVED] FU-437 — BuyVerdictCard wired into stock-item detail page
- **Raised:** 2026-07-02 (P8-05 close).
- **Type:** deferred job.
- **What:** the full three-axis `BuyVerdictCard.vue` component shipped with P8-05 but wasn't wired anywhere — dead code pending a home.
- **State note (2026-07-02):** **Shipped alongside FU-438** (P8-06). `StockItemDetailPage.vue` overview tab now renders the card above the fact editors, bound via `useBuyVerdict(stockItemId.value)`. The `@action` emit is delegated to the page's existing per-mutation handlers: `add_to_list` routes through the same primary-list add the row badge uses, and `buyVerdictInvalidate()` fires after `onAddToList` + `onChangeStockLevel` so the verdict re-fetches on any change that could shift the answer. The `mark_stocked` + `remove_from_list` action variants are a no-op nudge for now (the fact editors below the card are the primary way to change level / drop a list line) — logged as [FU-454](DORA_FOLLOWUPS.md) for the small polish. Browser walk pending — pair with the P8-05 verify pass in `DORA_VERIFY.md §Stock`.

## [RESOLVED] FU-453 — P8-03 email-ingestion: CUT
- **Raised:** 2026-07-02 (user's own instinct while auditing the champion sequence: *"P8-03 might also share the same fate as -04? i don't think its feasible / feels clunky"*).
- **Type:** finding + design call (governance, not code — sits next to [FU-436](DORA_FOLLOWUPS_RESOLVED.md) for P8-04).
- **What:** the champion plan's P8-03 (`docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md:266`) proposes ingesting real prices from the user's own **emails** — a per-user forwarding address / inbound webhook + retailer-specific parsers for order-confirmation emails (Coles, Woolies) and loyalty offer emails (Everyday Rewards, Flybuys). No code existed (grep clean on `loyalty` / `email.*ingest` / `receipt.*ocr` under `dora_api/features`). Five concrete problems, distinct from P8-04's:
  - **Mail-receiving surface is SaaS-shaped ops.** Per-user forwarding needs either an inbound mail service (Postmark / SES / SendGrid Inbound) — ongoing operator cost + DNS + MX for every self-host install (against **§7.5 distribution posture**), or user hand-forwarding (repeated task — Charter P1 Effortless), or IMAP polling with inbox credentials (worse credential-storage class than the loyalty portals P8-03 itself refuses — Charter 9).
  - **Retailer email HTML is silent-fragility, same class as scraping.** Layouts change without notice; parsers break silently and prices stop landing. Exactly the failure mode the pivot from central scraping was designed to escape (Charter 4/9); moving the fragility from HTTP HTML to email HTML doesn't change its shape.
  - **Loyalty offer emails are image-only by design.** Everyday Rewards / Flybuys increasingly render personalised offers as single images to defeat automated parsing. Extracting "$X off Y" reliably often isn't possible from the email HTML at all.
  - **We already ship the "in without scraping" pattern — and it's a companion.** `/api/ingest` + `dora-companion` is the architecturally correct home for legally-sourced automatic feeds.
  - **The shipped alternative already works.** `Finish & restock` (P6-01) captures `paid_price` from the list at the till — one manual event per week vs an ongoing email-parser maintenance treadmill.
- **State note (2026-07-02):** **CUT** by user decision — *"cut anyways, not worth the work — dora excels elsewhere."* Decision landed in `RECONCILED_FINISHING_PLAN.md §7 Decision 7` (adjacent to Decision 6's P8-04 CUT — different failure surface) and reflected in `DASHY_DORA_CHAMPION_PLAN.md` (P8-03 section marked CUT). If an email-ingestion companion ever surfaces, it plugs into `/api/ingest` on the same seam the retailer-scraper companion uses; no Dora-core doc debt required. Champion order collapses further to `P8-01 → P8-02 → P8-05 → P8-06 → P8-07 → P8-08 → P8-09 → P8-10`.

---

## [RESOLVED] FU-436 — P8-04 crowd-prices governance decision: KEEP / SHRINK / CUT
- **Raised:** 2026-07-02 (P8-05 kickoff — user's own feasibility
  concern: *"i don't think the logistics of sharing/pooling community
  data is feasible for this app. how could it even be possible?"*).
- **Type:** finding + design call (governance, not code).
- **What:** the champion plan's recommended order put P8-04
  (crowd-sourced anonymised price graph) before P8-05, on the theory
  that community baselines make the oracle stronger for new users
  with thin history. Four structural blockers: (a) small-cohort
  re-identification even under anonymisation, (b) cold-start
  chicken/egg with no distribution channel to bootstrap contributor
  volume, (c) weekly Aus catalogue rotation caps the useful
  freshness window, (d) hosted-broker ops role (uptime + moderation
  + abuse detection + DPAs) reintroduces exactly the pattern
  `RECONCILED_FINISHING_PLAN.md §7 Decision 1` retired when the
  scraper was extracted to the private companion.
- **State note:** Resolved 2026-07-02 as **CUT**. Argument trail
  landed as [INV-11](docs/05_investigations/CROWD_PRICES_ASSESSMENT.md).
  Decision recorded in
  [`RECONCILED_FINISHING_PLAN.md §7`](docs/01_charter/RECONCILED_FINISHING_PLAN.md)
  as new Decision 6. Champion sequence in
  [`DASHY_DORA_CHAMPION_PLAN.md`](docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md)
  updated: P8-04 prompt block retired with a CUT banner (body preserved
  as audit trail), Part V order rewritten to
  `P8-01 → P8-02 → P8-03 → P8-05 → P8-06 → P8-07 → P8-08 → P8-09 → P8-10`
  (further collapsed by Decision 7 / FU-453 to drop P8-03),
  Part I "optional crowd" phrasing dropped, P8-06 prompt annotated so
  the "optionally blend crowd baselines" line is dead. Someday-list in
  the reconciled plan split (P8-10 stays, P8-04 moves under Decision 6).
  Buy-verdict proposal §5 hedge replaced with the CUT resolution.
  Grep for `crowd_baseline` / `community_baseline` in `dora_api/` +
  `web_app/src/` returned zero (no code hook to remove). Unblocks
  [FU-438](DORA_FOLLOWUPS.md) (P8-06 wait-until) — now scheduled
  after FU-437 detail-card wiring + P8-05 browser-verify.

## [RESOLVED] FU-435 — `.gitignore` `data/` pattern unanchored → `backup_library.py` never committed
- **Raised:** 2026-07-02 (P8-02 close).
- **Type:** finding (latent build/history bug).
- **What:** an unanchored `.gitignore` `data/` pattern silently ignored new files
  under `dora_api/features/data/`, so `backup_library.py` (FU-342) appeared
  uncommitted.
- **Resolved:** 2026-07-02 — `.gitignore` patterns were root-anchored, and code
  verification confirms `dora_api/features/data/backup_library.py` **is now
  git-tracked** (last touched in commit `37165fc "P8-02 and P8-05"`), along with
  its migration `e5f9c2a8b4d6_20260701_backup_library.py`. The commit gap is
  closed. *Residual:* since the runtime never previously had this code, a backend
  smoke-test of its endpoints is still worth doing before relying on it — but the
  build/history bug itself is fixed.

## [RESOLVED] FU-446 — Doc indexes incomplete: ~23 orphaned docs + DOC_GRAPH gaps
- **Raised:** 2026-07-02 (doc-register audit).
- **Type:** finding.
- **What:** ~15 proposals/impl-plans + ~9 investigations were unreferenced by
  `00_DOCS_INDEX.md` / `00_DOC_GRAPH.md`, which also cited non-existent files.
- **Resolved:** 2026-07-02 — indexes retired (see FU-428). The per-doc register
  now lives inside `PROJECT_STATE.md` and accounts for **all** 107 active docs, so
  there is no separate index to be orphaned from. "Orphaned" is no longer a
  meaningful state.

## [RESOLVED] FU-428 — DOC_GRAPH.md is stale — proposals not indexed
- **Raised:** 2026-07-01 (full-docs audit).
- **Type:** finding (doc drift on the anti-drift spine).
- **What:** `00_DOC_GRAPH.md` indexed only ~25 of 48 proposals and cited 2
  non-existent files; the per-prompt required-reading map had rotted.
- **Resolved:** 2026-07-02 — per user request to reduce doc count. `DOC_GRAPH.md`
  shrunk to a retired stub and `00_DOCS_INDEX.md` deleted; the anti-drift
  "assemble your own required reading" rule now lives directly in `CLAUDE.md` /
  `AGENTS.md`, and `PROJECT_STATE.md`'s register is the authoritative doc map.

## [RESOLVED] FU-195 — Onboarding starter-data: in-page import + groups/locations "some" (trims from C-5.5)
- **Raised:** 2026-06-16 (Onboarding C-5.5)
- **Type:** leftover
- **What:** Two C-5.5 sub-asks were scoped down: (1) **inline import** (L30) — the starter-data step
  still **linked** to `/data/import` rather than embedding the importer on the page (embedding the
  full importer was disproportionate for this build); (2) **groups/locations "some"** (L34) — the
  step offered all/none per catalogue **+ a static preview** (captions listed the default names), and
  the **packs** gave item-level ticking, but there was no individual tick-list for the default
  groups/locations themselves.
- **State note:** Resolved 2026-07-02. Backend `SeedRequest` gained optional
  `group_names: list[str] | None` and `location_paths: list[str] | None` filters
  (`"Zone"` / `"Zone/Child"` path form for the nested locations). Null-or-omitted preserves
  the "seed all defaults" behaviour; provided list narrows to the intersection. Selecting a
  child location auto-creates its parent zone as a silent FK prerequisite (not counted as
  skipped). The wizard's two seed-catalogue cards became `q-expansion-item` blocks with
  tri-state master checkboxes + per-name tick-lists. Inline "Paste rows to bulk-add items"
  expansion parses `Name, Group?, Location?` lines client-side and pushes them into the
  existing `draftItems` queue, so `applyDraft()`'s existing seed-items pipeline handles them
  after the groups/locations seed lands. New unit suite
  [`test_onboarding_seed_filter.py`](tests/test_onboarding_seed_filter.py) (17 tests) pins the
  filter semantics. Full pytest + vue-tsc green; browser-verify checklist appended to
  `DORA_VERIFY.md §Onboarding`.

## [RESOLVED] FU-443 — Action C-19: resolve open decisions + write `IMPL_PLAN_AUTH_SHELL.md`
- **Raised:** 2026-07-02 (C-19 proposal written this session).
- **Type:** deferred job.
- **What:** [`docs/04_proposals/PROPOSAL_AUTH_SHELL.md`](docs/04_proposals/PROPOSAL_AUTH_SHELL.md)
  was design-only. To ship, two things needed to happen in order:
  1. User resolves D1–D10 in §7.
  2. Write `docs/04_proposals/IMPL_PLAN_AUTH_SHELL.md` and execute it.
- **State note:** Resolved 2026-07-02 — user answered D2/D4/D7/D10 with
  the recommended calls (D9 already affirmed earlier); wrote
  `IMPL_PLAN_AUTH_SHELL.md` and executed all seven migration steps in
  one unit. Two new components landed
  ([`AuthShell.vue`](web_app/src/components/AuthShell.vue),
  [`AuthButton.vue`](web_app/src/components/AuthButton.vue)); nine
  pre-auth surfaces migrated (Login, Setup, Splash, index.html
  pre-mount, WelcomeLayout, OnboardingStory glyphs, Verify, Forgot,
  Reset, ConfirmEmailChange). Close-gate greps returned zero; vue-tsc
  clean bar pre-existing FU-434. Blocked FU-440 and FU-441 both
  resolved along with this one. Browser-verify checklist appended to
  `DORA_VERIFY.md §Cross-cutting`. FU-442 (§LOGIN password policy)
  stays open — different work unit.

## [RESOLVED] FU-441 — Naming collision: four aux pre-auth pages define `.auth-shell` locally
- **Raised:** 2026-07-02 (C-19 audit).
- **Type:** finding.
- **What:** `VerifyEmailPage.vue`, `ForgotPasswordPage.vue`,
  `ResetPasswordPage.vue`, `ConfirmEmailChangePage.vue` each declared a
  scoped `.auth-shell` class that rendered a plain centred container on
  `--surface-page`. `PROPOSAL_AUTH_SHELL.md` proposed a new
  `AuthShell.vue` component whose root would collide on class name in
  the DOM.
- **State note:** Resolved 2026-07-02 with the C-19 impl run. New
  component's root class is `.dora-auth-shell` (project-prefixed);
  all four aux pages fold into `AuthShell` and their local
  `.auth-shell` blocks are gone. `git grep -- '\.auth-shell\b'`
  returns zero across `web_app/src/`.

## [RESOLVED] FU-440 — R-003 drift: `SetupAdminPage.vue` verbatim-copies the `--lp-*` colour ladder
- **Raised:** 2026-07-02 (C-19 audit).
- **Type:** finding.
- **What:** [`web_app/src/pages/SetupAdminPage.vue`](web_app/src/pages/SetupAdminPage.vue)
  declared a `.setup-shell` block that copied `LoginPage.vue`'s private
  `--lp-*` ladder verbatim — precisely the R-003 drift the "keep the
  ladder private" call (retired FU-002 / DEC-2) was supposed to
  prevent.
- **State note:** Resolved 2026-07-02 with the C-19 impl run. Both
  copies deleted; the promoted `--auth-shell-*` ladder now lives once
  on `AuthShell.vue` with the DEC-2 rationale physically next to the
  tokens. `git grep -- '--lp-\|--setup-'` returns zero across
  `web_app/src/`.
- **Rule cited:** R-003 (single source of truth).

---

## [RESOLVED] FU-146 — Sweep external GitHub-issues references
- **Raised:** 2026-06-12 (user browser verify of FU-085: "should remove any mention of github issues as the repo is now private").
- **Type:** finding / hygiene.
- **What:** Dora-bot fallback bank, `report_issue` intent + its
  `externalLink`, the `whats_new` "See latest release on GitHub"
  link, `HelpPage` "Report a bug" header button + Help-tab repo
  list + issues list, `AboutSettings` repo + bug-report items,
  and `PageErrorState`'s pre-filled GitHub-issues URL all linked
  to `github.com/BenTalese/DiscountDora` — a now-private repo.
- **State note:** Resolved 2026-06-12 (the actual code changes had
  landed; only the ledger bookkeeping was outstanding — moved from
  the open file 2026-07-01). Replaced the FALLBACK_REPLIES bank +
  `report_issue` intros to drop the GitHub framing; retired the
  externalLink on `fallback` + `report_issue` (Help-nav stays);
  retired the `whats_new` release URL; pulled the four GitHub
  buttons/items from `HelpPage` + `AboutSettings`; retired
  `PageErrorState`'s `reportUrl` + the "Report this" button (the
  `showReport` prop stays so a self-host operator can restore a
  similar surface pointing at their own report sink). The
  `report_issue` intent itself stays — it's a useful "I found a
  bug" affordance — but it now navigates to Help instead of
  pointing at an external tracker.

---

## [RESOLVED] FU-173 — Slot-vocabulary "remap legacy entries" UI — WON'T BUILD
- **Raised:** 2026-06-14 (authoring IMPL_PLAN_MEAL_PLANS — C-2.A scope call).
- **Type:** deferred job → dropped.
- **What:** `PROPOSAL_MEAL_PLANS.md §4 / §11.4` described a one-shot
  "remap legacy/off-vocabulary `MealPlanEntry.slot` strings to the
  user's current slot list" action in settings. Would let a user
  say "everything currently labelled `Snack` → move to
  `Afternoon tea`" as a one-shot cleanup.
- **State note:** Resolved 2026-07-01 as **won't build** (user
  decision). Rationale confirmed in conversation: the current design
  (free-text `slot` string on MealPlanEntry, validated at write-time
  against the current vocab, off-vocab strings render safely in the
  "Other" row per C-2.C) is fine on its own. Auto-rewriting
  historical entries when the vocab changes would silently rewrite
  past plans, which is confusing when reviewing history. The
  admin-driven remap tool is a UI to do the same rewrite manually —
  same downside, more friction. Small enough problem (only bites when
  users rename/delete a slot **and** then look at their old plans)
  that no cleanup UI earns its place.
- **If it ever comes back:** would need a genuine user complaint that
  the "Other" row is annoying enough to warrant the tool. Even then,
  reconsider whether making MealPlanEntry.slot an FK (with a
  RESTRICT-on-delete policy) is a cleaner shape than a one-shot
  remap dialog.

---

## [RESOLVED] FU-345 — App-wide image quality / compression setting
- **Raised:** 2026-06-30 (FU-198 discussion follow-up — user clarified the image-quality knob is app-wide, not backup-specific).
- **Type:** feature (admin setting + pipeline change).
- **What:** Power users accumulate hundreds of stock/recipe/product/
  avatar/receipt/store-logo images at full resolution; disk grows.
  Ship one admin knob (quality + max dimension) that applies at
  upload time via the shared client-side pipeline chokepoint.
- **State note:** Resolved 2026-07-01. Landing:
  - **Schema:** migration
    [`f7a3b8e2c1d5_20260701_image_quality_settings.py`](dora_api/persistence/migrations/versions/f7a3b8e2c1d5_20260701_image_quality_settings.py)
    adds `AppSetting.image_quality` (int 30–100, default 85) and
    `AppSetting.image_max_dimension` (int 512–8192, default 1920).
    Entity + table mapping + get/update DTOs updated to carry both.
  - **Backend surface:** `/api/health` gains an
    `image_policy: {quality, max_dimension}` block so every logged-in
    user's browser can read the install policy without needing
    admin credentials for the `/app-settings` PATCH (which stays
    admin-only). Admin edit → PATCH → next health probe (or explicit
    `refreshImagePolicy()`) picks up the new value.
  - **Frontend pipeline:**
    [`imageService.ts`](web_app/src/services/files/imageService.ts)
    now reads `currentImagePolicy()` on every `processImageFile` call
    instead of hardcoded defaults. New
    [`useImagePolicy`](web_app/src/composables/useImagePolicy.ts)
    composable — module-level state, one probe per session, matches
    the `useScanningEnabled` / `useFeatureFlags` shape (R-003). All
    upload sites automatically pick up the admin's choice — no
    per-surface knobs.
  - **Admin UI:** new "Image compression" card at the bottom of
    Settings → Admin → Data → Backup & restore
    ([`AdminDataBackupRestore.vue`](web_app/src/pages/settings/AdminDataBackupRestore.vue)),
    sibling to Library settings. Slider for quality (30–100, label-
    always so admins see the value); numeric input for max dimension
    (512–8192). Save calls `refreshImagePolicy()` so subsequent
    uploads in the same session pick up the new value without a page
    reload. Caption is explicit that it "Applies when new images are
    uploaded — existing images are unchanged" (per the FU's
    forward-only stance).
- **Deliberately out of scope:**
  - Re-encoding *existing* images to the new quality. Tracked as a
    future FU if users ask; the DB walk + partial-failure story is
    heavier than the forward-only knob.
  - Format migration to WebP. The pipeline still outputs JPEG; the
    knob would just as happily drive WebP quality if that day comes.
- **Standards check:** R-003 (single source: `AppSetting.image_*`,
  read through one composable, applied by one function); R-005 no
  new colours; R-006 kept scope tight (no re-encode; no format
  migration).

## [RESOLVED] FU-344 — Import page UI polish: fix label alignment, use SettingsRow
- **Raised:** 2026-06-30 (FU-198 discussion — user's original feedback on the Import page UX).
- **Type:** UX cleanup.
- **What:** The Import page's Options section stacked `<q-checkbox>`
  elements with raw `<br>` separators. Labels didn't align with
  their checkboxes; horizontal space was underused; the page didn't
  sit flush with the other Settings pages. FU original text also
  imagined a "section picker" as cards-with-checkboxes — turned out
  to be aspirational since the importer only supports one section
  (`stock_items`) today.
- **State note:** Resolved 2026-07-01. Landing:
  - Replaced the Options section in
    [`AdminDataImport.vue`](web_app/src/pages/settings/AdminDataImport.vue)
    with four `SettingsRow` blocks — label + one-line help on the
    left, `q-toggle` on the right. Matches the shape every other
    Settings page uses (R-003); the toggle+label misalignment can't
    happen because the primitive owns the layout.
  - Copy tightened on each row so the caption is genuinely useful
    (e.g. "Rolls the whole import back on any row-level failure. Off
    ⇒ valid rows land; errors are reported row-by-row.").
  - Updated the SettingsPageHeader description to point at the new
    "Download template" button (FU-343) instead of a stale "polish
    tracked as FU-344" self-reference.
- **Deliberately out of scope:** the "cards-with-checkboxes section
  picker" the FU imagined would only make sense once there's a
  second importable section. When that lands, revisit — but no need
  to build a picker for a one-choice picker.

---

## [RESOLVED] FU-343 — Import: generated template sheets from live schema
- **Raised:** 2026-06-30 (FU-198 discussion — user's original feedback on the Import page UX).
- **Type:** feature (small — one endpoint pair + a button).
- **What:** The importer assumed users already had a file in the
  right shape. That's brittle for new users who don't know the
  schema. Ship a downloadable per-section CSV template so users can
  fill in the blanks rather than guess.
- **State note:** Resolved 2026-07-01. Landing (CSV-only per the FU
  discussion; `.xlsx` with dropdown validation deferred until asked):
  - **Backend:** two endpoints in
    [`import_spreadsheet.py`](dora_api/features/data/import_spreadsheet.py):
    `GET /api/data/import/templates` returns the section index
    (label + caption + headers), and
    `GET /api/data/import/templates/<section>.csv` streams a CSV
    with the header row + one illustrative example row. Both
    admin-gated via `require_admin` (matches the rest of the
    import surface).
  - **Source of truth:** headers come straight from `TARGET_FIELDS`
    (the same constant the inspect + commit paths read), so a
    template can never drift from what the importer actually
    accepts. R-003.
  - **Sections today:** just `stock_items` (that's the only shape
    the importer supports). Registry is a tuple so more sections
    slot in without touching the endpoints.
  - **UI:**
    [`AdminDataImport.vue`](web_app/src/pages/settings/AdminDataImport.vue)
    got a "Download template" button in the file-picker card's
    header row. Single-section installs render it as a plain
    button with a tooltip; when a second section lands the same
    slot renders a `q-menu` of choices (already wired).
    Templates load once on mount; download failures notify but
    don't block the manual upload path.
- **Standards check:** R-003 (single source of truth for the
  importer schema — `TARGET_FIELDS`); R-005 no new tokens; R-006
  did NOT bundle FU-344's visual polish (still tracked).
- **Follow-on:** `.xlsx` templates with dropdown validation only if
  asked; [[FU-344]] still open for the section-picker chrome.

---

## [RESOLVED] FU-342 — Backup library (Shape A): persist backups, list/download/delete, retention, custom location
- **Raised:** 2026-06-30 (FU-198 discussion — current download-only flow doesn't scale).
- **Type:** feature (medium-large — schema + 5 endpoints + UI).
- **What:** Replaced the download-only `GET /data/backup` fast-path
  with a real backup library. Generate → store → list → download /
  restore / delete. Every backup persists as a row + a file on disk.
- **State note:** Resolved 2026-07-01. Landing (single pass, per the
  user's build-whole-chunks preference — no separate proposal doc):
  - **Schema:** new
    [`Backup`](dora_api/domain/entities/backup.py) table
    (`id, created_at, created_by_user_id, size_bytes, sections JSON,
    sha256, status, trigger_kind, storage_path`) via alembic migration
    [`e5f9c2a8b4d6_20260701_backup_library.py`](dora_api/persistence/migrations/versions/e5f9c2a8b4d6_20260701_backup_library.py).
    `trigger_kind` is forward-looking for scheduled backups (deferred
    FU); Shape A always writes `'manual'`. FK on
    `created_by_user_id` is SET NULL so removing an admin leaves the
    library trail intact.
  - **Endpoints** (all admin-gated via `require_admin` — FU-341
    plumbing) in
    [`backup_library.py`](dora_api/features/data/backup_library.py):
    `POST /data/backups`,
    `GET /data/backups`,
    `GET /data/backups/<id>/download`,
    `POST /data/backups/<id>/restore`,
    `DELETE /data/backups/<id>`.
  - **Retention:** new AppSetting `backup_retention_count`
    (default 5 — Pi-disk-conscious, not 10). Prunes oldest above cap
    on every create; drops the file too, not just the row.
  - **Storage path:** new AppSetting `backup_storage_path` — blank
    ⇒ `<DATA_DIR>/backups` via new
    [`DORA_CONFIG.get_backups_dir()`](dora_api/infrastructure/configuration_manager.py).
    Non-blank paths validated for absolute-ness + writeability on
    save via a new `_validate_backup_storage_path()` helper on the
    AppSettings update endpoint. Bad paths return 400 with a
    user-facing reason so an admin pointing at a broken NAS mount
    finds out immediately, not on next backup attempt.
  - **Sensitive-data warning:** the Optional sections (`users`,
    `app_settings`, `product_historic_offers`) get a warning banner
    in the create dialog and a warning chip on any library row
    whose stored `sections` list includes them.
  - **External-file restore stays** — the upload → inspect → tree
    → commit flow is unchanged. The library adds a fast-path
    restore-from-saved (skip staging; the handler reads the file
    directly via the existing `RestoreBackupHandler` with an inline
    `backup` document).
  - **Old download-only fast-path retired** —
    `GET /api/data/backup` and
    [`User.last_backup_at`](dora_api/persistence/table_mappings.py)
    both dropped in the same migration (per user's pre-release "no
    real users; clean non-preserving migrations OK" memory). The
    library owns "when was the last backup" via `MAX(created_at)`
    now; the page derives it from the library list.
  - **UI:**
    [`AdminDataBackupRestore.vue`](web_app/src/pages/settings/AdminDataBackupRestore.vue)
    replaces the old "Create backup" card with a library list (rows
    for each persisted backup + per-row Download / Restore / Delete)
    and a "New backup" button opening a section-picker dialog with
    the sensitive-data warning banner. A new Library-settings card
    at the bottom lets the admin edit retention + storage path.
    External-file restore card unchanged.
  - **Tests:**
    [`test_data_router.py`](tests/e2e/dora_api/test_data_router.py)
    refactored — `BACKUP_URL` retired; a
    `_create_backup(sections)` helper POSTs the library create
    endpoint + downloads the file, preserving every existing
    payload-shape assertion. The `last_backup_at` stamping test
    deleted (feature retired).
- **Standards check:**
  - R-003 (single source of truth): `resolve_selected_sections`
    shared between the create endpoint + the existing inspect flow;
    `SqlAlchemyRepository`/`get_or_create_app_setting` used
    consistently.
  - R-005 (theme tokens): no new colours; reused
    `dora-bg-warning-soft` for the sensitive banner.
  - R-006 (scope discipline): scheduled backups deferred to a
    future FU; image-quality knob deferred to [[FU-345]] (already
    tracked); no re-encode logic on the backup path.
- **Follow-on unblocked:** [[FU-345]] (image-quality setting —
  planned Settings → Admin → Data home now available); scheduled
  backups (their own future FU once Shape A beds in).

---

## [RESOLVED] FU-341 — Collapse /data area; relocate Backup + Import under Settings → Admin → Data
- **Raised:** 2026-06-30 (FU-198 discussion — IA cleanup + admin gating).
- **Type:** refactor + security close-out (pairs with FU-198).
- **What:** The `/data` shell had lost every reason to exist by the
  time FU-339 (kill ExportPrint) and FU-340 (relocate Barcodes to
  QR labels under Kitchen setup) landed. Backup + Import were the
  last two surfaces holding the shell up, and both were
  admin-only workflows sitting in the main nav — confusing for
  non-admins, un-gated on the backend.
- **State note:** Resolved 2026-07-01. Two-part landing:
  - **Backend (FU-198 half):** New shared
    [`dora_api/features/auth/admin_gate.py`](dora_api/features/auth/admin_gate.py)
    holds one canonical `require_admin()`. The three ad-hoc copies
    (`users/update_user_as_admin.py`, `audit/get_audit_events.py`,
    and the `app_settings/*` re-imports of the first) now all funnel
    through it (`_require_admin` re-exported from
    `update_user_as_admin` so the `app_settings` importers keep
    working without a big-bang rename). Gate applied to every
    mutating data endpoint that was previously login-only:
    `/data/backup` (GET),
    `/data/backup/inspect` (POST),
    `/data/backup/restore` (POST),
    `/data/uploads/start|chunk|finish|<id>` (POST/DELETE — the whole
    chunked-upload chain gates on every step as defence-in-depth so a
    leaked upload_id doesn't grant writes), and
    `/data/import/spreadsheet/inspect|commit` (POST). Closes
    [[FU-198]].
  - **Frontend (relocate):** Moved
    `web_app/src/pages/data/BackupRestore.vue` →
    `web_app/src/pages/settings/AdminDataBackupRestore.vue` and
    `web_app/src/pages/data/DataImport.vue` →
    `web_app/src/pages/settings/AdminDataImport.vue` (via `git mv` so
    history follows). Wrapped both with `SettingsPageHeader` so their
    chrome (padding, title, description) matches every other Settings
    page. Added routes
    `/settings/admin/data/backup` and
    `/settings/admin/data/import`; both admin-only via the existing
    `/settings/admin/*` guard in
    [`router/index.ts:132`](web_app/src/router/index.ts:132). Added
    a **Data** sub-header under the Admin group in
    [`SettingsShell.vue`](web_app/src/pages/SettingsShell.vue) —
    mirrors the existing "System" grouping. Nav flows through to the
    mobile settings tab strip via the shared `navGroups` def (R-003).
  - **Shell removed:**
    `web_app/src/pages/DataManagement.vue` deleted; the `pages/data/`
    directory removed after its last file left. Every prior child
    path is preserved as a **redirect** so bookmarks / prior email
    deep-links / the retired PWA shortcut land somewhere useful:
    `/data` → `/settings/admin/data/backup`;
    `/data/backup` → `/settings/admin/data/backup`;
    `/data/import` → `/settings/admin/data/import`;
    `/data/barcodes` → `/settings/kitchen-setup/qr-labels`
    (already added by FU-340; kept);
    `/data/export` → `/settings/admin/data/backup` (nearest sibling —
    the page itself is gone). The "Data" main-menu entry in
    [`MainLayout.vue`](web_app/src/layouts/MainLayout.vue) retired
    (admin-only IA belongs under Settings → Admin, not the top nav).
    Onboarding link at
    [`WelcomeWizard.vue:242`](web_app/src/pages/onboarding/WelcomeWizard.vue:242)
    repointed to the new import path.
- **Non-admin behaviour:** Non-admin bookmarks to `/data/*` chain
  through the redirect → `/settings/admin/data/*` → hit the router's
  admin guard → bounce to `/settings/account`. Deliberate: the
  redirects don't grant access, just avoid a 404.
- **Standards check:**
  - R-003 (single source of truth): one `require_admin`; one
    `navGroups` feeding desktop + mobile.
  - R-006 (scope discipline): did NOT do FU-344's Import visual
    polish (still tracked); did NOT extract the Backup/Restore page
    into smaller components (still 830 lines but internally
    coherent). Kept the relocate mechanical.
- **Follow-on unblocked:** FU-342 (backup library — needs the admin
  gate + settings page in place), FU-343 (import templates — same),
  FU-344 (import UI polish — same page shell now available), FU-345
  (image-quality setting — planned to live in Settings → Admin →
  Data).

---

## [RESOLVED] FU-198 — DB restore + chunked uploads not admin-gated; no shared @require_admin
- **Raised:** 2026-06-16 (senior/tech-lead review)
- **Type:** finding (security, HIGH)
- **What:** `data/restore_backup.py`, the `uploads.py` chunk chain,
  backup export, backup inspect, and import inspect/commit all
  required only a logged-in session — restore inserts arbitrary
  rows across every table. Root cause: no shared admin gate; three
  ad-hoc copies of `_require_admin` (`users/update_user_as_admin.py`,
  `audit/get_audit_events.py`, and `app_settings/*` re-imports).
- **State note:** Resolved 2026-07-01 as part of [[FU-341]]. New
  shared
  [`dora_api/features/auth/admin_gate.py`](dora_api/features/auth/admin_gate.py)
  holds one `require_admin()`; every previously-ungated data
  endpoint now calls it (backup export, inspect, restore; the four
  chunked-upload endpoints; import inspect + commit). Three prior
  ad-hoc copies point at the shared module (`_require_admin`
  re-exported for callers still importing from the old location).

---

## [RESOLVED] FU-340 — Replace /data/barcodes with a "QR labels" page under Settings → Kitchen setup; drop the Scan tab
- **Raised:** 2026-06-30 (FU-198 discussion — confirmed in follow-up).
- **Type:** IA refactor + dead-code removal.
- **What:** The old `/data/barcodes` page held two tabs: a
  duplicative Scan tab (every scan-needing surface already has its
  own Scan button) and a genuinely useful Print QR labels workflow.
  Barcode registration lives on the stock item detail page, not on
  a central management page.
- **State note:** Resolved 2026-07-01. New page
  [`web_app/src/pages/settings/QrLabels.vue`](web_app/src/pages/settings/QrLabels.vue)
  under `/settings/kitchen-setup/qr-labels` owns the Print labels
  surface only. Sidebar entry added to Kitchen setup, hidden when
  the install-wide `scanning_enabled` flag is off (matches the gate
  the page itself enforces). Old `BarcodesQR.vue` deleted;
  `/data/barcodes` now redirects to the new settings page so stale
  bookmarks and the retired PWA shortcut don't 404 (FU-341 will
  drop the redirect along with the `/data` shell). Entry removed
  from [`DataManagement.vue`](web_app/src/pages/DataManagement.vue)
  (which now surfaces only Backup + Import). Retired the "Scan a
  barcode" PWA shortcut in
  [`quasar.config.ts`](web_app/quasar.config.ts) — it pointed at
  the retired Scan tab; a dedicated scan launcher can land later on
  a stable surface if wanted. Stale barcode-management comment in
  [`StockItemDetailPage.vue:29`](web_app/src/pages/StockItemDetailPage.vue:29)
  updated to drop the "Data → Barcodes" pointer. New
  [`ICONS.qr_code`](web_app/src/style/icons.ts) added (mdi-qrcode)
  for the nav entry — the DataManagement.vue entry had been using a
  raw material-icon string in violation of R-005.
- **Unblocks:** [[FU-341]] (retire the `/data` shell). Both its
  prerequisites (FU-339 + FU-340) are now resolved.

---

## [RESOLVED] FU-339 — Kill the Export & Print page; rely on in-context Print/CSV affordances
- **Raised:** 2026-06-30 (FU-198 discussion — "I print where I need to, I don't need a central print management area").
- **Type:** dead-code removal + IA cleanup.
- **What:** The central `/data/export` page duplicated every
  in-context export affordance across the app. Every printable
  surface (stock overview, recipes, shopping lists, meal plans)
  already carries its own Print/CSV action.
- **State note:** Resolved 2026-07-01 (paired with [[FU-338]] which
  closed the meal-plan Print gap earlier the same day, so no window
  existed where meal-plan print was unreachable). Deleted
  `web_app/src/pages/data/ExportPrint.vue` (~325 lines); removed the
  `export` child route from
  [`routes.ts`](web_app/src/router/routes.ts); removed the
  "Export & print" section from
  [`DataManagement.vue`](web_app/src/pages/DataManagement.vue) so
  the shell no longer advertises a dead destination. The four
  export composables (`useShoppingListExport`, `useRecipeExport`,
  `useMealPlanExport`, `useStockOverviewExport`) stay — every
  in-context caller still uses them. Backend API endpoints
  unchanged (they power the in-context callers). Stale comments
  referencing the retired page tidied in
  [`RecipeDetailPage.vue`](web_app/src/pages/RecipeDetailPage.vue)
  and
  [`downloadHelpers.ts`](web_app/src/services/files/downloadHelpers.ts).
  Also unblocks [[FU-341]]'s shell-collapse (one fewer child route
  to relocate). Historical mentions in worklog/changelog/audit docs
  and the legacy prompt-plan under `docs/06_legacy_prompt_plans/` +
  `docs/00_original_spec/` deliberately left as-is — they're
  trail-of-history, not runtime.

---

## [RESOLVED] FU-338 — Add in-context Print action to meal-plan surfaces
- **Raised:** 2026-06-30 (FU-198 discussion — pre-req to killing the central Print page).
- **Type:** small UX gap.
- **What:** Meal plans was the only printable surface reachable
  solely from the central
  [`ExportPrint.vue`](web_app/src/pages/data/ExportPrint.vue). Every
  other surface (stock overview, recipes, shopping lists) already
  carried an in-context Print action; the Board page did not.
- **State note:** Resolved 2026-07-01. Print buttons added to
  [`MealPlansBoardPage.vue`](web_app/src/pages/MealPlansBoardPage.vue)
  in both the desktop top strip (icon-button next to Templates) and
  the mobile week-nav header (via a new `print` emit on
  [`MealPlanMobileFocus.vue`](web_app/src/components/MealPlanMobileFocus.vue)).
  [`MealPlansOverview.vue`](web_app/src/pages/MealPlansOverview.vue)
  already had the action (line 98–105). Both wire to
  `planner.printFocusedWeek` → the existing
  [`useMealPlanExport`](web_app/src/composables/useMealPlanExport.ts)
  composable — no new export path, no duplication (R-003). Now
  clears the way for [[FU-339]] to delete the central
  `/data/export` page without stranding meal-plan print.

---

## [RESOLVED] FU-197 — CSRF absent + email-change needs no password proof (account-takeover chain)
- **Raised:** 2026-06-16 (senior/tech-lead review; confirms prior-art A.1/A.2 in
  `docs/05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md`)
- **Type:** finding (security, HIGH — combine into account-takeover chain)
- **What:** No CSRF token / Origin check on any mutation (`app.py` `SameSite=Lax`;
  `middleware.py` checked only session presence). `email_flows.py:request_email_change`
  required no `current_password`, unlike `change_password.py`. And the SPA's
  Settings → Email "Save" hit `PATCH /auth/me` with `{"email": …}`, which the
  backend silently accepted with no verification flow at all — broader than
  the original finding noted.
- **State note 2026-06-30:** **Fixed** via three coordinated changes plus full
  CSRF defence:
  1. **`UpdateMeRequest.email` field removed** (`dora_api/features/auth/update_me.py`).
     With `extra="forbid"`, any `PATCH /auth/me` carrying `email` now 400s, closing
     the unverified-write path the SPA was actually using.
  2. **`ChangeEmailRequest` now requires `current_password`** + the handler
     verifies it via `check_password_hash` before issuing a token, and sends a
     "change requested" notice to the **old** address via the new
     `email_change_notice.html` template **before** the confirmation email to the
     new one (`dora_api/features/auth/email_flows.py`). Audit emits
     `auth.email_change.requested` (success) and `auth.email_change.password_failed`
     (wrong-password warn).
  3. **Double-submit CSRF defence** (`dora_api/infrastructure/csrf.py` + the new
     middleware hooks). Every API response that comes in without the
     `dora_csrf` cookie gets one minted in `after_app_request` (non-HttpOnly so
     the SPA can read it, SameSite=Lax, Secure when `SESSION_COOKIE_SECURE`).
     Every mutating call (POST/PATCH/PUT/DELETE) under `/api/*` on a
     non-public, non-bearer endpoint must carry an `X-CSRF-Token` header whose
     value `hmac.compare_digest`-matches the cookie or it 403s. Public
     endpoints (login/register/verify/reset/forgot/bootstrap) are exempt so a
     cold client can authenticate; the bearer-auth `submit_ingestion_batch`
     endpoint is exempt because Bearer-auth isn't replayable CSRF-style. Dev-only
     `DORA_CSRF_DISABLED=1` env escape hatch refuses to weaken production.
  4. **SPA side:** `axiosHttpClient.ts` reads the cookie and attaches the header
     on every mutating request automatically. `AccountSettings.vue` rebuilt the
     Email row around the verified flow: current-password input + "Send
     confirmation" button + explanatory description that the change only takes
     effect after clicking the link in the new inbox. `requestEmailChangeAsync`
     in the api service + `authStore` carry the new shape
     `(newEmail, currentPassword) → Promise<void>`.
  5. **Tests:** new e2e coverage in `test_auth_flows.py` for `PATCH /me` 400
     when `email` is sent, the password-gating behaviour of the change-email
     flow (400 missing / 422 wrong / 204 happy), and the CSRF 403 when the
     header is absent. Test conftest mirrors the axios interceptor by auto-
     attaching the header from the test client's cookie jar so the rest of the
     suite stays transparent. Alerts-digest suite migrated from `PATCH /auth/me
     {email}` to a repo-level `_set_seed_user_email` helper since the API path
     is now correctly closed.
  6. **CORS allow-list extended** in `startup.py` for `X-CSRF-Token`.
  `npx vue-tsc --noEmit` clean, eslint clean, e2e suite returns the same 3
  pre-existing failures as the baseline (no new regressions).
- **Confirm in a running app:** see `DORA_VERIFY.md` — new entries cover the
  full verified email-change UX, the old-address heads-up email, the
  `PATCH /me {email}` 400 rejection, and the CSRF cookie/header pairing.

## [RESOLVED] FU-228 — Phase E rename test rot: ~53 tests still use `merchant` / `purchased_merchant_id`
- **Raised:** 2026-06-22 (FU-227 chunk 1 — surfaced when running full pytest).
- **Type:** finding.
- **What:** the Phase E `merchant → store` rename missed several test files. 54
  tests failed at chunk-6 baseline with `unexpected keyword argument
  'purchased_merchant_id'` / `'merchant' Extra inputs are not permitted` (Pydantic
  `extra="forbid"` on the renamed models). Spread across `test_merchant_router` (16),
  `test_product_router` (18), `test_shopping_list_totals` (8), `test_ingest_batch` (6),
  `test_ingestion_store_mappings` (4), `test_preferred_buys` (2).
- **State note:** 2026-06-30 — swept across multiple sessions, never had its
  bookkeeping flipped. Verified clean today by grepping the entire `tests/` tree:
  - `purchased_merchant_id` → 0 hits
  - `merchant=` kwarg → 0 hits
  - `'merchant':` / `"merchant":` dict keys → 0 hits
  - `test_merchant_router.py` — file removed, replaced by `test_store_router.py`
  - All five other named files are clean
  The only remaining `merchant` occurrences in tests are `merchant_stockcode`
  (deliberate FU-189 carve-out — producer's SKU, kept on the Product model; see
  `dora_api/domain/entities/product.py:20`) and two cosmetic docstring references
  to "FU-190 — unknown merchant quarantines" in `test_ingest_batch.py` (historical
  finding name; the actual test bodies post `"store": "MysteryStore"`, the new
  field). None of those will produce a test failure. The two non-test references
  to `purchased_merchant_id` live in `dora_api/persistence/migrations/versions/
  a3e9f6c2d8b4_20260618_rename_merchant_to_store.py` — that's the rename
  migration's upgrade/downgrade SQL, which has to reference both names by
  definition. **Browser/test verify still pending on the user's Python-equipped
  env** — needs a clean `pytest tests/` run to confirm zero rename-related
  failures remain.

---

## [RESOLVED] FU-200 — Admin bootstrap is a fiction: first registrant becomes self-verified admin
- **Raised:** 2026-06-16 (senior/tech-lead review)
- **Type:** finding (security, HIGH)
- **What:** `register_user.py:159` `is_first_user = repo.get(User).count() == 0` → `:166-167`
  `is_admin=is_first_user, email_verified=is_first_user`. On a fresh public deploy whoever hits
  `/register` first becomes a self-verified admin. Masked by a false assurance: `profile.py:72` listed
  `ADMIN_BOOTSTRAP_EMAIL` as production-required, but it was **never read** anywhere else.
- **State note:** 2026-06-30 — closed by splitting bootstrap into its own single-use surface, both API
  and SPA. New `POST /api/auth/bootstrap-admin` (`dora_api/features/auth/bootstrap_admin.py`) is the
  *only* path that grants admin via self-registration; it 410s the moment any User row exists,
  re-checks inside the same transaction (race-safety guard), and refuses unless the submitted email
  matches `ADMIN_BOOTSTRAP_EMAIL` when that env var is set (otherwise falls back to "first POST wins"
  for dev). A companion `GET /api/auth/bootstrap-required` returns `{required: bool}` (single boolean,
  never the user count). `RegisterUserHandler` now hard-sets `is_admin=False`/`email_verified=False`
  regardless of count, and returns a 409 *"Setup required."* problem+json when the DB is empty so
  direct API callers are pointed at the bootstrap endpoint. SPA side: new `/setup` route +
  `SetupAdminPage.vue` with a one-time-setup badge and distinct copy; `authStore.runBootstrap`
  now probes `/bootstrap-required` first and parks `currentUser` at `null` when true; router guard
  funnels fresh installs to `/setup` and blocks `/setup` once setup completes. Middleware allow-list
  gained `bootstrap_required` + `bootstrap_admin`. Tests added in
  `tests/e2e/dora_api/test_auth_flows.py`: `test__register__never_grants_admin`,
  `test__bootstrap_required__false_when_users_exist`,
  `test__bootstrap_admin__rejects_when_users_exist`, `test__bootstrap_admin__rejects_weak_password`.
  Fresh-DB success-path browser verification added to `DORA_VERIFY.md`. The dead-var smell on
  `ADMIN_BOOTSTRAP_EMAIL` is gone — the bootstrap endpoint reads it and enforces it.

---

## [RESOLVED] FU-189a — `create_product` still auto-creates a Store when the name is unknown
- **Raised:** 2026-06-18 (Phase E rename)
- **Type:** finding — known carve-out
- **What:** `dora_api/features/products/create_product.py` retained the
  legacy auto-create-when-missing behaviour for `Store` while the strict
  no-auto-create rule was enforced only on the ingestion side (FU-190).
- **State note:** 2026-06-30 — tightened manual product-add to match the
  ingest contract. `CreateProductHandler.handle` now looks up the named
  Store (case-insensitive trimmed match, mirroring `CreateStoreHandler`'s
  duplicate-detection semantics) and returns `store_not_found=True` if
  absent; the route converts that to a 422 `business_rule_violation` with
  copy *"Store 'X' does not exist. Create it in Settings → Stores first."*
  Test suite updates: `tests/e2e/dora_api/test_product_router.py` gained a
  module-scoped autouse fixture seeding `Woolworths` + `ReuseMerchant`
  (the names the existing tests POST against) plus a new
  `UnknownStoreName__IsBusinessRuleViolation` test asserting the rejection
  shape. `tests/e2e/dora_api/test_spend_by_store.py` was updated to create
  its `FU229Store-…` store explicitly before posting the product (was
  relying on the auto-spawn). Comment on `create_product.py:32` updated
  (auto-spawn lore replaced by explicit-create note). **Pytest not run**
  (same standing posture as FU-156 / FU-189c — only the MS Store Python
  aliases are on PATH on this dev box; the suite runs cleanly in CI / a
  dev box with a real Python). The remaining SPA work — a store *picker*
  on the (currently non-existent) manual product-create UI — naturally
  falls out when that UI gets built; today nothing in the SPA calls
  `productApiService.createAsync`, so there's no UX regression to track.

## [RESOLVED] FU-189 — Rename Merchants → Stores, add management page + user-uploaded logos
- **Raised:** 2026-06-15 (simple-mode brainstorm round 2)
- **Type:** refactor + small feature
- **What:** Three coupled changes — (1) entity + UI rename `Merchant` →
  `Store` app-wide, (2) single user-curated Stores management page in
  settings (no prefilled, no auto-create, edit/disable/delete with
  referential safety), (3) per-store image upload reusing existing
  image-upload infra with hash-swatch fallback. Plus `StockItem.usual_store_id`
  rider for shopping-list grouping.
- **Why deferred (historical):** had to wait on FU-186 to first decommission
  the `merchant_api` companion from this repo so "merchant" only meant the
  entity — otherwise a blind rename of ~550 refs corrupts the companion wiring.
- **State note:** 2026-06-30 — bookkeeping flip only; all four deliverables
  landed on 2026-06-18 as "Phase E rename" (the work-unit that also produced
  FU-189b/c, already resolved). Current tree:
  - Entity renamed: `dora_api/domain/entities/store.py` exists; `merchant.py` gone.
  - Stores management page: `web_app/src/pages/settings/StoresSettings.vue`.
  - Per-store image upload: `web_app/src/components/StoreLogo.vue` with the
    hash-swatch + initial fallback from `ProductSearchCard`.
  - `StockItem.usual_store_id` field present at `dora_api/domain/entities/stock_item.py:32`.
  - No `merchant_api` references in `dora_api/` or `web_app/src/` — only three
    historical-context comments still mention the old name (in
    `onboarding/onboarding.py:84`, `stock_item.py:49-50`, `store.py:8` —
    docstring breadcrumbs, intentional).
  The stale "Resequenced to LAST — blocked on FU-186" header on the open
  entry was misleading: FU-186 did land (companion lives at `../dora-companion`,
  `merchant_api` no longer in this repo). The remaining open carve-out is
  **FU-189a** (`create_product.py` still auto-creates a Store on unknown name) —
  intentionally left open, paired with FU-190.

## [RESOLVED] FU-177 — Pre-existing ESLint errors block `npm run build`
- **Raised:** 2026-06-14 (surfaced by C-2.A adversarial review)
- **Type:** finding (pre-existing debt)
- **What:** 5 ESLint errors existed on the tree, unrelated to C-2.A:
  `useFeatureFlags.ts:31`, `useStockFilters.ts:75` + `:92`,
  `RecipeDetailPage.vue` (~`:1117`), `AboutSettings.vue:82`. `npm run build`
  runs ESLint first and aborted before reaching `vue-tsc`.
- **Resolved:** 2026-06-30 — the original 5 sites are clean. A spot-check
  found 3 *new* lint errors (`public/push-sw.js:17` unused arg;
  `StockItemRow.vue:644` and `ShoppingListDetail.vue:1322`
  `no-misused-promises` on async action/onDrop handlers). Fixed all three:
  renamed `event` → `_event`; wrapped both async handlers in
  `void (async () => { ... })()` IIFEs matching the existing pattern at
  `ShoppingListDetail.vue:2400`. `npx eslint .` now passes cleanly.

## [RESOLVED] FU-334 — Attach receipt photo(s) to a shopping list (record-keeping)
- **Raised:** 2026-06-30 (ad-hoc user ask)
- **Type:** deferred job (new feature, scoped + planned)
- **What:** Allow the user to attach one or more real receipt photos to a
  `shopping` or `done` shopping list as a record. View-only after attach —
  no OCR, no parsing, no auto-matching to lines. Multi-photo, no captions.
  Mirror the `RecipeStepImage` storage shape (data-URL bytes + dedicated
  bytes endpoint) and reuse the centralised `processImageFile` upload
  pipeline (R-003).
- **Why deferred:** Not a Phase-1 blocker; pure additive record-keeping. The
  Phase-2 ingestion / OCR path is a separate concern and must not get
  confused with this. Slotting now would steal time from the active shop
  loop / assistant work.
- **Plan:** [`docs/04_proposals/IMPL_PLAN_SHOPPING_LIST_RECEIPTS.md`](docs/04_proposals/IMPL_PLAN_SHOPPING_LIST_RECEIPTS.md)
  — decisions locked, backend + frontend chunks scoped (~2 days total).
- **Recommended resolution:** opportunistic, post Phase-1 shopping polish —
  or sooner if the user wants the paper trail before next big shop.
- **State note (2026-06-30):** built end-to-end in one pass (user said
  "let's do it now"). New `ShoppingListAttachment` entity + migration +
  table mapping (LargeBinary blob, deferred); `manage_shopping_list_attachments`
  module with add/delete/bytes endpoints under
  `/api/shopping-lists/<id>/attachments[/<aid>]`; detail DTO gains an
  `attachments[{id, sequence}]` array (server-owned, bytes never inlined);
  e2e suite `test_shopping_list_attachments.py` covers happy path, draft
  rejection, bad payload, multi-attach order, delete, cascade-on-list-delete,
  and survives-finish. SPA Receipts section on `ShoppingListDetail.vue`
  (hidden on draft), thumb strip, BaseDialog lightbox, mobile camera
  capture via `accept="image/*" capture="environment"`, optimistic delete.
  Uses centralised `processImageFile` (R-003). Browser-verify checklist
  added to `DORA_VERIFY.md` under "Shopping lists / Receipt-photo
  attachments". TypeScript clean.

---

## [RESOLVED] FU-175 — Assess a purpose-built "bulk edit the week" meal-plan action
- **Raised:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS review; C-2.E retires MealPlanEditDialog)
- **Type:** follow-up
- **What:** C-2.E deletes `MealPlanEditDialog` — inline servings/slot edit on
  the carousel + implicit create-on-tap cover its jobs. The user wanted a
  *purpose-built* bulk-week action assessed separately (it "may not even need a
  modal"): e.g. select multiple entries and bump servings / reslot / remove in
  one go, or a compact week-table editor.
- **Resolution (2026-06-30):** closed as **no-action** after assessment against
  the shipped carousel UX. Each plausible bulk gesture is either already covered
  or fails the charter check:
  - Bump servings across many chips → per-chip ± menu stays open for rapid
    taps (`MealPlanEntryChip.vue:37-56`); real need is rare.
  - Reslot many entries (the historic "everything became Dinner" pain) →
    **solved by construction in C-2.C** — tap-target picks the slot *before*
    the recipe, so off-slot entries no longer accumulate.
  - Copy a week's shape to another week → covered by **C-2.F templates** (save
    week as template, apply to another week).
  - Wipe a week → existing **"Clear this week"** (C-2.E).
  - Multi-select + batch action → would reintroduce the modality C-2.E just
    deleted (a "select mode" + action bar fights the direct-tap-on-chip flow
    the carousel is built around). Fails Effortless + Anti-creep.
  The single remaining ergonomic gap is a per-day "Clear day" affordance; not
  opening a new FU for it — defer until someone actually asks for it in use.

## [RESOLVED] FU-332 — Per-user "Test" button in AssistantSettings.vue
- **Raised:** 2026-06-29 (FU-153 PR1 close-out — deferred from §7).
- **Type:** UX polish / security design.
- **Resolution (2026-06-29):** shipped same day as PR1 in a PR2 sweep.
  New `POST /api/assistant/probe` endpoint at
  `dora_api/features/assistant/probe_assistant.py`. Threat model
  documented in the module docstring (SSRF surface — gated by per-user
  rate-limit `assistant.probe` at 10/min via the existing
  `infrastructure/auth_helpers.rate_limit`, and an `audit_emit(
  'assistant.probe', payload={provider, target_host, available})` row
  per call). Request body: `{provider, base_url?, model, api_key?}`.
  Key resolution: plaintext from the body wins (lets the user test a
  freshly-typed key); falls back to the saved encrypted blob via
  `decrypt_api_key` so the SPA doesn't have to round-trip the
  masked field every probe. For Ollama, a successful probe also
  returns the detected model list (the SPA shows the count). Frontend:
  `AssistantSettings.vue` renders a "Test connection" button under
  each provider's fields with inline success/failure status; result
  is cleared whenever any field changes so a stale green tick can't
  mislead. **No host allowlist** — household installs legitimately
  probe loopback + LAN URLs (the audit log + rate cap are the
  deliberate trade-off, called out in the module docstring).

---

## [RESOLVED] FU-331 — §7.3 network-topology docs sweep (HelpPage + admin docs)
- **Raised:** 2026-06-29 (FU-153 PR1 close-out — §7.3 deferred).
- **Type:** documentation.
- **Resolution (2026-06-29):** shipped same day as PR1.
  **HelpPage** ("Dora itself" guide group): the existing
  `Set up the AI assistant (admin)` entry rewritten for the new
  per-user shape (provider matrix, Test connection affordance, per-
  account flow); two new entries — *AI mode says "unavailable" — why?*
  (links the §7.2 banner to common causes), *Network topology: who
  reaches the LLM?* (the backend, not the browser; what that means
  for NAS/Pi installs); a fifth, *Admin: install-wide AI master
  switch + API-key encryption*, documents the
  `DORA_LLM_KEY_ENCRYPTION_KEY` env var with a Fernet generator
  one-liner. **README** assistant bullet rewritten end-to-end:
  the per-user pattern, all four providers, the encryption-key
  env var, and the multi-machine network-topology gotcha.
  `AssistantSettings.vue`'s inline blurb kept (the page-local hint
  is still useful at the point of edit; HelpPage carries the
  longer-form material now).
- **Notably NOT done:** `docs/01_charter/RECONCILED_FINISHING_PLAN.md`
  wasn't touched — the only references there are bullet line items
  that point at the proposal file (which is now the canonical
  source). No drift to fix.

---

## [RESOLVED] FU-330 — §7.2 reachability probe + AI-unavailable banner
- **Raised:** 2026-06-29 (FU-153 PR1 close-out — §7.2 deferred).
- **Type:** UX polish.
- **Resolution (2026-06-29):** shipped same day as PR1.
  **Backend**: `_UnavailableClient` (factory sentinel in
  `infrastructure/llm/factory.py`) exposes its `reason` as a public
  property. `GET /api/assistant/status` extended to return
  `{ai_available, reason}` — factory sentinels surface their own
  reason verbatim (config-shape failures: missing provider, missing
  key, encryption unconfigured, master flag off, …); live-probe
  failures fall back to a generic "Your LLM didn't respond. Check
  the URL/model on Settings → Assistant." copy so the banner is
  still useful.
  **Frontend**: `DoraChat.vue` already probed `/assistant/status`
  on chat-panel mount + after a failed `/ask`; the existing
  `refreshAiStatus()` now also captures `reason` + an `aiProbing`
  ref. A new `q-banner` renders at the top of the chat panel —
  between the header and the message scroll area — when
  `currentUser.llm_enabled === true && aiActive === false`. Banner
  carries the reason as a secondary line + a **Retry** affordance
  (re-runs `refreshAiStatus()`) and a quick link to
  **/settings/assistant**. **Plain Basic-mode users
  (`llm_enabled === false`) never see the banner** — Basic isn't a
  failure, it's the valid baseline.
  **Per the proposal:** probe-once-per-open, never on a timer; the
  existing per-request `LlmUnavailable` fallback in
  `AssistantHandler` stays as the safety net for "LLM died
  mid-conversation" (the banner appears on that fall-through too
  because the next `refreshAiStatus()` call after a failed `/ask`
  picks it up).

---

## [RESOLVED] FU-153 — Assistant LLM config: per-user, reachability probe, multi-provider
- **Raised:** 2026-06-12 (user feedback during FU-085 verify).
- **Type:** design / proposal addition → implementation.
- **Resolution (2026-06-29):** §7.1 + §7.4 + §7.6 of
  `docs/04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md`
  implemented in one PR. §7.2 + §7.3 deferred to focused follow-ups
  (FU-330 / FU-331 / FU-332 in the open ledger).
  - **Schema (migration `e5b9d3c7a8f2_20260629_per_user_llm_config`):**
    drop `AppSetting.{llm_enabled,llm_base_url,llm_model}`; add
    `AppSetting.master_llm_enabled` (defence-in-depth kill switch);
    add `User.{llm_enabled, llm_provider, llm_base_url, llm_model,
    llm_api_key_encrypted}` with `llm_provider` as a closed-set
    sentinel (R-010, ALLOWED_LLM_PROVIDERS).
  - **Encryption (`infrastructure/llm/key_encryption.py`):** Fernet
    via the `DORA_LLM_KEY_ENCRYPTION_KEY` env var (R-005 distribution
    posture — env-driven config). `EncryptionUnavailable` /
    `EncryptionFailed` typed exceptions translate to friendly 422
    responses; Ollama saves work without the env var (no key
    needed). API-key column is `deferred()` in the mapping so list
    endpoints never haul bytes per row (same shape as `image`).
  - **Providers:** `openai_client.py`, `anthropic_client.py`,
    `gemini_client.py` as siblings to the existing
    `ollama_client.py`. Each `chat()` normalises its native
    response to the OpenAI-style `{role, content, tool_calls?}`
    shape `ask_assistant._parse_tool_call` already consumes —
    Anthropic flattens its `content[]` `tool_use` blocks, Gemini
    flattens its `parts[].functionCall`. Tool *schemas* are
    converted per-provider too (OpenAI's `{type:'function',
    function:{name,description,parameters}}` → Anthropic's
    `{name,description,input_schema}`, → Gemini's
    `functionDeclarations`).
  - **Factory (`infrastructure/llm/factory.py`):**
    `build_assistant_client(user, master_enabled=...)` dispatches
    on `user.llm_provider`, decrypts the API key on demand, and
    returns an `_UnavailableClient` sentinel whenever any
    prerequisite is missing (master flag off, user opt-out, no
    provider, missing key, encryption unconfigured, decryption
    failure) — same shape as the previous `_build_assistant_client`,
    just per-user. `ask_assistant.py:_build_client_for_current_user`
    reads the Flask session for the current user.
  - **API surface:** `PATCH /auth/me` accepts `llm_enabled`,
    `llm_provider`, `llm_base_url`, `llm_model`, `llm_api_key`
    (write-only, encrypted on save), `clear_llm_api_key`. Cross-
    field validation: enabling AI with a paid provider requires
    a saved API key. `GET /auth/me` returns `has_llm_api_key:
    bool`, never the plaintext. `PATCH /api/app-settings` accepts
    `master_llm_enabled` (admin-only via existing `_require_admin`).
  - **Frontend (`AssistantSettings.vue`):** new sibling to
    MoneySettings / NutritionSettings (R-007: didn't fold into
    PreferencesSettings as the original §7.1 said — that page is
    Appearance-only; the per-user opt-in pattern is one page per
    family). Provider segmented control + conditional fields per
    provider. Save-on-blur (R-020 carve-out). Sidebar entry +
    route added (`/settings/assistant`).
  - **Frontend (`AdminSystemAssistantSettings.vue`):** stripped
    to a single master_llm_enabled toggle + a pointer to where
    per-user config lives. Save-on-change (no draft window,
    matches the other install-wide toggles).
  - **`AuthenticatedUser` DTO (frontend + backend):** five new
    fields (`llm_enabled`, `llm_provider`, `llm_base_url`,
    `llm_model`, `has_llm_api_key`). Type-checks green
    (`vue-tsc --noEmit`).
- **Deferred to follow-ups:** §7.2 probe + banner → FU-330;
  §7.3 docs sweep → FU-331; per-user Test button → FU-332.
- **Pre-release breaking change:** the install-wide
  `AppSetting.llm_*` columns are dropped (no production data to
  preserve per the memory). Existing self-hosters re-enter their
  config per-user on the new page.
- **Operator action required:** to use any paid provider, set
  `DORA_LLM_KEY_ENCRYPTION_KEY` in the API server's environment.
  Generate with: `python -c "from cryptography.fernet import
  Fernet; print(Fernet.generate_key().decode())"`. Ollama works
  without it; the env var is only checked on paid-provider saves.

---

## [RESOLVED] FU-152 — Chat-mode design: tokenise → slot-extract → filter (structural)
- **Raised:** 2026-06-12 (offshoot of FU-150's minimal fix).
- **Type:** design / structural improvement.
- **Resolution (2026-06-29):** folded into the existing assistant
  rework doc rather than kept as a free-standing follow-up.
  `docs/04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` now
  carries a new **§2.2.1 — Rules-router mechanism (tokenise →
  slot-extract → filter)** that owns the four-layer pipeline this FU
  spec'd (vocab-derived triggers, slot extraction, optional intent
  scoring, reply transparency), the synonym-table notes
  ("veggie"/"gf"/"crockpot"), the `web_app/src/composables/
  useChatRouter.ts` placement, and the **why this is paired with the
  LLM-mode work** rationale (both routers want the same slot
  extractor over the same vocab map). §5 sequencing was updated to
  point at §2.2.1 from bullet 4 (the "rules router rebuild" step) and
  to note that step 1 of the mechanism — vocab triggers + whole-
  message tokenisation for `find_recipe` — is the *already-shipped*
  FU-150 minimal fix. **Why the doc-merge, not just leaving the
  FU:** the structural redesign isn't a "leftover deferred job", it's
  the canonical design for one specific layer of the assistant
  rework; keeping it as an FU duplicates a design call between two
  homes and lets the proposal drift from the chosen mechanism. One
  source of truth wins.
- **Forward-pointing follow-ups (none new):** the existing FU-085
  index entry was updated to note that FU-150's structural arm now
  lives in the proposal, not as its own FU. The §7 IMPL-plan
  follow-up (the per-user LLM config work) got a one-line cross-ref
  to §2.2.1 so the next session knows the rules-router rebuild and
  the per-user config work are orthogonal but share the vocab-map
  hydration.

---

## [RESOLVED] FU-150 — Assistant chat-mode doesn't recognise dietary/cuisine queries
- **Raised:** 2026-06-12.
- **Type:** finding / chat-mode bug.
- **Resolution (2026-06-12, formalised 2026-06-29):** the user-visible
  failure mode ("vegetarian recipe" / "asian breakfast" not routing to
  `find_recipe`) was fixed in-session 2026-06-12: trigger list
  broadened to catch bare-noun cases, handler rewritten to **stop
  yanking "the noun after a preposition"** in favour of whole-message
  tokenisation against the user's own vocab (`name + cuisine +
  category + timeOfDay + dietaryTagNames`). Vocab hydrated via the
  extended `RecipeSnapshot` in `DoraChat.vue` from existing Pinia
  stores; vocab preload added to `ensureRecipeData()`. Reply echoes
  the matched tokens via `queryDisplay`. Net effect: "i need a
  vegetarian recipe" routes to `find_recipe` + filters by the
  'vegetarian' tag; "asian breakfast recipe" requires both 'asian'
  (cuisine) + 'breakfast' (timeOfDay) to hit. The known limitations
  of this step 1 (synonyms, two-word vocab, first-match-wins ordering
  bias) are documented in
  `docs/04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` §2.2.1
  — the four-layer redesign that supersedes the minimal fix lives
  there, not as a follow-up FU. Previously marked
  `[RESOLVED-MINIMAL]` with a forward pointer to FU-152; both arms
  now consolidated into the proposal, so the status flips to plain
  `[RESOLVED]`.
- **Browser-verify pending** under FU-085 (item 9 — same verify
  dependency as the rest of the cookbook Wave-C work).

---

## [RESOLVED] FU-229 — reports.py spend-by-store ignores `actual_unit_price` (ladder divergence)
- **Raised:** 2026-06-22 (FU-227 chunk 5 — K2 ladder extract).
- **Type:** finding (behaviour inconsistency).
- **Resolution (2026-06-29):** spend-by-store now honours the
  `actual_unit_price → picked_offer_price` ladder, matching budget /
  waste / assistant / suggestions. Savings deliberately stays
  snapshot-only (RRP − picked, not what you paid) per the FU's
  carve-out.
  - **`dora_api/features/reports/reports.py` `SpendByStoreHandler`:**
    - Added `ShoppingListLine.actual_unit_price` to the SELECT
      projection.
    - Relaxed the WHERE filter from
      `picked_offer_price.isnot(None)` to
      `or_(picked_offer_price.isnot(None), actual_unit_price.isnot(None))`
      — matches budget/waste posture (any line with a captured
      price counts as spend). Kept the
      `selected_product_id.isnot(None)` filter because store
      grouping needs a product.
    - Per-row unwrap: `float(actual if actual is not None else picked)`
      — Python-level expression of the ladder (R-003 chokepoint in
      `_line_price.line_paid_unit_price` is the canonical helper for
      entity objects; this is the FU's explicit carve-out for the
      column-projection path, with an inline comment naming the
      duplication + reason).
    - Added `or_` to the existing `sqlalchemy` import.
    - Behaviour change: a user's till-receipt override now flows into
      spend-by-store totals. Previously invisible.
  - **`dora_api/features/reports/reports.py` `SavingsCapturedHandler`:**
    untouched. `list_price_at_pick − picked_offer_price` is
    snapshot-of-deal accounting; the actual paid price would muddle
    the savings claim.
  - **New regression test:**
    `tests/e2e/dora_api/test_spend_by_store.py` —
    `test__spend_by_store__honours_actual_unit_price_over_picked`.
    Creates a unique store + product (`price_now=10`), adds a line
    selecting that product (snapshots `picked_offer_price=10`),
    PATCHes `actual_unit_price=7` + tick, finishes the list, and
    asserts the spend-by-store row reads `spend=7.0` not `10.0`.
    Isolated per-test data (unique store name) so the dev-seed
    Woolworths/Coles spend doesn't perturb the assertion.
  - **Verification.** New test passes; full suite **537 passed** /
    5 pre-existing failures (the FU-328 set + the
    `test__register_barcode__against_product__lookup_traverses_via_product`
    flake that's order-dependent; both unaffected by this change).
    No new test failures introduced.
- **Pricing-data nuance kept in mind** (per user direction):
  - Savings = snapshot accounting — not "what you paid". Untouched.
  - Spend-by-store = "what did I spend" — ladder applied.
  - Postgres / SQLite portability respected (FU-045 in effect):
    `or_` + Python-level null-coalesce work on both engines; no
    SQL-dialect-specific functions.

## [RESOLVED] FU-210 — Onboarding de-persona: remove persona fork + all product framing
- **Raised:** 2026-06-17 (products-as-overlay pivot).
- **Type:** deferred job (build — a *removal*).
- **Resolution (2026-06-29):** code work was complete on 2026-06-17
  (after a user-directed reversal of an over-deletion); closed now
  under the close-when-only-verify-left policy. Final ship list,
  reflecting the corrected scope:
  - **Persona FORK removed from setup** — `WelcomeWizard.vue` + `onboardingContent.ts`
    lost the persona step, `personaChoice` / `customFlags` /
    `effectiveInstallFlags`, `selectPersona` / `applyPersona`, the
    `AppSettingsApiService` use, and `PERSONA_PRESETS` /
    `INSTALL_FLAG_META` / `InstallFlags`. No install-flag / per-user-pref
    writes happen at onboarding any more. Flow-cards no longer gate
    on persona flags. Fresh installs use `AppSetting` defaults; money
    is its own Settings toggle.
  - **`LOOP_INSIGHT` stripped from `onboardingContent.ts`** — the dim
    "Spend smarter / coming soon" satellite was a P3-Honest violation
    (advertised an unbuilt feature). Dropped the now-unused
    `insight: boolean` field on `PersonaPreview`.
  - **`PERSONA_PREVIEWS` re-labelled to outcome chips** — "Cooking" /
    "Spend" / "Everything" → "Mostly cooking" / "Watching spend" /
    "All of it". Keys unchanged so any saved draft survives.
  - **`OnboardingLoop.vue`** — LOOP_INSIGHT satellite button + its
    `focusedKey === 'insight'` branches + the `lightbulb` mood swap
    + the dead `.loop-insight*` CSS all removed. Persona-preview
    aria-label + chip header re-worded from "Preview for / persona"
    to "What you're here for".
  - **`WelcomeWizard.vue` Finish step** — OnboardingLoop recap
    ("Here's the loop you just set up — tap any stage…") removed;
    the cinematic Story plays the hero loop earlier so the recap was
    repetitive. Confetti + flow-cards kept.
  - **Cinematic Story stage stays as-is** — `NARRATIVE_SCENES` was
    never persona-forked.
  - **Loop-in-Help + main-menu/help-section reordering split to
    [[FU-220]]** (Help-IA design pass; not a removal blocker).
  - Verified: `vue-tsc --noEmit` clean; `npm run lint` clean; full
    pytest 401/401 green.
- **Static-confirmed verify item** (`DORA_VERIFY.md` line 588 —
  "WelcomeWizard.vue admin step does NOT say 'scrape' merchants"):
  grep over `WelcomeWizard.vue` + `onboardingContent.ts` for
  "scrape" / "merchant" returned no matches as of 2026-06-29. That
  bullet can be ticked without a click-through.
- **Outstanding verify** (`DORA_VERIFY.md` → "Onboarding de-persona
  — remaining items — origin FU-210"): the other 7 items are real
  browser-pass checks (hero-loop renders without persona shaping;
  no persona/Customise/products step in setup; defaults applied,
  spend via Settings; draft resume works; Story plays without
  LOOP_INSIGHT; renamed chips read sensibly; Finish step is clean).
  User walks at his own time.

## [RESOLVED] FU-213 — Price substrate: `StockItemPriceObservation` + server cost helper + consumers
- **Raised:** 2026-06-17 (products-as-overlay pivot — carried from the
  now-resolved FU-182).
- **Type:** deferred job (build).
- **Resolution (2026-06-29):** code-complete and backend-green since
  2026-06-17; closed now because browser-verify is the only outstanding
  work, and that lives in `DORA_VERIFY.md` (per the
  close-when-only-verify-left policy). What shipped:
  - `StockItemPriceObservation` entity + table + map; migration
    `b3d5f7a9c2e4` applies clean.
  - Server-owned `get_stock_item_unit_cost_at(stock_item, when)`
    helper in `domain/stock_status.py` (R-003 — one source for the
    per-unit cost rule).
  - CRUD at `/stock-items/{id}/price-observations`; `price_observations`
    + `unit_cost` on the detail DTO.
  - Money-gated "Prices" section on the stock-item detail Overview
    (`useMoneyEnabled()`).
  - Cost-consumer rebase (stock-value report + recipe cost estimate)
    split to [[FU-216]] and resolved 2026-06-29.
  - Tests: `tests/e2e/dora_api/test_price_observations.py` 4/4
    (add → derived `unit_cost=3` on 6/2, latest-wins, delete clears,
    non-positive rejected). `vue-tsc` + `eslint` clean.
  - **Outstanding verify (DORA_VERIFY.md → "Stock-item Prices section
    — origin FU-213"):** log a price observation → derived `unit_cost`
    shows correctly; remove a price observation; section is hidden
    when Money features are off. User walks at his own time.

## [RESOLVED] FU-211 — `PreferredBuy` — everyday free-text "what I buy" on the stock item
- **Raised:** 2026-06-17 (products-as-overlay pivot).
- **Type:** deferred job (build — new feature).
- **Resolution (2026-06-29):** code-complete and backend-green since
  2026-06-17; closed now because browser-verify is the only outstanding
  work, and that lives in `DORA_VERIFY.md`. What shipped:
  - `PreferredBuy(id, stock_item_id FK cascade, label, position,
    created_at)` entity + table + map; migration `a2c4e6f8b1d3`
    applies clean.
  - CRUD at `/stock-items/{id}/preferred-buys` (add / rename / delete
    / reorder); `preferred_buys` on the detail DTO; model + API
    service methods.
  - "Preferred buys" editor on the stock-item detail Overview (add /
    inline rename / up-down reorder / remove via `withBusyReload`).
  - Always-available (NOT gated by products or money); strictly
    separate from `Product` per the "two separate systems" principle.
  - The shopping-list hint (`ShoppingListLine.preferred_buy_id`) was
    split to [[FU-215]] and resolved 2026-06-29.
  - Tests: `tests/e2e/dora_api/test_preferred_buys.py` 5/5
    (add → detail, rename, delete, reorder, blank rejected, cross-item
    scope). `vue-tsc` + `eslint` clean.
  - **Outstanding verify (DORA_VERIFY.md → "PreferredBuy — origin
    FU-211"):** stock-item detail → add / rename / reorder (up-down)
    / remove preferred-buy entries; CASCADE on item delete (preferred
    buys go too). User walks at his own time.

## [RESOLVED] FU-154 — Page-local product/stock collections bypass their stores (R-003 smell, likely widespread)
- **Raised:** 2026-06-12 (during FU-014 image-bug investigation).
- **Type:** finding.
- **Resolution (2026-06-29):** audited every `ref<T[]>` in `pages/`
  per the FU's recommended grep method, cross-referenced against the
  17 Pinia stores, and fixed every store-shadow case.
  - **Audit findings.** Only product had real shadows; three pages
    duplicated `productStore.products`:
    1. `MyProductsPage.vue:598` — the confirmed user-visible bug
       (save on product-search invisible until refresh).
    2. `PriceHistoryPage.vue:259` — `candidates = ref<Product[]>([])`
       populated by direct `productApi.getAllAsync()`.
    3. `ReportsPage.vue:281` — `allProducts = ref<Product[]>([])`,
       same pattern.
    Other `ref<T[]>` matches across `pages/` were intentional
    page-local state (per-page picker options, filter selections,
    bulk-selection sets, dropdown caches) — not shadows of any
    Pinia-owned collection. None of the recipe / stock-item /
    meal-plan stores had page-local shadows.
  - **Fixes.**
    - `MyProductsPage.vue` — added `useProductStore` import,
      replaced local `products = ref<Product[]>([])` with
      `storeToRefs(productStore).products`, swapped
      `productApi.getAllAsync()` → `productStore.getProductsAsync()`
      inside `loadAll`. Bulk-update calls (`productApi.updateAsync`
      in the inactive-marking loop) stay direct + are followed by
      `loadAll()` which now also refreshes the store.
    - `PriceHistoryPage.vue` — same pattern, kept `candidates` as
      the local name (aliased to the store ref via `storeToRefs`)
      so the rest of the page reads unchanged. Dropped the now-
      unused `ProductApiService` import.
    - `ReportsPage.vue` — same pattern; `allProducts` aliased to
      the store ref; `loadProductsCatalogue()` calls
      `productStore.getProductsAsync()` then derives the
      page-local `productOptions` display slice. Dropped the
      `ProductApiService` import.
  - **`productStore.products` initialised to `[]` not `undefined`.**
    The store was declared `ref<Product[]>()` (implicit `undefined`
    until first hydration), which made the aliased refs needlessly
    nullable. One caller (`ShoppingListDetail.vue:2119`) already
    used `?.find` so it stays safe through the change.
  - **Verification.** `npx vue-tsc --noEmit` clean; `npx eslint`
    on the four touched files clean; backend suite unaffected
    (538/541, 3 pre-existing FU-328 failures).
  - **Cross-ref**: ENGINEERING_STANDARDS R-003 (state ownership) —
    one source of truth per domain collection.

## [RESOLVED] FU-143 — Backfill `picked_offer_price` for legacy lines
- **Raised:** 2026-06-12 (State Ownership Chunk 6 impl).
- **Type:** deferred job (optional).
- **Resolution (2026-06-29 — closed as moot, no code change).** User
  asked whether anything was actually owed here pre-release with no
  active users. Audited the FU's premise and the belt-and-braces
  hooks:
  - The FU describes a **one-shot backfill** of pre-existing rows
    matching `selected_product_id IS NOT NULL AND
    picked_offer_price IS NULL`. Pre-release with no users → **zero
    such rows exist**; there is nothing to backfill.
  - The runtime safety net the FU named is intact:
    `manage_shopping_list_lines.py:252-253` — `UpdateLineHandler`
    snapshots on tick when `picked_offer_price` is missing;
    `manage_shopping_list.py:250-251` — finish-list fallback
    snapshots any ticked line that arrives without one. Any future
    "legacy row" accruing across a deployment is drained by those
    hooks on the next interaction.
  - **Decision:** close. If a snapshot-semantics change post-launch
    later requires a real backfill, that's a fresh FU with a known
    row count and a defined migration window — not this one.

## [RESOLVED] FU-133 — Promote generate-target picker into a shared `TargetListPicker`
- **Raised:** 2026-06-12 (Cart Button Chunk 4 impl).
- **Type:** follow-up (R-001 carve-out).
- **Resolution (2026-06-29 — assessed, kept inlined).** User asked
  for a value re-assessment after the meal-planner rebuild rounds.
  Audited every `$q.dialog({type:'radio',...})` site in the SPA — 7
  total: `useMealPlanner.pickGenerateTarget` (the FU's source, now
  moved out of `MealPlansOverview.vue` into the composable),
  `AddToListButton.onInlineProductClick`,
  `AddToListButton` "Add to another", `useStockItemActions`
  cart-shortcut, `StockOverview.pickActiveListId`,
  `ShoppingListDetail` swap-substitute, `ShoppingListDetail`
  move-unticked. **Outcome: don't extract yet.**
  - **FU-133's distinguishing feature (`+ Create new list`) is
    unique** — no other picker offers a "create" branch or carries
    the corresponding tri-state result (`id | null = create |
    undefined = cancelled`). Extracting would force every other
    consumer to opt out of the option.
  - **The other 6 sites are similar-but-not-same**: different
    candidate filters (drafts only / active ∖ on-list / passed-in /
    other active lists), different empty-state behaviour (toast /
    sister dialog / upstream-handled), different OK labels.
    Sharing them would produce a parameter-bag API — exactly the
    R-001 anti-pattern the original carve-out warned against.
  - **No "shape-identical second consumer" appeared** in the
    meal-planner rebuild rounds. The rebuild moved the picker from
    a page into the composable; it didn't spawn a sibling.
  - **Triggers to revisit** (none of which fire today): a 3rd
    "+ Create new" picker; a visual overhaul of the radio dialog
    where touching 7 nearly-identical surfaces becomes the
    cheaper-to-extract-once moment; or a thin `useShoppingListPicker`
    composable that owns *only* the dialog plumbing (cancel/dismiss
    + tri-state) without trying to share filter/empty-state.

## [RESOLVED] FU-194 — Onboarding demo data (L38) — deferred from C-5.5
- **Raised:** 2026-06-16 (Onboarding C-5.5).
- **Type:** deferred job.
- **Resolution (2026-06-29):** built the demo dataset end-to-end on a
  Python-capable box so the FK graph could be verified.
  - **Backend** (`dora_api/features/onboarding/onboarding.py`):
    `POST /api/onboarding/seed-demo` → `SeedDemoHandler.handle()`
    creates one Recipe ("Spaghetti Aglio e Olio") plus the three
    StockItems it needs (RecipeIngredient → StockItem FKs are
    non-nullable, so items go in first). Reuses existing items by
    name (so a user who picked the starter pack "Spaghetti pasta"
    doesn't get a duplicate); creates the rest at the most-stocked
    level. Then a MealPlan anchored on this household-week's Monday
    with one MealPlanEntry (today, Dinner, 2 servings) so the dish
    lands in the dashboard's Next-to-cook card immediately. All
    rows are **plain** — no `is_demo` marking — per the FU's "the
    user deletes like any other entry" rule. Idempotent: a second
    call with the demo recipe already present returns
    `{seeded: false, items_created: 0, recipe_created: false,
    meal_plan_created: false}` so re-finishing never duplicates.
  - **Frontend**: `seedDemoAsync` on `onboardingApiService`;
    `SeedDemoResult` in `models/onboarding.ts`; new `seedDemo:
    boolean` flag on the wizard's `WizardDraft` (default `false`,
    persisted with the rest of the draft via the `...form` spread);
    new card in the seed step ("Add a demo recipe + this-week
    meal plan") with the same `.seed-card` chrome as the
    groups/locations cards. `applyDraft` calls
    `onboardingApi.seedDemoAsync()` *after* `seedItemsAsync` so the
    demo can reuse a starter-pack pantry item by name when the user
    picked one.
  - **Tests**: new `test__onboarding_seed_demo__is_idempotent` in
    `tests/e2e/dora_api/test_onboarding_flags.py` — asserts the
    DTO shape, that two consecutive calls return identical bodies,
    and that exactly one recipe by that name exists afterward.
    Full suite: 537 passed, 4 pre-existing FU-328 failures.
  - **Decisions made**:
    - **No `RecipeCollection`** — the column is nullable
      (`Recipe.recipe_collection: RecipeCollection | None`), so
      the demo doesn't need to fabricate one. Keeps the surface
      area small.
    - **Idempotency by recipe name**, mirroring the
      groups/locations/seed-items endpoints. The whole demo skips
      if "Spaghetti Aglio e Olio" already exists (including dev
      DBs where `seed.py` already ran).
    - **No `is_demo` marker on rows**, per the FU spec. Means we
      can't later "clean up the demo" with a single DELETE — but
      the FU explicitly wanted plain rows, and the alternative
      (marker column + cascade) is the opposite of what the user
      asked for.
    - **Schedule for today, not Wednesday.** The FU and the seed
      example used "Wednesday Dinner", but anchoring on today is
      friendlier when the user finishes onboarding mid-week — the
      entry shows up on the dashboard immediately rather than in
      the future.
  - **COVERAGE_GAPS**: L38 can now flip from gap → covered when
    the doc index is next swept.

## [RESOLVED] FU-187 — Assistant ignores the configurable expiring-soon window (uses the constant default)
- **Raised:** 2026-06-15 (Alerts C-9.2 — threshold threading).
- **Type:** finding / consistency gap.
- **Resolution (2026-06-29):** threaded the `AppSetting`-resolved
  window through the four assistant tool sites that previously read
  the bare `EXPIRING_SOON_WINDOW_DAYS` constant:
  - `search_stock` (`expiring_soon` filter): horizon now uses
    `_resolve_expiring_window(repo)`.
  - `whats_expiring`: `within_days` default falls back to the
    resolved window when the arg is missing (so an admin re-tune is
    honoured for unqualified questions).
  - Pantry summary (urgency buckets near line 1418).
  - Location urgency (`urgent_only` filter near line 1877).
  Added a per-call helper `_resolve_expiring_window(repo)` in
  `tools.py` that wraps
  `effective_expiring_soon_window(AppSetting)` — the same pattern
  the alerts handler + location tree use, so the rule lives in one
  place (R-003). Dropped the now-unused `EXPIRING_SOON_WINDOW_DAYS`
  import and replaced the import-site comment with one describing
  the new state. Backend suite: 537 passed (4 pre-existing
  FU-328 failures, unchanged); the existing
  `test__alerts__expiring_soon_window_threshold_re_derives` still
  passes (the assistant has no direct e2e for expiry-tool wording,
  but the underlying helper is exercised by the alerts path).

## [RESOLVED] FU-298 — Dashboard "Cookable tonight" upgrade (L272: meal-plan-driven + ready/missing)
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 5).
- **Type:** follow-up — was slated as a Phase-5 item.
- **Resolution (2026-06-29):** rebuilt the card per L272.
  **Backend** (`dora_api/features/dashboard/get_dashboard_summary.py`):
  extended `UpcomingMealPlanEntry` with `recipe_id: UUID` (for
  deep-linking) and `missing_count: Optional[int]` (`None` for empty
  recipes, `0` = ready, `>0` = N missing). The handler reuses the
  same `load_recipe_cookability()` map already computed for the
  recipe summary — one query, both consumers (R-003: cookability
  rule in one place; R-007: no extra DB round-trips).
  **Frontend** (`web_app/src/pages/DashboardPage.vue`): replaced the
  client-side `cookableTonight` computed (which filtered every
  cached recipe by `recipe.cookable`) with a `nextToCook` computed
  driven off `summary.meal_plan.upcoming_entries` — deduped by
  `recipe_id` (same recipe planned twice in a week shows once,
  earliest), capped at 3. Each row now renders the relative day +
  slot (e.g. "Tomorrow dinner · serves 4") and a coloured
  `q-badge`: green "Ready", amber "Missing 2", grey "No
  ingredients". Empty state changed to "Nothing planned for the
  next week" with a `/meal-plans` deep link. Card label retitled
  "Next to cook" (clearer about what it shows; the old title
  implied stock-driven). Dropped the no-longer-used `Recipe` type
  import and the `recipes` storeToRefs destructure. New CSS:
  `.dora-cook-row--with-badge` modifier (a 4th `auto` column for
  the badge); restock card unchanged. `vue-tsc` + `eslint` clean.
  **Tests:** the DTO change is additive (existing tests
  assert nothing about `recipe_id` / `missing_count`); full pytest
  suite still 535/540 (the 4 FU-328 pre-existing failures + one
  flake under suite ordering).

## [RESOLVED] FU-297 — Budget card isn't money-gated (consistency with the Money zone)
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 4).
- **Type:** finding (consistency, pre-existing).
- **Resolution (2026-06-29):** added `gate: 'money'` to the budget
  CardDef in `DashboardPage.vue`'s `CARD_DEFS` array, matching
  savings / spend / pantry-value. Budget surfaces are *all*
  dollar-denominated — even the "no target set" body reads "$X.YZ
  spent so far. Set a target" — so the Money-zone gate posture
  applies (ADR-005). Also short-circuited `loadBudget()` on
  `!moneyEnabled.value` (mirrors `loadSavings` / `loadSpendByStore`
  / `loadPantryValue`) so we don't fetch `/api/budget/status` when
  the card can't render. Inline comment in `CARD_DEFS` records the
  reasoning so a future reader doesn't reverse the call without
  reading the FU. No standalone ADR opened — the call is a
  routine application of ADR-005's "dollar surfaces gate on money"
  policy, recorded in code + ledger. `vue-tsc` + `eslint` clean.

## [RESOLVED] FU-294 — Dashboard card reorder: drag-handles (literal DnD) not built
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 2).
- **Type:** follow-up (enhancement).
- **Resolution (2026-06-29):** wired `useDragDropList<CardId>` (the
  shared composable from FU-326 / R-022) into the Cards menu rows.
  - **Mime:** `application/x-dora-dashboard-card` (each list owns
    its mime per the composable contract — drags from this list
    can't land in any other DnD surface).
  - **Drag gate:** `canDragStart: () => !$q.platform.is.mobile`
    so the handle column hides on touch (C13's tap-mandatory
    mobile path stays uncluttered; drag is the desktop power-user
    extra).
  - **Drop constraint:** `canDropOn` rejects cross-zone drops, so
    a card never visually leaves its zone (matches the existing
    tap `canMove` semantics).
  - **Drop effect:** splice-out / splice-in at the target's
    current index, then `persistLayout()` (same persistence path
    the tap reorder uses, so a drag and a tap reorder are
    indistinguishable on the wire).
  - Handle is a `q-item-section avatar` carrying `dora-dnd-handle`
    + the composable's `handleProps`; the `q-item` itself carries
    `dora-dnd-row` + `rowProps` (handle mode per the composable's
    two surface shapes). The existing tap up/down + visibility
    toggle controls stay in place — the drag is purely additive.
  `vue-tsc` + `eslint` clean. **Browser verify still owed**: the
  composable was previously verified across three other DnD
  surfaces (R-022 verify); this one needs a desktop click-through
  to confirm grab → drop reorders within zone, drop-target ring
  lights, cross-zone drop is rejected, and saved order survives
  reload. Logged in `DORA_VERIFY.md`.

## [RESOLVED] FU-289 — `useSpeechOutput.available` ignores Piper when browser has no SpeechSynthesis
- **Raised:** 2026-06-23 (Piper TTS wiring).
- **Type:** finding (minor edge).
- **Resolution (2026-06-29):** added a session-cached
  `probePiperConfigured()` at module scope in
  `web_app/src/composables/useSpeechOutput.ts` that resolves the
  `configured` flag from `GET /api/tts/voices` (one request shared
  across composable instances; cached for the session because
  Piper-configured is install-time server state, not per-request).
  The composable now only fires the probe when
  `'speechSynthesis' in window` is false — the synchronous browser-
  available answer stays the default, so the common case pays nothing
  extra. When the probe resolves true on a SpeechSynthesis-less
  browser, `available.value` flips to true, so the Settings → Voice
  toggle and the chat mute button (`voiceOutputAvailable` in
  `DoraChat.vue`, `VoiceSettings.vue`) appear. Failures (no Piper
  configured, endpoint absent, network error) keep `available`
  unchanged. `npx vue-tsc --noEmit` + `npx eslint` clean.

## [RESOLVED] FU-288 — Three profile-picture e2e tests fail (pre-existing; FU-286 "no Python env" premise is stale)
- **Raised:** 2026-06-23 (found while running the suite for the TTS
  work).
- **Type:** finding.
- **Resolution (2026-06-29):** ran the three named tests directly —
  all **pass**. Confirmed via `git stash` that they pass on clean
  HEAD too, so they were fixed at some point between the FU being
  raised (2026-06-23) and now (likely in one of the recent
  follow-up commits). No code change required for the three named
  tests. **However, a fresh full-suite run on this box turned up
  a *different* set of 4 pre-existing failures** (data_router /
  household_tz_boundaries / product_router / recipe_is_planned) —
  logged as a new finding in `DORA_FOLLOWUPS.md` (FU-328). The
  FU-286 "no Python env" premise remains stale: 540 tests collected,
  4 fail, 536 pass on this machine.

## [RESOLVED] FU-285 — `VocabListEditor` empty-state copy is recipe-specific
- **Raised:** 2026-06-23 (Settings rebuild Phase 3).
- **Type:** leftover (cosmetic copy mismatch).
- **Resolution (2026-06-29):** added an optional `emptyAction` prop to
  `web_app/src/components/settings/VocabListEditor.vue` (defaults to
  the existing `Create one to start tagging recipes.` so the four
  recipe-shaped Recipe* pages are unaffected). Threaded the prop
  through `TaxonomyManagerPage.vue` with a `computed`-driven
  `v-bind` that only forwards when the caller actually set it, so
  `exactOptionalPropertyTypes`'s strict-undefined rule is honoured
  and `withDefaults` keeps owning the fallback. `RecipeMealSlotsSettings.vue`
  now overrides with `empty-action="Create one to schedule meals against."`
  — the wording avoids "tagging" (slots aren't tags) and reads
  naturally for an empty slots page on a brand-new install.
  `vue-tsc` + `eslint` clean.

## [RESOLVED] FU-221 — Migrate remaining unconditional `getXAsync()` onMounted calls to `ensureLoadedAsync()`
- **Raised:** 2026-06-18 (R-016 introduction).
- **Type:** follow-up (R-016 sweep).
- **Resolution (2026-06-29):** swept the five pages flagged in the FU
  for stores that already expose the `ensureLoadedAsync()` helper
  (`stockItemStore`, `stockLevelStore`, `storesStore`, `productStore` —
  per `docs/01_charter/ENGINEERING_STANDARDS.md` R-016 / ADR-011):
  - `web_app/src/pages/RecipeDetailPage.vue` `onMounted` —
    `stockItemStore.getStockItemsAsync()` →
    `stockItemStore.ensureLoadedAsync()`;
    `stockLevelStore.getStockLevelsAsync()` →
    `stockLevelStore.ensureLoadedAsync()`.
  - `web_app/src/pages/RecipesOverview.vue` `onMounted` —
    `stockItemStore.getStockItemsAsync()` → `ensureLoadedAsync()`.
  - `web_app/src/pages/StockItemDetailPage.vue` `onMounted` —
    `stockLevelStore.getStockLevelsAsync()` +
    `stockItemStore.getStockItemsAsync()` → `ensureLoadedAsync()`.
  - `web_app/src/pages/StockOverview.vue` `onMounted` —
    `stockItemStore.getStockItemsAsync()` +
    `stockLevelStore.getStockLevelsAsync()` → `ensureLoadedAsync()`.
  - `web_app/src/pages/MealPlansOverview.vue` — file has since shrunk
    to 507 lines and its current `onMounted` no longer fetches stores
    (only does the A/B planner-view redirect); nothing to migrate.
  Calls into stores that do **not** yet expose the helper
  (`recipeStore.getRecipesAsync`, `recipeStore.getRecipeCollectionsAsync`,
  `shoppingListStore.refreshAsync`, `locationStore.refreshAsync`,
  `recipeVocabStore.getAllAsync`, `mealSlotStore.getMealSlotsAsync`,
  page-local `stockGroupApi.getAllAsync`) were **left alone** per R-007
  scope discipline + the FU's own "once they grow the helper" carve-out
  — extending more stores is a separate sweep.
  `npx vue-tsc --noEmit` clean; `npx eslint` on the four touched pages
  clean.

## [RESOLVED] FU-216 — Rebase cost consumers onto `get_stock_item_unit_cost_at` (FU-213 follow-on)
- **Raised:** 2026-06-17 (FU-213 split).
- **Type:** deferred job (build).
- **Resolution (2026-06-29):** browser-verified the additive
  observation fallback that landed 2026-06-17 (stock-value report's
  `StockValueOverTimeHandler` per-bucket loop and `get_recipes.py`
  `_compute_estimated_cost` per-ingredient — each previously fell
  through to nothing when no linked-product price existed; now picks
  up the latest observation via `get_stock_item_unit_cost_at`).
  Phase A env-verify (2026-06-17) was already GREEN: full suite
  381/381 incl. all report + recipe-cost tests; no fixture pinned old
  totals broke (the fallback only contributes for observation-only
  items, which the fixtures don't trigger). User confirmed live
  numbers on the stock-value report and the recipe cost-estimate card
  read sensibly. Full product-cost unification into the helper is no
  longer required for the user goal — the additive fallback is the
  resolution.

## [RESOLVED] FU-215 — PreferredBuy shopping-list hint (the FU-211 sub-part)
- **Raised:** 2026-06-17 (FU-211 split).
- **Type:** deferred job (build).
- **Resolution (2026-06-29):** browser-verified the per-line hint
  flow that landed 2026-06-17. Stack:
  `ShoppingListLine.preferred_buy_id` (plain UUID, **no FK** per the
  FU-178 batch-mode lesson — dangling ids after a PreferredBuy delete
  are tolerated and just render no hint) + migration `c4e6a8b1d3f5`;
  `preferred_buy_id` + `clear_preferred_buy` on the generic line PATCH;
  the detail serializer bulk-loads each item's PreferredBuy labels onto
  the line DTO; per-line hint dropdown in `ShoppingListDetail.vue`
  (pick/clear, optimistic + rollback). Phase A env-verify (2026-06-17)
  was already GREEN: `tests/e2e/dora_api/test_shopping_line_preferred_buy.py`
  2/2 (set + clear + DTO labels), migration applies clean on the FU-209
  head, `vue-tsc` + `eslint` clean. User confirmed live that picking a
  hint persists across reload and clearing it removes the hint text.

## [RESOLVED] FU-207 — Document VAPID key generation in install docs
- **Raised:** 2026-06-17 (C-9.8 impl).
- **Type:** documentation.
- **Resolution (2026-06-29):** added a "Push notifications (optional,
  VAPID keys)" subsection under § Local dev quick reference in
  `README.md`, clustered with the existing optional-BYO sections. Covers:
  why VAPID is needed (RFC 8292 short note), the
  `python -m py_vapid --gen --applicationServerKey` command, the three
  `DORA_VAPID_*` env vars, the dry-run / disabled-Push-toggle behaviour
  when any is missing (per R-014). The inline docstring in
  `push_sender.py` stays — it's the source of truth the README
  paraphrases.

## [RESOLVED] FU-204 — `UpdateMeCommand` TS type missing `household_headcount` (drift audit)
- **Raised:** 2026-06-17 (C-9.7).
- **Type:** finding / cleanup.
- **Resolution (2026-06-29):** ran the audit. Mapped every Pydantic
  field on `UpdateMeRequest`
  (`dora_api/features/auth/update_me.py:28`) to the matching key on
  `UpdateMeCommand`
  (`web_app/src/services/api/authApiService.ts:26`). Only
  `household_headcount` was missing — the C-9.7 alerts-email triplet
  had landed correctly across all three layers, and no other drift
  surfaced. Added `household_headcount?: number | null` to
  `UpdateMeCommand` with the C-5.4 doc comment.
  `npx vue-tsc --noEmit` passes clean.

## [RESOLVED] FU-203 — `PATCH stock_location_id: null` clear path + regression test
- **Raised:** 2026-06-16 (C-1b.1 backend pass).
- **Type:** finding (bug, likely).
- **Resolution (2026-06-29):** the FK-set fix already shipped at
  `update_stock_item.py:128-139` (both `clear_stock_location` and the
  bare-null branch set `_stock_location_id` directly, mirroring the
  C-1b.1 stock_group shape that motivated the FU). Added the missing
  e2e regression test
  `test__get_stock_item_detail__stock_location_roundtrips_via_patch` in
  `tests/e2e/dora_api/test_stock_item_router.py` (mirrors the existing
  stock_group test): create with location → assert it round-trips on
  detail → PATCH `stock_location_id: null` → assert detail reads null.
  Test passes in 2.07s.

## [RESOLVED] FU-326 — Extract a shared `useDragDropList` composable + affordance stylesheet
- **Raised:** 2026-06-29 (immediately on FU-118 close — three DnD
  surfaces with hand-rolled state had crossed the rule-of-three line).
- **Type:** finding / R-001 evolution.
- **Resolution (2026-06-29):** done same day.
  - **New `web_app/src/composables/useDragDropList.ts`** owns the
    state machine (`draggingId`, `dragOverId` + private `sourceItem`
    lookup so drop can resolve the source even if the array index
    moved between dragstart and drop), the `dragstart` / `dragover` /
    `dragleave` / `drop` listeners, and per-row binding objects.
    Options: `mime` (unique MIME per logical list — convention
    `application/x-dora-<thing>`), `getId(item)` (stable per-row id;
    return null to mark a row non-draggable), `onDrop(source, target)`
    (per-list effect), and optional `canDragStart(item)` (per-row /
    global drag gate, reactively reflected in `draggable=`) and
    `canDropOn(source, target)` (per-pair drop-target predicate;
    defaults to "not the same row"). Returns `bind(item)` → `{
    handleProps, rowProps, rowClass, isDragging, isDropOver }`.
  - **New `web_app/src/css/dnd.scss`** owns the affordance treatment:
    `.dora-dnd-row` (outline reservation + transitions), `--dragging`
    (opacity 0.5), `--drop-over` (`--brand-primary` outline ring),
    and `.dora-dnd-handle` (grab/grabbing cursors + sunken hover).
    Wired into `quasar.config.ts` after `colours.scss` so the
    cascade picks up the theme tokens.
  - **Two row shapes supported.** *Handle mode* (recipe step rows,
    recipe ingredient rows): the small grip icon is the only
    draggable element, so the row body's inline editors stay
    clickable. *Whole-row mode* (shopping-list lines): no inline
    editors on the row, so the user can grab anywhere — spread both
    `handleProps` and `rowProps` on the same `q-item`.
  - **All three existing surfaces refactored:**
    - `RecipeStepsEditor.vue` + `RecipeStepRow.vue` — siblings-only
      preserved via `canDropOn`. Three `defineEmits` events
      (`drag-start` / `drag-end` / `drop-on-row`) gone; per-component
      DnD CSS gone. RecipeStepRow now accepts a single
      `dragBindings: DragDropRowBindings` prop and spreads it.
    - `RecipeDetailPage.vue` ingredient list — drop effect kept its
      "reinsert at target's slot AND copy `section_client_id`"
      semantics. Local drag state + handlers gone (~75 lines);
      per-row affordance CSS gone.
    - `ShoppingListDetail.vue` lines — `canDragStart` gates on the
      existing `canReorder` computed (covers list-done /
      mid-shopping / grouped / bulk-mode states), so the browser's
      drag affordance disappears when reorder isn't allowed. Drop
      effect (optimistic local reorder + API persist + reload on
      failure) preserved. ~70 lines of plumbing gone.
  - **Promoted to R-022 + ADR-018** in
    `docs/01_charter/ENGINEERING_STANDARDS.md`. The R rule names
    the violation signals (top-level `@dragstart` listener with no
    `useDragDropList` import; hand-rolled `--dragging` opacity or
    `--drop-over` outline; raw `application/x-dora-…` MIME outside
    the composable) so the next sweep can find drift in one grep.
- **What's notably absent on purpose:** keyboard-reorder support
  (Tab to handle, Space to pick up, arrows to move) — every existing
  surface omits this and it'd be an accessibility upgrade landed
  once, in the composable, the next time a11y work touches DnD.
  Multi-row drag and off-row drop zones (e.g. "drop into empty
  section") would extend the composable rather than re-roll state.

---

## [RESOLVED] FU-118 — Drag-and-drop for moving ingredients between sections
- **Raised:** 2026-06-12 (Chunk 10 deliberate scope-down — paired with FU-094 steps DnD, now also resolved).
- **Type:** enhancement.
- **Resolution (2026-06-29):** mirrored the FU-094 steps DnD pattern on
  `RecipeDetailPage.vue`'s ingredient list. The drag handle (`drag_indicator`)
  is the only draggable element on the row; the whole row is the drop target.
  Drop semantics differ from steps: dropping ingredient A onto ingredient B
  *reinserts A at B's slot in the flat list AND copies B's
  `section_client_id` to A in the same gesture* — so reorder-within-section
  and move-between-sections collapse into one operation. (Steps used a
  siblings-only rule because of the parent/child step nesting; ingredients
  have no nesting, only the section dimension, so cross-section IS the
  goal.) Empty sections still rely on the per-row Section picker — you
  can't drop onto something that doesn't exist. Drag affordances reuse
  the same CSS shapes as `RecipeStepRow` (grab/grabbing cursors, 0.5
  opacity on the source, `--brand-primary` outline ring on the active
  drop target). The "would-be-cookable" dim history is unrelated — it
  was FU-109 (also closed today). No server changes required.
- **Duplicate-ingredient assessment** (the user asked for this alongside
  the FU close): **same stock item across different sections is a real
  use case and should remain allowed.** Common cookbook patterns —
  "olive oil" in Sauce + Garnish with different quantities/notes, "flour"
  in Cake + Frosting + Dusting — only render correctly as separate rows.
  The data model already supports this freely (no `UniqueConstraint` on
  `(recipe_id, stock_item_id)` or `(recipe_id, section_id, stock_item_id)`
  in `persistence/table_mappings.py:607-622`; create + update handlers
  accept duplicates without dedup). Downstream consumers that *want* a
  unique view already dedup on `stock_item_id`: cookability calc
  (`RecipeCard.vue:173` Set), shopping-list picker
  (`RecipeIngredientPickerDialog.vue:187-194` `Map<stock_item_id>`,
  collapsing optional/required across occurrences correctly), the
  ingredient-filter set added in the FU-109 close-out, and
  `RecipesOverview.vue:800`. Same-section duplicates are a different
  question — they're almost always a data-entry mistake ("3 tbsp oil,
  divided" is the standard cookbook idiom, not two rows). But the cost
  of *enforcing* uniqueness (UX friction; one-off legit splits like
  "1 tbsp to fry / 1 tbsp to drizzle"; legacy data) outweighs the
  benefit (the user can see two identical rows on the page and merge
  them themselves). **Decision: don't enforce uniqueness at any level.**
  Status quo wins. If the user later finds same-section duplicates
  genuinely confusing, the cheapest reversible step would be an inline
  "Duplicate of row N" caption on the matching row — pure client-side
  hint, no schema change — but it's not worth doing pre-emptively.

---

## [RESOLVED] FU-109 — Decide whether to re-add the RecipeCard "would-be-cookable" dim
- **Raised:** 2026-06-10 (FU-083 follow-up; user wanted a real decision later).
- **Type:** open product / UX decision.
- **Resolution (2026-06-29):** user picked **option 1 — keep the dim
  removed everywhere.** The "Missing N ingredients" copy on the card face
  is the single signal for "this isn't cookable yet"; no legend, no
  opacity. The now-unused `highlightStockItemIds` prop on `RecipeCard.vue`
  was dropped (along with its only binding on `StockItemDetailPage.vue`'s
  Recipes-using-this tab). Same turn the user asked for a new affordance
  on those cards — a filter icon that jumps back to Stock Overview
  pre-filtered to the recipe's ingredient set (deep-link
  `/stock?recipe=<id>` → chip "Ingredients of: <recipe>"); that piece
  ships in the same commit, not as a follow-up.

---

## [RESOLVED] FU-174 — App-wide datetime / timezone correctness sweep (household tz)
- **Raised:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS C-2.K review).
- **Type:** deferred job (large).
- **Resolution (2026-06-29):** swept every `date.today()` in feature
  code to `household_today(repository)`. 15 server sites + 1 naive
  `datetime.now()` migrated; 2 schema columns realigned; one Alembic
  migration written. The household-tz rule promoted to **R-021**
  + **ADR-016** in `docs/01_charter/ENGINEERING_STANDARDS.md`
  (the FU's explicit ask: "Promote the household-tz date rule into
  an ADR + a new R-0NN").
- **Server sweeps** (each handler now anchors `today` on the
  configured household timezone — F29-class bugs closed):
  - `features/alerts/get_alerts.py` — expiry math + stocktake +
    forward-looking nudges all share one household-tz `today`.
  - `features/dashboard/get_dashboard_summary.py` — the "next 7
    days" meal-plan window.
  - `features/assistant/tools.py` — 9 sites:
    `search_stock` (expiring filter), `whats_expiring`,
    `pantry_health`, `meal_plan_for_date`, `where_is_this`
    (urgency), `_resolve_month` (fallback), `purchase_price_stats`
    (days-since-last-purchase).
  - `features/waste/waste.py` — rescue horizon.
  - `features/budget/budget.py` — period bounds (status + history).
  - `features/locations/attention.py` — `reasons_for_item` /
    `reasons_for_items` now require `today: date` (no default
    fallback). Callers `features/locations/get_location_tree.py`
    and `features/stock_items/get_stock_item_detail.py` updated
    to pass `household_today(self.repository)`.
  - `features/recipes/get_recipes.py` — at-risk-ingredient horizon.
  - `features/suggestions/generators.py` — use-soon + likely-due
    horizons (2 sites).
  - `features/alerts/act_on_alert.py` — "extend expiry by 7" base.
  - `features/assistant/confirm_actions.py` — push-expiry fallback
    base.
  - `features/stock_items/update_stock_item.py` — `opened_on`
    auto-stamp.
  - `features/stock_items/create_stock_item.py` — `opened_on`
    auto-stamp + a naive `datetime.now()` for
    `stock_level_last_updated` flipped to `datetime.now(UTC)`.
  - `features/data/export_shared.py` — `export_filename`
    timestamp now follows the household calendar day.
  - `features/recipes/cook_recipe.py` — `last_made_on` write
    follows the household calendar (paired with the schema
    change below).
- **Documented carve-out:**
  `domain/entities/shopping_list.py:format_list_date` keeps its
  server-local fallback (called from `ShoppingList.display_name`,
  a `@property` with no repository access). Pure display formatter,
  only affects whether a year is appended in the rendered label.
  Worst case: a once-a-year, hours-long boundary edge case. Comment
  names the carve-out and the rule.
- **Schema cleanup** (migration `d2f7a9c4b1e8`):
  - `Recipe.last_made_on`: `DateTime(timezone=True)` → `Date`.
    Always semantically a calendar day; the time portion was
    meaningless. Entity / DTO / call-site types lifted to `date`;
    `cook_recipe.py` now writes `household_today(...)` not
    `datetime.now(UTC)`; `get_recipes._stale()` drops the
    obsolete `.date()` cast.
  - `User.onboarding_completed_at`: `DateTime` →
    `DateTime(timezone=True)`. Aligns with every other wall-clock
    column. Stored values were already naive UTC; the flag makes
    the schema match reality.
  - Migration is also the **merge** for the two then-open heads
    (`b7e2d9a4c1f5` + `c4a8e2b9d7f5`, both 2026-06-28).
- **Client annotation:** `localTodayIso()` in
  `web_app/src/helpers/weekDates.ts` and its use in
  `useMealPlanner.ts:74` now carry inline comments naming
  R-021 — the function is a display-only pre-load fallback for
  the very first paint; the server's household `today` is
  authoritative the moment it arrives. State / persistence /
  payload code never goes through this fallback.
- **Tests:** new `tests/e2e/dora_api/test_household_tz_boundaries.py`
  (4 cases) pins the contract end-to-end — sets
  `AppSetting.timezone = Pacific/Kiritimati` (UTC+14) and asserts
  `/meal-plans/today`, the alerts handler, the dashboard summary,
  and the waste-rescue feed all evaluate boundaries against the
  household zone, not server-local. Each test brackets its zone
  change in a `try/finally` so a failure doesn't leak.
- **Standards close-gate:** clean. New **R-021 + ADR-016** promoted
  per the FU's instruction. R-001 / R-003 already covered: the
  single-source helper (`household_today`) was already in place;
  this is the rollout.
- **Verification:** `vue-tsc --noEmit` clean. Server tests not run
  (no Python in env); the new boundary tests + the existing alert
  / meal-plan-today tests pin the behaviour and will catch
  regressions on first run. Browser-verify of `last_made_on` now
  rendering as a date string (vs. datetime) in cookbook surfaces
  folds into [[FU-099-V]] / [[FU-321]] verify pass.
- **Carry-over:** none in scope. Cross-references:
  - **FU-107** (RFC 2822 → ISO 8601 wire format) — already
    delivered by ADR-007 + `DoraJSONProvider`; closing in the
    same session for tidiness (its only remaining bullet point
    was "Recipe.last_made_on (DateTime)" which this sweep also
    converts).

## [RESOLVED] FU-107 — Standardise API date serialisation on ISO 8601 (drop RFC 2822 default)
- **Raised:** 2026-06-10 (FU-083 "Planned" filter follow-up — RFC vs ISO
  parse bug).
- **Type:** finding / cross-cutting cleanup.
- **Resolution (already shipped 2026-06-12; closed for the record
  2026-06-29 during the FU-174 sweep):** delivered by **ADR-007** —
  `dora_api/app.py:DoraJSONProvider` serialises `datetime` → ISO 8601
  with offset (`Z` for naive, which the docstring explains is the
  SQLite-strip-tz workaround) and `date` → `YYYY-MM-DD`. Every
  date/datetime in every response went through the new provider; the
  RFC-aware workarounds in SPA models (`plannedRecipeIds` in
  RecipesOverview etc.) had already been dropped when the provider
  landed. The FU's residual bullet — "Recipe.last_made_on (DateTime)"
  — was independently resolved by the FU-174 sweep (the field is now
  a `Date` column, which also fixes the JS `new Date(rfc)`
  midnight-UTC drift that bullet flagged). Cross-ref ADR-007 for
  the wire-format decision; R-021 / ADR-016 for the calendar-day
  boundary rule.

## [RESOLVED] FU-323 — Convert remaining `message: describeApiError(e)` toasts to message + caption + ref
- **Raised:** 2026-06-29 (FU-099 close-out).
- **Type:** polish.
- **Resolution (2026-06-29):** the 10 stragglers identified during the
  FU-099 sweep migrated to the standard `message: '<action context>',`
  + `caption: toastCaption(e)` shape.
  - **ApiAccessSettings.vue (8 sites)** — load mappings / load stores /
    create / rename / toggle / revoke / upsert mapping / drop mapping.
    Each toast now leads with a one-line action context ("Couldn't
    create the API key.", "Couldn't toggle the API key.", …) and the
    error detail + ref-id flow through `toastCaption(e)` in the
    caption. The inline `loadError.value` banner for the source-list
    fetch also routed through `toastCaption(e)` so the banner carries
    a `ref:` suffix too.
  - **StoresSettings.vue (2 toast sites + 2 inline banner sites)** —
    save (insert/update branch decided by `editing.value`) and delete
    each get an action-specific lead message; both inline `loadError`
    banners (listAsync + ensureLoadedAsync) routed through
    `toastCaption(e)` to match.
  - Imports cleaned in both files (`describeApiError` removed,
    `toastCaption` added).
- **Standards close-gate:** clean — single source remains
  `toastCaption`, no new code shape. R-001 / R-003 already covered
  the principle; nothing new to promote.
- **Verification:** `vue-tsc --noEmit` clean. Browser-verify of the
  toasts (each shows the action message + the friendly cause + the
  ref) folds into [[FU-099-V]] — same verify pass.

## [RESOLVED] FU-099 — Raw backend / Pydantic error strings leak into user-facing toasts → design pass + fix
- **Raised:** 2026-06-09 (user, after the recipe-save Pydantic error).
- **Type:** cross-cutting UX gap + structured-error design.
- **Resolution (2026-06-29):** full design discussion + implementation
  per `docs/04_proposals/IMPL_PLAN_ERROR_HANDLING.md`. Seven decisions
  settled with the user (server-side friendly translation, inline +
  brief generic toast, ~15 Pydantic codes + fallback, 4xx
  console.warn, `{msg, code, raw}` wire shape, keep current
  network/5xx copy + ref, sweep every catch block in one PR).
- **Server changes:**
  - New `dora_api/infrastructure/error_translation.py` —
    `PYDANTIC_FRIENDLY` map (~30 codes incl. missing / extra_forbidden /
    int_parsing / string_too_short / uuid_parsing / greater_than / …)
    + `FRIENDLY_FALLBACK = "This value isn't valid."` for unknown
    codes. The single source of truth (R-003) for translating
    Pydantic prose to user copy.
  - New `ErrorEntry` dataclass in `api_response.py` —
    `{ msg, code, raw }`. Replaces the bare `str` that used to live
    inside `ProblemDetails.errors[field]`. Domain helpers
    (`bad_request`, `business_rule_violation`,
    `entity_existence_failure`) keep their plain-string signatures;
    a new `_lift_errors` helper folds each string into
    `ErrorEntry(code="domain", raw=None)` so 50+ existing call sites
    don't need per-site edits.
  - `middleware.py` — `ValidationError` handler now emits one
    `ErrorEntry` per Pydantic error carrying the friendly translation
    + the raw `err["type"]` code + the raw `err["msg"]` for dev
    inspection. Wire shape: `errors: { field: [{msg, code, raw}, …] }`.
  - Updated 45 existing assertion sites across
    `test_product_router`, `test_stock_item_router`,
    `test_stock_location_router` to the new shape, via new helpers
    `validation_err(code, raw)` / `domain_err(msg)` in
    `tests/e2e/dora_api/_error_assertions.py` (single-source — a
    future change to `PYDANTIC_FRIENDLY` only touches the table, not
    every test).
  - New `tests/e2e/dora_api/test_error_translation.py` — 6 e2e tests
    pinning the wire-shape contract: friendly msg + code + raw on
    Pydantic errors; missing / extra_forbidden codes; unknown code
    falls back to `FRIENDLY_FALLBACK`; domain BRV + entity-existence
    lift plain strings into the new shape.
- **Client changes:**
  - `apiErrorHandler.ts` — `ApiErrorEntry` type matches the server's
    wire shape. `extractFieldErrors` now handles both the new
    structured shape and (transitionally) the old string-array shape,
    extracting the friendly `msg` for inline rendering.
  - `describeApiError` — when field-keyed errors are present, returns
    the generic *"Couldn't save — check the highlighted fields."*
    instead of pasting the raw field strings into the caption. The
    field copy now belongs inline on the offending input, not in
    the toast caption.
  - New `correlationSuffix(err)` — builds `" · ref: <8-char id>"` from
    the X-Request-Id round-tripped by the server.
  - New `toastCaption(err)` — combines `describeApiError` +
    `correlationSuffix` into one drop-in for the old
    `describeApiError(err) || ''` idiom; every negative toast now
    carries the ref by default.
  - `axiosHttpClient.handleError` — `console.warn` now fires on
    *every* failed call (4xx + 5xx + network), not just 5xx. Same
    shape: `[api] METHOD path → status code (correlation-id)` with
    structured `details` blob. Pasting a toast caption's ref into a
    bug report now gives a dev one grep to find the request line.
  - New composable `useFormErrors()` (`web_app/src/composables/`) —
    one place owns the `fieldErrors` / `generalError` /
    `handleSaveError` / `reset` plumbing every form was hand-rolling.
- **Migrations:**
  - **Shape C (4 sites):** `RecipeEditDialog`, `CreateStockItemDialog`,
    `LoginPage` migrated to `useFormErrors()`. `WelcomeWizard`
    deliberately kept its direct `extractFieldErrors` call
    (custom routing of `username` → its own `displayNameError` slot,
    not a fit for the simple composable).
  - **Shape B sweep (95 substitutions across 33 files):** every
    `caption: describeApiError(err) || ''` rewritten to
    `caption: toastCaption(err)` via a one-shot Node script,
    with imports auto-updated (`describeApiError` removed where
    no longer used, `toastCaption` added). Files: AlertsPage,
    AlertsBell, ShoppingListDetail (23!), ShoppingListTemplates,
    StockItemRow, StockOverview, RecipeDetailPage, RecipesOverview,
    MyProductsPage, MealPlanTemplatesPage, MealPlanTemplatesDrawer,
    MealPlanRecipePicker, useMealPlanner, NewListDialog,
    StockGroupsSettings, StockLocationsSettings, UsersAdminSettings,
    AdminSystemFeaturesSettings, PreferencesSettings,
    AdminSystemAssistantSettings, AccountSettings (+ ~12 more).
- **Standards close-gate:**
  - **R-001 (componentisation):** `useFormErrors()` lifts the
    recurring catch-block plumbing into a single composable. The
    error-translation table is its own module. The toast-caption
    builder is its own helper. No hand-rolled five-liners remain
    across the migrated surfaces.
  - **R-003 (single source):** `PYDANTIC_FRIENDLY` is the sole code
    → copy map. `correlationSuffix` is the sole ref-id format.
    `toastCaption` is the sole toast-caption builder. The
    translation table is mirrored in test assertions through the
    `validation_err` helper, not duplicated.
  - **R-007 (scope discipline):** inclusion list is the ~30 codes
    our schemas actually emit; unknown codes fall back. No
    pre-built per-field bespoke copy.
- **Verification:** `vue-tsc --noEmit` clean. No Python interpreter
  in this session's env — server-side test suite not run; the new
  e2e tests pin the contract and the existing 45 assertions were
  updated to match. Browser-verify of the full pipeline logged as
  **[[FU-099-V]]**.
- **Carry-over (deliberately not in scope):**
  - **[[FU-323]]** — 10 surviving `message: describeApiError(e)`
    toasts in `ApiAccessSettings` + `StoresSettings` (different
    shape — friendly text in `message`, no `caption`/ref). They
    work correctly post-FU-099 (friendly copy renders, console.warn
    logs the ref); migrating to message + caption + ref is polish,
    not a real defect.

## [RESOLVED] FU-098 — Unsaved-changes guard on navigation (app-wide)
- **Raised:** 2026-06-09 (user, after cook-mode batch).
- **Type:** finding / cross-cutting UX gap.
- **Resolution (2026-06-29):** exhaustive sweep for "Save button +
  locally-deferred state" surfaces. The composable
  `useUnsavedChangesGuard` already exists (shipped with FU-156 on
  2026-06-12) and was wired into the two large editor pages;
  remaining gaps were:
  - **`AccountSettings.vue`** — `usernameDraft` + `emailDraft` each
    have their own Save button + `unchanged` computed. Guard wired
    on `!usernameUnchanged || !emailUnchanged`. Profile-picture
    upload and password change are deliberately excluded (both save
    immediately on action — no draft window; and browsers expect
    typed passwords to be lost on nav for security reasons).
  - **`AdminSystemAssistantSettings.vue`** — three drafts
    (`enabledDraft` / `baseUrlDraft` / `modelDraft`) + Save button
    + `unchanged` computed. Guard wired on `!unchanged`.
- **Audited and deliberately NOT guarded (with reason):**
  - `RecipeCookMode.vue` — session state (ticks, swaps,
    cookingFor) is real-time and transient, not a save-button form.
    The "Done" button persists stock-level changes via the explicit
    finish dialog; there's no notion of "draft progress" to warn
    about. Cooking is expected to be uninterruptible — flagging
    every nav would be noise.
  - `ShoppingListDetail.vue` — every line edit (quantity, name,
    status) saves immediately via `@blur` / `@update:model-value`.
    No locally-held dirty state on the page; the two `label="Save"`
    buttons live inside `q-menu` popovers (price editor + planned-
    date editor) where state is intentionally transient.
  - Settings pages that save-on-blur or save-on-change:
    `AdminSystemAlertsSettings` (blur), `AdminSystemFeaturesSettings`
    (toggle/blur), `AdminSystemTimezoneSettings` (change),
    `MoneySettings`, `NotificationsSettings`, `PreferencesSettings`
    (theme — live-applied + persisted), `NutritionSettings`,
    `VoiceSettings` — no Save button, no draft window.
  - Settings pages whose only `label="Save"` is inside an
    add/edit/rename `BaseDialog`: `StoresSettings`,
    `StockGroupsSettings`, `StockLocationsSettings`,
    `RecipeCategoriesSettings`, `RecipeCuisinesSettings`,
    `RecipeDietaryTagsSettings`, `RecipeMealSlotsSettings`,
    `RecipeToolsSettings`, `UsersAdminSettings`,
    `ApiAccessSettings`. Dialog state is intentionally transient —
    cancelling closes; route nav would close the parent component
    and lose the dialog along with it, but that's modal-close,
    not "discard your half-typed essay" territory. Out of scope
    for this FU.
  - `MealPlansBoardPage.vue`, `MealPlansOverview.vue`,
    `MealPlanTemplatesPage.vue` — no page-level draft (board
    mutations write immediately; the `label="Save template"`
    button on each is inside a `v-close-popup` dialog).
  - `RecipeEditDialog.vue`, `SubstituteMetadataDialog.vue`,
    `MealPlanTemplatesDrawer.vue` — dialogs/drawers, not pages.
- **Standards close-gate:** clean.
  - **R-001 (componentisation):** no new components — the existing
    `useUnsavedChangesGuard` was reused with no copy-paste.
  - **R-003 (single source):** the guard's policy (the confirm
    dialog copy, the `beforeunload` shape, the
    `onBeforeRouteLeave`/`onBeforeRouteUpdate` pair) lives in one
    file; each call site only supplies the dirty predicate.
  - **New rule promoted:** **R-020 + ADR-015** — "Deferred-save
    surfaces wire the unsaved-changes guard." Two events in six
    weeks (FU-156 + this sweep) where a new editor page forgot the
    guard is rule-worthy recurrence; the rule pins the predicate
    shape, names the four standing exclusion categories (inline
    save, real-time session, dialog-only, password field), and
    gives reviewers a one-line grep target for new diffs. Comments
    on the four already-wired sites updated to reference `R-020`
    so the rule's discoverable from the call site.
- **Verification:** `vue-tsc --noEmit` clean. Browser verify (the
  two new sites' nav prompts fire when dirty, suppress when clean)
  logged as **[[FU-322]]** for the next verify-pass.
- **Carry-over:** none in scope. Cook-mode session-state guarding
  was considered and rejected as out-of-scope for this FU (rationale
  above) — if a future user report flags lost cook sessions on
  accidental nav, that becomes its own follow-up.

## [RESOLVED] FU-097 — Roll out `formatQuantity()` to recipes/shopping-list surfaces
- **Raised:** 2026-06-09 (Cook Mode Chunk 2)
- **Type:** finding / R-001 + R-003 cleanup
- **Resolution (2026-06-29):** quantity-spacing sweep — `formatQuantity`
  is now the only place that knows the DEC-3 rule. Surfaces audited
  against the FU's original list:
  - **`MealPlanShoppingSummary.vue`** — switched the `needs {{ qty }} {{ unit }}`
    inline to `formatQuantity(ing.total_quantity, ing.unit)`.
  - **`SequentialBuilderDialog.vue`** — same pattern (kept the `round()`,
    just routed the result through `formatQuantity`).
  - **`RecipeCookMode.vue` substitute-ratio caption** and
  - **`StockItemDetailPage.vue` substitute-ratio caption** — both built
    `${qty} ${unit} → ${qty} ${unit}` by hand; now each half goes through
    `formatQuantity`. Safe because FU-034 canonicalises the ratio unit on
    persist (`"tablespoons"` → `"tbsp"`), so the lowercased no-space
    inclusion list catches every form. Cook mode's own ingredient-row
    display path was already on `displayQuantity` → `formatQuantity` from
    Chunk 2.
  - **Print view (`dora_api/features/data/export_recipe.py`)** — the
    server-rendered Jinja template was emitting `{{ quantity }} {{ unit }}`
    with an always-on space. Added a Python mirror **`format_quantity`** in
    `dora_api/domain/units.py` (R-003: the no-space inclusion list lives
    next to `UNIT_TABLE`, the existing single source of truth for units)
    and the template now calls it via a passed kwarg. Server + client
    spacing are guaranteed identical.
  - **FU items now N/A:** `RecipeDetailPage.vue` and `RecipeEditDialog.vue`
    use **separate** qty + unit `q-input`s (no concatenation to format);
    `RecipeCard.vue` and the cookbook overview don't render `qty + unit`
    at all (just name, time, servings, tags). The shopping-list bullet was
    already marked N/A by the FU's own 2026-06-12 update. The "Print/export
    view" item pointed at the SPA hub page (`ExportPrint.vue`) which is a
    list of export actions — the actual recipe print template was the
    server-side Jinja, fixed above.
- **Bound to:** the unit-canonicalisation work in `dora_api/domain/units.py`
  + FU-034 substitute ratios — canonical forms feed naturally into the
  formatter because matching is case-insensitive and the inclusion list
  covers every canonical "tight" unit (ml, g, kg, L, mg, oz, lb, fl oz,
  pt, qt). No drift risk between server-canonicalised units and
  client-side formatting.
- **Standards close-gate:**
  - **R-003 (single source)** — the rule is now stated **once per language**
    (TS `formatQuantity.ts`, Python `units.py:format_quantity`); inclusion
    lists are mirrored by intent (5-line frozenset / 1-line `ReadonlySet`)
    with a comment on each side flagging the sync requirement. No call
    site re-implements the rule.
  - **R-001 (componentisation)** — no new components; surfaces routed
    through the existing helper.
- **Verification:** `vue-tsc --noEmit` clean. Python compile not run
  (no interpreter in this session's env); the only Python change is a
  small pure helper + a Jinja `{% set %}`, both syntactically trivial.
  Browser verify of the print view + meal-plan summary + substitute
  ratio captions deferred — captured below if you'd like a verify pass.
- **Carry-over:** spawned a new [[FU-321]] — browser-verify the four
  routed display surfaces in a real Quasar build before trusting that
  every spacing case lands the right way ("1L" / "1 tbsp" / unitless
  fallbacks / ratios in both directions).

## [RESOLVED] FU-092 — Audit ALL implicit / automatic / "magic" behaviour
- **Raised:** 2026-06-09 (user, during C-7 cart-button design — started
  as the "preferred product" worry, broadened to every automatic
  behaviour).
- **Type:** open question / app-wide UX assessment.
- **Resolution (2026-06-28):** ran the full audit. Output at
  `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` — 18 behaviours
  catalogued, each with a current-state pointer, a surprise-risk read,
  and a recommended verdict. User reviewed every one and gave per-
  finding verdicts; results table at § Verdicts in the audit doc.
  Outcome: **13 of 18 already in the right shape** (alerts, suggestions,
  explicit endpoints, visible-by-design surfaces, FU-114-style
  visible-default flows) — no action. **4 small (b) follow-ups**
  spun off as [[FU-315]] (auto-add toast/chip verify),
  [[FU-316]] (remembered-list toast + "always ask" setting),
  [[FU-318]] (cheapest chip), [[FU-319]] (inline-pantry toast). **1
  plan-first follow-up** spun off as [[FU-317]] — F5 past-day
  meal-plan auto-drain wants a designed manual-reconcile feature
  (stocktake-mode-for-meals: dedicated page, alert, indication of
  what should have been consumed) plus an opt-in setting for the
  current auto-drain. Per the user's call, **no code touches the
  reconcile path before that proposal lands.** R-019 (no magic) is
  the standing rule going forward; this audit is the one-time backlog
  sweep that ratified what was already correct.

## [RESOLVED] FU-160 — Shopping-list "shopping day" alert (feedback L403)
- **Raised:** 2026-06-12 (re-surfaced during shopping-list buggy-merge audit)
- **Type:** deferred job
- **What:** Feedback L403 asked for an alert when a list's planned shop
  date is today / imminent / overdue.
- **Resolution (2026-06-28):** confirmed already shipped end-to-end.
  Server: `dora_api/features/alerts/get_alerts.py:391`
  (`_shopping_day_alerts`) — pulls every not-yet-done `ShoppingList`
  whose `planned_shop_date` falls within the next 3 days
  (`SHOPPING_DAY_WINDOW_DAYS`) or has already passed. Overdue lists
  bump to `SEVERITY_MEDIUM` ("Shopping day was yesterday / N days
  ago"); upcoming use `SEVERITY_LOW` with "today" / "tomorrow" /
  "in N days" wording. Kind `shopping_day` lives in
  `dora_api/features/alerts/alert_kinds.py:30` at `TIER_FYI`. Alerts
  ride the shared bell + snooze pipeline via `list_alert_key(...)` so
  user dismiss/snooze persists as the date rolls. Frontend renders +
  deep-links in `web_app/src/models/alert.ts` (kind union at L19,
  icon/label/route switches at L138/168/190/222/237) and
  `web_app/src/pages/AlertsPage.vue:265` (filter chip) /
  `:302` (deep-link target). Closing the FU to match reality —
  someone shipped this between when the FU was raised and now without
  closing it.

## [RESOLVED] FU-084 — Promoted to R-019 / ADR-014 ("no magic: explicit, verbose, consistent")
- **Raised:** 2026-06-09 (Chunk 2)
- **Type:** finding / engineering-standards
- **What:** Originally proposed promoting the SQLAlchemy
  `lazy="selectin"` shortcut on `Recipe.cuisine`/`.category` into a
  standing rule for "small always-wanted lookups".
- **Resolution (2026-06-28):** user re-scoped the FU from the narrow
  selectin recommendation to a top-line value: prefer **verbose,
  explicit, locally-readable code**; reject **magic** (AutoMapper-shaped
  reflection, decorator behaviour-mutation, convention-over-configuration
  past the framework, per-entity loading-strategy overrides that hide
  what runs at the call site); reject **inconsistent local patterns** ("most
  of the codebase does X but here we did Y because it felt right"). Added
  **R-019 — No magic: explicit, verbose, consistent** to
  `docs/01_charter/ENGINEERING_STANDARDS.md`, with **ADR-014** recording
  the decision and the FU-084 reframing. R-019 explicitly notes that
  per-entity SQLAlchemy `lazy="..."` overrides are themselves a flavour
  of magic and should be retired in favour of explicit call-site loading;
  the existing `Recipe.cuisine`/`.category` selectin opt-ins are
  grandfathered for R-007 reasons and flagged as [[FU-314]] for an
  opportunistic cleanup chunk.

## [RESOLVED] FU-140 — Sweep Cart Button Chunk 3 typing fallout (nullable `stock_item_id`)
- **Raised:** 2026-06-12 (State Ownership Chunk 4 typecheck)
- **Type:** finding / cleanup
- **What:** Cart Button Chunk 3 made `ShoppingListLine.stock_item_id`
  nullable; the audit was to catch consumers that compiled only
  because no other change had triggered re-checking.
- **Resolution (2026-06-28):** ran `npx vue-tsc --noEmit` from
  `web_app/` — exits clean under `exactOptionalPropertyTypes`. Then
  hand-audited every `ShoppingListLine.stock_item_id` reader:
  - `ShoppingListDetail.vue` — `openFinishReview` filters nulls
    out of the dedupe set and keeps them as "Not stock-tracked"
    rows in the finish modal (UI guarded by `v-if="entry.stock_item_id"`);
    `confirmFinish` narrows via typed `.filter` predicate before
    sending `FinishLevelOverride[]`; `onSwapSubstitute` early-returns
    on null and filters the on-list dedupe set through
    `(id): id is string => !!id`; `onRemoveLine` (the FU-131 rule-4
    path) checks `!before.stock_item_id` before triggering the
    extra remove; template guards `<router-link :to="/stock/{id}">`
    behind `!isNestedChild(line) && line.stock_item_id`.
  - `NewListDialog.vue` (lines 284, 374, 396) — all three id
    extractions use the typed filter predicate.
  - `StockOverview.vue:759` — `(l) => l.stock_item_id && selected.has(l.stock_item_id)`
    relies on TS narrowing within `&&`, type-checks.
  - The `removeByStockItemFromListAsync` call in `onRemoveLine`
    only fires when `alsoRemoveStockItemId` is non-null.
  Two collateral TS errors from FU-117's step-editor work surfaced
  during the audit and were fixed in the same pass:
  `RecipeDetailPage.vue:1914` (the import-recipe step factory now
  sets `section_client_id: null`) and `RecipeStepsEditor.vue:8`
  (passes `sectionOptions ?? []` so the optional prop doesn't
  leak `undefined` to the row under `exactOptionalPropertyTypes`).

## [RESOLVED] FU-139 — Finish migrating `getStockLevelColour(name)` callers to `colourForSequence(seq)`
- **Raised:** 2026-06-12 (State Ownership Chunk 4)
- **Type:** follow-up / cleanup
- **What:** Chunk 4 introduced `colourForSequence(seq)` and migrated
  the decision-driving call sites, leaving the legacy
  `getStockLevelColour(name)` as a soft-fallback on six display-only
  surfaces.
- **Resolution (2026-06-28):** confirmed already shipped — no code
  changes needed. The legacy `getStockLevelColour` no longer exists
  in `web_app/src/helpers/stockLevelLogic.ts`; the file now only
  exports `colourForSequence`, and a `grep -r getStockLevelColour
  web_app/src` returns just the historical mention in the
  `colourForSequence` doc-comment. Every named call site
  (`StockItemDetailPage.vue`, `RecipesOverview.vue`,
  `RecipeDetailPage.vue`, `QuickAddSheet.vue`,
  `CreateStockItemDialog.vue`, `MyProductsPage.vue`) routes through
  `colourForSequence(level.sequence)` / `colourForSequence(item.
  stock_level_sequence)`. Closing the FU to match reality.

## [RESOLVED] FU-138 — Query-count test for `GET /recipes` (no N+1)
- **Raised:** 2026-06-12 (State Ownership Chunk 2 close-gate)
- **Type:** deferred job (test infra)
- **What:** Pin the recipe-list endpoint's SELECT count so the
  batched cookability / missing-names aggregations can't silently
  regress into N+1 lazy loads.
- **Resolution (2026-06-28):** added a minimal `SelectCounter`
  context manager at `tests/e2e/dora_api/_query_counter.py` that
  listens on SQLAlchemy's `Engine.before_cursor_execute` and
  records every SELECT during its scope. New test
  `tests/e2e/dora_api/test_recipes_query_count.py` runs a ratio
  check rather than a hard ceiling: baseline `GET /recipes`,
  insert 10 throw-away recipes via `POST /api/recipes`, re-hit
  `GET /recipes`, assert the per-recipe SELECT delta stays under
  0.5 (cleanup deletes the probe recipes in the `finally`).
  Passes today with a delta of 0; an honest N+1 regression on
  cookability/ingredients/tags/tools/sections/plan-rollups would
  add ≥1 SELECT per recipe and blow the budget. Test fixture
  matches the existing e2e shape — uses `requests` rebound to the
  Flask test client by `tests/e2e/dora_api/conftest.py`. Kept the
  harness intentionally tiny (single class, ~50 LOC); resist
  growing it into shared infra until a second consumer shows up.

## [RESOLVED] FU-131 (original) — Cart Button Chunk 3 frontend UI (rule 4 modal + inline-product variant + nested display)
- **Raised:** 2026-06-12 (Cart Button Chunk 3 deliberate scope-down)
- **Type:** rollout
- **What:** Backend rules 1–3 + schema + DTO landed in the chunk
  itself; the UI side (rule 4 confirm modal, inline-product variant,
  nested display) plus a backup/restore round-trip were carved out.
- **Resolution (2026-06-28):**
  - **Rule 4 modal, inline-product variant, nested display** —
    confirmed already shipped (likely as part of a later FU-131
    follow-on session that didn't close the parent entry). Live in
    [ShoppingListDetail.vue:2132](web_app/src/pages/ShoppingListDetail.vue:2132)
    (`onRemoveLine` prompts "Also remove the stock item?" when the
    deleted line is product-only and its linked stock item is on
    the list as a separate row), [AddToListButton.vue:21](web_app/src/components/AddToListButton.vue:21)
    (`variant="inline-product"` + `productId` anchor path —
    wired into [MyProductsPage.vue:349](web_app/src/pages/MyProductsPage.vue:349) as
    "Add as product"), and [ShoppingListDetail.vue:1362](web_app/src/pages/ShoppingListDetail.vue:1362)
    (`nestedLinesFor` reorders child product lines immediately
    under their parent stock-item line; `isProductOnly` drives the
    `shopping-bag` chip + "Product only — no linked stock item on
    this list" tooltip).
  - **Backup / restore round-trip** — actual gap fixed this session.
    `restore_shared.py` left the new nullable `product_id` column
    unclassified, so a partial restore that included shopping lists
    but not `saved_products` would silently drop product-only lines
    (or null `product_id` on nested children, then crash the new
    `ck_shopping_list_line_anchor` CHECK on product-only rows).
    Added `("shopping_list_items", "product_id"): "saved_products"`
    to `HARD_FK_PULL_IN` so the referenced Product is auto-included,
    and added `("shopping_list_items", "product_id")` to
    `REQUIRED_FKS` so the row is dropped (with a warning) rather
    than silently re-shaped when the Product truly is missing.
    Annotated the existing `stock_item_id` REQUIRED entry to make
    the nullable-but-must-resolve semantics explicit.
- **Browser verification of the three UI pieces remains tracked
  as [[FU-145]].** Product-anchored cart-state membership is
  separately tracked as [[FU-144]].

## [RESOLVED] FU-117 — `RecipeStepsEditor` should let you pick a step's section
- **Raised:** 2026-06-12 (Chunk 10 deliberate scope-down)
- **Type:** enhancement
- **What:** Chunk 10 wired `section_id` on `RecipeStep` end-to-end
  but the steps editor lacked a section picker; hand-entered steps
  shipped with `section_id = NULL`.
- **Resolution (2026-06-28):** added `section_client_id: string | null`
  to `EditableStep` and a new `SectionOption` type in
  `recipeStepEditorTypes.ts`. `RecipeStepsEditor` now takes an
  optional `sectionOptions` prop and forwards it to each row;
  `RecipeStepRow` renders a compact `q-select` in the row header
  **only at `depth === 0`** and only when more than one option
  exists (the implicit `(Main)` plus at least one named section) —
  sub-steps inherit visually as the FU prescribed. `RecipeDetailPage`
  reuses its existing `sectionOptions` computed (already
  `[{value: null, label: '(Main)'}, …]`), passes it to the editor,
  hydrates `section_client_id` from `s.section_id` on load, and
  rides it through `stepsToSend` on save. `removeSection` now also
  detaches step references in addition to ingredient ones (parity
  with the existing ingredient-row picker). New-step factories in
  the editor initialise `section_client_id: null`. Importer left
  unchanged — `HowToSection` detection in the URL importer is a
  separate concern.


- **Raised:** 2026-06-11 (Cookbook Chunk 9 impl)
- **Type:** finding / cleanup
- **What:** Chunk 9 stopped rendering/editing the freeform
  `recipe.nutrition` text column in favour of the structured
  `kcal: int | None` field. The column survived in the DB + on the
  DTO + in the form's hydrate/save plumbing pending a prod audit.
- **Resolution (2026-06-28):** pre-release — no production data to
  preserve, so the column was dropped outright rather than audited.
  Migration `b7e2d9a4c1f5_20260628_drop_recipe_nutrition.py` drops
  `Recipe.nutrition`; the field was removed from the `Recipe`
  entity (incl. `Fields.NUTRITION`), `table_mappings.py`, the
  create/update request models + their entity assignments,
  `RecipeDto` + assignment in `get_recipes.py`,
  `new_recipe_version.py` clone, `import_recipe_from_url.py`
  (including `_coerce_nutrition` and the `ImportedRecipeDto`
  field), the export-recipe Jinja template, the seed factory, the
  `test_recipe_cookability` stub, and from the SPA
  (`recipe.ts`, `recipeApiService.ts` × 3, `RecipeDetailPage.vue`
  hydrate/empty/save-diff/import paths, `RecipesOverview.vue` import
  call, `RecipeEditDialog.vue` template input + form + create/update
  payloads).


- **Raised:** 2026-06-10 (Cookbook Chunk 7 impl)
- **Type:** R-001 cleanup
- **What:** Chunk 7 added a second "Import from URL" dialog
  (`RecipesOverview.vue`); the detail page already had one
  (`RecipeDetailPage.vue`). The two duplicated the dialog chrome, copy,
  URL input, `importFromUrlAsync` call, loading + error states.
- **Resolution (2026-06-28):** new `web_app/src/components/recipes/RecipeImportDialog.vue`
  owns:
  - the dialog chrome (`BaseDialog`, title, schema.org caption, URL input,
    Cancel + Import action),
  - the `url` / `error` / `importing` state,
  - the `importFromUrlAsync` call,
  - and resets its draft on every open via a `watch` on the v-model.

  Per the FU's recommendation, picked the **events** shape over a `mode`
  prop. The component emits `@imported(dto: ImportedRecipe)` and lets each
  caller decide what to do — no shared knowledge of `form`, `createAsync`,
  navigation, or `markDirty`. A single optional `degraded-hint` prop lets
  the detail surface append "Your existing recipe will be overwritten with
  the imported fields." to the caption without forking the dialog.

  **Callers updated:**
  - `RecipesOverview.vue` — handler `onRecipeImported` now just builds
    the create payload, POSTs it, navigates to the new recipe, and toasts.
    Dropped local `importUrl` / `importError` / `importing` refs (+ a
    now-unused `BaseDialog` import).
  - `RecipeDetailPage.vue` — handler `onRecipeImported` does the
    confirm-overwrite `$q.dialog`, patches the form fields, and toasts.
    Same local-state cleanup. Side fix: if the user cancels the
    confirm-overwrite, the import dialog now closes (previously stayed
    open on cancel — minor pre-existing bug).

  **Verification:** `vue-tsc` clean. Full e2e + unit suite **442/442
  passing.**

## [RESOLVED] FU-094 — Steps editor: drag-and-drop reorder (replaces up/down)
- **Raised:** 2026-06-09 (Cookbook Chunk 6 impl)
- **Type:** follow-up
- **What:** The structured-steps editor shipped with up/down arrow
  buttons instead of the drag-handle pattern from shopping-list lines.
  Replace once the editor is in real use.
- **Resolution (2026-06-28):** drag-and-drop landed.
  - **`RecipeStepRow.vue`** — added a drag handle (`drag_indicator`
    icon) that's the only `draggable="true"` element on the row, so
    textareas + selects stay normally clickable. The whole row is the
    drop target (`@dragover` / `@drop`); `setDragImage` points at the
    row's outer div so the visual preview is the whole row. Up/down
    arrow buttons removed.
  - **`RecipeStepsEditor.vue`** — owns the drag state
    (`draggingClientId` + `draggingParentId`) so every row decides
    whether *it* is a valid drop target. Reorder logic mirrors
    `ShoppingListDetail.onLineDrop`'s "insert at the target's slot"
    pattern; sequences re-packed through the existing
    `repackSequences`.
  - **Siblings-only constraint** (per the FU): `dragover` only allows
    `preventDefault` when the source's `parent_client_id` matches the
    target's. A top-step can't become a sub-step via drag and vice
    versa — that promotion/demotion is its own affordance and
    deliberately out of scope. Validation re-checked at drop time as
    belt-and-braces.
  - **Visual feedback** — dragging row gets `opacity: 0.5`; the
    hovered-valid drop target gets a 2px `var(--brand-primary)`
    outline. Handle has `cursor: grab`/`grabbing`, token-only colours
    (R-002).
  - **No backend change** — the persisted shape (parent + sequence) is
    what the editor already emits.
  - **Verification:** `vue-tsc` clean. Full e2e + unit suite
    **442/442 passing**. The DnD itself is browser-level; suite acts
    as a regression guard on the surrounding code.

## [RESOLVED] FU-081 — Move "Planned in" filter from client-side to server-derived Recipe.is_planned
- **Raised:** 2026-06-09 (Cookbook Chunk 1)
- **Type:** finding / state-ownership
- **What:** Cookbook overview was walking `mealPlanStore.mealPlans[].entries[]`
  client-side to build the "planned recipes" set — a cross-entity rule
  (recipes × meal plans × today) that R-003 says belongs on the server.
- **Resolution (2026-06-28):** moved to the server + added a tri-state UI on
  the same trip.
  - **Backend:** `RecipeDto.is_planned: bool` derived in
    `_hydrate_unallocated` from the already-running future-unconsumed
    `MealPlanEntry` query — zero extra round-trip.
  - **Pre-existing bug surfaced and fixed:** `_hydrate_unallocated`'s
    raw `text()` query bound stringified UUIDs against the `UUIDType`
    BLOB columns on SQLite (string-vs-BLOB never matches), so
    `committed_meals`, `unallocated_meals`, `plan_count` had been
    silently 0 for any future-planned recipe. Hidden by the seed
    (no future entries) and only surfaced today because the new
    `is_planned` test forced a future entry. Switched the derivation
    to ORM `select()` against the mapped table so SQLAlchemy applies
    the UUIDType bind-processor; portable across SQLite + Postgres.
  - **Frontend:** Recipe model + `is_planned` field; new
    `TriStateFilterChip.vue` (cycles `off → include → exclude → off`
    on each click, with swappable label/icon/colour per state);
    `RecipesOverview.vue` swaps `plannedInOnly: boolean` for a
    `plannedFilterState: TriState` and binds the new chip
    ("Planned" → click → "Not planned" → click → off). Predicate +
    active-filter count + Clear filters all updated.
  - **Round-trip eliminated:** the cookbook page no longer needs to
    `await mealPlanStore.getMealPlansAsync()` on mount; the
    `mealPlanStore` import + ref are gone from `RecipesOverview.vue`.
    Saves one network call per cookbook visit.
  - **Tests:** new `tests/e2e/dora_api/test_recipe_is_planned.py`
    (3 cases): toggles true when a future un-consumed entry is
    created, flips back to false on deletion, present on every DTO.
    Full suite **442/442**. `vue-tsc` clean.

## [RESOLVED] FU-075 — Run the new `test_shopping_list_planned_shop_date` e2e
- **Raised:** 2026-06-08 (Chunk 7 impl)
- **Type:** follow-up (verification gap)
- **What:** Pure runtime-verify of the four cases in
  `tests/e2e/dora_api/test_shopping_list_planned_shop_date.py`
  (create-with-date, create-without, PATCH set-and-clear-with-null,
  PATCH preserves-the-date-when-not-sent). Deferred because the original
  implementation session had no live Python env.
- **Resolution (2026-06-28):** ran the file on this session's working
  venv with migration `e1a4c7b2f9d0` (and every subsequent migration)
  applied. **4/4 passing** — the planned-shop-date wire-up survives
  every later schema and DTO change unchanged. Nothing to fix.

## [RESOLVED] FU-056 (slice 1b) — `UNIQUE(StockItemProduct.product_id)`, kill `product_multi_linked`
- **Raised:** 2026-06-28 (user pushed back on the multi-linked lookup kind)
- **Type:** model simplification — same FU.
- **What:** the user noticed `product_multi_linked` modelled a case that has
  no real semantic justification: a specific Product SKU (e.g. "Vitasoy
  Oat Milky 1L") satisfies one pantry slot, not many. The case only
  existed because the `StockItemProduct` join was symmetric m:n when the
  truth is asymmetric: many Products can satisfy one StockItem (different
  brands of milk all map to "Milk"), but a Product satisfies exactly one.
- **Resolution (2026-06-28):**
  - Migration `c4a8e2b9d7f5` — `UNIQUE(product_id)` on
    `StockItemProduct`. Seed already conformed (verified: 0 multi-linked
    products) so no backfill needed.
  - `barcode_lookup` simplified from 5 kinds to 4 — dropped
    `product_multi_linked`; barcode → Product → at most one stock item
    is structurally guaranteed.
  - Frontend types + `BarcodesQR.vue` dialog branches + `StockOverview.vue`
    scan handler + an existing e2e expectation all updated to the
    simpler shape.
  - **vue-tsc clean. Full suite 439/439.**

## [RESOLVED] FU-056 (slice 1) — Hybrid Barcode model + register-against-stock-item UI
- **Raised:** 2026-06-07 (P6-02 deferral); slice 1 shipped 2026-06-28.
- **Type:** deferred job
- **What:** P6-02 had explicitly dropped `StockItem.barcode` and routed
  every real EAN through `ProductBarcode → Product → StockItem`. That
  was conceptually correct for catalogued installs but broke scanning
  entirely for lightweight installs (FU-209 data-presence overlay
  → zero `Product` rows → no place to register an EAN).
- **Resolution (2026-06-28, slice 1):** discussed the design tension
  with the user; agreed on a **hybrid `Barcode` model** that keeps the
  "barcode = SKU" semantics when a Product exists AND lets a barcode
  attach directly to a stock item when one doesn't.

  **Schema (migration `b7f3a2c8d5e1`):**
  - Renamed `ProductBarcode` → `Barcode`.
  - `product_id` made NULLable + UNIQUE (enforces "one Product = one
    EAN"; UNIQUE-with-multi-NULLs is portable to both SQLite and PG).
  - `stock_item_id` added, NULLable, not unique (a stock item can carry
    many direct EANs).
  - CHECK constraint: at least one of the two FKs must be set.
  - `created_at` column added (mirrors other entities).
  - Restore-backup section + cross-table FK rules updated.

  **Backend (`features/data/barcodes.py`):**
  - **Lookup precedence:** dora:// QR → direct stock-item linkage →
    Product traversal (single linked / multi linked / no link). Five
    lookup kinds returned, each with the IDs the caller needs.
  - **`POST /api/data/barcodes`** — single registration endpoint;
    body has `barcode` + at least one of `product_id` /
    `stock_item_id`. Both is allowed. Pre-flight uniqueness check,
    DB UNIQUE as the real backstop, per-product UNIQUE catches "this
    Product already has a barcode".
  - **`DELETE /api/data/barcodes/<id>`** — remove a registration.
  - The old `/barcodes/register-against-product` route is collapsed
    into the new shape.

  **Stock-item detail (`get_stock_item_detail.py`):**
  - New `StockItemBarcodeDto` carrying `barcode_id`, `barcode`,
    `source` (`'direct' | 'via_product'`), and the product
    id/name for via-Product rows.
  - Handler derivation walks every `Barcode`, splits into direct vs
    via-Product (using `_StockItem.products` for the linked-Product
    set), sorts direct rows first.

  **Frontend:**
  - `models/stockItemDetail.ts` — new `StockItemBarcode` type +
    `barcodes` field.
  - `services/api/barcodeApiService.ts` — `registerAsync` /
    `deleteAsync` + the new five-kind `BarcodeLookupResult`.
  - `StockItemDetailPage.vue` — new **Barcodes** section under the
    Substitutes tab, gated on `features.scanning`. Lists direct +
    via-Product rows; "+ Add barcode" opens a small dialog
    (textbox-only for now; camera button is a future polish slot).
    Direct rows have a remove button; via-Product rows are read-only
    here (edit on the Product).
  - `BarcodesQR.vue` (Data → Scanning surface) — scan result dialog
    handles all five kinds; on `unknown` a register-now flow appears
    (stock-item picker → register via the new endpoint, with the
    barcode value coming from the scan).
  - `StockOverview.vue` scan integration — every result kind that
    resolves to a single stock item routes straight to it;
    Product-derived branches without a unique target surface a
    descriptive toast.

  **Tests (`test_data_router.py`):**
  - 6 new e2e cases (notes-only, ratio direction inversion, update-
    clears, half-filled rejection, qty=0, unknown unit) — sorry,
    wrong FU; for FU-056 the new tests are: register-against-product
    + lookup traversal, same-barcode-twice = 409, direct-stock-item +
    lookup returns `stock_item`, per-product UNIQUE = 409,
    neither-target = 400, delete round-trip.
  - Test fixture `_next_unused_product_id()` added because every test
    now consumes a Product (per-product UNIQUE forces it).
  - Full e2e + unit suite: **439/439 passing** post-landing. `vue-tsc`
    clean.

  **What stayed deferred (FU-056 stays OPEN at smaller scope):**
  - **Ingestion auto-populate** — Phase 2 work; endpoint already in
    place, ingestion just calls it.
  - **Product detail EAN field** — slot into the Products UI when
    that surface is touched; uses the same endpoint.

## [RESOLVED] FU-050 — Broader `'Out of Stock'` name-match smell beyond the 7 cookability copies
- **Raised:** 2026-06-07 (Phase 1 Chunk 3)
- **Type:** finding
- **What:** Chunk 3 removed the 7 recipe-cookability client copies, but a
  grep showed `'Out of Stock'` / `'Low Stock'` name-matching still living
  in non-recipe surfaces (`needToBuy`, restock sources, cook-mode
  availability, etc.), plus the legacy name-keyed
  `getStockLevelColour` helper that its own docstring marked for
  retirement.
- **Resolution (2026-06-27):** investigated; the **specific call sites
  the FU flagged were already migrated** — `needToBuy` now goes through
  the shared `useStockStatus().needsBuying` composable (sequence-keyed),
  and cook mode + ShoppingLists overview already key off
  `OUT_OF_STOCK_SEQUENCE` constants. The real remaining smell was the
  **legacy `getStockLevelColour(name)` helper** still being called from
  6 files (16 call sites). Swept all of them:
  - `CreateStockItemDialog.vue` — passes `scope.opt.sequence` to
    `colourForSequence`.
  - `QuickAddSheet.vue` — looks up `sequence` from the level store, not
    name.
  - `StockItemDetailPage.vue` — added a `detailLevelColour` computed
    that resolves the level's sequence via the store and routes through
    `colourForSequence`; per-level menu items use `level.sequence`
    directly. Also retired a suspicious `?? 'Well-Stocked'` default that
    was rendering untracked items in the success-green tone.
  - `MyProductsPage.vue`, `RecipeDetailPage.vue`, `RecipesOverview.vue` —
    same shape; the per-page colour computeds now key off
    `stock_level_sequence` (already on the StockItem model).
  - `helpers/stockLevelLogic.ts` — **legacy `getStockLevelColour`
    function deleted**, docstring updated to record the retirement.
  - **Bonus R-003 fix surfaced in the same area** —
    `services/doraIntents.ts` was carrying its **own copies** of
    `LOW_STOCK_SEQUENCE = 2` and `OUT_OF_STOCK_SEQUENCE = 3`,
    duplicating the canonical constants in `helpers/stockStatus.ts`.
    Deleted the duplicates and imported the shared ones.
- **Verification:** `vue-tsc --noEmit` clean. Full backend suite
  **435/435 — zero failures.** Final grep: every remaining
  `'Out of Stock'` / `'Low Stock'` literal in the codebase is in a
  comment / docstring describing the vocabulary; zero name-match code
  paths remain. The accepted carve-outs (`stockLevelLogic.ts` source,
  comment-only references in models) stay per the FU's original
  guidance.

## [RESOLVED] FU-049 — RecipeDetailPage cookability reflects saved recipe, not live edits
- **Raised:** 2026-06-07 (Phase 1 Chunk 3)
- **Type:** finding
- **What:** The recipe-detail sidebar "Cookable now / Missing N" reads
  `recipe.value` (the server-computed values on the loaded DTO) rather
  than recomputing live from `form.ingredients` while the user edits. So
  while adding/removing ingredients pre-save, the sidebar aggregate
  doesn't react until save reloads the DTO. The per-ingredient editor
  badge does update live (stock store boolean).
- **Resolution (2026-06-27):** user accepted on condition that the state
  refreshes after save. Verified end-to-end: `onSave()` at
  `RecipeDetailPage.vue:1703-1704` does
  `await updateRecipeAsync(command); await loadRecipe();`, and
  `loadRecipe()` (line 1601) re-fetches the full server DTO so the
  sidebar's `missing_count`, `cookable`, and `missing_stock_item_names`
  come back fresh. The same `loadRecipe()` runs after every other
  mutation that could affect cookability (favourite toggle, ingredient
  ops at lines 1729/1984/2004/2028/2144). Steady-state is correct;
  the temporary staleness during edit is the deliberate trade-off
  Chunk 3 made to avoid the client-recomputed stock-join duplication
  it removed (R-003). No code change.

## [RESOLVED] FU-310 — Four pre-existing e2e failures on `prototype/claude-upgrades`
- **Raised:** 2026-06-26 (surfaced during FU-082 test sweep)
- **Type:** finding (pre-existing test rot)
- **What:** Four `tests/e2e/dora_api` failures had drifted since the
  Settings rebuild Phase 4 / Dashboard rebuild Phase 2 work added new
  fields to the auth/user surface.
- **Resolution (2026-06-27):** root-caused and fixed.
  - **Real bug found** — `POST /api/auth/register` returned an ad-hoc
    dict (`user_id`, `username`, `email`, `is_admin`, `email_verified`,
    `verification_sent`) instead of the full `AuthenticatedUserDto`
    that `/login` and `/me` both return. The SPA's `registerAsync`
    already typed the response as `AuthenticatedUser`, so the auth
    store was being hydrated with `undefined` for every missing field
    (`has_image`, `dashboard_layout`, `theme`, `voice_engine`,
    `nutrition_mode`, etc.) — silent breakage masked by Vue
    permissiveness.
  - **Fix:** `register_user.py` now returns
    `dataclasses.asdict(AuthenticatedUserDto.from_entity(new_user))`
    plus the `verification_sent` extra. Mirrors `/login` and `/me` so
    the SPA can fully hydrate from any of the three.
  - **Two stale test assertions fixed:**
    - `test_user_router.py::test__get_users__GettingUsers__GetsAllExpectedAttributes`
      — added `'has_image'` to the expected key set (Settings rebuild
      Phase 4 added it to `UserDto` and bulk-stamps it via
      `_stamp_has_image`).
    - `test_auth_flows.py::test__profile_picture__rejects_oversize_data_url`
      — changed expected status from 422 to 400 (the codebase's
      convention for pydantic ValidationError, per
      `middleware.deserialise_web_request`; 84 other tests already
      use 400, only the one outlier used 422).
  - **Verification:** the 4 originally-failing tests now pass; full
    e2e + unit suite **435/435 — zero remaining failures.** Frontend
    `vue-tsc` clean.

## [RESOLVED] FU-034 — Wire up `StockItemSubstitute.notes` (substitution notes)
- **Raised:** 2026-06-06 (INV-1)
- **Type:** deferred job
- **What:** `StockItemSubstitute.notes` existed but was never wired. User
  confirmed the feature shape on 2026-06-27: **hybrid** — free-text note
  for any substitute, plus an **optional structured ratio** (e.g. "1 tsp
  → 1 tsp", "1 cup → 226 g") so the cook-mode swap picker can show the
  hint front-and-centre without forcing structure on swaps that don't
  need it.
- **Resolution (2026-06-27):** shipped end-to-end.
  - **Migration `a1c5e7d4f2b9`** — adds 4 ratio columns
    (`ratio_quantity_in`, `ratio_unit_in`, `ratio_quantity_out`,
    `ratio_unit_out`) and an `all-or-none` CHECK constraint so a
    half-filled ratio is rejected at the DB layer.
  - **Schema** — `table_mappings.py` `stock_item_substitute_table`
    grew the 4 columns + the constraint. No new entity class (the
    pair stays a bare association table, mirroring the existing
    pattern).
  - **Direction handling** — `dora_api/features/substitutes/metadata.py`
    (new) owns validation + direction-flip. Pairs are stored
    canonically (`a < b`); callers always think in "from THIS item to
    the substitute" terms. `build_metadata()` swaps in↔out at
    persist time when needed; `get_stock_item_detail` swaps at read
    time so consumers always see the ratio oriented "this → that".
  - **API:**
    - `POST /stock-items/<id>/substitutes` now accepts `notes` +
      `ratio_quantity_in` / `_unit_in` / `_quantity_out` / `_unit_out`
      (Pydantic 255-char cap on notes, 32-char cap on unit strings).
    - **New `PATCH /stock-items/<id>/substitutes/<sub_id>`** —
      replaces the metadata bundle; empty body clears it. Direction
      from the caller's POV; server flips into canonical storage.
    - **`SubstituteDto`** in `get_stock_item_detail.py` exposes the
      5 fields, ratio already oriented "this → that".
  - **Validation (R-003 — one source):** all-or-none ratio, qty > 0,
    units present in `dora_api.domain.units.UNIT_TABLE`. Unit strings
    are canonicalised on persist ("tablespoons" → "tbsp") so display
    is stable.
  - **Frontend:**
    - `Substitute` model + `notes` / ratio fields.
    - `services/api/stockItemApiService.ts` — `addSubstituteAsync`
      gained an optional `SubstituteMetadataInput` argument;
      `updateSubstituteAsync` is new.
    - **`SubstituteMetadataDialog.vue`** (new, ~250 lines) —
      textarea + "Add a ratio" toggle that reveals qty+unit pickers
      on each side, labelled "of {fromName}" / "of {toName}".
      `q-select` with `use-input` filters the UNIT_TABLE aliases so
      typing "tablespoons" finds tbsp.
    - **`StockItemDetailPage.vue`** substitutes tab — each row now
      shows the ratio caption + note caption inline under the
      substitute name; pencil icon next to the unlink icon opens
      the edit dialog.
    - **`RecipeCookMode.vue`** swap picker — chips replaced by a
      `q-list` so each substitute can carry its ratio caption + note
      below the name (same layout as the detail-page list, so the
      user reads the swap the same way in both places). Cook mode
      does NOT auto-compute the swap quantity in this phase — it
      surfaces the hint; the cook applies it. Per Anti-creep,
      structured auto-compute is a future-phase call.
  - **Tests:** new `tests/e2e/dora_api/test_substitute_metadata.py`
    (6 cases) — notes-only round-trip, ratio round-trip with
    direction inversion verified by viewing from the other side,
    update-clears-on-empty-body, half-filled rejection,
    non-positive quantity rejection, unknown unit rejection. **All
    6 pass.** Full e2e suite: **431/435** (4 pre-existing FU-310
    failures, unrelated).
  - **Frontend:** `vue-tsc --noEmit` clean.
- **Standards close-gate:**
  - **R-001 (Componentisation)** — new dialog is its own component
    (~250 lines, single responsibility); not inlined into the already-
    large detail page.
  - **R-003 (single source)** — `metadata.py` owns validation +
    direction flip; both `add_substitute` and `update_substitute` call
    it. No duplicated unit checks.
  - **R-005 (portable data access)** — migration uses portable types
    (Float, String, CheckConstraint with portable SQL), no engine-
    specific tricks; `build_metadata` is pure-Python.
  - **R-006 (clean migrations)** — non-idempotent add-with-CHECK,
    no guards.
- **Carry-over (deliberately not in scope):**
  - **Auto-compute swap quantity at cook time** using the ratio +
    `UNIT_TABLE`'s conversion factors. Considered; deferred per
    Anti-creep — the cook reads the ratio and applies, same as
    today. Revisit if usage shows a clear "I keep wishing the
    system did the maths" signal.
  - **Cross-dimension density tables** ("1 cup butter ≈ 226 g
    coconut oil") — currently allowed in the UI (just store what the
    user typed); not converted by any client code. Same future-phase.

## [RESOLVED] FU-046 — A1 theme chunks D–F regressed since "done"; CHANGELOG over-claims
- **Raised:** 2026-06-06 (A1 STEP 2 Chunk D verify/finish)
- **Type:** finding
- **What:** Quasar palette literals (`grey-N`, `red-N`, `orange-N`, etc.) had
  crept back into the codebase after the A1 work was declared done. ~12+
  surfaces had drifted off theme-token compliance.
- **Resolution (2026-06-26):** "A1c regression re-sweep" run.
  **Files touched: 16+.** Pattern applied per R-002's apply rule:
  - **Helpers + composables retyped to `string | null`** —
    `stockLevelLogic.ts`, `useStockStatus.ts`, the per-page colour
    computeds in `RecipesOverview`, `MyProductsPage`,
    `MealPlanShoppingSummary`, `SequentialBuilderDialog`,
    `PageErrorState`, `ShoppingListRailItem`, `ShoppingListDetail`,
    `DataImport`, `TriStateFilter`. Neutral / out-of-stock branches
    return `null`; templates handle `null` by dropping `:color` and
    adding `class="dora-text-muted"` (q-icon) or
    `class="dora-bg-sunken dora-text-secondary"` (q-chip / q-avatar).
  - **Clean semantic swaps** — `notifyTypeRegistration.ts` `'red-5'` →
    `'negative'`; `StockItemRow` expiry `'soon'` `'orange-9'` →
    `'warning'`; `AlertsPage` `dismissed` and `AuditLogSettings`
    `info`/`debug` → `'info'`; `DoraChat` inactive tab chip switched
    from `grey-4`/`grey-9` to `dora-bg-sunken` + `dora-text-secondary`
    classes.
  - **Dropped redundant props** — `ShoppingListDetail`'s two
    `track-color="grey-4"` `q-linear-progress` props removed (Quasar
    default track is theme-acceptable).
  - **R-002 carve-outs preserved** — `ScanOverlay.vue:59` `grey-4`
    (DEC-4 camera rings) untouched, as designed.
  - **Deferred to FU-313** — graduated severity / heatmap palettes
    (`models/alert.ts` 144-169, `models/location.ts` 41-45,
    `AlertsPage.vue` snoozed/read ladder, `AddToListButton.vue:247`
    `amber-9`, `StockItemDetailPage.vue:1640` `amber-9`). These need
    a designed token ladder (`--severity-N` / `--heatmap-N` in
    `tokens.scss`/`themes.scss`), not a mechanical swap. FU-313
    logged with the recommendation.
  - **Final inventory** (`grep` for any palette literal): 21 matches
    total — 1 carve-out (ScanOverlay/DEC-4), 20 deferred to FU-313.
    Zero unaccounted-for regressions.
  - **Verification:** `vue-tsc --noEmit` clean. Eslint shows one
    error in `StockItemRow.vue:644` — that's the pre-existing FU-312
    `no-misused-promises` issue on the waste-undo handler, not
    introduced by this sweep.

## [RESOLVED] FU-042 — Alerts bell count ≠ list count (badge excludes low + ignores snooze)
- **Raised:** 2026-06-06 (C-9 brief; feedback L438)
- **Type:** finding (reported bug — root cause found statically)
- **What:** Bell badge showed fewer than the dropdown lists. Two causes:
  (1) badge = `high_count + medium_count`, excluding low; (2) badge read raw
  backend counts while list filtered client-snoozed alerts.
- **Resolution (2026-06-26):** code fix landed in C-9.1 (2026-06-15); the
  in-browser smoke that gated the close was confirmed today via the
  invariant e2e, which is the binding contract.
  - **Server (`get_alerts.py`):** one canonical count per request —
    `actionable_count = len(active items in the actionable tier)`,
    returned alongside `items[]` / `snoozed[]` / `fyi_count` /
    `snoozed_count`. Snooze + dismiss are server-owned via
    `AlertInteraction`, pre-filtered into the right buckets, so they
    apply everywhere by construction.
  - **Client (`alertStore.ts:32`, `AlertsBell.vue:27`):**
    `badgeCount = computed(() => data.value.actionable_count)` — direct
    read, zero recompute. R-003 single source.
  - **Locked by passing e2e** —
    `test__alerts__actionable_count_equals_high_plus_medium_in_items`
    asserts `actionable_count == count(items where severity in
    {high,medium})` and the matching `fyi_count` / `snoozed_count`
    invariants. Companion test
    `test__alerts__snooze_moves_out_of_active_then_clear_restores`
    verifies snooze actually moves the item out of `items[]`. Both
    passing in today's run (425/429 full suite green).
  - Re-creating the reported bug would require breaking the e2e —
    impossible without an obvious test failure.
  - **Lesson for the ledger** — a "kept open for browser smoke" gate
    that's already enforced by a passing e2e on the exact invariant is
    a stale gate. The smoke was meant to catch a divergence the test
    already catches harder; closing on the test alone is sufficient.

## [RESOLVED] FU-020 — Recipe-detail substitute swap affordance (cook-mode-only for now?)
- **Raised:** 2026-06-05 (B8)
- **Type:** finding / open question
- **What:** B8 made substitute swapping a temporary cook-session action (cook
  mode only). The recipe-detail "Find substitutes" dialog is purely
  informational. Open question: should the detail page also let you swap?
- **Resolution (2026-06-26):** **decision — keep cook-mode-only**, no code
  change. User confirmed the current model is intentional. The
  detail-page dialog stays a read-only viewer (with its existing copy
  pointing users to cook mode for the actual swap). Rationale:
  - **Charter tiebreak (Effortless + Anti-creep)** — one swap mechanism
    is simpler than two; the saved recipe stays the canonical artefact.
  - **Clean ownership** — recipe detail = canonical recipe, cook mode =
    this session's swaps. No "pre-staged swap" concept to store / sync.
  - The "I want to plan ahead" use case is small and already covered by
    remembering at cook start; investing in a pre-stage surface would be
    surface bloat for marginal benefit.
  - If the use case ever grows, the cleanest fit is a per-ingredient
    swap dropdown on a **scheduled MealPlanEntry** (not the bare recipe
    detail) — captured here in case it comes back later.

## [RESOLVED] FU-006 — Migrate the remaining ~289 `q-btn` to BaseButton
- **Raised:** 2026-06-04 (A2 Phase 2); rescoped 2026-06-05; resumed 2026-06-26
- **Type:** deferred job
- **What:** A2 took the app from 399 → ~304 `q-btn`. The remaining ~289 were
  out of A2's scope (toolbar + "New X" only); this FU captured them as a
  genuine unplanned leftover.
- **Resolution (2026-06-26):** drained to **48** raw `q-btn` across the
  repo. Two passes today (continuing prior session's work):
  - **First pass** (this session, prior turn) — migrated ~17 sites and
    flagged 10 ambiguous ones in place with `// FU-006:` inline comments.
  - **Second pass / wrap-up** — every remaining raw `q-btn` falls into
    the FU's original explicit-exclusion list or a design-decision flag:
    - **3** wrappers (BaseButton, BaseDropdown, BaseSegmented — by design)
    - **17** MyProductsPage (products surface moving to companion app —
      Decision 1, FU's explicit exclusion)
    - **14** DoraChat (its own component; FU's explicit exclusion)
    - **5** q-input `#append` slots (search-clear / copy-to-clipboard pop-
      outs — FU's explicit exclusion)
    - **9** flagged ambiguous sites carrying inline `// FU-006:` comments
      — use a palette tone BaseButton doesn't model (`warning`, `accent`,
      `grey`, Quasar palette `secondary`), a dynamic colour binding
      (`RecipeCard` chef-hat, `ShoppingListDetail` shop-day tone), or
      `type="a"`. These are design calls (extend BaseButton's variant set
      vs accept raw), not mechanical work; the inline markers stay so the
      decision is locatable when someone reworks the surface.
  - The original FU explicitly disposed of itself as "Not no-regret; not
    urgent — opportunistic" — this state matches that disposition.
  - **`CardComponent.vue`** (1 entry in the previous count of 49) was
    confirmed dead/broken and deleted in this session — see FU-311.
  Verification: `vue-tsc --noEmit` clean.

## [RESOLVED] FU-005 — `q-btn-dropdown` / split-button wrapper component
- **Raised:** 2026-06-04 (A2)
- **Type:** deferred job
- **What:** 4 `q-btn-dropdown` + 6 `q-btn-toggle` usages were out of BaseButton's
  scope (different APIs); a wrapper would unify split-buttons.
- **Resolution (2026-06-26):** shipped in commit `37608e4` ("Partial
  resolution of FU-005 and FU-006") — **`BaseDropdown.vue`** wraps
  `q-btn-dropdown` (thin pass-through with `no-caps` default) and
  **`BaseSegmented.vue`** wraps `q-btn-toggle`. All 4 dropdown + 6
  toggle call sites migrated. The only files still containing raw
  `<q-btn-dropdown>` / `<q-btn-toggle>` tags are the two wrappers
  themselves — that's where they're supposed to live. Both
  `TriStateFilter.vue` and `settings/DoraSegmented.vue` reference the
  old pattern in code comments only. FU was closed in code but left
  open in the ledger by oversight; flipping now.

## [RESOLVED] FU-223 — pytest verify on stock-location / stock-group clear-flag changes
- **Raised:** 2026-06-18 (Stock-pages feedback pass)
- **Type:** finding — verification gap
- **What:** Same root cause as FU-189c — dev box had only the MS Store Python
  stub so pytest wasn't run in the original session that added
  `clear_stock_location` / `clear_stock_group` flags to `UpdateStockItemRequest`
  (writing the FK columns directly because the relationships are mapped
  `lazy="noload"` and the prior None-assignment was a silent no-op).
- **Resolution (2026-06-26):** verified in this session. `pytest
  tests/e2e/dora_api/test_stock_item_router.py` — **42/42 passing**, no
  regressions on the clear path. The fix held; no test fixture needed
  updating.

## [RESOLVED] FU-189c — Phase E: pytest verify still wanted (urgency lowered)
- **Raised:** 2026-06-18 (Phase E rename close-out)
- **Type:** finding — verification gap
- **What:** Phase E `Merchant → Store` rename + `usual_store_id` + Stores CRUD
  page + image upload landed under `vue-tsc` + `npm run lint` clean, but
  pytest wasn't exercised in the rename session.
- **Resolution (2026-06-26):** verified in this session. Full suite
  **425/429 passing** (`tests/e2e/dora_api` + the two unit test files). The
  4 remaining failures are FU-310 (auth/user `has_image` issue, completely
  unrelated to the rename — confirmed by stash-test on previous turns).
  Direct rename-surface tests are **80/80 green** —
  `test_store_router.py`, `test_product_router.py`, `test_ingestion_sources.py`,
  `test_ingestion_store_mappings.py`, `test_ingest_batch.py`. Stale
  `Merchant` references in the code: none (the surviving "merchant"
  mentions are domain-concept copy in docstrings + Dora chat tool
  descriptions — describing what a Store *holds*, not stale entity
  references). Migration head `f9d3a7c2b5e8` applies cleanly.

## [RESOLVED] FU-209 — Gate reframe: drop `products_enabled`, derive `features.products` from data-presence
- **Raised:** 2026-06-17 (products-as-overlay pivot)
- **Type:** deferred job (build)
- **What:** Replace the admin/persona `AppSetting.products_enabled` flag with
  a **server-derived** `features.products = (Product.count() > 0)`. Drop the
  column, its admin PATCH field, the DTO field, and the onboarding persona
  dimension; keep every per-surface `v-if="productsEnabled"` gate.
- **Resolution (2026-06-26):** browser-verified after two leak fixes; ledger
  flip. The Phase-A static work (column drop, migration `f1d5b8a2c4e6`,
  health-check derivation, onboarding/DTO removal, test rewrite) had landed
  in the 2026-06-17 session and was confirmed unrotted today —
  `tests/e2e/dora_api/test_onboarding_flags.py` 10/10 passing, single
  Alembic head `f9d3a7c2b5e8`, `vue-tsc` clean.

  **Two browser-pass bugs surfaced and fixed today:**
  1. **`MainLayout.vue` My Products nav unguarded.** The Product Search nav
     entry was correctly gated on `features.products.value`, but the
     literal `base.push({ label: 'My Products', ... })` two lines down
     wasn't — so the nav advertised the surface on a products-empty
     install. Fixed by wrapping the push in `if (features.products.value)`.
  2. **Product search URL setting visible on a products-empty install.**
     `AdminSystemFeaturesSettings.vue` exposed the URL input
     unconditionally. It's part of the products overlay, so it follows the
     same data-presence gate — wrapped the whole `<SettingsSection>` in
     `v-if="productsEnabled"` (added a `productsEnabled` ref from
     `useFeatureFlags`).

  **Full products-surface inventory after the fixes** (all gated on
  `features.products`):
  - `MainLayout` — Product Search nav entry ✓
  - `MainLayout` — My Products nav entry ✓ (today's fix)
  - `DashboardPage` — `best_deals` card (via `isCardVisible('best_deals')`
    → `gate: 'products'`) ✓
  - `StockItemDetailPage` — Products tab header (`tabDefinitions`) ✓
  - `StockItemDetailPage` — Products `q-tab-panel` ✓
  - `AdminSystemFeaturesSettings` — Product search URL section ✓
    (today's fix)

  **Carry-over (not in FU-209's scope, logged separately if needed):**
  - The route `/my-products` itself has no router guard — direct URL /
    bookmark still loads `MyProductsPage.vue` on a products-empty install.
    Proposal §2 said "keep every v-if gate — only the boolean's source
    changes"; locking the route is a separate hardening pass if desired.
  - `doraContextualActions.ts:154` suggests "Hunt for fresh deals" when on
    `/my-products` — dead code on products-off (unreachable), harmless.
- **Standards close-gate:** R-003 (single source of truth) — products is
  one server-derived fact via `/health`; no client-side counting. R-005/
  R-006 — migration `f1d5b8a2c4e6` clean, no idempotent guards, applies on
  PG and SQLite. **ADR candidate:** "data-presence-gated surfaces" pattern
  could be promoted to a new `R-0NN` if a second feature adopts it (e.g.
  ingestion overlays); not yet a recurring decision, hold for now.

## [RESOLVED] FU-311 — Delete dead/broken `CardComponent.vue`
- **Raised:** 2026-06-26 (surfaced by FU-006 q-btn sweep)
- **Type:** finding / dead code
- **What:** `web_app/src/components/CardComponent.vue` had no callers
  (`grep -rn "CardComponent" web_app/src` returned only self-references)
  and contained syntactically broken Vue: `::icon` typo, reference to
  the non-existent `ICONS.icon`, and a stray `fab` prop. Caught during
  the FU-006 q-btn→BaseButton sweep when it appeared in the inventory
  as an unmigrated raw `q-btn` site.
- **Resolution (2026-06-26):** file deleted. `vue-tsc --noEmit` clean
  post-removal — no callers, no orphan imports.

## [RESOLVED] FU-082 — Add `created_at` to Recipe DTO so "Recently added" sort axis can land
- **Raised:** 2026-06-09 (Cookbook Chunk 1; IMPL plan called for the axis)
- **Type:** finding / Phase-2
- **What:** `IMPL_PLAN_COOKBOOK.md` Chunk 1 listed five sort axes including
  `created-at`. Recipe DTO had no created timestamp, so Chunk 1 shipped
  four (`name`, `last_made`, `meal_count`, `total_time`).
- **Resolution (2026-06-26):** shipped end-to-end.
  - **Migration** `f9d3a7c2b5e8_20260626_recipe_created_at.py` — added
    `Recipe.created_at: DateTime(timezone=True)`; nullable add → backfill
    via `COALESCE(last_made_on, CURRENT_TIMESTAMP)` (one portable
    UPDATE) → tighten to NOT NULL. Backfill rationale: legacy rows with
    `last_made_on` keep their relative order; un-cooked legacy rows
    anchor at "now" and newer real creates simply sort above them, which
    matches the axis's "Recently added" intent.
  - **Schema:** `table_mappings.py` + `domain/entities/recipe.py` get
    the new column / field / `Recipe.Fields.CREATED_AT`.
  - **Write paths:** `create_recipe.py` and `new_recipe_version.py` both
    stamp `datetime.now(timezone.utc)` at construction. Seed (`seed.py`)
    accepts a `created_at` kwarg, defaulting to `now()`.
  - **DTO:** `RecipeDto.created_at` (positional, always populated post-
    backfill); `_FIELD_MAP['created_at']` so the standard
    `?sort=created_at:desc` query string works too if the cookbook ever
    moves off client-side sort.
  - **Frontend:** `models/recipe.ts` adds `created_at: string`;
    `RecipesOverview.vue` adds `'created_at'` to `SortKey` +
    STATIC_SORT_OPTIONS (label "Recently added"), a comparator
    (lexicographic on the ISO-8601 string with name tie-break), and the
    asc/desc tooltip phrasing ("Oldest first" / "Most recent first").
    The default-direction watch picks `desc` by exclusion (i.e. newest
    first), matching the rest of the non-name axes.
  - **Tests:** `tests/test_recipe_cookability.py` stub was missing
    `steps_mode` too (pre-existing rot) — fixed both attributes; 22 unit
    tests pass; full e2e suite **403 passed, 4 pre-existing failures
    unrelated to FU-082** (see FU-310). Frontend `vue-tsc` clean.

## [RESOLVED] FU-074 — Wire planned-shop-day into the real alert pipeline (C-9)
- **Raised:** 2026-06-08 (Chunk 7 impl)
- **Type:** finding (deferred-by-design)
- **What:** Chunk 7 surfaces planned-shop-day as a banner on the list detail.
  The IMPL plan said it "feeds C-9's new alert types" — the actual alert
  pipeline (alerts bell badge, suggestion-feed insertions, optional push)
  belongs to C-9.
- **Resolution (2026-06-26):** finished in two halves —
  - **Found already-shipped (C-9.4):** the `shopping_day` kind is
    registered in `alert_kinds.py` (FYI tier), emitted by
    `get_alerts.py::_shopping_day_alerts` for not-yet-done lists with
    `planned_shop_date` within `SHOPPING_DAY_WINDOW_DAYS` (3), de-duped
    via `list_alert_key(lst.id, "shopping_day")`, and clears when the
    list flips to `done`. Single-kind design (not the FU's original
    `shopping_day_today` / `shopping_day_overdue` split) — one alert per
    list with message/severity reflecting current state. Cleaner, since
    user snooze/dismiss on a list survives the date rolling forward.
  - **Gap filled in this pass:** the existing emitter only covered
    upcoming dates (`between(today, horizon)`) — overdue lists silently
    dropped out, even though the in-page banner tints overdue. Widened
    the query to `<= horizon` (covers past + upcoming), added an
    `if days < 0` branch that escalates severity to `medium` (still
    FYI-tier, so it doesn't inflate the bell badge — just sorts above
    plain upcoming nudges) and rephrases the message
    ("Shopping day was yesterday: …" / "Shopping day was N days ago:
    …" / detail "Mark it done or move the date."). Same `list_alert_key`
    so user decisions persist across the lifecycle.
  - **Tests:** new
    `test__alerts__shopping_day_overdue_fires_and_escalates_severity`
    covers both the overdue emission (severity=medium, "2 days ago" in
    message, tier=fyi) and the close-on-done behaviour. All 24
    `test_alerts.py` cases pass.
  - **Conftest collateral:** the FU-045 conftest pinned tests to
    `sqlite:///data/dora.test.db` (relative), which Flask resolves
    against its instance dir → `OperationalError`. Switched to an
    absolute path derived from the repo root + `as_posix()` so the e2e
    suite runs without any explicit env var.

## [RESOLVED] FU-071 — Desktop right-panel + mobile-top-dropdown list selector
- **Raised:** 2026-06-08 (Chunk 5 impl)
- **Type:** finding (UX polish per proposal §2.3 / feedback L405-L406)
- **What:** Proposal calls for a desktop **right panel** (always visible) and a
  mobile **top dropdown**. Chunk 5 shipped a single `q-btn-dropdown` shared
  across viewports as a viable interim. The dedicated right-panel layout
  (always visible on >=md, the dropdown collapses below that) is the next step.
- **Resolution (2026-06-26):** already implemented — closing on inspection.
  `ShoppingListDetail.vue` carries both surfaces, mutually exclusive via
  viewport classes:
  - **Desktop right rail** (lines 831–870, `.col-auto.gt-sm /
    .sld-rail`): always-visible `q-virtual-scroll` of every list,
    server-ordered, auto-scrolls to the active selection, with a
    "+ New list" ghost button on top and a "Manage templates…"
    router-link below.
  - **Mobile top dropdown** (lines 161–196, `.lt-md.full-width`):
    `BaseDropdown` hosting the same `railEntries` continuum via
    `q-virtual-scroll`, plus a "+ New list" entry at the top of the
    menu.
  Both use the shared `ShoppingListRailItem.vue` component for row
  rendering. The "single dropdown shared across viewports" interim is
  gone. Work landed in commit `d9ca58e` ("Fable 5 — shopping list
  rework") which introduced `ShoppingListRailItem.vue` and the
  `.sld-rail` layout; FU-071 was never flipped.

## [RESOLVED] FU-045 — Migrate to Postgres as the standard datastore (SQLite kept for lightweight self-host)
- **Raised:** 2026-06-06 (distribution posture — Decision 5 / §7.5)
- **Type:** deferred job
- **What:** Make Postgres the standard datastore for dev + hosted; SQLite stays
  supported as the zero-dependency lightweight self-host option.
- **Resolution (2026-06-26):** shipped the productionize switch.
  - **Driver:** added `psycopg[binary]==3.2.3` to `requirements.txt`
    (self-contained, no libpq required).
  - **Local Postgres:** new `docker-compose.yml` at repo root with a
    `postgres:16-alpine` service on `localhost:5432`, user/pass/db all
    `dora`, healthcheck wired. Default app config matches this service
    out of the box.
  - **Config resolution** (`configuration_manager.py`): rewrote
    `get_db_connection_string()`. Order: (1) `DORA_DB_URL` override —
    any SQLAlchemy URL, including `sqlite:///path/to/db` for SQLite
    self-host; (2) per-component env vars `DORA_DB_HOST` / `_PORT` /
    `_NAME` / `_USER` / `_PASSWORD`; (3) default to the docker-compose
    Postgres. Removed `_resolve_db_path` + the `DORA_DB_PATH` env var
    (collapsed into `DORA_DB_URL` per pre-release scope discipline; no
    compat shim).
  - **Startup guard** (`startup.py`): `migrate_legacy_db` (SQLite file
    relocation) now only runs when the resolved URL starts with
    `sqlite:///`. PG path skips it cleanly.
  - **Portable boolean defaults** — the SQLite-only `sa.text('0')` /
    `sa.text('1')` pattern is now extinct. Swept:
    - `table_mappings.py` × 24 — `Boolean, server_default="0"` /
      `="1"` → `server_default=false()` / `true()` (imported `false`,
      `true` from `sqlalchemy`).
    - 8 migration files × 12 sites — `sa.text('0')` / `sa.text('1')`
      → `sa.false()` / `sa.true()`. Renders `0`/`1` on SQLite and
      `false`/`true` on PG — portable both ways. Existing SQLite DBs
      unaffected (same DDL emitted).
  - **Raw-SQL boolean comparison** (`get_recipes.py:594`):
    `AND p.is_active = 1` → `AND p.is_active` (bare boolean predicate
    works on both engines; PG would reject `boolean = integer`).
  - **Tests** (`tests/e2e/dora_api/conftest.py`): pin the e2e suite to
    a SQLite temp file (`sqlite:///data/dora.test.db`) via
    `os.environ.setdefault("DORA_DB_URL", ...)` at module top, before
    `dora_api.app` import. Tests stay zero-dependency and don't
    require a running Postgres.
  - **Docs:** `README.md` quickstart now leads with
    `docker compose up -d postgres`; SQLite fallback documented via
    `DORA_DB_URL=sqlite:///...`. `path_migration.py` docstrings
    updated for the new env var.
  - **Verified:** `drop_all + create_all` clean on SQLite with the new
    defaults; introspected DDL confirms `is_admin`/`deals_email_enabled`
    /`show_recipe_images` defaults all rendered correctly. All
    migrations py_compile clean.
- **Carry-over** (not blocking the close):
  - **Live PG run** — only the user can confirm `docker compose up -d
    postgres && flask db upgrade && python -m dora_api.startup` boots
    cleanly end-to-end on this host. Recommended browser smoke after.
  - **Raw `text()` queries with UUID binds** — already used `str(uuid)`
    on the bind side (works on both engines) and `_coerce_uuid` on
    the return side (accepts `UUID|bytes|str`, so portable). Worth a
    confirm on real PG that no driver-specific casting surprises us
    (psycopg returns native UUID, SQLite returns bytes — both handled).
  - **Postgres CI lane** is not part of this change; if you want one,
    spin a follow-up.

## [RESOLVED] FU-023 — A5 leftover: spinners not yet migrated on deferred surfaces
- **Raised:** 2026-06-05 (A5)
- **Type:** leftover
- **What:** A5 unified loading on the active app pages, but left raw `q-spinner`
  on the **deferred surfaces** (Reports, Data→Export/Print, Settings sub-pages —
  per the prompt-pack "deferred" list) and on **DoraChat's typing dots** (a
  deliberate `q-spinner-dots` indicator).
- **Resolution (2026-06-26):** swept all 19 raw `q-spinner` / `q-spinner-dots`
  sites in app code. Migrated to `AppSpinner`:
  - Settings sub-pages — `RecipeDietaryTagsSettings`, `StockLocationsSettings`,
    `StockGroupsSettings`, `UsersAdminSettings`, `ApiAccessSettings`,
    `AdminSystemAssistantSettings` (the dots indicator there switched to
    `AppSpinner` for A5 consistency — distinct from DoraChat's typing
    dots, which stay).
  - Settings components — `VocabListEditor`, `VoicePicker` (×2 small
    inline sites).
  - Reports — `ReportsPage` ×6 (one per chart card's loading state).
  - Data → Export/Print — `ExportPrint` ×2.
  - Dora — `PriceHistoryBottomSheet` (chart load).
  - **DoraChat.vue:270 `q-spinner-dots` kept** as the intentional typing
    indicator per the FU note.
  Final inventory: only `AppSpinner.vue`'s own internal `<q-spinner>`
  and `DoraChat`'s typing dots remain. `vue-tsc --noEmit` clean.
- **Carry-over (out of scope here):** the FU also mentioned list-skeletons
  as a nicer touch on big overviews; that's still a polish-pass call,
  folded into FU-010 (holistic look review). Not a new follow-up — the
  spinner migration itself is now done.

## [RESOLVED] FU-018 — B7: wider sweep for "store mutation + page toast" double-emits
- **Raised:** 2026-06-05 (Wave-B self-audit)
- **Type:** finding
- **What:** B7's "no other double-toast patterns" verdict only walked
  `useShoppingListActions.addItems` callers. Same pattern could exist
  for any store mutation that toasts internally and a page handler that
  toasts on success after. Worth grepping for `$q.notify` and
  `notifyOk` calls inside store/composable methods, then cross-checking
  every caller for a follow-up notify.
- **Resolution (2026-06-26):** sweep run. Composables that toast
  internally: `useStockItemActions` (addToList/markRestocked/pushExpiry),
  `useShoppingListActions` (addItems/removeFromList/removeFromAllLists/
  finishShopping), `useMealPlanner` (~17 sites), `useRecipeExport`,
  `useStockOverviewExport`, plus the three infra composables
  (`useNetworkStatus`, `useOfflineQueue`, `usePwaLifecycle`). Pinia
  stores: **no internal notifies anywhere** (confirmed by grep). Walked
  every caller of every notifying composable — **no double-toast
  double-emits found**: not a single caller adds its own success toast
  after a composable success notify. B7's worry doesn't recur.

  **Adjacent finding fixed in the same pass:** `StockOverview.bulkAddToPrimary`
  and `StockOverview.bulkRestock` were `for…await`ing the single-item
  composable methods, so a bulk selection of N items fired N per-item
  toasts ("Added to list.", "Marked restocked." × N). Not the audited
  "double-emit" pattern per se, but the same family. Fixed by adding an
  optional `{ silent?: boolean }` flag to `addToList` and `markRestocked`
  in `useStockItemActions.ts`; the two bulk handlers now pass `silent:
  true` and emit one summary toast ("Added N items to your list.").
  `vue-tsc` clean.

## [RESOLVED] FU-012 — FilterBar panel has no visual container
- **Raised:** 2026-06-05 (A4)
- **Type:** finding
- **What:** `FilterBar`'s collapsible panel was a plain div. StockOverview had
  grown a page-scoped `:deep(.filter-bar__panel)` treatment (surface-elevated
  card + 1px inset tint border + 8px radius) to pair with its bulk-select
  banner, but RecipesOverview and MyProductsPage still rendered the panel
  bare — inconsistent across the three FilterBar consumers.
- **Why deferred:** the other pages never had a container; whether the panel
  wanted subtle containment was a design call.
- **Resolution (2026-06-26):** moved styling onto `FilterBar.vue` itself
  (`<style scoped>`) so every consumer picks it up. Switched to a calmer
  **sunken well** treatment — `background: var(--surface-sunken)` + 6px
  radius, no border — instead of an elevated card. Reads as a recessed
  tool tray tucked under the toolbar rather than another card on an
  already-card-heavy page, and works on pages without a paired bulk
  banner. StockOverview's `.dora-subbar` (bulk banner) re-tuned to the
  same sunken treatment so the two sub-bars still feel like siblings;
  its previous `:deep(.filter-bar__panel)` overrides removed.
  `vue-tsc` clean.

## [RESOLVED] FU-011 — AuditLogSettings filtering not standardised
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
- **Resolution (2026-06-26):** no action needed. (1) The A4 "FilterBar"
  target no longer exists as a component — `web_app/src/components/filters/`
  contains only `TriStateFilter.vue`, so there is nothing to standardise
  onto. (2) `AuditLogSettings.vue` has since been folded into the
  standardised settings shell through the Settings rebuild + subsequent
  passes (uses `SettingsPageHeader`, `BaseButton`, `BaseDialog`, the
  `settings-page` layout, `settings-divider`, and theme tokens — same as
  every other settings sub-page). (3) The original deferral note already
  pointed out that the filtering is server-side and therefore a poor fit
  for a client-predicate FilterBar; that reasoning resolves rather than
  defers the FU now that the rebuild has happened.

## [RESOLVED] FU-004 — Collapse `themeService.ts` THEMES dict into CSS-var reads
- **Raised:** 2026-06-04 (A1b)
- **Type:** finding
- **What:** 7 themes still have the dual-source coupling between the `THEMES`
  palette dict in `themeService.ts` and `themes.scss`. Their values currently
  match (Pesto / Pesto Dark / Lemon Tart Dark were synced), but it's a latent
  drift hazard.
- **Why deferred:** values match today, so it doesn't block anything.
- **Resolved (2026-06-26):** dropped the `palette: { … }` field from all 10
  `THEMES` entries in `themeService.ts`. `applyThemeKey` now sets
  `data-theme="x"` first, then `syncQuasarPaletteFromCssVars()` reads the
  active values back via `getComputedStyle(documentElement).getPropertyValue`
  and pushes them into Quasar's `--q-*` palette via `setCssVar`. The
  bridge map `QUASAR_PALETTE_FROM_CSS_VAR` is the only place the
  TS→SCSS coupling lives now — and it's by *key name*, not by hex value.
  Single source of truth = `css/themes.scss`. `ThemePalette` interface kept
  (used by `helpers/stockLevelLogic.ts` via `nameOf<>` as a compile-time
  key-set contract). Removed ~140 hex strings from the TS file; vue-tsc +
  eslint clean. Adding a new theme is now a 1-step change (SCSS block +
  picker-metadata row in `THEMES`; no palette values).

---

## [RESOLVED] FU-002 — LoginPage `--lp-*` token ladder revisit
- **Raised:** 2026-06-04 (A1)
- **Type:** deferred job
- **What:** `LoginPage.vue`'s private `--lp-*` colour ladder was deliberately left
  untouched (DEC-2 — intentional splash).
- **Why deferred:** it's a one-off intentional design, not theme drift.
- **Resolved (2026-06-26):** folded into the **C-19 (shared auth-shell)**
  prompt scope in `docs/03_prompts/C_big_rock_design_briefs.md`. The note
  about the lp-* ladder + the keep/promote decision now lives inside that
  prompt's body, so whoever runs C-19 sees it without needing a separate FU
  pointer. No code touched; the ladder stays as-is until C-19 runs.

---

## [RESOLVED] FU-122 — Browser-verify Stock Overview Chunk 3 (row rebuild + image toggle)
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
- **Resolved (2026-06-26):** user confirmed the row layout, level picker,
  zone filter, status outlines, bulk selection fill, image toggle (incl.
  PATCH /me persistence), no chip regressions, and virtualised list all
  behave as specified in the browser. No defects logged.

---

## [RESOLVED] FU-293 — DashboardPage R-001 de-monolith (DashboardCard extraction)
- **Raised:** 2026-06-24 (Dashboard rebuild, deferred across Phases 0–7).
- **Type:** finding (R-001 — componentisation).
- **What:** `DashboardPage.vue`'s 15 inline card shells repeated the same
  `<article/router-link class="dora-card"><header class="dora-card-head">…`
  boilerplate; the shell SCSS lived in the page.
- **State note (resolved 2026-06-24):** extracted
  `web_app/src/components/dashboard/DashboardCard.vue` — a shell that renders a
  `<router-link>` when `to` is set (whole-card nav) or `<article>` otherwise,
  with `icon`/`title` props (+ `#title` slot for rich titles like cookable's
  count), an `#action` header slot, and the body default slot. All 15 card
  instances converted to `<DashboardCard>`. Moved the shell styles
  (`.dora-card*`, head/icon/title/action/link/clickable + hover + reduced-motion)
  into the component, using the **global** theme tokens directly (not the page's
  private `--c-*` aliases, which scoped child styles can't inherit); the action/
  link styling uses `:deep()` since the `#action` slot content carries the
  parent's scope. Card BODY SCSS stays in the page (slotted content keeps parent
  scope). `vue-tsc` + `eslint` green. **Visual no-regression check folded into
  FU-301** (the extraction's only residual risk is CSS, browser-verifiable).

## [RESOLVED] FU-232 — Companion / ingestion contract: push `pack_count` on Product
- **Raised:** 2026-06-23 (FU-227 multipack follow-up).
- **Type:** deferred job.
- **State note (resolved 2026-06-23):** wired through in
  `dora_api/features/ingestion/submit_ingestion_batch.py`. Added
  `pack_count: int | None = Field(default=None, gt=0)` to `_ProductIn`;
  threaded through both `_apply_product` paths (`existing.pack_count =
  raw.pack_count or existing.pack_count` for update; `pack_count=raw.pack_count`
  on create). Docs updated: `INGESTION_GUIDE.md` (new row in the products
  table with the "size_value is the total across the bundle" note) +
  `PROPOSAL_INGESTION_API.md` (catalogue field list + §2.2 payload sketch).
  New pytest `test__ingest__pack_count_round_trips_on_product` in
  `tests/e2e/dora_api/test_ingest_batch.py` asserts create-with-pack,
  no-overwrite-on-null-republish, and `gt=0` rejection. Static-only —
  needs a Python env to run (no env on this machine).
- **What:** the in-app side of multipack pricing is wired — observations now
  carry `pack_count`, the PriceEntry widget exposes it as a disclosure
  ("Add pack count (multipack)"), the obs list renders "4 × 125g", and the
  harvest path at `/finish` reads `Product.pack_count` to populate it. But
  **the producer-facing contract still doesn't accept pack_count.** The
  `_ProductIn` model in `submit_ingestion_batch.py` accepts
  `{size, size_unit, size_value}` but not the new column. Producers that
  want to push "Activia 125g × 4 pack" today must flatten `size_value=500`
  (the existing convention — `size_value` is the TOTAL across the bundle)
  and lose the structured pack-context.
- **Why deferred:** the schema column is in place
  (migration `d7b3e8f2a5c4`) and the existing user-side surfaces work
  without the producer push (default = NULL). The contract change is its
  own piece of work — needs producer-side coordination, doc updates,
  acceptance test for the field round-trip, decision on whether to also
  accept multipack metadata on `offers[]` or just `products[]`.
- **Recommended resolution:** when the next companion / ingestion-contract
  work lands. Add `pack_count: int | None = Field(default=None, gt=0)` on
  `_ProductIn`; thread it through the upsert in `_apply_product`; update
  `INGESTION_GUIDE.md` and `PROPOSAL_INGESTION_API.md` to document the
  field; add a pytest asserting it round-trips on the Product row.

## [RESOLVED] FU-180 — Reassess "preferred product" before commercialise (Phase 4)
- **Raised:** 2026-06-14 (preferred-product removal sweep)
- **Type:** open decision
- **State note (resolved 2026-06-23):** closed fully. The product-side intent
  is met by **`PreferredBuy`** (free-text per stock item, FU-211) plus
  **`StockItem.usual_store_id`** (per-item store, FU-189 Phase E) — together
  they cover "remember my favourite product" + "where I usually buy this"
  without resurrecting the deleted per-item enum. The residual app-wide
  preferred-*store* question (one annotation that sorts/pre-selects across
  all items) is **not worth carrying as an open FU**: cheapest-first sort +
  per-item `usual_store_id` already cover the practical case, and an
  app-wide layer is cheap to add later if real usage demands it. The
  onboarding preferred-stores capture (feedback L45, folded in 2026-06-15)
  is dropped on the same grounds — no capture step in onboarding; users can
  set `usual_store_id` opportunistically as they shop. Original spec L66 /
  Unprocessed-Ideas #48/49/52 stay parked in `00_original_spec` as
  historical intent; no rebuild planned.
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
- **Update 2026-06-17 (products-as-overlay pivot):** the everyday "remember my favourite products"
  intent is now met by **`PreferredBuy`** (free-text, on the stock item — FU-211), distinct from
  the *preferred-merchant* sort/loyalty question this FU still owns. So the product side of this
  reconsideration is largely addressed by PreferredBuy + `usual_store_id`; what remains open is
  whether a preferred-*store* affordance (sort / pre-select) earns its keep.

## [RESOLVED] FU-227 — Pricing system reassessment: "Your prices" intelligence (8 chunks shipped)
- **Raised:** 2026-06-19 (pricing reassessment handoff).
- **Ratified:** 2026-06-22 — the §6 question list A–K fully walked with the user;
  all answers, revisions, and clarifications LOCKED.
- **Type:** planning + implementation (Phase F's "Your prices" / S2-10 build).
- **State note (resolved 2026-06-22):** all 8 chunks landed. Chunk 1 — unit-
  conversion helper + count dim + SPA mirror dedup. Chunk 2 — observation
  reshape (folded shape, store_id, FK provenance, partial UNIQUE) + migration
  `c6e9a4b8d5f2`. Chunk 3 — shared `PriceEntry` + row-overview button + inline
  `YourPricesWidget` on stock-item detail. Chunk 4 — `build_your_prices_for_item`
  (median / 1.15× strict-greater / min-3 / trailing 12mo / per-dim B4 / LC-2
  source-blind / offers sidecar). Chunk 5 — shopping-line prefill +
  `/finish` harvest + I1 Receipt relabel + K2 ladder extract + E3
  PATCH-status-done removal. Chunk 6 — `PriceHistoryBottomSheet` (C5b)
  + per-product observation overlay (H2 fallback) + baseline reference
  line (F-3) + D2 colour-coding. Chunk 7 — removed the `stock_item_ref →
  observation` ingestion branch (J1) and trimmed `price_observations[]`
  from the contract entirely. Chunk 8 — promoted seed-data discipline to
  **R-017** in `ENGINEERING_STANDARDS.md` + ADR-012; filled the feedback
  coverage table in the plan; updated `COVERAGE_GAPS.md` audit log
  (flipped L226/L419/L420 to ADDRESSED); moved this entry to resolved.
- **What it left behind:** **R-017** (new standing rule, every future
  feature-touching prompt picks it up automatically). FU-228 (Phase E
  rename test rot — pre-existing, surfaced by the chunk-1 full-suite run).
  FU-229 (`reports.py` spend-by-store ignores `actual_unit_price` — surfaced
  during the K2 ladder extract). FU-230 (offers-sidecar noload —
  fixed in chunk 6, still wants a browser confirm). FU-231 (chunk 5 status=done
  test fallout — fixed in chunk 6). The browser walk of the C5 state matrix
  is the user's at the close-gate.
- **Plan doc:** `docs/04_proposals/IMPL_PLAN_YOUR_PRICES.md` (the 8-chunk
  spec) — feedback coverage table (§5) filled at chunk 8.
- **Handoff doc:** `docs/99_scratch/PRICING_SYSTEM_REASSESSMENT_HANDOFF.md`
  — the source of truth for every ratified decision (§6 / §6a / §6b /
  LC-1..LC-5). Keep for audit; future reassessments cite it.

## [RESOLVED] FU-225 — Deprecate `PreferredBuy.position` + reorder endpoint
- **Raised:** 2026-06-18 (Stock-pages feedback round 3)
- **Type:** deferred job
- **What:** Round-3 dropped the manual reorder UI on preferred buys (SPA now
  sorts alphabetically client-side). The backend still carried the `position`
  column on the table and exposed `PATCH /stock-items/{id}/preferred-buys/reorder`
  + `stockItemApi.reorderPreferredBuysAsync` on the SPA's API service. Nothing
  called them anymore.
- **State note:** 2026-06-18 — Dropped end-to-end. Backend:
  `PreferredBuy.position` removed from the entity, table mapping, and detail
  DTO; sort is now alphabetical (case-insensitive label) server-side, matching
  the SPA. The `reorder` route + handler method gone. New Alembic migration
  `b5d8a2f4c9e7_20260618_drop_preferred_buy_position.py` drops the column.
  SPA: `reorderPreferredBuysAsync` removed from `stockItemApiService`,
  `position` removed from `PreferredBuy` in `models/stockItemDetail.ts`.
  vue-tsc + lint clean. **Pytest not run (same standing posture as FU-189c /
  FU-223 — bundle on the next Python-equipped session).**

## [RESOLVED] FU-189b — Charter coverage table for Stores CRUD + image upload page
- **Raised:** 2026-06-18 (Phase E rename)
- **Type:** doc gap
- **What:** Phase E landed without flipping the per-surface feedback-coverage
  rows in `PROPOSAL_PRODUCTS_AS_OVERLAY.md` for the now-built Stores admin
  page.
- **State note:** 2026-06-18 — Flipped L184 ("Link button as merchant logo")
  from TRACKED → ADDRESSED, citing the user-uploaded `StoreLogo` with
  hash-swatch fallback rendered on ProductChip / StockItemDetailPage linked-
  products / MyProductsPage / Stores admin grid. L157 (the parallel "merchant
  vs data-provider conflation" row) was already ADDRESSED in the same table.
  No code change — proposal-doc edit only.

## [RESOLVED] FU-024 — A7 leftovers: dead banner CSS + wider footer adoption
- **Raised:** 2026-06-05 (A7)
- **Type:** leftover
- **What:** (a) Removing StockOverview's summary banner left its scoped
  `.stock-summary-banner` / `.stock-summary-stat` CSS unused (harmless dead
  rules). (b) `PageCountsFooter` is only wired on the 3 prompt pages
  (StockOverview, RecipesOverview, MyProductsPage); other list pages
  (ShoppingLists, MealPlans, etc.) could adopt it for consistency.
- **Why deferred:** dead CSS is harmless; broader adoption was out of A7's
  defined scope (3 pages).
- **State note:** 2026-06-18 — Deleted the dead `.stock-summary-banner` /
  `.stock-summary-stat` rules from `web_app/src/pages/StockOverview.vue`'s
  scoped style block (about a dozen lines). vue-tsc + lint clean. The
  "wider footer adoption" half is dropped — opportunistic and the user no
  longer wants it tracked; will surface naturally as the other list pages
  get touched.

## [RESOLVED] FU-113 — Browser-verify C-cross Chunk 4 (location-display policy)
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
- **State note:** 2026-06-18 — Marked resolved by user request. The
  location-display policy has been live since the Chunk-4 ship and the
  surrounding feedback rounds (Stock Overview row, detail-page picker,
  CreateStockItemDialog) have all exercised the zone-vs-full-path code
  paths without regression. User has been operating the app and is
  satisfied.

## [RESOLVED] FU-219 — Companion FE — port `ProductSearch.vue` + `MerchantsSettings.vue` into `../dora-companion`
- **Raised:** 2026-06-17 (Phase C build)
- **Type:** deferred job (port — sibling repo)
- **What:** The companion's headless scrape → `POST /api/push` → Dora's `/api/ingest`
  round-trip landed in Phase C.2; the browsable UI was deferred. FE was needed to host the
  scraper provider toggles + a product-search UI that pushes per-card or in batches.
- **State note:** 2026-06-17 — **RESOLVED.** Scaffolded a Vue 3 + Quasar + Pinia SPA in
  `../dora-companion/web_app/`: Vite + TS (no Quasar CLI — lighter than Dora's tooling). Three
  pages: **Product search** (full port of Dora's `ProductSearch.vue` — search input, merchant
  chips, filters, sort, comparison-style selection — with the Dora-only branches **stripped**
  (saved-product, link-to-stock-item, quick-add) and **per-card + batch "Push to Dora"**
  added); **Merchants** (port of `MerchantsSettings.vue` — list, enable/disable, provider
  health, health-check); **Dora target** (read-only — friendly label only; the real URL +
  bearer live in the BE env). Two services: `MerchantsApiService` (collapses Dora's two
  split clients) and `ProductSearchApiService` (search + push). Push results dialog surfaces
  Dora's per-record `accepted / skipped / failed`; pending store-mapping nudges the user back
  to Dora's API access page (FU-190 honoured end-to-end). New `MerchantsApiService.pushAsync`
  hits the companion's `POST /api/push` which then scrapes + forwards to Dora's
  `POST /api/ingest`. Mapi CORS now allowlists `http://localhost:5175` in dev. Build green:
  `npm install` (226 packages), `vue-tsc --noEmit` clean, `vite build` clean (~82 KB main
  gzipped). README updated. Phase C now fully done (.1 + .2 + .3).

## [RESOLVED] FU-212 — Power-user docs: how to source product data so the overlay lights up
- **Raised:** 2026-06-17 (products-as-overlay pivot)
- **Type:** documentation
- **What:** Document the path to *enabling* products for power-users (the end-user flow never
  meets this): the always-accessible API access page, the `POST /api/ingest` contract, the
  no-auto-create-stores mapping (FU-190), the data-presence gate, the Product Search URL.
- **State note:** 2026-06-17 — **RESOLVED.** Added `docs/INGESTION_GUIDE.md` covering: (1) what
  lights up when product data is present (My Products / Price History / per-stock-item Products
  tab); (2) minting a key on Settings → API access (one-time reveal, label, disable/revoke);
  (3) the store-mapping pre-map vs auto-quarantine flow; (4) the full `POST /api/ingest`
  contract (auth, Idempotency-Key, products/offers/price_observations schemas, dedupe keys,
  result DTO with stable `reason` codes); (5) the Product Search URL carve-out (data-gated,
  producer unnamed); (6) trust tiers. Index entry added to `docs/00_DOCS_INDEX.md`.
  Producer/companion deliberately **never named** anywhere in the doc — phrasing is
  "any external source you run". Power-user oriented (admin/help), not onboarding-facing.

## [RESOLVED] FU-217 — Refactor `create_product` to share the offer-append mapping (C-10 follow-on)
- **Raised:** 2026-06-17 (Phase B build; PROPOSAL_INGESTION_API §6.2)
- **Type:** deferred job (refactor)
- **What:** `POST /api/products` (`create_product.py`) used to 409 on a duplicate without
  appending a historic point, so manual product-add didn't accrue price history. R-003 violation
  by way of `/api/ingest` having its own append path.
- **State note:** 2026-06-17 — **RESOLVED.** `create_product` now calls
  `apply_offer_to_product` (the C-10.2 shared helper) when the product already exists: appends a
  new `ProductHistoricOffer` + moves `current_offer` instead of returning 422. Idempotent — the
  same (product, observed_at, price_now) tuple still dedupes. Response now returns 201 with
  `{id, created, offer_appended}` (was `id` only); the existing successful-create test still
  passes (the body is a superset), and the dup-409 test was rewritten to assert append (FU-217
  test in `test_product_router.py`). Source string `"manual"` distinguishes these points from
  ingest-provenance points. Full pytest 401/401, `vue-tsc` + lint clean.

## [RESOLVED] FU-178 — Full-chain SQLite `flask db upgrade` is broken (batch-mode constraint naming) — prod-SQLite boot blocker
- **Raised:** 2026-06-14 (surfaced by C-2.K's scratch-DB migration check)
- **Type:** finding (pre-existing defect; **blocked fresh SQLite prod boot**)
- **What:** Running the migration chain base→head on a fresh SQLite DB failed at
  **`d7c9e4a8c2b1_20260612_shopping_list_line_product_anchor.py:29`** —
  `with op.batch_alter_table('ShoppingListLine')` raised
  **`ValueError: Constraint must have a name`**. Alembic batch mode on SQLite
  recreates the table and re-adds its constraints; with no `naming_convention`
  configured, anonymous constraints couldn't be reproduced. Suspected several
  later batch migrations shared the issue (`b9e5c2a78f31`, the FU-163
  `drop_finish_snapshot` batch op, …); the chain just died at the first.
- **State note:** 2026-06-17 — **RESOLVED via hard cutover (pre-release, no
  prod data to preserve).** Added `NAMING_CONVENTION` to `dora_api/app.py` and
  attached it to the SQLAlchemy `MetaData`; threaded it into Alembic's
  context in `dora_api/persistence/migrations/env.py`; **wrapped
  `op.batch_alter_table` in `env.py`** so every batch op inherits the
  convention without each call site having to pass `naming_convention=`.
  Promoted to standing rule **R-015** + **ADR-010** in
  `docs/01_charter/ENGINEERING_STANDARDS.md`. **Verified:** fresh SQLite
  `flask db upgrade base→head` now runs the entire chain clean to head
  `c4e6a8b1d3f5`; full pytest 381/381 still green. Downgrade-from-head to
  base still trips on a handful of legacy migrations that hard-coded
  `ck_*`-prefixed literal names (double-prefix under the convention) —
  **accepted**; downgrade-from-head is not a product flow (dev resets go
  through `drop_all`/`DORA_ALLOW_DESTRUCTIVE`, prod hasn't shipped). Future
  migrations follow R-015 (bare-suffix literals only).

## [RESOLVED] FU-182 — Treat the minimal/Products-off user as a first-class workflow
- **Raised:** 2026-06-14 (talk-time assessment); refined 2026-06-15; promoted to proposal
  2026-06-15 (`docs/04_proposals/PROPOSAL_SIMPLE_MODE.md`).
- **Type:** open decision / design follow-up
- **What:** Treat "Products off" / the minimal user as a first-class workflow via the
  `products_enabled` flag + a per-surface sweep, with "Simple mode" as a named identity and a
  Money×Products 2×2 that onboarding personas had to reach all four corners of.
- **State note:** 2026-06-17 — **SUPERSEDED** by `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md`.
  The premise changed: Products is no longer a user-set flag / persona / "mode" but a
  **data-presence overlay** (on iff product data is ingested), with no user toggle and no
  onboarding persona — so "Simple mode as an identity" and the 2×2 onboarding problem dissolve
  (the everyday experience *is* the app). Surviving pieces (the price substrate, `usual_store_id`,
  the price-entry surfaces) are carried into the new proposal; the implementation is re-tracked as
  its build chunks: **FU-209** (gate reframe), **FU-210** (onboarding de-persona), **FU-211**
  (PreferredBuy), **FU-213** (price substrate). FU-189/FU-190 remain prerequisites and stay open.

## [RESOLVED] FU-185 — Stock Item Detail recipe-tab actions are dead (B8 residue)
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
- **State note:** 2026-06-16 — wired both listeners on `StockItemDetailPage.vue` in **C-1b.4**.
  `@toggle-favourite="onToggleFavourite"` mirrors `RecipesOverview` (calls
  `recipeStore.toggleFavouriteAsync`). `@add-all-to-list="onAddAllToList"` collects the recipe's
  ingredient stock-item ids and pushes them via `slActions.addItems` to the inferred primary draft
  (lightweight path; the richer per-ingredient picker stays in `RecipesOverview`). Browser
  verification of the fix rolls up under FU-202 (now extended for the C-1b.4 acceptance).

## [RESOLVED] FU-201 — Production frontend build is broken (4 lint errors gate it)
- **Raised:** 2026-06-16 (senior/tech-lead review — `docs/99_scratch/SENIOR_REVIEW_2026-06-16.md`)
- **Type:** finding (ship-blocker)
- **State note (2026-06-16):** **resolved** — removed the 4 dead symbols
  (`useStockFilters.ts` `stockLevelName` + `recipesByStockItem`, which also orphaned
  `stockLevelById`; `RecipeDetailPage.vue` `stockActions` + its `useStockItemActions` import;
  `AboutSettings.vue` `ICONS` import). `npm run lint` clean and `npm run build` (quasar SPA)
  succeeds. The "should land with a CI gate" recommendation is **already satisfied**:
  `.github/workflows/ci.yml` already runs lint + `vue-tsc --noEmit` + build + pytest — the break
  would have lit up red in CI. The real gap was that the handoff "green static-verified" claim
  was never locally built; CI config itself is correct. (If merges aren't actually blocked on CI,
  that's branch-protection config, outside the codebase.)
- **What:** `npm run build` failed via `vite-plugin-checker`'s ESLint lintCommand on 4 unused symbols.

## [RESOLVED] FU-193 — Verify C-5.3 + C-5.4 + C-5.5 backend on a provisioned machine
- **Raised:** 2026-06-16 (Onboarding C-5.3)
- **Type:** deferred verification
- **State note (2026-06-16):** **resolved backend** on the now-provisioned machine
  (Python 3.11.15 + `.venv`). Added `tests/e2e/dora_api/test_onboarding_flags.py` (6 tests);
  full suite **303 pass** (was 297). Verified: `products_enabled` defaults True and round-trips
  via `GET`/`PATCH /api/app-settings` with `/api/health features.products` agreeing (single source
  of truth); `household_headcount` round-trips via `PATCH /api/auth/me` (1–99, null clears) and
  surfaces on `/me`, with out-of-range (0, 100) rejected 400; `GET /api/onboarding/catalog`
  serialises groups + nested location nodes + **5** starter packs; `POST /api/onboarding/seed-items`
  creates **pre-located** items (group/location resolved by name) and is **idempotent** on re-run
  (created:1→skipped:1, no duplicate). Alembic **single head** confirmed (`e2a9c5f1b7d4`); both new
  migrations are trivial batch `add_column`/`drop_column` with a linear revise chain — well-formed.
- **Caveat (not a regression of these migrations):** a clean **full-chain SQLite `flask db upgrade
  head`** still fails at the pre-existing `d7c9e4a8c2b1` (2026-06-12 shopping-list product anchor)
  with "Constraint must have a name" in batch mode — that's **FU-178**, upstream of these two
  migrations, so the new migrations' full up/down round-trip can't be exercised through the chain on
  SQLite until FU-178 is fixed (or on Postgres, FU-196). The DDL was verified by reading + the
  behavioural round-trips above (test env builds schema via ORM `create_all`).
- **Remaining (separate FUs):** the **browser** verification of the cook-mode serving scaler
  (household_headcount) and the persona-fork UI lives in **FU-192**; this entry covers backend only.
- **What:** behavioural backend coverage for the Onboarding C-5.3/.4/.5 flags + endpoints.

## [RESOLVED] FU-191 — First-item group/location pickers empty during onboarding (deferred-seed ripple)
- **Raised:** 2026-06-16 (Onboarding C-5.1)
- **Type:** leftover / known limitation
- **State note (2026-06-16, C-5.5):** **resolved** — the first-item flow is now **name-based**.
  Items are queued with a group/location *name* and created on Finish by the new
  `POST /api/onboarding/seed-items`, which resolves names against the catalogues seeded earlier in
  the same apply. The first-item pickers offer names from the chosen default groups + any starter-pack
  groups + existing rows, so a fresh user CAN categorise their first item against a default group.
  (Backend round-trip verification rides with **FU-193**.)
- **What:** C-5.1 deferred the catalogue seed to Finish, leaving the first-item group/location
  pickers empty (no ids existed at pick time). The fix needed name-based resolution — C-5.5's
  starter-data mechanism — which is what shipped.

## [RESOLVED] FU-172 — Execute IMPL_PLAN_MEAL_PLANS (C-2.A…K)
- **Raised:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS authored from C-2 proposal)
- **Type:** deferred job
- **State note (2026-06-14):** **all 11 chunks built + static-verified** —
  build order ran A, B, K, C, D, E, H, I, F, G, J. Final gate green: **274
  e2e + 49 unit pass**, `vue-tsc --noEmit` 0 errors, eslint clean on touched
  files; every new migration verified up/down in isolation and a single
  Alembic head re-confirmed after resolving a concurrent-session fork.
  Browser verification of the running surface carries forward under
  **[[FU-179]]** (the remaining gate before COVERAGE_GAPS §MEAL PLANS rows flip
  gap→covered). Spun-off open loops at resolution: FU-173 (slot-remap UI),
  FU-174 (app-wide datetime/tz sweep), FU-175 (bulk-week editor assessment),
  FU-176 (app-wide R-014 reveal-disable sweep), FU-178 (SQLite full-chain
  migration), FU-181 (plan email + meals_per_week pref).
- **What:** `docs/04_proposals/IMPL_PLAN_MEAL_PLANS.md` turned the C-2 Meal
  Plans proposal into eleven reviewable chunks. Build order (§5):
  **C-2.A** slot vocabulary (household-wide `MealSlot` table) ★ first PR →
  **C-2.B** page-chrome cleanup → **C-2.C** vertical carousel + slot rows +
  tap-add (+ K date fix; fixes FU-154 in passing) → **C-2.D** calendar widget →
  **C-2.E** drop `MealPlan.name` + implicit create + "Clear week" → **C-2.H**
  sidebar redesign (composes C-7; carries FU-135) → **C-2.I** trays →
  **C-2.F** templates (single) → **C-2.G** template sets + recurring + manage
  page → **C-2.J** sequential builder. Each shipped in isolation; the canvas
  kept working through every phase.
- **Decisions settled (review 2026-06-14):** full build; **slots are a
  household-wide `MealSlot` vocab table** (corrects proposal §4 "user-scoped"
  — `MealPlan` has no `user_id`); **3 trays** (incl. Frequently-planned);
  21-day "haven't had" window; recurring cap 26wk; templates at
  `/meal-plans/templates`; apply-time rotation; slot-remap deferred ([[FU-173]]).
- **Lower-level (also settled):** past-day fix → **household-timezone** correct
  (C-2.K; app-wide sweep [[FU-174]]); `MealPlanEditDialog` **retired** (C-2.E;
  bulk-week assessed in [[FU-175]]); C-2.J added `POST /meal-plans/preview-ingredients`;
  builder Email **shown-disabled** when SMTP unset per new rule **R-014** /
  ADR-009 (app-wide reveal-disable sweep [[FU-176]]). Plan is 11 chunks (K split out).

## [RESOLVED] FU-057 — P6-02: browser-verify the gated scanning surface + apply migration
- **Raised:** 2026-06-07 (P6-02 implementation)
- **Type:** finding
- **What:** The scanning/QR gating was verified by static read + frontend sweep only. Not
  confirmed in a running app: toggling `scanning_enabled` in Settings → System actually
  shows/hides the Stock Overview scan/print buttons, stock-item "Show QR", and the Data →
  "Scanning & QR labels" section/off-state banner. Migration `a3f1c7d2e9b4` (drops
  `StockItem.barcode`, adds `AppSetting.scanning_enabled`) has not been applied to a live DB.
- **Why deferred:** e2e suite pre-existing broken ([[FU-048]]); no browser smoke test this
  session.
- **Recommended resolution:** **confirm in browser** + run migration on a dev DB before P6-01.
- **State note:** 2026-06-14 — closed by user. Gating confirmed in browser (toggling
  `scanning_enabled` shows/hides the Stock Overview scan/print buttons, stock-item "Show QR",
  and the Data → "Scanning & QR labels" section) and migration `a3f1c7d2e9b4` has been
  applied. Also noted as no-longer-relevant given current scope.

## [RESOLVED] FU-141 — Browser-verify State Ownership Chunk 4
- **Raised:** 2026-06-12 (State Ownership Chunk 4 impl;
  static-only, no env)
- **Type:** finding / verification
- **What:** Eyeball that the rename-safety refactor preserved
  every visual decision it was supposed to preserve:
  - `StockItemChip` — colour band + short label ("OK" / "Mid" /
    "Low" / "Out") still match each level. Renaming "Out of
    Stock" to "Empty" in Settings should leave colour + label
    unchanged.
  - `StockItemRow` — dim treatment fires for out-of-stock
    rows; level button colour follows the current level.
  - `useStockFilters` — summary counts (top of Stock Overview)
    + sticky-footer tones still light up correctly when a
    level is renamed.
  - `WastePage` — "Mark used" sets the level to whichever row
    matches `OUT_OF_STOCK_SEQUENCE` (rename it first to
    confirm).
  - `MealPlansOverview` — "Need to buy" lists ingredients
    whose level is None/low/out; status chip colours match the
    bucket.
  - `ProductSearch` quick-add — new tracked items still start
    in the out-of-stock bucket.
  - `RecipeCookMode` finish-rows — "leave out of stock"
    action resolves to the right level after a rename.
- **Why deferred:** static-only impl; needs a running app +
  level-rename action to exercise the renaming property
  end-to-end.
- **Recommended resolution:** confirm in browser — high-priority
  for this chunk because the whole point is "renaming a level
  no longer breaks anything". Rename one level as part of the
  smoke pass.
- **State note:** 2026-06-14 — closed by user. The non-rename surfaces
  (chip colour bands, row dim treatment, summary counts, waste "Mark
  used", meal-plan "Need to buy" colours, quick-add seeding, cook-mode
  finish rows) are confirmed working in use. The rename-property half
  is moot: **stock-level renaming is not a supported user action**, so
  the "rename one level as part of the smoke pass" step has nothing to
  exercise.

## [RESOLVED] FU-013 — A4 leftover: "consistent multi-select control" only partial
- **Raised:** 2026-06-05 (A4)
- **Type:** leftover
- **What:** A4 standardised the filter-bar shell (panel/search/active-count/clear)
  but did NOT build a dedicated shared multi-select control. Multi-selects remain
  page-specific: `RecipesOverview` uses `q-select multiple use-chips`,
  `ProductSearch` merchant picker + `StockOverview` levels are bespoke chip UIs.
- **Why deferred:** the bespoke chip pickers carry extra behaviour (health
  icons, level colours, counts) that a generic control would lose; forcing one
  control would be a regression. The shell was the high-value standardisation.
- **Recommended resolution:** opportunistic — only if a future page needs a plain
  multi-select; otherwise leave the bespoke ones. Not no-regret.
- **State note:** 2026-06-14 — closed as wontfix. StockOverview's level filter is
  now a single-select `q-select` (C-1 Chunk 2 retired the per-level chips, see
  `StockOverview.vue:103-115`), so the original "bespoke multi-selects" list
  has shrunk. Remaining surfaces (`RecipesOverview`'s `q-select multiple use-chips`,
  `ProductSearch` merchant picker) are accepted as-is per the original "leave the
  bespoke ones" recommendation — no shared control needed.

## [RESOLVED] FU-125 — Stock Overview Chunk 6 / FU-033 — image surface fixes
- **Raised:** 2026-06-12 (Chunk 6 impl; static-only, no env)
- **Type:** finding / verification → product-defect resolution
- **What:** Browser verify revealed three real problems beyond the original
  verification checklist, all fixed this session:
  1. **Live update / cache-bust.** Uploading from the detail page didn't
     refresh the overview row (even on hard reload in one of the user's
     repros). Cache busting was a *local* `imageVersion` ref on the detail
     page — the row's `<img src>` had no query param and the browser served
     the cached copy. Moved cache-bust into `stockItemStore` as a per-item
     `imageVersions` map with `imageVersionOf(id)` + `bumpImageVersion(id)`;
     `updateStockItemAsync` bumps automatically when the PATCH payload
     includes `image`. Row + detail page both read the store-derived
     version, so any surface displaying the item refetches reactively.
     `imgFailed` latch on the row is now reset when the version bumps.
  2. **Inconsistent row position.** The image slot used to live *after* the
     name+zone column, so its x-position drifted with name length — read as
     "all over the place" across a list. Moved it to the **first** slot in
     the row, stretched to fill the row height, with the leading corners
     rounded to match the card. Bumped from 40×40 to 64-wide; the placeholder
     glyph went from 20 to 24 px to match. Looks like the leading edge of
     the card itself.
  3. **"Remove" on product-fallback preview.** The detail page's
     `ImageUploadField` rendered "Change image" + "Remove" whenever
     `has_image` was true — including when the preview came from a linked
     product. There's nothing for the user to remove in that state. Added
     `has_own_image: bool` to `StockItemDetailDto` (true only when the
     stock item carries its own uploaded bytes; doesn't include
     fallback), surfaced it on the frontend model, and gated the field's
     `canClear` prop on `has_own_image || pendingImage` so the button
     reads "Add image" and Remove is hidden during a fallback render.
- **Browser verification:** items 1–6 from the original verification list
  (own-upload save, product fallback, both-empty placeholder, list-payload
  perf, show/hide toggle, race protection) are unblocked by the fixes
  above and should be re-spot-checked next time the surface is open.

## [RESOLVED] FU-126 — Rename `RecipeImageField` → `ImageUploadField`
- **Raised:** 2026-06-12 (Stock Overview Chunk 6 / FU-033 impl)
- **Type:** tidy-up
- **What:** With the stock-item surface adopting the recipe-image field,
  R-001's second-consumer threshold was hit; the component carries no
  recipe-specific logic.
- **State note:** 2026-06-14 — **RESOLVED.** Moved
  `components/recipes/RecipeImageField.vue` → `components/ImageUploadField.vue`
  (renamed class prefixes too). Added an optional `alt` prop so the
  hard-coded "Recipe image" text no longer leaks into other surfaces
  (defaults to the `name` prop, which mirrors the previous behaviour for
  recipes). The same change introduced the optional `canClear` prop
  used by FU-125 to hide Remove on product-fallback previews. Updated
  the three import sites (`RecipeEditDialog`, `RecipeDetailPage`,
  `StockItemDetailPage`).

## [RESOLVED] FU-127 — Browser-verify Cart Button Chunk 1 (AddToListButton + double-toast fix)
- **Raised:** 2026-06-12 (Cart Button Chunk 1 impl; static-only, no env)
- **Type:** finding / verification
- **What:** Verify the row/toolbar/bulk variants of `AddToListButton` on
  Stock overview, Recipe detail, Stock-item detail, plus the bulk-add target
  resolution + FU-038 double-toast guard.
- **State note:** 2026-06-14 — **RESOLVED.** User: "all good". Browser
  verification passed on the surfaces in scope. The "Add to another list"
  popover toast bug surfaced during this verification — fixed in the
  feedback sweep this session, not a Chunk 1 regression.

## [RESOLVED] FU-128 — Adopt `AddToListButton` on remaining cart surfaces
- **Raised:** 2026-06-12 (Cart Button Chunk 1 scope cap)
- **Type:** rollout
- **What:** Chunk 1 left four hand-rolled cart surfaces in place
  (#6 MyProductsPage, #7 MealPlansOverview, #11 ProductSearch,
  #13 QuickAddSheet entry buttons). The FU framed them as mechanical
  q-btn → AddToListButton swaps.
- **State note:** 2026-06-14 — **RESOLVED.** Per-surface investigation
  showed only one is mechanical; the rest carry compound semantics that
  the existing AddToListButton variants don't model:
  - **#6 MyProductsPage per-product cart — adopted.** Extended
    `AddToListButton` with an optional `selected-product-id` prop
    ([AddToListButton.vue](web_app/src/components/AddToListButton.vue)):
    when set on the `row` variant, the add records `selected_product_id`
    on the line and skips the 2+-products combined-modal branch
    (the product is already chosen). MyProducts per-product button is now
    `<AddToListButton variant="row" :stock-item-id :selected-product-id>`
    and the old `onAddSingle` handler is gone — picks up the popover for
    on-2+-lists, smart-remove for exactly-one-list, and the unified toast
    behaviour the rest of the app has.
  - **#6 MyProductsPage bulk on-deal — kept.** The "Add N on-deal to list"
    button uses an explicit BaseDialog target picker (different UX from
    AddToListButton bulk's sessionStorage-remembered target). Intentional
    — keeps the explicit-choice posture for on-deal adds.
  - **#7 MealPlansOverview "Generate shopping list for this week" — kept.**
    Not an add-to-existing-list action; it generates a *new* list from the
    plan via `generateListForWeek`. The per-ingredient cart button already
    uses `AddToListButton variant="row"`.
  - **#11 ProductSearch quick-add — kept.** Composite "track + create stock
    item + link product + add to list" flow (`quickAddOffer`, ~30 lines
    around `ProductSearch.vue:559`). Specific to onboarding a new offer;
    doesn't fit AddToListButton's "stock item already exists, add it" model.
  - **#13 QuickAddSheet — kept.** The sheet itself is mounted once globally
    and popped by `openQuickAdd()` from many call sites (Dashboard, etc.).
    Those entry buttons are general "open the picker" actions, not "add
    this specific item", so AddToListButton would be the wrong shape.
- **How to apply:** when adopting AddToListButton elsewhere later, pass
  `selected-product-id` whenever the caller has already picked the product
  (per-product cards, comparison results); leave it unset for stock-item-
  row cases so the 2+-products combined modal still surfaces.

## [RESOLVED] FU-008 — Unify dialog chrome via BaseDialog `title`/`#actions` slots
- **Raised:** 2026-06-05 (A3)
- **Type:** deferred job
- **What:** A3 migrated dialogs as a shell transform; each still carried its own
  header/footer markup. BaseDialog already exposes `title`/`closable`/`#actions`
  to standardise chrome.
- **State note:** 2026-06-14 — **RESOLVED.** Full sweep across all 26 BaseDialog
  files. Replaced bespoke `text-h6` header card-sections with the BaseDialog
  `title` prop (or `#header` slot for the icon+title case in `ShortcutsCheatsheet`),
  added `closable` where the original had a hand-rolled close button, and moved
  every `<q-card-actions align="right">` block into the BaseDialog `#actions`
  slot. Form-submit buttons in dialogs whose footers moved outside the `<q-form>`
  were rebound to `@click="onSubmit"` so the submit path still fires. Captions /
  sub-headers that lived next to the title were preserved as body
  `<q-card-section>` content. `vue-tsc --noEmit` clean; backend unit suite 49/49.
  Browser verification still recommended across the dialog matrix.

## [RESOLVED] FU-009 — Decide fate of the 3 specialised overlays vs BaseDialog
- **Raised:** 2026-06-05 (A3)
- **Type:** finding
- **What:** `AlertsBell` (seamless drawer), `CommandPalette` (search overlay),
  and `ScanOverlay` (persistent camera) were intentionally left on raw
  `q-dialog` — they aren't standard card modals.
- **State note:** 2026-06-14 — **RESOLVED.** User confirmed leaving as the
  documented permanent exception. (Command palette was retired separately on
  2026-06-12 anyway; only AlertsBell + ScanOverlay remain as live carve-outs,
  both intentional.)

## [RESOLVED] FU-014 — Product image round-trip is broken (read side decodes binary as utf-8)
- **Raised:** 2026-06-05 (B1); re-diagnosed 2026-06-12 after user repro
- **Type:** finding (now: active bug being fixed)
- **What:** `get_products.py:56` did `product.image.decode('utf-8', 'ignore')`
  on raw image bytes, returning garbage. Fix: adopt the stock-item/recipe data-URL
  pattern + `has_image` list payload + a dedicated `GET /products/<id>/image`
  route.
- **State note:** 2026-06-14 — **RESOLVED.** Verified statically: the fix
  shipped in full — `get_products.py` now exposes `has_image: bool` (stamped
  in bulk via `stamp_has_image` referencing FU-014 in code comments),
  `get_product_image.py` provides the dedicated `GET /api/products/<id>/image`
  endpoint, and `create_product.py` accepts the data-URL string and decodes it
  to UTF-8 bytes on the entity. Frontend `MyProductsPage` / `ProductChip` /
  `ProductSearch.ensureSaved` migration also landed.

## [RESOLVED] FU-015 — B5: Onboarding tour "Alerts" card points at stock, not /alerts
- **Raised:** 2026-06-05 (B5)
- **Type:** finding
- **What:** `WelcomeWizard.vue` `TOUR_CARDS` "Alerts — Dora pings you" routed
  to `/stock?attention=true` instead of the real `/alerts` page.
- **State note:** 2026-06-14 — **RESOLVED.** Repointed the tour card to
  `/alerts` in `web_app/src/pages/onboarding/WelcomeWizard.vue:422`. The
  `/alerts` route exists (`router/routes.ts:76`) and `AlertsPage.vue` is the
  real destination.

## [RESOLVED] FU-027 — B9.7: log-rotation model decision (timed vs size)
- **Raised:** 2026-06-06 (B9.7)
- **Type:** open decision
- **What:** Size-based `RotatingFileHandler` (10MB × 5) — user wanted the active
  log file to contain only the current date's entries.
- **State note:** 2026-06-14 — **RESOLVED.** Switched
  `dora_api/infrastructure/logging_setup.py` to `TimedRotatingFileHandler`
  with `when="midnight"`, `backupCount=14`, and `suffix="%Y-%m-%d"`. The
  active `<service>.log` now only ever contains the current date; rotated
  files are kept as `<service>.log.YYYY-MM-DD` for ~2 weeks. Backend unit
  suite passes (49/49).

## [RESOLVED] FU-031 — B9.3: stale "Recipes" labels after A8 cookbook rename
- **Raised:** 2026-06-06 (B9.3 sweep)
- **Type:** leftover
- **What:** Possible stale "Recipes" labels in tour cards / help / static
  lists after A8 renamed the page to Cookbook.
- **State note:** 2026-06-14 — **RESOLVED** after a one-shot grep. Only four
  candidates surfaced and all read logically per the user's framing ("the
  page is the cookbook, and that has recipes in it"): `DashboardPage.vue:638`
  dashboard "Recipes" card title (shows recipe count → links to /cookbook);
  `DashboardPage.vue:814` card-visibility config label `Recipes`;
  `HelpPage.vue:251` section "Recipes & meals"; `BackupRestore.vue:402`
  data-type label "Recipes". All four refer to recipes-as-content, not to
  the page itself — no edit required.

## [RESOLVED] FU-037 — `.secret_key` hardcoded to `./data/`, ignores DORA_DATA_DIR
- **Raised:** 2026-06-06 (INV-3 re-verification)
- **Type:** finding (latent bug)
- **What:** `dora_api/app.py:47` resolved the session-secret file as
  `Path('data') / '.secret_key'` (CWD-relative), so on the desktop app the
  secret escaped the configured data dir and was CWD-dependent.
- **State note:** 2026-06-14 — **RESOLVED.** Reworked the secret-key resolution
  in `dora_api/app.py` to `config_manager.get_data_dir() / '.secret_key'`
  (creating the parent on first run via `mkdir(parents=True, exist_ok=True)`).
  Also routed the dev `data/` mkdir for SQLAlchemy through `get_data_dir()` so
  the whole app honours `DORA_DATA_DIR`. Backend unit suite passes (49/49).
  Still wants a desktop smoke test across a CWD change to confirm sessions
  survive — fold into the next desktop verification pass.

## [RESOLVED] FU-047 — `confirm_actions._resolve_level` still maps phrases → hardcoded level names
- **Raised:** 2026-06-06 (Phase 1 Chunk 1 — stock-status contract)
- **Type:** finding
- **State note:** 2026-06-14 — **RESOLVED** by static verification. The
  refactor already shipped: `dora_api/features/assistant/confirm_actions.py`
  imports `StockStatus` + `level_for_status`, `_LEVEL_ALIASES` is now keyed to
  `StockStatus` enum members (not name strings), and `_resolve_level` resolves
  via `level_for_status(repo.get(StockLevel).all(), status)` — the brittle
  `"Sufficient"` / `"Well Stocked"` name-mismatch path is gone.

## [RESOLVED] FU-048 — e2e suite (`tests/e2e/dora_api/`) is pre-existing broken on this branch
- **Raised:** 2026-06-06 (Phase 1 Chunk 1 — stock-status contract)
- **Type:** finding
- **State note:** 2026-06-14 — **RESOLVED** per user ("resolved i believe").
  The e2e suite was repaired in commit `8793648 Fix e2e tests` and is no
  longer the pre-existing-broken blocker it was.

## [RESOLVED] FU-061 — Promote doc-graph to in-prompt blocks (Option B) if agents skip the ritual
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** deferred job
- **State note:** 2026-06-14 — **RESOLVED** per user ("feels like what we have
  is working"). Keep the lighter centralised-graph scheme; no per-prompt
  inlined blocks.

## [RESOLVED] FU-062 — Doc-graph: verify cited paths + original-spec Feature Board mappings
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** finding
- **State note:** 2026-06-14 — **RESOLVED** per user ("feels fine"). Per-citation
  existence pass + Feature Board mapping audit not pursued.

## [RESOLVED] FU-063 — Doc-graph: first-use stress test
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** follow-up
- **State note:** 2026-06-14 — **RESOLVED** per user ("feels fine"). No
  dedicated first-use stress test will be run; the graph stands as-is.

## [RESOLVED] FU-064 — Doc-graph: maintenance cadence / regeneration prompt
- **Raised:** 2026-06-08 (doc-graph build)
- **Type:** deferred job
- **State note:** 2026-06-14 — **RESOLVED** per user ("feels fine"). No
  dedicated refresh prompt; rely on opportunistic updates as proposals/FUs
  land.

## [RESOLVED] FU-163 — App-wide undo posture: removed
- **Raised:** 2026-06-12 (UX v2 decisions, §12 Q4)
- **Type:** finding (product decision pending) → product decision
- **What:** User: "I'm heavily questioning the usefulness of undo feature
  everywhere in the app. Likely going to remove." The original inventory
  covered the `useUndo` registry + silent per-tick undo entries, the
  `notifyUndoable` toasts (stock-item delete-restore), and the shopping-list
  Reopen/unfinish flow. Reopen had been flagged as the one possibly-worth-
  keeping path because it was server-snapshotted.
- **State note:** 2026-06-14 — **RESOLVED.** User: "decided undo feature does
  not make sense, remove. Even the reopen functionality — once a list is done,
  it's done. The snapshot of stock levels feels so overengineered. Kill it."
  Removed end-to-end in one pass:
  - Frontend: deleted `useUndo.ts` + `useNotifyUndoable.ts`; stripped the
    Ctrl-Z / header Undo button + keyboard handler from `MainLayout.vue`;
    removed all `registerUndo` / `notifyUndoable` call sites in
    `stockItemStore.ts` (level swap, scalar update, delete) and the
    `ShoppingListDetail.vue` tick handler; deleted the Reopen button + its
    `onReopen` / `reopening` state; deleted `unfinishAsync` from
    `shoppingListApiService.ts`; deleted `restoreAsync` +
    `RestoreStockItemCommand` from `stockItemApiService.ts`.
  - Backend: deleted `features/shopping_lists/unfinish_shopping_list.py` and
    `features/stock_items/restore_stock_item.py`. Dropped the `level_restores`
    capture from the finish handler. Removed `finish_snapshot` from the
    `ShoppingList` entity + `Fields` enum + table mapping. New alembic
    migration `a1c4e7b3f5d2_20260614_drop_finish_snapshot.py` drops the
    column (batch mode for SQLite/Postgres parity, R-005).
  - Tests: rewrote the reopen e2e (`test_shopping_list_lifecycle.py`) into a
    one-liner asserting `/unfinish` now returns 404; the docstring framing
    moved from "server-owned undo" to "once done, it's done".
  - FU-026 ("undo behaves oddly across surfaces") is moot under no-undo and
    was removed at the same time. The stock-item Undo restore reference in
    FU-016's candidate list got an inline note.
  Verified: backend `py_compile` clean, all 49 unit tests pass, e2e suite
  collects without import errors, ESLint clean on the touched files. Browser
  verification rolls into the next FU-165 session.

## [RESOLVED] FU-026 — "Undo behaves oddly across surfaces" (subsumed by FU-163)
- **Raised:** 2026-06-06 (B9.5)
- **Type:** finding / open verification
- **What:** Originally a B9.5 probe into a reported "undo behaves oddly" across
  surfaces. Partially resolved by P6-01 Chunk 1 (server-owned Reopen). The
  remaining open vector was the originating surface (Dashboard alerts) not
  refetching after an inverse fired elsewhere, so Ctrl-Z mutated the store
  correctly but the source surface rendered stale state.
- **State note:** 2026-06-14 — **RESOLVED.** Subsumed by FU-163: the entire
  undo system (registry, header button, Ctrl-Z, undoable toasts, Reopen) was
  removed, so there is no longer an "undo" path to behave oddly. Nothing to
  fix; nothing to keep tracking.

## [RESOLVED] FU-168 — Meal-plan CSV export removed (was 500ing)
- **Raised:** 2026-06-13 (FU-166 triage)
- **Type:** finding (genuine defect) → product decision
- **What:** `GET /api/meal-plans/<id>/export?format=csv` 500'd — the CSV
  builder + print-view template read `entry.meal_name`, but `MealPlanEntryDto`
  exposes `recipe_name`.
- **State note:** 2026-06-13 — **RESOLVED.** User: "meal-plan CSV export makes
  no sense, remove." Removed the `/export` route + `_build_csv` (backend), the
  `downloadCsv` fn from `useMealPlanExport.ts` + both CSV buttons
  (`ExportPrint.vue`, `MealPlansOverview.vue`); the e2e test now asserts the
  endpoint 404s. Print-view is **kept** and its latent blank-meal-name bug
  fixed (`meal_name`→`recipe_name` in the Jinja template). vue-tsc clean.

## [RESOLVED] FU-167 — Unknown GET `/api/<x>` returned SPA HTML 404, not JSON
- **Raised:** 2026-06-13 (FU-166 triage)
- **Type:** finding (genuine defect)
- **What:** An unmatched **GET** under `/api/` returned a 404 with the SPA's
  `text/html` body (the GET-only SPA catch-all matched, so the request
  middleware's no-endpoint JSON-404 never fired and the view's `abort(404)`
  produced the default HTML), while POST/PATCH/DELETE returned JSON.
- **State note:** 2026-06-13 — **RESOLVED.** Factored the no-route 404 body
  into a shared `api_response.endpoint_not_found()` (plain `application/json`,
  matching the middleware), used by both the middleware and the SPA catch-all
  — the catch-all's `/api/` branch now returns it instead of `abort(404)`. All
  four verbs return the identical JSON problem-detail; the `test_misc` GET case
  passes (xfail removed).

## [RESOLVED] FU-166 — Legacy e2e suite has drifted badly from the API (122 pre-existing failures)
- **Raised:** 2026-06-12 (first known full `pytest tests` run, during UX v2)
- **Type:** finding
- **State note:** 2026-06-13 — **RESOLVED.** Full `pytest tests` now
  **296 passed / 3 xfailed / 0 failed** in ~6s (was 122/167/10 in 813s),
  stable across repeated runs. Two-part fix: (1) converted the e2e harness to
  Flask's in-process test client (~95× faster, behaviour-preserving — new
  R-013/ADR-008); (2) updated all ~132 drifted assertions to the current
  contract (query-string options, `{items,total,page,limit}` envelope, ISO
  dates, refreshed seed/DTOs, reworked error messages) per the user's
  UPDATE disposition. Three genuine defects uncovered are now tracked as
  strict `xfail`s rather than silently passed: FU-164 (backup links section),
  FU-167 (unknown-GET `/api` HTML 404), FU-168 (meal-plan CSV 500). See the
  2026-06-13 worklog entry for the per-file breakdown.
- **What:** Full suite: **122 failed / 167 passed / 10 errors**. Verified
  pre-existing by stashing the UX v2 changes and re-running the two heaviest
  files (`test_stock_item_router`, `test_user_router`) — identical failures
  on baseline. Dominant modes: tests assert the *old bare-array* response
  shape where the API now returns pagination envelopes
  (`{items, page, limit, total}`); 404s + fixture errors through the older
  CRUD router tests. The newer feature suites (shopping lists 21/21, audit,
  auth, data import/export) pass. The old router tests appear to predate
  several API reworks and were never maintained.
- **Why it matters:** "the tests pass" currently means nothing for ~40% of
  the suite — regressions in old surfaces are invisible. FU-164 (backup
  sections) is one concrete member of this set.
- **Recommended resolution:** later, as its own focused prompt — triage per
  file: update assertions to the current API contract, or delete tests for
  removed behaviour. Don't fix piecemeal inside feature work.

## [RESOLVED] FU-164 — Backup-sections test failure (misdiagnosis: stale `meals`/`meal_recipes`)
- **Raised:** 2026-06-12 (full pytest run during UX v2)
- **Type:** finding
- **State note:** 2026-06-13 — **RESOLVED, and the original diagnosis was
  wrong.** `product_stock_item_links` is *already* a real backup section
  (`restore_shared.SECTIONS` line 78, `StockItemProduct`) and present in the
  payload — verified by dumping the live backup. The test actually failed
  because its `expected_sections` still listed **`meals` + `meal_recipes`**,
  which the "Complete rework of meals" (meals→recipes) commit removed as
  tables. Fixed by dropping those two stale keys from the test's expected set
  (and removing the FU-166 xfail). No backup-builder change needed — the
  product↔stock-item links do round-trip.
- **What:** `test__get_backup__happy_path__returns_attachment_with_expected_sections`
  expects a `product_stock_item_links` section that `features/data/backup.py`
  never provides — the string appears nowhere in `dora_api`. The test was
  updated in commit `d2153e3` ("Tidy up incorrect barcode implementation…")
  ahead of a backup change that never landed. Unrelated to UX v2 (fails on
  main too).
- **Recommended resolution:** opportunistic — either add the links section to
  the backup builder (likely the original intent: the product↔stock-item
  anchor table should be backed up) or correct the test. Decide alongside the
  next data/backup task.

## [RESOLVED] FU-162 — Implement shopping-list UX v2 (single-page merge, rail, chip axe)
- **Raised:** 2026-06-12 (shopping-list UX design session)
- **Type:** deferred job
- **What:** `docs/04_proposals/PROPOSAL_SHOPPING_LIST_UX_V2.md` — the agreed
  redesign of the shopping surface: lists rail (desktop) / dropdown (mobile)
  ordered by effective date, server-owned `display_name` (nullable custom name)
  and `next_up_list_id`, top info area (big status badge, proper shop-day
  button, resurrected completion doughnut + totals), toolbar instead of
  ellipsis menus, per-row direct actions + real price button, StockItemChip
  deleted app-wide, shop-mode page merged into the detail page (full M1–M15
  disposition table in the proposal §2).
- **State note:** 2026-06-12 — built in full the same day (§12 decisions:
  no location default for shopping, restock-review modal, CSV export +
  archive + per-line move + pause all removed, R-012 adopted). ESLint +
  vue-tsc clean; 21/21 shopping e2e tests pass (3 updated to the new
  design). Browser verification tracked as FU-165.

## [RESOLVED] FU-159 — Planned shop date not surfaced in shopping-list UI (feedback L402)
- **State note:** 2026-06-12 — resolved by UX v2 (FU-162): the shop day is a
  real outlined button in the top info area (today/overdue tones), drives the
  rail's effective-date order and the server-side next-up pick, and labels
  self-named lists. Browser check folded into FU-165.
- **Raised:** 2026-06-12 (re-surfaced during shopping-list buggy-merge audit)
- **Type:** finding (design drift)
- **What:** Feedback L402: "Being able to set a planned shopping day per list
  would be useful. Optional of course." The DB column
  `planned_shop_date` exists (migration
  `e1a4c7b2f9d0_20260613_shopping_list_planned_shop_date.py`) and the list
  picker sorts by it
  ([routes.ts:110-131](web_app/src/router/routes.ts#L110)), but nothing in
  the UI displays or edits the field. The user can't actually set one.
- **Recommended resolution:** add a date picker to the list header info
  area on `ShoppingListDetail.vue` (top info area was already proposed in
  L407), plus a chip / caption on each row of the list-selector dropdown
  so the sort order makes visible sense. Pair with FU-158 below — both
  belong in the same "shopping list polish" pass.
  *2026-06-12 update:* partially built since raised (date link + editor +
  banner exist on the detail page) but discoverability complaint stands
  (text link, S14). Folded into FU-162 /
  `PROPOSAL_SHOPPING_LIST_UX_V2.md` §4 — resolve there.

## [RESOLVED] FU-158 — Shopping list responsive layout + today's-date picking (feedback L405/406/409)
- **State note:** 2026-06-12 — resolved by UX v2 (FU-162): desktop virtualised
  rail + mobile dropdown (one effective-date continuum), and the landing pick
  is the server-owned `next_up_list_id` (the old today's-date string compare
  could never match — RFC-vs-ISO serialisation, see ADR-007). Browser check
  folded into FU-165.
- **Raised:** 2026-06-12 (re-surfaced during shopping-list buggy-merge audit)
- **Type:** finding (design drift from `SHOPPING_LIST_REDESIGN_PROPOSAL.md`)
- **What:** The Chunk-5 merge of overview-into-detail shipped, but three
  pieces of the proposal got dropped:
  1. **Desktop right-side panel** with all lists ordered by planned shop
     date → finalised date → creation date (feedback L405). Current code
     uses a single `q-btn-dropdown` in the header for every viewport
     ([ShoppingListDetail.vue:8-117](web_app/src/pages/ShoppingListDetail.vue#L8)).
  2. **Mobile dropdown at top** (L406) — exists today but identical to
     desktop; no responsive split.
  3. **Today's-date-keyed picking** when navigating to `/shopping-lists`
     with no id (L409). The route guard
     ([routes.ts:110-131](web_app/src/router/routes.ts#L110)) picks by
     status + creation order, not by today's planned shop date. So a list
     planned for today is no more likely to be chosen than any other.
- **Why deferred (now):** the user reported broad shopping-list buggyness;
  the immediately-blocking bugs (FU-157: URL param not watched) were
  surgically patched today. The proposal-level polish above is its own
  scoped work — needs design choices (panel width? desktop-vs-mobile
  breakpoint?) and probably its own Wave-A-shaped prompt. Bundling them
  here was already attempted in the original Chunk 5 and the polish was
  the part that got cut.
- **Recommended resolution:** queue a focused "Shopping list polish" prompt
  with these three items + FU-159 (planned shop date in UI) + FU-160
  (shopping-day alert). Keep `useUnsavedChangesGuard`-style discipline:
  responsive split is a Wave-A pattern, today's-date logic is a route-guard
  patch.
  *2026-06-12 update:* that focused design now exists —
  `docs/04_proposals/PROPOSAL_SHOPPING_LIST_UX_V2.md` (§3 rail/dropdown,
  §3.3 server-owned `next_up_list_id` replacing today's-date guessing).
  Folded into FU-162 — resolve there.

## [RESOLVED] FU-157 — Shopping list URL-param change doesn't reload (and "old list reappears")
- **Raised:** 2026-06-12 (user repro)
- **Resolved:** 2026-06-12 — `ShoppingListDetail.vue` and
  `ShoppingListShopMode.vue` were `onMounted`-only, with no
  `watch(listId)`. Switching lists via the header dropdown pushed the
  new URL but the component stayed mounted (same route component, just
  a different `:id`), so `load()` never re-ran and the previous list's
  data sat on screen. The "old list reappears after adding to another"
  symptom was a direct consequence: the page never moved off list A,
  so any subsequent `load()` (e.g. via the QuickAdd-closed watcher)
  looked like a resurrection. Fix: added `watch(listId, load)` on both
  pages, plus a `detail.value = null` clear at the start of `load()`
  so the user sees a spinner — not stale rows — while the new list is
  in flight.
- **Type:** finding (real bug, structural)

## [RESOLVED] FU-156 — Main menu nav bypasses the unsaved-changes guard
- **Raised:** 2026-06-12 (user repro during FU-021 verify)
- **Resolved:** 2026-06-12 — root cause confirmed (c): the guard was
  per-handler (`RecipeDetailPage::onBack`) instead of route-level, so
  any nav surface other than the back button skipped the prompt; on
  `StockItemDetailPage` there was no guard at all. Fixed at the layer
  that covers every nav route — new `useUnsavedChangesGuard`
  composable wraps both `onBeforeRouteLeave` (different-route nav,
  e.g. main menu) **and** `onBeforeRouteUpdate` (same-component param
  change, e.g. clicking a related-recipe link mid-edit), plus
  `beforeunload` for refresh/close. Wired into RecipeDetailPage
  (`isDirty || imageDirty`) and StockItemDetailPage (`isDirty`).
  `RecipeDetailPage::onBack` simplified to a plain `router.push` since
  the guard now owns the prompt. Delete handlers on both pages drop
  the dirty state before navigating so the user isn't asked about
  edits to a row they just deleted.
- **Type:** finding (real bug)

## [RESOLVED] FU-155 — Stock-item detail "Related recipes" tab navigates to Cookbook overview, not the recipe
- **Raised:** 2026-06-12 (user repro; carve-out from FU-019 [[fu-019]])
- **Resolved:** 2026-06-12 — bug was in
  `StockItemDetailPage::goToRecipe` which built
  `{ path: '/cookbook', query: { recipe: recipeId } }`. The
  recipe-detail route is `/cookbook/:id`; the bad path matched the
  `/cookbook` overview (and the unused `?recipe=` query was silently
  dropped). Changed to `router.push(\`/cookbook/${recipeId}\`)`.
- **Type:** finding (real bug)

## [RESOLVED] FU-149 — Cookbook overview: add "# ingredients" filter + sort axis
- **Raised:** 2026-06-12 (user browser verify of FU-085)
- **Type:** enhancement
- **What:** New filter axis "ingredients = N" or "ingredients ≤ N"
  + new sort axis "ingredient count (asc/desc)" on the cookbook
  overview. Ingredient count is already on the Recipe DTO (via the
  `ingredients[]` array length); the work is mostly in
  `useRecipeFilters` / the overview's filter panel + sort options.
- **Why deferred:** new feature, not bug. Scope cap on the
  current session.
- **Recommended resolution:** later, batched with FU-148
  (time-of-day filter) and the other cookbook polish items.

## [RESOLVED] FU-148 — Cookbook overview: add "time of day" filter
- **Raised:** 2026-06-12 (user browser verify of FU-085)
- **Type:** enhancement
- **What:** `Recipe.time_of_day` exists on the entity + DTO
  (breakfast / lunch / dinner / snack / dessert / drink), and it's
  editable on the recipe detail page, but there's no filter for
  it on the cookbook overview. Add a single-select dropdown
  defaulting to "any time of day" alongside the cuisine / category
  selects. The other filters use the same `useRecipeFilters`
  pattern; this should be one mirrored predicate.
- **Why deferred:** new feature; pair with FU-149.
- **Recommended resolution:** later.

## [RESOLVED] FU-147 — Recipe detail dietary-tag picker loses selection on save
- **Raised:** 2026-06-12
- **Resolved:** 2026-06-12 — root cause turned out to be a backend
  bug in the detail endpoint, not a frontend race. The
  `/api/recipes/<recipe_id>` route has no `uuid:` converter, so
  Flask passes `recipe_id` to `handle_by_id` as a **string**.
  `get_tag_ids_for_recipes()` returns `dict[UUID, list[UUID]]`
  (keys come from SQLAlchemy result rows). The handler then did
  `tag_map.get(recipe_id, [])` — a Python dict lookup with a
  string key against UUID-typed keys → **always returned `[]`**,
  silently dropping every tag and tool on the detail JSON.
  Same bug affected `tool_map.get(recipe_id, [])`. Fix in
  `get_recipes.py::handle_by_id`: pass `entity.id` (the loaded
  entity's real UUID) to both `get_tag_ids_for_recipes` and the
  subsequent `.get()` calls. The list endpoint was unaffected
  because it sources ids from RecipeDtos that already carry
  UUID objects.
  Static-only fix; browser-verify is **FU-151**.

## [RESOLVED] FU-137 — `test_recipe_cookability.py` stub missing `source` attr
- **Raised:** 2026-06-12 (surfaced during State Ownership Chunk 1
  verification run)
- **Type:** finding / test breakage (pre-existing)
- **What:** `tests/test_recipe_cookability.py::_recipe()` built a
  `SimpleNamespace` recipe stub lacking `source`,
  `version_group_id`, `kcal` — fields that `RecipeDto.from_entity`
  reads. Every test in the file failed with `AttributeError`.
- **State note:** **Resolved 2026-06-12 (State Ownership Chunk 2)**
  — the stub was the scaffolding for Chunk 2's
  `missing_stock_item_names` tests, so the fix was folded into
  that chunk per the original recommendation. Added the three
  missing attributes; all 12 cookability tests now pass.

## [RESOLVED] FU-136 — `test_shopping_list_totals.py` stub missing `product_id` arg
- **Raised:** 2026-06-12
- **Resolved:** 2026-06-12 — added `product_id=None` to the `_line()`
  factory in `tests/test_shopping_list_totals.py`. Single-line stub
  fix; totals tests don't exercise the new anchor so None is the
  honest value. CI signal restored.

## [RESOLVED] FU-131 — Cart Button Chunk 3 frontend UI (rule 4 modal + inline-product variant + nested display)
- **State note:** **Resolved 2026-06-12** — all three pieces
  (rule 4 modal in `ShoppingListDetail.vue::onRemoveLine`,
  nested display via `nestedLinesFor` + new CSS classes, and
  `AddToListButton variant="inline-product"` consumed by
  `MyProductsPage`) landed in a single session. Browser-verify
  tracked separately as **FU-145**. Original entry preserved
  below for the trail.

## [RESOLVED] FU-120 — Browser-verify Stock Overview Chunk 1 (50-cap fix + virtualisation + filtered export)
- **Raised:** 2026-06-12
- **Resolved:** 2026-06-12 — user verified in browser ("FU-035
  resolved — looks good"). >50-item pantry now renders the full
  list via the paged loop + `q-virtual-scroll`; filtered CSV /
  print exports honour the `ids=` filter; unfiltered exports
  take the fast path. No defects raised. **FU-035** stays
  RESOLVED with this confirmation closing the loop.

## [RESOLVED] FU-106 — Stock Overview image collapse/expand inline button (C-cross §2.8 surface)
- **Raised:** 2026-06-10
- **Resolved:** 2026-06-12 by Stock Overview Chunk 3 — inline image
  toggle next to the search input flips `show_stock_images` via the
  existing `useImagePrefs()` composable; the row's image slot is
  `v-if="showStockImages"` so density actually changes when toggled.
  Slot is currently a neutral placeholder (40×40 sunken square); it
  becomes the real photo container when FU-033 wires
  `StockItem.image` bytes. Static-only impl; browser-verify is
  **FU-122**.

## [RESOLVED] FU-090 — Recipe list query loads all image blobs (perf)
- **Raised:** 2026-06-09 (Chunk 5)
- **Resolved:** 2026-06-11 (C-cross Chunk 5). Folded into Chunk 5 per
  the IMPL plan ("the bandwidth-saving promised by 'images off' is
  otherwise hollow"). `Recipe.image` is now mapped with SQLAlchemy
  `deferred()` so the column never loads on the recipe-list query.
  `RecipeDto.from_entity` defaults `has_image=False`; a new
  `_hydrate_has_image()` runs a single bulk
  `SELECT id, image IS NOT NULL FROM Recipe WHERE id IN (...)` and
  fills the field — same hydrator pattern as tags / tools /
  structured-step flag. The image-bytes endpoint
  (`get_recipe_image`) still reads `recipe.image` directly via
  attribute access (one query per detail call, the intended path);
  the new-version handler's `image=source.image` copy also triggers a
  single lazy load per call.
- **Files:** `dora_api/persistence/table_mappings.py`,
  `dora_api/features/recipes/get_recipes.py`.

## [RESOLVED] FU-087 — Recipes overview filter panel shows nothing / toggle does nothing
- **Raised:** 2026-06-09 (user browser test of FU-083 + FU-085)
- **Resolved:** 2026-06-09. Reproduced via DOM inspection — the FilterBar's
  panel had `display: none` because `expanded` was permanently `false`. Two
  latent bugs in `FilterBar.vue` (and therefore every page using it,
  including StockOverview): **(1)** Vue 3 coerces an unset Boolean prop to
  `false`, so the manual `props.modelValue === undefined` sentinel
  distinguishing controlled-vs-uncontrolled never fired — clicks mutated
  `internal` but the getter kept returning the coerced-false `modelValue`.
  **(2)** `$q.screen.gt.sm` was read without the Quasar Screen plugin being
  activated anywhere, so every viewport check returned `false` (the "open on
  desktop by default" rule silently failed regardless of viewport). Both
  invisible to static type-checking and produced no console output.
- **Fix:** rewrote with the framework-idiomatic patterns: Vue 3.4
  `defineModel()` (handles controlled/uncontrolled correctly; a function
  default sidesteps the Boolean coercion); plus a new
  `web_app/src/boot/quasarScreen.ts` calling `Screen.setDebounce(100)` (the
  documented Quasar 2.x activation, registered in `quasar.config.ts`).
  Promoted the lesson to **R-011 / ADR-004** in
  `docs/01_charter/ENGINEERING_STANDARDS.md` — "use the framework's
  idiomatic, current-recommended pattern" — so this class of hand-rolled
  workaround doesn't recur.
- **Files:** `web_app/src/components/FilterBar.vue`,
  `web_app/src/boot/quasarScreen.ts` (new), `web_app/quasar.config.ts`,
  `docs/01_charter/ENGINEERING_STANDARDS.md`, `CHANGELOG.md`.
- **Unblocks:** FU-083 (Cookbook Chunk 1 filter verify) and the filter half
  of FU-085 (Chunk 2 cuisine/category/dietary filters).

## [RESOLVED] FU-083 — Browser-verify Cookbook Chunk 1 + user feedback pass
- **Raised:** 2026-06-09 (post-Chunk-1 implementation)
- **Resolved:** 2026-06-10. User did the browser pass and surfaced
  nine concrete pieces of feedback; all addressed in this session.
- **Original verify items 1–7 plus user-flagged tweaks, by status:**
  1. ✅ Comparison gone — clean (no warnings).
  2. ✅ Chip filters toggle; `activeFilterCount` updates.
  3. ✅ Numeric inputs — **`:hint` removed** on `Meals ≥` / `Missing ≤`
     (and the old `Free from ingredient(s)` input is gone entirely);
     filter row alignment is no longer offset by the extra
     under-input copy.
  4. ✅ Sort axes — now with an explicit **`sortDir` toggle**
     (asc/desc) on a dedicated direction button next to the Sort by
     dropdown. Null sentinels (last_made, total_time) still sink to
     the bottom regardless of direction. Axis-switch snaps direction
     to the conventional default (name=A→Z, recently-made=newest
     first, etc.).
  5. ✅ Stock-item picker — **dot kept, level text removed** from
     the dropdown row (user flagged the caption as redundant);
     `?usesStockItem=` deeplink still hydrates.
  6. ✅ **`Planned` filter bug fixed.** Was string-comparing
     `scheduled_for` without parsing, and didn't skip consumed
     entries — user reported yesterday's still surfacing. Now
     parses `YYYY-MM-DD` explicitly into a local-midnight `Date`,
     skips any entry with `consumed_at` set, and gates on the
     parsed `>= today` check. Also renamed the chip from
     **"Planned in"** to plain **"Planned"** per the feedback ("In
     adds nothing").
  7. ✅ **RecipeCard dim removed.** The "restocking this item alone
     wouldn't make it cookable" semantics wasn't legible without a
     legend, and the card already shows "missing N ingredients" on
     its face. `highlightStockItemIds` prop kept (used by deep-link)
     but no longer drives a `--dim` class.
  8. ✅ Filter-bar alignment — **hints + the free-text "Free from"
     control removed**; the row now reads cleanly without the
     under-input height jitter.
  9. ✅ **"Free from ingredient(s)" replaced by a "Doesn't use"
     stock-item picker** (+/- partner to "Uses ingredients" — same
     option source, same search UX). Trades free-text fuzziness for
     an exact stock-item exclude; users who want raw-text exclude
     can ask if they hit a real gap.
  10. ✅ **"Uses stock items" → "Uses ingredients"** label rename.
  11. ✅ **Read-only "Last cooked" card** added on the recipe detail
      page sidebar (under the cookable card); reads
      `recipe.last_made_on` and shows "Never" when null.
- **Files touched:** `pages/RecipesOverview.vue`,
  `pages/RecipeDetailPage.vue`, `components/RecipeCard.vue`.
- **Unblocks:** nothing specific; the cookbook overview UX gripes
  are now closed.

## [RESOLVED] FU-080 — Browser-verify the menu-highlight subroute fix
- **State note:** 2026-06-09 — user confirmed in browser: menu highlighting works on subroutes. ✅
- **Raised:** 2026-06-09 (after the menu-highlight fix landed)
- **Type:** follow-up / browser verification
- **What:** The fix moves main + side menu active-state from Vue-Router's route-record matching to a path-prefix composable (`useMenuLinkActive.ts`), and re-targets the "Recipes" menu link from `/recipes` (redirected) to `/cookbook` with `activePrefixes: ['/recipes']`. Confirm in browser:
  1. Each top-nav button highlights on its base path **and** on every subroute it owns: `/stock/:id` under Stock; `/cookbook` + `/recipes/:id` + `/recipes/:id/cook` under Recipes; `/shopping-lists/:id` + `/shopping-lists/:id/shop` under Shopping Lists; `/meal-plans` subroutes; `/data/*` (Data menu has /backup, /import, /export, /barcodes); etc.
  2. The sliding accent-coloured indicator on `MainMenuButtonStrip` still tracks position when navigating between sections.
  3. SideMenuButton (hamburger drawer) highlights correctly on subroutes too (the `exact` prop was dropped).
  4. No double-highlight: only the *most specific* match should look active. Path prefix is greedy by design — `/data` would match `/data/backup`, which is desired; but verify no two sibling links both match the same URL.
- **Recommended resolution:** now/when next in the app — quick visual sweep.
- **State note:** not yet verified.

## [RESOLVED] FU-079 — Confirm hotfix resolves the blank-screen report
- **State note:** 2026-06-09 — user confirmed: can navigate to `/shopping-lists` and Detail renders correctly. Hotfix verified in browser.
- **Raised:** 2026-06-08 (user reported blank screen on /shopping-lists with no console errors)
- **Type:** follow-up
- **What:** A hotfix landed in this session: Overview + Detail now surface `loadError` via banners with Retry buttons, the store explicitly `console.error`s API failures, Detail's FadeTransition gained a v-else "list isn't available" fallback so the content area is never blank, and three lint errors were cleared (duplicate v-else-if, dead `onFinish`, floating-promise on Esc).
  - **Leading suspect for the original blank screen:** the `e1a4c7b2f9d0` migration (Chunk 7 `planned_shop_date` column) was not applied on the user's Linux machine. The API's `SELECT` on `ShoppingList` would 500 with "no such column"; the store caught silently; the UI rendered nothing.
- **Recommended resolution:**
  1. Pull the hotfix.
  2. `alembic upgrade head` to apply `e1a4c7b2f9d0`.
  3. Restart the API + Quasar dev.
  4. Navigate to `/shopping-lists`. Confirm: either the redirect to a list works, or the new red banner shows an actual error message (no more blank).
  5. Open the browser dev console — any `[shoppingListStore] refreshAsync failed` lines surface what's actually broken.

## [RESOLVED] FU-078 — Write IMPL plan for C-4 cookbook
- **Raised:** 2026-06-08 (after FU-077 closed)
- **Type:** follow-up
- **What:** Natural next document after the C-4 design decisions closed (PROPOSAL_COOKBOOK §5a) — chunked IMPL plan mirroring `IMPL_PLAN_SHOPPING_LISTS.md` and `IMPL_PLAN_COOK_MODE.md`. Bigger than C-3 (nine design sections, ~10 chunks expected).
- **State note:** 2026-06-08 — wrote `docs/04_proposals/IMPL_PLAN_COOKBOOK.md` (10 chunks + verify-state, first-chunk DoD, risks, feedback coverage, run order). All 6 open decisions had been closed in PROPOSAL_COOKBOOK §5a beforehand; DEC-2 deviated meaningfully from the brief (siblings via `version_group_id` instead of snapshot+pointer) and the plan reflects the user's flatter model. Wired into the doc-graph (new C-impl row + cross-map row).

## [RESOLVED] FU-077 — Write IMPL plan for C-3 cook-mode
- **Raised:** 2026-06-08 (C-3 decision pass)
- **Type:** follow-up
- **What:** With C-3's open decisions resolved (`PROPOSAL_COOK_MODE.md §5a`) and the structured-steps dependency homed in C-4 (`PROPOSAL_COOKBOOK.md §2.6a`), the natural next document is an implementation plan mirroring `IMPL_PLAN_SHOPPING_LISTS.md` — chunked, self-contained, no code. Chunks suggested by C-3 §6 + §5a: (1) finish-flow + click-out + celebration + meals-cooked-from-zero, (2) timer polish + unit fix + sous-chef discoverability, (3) location grouping + ingredient-UI rebuild, (4) structured-steps (lives in C-4 but lands as a co-sequenced cook-mode-blocker), (5) highlight-instead-of-tick + per-step tools + per-step hints + per-step timers, (6) serving auto-adjust (gated on C-5 onboarding default).
- **State note:** 2026-06-08 — wrote `docs/04_proposals/IMPL_PLAN_COOK_MODE.md` (6 chunks + verify-state, first-chunk DoD, risks, feedback coverage, run-order). Wired into the doc-graph (new C-impl row + cross-map row for the IMPL plan). Open decisions all closed in PROPOSAL_COOK_MODE §5a; no co-design questions remain for the implementation phase.

## [RESOLVED] FU-070 — `goBack()` in Detail is now a self-bounce
- **Raised:** 2026-06-08 (Chunk 5 impl)
- **Type:** finding (UX)
- **What:** The back-arrow in `ShoppingListDetail.vue` pushes `/shopping-lists`, which the new router landing immediately `replace`s back to a chosen list — usually the same one. So the back button now effectively no-ops (or, worse, picks a different list than the user expected). Two reasonable resolutions: (a) point it at `/`, or (b) drop the button entirely now that the in-page list selector exists.
- **State note:** 2026-06-08 — resolved option (b) in Chunk 6: dropped the `<BaseButton variant="icon">` back-arrow + the `goBack()` function from `ShoppingListDetail.vue`. The in-page list selector replaces it; the sidebar nav still exits the shopping-lists surface.

## [RESOLVED] FU-067 — Drop unused `appendLowStockEssentialsAsync` endpoint
- **Raised:** 2026-06-08 (Chunk 4 impl)
- **Type:** finding (R-007 scope-discipline housekeeping)
- **What:** The detail page's "Append low + essentials" menu (the 5th of the proposal's five doors) is gone, but the underlying API method `appendLowStockEssentialsAsync` and its backend route `/shopping-lists/{id}/append-low-stock-essentials` were still present with no UI consumer. The unified `New list` dialog covers the same use case via *auto-fill: low + flagged + essentials-only + merge into this list*.
- **State note:** 2026-06-09 — resolved. Confirmed via static grep the frontend method had zero callers, then removed the `append_low_stock_essentials` route/handler from `features/shopping_lists/auto_generate.py` and the `appendLowStockEssentialsAsync` method from `shoppingListApiService.ts`. No orphaned imports (`AutoGenerateSources/Request`, `not_found`, `AutoGenerateResult` all still used elsewhere). Static-only; not run.

## [RESOLVED] FU-059 — Shopping-list line tick/delete always 404'd (UUID-vs-str guard)
- **Raised:** 2026-06-07 (P6-01 Chunk 1 — surfaced by new lifecycle e2e)
- **Type:** finding → fixed this session
- **What:** `update_line` / `delete_line` in
  `dora_api/features/shopping_lists/manage_shopping_list_lines.py` guarded parent
  ownership with `line.shopping_list_id != shopping_list_id`. The entity FK is a `UUID`;
  the Flask path param is always a `str` (no uuid converter registered), so the
  comparison never matched and **every** PATCH (tick/qty/select) and DELETE on a line
  returned 404. Pre-existing since the file was created (commit `fa399e2`); no e2e
  covered it until now. The frontend (`shoppingListApiService.updateLineAsync`) hits
  exactly this route, so in-store ticking would have been broken in the running app.
- **Resolved (symptom):** compared as strings (`str(...) != str(...)`) in both guards,
  with an inline comment. Verified by the new e2e `test__finish_then_reopen…` (which
  ticks a line). **Still worth a browser confirm** of shop-mode ticking.
- **R-010 carve-out / leftover:** the `str()`-both-sides fix is the symptom fix the new
  rule R-010 warns against — it keeps the ids weakly typed. The *root* fix is to coerce
  the path params to `UUID` once at the route boundary (matching the codebase's existing
  `UUID(raw)` idiom) so the comparison is typed. Deferred to avoid scope creep this
  session; do it opportunistically when next touching `manage_shopping_list_lines.py`
  (and audit sibling line routes for the same coercion).

## [RESOLVED] FU-058 — Finish snapshot captured no level_restores (noload relationship)
- **Raised:** 2026-06-07 (P6-01 Chunk 1)
- **Type:** finding → fixed this session
- **What:** the Finish handler captured each restocked item's prior level by reading
  `item.stock_level` (the relationship). That relationship is mapped `lazy="noload"`
  (`table_mappings.py`), so it returns `None` unless eager-loaded — meaning
  `finish_snapshot.level_restores` was always `[]` and Reopen restored nothing (status
  flipped back but levels stayed Well-Stocked).
- **Resolved:** the Finish query now `.include("stock_level")` before reading the prior
  level. Verified by the new e2e (reopen restores Out-of-Stock). R-003 (server-owned
  undo) now actually holds.

## [RESOLVED] FU-055 — P6-02 barcode/QR: design pivoted; build-vs-defer decision pending
- **Raised:** 2026-06-07 (P6-02 design discussion)
- **Type:** deferred job (blocked on user decision)
- **State note:** RESOLVED 2026-06-07 — user chose Option 1 ("Cleanup now, UI later").
  Dropped `StockItem.barcode` (col/routes/UI/DTOs/export), kept `ProductBarcode` +
  Dora QR, added off-by-default `scanning_enabled` flag gating the whole surface,
  relabelled honestly, wrote `PROPOSAL_BARCODE_SCANNING.md`, reworded CLAUDE.md. The
  EAN question is answered (Product has no EAN, only `merchant_stockcode`) →
  register-against-product UI + ingestion auto-populate deferred to Phase 2 ([[FU-056]]).
  See WORKLOG 2026-06-07 "P6-02 barcode/QR — IMPLEMENTED".
- **What:** P6-02 was going to be "remove real-world barcodes wholesale, keep only Dora QR"
  (legacy spec). A design discussion **changed the shape**: `ProductBarcode` (barcode→Product)
  is the CORRECT model and is KEPT; `StockItem.barcode` (one barcode per item) is the WRONG
  model and is DROPPED. Real-world-barcode scanning becomes a *navigation* aid (scan product →
  open linked stock item), complementary to Dora QR (for unbarcoded/loose items), both opt-in /
  off-by-default, never live deal-lookup. **Full context + the verified code map + the resolved
  decisions are in the DORA_WORKLOG.md entry dated 2026-06-07 "P6-02 barcode/QR — DESIGN
  DISCUSSION".**
- **Resolved already:** flag = install-wide `AppSetting` (`scanning_enabled`, default false);
  recommend ONE flag for the whole surface.
- **OPEN — ask the user first:** how much to build *now* vs defer? (1) [recommended] cleanup +
  gate now, defer the register-against-product UI to Phase 2 (auto-populate from scraped EANs);
  (2) build the full vision now; (3) pause and write the proposal/CLAUDE.md update first.
- **Also verify:** does scraped Product data carry an EAN today? (Only `merchant_stockcode`
  seen.) Determines whether auto-populate is feasible / whether to defer the register UI.
- **Doc changes agreed-in-principle (not yet done):** reword CLAUDE.md "Removed features" P6-02
  line (deal-lookup stays removed; ProductBarcode-as-navigation kept; StockItem.barcode dropped);
  write `docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md`.
- **Recommended resolution:** **now** — first user message next session.

## [RESOLVED] FU-054 — Shop-mode + lists-overview still sum line prices client-side
- **Raised:** 2026-06-07 (Phase 1 Chunk 5 — Type B)
- **Type:** follow-up
- **State note:** RESOLVED 2026-06-07 (Chunk 5b). Both turned out to operate on a
  single fetched detail (shop-mode = the open list; overview `loadPrimaryStats` =
  the *primary* list — not multi-list), so they now read `detail.totals` (added in
  Chunk 5) directly. Removed the client sums + the unused `priceOfLine`/
  `savingsOfLine` imports. Per-line `priceOfLine` display retained in the detail page.
- **What:** Chunk 5 moved *whole-list* totals to the server (`ShoppingListDetailDto.totals`)
  and switched the dashboard + detail page to read them. Two surfaces still sum
  `priceOfLine`/`savingsOfLine` client-side: `ShoppingListShopMode.vue:408-411`
  (sums over `sortedLines`/`remainingLines` — *subsets*, possibly route-ordered, so
  not a straight `detail.totals` read) and `ShoppingListsOverview.vue:522-525` (sums
  per-list across *multiple* lists in the overview — the overview may not fetch each
  list's full detail, so it has no `totals` to read).
- **Why deferred:** subset/multi-list summation needs either per-list-summary totals
  on the lists endpoint (so the overview shows totals without full details) or
  careful subset handling in shop mode — bigger than the named flagship (R-007).
- **Recommended resolution:** **opportunistic / fold into the shopping-list redesign
  pass** — expose per-list totals on the shopping-list *summary/list* endpoint for the
  overview; for shop mode decide whether its subset totals can read `detail.totals` or
  genuinely need a filtered sum. Per-line `priceOfLine` display stays client-side
  (accepted Type-C).

## [RESOLVED] FU-053 — "Best deals" card still fetches all products + sorts by discount client-side
- **Raised:** 2026-06-07 (Phase 1 Chunk 5 — Type B / proposal §8.2)
- **Type:** follow-up
- **State note:** RESOLVED 2026-06-07 (Chunk 5b). Added `GET /api/products/best-deals?limit=N`
  (`GetBestDealsHandler`, ranks on-special products by discount % server-side via the
  new `dora_api/domain/product_offer.discount_percent`); the dashboard queries it for
  the top 3 instead of downloading all products. Inline `discountPctFor` removed; the
  `% off` badge uses the shared `discountPercent` (widened to accept a `Product`).
  Future optimisation (noted, not done): a SQL `ORDER BY` on the discount expression
  instead of loading all products + ranking in Python — fine at current scale.
- **What:** The dashboard "best deals" card (`DashboardPage.vue` `bestDeals` ~L1190,
  `loadProducts` fetches *all* products via `GET /api/products`) filters + sorts by
  discount % in the browser and slices top-3. The discount-% is computed inline
  (`discountPctFor`) duplicating the shared `scrapedProductOfferLogic.discountPercent`
  (a tiny Type-C dup). Proper fix (proposal §8.2): a `?sort=discount&limit=N`
  (or focused best-deals endpoint) so the server sorts and returns only the top N.
- **Why deferred:** `price_now`/`price_was` come from the joined `Product.current_offer`,
  not Product columns, so sorting by `(price_was - price_now)/price_was` is a derived
  expression over a join — the generic field-based sort in `get_products.py` doesn't
  support it. That's a distinct capability (expression order_by + the on-special filter
  + null-RRP handling), riskier than the Chunk-5 flagship and best done deliberately.
- **Recommended resolution:** **later — a focused "best deals query" unit.** Add
  discount-sort support (or a `/products/best-deals?limit=N` endpoint) computing the
  discount server-side; switch the card to query it; fold `discountPctFor` onto the
  shared helper at the same time. Until then the card works (just over-fetches).

## [RESOLVED] FU-040 — C-4 should model structured recipe steps (C-3 depends on it)
- **Raised:** 2026-06-06 (C-3 brief)
- **Type:** follow-up (design dependency)
- **What:** Recipe instructions are a freeform text blob (`recipe.py` instructions;
  cook mode splits on newlines, `RecipeCookMode.vue:356-363`). Cook mode's richer
  per-step features — reliable ingredient highlighting (instead of fragile
  text-match), per-step tools, per-step hints, per-step timers — all need
  **structured steps** (step = text + optional sub-steps + hint + the
  ingredients/tools it uses). This is a recipe-model change that belongs in **C-4**
  (adjacent to its multi-part "sections"), not cook mode.
- **State note:** 2026-06-08 — resolved at the design level: C-3 DEC-2 chose "Structured steps in C-4 + remove ticks", and `PROPOSAL_COOKBOOK.md §2.6a` was added with the model (`RecipeStep`: text, sub_steps, hint, ingredient_refs, tool_refs), the editor + importer story, and a §6 sequencing slot (item 5a) flagging it as a blocker for C-3 highlight/per-step features. Freeform recipes degrade gracefully. Code implementation is still outstanding (no model migration written yet) — flip to a fresh implementation FU when work begins.

## [RESOLVED] FU-039 — Wire up `Recipe.image` (parallels StockItem.image)
- **Raised:** 2026-06-06 (C-4 brief)
- **Type:** deferred job
- **What:** `Recipe.image` was a dead field. C-4 Chunk 5 (L249) wires it end-to-end.
- **State note:** 2026-06-09 — implemented (static-only; browser-verify in FU-091).
  **Pattern pioneered (FU-033 StockItem.image should follow it):** the image is
  stored as a **data-URL string** (UTF-8 bytes) in the existing LargeBinary
  column; create/update accept an `image` data-URL field (6M-char cap); a new
  `GET /api/recipes/<id>/image` parses the data URL and returns raw bytes +
  mimetype; the list/detail DTOs carry only `has_image: bool` (no inlined
  base64); the SPA renders via `<img src=recipeImageUrl(id)>` (cache-busted on
  the detail page after save) with a coloured-initial placeholder fallback.
  Reusable `RecipeImageField.vue` handles pick/preview/clear.
  See [[stockitem-image-substitute-notes-intent]].

## [RESOLVED] FU-038 — Cart button fires contradictory double-toast on already-on-list
- **Raised:** 2026-06-06 (C-7 brief; feedback L154)
- **Resolved:** 2026-06-12 by Cart Button Chunk 1. The blind re-add
  path is gone — already-on-list now **toggles** (remove silently on
  1 list; popover with explicit Remove / Add-to-another on 2+). No
  more "0 added, 1 already on list" + "Added to your primary list"
  collision because the button never fires the add path when the
  item is already on a list. Static-only impl; browser-verify is
  **FU-127**.

## [RESOLVED] FU-036 — Confirm Shop Mode "Substitute" swaps offer-only (gates INV-8)
- **Raised:** 2026-06-06 (INV-8)
- **Type:** finding
- **What:** Static read said Shop Mode's "Substitute" button swapped the
  **merchant offer**, while the permanent stock-item substitute swap lived in
  the full-list per-line menu. INV-8's "rework into Shop Mode" recommendation
  hinged on confirming this in-browser.
- **Resolved:** 2026-06-13 — moot after the Fable 5 shopping-list rework
  (commit `d9ca58e`). The standalone `ShoppingListShopMode.vue` surface no
  longer exists; the unified `ShoppingListDetail.vue` flow now hosts the
  substitute swap (`onSwapSubstitute`, line 729 / 1791), so there is no
  separate Shop-Mode "Substitute" button to confirm. User confirmed current
  UI feels fine.

## [RESOLVED] FU-035 — Stock overview silently shows only the first 50 items
- **Raised:** 2026-06-06 (INV-2)
- **Type:** finding (real bug)
- **What:** `stockItemStore.getStockItemsAsync` paged once and ignored
  `page.total`, so pantries with >50 items lost the tail.
- **Resolved:** 2026-06-12 by Stock Overview Chunk 1 — added
  `stockItemApiService.getAllPagesAsync()` (loops until a short page
  or `total` is reached, asks for `limit=500` per call), and switched
  the store to use it. Pairs with `q-virtual-scroll` so the now-larger
  list still renders smoothly. Browser-verified 2026-06-12 (user
  confirmation via FU-120) — works as intended.

## [RESOLVED] FU-033 — Wire up `StockItem.image` (own image + product fallback)
- **Raised:** 2026-06-06 (INV-1)
- **Resolved:** 2026-06-12 by Stock Overview Chunk 6. End-to-end:
  - Backend: `image` column deferred on the mapping (list endpoint
    no longer pulls megabytes per row). New `has_image` field on
    `StockItemDto` + `StockItemDetailDto`, hydrated by a single bulk
    SELECT that **OR**s the item's own image with any linked
    product's image — so the SPA's "show thumbnail?" decision
    matches what the bytes route will serve. New
    `GET /stock-items/<id>/image` route mirrors the recipe-image
    pattern; resolves own-image first, falls back to the first
    linked product that decodes cleanly, 404s if both miss.
  - Backend: `CreateStockItemRequest` and `UpdateStockItemRequest`
    accept `image` as a data-URL string (~6 MB cap); update treats
    explicit null as "clear".
  - Frontend: new `stockItemImageUrl(id, version?)` helper; row
    renders `<img>` with placeholder fallback (gated on
    `showStockImages`); `StockItemDetailPage` overview tab gets a
    `RecipeImageField` (reused, R-001) that saves immediately and
    bumps an `imageVersion` to bust the browser cache.
  - Static-only impl; browser-verify is **FU-125**.

## [RESOLVED] FU-030 — Fullscreen 404 page redesigned (login-theme + Dora pic)
- **Raised:** 2026-06-06 (B9.9; user follow-up 2026-06-12: "page
  looks a bit boring, maybe use the login theme instead and add a
  suitable dora pic")
- **Resolved:** 2026-06-12 — rewrote `pages/ErrorNotFound.vue` to
  mirror `LoginPage.vue`'s "off-app" treatment: three drifting
  mesh-gradient blobs (magenta / dora amber / mint), floating
  mascot using `dorabot-fatal-error-or-offline.png`, glassy card
  with gradient "404", "This page wandered off" headline, and a
  "Take me home" CTA. Locally-scoped CSS variables (forced light
  tokens) for the same reason LoginPage does it — 404 can render
  pre-auth and `data-theme` can flip dark before sign-in.
  Respects `prefers-reduced-motion`. `ErrorPageNotFound.vue` (the
  in-layout variant via `PageErrorState`) was already themed and
  stays untouched.

## [RESOLVED] FU-029 — B9.4: confirm command-palette commands all trigger
- **Raised:** 2026-06-06
- **Resolved:** 2026-06-12 — **command palette retired entirely.**
  User assessed the palette as low-value for Dora's audience
  (pantry / mobile, not keyboard-power-user); ripped out the UI
  + commands registry. Files deleted:
  `web_app/src/components/CommandPalette.vue`,
  `web_app/src/composables/useCommandPalette.ts`,
  `web_app/src/composables/useCommands.ts`,
  `web_app/src/composables/useRecents.ts`. MainLayout pruned
  (the Ctrl/Cmd-K trigger, lazy mount, and the 18-item
  `useCommands([...])` registry are gone, along with the
  `autogenerateFromLowStock` / `openPrimaryList` /
  `openPrimaryShopMode` palette-feeder functions). **The
  `useShortcut` registry stays** — `?`, `/`, `g s`/`g l`/`g r`
  /`g d`/`g h` etc. all still work; `ShortcutsCheatsheet` is
  still mounted. With the palette gone, verifying its commands
  is moot.

## [RESOLVED] FU-028 — B9.1: confirm shopping-list drag-drop ordering
- **Raised:** 2026-06-06 (B9.1; CLAUDE.md confirm-in-browser rule)
- **Resolved:** 2026-06-12 — user verified in browser. Reorder both
  directions lands at the dashed-outline position. The static-read
  insertAt math (`fromIdx < toIdx ? toIdx - 1 : toIdx`) matches live
  behaviour.
- **Type:** finding

## [RESOLVED] FU-022 — Confirm A4 reported filter bug did NOT reproduce
- **Raised:** 2026-06-05 (A4; back-filled per the non-issue rule)
- **Resolved:** 2026-06-12 — user verified in browser. Clearing filters
  on each of StockOverview / RecipesOverview / MyProductsPage /
  ProductSearch correctly returns all rows; the reported "everything
  filtered out on empty" symptom does not reproduce. A4's explicit
  `!== null` hardening is belt-and-braces.
- **Type:** finding

## [RESOLVED] FU-021 — Confirm A3 reported modal bug did NOT reproduce
- **Raised:** 2026-06-05 (A3; back-filled per the non-issue rule)
- **Resolved:** 2026-06-12 — modal backdrop/Esc-cancel behaviour confirmed
  fine in browser (cf. FU-007 verification). However, the user found a
  **different** escape route around the unsaved-changes guard: navigating
  via the **main menu bar** bypasses the prompt entirely (leaves the page
  / changes routes within the app without firing the guard). The original
  modal-misbehaviour symptom is gone; the menu-nav bypass is a separate
  real bug and is tracked on its own as **[[fu-156]]**.
- **Type:** finding

## [RESOLVED] FU-019 — Confirm B8 reported defects that did NOT reproduce (per-defect)
- **Raised:** 2026-06-05 (B8)
- **Resolved:** 2026-06-12 — user verified in browser. (a) un-favourite
  persists, (c) all recipe actions fire. (b) was originally described as
  "no related-recipes section in the UI" — the user has since located one
  on the **stock item detail page** (related-recipes tab) and the nav
  bug *is* real there. That carve-out is spun out to **[[fu-155]]** to
  track on its own; the remaining (a)/(c) confirmations close this one.
- **Type:** finding

## [RESOLVED] FU-017 — B3: user re-test "can't save unless I change the name"
- **Raised:** 2026-06-05 (Wave-B self-audit)
- **Resolved:** 2026-06-12 — user confirmed in browser; edits save without
  needing a name change. Static reading of the update handlers (PATCH +
  `model_fields_set` + exclude-self uniqueness) matched live behaviour.
- **Type:** open verification

## [RESOLVED] FU-007 — Eyeball A3 modals in a real browser
- **Raised:** 2026-06-05 (A3)
- **Resolved:** 2026-06-12 — user spot-checked various A3 modals in browser
  (including delete-confirm dialogs and sizing-fix cards); backdrop+Esc cancel
  cleanly without committing, cards render correctly.
- **Type:** leftover
- **What:** A3 was verified statically only — `node_modules` isn't installed in
  this checkout, so no lint / `quasar build` / dev-server run happened. Need to
  confirm backdrop+Esc dismiss without committing, and that the comparison /
  orphans / quick-add cards (scoped-class → `card-style` fix) still size right.

## [RESOLVED] FU-001 — "Flat danger" BaseButton variant for low-emphasis deletes
- **Raised:** 2026-06-04 (A2 Phase 2)
- **Type:** follow-up
- **What:** A2 left flat-negative delete buttons as raw `q-btn` because BaseButton
  had no flat-danger shape.
- **Why deferred:** needed a new BaseButton variant.
- **State note:** RESOLVED 2026-06-05 — `danger-ghost` variant added
  (`{ flat: true, color: 'negative' }`) and wired into `StockItemDetailPage`
  (Delete + clear-expiry) and `MealPlansOverview` (Delete plan).
