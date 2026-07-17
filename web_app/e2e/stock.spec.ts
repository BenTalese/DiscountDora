import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet } from './helpers';

// Batch 2 (Stock) regression pins from the verify campaign:
//   FU-508 — StockItem.image was dropped app-wide. Guards against the
//            column/upload/thumbnail creeping back in.
//   FU-507 — expiry-on-open prompt: marking a SEALED item open offers to
//            update its effective expiry; re-sealing does NOT prompt.
//
// State: the curated dev seed (bulk=0) is deterministic. "Kensington Pride
// Mangoes" is created sealed with an expiry a few days out — the exact shape
// FU-507 needs. Keep in sync with seed.py.

type StockItem = { stock_item_id: string; name: string; is_open: boolean; expiry_date: string | null };

async function findItem(page: Page, name: string): Promise<StockItem> {
    const data = await apiGet<{ items: StockItem[] }>(page, '/stock-items?limit=500');
    const item = data.items.find((i) => i.name === name);
    expect(item, `seeded item "${name}" exists`).toBeTruthy();
    return item!;
}

test.describe('FU-508 — StockItem.image dropped', () => {
    test('no image endpoint is ever hit on stock pages', async ({ page }) => {
        const imageCalls: string[] = [];
        page.on('request', (r) => {
            if (/\/api\/stock-items\/[^/]+\/image/.test(r.url())) imageCalls.push(r.url());
        });

        await page.goto('/#/stock');
        await page.waitForLoadState('networkidle');
        // Into a detail page too — that's where an image once rendered.
        const item = await findItem(page, 'Full Cream Milk');
        await page.goto(`/#/stock/${item.stock_item_id}`);
        await page.waitForLoadState('networkidle');

        expect(imageCalls, 'no /stock-items/<id>/image requests').toEqual([]);
    });

    test('overview toolbar has no row-image toggle', async ({ page }) => {
        await page.goto('/#/stock');
        await expect(page.getByRole('button', { name: /row images/i })).toHaveCount(0);
    });

    test('detail Overview tab exposes no file/image upload input', async ({ page }) => {
        const item = await findItem(page, 'Full Cream Milk');
        await page.goto(`/#/stock/${item.stock_item_id}`);
        await expect(page.getByText('Open / in-use')).toBeVisible(); // detail mounted
        await expect(page.locator('input[type="file"]')).toHaveCount(0);
    });
});

test.describe('Stocktake "Needs check" quick-filter (verify L755–760)', () => {
    // Read-only: this only toggles a client-side filter (mutates nothing), so
    // it needs no restore. It DOES depend on the seed's overdue set being
    // intact, so it must run before stocktake.spec.ts drains the queue — file
    // order guarantees that ('stock.spec' sorts before 'stocktake.spec').
    //
    // The chip narrows the list to the server-owned stocktake queue (R-003 —
    // the SPA never re-derives "overdue"; both the "Stocktake (N)" button count
    // and the filter set come from /stocktake/queue). Asserted against that
    // server truth so the pin doesn't hinge on which items the seed happens to
    // mark overdue.
    type QueueItem = { stock_item_id: string; name: string };
    const queue = (page: Page) =>
        apiGet<{ items: QueueItem[]; total: number }>(page, '/stocktake/queue?limit=500');

    const chip = (page: Page) => page.locator('.q-chip').filter({ hasText: 'Needs check' });

    test('chip narrows the list to exactly the overdue set; toggling off restores', async ({ page }) => {
        const { items: overdue, total } = await queue(page);
        expect(total, 'seed has overdue items to check').toBeGreaterThan(0);

        await page.goto('/#/stock');
        await page.waitForLoadState('networkidle');

        // The toolbar button mirrors the same server-owned count. (It's a
        // BaseButton with a `to=` route, so it renders as a link, not a
        // button — assert on its visible label.)
        await expect(page.getByText(`Stocktake (${total})`, { exact: true })).toBeVisible();

        // Unfiltered, the list is strictly larger than the overdue subset.
        const allRows = await page.locator('.stock-row').count();
        expect(allRows).toBeGreaterThan(total);

        // The chip cluster lives in the collapsed FilterBar panel — open it.
        await page.getByRole('button', { name: 'Filters' }).click();

        // Flip "Needs check" on → the list narrows to exactly the queue ids.
        await chip(page).click();
        await expect(page.locator('.stock-row')).toHaveCount(total);
        for (const item of overdue) {
            await expect(
                page.locator('.stock-row').filter({ hasText: item.name }),
            ).toBeVisible();
        }

        // Toggle off → the full list returns.
        await chip(page).click();
        await expect(page.locator('.stock-row')).toHaveCount(allRows);
    });
});

test.describe('FU-507 — expiry-on-open prompt', () => {
    // Mutates one item's open flag — keep ordered and restore at the end.
    test.describe.configure({ mode: 'serial' });
    const NAME = 'Kensington Pride Mangoes';

    test('the seeded item is sealed with an expiry (fixture contract)', async ({ page }) => {
        await page.goto('/#/');
        const item = await findItem(page, NAME);
        expect(item.is_open, 'starts sealed').toBe(false);
        expect(item.expiry_date, 'has an expiry').toBeTruthy();
    });

    test('detail toggle → dialog → Update expiry saves both', async ({ page }) => {
        const item = await findItem(page, NAME);
        await page.goto(`/#/stock/${item.stock_item_id}`);
        await expect(page.getByText('Open / in-use')).toBeVisible();

        // Flip the Open toggle → the "Marking … as open" prompt appears.
        await page.locator('.q-toggle').first().click();
        const dialog = page.locator('.q-dialog').filter({ hasText: `Marking "${NAME}" as open` });
        await expect(dialog).toBeVisible();

        // Pick a new expiry and confirm.
        const newExpiry = '2027-01-15';
        await dialog.locator('input[type="date"]').fill(newExpiry);
        await dialog.getByRole('button', { name: 'Update expiry' }).click();

        // The detail-page toggle reloads silently (no toast — that's the row
        // path). Assert on server truth: both is_open and the new expiry
        // persisted in the one PATCH.
        await expect
            .poll(async () => (await findItem(page, NAME)).is_open)
            .toBe(true);
        expect((await findItem(page, NAME)).expiry_date).toBe(newExpiry);
    });

    test('re-sealing does NOT prompt (fires only on open) and restores state', async ({ page }) => {
        const item = await findItem(page, NAME);
        expect(item.is_open, 'is open from the previous test').toBe(true);
        await page.goto(`/#/stock/${item.stock_item_id}`);
        await expect(page.getByText('Open / in-use')).toBeVisible();

        await page.locator('.q-toggle').first().click();
        // No "Marking … as open" dialog on the seal direction — give it a beat
        // to (not) appear, then assert absence.
        await page.waitForTimeout(500);
        await expect(
            page.locator('.q-dialog').filter({ hasText: 'as open' }),
        ).toHaveCount(0);

        // Server truth: the item re-sealed (restores the fixture).
        await expect.poll(async () => (await findItem(page, NAME)).is_open).toBe(false);
    });
});
