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
 *
 * **2026-09-04 — zones removed, six cards cut, two added.** The zone
 * invariants went with the zones; the retired-id list grew by six, which is the
 * part that still matters, because those ids are sitting in every existing
 * user's stored `dashboard_layout`.
 */
import { describe, expect, it } from 'vitest';
import {
    CARD_DEFS,
    DEFAULT_VISIBLE_COUNT,
    type CardId,
} from 'src/helpers/dashboardCards';

const defaultVisible = () => CARD_DEFS.filter((c) => !c.defaultHidden);

describe('the default-visible count is a decision, not a default', () => {
    it('matches DEFAULT_VISIBLE_COUNT — change both together, on purpose', () => {
        expect(
            defaultVisible().length,
            'A card was added or un-hidden. IMPL_PLAN_DASHBOARD_REBUILD §2.2 owns ' +
                'this number. Either mark the new card `defaultHidden: true`, or get ' +
                'the count re-agreed and update DEFAULT_VISIBLE_COUNT deliberately.',
        ).toBe(DEFAULT_VISIBLE_COUNT);
    });

    it('is 9, and 9 is also what actually renders', () => {
        expect(DEFAULT_VISIBLE_COUNT).toBe(9);
        // Before the 09-04 cull the registered count and the rendered count
        // differed (`reconcile_pending` hid itself when its queue was empty),
        // and the docs had to keep explaining "11, or 10 in practice". That card
        // is gone and no survivor hides on its own data, so the two numbers are
        // one number again. `cardRendered` in the page is where a future
        // hide-when-empty card would reintroduce the distinction.
        expect(defaultVisible()).toHaveLength(9);
    });

    it('keeps every card the owner left default-on', () => {
        const expected: CardId[] = [
            'next_to_cook',
            'use_it_up',
            'before_you_shop',
            'shopping_lists',
            'meal_plan',
            'restock',
            'dora_score',
            'stock_items',
            'savings',
        ];
        expect(defaultVisible().map((c) => c.id).sort()).toEqual([...expected].sort());
    });

    it('has exactly the opt-in set the review left opt-in', () => {
        // Down to one: `spend_trend` and `pantry_value` were cut outright on
        // 2026-09-04 as reports that had wandered onto the dashboard.
        expect(CARD_DEFS.filter((c) => c.defaultHidden).map((c) => c.id).sort()).toEqual(
            ['price_drops'],
        );
    });
});

describe('retired cards stay retired', () => {
    // A stored `dashboard_layout` still names these. The page's `parseLayout`
    // filters to known ids, so they drop out — but only as long as they are
    // genuinely absent from the registry. Resurrecting one of these ids for a
    // *different* card would silently inherit some users' hidden flag.
    const retired = [
        // FU-818 / FU-819 / FU-830
        'calendar', 'budget', 'best_deals',
        // The 2026-09-04 owner cull
        'attention', 'draft_shop', 'suggestions', 'spend_trend', 'pantry_value',
        'reconcile_pending',
        // Renamed in the same batch — the old ids must not linger either, or a
        // stored layout would carry both the old and the new entry.
        'cookable', 'primary_list',
    ];
    for (const gone of retired) {
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

    it('gates every card that states dollars', () => {
        // FU-297: even a "no target set" body shows dollar amounts, so an
        // ungated money card would leak dollars onto a money-off install
        // (ADR-005, feedback L254). This used to be expressible as "every card
        // in the Money zone"; with the zones gone the money cards have to be
        // named, which is the honest version of the same assertion — a new
        // dollar card has to be added here deliberately.
        //
        // `price_drops` is products-gated instead: it is a product surface
        // first, and the owner asked specifically that it be gated on the
        // products feature (2026-09-04).
        const statesDollars: CardId[] = ['savings'];
        for (const id of statesDollars) {
            const card = CARD_DEFS.find((c) => c.id === id);
            expect(card, `${id} is missing from the registry`).toBeDefined();
            expect(card!.gate, `${id} states dollars`).toBe('money');
        }
        expect(CARD_DEFS.find((c) => c.id === 'price_drops')!.gate).toBe('products');
    });

    it('declares no zone — the grouping was removed on 2026-09-04', () => {
        // Owner: *"with how many widgets we're axing, I don't think we need the
        // groupings. Allow the user to reorder the cards however they want."*
        // A `zone` key creeping back in would mean the flat-order model has
        // quietly grown a second, conflicting one.
        for (const card of CARD_DEFS) {
            expect(card, card.id).not.toHaveProperty('zone');
        }
    });
});
