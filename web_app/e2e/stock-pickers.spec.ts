import { test, expect } from './fixtures';
import { apiGet, apiMutate } from './helpers';

// Stock pickers (2026-06-30 feedback, verify-campaign Batch 3). The dot
// *styling* consistency across the three level pickers is a one-time visual;
// these tests pin the behavioural halves: the detail-page Level row actually
// saves (dropdown pick → "Updated just now" stamp → server truth) and the
// overview level filter's set→clear cycle survives without console noise
// (the cleared trigger falls back to the sunken dot instead of blowing up on
// an undefined sequence).

test('detail Level row: pick → "Updated just now" → server truth (throwaway item)', async ({ page }) => {
    await page.goto('/#/');
    const levels = await apiGet<{ items: { stock_level_id: string; name: string; sequence: number }[] }>(
        page, '/stock-levels?limit=50',
    );
    const stocked = levels.items.find((l) => l.name === 'Stocked')!;
    const low = levels.items.find((l) => l.name === 'Low Stock')!;
    expect(stocked && low, 'seeded canonical levels exist').toBeTruthy();

    // Throwaway item so the walk can't trip auto-add or another spec's seed
    // state (created Stocked, not Essential, on no list).
    const created = await apiMutate(page, 'post', '/stock-items', {
        name: `e2e level picker ${Date.now()}`,
        stock_level_id: stocked.stock_level_id,
    });
    const id = ((await created.json()) as { stock_item_id: string }).stock_item_id;
    try {
        await page.goto(`/#/stock/${id}`);
        await page.waitForLoadState('networkidle');

        // The Level row dropdown (BaseDropdown, accessible name "Expand")
        // shows the current level; pick Low Stock.
        await page.getByRole('button', { name: 'Expand' }).filter({ hasText: 'Stocked' }).click();
        await page.getByRole('listitem').filter({ hasText: 'Low Stock' }).click();

        // The stamp flips to "just now" and the trigger re-labels.
        await expect(page.getByText('Updated just now')).toBeVisible();
        await expect(
            page.getByRole('button', { name: 'Expand' }).filter({ hasText: 'Low Stock' }),
        ).toBeVisible();

        // Server truth.
        await expect.poll(async () => {
            const data = await apiGet<{ items: { stock_item_id: string; stock_level_id: string }[] }>(
                page, '/stock-items?limit=500',
            );
            return data.items.find((i) => i.stock_item_id === id)?.stock_level_id;
        }).toBe(low.stock_level_id);
    } finally {
        await apiMutate(page, 'delete', `/stock-items/${id}`);
    }
});

test('overview level filter: set → clear round-trip stays console-clean with the fallback trigger', async ({ page }) => {
    const noise: string[] = [];
    page.on('console', (m) => {
        if (m.type() === 'warning' || m.type() === 'error') noise.push(`${m.type()}: ${m.text()}`);
    });
    page.on('pageerror', (e) => noise.push(`pageerror: ${e.message}`));

    await page.goto('/#/stock');
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: 'Filters' }).click();

    const allRows = await page.locator('.stock-row').count();
    expect(allRows).toBeGreaterThan(0);

    // Pick a level → the list narrows.
    const levelSelect = page.locator('.q-select').filter({ hasText: 'Any level' }).first();
    await levelSelect.click();
    await page.getByRole('option').filter({ hasText: 'Low Stock' }).click();
    await expect.poll(() => page.locator('.stock-row').count()).toBeLessThan(allRows);

    // Clear it via the select's × → full list back, trigger falls back to
    // the muted "Any level" state without slot/sequence errors.
    await levelSelect.locator('.q-field__focusable-action').first().click();
    await expect.poll(() => page.locator('.stock-row').count()).toBe(allRows);
    await expect(levelSelect.getByText('Any level')).toBeVisible();

    expect(noise, `console noise during the filter round-trip:\n${noise.join('\n')}`).toHaveLength(0);
});
