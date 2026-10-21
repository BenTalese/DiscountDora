# Proposal — Barcode Scanning & QR Labels (P6-02)

**Status:** Implemented (cleanup slice + P8-02 barcode-to-add + FU-373
register-against-product) · **Date:** 2026-06-07 (last updated 2026-07-15) ·
Only remaining deferred item is §5.2 ingestion auto-populate, which needs an EAN
field on `Product` (ingestion-API work).  
**Scope:** Correct the data model behind scanning, gate the whole
scanning + QR-label surface behind one off-by-default install flag, relabel it
honestly, and draw a hard boundary: **scanning is a navigation aid only — it
never does live deal/price lookup.** The register-against-product UI and the
scan-unknown rework are designed here but deferred to Phase 2 (ingestion).

> **Charter tie-break for every decision below:** Effortless (P1) + Anti-creep
> (P10). Scanning is an optional power-user convenience, not a core loop — so it
> ships *off*, and we refuse to grow it into a price-lookup feature (the removed
> hosted-scraping concern).

---

## 1. The problem

The codebase shipped **two different "scan a code" systems** that were
conflated in the UI and one of which used the wrong data model:

1. **Dora's own QR labels.** Each stock item can render a `dora://stock-item/<id>`
   QR. You print these, stick them on shelves/containers, and scanning one jumps
   straight to that stock item's detail page. This is correct and useful.
2. **Real-world product barcodes (EAN/UPC).** The old code stored these in a
   `StockItem.barcode` column and "registered" a scanned barcode *against a stock
   item*. **This is the wrong model.** A real-world barcode identifies a
   *Product* (a sellable SKU), not your personal stock item. The same barcode on
   a tin of tomatoes is the same product regardless of whose pantry it sits in.

The UI made it worse: a "Manage" tab and a "Register barcode" button asked the
user to attach a raw barcode to a stock item, sitting next to "Show QR" with no
explanation of how they differed (directly the user's INV-5 question — *"How
does show QR code and register barcode work? Are they different features?"*).

There was also a latent risk of scope-creep toward "scan a barcode → look up the
cheapest deal," which is the **removed** hosted-scraping feature (P7-01). That
boundary must be defended in the design, not just the code.

---

## 2. The corrected model

- A real-world barcode lives in **`ProductBarcode`** (`product_id`, `barcode`,
  unique on `barcode`). It links a real EAN/UPC → a `Product`.
- **`StockItem.barcode` is dropped entirely** (column + register/clear routes +
  the wrong-model UI). A stock item is reached from a real barcode *transitively*:
  barcode → Product → linked stock item (via `preferred_product_id` or the
  `StockItemProduct` m2m).
- Lookup (`GET /api/data/barcodes/lookup?value=...`) resolves in this order:
  1. `dora://stock-item/<uuid>` → `{kind: "stock_item", id}` (Dora's own QR).
  2. `ProductBarcode` hit → `{kind: "product", id, stock_item_id|null}`
     (real barcode → product, plus linked stock item if any).
  3. otherwise → `{kind: "unknown", value}`.

There is deliberately **no path that resolves a real barcode straight to a stock
item** — that only happens through a Product link.

---

## 3. Off-by-default gating

The entire scanning + QR-label surface is gated behind a single install-wide
flag: **`AppSetting.scanning_enabled`** (boolean, default `false`).

- One flag, not per-feature toggles — anti-creep, and it matches the user's
  mental model ("turn scanning on/off").
- Exposed to the client through the existing health capability endpoint as
  `features.scanning`, consumed by a new `useScanningEnabled()` composable. No
  new Pinia store.
- Admin toggle lives in **Settings → System** (wired PATCH of `scanning_enabled`).
- When off, every entry point is hidden: the Stock Overview "Scan" + bulk
  "Print QRs" buttons, the stock-item-detail "Show QR" button, the Data →
  "Scanning & QR labels" nav section, and the section page itself shows an
  off-state banner pointing the user at the admin toggle.

This is the **distribution-posture-correct** choice: the *same artifact*
self-hosts or runs managed; scanning is a config-driven difference, not a build
fork.

---

## 4. Honest relabelling

- Data section renamed **"Barcodes & QR" → "Scanning & QR labels"**, caption
  "Scan product barcodes; print item & shelf QR labels".
- The section page drops the "Manage" tab; tabs are now **Scan** and
  **Print labels**.
- A banner states plainly: *scanning is a navigation aid only — it never looks
  up live prices*; camera needs HTTPS in production.
- Result dialog after a scan handles all three lookup kinds: stock-item (open
  detail), product-with-linked-item (open detail), product-not-linked
  (explain), unknown (explain "not linked to a product yet").

---

## 5. What this slice does NOT do (deferred to Phase 2 — ingestion)

These are designed but intentionally not built now, because the natural place to
populate `ProductBarcode` at scale is the ingestion API, and `Product` has no
EAN field yet (only `merchant_stockcode`):

1. **Register-against-product UI.** ✅ **Shipped 2026-07-15 (FU-373).** The
   backend (`POST /api/data/barcodes` with a `product_id`) always existed and was
   tested; the UI now lives on **My Products** — the per-product "⋮" menu →
   *Register barcode…* opens a text-entry dialog that POSTs `{barcode, product_id}`.
   This is the "next to product management, not stock items" home called for here,
   mirroring the stock-item detail *Add barcode* dialog and gated on the same
   install-wide `scanning_enabled` flag. **Scope call (owner, 2026-07-15):** the
   entry point is My Products only — the scan-unknown flow was deliberately *not*
   reworked into a "link to an existing product vs. add a new item" fork, to keep
   the one-tap P8-02 add path friction-free (Effortless P1 + Anti-creep P10).
2. **Ingestion auto-populate.** When the ingestion API imports a retailer
   catalogue, it should populate `ProductBarcode` from the feed's EAN/UPC field
   automatically, so most barcodes resolve without any manual registration. This
   requires an EAN field on `Product` (ingestion-API work).
3. **Scan → quick-actions modal** (feedback: *"QR code scanning should bring up
   a modal of quick actions on that item"* and the "scan mode" pick-an-action
   idea). Today scan → result dialog → open detail. A richer quick-actions modal
   (mark out of stock / well-stocked / open detail) is a Stock-Overview-scan
   concern and is folded into the C-1 Stock Overview overhaul, not here.

---

## 6. Open design questions (for the deferred slices)

- ✅ **Resolved.** Should the "Scan" tab exist under Data → Scanning at all, or
  only on Stock Overview? (Feedback flagged it as possibly redundant here.)
  **Outcome:** the Data → Scan tab was removed entirely; the Data page is now
  "Print QR labels" only, and the *action-oriented* scan lives on Stock Overview
  (FU-378) where item context exists. Per-item barcode registration lives on the
  stock-item detail page; per-product registration on My Products (FU-373). See
  the note in `QrLabels.vue`.
- QR labels with the Dora logo in the centre (D/D mark) — nice-to-have polish,
  not load-bearing; slot into the label-rendering work whenever it's touched.

---

## 7. Feedback coverage table

Maps the feedback bullets that motivated this P6-02 work (source:
`docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md`) to sections above.

| # | Feedback bullet | Where addressed |
|---|---|---|
| F-scan-1 | "How does show QR code and register barcode work? Are they different features?" (INV-5: QR vs register-barcode) | §1, §2, §4 — they were two systems with the wrong model; register-against-stock-item removed, QR labels vs product barcodes now distinct and explained |
| F-scan-2 | "Is it still barcodes and QR? Should it be renamed to QR codes?" | §4 — renamed "Scanning & QR labels" (kept "scanning" because real-barcode scan-to-navigate survives via ProductBarcode; not a pure "QR codes" surface) |
| F-scan-3 | "What's the point of the scan tab under QR codes in this area? Feels like only useful in stock overview." | §6 — flagged as open question; action-oriented scan deferred to C-1 Stock Overview, Data tab keeps label printing |
| F-scan-4 | Breadcrumb fluff: "Backup, import, export and barcode tools for your Dora data" | §4 — intro caption changed "barcode tools" → "label tools" (full breadcrumb teardown is C-DATA scope) |
| F-scan-5 | "QR code scanning should bring up a modal of quick actions on that item" | §5.3 — deferred to C-1 Stock Overview overhaul (scan + quick-actions belong where item context exists) |
| F-scan-6 | "Scan mode button — pick an action performed on scanned items (open details / mark out of stock / well-stocked)" | §5.3 — same deferral as F-scan-5 |
| F-scan-7 | "QR codes with the Dora logo in the middle (D/D simple one)" | §6 — noted nice-to-have, opportunistic during label-render work |

**Out of scope (with reason):** live deal/price lookup from a scanned barcode —
**explicitly removed** (P7-01 hosted scraping); §1, §3 defend this boundary.

---

## 8. From the original spec

The original spec (`docs/00_original_spec/`, pre-~100k-LOC, **historical, not
authoritative**) framed barcodes as a stock-item attribute, which is exactly the
wrong model this proposal corrects — **superseded**. Nothing worth extracting:
the ProductBarcode/Product framing post-dates and overrides it.

---

## 9. P8-02 — Barcode-to-add via Open Food Facts (2026-07-02)

**Status:** Implemented · **Scope:** extend the *unknown-EAN* branch of the
scan flow so a real barcode on any packaged product turns into a one-tap add.

### 9.1 The problem

The FU-056 hybrid barcode model closed the "already-mapped EAN" side of
scanning — direct linkage wins, else Product → StockItem traversal — but an
`unknown` EAN dead-ended in a `warning` toast: *"Unknown barcode — not
registered yet."* That's honest, but the user's next move (find the item's
name, category, image, then create it manually) is exactly the input-friction
gap champion-plan P8-02 exists to close.

### 9.2 The seam

Open Food Facts (world.openfoodfacts.org) is an open-data, community-maintained
product database. It's the correct source here because it:

- is **open data** (no scraping, no legal grey — Charter P9),
- exposes a stable JSON API with a permissive access policy,
- covers the packaged-food corpus that dominates pantry scans, and
- has an explicit "add-only" fit — we consume names, images, categories; we
  don't consume prices, deals, or merchant links (P8-02 defends the same
  boundary §1 defended: **scanning never does deal lookup**).

### 9.3 The invariant P8-02 must uphold

**Already-mapped EANs must never trigger an OFF call and must never create a
duplicate stock item.** The flow is layered so this is guaranteed by the
call ordering, not by inference:

```
scan value
   │
   ▼
GET /api/data/barcodes/lookup?value=...       ← existing, unchanged
   │
   ├─ kind = stock_item              → navigate to /stock/<id>          [existing]
   ├─ kind = stock_item_via_product  → navigate to /stock/<id>          [existing]
   ├─ kind = product_no_link         → open Add-Item dialog             [NEW: barcode-only prefill,
   │                                                                          register EAN on save,
   │                                                                          NO OFF call — user's
   │                                                                          Product data wins]
   └─ kind = unknown                 → GET /api/data/products/off-lookup?value=...   [NEW]
                                        │
                                        ├─ found: true  → open Add-Item dialog with OFF prefill
                                        │                 (name, brand, image, category); register
                                        │                 EAN against new stock item on save
                                        └─ found: false → open Add-Item dialog barcode-only;
                                                          register EAN on save
```

OFF is called **only** on the `unknown` branch. This is defended in one place
(`onOverviewScanDecoded` in `StockOverview.vue`) — no other caller reaches
`/api/data/products/off-lookup`, and the endpoint itself doesn't consult
Dora's tables (there's nothing to double-up on).

### 9.4 What ships

**Backend** — `dora_api/features/data/off_lookup.py`:

- `GET /api/data/products/off-lookup?value=<ean>` — server-side call so the
  browser never has to deal with OFF's CORS or User-Agent policy. Returns
  `{found: bool, name?, brand?, image_url?, categories?, quantity?}`.
- In-memory bounded FIFO cache (512 entries, 24 h TTL). Repeat scans of the
  same code are free.
- 5 s network timeout. Any network / JSON / shape failure returns
  `{found: false}` — no error surface for the SPA to special-case.
- User-Agent: `DashyDora/<version> (barcode-to-add; +https://openfoodfacts.org)`
  per OFF's polite-caller ask.
- Plausible-EAN gate (`\d{8,14}`) rejects Dora QR URIs and freeform garbage
  without a wasted OFF round-trip.

**Frontend**:

- `barcodeApiService.ts` — `offLookupAsync(value)` + `OpenFoodFactsSuggestion`
  type. Docstring reiterates the "unknown-only" invariant.
- `CreateStockItemDialog.vue` — new optional `prefill` prop
  (`CreateStockItemPrefill`) with `name / barcode / imageUrl / brand /
  quantity / categories / source`. When `barcode` is set, submit also POSTs
  `/api/data/barcodes` linking the EAN to the new stock item. A 409 there
  (rare race — the EAN was registered elsewhere between lookup and submit) is
  surfaced as a warning but doesn't roll back the create; the item still
  exists.
- `StockOverview.vue` — `onOverviewScanDecoded` rewired per §9.3.
  `product_no_link` is now a *first-class* case (opens the add dialog) rather
  than a dead-end toast.

**Tests** — `tests/test_off_lookup.py`:
- Parser: status-0 miss, status-1 hit, `generic_name` / `image_url` fallback.
- EAN plausibility gate.
- Cache: hit-caches-across-calls, TTL expiry refetches, FIFO eviction bounded.
- Fetch: URLError → not-found, non-JSON body → not-found.

**Not shipped (deferred):**
- **OFF lookup from *other* scan surfaces.** Only StockOverview drives the
  ScanOverlay today (StockItemDetailPage's Barcodes section is a manual-entry
  register box, not a scan flow). Adding scan buttons to inline
  "add-to-list" / recipe surfaces is a separate C-1 / C-7 concern.
- **Category → stock group mapping.** OFF's `categories` string is displayed
  verbatim in the suggestion banner; wiring it to a Dora stock group needs a
  taxonomy pass (C-cross Chunk 3 territory).
- **Image ingestion.** The dialog previews `image_url` but doesn't yet fetch
  it into `StockItem.image`. Image bytes over the wire raise different
  R-014 / image-policy questions (compression, reject-oversized); handled
  when FU-033 (`StockItem.image`) lands the actual image seam. Until then
  users can add the image manually after create.

### 9.5 Charter alignment

- **P1 Effortless** — the whole point: one scan → one confirm → stock item
  exists with a plausible name and image.
- **P3 Honest / P7 Preview-undo** — OFF data is labelled "Suggested from Open
  Food Facts — review and confirm" in the dialog banner. Nothing writes
  without a confirm. Miss + network fail collapse to the same UX (barcode-
  only fallback) so the user doesn't need to interpret error branches.
- **P9 No-scrape** — open data, credited source, no retailer round-trip.
- **P10 Anti-creep** — reuses `CreateStockItemDialog` and the existing
  `Barcode` register endpoint; the only new surface is one endpoint + one
  prefill prop.
- **P12 No-invent** — miss = miss; no LLM guess-a-name path.

### 9.6 Feedback coverage

P8-02 has no direct entry in
`docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` — the feedback
predates the champion-plan flag surface. The relevant motivations sit in the
champion plan directly (`DASHY_DORA_CHAMPION_PLAN.md` §P8-02) and in the
`§STOCK ITEM DETAIL` INV-5 bullet on the QR-vs-barcode confusion (§4 above),
both of which are covered.

Out of scope (with reason):
- **Live deal / price lookup from a scanned barcode** — explicitly **removed**
  (P7-01 hosted scraping). Defended in §1 and §9.3.
- **Merchant registration UI from a scan** — the "register this EAN against a
  Product" flow is FU-056 Phase-2 (deferred, needs the Products overlay to be
  in play).
