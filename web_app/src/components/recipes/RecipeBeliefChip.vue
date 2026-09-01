<template>
    <!--
        FU-653 — Dora's belief about a recipe, as a remark.

        Extracted from `RecipeCard` + `RecipeRow` on 2026-09-01 (R-003):
        both rendered the same chip with the same props and the same
        tooltip, and the owner's "filled with neutral text" restyle would
        otherwise have had to be made twice. Callers decide only whether
        the label shows — the compact row suppresses it for width and
        leans on the tooltip.

        Neutral, not outline (owner 2026-09-01): the outline version was
        hard to read in both themes. See `.dora-chip--neutral` in
        `colours.scss` for the D-002/D-013 reasoning — the semantic colour
        survives on the icon only.
    -->
    <q-chip
        v-if="recipe.inference_hint"
        dense
        :icon="ICONS.dora_voice"
        class="dora-chip--neutral"
        :class="recipe.inference_hint === 'at_risk' ? 'dora-chip--warning' : 'dora-chip--positive'"
    >
        <span v-if="labelled">
            {{ recipe.inference_hint === 'at_risk' ? 'May be short' : 'May be cookable' }}
        </span>
        <q-tooltip max-width="300px">{{ inferenceTooltip }}</q-tooltip>
    </q-chip>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import type { Recipe } from 'src/models/recipe';
    import { useRecipeDisplay } from 'src/composables/useRecipeDisplay';

    const props = withDefaults(
        defineProps<{
            recipe: Recipe;
            /** Show the wording beside the glyph. Off in the compact row,
             *  where the tooltip carries it instead. */
            labelled?: boolean;
        }>(),
        { labelled: true },
    );

    const { inferenceTooltip } = useRecipeDisplay(() => props.recipe);
</script>
