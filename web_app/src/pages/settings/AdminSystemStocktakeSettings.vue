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
            <!-- 2026-08-20 owner feedback — the install-wide master switch.
                 Off hides the whole surface: the Stock-overview button, the
                 "Needs check" filter, the per-item toggle on an item's detail
                 page, and the queue itself (the server stops resolving an
                 overdue set, so the alerts bell goes quiet too). This page is
                 the only way back on, which is why it stays in the nav and
                 keeps rendering when the feature is off. -->
            <SettingsSection>
                <template #title>Stocktake</template>
                <template #description>
                    Stocktake is the guided count that walks you through items
                    Dora hasn't seen in a while. Turn it off and every
                    stocktake control disappears from the app — nothing is
                    deleted, and turning it back on restores the queue.
                </template>

                <SettingsRow label="Enabled">
                    <q-toggle
                        :model-value="enabledDraft"
                        @update:model-value="onEnabledChange"
                    />
                </SettingsRow>

                <SettingsRow
                    v-if="enabledDraft"
                    label="New items"
                    help="Whether an item you add joins the stocktake rotation straight away. Off means you opt each item in from its detail page."
                >
                    <q-toggle
                        :model-value="optInDraft"
                        @update:model-value="onOptInChange"
                    />
                </SettingsRow>
            </SettingsSection>

            <hr v-if="enabledDraft" class="settings-divider" />

            <SettingsSection v-if="enabledDraft">
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
                        @update:model-value="onBandChange"
                    />
                </SettingsRow>
            </SettingsSection>

            <hr v-if="enabledDraft" class="settings-divider" />

            <SettingsSection v-if="enabledDraft">
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
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
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
    // 2026-08-20 — the master switch + the new-item opt-in default.
    const enabledDraft = ref<boolean>(true);
    const optInDraft = ref<boolean>(true);
    // Track the last-saved value separately so a failed save can revert
    // the draft without a re-fetch round-trip.
    let savedBand: CadenceBand = 'fortnightly';
    let savedAuto = true;
    let savedEnabled = true;
    let savedOptIn = true;

    // Flipping the master switch changes what `/api/health features.stocktake`
    // answers, and every gated surface reads that through this one cache — so
    // refresh it here or the Stock-overview button stays visible until a
    // reload (the FU-580 lesson from the scanning flag).
    const { refresh: featureFlags$refresh } = useFeatureFlags();

    async function onEnabledChange(next: boolean) {
        if (next === savedEnabled) return;
        try {
            const result = await api.updateAsync({ stocktake_enabled: next });
            savedEnabled = result.stocktake_enabled;
            enabledDraft.value = savedEnabled;
            await featureFlags$refresh();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: savedEnabled ? 'Stocktake is on.' : 'Stocktake is off.',
            });
        } catch (err) {
            enabledDraft.value = savedEnabled;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save the stocktake switch.',
                caption: toastCaption(err),
            });
        }
    }

    async function onOptInChange(next: boolean) {
        if (next === savedOptIn) return;
        try {
            const result = await api.updateAsync({
                stocktake_new_items_opt_in: next,
            });
            savedOptIn = result.stocktake_new_items_opt_in;
            optInDraft.value = savedOptIn;
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: savedOptIn
                    ? 'New items will join the stocktake rotation.'
                    : 'New items start out of the stocktake rotation.',
            });
        } catch (err) {
            optInDraft.value = savedOptIn;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save the new-item default.',
                caption: toastCaption(err),
            });
        }
    }

    async function onBandChange(next: CadenceBand) {
        if (next === savedBand) return;
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
        }
    }

    async function onAutoChange(next: boolean) {
        if (next === savedAuto) return;
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
            if (typeof s.stocktake_enabled === 'boolean') {
                savedEnabled = s.stocktake_enabled;
                enabledDraft.value = savedEnabled;
            }
            if (typeof s.stocktake_new_items_opt_in === 'boolean') {
                savedOptIn = s.stocktake_new_items_opt_in;
                optInDraft.value = savedOptIn;
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
