<template>
    <!--
        The per-100g nutrient table for a linked food.

        Only rows the source actually carries are rendered. A missing nutrient
        is left out rather than shown as "0" or "—": USDA and Open Food Facts
        are both sparse, and a zero is a claim (P12 No-invent / P3 Honest).
        If nothing but energy is known, the caller's summary line has already
        said it and this list stays empty.
    -->
    <dl v-if="rows.length" class="nutrition-facts">
        <template v-for="row in rows" :key="row.label">
            <dt class="nutrition-facts__label dora-text-secondary">{{ row.label }}</dt>
            <dd class="nutrition-facts__value">{{ row.value }}</dd>
        </template>
    </dl>
</template>

<script setup lang="ts">
    import { computed } from 'vue';
    import type { LinkedNutritionFood } from 'src/models/stockItemDetail';

    const props = defineProps<{
        food: LinkedNutritionFood;
    }>();

    type Row = { label: string; value: string };

    // Whole numbers for energy and sodium (nobody reads 412.7 kcal); one
    // decimal for the gram figures, where 0.4g vs 0g is a real difference.
    function grams(value: number | null): string | null {
        return value === null ? null : `${round(value, 1)} g`;
    }
    function whole(value: number | null, unit: string): string | null {
        return value === null ? null : `${Math.round(value)} ${unit}`;
    }
    function round(value: number, places: number): string {
        return String(Number(value.toFixed(places)));
    }

    // Order mirrors `dora_api/features/nutrition/nutrients.py` so the app reads
    // the same top-to-bottom on both sides of the wire.
    const rows = computed<Row[]>(() => {
        const f = props.food;
        const candidates: Array<[string, string | null]> = [
            ['Energy', whole(f.kcal_per_100g, 'kcal')],
            ['Protein', grams(f.protein_g_per_100g)],
            ['Carbohydrate', grams(f.carbs_g_per_100g)],
            ['— of which sugars', grams(f.sugars_g_per_100g)],
            ['Fat', grams(f.fat_g_per_100g)],
            ['— of which saturates', grams(f.saturated_fat_g_per_100g)],
            ['Fibre', grams(f.fibre_g_per_100g)],
            ['Sodium', whole(f.sodium_mg_per_100g, 'mg')],
        ];
        return candidates
            .filter((entry): entry is [string, string] => entry[1] !== null)
            .map(([label, value]) => ({ label, value }));
    });
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
    .nutrition-facts__value {
        margin: 0;
        text-align: right;
        font-variant-numeric: tabular-nums;
        color: var(--text-primary);
    }
</style>
