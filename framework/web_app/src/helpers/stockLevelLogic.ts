import { StockLevelName } from "src/models/StockLevel";

export function getStockLevelColour(stockLevelName: StockLevelName) {
    const stockLevelColourByName: Record<StockLevelName, string> = {
        'Well-Stocked': 'green',
        'Sufficient Stock': 'yellow',
        'Low Stock': 'red',
        'Out of Stock': 'grey'
    };

    const stockLevelColour = stockLevelColourByName[stockLevelName]

    if (!stockLevelColour) {
        console.error(`Colour not configured for stock level '${stockLevelName}'.`)
    }

    return stockLevelColour
}
