<template>
    <!-- DR-15 / D-010: same micro-feedback pair as FilterChip, and this
         control needs it more — one click can move between three states whose
         only difference is a fill colour and a label, so the bump is what
         confirms the cycle advanced rather than the click missing. -->
    <q-chip
        clickable
        outline
        :class="['dora-press', cycleFeedback]"
        :selected="modelValue !== 'off'"
        :color="chipColour"
        :text-color="modelValue !== 'off' ? 'white' : undefined"
        @click="onCycle"
    >
        <q-icon v-if="iconForState" :name="iconForState" size="14px" class="q-mr-xs" />
        {{ labelForState }}
    </q-chip>
</template>

<script setup lang="ts">
    /**
     * Tri-state filter chip — cycles through `off → include → exclude → off`
     * on each click. Used where a boolean "X only" filter would benefit from
     * its inverse ("not X") on the same control rather than two separate
     * chips (R-001 + Charter Effortless).
     *
     * - **off**: outlined, neutral. The default; no constraint applied.
     * - **include**: filled in `includeColor` (default semantic `info`),
     *   the standard "X only" mode.
     * - **exclude**: filled in `excludeColor` (default semantic `negative`),
     *   the "not X" mode. The label and icon can swap in this mode so the
     *   user reads the negation directly.
     */
    import { useMicroFeedback } from 'src/composables/useMicroFeedback';
    import { computed } from 'vue';

    export type TriState = 'off' | 'include' | 'exclude';

    const props = withDefaults(
        defineProps<{
            modelValue: TriState;
            includeLabel: string;
            excludeLabel: string;
            includeIcon?: string;
            excludeIcon?: string;
            includeColor?: string;
            excludeColor?: string;
        }>(),
        {
            includeColor: 'info',
            excludeColor: 'negative',
        },
    );

    const emit = defineEmits<{
        (e: 'update:modelValue', value: TriState): void;
    }>();

    const labelForState = computed(() =>
        props.modelValue === 'exclude' ? props.excludeLabel : props.includeLabel,
    );
    const iconForState = computed<string | undefined>(() =>
        props.modelValue === 'exclude'
            ? (props.excludeIcon ?? props.includeIcon)
            : props.includeIcon,
    );
    const chipColour = computed<string | undefined>(() => {
        if (props.modelValue === 'include') return props.includeColor;
        if (props.modelValue === 'exclude') return props.excludeColor;
        return undefined;
    });

    const cycleFeedback = useMicroFeedback(() => props.modelValue, 'bump');

    function onCycle(): void {
        const next: TriState =
            props.modelValue === 'off' ? 'include'
            : props.modelValue === 'include' ? 'exclude'
            : 'off';
        emit('update:modelValue', next);
    }
</script>
