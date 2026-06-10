export type StockLevel = {
    /** Display name — user-renameable. Never compare against literals like
     *  "Out of Stock"; key off `sequence` via `helpers/stockStatus.ts`. */
    name: string;
    sequence: number;
    stock_level_id: string;
};
