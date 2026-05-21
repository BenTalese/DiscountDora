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

    const primaryListId = computed(() => membership.value?.primary_shopping_list_id ?? null);
    const primarySummary = computed(() =>
        summaries.value.find((s) => s.is_primary) ?? null
    );

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
        } catch (err) {
            loadError.value = String(err);
        } finally {
            loading.value = false;
        }
    };

    return {
        summaries: readonly(summaries),
        membership: readonly(membership),
        loading: readonly(loading),
        loadError: readonly(loadError),
        primaryListId,
        primarySummary,
        refreshAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useShoppingListStore, import.meta.hot));
}
