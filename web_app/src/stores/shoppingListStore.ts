import { acceptHMRUpdate, defineStore } from 'pinia';
import type {
    Membership,
    ShoppingListSummary
} from 'src/models/shoppingList';
import ShoppingListApiService from 'src/services/api/shoppingListApiService';
import { computed, readonly, ref } from 'vue';

const api = new ShoppingListApiService();

export const useShoppingListStore = defineStore('shoppingList', () => {
    const summaries = ref<ShoppingListSummary[]>([]);
    const membership = ref<Membership | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);

    // Chunk 2: "primary" is inferred — the server returns the quick-add target
    // id only when exactly one DRAFT exists; otherwise it's null and the caller
    // must prompt the user.
    const quickAddTargetListId = computed(
        () => membership.value?.quick_add_target_list_id ?? null
    );
    const quickAddTargetSummary = computed(() => {
        const id = quickAddTargetListId.value;
        if (!id) return null;
        return summaries.value.find((s) => s.shopping_list_id === id) ?? null;
    });

    let hydrated = false;
    let inflight: Promise<void> | null = null;

    const refreshAsync = async () => {
        loading.value = true;
        loadError.value = null;
        try {
            const [s, m] = await Promise.all([
                api.getAllAsync(),
                api.getMembershipAsync()
            ]);
            summaries.value = s;
            membership.value = m;
            hydrated = true;
        } catch (err) {
            // Surface to the console explicitly — the catch used to set
            // `loadError` silently and the UI rendered nothing useful,
            // which read as a "blank screen" bug.
            console.error('[shoppingListStore] refreshAsync failed', err);
            loadError.value = err instanceof Error ? err.message : String(err);
        } finally {
            loading.value = false;
        }
    };

    /** R-016 — lazy hydration. Use this in `onMounted` when you need
     *  summaries/membership populated but don't care about a forced refresh.
     *  Call `refreshAsync` directly for an explicit refetch (post-mutation,
     *  pull-to-refresh, explicit reload). */
    const ensureLoadedAsync = (): Promise<void> => {
        if (hydrated) return Promise.resolve();
        inflight ??= refreshAsync().finally(() => { inflight = null; });
        return inflight;
    };

    return {
        summaries: readonly(summaries),
        membership: readonly(membership),
        loading: readonly(loading),
        loadError: readonly(loadError),
        quickAddTargetListId,
        quickAddTargetSummary,
        refreshAsync,
        ensureLoadedAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useShoppingListStore, import.meta.hot));
}
