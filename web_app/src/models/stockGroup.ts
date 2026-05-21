export type StockGroup = {
    stock_group_id: string;
    name: string;
    // Convenience count rolled up on the backend list endpoint. Detail
    // / per-item references don't carry this — leave the field missing
    // when constructed locally.
    item_count?: number;
};
