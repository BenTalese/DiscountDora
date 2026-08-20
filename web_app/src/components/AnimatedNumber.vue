<template>
    <span>{{ display }}</span>
</template>

<script lang="ts" setup>
    // Tweens its displayed value whenever `value` changes, so dashboard
    // stats count up/down instead of snapping. Honours prefers-reduced-motion
    // (jumps straight to the target) and falls back to an instant set if the
    // browser can't run rAF. Formatting (decimals, prefix/suffix) is applied
    // to the in-flight tweened value so currency/counts read correctly.
    import { motionDurationMs } from 'src/composables/useMicroFeedback';
    import { computed, onBeforeUnmount, ref, watch } from 'vue';

    const props = withDefaults(
        defineProps<{
            value: number;
            decimals?: number;
            /** Override the tween length. Leave unset to ride the motion
             *  tokens — see `duration` below. */
            durationMs?: number;
            prefix?: string;
            suffix?: string;
        }>(),
        { decimals: 0, prefix: '', suffix: '' },
    );

    /* DR-15 / D-010 — "all animation reads --motion-* tokens, no literal ms".
       This is a JS tween rather than a CSS transition, but the rule is about
       the app having one set of durations, not about the mechanism: a
       hardcoded 600ms here is exactly the drift the tokens exist to prevent.
       A count-up is a *large surface* settle, so it takes --motion-slow, read
       at call time so the reduced-motion rewrite (~0ms) applies here too —
       which is also why the rAF path keeps its own prefers-reduced-motion
       shortcut below: at 0.01ms the tween would still run for one frame. */
    const duration = computed(() => props.durationMs ?? motionDurationMs('--motion-slow'));

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
            const t = Math.min(1, (now - start) / duration.value);
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
