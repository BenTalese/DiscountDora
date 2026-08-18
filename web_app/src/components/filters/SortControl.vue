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
            <q-btn
                flat
                dense
                round
                size="sm"
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
    // The append button sits inside the field; strip the padding Quasar adds
    // around append content so the field's height is unchanged by it.
    .sort-control__dir {
        margin-right: -4px;
    }
</style>
