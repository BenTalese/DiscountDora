import { test, expect } from './fixtures';

// Regression pins for the password policy (FU-442) + the hint-copy
// regression it later suffered (FU-568, dropped in the C-19 auth-shell
// rebuild and restored 2026-07-17). Verified manually in the Batch-0
// verify campaign; codified so a future rebuild can't silently drop
// them again.
//
// The set-time-only rule ("pre-policy short passwords still log in") is
// pinned implicitly by auth.setup.ts — the whole suite logs in as the
// seeded 4-char `dora`/`dora` admin.

const HINT = 'At least 8 characters — a passphrase works well.';

// These specs exercise the unauthenticated register/login forms, so start
// from a clean session rather than the saved admin state.
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('register-form password policy', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.getByRole('button', { name: /need an account\? register/i }).click();
    });

    test('shows the passphrase hint (FU-568 pin)', async ({ page }) => {
        await expect(page.getByText(HINT)).toBeVisible();
    });

    test('rejects a short password with an inline message', async ({ page }) => {
        await page.locator('input[autocomplete="username"]').fill(`qa-short-${Date.now()}`);
        await page.locator('input[autocomplete="new-password"]').fill('abc123');
        await page.getByRole('button', { name: /create account/i }).click();

        await expect(page.getByText(/at least 8 characters/i).first()).toBeVisible();
        // Still on the register form — no account was created.
        await expect(page.getByRole('button', { name: /create account/i })).toBeVisible();
    });

    test('rejects a breach-listed password, case-insensitively', async ({ page }) => {
        await page.locator('input[autocomplete="username"]').fill(`qa-breach-${Date.now()}`);
        // Long enough to clear the length rule; fails only the breach list.
        await page.locator('input[autocomplete="new-password"]').fill('PASSWORD123');
        await page.getByRole('button', { name: /create account/i }).click();

        await expect(page.getByText(/too common|breach|often-used|commonly used/i).first())
            .toBeVisible();
        await expect(page.getByRole('button', { name: /create account/i })).toBeVisible();
    });

    test('accepts an 8+ character passphrase (no digit rule)', async ({ page }) => {
        // Letters-only, non-breached — pins "length is the only shape rule".
        await page.locator('input[autocomplete="username"]').fill(`qa-pass-${Date.now()}`);
        await page.locator('input[autocomplete="new-password"]').fill('passphrase please');
        await page.getByRole('button', { name: /create account/i }).click();

        // Registration succeeds → authenticated app shell, no register form.
        await expect(page.getByRole('button', { name: /create account/i })).toHaveCount(0);
        await expect(page.locator('.q-layout').first()).toBeVisible();
    });
});

test('reset-password page carries the passphrase hint (FU-568 pin)', async ({ page }) => {
    // The page renders (and hints) regardless of token validity — the token
    // is only checked on submit.
    await page.goto('/#/reset-password?token=e2e-probe');
    await expect(page.getByText(HINT)).toBeVisible();
});
