<template>
    <div v-if="!currentUser">
        <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
    </div>

    <div v-else class="settings-page">
        <SettingsPageHeader
            title="Money &amp; budgets"
            description="Show dollar surfaces — recipe cost estimates, shopping-list totals, the dashboard budget card. Off by default; turn on to opt in."
        />

        <SettingsSection>
            <template #title>Money features</template>
            <template #description>
                Your saved budget number is kept either way.
            </template>

            <SettingsRow label="Show money features">
                <q-toggle
                    :model-value="currentUser.money_features_enabled"
                    :disable="!moneyInstallEnabled || saving"
                    @update:model-value="onMoneyFeaturesChange"
                />
            </SettingsRow>
            <div
                v-if="!moneyInstallEnabled"
                class="settings-page__note dora-text-muted"
            >
                This install has money features turned off. Ask an admin
                to enable them in System → Features.
            </div>
        </SettingsSection>

        <template v-if="moneyEnabled">
            <hr class="settings-divider" />

            <SettingsSection>
                <template #title>Grocery budget</template>
                <template #description>
                    Set a weekly or monthly target; Dora will track how much
                    you've spent across every finished shopping list in the
                    period.
                </template>

                <SettingsRow label="Track a grocery budget">
                    <q-toggle
                        :model-value="budgetEnabledDraft"
                        :disable="saving"
                        @update:model-value="onBudgetEnabledChange"
                    />
                </SettingsRow>

                <template v-if="budgetEnabledDraft">
                    <SettingsRow label="Amount">
                        <q-input
                            v-model.number="budgetAmountDraft"
                            type="number"
                            step="1"
                            min="0"
                            :prefix="currencySymbol"
                            outlined
                            dense
                            style="max-width: 160px"
                            :disable="saving"
                            @blur="onBudgetAmountBlur"
                            @keydown.enter.prevent="onBudgetAmountBlur"
                        />
                    </SettingsRow>

                    <SettingsRow label="Period">
                        <DoraSegmented
                            :model-value="budgetPeriodDraft"
                            :options="budgetPeriodOptions"
                            @update:model-value="onBudgetPeriodChange"
                        />
                    </SettingsRow>
                </template>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type { BudgetPeriod } from 'src/models/auth';
    import { useAuthStore } from 'src/stores/authStore';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { useMoney } from 'src/composables/useMoney';
    // budget input prefix follows the install currency symbol.
    const { currencySymbol } = useMoney();
    import { ref, watch } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import DoraSegmented, { type DoraSegmentedOption } from 'src/components/settings/DoraSegmented.vue';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    const {
        moneyEnabled,
        installEnabled: moneyInstallEnabled,
    } = useMoneyEnabled();

    const budgetAmountDraft = ref<number | null>(currentUser.value?.budget_amount ?? null);
    const budgetPeriodDraft = ref<BudgetPeriod>(currentUser.value?.budget_period ?? 'weekly');
    const budgetEnabledDraft = ref<boolean>(
        currentUser.value?.budget_amount != null && currentUser.value.budget_amount > 0
    );

    const budgetPeriodOptions: DoraSegmentedOption<BudgetPeriod>[] = [
        { label: 'Weekly (Mon–Sun)', value: 'weekly' },
        { label: 'Monthly', value: 'monthly' },
    ];

    const saving = ref(false);

    watch(currentUser, (u) => {
        if (!u) return;
        budgetAmountDraft.value = u.budget_amount ?? null;
        budgetPeriodDraft.value = u.budget_period ?? 'weekly';
        budgetEnabledDraft.value = u.budget_amount != null && u.budget_amount > 0;
    });

    function notifySuccess(message: string) {
        $q.notify({ type: 'positive', position: 'bottom-right', message });
    }
    function notifyError(message: string, err?: unknown) {
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            caption: toastCaption(err)
        });
    }

    async function update<T>(label: string, run: () => Promise<T>): Promise<T | null> {
        saving.value = true;
        try {
            const result = await run();
            notifySuccess(label);
            return result;
        } catch (err) {
            notifyError(`Could not save ${label.toLowerCase()}.`, err);
            return null;
        } finally {
            saving.value = false;
        }
    }

    async function onMoneyFeaturesChange(value: boolean) {
        await update(
            value ? 'Money features turned on.' : 'Money features turned off.',
            () => authStore.updateMeAsync({ money_features_enabled: value }),
        );
    }

    async function onBudgetEnabledChange(value: boolean) {
        budgetEnabledDraft.value = value;
        if (!value) {
            const result = await update('Budget tracking turned off.', () =>
                authStore.updateMeAsync({ clear_budget_amount: true })
            );
            if (result === null) budgetEnabledDraft.value = true;
            return;
        }
        if (
            budgetAmountDraft.value != null
            && budgetAmountDraft.value > 0
            && currentUser.value?.budget_amount !== budgetAmountDraft.value
        ) {
            const result = await update('Budget enabled.', () =>
                authStore.updateMeAsync({
                    budget_amount: budgetAmountDraft.value!,
                    budget_period: budgetPeriodDraft.value,
                })
            );
            if (result === null) budgetEnabledDraft.value = false;
        }
    }

    async function onBudgetAmountBlur() {
        if (!budgetEnabledDraft.value) return;
        const value = budgetAmountDraft.value;
        if (value == null || Number.isNaN(value) || value <= 0) {
            budgetEnabledDraft.value = false;
            await update('Budget tracking turned off.', () =>
                authStore.updateMeAsync({ clear_budget_amount: true })
            );
            return;
        }
        if (currentUser.value?.budget_amount === value) return;
        const previous = currentUser.value?.budget_amount ?? null;
        const result = await update('Budget updated.', () =>
            authStore.updateMeAsync({ budget_amount: value })
        );
        if (result === null) budgetAmountDraft.value = previous;
    }

    async function onBudgetPeriodChange(value: BudgetPeriod) {
        const previous = currentUser.value?.budget_period ?? 'weekly';
        budgetPeriodDraft.value = value;
        const result = await update('Budget period updated.', () =>
            authStore.updateMeAsync({ budget_period: value })
        );
        if (result === null) budgetPeriodDraft.value = previous;
    }
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
</style>
