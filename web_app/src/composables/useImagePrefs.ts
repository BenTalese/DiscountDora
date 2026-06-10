// C-cross Chunk 5 — image-display opt-ins. ADR-005 family composable:
// owns both the per-user `show_*_images` flags AND the optimistic-flip
// setters that PATCH /me. Surfaces consume `showRecipeImages` /
// `showStockImages` as render gates; inline toggle buttons (recipes
// overview ships its button this chunk; stock overview's button comes
// with the C-1 row redesign — FU-106) call the setters.
//
// Unlike `useMoneyEnabled` / `useNutritionMode`, there's **no install-
// wide layer here** — image rendering is a personal UI preference, not
// a feature-availability gate. The proposal §2.8 calls this out
// explicitly.

import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useAuthStore } from 'src/stores/authStore';

export function useImagePrefs() {
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    // Default to `true` when the user hasn't loaded yet so the first
    // paint shows photos (avoids a flash of placeholders on login).
    const showRecipeImages = computed(
        () => currentUser.value?.show_recipe_images ?? true,
    );
    const showStockImages = computed(
        () => currentUser.value?.show_stock_images ?? true,
    );

    async function setRecipeImages(next: boolean): Promise<void> {
        // The authStore's updateMeAsync optimistically updates the local
        // user object + PATCHes the server; on failure it'll throw and
        // leave the in-memory user as-is, which is the right behaviour
        // here too (the toggle button's caller handles the error toast).
        await authStore.updateMeAsync({ show_recipe_images: next });
    }
    async function setStockImages(next: boolean): Promise<void> {
        await authStore.updateMeAsync({ show_stock_images: next });
    }

    return {
        showRecipeImages,
        showStockImages,
        setRecipeImages,
        setStockImages,
    };
}
