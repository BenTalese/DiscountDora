import { boot } from 'quasar/wrappers';
import { installPwaLifecycle } from 'src/composables/usePwaLifecycle';

// Wires `beforeinstallprompt`, `appinstalled` and the SW `controllerchange`
// listeners exactly once for the lifetime of the SPA. Safe to load in
// non-PWA modes too — the SW listener is gated on `'serviceWorker' in
// navigator`, so a SPA-mode build is a no-op.
export default boot(() => {
    installPwaLifecycle();
});
