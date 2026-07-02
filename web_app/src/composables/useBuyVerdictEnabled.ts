import { ref } from 'vue';
import HealthApiService from 'src/services/api/healthApiService';

// P8-05 — install-wide `buy_verdict_enabled` AppSetting, surfaced to
// the client as `features.buy_verdict` on GET /api/health. Defaults to
// **true** (unlike scanning): the oracle is a pure-personal feature
// with no external surface to disable, so the default is on.
//
// Module-level so the health probe runs once per session and every
// caller shares the same reactive answer (matches
// `useScanningEnabled` shape).
const enabled = ref(true);
const loaded = ref(false);
let inflight: Promise<void> | null = null;

function load(): Promise<void> {
    if (!inflight) {
        inflight = new HealthApiService()
            .getInfoAsync()
            .then((info) => {
                // `buy_verdict` is a new health flag — treat missing
                // as "on" so a client running against an older backend
                // still sees the oracle (or rather: the badge is
                // client-only; a server without the endpoint will 404
                // and the composable will hide the badge for that
                // item, which is safe).
                enabled.value = info.features.buy_verdict !== false;
            })
            .catch(() => {
                // Probe failed — leave the default on so an offline
                // start doesn't hide a working feature.
                enabled.value = true;
            })
            .finally(() => {
                loaded.value = true;
            });
    }
    return inflight;
}

export function useBuyVerdictEnabled() {
    void load();
    function refresh(): Promise<void> {
        loaded.value = false;
        inflight = null;
        return load();
    }
    return {
        buyVerdictEnabled: enabled,
        buyVerdictLoaded: loaded,
        refreshBuyVerdict: refresh,
    };
}
