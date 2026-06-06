# DiscountDora — Prompt Plan

A complete, paste-ready set of prompts for finishing DiscountDora as a stable, componentised, feature-rich, fully-functional app.

Each prompt is self-contained: a fresh Claude session can run it cold. Every prompt starts with a **READ FIRST** step so it survives stale-code drift.

---

## How to use

- Pick a prompt, paste it into a Claude Code session, let it run.
- Don't run prompts in parallel with another session working on overlapping areas.
- After each prompt lands, do a quick `git log` / CHANGELOG read before the next one so the next prompt reflects reality.
- When a prompt references another (e.g. "from P0", "depends on F3"), run the dependency first.

---

## Recommended order

1. **Foundations primitives** — F6 → F4 → F2
2. **Hub screens & connective tissue** — P0 → P1 → P2 → P5 → P4 → P3
3. **Feature-rich screens** — P6 → P7 → P8 → P9 → P10 → P11 → P12 → P13 → P14
4. **Resilience & polish** — F3 → F1 → F5 → S5 → S1
5. **Greenfield Data Management** — N1 → N2 → N3 → N4 → N5
6. **Backend hardening & auth** — I1+I2 → A1 → M1
7. **Heavy features** — X1 → X5
8. **Other greenfield** — N6 → N7 → N8 → N9
9. **Design system & docs** — DS1 → DS2 → DS5 → DS4 → DS3 → Doc1 → Doc2 → Doc3 → Doc4
10. **DevOps** — D2 → D3 → D1 → D4 → D5
11. **Testing** — T1

---

## Cross-cutting rules

When running each screen prompt, remind the executing agent of these:

- **Every entity reference is a chip** (`<StockItemChip>`, `<ProductChip>`, `<RecipeCard>`) — never bare text. Chips navigate or open a side panel.
- **Every action goes through the composables in P0** — no screen reimplements add-to-list, restock, etc.
- **Every screen has at least one "feed me into another screen" action** — generate a list, plan a meal, find a recipe, jump to location.
- **Every list/grid has an empty state that points to another screen** that would populate it.
- **Cross-feature counts are live, not stored** (e.g. "on 2 lists", "used in 5 recipes", "3 substitutes") — they come from queries, so they never go stale.

---

# Tier A — Connective tissue (run before screens)

## P0 — Cross-feature primitives

```
Build the cross-feature primitives that every screen will lean on:
(a) `useStockItemActions` composable — add-to-list, mark-restocked, push-expiry,
    open-detail, find-substitutes, see-recipes-using.
(b) `useShoppingListActions` — add-items, set-primary, finish-shopping.
(c) `<StockItemChip>` and `<ProductChip>` displaying picture, name, level badge,
    on-list indicator, alert dot — clickable to detail, with overflow menu wired
    to those composables.
(d) A global `<QuickAddSheet>` invoked from anywhere to push items onto a
    shopping list with merchant offer picker.

These are the LEGO bricks every screen below uses.
```

---

# Tier B — Screen prompts (feature-rich, interconnected)

## P1 — Stock Overview (the hub)

```
Make StockOverview the command center. Each row uses <StockItemChip> and shows:
picture, name, level badge, location chip (click → filter to that location),
'on N lists' chip (click → which lists), expiry/alert dot (click → push/clear
expiry inline), 'used in N recipes' icon (hover → recipe list, click → recipe).
Cart button quick-adds to primary list via useStockItemActions. Selecting items
reveals a bulk action bar (add to list, move location, mark restocked, set
substitute). Splitter detail panel shows the full StockItemDetail without
leaving the page. Filter chips: level, location, essentials, on-list, has-alert,
used-in-recipe. Empty state suggests 'Create from a recipe's ingredients' and
'Import from a shopping list'.
```

## P2 — Stock Item Detail

```
Build StockItemDetailPage as a hub of relationships. Tabs or sections:
Overview (level, location breadcrumb, expiry, opened-on), Linked Products
(cards with current deal, price trend sparkline, preferred-merchant toggle,
'add cheapest to list' button), Recipes Using This (<RecipeCard> grid, greyed
if other ingredients are also missing), Substitutes (<StockItemChip> list,
'swap into shopping list' action for each), On Shopping Lists (live), History
(level changes, last stocktake). Every related entity is a chip that navigates
or opens a side panel. Toolbar actions: mark open, restock, set expiry, find
deals, add to list.
```

## P3 — Locations Overview / Detail

```
Wire Locations into the rest of the app. Heatmap nodes show attention rolled
up from descendants (expired count, low-stock, flagged). Click a node → side
panel listing the <StockItemChip>s in it, with quick-actions (move, restock,
add-to-list, view-recipes-using). Drag from StockOverview onto a location node
moves the item. Add 'Items needing attention here' shortcut that opens those
items in StockOverview pre-filtered. Each node has 'Generate shopping list
for this area' (everything low/out in this zone → new list).
```

## P4 — Shopping Lists Overview

```
ShoppingListsOverview shows active vs archived lists with live counts (items
remaining, est. total). Primary list is visually distinct and shows quick
stats. Each card has actions: open, set primary, copy unticked to new list,
copy archived → new list, archive, delete. Toolbar: 'Auto-generate from
low/out stock', 'Generate from a recipe', 'Generate from a meal plan',
'Generate from flagged items'. Empty state recommends auto-generate based on
current low-stock count from StockOverview data.
```

## P5 — Shopping List Detail

```
ShoppingListDetail groups items by stock location (matching shopper's route
through the store), then alphabetical. Each line: <StockItemChip>, quantity
stepper, merchant offer picker (showing current deal, savings vs avg,
preferred merchant first), tick to mark picked, swipe/menu → 'swap with
substitute', 'move to another list', 'remove'. Live totals: remaining, picked,
full estimated total, savings vs RRP. Toolbar: refresh deals, review mode
(ticked only with auto-stock-bump preview), finish shopping (archives + bumps
levels + offers 'add unticked to new list'). 'Add item' opens <QuickAddSheet>
with frequently-added suggestions and search across all stock items.
```

## P6 — Recipes Overview

```
RecipesOverview shows <RecipeCard> grid grouped by collection. Each card
displays a 'cookable now' badge based on real-time stock check, with a
'missing N ingredients' chip if not — clicking the chip opens a 'Add missing
to shopping list' dialog with the <QuickAddSheet>. Card actions: cook
(→ CookMode), edit, duplicate, add to meal plan, add all ingredients to list.
Filters: cookable now, missing ≤ N ingredients, collection, by tag, by stock
item used. Comparison mode lets you select 2-3 and compare side by side.
```

## P7 — Recipe Detail / Edit

```
Recipe edit view: each ingredient row is a <StockItemChip> autocomplete bound
to real stock items (creating one inline if it doesn't exist). Show live
current level next to each, with a chip showing 'low'/'out' state and a
per-row 'add to list' button. Sidebar: 'Add all missing to shopping list',
'Start cook mode', 'Find substitutes for missing ingredients' (uses the
substitutes graph from P2). Import-from-URL fills the same structure.
Nutrition optional.
```

## P8 — Cook Mode

```
RecipeCookMode is fullscreen, step-by-step. Ingredients pane shows
<StockItemChip> rows that auto-mark 'used' when you tick the step. On finish:
prompt 'Update stock levels?' (decrement used items), 'Log this as a meal
eaten' (→ meals), 'Anything ran out? Add to shopping list' (auto-pre-selects
items now at low/out). Timer per step.
```

## P9 — Meal Plans

```
MealPlansOverview is a weekly calendar grid. Drop a recipe onto a day to plan
it. Sidebar rolls up the week's combined ingredient demand vs current stock
and shows 'You'll need to buy: X' with a one-click 'Generate shopping list
for this week'. Click a planned meal → recipe detail. Mark cooked → trigger
CookMode flow from P8. 'Suggest meals I can cook now' button uses the same
cookable-now check from P6.
```

## P10 — Product Search

```
ProductSearch results are <ProductCard>s with: current deal %off badge
(visually scaled by discount), unit price, merchant logo, price history
sparkline. Each card: save (favourite), link to existing stock item
(autocomplete picker), 'quick-add' (creates stock item + links + adds to
shopping list in one move), 'add to comparison'. Filters: price range,
unit-price range, weight range, half-price-or-better toggle, merchant,
in-stock. Sort: relevancy, unit price, name, % off. Show merchant connection
status badges in the toolbar.
```

## P11 — My Products

```
MyProducts shows saved <ProductCard>s with the stock item each is linked to
(chip → navigate). Filters: by linked stock item, on-deal-now, by merchant.
Bulk actions: add all on-deal to a list, unlink, mark inactive. 'Stock items
without products' shortcut lists candidates needing linking.
```

## P12 — Dashboard

```
Dashboard is the morning glance. Cards: 'Needs your attention' (pulls from
Alerts P4 data — <StockItemChip> rows with inline actions), 'Cookable
tonight' (top 3 recipes from P6 logic), 'Best deals on your saved products'
(top % off from P11), 'Primary shopping list' (live totals, jump-to button),
'This week's meal plan' (mini calendar from P9). Every chip and number is a
deep link into the relevant screen.
```

## P13 — Alerts Panel

```
Already exists — round it out: every alert row is a <StockItemChip> with the
same inline actions as everywhere else, plus 'view in context' (jumps to
StockOverview filtered to this alert type) and 'snooze 7 days'. Group by
severity. Bottom action: 'Add all low/out items to primary shopping list'
wired through useShoppingListActions.
```

## P14 — Dora Assistant

```
Make Dora context-aware. On any screen, the help panel shows actions relevant
to *that* screen + current selection. From StockItemDetail: 'find cheaper
alternatives', 'add to list', 'find substitutes'. From a Recipe: 'what's
missing?', 'plan this for a day', 'add missing to list'. Dora's quick-actions
invoke the same composables (P0) so behaviour stays consistent.
```

---

# Tier C — Greenfield: Data Management

## N1 — Data Management page shell

```
Build a new Data Management section for DiscountDora. This is a greenfield area —
no existing pages cover it.

READ FIRST (do not skip):
- web_app/src/pages/SettingsShell.vue and web_app/src/pages/settings/*.vue to match
  the existing tab/shell pattern, naming, and Quasar component usage.
- web_app/src/router/ to learn how routes are registered.
- web_app/src/layouts/ to learn how the nav menu is structured.
- CHANGELOG.md to see what version we're on and match the writing style for the
  entry you'll add.
- The taskboard memory: this is pre-release, destructive schema changes are fine.

WHAT TO BUILD:
1. A new top-level page DataManagement.vue at web_app/src/pages/, routed at /data.
   It uses the same shell pattern as SettingsShell — left rail (or top tabs on
   mobile) listing sections, right pane for the active section's content.
2. Four sub-sections, each as its own .vue under web_app/src/pages/data/:
   - BackupRestore.vue
   - DataImport.vue
   - ExportPrint.vue
   - BarcodesQR.vue
   For now, each sub-page renders a placeholder "Coming soon" card with the
   section title, a one-sentence description, and an icon. Subsequent prompts
   (N2-N5) will fill these in.
3. Add a nav entry "Data" in the main nav menu, with an appropriate Quasar icon
   (database / archive-style).
4. Add breadcrumbs: Data > <section>.
5. Add a CHANGELOG entry under [Unreleased]: "Added: Data Management shell
   (backup/restore, import, export & print, barcodes — sections to follow)."

OUT OF SCOPE:
- Any actual backup, import, export, or barcode logic. Just the shell.
- Backend changes. Frontend-only.

DEFINITION OF DONE:
- /data loads, shows the four sections, each navigable.
- Nav menu shows "Data".
- TypeScript and lint pass.
- No regression in existing pages.

If any of this brief conflicts with what already exists in the repo, stop and
report before writing code.
```

## N2 — Backup & Restore

```
Implement the Backup & Restore section of Data Management for DiscountDora.

READ FIRST:
- web_app/src/pages/data/BackupRestore.vue (the placeholder from N1).
- dora_api/ models, especially the entities for stock items, stock groups,
  stock locations, shopping lists, recipes, meals, meal plans, saved products,
  users.
- dora_api/ existing route conventions (look at one of the larger feature routers
  to copy patterns: auth, error handling, request schemas).
- Memory: pre-release, "nuke the table" is acceptable, no backward-compat shims.

BACKEND (dora_api):
1. New endpoint GET /api/data/backup
   - Auth required.
   - Serialises the current user's data (and global system data they can see) to
     a single JSON document with this shape:
       {
         "schema_version": 1,
         "exported_at": "<iso>",
         "exported_by": "<username>",
         "stock_groups": [...],
         "stock_locations": [...],   // include parent_id / kind / sequence
         "stock_items": [...],       // include level, expiry, location_id, etc.
         "saved_products": [...],
         "product_stock_item_links": [...],
         "shopping_lists": [...],
         "shopping_list_items": [...],
         "recipes": [...],
         "recipe_ingredients": [...],
         "meals": [...],
         "meal_plans": [...]
       }
   - Each entity carries its UUID/PK so cross-refs survive round-trip.
   - Returns as application/json with a Content-Disposition attachment
     filename "dora-backup-<iso-date>.json".

2. New endpoint POST /api/data/backup/inspect
   - Accepts an uploaded backup file (multipart).
   - Validates schema_version (reject if newer than supported).
   - Returns a structured preview:
       { "entity_counts": {...}, "duplicates": { "stock_items": [<names>], ... } }
   - "Duplicates" = entities whose unique field (name for items/lists/recipes,
     name+parent for locations) already exists for the current user.

3. New endpoint POST /api/data/backup/restore
   - Body: { "backup": <full backup json>, "selection": { "stock_items": [<ids>], ... },
              "mode": "all_skip_duplicates" | "partial" }
   - "all_skip_duplicates": import everything except items that collide on the
     uniqueness key.
   - "partial": import only the IDs in selection. Resolve FKs — if a stock item
     references a location not being imported AND not present in current DB,
     either (a) also pull that location in transparently OR (b) drop the FK to
     null and surface a warning. Pick (a) for locations and groups, (b) for
     softer links.
   - Wrap the whole restore in a transaction. On failure, roll back and return
     a structured error.
   - Return summary { "created": {entity: count, ...}, "skipped": {...},
     "warnings": [...] }.

FRONTEND (BackupRestore.vue):
1. Two cards side by side (stacked on mobile):
   - "Create Backup": single button "Download backup". Triggers the backup
     endpoint, saves the file via browser download. Show last-backup-at if we
     persist it in a user pref (optional; if no backend support, skip).
   - "Restore from Backup": file picker accepting .json.

2. On file selection:
   - POST to /inspect. While loading, show a spinner.
   - Render a preview pane: tree view, one branch per entity type, expanded
     by default for the first few. Each leaf is a checkbox + entity name +
     a "duplicate" chip if the inspect endpoint flagged it. Duplicate rows are
     checkbox-disabled.
   - Top of the tree: select-all / deselect-all, and a counter
     "X of Y items selected, Z duplicates skipped".
   - Two action buttons:
       - "Restore selection" (partial mode)
       - "Restore all (skip duplicates)" (all_skip_duplicates mode)
   - Confirm dialog before commit, listing what'll change.

3. On successful restore: toast with the summary, refresh any relevant Pinia
   stores so the UI reflects the new data without a page reload.

4. On failure: error notification with the server's structured error message.
   The page should remain usable (don't blank it out).

UX DETAILS:
- File size: cap at 50 MB on the client, surface a clean error if exceeded.
- Empty backup (every selection unchecked, no duplicates): disable the restore
  button.
- Add a small explainer at the top: "Backups capture your stock, lists, recipes,
  meals, and saved products. They don't include cached merchant data or your
  password." Keep to one sentence.

DEFINITION OF DONE:
- Round-trip works: export, wipe a dev DB, restore, data matches.
- Partial restore works: pick a subset, only those land.
- Duplicate detection works: re-importing the same file changes nothing.
- CHANGELOG entry under [Unreleased].
- TypeScript and Python tests pass; add at least one backend test for the
  round-trip endpoint and one for duplicate skipping.

STOP AND ASK before writing code if any entity in the spec above isn't in the
current schema, or if the patterns in existing routers diverge from what's
described.
```

## N3 — Import (Grocy + spreadsheet)

```
Implement the Import section of Data Management for DiscountDora.

READ FIRST:
- web_app/src/pages/data/DataImport.vue (placeholder from N1).
- The backup/restore implementation from N2 — reuse its entity-write helpers.
- A sample Grocy export if one is checked into the repo; otherwise consult
  https://demo.grocy.info docs for the userentities / products / stock JSON
  shapes. Pick the smallest viable subset: products, stock entries, locations.
- The user's existing stock_locations hierarchy code in dora_api.

BACKEND:
1. POST /api/data/import/grocy/inspect — accepts a Grocy JSON export
   (multipart). Returns a mapping preview:
     {
       "detected": { "products": N, "stock_entries": N, "locations": N },
       "field_mapping": { "grocy.products.name" -> "stock_items.name", ... },
       "warnings": [...]
     }
   The mapping is fixed/opinionated — no user-config needed for Grocy.

2. POST /api/data/import/grocy/commit — actually performs the import using
   the same transactional pattern as N2's restore. Returns the same summary
   shape.

3. POST /api/data/import/spreadsheet/inspect — accepts xlsx or csv. Returns:
     { "sheets": [<name>...], "preview_rows": {<sheet>: [first 5 rows]},
       "detected_columns": [...] }
   Use openpyxl for xlsx; csv module for csv.

4. POST /api/data/import/spreadsheet/commit — body:
     { "file_token": <id from inspect>, "sheet": <name>,
       "column_map": { "name": "Item", "level": "Status", "location": "Where",
                       "group": "Group", "expiry": "Best before",
                       "is_essential": "Essential?" },
       "options": { "skip_duplicates": bool, "create_missing_locations": bool,
                    "create_missing_groups": bool } }
   - Validate row-by-row. Collect errors with row numbers. If errors and the
     user picked "halt on error", abort the whole thing. Otherwise import
     valid rows and return a per-row report.
   - Stash the uploaded file in a short-lived server cache keyed by file_token
     so inspect → commit doesn't require re-upload.

FRONTEND (DataImport.vue):
1. Two tabs: "Grocy" and "Spreadsheet".

2. Grocy tab:
   - File picker. On select, call /grocy/inspect, show a summary card with
     entity counts and warnings.
   - Single button "Import". On click, confirm dialog showing what will be
     created, then call /grocy/commit. Show summary toast.

3. Spreadsheet tab:
   - File picker (.xlsx, .csv).
   - On select: call /spreadsheet/inspect, then show:
       (a) Sheet selector (radio or q-select) if multiple sheets.
       (b) Column mapping UI: for each of our target fields (name [required],
           level, location, group, expiry, is_essential), a q-select listing
           the sheet's columns. Auto-pick obvious matches by name similarity.
       (c) Live preview table: 5 rows showing how the mapping resolves.
       (d) Options: "Create missing locations on the fly", "Create missing
           groups", "Halt on first error" toggles.
   - "Import" button → /spreadsheet/commit → result modal showing per-row
     status (success / skipped-duplicate / error with reason). Allow user to
     download the error rows as a CSV for fixing offline.

UX DETAILS:
- Show clearly that "name" is required and the mapping is invalid without it.
- If level values don't match our enum, surface that as a row-level error with
  the offending value and the valid options.
- Don't import anything if the user closes the dialog before confirming.

DEFINITION OF DONE:
- A real Grocy export round-trips into Dora.
- A 50-row spreadsheet imports cleanly with sensible auto-mapping.
- Errors are itemised, not just "import failed".
- CHANGELOG entry under [Unreleased].
- One backend test per importer happy path, one for the error-row path.

STOP AND ASK before writing code if the Grocy field shapes are unclear or if
N2's helpers aren't structured for reuse.
```

## N4 — Export & Print

```
Implement the Export & Print section of Data Management for DiscountDora, plus
hook it into ShoppingListDetail.

READ FIRST:
- web_app/src/pages/data/ExportPrint.vue (placeholder from N1).
- web_app/src/pages/ShoppingListDetail.vue — you'll add a toolbar action.
- dora_api/ shopping list models + the location hierarchy code (lists group by
  location).
- Whatever PDF generation library, if any, is already in requirements.txt. If
  none, use weasyprint (HTML→PDF, clean output, good with CSS).

BACKEND:
1. GET /api/shopping-lists/<id>/export?format=csv
   - Auth + ownership check.
   - CSV columns: location, item, quantity, merchant, unit_price, total,
     picked_up (bool), notes.
   - Grouped by location, sorted alphabetical within location.
   - Returns text/csv with Content-Disposition.

2. GET /api/shopping-lists/<id>/export?format=pdf
   - Same data, rendered via a Jinja template + weasyprint.
   - Layout: title (list name + date), small totals strip (remaining count,
     estimated total), then sections per location. Each row: large checkbox,
     item name (bold), qty, merchant, est. price right-aligned. Generous
     whitespace, big tap-friendly checkboxes, no Dora branding chrome (this
     is going on a fridge).
   - Footer: page number + generated-at timestamp.

3. GET /api/shopping-lists/<id>/print-view (HTML)
   - Same content as the PDF, returned as HTML with a print stylesheet
     (@media print rules). Used for in-browser printing.

FRONTEND:
1. ExportPrint.vue:
   - List of the user's shopping lists (active first, then archived). Each row:
     name, item count, status chip, and three buttons: "Download CSV",
     "Download PDF", "Print". Print opens /print-view in a new tab and triggers
     window.print().
   - Filter chips: Active / Archived / All.
   - Empty state with a link to ShoppingListsOverview.

2. ShoppingListDetail.vue:
   - Add a toolbar menu (overflow / "more" button) with: Export as CSV,
     Export as PDF, Print. Same endpoints as above. Don't duplicate logic —
     extract a `useShoppingListExport(listId)` composable in
     web_app/src/composables/ and use it from both places.

UX DETAILS:
- PDF and CSV downloads should preserve the list name in the filename
  (slugified): "shopping-list-weekly-shop-2026-05-21.pdf".
- Print stylesheet must hide the app's nav/header/footer chrome.

DEFINITION OF DONE:
- Both formats download and open correctly on macOS, Windows, and a phone.
- Print view renders cleanly with no nav chrome.
- CHANGELOG entry under [Unreleased].
- One backend test per format that asserts the response content-type and a
  representative row of content.

STOP AND ASK before writing code if weasyprint isn't already a dependency and
adding it would be a big change.
```

## N5 — Barcodes & QR

```
Implement the Barcodes & QR section of Data Management for DiscountDora, plus
hooks into StockItemDetailPage and StockOverview.

READ FIRST:
- web_app/src/pages/data/BarcodesQR.vue (placeholder from N1).
- web_app/src/pages/StockItemDetailPage.vue and StockOverview.vue — you'll add
  scan and barcode-related actions.
- Pick a barcode library: server-side python-barcode + qrcode for generation,
  client-side @zxing/browser for camera-based scanning.

DATA MODEL:
1. Add a column `barcode` (string, nullable, unique-per-user) to stock_items.
2. Add a separate table `product_barcodes` (product_id, barcode), so a single
   stock item can have many merchant-product barcodes attached via its linked
   products.
3. Migration is destructive per pre-release rules — drop + recreate is fine if
   simpler.

BACKEND:
1. GET /api/stock-items/<id>/qr — returns a PNG of a QR code encoding
   "dora://stock-item/<uuid>". 256x256 default, ?size= override allowed.

2. GET /api/stock-items/qr/sheet?ids=<csv>&layout=avery-5160 — returns a PDF
   sheet of multiple QR codes laid out for a common label sheet. Each label
   shows: QR + item name + current level. Default layout: 3 cols x 10 rows
   on US Letter / A4. Make the layout parameter at least extensible.

3. POST /api/stock-items/<id>/barcode — body { "barcode": "<value>" }.
   Validates uniqueness per user. Returns 409 on collision.

4. GET /api/barcodes/lookup?value=<scanned> — returns:
     - { "kind": "stock_item", "id": <id> } if it matches stock_items.barcode
       OR a dora://stock-item/<uuid> link
     - { "kind": "product", "id": <id>, "stock_item_id": <id|null> } if it
       matches product_barcodes
     - { "kind": "unknown", "value": "<raw>" } otherwise.

FRONTEND (BarcodesQR.vue):
1. Three sub-sections in tabs or stacked cards: Scan, Print Sheets, Manage.

2. Scan:
   - Big "Open camera" button → opens a fullscreen scan overlay using
     @zxing/browser.
   - Crosshair targeting box, dim overlay outside the box.
   - On successful decode:
       - Green flash + a short "ding" (a 100-200ms tone — use Web Audio API,
         no audio file dependency).
       - Call /barcodes/lookup.
       - If kind = stock_item: open a modal with the stock item's name,
         level stepper (commit on +/-), expiry quick-actions, "add to primary
         list" button, "open detail" button. Closing the modal returns to the
         scanning view ready for the next code.
       - If kind = product: show product card with "link to a stock item"
         autocomplete; on link, register the barcode under product_barcodes.
       - If kind = unknown: prompt "Register this barcode against...?" with a
         stock item autocomplete and a product autocomplete.
   - On failed/invalid decode (low confidence, parser error): red flash +
     "buzz" tone, keep camera running.

3. Print Sheets:
   - Multi-select of stock items (use a virtualised list, filter box at top).
   - Layout picker (Avery 5160 / 5163 / A4 21-up — start with one or two).
   - "Generate PDF" → /qr/sheet?ids=...&layout=... opens the PDF in a new tab.
   - "Print all stock items" shortcut button.

4. Manage:
   - Table of stock items with their currently registered barcode (if any).
   - Per row: "Print one" → single-QR PDF, "Edit barcode" inline, "Clear".

STOCK ITEM DETAIL HOOK:
- Add to StockItemDetailPage toolbar: "Show QR" (modal with a big QR + Print
  button), "Register barcode" (opens the scan overlay focused on registering
  a product barcode against this item).

STOCK OVERVIEW HOOK:
- Add a "Scan" button in the toolbar that opens the same scan overlay —
  same flow as the Data Management Scan tab. (Extract the overlay as
  components/ScanOverlay.vue so both call sites share it.)

UX DETAILS:
- The scan overlay should ignore the same code being held in front of the
  camera repeatedly — debounce on (decoded value + 2 second window).
- Provide a torch toggle if the browser supports it.
- Camera permission denied → friendly empty state with instructions to enable.

DEFINITION OF DONE:
- Generate a QR for a stock item, print it, scan it, modal opens for that
  item, level adjustment persists.
- Register an unknown barcode against a stock item; rescanning later opens
  that item's modal.
- CHANGELOG entry under [Unreleased].
- Backend tests for lookup happy paths and the duplicate-barcode 409.

STOP AND ASK before writing code if @zxing/browser isn't an acceptable
dependency, if there's a Quasar-blessed scanner plugin already in use, or if
the barcode column already exists under a different name.
```

---

# Tier D — Other greenfield

## N6 — Reports / Analytics page

```
Build a brand-new Reports page for DiscountDora.

READ FIRST:
- web_app/src/pages/DashboardPage.vue — match its card style and layout idioms.
- dora_api/ shopping list, stock item, and product models — figure out which
  timestamps and price snapshots are already captured.
- The user's saved products and product price history — see what's queryable.

NEW ROUTE: /reports

BACKEND endpoints (all auth'd, all scoped to the current user):
1. GET /api/reports/stock-value-over-time?range=30d|90d|1y
   Returns: [{ "date": iso, "value": float }]
   Value = sum over all stock items of (current level rank * preferred-merchant
   most-recent unit price). It's an estimate, not accounting. Document that.

2. GET /api/reports/spend-by-merchant?range=...
   Returns: [{ "merchant": str, "spend": float, "list_count": int }]
   Only counts archived (completed) shopping lists.

3. GET /api/reports/most-bought-items?range=...&limit=10
   Returns top N stock items by appearances on archived lists.

4. GET /api/reports/keeps-running-out?limit=10
   Items most often at "out of stock" level at the moment of being added to a
   list. Useful "buy more of these" signal.

5. GET /api/reports/price-trends?product_ids=<csv>&range=...
   Returns per-product time series of unit price.

6. GET /api/reports/savings-captured?range=...
   For each archived list, sum(picked_offer_price) vs sum(rrp_at_time). Returns
   total savings and a per-list breakdown.

FRONTEND (ReportsPage.vue):
- Top strip: range selector (30 days / 90 days / 1 year / all time).
- Cards (responsive grid, 2 cols desktop, 1 col mobile):
  - "Stock value over time" — line chart.
  - "Spend by merchant" — donut + legend with $ amounts.
  - "Top 10 most-bought" — list with <StockItemChip> and a count column.
  - "You keep running out of these" — same chip list, with a "Make essential"
    bulk action button.
  - "Savings captured" — big number (total $ saved) + sparkline.
  - "Price trends" — multi-series line chart; product picker with autocomplete
    above it; users add/remove up to 5 products to overlay.
- Use Apache ECharts via vue-echarts, OR Chart.js — match whatever's already
  in the project; if neither, add ECharts.
- Every chip and number is clickable: deep links to StockItemDetail or to a
  pre-filtered StockOverview.
- Empty states for each card explain what data is needed to populate it.

DEFINITION OF DONE:
- /reports renders all six cards with real data on a dev DB seeded with a
  handful of completed shopping lists.
- Range selector changes refetch all cards.
- CHANGELOG entry under [Unreleased].
- No new schema needed if the timestamps exist; if not, add the minimum
  (e.g. shopping_list_items.picked_offer_price snapshot) and migrate.

STOP AND ASK if any of the price/snapshot fields don't exist and adding them
would change the data model significantly.
```

## N7 — Substitutes Graph

```
Build a brand-new Substitutes Graph view for DiscountDora.

READ FIRST:
- web_app/src/pages/StockItemDetailPage.vue — the substitute link feature
  ("I can link a stock item to another as an alternative") should already exist
  in some form. Find the model and the linker UI.
- web_app/src/pages/LocationsOverview.vue — copy its visual idioms (cards,
  attention chips, side panel pattern).

NEW ROUTE: /substitutes

DATA:
- A stock_item_substitutes table (stock_item_id, substitute_id, optional
  notes) is expected to exist. If not, add it (symmetric: A↔B is one row,
  treat as undirected). Pre-release, destructive migration if needed.

BACKEND:
1. GET /api/substitutes/graph
   Returns:
     { "nodes": [{ "id": uuid, "name": str, "level": str, "group_id": uuid }],
       "edges": [{ "a": uuid, "b": uuid, "notes": str|null }] }
2. POST /api/substitutes — body { "a": uuid, "b": uuid, "notes"?: str }.
   Idempotent on the unordered pair.
3. DELETE /api/substitutes — body same as POST.

FRONTEND (SubstitutesGraph.vue):
- Force-directed graph using vis-network or cytoscape.js (lighter is better;
  pick cytoscape unless one is already in the project).
- Nodes are circles labelled with item name; colour by stock_group. Out-of-stock
  items have a red ring; low-stock have amber.
- Edges are thin lines, hover reveals notes if any.
- Top toolbar:
    - Search box (highlights matching node, dims the rest).
    - Stock group filter chips (multi-select).
    - "Show isolated items" toggle (items with no substitutes).
    - "Layout" picker (force / concentric / breadthfirst).
- Click a node → side panel:
    - Item summary (<StockItemChip> from P0 if it exists, otherwise inline).
    - List of current substitutes with "Remove" per row.
    - "Add substitute" autocomplete (searches all stock items, excludes self
      and already-linked).
    - "Open in stock detail" button.
- Click an edge → side panel: both items + notes editor + remove button.
- Empty state when no substitutes exist: explainer + "Add your first
  substitute" CTA opening the same autocomplete.

UX DETAILS:
- The graph layout should be stable on rerender (no jarring full re-layout
  when you add one edge).
- Pinch/zoom + drag pan on mobile.

DEFINITION OF DONE:
- Build a substitute graph from a seeded dev DB; visually navigate it.
- Add and remove substitutes from inside the view.
- CHANGELOG entry under [Unreleased].

STOP AND ASK if the substitutes table doesn't exist and you're unsure whether
this should be additive or part of a bigger relationship feature.
```

## N8 — Price History Explorer

```
Build a brand-new Price History Explorer page for DiscountDora.

READ FIRST:
- merchant_api/ — find the price snapshot persistence (whatever stores
  scraped product prices over time).
- web_app/src/pages/ProductSearch.vue — match the product card / merchant logo
  conventions.
- The saved-products model in dora_api — products users have favourited.

NEW ROUTE: /price-history

BACKEND:
1. GET /api/price-history?product_ids=<csv>&range=30d|90d|1y|all
   Returns per product:
     { "product_id": uuid, "name": str, "merchant": str,
       "points": [{ "date": iso, "unit_price": float, "list_price": float,
                    "on_deal": bool }],
       "current": { "unit_price": float, "list_price": float, "deal_pct": int },
       "all_time_low": { "unit_price": float, "date": iso } }

2. POST /api/price-history/alerts
   Body: { "product_id": uuid, "threshold_unit_price": float }
   Creates a per-user subscription that fires (existing notification path) when
   a future scrape sees unit_price <= threshold.

3. GET /api/price-history/alerts and DELETE /api/price-history/alerts/<id>.

FRONTEND (PriceHistory.vue):
- Left rail: product picker. Autocomplete searching saved products first,
  then all known products. Multi-select up to 5. Selected products are listed
  as removable chips.
- Main area: overlaid line chart, one line per selected product, distinct
  colours. Hover crosshair shows date + each product's price + which were on
  deal that day.
- Range buttons (30d / 90d / 1y / all).
- Below the chart, a comparison strip — one card per selected product:
    - Current unit price (large) + change vs 7-day average chip
    - All-time low + "X% above low" indicator
    - Most-recent deal % off
    - "Notify me below $___" input with a "Set alert" button → calls the
      alerts endpoint.
- Top-right toolbar: "Manage alerts" button opens a modal listing every
  active alert with remove buttons.
- Deep-link from saved-products / ProductCard menus: "View price history"
  pre-selects that product.

UX DETAILS:
- If a product has no price history yet, show it in the chart as "no data"
  rather than dropping it silently.
- Time zone: render in the user's local TZ.

DEFINITION OF DONE:
- Compare 3 products' price history visually.
- Set and clear a price alert.
- CHANGELOG entry under [Unreleased].
- Backend tests for the multi-product query and the alert creation/listing.

STOP AND ASK if price snapshots aren't being stored at all currently — that's
a much bigger build and worth confirming scope first.
```

## N9 — Stock Map

```
Build a brand-new Stock Map view for DiscountDora.

READ FIRST:
- web_app/src/pages/LocationsOverview.vue and LocationDetail.vue — the
  hierarchical locations are the source of truth; this is a visual companion,
  not a replacement.
- The stock_locations and stock_items models.

NEW ROUTE: /map

DATA:
- Add a `map_layout` JSON column on the user (or a single-row settings table)
  storing per-location coordinates and shapes:
    {
      "nodes": [{ "location_id": uuid, "x": int, "y": int,
                  "w": int, "h": int, "shape": "rect"|"circle",
                  "colour": "<hex>", "label": str }],
      "canvas": { "w": int, "h": int }
    }
- Pre-release: store this destructively, no migration backwards-compat needed.

BACKEND:
1. GET /api/stock-map and PUT /api/stock-map. Trivial JSON blob get/set.

FRONTEND (StockMap.vue):
- A 2D canvas using Konva (or fabric.js — pick whichever is lighter and not
  already a dep collision).
- Toolbar:
    - "Add zone/area/section" buttons — drops a labelled rectangle on the
      canvas, click to choose which location it represents (autocomplete
      restricted to locations not yet placed).
    - "Snap to grid" toggle.
    - "Save layout" button (auto-save after a 2-second debounce too).
    - "Reset" with confirm.
- Each rectangle:
    - Drag to move, handles to resize.
    - Right-click / long-press menu: rename label, change colour, remove from
      map (does not delete the location).
    - Body lists <StockItemChip>s pinned to that location (read from the
      current items-by-location query, not stored on the map).
- Drag a stock item chip from a side panel "All items" list onto a rectangle
  to move it to that location (calls the existing move-item endpoint).
- Mobile: simplified read-only view — view, tap chips, but no drag-edit.

UX DETAILS:
- Persist the canvas on every meaningful change with a debounce.
- Undo/redo would be nice but is out of scope for the first cut.

DEFINITION OF DONE:
- Lay out a kitchen with 5–10 zones, drag items into them, refresh, layout
  persists, items reflect their location.
- CHANGELOG entry under [Unreleased].

STOP AND ASK before writing code — this one's the biggest. Confirm scope and
whether Konva/fabric are acceptable additions before starting.
```

---

# Tier E — Foundations primitives

## F2 — Empty states & loading skeletons

```
Build shared <EmptyState> and <LoadingSkeleton> components for DiscountDora,
then migrate existing pages onto them.

READ FIRST:
- web_app/src/pages/*.vue — scan how empty/loading states are currently handled
  (likely inline and inconsistent). List every variation.
- Quasar's q-skeleton docs.

BUILD:
1. components/EmptyState.vue — props: icon (string|component), title, body,
   primary-action {label, onClick}, secondary-action {label, onClick}. Slot
   override for custom content.
2. components/LoadingSkeleton.vue — variants via prop: "list", "grid",
   "detail", "table", "chart". Render the right q-skeleton arrangement per
   variant. Accept a `count` for lists/grids.
3. Migrate every page identified in the audit to use these. Delete inline
   implementations.

DONE WHEN:
- Grep finds zero ad-hoc empty/loading markup in pages/.
- One CHANGELOG line under [Unreleased].
```

## F4 — Notify / Confirm primitives

```
Centralise notification and confirmation patterns in DiscountDora.

READ FIRST:
- Every call to Quasar's $q.notify and $q.dialog across web_app/src/. List
  current variants (success, error, warn, info — and their styling drift).
- Existing boot files in web_app/src/boot/.

BUILD:
1. composables/useNotify.ts — exports notifySuccess, notifyError, notifyWarn,
   notifyInfo, notifyLoading (returns a dismiss fn). Standardise position,
   timeout, icon, colour. One source of truth.
2. composables/useConfirm.ts — async confirm({ title, message, danger?: bool,
   confirmLabel?, cancelLabel? }) → boolean. Danger uses red styling and
   requires typing the entity name if `requireTyped` is set.
3. boot/notify.ts — set defaults globally (taskboard: "Set defaults for
   notify in boot file").
4. Migrate every existing $q.notify and $q.dialog call site to the composables.
   Destructive actions must use useConfirm; warn if any direct dialog call
   survives a destructive code path.

DONE WHEN:
- Grep finds zero direct $q.notify / $q.dialog calls in pages/ or components/.
- CHANGELOG line under [Unreleased].
```

## F6 — Validation library

```
Centralise validation rules across DiscountDora frontend + backend.

READ FIRST:
- dora_api/ pydantic schemas — what's currently validated where.
- web_app/src/ form code — Quasar q-input :rules usage. List every ad-hoc rule.
- Taskboard items: empty-string validation, name uniqueness for stock items,
  duplicate stock items, "5000 days until stocktake" prevention.

BUILD:
1. A shared validation contract. Either:
   - Pydantic on the backend + hand-mirrored zod schemas on the frontend, OR
   - Define schemas in JSON Schema and generate both sides.
   Pick the lighter option. Document the choice in a 3-line README in
   web_app/src/validation/.
2. web_app/src/validation/ exports: stockItemSchema, shoppingListSchema,
   recipeSchema, locationSchema, userSchema, productSchema. Each captures
   required fields, max lengths, regex, range bounds, plus a `formRules()`
   helper that returns an array of Quasar q-input :rules functions.
3. Backend uses pydantic models that enforce the same rules. Add a unit test
   asserting that a representative invalid payload is rejected by both.
4. Migrate every form on the frontend to consume `formRules()`. Remove inline
   rules.

EXPLICIT RULES TO ENFORCE:
- Stock item name: non-empty after trim, max 120 chars, unique per user
  (uniqueness check via API on blur).
- Days until stocktake alert: integer 1–365.
- Shopping list name: non-empty after trim, max 80 chars.
- Email: standard format + max length.
- Username: non-empty, max 40, no whitespace.

DONE WHEN:
- Creating a stock item with whitespace/empty name fails on both client and
  server.
- Duplicate stock item name shows an inline form error before submit.
- CHANGELOG line under [Unreleased].
```

---

# Tier F — Navigation primitives

## S4 — Breadcrumbs everywhere

```
Standardise breadcrumbs across DiscountDora.

READ FIRST:
- Every page in web_app/src/pages/. Note which have breadcrumbs, which have
  manual back buttons, which have neither.
- The router config to understand route nesting.

BUILD:
1. components/PageBreadcrumbs.vue — renders Quasar q-breadcrumbs from a route
   meta `breadcrumbs` array OR from an explicit prop. Last item is non-link.
2. Set `meta.breadcrumbs` on every route, including dynamic ones (use route
   params + a resolver where needed, e.g. ShoppingListDetail shows the list
   name).
3. Render <PageBreadcrumbs> in the layout (or per page if more flexible).
4. Remove every ad-hoc back button and ad-hoc breadcrumb implementation.

DONE WHEN:
- Every page (except Login and ErrorNotFound) shows breadcrumbs.
- The path matches actual navigation hierarchy, not just URL nesting.
- CHANGELOG line under [Unreleased].
```

## S5 — Keyboard shortcuts + cheatsheet

```
Add a keyboard shortcut layer to DiscountDora.

READ FIRST:
- Existing focus-handling code. Any places that capture keyboard events.

BUILD:
1. composables/useShortcut.ts — register({ keys, scope, handler, description }).
   Scopes: 'global' (always on) or a route-name. Auto-deregisters on unmount.
   Ignores typing in inputs/textareas unless `allowInInput: true`.
2. Global shortcuts:
   - "/" → focus the StockOverview search (when on that page) OR open command
     palette (after S1 lands; for now, focus a global search route).
   - "?" → open a cheatsheet modal listing every registered shortcut grouped
     by scope.
   - "Esc" → close topmost overlay/modal/sheet.
   - "g s" → go to StockOverview, "g l" → ShoppingLists, "g r" → Recipes,
     "g d" → Dashboard, "g h" → Help. Use a mousetrap-style sequence library
     or implement a tiny sequence matcher.
3. Per-page:
   - StockOverview: "n" = new item, "f" = focus filter, "a" = add selected to
     primary list, arrow keys navigate the grid.
   - ShoppingListDetail: space = tick current row, "n" = add item.
4. components/ShortcutsCheatsheet.vue — modal listing all currently-registered
   shortcuts.

DONE WHEN:
- "?" opens a populated cheatsheet anywhere in the app.
- Sequences work even mid-typing only when allowInInput is true.
- CHANGELOG line under [Unreleased].
```

## S1 — Global command palette

```
Build a Ctrl/Cmd-K command palette for DiscountDora.

READ FIRST:
- web_app/src/router/ for route names.
- All Pinia stores — palette searches across stock items, recipes, shopping
  lists, locations, products.
- S5 (keyboard shortcuts) — depends on it for the trigger registration.

BACKEND:
1. GET /api/search?q=<query>&types=<csv>&limit=N (default limit 8 per type)
   - Returns:
       { "results": [{
           "type": "stock_item"|"shopping_list"|"recipe"|"location"|
                   "product"|"meal"|"meal_plan",
           "id": uuid,
           "title": str,
           "subtitle": str|null,
           "icon": str|null,
           "score": float,
           "match_spans": [[start, end], ...] // for highlighting
         }] }
   - Lowercased substring + fuzzy match (rapidfuzz or similar). Single
     query, parallel queries across entity types in the resolver.
   - Auth + user-scoping enforced per type.

2. GET /api/search/recents — last 20 entities the current user has navigated
   to (record navigations in a lightweight `user_recents` table or capture
   from server-side route hits).

3. POST /api/search/recents { "type", "id" } — frontend pings on navigation.

FRONTEND:
1. components/CommandPalette.vue — fullscreen modal overlay:
   - Centred card, ~600px wide, top of screen.
   - Single input at top, autofocus on open.
   - Sections below input:
     a. Commands (always visible when query is empty or matches).
     b. Recents (when query empty).
     c. Stock items, Shopping lists, Recipes, Locations, Products, Meals —
        each as a labelled section with up to 8 results.
   - Keyboard nav: arrows move selection, Enter executes, Esc closes.
   - Cmd/Ctrl-K toggles open/close.

2. Commands registry (in-app, not from backend):
   - Static commands available from anywhere:
     - "Create stock item" → opens the create modal
     - "Create shopping list"
     - "Create recipe"
     - "Auto-generate shopping list from low stock"
     - "Open primary shopping list"
     - "Go to dashboard / stock / lists / recipes / meals / products / data /
       settings / help"
     - "Toggle dark mode"
     - "Restart onboarding"
     - "Scan barcode" (if N5 is built)
     - "Show keyboard shortcuts" (opens S5 cheatsheet)
   - Context-aware commands registered by the active page via
     `useCommands().register({ id, label, action, when, icon })`. Unregistered
     on unmount.
   - Filter logic: fuzzy match on label + tags.

3. Result row visual:
   - Icon, title (with highlighted match spans), subtitle, type badge on the
     right. Selected row has a strong background.

4. On result select:
   - Entity result: navigate to its detail page, push to recents.
   - Command result: invoke the action.

5. composables/useCommandPalette.ts — open(), close(), focusQuery().
6. composables/useCommands.ts — register/unregister API for context commands.

UX DETAILS:
- Debounce search input by 120ms.
- Show a thin progress strip while a query is in-flight.
- Empty-query view shows recents + the top 6 most-used commands (track usage
  in localStorage; bump on each invocation).
- "Quick actions" pinned at the top: Create stock item, Open primary list,
  Scan barcode — visible regardless of query.
- Esc clears query before closing if non-empty (first Esc clears, second
  closes).
- Backdrop click closes.
- Render via a teleport to body to avoid stacking-context issues.

ACCESSIBILITY:
- role="dialog", aria-modal=true, focus trap inside the modal.
- Each section labelled, results have aria-selected on the active row.
- Announce result count changes via aria-live.

PERFORMANCE:
- Lazy mount: the component isn't rendered until first open, then kept
  mounted.
- Result list virtualised if total > 50.

DONE WHEN:
- Cmd-K opens from any screen.
- Typing "tom" surfaces stock items, recipes, and the "Create stock item"
  command, all rankable.
- Recents populate after navigating to a few entities.
- CHANGELOG entry under [Unreleased].
- Tests: command registration lifecycle, fuzzy match scoring sanity, keyboard
  nav across sections.

STOP AND ASK if a search endpoint with overlapping responsibility already
exists — don't duplicate it.
```

---

# Tier G — Resilience

## F1 — First-run onboarding

```
Build a first-run onboarding flow for DiscountDora.

READ FIRST:
- web_app/src/pages/LoginPage.vue and the router/auth guard logic.
- dora_api/ user model — confirm there's an `is_first_user`/admin flag and
  some way to detect "no data yet" per user (no stock items, no locations).
- web_app/src/pages/settings/StockLocationsSettings.vue,
  StockGroupsSettings.vue — onboarding seeds these.
- The pre-defined stock groups feature: "I have pre-defined stock groups on
  first usage of Dora".
- Memory: this is pre-release, destructive seed data is fine.

DATA / BACKEND:
1. Add user.onboarding_completed_at (nullable timestamp).
2. Endpoint POST /api/onboarding/complete sets it to now() for the current
   user.
3. Endpoint GET /api/onboarding/state returns:
     { "completed": bool, "first_user": bool, "has_locations": bool,
       "has_groups": bool, "has_stock_items": bool, "merchant_status": {...} }
   Used by the wizard to skip already-done steps if the user re-enters.
4. Seed catalogues bundled in the backend (NOT created on signup — offered
   in step 3):
   - default_stock_groups.json (Pantry, Fridge, Freezer, Cleaning, Toiletries,
     Pet, Other — adjust to taste).
   - default_locations.json (Kitchen > Pantry, Kitchen > Fridge,
     Kitchen > Freezer, Bathroom > Cabinet, Laundry > Shelf — Zone/Area/Section
     hierarchy).
   Endpoint POST /api/onboarding/seed with body { "groups": bool,
   "locations": bool } imports the selected catalogues.

ROUTING / GUARDS:
1. Auth-guard rule: if logged-in AND onboarding_completed_at is null, force
   redirect to /welcome regardless of requested route (except /logout).
2. /welcome is a new route that hosts the wizard layout (no app chrome —
   minimal header, no nav).

WIZARD (web_app/src/pages/onboarding/):
Five steps, with a progress bar at the top, "Back" and "Next" buttons, plus a
"Skip everything" link in the corner that just marks complete.

Step 1 — Welcome
  - Hero with Dora mascot, the chosen logo font, one-line value prop.
  - "Tell me your name" (writable display name) + theme picker (System /
    Light / Dark) + font picker. Saves to user prefs on Next.

Step 2 — Admin only: bootstrap
  - Only shown if state.first_user.
  - Confirm admin email, set a strong password (already set during signup —
    re-confirm or skip), invite teammates (optional, no-op if A2 household
    sharing isn't built).

Step 3 — Seed catalogues
  - Two cards side by side:
    - "Use Dora's default stock groups" — preview table of names + icons.
      Checkbox "Use these". Skipping = empty list, user creates their own.
    - "Use Dora's default locations" — preview tree. Same checkbox.
  - "Import from Grocy / spreadsheet instead" link → /data/import (N3).
    Returning user resumes at step 4.

Step 4 — Create your first stock item
  - A simplified inline create form (name, group, location, level).
  - "Create and add another" + "I'll do this later" link.
  - Skip allowed.

Step 5 — Tour
  - 4-card slide: Stock Overview (where you live), Shopping Lists (the
    killer loop), Alerts (Dora pings you), Help (Dora is here).
  - Each card has a "Show me" button that closes the wizard, navigates to
    the screen, and opens a contextual coachmark (one tooltip pointing at
    the primary action).
  - Finish button → POST /onboarding/complete → redirect to /dashboard.

UX DETAILS:
- The wizard remembers progress (writes a draft into localStorage). Refresh
  resumes the user at the last step.
- Every step's primary action is keyboard-accessible (Enter advances).
- Skip-everything sets onboarding_completed_at and removes the guard, but
  shows a one-time banner on the dashboard for 24h: "Welcome — finish
  setting up: [Continue]".
- A "Restart onboarding" entry in Settings > Account lets returning users
  redo it (clears the timestamp).

DONE WHEN:
- Fresh user lands at /welcome and cannot escape until completion or skip.
- Defaults seed correctly when selected.
- First-user becomes admin without intervention.
- Restart from Settings works.
- CHANGELOG entry under [Unreleased].
- One backend test for the seed endpoint round-trip, one frontend test for
  the guard redirect.

STOP AND ASK if user.onboarding_completed_at conflicts with an existing
column, or if the seed catalogues should live elsewhere (e.g. tenant-scoped
templates).
```

## F3 — Offline experience + global error boundary

```
Make DiscountDora gracefully handle errors and network loss.

READ FIRST:
- web_app/src/boot/ — any axios/fetch interceptors already configured.
- web_app/src/stores/ — Pinia stores; need to know how state is hydrated.
- The router config — for global error route.
- Taskboard items: "Hitting an endpoint that doesn't exist in the API just
  explodes", "Check if API online and report online/offline in UI",
  "I am alerted when I've gone offline / regained connection",
  "I can see immediate UI feedback on the search if there's no internet".

NETWORK STATE:
1. composables/useNetworkStatus.ts — exposes:
   { online: ref<bool>, apiReachable: ref<bool>, lastSeenOnline: ref<Date>,
     reconnecting: ref<bool> }
   - online: navigator.onLine + window 'online'/'offline' events.
   - apiReachable: polls /healthz on dora_api every 30s when online, every 5s
     when believed unreachable, with exponential backoff.
   - On state transition, fires a notify via F4's useNotify.

2. components/OfflineBanner.vue — slim red strip pinned under the app header
   when !online OR !apiReachable. Shows "You're offline. Some actions are
   queued." with a "Retry" button.

3. The OfflineBanner mounts in the root layout so it's global.

HTTP CLIENT HARDENING:
1. boot/http.ts — central axios instance with interceptors:
   - Request: attach auth token + correlation ID (uuid per request, header
     X-Request-Id).
   - Response error normalisation: map every error into
     { status, code, message, details } regardless of backend shape.
   - Retry: GET requests retry up to 3 times with exponential backoff on
     network errors, 502, 503, 504. NEVER retry POST/PUT/DELETE.
   - 401: trigger a re-auth flow (redirect to /login with returnTo).
   - 5xx: surface via useNotify error toast + log to console with the
     correlation ID.

MUTATION QUEUE (offline-tolerant mutations):
1. composables/useOfflineQueue.ts — when a mutation fails due to network
   error AND the action is registered as queueable, enqueue it in
   localStorage with { id, endpoint, method, body, createdAt, label }.
2. When apiReachable becomes true, drain the queue oldest-first. Show progress
   in a small "Syncing N changes" indicator. On per-item failure (non-network),
   surface a per-item conflict resolution dialog.
3. Queueable mutations to support:
   - Stock level updates (most common)
   - Tick/untick shopping list items
   - Mark stock item as opened/restocked
   - Push expiry / clear expiry
   These four cover the bulk of "user actions during a grocery run". Anything
   else fails loudly when offline (e.g. creating new entities).

GLOBAL ERROR BOUNDARY:
1. App.vue wraps the router-view in <ErrorBoundary> that catches Vue render
   errors, lifecycle errors, and async setup errors.
2. components/ErrorBoundary.vue:
   - Renders children normally.
   - On caught error: shows a full-page friendly error card with: "Something
     went wrong on this screen", the correlation ID (if any), "Reload page",
     "Go to dashboard", "Report this" (opens a mailto/GH issue prefilled with
     the error message + correlation ID).
   - Logs the error structured to the audit log endpoint (depends on I1+I2)
     if reachable; otherwise queues it for later.
3. router error handler:
   - Unknown route → /errors/not-found.
   - Navigation error → /errors/navigation with retry.
4. New routes /errors/not-found and /errors/server, both rendering
   components/PageErrorState.vue with friendly messaging.

EMPTY-LIST-WHILE-OFFLINE PATTERN:
- Stores must distinguish "loaded empty" vs "never loaded" vs "load failed".
  Pages display:
  - never loaded + offline: skeleton + "you're offline" hint.
  - load failed: empty state with Retry button (uses F2's EmptyState).
  - loaded empty: normal empty state.

DONE WHEN:
- Kill the API container; the UI shows the banner within 10s.
- Tick items on a shopping list while API is down; on restart, ticks sync.
- Throw a deliberate render error in a dev-only route; boundary catches it.
- 404 from /api gives the normalised error envelope, not a raw 500.
- CHANGELOG entry under [Unreleased].
- Tests: useOfflineQueue drain order, ErrorBoundary catches a thrown error,
  http retry stops after 3 attempts.

STOP AND ASK if optimistic UI patterns are already in place — the offline
queue assumes mutations are eventually-consistent; if everything is pessimistic
today, that's a bigger refactor and should be confirmed.
```

## F5 — Undo system

```
Add a global undo system to DiscountDora.

READ FIRST:
- Taskboard: "I can undo my last action via a button in the toolbar".
- Taskboard caution: "Consider simpler 'update' action that covers all
  updates for an entity (could overcomplicate rollbacks with optimistic UI)".
- Existing mutation surface in stores/ and composables.

CONCEPT:
- Undoable actions register an "inverse" at the time they fire. The inverse
  re-applies the prior state.
- Scope: per-tab session. Not persisted across reloads (too dangerous;
  state may have changed).
- History depth: 20 actions.

CORE:
1. composables/useUndo.ts — exports:
     register({ label, inverse, redo?, scope? }): void
     undo(): Promise<bool>
     redo(): Promise<bool>
     canUndo: ref<bool>
     canRedo: ref<bool>
     stack: readonly view of the last 20 entries.

2. The label is shown in the toast: "Deleted 'Tomato Soup'. [Undo]".
3. After undo, the action moves to a redo stack until a new action is
   registered (which clears redo).

WIRE INTO ACTIONS (the registered set):
- Delete stock item → inverse re-creates it with same ID and FK relations.
- Delete shopping list → inverse re-creates list + items.
- Tick item on shopping list → inverse unticks.
- Move stock item to another location → inverse moves back.
- Bump stock level → inverse restores prior level.
- Remove item from shopping list → inverse re-adds at same position.
- Auto-archive after "finish shopping" → inverse unarchives and rolls back
  the bulk stock level bumps (this is the big one — combine into a single
  undo entry).
- Recipe ingredient changes — bulk: inverse restores the prior ingredient
  set.

Each backend mutation needs to support its inverse cheaply. Two options:
   (a) snapshot-based: capture the entity (or relevant fields) before mutation;
       inverse posts that snapshot back. Simple, works for most cases.
   (b) compensation endpoints: explicit "undo-delete" etc. Rare; only for
       cases (a) can't handle (e.g. side effects already fired).
   Default to (a). Use (b) only for the "finish shopping" composite.

UI:
1. Add an Undo button in the global toolbar (top bar). Shows the label of
   the top-of-stack action on hover. Disabled when canUndo is false.
2. Ctrl/Cmd-Z and Ctrl/Cmd-Shift-Z (or Ctrl-Y) wired via S5's shortcut layer.
3. Every notifySuccess for an undoable action includes an inline "Undo" action.
4. After 10 seconds the undo entry stays in the stack, but the toast's
   inline button disappears (the global button still works).

CONSTRAINTS:
- Optimistic mutations also register their undo, but the registration is
  finalised only after server confirmation. If the optimistic op fails server-
  side, the entry is silently discarded.
- If the same entity has changed since the action (detected via updated_at
  comparison on inverse apply), surface "This was changed since — undo
  anyway?" confirm dialog.
- Undo of a delete may collide with new entities sharing that name —
  enforce the inverse using the original UUID; if it's been reused (extremely
  unlikely), bail with a clear error.

DONE WHEN:
- Delete a stock item, click Undo, item is back identically.
- Finish shopping, click Undo, list returns to active and stock levels roll
  back.
- Undo after offline-queued mutation works after sync completes.
- CHANGELOG entry under [Unreleased].
- Tests: register + undo on a snapshot-based mutation; redo after undo; clear
  redo on new action.

STOP AND ASK if "finish shopping" archiving already has a different reverse
flow defined — this composite undo is the trickiest piece.
```

---

# Tier H — Auth & PWA

## A1 — Registration + password reset

```
Build the full self-serve auth surface for DiscountDora.

READ FIRST:
- web_app/src/pages/LoginPage.vue.
- dora_api/ user model + existing auth (cookie session vs JWT?).
- emailer/ — confirm there's an outbound email path (and how to enqueue).
- Memory: first-user-is-admin already in place.

BACKEND:
1. POST /api/auth/register — body { "username", "email", "password" }.
   - Enforce password rules: min 10 chars, 1 letter + 1 digit.
   - Email format validation.
   - Username uniqueness + email uniqueness (case-insensitive).
   - Creates user with email_verified=false.
   - Sends verification email containing a token (random 32-byte URL-safe),
     stored hashed with a 24h expiry.
   - First user automatically gets is_admin=true AND email_verified=true
     (sysadmin shouldn't be locked out by missing mail config).
   - Returns 201 with the user payload (excluding password hash).

2. GET /api/auth/verify-email?token=<t> — marks email verified, deletes
   token. Redirects to /login?verified=1.

3. POST /api/auth/resend-verification — body { "email" }. Always returns
   200 even if email doesn't exist (no enumeration). Throttle: 1/min per
   IP + email.

4. POST /api/auth/forgot-password — body { "email" }. Same anti-enumeration
   behaviour. Sends a reset email with a token (separate from verification
   token; 1h expiry; single-use).

5. POST /api/auth/reset-password — body { "token", "new_password" }.
   Validates token, applies rules, invalidates all existing sessions for
   the user.

6. POST /api/auth/change-password (authenticated) — body { "current_password",
   "new_password" }. Validates current, applies new, optionally invalidates
   other sessions (keep current).

7. Rate limiting on all of the above: 10/min per IP for register, 5/min for
   reset / forgot, 5/min for login.

EMAIL TEMPLATES (emailer/):
1. verify_email.html / .txt — branded, includes the verification URL with
   the token, a "this link expires in 24h" line, a footer with "If you
   didn't sign up, ignore this email."
2. reset_password.html / .txt — same pattern, 1h expiry.
3. password_changed_notification.html / .txt — sent on successful password
   change as a confirmation, includes "If this wasn't you, contact admin".

FRONTEND:
1. /register page mirroring LoginPage styling:
   - Fields: username, email, password (with show/hide toggle), confirm
     password. Inline validation using F6's schemas.
   - Submit shows a success screen: "Check your email to verify your account"
     with a "Resend verification" button (throttled UI-side too).
2. /verify-email landing page: handles ?token=, calls verify endpoint, shows
   success → "Continue to login" button, or failure with "Resend" CTA.
3. /forgot-password page: single email field → success screen "Check your
   email" (no leak about whether email exists).
4. /reset-password landing page: ?token= + new password field + confirm.
   Success → redirect to login with toast.
5. LoginPage additions:
   - Link to /register.
   - Link to /forgot-password.
   - If ?verified=1 in URL, show "Email verified. Sign in to continue." toast.
   - If a user logs in but isn't verified: surface a banner "Verify your
     email to unlock all features" with a "Resend" button. (Decide: do you
     gate features behind verification? Recommend not — friction. Verification
     is informational + needed for password reset.)
6. Settings > Account additions:
   - "Change password" form using /change-password.
   - "Change email" flow (sends a verification to the new address; only
     swaps on confirm).

SECURITY:
- Tokens are SHA-256 hashed at rest; raw tokens only in the email link.
- Password hashing: argon2 (or bcrypt if already in use; taskboard mentions
  bcrypt).
- Session invalidation on password reset & change.
- Constant-time comparisons for token lookup.
- Generic error messages for forgot-password / verify-resend regardless of
  whether the account exists.

DONE WHEN:
- Register → verify → login round-trip works end to end on a dev SMTP.
- Forgot-password → reset round-trip works and invalidates an existing
  session.
- Change-password works from settings.
- All rate limits return 429 with retry-after.
- CHANGELOG entry under [Unreleased].
- Tests: register happy path, duplicate email rejection, verify expiry,
  reset token single-use, anti-enumeration on forgot.

STOP AND ASK before coding if the current auth is a different shape (e.g.
external IdP / OAuth) — the above assumes username+password local auth.
```

## M1 — PWA setup

```
Make DiscountDora a real PWA.

READ FIRST:
- quasar.config.ts — Quasar has built-in PWA mode. Confirm current setting.
- web_app/public/ for existing icons.
- Taskboard items: "Check out all the options under quasar.config.ts (pwa, etc)",
  "You (or an AE) specified an explicit quasar.config file > devServer > port.
   It is recommended to use a different devServer > port for each Quasar mode".

CONFIG:
1. Enable Quasar PWA mode: `quasar mode add pwa` if not added; configure
   in quasar.config.ts:
     pwa: {
       workboxMode: 'GenerateSW',
       injectPwaMetaTags: true,
       swFilename: 'sw.js',
       manifestFilename: 'manifest.json',
       useCredentialsForManifestTag: false,
     }
2. Different devServer port per mode (taskboard quote) — set ssr/pwa/spa
   to different ports.

MANIFEST:
1. quasar.config.ts → pwa.extendManifestJson:
   - name: "Discount Dora"
   - short_name: "Dora"
   - description: short tagline.
   - theme_color + background_color from DS1 tokens.
   - display: "standalone".
   - orientation: "portrait-primary" (kitchen phone usage).
   - icons: 192, 256, 384, 512 PNG + 512 maskable. Use the existing Dora
     mascot/logo.
   - shortcuts (app-launcher quick actions):
     - "Primary list" → /shopping-lists?open=primary
     - "Scan" → /data#scan (depends on N5)
     - "Add item" → /stock?new=1
   - share_target (optional, advanced):
     - action: /share, method: POST — share a product URL into Dora's
       product search.

SERVICE WORKER STRATEGY:
1. Precache: the SPA shell (HTML/JS/CSS/images bundle).
2. Runtime caching rules:
   - /api/* — NetworkFirst with 5s timeout, cache fallback for GETs.
   - Image CDN paths (image cache served by dora_api) — CacheFirst with
     30-day expiry, max 200 entries.
   - Merchant product images — CacheFirst, 7-day expiry, max 500 entries.
3. Skip-waiting + clients-claim on activate for snappy upgrades.
4. Update flow: when a new SW is detected, App.vue listens for
   `controllerchange` and shows a toast "New version available — Reload".
   The toast button posts {type:'SKIP_WAITING'} to the worker.

INSTALL PROMPT:
1. components/PwaInstallPrompt.vue — captures `beforeinstallprompt`,
   stashes the event, surfaces a Settings entry "Install Dora as an app".
   Also shows a one-time gentle prompt 7 days after first visit if not
   installed.
2. Detect iOS and show appropriate "Add to Home Screen" instructions
   (iOS Safari doesn't fire beforeinstallprompt).

OFFLINE:
1. Offline fallback page: /offline.html served when navigation fails.
   Friendly, branded, "you're offline — open Dora once you're back online,
   queued changes will sync." Mention the queue from F3.
2. Works alongside F3's offline queue — service worker handles network,
   the app handles state.

ICONS / SPLASH:
1. Generate the full icon set from a single 1024×1024 source. Recommend the
   pwa-asset-generator npm tool. Output: web_app/public/icons/.
2. Apple splash screens for iOS in a few common sizes.

LIGHTHOUSE / TESTING:
1. CI step (D4) runs Lighthouse against a built PWA, gates on PWA score
   threshold (≥ 90).
2. Manual test matrix: Chrome Android install, Safari iOS add-to-homescreen,
   Edge desktop install.

DONE WHEN:
- Visiting the deployed app on Chrome offers "Install Dora".
- After install, the app launches in its own window with no browser chrome.
- Going offline mid-session keeps the app usable (cached shell + queued
  mutations from F3).
- A new build triggers the "New version" toast.
- Lighthouse PWA score ≥ 90.
- CHANGELOG entry under [Unreleased].

STOP AND ASK if Quasar mode add pwa requires a non-trivial reorg, or if
the project's build pipeline doesn't support multiple Quasar modes today.
```

---

# Tier I — Heavy features

## X1 — Stocktake / Focused Review mode

```
Implement the Stocktake mode for DiscountDora.

READ FIRST:
- Feature notes:
  - "I can enter a focused stocktake mode, which shows me only the stock
    items that have not been checked on recently"
  - "When I check a stock item in focused review mode, it disappears from
    the list"
  - "I can enter a review mode from the shopping list where all checked
    items are shown and stock levels are set to well stocked automatically"
- Taskboard:
  - "The stocktake button glows when items require review/attention"
  - "Need some way to check on stock levels, so it's not last updated but
    lasted checked because you may not need to change stock levels"
- The stock_items model — find last_updated, expected last_checked, the
  days_until_stocktake_alert field.

DATA MODEL:
1. Add stock_items.last_checked_at (nullable). Distinct from last_updated_at:
   a "check" is the user confirming the current level is correct without
   changing it. Updating the level updates BOTH timestamps.
2. Add user/global setting `default_days_until_stocktake_alert` (existing —
   confirm; taskboard mentions "implement global fallback if value is zero").
3. Derived field (compute in query): `stocktake_overdue_by_days` =
   max(0, days_since(last_checked_at) - days_until_stocktake_alert).
4. Index on (user_id, last_checked_at) for cheap "oldest checked first"
   queries.

BACKEND:
1. GET /api/stocktake/queue?limit=50 — returns the items needing stocktake,
   ordered by stocktake_overdue_by_days desc, then last_checked_at asc.
   Response:
     { "items": [<stock_item_summary + overdue_days>], "total": N }

2. POST /api/stock-items/<id>/check — sets last_checked_at = now without
   changing level. Idempotent (returns same payload regardless of prior
   state).

3. POST /api/stocktake/bulk-check — body { "ids": [...] } sets last_checked_at
   for many.

4. POST /api/shopping-lists/<id>/review/complete — body { "set_well_stocked":
   bool } — for the shopping-list-review-mode flow:
   - Updates stock level to "well_stocked" for every ticked item.
   - Updates last_checked_at AND last_updated_at on those items.
   - Returns counts.

FRONTEND:
1. New route /stocktake (linked from StockOverview toolbar + nav menu).
2. pages/StocktakePage.vue:
   - Header card: total overdue count, most-overdue item highlight.
   - Big "Start" button.
   - Optional filters before starting: stock group, location subtree.
3. pages/StocktakeRunner.vue (separate sub-route /stocktake/run):
   - Fullscreen focus mode (no app nav chrome).
   - One item at a time, large card:
     - Picture, name, location, current level (visual stock-level dots).
     - Three primary buttons:
       (a) "Still correct" — POST /check, slide-out animation, next item.
       (b) "Change level" — opens an inline stepper / level picker. On
           confirm: PATCH stock-item, slide-out, next item.
       (c) "Out of stock" — shortcut for setting level=out, plus a tick to
           "Add to primary shopping list".
   - "Skip" (sets nothing, removes from this session only) and "Add to list"
     (quick add) secondary actions.
   - Progress strip top: "12 of 38 reviewed".
   - Keyboard: 1 = correct, 2 = change (focuses stepper), 3 = out, s = skip.
   - At session end: summary card with what was changed, what was added to
     lists, "Done" button → back to /stocktake.

4. StockOverview integration:
   - Toolbar button "Stocktake (N)" where N is the overdue count.
   - Glow / pulse animation on the button when N > 0 (taskboard request).
   - On click → /stocktake.

5. Shopping list "Review mode" (feature note):
   - In ShoppingListDetail, a toggle "Review mode" filters to ticked items
     only. A persistent footer says "Finish review and mark all as
     Well-Stocked" → calls /review/complete with set_well_stocked=true.
   - This is the existing finish-shopping flow's spiritual sibling; reuse
     wherever possible.

6. New filter on StockOverview: "Needs stocktake" chip (sets a query param
   that filters to stocktake_overdue_by_days > 0).

UX DETAILS:
- Stocktake runner is one-at-a-time by design (focus + speed). Don't show
  the full queue grid.
- After the session, the runner remembers what was checked in this session
  and doesn't re-show them even if they re-qualify mid-session.
- Persistent settings: default mode (start-from-most-overdue vs random),
  default filter scope. Saved per user.

NOTIFICATIONS:
- A daily morning notification (if push is enabled, M1 + No2): "X items
  need stocktake today". Throttle: max 1/day.

DONE WHEN:
- An item with last_checked_at older than its allowed window shows up in
  /stocktake.
- "Still correct" only updates last_checked_at, not last_updated_at.
- "Out of stock" both changes level AND optionally adds to primary list.
- The stocktake glow appears in StockOverview when overdue > 0.
- Shopping-list review-mode finish call bulk-sets levels.
- CHANGELOG entry under [Unreleased].
- Tests: queue ordering, /check idempotency, bulk-check transaction,
  review/complete with set_well_stocked.

STOP AND ASK if last_checked_at conflicts with an existing column or if
the days_until_stocktake_alert field lives somewhere unexpected.
```

## X5 — Auto-generated shopping lists

```
Build the auto-generated shopping list feature set for DiscountDora.

READ FIRST:
- Feature notes:
  - "I can auto-generate a shopping list via the Shopping List Overview
    Manager"
  - "I can flag a stock item to be added to an auto-generated shopping
    list"
  - "When I auto-generate a shopping list, all flagged stock items are
    added to the shopping list"
  - "I can at any point choose to auto-add essential items that are low/
    out of stock to an existing shopping list"
  - "Frequently Added suggestions for shopping list"
  - "I can enable/disable an option to auto-add a stock item to my
    shopping list when it drops to low stock or out of stock"
- stock_items model — confirm existing fields (is_essential, etc).
- ShoppingListsOverview + ShoppingListDetail.

DATA MODEL:
1. Add stock_items.flagged_for_auto_list (bool, default false). Distinct
   from is_essential — is_essential is a property of the item; flagged is
   "include in next auto-gen even if currently well stocked".
2. Add stock_items.auto_add_on_low (bool, default false) — when level drops
   to "low" or "out", the item is silently added to the user's primary
   shopping list (if not already on one).
3. shopping_list_items.added_via (enum: "manual" | "auto_low_stock" |
   "auto_essential" | "auto_flagged" | "auto_recipe" | "auto_meal_plan").
   Captures provenance so the user knows why something appeared.
4. shopping_list_items.added_at (timestamp) if not already present.

BACKEND:
1. POST /api/shopping-lists/auto-generate
   Body:
     { "name": str|null,                 // null => "Auto N - <date>"
       "sources": {
         "low_stock": bool,
         "out_of_stock": bool,
         "essentials_only_for_low": bool,
         "flagged": bool,
         "frequently_added": bool,        // top N items by past list freq
         "meal_plan_week": iso_date|null, // pull from a planned week
         "recipes": [recipe_id, ...]     // ingredients minus what's in stock
       },
       "merge_into_list_id": uuid|null    // null => create new list
     }
   Behaviour:
   - Collect candidate stock items from each enabled source.
   - Dedupe across sources, preserving the highest-priority added_via tag.
     Priority: auto_recipe > auto_meal_plan > auto_flagged > auto_essential
     > auto_low_stock > auto_frequently_added (tweak to taste).
   - For recipe/meal-plan sources, subtract items already at "well stocked"
     level.
   - If merge_into_list_id: append new items skipping duplicates. Otherwise
     create a new list named per `name` or default.
   - Return the resulting list with per-item added_via.

2. POST /api/shopping-lists/<id>/append-low-stock-essentials — convenience
   variant of (1) that appends essential + (low|out) items to an existing
   list. Reuses (1)'s logic.

3. Trigger for auto_add_on_low:
   - On any stock level mutation, if new level in (low, out) AND
     auto_add_on_low AND not already on any active list — add to user's
     primary list with added_via=auto_low_stock. Surface a notification:
     "Tomato Soup auto-added to <primary list>. [Undo]". The undo hook
     uses F5.

4. GET /api/shopping-lists/frequently-added?limit=20 — items most often
   appearing on archived lists for this user.

FRONTEND:
1. ShoppingListsOverview toolbar — primary "Auto-generate" button opens a
   modal:
   - Source toggles (checkboxes) as per the request shape.
   - "Generate as new list" or "Merge into" (with list picker — defaults to
     primary).
   - Preview pane: live count + item chips per source, with overlap
     resolution shown (e.g. "Tomato Soup: low stock + flagged → counted
     once").
   - "Generate" button → POST + navigate to the resulting list.

2. Stock item create / edit form additions:
   - Toggle "Auto-add when low/out" → stock_items.auto_add_on_low.
   - Toggle "Always include in auto-generated lists" →
     stock_items.flagged_for_auto_list.
   - Each has a small (i) tooltip explaining the difference (taskboard:
     "I can see an explanatory tooltip next to the 'long-life' check box").

3. StockOverview filter chips:
   - "Flagged for auto" filter.
   - "Will auto-add on low" filter.

4. ShoppingListDetail additions:
   - Each line shows a tiny chip for added_via if not "manual":
     "auto: low stock" / "auto: essential" / "auto: recipe Tomato Soup".
   - Toolbar "Append low+essentials" button → calls (2).

5. "Frequently added" suggestions inside the ShoppingListDetail "Add item"
   sheet (the QuickAddSheet from P0). Top section: "Suggested" with the
   /frequently-added results, one tap to add.

6. Recipe / meal-plan integration:
   - Recipe detail "Add missing to list" (already partially planned in P7)
     now routes through /auto-generate with sources.recipes=[id].
   - MealPlansOverview "Generate shopping list for this week" routes
     through with sources.meal_plan_week=<week_start>.

UX DETAILS:
- The notification for silent auto_add_on_low must include Undo (F5). If
  the user undoes, also clear auto_add_on_low? No — that's surprising.
  Just undo the addition; the toggle stays.
- Provide a way to see what would happen: /shopping-lists/auto-generate
  modal's "preview" never commits without explicit Generate click.
- Per-item added_via is informational; users can manually edit, in which
  case added_via flips to "manual" automatically.

DONE WHEN:
- Auto-generate from low stock creates a populated list.
- Auto-generate from a meal plan subtracts in-stock ingredients.
- Lowering a flagged item's level triggers a silent add + undoable
  notification.
- Frequently-added suggestions appear in the add-item sheet.
- CHANGELOG entry under [Unreleased].
- Tests: dedupe priority correctness, recipe subtraction math, auto_add
  trigger fires only on transition into low/out (not on every mutation).

STOP AND ASK if "primary list" concept isn't fully implemented yet — the
auto_add_on_low path depends on it.
```

---

# Tier J — Backend hardening

## I1 + I2 — Audit log + logging strategy (combined)

```
Add structured logging and an audit log to DiscountDora.

READ FIRST:
- Existing logging in dora_api, merchant_api, emailer — what's in place,
  what's print() vs log.
- Taskboard items:
  - "Configure root logger in each application and set log path to logs
    folder"
  - "Find good places to log in the code, and do so (info logging)"
  - "Only want to print what the persistence context is doing if in debug"
  - "Add better logging, non-existent in most cases"
  - "API auditing saved into the DB (make a logs table, where all parts of
    the application can log to, making sure to make a column for source
    e.g. DAPI) (do this in the middleware for DAPI)"

PART 1 — LOGGING STRATEGY (filesystem + console):

1. Per service (dora_api, merchant_api, emailer), configure Python logging:
   - Root logger at level INFO by default; DEBUG when ENV=development.
   - Two handlers:
     - StreamHandler → stdout (for docker logs aggregation).
     - RotatingFileHandler → ${LOG_DIR}/<service>.log, 10MB × 5 files.
   - Formatter:
     %(asctime)s %(levelname)s [%(name)s] [req=%(request_id)s]
     [user=%(user_id)s] %(message)s
     Use a logging.Filter to inject request_id and user_id from context
     (contextvars).
   - Per-module loggers obtained via logging.getLogger(__name__).
   - The persistence layer logs at DEBUG, not INFO (taskboard: "only print
     what the persistence context is doing if in debug").

2. Request middleware:
   - Generate request_id from X-Request-Id header if present, else uuid4.
   - Bind request_id + (if authed) user_id into contextvars for the duration
     of the request.
   - Log an INFO line at request start (method, path, user_id) and at
     request end (status, duration_ms).

3. Frontend: a small logger composable that mirrors levels and ships ERROR
   to a backend endpoint (/api/client-logs) for visibility into client
   crashes. Rate-limited.

4. Log directory permissions + docker volume in D2 already covers this.

PART 2 — AUDIT LOG (persisted, queryable):

1. New table `audit_events`:
     id (uuid)
     occurred_at (timestamp, indexed)
     source (enum: "dapi" | "mapi" | "emailer" | "web" | "system")
     actor_user_id (nullable; system events have no actor)
     actor_ip (nullable)
     action (str — verb-noun, e.g. "stock_item.created",
             "shopping_list.archived", "auth.login.failed")
     entity_type (nullable, e.g. "stock_item")
     entity_id (nullable, uuid)
     request_id (nullable, ties to request log)
     payload (json — minimal context, no PII secrets, no full bodies)
     severity (enum: "debug" | "info" | "warn" | "error" | "audit")
   Indexes: (occurred_at), (actor_user_id, occurred_at), (entity_type,
   entity_id, occurred_at), (action, occurred_at).

2. dora_api middleware:
   - After each request, if the route is in the auditable set (mutating
     routes by default — POST/PUT/PATCH/DELETE), emit an audit event with
     source=dapi, action derived from route name, entity_id from response
     where applicable.
   - Special-case auth: log success and failure of login, password change,
     password reset, registration, verification — even when other paths
     are skipped.

3. Domain-level audit emit helper:
   - audit.emit(action, entity_type=None, entity_id=None, payload=None,
                severity="info")
   - Called from service-layer code when the route-level event isn't
     descriptive enough (e.g. "stock_item.auto_added_to_list" from X5's
     trigger).

4. Frontend errors via /api/client-logs become source=web,
   action="client.error", severity=error.

5. Retention: configurable RETENTION_DAYS (default 365). A nightly job
   deletes events older than that. (Add a simple scheduler — APScheduler
   is fine.)

ADMIN UI:
1. New admin-only page Settings > System > Audit Log.
2. Table view with filters: time range, source, actor (user picker), action
   (autocomplete), entity type + id, severity.
3. Row click → detail drawer with full payload JSON pretty-printed and a
   "Find related" button (filters to same request_id).
4. Export selection to CSV.

ENDPOINTS:
- GET /api/audit/events?<filters>&page=&size= — admin only.
- GET /api/audit/events/<id> — admin only.

PRIVACY:
- payload must never include passwords, tokens, full PII dumps. A helper
  audit.scrub(payload) drops known-bad keys.
- Document the policy in the audit log code module's docstring.

DONE WHEN:
- A POST /api/stock-items writes one audit row with action=
  "stock_item.created", entity_id matching the new row, request_id matching
  the http log line.
- A failed login writes action="auth.login.failed", severity=warn.
- The admin Audit Log page loads, filters work, related-event navigation
  works.
- Logs roll over correctly at the configured size.
- ENV=production has DEBUG silenced for persistence.
- CHANGELOG entry under [Unreleased].
- Tests: audit middleware emits for one mutating route and skips for a GET;
  retention job deletes older-than-threshold rows; scrub drops password keys.

STOP AND ASK if a parallel audit/log table already exists with a different
shape — extend it rather than introducing a second one.
```

---

# Tier K — Design system

## DS1 — Design tokens + theme variables

```
Lock down DiscountDora's colour and spacing system.

READ FIRST:
- Every CSS/SCSS file in web_app/src/css/ and per-component <style> blocks.
- Quasar's $primary / $secondary / $brand setup.
- Taskboard: "Lock in colour scheme and apply it everywhere currently
  possible" + "Colours look different between chrome and firefox".

BUILD:
1. css/tokens.scss — every brand colour, neutral, semantic colour (success,
   warn, danger, info), surface/elevation tokens, spacing scale, radius
   scale, font-size scale. Use CSS custom properties so dark mode can swap
   them at the :root level.
2. css/themes.scss — :root (light) and [data-theme="dark"] overrides for the
   semantic tokens only.
3. Replace EVERY hard-coded hex / rgb in the codebase with a token variable.
   Grep #[0-9a-f] and rgb( to verify.
4. Quasar palette wired from the same tokens via quasar.variables.scss.
5. Fix the Chrome vs Firefox colour drift (likely caused by mixing srgb and
   p3 declarations or relying on browser-default colour spaces). Force a
   single colour space.

DONE WHEN:
- Zero hard-coded colours outside tokens.scss.
- Switching theme is a single attribute flip.
- Chrome and Firefox render identically on a representative page.
- CHANGELOG line under [Unreleased].
```

## DS2 — Icon audit

```
Standardise iconography across DiscountDora.

READ FIRST:
- Every `icon="..."` attribute usage. List every icon used.
- The current Quasar icon set in quasar.config.ts.

BUILD:
1. Pick ONE icon set. Quasar supports MDI, Material Symbols, Fontawesome,
   etc. Recommend MDI for breadth. Document the choice.
2. css/icons.ts (or similar) — a constants map of semantic names to icon
   strings: ICONS.stockItem, ICONS.shoppingList, ICONS.cartAdd, ICONS.expiry,
   ICONS.essential, ICONS.merchant, ICONS.recipe, ICONS.meal, ICONS.location,
   ICONS.user, ICONS.settings, ICONS.scan, ICONS.add, ICONS.delete,
   ICONS.edit, ICONS.confirm, ICONS.cancel, ICONS.search, ICONS.filter,
   ICONS.sort.
3. Replace every direct icon string in templates with ICONS.x.
4. Pick the nav-bar icons explicitly (taskboard: "Choose better icons for
   nav bar").

DONE WHEN:
- Grep for icon="" attributes finds only ICONS.x references.
- One CHANGELOG line under [Unreleased].
```

## DS3 — Component gallery / Storybook

```
Add a component gallery to DiscountDora.

READ FIRST:
- web_app/src/components/ and web_app/src/components/dora|locations|settings/.

BUILD:
1. Install Histoire (Vue-native, lighter than Storybook) or Storybook 8.
   Recommend Histoire for the Vue/Quasar fit. Document choice.
2. Write stories for every component in components/:
   - One per visual variant (slim/square, light/dark, with/without data).
   - Interactive controls for primary props.
3. CI step that runs the gallery build (smoke check that no story is broken).
4. README link to running the gallery locally.

DONE WHEN:
- `npm run gallery` opens a browseable catalogue of every shared component.
- CHANGELOG line under [Unreleased].
```

## DS4 — Animation library

```
Standardise animations and transitions in DiscountDora.

READ FIRST:
- Quasar's animation docs (q-transition primitives + the Animate.css
  bridge in quasar.config.ts).
- Taskboard mentions: "Look into animations", "smooth fade", "Cool modal
  animation: vuejs.org/examples/#modal".

BUILD:
1. Decide and document an animation philosophy: durations (fast 120ms,
   normal 200ms, slow 320ms), easing (default `cubic-bezier(0.4, 0, 0.2, 1)`),
   when to animate (state change, route transition, list reordering),
   when NOT to (frequent UI churn).
2. css/motion.scss — tokens for duration/easing.
3. components/transitions/ — wrappers:
   - <FadeTransition>, <SlideUpTransition>, <ScaleTransition>,
     <ListTransition> (for v-for grids).
4. Apply across:
   - Modal open/close (the vuejs.org example pattern).
   - Stock item grid: enter/leave + reorder animations (taskboard requests
     these explicitly).
   - Page route transitions.
5. Respect `prefers-reduced-motion` — disable all transitions when set.

DONE WHEN:
- Every modal uses the same open animation.
- Stock overview animates on data changes.
- prefers-reduced-motion disables them.
- CHANGELOG line under [Unreleased].
```

## DS5 — Naming consistency pass

```
Enforce naming conventions across DiscountDora frontend.

READ FIRST:
- The taskboard rule: "Standardise Event Handler method name. Prefix them
  with 'On'. E.g., OnBtnClick".
- Existing eslint config.

BUILD:
1. Update eslint config: add a rule (custom if needed) flagging Vue method
   names bound to @event handlers that don't start with "on" (lowercase, per
   JS convention — adjust the taskboard's "OnBtnClick" to "onBtnClick" unless
   the user prefers PascalCase; flag this in your response).
2. Rename every existing handler accordingly.
3. Add a second lint rule (or just a doc) for component naming
   (PascalCase, multi-word), prop naming (camelCase in script, kebab-case
   in template), event names (kebab-case emit, camelCase listener).
4. Run lint --fix; commit the renames as a separate commit from the rule
   addition.

DONE WHEN:
- Lint passes with the new rules.
- Grep finds zero @click="handleX" — all are @click="onX".
- CHANGELOG line under [Unreleased].
```

---

# Tier L — Documentation

## Doc1 — Proper README

```
Rewrite README.md for DiscountDora.

READ FIRST:
- Current README.md.
- CHANGELOG.md (the latest version is the public face).
- Taskboard: "Write a proper readme", "Include screenshots and detailed
  setup instructions in readme, look at popular docker container instructions
  for inspiration", "FONT FAMILY! (Part of the logo) - update the readme
  with this font for the logo/main title".
- Grocy's README as a reference.

WRITE:
1. Hero: logo (in the chosen logo font), one-line tagline, mascot Dora at
   the bottom with "My name is Dora and I approve this message." (taskboard
   item).
2. Screenshot grid: stock overview, shopping list detail, recipes, dashboard,
   alerts panel, locations heatmap. Use representative seeded data.
3. Feature highlights (10–15 bullets, grouped: Stock, Lists, Recipes & Meals,
   Deals & Products, Insights, Admin).
4. Quick start with Docker compose:
   - One-line up command.
   - Default URL + first-user-is-admin note.
   - Where data lives (volumes).
5. Configuration: env vars table.
6. Sponsorship button placeholder (taskboard item).
7. Roadmap pointer (link to Discount Dora/🗺️ Roadmap.md or an equivalent
   in-repo file).
8. Contributing: link to CONTRIBUTING.md (Doc2).
9. Licence + credits.

DONE WHEN:
- A new user could install + run from the README alone.
- CHANGELOG line under [Unreleased].
```

## Doc2 — CONTRIBUTING.md

```
Write a contribution guide for DiscountDora.

READ FIRST:
- Project structure (web_app, dora_api, merchant_api, emailer).
- Existing eslint/lint/test setup.
- Taskboard rules already established: "OnXyz" handler naming, separation
  of concerns rules.

WRITE CONTRIBUTING.md:
1. Project layout (one paragraph per service).
2. Local dev setup (prereqs, docker compose, npm install, run scripts).
3. Code style:
   - Frontend: Vue 3 + Composition API, Quasar, TypeScript strict.
   - Backend: Python, pydantic models, type hints required.
   - Event handler naming rule from DS5.
   - Entity ID rule (taskboard: "entity ID shouldn't be accessible at all
     in the domain, it's a persistence concern only").
4. Branching + PR conventions (small PRs, conventional commit prefixes if
   adopted).
5. Adding a feature: where the model goes, where the route goes, where the
   page goes, where the test goes.
6. Testing requirements: at least one test per new endpoint, one component
   test per new shared component.
7. CHANGELOG discipline: every PR adds a line under [Unreleased].
8. Filing a bug: template (repro, expected, actual, version).

DONE WHEN:
- CONTRIBUTING.md exists at repo root.
- Linked from README.
- CHANGELOG line under [Unreleased].
```

## Doc3 — API docs

```
Publish the DiscountDora API documentation.

READ FIRST:
- dora_api and merchant_api startup code. If FastAPI, OpenAPI is already
  generated at /docs and /redoc — verify both work.
- Existing route handlers — note any that lack response_model or summary.

BUILD:
1. Ensure both APIs serve OpenAPI JSON + Swagger UI + ReDoc in dev. Production
   gating optional — recommend gated behind an env flag.
2. Audit every endpoint: must have a tag, a summary, response_model, and
   error responses documented.
3. Generate a static HTML build of the OpenAPI doc and commit it as
   docs/api/ for offline browsing.
4. README: link to live docs URLs and the static build.

DONE WHEN:
- Swagger UI lists every endpoint with descriptions.
- No endpoint is missing tag/summary/response_model.
- CHANGELOG line under [Unreleased].
```

## Doc4 — User-facing help content

```
Fill the in-app Help section with real guides.

READ FIRST:
- web_app/src/pages/HelpPage.vue — current structure.
- Every feature board in C:\Users\ben.talese\Downloads\Discount Dora\
  Feature Boards\ — these tell you what features exist.
- CHANGELOG.md — link to "What's new" within Help.

BUILD:
1. Define a guides content store. Either:
   - Markdown files under web_app/src/content/help/ loaded at build time, OR
   - A guides table in the DB.
   Recommend markdown — easier to author and review.
2. Write one guide per major feature area:
   - Stock Overview & filters
   - Stock item lifecycle (create, update, stocktake, delete)
   - Locations (zones/areas/sections)
   - Shopping lists end-to-end
   - Recipes & cooking
   - Meals & meal plans
   - Products & deals
   - Alerts
   - Settings (per-user + admin)
   - Data Management (backup/import/export/barcodes — when those land)
   - Dora assistant
3. Each guide: 2–6 short sections with screenshots. End with "Related" links.
4. HelpPage gets a left-rail TOC + search across guide titles/bodies.
5. The Dora assistant's "What can I do on this page?" should deep-link to
   the matching guide section.

DONE WHEN:
- Help page is populated and navigable.
- Search returns hits.
- CHANGELOG line under [Unreleased].
```

---

# Tier M — DevOps

## D1 — Docker compose finalisation

```
Finalise the docker compose setup for DiscountDora.

READ FIRST:
- compose.yml, Dockerfile, startup.sh, nginx.conf.
- Taskboard: "Setup docker compose to make webapp depend on API",
  "Put .image_cache under /cache so it gets persisted over docker container
  instances", "Move ALDI products by category json to /cache",
  "Don't store the DB in the framework code folder".

BUILD:
1. Services: web_app (nginx serving built SPA), dora_api, merchant_api,
   emailer, db (or sqlite volume if that's the choice).
2. depends_on with healthcheck conditions: web waits on dora_api healthy;
   dora_api waits on db healthy; emailer waits on dora_api healthy.
3. Healthchecks: /healthz on each API (add if missing).
4. Volumes:
   - /data — sqlite DB + uploaded images
   - /cache — image cache + scraped json cache
   - /logs — application logs
   All declared as named volumes with sensible defaults + mount instructions.
5. Env vars in a single .env.example at repo root: DB_PATH, CACHE_DIR,
   LOG_DIR, API_KEY (if A4 lands), SCRAPER_*, EMAIL_*, ADMIN_BOOTSTRAP_EMAIL.
6. Document override patterns (compose.override.yml for dev).

DONE WHEN:
- `docker compose up` from a clean checkout produces a working app with one
  persistent volume per data type.
- Killing dora_api alone causes web to show offline banner, not crash.
- CHANGELOG line under [Unreleased].
```

## D2 — Cache & data path discipline

```
Move all runtime state out of the source tree for DiscountDora.

READ FIRST:
- Every code path that writes to disk: image cache, scraper JSON cache, DB
  file location, log path.
- Taskboard items: "Move image cache to /cache", "Move ALDI products by
  category json to /cache", "Put .image_cache under /cache so it gets
  persisted", "Don't store the DB in the framework code folder, put it
  somewhere else and allow user to define that location (potentially)",
  "Configure root logger in each application and set log path to logs
  folder".

BUILD:
1. A single config module per service exposes:
   DATA_DIR (default /data), CACHE_DIR (default /cache), LOG_DIR (default
   /logs). Pulled from env, with dev fallbacks.
2. Replace every hard-coded path with these.
3. Migration: on startup, if old paths exist, move files into the new
   locations once (with a backup copy). Idempotent.
4. .gitignore: remove now-irrelevant entries, add the local dev fallback
   paths.

DONE WHEN:
- Grep finds zero hard-coded ".image_cache", ".cache", DB filename string
  in code paths.
- Docker volume mounts cover all three dirs.
- CHANGELOG line under [Unreleased].
```

## D3 — Production vs dev config

```
Split configuration for dev and production in DiscountDora.

READ FIRST:
- Current config loading per service.
- Taskboard: "Create separate appsettings for development and production?
  Possibly doesn't matter", "Generate appsettings on start with defaults".

BUILD:
1. Per service: layered config — defaults → ENV file → environment vars.
   Pydantic Settings (Python) or equivalent.
2. ENV env var selects profile: development | production | test.
3. Generate a default config on first startup if none exists, writing to
   DATA_DIR. Document in CONTRIBUTING.md.
4. Differences enforced:
   - dev: CORS open, debug logging, hot reload, dev seed data.
   - production: CORS pinned, info logging, no seed data, requires API_KEY
     and admin bootstrap email.
5. Refuse to start production without required vars set; print a friendly
   error listing them.

DONE WHEN:
- ENV=production startup fails fast on missing required vars.
- ENV=development "just works" out of the box.
- CHANGELOG line under [Unreleased].
```

## D4 — CI pipeline

```
Add a CI pipeline for DiscountDora.

READ FIRST:
- package.json scripts.
- Python test runner config (pytest/unittest).
- Existing GitHub Actions workflows, if any.

BUILD .github/workflows/ci.yml:
1. Triggers: push, pull_request, manual dispatch.
2. Jobs (in parallel where possible):
   - frontend: npm ci, lint, typecheck, test, build.
   - backend-dora: pip install, ruff/flake8, mypy (optional), pytest.
   - backend-merchant: same.
   - emailer: same.
3. On main only, after all green: build & push Docker images tagged with
   commit sha + `latest`. Use GitHub Container Registry.
4. Cache: npm cache, pip cache, Docker layer cache.

DONE WHEN:
- A PR shows green check from each job.
- Main pushes produce tagged images visible in ghcr.
- CHANGELOG line under [Unreleased].
```

## D5 — Release automation

```
Automate releases for DiscountDora.

READ FIRST:
- CHANGELOG.md format (Keep-a-Changelog-style, [Unreleased] block).
- Current git tag history.
- D4's CI pipeline (depends on it).

BUILD .github/workflows/release.yml:
1. Trigger: manual dispatch with input `version` (semver).
2. Steps:
   - Validate input is semver and is higher than latest tag.
   - Move CHANGELOG [Unreleased] content into a new [<version>] - <date>
     block. Recreate empty [Unreleased].
   - Bump version in package.json and any Python __version__.
   - Commit the bump on a release branch and open a PR to main.
3. Separate workflow `tag-and-publish.yml` triggered on merge of that PR:
   - Tag v<version>.
   - Build + push Docker images with the version tag (and `latest`).
   - Create a GitHub Release with the [<version>] changelog block as body.

DONE WHEN:
- Running the workflow with version 0.8.0 produces a clean release commit,
  PR, merged tag, images, and GitHub Release.
- CHANGELOG line under [Unreleased] mentioning the automation.
```

---

# Tier N — Testing

## T1 — E2E test suite

```
Stand up an end-to-end test suite for DiscountDora.

READ FIRST:
- web_app/package.json — pick the lightest Playwright-compatible setup.
- compose.yml — how the stack starts.
- The existing tests/ directory at repo root.
- CI workflow from D4 (depends on it for integration).

FOUNDATION:
1. Add Playwright to web_app/devDependencies. Use the @playwright/test
   runner.
2. tests/e2e/ at repo root for E2E specs. (Keep separate from existing
   unit-style tests/.)
3. tests/e2e/fixtures.ts — shared fixtures:
   - `app` page object with helpers (login, createStockItem, openPrimaryList).
   - `seededUser` fixture that creates a user via API + seeds basics.
   - `cleanup` fixture wipes the user post-test.
4. tests/e2e/playwright.config.ts:
   - Targets: chromium-desktop, chromium-mobile (Pixel 5 emulation),
     firefox-desktop (taskboard mentions Firefox-specific issues).
   - baseURL from env (E2E_BASE_URL, default http://localhost:9000).
   - Web server launch: `docker compose up -d` if E2E_AUTOSTART=1.
   - Retries: 1 in CI, 0 locally.
   - Trace: on-first-retry.
   - Screenshots: only-on-failure.
   - Video: retain-on-failure.
5. Test DB strategy: each test creates a fresh user via /api/auth/register
   and operates entirely within that user's data. No shared global state
   except seed catalogues.

GOLDEN PATH SPECS (write these, in priority order):

spec/auth.spec.ts
  - Register → verify email (use a test-mode bypass: backend exposes
    /api/test/last-verification-token under E2E_MODE=1) → login.
  - Forgot password round-trip.
  - Wrong password shows error, doesn't navigate.

spec/onboarding.spec.ts
  - First user lands at /welcome, completes wizard, seeds defaults, lands
    on dashboard.
  - Re-login does NOT bounce back to /welcome.
  - Restart-onboarding from settings does.

spec/stock-overview.spec.ts
  - Create stock item via toolbar.
  - Filter by stock level → list reduces.
  - Sort by name → ordering changes.
  - Click row → detail panel opens.
  - Delete from detail → confirm → row disappears.
  - Undo via toolbar → row reappears.

spec/shopping-list.spec.ts (THE killer-loop happy path)
  - Create a list from auto-generate low+essentials.
  - Tick three items.
  - Adjust quantity on one.
  - Pick a merchant offer on another.
  - Finish shopping → list archives + ticked items' levels move to
    well-stocked.
  - Open archived list → items still ticked, levels show updated.
  - Undo → list active again, levels reverted.

spec/stocktake.spec.ts
  - Stale an item by manipulating last_checked_at via /api/test/set-time
    (test-only helper).
  - StockOverview shows glow on stocktake button.
  - Run /stocktake, mark "still correct" → item drops out of queue.

spec/scan.spec.ts (if N5 lands)
  - Register a barcode against a stock item via API.
  - Open scan UI, inject a synthetic decode event via a Playwright hook.
  - Modal opens for the right item.
  - Adjust level, confirm, level updates.

spec/data-management.spec.ts (if N2 lands)
  - Export backup.
  - Wipe key entities via API.
  - Restore selected subset.
  - Re-import same backup → no duplicates created.

spec/offline.spec.ts (if F3 lands)
  - Go offline via Playwright context.setOffline(true) mid-task.
  - Tick a shopping list item.
  - Banner shows.
  - Go back online — toast confirms sync.

TEST-MODE HELPERS (backend):
- Gated behind E2E_MODE=1 env (refuse to start in production).
- POST /api/test/reset — wipes the current user's data.
- POST /api/test/set-time { entity, id, field, iso } — backdate timestamps
  (last_checked_at, last_updated_at) for predictable stocktake / expiry
  scenarios.
- GET /api/test/last-verification-token?email=<e> — returns the latest
  unconsumed token, so tests don't need real email.
- GET /api/test/last-reset-token?email=<e> — same for resets.
- Document these aggressively as test-only. Audit log every call.

CI INTEGRATION (depends on D4):
- New job `e2e` in ci.yml:
  - Runs after frontend + backend jobs pass.
  - docker compose up with E2E_MODE=1.
  - Wait for /healthz.
  - npx playwright test --reporter=github,html.
  - Upload html report + traces as artifacts.
- Required for merge to main.

REPORTING:
- HTML report committed nowhere (CI artifact only).
- A README in tests/e2e/ explains how to run locally, how to debug,
  how the test-mode helpers work.

DONE WHEN:
- `npx playwright test` runs all specs locally against a docker compose
  stack.
- All golden-path specs pass.
- CI runs them on every PR.
- A deliberately-introduced regression (e.g. break "finish shopping")
  is caught by the right spec.
- CHANGELOG entry under [Unreleased].

STOP AND ASK if there's already a half-built Cypress suite — don't run two
frameworks in parallel.
```

---

# Deferred (decide later)

These were flagged as scope-creep risks. Don't spec until ready to commit.

- **A2** — Household / multi-user sharing (big architectural addition)
- **X2** — Recipe comparison tool
- **X3** — Product comparison tool
- **X4** — Deals catalogue view
- **X6** — Nutrition tracking
- **X7** — Unit conversion
- **X8** — Recipe import from URL
- **X9** — Recipe-as-markdown storage option
- **X13** — Automated meal plan generator
- **L1** — i18n wiring (decide: ship English-only and remove, or fill properly)

---

# Notes

- Prompts depend on each other; respect the recommended order.
- Every prompt has a **READ FIRST** and **STOP AND ASK** clause as drift protection.
- After each prompt lands, ask for a polish-pass prompt to revisit edges (empty states, error handling, mobile checks) once you've seen it running.
