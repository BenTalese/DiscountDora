/*
Notes for later:
    - If i export interface from here, i get an ambigious export error
    - If i then move the interface to StockItemApiService.ts, i no longer get the error
    - Exporting as type or class instead from here does not have the issue either
    - If i export interface from here, but then duplicate the interface in the .vue file i don't get the error
*/

export type StockItem = {
    name: string;
    stock_item_id: string;
    stock_level_id: string;
    stock_location_id: string | null;
}

export type CreateStockItemCommand = {
    name: string;
    stock_level_id: string;
    stock_location_id: string | null;
}
