// runtime-configurable Dora API base URL.
//
// The SPA runs in three shapes:
//   - web (dev / prod PWA): baseURL follows the current origin (env-baked
//     `VITE_API_BASE_URL` if provided, else `${protocol}//${hostname}:5170/api`).
//   - Capacitor native (Android APK / iOS): the app is served from
//     `capacitor://localhost` (Android WebView remaps to `https://localhost`),
//     so it CANNOT infer a backend from `window.location`. The user picks
//     their instance URL on first launch — we persist it via
//     `@capacitor/preferences` and prepend it to every API request.
//
// Storage layout: a single Preferences key `dora.backendBaseUrl`. The web
// fallback also honours a `localStorage` copy so a browser user can override
// the env default from the same Settings screen without touching env files.
//
// The axios request interceptor calls `getBackendBaseUrl()` synchronously
// per request, so a runtime change (Settings → save) applies to the next
// request without any client rebuild.

import { Capacitor } from '@capacitor/core';
import { Preferences } from '@capacitor/preferences';

const PREF_KEY = 'dora.backendBaseUrl';
const LS_KEY = 'dora.backendBaseUrl';

let cache: string | null = null;
let loaded = false;

export function isNativePlatform(): boolean {
    try {
        return Capacitor.isNativePlatform();
    } catch {
        return false;
    }
}

function envDefault(): string {
    const env = import.meta.env.VITE_API_BASE_URL;
    if (env && env.length > 0) return env.replace(/\/+$/, '');
    if (isNativePlatform()) {
        // Capacitor serves the SPA from https://localhost (Android) or
        // capacitor://localhost (iOS) — neither is a real backend, so
        // there is no honest default. Force the runtime-override path.
        return '';
    }
    if (typeof window !== 'undefined' && window.location) {
        const { protocol, hostname } = window.location;
        return `${protocol}//${hostname}:5170/api`;
    }
    return '';
}

export function getBackendBaseUrl(): string {
    if (cache !== null) return cache;
    return envDefault();
}

export function hasBackendBaseUrl(): boolean {
    if (cache !== null && cache.length > 0) return true;
    // Browsers: the env / window fallback is always usable, so a user
    // never sees the setup gate. Native: only "yes" once the user has
    // saved a URL.
    if (!isNativePlatform()) {
        return envDefault().length > 0;
    }
    return false;
}

function normaliseUrl(raw: string): string {
    let url = raw.trim().replace(/\/+$/, '');
    if (!/^https?:\/\//i.test(url)) {
        url = 'https://' + url;
    }
    // The app always talks to /api/*; accept both "http://host" and
    // "http://host/api" from users and store the /api-prefixed form.
    if (!/\/api$/i.test(url)) {
        url = url + '/api';
    }
    return url;
}

export async function setBackendBaseUrl(raw: string): Promise<string> {
    const url = normaliseUrl(raw);
    cache = url;
    loaded = true;
    if (isNativePlatform()) {
        await Preferences.set({ key: PREF_KEY, value: url });
    } else {
        try {
            localStorage.setItem(LS_KEY, url);
        } catch {
            // Storage disabled — the in-memory cache still holds for this session.
        }
    }
    return url;
}

export async function clearBackendBaseUrl(): Promise<void> {
    cache = null;
    loaded = true;
    if (isNativePlatform()) {
        await Preferences.remove({ key: PREF_KEY });
    } else {
        try {
            localStorage.removeItem(LS_KEY);
        } catch {
            // Ignore.
        }
    }
}

export async function loadBackendBaseUrl(): Promise<string | null> {
    if (loaded) return cache;
    if (isNativePlatform()) {
        try {
            const { value } = await Preferences.get({ key: PREF_KEY });
            if (value && value.length > 0) cache = value;
        } catch {
            // Preferences not available (e.g. web fallback failure).
        }
    } else {
        try {
            const value = localStorage.getItem(LS_KEY);
            if (value && value.length > 0) cache = value;
        } catch {
            // Ignore.
        }
    }
    loaded = true;
    return cache;
}

export function backendBaseUrlIsUserSet(): boolean {
    return cache !== null && cache.length > 0;
}
