export type StockItem = {
    name: string;
    //Readonly(x) is shallow. There is no built in deep readonly, will need a custom type to achieve this.
    product_ids: readonly string[]
    stock_group_id: string | null;
    stock_item_id: string;
    stock_level_id: string;
    stock_location_id: string | null;
}
