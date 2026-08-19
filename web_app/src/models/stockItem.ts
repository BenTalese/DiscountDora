export type StockItem = {
    name: string;
    stock_group_id: string | null;
    stock_item_id: string;
    stock_level_id: string;
    stock_location_id: string | null;
    expiry_date?: string | null;
    is_essential?: boolean;
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
    /** Server-owned attention (Chunk 3b, `stock_attention.py`). The single
     *  rule behind the row outline, the "Needs attention" chip + count, and
     *  the bell's per-item kinds. **Do not re-derive any of this client-side**
     *  — the copy that used to live in `useStockFilters.hasAlert` disagreed
     *  with the server in four separate ways (B1–B4 in the impl plan).
     *  `attention_severity` orders the outlined band; `attention_kinds` says
     *  which conditions fired, for chips that narrow to one of them. */
    needs_attention?: boolean;
    attention_severity?: 'high' | 'medium' | 'low' | null;
    attention_kinds?: readonly string[];
    /** C-7 Chunk 2 — count of linked products. Drives the combined
     *  modal decision in `AddToListButton`: 2+ → open QuickAddSheet
     *  (one combined surface) instead of stacking two prompts. */
    linked_product_count?: number;
};
