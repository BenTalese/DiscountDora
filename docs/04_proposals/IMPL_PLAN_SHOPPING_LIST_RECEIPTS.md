# Implementation Plan — Receipt-photo attachments on shopping lists

**Status:** Plan for review · **Date:** 2026-06-30 · **No code yet.**
**Origin:** ad-hoc user request, 2026-06-30 — "ability to attach a real
receipt photo to a shopping list, just for record keeping."
**Tracked as:** `DORA_FOLLOWUPS.md` FU-334.
**Phase:** opportunistic — *not* a Phase-1 blocker; slot in during shopping
polish or after the Phase-1 loop is closed.

---

## 1. Intent

Let the user attach **one or more receipt photos** to a shopping list as a
record. View-only after attach — **no OCR, no parsing, no totals math, no
auto-matching back to lines**. Pure record-keeping, surfaced inline on the
list detail and on the post-shop summary.

This is the cheap, honest version of the "I want a paper trail for my shop"
ask. The full ingestion / OCR path is Phase 2 and is unrelated — keep that
separation clean.

## 2. Resolved decisions (locked 2026-06-30)

| # | Question | Decision |
|---|----------|----------|
| 1 | One photo or many? | **Many** (1..N). Long receipts span multiple photos; one shop may hit two stores. |
| 2 | Caption per photo? | **Drop.** No caption field in v1. Add only if real usage demands it. |
| 3 | Per-store linkage? | **No.** Receipts are evidence, not structured data. Don't tie to `purchased_store_id`. |
| 4 | Lifecycle gate? | Visible/attachable on `shopping` and `done` lists. Hidden on `draft` (no shop happened yet). |
| 5 | Delete after `done`? | **Yes** — user owns the record. |
| 6 | Storage shape? | Mirror `RecipeStepImage` — row stores `data:image/...;base64,...` UTF-8 bytes; raw bytes served from a dedicated endpoint. |

## 3. State-ownership & engineering-standards check

- **R-003 (centralised image upload):** Reuse `processImageFile`
  ([web_app/src/services/files/imageService.ts:60](../../web_app/src/services/files/imageService.ts))
  — 1600px long-edge, JPEG q0.85, 12MB input cap, MIME allow-list. Do **not**
  add a parallel resize/encode path.
- **R-003 (server-owned display strings):** The detail payload exposes a
  `url` for each attachment (pointing at the bytes endpoint). Client never
  constructs the URL by hand.
- **R-005 (portable data access):** Bytes column must work on SQLite (BLOB)
  and Postgres (BYTEA). Mirror the existing `recipe_step_image.image`
  mapping exactly.
- **State-ownership:** No domain logic on the client. The "attach is allowed"
  gate is enforced server-side; the SPA hides the button when
  `status === 'draft'` purely as UX, not as the authority.

## 4. Backend

### 4.1 Entity
`dora_api/domain/entities/shopping_list_attachment.py` — fields:
- `shopping_list_id: UUID`
- `sequence: int` (ordering within the list)
- `image: bytes` (UTF-8 encoded `data:image/...;base64,...`)

Pattern lift from
[recipe_step_image.py](../../dora_api/domain/entities/recipe_step_image.py).

### 4.2 Migration
New table `shopping_list_attachment`:
- `id` UUID PK
- `shopping_list_id` UUID FK → `shopping_list.id`, **ON DELETE CASCADE**
- `sequence` int NOT NULL DEFAULT 0
- `image` BLOB/BYTEA NOT NULL
- `created_at` timestamp NOT NULL
- Index on `shopping_list_id`

Portable SQLite + Postgres. No `caption` column (decision #2).

### 4.3 Table mapping
`dora_api/persistence/table_mappings.py` — register with `lazy="noload"` so
the bytes never load unless explicitly requested; the detail payload only
needs id + sequence.

### 4.4 Feature handlers (`dora_api/features/shopping_lists/`)

**`manage_shopping_list_attachments.py`**
- `add_attachment(list_id, data_url)` — reject if list is `draft`; reject if
  bytes exceed a defence-in-depth cap (~3MB encoded, well above the 1600px
  JPEG q0.85 ceiling); assign next `sequence`; return new id.
- `delete_attachment(list_id, attachment_id)` — straight delete.
- `reorder_attachments(list_id, ordered_ids)` — optional; skip in v1 unless
  cheap.

**`get_shopping_list_attachment_bytes.py`**
- Bytes endpoint `GET /shopping-lists/<list_id>/attachments/<attachment_id>`
  returning raw decoded bytes with the sniffed `Content-Type` header.
  Pattern lift from the recipe step-image bytes endpoint
  ([get_recipes.py](../../dora_api/features/recipes/get_recipes.py)).

### 4.5 Detail payload
`get_shopping_list_detail` adds an `attachments: [{id, sequence, url}]`
array. `url` points at the bytes endpoint, never inlines base64 — keeps the
JSON small and lets the browser cache per-image.

### 4.6 Tests
- e2e: attach → list detail returns the attachment → bytes endpoint serves
  raw image with correct Content-Type → delete → gone.
- Reject attach on `draft` list.
- Cascade: deleting the list removes its attachments.

## 5. Frontend

### 5.1 Model
[web_app/src/models/shoppingList.ts](../../web_app/src/models/shoppingList.ts)
— add `attachments: ShoppingListAttachment[]` where
`ShoppingListAttachment = { id: string; sequence: number; url: string }`.

### 5.2 API service
[web_app/src/services/api/shoppingListApiService.ts](../../web_app/src/services/api/shoppingListApiService.ts):
- `addAttachment(listId, file: File)` — calls
  `processImageFile(file)` first, then POSTs the resulting `dataUrl`.
- `deleteAttachment(listId, attachmentId)`.

### 5.3 UI on `ShoppingListDetail.vue`
- New "Receipts" section near the bottom of the list, rendered only when
  `status !== 'draft'`.
- **Empty state:** inline button "📎 Attach receipt photo" — a file input
  with `accept="image/*"` and `capture="environment"` so mobile goes straight
  to the rear camera.
- **Populated state:** horizontal thumb strip; tap a thumb opens a
  full-screen viewer (Quasar `q-dialog` + swipeable carousel, or whatever the
  recipe step-image viewer already uses — reuse, don't fork). Each entry has
  a trash icon.
- **Optimistic add:** thumb appears immediately with a spinner overlay; on
  failure, roll back and surface the standard friendly-error toast.

### 5.4 Post-shop summary
If the "Finish shop / restock review" recap view exists, render the same
thumb strip in read-only mode. Reuse the component.

## 6. Out of scope (explicit)

- OCR / receipt parsing (Phase 2 ingestion territory; separate concern).
- Auto-matching photo line-items back to `ShoppingListLine` rows.
- Storing or reconciling receipt totals against `actual_unit_price`.
- Sharing / exporting receipts to other people or storage.
- Linking an attachment to a specific store on a multi-store shop.
- Captions (decision #2 — revisit only on real usage demand).

## 7. Effort

- Backend: ~1 day (entity + migration + table mapping + 2 handlers + bytes
  endpoint + detail payload field + e2e tests).
- Frontend: ~1 day (model + API methods + Receipts section + thumb strip +
  viewer + optimistic flow).
- Verify checklist: ~6 items in `DORA_VERIFY.md` under a new
  "Shopping lists / Receipts" sub-heading — attach from camera, attach from
  gallery, multi-attach, delete, attach blocked on draft, attachments survive
  reload.

## 8. Coverage cross-check

This is **not** a feedback-driven proposal — it's a user ask raised
2026-06-30 outside the feedback library. No bullet from
`docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` motivates it,
so no `F##` mapping table is required (per CLAUDE.md "cross-checking
against the original feedback" — that rule targets surface-wide
briefs/proposals; this is a single ad-hoc feature). The original-spec
skim returned nothing relevant: `docs/00_original_spec/` mentions
"receipt" only in the OCR / ingestion sense, never as a record-keeping
attachment.
