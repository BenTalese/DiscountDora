import {
    LOW_STOCK_SEQUENCE,
    OUT_OF_STOCK_SEQUENCE,
    SUFFICIENT_STOCK_SEQUENCE,
    WELL_STOCKED_SEQUENCE,
} from 'src/helpers/stockStatus';
import type { ThemePalette } from 'src/services/themeService';
import nameOf from './nameOf';

// "Out of stock" reads as a mid-grey (`grey-5` / `#9e9e9e`) — depleted but
// not so light it disappears. (Round 11 briefly bumped to grey-4 to
// compensate for a CSS-variable bug that mis-rendered the swatch as
// near-black; round 12 fixed the root cause — `var(--q-grey-5)` doesn't
// exist, the row level button now uses Quasar's `bg-grey-5` utility class
// instead. Once the swatch rendered correctly, grey-4 read too light.)
const COLOUR_BY_SEQUENCE: Record<number, string> = {
    [WELL_STOCKED_SEQUENCE]: nameOf<ThemePalette>('positive'),
    [SUFFICIENT_STOCK_SEQUENCE]: nameOf<ThemePalette>('warning'),
    [LOW_STOCK_SEQUENCE]: nameOf<ThemePalette>('negative'),
    [OUT_OF_STOCK_SEQUENCE]: 'grey-5',
};

/** Canonical colour — keyed to the level's sequence so renaming a level
 *  doesn't change its colour. Prefer this over `getStockLevelColour`. */
export function colourForSequence(sequence: number | null | undefined): string {
    if (sequence === null || sequence === undefined) return 'grey-5';
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
        default: return 'grey-5';
    }
}
