import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, apiMutate, toast } from './helpers';

// FU-300 — the dashboard "Log price" quick action (verify-campaign Dashboard
// batch), plus FU-297's money-gate (same seam: both surfaces hang off
// useMoneyEnabled, so one PATCH /auth/me toggle exercises them together).
//
// Covered here: the three-button quick-action bar; the two-step LogPriceSheet
// (picker shortlist low/out-first, live filtering, title update on selection,
// prefill from the detail DTO, back-arrow reset); the submit happy path with
// server truth (the observation lands in the detail DTO) and the Your-Prices
// widget render; dismiss-means-cancel (no POST) + fresh reopen; and money OFF
// hiding Log price AND the budget card (dashboard + Cards menu) with no
// /api/budget/status request fired.
//
// The e2e seed ships with money OFF at BOTH layers (install `money_enabled`
// AppSetting and the per-user opt-in default False), so this spec enables
// both up front and restores the seed state in afterAll; the suite is
// single-worker serial, so nothing races it. The submitted observation is
// deleted via the API in a finally.
test.describe.configure({ mode: 'serial' });

const ITEM = 'Full Cream Milk';

async function setMoney(page: Page, layer: 'install' | 'user', on: boolean) {
    if (layer === 'install') {
        await apiMutate(page, 'patch', '/app-settings', { money_enabled: on });
    } else {
        await apiMutate(page, 'patch', '/auth/me', { money_features_enabled: on });
    }
}

test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    await page.goto('/#/');
    await setMoney(page, 'install', true);
    await setMoney(page, 'user', true);
    await page.close();
});

test.afterAll(async ({ browser }) => {
    const page = await browser.newPage();
    await page.goto('/#/');
    await setMoney(page, 'user', false);
    await setMoney(page, 'install', false);
    await page.close();
});

interface StockItemsDto {
    items: { stock_item_id: string; name: string; stock_level_id: string | null }[];
}
interface StockLevelsDto {
    items: { stock_level_id: string; sequence: number }[];
}
interface DetailDto {
    price_observations?: {
        observation_id: string;
        total_price: number;
        total_measure: number;
        unit: string;
        store_id: string | null;
    }[];
    price_entry_prefill?: {
        total_price: number;
        total_measure: number;
        unit: string;
    } | null;
}

async function itemIdByName(page: Page, name: string): Promise<string> {
    const data = await apiGet<StockItemsDto>(page, '/stock-items?limit=500');
    const item = data.items.find((i) => i.name === name);
    expect(item, `seed item "${name}" exists`).toBeTruthy();
    return item!.stock_item_id;
}

function sheet(page: Page) {
    return page.locator('.q-dialog').filter({ hasText: 'Log a price' });
}

async function openSheet(page: Page) {
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: 'Log price' }).click();
    await expect(sheet(page)).toBeVisible();
}

test('picker: low/out-first shortlist, live filter, title update, prefill, back-arrow reset', async ({ page }) => {
    await openSheet(page);

    // Step 1 — the no-query shortlist: at most 12 rows, and the first row is
    // one of the most-depleted items (max level sequence per server truth) —
    // the "thing I just bought that was running low" ordering.
    const search = sheet(page).getByLabel('Search stock items');
    await expect(search).toBeVisible();
    const rows = sheet(page).locator('.log-price-sheet__results .q-item');
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
    expect(rowCount).toBeLessThanOrEqual(12);

    const [items, levels] = await Promise.all([
        apiGet<StockItemsDto>(page, '/stock-items?limit=500'),
        apiGet<StockLevelsDto>(page, '/stock-levels?limit=50'),
    ]);
    const seqOf = (levelId: string | null) =>
        levels.items.find((l) => l.stock_level_id === levelId)?.sequence ?? -1;
    const maxSeq = Math.max(...items.items.map((i) => seqOf(i.stock_level_id)));
    // innerText carries the avatar's icon ligature on its own line — the
    // item name is the last non-empty line.
    const firstName = (await rows.first().innerText())
        .split('\n').map((s) => s.trim()).filter(Boolean).pop();
    const firstItem = items.items.find((i) => i.name === firstName);
    expect(firstItem, `picker's first row "${firstName}" is a known item`).toBeTruthy();
    expect(seqOf(firstItem!.stock_level_id)).toBe(maxSeq);

    // Live filtering: every result contains the query.
    await search.fill('milk');
    await expect(rows.first()).toContainText(/milk/i);
    for (const text of await rows.allInnerTexts()) {
        expect(text.toLowerCase()).toContain('milk');
    }

    // Step 2 — selection flips the sheet title and renders the entry form.
    await rows.filter({ hasText: ITEM }).first().click();
    await expect(sheet(page).getByText(`Log a price · ${ITEM}`)).toBeVisible();
    await expect(sheet(page).getByLabel('Price')).toBeVisible();
    await expect(sheet(page).getByRole('button', { name: 'Log', exact: true })).toBeVisible();

    // Prefill contract (F2): when the detail DTO carries a prefill, the form
    // seeds from it — server truth, not a hardcoded expectation.
    const id = await itemIdByName(page, ITEM);
    const detail = await apiGet<DetailDto>(page, `/stock-items/${id}/detail`);
    if (detail.price_entry_prefill) {
        await expect(sheet(page).getByLabel('Price')).toHaveValue(
            String(detail.price_entry_prefill.total_price),
        );
        await expect(sheet(page).getByText('Prefilled')).toBeVisible();
    }

    // Back arrow returns to the picker. The QUERY IS PRESERVED — the code's
    // clearSelection() only drops the selection (the full reset happens on
    // dialog dismiss, pinned in the cancel test). The FU-300 verify bullet
    // expected a cleared input; behaviour-vs-checklist call logged as FU-585
    // — repoint this assertion if the decision goes the other way.
    await sheet(page).getByRole('button', { name: 'Back to item picker' }).click();
    await expect(sheet(page).getByLabel('Search stock items')).toHaveValue('milk');
    await expect(sheet(page).getByText(`Log a price · ${ITEM}`)).toHaveCount(0);

    await page.keyboard.press('Escape');
    await expect(sheet(page)).toHaveCount(0);
});

test('submit logs the observation: toast, server truth, Your-Prices render', async ({ page }) => {
    const id = await (async () => {
        await page.goto('/#/');
        return itemIdByName(page, ITEM);
    })();
    const before = await apiGet<DetailDto>(page, `/stock-items/${id}/detail`);
    const beforeIds = new Set((before.price_observations ?? []).map((o) => o.observation_id));

    await openSheet(page);
    const search = sheet(page).getByLabel('Search stock items');
    await search.fill('full cream');
    await sheet(page).locator('.log-price-sheet__results .q-item').filter({ hasText: ITEM }).first().click();
    await expect(sheet(page).getByText(`Log a price · ${ITEM}`)).toBeVisible();

    // Distinctive values so the server-truth assertion can't false-positive
    // on a seeded observation; chosen so the derived per-unit ($3.20/L)
    // formats without float-rounding ambiguity.
    await sheet(page).getByLabel('Price').fill('6.40');
    await sheet(page).getByLabel('Size').fill('2');
    await sheet(page).getByLabel('Unit').click();
    await page.locator('.q-menu').getByText('volume — L', { exact: true }).click();

    let createdId: string | null = null;
    try {
        await sheet(page).getByRole('button', { name: 'Log', exact: true }).click();
        await expect(toast(page, `Logged a price for ${ITEM}.`)).toBeVisible();
        await expect(sheet(page)).toHaveCount(0);

        // Server truth: exactly one new observation, carrying the folded shape.
        const after = await apiGet<DetailDto>(page, `/stock-items/${id}/detail`);
        const created = (after.price_observations ?? []).filter(
            (o) => !beforeIds.has(o.observation_id),
        );
        expect(created).toHaveLength(1);
        createdId = created[0]!.observation_id;
        expect(created[0]!.total_price).toBe(6.4);
        expect(created[0]!.total_measure).toBe(2);
        expect(created[0]!.unit).toBe('L');

        // The Your-Prices widget on the detail page shows it. Fresh page →
        // single full goto (the double-goto hash race is FU-584).
        const detailPage = await page.context().newPage();
        await detailPage.goto(`/#/stock/${id}`);
        await detailPage.waitForLoadState('networkidle');
        // The widget shows the server-derived per-unit price (R-003 — the
        // client never divides): $6.40 over 2 L → "Last seen $3.20 / L".
        const widget = detailPage.locator('.dora-your-prices');
        await expect(widget).toBeVisible();
        await expect(widget.getByText(/Last seen/)).toBeVisible();
        await expect(widget.getByText(/3\.20/)).toBeVisible();
        await detailPage.close();
    } finally {
        if (createdId) {
            await apiMutate(page, 'delete', `/stock-items/${id}/price-observations/${createdId}`);
        }
    }
});

test('dismiss is a cancel (no POST); the next open starts fresh', async ({ page }) => {
    const posts: string[] = [];
    page.on('request', (r) => {
        if (r.method() === 'POST' && r.url().includes('/price-observations')) posts.push(r.url());
    });

    await openSheet(page);
    await sheet(page).getByLabel('Search stock items').fill('full cream');
    await sheet(page).locator('.log-price-sheet__results .q-item').filter({ hasText: ITEM }).first().click();
    await expect(sheet(page).getByText(`Log a price · ${ITEM}`)).toBeVisible();

    // Cancel from within the entry form closes the sheet without a request.
    await sheet(page).getByRole('button', { name: 'Cancel' }).click();
    await expect(sheet(page)).toHaveCount(0);
    expect(posts).toHaveLength(0);

    // Reopen → picker mode, no stale selection or query.
    await page.getByRole('button', { name: 'Log price' }).click();
    await expect(sheet(page)).toBeVisible();
    await expect(sheet(page).getByLabel('Search stock items')).toHaveValue('');
    await expect(sheet(page).getByText(`Log a price · ${ITEM}`)).toHaveCount(0);
    await page.keyboard.press('Escape');
});

test('money OFF hides Log price and the budget card (no budget-status request); ON restores', async ({ page }) => {
    const budgetRequests: string[] = [];
    page.on('request', (r) => {
        if (r.url().includes('/budget/status')) budgetRequests.push(r.url());
    });

    try {
        await apiMutate(page, 'patch', '/auth/me', { money_features_enabled: false });
        await page.goto('/#/');
        await page.waitForLoadState('networkidle');

        // Quick-action bar: the two money-free actions stay, Log price goes.
        await expect(page.getByRole('button', { name: 'Add item' })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Add to list' })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Log price' })).toHaveCount(0);

        // FU-297: the budget card ("Grocery budget" / "Grocery spend this
        // …") is absent from the dashboard AND the Cards menu, and no GET
        // /api/budget/status fires on load.
        await expect(page.getByText(/Grocery (budget|spend)/)).toHaveCount(0);
        expect(budgetRequests).toHaveLength(0);
        await page.getByRole('button', { name: 'Cards' }).click();
        await expect(page.locator('.q-menu .q-item').filter({ hasText: /Grocery (budget|spend)/ })).toHaveCount(0);
        await page.keyboard.press('Escape');
    } finally {
        await apiMutate(page, 'patch', '/auth/me', { money_features_enabled: true });
    }

    // Money back ON: the button returns (a same-URL goto is a no-op for the
    // SPA, so reload to refetch /auth/me). NOT pinned: the budget-status
    // request firing on this load — DashboardPage.loadAll() races the
    // one-shot /api/health flags probe on a cold mount and never retries
    // when the flags land (FU-586), so the money loaders can silently skip.
    // Assert the request here once that's fixed.
    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('button', { name: 'Log price' })).toBeVisible();
});
