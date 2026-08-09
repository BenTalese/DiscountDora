// FU-520 workstream 1 — behavioural coverage for the pantry filter engine.
//
// `useStockFilters` owns every filter / sort / summary rule on the stock
// overview (and any future stock-item picker). The composable takes its data
// as getter functions precisely so it can be exercised with fixtures — no
// pinia, no network. The rules pinned here are the ones that silently regress:
// the "empty = off" (A4) filter contract, the Model-C needs-attention rule,
// the nulls-last expiry sort, and the footer's filtered-view counts.
//
// DETERMINISM: the clock is pinned (expiry math uses Date.now); sorting uses
// an explicit 'en' collator inside the composable, so no machine-locale drift.
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { ref } from 'vue';

import { clearAllListState } from 'src/composables/useListState';
import { useStockFilters } from 'src/composables/useStockFilters';
import type { LocationNode } from 'src/models/location';
import type { Recipe } from 'src/models/recipe';
import type { Membership } from 'src/models/shoppingList';
import type { StockGroup } from 'src/models/stockGroup';
import type { StockItem } from 'src/models/stockItem';
import type { StockLevel } from 'src/models/stockLevel';
import { vi } from 'vitest';

// Pinned "now": 2026-07-10 12:00 UTC. Expiry fixtures are offsets from this.
const NOW = new Date('2026-07-10T12:00:00.000Z');

// ── Fixtures ────────────────────────────────────────────────────────────

const LEVELS: StockLevel[] = [
    { stock_level_id: 'lv-stocked', name: 'Stocked', sequence: 0 },
    { stock_level_id: 'lv-low', name: 'Low Stock', sequence: 1 },
    { stock_level_id: 'lv-out', name: 'Out of Stock', sequence: 2 },
];

function item(overrides: Partial<StockItem> & Pick<StockItem, 'stock_item_id' | 'name'>): StockItem {
    return {
        stock_group_id: null,
        stock_level_id: 'lv-stocked',
        stock_location_id: null,
        ...overrides,
    };
}

// Six items exercising every attention tier:
//   apple  — stocked, plain                       (no alert)
//   bread  — essential + low                      (WARN alert)
//   cheese — essential + out                      (ALERT)
//   dill   — expiring in 3 days                   (WARN alert)
//   egg    — already expired                      (ALERT)
//   flour  — low but NOT essential, currently open (no alert — Model C)
const ITEMS: StockItem[] = [
    item({ stock_item_id: 'si-apple', name: 'Apple', stock_location_id: 'loc-pantry', stock_group_id: 'grp-fresh', stock_level_last_updated: '2026-07-01T00:00:00Z' }),
    item({ stock_item_id: 'si-bread', name: 'Bread', stock_level_id: 'lv-low', is_essential: true, stock_location_id: 'loc-pantry', stock_level_last_updated: '2026-07-09T00:00:00Z' }),
    item({ stock_item_id: 'si-cheese', name: 'Cheese', stock_level_id: 'lv-out', is_essential: true }),
    item({ stock_item_id: 'si-dill', name: 'Dill', expiry_date: '2026-07-13', stock_location_id: 'loc-shelf', stock_group_id: 'grp-fresh' }),
    item({ stock_item_id: 'si-egg', name: 'Egg', expiry_date: '2026-07-01' }),
    item({ stock_item_id: 'si-flour', name: 'Flour', stock_level_id: 'lv-low', is_open: true, stock_level_last_updated: '2026-07-05T00:00:00Z' }),
];

const TREE: LocationNode[] = [
    {
        location_id: 'loc-pantry',
        name: 'Pantry',
        kind: 'zone',
        parent_id: null,
        sequence: 0,
        direct_item_count: 2,
        descendant_item_count: 3,
        items: [],
        children: [
            {
                location_id: 'loc-shelf',
                name: 'Middle shelf',
                kind: 'section',
                parent_id: 'loc-pantry',
                sequence: 0,
                direct_item_count: 1,
                descendant_item_count: 1,
                items: [],
                children: [],
            },
        ],
    },
];

const GROUPS: StockGroup[] = [
    { stock_group_id: 'grp-fresh', name: 'Fresh produce' },
];

// Recipe fixture — only the fields the composable reads. The full Recipe
// type is a large DTO; building it wholesale would drown the test in noise.
const RECIPES = [
    {
        recipe_id: 'rcp-pie',
        name: 'Apple pie',
        ingredients: [
            { stock_item_id: 'si-apple' },
            { stock_item_id: 'si-egg' },
            { stock_item_id: null },
        ],
    },
] as unknown as Recipe[];

const MEMBERSHIP: Membership = {
    quick_add_target_list_id: 'list-a',
    items: [
        { stock_item_id: 'si-apple', unticked_list_ids: ['list-a'], on_quick_add_target: true },
        { stock_item_id: 'si-bread', unticked_list_ids: ['list-a', 'list-b'], on_quick_add_target: true },
    ],
};

/** Build the composable over the standard fixture set. */
function makeFilters(overrides: {
    membership?: Membership | null;
    needsCheckIds?: () => ReadonlySet<string>;
} = {}) {
    return useStockFilters({
        stockItems: () => ITEMS,
        stockLevels: () => LEVELS,
        locationTree: () => TREE,
        recipes: () => RECIPES,
        stockGroups: () => GROUPS,
        membership: () => ('membership' in overrides ? overrides.membership ?? null : MEMBERSHIP),
        ...(overrides.needsCheckIds ? { needsCheckIds: overrides.needsCheckIds } : {}),
    });
}

function names(filters: ReturnType<typeof makeFilters>): string[] {
    return filters.filteredStockItems.value.map((i) => i.name);
}

beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
    clearAllListState();
});
afterEach(() => {
    vi.useRealTimers();
});

// ── Filtering ───────────────────────────────────────────────────────────

describe('useStockFilters — filtering', () => {
    it('shows everything, name-ascending, when no filter is active', () => {
        const f = makeFilters();
        expect(names(f)).toEqual(['Apple', 'Bread', 'Cheese', 'Dill', 'Egg', 'Flour']);
        expect(f.activeFilterCount.value).toBe(0);
    });

    it('search is case-insensitive and matches ANY whitespace-separated token', () => {
        const f = makeFilters();
        f.searchText.value = '  APP   egg ';
        expect(names(f)).toEqual(['Apple', 'Egg']);
    });

    it('search with no hits yields an empty list, not an error', () => {
        const f = makeFilters();
        f.searchText.value = 'zzz';
        expect(names(f)).toEqual([]);
    });

    it('level filter: null means OFF, an id narrows to that level (A4)', () => {
        const f = makeFilters();
        expect(f.levelFilter.value).toBeNull();
        f.levelFilter.value = 'lv-low';
        expect(names(f)).toEqual(['Bread', 'Flour']);
        f.levelFilter.value = null;
        expect(names(f)).toHaveLength(6);
    });

    it('location filter matches the exact node only (no descendant roll-up)', () => {
        const f = makeFilters();
        f.locationFilter.value = 'loc-pantry';
        expect(names(f)).toEqual(['Apple', 'Bread']);
        f.locationFilter.value = 'loc-shelf';
        expect(names(f)).toEqual(['Dill']);
    });

    it('group filter narrows to the selected stock group', () => {
        const f = makeFilters();
        f.groupFilter.value = 'grp-fresh';
        expect(names(f)).toEqual(['Apple', 'Dill']);
    });

    it('essentials-only keeps just the flagged items', () => {
        const f = makeFilters();
        f.essentialsOnly.value = true;
        expect(names(f)).toEqual(['Bread', 'Cheese']);
    });

    it('open-only keeps just the currently-open items', () => {
        const f = makeFilters();
        f.openOnly.value = true;
        expect(names(f)).toEqual(['Flour']);
    });

    it('needs-attention = essential low/out OR expired OR expiring ≤7d; non-essential low stays silent (Model C)', () => {
        const f = makeFilters();
        f.hasAlertOnly.value = true;
        // Flour (low, not essential) deliberately absent.
        expect(names(f)).toEqual(['Bread', 'Cheese', 'Dill', 'Egg']);
    });

    it('needs-check matches nothing when the caller has not wired the signal', () => {
        const f = makeFilters();
        f.needsCheckOnly.value = true;
        expect(names(f)).toEqual([]);
    });

    it('needs-check narrows to the server-owned stocktake queue when wired', () => {
        const queue = ref(new Set(['si-flour', 'si-egg']));
        const f = makeFilters({ needsCheckIds: () => queue.value });
        f.needsCheckOnly.value = true;
        expect(names(f)).toEqual(['Egg', 'Flour']);
    });

    it('expiring-soon keeps items expiring ≤7d OR already expired (FU-583 freshness deep-link)', () => {
        const f = makeFilters();
        f.expiringSoonOnly.value = true;
        // Dill expires in 3 days (≤7d), Egg is already expired; nothing else
        // carries an expiry date. Non-essential and stock-level status are
        // irrelevant to this filter.
        expect(names(f)).toEqual(['Dill', 'Egg']);
        expect(f.activeFilterCount.value).toBe(1);
    });

    it('cart filter: on_list keeps items on any unticked list, off_list the rest', () => {
        const f = makeFilters();
        f.cartFilter.value = 'on_list';
        expect(names(f)).toEqual(['Apple', 'Bread']);
        f.cartFilter.value = 'off_list';
        expect(names(f)).toEqual(['Cheese', 'Dill', 'Egg', 'Flour']);
    });

    it('cart filter treats a missing membership payload as nothing-on-a-list', () => {
        const f = makeFilters({ membership: null });
        f.cartFilter.value = 'on_list';
        expect(names(f)).toEqual([]);
    });

    it('recipe filter narrows to the recipe\'s linked ingredients and exposes its name', () => {
        const f = makeFilters();
        f.recipeFilter.value = 'rcp-pie';
        expect(names(f)).toEqual(['Apple', 'Egg']);
        expect(f.recipeFilterContext.value?.name).toBe('Apple pie');
    });

    it('an orphaned recipe id silently disables the filter rather than emptying the list', () => {
        const f = makeFilters();
        f.recipeFilter.value = 'rcp-deleted';
        expect(f.recipeFilterContext.value).toBeNull();
        expect(names(f)).toHaveLength(6);
    });

    it('filters compose with AND semantics', () => {
        const f = makeFilters();
        f.levelFilter.value = 'lv-low';
        f.essentialsOnly.value = true;
        expect(names(f)).toEqual(['Bread']);
    });

    it('server-derived stock booleans win over the client sequence lookup', () => {
        // Item claims a stocked level but the server says it's low — the
        // derived boolean must drive the attention rule (R-003 contract).
        const overridden: StockItem[] = [
            item({ stock_item_id: 'si-x', name: 'X', is_essential: true, is_low_stock: true }),
        ];
        const f = useStockFilters({
            stockItems: () => overridden,
            stockLevels: () => LEVELS,
            locationTree: () => [],
            recipes: () => [],
            stockGroups: () => [],
            membership: () => null,
        });
        f.hasAlertOnly.value = true;
        expect(names(f)).toEqual(['X']);
    });
});

// ── Sorting ─────────────────────────────────────────────────────────────

describe('useStockFilters — sorting', () => {
    it('name_desc reverses the alphabetical order', () => {
        const f = makeFilters();
        f.sortBy.value = 'name_desc';
        expect(names(f)).toEqual(['Flour', 'Egg', 'Dill', 'Cheese', 'Bread', 'Apple']);
    });

    it('level_lowest puts the most-depleted items first, ties broken by name', () => {
        const f = makeFilters();
        f.sortBy.value = 'level_lowest';
        expect(names(f)).toEqual(['Cheese', 'Bread', 'Flour', 'Apple', 'Dill', 'Egg']);
    });

    it('level_highest puts the best-stocked items first', () => {
        const f = makeFilters();
        f.sortBy.value = 'level_highest';
        expect(names(f)).toEqual(['Apple', 'Dill', 'Egg', 'Bread', 'Flour', 'Cheese']);
    });

    it('updated_recent orders by last stock-level touch, newest first', () => {
        const f = makeFilters();
        f.sortBy.value = 'updated_recent';
        // Bread (07-09) > Flour (07-05) > Apple (07-01) > the never-updated.
        expect(names(f).slice(0, 3)).toEqual(['Bread', 'Flour', 'Apple']);
    });

    it('expiry_asc puts nearest expiry first and items without a date last', () => {
        const f = makeFilters();
        f.sortBy.value = 'expiry_asc';
        expect(names(f).slice(0, 2)).toEqual(['Egg', 'Dill']);
        // No-expiry items follow, ordered by least-recently-updated then name:
        // Apple (07-01) < Flour (07-05) < Bread (07-09) — wait, Bread has a
        // date; remaining are Apple, Bread, Cheese, Flour. Bread(07-09) >
        // Flour(07-05) > Apple(07-01); Cheese has no update date → first.
        expect(names(f).slice(2)).toEqual(['Cheese', 'Apple', 'Flour', 'Bread']);
    });
});

// ── Summaries, counts, and helpers ──────────────────────────────────────

describe('useStockFilters — summaries and helpers', () => {
    it('summaryCounts totals low / out / essentials / open across ALL items', () => {
        const f = makeFilters();
        expect(f.summaryCounts.value).toEqual({ low: 2, out: 1, essentials: 2, open: 1 });
    });

    it('countByLevel maps level id → item count', () => {
        const f = makeFilters();
        expect(f.countByLevel.value.get('lv-stocked')).toBe(3);
        expect(f.countByLevel.value.get('lv-low')).toBe(2);
        expect(f.countByLevel.value.get('lv-out')).toBe(1);
    });

    it('location options render full "parent › child" paths, alphabetically', () => {
        const f = makeFilters();
        expect(f.allLocationOptions.value).toEqual([
            { label: 'Pantry', value: 'loc-pantry' },
            { label: 'Pantry › Middle shelf', value: 'loc-shelf' },
        ]);
    });

    it('filterLocations narrows the searchable options and restores on empty', () => {
        const f = makeFilters();
        const runNow = (cb: () => void) => cb();
        f.filterLocations('shelf', runNow);
        expect(f.locationOptions.value).toEqual([
            { label: 'Pantry › Middle shelf', value: 'loc-shelf' },
        ]);
        f.filterLocations('', runNow);
        expect(f.locationOptions.value).toHaveLength(2);
    });

    it('activeFilterCount counts set filters but never the search text', () => {
        const f = makeFilters();
        f.searchText.value = 'milk';
        expect(f.activeFilterCount.value).toBe(0);
        f.levelFilter.value = 'lv-low';
        f.essentialsOnly.value = true;
        f.cartFilter.value = 'on_list';
        expect(f.activeFilterCount.value).toBe(3);
    });

    it('toggleLevelFilter sets, then clears on the same id', () => {
        const f = makeFilters();
        f.toggleLevelFilter('lv-low');
        expect(f.levelFilter.value).toBe('lv-low');
        f.toggleLevelFilter('lv-low');
        expect(f.levelFilter.value).toBeNull();
        f.toggleLevelFilter('lv-low');
        f.toggleLevelFilter('lv-out');
        expect(f.levelFilter.value).toBe('lv-out');
    });

    it('clearFilters resets every filter and the search box', () => {
        const f = makeFilters();
        f.searchText.value = 'x';
        f.levelFilter.value = 'lv-low';
        f.essentialsOnly.value = true;
        f.openOnly.value = true;
        f.hasAlertOnly.value = true;
        f.expiringSoonOnly.value = true;
        f.cartFilter.value = 'on_list';
        f.recipeFilter.value = 'rcp-pie';

        f.clearFilters();

        expect(names(f)).toHaveLength(6);
        expect(f.activeFilterCount.value).toBe(0);
        expect(f.searchText.value).toBe('');
    });

    it('footerCounts reflect the FILTERED view with shortened level labels', () => {
        const f = makeFilters();
        f.levelFilter.value = 'lv-low';
        const counts = f.footerCounts.value;
        const byLabel = new Map(counts.map((c) => [c.label, c.value]));

        expect(byLabel.get('Shown')).toBe(2); // Bread + Flour
        expect(byLabel.get('Needs attention')).toBe(1); // Bread only (Model C)
        // "Low Stock" / "Out of Stock" are shortened for the sticky row.
        expect(byLabel.get('Low')).toBe(2);
        expect(byLabel.get('Out')).toBe(0);
        expect(byLabel.get('Stocked')).toBe(0);
        expect(byLabel.get('Essential')).toBe(1); // Bread
        expect(byLabel.get('On a list')).toBe(1); // Bread (on two lists → counted once)
    });
});
