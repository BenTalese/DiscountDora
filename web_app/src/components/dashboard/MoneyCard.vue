<template>
    <DashboardCard :icon="ICONS.savings" title="Grocery spend" :to="'/settings/money'">
        <template #action>
            <span class="dora-card-action">
                {{ budget?.enabled ? 'Settings →' : 'Set a budget →' }}
            </span>
        </template>

        <!-- ── Spend is the headline (FU-810 / ADR-068) ──────────────────────
             This card used to lead with savings-vs-RRP, which measures how good
             the specials were rather than how little the household spent. Spend
             against the budget period leads now; savings is the supporting
             line. -->
        <CardLoadError
            v-if="budgetFailed"
            line="I couldn't load your spend for this period."
            @retry="emit('retry-budget')"
        />
        <div v-else-if="budget" class="dora-budget-body">
            <div class="dora-budget-headline">
                <span
                    class="dora-budget-spent"
                    :class="{ 'text-negative': budget.over_budget }"
                >
                    {{ formatMoney(budget.spent) }}
                </span>
                <span class="dora-budget-of">
                    {{ budget.enabled
                        ? `of ${formatMoney(budget.amount!)} this ${periodWord}`
                        : `spent this ${periodWord}` }}
                </span>
                <span
                    v-if="budget.enabled"
                    class="dora-budget-remaining"
                    :class="budget.over_budget ? 'text-negative' : 'dora-text-muted'"
                >
                    {{
                        budget.over_budget
                            ? `${formatMoney(Math.abs(budget.remaining ?? 0))} over`
                            : `${formatMoney(budget.remaining ?? 0)} left`
                    }}
                </span>
            </div>
            <q-linear-progress
                v-if="budget.enabled"
                :value="Math.min(1, budget.spent / (budget.amount || 1))"
                :color="budget.over_budget ? 'negative' : 'primary'"
                class="q-mt-sm"
                size="8px"
                rounded
            />
            <div
                v-if="budget.projected_active > 0"
                class="text-caption dora-text-muted q-mt-xs"
            >
                +{{ formatMoney(budget.projected_active) }} in active lists
            </div>
            <!-- FU-451 — budget-defense swaps signpost. Deep-links to the
                 planner, where the Suggestions panel lives. -->
            <div
                v-if="swaps"
                class="dora-swap-bullet q-mt-sm"
                @click.stop="emit('open-swaps')"
            >
                <q-icon :name="ICONS.savings" size="16px" class="q-mr-xs" />
                <strong>Save {{ formatMoney(swaps.saved) }} this week</strong>
                — {{ swaps.count }} {{ swaps.count === 1 ? 'swap' : 'swaps' }} ready ·
                <span class="dora-swap-bullet__cta">See suggestions →</span>
            </div>
        </div>

        <!-- ── Savings, as support ───────────────────────────────────────────
             Its own window, and R-071 requires that window be in the label
             rather than implied: the budget block above runs on the household's
             budget period, this runs on the range toggle, and the two are
             deliberately never summed. -->
        <div class="dora-money-savings">
            <div class="dora-money-savings__head">
                <span class="dora-money-savings__label">
                    Kept vs RRP
                    <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                        <q-tooltip>
                            Savings against each line's RRP across every shopping
                            list you finished in this window — counting only lines
                            where a real deal price was captured. Changing this to
                            your own usual price is FU-831 / ADR-068.
                        </q-tooltip>
                    </q-icon>
                </span>
                <!-- No `flat`: BaseSegmented forces `--text-on-primary` on the
                     pressed segment, so it needs Quasar to paint the primary
                     fill underneath. With `flat` the selected label came out
                     white-on-light — measured 1.21:1, invisible (D-002). -->
                <BaseSegmented
                    :model-value="range"
                    :options="ranges"
                    aria-label="Savings period"
                    dense
                    size="sm"
                    pill
                    @update:model-value="(v: ReportRange) => emit('update:range', v)"
                />
            </div>
            <CardLoadError
                v-if="savingsFailed"
                line="I couldn't tally your savings just now."
                class="q-mt-xs"
                @retry="emit('retry-savings')"
            />
            <div
                v-else-if="savings && savings.total_savings > 0"
                class="dora-money-savings__body"
            >
                <span class="dora-money-savings__amount">
                    <AnimatedNumber :value="savings.total_savings" :format="formatMoney" />
                </span>
                <span class="dora-money-savings__meta">
                    {{ rangeLabel }}, across
                    {{ savings.lists.length }} shop{{ savings.lists.length === 1 ? '' : 's' }}
                </span>
            </div>
            <div v-else class="dora-money-savings__meta">
                Finish a shop and I'll tally what you kept.
            </div>
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * The Money zone's one card: spend against the budget period, with
     * kept-vs-RRP as its supporting line.
     *
     * This absorbed the separate "Grocery budget" card in FU-830 — the two were
     * halves of the same sentence, and could show *different periods* side by
     * side (budget's came from settings, savings' from a range toggle). They
     * still do run on two windows, which is legitimate; R-071 is what makes it
     * honest, by requiring each to name its own window in the label rather than
     * leaving the reader to assume they match.
     *
     * Extracted from `DashboardPage.vue` (FU-829). The page keeps both fetches:
     * budget and savings are separate slots with separate error states, and the
     * savings range change triggers a refetch the page owns.
     */
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import { formatMoney } from 'src/composables/useMoney';
    import AnimatedNumber from 'src/components/AnimatedNumber.vue';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import type { BudgetStatus } from 'src/services/api/budgetApiService';
    import type {
        ReportRange,
        SavingsCapturedResponse,
    } from 'src/services/api/reportsApiService';

    const props = withDefaults(
        defineProps<{
            budget: BudgetStatus | null;
            savings: SavingsCapturedResponse | null;
            /** Budget-defense swap summary for the current week, or null. */
            swaps: { saved: number; count: number } | null;
            range: ReportRange;
            ranges: { value: ReportRange; label: string }[];
            /** Human label for the active range ("last 30 days"). */
            rangeLabel: string;
            budgetFailed?: boolean;
            savingsFailed?: boolean;
        }>(),
        { budgetFailed: false, savingsFailed: false },
    );

    const emit = defineEmits<{
        (e: 'update:range', value: ReportRange): void;
        (e: 'retry-budget'): void;
        (e: 'retry-savings'): void;
        (e: 'open-swaps'): void;
    }>();

    /** "weekly" → "week", "monthly" → "month" — the period read as a noun. */
    const periodWord = computed(() => props.budget?.period.replace('ly', '') ?? '');
</script>

<style scoped lang="scss">
    /* Moved with the card (R-027). Was on the page's `--c-*` aliases, which are
       declared on `.dora-dash` and resolve to nothing from a component (R-060);
       on the real tokens now. */
    .dora-budget-body {
        padding: var(--space-1) var(--space-1) var(--space-2);
    }
    .dora-budget-headline {
        display: flex;
        align-items: baseline;
        gap: var(--space-2);
        flex-wrap: wrap;
    }
    .dora-budget-spent {
        font-size: calc(var(--font-size-2xl) * 1rem);
        font-weight: 700;
    }
    .dora-budget-of {
        font-size: calc(var(--font-size-md) * 1rem);
        color: var(--text-secondary);
    }
    .dora-budget-remaining {
        margin-left: auto;
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 600;
    }
    .dora-swap-bullet {
        font-size: calc(var(--font-size-sm) * 1rem);
        cursor: pointer;
        color: var(--savings-accent);
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--space-1);
    }
    .dora-swap-bullet__cta {
        text-decoration: underline;
        margin-left: var(--space-1);
    }

    /* The savings half. Deliberately quieter than the spend headline above it:
       savings is support, not the claim (ADR-068). */
    .dora-money-savings {
        margin-top: var(--space-4);
        padding-top: var(--space-3);
        /* A6: an in-card separator is `--divider`, not a border token. */
        border-top: 1px solid var(--divider);
    }
    .dora-money-savings__head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-2);
        flex-wrap: wrap;
    }
    .dora-money-savings__label {
        display: inline-flex;
        align-items: center;
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 600;
        color: var(--text-secondary);
    }
    .dora-money-savings__body {
        display: flex;
        align-items: baseline;
        gap: var(--space-2);
        flex-wrap: wrap;
        margin-top: var(--space-1);
    }
    .dora-money-savings__amount {
        font-size: calc(var(--font-size-xl) * 1rem);
        font-weight: 700;
        color: var(--semantic-positive);
    }
    .dora-money-savings__meta {
        font-size: calc(var(--font-size-sm) * 1rem);
        color: var(--text-secondary);
        margin-top: var(--space-1);
    }
</style>
