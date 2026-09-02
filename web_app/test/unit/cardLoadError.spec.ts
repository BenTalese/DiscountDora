// @vitest-environment jsdom
/**
 * FU-840 — a dashboard card that failed to load must say so, not borrow its
 * empty state.
 *
 * Every slot loader used to `catch { thing.value = null }`, so the card fell
 * through to "nothing here yet". The consequences were specific and bad:
 *
 *   savings 500s  →  "Finish a shop and I'll tally what you kept."
 *   alerts 500s   →  "All clear — nothing needs your attention right now."
 *
 * The second is the one that matters: the dashboard told you nothing was wrong
 * at precisely the moment it could not know. Failure was indistinguishable from
 * absence, biased toward reassurance — Honesty inverted (`DASHBOARD_PAGE_REVIEW`
 * §4.7, finding 10, eleven instances).
 *
 * The state itself is a component, so it is worth pinning the two things that
 * make it *not* an empty state: it names the failure, and it offers the one
 * action that can fix it.
 */
import { describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import CardLoadError from 'src/components/dashboard/CardLoadError.vue';

/** Quasar's components aren't installed in this bare mount; stub the two used. */
const global = {
    stubs: {
        'q-icon': { template: '<i class="q-icon" />' },
        BaseButton: {
            name: 'BaseButton',
            props: ['label', 'icon', 'loading'],
            emits: ['click'],
            // `data-loading` mirrors the prop so the busy state can be asserted
            // from the DOM as well as from props.
            template:
                '<button class="stub-btn" :data-loading="String(loading)" @click="$emit(\'click\')">{{ label }}</button>',
        },
    },
};

describe('CardLoadError', () => {
    it('states that loading failed, in Dora\'s voice, by default', () => {
        const w = mount(CardLoadError, { global });
        expect(w.text()).toContain("I couldn't load this just now.");
    });

    it('never renders anything that reads as "there is nothing here"', () => {
        // The regression guard: this component exists precisely so a failure
        // stops being reported as an absence. If someone reworded it into
        // "nothing to show", the whole point would be lost.
        const w = mount(CardLoadError, { global });
        const text = w.text().toLowerCase();
        for (const reassurance of [
            'all clear',
            'nothing needs',
            'nothing to',
            'no data',
            "you're on top of things",
        ]) {
            expect(text, `copy must not reassure: "${reassurance}"`).not.toContain(reassurance);
        }
    });

    it('takes per-card copy so a card can name what failed', () => {
        const w = mount(CardLoadError, {
            props: { line: "I couldn't check your alerts just now." },
            global,
        });
        expect(w.text()).toContain('alerts');
    });

    it('offers a retry and emits it', async () => {
        const w = mount(CardLoadError, { global });
        const btn = w.find('.stub-btn');
        expect(btn.exists()).toBe(true);
        expect(btn.text()).toBe('Try again');
        await btn.trigger('click');
        expect(w.emitted('retry')).toHaveLength(1);
    });

    it('shows a brief busy state after a retry, then clears it', async () => {
        vi.useFakeTimers();
        try {
            const w = mount(CardLoadError, { global });
            await w.find('.stub-btn').trigger('click');
            expect(w.find('.stub-btn').attributes('data-loading')).toBe('true');
            vi.advanceTimersByTime(1500);
            await w.vm.$nextTick();
            expect(w.find('.stub-btn').attributes('data-loading')).toBe('false');
        } finally {
            vi.useRealTimers();
        }
    });

    it('is announced to assistive tech', () => {
        // A card silently swapping to an error is invisible to a screen reader;
        // `role="status"` makes the change announced (A6).
        const w = mount(CardLoadError, { global });
        expect(w.attributes('role')).toBe('status');
    });
});
