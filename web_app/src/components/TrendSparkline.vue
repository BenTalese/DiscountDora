<template>
    <svg
        v-if="values.length >= 2"
        :width="w"
        :height="h"
        :viewBox="`0 0 ${w} ${h}`"
        class="sparkline"
        preserveAspectRatio="none"
    >
        <polyline :points="polyline" fill="none" :stroke="strokeColour" stroke-width="1.5" />
        <circle :cx="lastPoint.x" :cy="lastPoint.y" r="2" :fill="strokeColour" />
    </svg>
    <span v-else class="text-caption dora-text-muted">—</span>
</template>

<script lang="ts" setup>
    import { computed } from 'vue';

    const props = withDefaults(
        defineProps<{
            // Series of values, oldest → newest.
            values: number[];
            width?: number;
            height?: number;
            color?: string;
        }>(),
        { width: 120, height: 28, color: '' },
    );

    const pad = 2;
    const w = computed(() => props.width ?? 120);
    const h = computed(() => props.height ?? 28);

    const strokeColour = computed(() => {
        if (props.color) return props.color;
        const first = props.values[0] ?? 0;
        const last = props.values[props.values.length - 1] ?? 0;
        const token = last <= first ? '--semantic-positive' : '--semantic-negative';
        if (typeof document === 'undefined') {
            return last <= first ? 'hsl(140, 50%, 45%)' : 'hsl(7, 75%, 56%)';
        }
        return getComputedStyle(document.documentElement)
            .getPropertyValue(token)
            .trim() || (last <= first ? 'hsl(140, 50%, 45%)' : 'hsl(7, 75%, 56%)');
    });

    const coords = computed(() => {
        const vals = props.values;
        const min = Math.min(...vals);
        const max = Math.max(...vals);
        const span = max - min || 1;
        const innerW = props.width - pad * 2;
        const innerH = props.height - pad * 2;
        return vals.map((v, i) => {
            const x = pad + (vals.length === 1 ? 0 : (i / (vals.length - 1)) * innerW);
            // Invert y so higher price is higher on the chart.
            const y = pad + innerH - ((v - min) / span) * innerH;
            return { x, y };
        });
    });

    const polyline = computed(() => coords.value.map((c) => `${c.x},${c.y}`).join(' '));
    const lastPoint = computed(() => coords.value[coords.value.length - 1] ?? { x: 0, y: 0 });
</script>

<style scoped>
    .sparkline {
        display: block;
    }
</style>
