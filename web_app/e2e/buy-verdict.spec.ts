import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, apiMutate, toast } from './helpers';

// Regression pins for the BuyVerdictCard one-tap actions (FU-454, walked
// manually in verify-campaign Batch 0) and the cache-staleness fix
// (FU-572: after an action the card must repaint with the fresh verdict
// IN PLACE, not keep the old answer until a remount).
//
// State comes from the seeded QA fixture (seed_dev_data(qa_fixtures=True)):
// "QA Verdict Cheese" — 3 priced purchases 90/60/30 days ago + 2 waste
// events + level Stocked → the oracle answers skip/high with the
// mark_stocked one-tap. Keep the numbers in sync with seed.py.

const FIXTURE_NAME = 'QA Verdict Cheese';

type Verdict = {
    verdict: string;
    confidence: string;
    one_tap_action: { kind: string; label: string } | null;
};

async function fixtureItemId(page: Page): Promise<string> {
    const data = await apiGet<{ items: { stock_item_id: string; name: string }[] }>(
        page, '/stock-items?limit=500',
    );
    const item = data.items.find((i) => i.name === FIXTURE_NAME);
    expect(item, `seeded fixture "${FIXTURE_NAME}" exists`).toBeTruthy();
    return item!.stock_item_id;
}

async function draftListId(page: Page): Promise<string> {
    // Bare array of summaries (get_shopping_lists.py `ok(_Summaries)`) — not
    // paginated like /stock-items.
    const data = await apiGet<{ shopping_list_id: string; name: string }[]>(
        page, '/shopping-lists',
    );
    const draft = data.find((l) => l.name === 'This week');
    expect(draft, 'seeded draft list "This week" exists').toBeTruthy();
    return draft!.shopping_list_id;
}

type StockLevel = { stock_level_id: string; name: string; sequence: number };

async function levelByName(page: Page, name: string): Promise<StockLevel> {
    const { items } = await apiGet<{ items: StockLevel[] }>(page, '/stock-levels?limit=50');
    const lvl = items.find((l) => l.name === name);
    expect(lvl, `stock level "${name}" exists`).toBeTruthy();
    return lvl!;
}

async function itemIdByName(page: Page, name: string): Promise<string> {
    const data = await apiGet<{ items: { stock_item_id: string; name: string }[] }>(
        page, '/stock-items?limit=500',
    );
    const item = data.items.find((i) => i.name === name);
    expect(item, `seed item "${name}" exists`).toBeTruthy();
    return item!.stock_item_id;
}

async function listContains(page: Page, listId: string, itemId: string): Promise<boolean> {
    const detail = await apiGet<{ lines: { stock_item_id: string | null }[] }>(
        page, `/shopping-lists/${listId}`,
    );
    return detail.lines.some((l) => l.stock_item_id === itemId);
}

// The tests mutate and restore one shared fixture item — keep them ordered.
test.describe.configure({ mode: 'serial' });

// Hard-reset via the API so nothing leaks even if a test bailed mid-flow:
// oracle flag back on, fixture back to Stocked, fixture off the draft list.
test.afterAll(async ({ browser }) => {
    const context = await browser.newContext({ storageState: 'e2e/.auth/user.json' });
    const page = await context.newPage();
    try {
        const settings = await apiGet<{ buy_verdict_enabled: boolean }>(page, '/app-settings');
        if (!settings.buy_verdict_enabled) {
            await apiMutate(page, 'patch', '/app-settings', { buy_verdict_enabled: true });
        }
        const id = await fixtureItemId(page);
        const listId = await draftListId(page);
        if (await listContains(page, listId, id)) {
            await apiMutate(page, 'delete', `/shopping-lists/${listId}/lines/by-stock-item/${id}`);
        }
        const stocked = await levelByName(page, 'Stocked');
        await apiMutate(page, 'patch', `/stock-items/${id}`, {
            stock_level_id: stocked.stock_level_id,
        });
    } finally {
        await context.close();
    }
});

test('the seeded fixture yields skip/high + mark_stocked (oracle contract)', async ({ page }) => {
    // Cheap canary: if the seed numbers drift, fail HERE with a clear
    // message instead of in the UI walks below.
    await page.goto('/#/');
    const id = await fixtureItemId(page);
    const v = await apiGet<Verdict>(page, `/stock-items/${id}/buy-verdict`);
    expect(v.verdict).toBe('skip');
    expect(v.confidence).toBe('high');
    expect(v.one_tap_action?.kind).toBe('mark_stocked');
});

test('overview: Skip chip → popover → one-tap "Already stocked" (FU-454)', async ({ page }) => {
    await page.goto('/#/stock');
    const search = page
        .locator('input[type="search"], input[placeholder*="earch" i], input[aria-label*="earch" i]')
        .first();
    await search.fill(FIXTURE_NAME);

    const row = page.locator('[class*="stock-row"]').filter({ hasText: FIXTURE_NAME }).first();
    await row.getByText('Skip', { exact: true }).first().click();

    // The verdict popover, with the one-tap action.
    await page.getByRole('button', { name: 'Already stocked' }).click();

    // Data-driven toast copy (FU-572 — the level's real name, not the
    // retired hardcoded "Well-Stocked").
    await expect(toast(page, 'Marked as Stocked.')).toBeVisible();
});

test('detail: one-tap removes the line and the card repaints in place (FU-572 pin)', async ({ page }) => {
    // Engineer the on-list state BEFORE any page load (page.request works
    // off the context cookie jar alone). The single goto below is then a
    // full document load at the detail route — a same-document hash-only
    // goto (dashboard → detail) doesn't reliably drive vue-router here.
    const id = await fixtureItemId(page);
    const listId = await draftListId(page);
    // The UI path for add-to-list is pinned above and in the cart-button
    // suites; here the list line is just setup.
    await apiMutate(page, 'post', `/shopping-lists/${listId}/lines`, { stock_item_id: id });

    await page.goto(`/#/stock/${id}`);
    // Fresh page load → fresh verdict → the on-list one-tap.
    const removeBtn = page.getByRole('button', { name: 'Remove from list' });
    await removeBtn.click();

    await expect(toast(page, /removed from/i)).toBeVisible();

    // FU-572: the card refetches on invalidation and swaps the one-tap IN
    // PLACE — before the fix it kept "Remove from list" until a remount.
    await expect(page.getByRole('button', { name: 'Already stocked' })).toBeVisible();

    // Server truth: the line is gone (fixture restored to its seeded state).
    const list = await apiGet(page, `/shopping-lists/${listId}`);
    expect(JSON.stringify(list)).not.toContain(id);
});

test('out of stock: Buy badge, "You\'re out of stock" leads, one-tap lands on the draft list', async ({ page }) => {
    // P8-05 verify: out-of-stock overrides everything (even the fixture's
    // wasteful history) → buy/high with the need reason first.
    await page.goto('/#/');
    const id = await fixtureItemId(page);
    const listId = await draftListId(page);
    const out = await levelByName(page, 'Out of Stock');
    await apiMutate(page, 'patch', `/stock-items/${id}`, { stock_level_id: out.stock_level_id });

    // API canary before the UI walk — fail here with a clear message if the
    // composer contract drifts.
    const v = await apiGet<Verdict & { reasons: { signal: string }[] }>(
        page, `/stock-items/${id}/buy-verdict`,
    );
    expect(v.verdict).toBe('buy');
    expect(v.confidence).toBe('high');
    expect(v.reasons[0]?.signal).toBe('out_of_stock');
    expect(v.one_tap_action?.kind).toBe('add_to_list');

    await page.goto('/#/stock');
    await page.waitForLoadState('networkidle');
    const search = page
        .locator('input[type="search"], input[placeholder*="earch" i], input[aria-label*="earch" i]')
        .first();
    await search.fill(FIXTURE_NAME);
    const row = page.locator('[class*="stock-row"]').filter({ hasText: FIXTURE_NAME }).first();
    await row.getByText('Buy', { exact: true }).first().click();

    await expect(page.getByText("You're out of stock")).toBeVisible();
    await page.getByRole('button', { name: 'Add to primary list' }).click();
    await expect(toast(page, '1 added.')).toBeVisible();

    // Server truth: the one-tap landed the item on the primary draft.
    await expect.poll(() => listContains(page, listId, id)).toBe(true);

    // Restore: off the list, back to Stocked.
    await apiMutate(page, 'delete', `/shopping-lists/${listId}/lines/by-stock-item/${id}`);
    const stocked = await levelByName(page, 'Stocked');
    await apiMutate(page, 'patch', `/stock-items/${id}`, { stock_level_id: stocked.stock_level_id });
});

test('low confidence stays silent: thin-history item renders no badge', async ({ page }) => {
    // P8-05 verify: low-confidence noise on every row breaks Charter P3 —
    // the row hides the badge whenever the oracle answers confidence=low.
    // Jasmine Rice is a seed item with no price history (read-only here).
    await page.goto('/#/');
    const id = await itemIdByName(page, 'Jasmine Rice');
    const v = await apiGet<Verdict>(page, `/stock-items/${id}/buy-verdict`);
    expect(v.confidence).toBe('low');

    await page.goto('/#/stock');
    await page.waitForLoadState('networkidle');
    const search = page
        .locator('input[type="search"], input[placeholder*="earch" i], input[aria-label*="earch" i]')
        .first();
    await search.fill('Jasmine Rice');
    const row = page.locator('[class*="stock-row"]').filter({ hasText: 'Jasmine Rice' }).first();
    // The row itself rendered (so the absence check isn't a blank page)…
    await expect(row).toBeVisible();
    // …but no verdict chip of any flavour.
    await expect(row.locator('.dora-buy-verdict-badge')).toHaveCount(0);
});

test('feature flag: toggling the oracle off hides every badge; back on restores them', async ({ page }) => {
    // P8-05 verify: Settings → Admin → System → Features. The flag rides the
    // /health features probe, which runs once per document load — each
    // full-page goto below re-reads it.
    await page.goto('/#/settings/admin/system/features');
    await page.waitForLoadState('networkidle');
    const oracleRow = page.locator('.settings-row')
        .filter({ hasText: '"Should I buy?" oracle' })
        .first();
    await oracleRow.locator('.q-toggle').click();
    await expect(toast(page, '"Should I buy?" verdicts disabled.')).toBeVisible();
    await expect
        .poll(async () => (await apiGet<{ buy_verdict_enabled: boolean }>(page, '/app-settings')).buy_verdict_enabled)
        .toBe(false);

    // Fresh document load → fresh health probe → no badges anywhere, even on
    // the fixture row that reliably yields skip/high when the oracle is on.
    await page.goto('/#/stock');
    // A hash-only goto is a same-document navigation; the enabled-flag
    // health probe runs once per document, so force a full load — the
    // verify contract is "reload Stock Overview" (no live flip; see the
    // follow-up on the settings toggle not refreshing the probe).
    await page.reload();
    await page.waitForLoadState('networkidle');
    const search = page
        .locator('input[type="search"], input[placeholder*="earch" i], input[aria-label*="earch" i]')
        .first();
    await search.fill(FIXTURE_NAME);
    const row = page.locator('[class*="stock-row"]').filter({ hasText: FIXTURE_NAME }).first();
    await expect(row).toBeVisible();
    await expect(row.locator('.dora-buy-verdict-badge')).toHaveCount(0);

    // Toggle back on → the badge returns on the same row.
    await page.goto('/#/settings/admin/system/features');
    await page.waitForLoadState('networkidle');
    const rowAgain = page.locator('.settings-row')
        .filter({ hasText: '"Should I buy?" oracle' })
        .first();
    await rowAgain.locator('.q-toggle').click();
    await expect(toast(page, '"Should I buy?" verdicts enabled.')).toBeVisible();

    await page.goto('/#/stock');
    // A hash-only goto is a same-document navigation; the enabled-flag
    // health probe runs once per document, so force a full load — the
    // verify contract is "reload Stock Overview" (no live flip; see the
    // follow-up on the settings toggle not refreshing the probe).
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page
        .locator('input[type="search"], input[placeholder*="earch" i], input[aria-label*="earch" i]')
        .first()
        .fill(FIXTURE_NAME);
    const restoredRow = page.locator('[class*="stock-row"]').filter({ hasText: FIXTURE_NAME }).first();
    await expect(restoredRow.getByText('Skip', { exact: true })).toBeVisible();
});
