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
