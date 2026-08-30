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
        :class="[`filter-row--${variant}`, { 'filter-row--wide-wraps': wideWraps }]"
    >
        <slot />
    </div>
</template>

<script setup lang="ts">
    withDefaults(
        defineProps<{
            /** `chips` = content-width toggles; `fields` = uniform control scale. */
            variant?: 'chips' | 'fields';
            /** Let the band wrap onto further lines once there's desktop width
             *  to wrap into, instead of scrolling sideways (owner ask
             *  2026-08-28, for the cookbook's long field row).
             *
             *  Opt-in rather than the default because the two shapes suit
             *  different row lengths: sideways scroll keeps a short row on one
             *  line, and only a row with more controls than fit is better off
             *  stacked. Below the breakpoint every row scrolls regardless —
             *  wrapping fourteen controls on a phone builds a wall. */
            wideWraps?: boolean;
        }>(),
        { variant: 'chips', wideWraps: false },
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
    /* Owner feedback 2026-08-28: "1 or 2 px extra space between filter rows…
       commonly applied across pages with filters". Lives here rather than on
       each page for exactly that reason — every stacked filter band in the app
       (Stock overview, Cookbook) comes through this component, so one rule
       covers them and a new page gets it for free. Sibling rule, so a lone row
       still sits flush against the panel's own padding. */
    .filter-row + .filter-row {
        margin-top: 2px;
    }
    /* 600px is Quasar's `sm` floor — the same line `$q.screen.lt.sm` draws, so
       "desktop" means the same thing here as it does in the components that
       branch in script. Overflow goes back to visible on *both* axes: a
       wrapping row can never overflow horizontally, and leaving `auto` on it
       clips the focus rings at the row's edge. Both axes deliberately — CSS
       promotes a `visible` axis to `auto` whenever its partner is `hidden`, so
       setting `overflow-x` alone silently computed straight back to `auto`
       (measured in the browser; it did).
       `.no-wrap` is a Quasar utility class on the element, so this needs the
       specificity of two classes to beat it. */
    @media (min-width: 600px) {
        .filter-row--wide-wraps.filter-row--wide-wraps {
            flex-wrap: wrap;
            overflow: visible;
            row-gap: var(--space-2);
        }
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
       of filters"), 2026-08-19 ("can we not achieve uniformity via base
       components?") and 2026-08-29 ("some filters seem bigger than others for
       no reason (kcal, ingredient count) — consistency").

       One height and **one** width for everything. There used to be a second,
       20px-wider track for the numeric bounds, justified by a label
       ("Missing ingredients ≤") that was deleted on 2026-08-20 — so the only
       thing left holding the two tracks apart was the fact they existed. The
       sort control keeps its own, wider track: it packs a direction chip
       *inside* the field, which is a real difference in what the control
       holds rather than a difference in species. */
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
    /* The track for anything in a fields row, so a control added later lands
       at the right width without the page restating it. The one opt-out left
       is `.filter-row__auto` (content-sized). */
    .filter-row--fields > :deep(:not(.filter-row__auto)) {
        min-width: var(--filter-control-w);
        max-width: var(--filter-control-w);
    }
    .filter-row--fields > :deep(.sort-control) {
        min-width: var(--filter-control-w-sort);
        max-width: var(--filter-control-w-sort);
    }
</style>
