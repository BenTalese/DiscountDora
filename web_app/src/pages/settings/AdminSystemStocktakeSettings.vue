<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Stocktake"
            description="How often Dora asks you to check each item, and whether she self-tunes that per item from how fast it actually moves."
            :icon="ICONS.fact_check"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <template #title>Default check cadence</template>
                <template #description>
                    The baseline cadence applied to every item. Individual
                    items can move faster if they're flagged Essential (one
                    band faster) or if Auto self-tuning is on (below).
                </template>

                <SettingsRow label="Cadence">
                    <q-btn-toggle
                        :model-value="bandDraft"
                        :options="BAND_OPTIONS"
                        toggle-color="primary"
                        unelevated
                        no-caps
                        :disable="savingBand"
                        @update:model-value="onBandChange"
                    />
                </SettingsRow>
            </SettingsSection>

            <hr class="settings-divider" />

            <SettingsSection>
                <template #title>Auto self-tuning</template>
                <template #description>
                    When on, Dora checks fast-moving items more often and
                    stable ones less — driven by each item's stock-level
                    history. Turn off to hold every item at the default
                    cadence above. Essential items still move one band
                    faster either way.
                </template>

                <SettingsRow label="Auto">
                    <q-toggle
                        :model-value="autoDraft"
                        :disable="savingAuto"
                        @update:model-value="onAutoChange"
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
    import type { CadenceBand } from 'src/services/api/stocktakeApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    /**
     * PROPOSAL_STOCKTAKE_MODE §8 — the two global stocktake dials.
     * Backing AppSetting columns land in Chunk 1's migration
     * (d1f9c3a8b2e4). Everything is a single-value toggle so we save
     * eagerly on change; no explicit Save button needed (matches the
     * pattern the neighbouring Alert-thresholds page uses).
     */
    // q-btn-toggle's `options` prop wants a mutable array; keeping the
    // list mutable is fine here — nothing else in this component
    // mutates it, and the CadenceBand type still constrains the value.
    const BAND_OPTIONS: { label: string; value: CadenceBand }[] = [
        { label: 'Weekly', value: 'weekly' },
        { label: 'Fortnightly', value: 'fortnightly' },
        { label: 'Monthly', value: 'monthly' },
    ];

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const bandDraft = ref<CadenceBand>('fortnightly');
    const autoDraft = ref<boolean>(true);
    // Track the last-saved value separately so a failed save can revert
    // the draft without a re-fetch round-trip.
    let savedBand: CadenceBand = 'fortnightly';
    let savedAuto = true;
    const savingBand = ref(false);
    const savingAuto = ref(false);

    async function onBandChange(next: CadenceBand) {
        if (next === savedBand) return;
        savingBand.value = true;
        try {
            const result = await api.updateAsync({
                stocktake_default_cadence_band: next,
            });
            savedBand = result.stocktake_default_cadence_band;
            bandDraft.value = savedBand;
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: 'Default cadence saved.',
            });
        } catch (err) {
            bandDraft.value = savedBand;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save cadence.',
                caption: toastCaption(err),
            });
        } finally {
            savingBand.value = false;
        }
    }

    async function onAutoChange(next: boolean) {
        if (next === savedAuto) return;
        savingAuto.value = true;
        try {
            const result = await api.updateAsync({
                stocktake_auto_tuning_enabled: next,
            });
            savedAuto = result.stocktake_auto_tuning_enabled;
            autoDraft.value = savedAuto;
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: savedAuto ? 'Auto self-tuning on.' : 'Auto self-tuning off.',
            });
        } catch (err) {
            autoDraft.value = savedAuto;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save Auto setting.',
                caption: toastCaption(err),
            });
        } finally {
            savingAuto.value = false;
        }
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            const s = await api.getAsync();
            if (s.stocktake_default_cadence_band) {
                savedBand = s.stocktake_default_cadence_band;
                bandDraft.value = savedBand;
            }
            if (typeof s.stocktake_auto_tuning_enabled === 'boolean') {
                savedAuto = s.stocktake_auto_tuning_enabled;
                autoDraft.value = savedAuto;
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
