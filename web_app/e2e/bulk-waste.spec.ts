import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, apiMutate, toast } from './helpers';

// Batch 3 — Bulk "Log waste…" on Stock Overview (origin FU-226, PROPOSAL_
// WASTE_MINIMISATION §5). The bulk-select bar reuses the single-item reason
// picker (R-001): one reason logs one StockItemWasteEvent per selected item
// AND clears each item's expiry, with a single summary toast whose Undo
// reverses BOTH. Regression-worthy because it's a per-item loop wrapped in
// batch summary/undo math (singular vs plural copy, "restore each expiry").
//
// State: mutates waste events (+ one item's expiry) on three stable seed
// items no other spec touches — Canned Tomatoes / Brown Onions / Garlic (all
// Stocked, no seeded expiry). Each test restores via the UI Undo it's pinning;
// an afterAll safety net then hard-resets via the API (delete any lingering
// event, null any expiry) so a mid-flow failure can't leak into later specs.
test.describe.configure({ mode: 'serial' });

type StockItem = { stock_item_id: string; name: string; expiry_date: string | null };
type WasteEvent = { event_id: string; stock_item_id: string; reason: string };

const NAMES = ['Canned Tomatoes', 'Brown Onions', 'Garlic'] as const;

async function itemsByName(page: Page): Promise<Record<string, StockItem>> {
    const data = await apiGet<{ items: StockItem[] }>(page, '/stock-items?limit=500');
    const out: Record<string, StockItem> = {};
    for (const name of NAMES) {
        const item = data.items.find((i) => i.name === name);
        expect(item, `seed item "${name}" exists`).toBeTruthy();
        out[name] = item!;
    }
    return out;
}

async function eventsFor(page: Page, ids: string[]): Promise<WasteEvent[]> {
    const { events } = await apiGet<{ events: WasteEvent[] }>(page, '/waste/events?limit=200');
    return events.filter((e) => ids.includes(e.stock_item_id));
}

// Enter bulk mode and tick the given seed items by name.
async function selectRows(page: Page, names: readonly string[]) {
    await page.goto('/#/stock');
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: 'Bulk select' }).click();
    for (const name of names) {
        await page.locator('.stock-row').filter({ hasText: name })
            .locator('.q-checkbox').click();
    }
}

// Hard-reset via the API so nothing leaks even if a UI Undo above didn't run.
test.afterAll(async ({ browser }) => {
    const context = await browser.newContext({ storageState: 'e2e/.auth/user.json' });
    const page = await context.newPage();
    try {
        const items = await itemsByName(page);
        const ids = NAMES.map((n) => items[n].stock_item_id);
        for (const e of await eventsFor(page, ids)) {
            await apiMutate(page, 'delete', `/waste/events/${e.event_id}`);
        }
        for (const n of NAMES) {
            if (items[n].expiry_date !== null) {
                await apiMutate(page, 'patch', `/stock-items/${items[n].stock_item_id}`, {
                    expiry_date: null,
                });
            }
        }
    } finally {
        await context.close();
    }
});

test('"Log waste…" is disabled until something is selected', async ({ page }) => {
    await page.goto('/#/stock');
    await page.getByRole('button', { name: 'Bulk select' }).click();
    // Bulk bar visible, nothing ticked → the action is disabled (matches the
    // other bulk actions).
    await expect(page.getByRole('button', { name: /Log waste/ })).toBeDisabled();
});

test('bulk waste logs one event per item, plural toast, and Undo reverses it', async ({ page }) => {
    const items = await itemsByName(page);
    const ids = NAMES.map((n) => items[n].stock_item_id);
    expect(await eventsFor(page, ids), 'items start with no waste events').toHaveLength(0);

    await selectRows(page, NAMES);

    // Open the reason picker and assert its bulk-mode copy.
    await page.getByRole('button', { name: /Log waste/ }).click();
    const dialog = page.locator('.q-dialog').filter({ hasText: 'Why did this go to waste?' });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText('3 items', { exact: true })).toBeVisible();
    await expect(dialog.getByText('One reason applies to every selected item.')).toBeVisible();

    // A tile tap IS the submit (no separate Log button).
    await dialog.getByRole('button', { name: 'Spoiled' }).click();
    await expect(dialog).toBeHidden();

    // One summary toast (plural) with an Undo action; bulk mode exits.
    await expect(toast(page, 'Logged 3 items as wasted.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Bulk select' })).toBeVisible();

    // Server truth: exactly one 'spoiled' event per selected item.
    await expect.poll(async () => (await eventsFor(page, ids)).length).toBe(3);
    for (const e of await eventsFor(page, ids)) {
        expect(e.reason).toBe('spoiled');
    }

    // Undo (on the summary toast) removes all three events.
    await toast(page, 'Logged 3 items as wasted.').getByRole('button', { name: 'Undo' }).click();
    await expect(toast(page, 'Undone.')).toBeVisible();
    await expect.poll(async () => (await eventsFor(page, ids)).length).toBe(0);
});

test('a single selected item uses singular copy', async ({ page }) => {
    const items = await itemsByName(page);
    const id = items['Canned Tomatoes'].stock_item_id;

    await selectRows(page, ['Canned Tomatoes']);
    await page.getByRole('button', { name: /Log waste/ }).click();
    const dialog = page.locator('.q-dialog').filter({ hasText: 'Why did this go to waste?' });
    await expect(dialog.getByText('1 item', { exact: true })).toBeVisible();
    await dialog.getByRole('button', { name: 'Spoiled' }).click();

    await expect(toast(page, 'Logged 1 item as wasted.')).toBeVisible();
    await expect.poll(async () => (await eventsFor(page, [id])).length).toBe(1);

    // Restore.
    await toast(page, 'Logged 1 item as wasted.').getByRole('button', { name: 'Undo' }).click();
    await expect.poll(async () => (await eventsFor(page, [id])).length).toBe(0);
});

test('logging waste clears a set expiry; Undo restores it', async ({ page }) => {
    const items = await itemsByName(page);
    const id = items['Garlic'].stock_item_id;
    const EXPIRY = '2027-04-01';

    // Give Garlic an expiry to clear (the seed item has none).
    await apiMutate(page, 'patch', `/stock-items/${id}`, { expiry_date: EXPIRY });
    expect((await itemsByName(page))['Garlic'].expiry_date).toBe(EXPIRY);

    await selectRows(page, ['Garlic']);
    await page.getByRole('button', { name: /Log waste/ }).click();
    const dialog = page.locator('.q-dialog').filter({ hasText: 'Why did this go to waste?' });
    await dialog.getByRole('button', { name: 'Spoiled' }).click();
    await expect(toast(page, 'Logged 1 item as wasted.')).toBeVisible();

    // Expiry cleared as part of the waste log.
    await expect.poll(async () => (await itemsByName(page))['Garlic'].expiry_date).toBeNull();

    // Undo restores BOTH the event deletion and the original expiry.
    await toast(page, 'Logged 1 item as wasted.').getByRole('button', { name: 'Undo' }).click();
    await expect(toast(page, 'Undone.')).toBeVisible();
    await expect.poll(async () => (await itemsByName(page))['Garlic'].expiry_date).toBe(EXPIRY);
    await expect.poll(async () => (await eventsFor(page, [id])).length).toBe(0);

    // Reset the seed item back to no-expiry.
    await apiMutate(page, 'patch', `/stock-items/${id}`, { expiry_date: null });
});

test('single-item row expiry-menu "Log waste" still works (bulk path did not regress it)', async ({ page }) => {
    // L836 sanity — the per-row waste path is a *different* handler (its own
    // toast copy, quoting the item name) that the bulk flow reuses the dialog
    // from. The row menu only appears when the item HAS an expiry (no-expiry
    // shows a date picker instead), so give Canned Tomatoes one first.
    const items = await itemsByName(page);
    const id = items['Canned Tomatoes'].stock_item_id;
    const EXPIRY = '2027-05-01';
    await apiMutate(page, 'patch', `/stock-items/${id}`, { expiry_date: EXPIRY });

    await page.goto('/#/stock');
    await page.waitForLoadState('networkidle');
    const row = page.locator('.stock-row').filter({ hasText: 'Canned Tomatoes' });

    // The expiry action button's accessible name is "Expires <date>" when set
    // → click it to open the push/clear/log-waste menu, then Log waste.
    await row.getByRole('button', { name: `Expires ${EXPIRY}` }).click();
    await page.getByRole('listitem').filter({ hasText: 'Log waste' }).click();

    const dialog = page.locator('.q-dialog').filter({ hasText: 'Why did this go to waste?' });
    await expect(dialog).toBeVisible();
    await dialog.getByRole('button', { name: 'Spoiled' }).click();

    // Per-item toast quotes the item name (distinct from the bulk summary copy).
    await expect(toast(page, 'Logged "Canned Tomatoes" as wasted.')).toBeVisible();
    await expect.poll(async () => (await eventsFor(page, [id])).length).toBe(1);
    await expect.poll(async () => (await itemsByName(page))['Canned Tomatoes'].expiry_date).toBeNull();

    // Undo reverses the event + restores the expiry.
    await toast(page, 'Logged "Canned Tomatoes" as wasted.')
        .getByRole('button', { name: 'Undo' }).click();
    await expect(toast(page, 'Undone.')).toBeVisible();
    await expect.poll(async () => (await eventsFor(page, [id])).length).toBe(0);
    await expect.poll(async () => (await itemsByName(page))['Canned Tomatoes'].expiry_date).toBe(EXPIRY);

    // Reset the seed item back to no-expiry.
    await apiMutate(page, 'patch', `/stock-items/${id}`, { expiry_date: null });
});
