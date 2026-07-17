import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, toast } from './helpers';

// Batch 2 — Stocktake redesign Chunk 3 Settings (PROPOSAL_STOCKTAKE_MODE §8).
// Pins the two global stocktake dials on Settings → Admin → System →
// Stocktake: the default cadence band + Auto self-tuning. Both save eagerly
// (no Save button), so the regression-worthy seam is: tap → toast → the PATCH
// persists across a reload. Asserted against server truth (/app-settings) so
// the pins don't hinge on Quasar's active-button styling.
//
// Self-restoring: every test ends at the seeded defaults (Fortnightly + Auto
// on) so this file does NOT perturb the overdue queue that stocktake.spec.ts
// relies on (it sorts before stocktake.spec.ts and runs first).
test.describe.configure({ mode: 'serial' });

const PAGE = '/#/settings/admin/system/stocktake';

type AppSettings = {
    stocktake_default_cadence_band: string;
    stocktake_auto_tuning_enabled: boolean;
};
const settings = (page: Page) => apiGet<AppSettings>(page, '/app-settings');

test('page loads with the three cadence bands; server default is Fortnightly', async ({ page }) => {
    await page.goto(PAGE);
    await expect(
        page.getByText(/How often Dora asks you to check each item/),
    ).toBeVisible();
    for (const band of ['Weekly', 'Fortnightly', 'Monthly']) {
        await expect(page.getByRole('button', { name: band })).toBeVisible();
    }
    expect((await settings(page)).stocktake_default_cadence_band).toBe('fortnightly');
});

test('changing the cadence toasts and persists across a reload, then restores', async ({ page }) => {
    await page.goto(PAGE);

    await page.getByRole('button', { name: 'Weekly' }).click();
    await expect(toast(page, 'Default cadence saved.')).toBeVisible();
    await expect
        .poll(async () => (await settings(page)).stocktake_default_cadence_band)
        .toBe('weekly');

    // Reload → the page re-fetches on mount and still reads the new value.
    await page.reload();
    await expect(page.getByRole('button', { name: 'Weekly' })).toBeVisible();
    expect((await settings(page)).stocktake_default_cadence_band).toBe('weekly');

    // Restore the seeded default so the stocktake queue stays deterministic.
    await page.getByRole('button', { name: 'Fortnightly' }).click();
    await expect
        .poll(async () => (await settings(page)).stocktake_default_cadence_band)
        .toBe('fortnightly');
});

test('Auto self-tuning toggles with the right toast copy, persists, then restores', async ({ page }) => {
    await page.goto(PAGE);

    // On by default → flip off.
    await page.locator('.q-toggle').first().click();
    await expect(toast(page, 'Auto self-tuning off.')).toBeVisible();
    await expect
        .poll(async () => (await settings(page)).stocktake_auto_tuning_enabled)
        .toBe(false);

    await page.reload();
    expect((await settings(page)).stocktake_auto_tuning_enabled).toBe(false);

    // Flip back on (= the seeded default).
    await page.locator('.q-toggle').first().click();
    await expect(toast(page, 'Auto self-tuning on.')).toBeVisible();
    await expect
        .poll(async () => (await settings(page)).stocktake_auto_tuning_enabled)
        .toBe(true);
});
