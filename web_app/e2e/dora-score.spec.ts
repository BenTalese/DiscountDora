import { test, expect } from './fixtures';
import { apiGet } from './helpers';

// P8-08 — the Dashboard "Kitchen health" (Dora Score) card (verify-campaign
// Dashboard batch). The scoring engine is unit-pinned (test_dora_score.py: 8
// suites over composite/components/trend/windows) and the endpoint shape +
// anonymous-401 are backend-pinned (test_dashboard_router.py, DTO snapshot,
// route-auth sweep). These tests pin the UI seams: hero + ordered component
// rows against server truth, the dormant-component render (seed has no budget
// → Budget row must show "—", dim, and NOT drag the composite), the action
// links, and the Cards-menu visibility toggle.
//
// Known + deliberate: the Waste row has NO action link (the /waste page was
// dissolved — PROPOSAL_WASTE_MINIMISATION D10); pinned as an absence so a dead
// link can't creep back. Known gap (FU-583): the Freshness/Stocktake links
// carry ?expiring=1 / ?stocktake=1 but StockOverview only honours
// location_id/attention/level_id/create/recipe — the params are silently
// ignored, so these tests assert navigation only, not filtering.
//
// Read-only on shared seed state; serial only to keep dashboard navigation
// deterministic.
test.describe.configure({ mode: 'serial' });

const CARD_TITLE = 'Kitchen health';

interface DoraScoreDto {
    composite: number | null;
    trend_delta: number | null;
    trend_direction: string;
    window_days: number;
    components: { key: string; label: string; score: number | null; reason: string }[];
}

test('hero + five ordered component rows render server truth; Budget is dormant, not zeroed', async ({ page }) => {
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: CARD_TITLE })).toBeVisible();

    const server = await apiGet<DoraScoreDto>(page, '/dashboard/dora-score');

    // Seeded install has activity, so the composite is a real number — and the
    // hero renders exactly it, with the honest caption.
    expect(server.composite).not.toBeNull();
    await expect(page.locator('.dora-score-hero__number')).toHaveText(String(server.composite));
    await expect(page.getByText('out of 100')).toBeVisible();
    // "last 30 days" also appears inside component reasons — scope to the hero.
    await expect(
        page.locator('.dora-score-hero__caption').getByText(`last ${server.window_days} days`),
    ).toBeVisible();

    // Five components, in the server's canonical order.
    expect(server.components.map((c) => c.key)).toEqual([
        'waste', 'budget', 'freshness', 'runouts', 'stocktake',
    ]);
    await expect(page.locator('.dora-score-component__label')).toHaveText(
        server.components.map((c) => c.label),
    );

    // Dormant contract on real data: the seed sets no budget, so Budget is
    // score=null server-side and the row renders "—" + dormant styling with
    // no mini-bar — while the composite stays a number (excluded, not zeroed).
    const budget = server.components.find((c) => c.key === 'budget');
    expect(budget?.score, 'seed precondition: no budget configured').toBeNull();
    const budgetRow = page
        .locator('.dora-score-component--dormant')
        .filter({ hasText: budget!.label });
    await expect(budgetRow).toHaveCount(1);
    await expect(budgetRow.locator('.dora-score-component__score')).toHaveText('—');
    await expect(budgetRow.locator('.dora-score-component__bar')).toHaveCount(0);

    // Every non-dormant row carries a filled mini-bar and a server reason.
    for (const c of server.components) {
        const row = page.locator('.dora-score-component').filter({ hasText: c.label });
        await expect(row.locator('.dora-score-component__reason')).toHaveText(c.reason);
        if (c.score !== null) {
            await expect(row.locator('.dora-score-component__bar-fill')).toHaveCount(1);
        }
    }

    // Placement: Kitchen health sits above the Pantry card in the kitchen zone.
    const khBox = await page.getByRole('heading', { name: CARD_TITLE }).boundingBox();
    const pantryBox = await page.getByRole('heading', { name: 'Pantry' }).boundingBox();
    expect(khBox && pantryBox && khBox.y < pantryBox.y).toBe(true);
});

test('component action links navigate; Waste deliberately has none', async ({ page }) => {
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');

    const row = (label: string) =>
        page.locator('.dora-score-component').filter({ hasText: label });

    // Waste: reason renders, but no action link (the /waste page was dissolved).
    await expect(row('Waste').locator('.dora-score-component__action')).toHaveCount(0);

    const cases = [
        { rowLabel: 'Budget', link: 'Set a budget', url: /settings\/preferences/ },
        { rowLabel: 'Freshness', link: 'Expiring items', url: /stock\?expiring=1/ },
        { rowLabel: 'Run-outs', link: 'Shopping lists', url: /shopping-lists/ },
        { rowLabel: 'Stocktake', link: 'Do a stocktake', url: /stock\?stocktake=1/ },
    ];
    for (const c of cases) {
        await page.goto('/#/');
        await page.waitForLoadState('networkidle');
        await row(c.rowLabel).getByText(c.link).click();
        await page.waitForURL(c.url);
        // Landed on a real page, not the 404.
        await expect(page.getByText('This page wandered off')).toHaveCount(0);
    }
});

test('the Cards menu hides and restores the card', async ({ page }) => {
    await page.goto('/#/');
    await page.waitForLoadState('networkidle');
    const cardOnPage = page.getByRole('heading', { name: CARD_TITLE });
    await expect(cardOnPage).toBeVisible();

    // Visibility is the row's q-toggle, not the label (same seam as the
    // draft-shop spec).
    const menuRow = () => page.locator('.q-menu .q-item').filter({ hasText: CARD_TITLE });
    await page.getByRole('button', { name: 'Cards' }).click();
    await menuRow().locator('.q-toggle').click();
    await page.keyboard.press('Escape');
    await expect(cardOnPage).toHaveCount(0);

    await page.getByRole('button', { name: 'Cards' }).click();
    await menuRow().locator('.q-toggle').click();
    await page.keyboard.press('Escape');
    await expect(cardOnPage).toBeVisible();
});
