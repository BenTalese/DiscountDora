import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';

// Batch 2 — Stocktake redesign Chunk 2 runner (PROPOSAL_STOCKTAKE_MODE).
// Covers the whole runner: no landing page, legacy redirect, the (?) help
// dialog, all five verbs (Still correct / Change level / Skip / Push / Mute),
// the five-counter completion summary, and the SK-7 batch add-to-list prompt.
//
// The curated seed (bulk=0) yields exactly four alerts-enabled overdue items
// (Vanilla Ice Cream, Brazil Nuts, Hot Crispy Chippies, Broccoli — see
// seed.py), so the verb-walk below is fully deterministic on a fresh e2e DB.
// It uses each verb once and drains the queue, so it must run before the
// caught-up test and nothing else may assert on the queue.
test.describe.configure({ mode: 'serial' });

const itemName = (page: Page) => page.locator('.runner-card .text-h5');

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

test('(?) help dialog explains all five verbs', async ({ page }) => {
    await page.goto('/#/stocktake');
    await expect(page.getByRole('button', { name: 'Still correct' })).toBeVisible();

    await page.getByRole('button', { name: 'How stocktake works' }).click();
    const dialog = page.locator('.q-dialog');
    await expect(dialog.getByText('How stocktake works')).toBeVisible();
    // The five verbs each get a definition term.
    for (const verb of ['Still correct', 'Change level', 'Skip', 'Push 3 days', 'Mute']) {
        await expect(dialog.locator('dt', { hasText: verb })).toBeVisible();
    }
});

test('verb-walk: Skip / Change / Push / Mute / Still-correct drains the queue and tallies the summary', async ({ page }) => {
    await page.goto('/#/stocktake');
    // goto resolves before the async queue fetch paints the first card.
    await expect(page.getByRole('button', { name: 'Still correct' })).toBeVisible();

    // ── Skip (session-only): the item drops to the end of the queue, no
    // API call. Assert we advanced to a different item. ──
    const firstItem = await itemName(page).textContent();
    await page.getByRole('button', { name: 'Skip' }).click();
    await expect(itemName(page)).not.toHaveText(firstItem ?? '');

    // ── Change level → Out of Stock: resets the clock (removed from the
    // overdue queue) and, because Out is restockable, feeds the SK-7
    // batch add-to-list prompt on the completion screen. ──
    await page.getByRole('button', { name: /\(change\)/ }).click();
    const picker = page.locator('.q-dialog');
    await expect(picker.getByText('Set level')).toBeVisible();
    await picker.getByRole('listitem').filter({ hasText: 'Out of Stock' }).click();
    // Advanced past the changed item.
    await expect(page.getByRole('button', { name: 'Still correct' })).toBeVisible();

    // ── Push 3 days: snoozes the item (no last_checked bump), advances. ──
    await page.getByRole('button', { name: 'Push 3 days' }).click();
    await expect(page.getByRole('button', { name: 'Still correct' })).toBeVisible();

    // ── Mute: nuclear, always confirms. The card's Mute button opens a
    // Quasar confirm dialog whose OK is also labelled "Mute". ──
    await page.getByRole('button', { name: 'Mute' }).click();
    const muteConfirm = page.locator('.q-dialog');
    await expect(muteConfirm.getByText(/^Mute .+\?$/)).toBeVisible();
    await muteConfirm.getByRole('button', { name: 'Mute' }).click();

    // ── The Skipped item was re-queued at the end; Still-correct it to
    // reach the completion summary. ──
    await expect(itemName(page)).toHaveText(firstItem ?? '');
    await page.getByRole('button', { name: 'Still correct' }).click();

    // ── Completion summary: each verb fired exactly once. ──
    await expect(page.getByText('Stocktake complete')).toBeVisible();
    const row = (label: string) =>
        page.locator('.runner-summary__row').filter({ hasText: label });
    for (const label of ['checked', 'changed', 'skipped', 'pushed', 'muted']) {
        await expect(row(label).locator('.runner-summary__count')).toHaveText('1');
    }

    // ── SK-7 batch add-to-list: one item went Out, so the prompt offers to
    // add it to an active list ("This week" is seeded). ──
    await expect(page.getByText(/1 item went Low or Out/)).toBeVisible();
    await page.getByRole('button', { name: /Add to list/ }).click();
    const listPick = page.locator('.q-dialog');
    await expect(listPick.getByText('Add to which list?')).toBeVisible();
    await listPick.getByRole('button', { name: 'OK' }).click();
    await expect(page.getByText('Added.')).toBeVisible();

    // Done returns to Stock.
    await page.getByRole('link', { name: 'Done' }).click();
    await expect(page).toHaveURL(/#\/stock$/);
});

test('re-entering the runner after clearing the queue shows the caught-up card', async ({ page }) => {
    // The verb-walk dispositioned every overdue item (checked / changed /
    // pushed / muted), so the queue is now empty for this fresh-DB run.
    await page.goto('/#/stocktake');
    await expect(page.getByText("You're all caught up.")).toBeVisible();
    await expect(page.getByRole('link', { name: 'Back to Stock' })).toBeVisible();
});
