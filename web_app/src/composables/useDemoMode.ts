import { ref } from 'vue';
import AuthApiService from 'src/services/api/authApiService';

// Demo / sellable-showcase mode (FU-392). Surfaced to the client via the
// pre-auth `demo_mode` flag on GET /api/auth/capabilities. When on, the SPA
// renders a persistent "this is a demo, it resets periodically" banner. The
// flag is an operator/deployment decision (env `DORA_DEMO_MODE`), never an
// in-app setting, so it's stable for the whole session.
//
// Module-level so the capabilities probe runs once per session and every
// caller shares the same reactive answer.
const enabled = ref(false);
const loaded = ref(false);
let inflight: Promise<void> | null = null;

function load(): Promise<void> {
    if (!inflight) {
        inflight = new AuthApiService()
            .getCapabilitiesAsync()
            .then((caps) => {
                enabled.value = caps.demoMode;
            })
            .catch(() => {
                // Probe failure → assume not a demo (hide the banner).
                enabled.value = false;
            })
            .finally(() => {
                loaded.value = true;
            });
    }
    return inflight;
}

export function useDemoMode() {
    void load();
    return { demoMode: enabled, demoModeLoaded: loaded };
}
