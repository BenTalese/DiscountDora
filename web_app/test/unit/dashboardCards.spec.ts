/**
 * FU-830 / §2.2 — the dashboard's default-visible card count is a **resolved
 * decision**, and this is the mechanism that holds it.
 *
 * `IMPL_PLAN_DASHBOARD_REBUILD.md` §2.2 fixed that count with the owner on
 * 2026-06-23 so the dashboard "looks focused out of the box" (Anti-creep). By
 * September it had drifted to 13 of 17 — not because anyone made a bad call, but
 * because three later features each shipped without `defaultHidden` and **nothing
 * was holding the number**: no test, no comment, no trigger to reopen §2.2. That
 * is the whole finding of `DASHBOARD_PAGE_REVIEW.md` §3.1, and it is a process
 * gap, not a code bug.
 *
 * So this file is deliberately blunt. If you add a card without
 * `defaultHidden: true`, the first test fails and you have to either mark it
 * opt-in or change `DEFAULT_VISIBLE_COUNT` on purpose — which is exactly the
 * conversation §2.2 wanted and never got.
 *
 * The rest pins the registry's structural invariants, all of which have been
 * broken at least once: a CardId missing from the union hard-failed
 * `quasar build` (FU-550), and the ids of retired cards have to stay retired or
 * a stored layout resurrects them.
 */
import { describe, expect, it } from 'vitest';
import {
    CARD_DEFS,
    DEFAULT_VISIBLE_COUNT,
    ZONES,
    type CardId,
} from 'src/helpers/dashboardCards';

const defaultVisible = () => CARD_DEFS.filter((c) => !c.defaultHidden);

describe('the default-visible count is a decision, not a default', () => {
    it('matches DEFAULT_VISIBLE_COUNT — change both together, on purpose', () => {
        expect(
            defaultVisible().length,
            'A card was added or un-hidden. IMPL_PLAN_DASHBOARD_REBUILD §2.2 owns ' +
                'this number (amended by the owner 2026-09-02 to "merges only, no ' +
                'demotions"). Either mark the new card `defaultHidden: true`, or get ' +
                'the count re-agreed and update DEFAULT_VISIBLE_COUNT deliberately.',
        ).toBe(DEFAULT_VISIBLE_COUNT);
    });

    it('is 11 registered — 10 in practice, since reconcile_pending hides itself', () => {
        expect(DEFAULT_VISIBLE_COUNT).toBe(11);
        // `reconcile_pending` renders nothing when the queue is empty (R-029),
        // so a quiet install sees ten. Asserted so the "10 vs 11" distinction in
        // the docs stays true to the registry.
        const selfHiding = CARD_DEFS.filter((c) => c.id === 'reconcile_pending');
        expect(selfHiding).toHaveLength(1);
        expect(selfHiding[0]!.defaultHidden).toBeUndefined();
    });

    it('keeps every card that was default-on after the FU-830 merges', () => {
        // The owner chose "merges only, no demotions", so these must all still be
        // default-visible. A future tidy-up that quietly demotes one is a
        // decision, not a cleanup.
        const expected: CardId[] = [
            'attention',
            'draft_shop',
            'suggestions',
            'cookable',
            'meal_plan',
            'primary_list',
            'restock',
            'savings',
            'dora_score',
            'reconcile_pending',
            'stock_items',
        ];
        expect(defaultVisible().map((c) => c.id).sort()).toEqual([...expected].sort());
    });

    it('has exactly the opt-in set the review left opt-in', () => {
        expect(CARD_DEFS.filter((c) => c.defaultHidden).map((c) => c.id).sort()).toEqual(
            ['pantry_value', 'price_drops', 'spend_trend'].sort(),
        );
    });
});

describe('cards retired by FU-818 / FU-819 / FU-830 stay retired', () => {
    // A stored `dashboard_layout` from before the merges still names these. The
    // page's `parseLayout` filters to known ids, so they drop out — but only as
    // long as they are genuinely absent from the registry.
    for (const gone of ['calendar', 'budget', 'best_deals']) {
        it(`${gone} is not in the registry`, () => {
            expect(CARD_DEFS.map((c) => String(c.id))).not.toContain(gone);
        });
    }
});

describe('registry invariants', () => {
    it('has unique ids', () => {
        const ids = CARD_DEFS.map((c) => c.id);
        expect(new Set(ids).size).toBe(ids.length);
    });

    it('places every card in a declared zone', () => {
        const zoneIds = new Set(ZONES.map((z) => z.id));
        for (const card of CARD_DEFS) {
            expect(zoneIds.has(card.zone), `${card.id} → ${card.zone}`).toBe(true);
        }
    });

    it('gives every card a non-empty label and icon', () => {
        // The label is what the Cards menu shows; an empty one is an invisible
        // toggle.
        for (const card of CARD_DEFS) {
            expect(card.label.trim(), card.id).not.toBe('');
            expect(card.icon.trim(), card.id).not.toBe('');
        }
    });

    it('uses only the two known gates', () => {
        for (const card of CARD_DEFS) {
            if (card.gate !== undefined) {
                expect(['money', 'products'], card.id).toContain(card.gate);
            }
        }
    });

    it('money-gates every card in the Money zone that states dollars', () => {
        // FU-297: even a "no target set" body shows dollar amounts, so a Money
        // zone card without a gate would leak dollars onto a money-off install
        // (ADR-005, feedback L254). `price_drops` is products-gated instead —
        // it is a product surface first.
        for (const card of CARD_DEFS.filter((c) => c.zone === 'money')) {
            expect(card.gate, `${card.id} sits in the Money zone`).toBeDefined();
        }
    });

    it('keeps at least one card in every zone, so no band is dead weight', () => {
        for (const zone of ZONES) {
            expect(
                CARD_DEFS.some((c) => c.zone === zone.id),
                `zone "${zone.id}" has no cards`,
            ).toBe(true);
        }
    });
});
