import { type APIRequestContext, type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, apiMutate, toast } from './helpers';

// C-1b.4 — the stock-item detail page's Recipes / Lists / Substitutes tab
// actions (origin FU-202; verify-campaign Batch 3 codify-next). These were
// once live defects ("remove from favourites does nothing", "every recipe
// action except Cook is dead") — the wiring deserves a regression pin.
//
// State: an entirely throwaway universe created via the API (two Stocked
// stock items + one recipe using both), so cookability is guaranteed and no
// seed item or other spec is touched. Torn down in afterAll.
test.describe.configure({ mode: 'serial' });

const STAMP = Date.now();
const ITEM_A = `e2e c1b4 flour ${STAMP}`;
const ITEM_B = `e2e c1b4 sugar ${STAMP}`;
const RECIPE = `e2e c1b4 cake ${STAMP}`;

let itemAId: string;
let itemBId: string;
let recipeId: string;

async function draftListId(page: Page): Promise<string> {
    const lists = await apiGet<{ shopping_list_id: string; status: string }[]>(
        page, '/shopping-lists',
    );
    const draft = lists.find((l) => l.status === 'draft');
    expect(draft, 'the seeded draft list exists').toBeTruthy();
    return draft!.shopping_list_id;
}

test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext({ storageState: 'e2e/.auth/user.json' });
    const page = await context.newPage();
    try {
        const levels = await apiGet<{ items: { stock_level_id: string; name: string }[] }>(
            page, '/stock-levels?limit=50',
        );
        const stocked = levels.items.find((l) => l.name === 'Stocked')!;
        const mk = async (name: string) => {
            const res = await apiMutate(page, 'post', '/stock-items', {
                name, stock_level_id: stocked.stock_level_id,
            });
            return ((await res.json()) as { stock_item_id: string }).stock_item_id;
        };
        itemAId = await mk(ITEM_A);
        itemBId = await mk(ITEM_B);
        const rec = await apiMutate(page, 'post', '/recipes', {
            name: RECIPE,
            servings: 2,
            ingredients: [
                { stock_item_id: itemAId, quantity: 1, unit: 'ea' },
                { stock_item_id: itemBId, quantity: 1, unit: 'ea' },
            ],
        });
        recipeId = ((await rec.json()) as { recipe_id: string }).recipe_id;
    } finally {
        await context.close();
    }
});

test.afterAll(async ({ browser }) => {
    const context = await browser.newContext({ storageState: 'e2e/.auth/user.json' });
    const page = await context.newPage();
    try {
        const listId = await draftListId(page);
        for (const id of [itemAId, itemBId]) {
            if (!id) continue;
            // Tolerate a not-found: apiMutate asserts ok, so probe first.
            const detail = await apiGet<{ lines: { stock_item_id: string | null }[] }>(
                page, `/shopping-lists/${listId}`,
            );
            if (detail.lines.some((l) => l.stock_item_id === id)) {
                await apiMutate(page, 'delete', `/shopping-lists/${listId}/lines/by-stock-item/${id}`);
            }
        }
        if (recipeId) await apiMutate(page, 'delete', `/recipes/${recipeId}`);
        if (itemAId) await apiMutate(page, 'delete', `/stock-items/${itemAId}`);
        if (itemBId) await apiMutate(page, 'delete', `/stock-items/${itemBId}`);
    } finally {
        await context.close();
    }
});

async function openTab(page: Page, tab: string): Promise<void> {
    await page.goto(`/#/stock/${itemAId}`);
    await page.waitForLoadState('networkidle');
    await page.getByRole('tab', { name: tab }).click();
}

async function isFavourite(page: Page): Promise<boolean> {
    const data = await apiGet<{ items: { recipe_id: string; is_favourite: boolean }[] }>(
        page, '/recipes?limit=200',
    );
    return data.items.find((r) => r.recipe_id === recipeId)!.is_favourite;
}

test('heart toggles favourite on and off again (server truth both ways)', async ({ page }) => {
    await page.goto('/#/');
    expect(await isFavourite(page)).toBe(false);
    await openTab(page, 'Recipes');
    const card = page.locator('.recipe-card').filter({ hasText: RECIPE }).first();
    await expect(card).toBeVisible();

    await card.locator('.mdi-heart-outline').click();
    await expect.poll(() => isFavourite(page)).toBe(true);
    // The card re-renders from the store: outline → filled heart.
    await expect(card.locator('.mdi-heart')).toBeVisible();

    await card.locator('.mdi-heart').first().click();
    await expect.poll(() => isFavourite(page)).toBe(false);
});

test('cookable card "Add all to list" lands every ingredient on the primary draft; Lists tab shows it', async ({ page }) => {
    await page.goto('/#/');
    const listId = await draftListId(page);
    await openTab(page, 'Recipes');
    const card = page.locator('.recipe-card').filter({ hasText: RECIPE }).first();

    // Both ingredients Stocked → cookable → the cart button is "add all".
    await card.locator('.mdi-cart-plus').click();
    await expect(toast(page, '2 added.')).toBeVisible();

    const onDraft = async () => {
        const detail = await apiGet<{ lines: { stock_item_id: string | null }[] }>(
            page, `/shopping-lists/${listId}`,
        );
        return [itemAId, itemBId].filter(
            (id) => detail.lines.some((l) => l.stock_item_id === id),
        ).length;
    };
    await expect.poll(onDraft).toBe(2);

    // Lists tab reflects the membership (no dead open_in_new control here).
    await page.getByRole('tab', { name: 'Lists' }).click();
    await expect(page.locator('.q-tab-panel').getByText(/This week/).first()).toBeVisible();
    await expect(page.locator('.q-tab-panel .mdi-open-in-new')).toHaveCount(0);

    // Restore: pull both lines again.
    for (const id of [itemAId, itemBId]) {
        await apiMutate(page, 'delete', `/shopping-lists/${listId}/lines/by-stock-item/${id}`);
    }
});

test('substitutes: row renders without "Swap into list"; Remove unlinks (server truth)', async ({ page }) => {
    await page.goto('/#/');
    await apiMutate(page, 'post', `/stock-items/${itemAId}/substitutes`, {
        substitute_id: itemBId,
    });
    await openTab(page, 'Substitutes');

    const row = page.locator('.q-item').filter({ hasText: ITEM_B }).first();
    await expect(row).toBeVisible();
    // The retired per-row action stays gone.
    await expect(page.getByText(/Swap into list/i)).toHaveCount(0);

    await row.locator('.mdi-link-off').click();
    await expect.poll(async () => {
        const detail = await apiGet<{ substitutes: { stock_item_id: string }[] }>(
            page, `/stock-items/${itemAId}/detail`,
        );
        return detail.substitutes.length;
    }).toBe(0);
    await expect(row).toHaveCount(0);
});
