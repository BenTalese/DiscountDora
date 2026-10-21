// @vitest-environment jsdom
// DR-15 / D-010 — the micro-feedback class lifecycle.
//
// The *look* of these animations can only be judged by eye in a real browser
// (the verify pane is rAF-starved and pins transitions at their start value),
// so the visual walk lives in DORA_VERIFY.md. What IS worth pinning here is
// the part that would break silently and isn't visible in a screenshot: the
// class must appear only on a real change, and must be REMOVED again. A class
// left on re-runs its animation on every subsequent re-render, which is how a
// one-shot acknowledgement turns into the ambient wallpaper D-010 warns about.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick, ref } from 'vue';
import { mount } from '@vue/test-utils';

import { motionDurationMs, useMicroFeedback } from 'src/composables/useMicroFeedback';

/** Settle the microtask queue. The composable's watcher fires during a flush
 *  and schedules its class write on the *next* tick, whose render then needs a
 *  tick of its own — so a single `await nextTick()` sees the DOM one step
 *  short. */
async function flush(): Promise<void> {
    await nextTick();
    await nextTick();
    await nextTick();
}

/** Minimal host: one div carrying whatever the composable hands back. */
function host(kind: 'settle' | 'bump' = 'settle') {
    const source = ref(0);
    const Comp = defineComponent({
        setup() {
            const feedback = useMicroFeedback(() => source.value, kind);
            return () => h('div', { class: ['probe', feedback.value] });
        },
    });
    const wrapper = mount(Comp);
    const classes = () => wrapper.get('div').classes();
    return { source, wrapper, classes };
}

describe('useMicroFeedback', () => {
    beforeEach(() => vi.useFakeTimers());
    afterEach(() => vi.useRealTimers());

    it('applies nothing on mount — only a change is feedback-worthy', async () => {
        const { classes } = host();
        await nextTick();
        expect(classes()).not.toContain('dora-settle');
    });

    it('applies the class on a change and removes it once the cycle is over', async () => {
        const { source, classes } = host('settle');

        source.value = 1;
        await flush();
        expect(classes()).toContain('dora-settle');

        // Still on while the animation is running...
        vi.advanceTimersByTime(100);
        await flush();
        expect(classes()).toContain('dora-settle');

        // ...and gone once the token duration (+ tail) has elapsed.
        vi.advanceTimersByTime(200);
        await flush();
        expect(classes()).not.toContain('dora-settle');
    });

    it('uses the requested variant', async () => {
        const { source, classes } = host('bump');
        source.value = 1;
        await flush();
        expect(classes()).toContain('dora-bump');
        expect(classes()).not.toContain('dora-settle');
    });

    it('ignores a write that does not change the value', async () => {
        const { source, classes } = host();
        source.value = 0;
        await flush();
        expect(classes()).not.toContain('dora-settle');
    });

    it('restarts rather than stacking when a second change lands mid-cycle', async () => {
        const { source, classes } = host('bump');

        source.value = 1;
        await flush();
        vi.advanceTimersByTime(60);

        source.value = 2;
        await flush();
        expect(classes()).toContain('dora-bump');

        // The first change's timer must not clear the second change's class.
        vi.advanceTimersByTime(110);
        await flush();
        expect(classes()).toContain('dora-bump');

        vi.advanceTimersByTime(200);
        await flush();
        expect(classes()).not.toContain('dora-bump');
    });

    it('drops its timer on unmount', async () => {
        const { source, wrapper } = host();
        source.value = 1;
        await flush();
        // Would throw on a write to an unmounted component's ref if the timer
        // outlived the instance.
        expect(() => {
            wrapper.unmount();
            vi.advanceTimersByTime(500);
        }).not.toThrow();
    });
});

describe('motionDurationMs', () => {
    afterEach(() => {
        document.documentElement.style.removeProperty('--probe-duration');
    });

    it('parses a ms-suffixed token', () => {
        document.documentElement.style.setProperty('--probe-duration', '250ms');
        expect(motionDurationMs('--probe-duration')).toBe(250);
    });

    it('parses the near-zero value the reduced-motion block substitutes', () => {
        document.documentElement.style.setProperty('--probe-duration', '0.01ms');
        expect(motionDurationMs('--probe-duration')).toBeCloseTo(0.01);
    });

    it('scales a seconds-suffixed token', () => {
        document.documentElement.style.setProperty('--probe-duration', '0.4s');
        expect(motionDurationMs('--probe-duration')).toBe(400);
    });

    it('falls back when the token is unset or unparseable', () => {
        expect(motionDurationMs('--nope-not-a-token', 999)).toBe(999);
        document.documentElement.style.setProperty('--probe-duration', 'inherit');
        expect(motionDurationMs('--probe-duration', 999)).toBe(999);
    });
});
