<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Region & locale"
            description="Where this household lives. Sets how money and dates are written, and which day counts as today."
            :icon="ICONS.language"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <!-- Preview first. The three fields below are abstractions
                 (ISO code, BCP-47 tag, IANA zone) whose only observable effect
                 is this line — so it leads, and it updates as you pick rather
                 than after a save round-trip. -->
            <div class="region-preview">
                <div class="region-preview__row">
                    <span class="region-preview__label">Money</span>
                    <span class="region-preview__value">{{ previewMoney }}</span>
                </div>
                <div class="region-preview__row">
                    <span class="region-preview__label">Dates</span>
                    <span class="region-preview__value">{{ previewDate }}</span>
                </div>
                <div class="region-preview__row">
                    <span class="region-preview__label">Today is</span>
                    <span class="region-preview__value">{{ previewToday }}</span>
                </div>
                <!-- One button replaces the two "Use this device" buttons that
                     used to sit in separate sections doing overlapping jobs.
                     It fills in everything the browser can actually tell us —
                     zone and locale — and leaves currency alone, because a
                     device in Australia can be spending in USD. -->
                <BaseButton
                    variant="secondary"
                    :icon="ICONS.place"
                    label="Match this device"
                    :disable="saving"
                    class="region-preview__detect"
                    @click="onMatchDevice"
                />
            </div>

            <SettingsSection>
                <SettingsRow
                    label="Currency"
                    help="What your prices are in."
                >
                    <q-select
                        :model-value="currencyDraft"
                        :options="currencyOptions"
                        outlined
                        dense
                        use-input
                        hide-selected
                        fill-input
                        emit-value
                        map-options
                        input-debounce="0"
                        options-dense
                        new-value-mode="add-unique"
                        class="region-field"
                        :error="currencyError !== null"
                        :error-message="currencyError ?? ''"
                        @filter="onCurrencyFilter"
                        @update:model-value="onPickCurrency"
                        @new-value="onPickCurrency"
                        @input-value="currencyTyped = $event"
                        @keydown.enter="onCurrencyEnter"
                        @blur="onCurrencyBlur"
                    />
                </SettingsRow>

                <SettingsRow
                    label="Language & format"
                    help="Decides symbol placement, decimal marks and date order."
                >
                    <q-select
                        :model-value="localeDraft"
                        :options="localeOptions"
                        outlined
                        dense
                        use-input
                        hide-selected
                        fill-input
                        emit-value
                        map-options
                        input-debounce="0"
                        options-dense
                        new-value-mode="add-unique"
                        class="region-field"
                        :error="localeError !== null"
                        :error-message="localeError ?? ''"
                        @filter="onLocaleFilter"
                        @update:model-value="onPickLocale"
                        @new-value="onPickLocale"
                        @input-value="localeTyped = $event"
                        @keydown.enter="onLocaleEnter"
                        @blur="onLocaleBlur"
                    />
                </SettingsRow>

                <SettingsRow
                    label="Timezone"
                    help="Fixes the &quot;today&quot; boundary, wherever the server runs."
                >
                    <q-select
                        :model-value="timezoneDraft"
                        :options="timezoneOptions"
                        outlined
                        dense
                        use-input
                        hide-selected
                        fill-input
                        input-debounce="0"
                        options-dense
                        class="region-field"
                        @filter="onTimezoneFilter"
                        @update:model-value="onSaveTimezone"
                    />
                </SettingsRow>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    // Owner call 2026-08-17 — the page was three stacked essays around four
    // bare text inputs, explaining ISO 4217 and BCP-47 to someone who just
    // wants dollars and DD/MM. Rebuilt around what the settings actually *do*:
    // a live preview at the top, then three labelled pickers with one line of
    // help each. Currency and locale became searchable selects of real
    // options (free text still accepted, for anything not on the list), and
    // the two scattered "Use this device" buttons collapsed into one.
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import BaseButton from 'src/components/BaseButton.vue';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import { refreshMoneyPolicy } from 'src/composables/useMoney';
    import { CURRENCY_CHOICES, LOCALE_CHOICES } from 'src/models/regionChoices';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const saving = ref(false);

    const timezoneDraft = ref<string>('UTC');
    const currencyDraft = ref<string>('AUD');
    const localeDraft = ref<string>('en-AU');
    const currencyError = ref<string | null>(null);
    const localeError = ref<string | null>(null);

    // Last-saved values, so a re-pick of the same option is a no-op instead of
    // a redundant PATCH.
    let lastSavedCurrency = 'AUD';
    let lastSavedLocale = 'en-AU';

    // What's currently *typed* into each combobox, tracked so leaving the
    // field commits it. `@new-value` alone only fires on Enter-with-the-popup-
    // open; someone who types "USD" and clicks away would otherwise be left
    // looking at a field that says USD while the install is still on AUD —
    // silently ignoring input is worse than rejecting it.
    const currencyTyped = ref('');
    const localeTyped = ref('');

    /** True when the text is one of the list's display labels rather than
     *  something the user typed. `fill-input` writes the label into the input
     *  after a pick ("AUD — Australian dollar"), so a commit path that didn't
     *  check this would try to save a display string. */
    function isChoiceLabel(choices: readonly { label: string }[], text: string): boolean {
        return choices.some((c) => c.label === text);
    }

    // Free text (a currency or language the shortlist doesn't carry) commits on
    // BOTH Enter and blur. Quasar's own `new-value-mode` Enter handling only
    // runs while the options popup is open, so typing a code and tabbing away
    // would otherwise be silently dropped — and an install in an unlisted
    // country would have no way to set its currency at all.
    //
    // Committing twice is harmless: `pendingCurrency` / `pendingLocale` below
    // swallow the duplicate, and the label guard means the post-pick reset
    // (`fill-input` rewrites the field to "AUD — Australian dollar") is never
    // mistaken for input. Both event orderings are therefore safe.
    //
    // The shape checks are deliberately silent rather than error-raising: a
    // half-typed "US" abandoned on blur should just be dropped, not shouted at.
    function onCurrencyEnter() { commitCurrency(); }
    function onCurrencyBlur() { commitCurrency(); }
    function onLocaleEnter() { commitLocale(); }
    function onLocaleBlur() { commitLocale(); }

    function commitCurrency() {
        const typed = currencyTyped.value.trim();
        if (!typed || isChoiceLabel(CURRENCY_CHOICES, typed)) return;
        if (!/^[A-Za-z]{3}$/.test(typed)) return;
        void onPickCurrency(typed);
    }

    function commitLocale() {
        const typed = localeTyped.value.trim();
        if (!typed || isChoiceLabel(LOCALE_CHOICES, typed)) return;
        try {
            new Intl.Locale(typed);
        } catch {
            return;
        }
        void onPickLocale(typed);
    }

    // ── Preview ───────────────────────────────────────────────────────
    // Built here from the *draft* values with plain Intl, not via
    // useMoney/useDateFormat: those two read the install's saved policy (they
    // are the authority for every real render in the app, R-003), which is
    // exactly the wrong thing for a preview of a choice you haven't committed.
    // Pure display maths on values already in hand — no server round-trip.
    function safeFormat(build: () => string, fallback: string): string {
        // An unsaved free-text entry can be a not-yet-valid tag/code, and Intl
        // throws on those. The preview should go quiet, not blow up the page.
        try {
            return build();
        } catch {
            return fallback;
        }
    }

    const previewMoney = computed(() => safeFormat(
        () => {
            const fmt = new Intl.NumberFormat(localeDraft.value, {
                style: 'currency', currency: currencyDraft.value,
            });
            return `${fmt.format(12.5)}  ·  ${fmt.format(1234.56)}`;
        },
        '—',
    ));

    const previewDate = computed(() => safeFormat(
        () => {
            const sample = new Date(2026, 11, 31);
            const short = new Intl.DateTimeFormat(localeDraft.value).format(sample);
            const long = new Intl.DateTimeFormat(localeDraft.value, {
                dateStyle: 'medium',
            }).format(sample);
            return `${short}  ·  ${long}`;
        },
        '—',
    ));

    const previewToday = computed(() => safeFormat(
        () => new Intl.DateTimeFormat(localeDraft.value, {
            weekday: 'long', day: 'numeric', month: 'long',
            timeZone: timezoneDraft.value,
        }).format(new Date()),
        '—',
    ));

    // ── Option lists ──────────────────────────────────────────────────
    const currencyOptions = ref([...CURRENCY_CHOICES]);
    function onCurrencyFilter(val: string, update: (cb: () => void) => void) {
        update(() => {
            const needle = val.toLowerCase();
            currencyOptions.value = needle
                ? CURRENCY_CHOICES.filter((c) => c.label.toLowerCase().includes(needle))
                : [...CURRENCY_CHOICES];
        });
    }

    const localeOptions = ref([...LOCALE_CHOICES]);
    function onLocaleFilter(val: string, update: (cb: () => void) => void) {
        update(() => {
            const needle = val.toLowerCase();
            localeOptions.value = needle
                ? LOCALE_CHOICES.filter((l) => l.label.toLowerCase().includes(needle))
                : [...LOCALE_CHOICES];
        });
    }

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

    // ── Saving ────────────────────────────────────────────────────────
    async function onSaveTimezone(value: string) {
        if (!value || value === timezoneDraft.value) return;
        const previous = timezoneDraft.value;
        timezoneDraft.value = value;   // preview follows the pick immediately
        saving.value = true;
        try {
            const result = await api.updateAsync({ timezone: value });
            timezoneDraft.value = result.timezone;
        } catch (err) {
            timezoneDraft.value = previous;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save the timezone.',
                caption: toastCaption(err),
            });
        } finally {
            saving.value = false;
        }
    }

    // Guards a double-submit: with the popup open, Quasar's own `new-value`
    // handling and the explicit Enter handler both fire for the same
    // keystroke, and `lastSaved*` doesn't update until the PATCH resolves.
    let pendingCurrency: string | null = null;
    let pendingLocale: string | null = null;

    async function onPickCurrency(raw: string | null) {
        const value = String(raw ?? '').trim().toUpperCase();
        if (!value || value === lastSavedCurrency || value === pendingCurrency) return;
        pendingCurrency = value;
        currencyDraft.value = value;
        if (!/^[A-Z]{3}$/.test(value)) {
            currencyError.value = 'Must be a 3-letter code, like AUD or USD.';
            pendingCurrency = null;
            return;
        }
        currencyError.value = null;
        saving.value = true;
        try {
            const result = await api.updateAsync({ currency: value });
            currencyDraft.value = result.currency;
            lastSavedCurrency = result.currency;
            await refreshMoneyPolicy();
        } catch (err) {
            currencyError.value = 'Could not save the currency.';
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save the currency.',
                caption: toastCaption(err),
            });
        } finally {
            saving.value = false;
            pendingCurrency = null;
        }
    }

    async function onPickLocale(raw: string | null) {
        const value = String(raw ?? '').trim();
        if (!value || value === lastSavedLocale || value === pendingLocale) return;
        pendingLocale = value;
        localeDraft.value = value;
        // Ask the browser's own Intl.Locale to parse it before the round-trip
        // — same BCP-47 check the server runs, without the latency.
        try {
            new Intl.Locale(value);
        } catch {
            localeError.value = 'Not a valid language tag, like en-AU.';
            pendingLocale = null;
            return;
        }
        localeError.value = null;
        saving.value = true;
        try {
            const result = await api.updateAsync({ locale: value });
            localeDraft.value = result.locale;
            lastSavedLocale = result.locale;
            await refreshMoneyPolicy();
        } catch (err) {
            localeError.value = 'Could not save the language.';
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save the language.',
                caption: toastCaption(err),
            });
        } finally {
            saving.value = false;
            pendingLocale = null;
        }
    }

    async function onMatchDevice() {
        const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const language = (typeof navigator !== 'undefined' && navigator.language) || '';
        if (zone) await onSaveTimezone(zone);
        if (language) await onPickLocale(language);
        $q.notify({
            type: 'positive', position: 'bottom-right',
            message: 'Matched to this device. Currency is unchanged — set it below.',
        });
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
            // FU-600: with money features off, no money surface mounts to
            // trigger the policy read lazily — so force one, or the rest of
            // the app keeps rendering the AUD/en-AU defaults after a change
            // made here.
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

    .region-preview {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 16px 18px;
        margin-bottom: 20px;
        border-radius: 10px;
        background: var(--surface-sunken);
        border: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
    .region-preview__row {
        display: flex;
        align-items: baseline;
        gap: 12px;
        flex-wrap: wrap;
    }
    .region-preview__label {
        flex: 0 0 72px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
    }
    .region-preview__value {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    .region-preview__detect {
        align-self: flex-start;
        margin-top: 4px;
    }

    .region-field {
        width: 100%;
        min-width: 200px;
    }
</style>
