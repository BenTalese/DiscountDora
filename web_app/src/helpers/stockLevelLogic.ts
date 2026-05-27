import type { StockLevelName } from 'src/models/stockLevel';
import type { ThemePalette } from 'src/services/themeService';
import nameOf from './nameOf';

export function getStockLevelColour(stockLevelName: StockLevelName) {
    const stockLevelColourByName: Record<StockLevelName, string> = {
        'Well-Stocked': nameOf<ThemePalette>('positive'),
        'Sufficient Stock': nameOf<ThemePalette>('warning'),
        'Low Stock': nameOf<ThemePalette>('negative'),
        'Out of Stock': 'grey' // TODO: Define and use theme colour
    };

    const stockLevelColour = stockLevelColourByName[stockLevelName];

    if (!stockLevelColour) {
        console.error(`Colour not configured for stock level '${stockLevelName}'.`);
    }

    return stockLevelColour;
}
