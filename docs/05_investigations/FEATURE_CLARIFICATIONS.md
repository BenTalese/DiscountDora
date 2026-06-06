# FEATURE_CLARIFICATIONS — INV-5

**Date:** 2026-06-06  
**Type:** Read-only investigation. No code changes.  
**Purpose:** Clarify three "how does this work / is it redundant?" questions:
(a) QR vs register-barcode vs print, (b) product-search relevancy ranking,
(c) the expiry↔open relationship.

---

## (a) "Show QR" vs "Register barcode" vs "Print QR" — distinct or redundant?

**They are two distinct features, not three, and not redundant.** Both are
navigation/labelling aids; neither is the removed "barcodes for deal lookup."

### Feature 1 — Dora's own per-item QR (show + print)
- **Show QR** (`StockItemDetailPage.vue:55`, dialog ~66-90) renders a generated
  QR encoding `dora://stock-item/<uuid>` from `GET /api/stock-items/<id>/qr`
  (`features/data/barcodes.py:123-141`).
- **Print one** is a sub-action *inside* that dialog → opens
  `GET /api/stock-items/qr/sheet?ids=<id>` (label-sheet templates, Avery 5160 /
  A4 21-up, `barcodes.py:146-274`).
- So "Show QR" and "Print" are **one feature** (Dora's own labels). Per the
  charter these QR labels are **kept but off by default**.

### Feature 2 — Register a real-world barcode (scan-to-jump)
- **Register barcode** (`StockItemDetailPage.vue:56-61`) opens a camera scan and
  `POST`s the scanned value into `StockItem.barcode`
  (`barcodes.py:284-320`, dup → 409).
- Its only consumer is `GET /api/barcodes/lookup?value=…`
  (`barcodes.py:350-401`), which resolves a scanned code to a **stock item to
  jump to** (`{"kind":"stock_item","id":…}`). It does **not** look up deals or
  prices.
- **Important distinction:** the removed P6-02 feature was *real-world barcodes
  for **deal lookup***. This scan-to-jump navigation aid is a different thing and
  is not what was cut. (The lookup also has a step-3 `ProductBarcode` branch,
  which *is* legacy from the removed path and resolves identity, not offers.)

### Recommendation: **CLARIFY (keep both)**
- They aren't redundant — one prints labels you scan to open an item, the other
  registers an existing product barcode to open the same item. Both are
  scan-to-open aids.
- The confusion is **labelling**, not overlap. Suggest: group both under one
  "Labels & scanning" area on the detail page; rename "Print one" → "Print
  label". Keep both behind the off-by-default QR/scanning preference.
- Leave the dead `ProductBarcode` step-3 branch alone here; it's part of the
  already-tracked P6-02 removal, not this investigation's scope.

---

## (b) Product-search "relevancy" ranking — how it ranks, does it work?

### What it does today
- `features/products/.../search_for_product.py:66-70` scores each offer name with
  `get_similarity_score(offer.name, term, threshold=70)` and sorts descending.
- `similarity.py:4-17`: token-overlap on `fuzzywuzzy.fuzz.ratio` — splits both
  strings into lowercase words, compares each word pair, sums the scores of pairs
  that clear 70%.
- Frontend (`ProductSearch.vue:76-128`) adds **post-search filters** (price, unit
  price, size, in-stock, specials, half-price) but **no re-rank control** — the
  server order is final.

### Assessment
Simple, transparent, predictable. Works for literal word matches and typos
("tomatoe"≈"tomato"). Weaknesses: no synonyms ("butter"↔"margarine"), no token
weighting ("olive oil" vs "oil soap"), word-order-insensitive, no
merchant-preference tie-break, threshold hardcoded at 70.

### Recommendation: **KEEP + DOCUMENT**
No urgent change. Add a one-line help affordance ("ranked by word overlap; try
other terms"). Defer real improvements (merchant-preference tie-break, sort-by-
price toggle) until user feedback says results are actually bad — this surface is
also moving toward the companion app, so don't over-invest.

---

## (c) Expiry ↔ open — do they affect each other?

### What it does today: **fully independent. No derivation.**
- `expiry_date` is user-set via "Set expiry" (`StockItemDetailPage.vue:51`,
  dialog ~431-441); copied as-is on create (`create_stock_item.py:92`).
- `is_open` / `opened_on`: toggling `is_open` False→True **auto-sets**
  `opened_on=today`; flipping back clears it (`update_stock_item.py:156-163`);
  `opened_on` is also manually editable (165-166).
- There is **no** cross-field logic — opening does not shift expiry, and expiry
  does not affect open state. No "use within N days of opening" computation
  exists anywhere.

### Recommendation: **KEEP independent + add a one-line clarification**
The design is intentional and correct: `expiry_date` = the package's sealed
shelf-life; `opened_on` = consumption metadata the user reads with their own
judgement. Add a short tooltip saying they're independent (and that Dora doesn't
auto-expire after opening). Only if a "use-by-after-opening" rule is ever
requested would you add a derived field — out of scope now.

---

## Summary

| Question | Verdict |
|---|---|
| (a) QR / register-barcode / print | Two distinct kept features (own-QR show+print; real-world-barcode scan-to-jump). **Clarify labels**; not redundant; not the removed deal-lookup. |
| (b) Relevancy ranking | Naive token-overlap fuzzy match. **Keep + document**; defer improvements. |
| (c) Expiry ↔ open | Fully independent by design. **Keep**; add a clarifying tooltip. |

---

## Feedback coverage

| User-flagged item | Finding |
|---|---|
| QR vs barcode vs print — redundant? | Not redundant: own-QR (show+print) and real-world-barcode (scan-to-jump) are distinct aids. Clarify labelling. |
| Relevancy filter — how/does it work? | Token-overlap fuzzy (fuzzywuzzy ratio, threshold 70), final server sort, post-filters on top. Transparent but naive; keep + document. |
| Expiry ↔ open relationship | Independent; `opened_on` auto-set on open, no expiry derivation. Keep + add tooltip. |
