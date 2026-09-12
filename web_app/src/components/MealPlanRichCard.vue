<template>
    <button
        type="button"
        class="rich-card"
        :class="[
            entry.consumed_at ? 'rich-card--consumed' : '',
            shortfall && batchEnabled ? 'rich-card--shortfall' : '',
            highlight ? 'rich-card--highlight' : '',
        ]"
        :disabled="!!entry.consumed_at"
        :aria-label="accessibleLabel"
    >
        <div class="rich-card__thumb" :class="{ 'rich-card__thumb--mono': !entry.has_image }">
            <img
                v-if="entry.has_image"
                :src="thumbUrl"
                :alt="entry.recipe_name"
                loading="lazy"
            />
            <span v-else class="rich-card__mono-letter">{{ monogramLetter }}</span>
        </div>
        <div class="rich-card__body">
            <div class="rich-card__name">{{ entry.recipe_name }}</div>
            <div class="rich-card__meta">
                <!-- Owner 2026-09-05 — the slot tag is gone. It was the card's
                     only statement of which meal this was, and the owner's read
                     of it was that *"a chip on the meal row is not very obvious
                     or easy to read for groupings of meals (based on slot)"*.
                     Its one caller now groups the day under slot headings
                     (`MealPlanMobileFocus`), so the tag was restating the
                     heading two lines above it in 0.68rem uppercase. The slot
                     is still in `accessibleLabel`, where a screen reader has no
                     heading to have just passed. -->
                <span
                    v-if="linked"
                    class="rich-card__cook"
                    :class="{ 'rich-card__cook--leftover': !entry.is_cook_day }"
                >
                    <q-icon :name="ICONS.link" size="12px" />
                    {{ cookMarkerLabel }}
                </span>
                <!-- Owner 2026-09-04 — the fresh marker takes the linked-cook
                     slot: both answer "how does this meal relate to the pool?",
                     and they can never both be true. -->
                <span v-else-if="fresh" class="rich-card__cook rich-card__cook--fresh">
                    <q-icon :name="ICONS.cookFresh" size="12px" />
                    Fresh
                </span>
                <!-- Owner feedback 2026-09-03 — the sometimes-there glyph sits
                     LEFT of the always-there servings count, so the counts line
                     up down the day's cards. Same order as the desktop chip. -->
                <q-icon
                    v-if="entry.consumed_at"
                    :name="ICONS.check"
                    size="14px"
                    class="rich-card__status text-positive"
                >
                    <BaseTooltip>Cooked</BaseTooltip>
                </q-icon>
                <q-icon
                    v-else-if="shortfall && batchEnabled"
                    :name="ICONS.chef_hat"
                    size="14px"
                    class="rich-card__status text-warning"
                >
                    <BaseTooltip>Needs cooking — pool is short</BaseTooltip>
                </q-icon>
                <span class="rich-card__servings">×{{ entry.servings }}</span>
                <!-- Cookability, flagged only when it's a problem — see
                     `showsMissingIngredients` for why there is no positive
                     state and why a leftovers day never asks. -->
                <span v-if="showsMissing" class="rich-card__missing">
                    <q-icon :name="ICONS.add_shopping_cart" size="12px" />
                    {{ entry.missing_count }} to buy
                    <BaseTooltip>
                        You're missing {{ entry.missing_count }} ingredient{{ entry.missing_count === 1 ? '' : 's' }} for this.
                    </BaseTooltip>
                </span>
                <span v-if="entry.cook_time_minutes" class="rich-card__cook-time">
                    <q-icon :name="ICONS.timer" size="12px" />
                    {{ entry.cook_time_minutes }}m
                </span>
                <!-- Owner 2026-09-05 — what this meal costs at the servings
                     it's planned for, so the week's total has visible parts.
                     Money-gated install-wide: with money off the server sends
                     no figure, so there is nothing to hide. -->
                <span v-if="moneyEnabled && entry.estimated_cost !== null">
                    {{ formatMoney(entry.estimated_cost) }}
                </span>
            </div>
        </div>

        <!-- The menu is shared with `MealPlanEntryChip` (R-001) — see
             `MealPlanEntryMenu.vue`. -->
        <MealPlanEntryMenu
            v-if="!entry.consumed_at"
            :entry="entry"
            @view="emit('view')"
            @cook="emit('cook')"
            @lighter="emit('lighter')"
            @remove="emit('remove')"
            @adjust="(d: number) => emit('adjust', d)"
            @link="emit('link')"
            @unlink="emit('unlink')"
            @fresh="emit('fresh')"
        />
    </button>
</template>

<script lang="ts" setup>
    import BaseTooltip from 'src/components/BaseTooltip.vue';
    import { ICONS } from 'src/style/icons';
    import MealPlanEntryMenu from 'src/components/MealPlanEntryMenu.vue';
    import { recipeImageUrl } from 'src/services/api/recipeApiService';
    import { formatMoney } from 'src/composables/useMoney';
    import { showsMissingIngredients } from 'src/helpers/mealPlanEntryFlags';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import type { MealPlanEntry } from 'src/models/mealPlan';
    import { computed } from 'vue';

    const { batchEnabled } = useBatchEnabled();
    const { moneyEnabled } = useMoneyEnabled();

    const props = withDefaults(
        defineProps<{
            entry: MealPlanEntry;
            shortfall?: boolean;
            highlight?: boolean;
        }>(),
        { shortfall: false, highlight: false },
    );

    const emit = defineEmits<{
        (e: 'view'): void;
        (e: 'cook'): void;
        (e: 'lighter'): void;
        (e: 'remove'): void;
        (e: 'adjust', delta: number): void;
        (e: 'link'): void;
        (e: 'unlink'): void;
        (e: 'fresh'): void;
    }>();

    // PROPOSAL_MEAL_PLANS_PART_2 — linked cook batch (Batch households only).
    const linked = computed(() => batchEnabled.value && !!props.entry.cook_batch_id);
    // Owner 2026-09-04 — cooked on the day, outside the pool. Batch households
    // only: where every meal is fresh, saying so about one of them is noise.
    const fresh = computed(() => batchEnabled.value && props.entry.cook_fresh);
    const cookMarkerLabel = computed(() =>
        props.entry.is_cook_day
            ? `Cook · serves ${props.entry.cook_batch_total_servings ?? props.entry.servings}`
            : 'Leftovers',
    );

    const showsMissing = computed(
        () => showsMissingIngredients(props.entry, batchEnabled.value),
    );

    const thumbUrl = computed(() => recipeImageUrl(props.entry.recipe_id));
    const monogramLetter = computed(
        () => (props.entry.recipe_name?.trim().charAt(0) || '?').toUpperCase(),
    );

    // R-Phase 6 §4.6 — single combined accessible label so AT users hear the
    // whole meal at once (name + slot + servings + status) instead of as
    // separate text fragments. Status text alternative covers 1.4.1.
    const accessibleLabel = computed(() => {
        const base = `${props.entry.recipe_name}, ${props.entry.slot}, ${props.entry.servings} serving${props.entry.servings === 1 ? '' : 's'}`;
        let withCook = base;
        if (linked.value) {
            withCook = `${base}, ${props.entry.is_cook_day ? 'cook day of a batch' : 'leftovers from a batch cook'}`;
        } else if (fresh.value) {
            withCook = `${base}, cooked fresh on the day`;
        }
        if (props.entry.consumed_at) return `${withCook}, cooked`;
        if (props.shortfall && batchEnabled.value) return `${withCook}, needs cooking`;
        return withCook;
    });
</script>

<style scoped>
    .rich-card {
        display: flex;
        align-items: stretch;
        gap: 8px;
        padding: 6px 8px;
        background: var(--surface-elevated);
        border: 1px solid var(--border-default);
        border-left: 3px solid var(--brand-primary);
        border-radius: 8px;
        cursor: pointer;
        transition: background 0.12s ease, border-color 0.12s ease, transform 0.12s ease;
        position: relative;
        color: var(--text-primary);
        text-align: left;
        font: inherit;
        width: 100%;
        min-height: 44px;
    }
    .rich-card:disabled {
        cursor: default;
    }
    .rich-card:hover,
    .rich-card:focus-visible {
        background: var(--surface-sunken);
        outline: none;
    }
    .rich-card:focus-visible {
        border-color: var(--q-primary);
    }
    .rich-card--consumed {
        opacity: 0.55;
        border-left-color: var(--border-default);
    }
    .rich-card--shortfall {
        border-left-color: var(--q-warning);
    }
    .rich-card--highlight {
        outline: 2px solid var(--brand-primary);
        outline-offset: 1px;
    }
    .rich-card__thumb {
        flex: 0 0 auto;
        width: 42px;
        height: 42px;
        border-radius: 6px;
        overflow: hidden;
        background: var(--surface-sunken);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .rich-card__thumb img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }
    .rich-card__thumb--mono {
        background: var(--surface-elevated);
        border: 1px dashed var(--border-default);
    }
    .rich-card__mono-letter {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text-secondary);
        line-height: 1;
    }
    .rich-card__body {
        flex: 1 1 auto;
        min-width: 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 2px;
    }
    .rich-card__name {
        font-weight: 600;
        font-size: 0.9rem;
        line-height: 1.2;
        word-break: break-word;
    }
    .rich-card__meta {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px 8px;
        font-size: 0.72rem;
        color: var(--text-muted);
    }
    .rich-card__servings {
        font-weight: 600;
    }
    /* PROPOSAL_MEAL_PLANS_PART_2 — linked-cook marker (icon + text, D-014-safe). */
    .rich-card__cook {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        font-weight: 600;
        color: var(--brand-primary);
    }
    .rich-card__cook--leftover {
        color: var(--text-muted);
        font-weight: 500;
    }
    /* Fresh is a deliberate state, not a shortage — secondary ink, never the
       amber that means "the pool is short one of these". */
    .rich-card__cook--fresh {
        color: var(--text-secondary);
        font-weight: 500;
    }
    .rich-card__cook-time {
        display: inline-flex;
        align-items: center;
        gap: 2px;
    }
    /* Owner 2026-09-12 — this used to be `margin-left: auto`, which pushed the
       status glyph to the right edge and took the servings, time and money with
       it. Only the meals that HAVE a glyph did that, so a day's cards read
       left-aligned or right-aligned depending on whether they were short —
       *"green meals have the text on the left, shortfall meals have it on the
       right. Inconsistent."* The meta line reads left-to-right for every card
       now; the glyph keeps its place immediately before the servings count,
       which is the column the 2026-09-03 alignment feedback established. */
    .rich-card__status {
        flex: 0 0 auto;
    }
    /* The one negative signal on the card. The tint rides the glyph, never the
       words — full-strength warning ink is the D-002 contrast fail. */
    .rich-card__missing {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        color: var(--text-secondary);
    }
    .rich-card__missing .q-icon {
        color: var(--semantic-warning);
    }
</style>
