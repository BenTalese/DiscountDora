import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, toast } from './helpers';

// Batch 2 — Stocktake redesign Chunk 3 (PROPOSAL_STOCKTAKE_MODE §7).
// Pins the *clean removal* of the old "Default stocktake reminder" dial from
// Settings → Admin → System → Alert thresholds: that numeric-days section is
// superseded by the cadence-band system (which now lives on the dedicated
// Settings → Stocktake page, pinned by stocktake-settings.spec.ts). The only
// dial that survives on this page is "Expiring-soon window", so this file
// guards two seams: (1) the stocktake-reminder input is gone, and (2) the
// surviving window still edits + saves (regression check).
//
// Self-restoring: the edit test ends back at the seeded default (7 days) so it
// doesn't perturb expiring-soon behaviour for any other spec. The input saves
// eagerly on blur (no Save button), so we assert against server truth
// (/app-settings) rather than DOM state.
test.describe.configure({ mode: 'serial' });

const PAGE = '/#/settings/admin/system/alerts';

type AppSettings = { expiring_soon_window_days: number };
const settings = (page: Page) => apiGet<AppSettings>(page, '/app-settings');

const daysInput = (page: Page) =>
    page.locator('input[type="number"]').first();

test('the old "Default stocktake reminder" section is gone; only the window remains', async ({ page }) => {
    await page.goto(PAGE);
    await expect(page.getByText('Expiring-soon window')).toBeVisible();

    // The stocktake-reminder dial was pulled entirely — no copy, no input for it.
    await expect(page.getByText(/stocktake reminder/i)).toHaveCount(0);
    // Exactly one numeric dial survives on the page (the window's Days input).
    await expect(page.locator('input[type="number"]')).toHaveCount(1);
});

test('the Expiring-soon window still edits + saves + persists, then restores', async ({ page }) => {
    await page.goto(PAGE);
    expect((await settings(page)).expiring_soon_window_days).toBe(7);

    // Edit → blur triggers the eager save.
    await daysInput(page).fill('10');
    await daysInput(page).blur();
    await expect(toast(page, 'Alert thresholds saved.')).toBeVisible();
    await expect
        .poll(async () => (await settings(page)).expiring_soon_window_days)
        .toBe(10);

    // Reload → the page re-fetches on mount and still reads the new value.
    await page.reload();
    await expect(daysInput(page)).toHaveValue('10');
    expect((await settings(page)).expiring_soon_window_days).toBe(10);

    // Restore the seeded default so expiring-soon stays deterministic elsewhere.
    await daysInput(page).fill('7');
    await daysInput(page).blur();
    await expect
        .poll(async () => (await settings(page)).expiring_soon_window_days)
        .toBe(7);
});
