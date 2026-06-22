export type LinkedProduct = {
    product_id: string;
    name: string;
    brand: string | null;
    store_id: string;
    store_name: string;
    /** FU-189 carve-out: producer's SKU code, retained verbatim. */
    merchant_stockcode: string | null;
    size: string | null;
    web_url: string | null;
    price_now: number | null;
    price_was: number | null;
};

export type LinkedRecipe = {
    recipe_id: string;
    name: string;
};

export type Substitute = {
    stock_item_id: string;
    name: string;
    stock_level_id: string | null;
    stock_level_name: string | null;
};

export type LevelChange = {
    changed_at: string; // ISO datetime
    stock_level_id: string | null;
    stock_level_name: string | null;
};

// C-1b.5 / INV-7 — lifecycle timeline inputs. The History tab merges
// these with `level_history` (and synthesises Opened/Checked rows from
// current state) into a single date-sorted q-timeline.
export type WasteEvent = {
    occurred_at: string; // ISO datetime
    reason: string;
    quantity: number | null;
    estimated_value: number | null;
    note: string | null;
};

export type ListAddEvent = {
    added_at: string; // ISO datetime
    added_via: string;
    shopping_list_id: string;
    shopping_list_name: string;
};

// FU-211 — free-text "what I actually buy" reminders on a stock item
// (PROPOSAL_PRODUCTS_AS_OVERLAY §3.1). Everyday-user construct, separate from
// the Product overlay; always present, never gated.
export type PreferredBuy = {
    preferred_buy_id: string;
    label: string;
};

// FU-227 chunk 2 — folded shape (A1). Money-gated at the UI. Per-unit cost
// derived server-side (R-003) — client never divides total_price by total_measure.
// `store_name` populated when a store was attached at entry (A2). When the row
// was harvested from a finished shopping line at /finish (chunk 5),
// `shopping_list_line_id` + `shopping_list_name` carry the provenance label
// ("from Wed's shopping list"); both null for manual entries.
export type PriceObservation = {
    observation_id: string;
    total_price: number;
    total_measure: number;
    unit: string;
    observed_at: string; // ISO datetime
    store_id: string | null;
    store_name: string | null;
    shopping_list_line_id: string | null;
    shopping_list_name: string | null;
};

// FU-227 chunk 3 — what the PriceEntry widget seeds itself with on open (F2).
// Resolved server-side so the source_label stays consistent. Null when no
// prior observation exists for the item.
export type PriceEntryPrefill = {
    total_price: number;
    total_measure: number;
    unit: string;
    store_id: string | null;
    store_name: string | null;
    /** Short human chip ("from your last log" / "from your last receipt"). */
    source_label: string;
};

// FU-227 chunk 4 — server-derived baseline + signal (R-003). The widget
// reads booleans / numbers and renders; never re-computes. `offers_sidecar`
// (LC-2) is a separate UI region — never folded into the median or count.
export type OfferSidecar = {
    store_name: string;
    price_per_unit: number;
    unit: string;
};

export type YourPrices = {
    baseline: number | null;
    baseline_unit: string | null;
    current: number | null;
    above_baseline: boolean;
    sample_count: number;
    last_observed_at: string | null; // ISO datetime
    last_seen_store_name: string | null;
    offers_sidecar: OfferSidecar[];
};

import type { AttentionReasons } from 'src/models/location';

export type StockItemDetail = {
    stock_item_id: string;
    name: string;
    notes: string | null;
    days_until_stocktake_alert: number;
    stocktake_alerts_are_enabled: boolean;
    stock_level_id: string | null;
    stock_level_name: string | null;
    stock_location_id: string | null;
    stock_location_name: string | null;
    stock_location_breadcrumb: string[];
    stock_group_id: string | null;
    stock_group_name: string | null;
    stock_level_last_updated: string; // ISO datetime
    expiry_date: string | null;
    is_open: boolean;
    opened_on: string | null;
    is_flagged: boolean;
    auto_add_when_low: boolean;
    /** FU-189 — usual store hint (nullable). Drives the shopping-list
     *  grouping + a small picker on the stock-item detail. */
    usual_store_id: string | null;
    usual_store_name: string | null;
    /** FU-125 — true only when the user has uploaded their own image (no
     *  product-fallback). Drives whether the image field reads "Add" /
     *  "Change + Remove" — a fallback preview shouldn't show Remove. */
    has_own_image?: boolean;
    attention_score: number;
    attention_reasons: AttentionReasons;
    products: LinkedProduct[];
    recipes: LinkedRecipe[];
    substitutes: Substitute[];
    level_history: LevelChange[];
    /** C-1b.5 / INV-7 — append-only waste log entries for this item,
     *  newest first, capped on the server. Empty when nothing thrown
     *  out (the common case). */
    waste_events?: WasteEvent[];
    /** C-1b.5 / INV-7 — past shopping-list adds for this item (any list
     *  status), newest first, capped on the server. The History tab
     *  humanises `added_via` ("auto: low stock" / "auto: recipe" / …). */
    recent_list_adds?: ListAddEvent[];
    /** FU-211 — free-text "what I buy" reminders, ordered by position.
     *  Always present (not gated by products/money). */
    preferred_buys?: PreferredBuy[];
    /** FU-213 — price observations (newest first) + the server-derived
     *  per-unit cost. Money-gated at the UI. */
    price_observations?: PriceObservation[];
    unit_cost?: number | null;
    /** FU-227 chunk 3 — what the PriceEntry widget should seed itself with
     *  on open (F2). Null when no prior observation exists for this item. */
    price_entry_prefill?: PriceEntryPrefill | null;
    /** FU-227 chunk 3 placeholder — chunk 4 lights it up with the real
     *  baseline/threshold output. Until then the widget renders the
     *  empty state. */
    your_prices?: YourPrices | null;
    /** X1 — last "still correct" check; surfaced in the lifecycle
     *  timeline as a synthetic Checked entry when it differs from the
     *  most recent level change. Null = never checked. */
    last_checked_at?: string | null;
    /** C-1 Chunk 6 / FU-033 — true when the item has its own image OR a
     *  linked product carries one. Bytes served via
     *  `GET /stock-items/<id>/image`. */
    has_image?: boolean;
};

export type PricePoint = {
    offered_on: string; // ISO datetime
    price_now: number | null;
    price_was: number | null;
};

export type PriceHistory = {
    product_id: string;
    points: PricePoint[];
};
