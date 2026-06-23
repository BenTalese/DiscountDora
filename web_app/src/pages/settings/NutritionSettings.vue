<template>
    <div v-if="!currentUser">
        <q-card flat bordered>
            <q-card-section>
                <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
            </q-card-section>
        </q-card>
    </div>

    <div v-else class="column q-gutter-md">
        <!-- C-cross Chunk 3 — per-user nutrition mode (proposal §2.3).
             Three-way toggle. `complex` is disabled when the install
             admin hasn't configured a nutrition source (the reserved
             seam). The per-recipe kcal field + cookbook kcal sort axis
             are C-4 Chunk 9, gated on this composable. -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Nutrition</div>
                <div class="text-caption dora-text-muted">
                    Off by default. <strong>Simple</strong> adds a single kcal
                    number per recipe that you type in.
                    <strong>Complex</strong> would derive nutrition from a
                    nutrition database — not built yet, and disabled until an
                    admin configures a source.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <div class="row items-center q-gutter-md">
                    <q-btn-toggle
                        :model-value="currentUser.nutrition_mode"
                        :options="nutritionToggleOptions"
                        no-caps
                        toggle-color="primary"
                        :disable="!nutritionInstallEnabled || saving"
                        @update:model-value="onNutritionModeChange"
                    />
                </div>
                <div
                    v-if="!nutritionInstallEnabled"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    This install has nutrition turned off. Ask an admin to
                    enable it in System → Features.
                </div>
                <div
                    v-else-if="currentUser.nutrition_mode === 'complex' && !complexAvailable"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    Complex mode needs an admin-configured nutrition source.
                </div>
            </q-card-section>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useAuthStore } from 'src/stores/authStore';
    import {
        useNutritionMode,
        type NutritionMode,
    } from 'src/composables/useNutritionMode';
    import { computed, ref } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    // C-cross Chunk 3 — nutrition opt-in layering. `complexAvailable`
    // gates the third toggle button + caption; the install flag gates
    // the whole control.
    const {
        installEnabled: nutritionInstallEnabled,
        complexAvailable,
    } = useNutritionMode();
    const nutritionToggleOptions = computed(() => [
        { label: 'Off', value: 'off' as NutritionMode },
        { label: 'Simple', value: 'simple' as NutritionMode },
        { label: 'Complex', value: 'complex' as NutritionMode, disable: !complexAvailable.value },
    ]);

    const saving = ref(false);

    function notifySuccess(message: string) {
        $q.notify({ type: 'positive', position: 'bottom-right', message });
    }
    function notifyError(message: string, err?: unknown) {
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            caption: describeApiError(err) || ''
        });
    }

    async function update<T>(label: string, run: () => Promise<T>): Promise<T | null> {
        saving.value = true;
        try {
            const result = await run();
            notifySuccess(label);
            return result;
        } catch (err) {
            notifyError(`Could not save ${label.toLowerCase()}.`, err);
            return null;
        } finally {
            saving.value = false;
        }
    }

    // C-cross Chunk 3 — per-user nutrition mode. Server rejects
    // `complex` when no nutrition source is configured; the toggle
    // option is also disabled in that state so this should never
    // 422 in normal use.
    async function onNutritionModeChange(value: NutritionMode) {
        const labelByMode: Record<NutritionMode, string> = {
            off: 'Nutrition turned off.',
            simple: 'Simple nutrition turned on.',
            complex: 'Complex nutrition turned on.',
        };
        await update(
            labelByMode[value],
            () => authStore.updateMeAsync({ nutrition_mode: value }),
        );
    }
</script>
