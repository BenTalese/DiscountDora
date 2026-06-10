import {
    LOW_STOCK_SEQUENCE,
    OUT_OF_STOCK_SEQUENCE,
    SUFFICIENT_STOCK_SEQUENCE,
    WELL_STOCKED_SEQUENCE,
} from 'src/helpers/stockStatus';
import type { ThemePalette } from 'src/services/themeService';
import nameOf from './nameOf';

const COLOUR_BY_SEQUENCE: Record<number, string> = {
    [WELL_STOCKED_SEQUENCE]: nameOf<ThemePalette>('positive'),
    [SUFFICIENT_STOCK_SEQUENCE]: nameOf<ThemePalette>('warning'),
    [LOW_STOCK_SEQUENCE]: nameOf<ThemePalette>('negative'),
    [OUT_OF_STOCK_SEQUENCE]: 'grey',
};

/** Canonical colour — keyed to the level's sequence so renaming a level
 *  doesn't change its colour. Prefer this over `getStockLevelColour`. */
export function colourForSequence(sequence: number | null | undefined): string {
    if (sequence === null || sequence === undefined) return 'grey';
    return COLOUR_BY_SEQUENCE[sequence] ?? COLOUR_BY_SEQUENCE[OUT_OF_STOCK_SEQUENCE]!;
}

/** Legacy name-keyed colour — kept so existing callers compile while the
 *  surface-by-surface Chunk 4 sweep migrates them to `colourForSequence`.
 *  Falls back to grey for unknown / custom-renamed levels instead of
 *  console-erroring (renaming a level is now legal). */
export function getStockLevelColour(stockLevelName: string | null | undefined): string {
    switch (stockLevelName) {
        case 'Well-Stocked': return COLOUR_BY_SEQUENCE[WELL_STOCKED_SEQUENCE]!;
        case 'Sufficient Stock': return COLOUR_BY_SEQUENCE[SUFFICIENT_STOCK_SEQUENCE]!;
        case 'Low Stock': return COLOUR_BY_SEQUENCE[LOW_STOCK_SEQUENCE]!;
        case 'Out of Stock': return COLOUR_BY_SEQUENCE[OUT_OF_STOCK_SEQUENCE]!;
        default: return 'grey';
    }
}
