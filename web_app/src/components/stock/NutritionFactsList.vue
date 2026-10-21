<template>
    <!--
        The per-100g nutrient table for a linked food.

        Only rows the source actually carries are rendered. A missing nutrient
        is left out rather than shown as "0" or "—": USDA and Open Food Facts
        are both sparse, and a zero is a claim (P12 No-invent / P3 Honest).
        If nothing but energy is known, the caller's summary line has already
        said it and this list stays empty.

        Rows arrive pre-formatted from the server (`nutrients.display_rows`),
        which owns the label wording, the order, the units and the rounding.
        This component only decides layout — sub-rows indent, and the optional
        vitamins-and-minerals block hides behind a disclosure so a food with a
        rich USDA profile can't push the panel off a phone screen.
    -->
    <div v-if="panelRows.length || moreRows.length">
        <dl v-if="panelRows.length" class="nutrition-facts">
            <template v-for="row in panelRows" :key="row.label">
                <dt
                    class="nutrition-facts__label dora-text-secondary"
                    :class="{ 'nutrition-facts__label--sub': row.indent }"
                >{{ row.label }}</dt>
                <dd class="nutrition-facts__value">{{ row.value }}</dd>
            </template>
        </dl>

        <template v-if="moreRows.length">
            <BaseButton
                variant="ghost"
                dense
                size="sm"
                class="q-mt-xs"
                :icon="moreExpanded ? ICONS.collapse : ICONS.expand"
                :label="`Vitamins & minerals (${moreRows.length})`"
                @click="moreExpanded = !moreExpanded"
            />
            <dl v-if="moreExpanded" class="nutrition-facts q-mt-xs">
                <template v-for="row in moreRows" :key="row.label">
                    <dt class="nutrition-facts__label dora-text-secondary">{{ row.label }}</dt>
                    <dd class="nutrition-facts__value">{{ row.value }}</dd>
                </template>
            </dl>
        </template>
    </div>
</template>

<script setup lang="ts">
    import { computed, ref } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import type { LinkedNutritionFood } from 'src/models/stockItemDetail';
    import { ICONS } from 'src/style/icons';

    const props = defineProps<{
        food: LinkedNutritionFood;
    }>();

    // Collapsed by default, and it stays collapsed across food changes: the
    // block is a "tell me more" answer, not something the page owes the reader
    // on arrival.
    const moreExpanded = ref(false);

    const rows = computed(() => props.food.nutrient_rows ?? []);
    const panelRows = computed(() => rows.value.filter((r) => r.group === 'panel'));
    const moreRows = computed(() => rows.value.filter((r) => r.group === 'more'));
</script>

<style scoped>
    .nutrition-facts {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 2px 16px;
        margin: 0;
        font-size: 0.8125rem;
    }
    .nutrition-facts__label {
        margin: 0;
    }
    /* Sub-rows sit under their parent nutrient the way a printed panel sets
       them — indentation rather than an em-dash prefix, so the label reads as
       "Saturated" and not "— of which saturates". */
    .nutrition-facts__label--sub {
        padding-left: 12px;
    }
    .nutrition-facts__value {
        margin: 0;
        text-align: right;
        font-variant-numeric: tabular-nums;
        color: var(--text-primary);
    }
</style>
