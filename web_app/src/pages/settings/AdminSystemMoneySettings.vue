<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Money"
            description="Whether this install talks about money at all."
            :icon="ICONS.savings"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <SettingsRow inline>
                    <template #label>
                        Money &amp; budgets
                        <InfoTip label="Money and budgets">
                            Turns on recipe cost estimates, shopping-list totals,
                            price history and budget tracking. With it off Dora
                            still runs the kitchen — it just never shows a
                            dollar figure.
                        </InfoTip>
                    </template>
                    <q-toggle
                        :model-value="moneyDraft"
                        @update:model-value="onMoneyToggle"
                    />
                </SettingsRow>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    // Owner 2026-09-03 — the Features page was dissolved and its switches sent
    // to the surfaces they govern. Money got a page of its own under Kitchen
    // features rather than a row on the personal `/settings/money` budget page,
    // because that page is itself hidden when this flag is off: the switch
    // would have been the one control you can't reach once you've used it.
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import InfoTip from 'src/components/help/InfoTip.vue';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();
    // Money gates a nav entry and a dozen surfaces off the cached
    // `/api/health` answer, so a flip has to invalidate that cache.
    const { refresh: featureFlags$refresh } = useFeatureFlags();

    const loading = ref(true);
    const moneyDraft = ref(false);

    async function onMoneyToggle(next: boolean) {
        const previous = moneyDraft.value;
        moneyDraft.value = next;
        try {
            const result = await api.updateAsync({ money_enabled: next });
            moneyDraft.value = result.money_enabled;
            await featureFlags$refresh();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: next ? 'Money & budgets enabled.' : 'Money & budgets disabled.',
            });
        } catch (err) {
            moneyDraft.value = previous;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save the money setting.',
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
            moneyDraft.value = (await api.getAsync()).money_enabled;
        } catch {
            // Leave the default; the toggle just shows off until a retry.
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
</style>
