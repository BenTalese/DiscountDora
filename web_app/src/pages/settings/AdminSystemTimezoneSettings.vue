<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Timezone"
            description="The household's timezone. Dates like &quot;today&quot; on the meal planner are worked out here, so they stay correct no matter where the server runs."
            :icon="ICONS.event"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <SettingsSection v-else-if="!loading">
            <template #title>Household timezone</template>

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
                        :disable="savingTimezone"
                        :loading="savingTimezone"
                        @filter="onTimezoneFilter"
                        @update:model-value="onSaveTimezone"
                    />
                    <!-- FU-006: ambiguous — outline with Quasar palette color="secondary" (not the BaseButton "secondary" variant which is primary outline). Left as raw q-btn for review. -->
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
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, ref } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
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

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
</style>
