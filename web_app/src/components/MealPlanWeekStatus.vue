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
            <!-- Owner feedback 2026-08-27 — this used to count everything the
                 week needed that wasn't in the pantry, so it read "3 to buy"
                 forever, including after you'd put all three on a list. The
                 headline is now the outstanding half: what's still yours to
                 do. The handled half is named next to it rather than vanishing,
                 so the number can't look like it lost track of something. -->
            <span
                class="week-status__cell"
                :class="outstandingCount > 0 ? 'text-negative' : 'text-positive'"
            >
                <q-icon :name="ICONS.shopping_cart" size="14px" class="q-mr-xs" />
                {{ statusLabel }}
            </span>
            <span v-if="onListCount > 0" class="week-status__cell dora-text-muted">
                {{ onListCount }} already on a list
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
    import { computed } from 'vue';

    const props = defineProps<{
        plannedCount: number;
        shortfallCount: number;
        /** Items the week needs that aren't in the pantry *and* aren't on a
         *  list yet — the count that actually moves when you shop-plan. */
        outstandingCount: number;
        /** Items the week needs that are already sitting on an open list. */
        onListCount: number;
        cookByLabel: string;
    }>();

    const { batchEnabled } = useBatchEnabled();

    // Three states, because "fully stocked" and "nothing left to do" are
    // different facts and saying the first when the second is true would be a
    // lie the user can see through (there are items on a list).
    const statusLabel = computed(() => {
        if (props.outstandingCount > 0) return `${props.outstandingCount} to buy`;
        return props.onListCount > 0 ? 'all on a list' : 'fully stocked';
    });
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
