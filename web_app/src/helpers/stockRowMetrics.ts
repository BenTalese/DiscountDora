/**
 * Stock-overview row geometry — the single source for "how tall is a row".
 *
 * The overview's virtualised branch needs an exact `virtual-scroll-item-size`;
 * when the number it's given disagrees with the rendered height, Quasar
 * re-measures mid-scroll and re-pads the spacer, which reads to the user as
 * the list snapping to a point rather than gliding (2026-08-15 feedback).
 * Fixing that means the row must be a *fixed* height, not a min-height, and
 * the number must live in exactly one place — here. The page binds it to the
 * list as a CSS custom property (`--stock-row-height`) and hands the same
 * value to `q-virtual-scroll`, so the two can never drift.
 *
 * Two values because phones let the item name wrap to two lines (DR-9), which
 * genuinely needs the extra room; every row within a breakpoint is uniform.
 * Both include the row's 8px bottom gap.
 */
export const STOCK_ROW_HEIGHT_DESKTOP = 64;
export const STOCK_ROW_HEIGHT_MOBILE = 76;
