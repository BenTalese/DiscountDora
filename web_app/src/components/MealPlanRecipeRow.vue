<template>
    <!-- BRIEF_MEAL_PLANNER_RAIL_AND_SHELL §4.5 — the meal planner rail's row.
         Text-first by settled decision, not preference: `RecipeRow.vue:23-27`
         records the owner call of 2026-08-18 folding the show-photos toggle into
         the cards/compact switch, so compact IS the without-photos shape; and
         `seed_builders.py` sets `image=None` on every seeded recipe, so a fresh
         install has zero recipe photos anyway. A thumbnail proposal must answer
         that seed-coverage problem first.

         Why not reuse `RecipeRow.vue`: four blockers, all structural. Its
         `compact` is derived from the VIEWPORT (`$q.screen.lt.sm`), so in a
         280px rail on a desktop it believes it has full width; its trailing
         action cluster is `flex: 0 0 auto` at ~180-200px, so only the name zone
         shrinks and the name gets ~60px; the squeeze that would fix that is
         behind `@media (max-width: 599px)`, another viewport query that never
         fires here; and its four actions are cookbook verbs, where the rail has
         exactly one — add to the targeted slot.

         What IS shared is the arithmetic: `useRecipeDisplay` is the single
         authority for the meta figures both cookbook views use, so the rail
         cannot drift from them (R-003). This component decides layout only. -->
    <div
        class="mp-row dora-press"
        :class="{
            'mp-row--targeting': mode === 'targeting',
            'mp-row--suggesting': mode === 'suggesting',
        }"
        role="button"
        tabindex="0"
        :aria-label="ariaLabel"
        @click="emit('pick', recipe.recipe_id)"
        @keydown.enter.prevent="emit('pick', recipe.recipe_id)"
        @keydown.space.prevent="emit('pick', recipe.recipe_id)"
    >
        <div class="mp-row__body">
            <div class="mp-row__name">{{ recipe.name }}</div>

            <!-- One meta line of at most two facts. Browsing shows the figures;
                 targeting replaces them with the destination, because when you
                 have armed a slot the only question left is "does this go
                 there"; suggesting replaces them with Dora's reason. -->
            <div v-if="mode === 'targeting'" class="mp-row__meta mp-row__meta--target">
                <q-icon :name="ICONS.arrow_forward" size="14px" />
                {{ targetSlot }}
            </div>
            <div v-else-if="mode === 'suggesting' && reasonText" class="mp-row__meta mp-row__meta--reason">
                <q-icon :name="ICONS.auto_awesome" size="14px" />
                {{ reasonText }}
            </div>
            <div v-else-if="metaFacts" class="mp-row__meta">{{ metaFacts }}</div>
        </div>

        <!-- F26 / F42 / FU-088 — the cooked-pool controls for batch households.
             F42 is an open complaint that the on-hand count "is a bit hidden,
             could be better displayed… make the number bigger maybe", so the
             count is a real figure at display size rather than a caption, and
             the ± controls sit beside it. Kept out of the flow above so a
             non-batch install renders a plain two-line row. -->
        <div
            v-if="batchEnabled"
            class="mp-row__pool"
            @click.stop
        >
            <BaseButton
                variant="icon"
                size="sm"
                :icon="ICONS.remove"
                :disable="recipe.available_meals <= 0"
                aria-label="One fewer cooked"
                @click="emit('poolAdjust', recipe.recipe_id, -1)"
            >
                <q-tooltip>One fewer cooked</q-tooltip>
            </BaseButton>
            <span class="mp-row__pool-count">{{ recipe.available_meals }}</span>
            <BaseButton
                variant="icon"
                size="sm"
                :icon="ICONS.add"
                aria-label="One more cooked"
                @click="emit('poolAdjust', recipe.recipe_id, 1)"
            >
                <q-tooltip>One more cooked</q-tooltip>
            </BaseButton>
            <BaseButton
                variant="icon"
                size="sm"
                :icon="ICONS.restaurant"
                aria-label="Log a cook"
                @click="emit('logCook', recipe.recipe_id)"
            >
                <q-tooltip>Log a cook…</q-tooltip>
            </BaseButton>
        </div>
    </div>
</template>

<script setup lang="ts">
    import BaseButton from 'src/components/BaseButton.vue';
    import { useRecipeDisplay } from 'src/composables/useRecipeDisplay';
    import type { Recipe } from 'src/models/recipe';
    import { ICONS } from 'src/style/icons';
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{
            recipe: Recipe;
            /** Drives what the meta line says. Explicit prop, never a viewport
             *  sniff or a container query (R-019 / ADR-014) — the rail's width
             *  has nothing to do with the window's. */
            mode?: 'browsing' | 'targeting' | 'suggesting' | undefined;
            /** Destination slot name, shown in `targeting` mode. */
            targetSlot?: string | undefined;
            /** Dora's reason phrase, shown in `suggesting` mode. */
            reasonText?: string | undefined;
            batchEnabled?: boolean | undefined;
        }>(),
        { mode: 'browsing', batchEnabled: false },
    );

    const emit = defineEmits<{
        (e: 'pick', recipeId: string): void;
        (e: 'poolAdjust', recipeId: string, delta: number): void;
        (e: 'logCook', recipeId: string): void;
    }>();

    const display = useRecipeDisplay(() => props.recipe);

    /** At most two facts — time and kcal, whichever exist. The rail is 280px;
     *  the cookbook's four-part meta line does not fit and would wrap into the
     *  next row's space. */
    const metaFacts = computed(() => {
        const facts: string[] = [];
        const time = display.totalTime.value;
        if (time !== null) facts.push(`${time}m`);
        const { value, judgeable } = display.kcal.value;
        if (value !== null) {
            facts.push(`${Math.round(value)} kcal${judgeable ? '' : ' (part)'}`);
        }
        return facts.join(' · ');
    });

    const ariaLabel = computed(() => {
        if (props.mode === 'targeting' && props.targetSlot) {
            return `${props.recipe.name} — add to ${props.targetSlot}`;
        }
        return props.recipe.name;
    });
</script>

<style scoped>
    /* R-001 carve-out: the brief (§4.5) asks for this row's chrome — bordered
       flat surface, accent-tinted hover, no lift — to be promoted to a SHARED
       class rather than a third private copy, since the look originated on
       `StockItemRow` and was already copied once to `RecipeRow`. That
       extraction is not done here: it would mean re-skinning both of those
       rows in a unit whose scope is the meal-planner rail, which is the kind
       of adjacent-surface edit R-007 exists to stop. The duplication is real
       and is logged as a follow-up; this block is the third copy until then. */
    .mp-row {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        width: 100%;
        padding: var(--space-2);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-sm);
        background: var(--surface-component);
        cursor: pointer;
        text-align: left;
        transition: background var(--motion-fast) var(--motion-ease),
            border-color var(--motion-fast) var(--motion-ease);
    }
    .mp-row + .mp-row {
        margin-top: var(--space-1);
    }
    .mp-row:hover {
        background: color-mix(in srgb, var(--brand-primary) 6%, var(--surface-component));
        border-color: color-mix(in srgb, var(--brand-primary) 35%, var(--border-default));
    }
    /* D-016 / A6 — a real focus ring. `RecipeRow` is a q-card with a click
       handler and no focus state, so it misses this today; the brief is
       explicit that the rail must not inherit that gap. */
    .mp-row:focus-visible {
        outline: 2px solid var(--brand-primary);
        outline-offset: 2px;
    }

    .mp-row__body {
        flex: 1 1 auto;
        min-width: 0;
    }

    /* FU-693 — `.recipe-row__name` is `1.05rem`, off the D-003 scale, kept only
       for parity with `StockItemRow`. A rail row would have been the THIRD site.
       Resolved as the brief recommended: use the token. A 280px rail is not
       where a 0.05rem parity is legible, and the scale is the rule. */
    .mp-row__name {
        font-size: calc(var(--font-size-md) * 1rem);
        font-weight: 500;
        line-height: 1.3;
        /* Name may take two lines, then clamps — a long recipe name must not
           push the row to four lines and break the virtual scroller's fixed
           item height. */
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .mp-row__meta {
        margin-top: 2px;
        font-size: calc(var(--font-size-sm) * 1rem);
        color: var(--text-secondary);
        display: flex;
        align-items: center;
        gap: var(--space-1);
        min-width: 0;
    }
    .mp-row__meta--target {
        color: var(--brand-primary);
        font-weight: 500;
    }
    .mp-row__meta--reason {
        color: var(--brand-primary);
    }

    .mp-row__pool {
        flex: 0 0 auto;
        display: flex;
        align-items: center;
        gap: 2px;
    }
    /* F42 — "the number is a bit hidden, could be better displayed… make the
       number bigger maybe". It was a caption line reading "N free"; it is now
       the row's one numeric figure, at display weight. */
    .mp-row__pool-count {
        min-width: 1.5rem;
        text-align: center;
        font-weight: 600;
        font-variant-numeric: tabular-nums;
    }
</style>
