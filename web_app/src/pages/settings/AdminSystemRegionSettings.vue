<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Region & locale"
            description="Where this household lives, moneywise and timewise. The timezone fixes the &quot;today&quot; boundary on the meal planner; the currency and display locale drive every money render across Dora — dashboard, shopping lists, reports, price history."
            :icon="ICONS.language"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <!-- Timezone ─────────────────────────────────────────────── -->
            <SettingsSection>
                <template #title>Household timezone</template>
                <template #description>
                    Dates like "today" on the meal planner are worked out here,
                    so they stay correct no matter where the server runs.
                </template>

                <SettingsRow stacked>
                    <div class="row q-col-gutter-sm items-end">
                        <q-select
                            :model-value="timezoneDraft"
                            :options="timezoneOptions"
                            outlined
                            dense
                            use-input
                            input-debounce="0"
                            options-dense
                            class="col-12 col-sm-8"
                            :loading="savingTimezone"
                            @filter="onTimezoneFilter"
                            @update:model-value="onSaveTimezone"
                        />
                        <!-- carve-out — raw q-btn: outline with Quasar 'secondary'
                             palette color has no matching BaseButton variant. -->
                        <q-btn
                            color="secondary"
                            no-caps
                            outline
                            label="Use this device"
                            :disable="savingTimezone"
                            @click="onDetectTimezone"
                        />
                    </div>
                </SettingsRow>
            </SettingsSection>

            <hr class="settings-divider" />

            <!-- Currency & display locale ─────────────────────────────── -->
            <SettingsSection>
                <template #title>Currency & display locale</template>
                <template #description>
                    Currency uses the ISO 4217 code (e.g. AUD, USD, EUR, GBP).
                    Locale uses a BCP-47 tag (e.g. en-AU, en-US, de-DE, fr-FR) —
                    it drives symbol placement, decimal + grouping separators,
                    and the default speech-recognition language.
                </template>

                <SettingsRow label="Currency">
                    <q-input
                        :model-value="currencyDraft"
                        outlined
                        dense
                        maxlength="3"
                        style="max-width: 120px; text-transform: uppercase"
                        :error="currencyError !== null"
                        :error-message="currencyError ?? ''"
                        hint="3-letter ISO 4217 code"
                        @update:model-value="onCurrencyInput"
                        @blur="onSaveCurrency"
                        @keydown.enter.prevent="onSaveCurrency"
                    />
                </SettingsRow>

                <SettingsRow label="Locale">
                    <q-input
                        :model-value="localeDraft"
                        outlined
                        dense
                        maxlength="35"
                        style="max-width: 200px"
                        :error="localeError !== null"
                        :error-message="localeError ?? ''"
                        hint="BCP-47 tag, e.g. en-AU"
                        @update:model-value="onLocaleInput"
                        @blur="onSaveLocale"
                        @keydown.enter.prevent="onSaveLocale"
                    />
                </SettingsRow>

                <SettingsRow label="Preview">
                    <div class="row items-center q-gutter-md">
                        <div class="text-body1">
                            <strong>{{ formatMoney(12.5) }}</strong>
                            <span class="dora-text-muted q-ml-xs">· {{ formatMoney(1234.56) }}</span>
                        </div>
                        <!-- carve-out — raw q-btn: outline with Quasar 'secondary'
                             palette color has no matching BaseButton variant. -->
                        <q-btn
                            color="secondary"
                            no-caps
                            outline
                            size="sm"
                            label="Use this device"
                            :disable="savingLocale"
                            @click="onDetectLocaleFromDevice"
                        />
                    </div>
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
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import { formatMoney, refreshMoneyPolicy } from 'src/composables/useMoney';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);

    // ── Timezone ──────────────────────────────────────────────────────
    const timezoneDraft = ref<string>('UTC');
    const savingTimezone = ref(false);

    type IntlWithSupported = typeof Intl & { supportedValuesOf?: (key: string) => string[] };
    const _supportedValuesOf = (Intl as IntlWithSupported).supportedValuesOf;
    const allTimezones: string[] = _supportedValuesOf ? _supportedValuesOf('timeZone') : ['UTC'];
    const timezoneOptions = ref<string[]>(allTimezones);

    function onTimezoneFilter(val: string, update: (cb: () => void) => void) {
        update(() => {
            const needle = val.toLowerCase();
            timezoneOptions.value = needle
                ? allTimezones.filter((t) => t.toLowerCase().includes(needle))
                : allTimezones;
        });
    }

    function onDetectTimezone() {
        const detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
        if (detected) void onSaveTimezone(detected);
    }

    async function onSaveTimezone(value: string) {
        if (!value || value === timezoneDraft.value) return;
        savingTimezone.value = true;
        try {
            const result = await api.updateAsync({ timezone: value });
            timezoneDraft.value = result.timezone;
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: `Household timezone set to ${result.timezone}.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save the timezone.',
                caption: toastCaption(err),
            });
        } finally {
            savingTimezone.value = false;
        }
    }

    // ── Currency & locale ─────────────────────────────────────────────
    const savingLocale = ref(false);
    const currencyDraft = ref<string>('AUD');
    const localeDraft = ref<string>('en-AU');
    const currencyError = ref<string | null>(null);
    const localeError = ref<string | null>(null);

    // Track the last-saved values so blur-with-no-change is a no-op (don't
    // fire a PATCH per focus loss).
    let lastSavedCurrency = 'AUD';
    let lastSavedLocale = 'en-AU';

    function onCurrencyInput(v: string | number | null) {
        currencyDraft.value = String(v ?? '').toUpperCase();
        currencyError.value = null;
    }

    function onLocaleInput(v: string | number | null) {
        localeDraft.value = String(v ?? '');
        localeError.value = null;
    }

    async function onSaveCurrency() {
        const value = currencyDraft.value.trim().toUpperCase();
        if (!value || value === lastSavedCurrency) return;
        if (value.length !== 3 || !/^[A-Z]{3}$/.test(value)) {
            currencyError.value = 'Must be a 3-letter ISO 4217 code.';
            return;
        }
        savingLocale.value = true;
        try {
            const result = await api.updateAsync({ currency: value });
            currencyDraft.value = result.currency;
            lastSavedCurrency = result.currency;
            await refreshMoneyPolicy();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: `Currency set to ${result.currency}.`,
            });
        } catch (err) {
            currencyError.value = 'Could not save the currency.';
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save the currency.',
                caption: toastCaption(err),
            });
        } finally {
            savingLocale.value = false;
        }
    }

    async function onSaveLocale() {
        const value = localeDraft.value.trim();
        if (!value || value === lastSavedLocale) return;
        // Belt-and-braces: ask the browser's own Intl.Locale to parse it
        // before the round-trip — matches the server-side BCP-47 check
        // and gives an immediate error without a network round-trip.
        try {
            new Intl.Locale(value);
        } catch {
            localeError.value = 'Not a valid BCP-47 locale tag.';
            return;
        }
        savingLocale.value = true;
        try {
            const result = await api.updateAsync({ locale: value });
            localeDraft.value = result.locale;
            lastSavedLocale = result.locale;
            await refreshMoneyPolicy();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: `Display locale set to ${result.locale}.`,
            });
        } catch (err) {
            localeError.value = 'Could not save the locale.';
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save the locale.',
                caption: toastCaption(err),
            });
        } finally {
            savingLocale.value = false;
        }
    }

    function onDetectLocaleFromDevice() {
        // Locale from the browser. Currency isn't in the browser API —
        // we can only offer to detect the locale; the admin still picks
        // the currency explicitly (it's a household choice, not a device
        // choice — a device in the AU can be spending in USD).
        const detected = (typeof navigator !== 'undefined' && navigator.language) || '';
        if (detected) {
            localeDraft.value = detected;
            void onSaveLocale();
        }
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            const s = await api.getAsync();
            if (s.timezone) timezoneDraft.value = s.timezone;
            if (s.currency) {
                currencyDraft.value = s.currency;
                lastSavedCurrency = s.currency;
            }
            if (s.locale) {
                localeDraft.value = s.locale;
                lastSavedLocale = s.locale;
            }
            // FU-600: the Preview renders through `formatMoney`, which reads the
            // module-level money policy. With money features off no money
            // surface mounts to trigger it lazily — so without this the preview
            // would show the AUD/en-AU defaults regardless of the saved policy.
            // Force a fresh read so the preview reflects the saved values.
            await refreshMoneyPolicy();
        } catch {
            // Leave the AU / UTC defaults; admin can retry once the DB is reachable.
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
        margin: 20px 0;
    }
</style>
