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
                <!-- Owner feedback 2026-09-03 - the closing sentence ("you'll
                     need to cook or shop for the missing ingredients") is gone:
                     it restated the two figures sitting either side of it. -->
                <InfoTip label="Cook by">
                    Meal-plan slots whose recipe doesn't have enough
                    cooked-and-frozen portions to cover them.
                </InfoTip>
            </span>
            <!-- Owner 2026-09-04 — *"I batch cook and freeze lunches for the
                 week, but dinner with the parents on Saturday is fresh."* A
                 fresh meal is still a cook, so the week counts it — but it is a
                 deliberate choice rather than a shortage, so it sits in its own
                 neutral cell instead of inflating the amber "to cook by". -->
            <span v-if="batchEnabled && freshCount > 0" class="week-status__cell">
                <q-icon :name="ICONS.cookFresh" size="14px" class="q-mr-xs" />
                {{ freshCount }} fresh
                <InfoTip label="Fresh">
                    Meals you've marked as cooked on the day. They don't take a
                    portion from the cooked pool, and they don't add to what
                    you have to batch-cook.
                </InfoTip>
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
            <!-- Owner 2026-09-05 — *"can't see much in the way of budget and
                 money… no display of estimated weekly cost for meals."* This is
                 the week's, summed server-side across every planned meal at the
                 servings it's planned for. Gated on the install-wide money
                 opt-in: with money off the server sends no figure at all, so
                 there is nothing to hide-when-empty (R-029) — it simply isn't
                 there. Coverage rides along when some meals couldn't be priced,
                 the same rule the kcal cell follows: a week costed from half
                 its meals must not look like a cheap week. -->
            <span
                v-if="moneyEnabled && estimatedCost !== null"
                class="week-status__cell"
            >
                <q-icon :name="ICONS.payments" size="14px" class="q-mr-xs" />
                {{ formatMoney(estimatedCost) }}
                <span v-if="costCountedMeals < costTotalMeals" class="q-ml-xs dora-text-muted">
                    ({{ costCountedMeals }}/{{ costTotalMeals }})
                </span>
                <InfoTip label="Estimated cost">
                    What this week's meals would cost to make, at the servings
                    they're planned for — the value of the ingredients they use,
                    whether or not you already have them.<template
                        v-if="costCountedMeals < costTotalMeals"
                    > Counting {{ costCountedMeals }} of {{ costTotalMeals }}
                    meals; the rest have nothing priced yet.</template>
                </InfoTip>
            </span>
            <!-- Owner feedback 2026-09-03 - *"X to buy, X already on list is
                 duplicated information"*. It was: the right rail now says both
                 halves per stock level ("2 of 3 to buy"), so repeating the
                 handled half here as its own cell said the same thing a second
                 time, less precisely. The strip keeps the number that is still
                 the user's to act on. -->
        </template>
        <span v-else class="week-status__empty dora-text-muted">
            No meals planned for this week yet.
        </span>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import InfoTip from 'src/components/help/InfoTip.vue';
    import { formatMoney } from 'src/composables/useMoney';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { computed } from 'vue';

    const props = defineProps<{
        plannedCount: number;
        shortfallCount: number;
        /** Meals marked "cooked fresh on the day" — outside the pool in both
         *  directions, so counted separately from the shortfall. */
        freshCount: number;
        /** Items the week needs that aren't in the pantry *and* aren't on a
         *  list yet — the count that actually moves when you shop-plan. */
        outstandingCount: number;
        /** Items the week needs that are already sitting on an open list. */
        onListCount: number;
        cookByLabel: string;
        /** Owner 2026-09-05 — the week's estimated cost, summed server-side.
         *  Null when money features are off or nothing could be priced. */
        estimatedCost: number | null;
        costCountedMeals: number;
        costTotalMeals: number;
    }>();

    const { batchEnabled } = useBatchEnabled();
    const { moneyEnabled } = useMoneyEnabled();

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
