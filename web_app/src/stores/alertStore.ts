import { acceptHMRUpdate, defineStore } from 'pinia';
import type { Alerts } from 'src/models/alert';
import AlertApiService from 'src/services/api/alertApiService';
import { computed, readonly, ref } from 'vue';

const api = new AlertApiService();

// Cached alerts shared across the app: the header bell badge, the
// notifications panel, and Dora's "what needs my attention?" intent all
// pull from the same store so they can't disagree.
export const useAlertStore = defineStore('alert', () => {
    const alerts = ref<Alerts>({
        items: [],
        high_count: 0,
        medium_count: 0,
        low_count: 0,
    });
    const loading = ref(false);
    const loadError = ref<string | null>(null);

    // High + medium count drives the bell badge — low-severity items
    // (e.g. one stocktake overdue) shouldn't visually nag.
    const badgeCount = computed(() => alerts.value.high_count + alerts.value.medium_count);
    const totalCount = computed(() => alerts.value.items.length);

    const refreshAsync = async () => {
        loading.value = true;
        loadError.value = null;
        try {
            alerts.value = await api.getAlertsAsync();
        } catch (err) {
            loadError.value = String(err);
        } finally {
            loading.value = false;
        }
    };

    return {
        alerts: readonly(alerts),
        loading: readonly(loading),
        loadError: readonly(loadError),
        badgeCount,
        totalCount,
        refreshAsync,
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useAlertStore, import.meta.hot));
}
