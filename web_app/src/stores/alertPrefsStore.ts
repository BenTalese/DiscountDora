import { acceptHMRUpdate, defineStore } from 'pinia';
import type { AlertKind, AlertPref } from 'src/models/alert';
import AlertApiService from 'src/services/api/alertApiService';
import { computed, readonly, ref } from 'vue';

const api = new AlertApiService();

// Per-user alert preferences (C-9.2): enable/disable a kind. That is the whole
// model — the tier override was cut at Step-0 Q3, since a per-user "is this
// actionable?" was an answer the stock rows could never see (B2).
// Server-owned and server-applied — GET /alerts
// already reflects these, so the badge/list need no client recompute (R-003).
// This store is the thin cache the (C-9.3) manage panel binds to; it lands
// here so that chunk is pure UI. Every mutation returns the full refreshed
// set, so the store stays in lock-step with the server without a re-fetch.
export const useAlertPrefsStore = defineStore('alertPrefs', () => {
    const prefs = ref<AlertPref[]>([]);
    const loading = ref(false);
    const loadError = ref<string | null>(null);

    const byKind = computed<Record<string, AlertPref>>(() =>
        Object.fromEntries(prefs.value.map((p) => [p.kind, p])));

    const refreshAsync = async () => {
        loading.value = true;
        loadError.value = null;
        try {
            prefs.value = (await api.getPrefsAsync()).prefs;
        } catch (err) {
            loadError.value = String(err);
        } finally {
            loading.value = false;
        }
    };

    const setEnabled = async (kind: AlertKind, enabled: boolean) => {
        prefs.value = (await api.updatePrefAsync({ kind, enabled })).prefs;
    };

    return {
        prefs: readonly(prefs),
        loading: readonly(loading),
        loadError: readonly(loadError),
        byKind,
        refreshAsync,
        setEnabled,
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useAlertPrefsStore, import.meta.hot));
}
