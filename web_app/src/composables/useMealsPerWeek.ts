// per-user "meals per week" preference. Drives the
// sequential builder's target-count. Falls back to `BUILDER_TARGET_MEALS_
// FALLBACK` (7) when the user hasn't set a value.
//
// Same shape as `useBatchEnabled` — reads the server-owned user pref
// reactively via authStore.

import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { BUILDER_TARGET_MEALS_FALLBACK } from 'src/composables/useMealPlanner';
import { useAuthStore } from 'src/stores/authStore';

export function useMealsPerWeek() {
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    const mealsPerWeek = computed<number>(
        () => currentUser.value?.meals_per_week ?? BUILDER_TARGET_MEALS_FALLBACK,
    );

    async function setMealsPerWeek(next: number | null): Promise<void> {
        await authStore.updateMeAsync({ meals_per_week: next });
    }

    return {
        mealsPerWeek,
        setMealsPerWeek,
    };
}
