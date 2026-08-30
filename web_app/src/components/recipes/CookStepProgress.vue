<template>
    <!--
        Cook-mode position indicator. Owner feedback 2026-08-28: *"Step
        indicator is a bit boring (styling). 'Step 1 of 6' in tiny boring text.
        Could be stylish/cool/fancy and in-line with the progress bar."*

        So the count and the bar are one object rather than a `text-caption`
        line floating above a `q-linear-progress`: a tinted badge carrying the
        number at display size, and a track beside it. Extracted rather than
        inlined because both cook-mode faces need it (R-001) — the step view
        counts steps, the image view counts photos — and they should read
        identically.

        The track is segmented when the count is small enough for segments to
        be legible, and falls back to a single fill bar past that. Purely an
        indicator: jumping between steps is the "All steps" list's job, so
        there is no sub-44px tap target here to answer for (D-004).
    -->
    <div class="cook-progress">
        <div class="cook-progress__badge">
            <span class="cook-progress__word">{{ noun }}</span>
            <span class="cook-progress__current">{{ current + 1 }}</span>
            <span class="cook-progress__total">of {{ total }}</span>
        </div>
        <div
            class="cook-progress__track"
            :class="{ 'cook-progress__track--continuous': !segmented }"
            role="progressbar"
            :aria-label="`${noun} ${current + 1} of ${total}`"
            :aria-valuenow="current + 1"
            aria-valuemin="1"
            :aria-valuemax="total"
        >
            <template v-if="segmented">
                <span
                    v-for="position in total"
                    :key="position"
                    class="cook-progress__segment"
                    :class="{
                        'cook-progress__segment--done': position < current + 1,
                        'cook-progress__segment--current': position === current + 1,
                    }"
                />
            </template>
            <span v-else class="cook-progress__fill" :style="{ width: fillWidth }" />
        </div>
    </div>
</template>

<script setup lang="ts">
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{
            /** Zero-based position of the step/photo being shown. */
            current: number;
            total: number;
            /** Displayed word for one unit of progress ("Step", "Photo"). */
            noun?: string;
        }>(),
        { noun: 'Step' },
    );

    /** Past this many, individual segments are thinner than the gaps between
     *  them and read as noise; one continuous fill is honest at any length. */
    const SEGMENT_LIMIT = 14;

    const segmented = computed(() => props.total > 0 && props.total <= SEGMENT_LIMIT);

    const fillWidth = computed(() => {
        if (props.total <= 0) return '0%';
        const fraction = (props.current + 1) / props.total;
        return `${Math.max(0, Math.min(1, fraction)) * 100}%`;
    });
</script>

<style scoped lang="scss">
    .cook-progress {
        display: flex;
        align-items: center;
        gap: var(--space-4);
    }
    .cook-progress__badge {
        display: flex;
        align-items: baseline;
        gap: var(--space-2);
        flex: 0 0 auto;
        padding: var(--space-2) var(--space-4);
        border-radius: var(--radius-lg);
        border: 1px solid color-mix(in srgb, var(--brand-primary) 35%, transparent);
        background: color-mix(in srgb, var(--brand-primary) 12%, transparent);
        white-space: nowrap;
    }
    .cook-progress__word {
        font-size: 0.6875rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-secondary);
    }
    .cook-progress__current {
        font-size: 1.5rem;
        font-weight: 700;
        line-height: 1;
        color: var(--brand-primary);
        font-variant-numeric: tabular-nums;
    }
    .cook-progress__total {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-secondary);
        font-variant-numeric: tabular-nums;
    }
    .cook-progress__track {
        display: flex;
        align-items: center;
        gap: 4px;
        flex: 1 1 auto;
        min-width: 0;
    }
    .cook-progress__segment {
        flex: 1 1 0;
        height: 10px;
        border-radius: var(--radius-sm);
        background: var(--surface-sunken);
        border: 1px solid var(--border-default);
        transition:
            background-color var(--motion-normal, 200ms) ease,
            transform var(--motion-normal, 200ms) ease;
    }
    .cook-progress__segment--done {
        background: color-mix(in srgb, var(--brand-primary) 45%, transparent);
        border-color: transparent;
    }
    /* The one segment the cook is standing on: full-strength, taller than its
       neighbours, and ringed — findable at arm's length across a kitchen. */
    .cook-progress__segment--current {
        background: var(--brand-primary);
        border-color: var(--brand-primary);
        height: 16px;
        box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand-primary) 20%, transparent);
    }
    .cook-progress__track--continuous {
        position: relative;
        height: 10px;
        border-radius: var(--radius-lg);
        background: var(--surface-sunken);
        border: 1px solid var(--border-default);
        overflow: hidden;
    }
    .cook-progress__fill {
        position: absolute;
        inset: 0 auto 0 0;
        background: var(--brand-primary);
        border-radius: inherit;
        transition: width var(--motion-normal, 200ms) ease;
    }
    @media (max-width: 599px) {
        .cook-progress {
            gap: var(--space-3);
        }
        .cook-progress__badge {
            padding: var(--space-1) var(--space-3);
        }
        .cook-progress__current {
            font-size: 1.25rem;
        }
    }
</style>
