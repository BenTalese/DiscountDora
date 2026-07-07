// screen wake lock (Screen Wake Lock API).
//
// Two callers today:
//   - RecipeCookMode.vue keeps the screen on while cooking, so a hands-free
//     "Next step" or a running timer stays readable without the user
//     wiping the sink off their hands to tap the display.
//   - ShoppingListDetail.vue holds the lock while the list is in
//     `status === 'shopping'` (shop mode), so the phone doesn't sleep
//     between aisles.
//
// The Wake Lock API is supported in every modern Chromium (desktop, PWA,
// Capacitor WebView), Safari 16.4+, and Firefox 126+. Where it isn't
// available we silently no-op — the feature is a UX polish, not a
// correctness invariant, so a fallback plugin isn't worth the weight.
//
// The browser drops the lock automatically when the tab loses visibility.
// We reacquire on `visibilitychange` back to `visible` for as long as the
// consumer's `enabled` flag stays true (e.g. shop mode still active).
//
// R-014 — this composable can be called from a component `setup()`; it
// registers `onUnmounted` to release the lock cleanly even if the caller
// forgets. No manual `release()` required for the golden path.

import { onUnmounted, ref, watch, type Ref } from 'vue';

type WakeLockSentinel = { release: () => Promise<void>; released: boolean };

function isSupported(): boolean {
    return typeof navigator !== 'undefined'
        && 'wakeLock' in navigator
        && typeof (navigator as unknown as { wakeLock?: { request?: unknown } }).wakeLock?.request === 'function';
}

export function useWakeLock(enabled: Ref<boolean>) {
    const active = ref(false);
    const supported = ref(isSupported());

    let sentinel: WakeLockSentinel | null = null;
    let visibilityHandler: (() => void) | null = null;

    async function acquire(): Promise<void> {
        if (!supported.value) return;
        if (sentinel && !sentinel.released) return;
        try {
            const wl = (navigator as unknown as {
                wakeLock: { request: (type: 'screen') => Promise<WakeLockSentinel> };
            }).wakeLock;
            sentinel = await wl.request('screen');
            active.value = true;
        } catch {
            // NotAllowedError (permission policy) / SecurityError (insecure
            // context) / AbortError (visibility lost mid-request) — none
            // are worth surfacing to the user.
            active.value = false;
        }
    }

    async function release(): Promise<void> {
        try {
            if (sentinel && !sentinel.released) await sentinel.release();
        } catch {
            // Ignore.
        }
        sentinel = null;
        active.value = false;
    }

    function onVisibilityChange() {
        if (document.visibilityState === 'visible' && enabled.value) {
            void acquire();
        }
    }

    watch(
        enabled,
        (want) => {
            if (want) {
                if (typeof document !== 'undefined' && !visibilityHandler) {
                    visibilityHandler = onVisibilityChange;
                    document.addEventListener('visibilitychange', visibilityHandler);
                }
                void acquire();
            } else {
                if (visibilityHandler) {
                    document.removeEventListener('visibilitychange', visibilityHandler);
                    visibilityHandler = null;
                }
                void release();
            }
        },
        { immediate: true },
    );

    onUnmounted(() => {
        if (visibilityHandler) {
            document.removeEventListener('visibilitychange', visibilityHandler);
            visibilityHandler = null;
        }
        void release();
    });

    return { active, supported };
}
