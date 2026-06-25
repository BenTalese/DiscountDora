// IMPL_PLAN_MEAL_PLANS_REBUILD §6.6 / Q3 — per-user batch-cooking posture.
// Charter P10 Anti-creep — default *off* (fresh). When the user opts in, the
// meal-planner reveals the cook-pool affordances (per-recipe ± / log-cook /
// "n free"), the shortfall warning, and the "to cook by" sidebar line.
//
// Mirrors `useImagePrefs` — server-owned user preference, optimistically
// flipped through the authStore. No install-wide layer (this is a personal
// UX preference; there's no feature-availability concern to gate at the
// install level).

import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useAuthStore } from 'src/stores/authStore';

export function useBatchEnabled() {
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    // Default false when the user hasn't loaded yet — Anti-creep, and avoids
    // a flash of batch affordances on first paint for a fresh household.
    const batchEnabled = computed(
        () => !!currentUser.value?.batch_features_enabled,
    );

    async function setBatchEnabled(next: boolean): Promise<void> {
        await authStore.updateMeAsync({ batch_features_enabled: next });
    }

    return {
        batchEnabled,
        setBatchEnabled,
    };
}
