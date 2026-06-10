// C-cross Chunk 3 — nutrition mode. ADR-005 family pattern: layer the
// install-wide `features.nutrition` flag (from useFeatureFlags) with
// the per-user `nutrition_mode` (from authStore.currentUser). Returns
// the active mode + derived booleans so consumers can gate either on
// "is nutrition enabled at all?" or "is the user in simple mode?".

import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useAuthStore } from 'src/stores/authStore';
import { useFeatureFlags } from 'src/composables/useFeatureFlags';

export const NUTRITION_MODE_VALUES = ['off', 'simple', 'complex'] as const;
export type NutritionMode = typeof NUTRITION_MODE_VALUES[number];

export function useNutritionMode() {
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);
    const {
        nutrition: installNutrition,
        nutritionComplexAvailable,
    } = useFeatureFlags();

    const installEnabled = computed(() => installNutrition.value);
    const userMode = computed<NutritionMode>(() => {
        const raw = currentUser.value?.nutrition_mode;
        return NUTRITION_MODE_VALUES.includes(raw as NutritionMode)
            ? (raw as NutritionMode)
            : 'off';
    });

    /** Effective mode the UI should obey. Install OFF forces `off`; the
     *  user's per-account pick applies when install is on. */
    const mode = computed<NutritionMode>(() =>
        installEnabled.value ? userMode.value : 'off',
    );

    const nutritionEnabled = computed(() => mode.value !== 'off');
    const isSimple = computed(() => mode.value === 'simple');
    const isComplex = computed(() => mode.value === 'complex');

    /** Whether the user can pick `complex` right now — install on AND
     *  admin has configured a nutrition source seam. The Settings
     *  toggle reads this to decide whether to disable the `complex`
     *  button + show the "ask admin to configure" caption. */
    const complexAvailable = computed(
        () => installEnabled.value && nutritionComplexAvailable.value,
    );

    return {
        mode,
        userMode,
        installEnabled,
        nutritionEnabled,
        isSimple,
        isComplex,
        complexAvailable,
    };
}
