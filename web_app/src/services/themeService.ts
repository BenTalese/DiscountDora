import { Dark, setCssVar } from 'quasar';
import type {
    FontFamilyPreference,
    FontSizePreference,
    ThemePreference
} from 'src/models/auth';

// Custom colours defined via colours.scss
export interface Theme {
    // Brand Colours
    primary: string;
    secondary: string;
    accent: string;

    // Background Colours
    page: string;
    component: string;

    // Status Colours
    positive: string;
    negative: string;
    info: string;
    warning: string;

    // Element Colours
    text: string;
    disabled: string;
    border: string;
    divider: string;
    focus: string;
}

const themes: { [key: string]: Theme } = {
    doraLight: {
        primary: '#17B073',
        secondary: '#006A80',
        accent: '#FED224',
        page: '#E8F6F3',
        component: 'whitesmoke',
        positive: '#8CF596',
        negative: '#FF9966',
        info: '#93C2C2',
        warning: '#EDE461',
        text: '#333333',
        disabled: '#BDBDBD',
        border: '#BDBDBD',
        divider: '#BDBDBD',
        focus: '#17B073'
    },
    doraDark: {
        primary: '#17B073',
        secondary: '#3FB6CC',
        accent: '#FED224',
        page: '#1B2026',
        component: '#262C33',
        positive: '#5BC871',
        negative: '#E07559',
        info: '#5FA8A8',
        warning: '#C9B53A',
        text: '#E8EAEC',
        disabled: '#6B7178',
        border: '#3A4047',
        divider: '#3A4047',
        focus: '#17B073'
    }
};

// Maps the user's font_size preference to a CSS body font-size. The values
// flow into a CSS custom property that all `rem`-based content scales
// against (set on :root in boot/theme.ts via document.documentElement).
const FONT_SIZE_PX: Record<FontSizePreference, string> = {
    sm: '14px',
    md: '16px',
    lg: '18px'
};

// font-family CSS values. `default` falls back to whatever the global CSS
// sets via `body { font-family: ... }` so legacy pages remain stable.
const SYSTEM_FALLBACK =
    "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
const FONT_FAMILY_CSS: Record<FontFamilyPreference, string> = {
    default: '',
    urbanist: `'Urbanist Variable', 'Urbanist', ${SYSTEM_FALLBACK}`,
    nunito: `'Nunito Variable', 'Nunito', ${SYSTEM_FALLBACK}`,
    inter: `'Inter Variable', 'Inter', ${SYSTEM_FALLBACK}`,
    lexend: `'Lexend Variable', 'Lexend', ${SYSTEM_FALLBACK}`,
    plus_jakarta_sans: `'Plus Jakarta Sans Variable', 'Plus Jakarta Sans', ${SYSTEM_FALLBACK}`
};

let mediaQuery: MediaQueryList | null = null;
let mediaQueryListener: ((e: MediaQueryListEvent) => void) | null = null;
let cachedThemePref: ThemePreference = 'system';

function effectiveMode(pref: ThemePreference): 'light' | 'dark' {
    if (pref === 'light') return 'light';
    if (pref === 'dark') return 'dark';
    if (typeof window !== 'undefined' && window.matchMedia) {
        return window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark'
            : 'light';
    }
    return 'light';
}

function applyMode(mode: 'light' | 'dark') {
    const theme = mode === 'dark' ? themes.doraDark : themes.doraLight;
    if (!theme) return;
    Object.entries(theme).forEach(([key, value]) => setCssVar(key, value));
    // Quasar tracks dark mode separately for its own components; keep them
    // in sync with the CSS-variable palette we just applied.
    Dark.set(mode === 'dark');
}

function attachSystemListener() {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    detachSystemListener();
    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQueryListener = () => {
        if (cachedThemePref === 'system') {
            applyMode(effectiveMode('system'));
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

export default class ThemeService {
    /** Initial paint on boot — uses the OS preference until the user's
     *  saved theme arrives from /auth/me, then re-paints. */
    applyTheme = () => {
        cachedThemePref = 'system';
        applyMode(effectiveMode('system'));
        attachSystemListener();
    };

    /** Apply the signed-in user's persisted preferences. Safe to call on
     *  every auth-store change — idempotent. */
    applyForUser = (
        theme: ThemePreference,
        fontFamily: FontFamilyPreference,
        fontSize: FontSizePreference
    ) => {
        cachedThemePref = theme;
        applyMode(effectiveMode(theme));
        if (theme === 'system') {
            attachSystemListener();
        } else {
            detachSystemListener();
        }

        if (typeof document !== 'undefined') {
            document.documentElement.style.setProperty(
                '--dora-base-font-size',
                FONT_SIZE_PX[fontSize]
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
