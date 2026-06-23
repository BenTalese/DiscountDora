<template>
    <q-card flat bordered>
        <q-card-section>
            <div class="text-subtitle1 text-weight-medium">
                <q-icon :name="ICONS.event" size="20px" class="q-mr-xs" />
                Timezone
            </div>
            <div class="text-caption dora-text-muted">
                The household's timezone. Dates like "today" on the meal
                planner are worked out here, so they stay correct no matter
                where the server runs.
            </div>
        </q-card-section>
        <q-separator />

        <q-card-section v-if="!isAdmin">
            <q-banner class="dora-bg-negative-soft text-negative" dense rounded>
                You don't have admin permissions to view this page.
            </q-banner>
        </q-card-section>

        <q-card-section v-else-if="!loading" class="row q-col-gutter-md items-center">
            <q-select
                :model-value="timezoneDraft"
                :options="timezoneOptions"
                label="Household timezone"
                outlined
                dense
                use-input
                input-debounce="0"
                options-dense
                class="col-12 col-sm-8"
                :disable="savingTimezone"
                :loading="savingTimezone"
                @filter="onTimezoneFilter"
                @update:model-value="onSaveTimezone"
            />
            <div class="col-12 col-sm-4">
                <q-btn
                    color="secondary"
                    no-caps
                    outline
                    label="Use this device's timezone"
                    :disable="savingTimezone"
                    @click="onDetectTimezone"
                />
            </div>
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, ref } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const timezoneDraft = ref<string>('UTC');
    const savingTimezone = ref(false);

    // `Intl.supportedValuesOf` ships in modern engines but isn't in every TS
    // lib target — feature-detect with a precise type rather than `any`.
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
                caption: describeApiError(err) || '',
            });
        } finally {
            savingTimezone.value = false;
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
        } catch {
            // Leave the UTC default.
        } finally {
            loading.value = false;
        }
    });
</script>
