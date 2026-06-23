<template>
    <q-card flat bordered>
        <q-card-section>
            <div class="text-subtitle1 text-weight-medium">
                <q-icon :name="ICONS.notifications" size="20px" class="q-mr-xs" />
                Alert thresholds
            </div>
            <div class="text-caption dora-text-muted">
                Household-wide tuning for inventory alerts. These shape the
                alerts list and the location heatmap for everyone; each
                account's own on/off and priority preferences layer on top.
            </div>
        </q-card-section>
        <q-separator />

        <q-card-section v-if="!isAdmin">
            <q-banner class="dora-bg-negative-soft text-negative" dense rounded>
                You don't have admin permissions to view this page.
            </q-banner>
        </q-card-section>

        <q-card-section v-else-if="!loading" class="row q-col-gutter-md items-start">
            <q-input
                v-model.number="expiringSoonWindowDraft"
                type="number"
                label="Expiring-soon window (days)"
                outlined
                dense
                class="col-12 col-sm-6"
                :min="1"
                :max="365"
                :disable="savingThresholds"
                :loading="savingThresholds"
                hint="Items within this many days of their expiry date show as 'expiring soon'."
                @blur="() => onSaveThreshold('expiring_soon_window_days', expiringSoonWindowDraft)"
            />
            <q-input
                v-model.number="stocktakeDefaultDraft"
                type="number"
                label="Default stocktake reminder (days)"
                outlined
                dense
                class="col-12 col-sm-6"
                :min="0"
                :max="3650"
                :disable="savingThresholds"
                :loading="savingThresholds"
                hint="Pre-filled check-in cadence for new stock items (0 = no reminder)."
                @blur="() => onSaveThreshold('default_days_until_stocktake_alert', stocktakeDefaultDraft)"
            />
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, reactive, ref } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);

    // ── Alert thresholds (C-9.2) ─────────────────────────────────────────
    // Household-wide. Saved on blur (one PATCH per committed edit); a no-op
    // blur (unchanged value) is skipped.
    const expiringSoonWindowDraft = ref<number>(7);
    const stocktakeDefaultDraft = ref<number>(0);
    const savedThresholds = reactive({
        expiring_soon_window_days: 7,
        default_days_until_stocktake_alert: 0,
    });
    const savingThresholds = ref(false);

    type ThresholdKey = 'expiring_soon_window_days' | 'default_days_until_stocktake_alert';

    function resetThresholdDrafts() {
        expiringSoonWindowDraft.value = savedThresholds.expiring_soon_window_days;
        stocktakeDefaultDraft.value = savedThresholds.default_days_until_stocktake_alert;
    }

    async function onSaveThreshold(key: ThresholdKey, value: number) {
        // q-input can hand back '' / NaN mid-edit; ignore those and reset the
        // field, and skip a no-op save (blur fires even with no change).
        if (typeof value !== 'number' || Number.isNaN(value)) {
            resetThresholdDrafts();
            return;
        }
        if (value === savedThresholds[key]) return;
        savingThresholds.value = true;
        try {
            const result = await api.updateAsync({ [key]: value });
            savedThresholds.expiring_soon_window_days = result.expiring_soon_window_days;
            savedThresholds.default_days_until_stocktake_alert = result.default_days_until_stocktake_alert;
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
                caption: describeApiError(err) || '',
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
            if (s.default_days_until_stocktake_alert !== undefined) {
                savedThresholds.default_days_until_stocktake_alert = s.default_days_until_stocktake_alert;
                stocktakeDefaultDraft.value = s.default_days_until_stocktake_alert;
            }
        } catch {
            // Leave defaults.
        } finally {
            loading.value = false;
        }
    });
</script>
