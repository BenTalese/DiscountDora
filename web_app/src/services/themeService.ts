import { Dark, setCssVar } from 'quasar';
import type {
    FontFamilyPreference,
    FontSizePreference,
    ThemePreference,
} from 'src/models/auth';

/*
 * DS1 — Themed palettes.
 *
 * Two things happen on theme apply:
 *   1. `document.documentElement.setAttribute('data-theme', name)` —
 *      drives the semantic CSS tokens declared in css/themes.scss.
 *   2. `setCssVar(...)` per Quasar palette key — keeps Quasar's own
 *      component palette ($primary etc.) in sync so q-btn, q-chip,
 *      q-banner et al. honour the active theme without per-call
 *      colour overrides.
 *
 * Adding a new theme is a 2-step change: append a `[data-theme="x"]`
 * block to themes.scss + a row to THEMES below. The fun-name catalogue
 * is the source of truth for the Preferences picker UI.
 */

export interface ThemePalette {
    primary: string;
    secondary: string;
    accent: string;
    page: string;
    component: string;
    positive: string;
    negative: string;
    info: string;
    warning: string;
    text: string;
    disabled: string;
    border: string;
    divider: string;
    focus: string;
}

export interface ThemeOption {
    /** key persisted on User.theme + sent over the wire. */
    key: ThemePreference;
    /** Fun display name shown in the preference picker. */
    label: string;
    /** Short description shown under the label. */
    blurb: string;
    /** One-line preview swatch hex strip (3 hexes) for the picker UI. */
    swatch: [string, string, string];
    /** Quasar palette values applied at runtime via setCssVar. */
    palette: ThemePalette;
    /** Whether Quasar's Dark.set() should be flipped on for this theme. */
    isDark: boolean;
}

// Resolved palette values per theme. These mirror the semantic CSS
// custom properties in css/themes.scss — keep them in sync if you
// change one, otherwise the SPA looks two-toned.
export const THEMES: Record<string, ThemeOption> = {
    // ───────── Pesto family ─────────────────────────────────────────
    'pesto': {
        key: 'pesto', label: 'Pesto',
        blurb: 'Fresh garden green + teal with a golden accent.',
        swatch: ['hsl(150,76%,39%)', 'hsl(189,100%,26%)', 'hsl(50,99%,56%)'],
        palette: {
            primary: 'hsl(150, 60%, 36%)', secondary: 'hsl(189, 100%, 26%)', accent: 'hsl(50, 99%, 56%)',
            page: 'hsl(168, 38%, 94%)', component: 'hsl(0, 0%, 100%)',
            positive: 'hsl(140, 50%, 45%)', negative: 'hsl(7, 75%, 56%)',
            info: 'hsl(218, 76%, 56%)', warning: 'hsl(33, 95%, 55%)',
            text: 'hsl(168, 28%, 12%)', disabled: 'hsl(168, 10%, 42%)',
            border: 'hsl(168, 18%, 84%)', divider: 'hsl(168, 14%, 86%)', focus: 'hsl(150, 60%, 36%)',
        },
        isDark: false,
    },
    'pesto-dark': {
        key: 'pesto-dark', label: 'Pesto Dark',
        blurb: 'Garden after midnight — forest teal with bright lime pop.',
        swatch: ['hsl(150,75%,55%)', 'hsl(170,28%,30%)', 'hsl(225,100%,93%)'],
        palette: {
            primary: 'hsl(150, 48%, 40%)', secondary: 'hsl(170, 28%, 30%)', accent: 'hsl(150, 48%, 40%)',
            page: 'hsl(165, 60%, 5%)', component: 'hsl(170, 28%, 12%)',
            positive: 'hsl(150, 48%, 40%)', negative: 'hsl(7, 78%, 65%)',
            info: 'hsl(218, 80%, 70%)', warning: 'hsl(33, 95%, 65%)',
            text: 'hsl(225, 100%, 93%)', disabled: 'hsl(205, 12%, 66%)',
            border: 'hsl(205, 12%, 28%)', divider: 'hsl(205, 12%, 24%)', focus: 'hsl(150, 48%, 40%)',
        },
        isDark: true,
    },

    // ───────── Lemon Tart family ────────────────────────────────────
    'lemon-tart': {
        key: 'lemon-tart', label: 'Lemon Tart',
        blurb: 'Warm yellow on cream — the original Dora vibe.',
        swatch: ['hsl(40,88%,67%)', 'hsl(189,100%,26%)', 'hsl(48,99%,56%)'],
        palette: {
            primary: 'hsl(40, 88%, 67%)', secondary: 'hsl(189, 100%, 26%)', accent: 'hsl(48, 99%, 56%)',
            page: 'hsl(40, 33%, 96%)', component: 'hsl(0, 0%, 100%)',
            positive: 'hsl(140, 50%, 45%)', negative: 'hsl(7, 75%, 56%)',
            info: 'hsl(218, 76%, 56%)', warning: 'hsl(33, 95%, 55%)',
            text: 'hsl(28, 26%, 14%)', disabled: 'hsl(28, 10%, 60%)',
            border: 'hsl(40, 22%, 86%)', divider: 'hsl(40, 18%, 88%)', focus: 'hsl(40, 88%, 67%)',
        },
        isDark: false,
    },
    'lemon-tart-dark': {
        key: 'lemon-tart-dark', label: 'Lemon Tart Dark',
        blurb: 'Late-night pantry raid — charcoal + golden + sunset orange.',
        swatch: ['hsl(46,100%,50%)', 'hsl(105,47%,36%)', 'hsl(23,100%,57%)'],
        palette: {
            primary: 'hsl(46, 100%, 50%)', secondary: 'hsl(105, 47%, 36%)', accent: 'hsl(23, 100%, 57%)',
            page: 'hsl(225, 16%, 14%)', component: 'hsl(225, 14%, 19%)',
            positive: 'hsl(105, 47%, 50%)', negative: 'hsl(7, 85%, 65%)',
            info: 'hsl(218, 80%, 70%)', warning: 'hsl(40, 90%, 60%)',
            text: 'hsl(0, 0%, 100%)', disabled: 'hsl(225, 12%, 50%)',
            border: 'hsl(225, 12%, 30%)', divider: 'hsl(225, 12%, 26%)', focus: 'hsl(46, 100%, 50%)',
        },
        isDark: true,
    },

    // ───────── Blueberry family ─────────────────────────────────────
    'blueberry': {
        key: 'blueberry', label: 'Blueberry',
        blurb: 'Cool cobalt + navy. Focused, easy on long-session eyes.',
        swatch: ['hsl(218,76%,56%)', 'hsl(220,60%,22%)', 'hsl(195,90%,60%)'],
        palette: {
            primary: 'hsl(218, 76%, 56%)', secondary: 'hsl(220, 60%, 22%)', accent: 'hsl(195, 90%, 60%)',
            page: 'hsl(218, 35%, 95%)', component: 'hsl(218, 30%, 98%)',
            positive: 'hsl(140, 50%, 45%)', negative: 'hsl(7, 75%, 56%)',
            info: 'hsl(195, 90%, 50%)', warning: 'hsl(33, 95%, 55%)',
            text: 'hsl(220, 32%, 14%)', disabled: 'hsl(220, 14%, 60%)',
            border: 'hsl(218, 22%, 84%)', divider: 'hsl(218, 18%, 86%)', focus: 'hsl(218, 76%, 56%)',
        },
        isDark: false,
    },
    'blueberry-dark': {
        key: 'blueberry-dark', label: 'Blueberry Dark',
        blurb: 'Muted teal + lavender on near-black. Twilight blueberry patch.',
        swatch: ['hsl(193,25%,66%)', 'hsl(184,14%,47%)', 'hsl(232,41%,75%)'],
        palette: {
            primary: 'hsl(193, 25%, 66%)', secondary: 'hsl(184, 14%, 47%)', accent: 'hsl(232, 41%, 75%)',
            page: 'hsl(220, 18%, 11%)', component: 'hsl(220, 16%, 16%)',
            positive: 'hsl(150, 50%, 60%)', negative: 'hsl(7, 70%, 65%)',
            info: 'hsl(196, 60%, 65%)', warning: 'hsl(40, 80%, 65%)',
            text: 'hsl(196, 47%, 71%)', disabled: 'hsl(193, 18%, 50%)',
            border: 'hsl(184, 14%, 30%)', divider: 'hsl(184, 14%, 26%)', focus: 'hsl(193, 25%, 66%)',
        },
        isDark: true,
    },

    // ───────── Cherry Cola family ───────────────────────────────────
    'cherry-cola': {
        key: 'cherry-cola', label: 'Cherry Cola',
        blurb: 'Bold cherry red + cocoa, served with a caramel accent.',
        swatch: ['hsl(352,65%,50%)', 'hsl(355,50%,18%)', 'hsl(36,85%,56%)'],
        palette: {
            primary: 'hsl(352, 65%, 50%)', secondary: 'hsl(355, 50%, 18%)', accent: 'hsl(36, 85%, 56%)',
            page: 'hsl(20, 35%, 95%)', component: 'hsl(20, 30%, 98%)',
            positive: 'hsl(140, 50%, 45%)', negative: 'hsl(7, 75%, 50%)',
            info: 'hsl(218, 76%, 56%)', warning: 'hsl(36, 85%, 56%)',
            text: 'hsl(355, 35%, 16%)', disabled: 'hsl(355, 12%, 60%)',
            border: 'hsl(20, 22%, 86%)', divider: 'hsl(20, 18%, 88%)', focus: 'hsl(352, 65%, 50%)',
        },
        isDark: false,
    },
    'cherry-cola-dark': {
        key: 'cherry-cola-dark', label: 'Cherry Cola Dark',
        blurb: 'Deep merlot + olive sage. Cellar-rich and unapologetic.',
        swatch: ['hsl(98,60%,70%)', 'hsl(2,16%,19%)', 'hsl(74,36%,44%)'],
        palette: {
            primary: 'hsl(98, 60%, 70%)', secondary: 'hsl(2, 16%, 19%)', accent: 'hsl(74, 36%, 44%)',
            page: 'hsl(335, 100%, 9%)', component: 'hsl(2, 16%, 16%)',
            positive: 'hsl(98, 60%, 60%)', negative: 'hsl(352, 65%, 65%)',
            info: 'hsl(218, 70%, 70%)', warning: 'hsl(40, 85%, 60%)',
            text: 'hsl(103, 50%, 88%)', disabled: 'hsl(83, 22%, 50%)',
            border: 'hsl(2, 16%, 28%)', divider: 'hsl(2, 16%, 24%)', focus: 'hsl(98, 60%, 70%)',
        },
        isDark: true,
    },

    // ───────── Sourdough family ─────────────────────────────────────
    'sourdough': {
        key: 'sourdough', label: 'Sourdough',
        blurb: 'Toasty amber + brown crust on a proofed cream. Rustic.',
        swatch: ['hsl(33,72%,55%)', 'hsl(28,36%,28%)', 'hsl(45,88%,60%)'],
        palette: {
            primary: 'hsl(33, 72%, 55%)', secondary: 'hsl(28, 36%, 28%)', accent: 'hsl(45, 88%, 60%)',
            page: 'hsl(36, 36%, 92%)', component: 'hsl(36, 32%, 97%)',
            positive: 'hsl(140, 50%, 45%)', negative: 'hsl(7, 75%, 56%)',
            info: 'hsl(218, 76%, 56%)', warning: 'hsl(33, 95%, 55%)',
            text: 'hsl(28, 32%, 16%)', disabled: 'hsl(28, 14%, 58%)',
            border: 'hsl(33, 22%, 82%)', divider: 'hsl(33, 18%, 84%)', focus: 'hsl(33, 72%, 55%)',
        },
        isDark: false,
    },
    'sourdough-dark': {
        key: 'sourdough-dark', label: 'Sourdough Dark',
        blurb: 'Bake at midnight — warm browns + honey on dark crust.',
        swatch: ['hsl(33,80%,60%)', 'hsl(28,30%,40%)', 'hsl(45,90%,65%)'],
        palette: {
            primary: 'hsl(33, 80%, 60%)', secondary: 'hsl(28, 30%, 40%)', accent: 'hsl(45, 90%, 65%)',
            page: 'hsl(28, 35%, 8%)', component: 'hsl(28, 28%, 13%)',
            positive: 'hsl(140, 55%, 60%)', negative: 'hsl(7, 78%, 65%)',
            info: 'hsl(218, 80%, 70%)', warning: 'hsl(33, 90%, 65%)',
            text: 'hsl(36, 50%, 92%)', disabled: 'hsl(28, 14%, 55%)',
            border: 'hsl(28, 18%, 28%)', divider: 'hsl(28, 18%, 24%)', focus: 'hsl(33, 80%, 60%)',
        },
        isDark: true,
    },
};

/** Family groupings for the Preferences picker. Each card renders one
 *  family with a Light / Dark toggle inside, so users can pick a vibe
 *  AND a mode separately. `system` is rendered as its own card. */
export interface ThemeFamily {
    key: string;            // family slug, not a theme key
    label: string;          // shown as the card title
    blurb: string;          // 1-line description
    light: string;          // theme key for the light variant
    dark: string;           // theme key for the dark variant
}

export const THEME_FAMILIES: readonly ThemeFamily[] = [
    {
        key: 'pesto',
        label: 'Pesto',
        blurb: "Fresh garden green + teal with a golden accent. Dora's default.",
        light: 'pesto', dark: 'pesto-dark',
    },
    {
        key: 'lemon-tart',
        label: 'Lemon Tart',
        blurb: 'Warm yellow on cream by day, charcoal + sunset by night.',
        light: 'lemon-tart', dark: 'lemon-tart-dark',
    },
    {
        key: 'blueberry',
        label: 'Blueberry',
        blurb: 'Cool cobalt + navy — focused, easy on long-session eyes.',
        light: 'blueberry', dark: 'blueberry-dark',
    },
    {
        key: 'cherry-cola',
        label: 'Cherry Cola',
        blurb: 'Bold cherry red + cocoa, with a caramel pop.',
        light: 'cherry-cola', dark: 'cherry-cola-dark',
    },
    {
        key: 'sourdough',
        label: 'Sourdough',
        blurb: 'Toasty amber + brown crust. Rustic any time of day.',
        light: 'sourdough', dark: 'sourdough-dark',
    },
];

/** Reverse index: given a theme key (e.g. 'pesto-dark') return its
 *  family + which variant it is. Used by the picker to render the
 *  active state. */
export function familyAndVariantOf(themeKey: string): { family: ThemeFamily; variant: 'light' | 'dark' } | null {
    for (const fam of THEME_FAMILIES) {
        if (fam.light === themeKey) return { family: fam, variant: 'light' };
        if (fam.dark === themeKey) return { family: fam, variant: 'dark' };
    }
    return null;
}

/** Map any persisted value (including legacy keys) to a current theme
 *  key. `system` follows OS preference — Pesto in light mode,
 *  Pesto Dark in dark mode (the brand stays consistent across both). */
function resolveThemeKey(pref: ThemePreference): string {
    // Legacy migrations
    if (pref === 'light' || pref === 'avocado') return 'pesto';
    if (pref === 'pesto-noir') return 'pesto-dark';
    if (pref === 'midnight-snack') return 'lemon-tart-dark';
    if (pref === 'dark') return 'pesto-dark';
    if (pref === 'system') {
        if (typeof window !== 'undefined' && window.matchMedia) {
            return window.matchMedia('(prefers-color-scheme: dark)').matches
                ? 'pesto-dark'
                : 'pesto';
        }
        return 'pesto';
    }
    return THEMES[pref] ? pref : 'pesto';
}

// A6 — re-spaced steps (ratios ~0.85 / 1.0 / 1.25 / 1.4) with a very slightly
// larger base than the old 16px. These drive the root font-size, so all
// rem-based text (incl. the --font-size-* ratio tokens) scales with them.
const FONT_SIZE_PX: Record<FontSizePreference, string> = {
    sm: '14px',
    md: '16.5px',
    lg: '20.5px',
    xl: '23px',
};

const SYSTEM_FALLBACK =
    "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
const FONT_FAMILY_CSS: Record<FontFamilyPreference, string> = {
    default: '',
    urbanist: `'Urbanist Variable', 'Urbanist', ${SYSTEM_FALLBACK}`,
    nunito: `'Nunito Variable', 'Nunito', ${SYSTEM_FALLBACK}`,
    inter: `'Inter Variable', 'Inter', ${SYSTEM_FALLBACK}`,
    lexend: `'Lexend Variable', 'Lexend', ${SYSTEM_FALLBACK}`,
    plus_jakarta_sans: `'Plus Jakarta Sans Variable', 'Plus Jakarta Sans', ${SYSTEM_FALLBACK}`,
};

let mediaQuery: MediaQueryList | null = null;
let mediaQueryListener: ((event: MediaQueryListEvent) => void) | null = null;
let cachedThemePref: ThemePreference = 'system';

function applyThemeKey(themeKey: string) {
    const theme = THEMES[themeKey];
    if (!theme) return;
    Object.entries(theme.palette).forEach(([key, value]) => setCssVar(key, value));
    if (typeof document !== 'undefined') {
        document.documentElement.setAttribute('data-theme', themeKey);
    }
    Dark.set(theme.isDark);
}

function attachSystemListener() {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    detachSystemListener();
    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQueryListener = () => {
        if (cachedThemePref === 'system') {
            applyThemeKey(resolveThemeKey('system'));
        }
    };
    mediaQuery.addEventListener('change', mediaQueryListener);
}

function detachSystemListener() {
    if (mediaQuery && mediaQueryListener) {
        mediaQuery.removeEventListener('change', mediaQueryListener);
    }
    mediaQuery = null;
    mediaQueryListener = null;
}

// Brand default — the theme used pre-auth and as the fallback for users
// without a saved preference. Bumping this is the single edit needed to
// shift the unauthenticated paint.
export const DEFAULT_THEME_KEY = 'pesto';

export default class ThemeService {
    /** Initial paint on boot — uses the OS preference until the
     *  user's saved theme arrives from /auth/me, then re-paints. */
    applyTheme = () => {
        cachedThemePref = 'system';
        applyThemeKey(resolveThemeKey('system'));
        attachSystemListener();
    };

    /** Apply the brand default theme. Used pre-auth and on sign-out so
     *  the app never silently flips into dark mode without the user
     *  asking — which was breaking the login page when the OS was in
     *  dark mode. */
    applyDefault = () => {
        cachedThemePref = DEFAULT_THEME_KEY as ThemePreference;
        applyThemeKey(DEFAULT_THEME_KEY);
        detachSystemListener();
    };

    /** Apply the signed-in user's persisted preferences. Safe to call
     *  on every auth-store change — idempotent. */
    applyForUser = (
        theme: ThemePreference,
        fontFamily: FontFamilyPreference,
        fontSize: FontSizePreference,
    ) => {
        cachedThemePref = theme;
        applyThemeKey(resolveThemeKey(theme));
        if (theme === 'system') attachSystemListener();
        else detachSystemListener();

        if (typeof document !== 'undefined') {
            document.documentElement.style.setProperty(
                '--dora-base-font-size',
                FONT_SIZE_PX[fontSize],
            );
            const family = FONT_FAMILY_CSS[fontFamily];
            if (family) {
                document.body.style.fontFamily = family;
            } else {
                document.body.style.removeProperty('font-family');
            }
        }
    };
}
