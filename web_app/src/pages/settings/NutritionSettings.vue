<template>
    <div v-if="!currentUser">
        <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
    </div>

    <div v-else class="settings-page">
        <SettingsPageHeader
            title="Nutrition"
            description="Off by default. Simple adds a single kcal number per recipe that you type in. Complex would derive nutrition from a database — not built yet."
        />

        <SettingsSection>
            <template #title>Mode</template>
            <template #description>
                <strong>Complex</strong> stays disabled until an admin
                configures a nutrition source.
            </template>

            <SettingsRow label="Per-user nutrition mode">
                <DoraSegmented
                    :model-value="currentUser.nutrition_mode"
                    :options="nutritionToggleOptions"
                    :disabled="!nutritionInstallEnabled || saving"
                    @update:model-value="onNutritionModeChange"
                />
            </SettingsRow>

            <div
                v-if="!nutritionInstallEnabled"
                class="settings-page__note dora-text-muted"
            >
                This install has nutrition turned off. Ask an admin to
                enable it in System → Features.
            </div>
            <div
                v-else-if="currentUser.nutrition_mode === 'complex' && !complexAvailable"
                class="settings-page__note dora-text-muted"
            >
                Complex mode needs an admin-configured nutrition source.
            </div>
        </SettingsSection>
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
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import DoraSegmented, { type DoraSegmentedOption } from 'src/components/settings/DoraSegmented.vue';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    const {
        installEnabled: nutritionInstallEnabled,
        complexAvailable,
    } = useNutritionMode();
    const nutritionToggleOptions = computed<DoraSegmentedOption<NutritionMode>[]>(() => [
        { label: 'Off', value: 'off' },
        { label: 'Simple', value: 'simple' },
        { label: 'Complex', value: 'complex', disabled: !complexAvailable.value },
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

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .settings-page__note {
        font-size: 0.8125rem;
        line-height: 1.4;
        margin-top: 4px;
    }
</style>
