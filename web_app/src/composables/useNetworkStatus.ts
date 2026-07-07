// Module-level network awareness (F3).
//
// Exposes reactive `online` (browser-level) and `apiReachable` (the dora_api
// /health probe). Used by:
//   - OfflineBanner: pin a red strip when either is false.
//   - useOfflineQueue: drain pending mutations when apiReachable flips true.
//   - Free-form code: any caller that wants to short-circuit before doing
//     an expensive search or background fetch.
//
// State lives at module scope so every consumer shares the same singleton
// — we only want one health-poll loop running per tab.

import { Notify } from 'quasar';
import { computed, readonly, ref } from 'vue';
import { getBackendBaseUrl } from 'src/services/api/backendUrl';

// Reads the runtime backend URL (env-baked, capacitor Preferences, or the
// browser localStorage override — see `services/api/backendUrl.ts`) and
// appends /health. Uses `fetch` directly so the probe sidesteps the
// AxiosHttpClient interceptors / retry layer.
function resolveHealthUrl(): string {
    const base = getBackendBaseUrl();
    if (base && base.length > 0) return base + '/health';
    return '';
}

// Poll cadence: when believed reachable we tick once every 30s — the UI
// reacts to errors in real time anyway, so the poll is just for the "I
// quietly stopped working" case. When unreachable we ramp from 5s up to
// 60s with exponential backoff so a long outage doesn't hammer.
const STABLE_INTERVAL_MS = 30_000;
const PROBE_INITIAL_MS = 5_000;
const PROBE_MAX_MS = 60_000;
const PROBE_TIMEOUT_MS = 4_000;

const online = ref(typeof navigator === 'undefined' ? true : navigator.onLine);
const apiReachable = ref(true);
const lastSeenOnline = ref<Date | null>(online.value ? new Date() : null);
const reconnecting = ref(false);

let pollTimer: ReturnType<typeof setTimeout> | null = null;
let currentBackoffMs = PROBE_INITIAL_MS;
let booted = false;

// Eats AbortError so we can race against a timeout without surfacing
// scary-looking unhandled rejections in the console.
async function probeOnce(): Promise<boolean> {
    if (!online.value) return false;
    const url = resolveHealthUrl();
    // on native before the user has picked an instance, the URL
    // resolves to empty; skip the probe cleanly rather than firing a
    // relative fetch at the WebView origin.
    if (!url) return false;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS);
    try {
        const res = await fetch(url, {
            method: 'GET',
            // The health endpoint is open and cookie-less — no need to
            // attach credentials. Keeps the request preflight-free in
            // CORS terms too.
            credentials: 'omit',
            cache: 'no-store',
            signal: controller.signal,
        });
        return res.ok;
    } catch {
        return false;
    } finally {
        clearTimeout(timeoutId);
    }
}

function scheduleNext(delayMs: number) {
    if (pollTimer) clearTimeout(pollTimer);
    pollTimer = setTimeout(() => void runProbe(), delayMs);
}

async function runProbe(): Promise<boolean> {
    if (!online.value) {
        // No point hitting the API while the browser says we're offline —
        // schedule a long-tail check so we recover if the browser misses
        // the 'online' event.
        scheduleNext(STABLE_INTERVAL_MS);
        return false;
    }
    reconnecting.value = !apiReachable.value;
    const ok = await probeOnce();
    const wasReachable = apiReachable.value;
    apiReachable.value = ok;
    reconnecting.value = false;

    if (ok) {
        currentBackoffMs = PROBE_INITIAL_MS;
        lastSeenOnline.value = new Date();
        if (!wasReachable) {
            Notify.create({
                type: 'positive',
                position: 'top',
                message: "We're back online. Syncing any queued changes.",
                timeout: 3000,
            });
        }
        scheduleNext(STABLE_INTERVAL_MS);
    } else {
        if (wasReachable) {
            // Just transitioned reachable → unreachable.
            Notify.create({
                type: 'warning',
                position: 'top',
                message:
                    "Couldn't reach the server. We'll keep trying — most actions still work and will sync when we reconnect.",
                timeout: 4000,
            });
        }
        scheduleNext(currentBackoffMs);
        currentBackoffMs = Math.min(currentBackoffMs * 2, PROBE_MAX_MS);
    }
    return ok;
}

function onBrowserOnline() {
    if (online.value) return;
    online.value = true;
    lastSeenOnline.value = new Date();
    Notify.create({
        type: 'info',
        position: 'top',
        message: 'Network detected. Checking the server…',
        timeout: 2500,
    });
    currentBackoffMs = PROBE_INITIAL_MS;
    void runProbe();
}

function onBrowserOffline() {
    online.value = false;
    apiReachable.value = false;
    Notify.create({
        type: 'warning',
        position: 'top',
        message:
            "You're offline. Stock changes will sync when you're back.",
        timeout: 4000,
    });
}

// One-shot setup. Idempotent because every consumer calls it via
// useNetworkStatus().
function boot() {
    if (booted) return;
    booted = true;
    if (typeof window !== 'undefined') {
        window.addEventListener('online', onBrowserOnline);
        window.addEventListener('offline', onBrowserOffline);
    }
    // First probe runs immediately so the banner state settles fast.
    void runProbe();
}

export function useNetworkStatus() {
    boot();
    return {
        online: readonly(online),
        apiReachable: readonly(apiReachable),
        lastSeenOnline: readonly(lastSeenOnline),
        reconnecting: readonly(reconnecting),
        isFullyOnline: computed(() => online.value && apiReachable.value),
        /** Force an immediate probe (e.g. when the user clicks "Retry"). */
        retryNow: () => {
            currentBackoffMs = PROBE_INITIAL_MS;
            void runProbe();
        },
    };
}
