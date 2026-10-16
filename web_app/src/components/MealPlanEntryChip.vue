<template>
    <button
        type="button"
        class="entry-chip"
        :class="[
            `entry-chip--trim-${status.trim}`,
            {
                'entry-chip--consumed': !!entry.consumed_at,
                'entry-chip--highlight': highlight,
            },
        ]"
        :aria-label="accessibleLabel"
        :disabled="!!entry.consumed_at"
    >
        <div class="entry-chip__body">
            <div v-if="showSlot" class="entry-chip__slot">{{ entry.slot }}</div>
            <!-- Owner 2026-09-12 — provenance (where this meal's food comes
                 from) reads as a labelled chip rather than loose eyebrow text:
                 *"cook cards for multi-linked days should say 'cook day - N
                 servings' in a chip"*. It carries NO verdict colour — it is a
                 fact about the plan, and the two status glyphs beside the name
                 are what say whether anything is wrong. That separation is the
                 whole point of the 2026-09-12 assessment: one axis per channel.
                 Owner 2026-09-04: the fresh marker takes the same position,
                 because it answers the same question and the two can never both
                 be true. Icon + word, never colour alone (D-014). -->
            <div v-if="linked || fresh" class="entry-chip__marks">
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
            </div>
            <div class="entry-chip__main">
                <span class="entry-chip__name">{{ entry.recipe_name }}</span>
                <!-- Owner 2026-09-12 — *"dislike the UI moving around too much:
                     put items that are always shown to the RIGHT of items that
                     show and hide."* So the row reads rarest-first:
                     Dora's hunch (rare) → the two status glyphs (conditional) →
                     cook time (usually) → price (usually) → servings (always).
                     The always-there servings pill therefore holds one column
                     down the day whatever the meals above it are doing, which
                     is the 2026-09-03 alignment ask generalised.

                     FU-653 — Dora's belief is a *remark*, not a state: the
                     week's shortfall and to-buy figures are unchanged by it,
                     and it keeps its own glyph rather than tinting one of the
                     two axes. Server sends it only for an opted-in surface, and
                     never on a cooked meal. -->
                <!-- Owner 2026-09-12 — order by how often each thing is
                     there: Dora's hunch is the rarest, then the price, then
                     the status glyphs, then the always-present servings. -->
                <q-icon
                    v-if="entry.inference_hint"
                    :name="ICONS.dora_voice"
                    size="22px"
                    class="entry-chip__status"
                    :class="entry.inference_hint === 'at_risk' ? 'text-warning' : 'text-positive'"
                >
                    <BaseTooltip max-width="280px">{{ inferenceTooltip }}</BaseTooltip>
                </q-icon>
                <span v-if="priceLabel" class="meal-chip meal-chip--price">{{ priceLabel }}</span>
                <!-- `chef_hat` = can you make it, `mealsPrepared` (the fridge) =
                     is it already made. One colour meaning each — green fine,
                     amber not — and an axis that doesn't apply to this meal
                     renders nothing. See `mealPlanEntryStatus`. -->
                <q-icon
                    v-if="entry.consumed_at"
                    :name="ICONS.check"
                    size="22px"
                    class="entry-chip__status"
                >
                    <BaseTooltip>Cooked</BaseTooltip>
                </q-icon>
                <template v-else>
                    <q-icon
                        v-if="status.supply"
                        :name="ICONS.chef_hat"
                        size="22px"
                        class="entry-chip__status"
                        :class="statusToneClass(status.supply)"
                    >
                        <BaseTooltip>{{ supplyTooltip(entry) }}</BaseTooltip>
                    </q-icon>
                    <q-icon
                        v-if="status.readiness"
                        :name="ICONS.mealsPrepared"
                        size="22px"
                        class="entry-chip__status"
                        :class="statusToneClass(status.readiness)"
                    >
                        <BaseTooltip>{{ readinessTooltip(entry, !!shortfall) }}</BaseTooltip>
                    </q-icon>
                </template>
                <span class="entry-chip__pill">×{{ entry.servings }}</span>
            </div>
        </div>

        <!-- The menu is shared with `MealPlanRichCard` (R-001) — see
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
    import {
        mealCardStatus, readinessTooltip, statusToneClass, supplyTooltip,
    } from 'src/helpers/mealPlanEntryStatus';
    import { formatMoney } from 'src/composables/useMoney';
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
            showSlot?: boolean;
            highlight?: boolean;
        }>(),
        { shortfall: false, showSlot: true, highlight: false },
    );

    const emit = defineEmits<{
        (e: 'view'): void;
        (e: 'cook'): void;
        (e: 'remove'): void;
        (e: 'adjust', delta: number): void;
        (e: 'link'): void;
        (e: 'unlink'): void;
        (e: 'lighter'): void;
        (e: 'fresh'): void;
    }>();

    // FU-653 — the belief glyph's explanation. Names the items and says the
    // plan is unchanged, so it reads as a heads-up rather than an error.
    const inferenceTooltip = computed(() => {
        const names = (props.entry.inference_stock_item_names ?? []).join(', ');
        return props.entry.inference_hint === 'at_risk'
            ? `Dora thinks you may have run out of ${names} since you planned this.`
            : `Recorded as missing ${names}, but Dora thinks you're back in stock.`;
    });

    // PROPOSAL_MEAL_PLANS_PART_2 — a linked cook batch (one cook, several days).
    // Only surfaced for Batch-cooking households.
    const linked = computed(() => batchEnabled.value && !!props.entry.cook_batch_id);
    // Owner 2026-09-04 — cooked on the day, outside the pool. Only meaningful
    // for a batch household: where every meal is cooked fresh, saying so about
    // one of them is noise.
    const fresh = computed(() => batchEnabled.value && props.entry.cook_fresh);
    // Owner 2026-09-12 — "Cook day · 6 servings" rather than "Cook · serves 6":
    // the chip names the day's role first, then what that one cook produces.
    const cookMarkerLabel = computed(() => {
        if (!props.entry.is_cook_day) return 'Leftovers';
        const serves = props.entry.cook_batch_total_servings ?? props.entry.servings;
        return `Cook day · ${serves} serving${serves === 1 ? '' : 's'}`;
    });

    const status = computed(
        () => mealCardStatus(props.entry, batchEnabled.value, props.shortfall),
    );

    /**
     * The price chip's text, or '' for no chip.
     *
     * A batch's COOK DAY prices the whole cook — the servings its own chip says
     * it will produce — and its leftover days price nothing, because the money
     * is spent once (owner 2026-09-12). Both figures are server-owned; the
     * client never divides or multiplies money here (R-003).
     */
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

    // R-Phase 6 §4.6 — single accessible label that names the recipe + slot +
    // servings, so AT users hear the whole meal at once instead of three
    // separate spans. Shortfall is announced as a status, not a colour.
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
    /*
        §7 colour discipline — chip is a content-forward card, not a saturated
        fill. Status reads through the border-left accent + icons + the
        aria-label's text alternative: three channels, so WCAG 1.4.1 is met
        without colour-only signalling.

        Owner assessment 2026-09-12 — the trim is now a ROLL-UP of the two
        status glyphs rather than a fourth opinion:
            green  — all good, and there's still something to do (you'll cook it)
            grey   — nothing is required of you (a leftovers day, or cooked)
            amber  — one of the glyphs is amber
        It therefore cannot contradict the icons, which is what "this one says
        okay and this one says not okay" was. The rule lives in
        `mealPlanEntryStatus`, shared with the phone card.
    */
    /* Owner 2026-09-12 — *"the text/elements in the middle area of the page
       feel too tiny compared with other areas of the app. Compare with stock
       overview."* They were: the meal name was inherited body at ~0.875rem
       inside a 28px chip, where the stock row gives its name 1.05rem in 64px.
       The chip is the thing you actually read on this page, so it now sits on
       the app's own scale — name at `--font-size-md`, a 36px floor, and the
       three status glyphs at 22px. */
    .entry-chip {
        display: flex;
        align-items: stretch;
        width: 100%;
        text-align: left;
        padding: 8px 10px;
        margin-bottom: 4px;
        background: var(--surface-elevated);
        border: 1px solid var(--border-default);
        border-left: 3px solid var(--brand-primary);
        border-radius: 8px;
        color: var(--text-primary);
        cursor: pointer;
        transition: background 0.12s ease, border-color 0.12s ease;
        min-height: 36px;
        font: inherit;
    }
    .entry-chip:hover,
    .entry-chip:focus-visible {
        background: var(--surface-sunken);
        outline: none;
    }
    .entry-chip:focus-visible {
        border-color: var(--q-primary);
    }
    .entry-chip--trim-alert {
        border-left-color: var(--q-warning);
    }
    .entry-chip--trim-idle {
        border-left-color: var(--border-strong);
    }
    .entry-chip--consumed {
        opacity: 0.55;
        cursor: default;
    }
    .entry-chip--highlight {
        outline: 2px solid var(--brand-primary);
        outline-offset: 1px;
    }
    .entry-chip__body {
        width: 100%;
        min-width: 0;
    }
    .entry-chip__slot {
        font-size: calc(var(--font-size-xs) * 1rem);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        color: var(--text-muted);
    }
    /* The provenance + price row. These are facts about the plan, so they wear
       the app's quiet chip shape and never a verdict colour — the two glyphs
       beside the name own the verdict. */
    .entry-chip__marks {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 3px;
        margin-bottom: 2px;
    }
    .entry-chip__main {
        display: flex;
        align-items: center;
        gap: 6px;
        width: 100%;
    }
    .entry-chip__name {
        flex: 1 1 auto;
        white-space: normal;
        word-break: break-word;
        line-height: 1.25;
        font-size: calc(var(--font-size-md) * 1rem);
        font-weight: 600;
    }
    .entry-chip__pill {
        flex: 0 0 auto;
        background: var(--surface-sunken);
        color: var(--text-secondary);
        border-radius: 6px;
        padding: 2px 8px;
        font-weight: 700;
        font-size: calc(var(--font-size-sm) * 1rem);
    }
    .entry-chip__status {
        flex: 0 0 auto;
    }
</style>
