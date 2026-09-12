<template>
    <button
        type="button"
        class="entry-chip"
        :class="{
            'entry-chip--consumed': !!entry.consumed_at,
            'entry-chip--shortfall': shortfall && batchEnabled && !entry.consumed_at,
            'entry-chip--highlight': highlight,
        }"
        :aria-label="accessibleLabel"
        :disabled="!!entry.consumed_at"
    >
        <div class="entry-chip__body">
            <div v-if="showSlot" class="entry-chip__slot">{{ entry.slot }}</div>
            <div v-if="linked" class="entry-chip__cook" :class="{ 'entry-chip__cook--leftover': !entry.is_cook_day }">
                <q-icon :name="ICONS.link" size="12px" />
                <span>{{ cookMarkerLabel }}</span>
            </div>
            <!-- Owner 2026-09-04 — the fresh marker sits where the linked-cook
                 eyebrow does, because it answers the same question ("how does
                 this meal relate to the pool?") and the two can never both be
                 true. Icon + word, not colour alone (D-014). -->
            <div v-else-if="fresh" class="entry-chip__cook entry-chip__cook--fresh">
                <q-icon :name="ICONS.cookFresh" size="12px" />
                <span>Fresh</span>
            </div>
            <div class="entry-chip__main">
                <span class="entry-chip__name">{{ entry.recipe_name }}</span>
                <!-- Owner feedback 2026-09-03 — *"put the needs-cook chef hat
                     on the LEFT of the servings counter so we get UI aligned
                     where possible. The chef hat is the element that is
                     sometimes there, sometimes not."* The servings pill is on
                     every chip, so it is the one that has to hold a column;
                     the conditional glyph moves to the variable side of it. -->
                <q-icon
                    v-if="entry.consumed_at"
                    :name="ICONS.check"
                    size="14px"
                    class="entry-chip__status text-positive"
                >
                    <BaseTooltip>Cooked</BaseTooltip>
                </q-icon>
                <q-icon
                    v-else-if="shortfall && batchEnabled"
                    :name="ICONS.chef_hat"
                    size="14px"
                    class="entry-chip__status text-warning"
                >
                    <BaseTooltip>Needs cooking — pool is short</BaseTooltip>
                </q-icon>
                <span class="entry-chip__pill">×{{ entry.servings }}</span>
                <!-- Cookability, flagged only when it's a problem — the rule
                     (and why a leftovers day never asks) lives in
                     `showsMissingIngredients`, shared with the phone card. -->
                <q-icon
                    v-if="showsMissing"
                    :name="ICONS.add_shopping_cart"
                    size="14px"
                    class="entry-chip__status text-warning"
                >
                    <BaseTooltip>
                        {{ entry.missing_count }} ingredient{{ entry.missing_count === 1 ? '' : 's' }} to buy for this
                    </BaseTooltip>
                </q-icon>
                <!-- FU-653 — Dora's belief about this meal. Its own glyph, not
                     a change to the chip's state: the week's shortfall and
                     "need to buy" figures are unchanged, and this sits beside
                     them as a remark. Server sends it only when the user opted
                     the meal-planner surface in, and never on a cooked meal. -->
                <q-icon
                    v-if="entry.inference_hint"
                    :name="ICONS.dora_voice"
                    size="14px"
                    class="entry-chip__status"
                    :class="entry.inference_hint === 'at_risk' ? 'text-warning' : 'text-positive'"
                >
                    <BaseTooltip max-width="280px">{{ inferenceTooltip }}</BaseTooltip>
                </q-icon>
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
    import { showsMissingIngredients } from 'src/helpers/mealPlanEntryFlags';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import type { MealPlanEntry } from 'src/models/mealPlan';
    import { computed } from 'vue';

    const { batchEnabled } = useBatchEnabled();

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
            ? `Dora thinks you may have run out of ${names} since you planned this. Your plan and its shopping figures are unchanged.`
            : `Recorded as missing ${names}, but Dora thinks you're back in stock — this may be cookable after all.`;
    });

    // PROPOSAL_MEAL_PLANS_PART_2 — a linked cook batch (one cook, several days).
    // Only surfaced for Batch-cooking households.
    const linked = computed(() => batchEnabled.value && !!props.entry.cook_batch_id);
    // Owner 2026-09-04 — cooked on the day, outside the pool. Only meaningful
    // for a batch household: where every meal is cooked fresh, saying so about
    // one of them is noise.
    const fresh = computed(() => batchEnabled.value && props.entry.cook_fresh);
    const cookMarkerLabel = computed(() =>
        props.entry.is_cook_day
            ? `Cook · serves ${props.entry.cook_batch_total_servings ?? props.entry.servings}`
            : 'Leftovers',
    );
    const showsMissing = computed(
        () => showsMissingIngredients(props.entry, batchEnabled.value),
    );

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
        §7 colour discipline — chip is a content-forward card, not a
        saturated fill. Status reads through:
            border-left accent (brand-primary normally, amber on shortfall,
            neutral on consumed)  +  icon  +  text alternative (aria-label).
        Three channels = WCAG 1.4.1 honoured without colour-only signalling.
    */
    .entry-chip {
        display: flex;
        align-items: stretch;
        width: 100%;
        text-align: left;
        padding: 6px 8px;
        margin-bottom: 4px;
        background: var(--surface-elevated);
        border: 1px solid var(--border-default);
        border-left: 3px solid var(--brand-primary);
        border-radius: 8px;
        color: var(--text-primary);
        cursor: pointer;
        transition: background 0.12s ease, border-color 0.12s ease;
        min-height: 28px;
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
    .entry-chip--shortfall {
        border-left-color: var(--q-warning);
    }
    .entry-chip--consumed {
        opacity: 0.55;
        border-left-color: var(--border-default);
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
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        color: var(--text-muted);
    }
    /* PROPOSAL_MEAL_PLANS_PART_2 — linked-cook eyebrow. Icon + text carry the
       signal (not colour alone), D-014-safe. */
    .entry-chip__cook {
        display: flex;
        align-items: center;
        gap: 3px;
        font-size: 0.68rem;
        font-weight: 600;
        color: var(--brand-primary);
        margin-bottom: 1px;
    }
    .entry-chip__cook--leftover {
        color: var(--text-muted);
        font-weight: 500;
    }
    /* Fresh is a deliberate state, not a shortage — it reads in the same
       secondary ink as a leftovers day rather than borrowing the amber that
       means "the pool is short one of these". */
    .entry-chip__cook--fresh {
        color: var(--text-secondary);
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
        line-height: 1.2;
        font-weight: 600;
    }
    .entry-chip__pill {
        flex: 0 0 auto;
        background: var(--surface-sunken);
        color: var(--text-secondary);
        border-radius: 6px;
        padding: 1px 6px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .entry-chip__status {
        flex: 0 0 auto;
    }
</style>
