/**
 * Shared 5-colour palette for the Price History Explorer (N8).
 *
 * Both `PriceHistoryChart.vue` and `PriceHistoryPage.vue` need the same
 * colour for each series so the chip in the picker, the polyline on the
 * chart, and the swatch on the comparison card all match. Index is the
 * series' position in the selection (stable for the duration of the
 * picker session); colours wrap if a future bump raises the per-page
 * cap above 5.
 *
 * Colours come from the active theme via `--chart-1` … `--chart-5`. The
 * hex fallbacks match the Pesto defaults so a server-render / pre-paint
 * call still returns a sensible colour.
 *
 * FU-824 — the token read goes through `paletteToken`, which registers a
 * dependency on the theme version. This was the **third** copy of the same
 * one-shot `getComputedStyle` read (with the dashboard donut and Reports'
 * `chartPalette`): correct on first paint, frozen thereafter, so a theme switch
 * left the chart on the old theme's hues. Callers still need to be inside a
 * reactive scope for the invalidation to reach them.
 */
import { paletteToken } from 'src/composables/useThemePalette';

const CHART_TOKEN_FALLBACKS: readonly string[] = [
    'hsl(150, 76%, 39%)', // --chart-1 (primary)
    'hsl(189, 100%, 32%)', // --chart-2 (secondary)
    'hsl(50, 95%, 50%)',  // --chart-3 (accent)
    'hsl(20, 85%, 60%)',  // --chart-4 (warm tertiary)
    'hsl(280, 50%, 58%)', // --chart-5 (cool tertiary)
];

function readVar(index: number): string {
    return paletteToken(`--chart-${index + 1}`, CHART_TOKEN_FALLBACKS[index]);
}

export function seriesColour(index: number): string {
    return readVar(index % CHART_TOKEN_FALLBACKS.length);
}

export function paletteSnapshot(): readonly string[] {
    return CHART_TOKEN_FALLBACKS.map((_, i) => readVar(i));
}
