import {
    LOW_STOCK_SEQUENCE,
    OUT_OF_STOCK_SEQUENCE,
    STOCKED_SEQUENCE,
} from 'src/helpers/stockStatus';
import type { ThemePalette } from 'src/services/themeService';
import nameOf from './nameOf';

// D-001 (DESIGN_STYLE_GUIDE) — level colour escalates with urgency:
// Stocked = positive (green), Low = warning (amber), Out of stock =
// negative (red). Grey/muted is reserved for "unknown / not-set" ONLY and
// must never stand for a real level — the pre-DR-2 map had Out rendering
// grey (calmer than Low's red) and Low rendering red, which read backwards
// (FU-578 #33). Only genuinely-unknown sequences fall through to `null`,
// where callers apply the neutral theme token (`dora-bg-neutral` /
// `dora-text-muted`) rather than a Quasar `grey-N` literal (R-002). The
// saturated branches ride Quasar semantics — those are theme-stable.
const COLOUR_BY_SEQUENCE: Record<number, string | null> = {
    [STOCKED_SEQUENCE]: nameOf<ThemePalette>('positive'),
    [LOW_STOCK_SEQUENCE]: nameOf<ThemePalette>('warning'),
    [OUT_OF_STOCK_SEQUENCE]: nameOf<ThemePalette>('negative'),
};

/** Canonical colour — keyed to the level's sequence so renaming a level
 *  doesn't change its colour. The legacy name-keyed `getStockLevelColour`
 *  was retired in FU-050; every caller now routes through this
 *  sequence-keyed entry point.
 *
 *  Returns `null` only for the unknown / not-set case (a missing sequence
 *  or a custom level beyond the seeded three) so the caller can apply
 *  `dora-text-muted` / `dora-bg-sunken` instead of a hardcoded grey palette
 *  literal (R-002). Out-of-stock is a *real* level and now maps to red
 *  (negative) per D-001 — it no longer routes through this null branch. */
export function colourForSequence(sequence: number | null | undefined): string | null {
    if (sequence === null || sequence === undefined) return null;
    return COLOUR_BY_SEQUENCE[sequence] ?? null;
}
