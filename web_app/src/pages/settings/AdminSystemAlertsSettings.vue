<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Alert thresholds"
            description="Household-wide tuning for inventory alerts. These shape the alerts list and the location heatmap for everyone; each account's own on/off and priority preferences layer on top."
            :icon="ICONS.notifications"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <template #title>Expiring-soon window</template>
                <template #description>
                    Items within this many days of their expiry date show as
                    "expiring soon".
                </template>

                <SettingsRow label="Days">
                    <q-input
                        v-model.number="expiringSoonWindowDraft"
                        type="number"
                        outlined
                        dense
                        style="max-width: 140px"
                        :min="1"
                        :max="365"
                        :loading="savingThresholds"
                        @blur="() => onSaveThreshold('expiring_soon_window_days', expiringSoonWindowDraft)"
                    />
                </SettingsRow>
            </SettingsSection>

            <!-- PROPOSAL_STOCKTAKE_MODE §7 — the "Default stocktake
                 reminder" section that used to live here (a numeric
                 days-per-item value backed by `default_days_until_
                 stocktake_alert`) is superseded by the band system.
                 The two new global dials live on the dedicated
                 Settings → Stocktake page. -->
        </template>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, reactive, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);

    const expiringSoonWindowDraft = ref<number>(7);
    const savedThresholds = reactive({
        expiring_soon_window_days: 7,
    });
    const savingThresholds = ref(false);

    type ThresholdKey = 'expiring_soon_window_days';

    function resetThresholdDrafts() {
        expiringSoonWindowDraft.value = savedThresholds.expiring_soon_window_days;
    }

    async function onSaveThreshold(key: ThresholdKey, value: number) {
        if (typeof value !== 'number' || Number.isNaN(value)) {
            resetThresholdDrafts();
            return;
        }
        if (value === savedThresholds[key]) return;
        savingThresholds.value = true;
        try {
            const result = await api.updateAsync({ [key]: value });
            savedThresholds.expiring_soon_window_days = result.expiring_soon_window_days;
            resetThresholdDrafts();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: 'Alert thresholds saved.',
            });
        } catch (err) {
            resetThresholdDrafts();
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save alert thresholds.',
                caption: toastCaption(err),
            });
        } finally {
            savingThresholds.value = false;
        }
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            const s = await api.getAsync();
            if (s.expiring_soon_window_days !== undefined) {
                savedThresholds.expiring_soon_window_days = s.expiring_soon_window_days;
                expiringSoonWindowDraft.value = s.expiring_soon_window_days;
            }
        } catch {
            // Leave defaults.
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
