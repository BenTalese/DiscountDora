import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet } from './helpers';

// FU-299 — the Pantry card's stock-donut deep-links (verify-campaign
// Dashboard batch). The card is no longer one big link: only the "View →"
// action, the low/out donut segments, and the low/out legend rows navigate —
// each to /stock?level_id=<id> resolved from server truth. The green
// in-stock segment/legend are deliberately inert (the page doesn't model a
// "not low/out" filter).
//
// The low-segment test clicks the actual SVG arc at a point computed from
// the /dashboard/summary proportions — pinning that the stroke really is
// pointer-hittable, not just that the handler is wired. Keyboard activation
// (Enter/Space on the tabbable segments) and the aria-labels cover the
// C13 keyboard/screen-reader bullets. Read-only on seed state.
test.describe.configure({ mode: 'serial' });

interface LevelsDto {
    items: { stock_level_id: string; name: string; sequence: number }[];
}
interface SummaryDto {
    stock_items: { total: number; low_stock: number; out_of_stock: number };
}
interface StockItemsDto {
    items: { stock_item_id: string; stock_level_id: string | null }[];
}

async function levelBySequence(page: Page, sequence: number) {
    const levels = await apiGet<LevelsDto>(page, '/stock-levels?limit=50');
    const lvl = levels.items.find((l) => l.sequence === sequence);
    expect(lvl, `seeded level with sequence ${sequence} exists`).toBeTruthy();
    return lvl!;
}

async function itemCountAtLevel(page: Page, levelId: string): Promise<number> {
    const data = await apiGet<StockItemsDto>(page, '/stock-items?limit=500');
    return data.items.filter((i) => i.stock_level_id === levelId).length;
}

test('only the low/out legend rows and "View →" are links; in-stock and the whole card stay inert', async ({ page }) => {
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Pantry' })).toBeVisible();

    const low = await levelBySequence(page, 1);
    const out = await levelBySequence(page, 2);

    // Legend deep-links resolve to the level-filtered stock view (server
    // truth ids), "View →" keeps the unfiltered pantry.
    const legend = page.locator('.dora-legend');
    await expect(legend.locator('a').filter({ hasText: 'running low' }))
        .toHaveAttribute('href', `#/stock?level_id=${low.stock_level_id}`);
    await expect(legend.locator('a').filter({ hasText: 'out' }))
        .toHaveAttribute('href', `#/stock?level_id=${out.stock_level_id}`);
    await expect(page.getByRole('link', { name: 'View →' })).toHaveAttribute('href', '#/stock');

    // The in-stock legend row is NOT a link, and clicking it goes nowhere —
    // the old whole-card navigation is gone.
    const inStockRow = legend.locator('li').filter({ hasText: 'in stock' });
    await expect(inStockRow.locator('a')).toHaveCount(0);
    await inStockRow.click();
    await expect(page).toHaveURL(/#\/$/);

    // Donut segments: seed has all three buckets populated → three arcs,
    // of which exactly the low/out pair are links (role, tabindex, class,
    // screen-reader label); the green residual carries none of it.
    const segs = page.locator('svg.dora-donut circle.dora-donut-seg');
    await expect(segs).toHaveCount(3);
    await expect(page.locator('svg.dora-donut circle[role="link"]')).toHaveCount(2);
    await expect(page.locator('circle[aria-label="View low items"]')).toHaveCount(1);
    await expect(page.locator('circle[aria-label="View out items"]')).toHaveCount(1);
    const green = segs.first();
    await expect(green).not.toHaveAttribute('role', 'link');
    await expect(green).not.toHaveAttribute('tabindex', '0');
    await expect(green).not.toHaveClass(/dora-donut-seg--link/);

    // Even a direct click event on the green arc navigates nowhere.
    await green.dispatchEvent('click');
    await expect(page).toHaveURL(/#\/$/);
});

test('pointer click on the low arc lands the filtered stock view: level chip + narrowed rows', async ({ page }) => {
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');

    const low = await levelBySequence(page, 1);
    const summary = await apiGet<SummaryDto>(page, '/dashboard/summary');
    const s = summary.stock_items;
    expect(s.low_stock, 'seed precondition: low-stock items exist').toBeGreaterThan(0);

    // Segments start at 12 o'clock and walk clockwise in push order
    // (in-stock → low → out). Click the middle of the low arc: angle
    // f·360° clockwise from 12 o'clock at the stroke radius (r=15.915 in
    // the 36-unit viewBox).
    const inStock = s.total - s.low_stock - s.out_of_stock;
    const f = (inStock + s.low_stock / 2) / s.total;
    // mouse.click doesn't scroll, and the Pantry card can sit below the
    // fold — bring the donut on-screen before measuring.
    await page.locator('svg.dora-donut').scrollIntoViewIfNeeded();
    const box = (await page.locator('svg.dora-donut').boundingBox())!;
    const R = (15.915 / 36) * box.width;
    const theta = f * 2 * Math.PI;
    const x = box.x + box.width / 2 + R * Math.sin(theta);
    const y = box.y + box.height / 2 - R * Math.cos(theta);
    await page.mouse.click(x, y);

    await page.waitForURL(new RegExp(`stock\\?level_id=${low.stock_level_id}`));
    await expect(page.getByText('This page wandered off')).toHaveCount(0);

    // The FilterBar's level select carries the deep-linked level, and only
    // that level's items render (count vs server truth).
    await page.getByRole('button', { name: 'Filters' }).click();
    await expect(
        page.locator('.q-select').filter({ hasText: low.name }).first(),
    ).toBeVisible();
    const expected = await itemCountAtLevel(page, low.stock_level_id);
    await expect.poll(() => page.locator('.stock-row').count()).toBe(expected);
});

test('keyboard: Enter on the out arc and Space on the low arc both navigate to their filtered views', async ({ page }) => {
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');

    const low = await levelBySequence(page, 1);
    const out = await levelBySequence(page, 2);

    await page.locator('circle[aria-label="View out items"]').press('Enter');
    await page.waitForURL(new RegExp(`stock\\?level_id=${out.stock_level_id}`));
    const expectedOut = await itemCountAtLevel(page, out.stock_level_id);
    await expect.poll(() => page.locator('.stock-row').count()).toBe(expectedOut);

    // Fresh full load rather than goBack — a warm history-back followed by
    // another router navigation can wedge the hash router (FU-584; it bit
    // the next-cook spec's Cook click).
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.goto('/#/');
    await expect(page.getByRole('heading', { name: 'Pantry' })).toBeVisible();

    await page.locator('circle[aria-label="View low items"]').press('Space');
    await page.waitForURL(new RegExp(`stock\\?level_id=${low.stock_level_id}`));
});
