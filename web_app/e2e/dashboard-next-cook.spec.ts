import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, apiMutate } from './helpers';

// FU-298 — the dashboard "Next to cook" card (verify-campaign Dashboard
// batch). Meal-plan-driven: the card renders the first ≤3 recipe-deduped
// entries of /dashboard/summary's upcoming_entries (server-sorted by
// scheduled_for, slot), each badged from the server-derived missing_count /
// unlinked_ingredient_count.
//
// State: a throwaway universe — two stock items (one Stocked, one Out), three
// recipes (ready / missing-one / no-ingredients) planned TODAY in the
// "Breakfast" slot. Breakfast sorts alphabetically before the seed plan's
// Dinner/Lunch entries on the same earliest date, so the engineered entries
// deterministically occupy the card's top 3 (they tie on (today, Breakfast);
// order within the tie is asserted against the DTO, not hardcoded). The
// ready recipe is also planned a second time later in the week to pin the
// dedupe. Torn down in afterAll. The empty-state render needs a plan-free
// install and stays a walk bullet.
test.describe.configure({ mode: 'serial' });

const STAMP = Date.now();
const ITEM_STOCKED = `e2e fu298 stocked ${STAMP}`;
const ITEM_OUT = `e2e fu298 out ${STAMP}`;
const RECIPE_READY = `e2e fu298 ready ${STAMP}`;
const RECIPE_MISSING = `e2e fu298 missing ${STAMP}`;
const RECIPE_EMPTY = `e2e fu298 empty ${STAMP}`;

let stockedItemId: string;
let outItemId: string;
let readyRecipeId: string;
let missingRecipeId: string;
let emptyRecipeId: string;
let planId: string;

interface UpcomingEntry {
    recipe_id: string;
    recipe_name: string;
    scheduled_for: string;
    slot: string;
    servings: number;
    missing_count: number | null;
    unlinked_ingredient_count: number;
}
interface SummaryDto {
    meal_plan: { upcoming_entries: UpcomingEntry[] };
}

function cardTop3(summary: SummaryDto): UpcomingEntry[] {
    const seen = new Set<string>();
    const picks: UpcomingEntry[] = [];
    for (const e of summary.meal_plan.upcoming_entries) {
        if (seen.has(e.recipe_id)) continue;
        seen.add(e.recipe_id);
        picks.push(e);
        if (picks.length >= 3) break;
    }
    return picks;
}

function badgeLabel(e: UpcomingEntry): string {
    if (e.unlinked_ingredient_count > 0) return `${e.unlinked_ingredient_count} to link`;
    if (e.missing_count === null) return 'No ingredients';
    if (e.missing_count === 0) return 'Ready';
    return `Missing ${e.missing_count}`;
}

test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext({ storageState: 'e2e/.auth/user.json' });
    const page = await context.newPage();
    try {
        const levels = await apiGet<{ items: { stock_level_id: string; name: string; sequence: number }[] }>(
            page, '/stock-levels?limit=50',
        );
        const stocked = levels.items.find((l) => l.sequence === 0)!;
        const out = levels.items.find((l) => l.sequence === 2)!;
        const mkItem = async (name: string, levelId: string) => {
            const res = await apiMutate(page, 'post', '/stock-items', {
                name, stock_level_id: levelId,
            });
            return ((await res.json()) as { stock_item_id: string }).stock_item_id;
        };
        stockedItemId = await mkItem(ITEM_STOCKED, stocked.stock_level_id);
        outItemId = await mkItem(ITEM_OUT, out.stock_level_id);

        const mkRecipe = async (name: string, ingredients: object[]) => {
            const res = await apiMutate(page, 'post', '/recipes', {
                name, servings: 2, ingredients,
            });
            return ((await res.json()) as { recipe_id: string }).recipe_id;
        };
        readyRecipeId = await mkRecipe(RECIPE_READY, [
            { stock_item_id: stockedItemId, quantity: 1, unit: 'ea' },
        ]);
        missingRecipeId = await mkRecipe(RECIPE_MISSING, [
            { stock_item_id: stockedItemId, quantity: 1, unit: 'ea' },
            { stock_item_id: outItemId, quantity: 1, unit: 'ea' },
        ]);
        emptyRecipeId = await mkRecipe(RECIPE_EMPTY, []);

        const { today } = await apiGet<{ today: string }>(page, '/meal-plans/today');
        const plan = await apiMutate(page, 'post', '/meal-plans', {
            name: `e2e fu298 plan ${STAMP}`,
            start_date: today,
            entries: [
                { recipe_id: readyRecipeId, scheduled_for: today, slot: 'Breakfast', servings: 2 },
                { recipe_id: missingRecipeId, scheduled_for: today, slot: 'Breakfast', servings: 3 },
                { recipe_id: emptyRecipeId, scheduled_for: today, slot: 'Breakfast', servings: 1 },
                // The dedupe probe: same recipe again later in the window.
                { recipe_id: readyRecipeId, scheduled_for: today, slot: 'Dinner', servings: 2 },
            ],
        });
        planId = ((await plan.json()) as { new_meal_plan_id: string }).new_meal_plan_id;
    } finally {
        await context.close();
    }
});

test.afterAll(async ({ browser }) => {
    const context = await browser.newContext({ storageState: 'e2e/.auth/user.json' });
    const page = await context.newPage();
    try {
        if (planId) await apiMutate(page, 'delete', `/meal-plans/${planId}`);
        for (const id of [readyRecipeId, missingRecipeId, emptyRecipeId]) {
            if (id) await apiMutate(page, 'delete', `/recipes/${id}`);
        }
        for (const id of [stockedItemId, outItemId]) {
            if (id) await apiMutate(page, 'delete', `/stock-items/${id}`);
        }
    } finally {
        await context.close();
    }
});

async function gotoDashboard(page: Page) {
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Next to cook' })).toBeVisible();
}

test('rows mirror the server DTO: dedupe, order, when-meta, and ready/missing/no-ingredients badges', async ({ page }) => {
    await gotoDashboard(page);

    const summary = await apiGet<SummaryDto>(page, '/dashboard/summary');
    const expected = cardTop3(summary);
    // The engineered (today, Breakfast) trio outsorts the seed's
    // Dinner/Lunch entries, so it owns the card.
    expect(expected.map((e) => e.recipe_name).sort()).toEqual(
        [RECIPE_READY, RECIPE_MISSING, RECIPE_EMPTY].sort(),
    );

    const rows = page.locator('.dora-cook-row');
    await expect(rows).toHaveCount(3);
    for (let i = 0; i < expected.length; i++) {
        const e = expected[i]!;
        const row = rows.nth(i);
        await expect(row.locator('.dora-cook-name')).toHaveText(e.recipe_name);
        await expect(row.locator('.dora-cook-meta')).toContainText(
            `Today ${e.slot.toLowerCase()}`,
        );
        await expect(row.locator('.dora-cook-meta')).toContainText(`serves ${e.servings}`);
        await expect(row.locator('.dora-cook-badge')).toHaveText(badgeLabel(e));
    }

    // The engineered truths behind the three badge flavours, pinned
    // explicitly so a DTO regression can't silently weaken the loop above.
    const byName = new Map(expected.map((e) => [e.recipe_name, e]));
    expect(byName.get(RECIPE_READY)!.missing_count).toBe(0);
    expect(byName.get(RECIPE_MISSING)!.missing_count).toBe(1);
    expect(byName.get(RECIPE_EMPTY)!.missing_count).toBeNull();

    // Dedupe: the ready recipe is planned twice today (Breakfast + Dinner)
    // but renders once.
    await expect(page.locator('.dora-cook-name').filter({ hasText: RECIPE_READY })).toHaveCount(1);
});

test('recipe name deep-links to the recipe; Cook goes straight to cook mode', async ({ page }) => {
    await gotoDashboard(page);

    await page.locator('.dora-cook-name').filter({ hasText: RECIPE_MISSING }).click();
    await page.waitForURL(new RegExp(`cookbook/${missingRecipeId}$`));
    await expect(page.getByText('This page wandered off')).toHaveCount(0);

    // Fresh full load for the Cook half — a warm goBack → immediate
    // router.push wedges the hash router (the FU-584 race, reproduced here
    // too), and that flake is FU-584's to fix, not this card's.
    await page.reload();
    await page.waitForLoadState('networkidle');
    await gotoDashboard(page);

    const readyRow = page.locator('.dora-cook-row').filter({ hasText: RECIPE_READY });
    await readyRow.getByRole('button', { name: 'Cook' }).click();
    await page.waitForURL(new RegExp(`cookbook/${readyRecipeId}/cook`));
    await expect(page.getByText('This page wandered off')).toHaveCount(0);
});
