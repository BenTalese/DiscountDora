import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, apiMutate } from './helpers';

// C-1b.3 — the stock-item detail Products tab (origin FU-202; verify-campaign
// Batch 3 codify-next). The install-wide `products` flag is a data-presence
// gate (Product rows exist) and the e2e seed ships products, so the ON path
// is what's drivable here: the linked-products render with the single
// cheapest-highlight, the quiet "Link another" header action, the empty-state
// CTA routing to product-search seeded with the item name, and the absence of
// the retired "Get cheapest" toolbar button. (The OFF half — tab hidden +
// `?section=products` falling back to Overview — needs a productless install
// and stays an ops-pack walk.)

async function itemIdByName(page: Page, name: string): Promise<string> {
    const data = await apiGet<{ items: { stock_item_id: string; name: string }[] }>(
        page, '/stock-items?limit=500',
    );
    const item = data.items.find((i) => i.name === name);
    expect(item, `seed item "${name}" exists`).toBeTruthy();
    return item!.stock_item_id;
}

test('linked products render with exactly one Cheapest highlight and a quiet "Link another"', async ({ page }) => {
    await page.goto('/#/');
    const id = await itemIdByName(page, 'Full Cream Milk');
    await page.goto(`/#/stock/${id}`);
    await page.waitForLoadState('networkidle');
    await page.getByRole('tab', { name: 'Products' }).click();

    await expect(page.getByText('Linked products')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Link another' })).toBeVisible();

    // Two seeded linked products (Woolworths + Coles milk); exactly ONE
    // carries the Cheapest chip + highlight class.
    const cards = page.locator('.q-tab-panel .q-card').filter({ hasText: 'Add to list' });
    expect(await cards.count()).toBeGreaterThanOrEqual(2);
    await expect(page.getByText('Cheapest', { exact: true })).toHaveCount(1);
    await expect(page.locator('.dora-product-card--cheapest')).toHaveCount(1);

    // The retired "Get cheapest" toolbar button stays gone page-wide.
    await expect(page.getByRole('button', { name: /Get cheapest/i })).toHaveCount(0);
});

test('empty Products tab shows the centred CTA (no "Link another")', async ({ page }) => {
    await page.goto('/#/');
    const name = `e2e c1b3 item ${Date.now()}`;
    const levels = await apiGet<{ items: { stock_level_id: string; name: string }[] }>(
        page, '/stock-levels?limit=50',
    );
    const created = await apiMutate(page, 'post', '/stock-items', {
        name, stock_level_id: levels.items[0]!.stock_level_id,
    });
    const id = ((await created.json()) as { stock_item_id: string }).stock_item_id;
    try {
        await page.goto(`/#/stock/${id}`);
        await page.waitForLoadState('networkidle');
        await page.getByRole('tab', { name: 'Products' }).click();

        await expect(page.getByText('No products linked yet')).toBeVisible();
        const cta = page.getByRole('button', { name: 'Find & link a product' });
        await expect(cta).toBeVisible();
        // No "Link another" in the empty state — the CTA is the only entry.
        await expect(page.getByRole('button', { name: 'Link another' })).toHaveCount(0);

        // NOT pinned: where the CTA navigates. It currently pushes the
        // retired `/product-search` route (FU-186) and lands on the 404 —
        // a real bug logged as a follow-up; assert the destination here
        // once that call decides the new target.
    } finally {
        await apiMutate(page, 'delete', `/stock-items/${id}`);
    }
});
