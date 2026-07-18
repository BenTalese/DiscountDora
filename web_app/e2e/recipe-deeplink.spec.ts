import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet } from './helpers';

// Recipe-ingredients deep-link filter (FU-109, verify-campaign Batch 3).
// The narrowing/orphan/compose semantics are Vitest-pinned in
// useStockFilters.spec.ts — these tests pin the URL/chip wiring the unit
// layer can't see: the RecipeCard filter action landing on
// /stock?recipe=<id> with the chip + auto-opened panel, chip-× and
// "Clear filters" both stripping the param, a bogus id degrading
// silently, the filter button existing ONLY on the stock-item-detail
// Recipes tab, and the FU-109 no-dim rule on that surface.
//
// Read-only: nothing mutates server state, no restore needed.

const RECIPE = 'Spaghetti Aglio e Olio';
const INGREDIENTS = ['Barilla Pasta', 'Garlic', 'Olive Oil'];

async function itemIdByName(page: Page, name: string): Promise<string> {
    const data = await apiGet<{ items: { stock_item_id: string; name: string }[] }>(
        page, '/stock-items?limit=500',
    );
    const item = data.items.find((i) => i.name === name);
    expect(item, `seed item "${name}" exists`).toBeTruthy();
    return item!.stock_item_id;
}

async function recipeIdByName(page: Page, name: string): Promise<string> {
    const data = await apiGet<{ items: { recipe_id: string; name: string }[] }>(
        page, '/recipes?limit=200',
    );
    const recipe = data.items.find((r) => r.name === name);
    expect(recipe, `seed recipe "${name}" exists`).toBeTruthy();
    return recipe!.recipe_id;
}

test('card filter action lands on /stock?recipe= with the chip, narrowed list, and chip-x teardown', async ({ page }) => {
    await page.goto('/#/');
    const garlicId = await itemIdByName(page, 'Garlic');
    await page.goto(`/#/stock/${garlicId}`);
    await page.waitForLoadState('networkidle');
    await page.getByRole('tab', { name: 'Recipes' }).click();

    // The aglio card carries the filter icon; click it.
    const card = page.locator('.recipe-card').filter({ hasText: RECIPE }).first();
    await expect(card).toBeVisible();
    await card.locator('.mdi-filter-variant').click();

    // Landed on Stock Overview with the deep-link param + visible chip.
    await expect(page).toHaveURL(/\/stock\?.*recipe=/);
    await expect(page.getByText(`Ingredients of: ${RECIPE}`)).toBeVisible();

    // The list narrows to exactly the recipe's ingredient items.
    await expect(page.locator('.stock-row')).toHaveCount(INGREDIENTS.length);
    for (const name of INGREDIENTS) {
        await expect(page.locator('.stock-row').filter({ hasText: name })).toBeVisible();
    }

    // Chip × → chip gone, param stripped, full list back.
    await page.locator('.q-chip').filter({ hasText: 'Ingredients of:' })
        .locator('.q-chip__icon--remove').click();
    await expect(page.getByText(`Ingredients of: ${RECIPE}`)).toHaveCount(0);
    await expect(page).not.toHaveURL(/recipe=/);
    expect(await page.locator('.stock-row').count()).toBeGreaterThan(INGREDIENTS.length);
});

test('"Clear filters" also strips ?recipe= so refresh/back cannot reinstate it', async ({ page }) => {
    await page.goto('/#/');
    const recipeId = await recipeIdByName(page, RECIPE);
    await page.goto(`/#/stock?recipe=${recipeId}`);
    await page.waitForLoadState('networkidle');

    // Deep-link entry: panel auto-opens with the chip, list narrowed.
    await expect(page.getByText(`Ingredients of: ${RECIPE}`)).toBeVisible();
    await expect(page.locator('.stock-row')).toHaveCount(INGREDIENTS.length);

    // The FilterToggleButton's "Clear" (wired to the page's clearAllFilters
    // wrapper, which strips the URL param alongside the in-memory state).
    await page.getByRole('button', { name: 'Clear', exact: true }).click();
    await expect(page.getByText(`Ingredients of: ${RECIPE}`)).toHaveCount(0);
    await expect(page).not.toHaveURL(/recipe=/);

    // A reload after clearing must not resurrect the filter.
    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(page.getByText(`Ingredients of: ${RECIPE}`)).toHaveCount(0);
    expect(await page.locator('.stock-row').count()).toBeGreaterThan(INGREDIENTS.length);
});

test('a bogus ?recipe= id silently disables the filter instead of blanking the list', async ({ page }) => {
    await page.goto(`/#/stock?recipe=00000000-0000-0000-0000-000000000000`);
    await page.waitForLoadState('networkidle');

    expect(await page.locator('.stock-row').count()).toBeGreaterThan(0);
    await expect(page.getByText(/Ingredients of:/)).toHaveCount(0);
});

test('filter button lives only on the detail Recipes tab; cards never dim there (FU-109)', async ({ page }) => {
    // Cookbook overview: cards render, none carries the filter icon.
    await page.goto('/#/cookbook');
    await page.waitForLoadState('networkidle');
    expect(await page.locator('.recipe-card').count()).toBeGreaterThan(0);
    await expect(page.locator('.recipe-card .mdi-filter-variant')).toHaveCount(0);

    // Detail Recipes tab: the icon is present (control for the absence
    // check above) and no card renders at reduced opacity — the
    // "Missing N ingredients" copy is the only incomplete-set signal.
    const garlicId = await itemIdByName(page, 'Garlic');
    await page.goto(`/#/stock/${garlicId}`);
    await page.waitForLoadState('networkidle');
    await page.getByRole('tab', { name: 'Recipes' }).click();
    const cards = page.locator('.recipe-card');
    expect(await cards.count()).toBeGreaterThan(0);
    expect(await page.locator('.recipe-card .mdi-filter-variant').count()).toBeGreaterThan(0);

    const opacities = await cards.evaluateAll(
        (els) => els.map((el) => window.getComputedStyle(el).opacity),
    );
    for (const o of opacities) expect(Number(o)).toBe(1);
});
