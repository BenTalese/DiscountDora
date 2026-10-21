// Nutrition depth — install-wide (owner call 2026-08-14).
//
// This used to layer an install-wide `features.nutrition` bool over a per-user
// `User.nutrition_mode`, which meant "is nutrition on?" had two answers and the
// personal settings page mostly existed to tell you to go ask an admin. Same
// double-switch shape money shed on 2026-08-12; nutrition now matches it.
//
// One source: `/api/health` `features.nutrition_mode`. No per-user layer, no
// authStore read.

import { computed } from 'vue';
import { useFeatureFlags } from 'src/composables/useFeatureFlags';

export const NUTRITION_MODE_VALUES = ['off', 'simple', 'complex'] as const;
export type NutritionMode = typeof NUTRITION_MODE_VALUES[number];

export function useNutritionMode() {
    const { nutritionMode, nutritionComplexUsable } = useFeatureFlags();

    const mode = computed<NutritionMode>(() => nutritionMode.value);
    const nutritionEnabled = computed(() => mode.value !== 'off');
    const isSimple = computed(() => mode.value === 'simple');
    const isComplex = computed(() => mode.value === 'complex');

    /** Complex is selected *and* a source can actually answer a lookup. The
     *  two are deliberately separate: an admin who picks complex before
     *  downloading a dataset should see "nothing installed yet", not a
     *  silently-off feature. */
    const complexUsable = computed(() => nutritionComplexUsable.value);

    return {
        mode,
        nutritionEnabled,
        isSimple,
        isComplex,
        complexUsable,
    };
}
