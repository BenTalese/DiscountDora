# Chunk 18 — Backup & restore + Import

**Session:** 2026-10-23 overnight (solo, no subagents) · **Stage:** 1 (analysis only — no code changed)
**Surface:** the two admin data pages and everything behind them — the backup **library** (`POST/GET /api/data/backups`, download / restore / delete per row, retention + storage path on `AppSetting`), the backup **document** (`backup.py` + the `SECTIONS` catalogue in `restore_shared.py`), **inspect** (streaming `ijson` preview) and **restore** (`all_skip_duplicates` / `partial` with FK pull-in), the **chunked upload** stack (`/api/data/uploads/*`), **spreadsheet import** (`/api/data/import/spreadsheet/{inspect,commit}`) with the per-section CSV **templates** (`/api/data/import/templates`), and the SPA pages `AdminDataBackupRestore.vue`, `AdminDataImport.vue`, `useChunkedUpload.ts`.
**Boundaries:** barcodes / QR / OFF lookup on the same `DATA_ROUTER` (`barcodes.py`, `off_lookup.py`) → chunks 5/6; recipe URL/paste import → chunk 1; the nutrition dataset import → chunk 13; print views + per-surface CSV exports (`useStockOverviewExport` etc., FU-647) → chunk 20; `SettingsFileDrop.vue` (shared drop zone, 251 lines) is used only by these two pages but was **not** read this pass (listed in §E as a ride-along for Stage 2); `AppSettings` TS type gaps → 13-R16.

---

## 0. Reading list + files walked

**Governing docs read:** `FINALISATION_PLAN.md §4` row 18; feedback `# DATA` (10 bullets, lines 464–476); `SECURITY_REVIEW.md` rows "Backup credential exclusion", "Backup format", uploads §(121–130); `DORA_VERIFY.md` "Settings: Image quality is its own page (2026-08-23)" (the Backup page bullets + FU-717 deploy note) and the three pending "Backup → restore round-trips …" bullets under Cookbook chunks 6/7/8. Open FUs: FU-716 (page bypasses the API service layer), FU-647 (hand-built API URLs in exports — sibling pattern), FU-625 (`UserLlmProvider` not a backup section), FU-405 (ops / scheduled backups — Phase 4). Resolved and consulted: FU-387 (credential exclusion), FU-343/348/349/350 (templates), FU-359 (A-2 page redesign; left #2 "multiple export formats" and #7 "Export & print" explicitly unaddressed), FU-342 (library), FU-164 ("misdiagnosis: stale `meals`/`meal_recipes`" — fixed the **test**, not the restore code, see 18-R1), FU-717.

**Files walked in full (backend 2,696 lines · SPA 2,197 · tests 1,118):**

| File | Lines | Role |
|---|---|---|
| `dora_api/features/data/backup.py` | 118 | document builder (`GetBackupHandler`, `resolve_selected_sections`) |
| `dora_api/features/data/backup_library.py` | 379 | 5 library endpoints, retention, storage path |
| `dora_api/features/data/inspect_backup.py` | 309 | `POST /backup/inspect` — streamed + inline paths |
| `dora_api/features/data/restore_backup.py` | 384 | `RestoreBackupHandler` + `POST /backup/restore` |
| `dora_api/features/data/restore_shared.py` | 272 | `SECTIONS` catalogue, FK maps, codecs |
| `dora_api/features/data/import_spreadsheet.py` | 932 | inspect / commit / templates |
| `dora_api/features/data/uploads.py` | 241 | chunked upload start / chunk / finish / abort |
| `dora_api/domain/entities/backup.py` | 54 | `Backup` entity, status/trigger tokens |
| `dora_api/domain/entities/app_setting.py:191–198` | — | `backup_retention_count`, `backup_storage_path` |
| `web_app/src/pages/settings/AdminDataBackupRestore.vue` | 1,337 | library + create dialog + file restore + report + library settings |
| `web_app/src/pages/settings/AdminDataImport.vue` | 717 | upload → sheet → map → preview → options → result |
| `web_app/src/composables/useChunkedUpload.ts` | 143 | 8 MB chunks, retry, abort |
| `web_app/src/services/files/downloadHelpers.ts` | — | `parseFilename`, `triggerSave` (the helpers both pages re-implement) |
| `web_app/src/router/routes.ts:195–217, 521–545` | — | legacy `/data/*` redirects, admin routes |
| `tests/e2e/dora_api/test_data_router.py` | 1,118 | 57 tests (backup 13 · upload 3 · restore 3 · import 5 · templates 6 · the rest are exports/barcodes/QR → other chunks) |

**Verification greps run:** `partial` in `test_data_router.py` (**0** — partial-mode restore has no test); `meal_recipes|"meal_id"` in the restore code (`restore_shared.py:217, 223–224` stale FK entries; `restore_backup.py:194` iterates `"meal_recipes"` as a section key — **not in `SECTIONS`**; the test file's own comment at :77 says "`meals` + `meal_recipes` were removed by the meals→recipes rework"); `git log -S meal_recipes` (removed from `SECTIONS` in `99131847 Complete rework of meals`, left in the restore loop); `product_barcodes` (**only** in `AdminDataBackupRestore.vue:541` — the server key is `barcodes`, `restore_shared.py:143`); SPA `BACKUP_SECTIONS` (20 keys) vs server `SECTIONS` (29) — the SPA list lacks `cuisines, categories, dietary_tags, tools, recipe_dietary_tags, recipe_tools, recipe_steps, recipe_step_ingredients, recipe_step_tools` and misnames `barcodes`; `credentials: 'include'` across `web_app/src` (**21** sites; 12 in `AdminDataBackupRestore.vue`, 5 in `AdminDataImport.vue`, 4 in `useChunkedUpload.ts` — FU-716 confirmed, no `DataApiService` exists); `createObjectURL` (7 files; `downloadHelpers.ts` already exports `parseFilename` + `triggerSave`, and both pages define their own); `html: true` on `$q.dialog` with interpolated **sheet name** (`AdminDataImport.vue:559`); `datetime.now()` naive (`import_spreadsheet.py:523`); `from uuid import uuid4` inside functions ×3 (`:511, :615, :646`); `"zone"` literal (`:621`) vs `LOCATION_KIND_ZONE` (`stock_location.py:9`); `StockGroup` table is `id + name` only (raw insert at `:649` is complete); `scheduled backup|TRIGGER_SCHEDULED|sha256` in the ledgers (scheduled backups deferred at FU-342 close, never re-raised; `sha256` has no reader anywhere); `backup_` in the TS settings types (**none** — the page reads `/app-settings` raw); `startswith("Restore failed and was rolled back")` ×2 + `startswith("No staged upload")` ×3 (string-coded error dispatch); `locale` on `AppSetting` (`en-AU` default, :190 — the date-order authority `_coerce_to_date` ignores).

---

## A. Full Systems Test — Backup & restore + Import

### A1. Preconditions
- An admin session; a non-admin for the 403 checks; a populated install (recipes **with structured steps**, a meal plan, a shopping list with a product-only line, a custom product, a user with LLM provider settings).
- One run on SQLite, one on Postgres (restore is raw `insert()` per row inside one transaction; FK enforcement differs).
- A second, empty install (or a wiped `data/`) for the "restore onto fresh" path.
- `DORA_DATA_DIR` writable; a second path for the storage-path override; a > 500 MB JSON for the chunked path (optional).

### A2. Golden path (persona: self-host admin)
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

### A3. Edge cases
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

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (G10 restore onto empty) | ✓ (large backup, `PREVIEW_ROW_LIMIT` 500 → "… and N more") | – | ✓ (import templates) | ✓ (owner of both pages) | ✓ (users section, `created_by`) | ✓ (storage path, retention, FU-717 deploy exclude) | ✓ (same; path likely a mounted volume) |

### A5. Load-bearing conditions
- **SQLite + Postgres** (raw inserts, FK enforcement, `DateTime` round-trip through `fromisoformat`).
- **Bad network** mid-upload (chunk retry + offset resume); **1920+** (mapping grid auto-fill) and **360×640** (library rows).
- **Themes × dark** — `color="warning"` chips with `text-color="dark"` / `"white"` (C11).

### A6. Release-gate rows
1. G2–G3 **New backup with defaults succeeds** (18-R2) and the file round-trips through G8–G10 on a fresh install, including recipe steps/tools/tags (VERIFY cookbook 6/7/8 bullets).
2. G9 **Restore selection** works (18-R1).
3. G12–G16 template → import → error CSV loop.
4. Credential exclusion spot-check on a downloaded file (G5).

---

## B. Help content — Backup & restore + Import

### B1. Current help audit
- **Nothing** in `HelpPage.vue` or `app_knowledge.py` mentions backup, restore, import, templates or the library (grep). The `(?)` chips are absent on both pages.
- In-page copy is already clear (header descriptions, "Passwords are never included", the Sensitive chip, option help strings). Entries below lift it and add the parts the pages can't say (what is **not** in a backup, what restore never does, the retention/storage semantics).
- Feedback `# DATA` #6 asked for the breadcrumb fluff to go — gone (settings shell).

### B2. Help entries

#### Back up your install (admin)
- **Group:** Settings & admin
- **What it does:** Saves everything Dora knows — stock, recipes (with steps, tools and tags), lists, meal plans, saved products, barcodes — to one JSON file kept on the server in the **Backup library**. Download any of them to keep a copy elsewhere.
- **When it fires / how to trigger it:** Settings → Admin → Data → Backup & restore → **New backup**. Backups are manual; nothing runs on a schedule.
- **What controls it:** `/settings/admin/data/backup`. *Library settings* at the bottom: how many to keep (oldest drop off on the next backup) and where on the server they're stored.
- **What it costs / might get wrong:** **Passwords are never included**, nor email/push secrets — after restoring user accounts everyone needs a password reset. *System settings*, *User accounts* and *Historic offers* are off by default and flagged **Sensitive** when included. Each person's assistant (AI) provider settings are not backed up yet. A backup is a point-in-time copy of the server, not a sync.
- **Related:** Restore a backup · Import stock items from a spreadsheet.
- **Chip:** `AdminDataBackupRestore.vue:3–7` (page header) → `<HelpHint topic="Back up your install (admin)">`.
- **Source:** `backup_library.py`, `restore_shared.SECTIONS`, FU-387, FU-625.

#### Restore a backup (admin)
- **Group:** Settings & admin
- **What it does:** Brings rows from a backup **into** the current install. Rows that already exist (same id, or same name at the same place) are **skipped, never overwritten**. From a library row it restores everything in one click; from a file you first see a preview and can pick exactly which items to bring in.
- **When it fires / how to trigger it:** Library row → Restore, or *Restore from a file* → drop the JSON → tick items → **Restore selection**, or **Restore all (skip duplicates)**.
- **What controls it:** `/settings/admin/data/backup`. Admins only.
- **What it costs / might get wrong:** Restore adds, it doesn't delete — it is not a "reset to that day". Picking a recipe or list pulls in what it needs (its ingredients, steps, the products a line points at); anything whose parent is missing is skipped and listed under *warnings*. Restored user accounts have no passwords. **Reload** afterwards so every page shows the new data. Backups from a newer Dora are refused.
- **Related:** Back up your install.
- **Chip:** `AdminDataBackupRestore.vue:169–173` (Restore section title) → `<HelpHint topic="Restore a backup (admin)">`.
- **Source:** `restore_backup.py` modes + FK maps; `inspect_backup.py`.

#### Import stock items from a spreadsheet (admin)
- **Group:** Settings & admin
- **What it does:** Creates stock items in bulk from an `.xlsx` or `.csv`. Only a **name** column is required; stock level, location, group, expiry date and "is essential" are optional. Dora guesses which column is which from the headings and lets you fix the mapping before anything is written.
- **When it fires / how to trigger it:** Settings → Admin → Data → Import. **Download template** gives you a CSV with the right headings and one example row to overwrite.
- **What controls it:** `/settings/admin/data/import`. Options: skip names you already have · create missing locations · create missing groups · halt on first error (rolls everything back).
- **What it costs / might get wrong:** Levels are matched by name against *your* levels and never created ("low" finds "Low Stock"). New locations are created as top-level zones. Dates: `2027-01-31` always works; `31/01/2027` is read day-first. A row with an error doesn't stop the others unless *Halt on first error* is on; download the error rows, fix them, and import just those.
- **Related:** Back up your install · Stock levels and locations (chunk 5).
- **Chip:** `AdminDataImport.vue:3–7` (page header) → `<HelpHint topic="Import stock items from a spreadsheet (admin)">`.
- **Source:** `import_spreadsheet.py` `TARGET_FIELDS`, `COLUMN_SYNONYMS`, `_coerce_to_date`, templates (FU-343/349/350).

### B3. DoraBot corpus delta
Add to `APP_OVERVIEW` (nothing exists):
> - Backup & restore (admin): Settings → Admin → Data. Backups are manual JSON snapshots kept in a library on the server (oldest drop off past the retention count); passwords and secrets are never included. Restore adds missing rows and never overwrites or deletes; from a file the admin can pick exactly which items to bring in.
> - Import (admin): stock items from a spreadsheet; download the CSV template, fill it, upload, check the column mapping, import. Levels must already exist; locations and groups can be created on the fly.

---

## C. Senior review — Backup & restore + Import

### C1. Bugs (verified or high-confidence latent)

**18-R1 — Partial restore raises `KeyError: 'meal_recipes'` (500) before any row is touched.** class: verified · where: `restore_backup.py:194` iterates `("product_stock_item_links", "stock_item_substitutes", "meal_recipes")` and indexes `TABLE_NAME_BY_BACKUP_KEY[backup_key]`; `meal_recipes` left `SECTIONS` in `99131847 Complete rework of meals` (the test comment at `test_data_router.py:77` records the removal; FU-164 fixed the *test's* section list and called the diagnosis a misdiagnosis). The lookup sits outside the `try` (:224), so it is an unhandled exception → Flask 500 → the SPA report says "Restore failed / HTTP 500". `MODE_ALL_SKIP_DUPLICATES` never enters that branch, which is why the three restore tests pass and why `grep partial` in the test file returns 0. Also stale: `REQUIRED_FKS` entries `("meal_plan_entries", "meal_id")` (:217 — the column is `recipe_id` now, `table_mappings.py:1061`) and `("meal_recipes", …)` ×2 (:223–224) — inert but misleading. · exact change: derive the m2m list from `SECTIONS` (`[s.backup_key for s in SECTIONS if len(primary_key_columns(table)) > 1]`) instead of a literal tuple; delete the three stale `REQUIRED_FKS` entries; add `("meal_plan_entries", "recipe_id")`. · blast: S · guard: none → **D1 (must-write)** · verdict: **execute** · **urgent**.

**18-R2 — "New backup" with the default selection is rejected: the SPA names a section the server doesn't have.** class: verified · where: `AdminDataBackupRestore.vue:541` `{ key: 'product_barcodes', … defaultOn: true }` vs `restore_shared.py:143` `Section("barcodes", "Barcode", …)`; `backup.py:45–48` returns `"Unknown backup section(s): product_barcodes."` → `backup_library.py:188–189` → 400; the SPA shows "Couldn't create backup." with that caption. Pinned server-side by `test__get_backup__unknown_section__is_rejected`; nothing pins the SPA list. Every default-selection backup from the UI fails until the user unticks "Product barcodes". · exact change: see 18-R3 (remove the mirror). Interim one-liner: rename the key to `barcodes`. · blast: S · guard: D2 · verdict: **execute** · **urgent** · note: static read — **confirm in browser** per CLAUDE.md (the owner may have been creating backups via a path that unticks it).

**18-R3 — The SPA carries a hand-copied, stale mirror of the server's section catalogue (R-003 — domain list in two languages).** class: verified · where: `AdminDataBackupRestore.vue:514–545` `BACKUP_SECTIONS` (20 keys; comment "Mirrors dora_api/…SECTIONS. Keep this in sync") vs `restore_shared.SECTIONS` (29). Missing: `cuisines, categories, dietary_tags, tools, recipe_dietary_tags, recipe_tools, recipe_steps, recipe_step_ingredients, recipe_step_tools`. Consequences beyond 18-R2: (a) a UI-created backup **never includes recipe steps, tools, tags, cuisines or categories** (the server dumps only the requested keys) — so a restore of such a backup yields recipes with no steps and null cuisine/category, and the three pending VERIFY bullets ("Backup → restore round-trips `RecipeStep`…") can only pass via `curl`; (b) the restore **report** (`:1140–1151`) and the tree labels (`SECTION_LABELS`, `TOP_LEVEL_KEYS`) hide those sections' counts. · exact change: new `GET /api/data/backup/sections` returning `[{key, label, category, default_on, sensitive}]` straight from `SECTIONS` (add `sensitive: bool` to `Section` for the three optional ones so `SENSITIVE_SECTIONS`/`SENSITIVE_LABEL_BY_KEY` at `:471–475` go too); the page loads it on mount and derives `backupSelected`, groups, labels and the report from it; `TOP_LEVEL_KEYS` becomes "sections with a `duplicate_key_fn`" or an explicit `pickable: bool` on `Section`. · blast: M · guard: D2 + existing 13 backup tests · verdict: **execute**.

**18-R4 — Spreadsheet import stamps `stock_level_last_updated` with naive local time.** class: verified (R-021) · where: `import_spreadsheet.py:523` `datetime.now()`; every other writer uses `datetime.now(timezone.utc)` (e.g. `backup.py:100`). On a server whose clock isn't UTC the imported items' "level changed" timestamps are offset, and the pantry-belief / staleness rules (chunk 7) read them. · exact change: `datetime.now(timezone.utc)`. · blast: S · guard: D4 · verdict: **execute**.

**18-R5 — Confirm dialog renders the uploaded workbook's sheet name as HTML.** class: verified (self-XSS / D-rule dialog convention) · where: `AdminDataImport.vue:556–563` `$q.dialog({ message: \`Import rows from <strong>${selectedSheet.value}</strong>?…\`, html: true })` — the sheet name comes from the file. Admin-only and self-uploaded, so the exposure is low, but it is the one place in the app a file's contents reach `innerHTML`. · exact change: drop `html: true`, plain text with `"…"` around the name; same for `AdminDataBackupRestore.vue:1083–1086` (constant strings, but `html: true` for a `<br>` is the same habit — use `\n` + `style="white-space: pre-line"` or two sentences). Both become `useConfirm` calls (13-R26). · blast: S · verdict: **execute**.

**18-R6 — `delete_backup` unlinks the file before it re-fetches the row, with two repositories.** class: latent · where: `backup_library.py:349–359` — `_resolve_backup` opens one `SqlAlchemyRepository`, the route unlinks, then opens another and `by_id`s again; if the second fetch misses (race with retention) the response is 404 after the file is already gone, and the row would point at nothing. · exact change: one repository through the route; remove the row first, commit, then unlink (a dangling file is recoverable; a dangling row isn't). · blast: S · verdict: **execute**.

### C2. Redundancy / DRY (R-001, R-003)

**18-R7 — Every call on both pages is a hand-rolled `fetch`.** tracked: **FU-716** · where: 12 sites in `AdminDataBackupRestore.vue`, 5 in `AdminDataImport.vue`, 4 in `useChunkedUpload.ts` (each with `resolveBaseURL()` + `credentials: 'include'` + `csrfHeader()` + its own `describeError`). Consequences FU-716 lists (no `X-Request-Id`, no `toastCaption`, no retry policy) — plus a fourth copy of `describeError` (`AdminDataBackupRestore.vue:1034–1037`, `AdminDataImport.vue:525–528`, `useChunkedUpload.ts:140–143`). · exact change: `services/api/dataApiService.ts` (`listBackupsAsync`, `createBackupAsync`, `downloadBackupAsync` → `responseType: 'blob'`, `restoreBackupRowAsync`, `deleteBackupAsync`, `inspectBackupAsync`, `restoreBackupAsync`, `inspectSpreadsheetAsync`, `commitSpreadsheetAsync`, `listImportTemplatesAsync`, `downloadImportTemplateAsync`, `backupSectionsAsync` for 18-R3) and `uploadsApiService.ts` (`start/chunk(FormData)/finish/abort`) on `AxiosHttpClient`; `useChunkedUpload` consumes the latter; the library settings move to `AppSettingsApiService` + the `AppSettings` type (13-R16 adds `backup_*`). Error captions via `toastCaption(e)`. · blast: M · guard: 57 pytest unchanged; `vue-tsc`; manual G1–G17 · verdict: **execute** (resolves FU-716 and the `useChunkedUpload` half of FU-571's raw-client list).

**18-R8 — `triggerSave` / `parseFilename` / anchor-click download are re-implemented in both pages although `downloadHelpers.ts` exports them.** where: `AdminDataBackupRestore.vue:965–980`, `AdminDataImport.vue:338–346, 664–672` vs `services/files/downloadHelpers.ts:10, 18`. · exact change: import the helpers; the error-rows CSV builder (`:645–673`) becomes `downloadCsv(rows, header, filename)` in the same module (RFC-4180 escape lives once — `useStockOverviewExport` and friends in chunk 20 want it too). · blast: S · verdict: **execute**.

**18-R9 — `confirmAsync` (page-local Promise wrapper) + 3 inline `$q.dialog` confirms.** where: `AdminDataBackupRestore.vue:880–889` (defines its own `confirmAsync`), `:1078–1095`, `AdminDataImport.vue:556–564`. · tracked: 13-R26 (`useConfirm`, chunk 20). · verdict: **execute in chunk 20**; 18-R5's `html: true` fix rides along.

**18-R10 — `_inspect_streamed` and `_inspect_inline` duplicate ~50 lines of envelope validation + sampling + duplicate flagging.** where: `inspect_backup.py:161–215` vs `:218–270` · exact change: one `_summarise(meta, rows_for(section) -> Iterator)`; the inline path passes `iter(payload.get(k, []))`, the streamed path `_iter_section_rows`; envelope validation (`schema_version` int / newer) also appears a third time in `RestoreBackupHandler.handle:88–95` → `restore_shared.validate_envelope(doc) -> str | None`. · blast: S · guard: inspect tests (3) · verdict: **execute**.

**18-R11 — String-coded errors with `startswith` dispatch ×5.** where: `RestoreBackupHandler.handle -> RestoreSummary | str`; `backup_library.py:333–337` and `restore_backup.py:373–378` both test `startswith("Restore failed and was rolled back")`; `import_spreadsheet.py:319–322, 674–679` test `startswith("No staged upload")`; `inspect_backup.py:285–286` parses the id back **out of the message** (`err.rsplit(" ", 1)[-1].rstrip(".")`). Same class as 13-R1 / 16-R28. · exact change: `class RestoreError(Exception)` with `.kind: Literal['not_found','invalid','rolled_back']`; handlers raise, routes map kind → `not_found/bad_request/internal_server_error`. · blast: S · verdict: **execute**.

**18-R12 — Date parsing ignores the install locale.** where: `import_spreadsheet.py:109` tries `%d/%m/%Y` before `%m/%d/%Y` unconditionally; `AppSetting.locale` (`en-AU` / `en-US`, `app_setting.py:190`) is the one authority for day/month order (R-021/R-003). `03/04/2027` imports as 3 April on a US install. · exact change: read `get_or_create_app_setting(repo).locale` once in `CommitSpreadsheetHandler.handle` (it already reads the setting for `stocktake_new_items_opt_in`) and order the two slash formats by it; mention the order in the template comment row. · blast: S · guard: D5 · verdict: **execute** (small; the help entry above states the day-first default until then).

**18-R13 — `.settings-divider` / `.settings-actions` / `.settings-page` scoped CSS copied into both pages.** tracked: 13-R9 (settings shell). · verdict: **execute under 13-R9**.

### C3. Dead code / unused fields / unread endpoints

**18-R14 — `Backup.sha256`, `Backup.status`, `STATUS_FAILED` have no reader.** evidence: `sha256` is written (`backup_library.py:207`) and returned in the DTO; grep across `dora_api` + `web_app/src` finds no comparison (download streams the file, restore re-reads it, the SPA type declares it and never renders it); `status` is always `STATUS_READY`; `STATUS_FAILED` is never assigned. The entity docstring promises corruption flagging. · exact change: either verify on download/restore (`_sha256_of(path) != row.sha256` → 409 "Backup file changed on disk") — 6 lines, and it gives the column its job — or drop the promise from the docstring. Recommend the check. `trigger_kind` stays (documented forward-looking column). · blast: S · guard: D3 · verdict: **execute** (the check).

**18-R15 — Multipart fallback in `inspect_backup`.** where: `inspect_backup.py:53–80, 103–111` (`_stream_upload_to_tempfile`, `DIRECT_UPLOAD_MAX_BYTES`, `CHUNK_BYTES`) — docstring: "kept as a fallback for curl-style ad-hoc inspection"; no SPA caller, no test (the three inspect tests use inline JSON or `upload_id`). · verdict: **waive** (documented operator affordance; 30 lines) — or delete if the owner wants the three-shape body gone. Record as 18-D3.

**18-R16 — `legacy /data/* redirects`** (`routes.ts:195–217`) — six redirect rows for bookmarks from the retired Data menu; `data/export` comment explains itself. · verdict: **waive** (cheap, intentional).

**18-R17 — `useChunkedUpload.lastUploadId`, `inFlight`** — returned but unused by either page (both track their own `uploadId` and `uploading`). · exact change: drop from the return (or have the pages use them — one owner). · verdict: **execute** (with 18-R7).

### C4. Componentisation opportunities (R-001)

**18-R18 — `AdminDataBackupRestore.vue` (1,337 lines) is four surfaces in one file.** · exact change: `BackupLibraryList.vue` (rows + 3 actions; emits), `BackupCreateDialog.vue` (section picker + sensitive banner; takes the catalogue from 18-R3), `BackupRestorePanel.vue` (drop + preview tree + actions), `RestoreReportDialog.vue`; the page keeps the API calls and the library-settings section. · blast: M · guard: manual G1–G11 · verdict: **execute**.

**18-R19 — `AdminDataImport.vue` (717)** — the result dialog (`:218–280`, virtual list + chips + error CSV) is a self-contained `ImportResultDialog.vue`. · blast: S · verdict: **execute**.

### C5. Placement / layering (R-003, R-005)

**18-R20 — Raw `db.metadata.tables` / `db.session` throughout the data feature.** where: `backup.py:68–69`, `backup_library.py:268–273`, `inspect_backup.py:147–148`, `restore_backup.py` (throughout — generic table walk), `import_spreadsheet.py:510, 616, 647`. The generic dump/restore **is** the legitimate R-005 carve-out (it iterates `SECTIONS` by table name on purpose); the import's three raw inserts are not — `create_stock_item` / `create_stock_group` / `create_stock_location` handlers exist and own defaults (`stocktake_new_items_opt_in` is already copied here because of it, `:395–399`). · exact change: comment the carve-out once at the top of `restore_shared.py` (`# R-005 carve-out: …`) for backup/inspect/restore; route the import's inserts through the three create handlers (or their shared "new entity" factories) so a future default isn't missed. `backup_library.list_backups:268` username lookup → `repository.get(User).all(in_)`. · blast: S–M · verdict: **execute** (import) / **explain** (backup). Also add to **FU-923**'s list.

**18-R21 — `list_backups` hand-rolls pagination** (`backup_library.py:246–262`: parses `page`/`size`, sorts the whole table in Python, slices) while every other list uses `parse_query_options` + `repository.paginate` + `paginated` (e.g. `/stores`). · exact change: `Backup` gets a `_FIELD_MAP` + `paginate(options, _row_to_dto…)` ordered by `created_at desc`; the SPA passes `?limit=200`. `_enforce_retention:151` likewise loads all rows — fine for ≤100 but use `order_by/offset` if `paginate` supports it. · blast: S · verdict: **execute**.

**18-R22 — `from uuid import uuid4` inside three functions, `from flask import Response` inside one, `DORA_CONFIG` import inside `upload_dir()`.** where: `import_spreadsheet.py:511, 615, 646, 927`; `uploads.py:58`. · exact change: module-level imports (no cycle — `configuration_manager` is imported at module level by `backup_library.py`). · verdict: **execute**.

### C6. Naming & idiom

**18-R23 — `"zone"` literal** (`import_spreadsheet.py:621`) → `LOCATION_KIND_ZONE` (`stock_location.py:9`). · **execute**.
**18-R24 — `existing_item_names: dict[str, UUID]` later assigned `True`** (`:529`) — type lie; use a `set[str]` of names (the ids are never read). · **execute**.
**18-R25 — `_Logger = logging.getLogger(__name__)` inside every route** (`backup_library.py:181, 306, 344`, `inspect_backup.py:275`, `restore_backup.py:363`, `uploads.py:100, 134, 206, 231`) vs the module-level `_Logger` convention in the ingestion package. · **execute** (mechanical).
**18-R26 — `ok` shadows `api_response.ok`** — `AdminDataBackupRestore.vue` is fine, but `backup_library.py` imports `ok` and the SPA-side word is unrelated; no issue. (Checked; no change.)
**18-R27 — Copy: "Restore all (skip duplicates)" vs "Restore selection" vs library "Restore this backup"** — three verbs for two behaviours; the dialog copy explains each. **waive** (owner-happy).

### C7. Efficiency

**18-R28 — Restore loads every row of every section's table into Python before applying** (`restore_backup.py:116–132`), including `ProductHistoricOffer` (potentially the largest table) even when the backup carries none; inspect does the same per section with a duplicate key fn (`_build_existing_duplicate_keys`). · exact change: skip tables whose backup section is empty; for PK presence use `select(pk_cols)` not `select(table)`. · blast: S · verdict: **execute** (cheap) — the full-table duplicate-key scan stays (it is the contract).
**18-R29 — Import hydrates every `StockItem`/`StockGroup`/`StockLocation` entity to build name maps** (`import_spreadsheet.py:418–431`). · exact change: `select(table.c.id, table.c.name)` via the repository's column query (or accept — 5k rows is fine). · verdict: **waive** (hobby scale; note).
**18-R30 — `_backups_dir()` → `get_or_create_app_setting` ×2 per create** (`:125, :149`). Memoised on `g` → **waive**.

### C8. Design-level findings — out of Stage-2 scope
- **18-D1 — Scheduled backups.** `trigger_kind` was added for them (FU-342) and FU-405 parks ops for Phase 4; no FU tracks the feature itself. Recommend a tiny APScheduler job ("nightly if anything changed") as a Phase-3 nicety; not now.
- **18-D2 — Feedback `# DATA` #2 "export to multiple formats (json, csv…)".** FU-359 left it; backups are JSON, per-surface CSV exists where it makes sense (stock overview, recipes). Recommend **won't-do** for a generic multi-format export; record the decision.
- **18-D3 — Keep the multipart `curl` fallback on `/backup/inspect`?** (18-R15). Recommend keep.
- **18-D4 — Restore semantics are "add, never overwrite, never delete".** Correct per the docstring and the help entry; a true "replace install" mode (wipe + restore) is a separate feature — not asked for.
- **18-D5 — `UserLlmProvider` backup section** (FU-625) — small, additive, with `api_key_encrypted` excluded; recommend bundling with 18-R3's catalogue work since `Section` gains fields anyway.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| Chunked resumable upload (`uploads.py` + `useChunkedUpload`) | 380 lines both sides | tus / flask-tus, Uppy | **keep** | — | Admin-only, two callers, 8 MB chunks with resume-by-offset; a protocol library adds a client bundle and a server dep for no new capability. |
| Streaming JSON inspect | `ijson` | — | already library | — | — |
| Spreadsheet parsing | `openpyxl` + stdlib `csv` | pandas | **keep** | — | pandas would be the heaviest dep in the app for one importer. |
| Restore FK resolution | hand-rolled maps in `restore_shared.py` | — | **keep** | — | Reflection-driven (`_resolve_fk_target` reads SQLAlchemy FKs); the hand maps are the *policy* (hard/soft/required), not the plumbing. Fix the stale entries (18-R1). |
| `_coerce_to_date` | 4 strptime formats | `dateutil.parser` | **keep + locale order** (18-R12) | — | `dateutil` guesses; the install knows. |
| Client CSV escaping | 15 lines | papaparse | **keep, centralise** (18-R8) | — | — |

### C10. Standards drift (R-0NN)
- **R-003** — section catalogue in two languages (18-R3); `describeError` ×3, download helpers ×2, `.settings-*` CSS ×2 (18-R7/R8/R13); `"zone"` literal (18-R23); import re-implements create defaults (18-R20).
- **R-005** — raw table access: carve-out for generic dump/restore (explain in place); import inserts (fix); username lookup (fix) — 18-R20.
- **R-021** — naive `datetime.now()` (18-R4); locale-blind date order (18-R12).
- **R-001** — 1,337-line page (18-R18).
- **R-045 / FU-716** — raw `fetch` + hand-built URLs (18-R7).
- **R-035 / D-rules** — bare icon strings `'warning'` (`AdminDataBackupRestore.vue:54, 114`, `AdminDataImport.vue:124`), `'check_circle'`/`'error'` (`:269`, `:222`) → `ICONS`; `text-color="dark"` (`:53`) and `text-color="white"` (`:228`, `AdminDataImport.vue:249`) → FU-671 sweep; `html: true` dialogs (18-R5); inline `style="max-width: 120px"` / `"min-width: 280px"` (`:345, :358`) → classes.
- **Security** — admin gate on all 19 `DATA_ROUTER` routes ✓ (pinned); upload ids validated / uuid converter ✓; secrets excluded ✓; 18-R5 is the one `innerHTML` sink.

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- `color="warning"` chips with `text-color="dark"` (Sensitive) vs `"white"` (duplicate) on the same page — one is wrong on one theme; both should be the `--text-on-warning` token (FU-674 family).
- `.backup-row:hover` uses `color-mix(var(--brand-primary) 4%, …)` — a pattern worth a `--surface-hover` token (chunk 20 theme list).

---

## D. Test plan — Backup & restore + Import

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

## E. Proposed follow-ups (orchestrator allocates ids)

- **urgent · bug** — partial restore 500s on `KeyError: 'meal_recipes'` (18-R1); stale `meal_*` FK entries. Resolution: **now** (Stage 2, chunk 18) + D1/D6.
- **urgent · bug** — UI "New backup" default selection is rejected (`product_barcodes`) and UI backups omit recipe steps/tools/tags/vocab (18-R2/R3). Resolution: **now**; **confirm in browser** that the default create fails today before closing.
- **bug** — import stamps naive local time (18-R4). Resolution: **now**.
- **finding · security-hygiene** — sheet name rendered as HTML in a confirm (18-R5). Resolution: **now** (with 13-R26).
- **finding** — `Backup.sha256` never verified; `status` always `ready` (18-R14). Resolution: **now** (6-line check) or docstring fix.
- **resolve FU-716** when 18-R7 lands; append `useChunkedUpload` to FU-571's cleared list.
- **append to FU-923** — raw-table sites in `import_spreadsheet.py` (fix) and the documented carve-out for `backup/inspect/restore` (explain).
- **finding** — date order ignores `AppSetting.locale` (18-R12). Resolution: **now** (small) — or fold into chunk 20's locale pass (FU-043).
- **decision** — 18-D2 multi-format export → recommend won't-do; 18-D1 scheduled backups → Phase 3 nicety; 18-D5 bundle FU-625 with 18-R3.
- **ride-along** — `SettingsFileDrop.vue` (251 lines, this chunk's only unread file) gets a read in Stage 2 when 18-R18 splits the page.
- **VERIFY** — after 18-R3, the three "Backup → restore round-trips …" bullets (Cookbook chunks 6/7/8) can be walked once with a UI-created backup (today they cannot pass via the UI).

---

## F. Feedback coverage — `# DATA` (10 bullets, lines 464–476)

| # | Bullet | Status | Where |
|---|---|---|---|
| 1 | Not in the main menu; under Settings as "My Data" | ✅ shipped | `/settings/admin/data/*` + legacy redirects (`routes.ts:195–217`); named "Data" under Admin (owner-approved shell). |
| 2 | Export to multiple formats (json, csv, …) | 🔴 **decision** (18-D2) | FU-359 left it; recommend won't-do for a generic exporter — backups are JSON, per-surface CSV exists where useful. |
| 3 | Ugly formatting / misaligned checkboxes | ✅ shipped | FU-359 redesign (`SettingsSection`/`SettingsRow`/`SettingsFileDrop`). |
| 4 | Heading type; optional section collapsed | ✅ shipped | Create dialog groups (Core open by default, Optional collapsed) — the owner's "does it need to be collapsed" is answered by moving the picker into a dialog. |
| 5 | Use horizontal space; cards with checkboxes | ✅ shipped | library rows as cards; mapping grid auto-fill. |
| 6 | Breadcrumb + subtitle fluff | ✅ shipped | settings shell has neither. |
| 7 | Template sheets generated from the live schema | ✅ shipped | FU-343/348/349/350 — CSV from `TARGET_FIELDS`, two-way symmetry asserted at boot. |
| 8 | Export & print tab unnecessary | ✅ shipped | tab removed; print lives in-context (`routes.ts:212–217`). |
| 9 | Scan tab under QR codes pointless here | ✅ shipped | FU-340; `data/barcodes` → `kitchen-setup/qr-labels`. |
| 10 | Rename "barcodes and QR" → "QR codes" | ✅ shipped | `/settings/kitchen-setup/qr-labels` (chunk 6). |

### Register summary
- **FST rows:** 17 golden + 15 edges · **Help entries:** 3 new + DoraBot 2 lines (none existed) · **Review findings:** 30 (execute 22 / FU 1 / waive 5 / explain 1 / decision 1) + 5 design notes · **Tests:** 7 (must-write 3) · **Bugs:** 6 (18-R1, R2, R3, R4, R5, R6)
- **One line:** the backup/restore engine is careful (streamed inspect, FK pull-in, credential exclusion, chunked uploads) but two things never had a test and are broken from the UI — *Restore selection* 500s on a section key the meals rework removed, and *New backup* with defaults is refused because the page carries its own stale copy of the section catalogue that also silently drops recipe steps and vocab from every UI backup; the pages bypass the API layer entirely (FU-716) and re-implement helpers the codebase already has.
