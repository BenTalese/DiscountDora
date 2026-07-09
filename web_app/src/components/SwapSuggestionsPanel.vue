<template>
    <!-- FU-451 — budget-defense recipe swaps. Renders only when money features
         are on AND the week is projected over budget (proposal §6b). -->
    <q-card
        v-if="moneyEnabled && suggestions && suggestions.projected_over"
        flat
        bordered
        class="swap-panel q-mt-md"
    >
        <q-card-section class="swap-panel__head">
            <div class="row items-center no-wrap q-gutter-sm">
                <q-icon :name="ICONS.warning" size="22px" color="negative" />
                <div class="text-subtitle1">
                    Over budget by {{ formatMoney(suggestions.overshoot) }} this week
                </div>
            </div>
            <div class="swap-panel__figures">
                <div>
                    <span class="dora-text-muted">Est. week cost</span>
                    <span class="swap-panel__amount">{{ formatMoney(suggestions.cost_per_week) }}</span>
                </div>
                <div v-if="suggestions.budget_amount !== null">
                    <span class="dora-text-muted">Budget</span>
                    <span class="swap-panel__amount">{{ formatMoney(suggestions.budget_amount) }}</span>
                </div>
            </div>
            <div v-if="suggestions.candidates.length" class="swap-panel__lede">
                <q-icon :name="ICONS.savings" size="16px" color="positive" class="q-mr-xs" />
                {{ suggestions.candidates.length }}
                {{ suggestions.candidates.length === 1 ? 'swap' : 'swaps' }}
                could bring it back to
                <strong>{{ formatMoney(suggestions.projected_after_applying_all) }}</strong>
            </div>
        </q-card-section>

        <!-- Just-applied undo banner (session-scoped) -->
        <q-banner v-if="lastLedgerId" dense class="swap-panel__undo">
            <template #avatar><q-icon :name="ICONS.check" color="positive" /></template>
            Swap applied.
            <template #action>
                <BaseButton
                    variant="secondary"
                    :icon="ICONS.undo"
                    label="Undo"
                    :loading="busy"
                    @click="onUndo"
                />
            </template>
        </q-banner>

        <!-- Candidate rows -->
        <q-list v-if="suggestions.candidates.length" separator>
            <q-item v-for="c in suggestions.candidates" :key="c.entry_id + c.to_recipe_id">
                <q-item-section avatar>
                    <q-icon :name="ICONS.restaurant" color="savings-accent" />
                </q-item-section>
                <q-item-section>
                    <q-item-label caption class="dora-text-muted">
                        Recipe swap · {{ dayLabel(c.entry_scheduled_for) }} {{ c.entry_slot }}
                    </q-item-label>
                    <q-item-label class="swap-row__names">
                        {{ c.from_recipe_name }}
                        <q-icon :name="ICONS.arrow_forward" size="14px" class="q-mx-xs" />
                        {{ c.to_recipe_name }}
                    </q-item-label>
                    <q-item-label caption class="swap-row__chip">
                        {{ chipLabel(c.reason_chip) }}
                    </q-item-label>
                </q-item-section>
                <q-item-section side top>
                    <div class="swap-row__saved">−{{ formatMoney(c.saved) }}</div>
                    <BaseButton variant="secondary" label="Preview" @click="openPreview(c)" />
                </q-item-section>
            </q-item>
        </q-list>

        <!-- Zero-state: over budget but nothing saves money -->
        <q-card-section v-else class="swap-panel__zero dora-text-muted">
            No swap saves you money this week — cutting from your shopping list may
            be the only lever.
            <div class="q-mt-sm">
                <BaseButton
                    variant="secondary"
                    :icon="ICONS.shopping_cart"
                    label="Open shopping lists"
                    @click="router.push('/shopping-lists')"
                />
            </div>
        </q-card-section>
    </q-card>

    <!-- Preview → confirm dialog (Charter P7) -->
    <q-dialog v-model="previewOpen">
        <q-card class="swap-preview">
            <q-card-section>
                <div class="text-subtitle1">
                    Swap {{ previewCandidate?.entry_slot }}'s
                    {{ previewCandidate?.from_recipe_name }}
                    → {{ previewCandidate?.to_recipe_name }}
                </div>
            </q-card-section>
            <q-card-section class="q-pt-none">
                <div class="dora-text-muted">Estimated week cost after this swap</div>
                <div class="swap-preview__cost">
                    {{ formatMoney(previewAfterCost) }}
                    <span class="dora-text-muted swap-preview__was">
                        (was {{ formatMoney(suggestions?.cost_per_week ?? 0) }},
                        save {{ formatMoney(previewCandidate?.saved ?? 0) }})
                    </span>
                </div>
                <template v-if="previewCandidate?.missing_ingredient_names.length">
                    <div class="dora-text-muted q-mt-md">Ingredients you'd need to buy</div>
                    <div>{{ previewCandidate.missing_ingredient_names.join(' · ') }}</div>
                </template>
            </q-card-section>
            <q-card-actions align="right">
                <BaseButton variant="secondary" label="Cancel" @click="previewOpen = false" />
                <BaseButton
                    variant="primary"
                    :icon="ICONS.swap_horiz"
                    label="Apply swap"
                    :loading="busy"
                    @click="onApply"
                />
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script lang="ts" setup>
    import { ref, watch } from 'vue';
    import { useRouter } from 'vue-router';
    import { useQuasar } from 'quasar';
    import { ICONS } from 'src/style/icons';
    import { formatMoney } from 'src/composables/useMoney';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import BaseButton from 'src/components/BaseButton.vue';
    import MealPlanApiService, {
        type RecipeSwapCandidate,
        type SwapSuggestions,
    } from 'src/services/api/mealPlanApiService';

    const props = defineProps<{ mealPlanId: string | null }>();
    // Emitted after a successful apply/undo so the parent reloads the week grid.
    const emit = defineEmits<{ (e: 'changed'): void }>();

    const $q = useQuasar();
    const router = useRouter();
    const { moneyEnabled } = useMoneyEnabled();
    const api = new MealPlanApiService();

    const suggestions = ref<SwapSuggestions | null>(null);
    const busy = ref(false);
    const previewOpen = ref(false);
    const previewCandidate = ref<RecipeSwapCandidate | null>(null);
    // Ledger id of the most recent apply this session — drives the undo banner.
    const lastLedgerId = ref<string | null>(null);

    const previewAfterCost = ref(0);

    const CHIP_LABELS: Record<RecipeSwapCandidate['reason_chip'], string> = {
        cheaper_recipe_cookable: 'Cheaper — uses stock you have',
        cheaper_recipe_similar: 'Cheaper — same style meal',
        cheaper_recipe_household_fav: "Cheaper — you've cooked it before",
    };
    function chipLabel(chip: RecipeSwapCandidate['reason_chip']): string {
        return CHIP_LABELS[chip] ?? 'Cheaper option';
    }

    function dayLabel(iso: string): string {
        const d = new Date(iso + 'T00:00:00');
        return d.toLocaleDateString(undefined, { weekday: 'long' });
    }

    async function load() {
        if (!props.mealPlanId || !moneyEnabled.value) {
            suggestions.value = null;
            return;
        }
        try {
            suggestions.value = await api.getSwapSuggestionsAsync(props.mealPlanId);
        } catch {
            suggestions.value = null;
        }
    }

    function openPreview(c: RecipeSwapCandidate) {
        previewCandidate.value = c;
        previewAfterCost.value = Math.max(0, (suggestions.value?.cost_per_week ?? 0) - c.saved);
        previewOpen.value = true;
    }

    async function onApply() {
        if (!props.mealPlanId || !previewCandidate.value) return;
        busy.value = true;
        try {
            const result = await api.applySwapAsync(props.mealPlanId, {
                kind: 'recipe',
                entry_id: previewCandidate.value.entry_id,
                to_recipe_id: previewCandidate.value.to_recipe_id,
                expected_from_recipe_id: previewCandidate.value.from_recipe_id,
            });
            lastLedgerId.value = result.swap_ledger_id;
            previewOpen.value = false;
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Swap applied.' });
            emit('changed');
            await load();
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not apply the swap.', caption: toastCaption(err),
            });
        } finally {
            busy.value = false;
        }
    }

    async function onUndo() {
        if (!props.mealPlanId || !lastLedgerId.value) return;
        busy.value = true;
        try {
            await api.undoSwapAsync(props.mealPlanId, lastLedgerId.value);
            lastLedgerId.value = null;
            $q.notify({ type: 'info', position: 'bottom-right', message: 'Swap undone.' });
            emit('changed');
            await load();
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not undo the swap.', caption: toastCaption(err),
            });
        } finally {
            busy.value = false;
        }
    }

    watch(() => props.mealPlanId, load, { immediate: true });
    watch(moneyEnabled, load);
    // Let the parent force a re-fetch (e.g. after editing the week elsewhere).
    defineExpose({ reload: load });
</script>

<style scoped lang="scss">
    .swap-panel__head {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .swap-panel__figures {
        display: flex;
        gap: 24px;
        font-size: 0.9rem;
        > div { display: flex; flex-direction: column; }
    }
    .swap-panel__amount { font-weight: 600; font-size: 1.05rem; }
    .swap-panel__lede { font-size: 0.9rem; }
    .swap-panel__undo {
        background: color-mix(in srgb, var(--savings-accent) 12%, transparent);
    }
    .swap-panel__zero { font-size: 0.9rem; }
    .swap-row__names { font-weight: 500; }
    .swap-row__chip { color: var(--savings-accent); }
    .swap-row__saved {
        font-weight: 700;
        color: var(--savings-accent);
        text-align: right;
        margin-bottom: 6px;
    }
    .swap-preview { min-width: 320px; max-width: 460px; }
    .swap-preview__cost { font-size: 1.4rem; font-weight: 700; }
    .swap-preview__was { font-size: 0.85rem; font-weight: 400; }
</style>
