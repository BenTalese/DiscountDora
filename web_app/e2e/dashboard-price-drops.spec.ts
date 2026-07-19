import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, apiMutate } from './helpers';

// FU-296 — the dashboard "Price drops" widget (verify-campaign Dashboard
// batch). Products-gated + defaultHidden: it lives in the Cards menu until
// enabled. The report's server halves (new-low honesty, no-history and
// inactive exclusions, %-then-amount ranking, the [1,20] limit clamp with
// default 5) are backend-pinned in test_reports_router.py; these tests pin
// the UI seams: hidden-by-default, menu enable/disable round-trip, the
// honest empty state on the seed (every seeded product sits AT its historic
// low, so no drops), and a real engineered drop rendering name · store ·
// linked-item link · price/was · "% off" badge.
//
// Two environment notes: (1) the dashboard is always WARM-navigated to
// (cold '/#/' loads race the one-shot /api/health flags probe and skip the
// products-gated fetch — FU-586); (2) the engineered product can't be
// deleted (no DELETE /products) so it's deactivated instead, which the
// report excludes (that exclusion is itself backend-pinned). The
// products-OFF half (card absent from dashboard AND menu) needs a
// productless install and stays a walk bullet.
test.describe.configure({ mode: 'serial' });

const STAMP = Date.now();
const PRODUCT = `e2e fu296 dropper ${STAMP}`;
const STORE = `e2e fu296 store ${STAMP}`;
const ITEM = `e2e fu296 item ${STAMP}`;

const CARD_TITLE = 'Price drops';

async function warmGotoDashboard(page: Page) {
    // Land on a lightweight page first so the health/flags probe resolves,
    // THEN in-app navigate — loadAll() must see products=true (FU-586).
    await page.goto('/#/stock');
    await page.waitForLoadState('networkidle');
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');
}

function card(page: Page) {
    return page.locator('.dora-card').filter({
        has: page.getByRole('heading', { name: CARD_TITLE }),
    });
}

async function toggleCardInMenu(page: Page) {
    await page.getByRole('button', { name: 'Cards' }).click();
    await page.locator('.q-menu .q-item').filter({ hasText: CARD_TITLE })
        .locator('.q-toggle').click();
    await page.keyboard.press('Escape');
}

test('hidden by default; Cards-menu enable shows the honest empty state on seed data', async ({ page }) => {
    // Seed precondition: every seeded product's current price equals its
    // historic low — a "first price" or "still at the low" is never a drop.
    const report = await apiGet<{ rows: unknown[] }>(page, '/reports/price-drops?limit=20');
    expect(report.rows, 'seed has no genuine new-low products').toHaveLength(0);

    await warmGotoDashboard(page);
    await expect(page.getByRole('heading', { name: CARD_TITLE })).toHaveCount(0);

    await toggleCardInMenu(page);
    await expect(card(page)).toHaveCount(1);
    await expect(card(page).getByText('Nothing at a new low right now')).toBeVisible();
    // No "My products →" action while there's nothing to review.
    await expect(card(page).getByText('My products →')).toHaveCount(0);
});

test('an engineered drop renders name · store · linked item · price/was · % badge', async ({ page }) => {
    await page.goto('/#/stock');

    // A tracked product at $10, then a price update to $8 (archives the
    // $10 offer → previous low) — a genuine 20% new low, linked to a
    // throwaway stock item so the row's deep-link renders.
    await apiMutate(page, 'post', '/stores', { name: STORE });
    const created = await apiMutate(page, 'post', '/products', {
        name: PRODUCT, store_name: STORE, merchant_stockcode: `FU296-${STAMP}`,
        brand: 'Test', price_now: 10.0, price_was: 12.0,
        is_active: true, is_available: true,
        size: '1L', size_unit: 'L', size_value: 1.0,
    });
    const productId = created.headers()['location']!.split(':').pop()!;
    await apiMutate(page, 'patch', `/products/${productId}`, {
        price_now: 8.0, price_was: 12.0,
    });
    const levels = await apiGet<{ items: { stock_level_id: string; sequence: number }[] }>(
        page, '/stock-levels?limit=50',
    );
    const item = await apiMutate(page, 'post', '/stock-items', {
        name: ITEM, stock_level_id: levels.items.find((l) => l.sequence === 0)!.stock_level_id,
    });
    const itemId = ((await item.json()) as { stock_item_id: string }).stock_item_id;
    await apiMutate(page, 'post', `/stock-items/${itemId}/products`, { product_id: productId });

    try {
        await warmGotoDashboard(page);
        const row = card(page).locator('.dora-deal-row').filter({ hasText: PRODUCT });
        await expect(row).toHaveCount(1);
        await expect(row).toContainText(STORE);
        await expect(row.locator('.dora-deal-now')).toContainText('8.00');
        await expect(row.locator('.dora-deal-was')).toContainText(/was .*10\.00/);
        await expect(row.locator('.dora-deal-badge')).toHaveText('20% off');
        await expect(row.getByRole('link', { name: ITEM }))
            .toHaveAttribute('href', `#/stock/${itemId}`);
        await expect(card(page).getByText('My products →')).toBeVisible();
    } finally {
        // No DELETE /products — deactivate instead (excluded from the
        // report, backend-pinned) and drop the throwaway item.
        await apiMutate(page, 'patch', `/products/${productId}`, { is_active: false });
        await apiMutate(page, 'delete', `/stock-items/${itemId}`);
    }

    // Deactivated → the card returns to the empty state on a fresh load.
    await warmGotoDashboard(page);
    await expect(card(page).getByText('Nothing at a new low right now')).toBeVisible();

    // Restore the card's defaultHidden state for later specs/runs.
    await toggleCardInMenu(page);
    await expect(page.getByRole('heading', { name: CARD_TITLE })).toHaveCount(0);
});
