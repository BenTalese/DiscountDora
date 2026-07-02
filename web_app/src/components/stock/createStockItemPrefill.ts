/** P8-02 — optional scan-driven prefill for `CreateStockItemDialog`.
 *
 *  Extracted from the SFC so page-level callers (StockOverview) can
 *  import it under ESLint's TS resolver, which does not always trace
 *  named exports across `.vue` boundaries.
 *
 *  `source` distinguishes where the prefill came from so the banner
 *  copy stays honest:
 *  - `'off'`             — Open Food Facts hit (name / image seeded)
 *  - `'product_no_link'` — EAN matched a Product with no linked
 *                          stock item; user's own Product data wins
 *                          over an open-data suggestion, so no OFF
 *                          call was made
 *  - `'unknown'`         — OFF miss + no product; barcode-only
 *                          prefill so the user still gets one-tap
 *                          confirm-add + EAN registration
 *
 *  When `barcode` is set on submit, the dialog also POSTs
 *  `/data/barcodes` to link the EAN to the new stock item.
 *
 *  Fields use `T | undefined` (not just `T?`) so callers can spread
 *  the result of an OFF lookup without extra narrowing under
 *  `exactOptionalPropertyTypes: true`.
 */
export interface CreateStockItemPrefill {
    name?: string | undefined;
    barcode?: string | undefined;
    imageUrl?: string | undefined;
    brand?: string | undefined;
    quantity?: string | undefined;
    categories?: string | undefined;
    source?: 'off' | 'product_no_link' | 'unknown' | undefined;
}
