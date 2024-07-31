export type StockItem = {
    name: string;
    product_ids: string[]
    stock_group_id: string | null;
    stock_item_id: string;
    stock_level_id: string;
    stock_location_id: string | null;
}
