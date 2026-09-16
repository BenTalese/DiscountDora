<template>
    <button
        type="button"
        class="rich-card"
        :class="[
            `rich-card--trim-${status.trim}`,
            entry.consumed_at ? 'rich-card--consumed' : '',
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
                     Its one caller groups the day under slot headings
                     (`MealPlanMobileFocus`), so the tag was restating the
                     heading two lines above it. The slot is still in
                     `accessibleLabel`, where a screen reader has no heading to
                     have just passed.

                     Owner 2026-09-12 — provenance is a CHIP and carries no
                     verdict colour (it is a fact about the plan), and the rest
                     of the row runs rarest-shown → always-shown, left to right,
                     so the servings count holds a column whatever its
                     neighbours are doing. `mealChips.scss` +
                     `helpers/mealPlanEntryStatus.ts`. -->
                <span
                    v-if="linked"
                    class="meal-chip"
                    :class="entry.is_cook_day ? 'meal-chip--cook' : 'meal-chip--leftover'"
                >
                    <q-icon :name="ICONS.link" size="12px" />
                    {{ cookMarkerLabel }}
                </span>
                <span v-else-if="fresh" class="meal-chip">
                    <q-icon :name="ICONS.cookFresh" size="12px" />
                    Fresh
                </span>
                <!-- Owner 2026-09-12 — order by how often each thing is
                     there: Dora's hunch is the rarest, then the price, then
                     the status glyphs, then the always-present servings. -->
                <q-icon
                    v-if="entry.inference_hint"
                    :name="ICONS.dora_voice"
                    size="22px"
                    class="rich-card__status"
                    :class="entry.inference_hint === 'at_risk' ? 'text-warning' : 'text-positive'"
                >
                    <BaseTooltip max-width="280px">{{ inferenceTooltip }}</BaseTooltip>
                </q-icon>
                <span v-if="priceLabel" class="meal-chip meal-chip--price">{{ priceLabel }}</span>
                <q-icon
                    v-if="entry.consumed_at"
                    :name="ICONS.check"
                    size="22px"
                    class="rich-card__status"
                >
                    <BaseTooltip>Cooked</BaseTooltip>
                </q-icon>
                <template v-else>
                    <q-icon
                        v-if="status.supply"
                        :name="ICONS.chef_hat"
                        size="22px"
                        class="rich-card__status"
                        :class="status.supply === 'ok' ? 'text-positive' : 'text-warning'"
                    >
                        <BaseTooltip>{{ supplyTooltip(entry) }}</BaseTooltip>
                    </q-icon>
                    <q-icon
                        v-if="status.readiness"
                        :name="ICONS.mealsPrepared"
                        size="22px"
                        class="rich-card__status"
                        :class="status.readiness === 'ok' ? 'text-positive' : 'text-warning'"
                    >
                        <BaseTooltip>{{ readinessTooltip(entry, !!shortfall) }}</BaseTooltip>
                    </q-icon>
                </template>
                <span v-if="entry.cook_time_minutes" class="rich-card__cook-time">
                    <q-icon :name="ICONS.timer" size="12px" />
                    {{ entry.cook_time_minutes }}m
                </span>
                <!-- A batch's cook day prices the whole cook (the servings its
                     own chip states); its leftover days price nothing, because
                     the money is spent once. -->
                <span class="rich-card__servings">×{{ entry.servings }}</span>
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
    import {
        mealCardStatus, readinessTooltip, supplyTooltip,
    } from 'src/helpers/mealPlanEntryStatus';
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

    // FU-653 — Dora's belief about this meal, as a remark. It was on the
    // desktop chip only until 2026-09-12; the two cards draw the same meal, so
    // the phone was quietly missing a signal the week grid had (R-001).
    const inferenceTooltip = computed(() => {
        const names = (props.entry.inference_stock_item_names ?? []).join(', ');
        return props.entry.inference_hint === 'at_risk'
            ? `Dora thinks you may have run out of ${names} since you planned this.`
            : `Recorded as missing ${names}, but Dora thinks you're back in stock — this may be cookable after all.`;
    });

    // PROPOSAL_MEAL_PLANS_PART_2 — linked cook batch (Batch households only).
    const linked = computed(() => batchEnabled.value && !!props.entry.cook_batch_id);
    // Owner 2026-09-04 — cooked on the day, outside the pool. Batch households
    // only: where every meal is fresh, saying so about one of them is noise.
    const fresh = computed(() => batchEnabled.value && props.entry.cook_fresh);
    // Owner 2026-09-12 — "Cook day · 6 servings": the chip names the day's role
    // first, then what that one cook produces.
    const cookMarkerLabel = computed(() => {
        if (!props.entry.is_cook_day) return 'Leftovers';
        const serves = props.entry.cook_batch_total_servings ?? props.entry.servings;
        return `Cook day · ${serves} serving${serves === 1 ? '' : 's'}`;
    });

    const status = computed(
        () => mealCardStatus(props.entry, batchEnabled.value, props.shortfall),
    );

    /** The price chip's text, or '' for no chip. A batch's cook day prices the
     *  whole cook; its leftover days price nothing. Both figures are
     *  server-owned — no money arithmetic here (R-003). */
    const priceLabel = computed(() => {
        if (!moneyEnabled.value) return '';
        if (props.entry.cook_batch_id !== null) {
            if (!props.entry.is_cook_day) return '';
            return props.entry.cook_batch_estimated_cost === null
                ? '' : formatMoney(props.entry.cook_batch_estimated_cost);
        }
        return props.entry.estimated_cost === null
            ? '' : formatMoney(props.entry.estimated_cost);
    });

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
    /* The trim rolls up the two status glyphs (see `mealPlanEntryStatus`):
       green = all good and something still to do, grey = nothing required of
       you (leftovers, or cooked), amber = one of the glyphs is amber. */
    .rich-card--consumed {
        opacity: 0.55;
    }
    .rich-card--trim-alert {
        border-left-color: var(--q-warning);
    }
    .rich-card--trim-idle {
        border-left-color: var(--border-strong);
    }
    .rich-card--highlight {
        outline: 2px solid var(--brand-primary);
        outline-offset: 1px;
    }
    .rich-card__thumb {
        flex: 0 0 auto;
        width: 48px;
        height: 48px;
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
        font-size: calc(var(--font-size-md) * 1rem);
        line-height: 1.25;
        word-break: break-word;
    }
    /* Owner 2026-09-12 — the whole middle pane was reading a size or two under
       the rest of the app (see `MealPlanEntryChip`); the phone card's meta line
       was 0.72rem. */
    .rich-card__meta {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px 8px;
        font-size: calc(var(--font-size-sm) * 1rem);
        color: var(--text-secondary);
    }
    .rich-card__servings {
        font-weight: 600;
    }
    /* The provenance + price chips are `mealChips.scss`, shared with the
       desktop week chip. */
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
</style>
