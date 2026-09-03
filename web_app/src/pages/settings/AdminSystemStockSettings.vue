<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Stock"
            description="How Dora auto-adds items to your shopping list when they run low."
            :icon="ICONS.inventory_2"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <template #title>Auto-add on low</template>
                <template #description>
                    When a stock item transitions to Low or Out, Dora can
                    silently drop it onto your primary shopping list (with
                    an undoable toast). Pick which items this fires for.
                    Essential items are the ones you've marked with the
                    flag on the stock overview.
                </template>

                <SettingsRow label="Fire for">
                    <DoraSegmented
                        :model-value="modeDraft"
                        :options="MODE_OPTIONS"
                        @update:model-value="onModeChange"
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
    import type { AutoAddMode } from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import DoraSegmented, { type DoraSegmentedOption } from 'src/components/settings/DoraSegmented.vue';

    /**
     * FU-511 — install-wide auto-add mode. Replaces the retired per-item
     * `StockItem.auto_add_when_low` toggle. Single-value dial so we save
     * eagerly on change; no explicit Save button (matches the neighbouring
     * Stocktake page's pattern).
     */
    // 2026-09-03: was a raw `q-btn-toggle`, the last squared-off segmented
    // control on the settings pages. `DoraSegmented` is the same control with
    // the app's one anatomy and proper radiogroup semantics.
    const MODE_OPTIONS: DoraSegmentedOption<AutoAddMode>[] = [
        { label: 'Off', value: 'off' },
        { label: 'Essential only', value: 'essential_only' },
        { label: 'All items', value: 'all' },
    ];

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const modeDraft = ref<AutoAddMode>('essential_only');
    let savedMode: AutoAddMode = 'essential_only';

    async function onModeChange(next: AutoAddMode) {
        if (next === savedMode) return;
        try {
            const result = await api.updateAsync({ auto_add_mode: next });
            savedMode = result.auto_add_mode;
            modeDraft.value = savedMode;
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: 'Auto-add mode saved.',
            });
        } catch (err) {
            modeDraft.value = savedMode;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save auto-add mode.',
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
            if (s.auto_add_mode) {
                savedMode = s.auto_add_mode;
                modeDraft.value = savedMode;
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
</style>
