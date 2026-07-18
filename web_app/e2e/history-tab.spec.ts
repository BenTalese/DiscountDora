import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, apiMutate } from './helpers';

// History tab (2026-06-30 feedback, verify-campaign Batch 3). The server
// halves are backend-pinned (expiry-event emission + per-kind cap +
// history_older_count in test_stock_item_router.py; the Bought/Cooked feeds
// in test_stock_item_history_feeds.py) — these tests pin the UI halves: the
// truncation footer against the seeded chatty item, the mixed-kind timeline
// render, the "Used in <recipe> · N meals" batch badge, and the full expiry
// set→pushed→cleared title/body family on a throwaway item.

async function itemIdByName(page: Page, name: string): Promise<string> {
    const data = await apiGet<{ items: { stock_item_id: string; name: string }[] }>(
        page, '/stock-items?limit=500',
    );
    const item = data.items.find((i) => i.name === name);
    expect(item, `seed item "${name}" exists`).toBeTruthy();
    return item!.stock_item_id;
}

async function openHistory(page: Page, itemId: string): Promise<void> {
    await page.goto(`/#/stock/${itemId}`);
    await page.waitForLoadState('networkidle');
    await page.getByRole('tab', { name: 'History' }).click();
}

test('seeded chatty item trips the cap: 16 older events not shown, count is server-stable', async ({ page }) => {
    await page.goto('/#/');
    const id = await itemIdByName(page, 'Sriracha (chatty history test)');
    await openHistory(page, id);

    // 66 seeded expiry events − the 50-per-kind cap = 16, pluralised.
    await expect(page.getByText('16 older events not shown')).toBeVisible();
    // The capped feed itself renders (newest pushes survive the cut).
    expect(await page.getByText(/Pushed expiry \+\d+ days?/).count()).toBeGreaterThan(5);

    // Reload → same footer count (server-derived, no client drift).
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.getByRole('tab', { name: 'History' }).click();
    await expect(page.getByText('16 older events not shown')).toBeVisible();
});

test('a busy item under the cap interleaves kinds with no footer', async ({ page }) => {
    await page.goto('/#/');
    const id = await itemIdByName(page, 'Full Cream Milk');
    await openHistory(page, id);

    // Seeded mix: purchases from finished lists, a spoiled waste event,
    // level bounces, an expiry push — all in one date-sorted timeline.
    await expect(page.getByText(/Bought · /).first()).toBeVisible();
    await expect(page.getByText(/Wasted: /).first()).toBeVisible();
    await expect(page.getByText(/Pushed expiry/).first()).toBeVisible();
    // Well under the 50-per-kind cap on every kind → the footer must not render.
    await expect(page.getByText(/older events? not shown/)).toHaveCount(0);
});

test('cook entries render "Used in <recipe>" with the batch-cook meals badge', async ({ page }) => {
    await page.goto('/#/');
    const id = await itemIdByName(page, 'Garlic');
    await openHistory(page, id);

    await expect(page.getByText(/Used in /).first()).toBeVisible();
    // The seed cooks garlic recipes with meals_cooked > 1 → the badge rides
    // the title ("Used in <recipe> · N meals").
    await expect(page.getByText(/Used in .+ · \d+ meals/).first()).toBeVisible();
});

test('expiry trail renders the full set → pushed → cleared family', async ({ page }) => {
    // Throwaway item engineered via the API: create with an expiry (set),
    // move it a week out (pushed +7), then clear it — the timeline must show
    // all three titles with their bodies. Deleted at the end.
    await page.goto('/#/');
    const levels = await apiGet<{ items: { stock_level_id: string; name: string }[] }>(
        page, '/stock-levels?limit=50',
    );
    const level = levels.items[0]!;
    const name = `e2e history trail ${Date.now()}`;
    const created = await apiMutate(page, 'post', '/stock-items', {
        name,
        stock_level_id: level.stock_level_id,
        expiry_date: '2030-01-01',
    });
    const id = ((await created.json()) as { stock_item_id: string }).stock_item_id;
    try {
        await apiMutate(page, 'patch', `/stock-items/${id}`, { expiry_date: '2030-01-08' });
        await apiMutate(page, 'patch', `/stock-items/${id}`, { expiry_date: null });

        await openHistory(page, id);
        await expect(page.getByText('Set expiry', { exact: true })).toBeVisible();
        await expect(page.getByText('Pushed expiry +7 days')).toBeVisible();
        await expect(page.getByText('2030-01-01 → 2030-01-08')).toBeVisible();
        await expect(page.getByText('Cleared expiry', { exact: true })).toBeVisible();
        await expect(page.getByText('Was 2030-01-08')).toBeVisible();
    } finally {
        await apiMutate(page, 'delete', `/stock-items/${id}`);
    }
});
