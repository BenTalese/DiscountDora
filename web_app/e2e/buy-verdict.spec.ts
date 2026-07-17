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

// The tests mutate and restore one shared fixture item — keep them ordered.
test.describe.configure({ mode: 'serial' });

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
