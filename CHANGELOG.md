# Changelog

All notable changes to Discount Dora live here. Versions follow loose
semver — major bumps signal schema or breaking-config changes.

## [Unreleased]

### Added
- **Substitutes graph** (N7). New `/substitutes` route with a
  force-directed cytoscape.js view of every stock item and which
  items can stand in for which. Search dims non-matching nodes;
  stock-group chips filter; "Show isolated" toggles loners; layout
  picker (force / concentric / breadth-first). Tap a node for a side
  panel with current substitutes, an autocomplete to add a new one,
  and a deep-link to the stock detail page. Tap an edge to edit notes
  or remove the pair. Layout stays stable across single-edge
  mutations.
  - **Schema refactor**. Migration `c8a1d3b6e9f4` rebuilds
    `StockItemSubstitute` as an undirected pair table — columns
    `stock_item_a_id`, `stock_item_b_id`, `notes`, `created_at`, with
    a CHECK enforcing canonical (a < b) ordering so each unordered
    pair has exactly one row. Pre-release destructive migration; dev
    DB re-seeds with canonical pairs. Existing per-stock-item add /
    remove endpoints canonicalise transparently; the stock detail
    page now reads pairs in both directions and the backup/restore
    pipeline tracks the new column names.
  - **`/api/substitutes` endpoints**. `GET /graph` returns nodes
    (every stock item) + edges (every pair). `POST` upserts an
    undirected pair with optional notes (idempotent on the unordered
    pair). `DELETE` removes a pair via `?a=&b=` query params.

- **Reports / Analytics page** (N6). New `/reports` route with six
  cards backed by `/api/reports/*` endpoints — stock value over time,
  spend by merchant, top 10 most-bought, items that keep running out,
  savings captured, and multi-product price trends. Range selector
  (30d / 90d / 1y / all). Charts rendered with ECharts via
  `vue-echarts`. Every item chip deep-links to the matching stock
  detail page; "Mark all essential" on the keeps-running-out card
  flags items in one click.
  - **Price snapshot on shopping list lines**. Migration
    `c6e9f4a82d15` adds `picked_offer_price` + `list_price_at_pick` to
    `ShoppingListLine`. Captured when a line is first ticked (cleared
    on untick); finishing a list backfills any ticked-without-snapshot
    rows so reports stay honest after future price moves.

- **Auto-generated shopping lists** (X5). The "build me a list" path is
  now one endpoint with seven sources you can mix-and-match.
  - `POST /api/shopping-lists/auto-generate` replaces the older single-
    source `/autogenerate`. Body shape:
    `{ name?, merge_into_list_id?, sources: { low_stock?, out_of_stock?,
      essentials_only_for_low?, flagged?, frequently_added?,
      frequently_added_limit?, meal_plan_week?, recipes?[] } }`.
    Items collected by more than one source are deduped, keeping the
    highest-priority provenance — order is
    `auto_recipe > auto_meal_plan > auto_flagged > auto_essential >
     auto_low_stock > auto_frequently_added`. Recipe and meal-plan
    sources subtract anything already at "Well-Stocked".
  - `POST /api/shopping-lists/<id>/append-low-stock-essentials` —
    one-click convenience wrapper that tops up an existing list with
    essentials that are low or out.
  - **Per-line provenance**. New `ShoppingListLine.added_via` (enum:
    `manual` / `auto_low_stock` / `auto_essential` / `auto_flagged` /
    `auto_recipe` / `auto_meal_plan` / `auto_frequently_added`) and
    `added_at` (timestamp) columns — migration `b5d8e2f3c14a`. Drives a
    chip on every non-manual line in **Shopping List detail** so the
    user can see *why* something landed on the list. Manual edits to
    quantity or merchant selection flip the line back to `manual`
    automatically.
  - **Silent auto-add on low**. The existing `StockItem.auto_add_when_low`
    trigger (which fires when a level drops to Low or Out) now lands
    the line with `added_via=auto_low_stock` and skips the silent add
    if the item is already on **any** non-archived list (not just the
    primary). `PATCH /api/stock-items/<id>` returns
    `{ auto_added: { line_id, shopping_list_id } }` when it fires, so
    the frontend can surface an undoable "Tomato Soup auto-added to
    <list>" toast.
  - **Stock item detail** gains the "Always include in auto-generated
    lists" toggle (`is_flagged`) alongside the existing "Auto-add when
    low or out" (`auto_add_when_low`); both have explanatory tooltips
    spelling out the difference.
  - **Stock Overview** filter chips: "Flagged for auto" and the new
    "Will auto-add on low".
  - **Shopping Lists overview** "New list" dropdown gains **Advanced
    auto-generate…** — a modal with checkboxes for every source plus a
    merge-into picker.
  - **Recipes overview** "Add missing to list" routes through
    `/auto-generate` with `sources.recipes=[id]`, so the lines land
    tagged `auto_recipe` with the recipe name as the chip detail.
  - **Meal Plans overview** "Generate shopping list for this week" now
    routes through `/auto-generate` with `sources.meal_plan_week=<start>`
    — well-stocked ingredients are subtracted server-side and every
    line is tagged `auto_meal_plan`.
- **Stocktake / focused review** (X1). New `StockItem.last_checked_at`
  column (migration `a4c7e1d9b832`, indexed) — distinct from
  `stock_level_last_updated` so a user confirming "yes, the level is
  still correct" stamps a check without rewriting the level history.
  Updating the level still bumps both timestamps.
  - `GET /api/stocktake/queue?limit=` — items past their per-item
    `days_until_stocktake_alert` window, ordered most-overdue-first;
    never-checked items surface ahead of everyone else (with an
    `overdue_days = -1` sentinel for the UI).
  - `POST /api/stock-items/<id>/check` — idempotent, only touches
    `last_checked_at`.
  - `POST /api/stocktake/bulk-check` — bulk variant.
  - `POST /api/shopping-lists/<id>/review/complete` — for the
    shopping-list review-mode flow; bulk-sets ticked items to
    Well-Stocked and stamps `last_checked_at`.
  - New `/stocktake` overview page (top-of-queue preview + "Start
    review" CTA) and `/stocktake/run` fullscreen focus mode: one item
    at a time, big "Still correct (1) / Change level (2) / Out of
    stock (3) / Skip (s)" buttons with keyboard shortcuts, "Add to
    list" secondary action, session-complete summary card.
  - **Stock Overview** toolbar gains a **Stocktake (N)** button that
    pulses with a brand-coloured glow when the overdue count is
    positive.
  - **Shopping List detail** menu gains **Finish review** —
    bulk-marks every ticked item as Well-Stocked + stamps the check
    (the spiritual sibling of the existing finish-shopping flow).
- **PWA mode** (M1). Discount Dora is now installable on every
  major surface. Quasar's `pwa` config block is fully wired:
  - **Manifest** — `name`, `short_name=Dora`, `description`,
    `theme_color` + `background_color` matching the brand swatches,
    `display: standalone`, `orientation: portrait-primary` (kitchen-
    phone use), icon set spanning 192/512 px (with the 512 doubling
    as the maskable), and three launcher shortcuts: **Primary list**
    (`/shopping-lists?open=primary`), **Scan**
    (`/data/barcodes?action=scan`), and **Add item**
    (`/stock?new=1`).
  - **Service worker** — Workbox `GenerateSW` with
    `skipWaiting + clientsClaim + cleanupOutdatedCaches`. Runtime
    caching: `/api/*` → NetworkFirst with a 5 s timeout (keeps the
    UI snappy when the backend lags), stock-item images → CacheFirst
    (30 days × 200 entries), merchant product images → CacheFirst
    (7 days × 500 entries). Navigation failures fall through to
    `index.html`; `/api/*` is on the navigate-fallback denylist so a
    backend outage doesn't silently swap a JSON response for HTML.
  - **Offline page** — `public/offline.html` (branded, mentions the
    F3 offline queue so the user knows their ticks aren't lost).
  - **Install prompt** — new `composables/usePwaLifecycle.ts` defers
    `beforeinstallprompt`; a `<PwaInstallPrompt />` component
    surfaces an "Install Dora" button in Settings → About. iOS
    Safari (which doesn't fire the event) gets a tailored
    "Share → Add to Home Screen" hint.
  - **Update flow** — `controllerchange` on `navigator.serviceWorker`
    pops a "New version available · Reload / Later" Notify (zero
    timeout — the user opts in to the reload).
  - **Per-mode dev ports** — SPA stays on 5174; PWA dev runs on
    5175, SSR on 5176, so all three can be served side-by-side
    during development.
- **Self-serve auth surface** (A1). The full out-of-band flow lands:
  - `POST /api/auth/register` enforces password rules (≥10 chars + a
    letter + a digit), email-format validation, and case-insensitive
    email uniqueness. First user still auto-becomes admin AND
    auto-verifies (so a fresh install without SMTP isn't locked out).
    Every other registration emails a verification link with a 24 h
    SHA-256-hashed token.
  - `POST /api/auth/verify-email`, `POST /api/auth/resend-verification`
    (anti-enumeration + 1/min/IP-email).
  - `POST /api/auth/forgot-password` (anti-enumeration, 5/min/IP-email)
    issues a single-use 1 h reset token; `POST /api/auth/reset-password`
    consumes it, applies the new password, bumps `password_changed_at`,
    revokes any still-live reset tokens, and emails a notification.
  - `POST /api/auth/me/password` extended with the same password rules
    + notification email; bumping `password_changed_at` invalidates
    every other-device session on its next `/me` probe via a new
    session-staleness check.
  - `POST /api/auth/me/email` (request) + `POST /api/auth/email-change/confirm`
    confirm a new address before it swaps (anti-account-takeover).
  - Login is rate-limited (5/min/IP) with proper `Retry-After`.
  - Every auth event audits via I2's `audit.emit`
    (`auth.user.registered`, `auth.email.verified`,
    `auth.password.reset_requested`, `auth.password.reset`,
    `auth.password.changed`, `auth.email.changed`,
    `auth.login.success`, `auth.login.failed`).
- **Deployment-aware email links.** A new `DORA_PUBLIC_URL` env var is
  the canonical home for the SPA across PWA, mobile-shell, and
  self-hosted-desktop deploys — verify / reset links are built off it
  (falls back to the request's `Origin` header, then
  `http://localhost:5174` for dev).
- **Transactional email helper.** New `dora_api/infrastructure/email_sender.py`
  drives SMTP from `DORA_SMTP_*` env vars with a Jinja-template loader at
  `dora_api/email_templates/` (`verify_email.html`, `reset_password.html`,
  `password_changed.html`, shared `_layout.html`). **Dry-run** mode
  kicks in when `DORA_SMTP_USERNAME` is unset — the email body lands
  in the regular log stream instead of being sent, so self-hosted
  desktop installs without SMTP can still copy-paste verification
  links.
- **Frontend auth pages.** `/verify-email`, `/forgot-password`,
  `/reset-password`, `/confirm-email-change` all land outside the
  main layout (no nav chrome for someone clicking a link in a fresh
  browser). LoginPage gains a **Forgot password?** link, a
  password-rule hint in register mode, and a "Email verified" toast
  on arrival from `?verified=1`. Frontend `AuthApiService` exposes
  every new endpoint with typed wrappers.
- **Audit log + admin viewer** (I2 round B). A new `AuditEvent` table
  (migration `e9a2c4b1f7d8`) captures every mutating API request,
  every login success/failure, every client-side `warn`/`error` shipped
  via `/api/client-logs`, and any explicit `audit.emit(...)` from
  service code. Rows carry `occurred_at`, `source` (`dapi` / `mapi` /
  `emailer` / `web` / `system`), `actor_user_id`, `actor_ip`, `action`
  (verb-noun, e.g. `stock_item.created`, `auth.login.failed`),
  `entity_type` + `entity_id`, `request_id` (matches the existing
  X-Request-Id correlation), JSON `payload`, and `severity`. Indexed
  on `occurred_at` plus per-actor / per-entity / per-action compound
  indexes for the admin filters. An `audit.scrub(payload)` pass strips
  any key matching the privacy deny-list (`password`, `token`,
  `api_key`, …) before persistence. Nightly `BackgroundScheduler` job
  prunes events older than `DORA_AUDIT_RETENTION_DAYS` (default 365).
  Admin-only `GET /api/audit/events` (filter by source / severity /
  actor / action / entity / request id / time range, paginated up to
  500 per page) plus `GET /api/audit/events/<id>`. New
  **Settings → Admin → Audit log** page with a filter strip, paginated
  table with severity chips, click-to-open detail dialog (pretty-printed
  payload, "Find related" button that pivots the filter to the same
  `request_id`), and **Export CSV** of the current page.
- **Structured logging across every service** (I1 round A). All three
  services (dora_api, merchant_api, emailer) now route through a single
  `configure_logging(service_name, log_dir, debug=...)` helper that
  wires a stdout `StreamHandler` (for `docker logs`-style aggregation)
  plus a `RotatingFileHandler` (10 MB × 5 backups, e.g.
  `data/logs/dapi/dapi.log`). The shared formatter is
  `%(asctime)s %(levelname)s [%(name)s] [req=…] [user=…] %(message)s`,
  with `request_id` and `user_id` injected from `contextvars` by a
  `LogContextFilter` so every line in a request emits with the same
  IDs without any caller plumbing. The dora_api middleware now
  generates a `request_id` (or honours an incoming `X-Request-Id`),
  binds the session user, logs `→ GET /api/...` at start +
  `← 200 GET /api/... (12.3ms)` at end, and echoes `X-Request-Id` on
  every response so the SPA's axios correlation id round-trips. The
  per-service old `configure_logger` helpers are gone; `sqlalchemy.engine`
  is pinned to WARNING regardless of root so SQL echo doesn't drown
  the stream, and Werkzeug's per-request INFO line is silenced (the
  middleware already emits a richer equivalent).
- **Client-side logger + `/api/client-logs`.** A new
  `useClientLogger` composable mirrors the standard levels and ships
  `warn` / `error` to the new `POST /api/client-logs` endpoint
  (rate-limited at 10 events / 60 s per session, server-side and
  client-side). The existing `boot/globalErrorHandler.ts` is hooked
  up to it, so Vue render errors, `window.onerror`, and unhandled
  promise rejections all land in the server's log stream now —
  including pre-login crashes (the endpoint is in `PUBLIC_ENDPOINTS`).
  Payload includes URL, user-agent, stack excerpt; capped at 2 KB.
  Audit-table persistence lands in the next round.
- **Export & Print: stock overview + meal plans.** Two new sections in
  Data → Export & print:
  - **Stock overview** — install-wide CSV (`location, name, level,
    expiry, is_flagged, is_open, auto_add_when_low, barcode, notes`,
    grouped by location) and a stocktake-friendly print view with
    checkbox column per item.
  - **Meal plans** — per-plan CSV (`scheduled_for, slot, meal, servings`)
    and a weekly-calendar print view with days as rows and slots
    (Breakfast / Lunch / Dinner / Snack + any custom ones) as columns.
  Both surface as `GET …/export?format=csv` and `…/print-view` to match
  the existing N4 endpoints. New "Export" dropdown on the Stock Overview
  toolbar (CSV / Print) and new CSV / Print buttons in the Meal Plans
  toolbar. The bulk-action banner on Stock Overview also gains a
  **Print QRs** action that opens the QR sheet for the current
  selection.
- **Scan polish.** The ScanOverlay shows a fading "Decoded: <value>"
  banner on a successful read, and a new `close-on-decode` prop closes
  the overlay automatically after the first valid scan (used by the
  Stock Overview Scan and the StockItemDetail "Register barcode" flows,
  where the user only ever wants one scan). The Data → Barcodes & QR
  Scan tab keeps the default continuous-scan behaviour.
- **Camera setup notes.** `web_app/README.md` calls out the HTTPS
  requirement for `getUserMedia` outside `localhost` so phone / LAN
  testing doesn't silently fail.
- **Backup uploader refactor.** Data → Backup & restore now uses the
  shared `useChunkedUpload` composable that powers DataImport, so the
  start/chunk/finish/abort plumbing has a single home. Behaviour is
  unchanged.
- **Barcodes & QR.** Data → Barcodes & QR is now live with three tabs:
  - **Scan** — fullscreen `@zxing/browser` camera overlay with a
    crosshair box, dim mask, debounced repeat-decodes (2 s window),
    torch toggle on supporting cameras, and a manual-entry escape
    hatch. On decode, hits `GET /api/data/barcodes/lookup?value=...`
    which resolves either a `dora://stock-item/<uuid>` link, a raw
    `StockItem.barcode` match, or a `ProductBarcode` (returning the
    linked stock item if any). Unknown values prompt
    "Register against a stock item" with a typeahead.
  - **Print sheets** — pick stock items (filter box, virtualised
    list), choose a layout (A4 21-up or Avery 5160), open a printable
    HTML grid in a new tab. PDF via the browser's Save-as-PDF, same as
    N4. A "Print all stock items" shortcut covers the stocktake case.
  - **Manage** — inline edit / clear / "Print one" QR per item.
  Stock-item detail page gets two new toolbar buttons: **Show QR**
  (modal with a big QR + Print One) and **Register barcode** (opens
  the scan overlay focused on the current item). Stock overview gets
  a **Scan** button that jumps straight to the matched item's detail
  page on a successful decode.
  Backend additions: a new `barcode` column on `StockItem` (globally
  unique per install), a new `ProductBarcode` table for many-to-one
  product↔barcode links, plus four endpoints:
  - `GET /api/stock-items/<id>/qr?size=...` — PNG, 64-1024 px range.
  - `GET /api/stock-items/qr/sheet?ids=&layout=` — printable HTML
    label sheet; missing `ids` falls back to all stock items.
  - `POST /api/stock-items/<id>/barcode` — 409 on collision.
  - `DELETE /api/stock-items/<id>/barcode` — clear.
  - `POST /api/data/barcodes/register-against-product` — wire an
    unknown scanned code to a saved product.
  QR encoding is `dora://stock-item/<uuid>` so a printed QR scanned
  back through the overlay round-trips to the item. ProductBarcode
  rows ride along in backups by default (new section in
  `restore_shared.SECTIONS`). Migration `d7f4a2c98e15`.
- **Export & Print.** Data → Export & print now lists every shopping list
  (filterable Active / Archived / All, primary pinned to the top) and
  every recipe (with name-filter), each row carrying **CSV** and
  **Print** buttons. New backend endpoints:
  - `GET /api/shopping-lists/<id>/export?format=csv` — columns
    `location, item, quantity, merchant, unit_price, total, picked_up,
    notes`, grouped by location and alphabetised within each group.
  - `GET /api/shopping-lists/<id>/print-view` — server-rendered HTML
    with a printer-friendly stylesheet (`@media print` strips the
    floating toolbar; big tap-friendly checkboxes; sections per
    location; totals strip showing remaining / picked-up / estimated
    total).
  - `GET /api/recipes/<id>/export?format=csv` — ingredient list
    (`ingredient, quantity, unit, notes, location`).
  - `GET /api/recipes/<id>/print-view` — recipe card with ingredient
    list + instructions + nutrition, sized for a fridge magnet pin.
  PDF generation is **browser-side** (Save as PDF from the print
  dialog) — no new server dependencies. Download filenames are
  slugified to e.g. `shopping-list-weekly-shop-2026-05-21.csv`. A new
  shared `useShoppingListExport` composable powers both ExportPrint and
  a new "Export as CSV" / "Print / Save as PDF" pair on the
  ShoppingListDetail overflow menu; a sibling `useRecipeExport` does
  the same for recipes.
- **Spreadsheet import.** Data → Import now accepts `.xlsx` and `.csv`
  files and turns them into stock items. The file is staged via the
  existing chunked-upload stack, then `POST /api/data/import/spreadsheet/inspect`
  reads its sheets, shows a five-row preview, and auto-picks the most
  likely column for each Dora field (Name [required], Stock level,
  Location, Group, Expiry, Is essential). The mapping is editable per
  sheet; the preview re-renders live as the user reassigns columns.
  `POST /api/data/import/spreadsheet/commit` walks every row in a
  single transaction with row-level error reporting — bad stock-level
  text becomes "Stock level 'foo' isn't recognised. Valid options:
  Well-Stocked, Sufficient Stock, Low Stock, Out of Stock", missing
  Location / Group can be auto-created via toggles, and
  **Halt on first error** rolls the whole import back. After commit the
  result dialog lists each row with a coloured chip (`ok` / `dup` / `err`)
  and a one-click **Download error rows (CSV)** so the user can fix
  problem rows offline and re-import only those. `is_essential` maps
  to `StockItem.is_flagged` (the closest existing flag in the schema).
- **Data Management shell** (backup/restore, import, export & print, barcodes —
  sections to follow). New top-level **Data** entry in the nav and command
  palette opens `/data`, with a left rail listing the four sub-sections and a
  breadcrumb crumbed `Data › <section>`. The sub-pages are placeholders for
  now; subsequent rounds wire up the actual backup, import, export and
  barcode tooling.
- **Backup export.** Data → Backup & restore now offers a one-click
  **Download backup** that streams a single JSON snapshot
  (`dora-backup-<date>.json`) of every in-scope entity — stock groups,
  levels, locations and items (including substitutes and product links),
  saved products, shopping lists and templates, recipe collections,
  recipes and ingredients, meals and meal plans. Images round-trip via
  base64. Cached merchant data (merchants, offer history, change log,
  notifications, app settings) and user credentials are intentionally
  excluded. Backed by a new `GET /api/data/backup` endpoint that records
  `exported_by` for provenance.
- **Chunked-resumable backup uploads.** New endpoints
  `POST /api/data/uploads/{start,chunk,finish}` and
  `DELETE /api/data/uploads/<id>` stage backup files under
  `data/uploads/` 8 MB at a time; a failed chunk retries up to three
  times without restarting the whole upload. Total cap is now **2 GB**.
  The SPA no longer parses backup files client-side at all — picking a
  file streams it via chunks, shows an upload progress bar, then calls
  `inspect` with the `upload_id`. `restore` likewise accepts
  `upload_id` (still backwards-compatible with inline `backup` bodies).
  Stale uploads older than an hour are swept on every new `start`, and
  cancelling the file picker issues `DELETE` proactively.
- **Stream-parsed inspect.** The backup preview now uses `ijson` to
  walk the staged file without ever instantiating the full document in
  server memory. Counts, duplicate-flagged names, and per-section
  sample rows (capped at 500 per section with an overflow indicator)
  are streamed out — multi-GB backups can be inspected on modest
  hardware. The tree view in the SPA renders straight from the
  inspect response.
- **Last-backup timestamp + restore report + bigger uploads.** The
  Create-backup card now shows "Last backup: N min/hr/days ago" using a
  new `User.last_backup_at` column (migration `c5e8f3a91b07`) that the
  backup endpoint stamps on every successful download. `/api/auth/me`
  carries the value so the card updates without a separate round-trip.
  After a restore lands, the page now opens a results dialog with a
  per-section "+N created · M skipped" breakdown plus an expandable
  warnings list, and a **Reload now** button to swap to a fresh app
  state on the user's own pace (no more silent auto-reload). Upload cap
  raised from 50 MB to **500 MB** on both client and server; the inspect
  endpoint streams multipart uploads to a temp file 8 MB at a time
  instead of holding them in memory. (True chunked-resumable uploads
  are still future work — flaky network mid-upload still requires a
  restart.)
- **Backup section toggles + more sections.** The Create-backup card now
  shows per-section checkboxes grouped into "Core data" (on by default —
  stock, lists, recipes, meals, etc.) and "Optional" (off by default).
  Three new optional sections are wired up: **System settings** (the
  install-wide AppSetting row), **User accounts** (every user row minus
  `password_hash` — restoring leaves the hash null so an admin reset is
  required for those accounts to log in), and **Historic product offers**.
  Each group has _All / None_ shortcuts and an "X of Y selected" caption.
  Under the hood the section catalogue is declared once in
  `restore_shared.SECTIONS` — adding a new section is a single entry there
  plus its FK classification, and both the export filter and the restore
  iterator pick it up automatically. `GET /api/data/backup` now accepts
  `?sections=a,b,c` to narrow the dump (unknown keys → 400) and records
  the included list in the payload's `sections` field.
- **Backup inspect + restore.** Picking a backup file in
  Data → Backup & restore now uploads it to a new `POST /api/data/backup/inspect`
  endpoint and renders a preview tree: counts per section, one branch per
  entity type, leaves checkbox-tickable. Rows whose natural key (name for
  most entities, name+parent for locations, merchant+stockcode for
  products) already exists locally are flagged with a `duplicate` chip and
  greyed out. A header counter reports "X of Y items selected, Z
  duplicates skipped" alongside select-all / clear-selection actions. Two
  commit buttons hit `POST /api/data/backup/restore`: **Restore selection**
  (partial mode) and **Restore all (skip duplicates)**. A confirm dialog
  precedes either. The restore is single-transaction; on failure the
  whole thing rolls back. Hard-FK targets (stock locations including
  parents, stock groups, recipe collections, stock levels) are pulled in
  transparently when partial mode would have orphaned them; soft FKs
  (preferred / selected product) null out with a warning if the target
  isn't being imported; required FKs that can't resolve skip the row
  with a warning. On success the page reloads so every store reflects
  the new data.

### Changed
- **Command palette anywhere with Cmd/Ctrl-K.** A top-of-screen palette opens
  from any page (even when an input is focused) and searches across stock
  items, shopping lists, recipes, locations, products, meals and meal plans —
  plus runs in-app commands like _Create stock item_, _Open primary shopping
  list_, _Auto-generate shopping list from low stock_, _Toggle dark mode_,
  _Show keyboard shortcuts_, and every _Go to …_ navigation. Substring and
  fuzzy matches are highlighted in the result title. Empty query shows your
  recents (last 20 entities you visited, kept per-device) and your most-used
  commands. Arrow keys move the selection, **Enter** runs it, the first
  **Esc** clears the query and the second closes. Pages can register their
  own contextual commands via `useCommands()`, auto-deregistered on unmount.
  The locations "find item" overlay now rides the same unified `/api/search`
  endpoint.
- **Keyboard shortcuts everywhere.** Press **?** anywhere to open a cheatsheet
  of every shortcut live on the current screen, grouped by area. Global keys:
  **/** focuses the Stock search (or jumps there), and **g** then **s / l / r /
  d / h** navigates to Stock, Lists, Recipes, Dashboard or Help. On the Stock
  screen, **n** adds an item, **f** focuses the filter, arrow keys move a
  highlight through the grid, **Enter** opens the focused item, and **a** adds
  the focused (or selected) items to your primary list. On a shopping list,
  arrow keys move between lines, **Space** ticks the focused line and **n** adds
  an item. Shortcuts ignore your typing in text fields, and **Esc** closes the
  cheatsheet. (Ctrl/Cmd-Z undo/redo from the undo system still works alongside.)
- **One-click Undo across the app.** A new Undo button in the header
  (tooltip shows the most-recent action label) reverses the last 20
  actions; Ctrl/Cmd-Z does the same from anywhere outside a text input,
  Ctrl/Cmd-Shift-Z (or Ctrl-Y) redoes. Destructive actions also pop a
  toast with an inline Undo for 10 seconds. Wired actions: bumping a
  stock item's level, ticking or unticking a shopping list line, moving
  / editing a stock item, **deleting a stock item** (round-trips through
  a new `/api/stock-items/restore` so the item comes back with the same
  id and references), removing a line from a shopping list, and the big
  one — **Finish shopping**: un-archives the list, rolls back the bulk
  stock-level bumps from the original ticks, and demotes whichever list
  was auto-promoted to primary, all in one click. Undoing an action that
  was processed via the offline queue works once sync completes.
- **Dora keeps working when the network doesn't.** A slim banner pins
  under the header whenever you're offline or we can't reach the server
  — with a Retry button and a live "N changes queued" counter. While
  offline, the four most common mid-shop actions (ticking shopping-list
  lines, bumping a stock item's level, marking it opened or restocked,
  pushing or clearing an expiry date) are queued in the browser and
  drained automatically when we reconnect — your optimistic ticks stay
  put in the meantime. Creates and deletes still fail loudly because
  silently inventing-or-vanishing entities is rarely what you want.
- **Errors no longer take down the whole screen.** A new error boundary
  wraps every page; if something on the page throws while rendering,
  the rest of the app (header, drawer, Dora bubble, alerts bell) stays
  alive and the page itself shows a friendly recovery card with Reload,
  Go to dashboard, and Report this (pre-fills a GitHub issue with the
  error message and a reference id). New `/errors/server` and
  `/errors/not-found` routes pick up failed lazy-chunk loads and
  in-app "not found" links respectively. Server (5xx) responses now
  surface a normalised "the server tripped" toast instead of silently
  collapsing.
- **HTTP client is harder to surprise.** Every request now carries a
  unique X-Request-Id so any error you see references back to the exact
  server log line. GETs auto-retry up to 3 times with exponential
  backoff on network errors and 502/503/504; mutations never auto-retry
  (the offline queue is the right tool for that). Every error reaching
  callers is normalised into the same shape — status, code, message,
  details, correlation id — instead of leaking raw axios objects.
- **Dora is now context-aware.** Open the chat on any screen and a fresh
  "On this page" chip row sits above the generic quick-actions, suggesting
  the 2-3 most useful next moves for that screen. On a stock item it's
  **Find cheaper alternatives** (jumps to Product Search pre-filtered),
  **Add to my list** (uses the same composable as the cart button), and
  **Find substitutes** (opens the substitutes section on the detail
  page). On a recipe: **What's missing?** (lists out-of-stock or
  untracked ingredients in chat), **Plan this for a day** (jumps to Meal
  Plans with the recipe pre-targeted), and **Add missing to a list**
  (bulk-adds the missing ingredients straight to your primary list).
  Stock overview, recipes overview, shopping list detail, my products,
  locations and the dashboard get their own contextual chips too. Every
  action routes through the same cross-feature composables (P0) the rest
  of the app uses, so behaviour stays identical wherever you trigger it.
- **Alerts panel rounded out.** Alerts are now grouped under **High
  priority / Medium / Low / FYI** headers so the eye doesn't have to
  scan for severity. Every row picks up two new actions alongside the
  existing extend-expiry / mark-restocked / acknowledge: **View in
  context** jumps you to the Stock screen pre-filtered to attention
  items, and **Snooze 7d** hides the alert on this device for a week
  (with a one-click Undo in the toast). Snoozed alerts get their own
  collapsed section at the bottom of the panel with per-row Unsnooze.
  A new bottom action — **Add N low/out items to primary list** —
  bulk-queues every low- and out-of-stock item from the panel onto your
  primary shopping list in one click (skipping anything already on it).
- **Dashboard is now the morning glance.** Four new cards sit above the
  pantry/totals strip and surface what to actually do, not just what
  exists:
  - **Needs your attention** lists the top alerts (expired, expiring soon,
    low/out, essentials low) with the same inline actions as the alerts
    panel — push expiry, mark restocked, acknowledge — and each item name
    deep-links to its stock detail page.
  - **Primary shopping list** shows the live "to grab" count, dollar
    remaining, and savings-vs-RRP total for whatever list is primary, with
    a one-tap jump-to-list. When no primary is set the card prompts you
    to pick one.
  - **Cookable tonight** lists up to three recipes that have every
    ingredient in stock right now (favourites and recently-cooked-less
    bubble up first), each with prep+cook time, servings, a deep link to
    the recipe and a "Cook" button straight into cook mode.
  - **Best deals on your saved products** ranks your saved products by %
    off, showing the merchant, the linked stock item chip, the price now
    vs the strike-through RRP, and the discount badge.
  Every chip, number, and "See more" link deep-links into the relevant
  screen (Stock, Recipes with `?cookable=true`, My Products, etc.). Cards
  can be toggled in the existing **Cards** menu.
- **Product search is now a deal-comparison surface.** Results render as cards
  with a discount badge that deepens from amber to red as the saving grows, the
  unit price (per 100g/ml or each), the merchant logo, and — for products you've
  saved — a price-trend sparkline. Each card can save to favourites, link to an
  existing stock item, or "quick-add" (saves the product, starts tracking it as
  a stock item, links them, and drops it on your primary list in one tap). Pick
  2–3 results and open a side-by-side comparison. New filters: price range,
  unit-price ceiling, size/weight range, and a half-price-or-better toggle;
  sort by relevancy, name, price, unit price or biggest saving. Merchant
  connection status badges sit up top so you can see at a glance which scrapers
  are healthy.
- **Meal plans are now a drag-and-drop week.** Drag any meal from the palette
  onto a day to plan it (cookable-now meals are flagged green), and click a
  planned entry to jump to its recipe or straight into cook mode. A sidebar
  rolls up the whole week's ingredient demand against current stock and shows
  exactly how many items you'll need to buy, with one click to generate a
  shopping list for the week. A "Suggest meals I can cook now" button surfaces
  everything fully in stock right now. (Also fixed the week's ingredient
  rollup, which was silently returning nothing.)
- **Cook mode now closes the loop on what you used.** The ingredients pane
  shows the shared stock-item chips and marks each one "used" as you tick a
  step (or advance through it) — names mentioned in a step are matched
  automatically, and you can toggle any ingredient by hand. Finishing prompts
  to update stock levels (used items step down one level), log it as a meal
  eaten, and add anything that's now low or out straight onto your primary
  shopping list. Per-step timers and voice control are unchanged.
- **Recipes overview is now a cooking command center.** Recipes are grouped
  by collection (with an "Uncategorised" bucket), every card surfaces a live
  **Cookable now** badge — or a one-click **Missing N** chip that opens an
  "add ingredients to a shopping list" dialog — and the action menu on each
  card covers cook, edit, duplicate, mark made, add all ingredients to a
  list, add to a meal plan and delete. New filters: cookable now, missing
  ≤ N ingredients, collection (incl. uncategorised), tags pulled from
  cuisine + category, and "uses stock item" (which deep-links here from the
  stock item detail page via `?usesStockItem=…`). A new **Compare** mode
  lets you pick 2–3 recipes and pop them open side-by-side — ingredients,
  times, difficulty and what's missing right now — so you can decide what
  to cook tonight at a glance.
- **Locations are wired into the rest of the app.** Clicking a zone on the
  heatmap now opens a side panel that lists every item stored anywhere
  under it (rolled up across descendants), with each chip carrying the same
  cross-feature menu the rest of the app uses — add to a list, mark
  restocked, push expiry, find substitutes, see recipes using it. Two new
  per-zone shortcuts: **Needs attention here** jumps to the Stock screen
  pre-filtered to that location's attention items, and **Shopping list**
  spins up a fresh list from every low/out item in the zone (named "Restock
  &lt;zone&gt;"). The same two actions live in the header of the zone detail
  page. The Stock screen now reads `?location_id=…&attention=true&level_id=…`
  query params so other screens can deep-link straight into a filtered view.
- **Shopping lists overview is the launchpad for every kind of list.** The
  "New list" menu now bundles every starting point in one place: from
  flagged essentials, from every low-or-out item (with a live count of how
  many that is), from a recipe (pulls the recipe's ingredients into a fresh
  list), from a meal plan (aggregates ingredients across every meal in the
  plan, scaled by servings), or from a saved template. Each card carries
  more actions — open, set primary, copy unticked → new list (active),
  copy archived → new list, archive without finishing, delete — and the
  primary list gets a richer stats strip showing remaining, full list and
  Savings vs RRP totals at a glance. The empty state recommends
  auto-generating from low/out items when stock data says there's something
  worth restocking.
- **Shopping list detail is now a shopping-trip companion.** Lines render as
  the shared stock-item chip — same level badge, alert dot, on-list
  indicator and overflow menu as everywhere else — with a per-line menu to
  swap an item with one of its recorded substitutes or move it onto another
  list. You can group lines by stock location (for a shopper's route through
  the storage areas at home) or by chosen merchant. Offer chips now mark
  your preferred merchant with a star and show how much you save vs the
  product's RRP, and the totals card carries a "Savings vs RRP" headline.
  A new **Review mode** hides unticked items and shows exactly which stock
  items will bump to Well-Stocked when you finish. Finishing a list with
  unticked items now offers to copy them straight into a new active list
  before archiving, so nothing falls through the cracks. The inline picker
  has been replaced by the shared **Quick add** sheet so the same search,
  offer-selection and frequently-added suggestions appear wherever you
  trigger it.
- **Stock item detail is now a relationship hub.** A tabbed page — Overview,
  Linked Products, Recipes, Substitutes, Lists and History — with a toolbar to
  mark open, restock, set expiry, find deals or add to a list. Linked products
  show the current deal, a price-trend sparkline and a preferred-merchant star,
  with one-click "add cheapest to list". Recipes that use the item appear as
  cards, dimmed when other ingredients are also missing. You can now record
  substitute items and swap one straight onto a shopping list, see every active
  list the item is on, and review a timeline of its stock-level changes.
- **Pantry is now the command center.** Every item row is built from the shared
  stock-item chip and surfaces its live cross-feature links inline: a location
  chip that filters to that spot, an "on N lists" chip that shows (and jumps to)
  the lists it's on, an expiry control to push or clear dates without leaving the
  page, and a "used in N recipes" badge that previews the recipes on hover. Click
  a row to peek at the full item detail in a side panel without navigating away.
  New filters for "needs attention" and "used in a recipe", and the bulk bar can
  now add to a list, move location, mark restocked or set a substitute. Empty
  state points you at building a pantry from a recipe or a shopping list.

### Added
- **First-run setup wizard.** New users (and anyone with a fresh
  `onboarding_completed_at`) land on a guarded `/welcome` route that
  walks them through five short steps: a name + theme + font picker,
  an admin "you're in charge" callout for the first user, optional
  seeding of Dora's default stock groups and locations (idempotent —
  re-importing won't duplicate), adding their first stock item with
  inline "add another" and skip, and a four-card tour with deep links
  into the screens that matter. Progress persists to localStorage so
  refresh resumes where you left off. **Skip everything** stamps the
  completion timestamp and surfaces a 24-hour "finish setting up"
  banner on the dashboard with a one-tap Continue. Settings → Account
  carries a **Restart onboarding** entry for returning users who want
  to redo the tour.
- **My Products is now its own screen.** A dedicated grid at `/my-products`
  shows every saved product with the stock item it links to (click the chip
  to jump to that item), the live deal badge, the merchant, and an
  inactive/out-of-stock marker. Filters: by linked stock item, on-deal-now,
  by merchant, plus search across name/brand/merchant/size. Bulk-select adds
  **Add all on-deal to a list** (pre-selecting the merchant offer per line),
  **Unlink** and **Mark inactive**. A "Stock items without products"
  shortcut lists every tracked item that no active product links to, with
  one-click jumps into Product Search to find a match.
- **Dedicated recipe detail / edit page.** Recipes now have a proper editing
  surface at `/recipes/:id` with a two-column layout. Each ingredient row
  is an autocomplete bound to your tracked stock items — type a name that
  doesn't exist and "Create '<name>'" inlines a new stock item without
  leaving the page — plus a live level badge, a "Missing" chip when it's
  out of stock or untracked, and a per-row "add to primary list" button.
  A sidebar carries the cooking shortcuts: **Start cook mode**, **Add all
  missing to a shopping list**, and **Find substitutes for missing
  ingredients** (uses the substitutes graph from each stock item's detail
  page — click a substitute chip to swap it straight into the recipe).
  Secondary actions (mark made, delete, mark favourite) are one click away.
- **Import a recipe from a URL.** Paste any recipe page that publishes
  schema.org/Recipe JSON-LD (which is most major recipe sites) and Dora
  pulls the name, cuisine, category, times, servings, instructions,
  nutrition and ingredients. Ingredients are fuzzy-matched against your
  tracked stock items so most rows land pre-filled; unmatched items keep
  their raw text in the notes so you can pick a match or create a new
  stock item inline.
- **Frequently-added suggestions in Quick add.** The Quick add sheet now
  surfaces the stock items you've added to a list most often — based on
  every line you've ever added — so opening it without typing puts your
  usual basket one tap away. Each frequent suggestion is starred so it's
  obvious why it's first.
- **Shared building blocks for stock and shopping actions.** Stock items now
  appear as a consistent chip everywhere — picture, live stock level, an
  on-a-list indicator and an attention dot — with a built-in menu to add to a
  list, mark restocked, push expiry, find substitutes or jump to recipes that
  use it. Products get a matching chip with the current deal and merchant. A
  global quick-add sheet lets you drop any item onto a list from anywhere,
  picking the merchant offer as you go. These are groundwork the upcoming
  screens build on, so the same action behaves identically wherever you trigger
  it.
- **Dora's chat can be backed by your own language model.** An optional,
  bring-your-own-LLM assistant: an admin enables it in **Settings → System** and
  points it at a language model they run themselves (e.g. a local Ollama),
  entering the base URL and model name. Off by default — nothing is bundled,
  downloaded, or dictated, and when it's off Dora uses its built-in rule-based
  helper. With it on, the chat understands plain-English questions about your
  data — "what's low in the fridge?", "any specials on cheese?". The model uses
  tool-calling to fetch real rows, so it can't invent items or prices.
- **Add to your shopping list by asking.** "Add 3 apples and some milk" now
  works: the model extracts the items and quantities, Dora matches each to your
  tracked stock items, and adds them to your primary list. When a name matches
  more than one item ("which milk?") she shows the options as chips and waits
  for you to pick before committing — nothing is added until you confirm. Items
  with no tracked match are reported, not invented.
- **"What should I cook?"** Dora now suggests recipes. Ask for an idea by mood
  ("something spicy", "something light") and she translates it into recipe
  terms; or ask what you can make from what you have and she ranks recipes by
  how many of their ingredients are in stock — calling out the ones you can
  make right now and what's missing for the rest.
- **Dora answers how-to and general questions too.** Beyond data queries and
  shopping-list actions, the assistant now handles "how do I…?", app-help and
  general/chit-chat messages conversationally, grounded in a guide to what Dora
  can do — so it points you to the right page (e.g. "open Product Search") rather
  than shrugging. The old rule-based replies are now only used as a fallback
  when the model isn't reachable.

## [0.7.0] - 2026-05-20

### Added — the killer loop

- **Shopping list overhaul.** Multiple lists, primary/default flag for
  quick actions, archive on completion, copy archived → new active list,
  copy unticked items to a new list. Detail page lets you tick items off,
  adjust quantity, and pick which merchant offer to buy per line. Live
  totals (remaining, picked up, full list). Finish-shopping flow archives
  the list and auto-bumps every ticked item's stock level to "Well-Stocked".
- **Stock overview filters + cart-button quick-add.** Autofocus search,
  filter chips for stock level, location, essentials-only and on-list /
  off-list. Sort menu (name, level, last-updated). Cart button on each row
  one-clicks the item onto your primary shopping list, with the icon and
  colour reflecting where the item already sits across all your lists.
  Bulk-select mode adds multiple items to the primary list at once.
- **In-app alerts.** Bell icon in the header with a live badge for
  high/medium-severity items. Slide-in panel lists everything that needs
  attention — expired, expiring soon, out/low stock (essentials called
  out separately), stocktake overdue — with inline actions (push expiry
  7 days, clear expiry, mark restocked, acknowledge stocktake). Polls
  every 60 seconds.
- **Dora now answers "what needs my attention?"** — new quick-action chip
  pulls the same data as the bell.

### Added
- **Dora help assistant.** A floating mascot (bottom-right) opens a chat
  panel with quick actions for "What can I do on this page?", "What's new?",
  "Tell me something" and more. A dedicated `/help` page surfaces guides,
  the changelog, and a random food fact.
- **Version + update detection.** Dora checks the GitHub repo for newer
  releases and surfaces an update banner when one is available.

## [0.5.0] - 2026-05-19

### Added
- **User & global options.** Per-user theme (System / Light / Dark with OS
  auto-follow), font family (Default / Urbanist / Nunito), and text size
  (small / medium / large). Update username and password in-app. Subscribe
  / unsubscribe to the weekly deals email and choose compact format.
- **Admin Users page.** View all accounts, toggle admin role, toggle the
  deals subscription on another user, edit username and email, and reset
  another user's password (one-time generated value, copy-to-clipboard).
- **First-user-is-admin** on fresh installs.

## [0.4.0] - 2026-05-19

### Added
- **Hierarchical locations.** Zones → Areas → Sections replace the old flat
  Stock Locations list. New **Locations** page with per-node heatmap
  attention scores (rolled up from descendants), reason chips ("2 expired,
  4 low stock, 1 flagged"), and a global search overlay.
- **Move items by drag-and-drop.** Drop a stock item chip onto a zone, area
  or section to move it. Click-to-move via a hierarchical picker dialog
  remains the touch/mobile path.
- **`is_admin` flag** on users; admin-only routes gated server-side.

### Changed
- Stock locations table rewritten with `parent_id`, `kind` and `sequence`.
  Pre-release migration drops existing rows.

## [0.3.0] - 2026-05-19

### Added
- Initial settings page with per-user and admin (global) sections.

## [0.2.0] - 2025-02-23

### Added
- Recipes, meals, meal plans.
- Stock items get expiry dates and flags.

## [0.1.0] - 2025-01-18

### Added
- Initial release. Stock items, stock locations, shopping lists, merchant
  scraping (Coles, Woolworths, IGA, Aldi).
