<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Meal reconciliation"
            description="How Dora handles past-day meal-plan entries — assume they were cooked (and just keep a log), or hold them pending for you to confirm."
            :icon="ICONS.event_note"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <template #title>Assume past-day meals were cooked</template>
                <template #description>
                    When on, past-day plan entries are silently marked cooked
                    at the day-roll and the recipe pool drains automatically —
                    Dora keeps a read-only <strong>log</strong> of what she did,
                    and doesn't nag you to confirm anything. When off, past-day
                    entries stay pending and land on the reconcile page for you
                    to confirm each — Cooked, Different portions, Cooked later,
                    or Didn't cook.
                </template>

                <SettingsRow label="Auto-drain">
                    <q-toggle
                        :model-value="autoDrainDraft"
                        @update:model-value="onAutoDrainChange"
                    />
                </SettingsRow>
            </SettingsSection>

            <hr class="settings-divider" />

            <SettingsSection>
                <template #title>{{ autoDrainDraft ? 'Meal log' : 'Reconcile past meals' }}</template>
                <template #description>
                    <template v-if="autoDrainDraft">
                        See what Dora did with past-day meals. Everyone can open
                        this — it isn't admin-only.
                    </template>
                    <template v-else>
                        Walk any past-day entries that haven't been confirmed.
                        Everyone can open this — it isn't admin-only.
                    </template>
                </template>

                <SettingsRow label="Open">
                    <BaseButton
                        variant="secondary"
                        :label="autoDrainDraft ? 'View meal log' : 'Go to reconcile'"
                        :icon="ICONS.event_note"
                        :to="'/meal-plans/reconcile'"
                    />
                </SettingsRow>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { refreshReconcilePolicy } from 'src/composables/useReconcilePolicy';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import BaseButton from 'src/components/BaseButton.vue';

    // FU-317 Chunk 6 — the single install-wide dial for the reconcile
    // feature (proposal D5). Same eager-save shape as the neighbouring
    // stocktake page.

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const autoDrainDraft = ref<boolean>(true);
    let savedAutoDrain = true;

    async function onAutoDrainChange(next: boolean) {
        if (next === savedAutoDrain) return;
        try {
            const result = await api.updateAsync({ auto_drain_past_meals: next });
            savedAutoDrain = result.auto_drain_past_meals;
            autoDrainDraft.value = savedAutoDrain;
            // Re-probe /health so `/meal-plans/reconcile` flips between the log
            // (auto) and the runner (manual) without a full reload.
            void refreshReconcilePolicy();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: savedAutoDrain
                    ? 'Past meals will auto-drain.'
                    : 'Past meals will wait for you to confirm.',
            });
        } catch (err) {
            autoDrainDraft.value = savedAutoDrain;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save reconcile setting.',
                caption: toastCaption(err),
            });
        }
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            const s = await api.getAsync();
            if (typeof s.auto_drain_past_meals === 'boolean') {
                savedAutoDrain = s.auto_drain_past_meals;
                autoDrainDraft.value = savedAutoDrain;
            }
        } catch {
            // Leave defaults; nothing else on the page depends on the fetch.
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .settings-divider {
        border: 0;
        height: 1px;
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        margin: 8px 0;
    }
</style>
