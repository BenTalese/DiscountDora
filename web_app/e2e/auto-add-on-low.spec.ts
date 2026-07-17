import { type Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { apiGet, apiMutate, toast } from './helpers';

// Batch 3 — Auto-add-on-low (FU-315/464/511, DORA_VERIFY L838–870). The
// install-wide `auto_add_mode` (Settings → Admin → System → Stock) decides
// whether a Stocked→Low/Out transition silently drops the item onto the one
// unambiguous DRAFT list, with an undoable toast + an `auto: low stock` line
// chip. The branching *matrix* (off/essential/all × dedup × draft-count) is
// server-owned pure logic (R-003) — see the follow-up logged for its missing
// backend coverage; this spec pins only the two UI seams the owner has to eye:
// (1) the settings dial loads/saves/persists, and (2) the `all`-mode happy
// path fires the toast and renders the line chip on the target list.
//
// State: uses the seed's Jasmine Rice (Stocked, on no list, untouched by other
// specs) and the sole seeded draft "This week". The happy-path test restores
// via the API (delete the auto line, reset the level), and an afterAll safety
// net re-asserts the clean state (mode back to the seeded `essential_only`,
// no lingering auto line, item Stocked) so nothing leaks into later specs.
test.describe.configure({ mode: 'serial' });

const SETTINGS_PAGE = '/#/settings/admin/system/stock';
const ITEM = 'Jasmine Rice';

type AutoAddMode = 'off' | 'essential_only' | 'all';
type AppSettings = { auto_add_mode: AutoAddMode };
type StockItem = { stock_item_id: string; name: string; stock_level_id: string };
type StockLevel = { stock_level_id: string; name: string; sequence: number };
type ListSummary = { shopping_list_id: string; display_name: string; status: string };
type ListLine = { stock_item_id: string | null; added_via: string };
type ListDetail = { display_name: string; status: string; lines: ListLine[] };

const settings = (page: Page) => apiGet<AppSettings>(page, '/app-settings');

async function itemByName(page: Page, name: string): Promise<StockItem> {
    const { items } = await apiGet<{ items: StockItem[] }>(page, '/stock-items?limit=500');
    const it = items.find((i) => i.name === name);
    expect(it, `seed item "${name}" exists`).toBeTruthy();
    return it!;
}

async function levelByName(page: Page, name: string): Promise<StockLevel> {
    const { items } = await apiGet<{ items: StockLevel[] }>(page, '/stock-levels?limit=50');
    const lvl = items.find((l) => l.name === name);
    expect(lvl, `stock level "${name}" exists`).toBeTruthy();
    return lvl!;
}

async function draftList(page: Page): Promise<ListSummary> {
    const lists = await apiGet<ListSummary[]>(page, '/shopping-lists');
    const drafts = lists.filter((l) => l.status === 'draft');
    expect(drafts, 'exactly one draft list (the unambiguous auto-add target)').toHaveLength(1);
    return drafts[0]!;
}

async function lineFor(page: Page, listId: string, itemId: string): Promise<ListLine | undefined> {
    const detail = await apiGet<ListDetail>(page, `/shopping-lists/${listId}`);
    return detail.lines.find((l) => l.stock_item_id === itemId);
}

// Hard-reset via the API so nothing leaks even if a test above bailed mid-flow.
test.afterAll(async ({ browser }) => {
    const context = await browser.newContext({ storageState: 'e2e/.auth/user.json' });
    const page = await context.newPage();
    try {
        const item = await itemByName(page, ITEM);
        const list = await draftList(page);
        if (await lineFor(page, list.shopping_list_id, item.stock_item_id)) {
            await apiMutate(page, 'delete',
                `/shopping-lists/${list.shopping_list_id}/lines/by-stock-item/${item.stock_item_id}`);
        }
        const stocked = await levelByName(page, 'Stocked');
        if (item.stock_level_id !== stocked.stock_level_id) {
            await apiMutate(page, 'patch', `/stock-items/${item.stock_item_id}`, {
                stock_level_id: stocked.stock_level_id,
            });
        }
        if ((await settings(page)).auto_add_mode !== 'essential_only') {
            await apiMutate(page, 'patch', '/app-settings', { auto_add_mode: 'essential_only' });
        }
    } finally {
        await context.close();
    }
});

test('the Auto-add mode dial loads, saves each state, and persists across reload', async ({ page }) => {
    await page.goto(SETTINGS_PAGE);
    // Seed default is Essential only; the three-way dial renders all options.
    expect((await settings(page)).auto_add_mode).toBe('essential_only');
    await expect(page.getByRole('button', { name: 'Off' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Essential only' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'All items' })).toBeVisible();

    // Saves eagerly on change (no Save button) with a confirmation toast.
    await page.getByRole('button', { name: 'All items' }).click();
    await expect(toast(page, 'Auto-add mode saved.')).toBeVisible();
    await expect.poll(async () => (await settings(page)).auto_add_mode).toBe('all');

    // Survives a reload: the page re-fetches on mount and still reads `all`.
    await page.reload();
    expect((await settings(page)).auto_add_mode).toBe('all');

    // A second state change persists too, then restore the seeded default.
    await page.getByRole('button', { name: 'Off' }).click();
    await expect.poll(async () => (await settings(page)).auto_add_mode).toBe('off');
    await page.getByRole('button', { name: 'Essential only' }).click();
    await expect.poll(async () => (await settings(page)).auto_add_mode).toBe('essential_only');
});

test('an `all`-mode level drop auto-adds to the draft list with a toast + line chip', async ({ page }) => {
    const item = await itemByName(page, ITEM);
    const list = await draftList(page);
    // Precondition: mode = all, item Stocked, not already on the target list.
    await apiMutate(page, 'patch', '/app-settings', { auto_add_mode: 'all' });
    expect(await lineFor(page, list.shopping_list_id, item.stock_item_id),
        'item starts off the draft list').toBeUndefined();

    // Drop the level Stocked → Low Stock via the row's level menu.
    await page.goto('/#/stock');
    await page.waitForLoadState('networkidle');
    const row = page.locator('.stock-row').filter({ hasText: ITEM });
    await row.getByRole('button', { name: 'Stock level: Stocked' }).click();
    await page.getByRole('listitem').filter({ hasText: 'Low Stock' }).click();

    // The auto-add fires an undoable toast naming the item + the target list.
    await expect(toast(page, `Added ${ITEM} to ${list.display_name}.`)).toBeVisible();
    await expect(toast(page, 'Auto-added because it went low.')).toBeVisible();

    // Server truth: the item now sits on the draft list, tagged auto_low_stock.
    await expect
        .poll(async () => (await lineFor(page, list.shopping_list_id, item.stock_item_id))?.added_via)
        .toBe('auto_low_stock');

    // The list-detail render shows the provenance chip on that line.
    await page.goto(`/#/shopping-lists/${list.shopping_list_id}`);
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('auto: low stock').first()).toBeVisible();

    // Restore: pull the auto line + put the item back to Stocked.
    await apiMutate(page, 'delete',
        `/shopping-lists/${list.shopping_list_id}/lines/by-stock-item/${item.stock_item_id}`);
    const stocked = await levelByName(page, 'Stocked');
    await apiMutate(page, 'patch', `/stock-items/${item.stock_item_id}`, {
        stock_level_id: stocked.stock_level_id,
    });
    await apiMutate(page, 'patch', '/app-settings', { auto_add_mode: 'essential_only' });
});

test('the retired per-item auto-add UI stays gone (filter chip, footer count, detail toggle)', async ({ page }) => {
    // L856/857 — the per-item `auto_add_when_low` toggle was collapsed into the
    // install-wide mode (FU-511). Guard against its UI creeping back: the stock
    // overview must not show a "Will auto-add on low" filter chip or an
    // "Auto-add" footer count, and the detail page must not show an "Auto-add
    // when low" toggle row (the Essential flag is what survives).
    await page.goto('/#/stock');
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: 'Filters' }).click();
    // Sanity: surviving controls render (so the absence checks aren't a blank page).
    await expect(page.getByText('Essential', { exact: true }).first()).toBeVisible();
    await expect(page.getByText(/Will auto-add on low/i)).toHaveCount(0);
    await expect(page.getByText('Auto-add', { exact: true })).toHaveCount(0);

    const item = await itemByName(page, ITEM);
    await page.goto(`/#/stock/${item.stock_item_id}`);
    await page.waitForLoadState('networkidle');
    // Sanity: the detail page rendered for this item.
    await expect(page.getByText(ITEM).first()).toBeVisible();
    await expect(page.getByText(/Auto-add/i)).toHaveCount(0);
});
