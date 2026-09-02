// @vitest-environment jsdom
/**
 * FU-821 — a tweened money figure must render through `formatMoney`.
 *
 * The bug: `AnimatedNumber` formats as `prefix + n.toFixed(decimals) + suffix`
 * with `decimals` defaulting to **0**, and all three dashboard money call sites
 * passed `:prefix="currencySymbol"` and no `decimals`. So:
 *
 *   "You've saved $128.45"  rendered  "$128"
 *   "$1,234.56 remaining"   rendered  "$1235"
 *
 * — rounded, no thousands separator, and the symbol force-prefixed even in
 * locales that suffix it. The savings card was the worst instance: its headline
 * used the prefix path while the supporting line beneath it used `formatMoney`,
 * so one card showed two formats for one currency (D-006).
 *
 * The `format` prop is the fix, and these tests pin both halves: money goes
 * through a real formatter, and the plain counter path still works for counts.
 */
import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import AnimatedNumber from 'src/components/AnimatedNumber.vue';

/** A stand-in with the shape of `formatMoney` — 2dp, grouped, symbol first.
 *  Using a local formatter keeps the test independent of the install's locale
 *  policy (which is fetched over HTTP at runtime). */
const money = (n: number) =>
    new Intl.NumberFormat('en-AU', {
        style: 'currency',
        currency: 'AUD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(n);

describe('AnimatedNumber — the `format` prop owns the whole string', () => {
    it('renders a money value with decimals and grouping, not toFixed(0)', () => {
        const w = mount(AnimatedNumber, {
            props: { value: 128.45, format: money },
        });
        expect(w.text()).toBe('$128.45');
        // The specific regression: never the rounded whole-dollar form.
        expect(w.text()).not.toBe('$128');
    });

    it('groups thousands', () => {
        const w = mount(AnimatedNumber, {
            props: { value: 1234.56, format: money },
        });
        expect(w.text()).toBe('$1,234.56');
        expect(w.text()).not.toBe('$1235');
    });

    it('lets the formatter place the symbol (so suffix locales work)', () => {
        const euro = (n: number) =>
            new Intl.NumberFormat('fr-FR', {
                style: 'currency',
                currency: 'EUR',
                minimumFractionDigits: 2,
            }).format(n);
        const w = mount(AnimatedNumber, { props: { value: 12.34, format: euro } });
        // fr-FR suffixes the symbol; the old `prefix` path could only ever
        // render "€12".
        expect(w.text()).toMatch(/12,34/);
        expect(w.text()).not.toMatch(/^€/);
    });

    it('ignores prefix/suffix/decimals when a formatter is supplied', () => {
        const w = mount(AnimatedNumber, {
            props: {
                value: 5,
                format: money,
                prefix: 'IGNORED',
                suffix: 'ALSO-IGNORED',
                decimals: 7,
            },
        });
        expect(w.text()).toBe('$5.00');
    });

    it('renders a zero money value as the formatter does, not as empty', () => {
        const w = mount(AnimatedNumber, { props: { value: 0, format: money } });
        expect(w.text()).toBe('$0.00');
    });
});

describe('AnimatedNumber — the counter path is unchanged', () => {
    it('renders a whole-number count with no decimals by default', () => {
        const w = mount(AnimatedNumber, { props: { value: 7 } });
        expect(w.text()).toBe('7');
    });

    it('still honours prefix/suffix/decimals for non-money callers', () => {
        const w = mount(AnimatedNumber, {
            props: { value: 42.5, decimals: 1, prefix: '~', suffix: ' items' },
        });
        expect(w.text()).toBe('~42.5 items');
    });
});
