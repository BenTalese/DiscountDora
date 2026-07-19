import { devices, type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, apiMutate } from './helpers';

// FU-294 (Cards-menu drag + tap reorder) and FU-292 (the `dashboard_layout`
// backend it persists through) — verify-campaign Dashboard batch. The layout
// {order, hidden} lives on the user (PATCH /auth/me), so every reorder here
// is asserted three ways: the menu's rendered row order, the server-truth
// JSON, and persistence across a reload / a second browser context ("another
// device"). The suite's per-run backend means the seed user starts with a
// null layout; the original value is captured and restored in afterAll so
// later specs (and re-runs) see the default order.
//
// The Today zone (Cookable tonight · The week ahead · Primary shopping
// list · Restock radar — all ungated) is the reorder guinea pig; Kitchen
// supplies the cross-zone rejection partner. Drag uses the native HTML5
// path (`page.dragAndDrop` → the useDragDropList handle); tap uses the
// C13-mandated up/down buttons. The mobile block runs under an iPhone UA —
// `cardDragEnabled` gates on Quasar's UA-based platform.is.mobile, not
// viewport width.
test.describe.configure({ mode: 'serial' });

const TODAY_FIRST = 'Cookable tonight';
const TODAY_SECOND = 'The week ahead';
// Hidden-by-default cards still list in the menu, so the zone's true last
// row is the opt-in calendar, not Restock radar.
const TODAY_LAST = 'This fortnight';
const KITCHEN_CARD = 'Pantry';

let originalLayout: string | null;

interface MeDto { dashboard_layout: string | null }

test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    originalLayout = (await apiGet<MeDto>(page, '/auth/me')).dashboard_layout;
    await page.close();
});

test.afterAll(async ({ browser }) => {
    const page = await browser.newPage();
    await apiMutate(page, 'patch', '/auth/me', { dashboard_layout: originalLayout });
    await page.close();
});

async function openMenu(page: Page) {
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: 'Cards' }).click();
    await expect(page.locator('.q-menu')).toBeVisible();
}

function menuRow(page: Page, label: string) {
    return page.locator('.q-menu .q-item').filter({ hasText: label });
}

/** Rendered top-to-bottom row labels of the open Cards menu. */
async function menuOrder(page: Page): Promise<string[]> {
    const rows = page.locator('.q-menu .q-item');
    const labels: string[] = [];
    for (const text of await rows.allInnerTexts()) {
        const clean = text.split('\n').map((s) => s.trim()).filter(Boolean);
        // Row text = icon ligatures + label; the label is the longest line.
        labels.push(clean.sort((a, b) => b.length - a.length)[0] ?? '');
    }
    return labels;
}

async function serverOrder(page: Page): Promise<string[]> {
    const me = await apiGet<MeDto>(page, '/auth/me');
    expect(me.dashboard_layout, 'layout persisted server-side').toBeTruthy();
    return (JSON.parse(me.dashboard_layout!) as { order: string[] }).order;
}

test('tap down-arrow reorders within the zone, persists server-side and across reload', async ({ page }) => {
    await openMenu(page);

    // Default order: the zone's first row can't move up, the last can't
    // move down. The arrows are targeted positionally (up, down) — they're
    // icon-only BaseButtons with tooltips but no aria-label, so they have
    // no accessible name (pre-existing; FU-578's unlabelled-buttons bucket).
    await expect(menuRow(page, TODAY_FIRST).locator('button').first()).toBeDisabled();
    await expect(menuRow(page, TODAY_LAST).locator('button').nth(1)).toBeDisabled();

    await menuRow(page, TODAY_FIRST).locator('button').nth(1).click();

    // Menu re-renders swapped; server truth has cookable after meal_plan.
    let order = await menuOrder(page);
    expect(order.indexOf(TODAY_SECOND)).toBeLessThan(order.indexOf(TODAY_FIRST));
    const stored = await serverOrder(page);
    expect(stored.indexOf('meal_plan')).toBeLessThan(stored.indexOf('cookable'));

    // Survives a full reload.
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: 'Cards' }).click();
    order = await menuOrder(page);
    expect(order.indexOf(TODAY_SECOND)).toBeLessThan(order.indexOf(TODAY_FIRST));

    // And the up-arrow undoes it (tap works both directions).
    await menuRow(page, TODAY_FIRST).locator('button').first().click();
    order = await menuOrder(page);
    expect(order.indexOf(TODAY_FIRST)).toBeLessThan(order.indexOf(TODAY_SECOND));
});

test('drag-handle drop reorders within the zone and follows the user to another context', async ({ page, browser }) => {
    await openMenu(page);

    // Desktop UA → every menu row carries the drag handle.
    const handles = page.locator('.q-menu .dora-dnd-handle');
    expect(await handles.count()).toBeGreaterThan(0);

    // Drag Cookable tonight onto Restock radar → drop-on semantics: the
    // dragged row takes the target's slot (end of the Today zone).
    await menuRow(page, TODAY_FIRST).locator('.dora-dnd-handle').dragTo(menuRow(page, TODAY_LAST));

    const order = await menuOrder(page);
    expect(order.indexOf(TODAY_LAST)).toBeLessThan(order.indexOf(TODAY_FIRST));
    const stored = await serverOrder(page);
    expect(stored.indexOf('restock')).toBeLessThan(stored.indexOf('cookable'));

    // "Another device": a fresh context (same user) renders the dragged
    // order — FU-292's cross-device contract.
    const otherPage = await browser.newPage();
    await otherPage.goto('/#/');
    await otherPage.waitForLoadState('networkidle');
    await otherPage.getByRole('button', { name: 'Cards' }).click();
    const otherOrder = await menuOrder(otherPage);
    expect(otherOrder.indexOf(TODAY_LAST)).toBeLessThan(otherOrder.indexOf(TODAY_FIRST));
    await otherPage.close();

    // Restore the default order for the remaining tests.
    await apiMutate(page, 'patch', '/auth/me', { dashboard_layout: originalLayout });
});

test('cross-zone drop is rejected: order unchanged in both zones', async ({ page }) => {
    await openMenu(page);
    const before = await menuOrder(page);

    await menuRow(page, KITCHEN_CARD).locator('.dora-dnd-handle').dragTo(menuRow(page, TODAY_SECOND));

    expect(await menuOrder(page)).toEqual(before);
    // Nothing was persisted either — the layout is untouched server-side.
    const me = await apiGet<MeDto>(page, '/auth/me');
    expect(me.dashboard_layout).toEqual(originalLayout);
});

test.describe('mobile (touch UA)', () => {
    test.use({
        userAgent: devices['iPhone 13'].userAgent,
        viewport: devices['iPhone 13'].viewport,
        hasTouch: true,
    });

    test('drag handles are hidden; tap arrows and visibility toggle remain', async ({ page }) => {
        await openMenu(page);
        await expect(page.locator('.q-menu .dora-dnd-handle')).toHaveCount(0);
        const row = menuRow(page, TODAY_FIRST);
        await expect(row.locator('button').nth(1)).toBeVisible();
        await expect(row.locator('.q-toggle')).toBeVisible();
    });
});
