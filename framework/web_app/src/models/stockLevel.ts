export type StockLevelName = 'Well-Stocked' | 'Sufficient Stock' | 'Low Stock' | 'Out of Stock';

export type StockLevel = {
    name: StockLevelName;
    sequence: number;
    stock_level_id: string;
};
