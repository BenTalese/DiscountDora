export type StockItem = {
    name: string;
    stock_group_id: string | null;
    stock_item_id: string;
    stock_level_id: string;
    stock_location_id: string | null;
    expiry_date?: string | null;
    is_flagged?: boolean;
    auto_add_when_low?: boolean;
    is_open?: boolean;
    opened_on?: string | null;
    stock_level_last_updated?: string | null;
    // Server-side level name — surfaced by get_stock_items so the print-sheet
    // labels can show "Low Stock" without a join lookup on the client.
    stock_level_name?: string | null;
    // Server-derived stock status (§3.1 contract). The client reads these
    // instead of matching `stock_level_name` against "Out of Stock" / "Low Stock".
    stock_level_sequence?: number | null;
    is_out_of_stock?: boolean;
    is_low_stock?: boolean;
    needs_restock?: boolean;
};
