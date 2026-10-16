// The meal card's status vocabulary (owner assessment, 2026-09-12).
//
// Worth pinning under the lean verification stance: it is a pure function with
// no pinia and no network, it decides what BOTH meal cards draw (so a drift
// between the desktop chip and the phone card would be invisible until someone
// opened both breakpoints), and the cases that matter — a batch household's
// leftovers day, a cook-fresh meal, a fresh household — each need a seeded
// week to reproduce by hand.
//
// The headline contract is the one the assessment was about: **one axis per
// channel**. Amber means exactly one thing, and an axis that doesn't apply to a
// meal renders nothing rather than a greyed-out claim.
import { describe, expect, it } from 'vitest';

import {
    mealCardStatus, readinessTooltip, supplyTooltip,
} from 'src/helpers/mealPlanEntryStatus';
import type { MealPlanEntry } from 'src/models/mealPlan';

function entry(over: Partial<MealPlanEntry>): MealPlanEntry {
    return {
        meal_plan_entry_id: 'id-1',
        recipe_id: 'recipe-1',
        recipe_name: 'Ragu',
        scheduled_for: '2026-09-14',
        servings: 2,
        slot: 'Dinner',
        consumed_at: null,
        cook_time_minutes: null,
        category_name: null,
        cuisine_name: null,
        has_image: false,
        cook_batch_id: null,
        is_cook_day: false,
        cook_batch_total_servings: null,
        cook_batch_size: null,
        kcal_per_serving: null,
        kcal_is_reliable: false,
        inference_hint: null,
        inference_stock_item_names: [],
        needs_cooking: false,
        cook_batch_pending: false,
        cook_fresh: false,
        estimated_cost: null,
        missing_count: 0,
        cook_batch_estimated_cost: null,
        ...over,
    };
}

const FRESH_HOUSEHOLD = false;
const BATCH_HOUSEHOLD = true;

describe('mealCardStatus — supply (can I make it?)', () => {
    it('is green when nothing is missing and amber when something is', () => {
        expect(mealCardStatus(entry({}), FRESH_HOUSEHOLD, false).supply).toBe('ok');
        expect(
            mealCardStatus(entry({ missing_count: 3 }), FRESH_HOUSEHOLD, false).supply,
        ).toBe('alert');
    });

    it('asks nothing of a leftovers day — that food is already cooked', () => {
        const leftovers = entry({
            cook_batch_id: 'batch-1', is_cook_day: false, missing_count: 3,
        });
        expect(mealCardStatus(leftovers, BATCH_HOUSEHOLD, false).supply).toBeNull();
    });

    it('asks nothing of a meal served from portions already cooked', () => {
        // Batch household, no batch link, not cook-fresh, and the allocation
        // covers it: it eats from the cooked portions, so its ingredients
        // aren't the question.
        expect(mealCardStatus(entry({ missing_count: 3 }), BATCH_HOUSEHOLD, false).supply)
            .toBeNull();
    });

    it('DOES ask it of a standalone meal the ready servings cannot cover', () => {
        // Owner 2026-09-12: *"is the cookability showing correctly? I only see
        // it on multi-linked days."* Under-showing — when `needs_cooking` says
        // there is no ready serving for this meal, somebody is cooking it from
        // ingredients, so whether you have them is exactly the question.
        expect(mealCardStatus(entry({ missing_count: 3 }), BATCH_HOUSEHOLD, true).supply)
            .toBe('alert');
        expect(mealCardStatus(entry({}), BATCH_HOUSEHOLD, true).supply).toBe('ok');
    });

    it('asks it of a cook day and of a cook-fresh meal', () => {
        const cookDay = entry({ cook_batch_id: 'batch-1', is_cook_day: true });
        const cookFresh = entry({ cook_fresh: true });
        expect(mealCardStatus(cookDay, BATCH_HOUSEHOLD, false).supply).toBe('ok');
        expect(mealCardStatus(cookFresh, BATCH_HOUSEHOLD, false).supply).toBe('ok');
    });
});

describe('mealCardStatus — readiness (is it already made?)', () => {
    it('does not exist in a fresh household, where there are no cooked portions', () => {
        expect(mealCardStatus(entry({}), FRESH_HOUSEHOLD, true).readiness).toBeNull();
    });

    it('is amber when this meal still has to be cooked, green when it does not', () => {
        expect(mealCardStatus(entry({}), BATCH_HOUSEHOLD, true).readiness).toBe('alert');
        expect(mealCardStatus(entry({}), BATCH_HOUSEHOLD, false).readiness).toBe('ok');
    });

    it('does not apply to a cook-fresh meal, which stands outside the portions', () => {
        expect(mealCardStatus(entry({ cook_fresh: true }), BATCH_HOUSEHOLD, true).readiness)
            .toBeNull();
    });
});

describe('mealCardStatus — the trim rolls the glyphs up', () => {
    it('is amber when either axis is amber, so it can never contradict them', () => {
        expect(mealCardStatus(entry({ missing_count: 1 }), FRESH_HOUSEHOLD, false).trim)
            .toBe('alert');
        expect(mealCardStatus(entry({}), BATCH_HOUSEHOLD, true).trim).toBe('alert');
    });

    it('is grey on a leftovers day — nothing is required of you', () => {
        const leftovers = entry({ cook_batch_id: 'batch-1', is_cook_day: false });
        expect(mealCardStatus(leftovers, BATCH_HOUSEHOLD, false).trim).toBe('idle');
    });

    it('is grey on a cooked meal, and says nothing else at all', () => {
        const done = mealCardStatus(entry({ consumed_at: '2026-09-13' }), BATCH_HOUSEHOLD, true);
        expect(done).toEqual({ supply: null, readiness: null, trim: 'idle' });
    });

    it('is green when the meal is fine and there is still something to do', () => {
        expect(mealCardStatus(entry({}), FRESH_HOUSEHOLD, false).trim).toBe('ok');
    });
});

describe('tooltips', () => {
    it('counts the missing ingredients, singular and plural', () => {
        expect(supplyTooltip(entry({ missing_count: 1 }))).toBe('Missing 1 ingredient');
        expect(supplyTooltip(entry({ missing_count: 3 }))).toBe('Missing 3 ingredients');
        expect(supplyTooltip(entry({}))).toBe('Cookable now');
    });

    it('never says "pool" — it is an internal word for the cooked portions', () => {
        const short = readinessTooltip(entry({ servings: 2 }), true);
        expect(short).toBe('Needs cooking: 2 servings');
        expect(readinessTooltip(entry({}), false)).not.toMatch(/pool/i);
        expect(short).not.toMatch(/pool/i);
    });

    // Owner 2026-10-15, the affogato report: a 2+2 batch with nothing cooked
    // said "short by 2" on its cook day and "a cooked serving is ready" on its
    // leftovers day.
    it('counts the whole batch on its cook day', () => {
        const cookDay = entry({
            servings: 2, cook_batch_id: 'b1', is_cook_day: true, cook_batch_total_servings: 4,
        });
        expect(readinessTooltip(cookDay, true)).toBe('Needs cooking: 4 servings for the batch');
    });

    it('does not call an uncooked batch\'s leftovers ready', () => {
        const leftovers = entry({
            servings: 2, cook_batch_id: 'b1', is_cook_day: false,
            cook_batch_total_servings: 4, cook_batch_pending: true,
        });
        expect(readinessTooltip(leftovers, false)).not.toMatch(/ready/i);
        const status = mealCardStatus(leftovers, BATCH_HOUSEHOLD, false);
        expect(status.readiness).toBe('pending');
        expect(status.trim).toBe('idle');
    });
});
