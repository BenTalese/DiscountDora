# Proposal — Barcode Scanning & QR Labels (P6-02)

**Status:** Implemented (cleanup slice) + Draft (deferred slices) · **Date:** 2026-06-07  
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

1. **Register-against-product UI.** The backend route
   `POST /api/data/barcodes/register-against-product` exists and is tested, but
   there is no UI to drive it. When built, the flow is: scan an unknown barcode →
   "link this to a product" → product picker → `ProductBarcode` row. This belongs
   next to product management, not stock items.
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

- Should the "Scan" tab exist under Data → Scanning at all, or only on Stock
  Overview? (Feedback flags it as possibly redundant here.) Leaning: keep Data →
  Scan as the "print labels" home; move the *action-oriented* scan to Stock
  Overview where context exists.
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
