// C-cross Chunk 2 — money opt-in. Per ADR-005, one composable per
// feature family: layer the install-wide `features.money` flag (from
// `useFeatureFlags`, server-owned via `/api/health`) with the per-user
// `money_features_enabled` flag (from `authStore.currentUser`, server-
// owned via `/api/users/me`). Both must be true for any dollar surface
// to render.
//
// Consumers use this composable instead of touching either layer
// directly. Render gates land in their own chunks (C-4 Chunk 9 cost
// estimate, C-2 plan budgets, dashboard budget card, etc.) and read a
// single `moneyEnabled.value` boolean from here.

import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useAuthStore } from 'src/stores/authStore';
import { useFeatureFlags } from 'src/composables/useFeatureFlags';

export function useMoneyEnabled() {
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);
    const { money: installMoney } = useFeatureFlags();

    const installEnabled = computed(() => installMoney.value);
    const userEnabled = computed(() => !!currentUser.value?.money_features_enabled);
    /** Both layers must be on for any dollar surface to render. */
    const moneyEnabled = computed(() => installEnabled.value && userEnabled.value);

    return {
        moneyEnabled,
        installEnabled,
        userEnabled,
    };
}
