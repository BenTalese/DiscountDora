export type LinkedProduct = {
    product_id: string;
    name: string;
    brand: string | null;
    merchant_id: string;
    merchant_name: string;
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
    position: number;
};

// FU-213 — everyday "what this cost me" price points. Money-gated at the UI.
export type PriceObservation = {
    observation_id: string;
    price: number;
    qty: number;
    unit: string;
    observed_at: string; // ISO datetime
    source: string;
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
