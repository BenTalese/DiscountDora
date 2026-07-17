import { test, expect } from './fixtures';

// Batch 2 — Stocktake redesign Chunk 2 runner (PROPOSAL_STOCKTAKE_MODE).
// Small first slice: the mainline "Still correct" walk — no landing page,
// legacy redirect, advance-through-queue, and the completion summary. The
// other four verbs (Change level / Skip / Push / Mute) + add-to-list are a
// later slice. Curated seed (bulk=0) yields a few deterministic overdue
// items, so the queue is non-empty on a fresh e2e DB.
//
// Consumes the stocktake queue (Still-correct resets each item's clock), so
// run last-ish; nothing else asserts on the queue.
test.describe.configure({ mode: 'serial' });

test('legacy /stocktake/run redirects to /stocktake', async ({ page }) => {
    await page.goto('/#/stocktake/run');
    await expect(page).toHaveURL(/#\/stocktake$/);
});

test('runner opens straight on the first item — no landing page', async ({ page }) => {
    await page.goto('/#/stocktake');
    // The item card shows the cadence/overdue caption + the mainline button;
    // there is no intermediate "N items need a check" landing.
    await expect(page.getByText(/day(s)? overdue/i).first()).toBeVisible();
    await expect(page.getByRole('button', { name: 'Still correct' })).toBeVisible();
    // The change-level button is tinted to the current level and labelled with
    // the level name + "(change)" — assert that shape, not a static label.
    await expect(page.getByRole('button', { name: /\(change\)/ })).toBeVisible();
    // The retired keyboard-shortcut hints / "Out of stock" button are gone.
    await expect(page.getByRole('button', { name: /^Out of stock$/ })).toHaveCount(0);
});

test('Still correct advances through the queue to the completion summary', async ({ page }) => {
    await page.goto('/#/stocktake');
    // Wait for the runner to actually mount before walking (goto resolves
    // before the async queue fetch paints the first card).
    await expect(page.getByRole('button', { name: 'Still correct' })).toBeVisible();

    let checked = 0;
    // Walk the whole queue with the mainline verb. Guard the loop.
    for (let i = 0; i < 30; i++) {
        const stillCorrect = page.getByRole('button', { name: 'Still correct' });
        if (await stillCorrect.count() === 0) break; // reached completion
        await stillCorrect.click();
        checked++;
        // Either the next item's button re-appears, or the summary lands.
        await page.waitForTimeout(200);
    }

    expect(checked, 'queue had at least one overdue item').toBeGreaterThan(0);

    // Completion summary: the "checked" counter reflects the walk.
    await expect(page.getByText('checked')).toBeVisible();
    await expect(page.getByText('Done')).toBeVisible();

    // Done returns to Stock.
    await page.getByText('Done').click();
    await expect(page).toHaveURL(/#\/stock$/);
});

test('re-entering the runner after clearing the queue shows the caught-up card', async ({ page }) => {
    // The previous test Still-corrected every overdue item, so the queue is
    // now empty for this fresh-DB run.
    await page.goto('/#/stocktake');
    await expect(page.getByText("You're all caught up.")).toBeVisible();
    await expect(page.getByRole('link', { name: 'Back to Stock' })).toBeVisible();
});
