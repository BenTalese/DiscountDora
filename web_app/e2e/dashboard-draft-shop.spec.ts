import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, apiMutate, toast } from './helpers';

// FU-351 — the Dashboard "Draft this week's shop" card (verify-campaign
// Dashboard batch). Server halves are backend-pinned (provenance priority in
// test_auto_generate_priority.py; unit-of-work commit; the zero-candidate
// no-phantom-list defer + explicit-name contract in
// test_auto_generate_draft_shop.py). These tests pin the UI seams: the card
// render, the one-click happy path (toast → navigate → named draft with
// provenance chips), and the Cards-menu visibility toggle.
//
// The happy path creates a real second draft — deleted in the test and again
// by an afterAll safety net (any "Weekly shop ·" list), so the sole-draft
// assumption other specs rely on holds.
test.describe.configure({ mode: 'serial' });

const CARD_TITLE = "Draft this week's shop";

async function deleteWeeklyShopLists(page: Page): Promise<void> {
    const lists = await apiGet<{ shopping_list_id: string; display_name: string }[]>(
        page, '/shopping-lists',
    );
    for (const l of lists) {
        if (l.display_name.startsWith('Weekly shop ·')) {
            await apiMutate(page, 'delete', `/shopping-lists/${l.shopping_list_id}`);
        }
    }
}

test.afterAll(async ({ browser }) => {
    const context = await browser.newContext({ storageState: 'e2e/.auth/user.json' });
    const page = await context.newPage();
    try {
        await deleteWeeklyShopLists(page);
    } finally {
        await context.close();
    }
});

test('one click drafts the week: toast → navigate → named draft with provenance chips', async ({ page }) => {
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');

    // The card sits in the act zone with its blurb + button.
    await expect(page.getByText(CARD_TITLE)).toBeVisible();
    await expect(page.getByText(/One-click starter list/)).toBeVisible();
    const button = page.getByRole('button', { name: 'Draft my shop' });
    await expect(button).toBeVisible();

    await button.click();

    // Seeded install always has candidates (meal plan + low/out + essentials).
    await expect(toast(page, /Drafted \d+ items?\./)).toBeVisible();
    await expect(toast(page, 'Review the list, then start shopping when ready.')).toBeVisible();

    // Navigated to the new draft, named for intent (not "Auto N · date").
    await page.waitForURL(/shopping-lists\/[0-9a-f-]+/);
    // `.first()` can land on a hidden sidebar node — assert a *visible* one.
    await expect(page.getByText(/Weekly shop · /).locator('visible=true').first()).toBeVisible();

    // Server-ranked provenance renders as added_via chips on the lines.
    await expect(page.getByText(/auto: /).first()).toBeVisible();

    // Restore the sole-draft world.
    await deleteWeeklyShopLists(page);
});

test('the Cards menu hides and restores the card', async ({ page }) => {
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');
    // The card renders its title as a heading; the Cards-menu item reuses
    // the same text but is not a heading — scope on the role.
    const cardOnPage = page.getByRole('heading', { name: CARD_TITLE });
    await expect(cardOnPage).toBeVisible();

    // Visibility is the row's q-toggle, not the label.
    const menuRow = () => page.locator('.q-menu .q-item').filter({ hasText: CARD_TITLE });
    await page.getByRole('button', { name: 'Cards' }).click();
    await menuRow().locator('.q-toggle').click();
    await page.keyboard.press('Escape');
    await expect(cardOnPage).toHaveCount(0);

    // Toggle back on.
    await page.getByRole('button', { name: 'Cards' }).click();
    await menuRow().locator('.q-toggle').click();
    await page.keyboard.press('Escape');
    await expect(cardOnPage).toBeVisible();
});
