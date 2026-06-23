<template>
    <div v-if="!currentUser">
        <q-card flat bordered>
            <q-card-section>
                <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
            </q-card-section>
        </q-card>
    </div>

    <div v-else class="column q-gutter-md">
        <!-- C-cross Chunk 2 — Money features opt-in.
             Layered with the install-wide `money_enabled` flag (admin
             owns that one in Settings → System → Features). The Grocery
             budget card below stays hidden until both layers are on.
             Saved `budget_amount` survives toggling this off. -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Money &amp; budgets</div>
                <div class="text-caption dora-text-muted">
                    Show dollar surfaces — recipe cost estimates, shopping-list
                    totals, the dashboard budget card. Off by default; turn on
                    to opt in. Your saved budget number is kept either way.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <q-toggle
                    :model-value="currentUser.money_features_enabled"
                    :disable="!moneyInstallEnabled || saving"
                    label="Show money features"
                    @update:model-value="onMoneyFeaturesChange"
                />
                <div
                    v-if="!moneyInstallEnabled"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    This install has money features turned off. Ask an admin
                    to enable them in System → Features.
                </div>
            </q-card-section>

            <!-- Grocery budget (P2-05) — same page, revealed once money
                 features are on (install-wide AND per-user). Saved value
                 preserved across toggles. -->
            <template v-if="moneyEnabled">
                <q-separator />

                <q-card-section>
                    <div class="text-subtitle2">Grocery budget</div>
                    <div class="text-caption dora-text-muted">
                        Optional. Set a weekly or monthly target and Dora will
                        track how much you've spent across every finished
                        shopping list in the period.
                    </div>
                </q-card-section>

                <q-card-section>
                    <q-toggle
                        :model-value="budgetEnabledDraft"
                        label="Track a grocery budget"
                        :disable="saving"
                        @update:model-value="onBudgetEnabledChange"
                    />
                </q-card-section>

                <q-card-section
                    v-if="budgetEnabledDraft"
                    class="row q-col-gutter-md items-end"
                >
                    <q-input
                        v-model.number="budgetAmountDraft"
                        label="Amount"
                        type="number"
                        step="1"
                        min="0"
                        prefix="$"
                        outlined
                        dense
                        class="col-12 col-sm-4"
                        :disable="saving"
                        @blur="onBudgetAmountBlur"
                        @keydown.enter.prevent="onBudgetAmountBlur"
                    />
                    <div class="col-12 col-sm-8">
                        <q-btn-toggle
                            v-model="budgetPeriodDraft"
                            no-caps
                            spread
                            toggle-color="primary"
                            :options="[
                                { label: 'Weekly (Mon–Sun)', value: 'weekly' },
                                { label: 'Monthly', value: 'monthly' }
                            ]"
                            @update:model-value="onBudgetPeriodChange"
                        />
                    </div>
                </q-card-section>
            </template>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type { BudgetPeriod } from 'src/models/auth';
    import { useAuthStore } from 'src/stores/authStore';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { ref, watch } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    // C-cross Chunk 2 — money opt-in layering. The Settings page exposes
    // both layers explicitly so the user can see why the budget card
    // might be missing (install off vs. their own toggle off).
    const {
        moneyEnabled,
        installEnabled: moneyInstallEnabled,
    } = useMoneyEnabled();

    // P2-05 — budget drafts. `enabled` is derived from amount-being-set;
    // we keep it as a separate draft so toggling off doesn't blow away
    // the user's amount typing (we restore it if they toggle back on
    // without saving).
    const budgetAmountDraft = ref<number | null>(currentUser.value?.budget_amount ?? null);
    const budgetPeriodDraft = ref<BudgetPeriod>(currentUser.value?.budget_period ?? 'weekly');
    const budgetEnabledDraft = ref<boolean>(
        currentUser.value?.budget_amount != null && currentUser.value.budget_amount > 0
    );

    const saving = ref(false);

    // Re-sync drafts when the auth store reloads (e.g. after refresh, login).
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
            caption: describeApiError(err) || ''
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

    // C-cross Chunk 2 — per-user money-features opt-in. The saved
    // budget value isn't touched (proposal §2.2: "data preserved").
    async function onMoneyFeaturesChange(value: boolean) {
        await update(
            value ? 'Money features turned on.' : 'Money features turned off.',
            () => authStore.updateMeAsync({ money_features_enabled: value }),
        );
    }

    // P2-05 — budget handlers.
    async function onBudgetEnabledChange(value: boolean) {
        budgetEnabledDraft.value = value;
        if (!value) {
            // Toggling off clears the persisted amount but keeps the draft
            // so a quick "actually, keep tracking" toggle restores it.
            const result = await update('Budget tracking turned off.', () =>
                authStore.updateMeAsync({ clear_budget_amount: true })
            );
            if (result === null) budgetEnabledDraft.value = true;
            return;
        }
        // Turning on without a number is a no-op until the user types one
        // and blurs — keeps the wire calm.
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
            // Empty / zero input is treated as "turn this off" — saves the
            // user a trip back to the toggle.
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
        const result = await update('Budget period updated.', () =>
            authStore.updateMeAsync({ budget_period: value })
        );
        if (result === null) budgetPeriodDraft.value = previous;
    }
</script>
