/**
 * Shared 5-colour palette for the Price History Explorer (N8).
 *
 * Both `PriceHistoryChart.vue` and `PriceHistoryPage.vue` need the same
 * colour for each series so the chip in the picker, the polyline on the
 * chart, and the swatch on the comparison card all match. Index is the
 * series' position in the selection (stable for the duration of the
 * picker session); colours wrap if a future bump raises the per-page
 * cap above 5.
 */
const PALETTE: readonly string[] = [
    '#1e88e5', // blue
    '#43a047', // green
    '#ef5350', // red
    '#ab47bc', // purple
    '#fb8c00', // orange
];

export function seriesColour(index: number): string {
    return PALETTE[index % PALETTE.length]!;
}

export function paletteSnapshot(): readonly string[] {
    return PALETTE;
}
