<template>
    <!--
        C-4 Chunk 2 (L237) — dietary-tag include/exclude filter. As of
        FU-083 follow-up this is a thin wrapper over the generalised
        `TriStateFilter`; the API stayed the same so existing call sites
        (RecipesOverview's tags + tools usage) don't need to change.
        New surfaces should use `TriStateFilter` directly.
    -->
    <TriStateFilter
        :options="options"
        :include="include"
        :exclude="exclude"
        :label="resolvedLabel"
        @update:include="(value: string[]) => emit('update:include', value)"
        @update:exclude="(value: string[]) => emit('update:exclude', value)"
    />
</template>

<script setup lang="ts">
    import { computed } from 'vue';
    import TriStateFilter from 'src/components/filters/TriStateFilter.vue';
    import type { TriStateOption } from 'src/components/filters/triStateFilterTypes';

    /** Dietary-tag options always supply `category` (the group header).
     *  `TriStateOption.category` is optional in general; for this filter
     *  it's required. */
    export type DietaryTagOption = Omit<TriStateOption, 'category'> & { category: string };

    const props = withDefaults(
        defineProps<{
            options: DietaryTagOption[];
            include: string[];
            exclude: string[];
            label?: string;
        }>(),
        { label: 'Dietary tags' },
    );

    const emit = defineEmits<{
        (e: 'update:include', value: string[]): void;
        (e: 'update:exclude', value: string[]): void;
    }>();

    // exactOptionalPropertyTypes — withDefaults still types `label` as
    // `string | undefined` even with a default. Re-resolve so the child
    // gets a definite string and matches its `label?: string` shape.
    const resolvedLabel = computed(() => props.label ?? 'Dietary tags');
</script>
