import {
    LOW_STOCK_SEQUENCE,
    OUT_OF_STOCK_SEQUENCE,
    STOCKED_SEQUENCE,
} from 'src/helpers/stockStatus';
import type { ThemePalette } from 'src/services/themeService';
import nameOf from './nameOf';

// "Out of stock" / unknown returns `null` so callers route the neutral
// branch through the theme-token classes (`dora-bg-sunken` /
// `dora-text-muted`) per R-002, rather than a Quasar `grey-N` literal
// that breaks dark themes. The saturated branches stay on Quasar
// semantics — those are theme-stable.
const COLOUR_BY_SEQUENCE: Record<number, string | null> = {
    [STOCKED_SEQUENCE]: nameOf<ThemePalette>('positive'),
    [LOW_STOCK_SEQUENCE]: nameOf<ThemePalette>('negative'),
    [OUT_OF_STOCK_SEQUENCE]: null,
};

/** Canonical colour — keyed to the level's sequence so renaming a level
 *  doesn't change its colour. The legacy name-keyed `getStockLevelColour`
 *  was retired in FU-050; every caller now routes through this
 *  sequence-keyed entry point.
 *
 *  Returns `null` for the neutral / out-of-stock / unknown case so the
 *  caller can apply `dora-text-muted` / `dora-bg-sunken` instead of a
 *  hardcoded grey palette literal (R-002). */
export function colourForSequence(sequence: number | null | undefined): string | null {
    if (sequence === null || sequence === undefined) return null;
    return COLOUR_BY_SEQUENCE[sequence] ?? null;
}
