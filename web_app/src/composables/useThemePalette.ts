import { computed, ref } from 'vue';

/**
 * FU-824 — a reactive read of the *live* theme's CSS custom properties.
 *
 * ## The bug this exists to fix
 *
 * Some surfaces can't express a colour in CSS — an SVG `stroke`, a canvas
 * series, a chart palette — so they read the token off the document with
 * `getComputedStyle(document.documentElement).getPropertyValue('--x')`. That
 * read is correct, and it is **not reactive**: `getComputedStyle` is a plain DOM
 * call, so a `computed()` wrapping it registers no dependency on the theme and
 * never re-evaluates when the theme changes. The value is sampled once and
 * frozen.
 *
 * Three surfaces had independently hit this, and two of them shipped a comment
 * claiming behaviour they did not have:
 *
 *  - `DashboardPage.vue`'s stock donut — *"Read the semantic-* tokens off the
 *    document so the donut recolours when the user switches theme without a full
 *    reload."* It does not; the computed's only dependencies are the summary and
 *    two route links.
 *  - `ReportsPage.vue`'s `chartPalette` — someone recognised the problem and
 *    added a `themeTick` ref to invalidate it, then never incremented it
 *    anywhere. Dead state advertising a fix.
 *  - `usePriceHistoryPalette.seriesColour` — the same one-shot read, no
 *    invalidation.
 *
 * ## How this works
 *
 * `themeService.applyThemeKey()` is the single place that writes
 * `data-theme` on `<html>`, so it calls `notifyThemeChanged()` right after —
 * one explicit notification rather than a MutationObserver watching for it
 * (R-019: no magic). Reading a token through `paletteToken()` touches the
 * version ref first, so any `computed()` that calls it gains a dependency on the
 * theme and re-evaluates on the next switch.
 *
 * R-003: this is the one place the app converts "a token name" into "the colour
 * it currently resolves to". Don't add a fourth private copy.
 */

/** Bumped on every theme application. Exported read-only via the composable. */
const themeVersion = ref(0);

/**
 * Tell the palette layer the theme changed. Called by
 * `themeService.applyThemeKey` immediately after `data-theme` is written and
 * Quasar's palette is resynced — at which point the new custom properties are
 * live and a read returns the new values.
 */
export function notifyThemeChanged(): void {
    themeVersion.value += 1;
}

/**
 * Resolve a CSS custom property against the live theme.
 *
 * Call this **inside** a `computed()` (or a render function) so the version
 * dependency is registered — that is what makes the result recolour on a theme
 * switch. Outside a reactive scope it still returns the right value, it just
 * won't invalidate.
 *
 * `fallback` covers SSR/no-document and a genuinely absent token. Per R-060 a
 * token you reference should exist, so a fallback here is a safety net, not a
 * licence to invent token names.
 */
export function paletteToken(name: string, fallback = ''): string {
    // Register the dependency BEFORE the DOM read, so the read is what gets
    // re-run when the theme changes.
    void themeVersion.value;
    if (typeof document === 'undefined' || typeof window === 'undefined') {
        return fallback;
    }
    const value = window
        .getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim();
    return value || fallback;
}

/** Resolve several tokens at once — the common case for a chart series or a
 *  multi-segment SVG. Same reactivity rules as `paletteToken`. */
export function paletteTokens(names: string[], fallbacks: string[] = []): string[] {
    return names.map((name, i) => paletteToken(name, fallbacks[i] ?? ''));
}

export function useThemePalette() {
    return {
        /** Increments on each theme application. Depend on this directly if you
         *  need to invalidate something `paletteToken` doesn't cover. */
        themeVersion: computed(() => themeVersion.value),
        paletteToken,
        paletteTokens,
    };
}
