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
    // Optional registered barcode (N5). Surfaces in
    // Data → Barcodes & QR · Manage and is matched by /api/barcodes/lookup.
    barcode?: string | null;
    // Server-side level name — surfaced by get_stock_items so the print-sheet
    // labels can show "Low Stock" without a join lookup on the client.
    stock_level_name?: string | null;
};
