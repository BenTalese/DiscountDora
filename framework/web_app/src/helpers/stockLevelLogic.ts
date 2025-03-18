import type { StockLevelName } from 'src/models/stockLevel';
import type { Theme } from 'src/services/themeService';
import nameOf from './nameOf';

export function getStockLevelColour(stockLevelName: StockLevelName) {
    const stockLevelColourByName: Record<StockLevelName, string> = {
        'Well-Stocked': nameOf<Theme>('positive'),
        'Sufficient Stock': nameOf<Theme>('warning'),
        'Low Stock': nameOf<Theme>('negative'),
        'Out of Stock': 'grey'
    };

    const stockLevelColour = stockLevelColourByName[stockLevelName];

    if (!stockLevelColour) {
        console.error(`Colour not configured for stock level '${stockLevelName}'.`);
    }

    return stockLevelColour;
}
