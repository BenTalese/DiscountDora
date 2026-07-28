// Phase D / FU-186 — admin-set URL the Product Search nav opens.
//
// Lives in the small composable shape established by `useFeatureFlags`
// (ADR-002): one composable per concern, never a parallel store. Fetches
// `/api/app-settings` once per session; `refresh()` re-reads after the
// admin saves a change.

import { computed, ref } from 'vue';
import type { Router } from 'vue-router';
import AppSettingsApiService from 'src/services/api/appSettingsApiService';

// Admin Features page that owns the Product Search URL row. Used as the
// fallback destination for every "Product Search" entry point when no URL is
// configured yet, so the not-set-up state stays actionable instead of dead.
export const PRODUCT_SEARCH_SETTINGS_PATH = '/settings/admin/system/features';

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
    const configured = computed(() => url.value.trim().length > 0);
    function refresh(): Promise<void> {
        loaded.value = false;
        inflight = null;
        return load();
    }
    return {
        url,
        loaded,
        configured,
        refresh,
    };
}

// Single destination resolver for every in-app "Product Search" entry point
// (nav strip + the empty-state / find-&-link CTAs). FU-186 removed the in-app
// `/product-search` route: a configured URL opens the external companion in a
// new tab; when unset we route to the admin Features page so the setup path is
// discoverable rather than a 404 (owner call, FU-581). The old `q` /
// `stock_item_id` seeding is dropped — nothing consumes it any more.
export function openProductSearch(router: Router): void {
    const target = url.value.trim();
    if (target) {
        window.open(target, '_blank', 'noopener,noreferrer');
    } else {
        void router.push(PRODUCT_SEARCH_SETTINGS_PATH);
    }
}
