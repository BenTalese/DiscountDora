/**
 * PWA lifecycle hooks the SPA listens to:
 *   - `beforeinstallprompt`  — defer the browser's native install
 *     prompt so we can surface it via our own "Install Dora" button.
 *   - `appinstalled`         — clear the deferred prompt + record state.
 *   - `controllerchange` on `navigator.serviceWorker` — a new service
 *     worker has activated; surface a Notify with a "Reload" button.
 *
 * Designed to be idempotent so multiple call sites (App.vue mounting,
 * Settings page surfacing the install button) share state via the
 * module-level refs without double-binding listeners.
 */
import { Notify } from 'quasar';
import { computed, ref } from 'vue';

// Augment the standard BeforeInstallPromptEvent (TS lib doesn't ship one).
interface BeforeInstallPromptEvent extends Event {
    prompt: () => Promise<void>;
    userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

const deferredPrompt = ref<BeforeInstallPromptEvent | null>(null);
const installed = ref(false);
let lifecycleInstalled = false;
let updateToastShown = false;

export function isIosSafari(): boolean {
    if (typeof navigator === 'undefined') return false;
    const ua = navigator.userAgent;
    const isIOS = /iPad|iPhone|iPod/.test(ua) && !(/CriOS|FxiOS|EdgiOS/.test(ua));
    return isIOS && /Safari/.test(ua);
}

export function installPromptAvailable() {
    return computed(() => deferredPrompt.value !== null);
}

export function isInstalled() {
    return computed(() => installed.value);
}

export async function showInstallPrompt(): Promise<'accepted' | 'dismissed' | 'unavailable'> {
    const event = deferredPrompt.value;
    if (!event) return 'unavailable';
    try {
        await event.prompt();
        const choice = await event.userChoice;
        deferredPrompt.value = null;
        return choice.outcome;
    } catch {
        return 'dismissed';
    }
}

/** Wire window + service-worker listeners exactly once. Call from a
 *  boot file or App.vue mounted hook. */
export function installPwaLifecycle(): void {
    if (lifecycleInstalled) return;
    if (typeof window === 'undefined') return;
    lifecycleInstalled = true;

    // Some browsers fire `appinstalled` for an install that happened in
    // a different tab. Best-effort flag — no behaviour depends on it
    // beyond hiding the "Install Dora" button.
    window.addEventListener('appinstalled', () => {
        installed.value = true;
        deferredPrompt.value = null;
    });

    window.addEventListener('beforeinstallprompt', (event) => {
        event.preventDefault();
        deferredPrompt.value = event as BeforeInstallPromptEvent;
    });

    // Treat `display-mode: standalone` as already installed so we don't
    // nag a user who launched from the home screen.
    try {
        if (window.matchMedia('(display-mode: standalone)').matches) {
            installed.value = true;
        }
    } catch {
        // Ancient browsers without matchMedia — ignored.
    }

    // Service-worker update flow: when the new SW activates and takes
    // control of this client, offer a reload via Notify rather than
    // hard-reloading mid-interaction.
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            if (updateToastShown) return;
            updateToastShown = true;
            Notify.create({
                type: 'info',
                position: 'top',
                message: 'New version available.',
                caption: 'Reload to pick up the latest Dora.',
                timeout: 0,
                actions: [
                    {
                        label: 'Reload',
                        color: 'white',
                        handler: () => window.location.reload(),
                    },
                    { label: 'Later', color: 'white' },
                ],
            });
        });
    }
}
