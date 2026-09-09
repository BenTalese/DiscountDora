<template>
    <!--
        Sort axis + direction as ONE control (owner feedback 2026-08-18:
        "attach the sort direction to the sort filter option picker so they are
        visually together, and make it consistent across screens").

        The direction toggle lives in the select's `#append` slot, so it sits
        inside the same bordered field rather than floating beside it as a
        separate button with its own height. That also means it inherits the
        field's height and border for free — the old standalone button measured
        36px next to a 40px select.

        The consistency half of the ask is what the `options` shape enforces: an
        axis carries its own direction wording (`ascLabel` / `descLabel`), so a
        screen can't express direction by listing "Name (A-Z)" and "Name (Z-A)"
        as two separate axes the way StockOverview used to. One axis, one
        toggle, everywhere.
    -->
    <BaseSelect
        :model-value="sortBy"
        :options="options"
        :label="label"
        emit-value
        map-options
        class="sort-control"
        dialog-title="Sort by"
        @update:model-value="onAxisChange"
    >
        <template #prepend>
            <q-icon :name="ICONS.sort" size="18px" />
        </template>
        <template #append>
            <!-- Owner feedback 2026-08-19: "can the sort direction arrow button
                 be any bigger … also it doesn't look very button-like (as in
                 you might not be able to tell you can click it/tap it)".
                 Both fixed here rather than at the call sites: it was `flat`
                 + `round` + `size="sm"`, i.e. a bare glyph at ~24px. It is now
                 a bordered, tinted chip inset in the field — see the style
                 block for why it is inset rather than flush to the edge. -->
            <q-btn
                unelevated
                dense
                class="sort-control__dir"
                :icon="sortDir === 'asc' ? ICONS.arrow_upward : ICONS.arrow_downward"
                :aria-label="`Sort ${directionLabel.toLowerCase()} — click to reverse`"
                @click.stop="toggleDirection"
            >
                <BaseTooltip>{{ directionLabel }}</BaseTooltip>
            </q-btn>
        </template>
    </BaseSelect>
</template>

<script setup lang="ts">
    import BaseTooltip from 'src/components/BaseTooltip.vue';
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseSelect from 'src/components/BaseSelect.vue';

    /** Axis definition narrowed to a page's own sort-key union, so a typo in a
     *  `value` is a compile error rather than a silently dead option. */
    export type SortAxisFor<T extends string> = Omit<SortAxis, 'value'> & { value: T };

    export type SortAxis = {
        label: string;
        value: string;
        /** How ascending reads on THIS axis, e.g. "Fastest first", "A → Z". */
        ascLabel: string;
        /** How descending reads on this axis, e.g. "Slowest first". */
        descLabel: string;
        /** Direction to snap to when this axis is picked. Defaults to 'desc'
         *  — most axes (recently made, most meals, highest kcal) want the big
         *  end first; name-like and "fewest/easiest" axes pass 'asc'. */
        defaultDir?: 'asc' | 'desc';
    };

    const props = withDefaults(
        defineProps<{
            sortBy: string;
            sortDir: 'asc' | 'desc';
            options: SortAxis[];
            label?: string;
        }>(),
        { label: 'Sort by' },
    );

    const emit = defineEmits<{
        (e: 'update:sortBy', value: string): void;
        (e: 'update:sortDir', value: 'asc' | 'desc'): void;
    }>();

    const activeAxis = computed(() => props.options.find((o) => o.value === props.sortBy));

    /** Reads the current direction in the active axis's own words, so the
     *  tooltip says "Fastest first" rather than a bare "Ascending". */
    const directionLabel = computed(() => {
        const axis = activeAxis.value;
        if (!axis) return props.sortDir === 'asc' ? 'Ascending' : 'Descending';
        return props.sortDir === 'asc' ? axis.ascLabel : axis.descLabel;
    });

    function toggleDirection() {
        emit('update:sortDir', props.sortDir === 'asc' ? 'desc' : 'asc');
    }

    /** Picking an axis also snaps the direction to that axis's conventional
     *  one, so the first thing you see makes sense (recently made → newest
     *  first; name → A→Z). The rule lives on the axis definition rather than
     *  in a per-page watcher, so each screen states it once alongside the
     *  labels instead of re-deriving it (R-003). */
    function onAxisChange(value: string) {
        emit('update:sortBy', value);
        const axis = props.options.find((o) => o.value === value);
        emit('update:sortDir', axis?.defaultDir ?? 'desc');
    }
</script>

<style scoped lang="scss">
    // The toggle is an inset chip inside the field, NOT a split-button half
    // flush to the field's right edge. It was written as the latter (full
    // inner height, `margin-right: -10px`, right-rounded, left-border-as-
    // separator) and both halves of that were wrong against the real DOM
    // (owner report 2026-08-20, measured):
    //
    //  1. It never reached the right edge. QSelect renders its dropdown
    //     chevron as a SECOND `.q-field__append` after any slotted one, so the
    //     chip sat mid-field with the chevron to its right — and the -10px
    //     margin slid it under that chevron. That collision is the "button
    //     outline / edge / fill visible sometimes, looks odd".
    //  2. It ate the field's top border. `.q-field__marginal` is a fixed 40px
    //     top-aligned inside the 44px control, so a full-height opaque chip
    //     started exactly on the border line — and Quasar paints the resting
    //     border as `.q-field__control:before`, i.e. UNDER the field's
    //     children, while the focus ring is `:after`, i.e. over them. Hence
    //     "chops off the top of the border only when unfocused".
    //
    // So: full radius, full border, no negative margin, and 3px of clearance
    // top and bottom. It still reads as a target — a bordered, tinted block
    // rather than the bare 24px glyph the 2026-08-19 feedback rejected.
    //
    // Sized off `--filter-control-h` (owned by `FilterRow`) when there is one,
    // so it grows with the row instead of carrying a second copy of the
    // number (R-003). Standalone uses fall back to 44px.
    .sort-control__dir {
        --sort-dir-h: calc(var(--filter-control-h, 44px) - 6px);
        min-height: var(--sort-dir-h);
        height: var(--sort-dir-h);
        min-width: 40px;
        border-radius: var(--radius-sm);
        border: 1px solid var(--border-default);
        background: var(--surface-sunken);
        color: var(--text-secondary);
    }
    // D-004 wants a 44x44 target; the chip is inset to 38x40 so the field's
    // border survives around it. This pushes the *hit* area back out to the
    // full 44 without changing what's drawn. (`.q-btn:before` is Quasar's
    // shadow box — `:after` is unused on a button, so it's free.)
    .sort-control__dir:after {
        content: '';
        position: absolute;
        top: -3px;
        bottom: -3px;
        left: -2px;
        right: -2px;
    }
    .sort-control__dir:hover {
        background: color-mix(in srgb, var(--brand-primary) 12%, var(--surface-sunken));
        color: var(--text-primary);
    }
    // Quasar's marginal is a fixed 40px block pinned to the top of the (44px)
    // control, so anything in it rides 2px high. Giving it the control's full
    // height centres the chip — and the chevron beside it — properly.
    .sort-control :deep(.q-field__marginal) {
        height: 100%;
    }
    // Quasar's ripple/focus helper paints its own rounded rect; match the
    // chip's.
    .sort-control__dir :deep(.q-focus-helper) {
        border-radius: inherit;
    }
</style>
