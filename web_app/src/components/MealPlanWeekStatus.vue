<template>
    <div class="week-status">
        <template v-if="plannedCount > 0">
            <span class="week-status__count">
                <strong>{{ plannedCount }}</strong> planned
            </span>
            <!-- Batch-only: cook-shortfall summary. Fresh households don't
                use the cook pool, so a "to cook by" line would be noise. -->
            <span v-if="batchEnabled && shortfallCount > 0" class="week-status__cell text-warning">
                <q-icon :name="ICONS.chef_hat" size="14px" class="q-mr-xs" />
                {{ cookByLabel }}
                <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                    <q-tooltip>
                        Meal-plan slots whose recipe doesn't have enough
                        cooked-and-frozen portions to cover them. You'll need to
                        cook or shop for the missing ingredients.
                    </q-tooltip>
                </q-icon>
            </span>
            <span
                class="week-status__cell"
                :class="needToBuyCount > 0 ? 'text-negative' : 'text-positive'"
            >
                <q-icon :name="ICONS.shopping_cart" size="14px" class="q-mr-xs" />
                {{ needToBuyCount > 0
                    ? `${needToBuyCount} to buy`
                    : 'fully stocked' }}
            </span>
        </template>
        <span v-else class="week-status__empty dora-text-muted">
            No meals planned for this week yet.
        </span>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';

    defineProps<{
        plannedCount: number;
        shortfallCount: number;
        needToBuyCount: number;
        cookByLabel: string;
    }>();

    const { batchEnabled } = useBatchEnabled();
</script>

<style scoped>
    .week-status {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 12px 18px;
        padding: 6px 10px;
        margin-bottom: 6px;
        background: var(--surface-sunken);
        border-radius: 8px;
        font-size: 0.85rem;
    }
    .week-status__count strong {
        font-weight: 700;
    }
    .week-status__cell {
        display: inline-flex;
        align-items: center;
    }
    .week-status__empty {
        font-style: italic;
    }
</style>
