<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Nutrition"
            description="How much nutrition detail Dora tracks. This is install-wide — one setting for the whole household, not per person."
            :icon="ICONS.restaurant"
        />

        <SettingsSection>
            <template #title>Mode</template>
            <template #description>
                <strong>Off</strong> hides nutrition everywhere.
                <strong>Simple</strong> adds one kcal number you type in per recipe.
                <strong>Complex</strong> links stock items to a food catalogue and
                works recipe nutrition out from those links.
            </template>

            <SettingsRow label="Nutrition mode">
                <DoraSegmented
                    :model-value="mode"
                    :options="modeOptions"
                    :disabled="saving"
                    @update:model-value="onModeChange"
                />
            </SettingsRow>

            <div
                v-if="mode === 'complex' && !anyAvailable"
                class="settings-page__note dora-text-muted"
            >
                Complex is on, but nothing can answer a lookup yet — download a
                food dataset below, or allow Open Food Facts.
            </div>
        </SettingsSection>

        <template v-if="mode === 'complex'">
            <hr class="settings-divider" />

            <SettingsSection>
                <template #title>Food datasets</template>
                <template #description>
                    Downloaded once and searched offline. USDA data is public
                    domain, so it stays on your server with no strings attached.
                    Best for generic ingredients — "banana", "flour" — which is
                    what recipes actually name.
                </template>

                <div v-if="loading" class="settings-page__note dora-text-muted">
                    Checking what's installed…
                </div>

                <div v-for="source in datasetSources" :key="source.id" class="dataset-row">
                    <div class="dataset-row__main">
                        <div class="dataset-row__head">
                            <span class="dataset-row__label">{{ source.label }}</span>
                            <q-chip
                                v-if="source.available"
                                dense
                                square
                                size="sm"
                                class="dora-bg-positive-soft text-positive"
                            >
                                {{ source.food_count.toLocaleString() }} foods
                            </q-chip>
                        </div>
                        <div class="dataset-row__status dora-text-muted">
                            {{ statusLine(source) }}
                        </div>
                    </div>
                    <BaseButton
                        :variant="source.available ? 'ghost' : 'secondary'"
                        :label="source.available ? 'Re-download' : 'Download'"
                        :disable="isBusy(source)"
                        :loading="isBusy(source)"
                        @click="onImport(source)"
                    />
                </div>
            </SettingsSection>

            <hr class="settings-divider" />

            <SettingsSection>
                <template #title>Other sources</template>
                <template #description>
                    Optional extras searched alongside the datasets. Every result
                    in the picker is labelled with where it came from.
                </template>

                <SettingsRow
                    label="Open Food Facts"
                    help="Looks up packaged products by barcode. Needs no key, but does reach the internet — turn it off on an offline install."
                >
                    <q-toggle
                        :model-value="offLookupEnabled"
                        :disable="saving"
                        @update:model-value="onOffLookupChange"
                    />
                </SettingsRow>

                <SettingsRow
                    label="USDA API key"
                    help="Optional. Query USDA live instead of holding the dataset on disk. Free from api.data.gov; about 1,000 lookups an hour."
                >
                    <q-input
                        v-model="usdaKeyDraft"
                        dense
                        outlined
                        type="password"
                        placeholder="Paste a key"
                        style="min-width: 240px"
                        :disable="saving"
                        @blur="onUsdaKeySave"
                        @keydown.enter.prevent="onUsdaKeySave"
                    />
                </SettingsRow>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    // Nutrition is install-wide (owner call 2026-08-14) — this page replaces
    // the per-user Settings → Nutrition page, which mostly existed to tell you
    // to go ask an admin. Mode + complex-mode source config in one place.
    import { ICONS } from 'src/style/icons';
    import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
    import { useSettingsSave } from 'src/composables/useSettingsSave';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import AppSettingsApiService, {
        type UpdateAppSettingsCommand,
    } from 'src/services/api/appSettingsApiService';
    import NutritionApiService, {
        type NutritionSourceStatus,
    } from 'src/services/api/nutritionApiService';
    import BaseButton from 'src/components/BaseButton.vue';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import DoraSegmented, { type DoraSegmentedOption } from 'src/components/settings/DoraSegmented.vue';

    type NutritionMode = 'off' | 'simple' | 'complex';

    const nutritionApi = new NutritionApiService();
    const appSettingsApi = new AppSettingsApiService();
    const { update, notifyError } = useSettingsSave();
    const { refresh: refreshFlags } = useFeatureFlags();

    const modeOptions: DoraSegmentedOption<NutritionMode>[] = [
        { label: 'Off', value: 'off' },
        { label: 'Simple', value: 'simple' },
        { label: 'Complex', value: 'complex' },
    ];

    const mode = ref<NutritionMode>('off');
    const sources = ref<NutritionSourceStatus[]>([]);
    const anyAvailable = ref(false);
    const offLookupEnabled = ref(true);
    const usdaKeyDraft = ref('');
    const savedUsdaKey = ref('');
    const loading = ref(true);
    const saving = ref(false);

    const datasetSources = computed(() =>
        sources.value.filter((s) => s.kind === 'dataset'),
    );

    function isBusy(source: NutritionSourceStatus): boolean {
        return ['downloading', 'parsing', 'saving'].includes(source.phase ?? '');
    }

    function statusLine(source: NutritionSourceStatus): string {
        switch (source.phase) {
            case 'downloading': return 'Downloading…';
            case 'parsing': return 'Reading the data…';
            case 'saving': return 'Saving foods…';
            case 'error': return source.error ?? 'That download failed.';
            default:
                return source.available
                    ? 'Installed and searchable.'
                    : 'Not downloaded yet.';
        }
    }

    async function refreshSources() {
        try {
            const res = await nutritionApi.getSourcesAsync();
            mode.value = res.mode;
            sources.value = res.sources;
            anyAvailable.value = res.any_available;
        } catch (err) {
            notifyError('Could not read the nutrition sources.', err);
        } finally {
            loading.value = false;
        }
    }

    // Poll only while an import is actually running, so an idle admin page
    // isn't hitting the server every couple of seconds.
    let pollTimer: ReturnType<typeof setInterval> | null = null;
    function stopPolling() {
        if (pollTimer !== null) { clearInterval(pollTimer); pollTimer = null; }
    }
    function ensurePolling() {
        if (pollTimer !== null) return;
        pollTimer = setInterval(() => {
            void refreshSources().then(() => {
                if (!datasetSources.value.some(isBusy)) stopPolling();
            });
        }, 2500);
    }

    async function loadSettings() {
        try {
            const settings = await appSettingsApi.getAsync();
            offLookupEnabled.value = settings.nutrition_off_lookup_enabled;
            savedUsdaKey.value = settings.nutrition_usda_api_key ?? '';
            usdaKeyDraft.value = savedUsdaKey.value;
        } catch (err) {
            notifyError('Could not read the nutrition settings.', err);
        }
    }

    // R-010 — typed against the real command shape, not a loose record, so a
    // renamed setting fails here rather than silently no-op'ing at runtime.
    async function patch(message: string, body: UpdateAppSettingsCommand) {
        saving.value = true;
        try {
            await update(message, () => appSettingsApi.updateAsync(body));
            // The mode drives /api/health gates all over the app; refresh the
            // cached flag map so other surfaces don't run on a stale answer.
            await refreshFlags();
        } finally {
            saving.value = false;
        }
    }

    async function onModeChange(value: NutritionMode) {
        const previous = mode.value;
        mode.value = value;
        try {
            await patch(`Nutrition set to ${value}.`, { nutrition_mode: value });
            await refreshSources();
        } catch {
            mode.value = previous;
        }
    }

    async function onOffLookupChange(value: boolean) {
        const previous = offLookupEnabled.value;
        offLookupEnabled.value = value;
        try {
            await patch(
                value ? 'Open Food Facts lookups on.' : 'Open Food Facts lookups off.',
                { nutrition_off_lookup_enabled: value },
            );
            await refreshSources();
        } catch {
            offLookupEnabled.value = previous;
        }
    }

    async function onUsdaKeySave() {
        const next = usdaKeyDraft.value.trim();
        if (next === savedUsdaKey.value) return;
        try {
            await patch('USDA API key saved.', { nutrition_usda_api_key: next });
            savedUsdaKey.value = next;
            await refreshSources();
        } catch {
            usdaKeyDraft.value = savedUsdaKey.value;
        }
    }

    async function onImport(source: NutritionSourceStatus) {
        try {
            const res = await nutritionApi.startDatasetImportAsync(source.id);
            sources.value = res.sources;
            anyAvailable.value = res.any_available;
            ensurePolling();
        } catch (err) {
            notifyError(`Could not start the ${source.label} download.`, err);
        }
    }

    onMounted(async () => {
        await Promise.all([refreshSources(), loadSettings()]);
        if (datasetSources.value.some(isBusy)) ensurePolling();
    });

    onBeforeUnmount(stopPolling);
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .settings-page__note {
        font-size: 0.8125rem;
        line-height: 1.4;
        margin-top: 4px;
    }
    .settings-divider {
        border: 0;
        height: 1px;
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        margin: 0;
    }
    .dataset-row {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        padding: var(--space-3) 0;
    }
    .dataset-row + .dataset-row {
        border-top: 1px solid var(--divider);
    }
    .dataset-row__main { flex: 1 1 auto; min-width: 0; }
    .dataset-row__head {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        flex-wrap: wrap;
    }
    .dataset-row__label {
        font-size: 0.9375rem;
        color: var(--text-primary);
    }
    .dataset-row__status {
        font-size: 0.8125rem;
        line-height: 1.4;
        margin-top: 2px;
    }
</style>
