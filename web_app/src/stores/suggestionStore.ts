import { acceptHMRUpdate, defineStore } from 'pinia';
import SuggestionsApiService, {
    type DoraSuggestion,
} from 'src/services/api/suggestionsApiService';
import { computed, readonly, ref } from 'vue';

/** P2-04 — shared store for Dora suggestions.
 *  Generators run server-side on every fetch and filter against the
 *  user's suppression list, so this store doesn't track per-suggestion
 *  state — just the most recent list plus a loading flag. The bubble
 *  badge, chat panel, and dashboard card all read from the same ref. */

const api = new SuggestionsApiService();

export const useSuggestionStore = defineStore('suggestion', () => {
    const suggestions = ref<DoraSuggestion[]>([]);
    const loading = ref(false);
    const lastLoadedAt = ref<number | null>(null);

    const count = computed(() => suggestions.value.length);
    const highCount = computed(
        () => suggestions.value.filter((s) => s.severity === 'high').length,
    );

    async function refreshAsync(): Promise<void> {
        loading.value = true;
        try {
            const result = await api.listAsync();
            suggestions.value = result.suggestions;
            lastLoadedAt.value = Date.now();
        } catch {
            // Endpoint may not exist on older backends — degrade silently
            // so the bubble badge / dashboard card just stay hidden.
            suggestions.value = [];
        } finally {
            loading.value = false;
        }
    }

    /** Remove a single suggestion from the local list — used after the
     *  server-side dismiss/snooze succeeds, so the UI updates without a
     *  full refetch. */
    function removeLocal(kind: string, dedupKey: string) {
        suggestions.value = suggestions.value.filter(
            (s) => !(s.kind === kind && s.dedup_key === dedupKey),
        );
    }

    async function dismissAsync(suggestion: DoraSuggestion): Promise<void> {
        await api.dismissAsync({
            kind: suggestion.kind,
            dedup_key: suggestion.dedup_key,
        });
        removeLocal(suggestion.kind, suggestion.dedup_key);
    }

    async function snoozeAsync(
        suggestion: DoraSuggestion,
        hours = 24,
    ): Promise<void> {
        await api.snoozeAsync({
            kind: suggestion.kind,
            dedup_key: suggestion.dedup_key,
            hours,
        });
        removeLocal(suggestion.kind, suggestion.dedup_key);
    }

    return {
        suggestions: readonly(suggestions),
        loading: readonly(loading),
        lastLoadedAt: readonly(lastLoadedAt),
        count,
        highCount,
        refreshAsync,
        dismissAsync,
        snoozeAsync,
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useSuggestionStore, import.meta.hot));
}
