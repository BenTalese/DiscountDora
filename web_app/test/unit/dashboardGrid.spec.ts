/**
 * FU-631 #3 / D-011 — no dashboard card sits beside dead air.
 *
 * `DASHBOARD_PAGE_REVIEW.md` §4.6 measured **five** dead regions on a default
 * desktop dashboard, which is what makes this worth pinning: it is arithmetic,
 * so it is exactly reproducible, and it regressed silently for months because
 * nobody counted. The cases below are the real zone compositions from
 * `CARD_DEFS`, so a future card added to a zone flips a parity here rather than
 * quietly stranding itself in the browser.
 */
import { describe, expect, it } from 'vitest';
import {
    CARD_COL_FULL,
    CARD_COL_HALF,
    zoneColClasses,
} from 'src/helpers/dashboardGrid';

/** How many cards sit on each row, given the classes. Mirrors how the flex
 *  grid packs: a full-width card owns its row, halves pair up. */
function rows(order: readonly string[], classes: Record<string, string>): string[][] {
    const out: string[][] = [];
    let current: string[] = [];
    for (const id of order) {
        if (classes[id] === CARD_COL_FULL) {
            if (current.length) out.push(current);
            out.push([id]);
            current = [];
        } else {
            current.push(id);
            if (current.length === 2) {
                out.push(current);
                current = [];
            }
        }
    }
    if (current.length) out.push(current);
    return out;
}

/** A row leaves dead air when it holds exactly one half-width card. */
function deadRegions(order: readonly string[], classes: Record<string, string>): string[][] {
    return rows(order, classes).filter(
        (r) => r.length === 1 && classes[r[0]!] === CARD_COL_HALF,
    );
}

describe('zoneColClasses — parity', () => {
    it('leaves an even run alone', () => {
        const order = ['a', 'b', 'c', 'd'];
        const classes = zoneColClasses(order);
        expect(Object.values(classes).every((c) => c === CARD_COL_HALF)).toBe(true);
        expect(deadRegions(order, classes)).toEqual([]);
    });

    it('widens the last card of an odd run', () => {
        const order = ['a', 'b', 'c'];
        const classes = zoneColClasses(order);
        expect(classes.a).toBe(CARD_COL_HALF);
        expect(classes.b).toBe(CARD_COL_HALF);
        expect(classes.c).toBe(CARD_COL_FULL);
        expect(deadRegions(order, classes)).toEqual([]);
    });

    it('makes a lone card full-width', () => {
        // B4 verbatim: "a single card in a 2-col row goes full-width".
        const classes = zoneColClasses(['only']);
        expect(classes.only).toBe(CARD_COL_FULL);
    });

    it('handles an empty zone', () => {
        expect(zoneColClasses([])).toEqual({});
    });
});

describe('zoneColClasses — runs split by a full-width card', () => {
    it('keeps an always-full card full and pairs the halves around it', () => {
        const order = ['a', 'b', 'wide', 'c', 'd'];
        const classes = zoneColClasses(order, new Set(['wide']));
        expect(classes.wide).toBe(CARD_COL_FULL);
        expect(classes.a).toBe(CARD_COL_HALF);
        expect(classes.d).toBe(CARD_COL_HALF);
        expect(deadRegions(order, classes)).toEqual([]);
    });

    it('fixes an ODD run that ends at a full-width card — the case a per-zone count gets wrong', () => {
        // Naive "is the zone odd?" says 3 cards + 1 wide = even, nothing to do,
        // and `a` is left stranded beside dead air. Per-run parity widens it.
        const order = ['a', 'wide', 'b', 'c'];
        const classes = zoneColClasses(order, new Set(['wide']));
        expect(classes.a).toBe(CARD_COL_FULL);
        expect(deadRegions(order, classes)).toEqual([]);
    });

    it('fixes both runs when both are odd', () => {
        const order = ['a', 'b', 'c', 'wide', 'd', 'e', 'f'];
        const classes = zoneColClasses(order, new Set(['wide']));
        expect(classes.c).toBe(CARD_COL_FULL);
        expect(classes.f).toBe(CARD_COL_FULL);
        expect(deadRegions(order, classes)).toEqual([]);
    });

    it('handles consecutive full-width cards', () => {
        const order = ['w1', 'w2', 'a'];
        const classes = zoneColClasses(order, new Set(['w1', 'w2']));
        expect(classes.w1).toBe(CARD_COL_FULL);
        expect(classes.w2).toBe(CARD_COL_FULL);
        expect(classes.a).toBe(CARD_COL_FULL); // lone trailing half
        expect(deadRegions(order, classes)).toEqual([]);
    });
});

describe('the five real dead regions from the review are gone', () => {
    // These are the actual default-visible compositions per zone, in CARD_DEFS
    // order. Before this helper they produced the five gaps §4.6 counted.
    const ZONES: Record<string, string[]> = {
        'act now': ['attention', 'draft_shop', 'suggestions'],
        today: ['cookable', 'meal_plan', 'primary_list', 'restock'],
        money: ['savings', 'budget', 'best_deals'],
        'your kitchen': ['dora_score', 'stock_items'],
    };

    for (const [zone, order] of Object.entries(ZONES)) {
        it(`${zone} packs with no dead air`, () => {
            expect(deadRegions(order, zoneColClasses(order))).toEqual([]);
        });
    }

    it('your kitchen still packs when the reconcile chip appears', () => {
        // `reconcile_pending` is hide-when-empty, so this zone alternates
        // between 2 and 3 cards as the queue fills and drains. Both must pack —
        // that alternation is why a hand-tuned width class could never work.
        const withChip = ['dora_score', 'reconcile_pending', 'stock_items'];
        expect(deadRegions(withChip, zoneColClasses(withChip))).toEqual([]);
    });

    it('money packs after the Chunk 3 merges leave it a single card', () => {
        // FU-830 folds budget into savings and cuts best_deals, so the default
        // Money zone becomes one card — which must go full-width, not sit in a
        // half beside nothing.
        const merged = ['savings'];
        const classes = zoneColClasses(merged);
        expect(classes.savings).toBe(CARD_COL_FULL);
        expect(deadRegions(merged, classes)).toEqual([]);
    });

    it('today packs with the fortnight calendar enabled', () => {
        const order = ['cookable', 'meal_plan', 'primary_list', 'restock', 'calendar'];
        const classes = zoneColClasses(order, new Set(['calendar']));
        expect(classes.calendar).toBe(CARD_COL_FULL);
        expect(deadRegions(order, classes)).toEqual([]);
    });

    it('no zone composition of 1..8 cards can produce dead air', () => {
        // Exhaustive over plausible zone sizes — the point of the helper is that
        // the user's own reordering and gating can't reintroduce a gap.
        for (let n = 1; n <= 8; n++) {
            const order = Array.from({ length: n }, (_, i) => `c${i}`);
            expect(
                deadRegions(order, zoneColClasses(order)),
                `zone of ${n} cards`,
            ).toEqual([]);
        }
    });
});
