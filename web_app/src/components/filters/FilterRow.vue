<template>
    <!--
        One horizontal band of filter controls, sideways-scrolling instead of
        wrapping.

        Extracted 2026-08-19 from `RecipesOverview` and `StockOverview`, which
        had grown two near-identical copies of the same ~40 lines: the same
        `overflow-x` + hidden-scrollbar treatment (the controls overflowing IS
        the affordance), the same `flex: 0 0 auto` to stop items shrinking past
        their own width once the row scrolls, and — on the input rows — the same
        fixed control height and width track. Two copies of one layout rule is
        the shape R-001/R-003 exist to prevent, and it is what let the two pages
        drift to different control heights in the first place.

        Two shapes, one component:
          - default (`variant="chips"`): natural widths, for toggle chips.
          - `variant="fields"`: one height and one width track for every
            control, so selects, numeric bounds and `BaseFilterField`s read as
            one row of peers rather than a mix of species.
    -->
    <div
        class="filter-row row items-center no-wrap"
        :class="`filter-row--${variant}`"
    >
        <slot />
    </div>
</template>

<script setup lang="ts">
    withDefaults(
        defineProps<{
            /** `chips` = content-width toggles; `fields` = uniform control scale. */
            variant?: 'chips' | 'fields';
        }>(),
        { variant: 'chips' },
    );
</script>

<style scoped lang="scss">
    .filter-row {
        gap: var(--space-2);
        overflow-x: auto;
        overflow-y: hidden;
        padding-bottom: 2px;
        /* Hidden deliberately: a 2px bar under the controls is noise, and the
           controls running off the edge already reads as "there's more". */
        scrollbar-width: none;
    }
    .filter-row::-webkit-scrollbar {
        display: none;
    }
    /* `:deep()` throughout, not plain child selectors: every control in here
       arrives through the slot, so it carries the *parent page's* scope id and
       a scoped `.filter-row > *` would compile to a selector that can never
       match it. */
    /* A flex item will shrink past its own `min-width` once the row scrolls,
       which is what made the Location picker come out 311px next to its 180px
       siblings — it inherits a global `width: 100%` for `use-input` selects. */
    .filter-row > :deep(*) {
        flex: 0 0 auto;
    }

    /* ── The uniform control scale ─────────────────────────────────────
       Owner feedback 2026-08-18 ("dislike the sizing difference between types
       of filters") and 2026-08-19 ("can we not achieve uniformity via base
       components?"). One height for everything, and two width tracks: the
       text-ish controls share one, numeric bounds get a slightly wider one
       because their labels ("Missing ingredients ≤") outrun their content. */
    .filter-row--fields {
        /* 44px, not the 40px this row used to run at: these are inputs on a
           surface a finger uses (the row scrolls sideways *because* it's used
           on phones), so B3's "min height 44px" and D-004's 44×44 touch floor
           both apply. The 32–36px dense allowance is for desktop-only chrome,
           which this isn't. Holding one number rather than a breakpoint pair
           also keeps the sort-direction toggle inside it above the floor. */
        --filter-control-h: 44px;
        /* 210px, up from 180 (owner, 2026-08-21: "in some cases it can be too
           small… you hardly see anything of the selected value"). 180 was set
           when these fields showed a bare label; they now carry a leading icon
           (D-005), a clear button and a chevron, which between them spend
           ~90px before a single character of the value is drawn. */
        --filter-control-w: 210px;
        --filter-control-w-num: 230px;
        /* The sort control spends another ~46px on the direction chip inside
           the same field, so it gets its own track rather than making every
           neighbour as wide as its widest member. */
        --filter-control-w-sort: 250px;
    }
    /* q-field's inner control is what actually sets the height — the outer
       element just wraps it. */
    .filter-row--fields :deep(.q-field--dense .q-field__control) {
        height: var(--filter-control-h);
    }
    /* Default track for anything in a fields row, so a control added later
       lands at the right width without the page restating it. Callers opt out
       per control with `.filter-row__wide` (numeric bounds) or
       `.filter-row__auto` (content-sized). */
    .filter-row--fields > :deep(:not(.filter-row__auto)) {
        min-width: var(--filter-control-w);
        max-width: var(--filter-control-w);
    }
    .filter-row--fields > :deep(.filter-row__wide) {
        min-width: var(--filter-control-w-num);
        max-width: var(--filter-control-w-num);
    }
    .filter-row--fields > :deep(.sort-control) {
        min-width: var(--filter-control-w-sort);
        max-width: var(--filter-control-w-sort);
    }
</style>
