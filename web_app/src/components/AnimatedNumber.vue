<template>
    <span>{{ display }}</span>
</template>

<script lang="ts" setup>
    // Tweens its displayed value whenever `value` changes, so dashboard
    // stats count up/down instead of snapping. Honours prefers-reduced-motion
    // (jumps straight to the target) and falls back to an instant set if the
    // browser can't run rAF. Formatting (decimals, prefix/suffix) is applied
    // to the in-flight tweened value so currency/counts read correctly.
    import { onBeforeUnmount, ref, watch } from 'vue';

    const props = withDefaults(
        defineProps<{
            value: number;
            decimals?: number;
            durationMs?: number;
            prefix?: string;
            suffix?: string;
        }>(),
        { decimals: 0, durationMs: 600, prefix: '', suffix: '' },
    );

    const current = ref(props.value);
    const display = ref(format(props.value));
    let frame: number | null = null;

    function format(n: number): string {
        return props.prefix + n.toFixed(props.decimals) + props.suffix;
    }

    // Material's standard-decelerate curve: fast start, gentle settle.
    function easeOut(t: number): number {
        return 1 - Math.pow(1 - t, 3);
    }

    const prefersReduced =
        typeof window !== 'undefined' &&
        window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

    function tweenTo(target: number): void {
        if (frame !== null) cancelAnimationFrame(frame);

        if (prefersReduced || typeof requestAnimationFrame === 'undefined') {
            current.value = target;
            display.value = format(target);
            return;
        }

        const from = current.value;
        const delta = target - from;
        const start = performance.now();

        const step = (now: number): void => {
            const t = Math.min(1, (now - start) / props.durationMs);
            const v = from + delta * easeOut(t);
            current.value = v;
            display.value = format(v);
            if (t < 1) {
                frame = requestAnimationFrame(step);
            } else {
                current.value = target;
                display.value = format(target);
                frame = null;
            }
        };

        frame = requestAnimationFrame(step);
    }

    watch(
        () => props.value,
        (v) => tweenTo(v),
    );

    onBeforeUnmount(() => {
        if (frame !== null) cancelAnimationFrame(frame);
    });
</script>
