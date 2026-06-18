// Phase D / FU-186 — admin-set URL the Product Search nav opens.
//
// Lives in the small composable shape established by `useFeatureFlags`
// (ADR-002): one composable per concern, never a parallel store. Fetches
// `/api/app-settings` once per session; `refresh()` re-reads after the
// admin saves a change.

import { ref } from 'vue';
import AppSettingsApiService from 'src/services/api/appSettingsApiService';

const url = ref<string>('');
const loaded = ref(false);
let inflight: Promise<void> | null = null;

function load(): Promise<void> {
    if (!inflight) {
        inflight = new AppSettingsApiService()
            .getAsync()
            .then((s) => {
                url.value = s.product_search_url || '';
            })
            .catch(() => {
                // Anonymous / unreachable / non-admin — leave the URL empty.
                // The Product Search nav entry just shows as "not set up".
            })
            .finally(() => {
                loaded.value = true;
            });
    }
    return inflight;
}

export function useProductSearchUrl() {
    void load();
    function refresh(): Promise<void> {
        loaded.value = false;
        inflight = null;
        return load();
    }
    return {
        url,
        loaded,
        refresh,
    };
}
