<template>
    <!-- The plan face's hero. Replaces the old stranded cluster of a doughnut
         plus three money lines that floated at the top-right with no container
         (D-011) and disappeared entirely at zero lines — exactly when a new
         user most needs orientation. This card always renders. -->
    <q-card flat bordered class="sl-trip-card">
        <q-card-section class="row items-center no-wrap q-gutter-md">
            <q-circular-progress
                v-if="lineCount > 0"
                show-value
                :value="progressPct"
                size="64px"
                :thickness="0.16"
                color="positive"
                track-color="grey-3"
                class="text-weight-medium sl-trip-ring"
            >
                <span class="text-caption">{{ tickedCount }}/{{ lineCount }}</span>
            </q-circular-progress>

            <div class="column q-gutter-xs" style="min-width: 0">
                <!-- The shop day is the one thing on this card you set rather
                     than read, so it stays a real button. Overdue/today fold
                     into its tone — one signal, not a button plus a banner. -->
                <BaseButton
                    variant="ghost"
                    dense
                    :icon="ICONS.event"
                    :label="shopDayLabel"
                    class="sl-trip-day"
                    :class="shopDayToneClass"
                    @click="emit('edit-shop-day')"
                >
                    <q-tooltip>
                        Set the day you plan to shop this list. Helps Dora pick which
                        list is your active one, and drives shop-day reminders.
                    </q-tooltip>
                </BaseButton>
                <div class="text-caption dora-text-muted">
                    {{ lineCount }} item{{ lineCount === 1 ? '' : 's' }}
                    <template v-if="lineCount > 0"> · {{ tickedCount }} ticked</template>
                </div>
            </div>

            <q-space />

            <div v-if="moneyEnabled && lineCount > 0" class="column items-end">
                <div class="text-h6 sl-trip-total">{{ formatMoney(remainingTotal) }}</div>
                <div class="text-caption dora-text-muted text-right">
                    <template v-if="tickedCount > 0">remaining of {{ formatMoney(fullTotal) }}</template>
                    <template v-else>estimated</template>
                    <template v-if="savingsTotal > 0">
                        · <span class="text-positive">saving {{ formatMoney(savingsTotal) }}</span>
                    </template>
                </div>
                <!-- Says out loud when the headline number is built from past
                     purchases rather than prices typed for this trip, so a
                     rough figure is never mistaken for a firm one. -->
                <div v-if="estimatedCount > 0" class="text-caption dora-text-muted">
                    {{ estimatedCount }} from what you last paid
                </div>
            </div>
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import { formatMoney } from 'src/composables/useMoney';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';

    const props = defineProps<{
        lineCount: number;
        tickedCount: number;
        remainingTotal: number;
        fullTotal: number;
        savingsTotal: number;
        /** How many active lines are priced from history rather than a price
         *  the user typed for this trip. Drives the "estimated" caption. */
        estimatedCount: number;
        shopDayLabel: string;
        /** 'overdue' | 'today' | null — folded into the day button's tone. */
        shopDayTone: 'overdue' | 'today' | null;
    }>();

    const emit = defineEmits<{ 'edit-shop-day': [] }>();

    const { moneyEnabled } = useMoneyEnabled();

    const progressPct = computed(() =>
        props.lineCount === 0 ? 0 : (props.tickedCount / props.lineCount) * 100
    );

    const shopDayToneClass = computed(() => {
        if (props.shopDayTone === 'overdue') return 'text-negative';
        if (props.shopDayTone === 'today') return 'text-positive';
        return '';
    });
</script>

<style scoped>
    .sl-trip-card {
        background: var(--surface-elevated);
    }
    .sl-trip-day {
        align-self: flex-start;
    }
    .sl-trip-total {
        line-height: 1.1;
        font-variant-numeric: tabular-nums;
    }
    .sl-trip-ring :deep(.q-circular-progress__text) {
        font-variant-numeric: tabular-nums;
    }
</style>
