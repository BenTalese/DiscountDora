<template>
    <DashboardCard :icon="ICONS.restaurant_menu" title="Next to cook">
        <template #action>
            <router-link class="dora-card-action dora-card-link" to="/meal-plans">
                Meal plan →
            </router-link>
        </template>
        <ul v-if="entries.length > 0" class="dora-cook-list">
            <li
                v-for="entry in entries"
                :key="`${entry.recipe_id}-${entry.scheduled_for}-${entry.slot}`"
                class="dora-cook-row dora-cook-row--with-badge"
            >
                <router-link class="dora-cook-name" :to="`/cookbook/${entry.recipe_id}`">
                    {{ entry.recipe_name }}
                </router-link>
                <span class="dora-cook-meta">
                    {{ whenLabel(entry) }}
                    <span v-if="entry.servings"> · serves {{ entry.servings }}</span>
                    <!-- Owner 2026-09-04 — the pool state, in the card's own
                         words. Before this the card offered "Cook" on a meal
                         already cooked and frozen, because it had no idea the
                         pool existed. Batch households only: with no pool,
                         every meal is simply a meal. -->
                    <span v-if="batchEnabled" class="dora-cook-state">
                        · <q-icon :name="cookState(entry).icon" size="13px" />
                        {{ cookState(entry).label }}
                    </span>
                </span>
                <q-badge
                    :color="badgeColour(entry)"
                    :label="badgeLabel(entry)"
                    class="dora-cook-badge"
                />
                <BaseButton
                    variant="ghost"
                    dense
                    size="sm"
                    :icon="ICONS.restaurant"
                    label="Cook"
                    @click="emit('cook', entry)"
                />
            </li>
        </ul>
        <!-- Two empty states, and telling them apart is the point. An empty
             list means "nothing planned" in a fresh household and "the freezer
             has the week covered" in a batch one — same absence, opposite
             news, and rendering the first at a batch household that has just
             cooked a fortnight of dinners would read as broken. -->
        <div v-else-if="batchEnabled && hasPlannedMeals" class="dora-empty dora-empty-ok">
            <q-icon :name="ICONS.check_circle" size="20px" class="q-mr-sm" />
            Nothing to cook — the pool covers what's planned.
        </div>
        <div v-else class="dora-empty">
            Nothing planned for the next week.
            <router-link class="dora-empty-cta" to="/meal-plans">Plan a meal →</router-link>
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * The next few meals worth cooking, each flagged ready / missing-N
     * (feedback L272, FU-298).
     *
     * **Which meals those are depends on how the household cooks** (owner,
     * 2026-09-04). The page selects; this renders. In a fresh household plan
     * day is cook day, so the selection is the next planned meals in order. In
     * a batch one the plan is not a cook schedule — one batch covers many
     * planned days — so the selection is the meals somebody actually has to
     * cook: the pool's shortfall, plus meals marked cook-fresh, which stand
     * outside the pool in both directions.
     *
     * The 09-04 batch before this one taught the card the pool's *labels*
     * (`to cook` / `fresh` / `already cooked`) while it still listed the
     * calendar. Labelling four meals "already cooked" answers the question by
     * apologising for the list; not listing them answers it.
     *
     * `REPORTS_PAGE_REVIEW`-adjacent note: of the four surfaces that render the
     * meal plan, this is the one FU-818 kept, because it is the only one that
     * answers a *question* — "what do I cook, and can I?" — rather than
     * restating the calendar. The badge is what makes it answer that, so the
     * tri-state below matters.
     *
     * Extracted from `DashboardPage.vue` (FU-829). The row anatomy comes from
     * `css/dashboardCards.scss`, shared with Restock radar.
     */
    import { ICONS } from 'src/style/icons';
    import { formatRelativeDay } from 'src/composables/useDateFormat';
    import BaseButton from 'src/components/BaseButton.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import type { UpcomingMealPlanEntry } from 'src/models/dashboard';

    withDefaults(
        defineProps<{
            /** Already selected by the page: chronological in a fresh
             *  household, the pool's shortfall (plus fresh-marked meals) in a
             *  batch one. See `nextToCook` in `DashboardPage.vue`. */
            entries: UpcomingMealPlanEntry[];
            /** Whether the week holds any planned meal at all — what separates
             *  "nothing planned" from "planned, and already cooked". */
            hasPlannedMeals?: boolean;
        }>(),
        { hasPlannedMeals: false },
    );

    const emit = defineEmits<{ (e: 'cook', entry: UpcomingMealPlanEntry): void }>();

    const { batchEnabled } = useBatchEnabled();

    /**
     * Where this meal stands with the cooked pool — the third channel on the
     * row, alongside the when/serves meta and the ingredient badge.
     *
     * Three states, and the one worth naming is the third: a meal the pool
     * already covers. `needs_cooking` and `cook_fresh` are server-owned and
     * never both true, so "neither" is a positive fact (it's cooked already, or
     * it's a batch's leftover day) rather than an absence of information.
     */
    function cookState(entry: UpcomingMealPlanEntry): { icon: string; label: string } {
        if (entry.cook_fresh) return { icon: ICONS.cookFresh, label: 'fresh' };
        if (entry.needs_cooking) return { icon: ICONS.chef_hat, label: 'to cook' };
        return { icon: ICONS.mealsPrepared, label: 'already cooked' };
    }

    function whenLabel(entry: UpcomingMealPlanEntry): string {
        return `${formatRelativeDay(entry.scheduled_for)} ${entry.slot.toLowerCase()}`;
    }

    /**
     * IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — a null `missing_count` has **two**
     * flavours, and conflating them is why this reads the unlinked count first:
     * "empty recipe" (nothing to evaluate) and "unlinked" (ingredients exist but
     * aren't linked to stock items, so cookability is genuinely unknown). The
     * second is actionable — link them and the answer appears — so it gets its
     * own label rather than the ambiguous "No ingredients".
     */
    function badgeLabel(entry: UpcomingMealPlanEntry): string {
        if (entry.unlinked_ingredient_count > 0) {
            return `${entry.unlinked_ingredient_count} to link`;
        }
        if (entry.missing_count === null) return 'No ingredients';
        if (entry.missing_count === 0) return 'Ready';
        return `Missing ${entry.missing_count}`;
    }

    function badgeColour(entry: UpcomingMealPlanEntry): string {
        if (entry.missing_count === 0) return 'positive';
        // `neutral-muted` (a real registered colour, see colours.scss) rather
        // than Quasar's `grey-6`, which R-002 forbids: "no signal yet / not
        // applicable" must be theme-aware, and D-001 reserves grey for exactly
        // this unknown state.
        if (entry.unlinked_ingredient_count > 0) return 'neutral-muted';
        if (entry.missing_count === null) return 'neutral-muted';
        return 'warning';
    }
</script>
