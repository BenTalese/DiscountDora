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
    <q-select
        :model-value="sortBy"
        :options="options"
        :label="label"
        emit-value
        map-options
        outlined
        dense
        class="sort-control"
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
                 a bordered, tinted, full-inner-height block separated from the
                 value by its own border — the same treatment a split-button's
                 trailing half gets, which is exactly what this is. -->
            <q-btn
                unelevated
                dense
                class="sort-control__dir"
                :icon="sortDir === 'asc' ? ICONS.arrow_upward : ICONS.arrow_downward"
                :aria-label="`Sort ${directionLabel.toLowerCase()} — click to reverse`"
                @click.stop="toggleDirection"
            >
                <q-tooltip>{{ directionLabel }}</q-tooltip>
            </q-btn>
        </template>
    </q-select>
</template>

<script setup lang="ts">
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';

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
    // The append button sits inside the field, so it owns the field's right
    // edge: negative margins cancel the padding Quasar puts around append
    // content, letting the button run the full inner height and butt up
    // against the border. Its own left border is the separator that makes it
    // read as a distinct target rather than a decorative glyph.
    //
    // Sized off `--filter-control-h` (owned by `FilterRow`) when there is one,
    // so it grows with the row instead of carrying a second copy of the
    // number (R-003). Standalone uses fall back to 40px.
    .sort-control__dir {
        --sort-dir-h: calc(var(--filter-control-h, 44px) - 4px);
        min-height: var(--sort-dir-h);
        height: var(--sort-dir-h);
        min-width: 44px;
        margin-right: -10px;
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
        border-left: 1px solid var(--border-default);
        background: var(--surface-sunken);
        color: var(--text-secondary);
    }
    .sort-control__dir:hover {
        background: color-mix(in srgb, var(--brand-primary) 12%, var(--surface-sunken));
        color: var(--text-primary);
    }
    // Quasar's ripple/focus helper paints the whole rounded rect; clip it to
    // the button's own (squared-left) shape.
    .sort-control__dir :deep(.q-focus-helper) {
        border-radius: inherit;
    }
</style>
