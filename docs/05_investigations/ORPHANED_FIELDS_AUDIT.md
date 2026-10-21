# ORPHANED_FIELDS_AUDIT — INV-1

**Date:** 2026-06-06  
**Type:** Read-only investigation. No code changes.  
**Purpose:** Find all fields / relationships that exist in the data model or DTOs
but have no way to be set or meaningfully used in the UI, or that are set but
never read. Feeds decisions about wiring up, surfacing, or removing dead weight.

---

## Method

- Read all `dora_api/domain/entities/*.py` files.
- Cross-checked every field against:
  - `dora_api/persistence/table_mappings.py` — DB column definition.
  - API handlers under `dora_api/features/` — what gets set and what gets into DTOs.
  - `web_app/src/` — grep (camelCase and snake_case) for display, edit, and model bindings.
  - Backend logic files (budget, reports, waste, assistant) for invisible use.
- Excluded `BaseEntity.id`, `BaseEntity.created_at`, and `BaseEntity.updated_at`
  (universal audit fields, always correct by convention).

---

## Entity-by-entity findings

### StockItem

| Field | Status | Detail |
|---|---|---|
| `image` | **UNFINISHED FEATURE** | Always `None` at creation (`create_stock_item.py:84`). Never returned in `StockItemDto` or `StockItemDetailDto`. Zero references in `web_app/src`. **Per the user, this is intended behaviour that was never built**: a stock item should be able to carry its own image, and if it has none but a *linked product* has an image, it should fall back to that product's image. Currently neither half exists. **WIRE UP**, don't remove. |
| `notes` | ok | In `StockItemDetailDto`; editable textarea in `StockItemDetailPage.vue`. Not in list DTO — correct (lean list). |
| `stock_group` | ok | Returned as `stock_group_id` in list DTO; full CRUD in `StockGroupsSettings.vue`; filter in `useStockFilters.ts`; editable dropdown in detail page and onboarding wizard. |
| `is_flagged` | ok | Set in detail page; drives auto-generate weighting and alert severity. |
| `auto_add_when_low` | ok | Editable toggle in detail page; triggers auto-add in stock-level change handler. |
| `is_open` / `opened_on` | ok | Toggled in detail page; `opened_on` auto-set on flip. |
| `barcode` | ok | Registered via camera-scan flow. |
| `last_checked_at` | ok | Updated by stocktake "Still correct" action; drives stocktake queue ordering. |
| `preferred_product_id` | ok | Returned in detail DTO; star icon in `StockItemDetailPage.vue`; drives shopping-list offer sort order. |
| `products` (m2m) | ok | Populated by product-search link flow; shown on detail page. |

**`StockItem.image` is an unfinished feature, not a true orphan** — see the
wire-up note in the row above.

---

### StockItemSubstitute join table

| Column | Status | Detail |
|---|---|---|
| `stock_item_a_id` | ok | Part of canonical undirected pair. |
| `stock_item_b_id` | ok | Part of canonical undirected pair. |
| `created_at` | ok | Audit timestamp. |
| `notes` | **UNFINISHED FEATURE** | Hardcoded to `None` in `add_substitute.py:66`. Never in `SubstituteDto` (`get_stock_item_detail.py:56-61`). Zero frontend references. Column was added in the `c8a1d3b6e9f4` migration ("undirected refactor") but the feature was never implemented. **Per the user, this is intended**: notes should capture *how* to substitute, e.g. "X butter can be replaced with Y amount of olive oil". **WIRE UP**, don't remove. |

---

### ShoppingListLine

| Field | Status | Detail |
|---|---|---|
| `quantity` | ok | In DTO; editable in shopping list. |
| `is_ticked` | ok | In DTO; primary shopping-list interaction. |
| `selected_product_id` | ok | In DTO; offer selection chip. |
| `sequence` | ok | In DTO; drag-reorder. |
| `added_via` | ok | In DTO; provenance chip ("auto: low stock", etc.). |
| `added_at` | ok | In DTO. |
| `picked_offer_price` | **BACKEND-ONLY** | NOT in `ShoppingListLineDto`. Used in `budget.py`, `assistant/tools.py`, `waste.py`, `reports.py` as the price snapshot at tick time. Frontend never sees it — by design: the UI works with `actual_unit_price` for any visible price; the backend falls back to this snapshot for invisible calculations. |
| `list_price_at_pick` | **BACKEND-ONLY** | NOT in DTO. Used only in `reports.py` savings calculation (`list_price_at_pick − picked_offer_price`). Same design rationale as above. |
| `actual_unit_price` | ok | In DTO; user-entered "what I actually paid". |
| `purchased_merchant_id` | ok | In DTO; resolves to merchant name. |

---

### Recipe

| Field | Status | Detail |
|---|---|---|
| `nutrition` | ok | Freeform string; imported from URL schema.org; editable in `RecipeEditDialog.vue`; displayed in detail and cook mode. |
| All other Recipe fields | ok | Name, description, servings, prep/cook/total time, source_url, image, tags — all surfaced. |

> **Note on "nutrition fields":** There are no structured nutrition columns
> (calories, protein, carbs, fat) anywhere in the data model. The single
> `Recipe.nutrition` field is a freeform text blob, fully wired.

---

### RecipeIngredient

| Field | Status | Detail |
|---|---|---|
| `notes` | ok | Editable in `RecipeEditDialog.vue`; displayed conditionally in `RecipeCookMode.vue`. |
| All other fields | ok | |

---

### Product

| Field | Status | Detail |
|---|---|---|
| `image` | **CHECK** | Stored as `LargeBinary` (same pattern as `StockItem.image`). Returned in product DTOs; displayed in product search cards in the UI. This one IS used — confirmed via grep. |
| All other fields | ok | brand, is_active, is_available, merchant_stockcode, size, size_unit, size_value, web_url, current_offer, historic_offers — all in DTOs and surfaced in the product explorer / shopping list. |

> `Product.image` is fine — it differs from `StockItem.image` (which is always `None`).

---

### PriceAlert

| Field | Status | Detail |
|---|---|---|
| `threshold_unit_price` | ok | In DTO; shown on alert list; editable via create-alert form. |
| `last_fired_at` | ok | Returned in `PriceHistoryPage` alert list (`priceHistoryApiService.ts:32`); shown as "last triggered" info. |

---

### Other entities (no orphans found)

`StockGroup`, `StockLevel`, `StockLocation`, `Merchant`, `MealPlan`,
`MealPlanEntry`, `ShoppingList`, `ShoppingListTemplate`, `StockLevelChange`,
`StockItemWasteEvent`, `ProductOffer`, `ProductHistoricOffer`, `ProductBarcode`,
`AuditEvent`, `AppSetting`, `AuthToken`, `DoraSuggestionSuppression`,
`RecipeCollection` — all fields checked. Either fully wired or well-documented
internal-only fields (e.g. `StockLevelChange` is an append-only audit log, not
meant to have a write UI).

---

## Summary table

| Entity | Field | Verdict | Recommendation |
|---|---|---|---|
| `StockItem` | `image` | Unfinished feature — own image + product-image fallback never built | **WIRE UP** (storage already exists; build upload + fallback + display) |
| `StockItemSubstitute` | `notes` | Unfinished feature — substitution notes never built | **WIRE UP** (add to request + DTO + edit/display UI) |
| `ShoppingListLine` | `picked_offer_price` | Backend-only (budget / reports / waste / assistant) | **DOCUMENT** — not a bug; add a one-line comment to the DTO file explaining it's intentionally excluded |
| `ShoppingListLine` | `list_price_at_pick` | Backend-only (reports savings calc only) | **DOCUMENT** — same as above |
| All others | — | Fully wired | LEAVE |

> **No true orphans found.** The two flagged fields are both deliberately-designed
> features whose implementation was never completed. Neither should be removed.

---

## Build cost estimates

**`StockItem.image` wire-up** — Medium / Large  
The column already exists; the work is the feature around it.
- Backend: accept image on create/update (multipart or base64), return it in
  `StockItemDto` + `StockItemDetailDto`. Implement the **product-image fallback**:
  when `image` is NULL but a linked product has an image, return that one (decide
  whether the fallback is computed server-side in the DTO or resolved client-side
  from `preferred_product_id` / `products`).
- Frontend: image upload control on the detail page, thumbnail in the list/detail,
  fallback display logic.
- New Alembic migration: none — column exists.
- Open design Qs: own-image vs product-image precedence (user confirmed own wins,
  product is fallback); image size/format limits; whether list view shows it.
- Risk: low (additive).

**`StockItemSubstitute.notes` wire-up** — Easy / Medium  
- Backend: add optional `notes` to `AddSubstituteRequest`, persist it (replace the
  hardcoded `notes=None` at `add_substitute.py:66`), add a field to `SubstituteDto`
  in `get_stock_item_detail.py`. Likely also an edit-notes endpoint (or fold into
  add as upsert).
- Frontend: notes input when adding/editing a substitute; display the note where
  substitutes are surfaced (detail page list, recipe substitution hints, and the
  B8 cook-mode temporary swap — "X butter → Y olive oil" is exactly the cook-mode
  use case).
- New Alembic migration: none — column exists.
- Risk: low (additive).

**Document backend-only snapshot fields** — Trivial  
- Add a one-line comment to the relevant DTO / handler file explaining that
  `picked_offer_price` and `list_price_at_pick` are intentionally absent from
  the DTO (they are internal audit fields for reports and the assistant).
- No migration, no code change.

---

## Recommended placement in the prompt plan

- **`StockItem.image` wire-up** — a small feature, not a tidy-up. Needs its own
  prompt (or folds into a stock-item-detail polish chunk). Resolve the precedence
  / fallback / size-limit design questions first.
- **`StockItemSubstitute.notes` wire-up** — natural fit alongside the substitute
  work: **INV-8** (substitute swap-into-list assessment) or the **B8** cook-mode
  temporary-swap chunk, since the substitution-note ("use Y amount of Z") is most
  valuable exactly at swap/cook time.
- **DTO documentation comment** — opportunistic, whenever a prompt next touches
  the shopping-list handlers.

---

## Feedback coverage table

The user flagged these specific fields for investigation. All accounted for:

| User-flagged topic | Finding |
|---|---|
| Stock groups | Fully wired — filter, CRUD settings, detail dropdown, onboarding wizard |
| Notes (stock item) | Fully wired in detail view |
| Notes (ingredient) | Fully wired in recipe edit and cook mode |
| Preferred merchant / product | Fully wired — `preferred_product_id` drives shopping-list sort |
| Nutrition fields | No structured nutrition columns exist; single `Recipe.nutrition` freeform string is fully wired |
| "Anything else" | Found: `StockItem.image` (unfinished feature — wire up w/ product-image fallback), `StockItemSubstitute.notes` (unfinished feature — wire up substitution notes), two backend-only snapshot fields on `ShoppingListLine` |
