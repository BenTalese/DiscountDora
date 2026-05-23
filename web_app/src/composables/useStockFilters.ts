import { cartStateFor, type CartState, type Membership } from 'src/models/shoppingList';
import type { Recipe } from 'src/models/recipe';
import type { StockGroup } from 'src/models/stockGroup';
import type { StockItem } from 'src/models/stockItem';
import type { StockLevel } from 'src/models/stockLevel';
import type { StockLocation } from 'src/services/api/stockLocationApiService';
import { computed, ref, type DeepReadonly } from 'vue';

export type StockSortKey =
    | 'name_asc'
    | 'name_desc'
    | 'level_lowest'
    | 'level_highest'
    | 'updated_recent'
    | 'updated_oldest';

export type StockCartFilter = 'all' | 'on_list' | 'off_list';

export const STOCK_SORT_OPTIONS: { value: StockSortKey; label: string }[] = [
    { value: 'name_asc', label: 'Name (A-Z)' },
    { value: 'name_desc', label: 'Name (Z-A)' },
    { value: 'level_lowest', label: 'Stock level (lowest first)' },
    { value: 'level_highest', label: 'Stock level (highest first)' },
    { value: 'updated_recent', label: 'Recently updated' },
    { value: 'updated_oldest', label: 'Stalest first' },
];

/**
 * All filter / sort / summary state for the pantry. Reusable wherever a list
 * of stock items needs the canonical filter UI — currently StockOverview but
 * intended to power any future "find a stock item" picker too.
 */
// Sources are passed as getter functions so the composable stays decoupled
// from where the data lives (pinia stores, props, fixtures in tests). Each
// computed re-reads the getter on track, preserving reactivity. We accept
// DeepReadonly because that's the shape Pinia's storeToRefs exposes.
type ReadList<T> = ReadonlyArray<DeepReadonly<T>>;

export function useStockFilters(sources: {
    stockItems: () => ReadList<StockItem>;
    stockLevels: () => ReadList<StockLevel>;
    stockLocations: () => ReadList<StockLocation>;
    recipes: () => ReadList<Recipe>;
    stockGroups: () => ReadList<StockGroup>;
    membership: () => Membership | null;
}) {
    // ── Raw filter state ────────────────────────────────────────────────
    const searchText = ref('');
    const levelFilter = ref<string | null>(null);
    const locationFilter = ref<string | null>(null);
    const groupFilter = ref<string | null>(null);
    const essentialsOnly = ref(false);
    const openOnly = ref(false);
    const hasAlertOnly = ref(false);
    const usedInRecipeOnly = ref(false);
    const cartFilter = ref<StockCartFilter>('all');
    const sortBy = ref<StockSortKey>('name_asc');

    // ── Lookup maps ─────────────────────────────────────────────────────
    const stockLevelById = computed(() => {
        const map = new Map<string, StockLevel>();
        for (const l of sources.stockLevels()) map.set(l.stock_level_id, l);
        return map;
    });
    function stockLevelName(id: string | null): string {
        if (!id) return '';
        return stockLevelById.value.get(id)?.name ?? '';
    }

    const levelSequenceById = computed(() => {
        const map = new Map<string, number>();
        for (const l of sources.stockLevels())
            map.set(l.stock_level_id, l.sequence ?? 0);
        return map;
    });
    function levelSequence(id: string | null): number {
        if (!id) return -1;
        return levelSequenceById.value.get(id) ?? -1;
    }

    // ── Cross-feature indexes ───────────────────────────────────────────
    const recipesByStockItem = computed(() => {
        const map = new Map<string, { recipe_id: string; name: string }[]>();
        for (const r of sources.recipes()) {
            const seen = new Set<string>();
            for (const ing of r.ingredients) {
                if (seen.has(ing.stock_item_id)) continue;
                seen.add(ing.stock_item_id);
                const arr = map.get(ing.stock_item_id) ?? [];
                arr.push({ recipe_id: r.recipe_id, name: r.name });
                map.set(ing.stock_item_id, arr);
            }
        }
        return map;
    });

    const cartStateById = computed(() => {
        const map = new Map<string, CartState>();
        const m = sources.membership();
        for (const item of sources.stockItems()) {
            map.set(item.stock_item_id, cartStateFor(item.stock_item_id, m));
        }
        return map;
    });

    // ── Per-item attention check (low/out/expiring/flagged) ─────────────
    function isExpiringSoon(item: StockItem): boolean {
        if (!item.expiry_date) return false;
        const days = (new Date(item.expiry_date).getTime() - Date.now()) / 86_400_000;
        return days <= 7;
    }
    function hasAlert(item: StockItem): boolean {
        const n = stockLevelName(item.stock_level_id);
        return (
            n === 'Low Stock' ||
            n === 'Out of Stock' ||
            isExpiringSoon(item) ||
            item.is_flagged === true
        );
    }

    // ── Dropdown option lists ───────────────────────────────────────────
    const locationOptions = computed(() =>
        sources.stockLocations().map((l) => ({
            label: l.name,
            value: l.stock_location_id,
        })),
    );
    const groupOptions = computed(() =>
        sources.stockGroups().map((g) => ({
            label: g.name,
            value: g.stock_group_id,
        })),
    );

    // ── Summary counts (header banner) ──────────────────────────────────
    const summaryCounts = computed(() => {
        let low = 0;
        let out = 0;
        let essentials = 0;
        let open = 0;
        for (const item of sources.stockItems()) {
            const name = stockLevelName(item.stock_level_id);
            if (name === 'Low Stock') low++;
            if (name === 'Out of Stock') out++;
            if (item.is_flagged) essentials++;
            if (item.is_open) open++;
        }
        return { low, out, essentials, open };
    });

    const countByLevel = computed(() => {
        const map = new Map<string, number>();
        for (const item of sources.stockItems()) {
            if (!item.stock_level_id) continue;
            map.set(item.stock_level_id, (map.get(item.stock_level_id) ?? 0) + 1);
        }
        return map;
    });

    // ── Filtered + sorted output ────────────────────────────────────────
    const filteredStockItems = computed(() => {
        const tokens = (searchText.value ?? '')
            .trim()
            .toLowerCase()
            .split(/\s+/)
            .filter((t) => t.length > 0);

        const matches = sources.stockItems().filter((item) => {
            if (levelFilter.value && item.stock_level_id !== levelFilter.value) return false;
            if (locationFilter.value && item.stock_location_id !== locationFilter.value)
                return false;
            if (groupFilter.value && item.stock_group_id !== groupFilter.value) return false;
            if (essentialsOnly.value && !item.is_flagged) return false;
            if (openOnly.value && !item.is_open) return false;
            if (hasAlertOnly.value && !hasAlert(item)) return false;
            if (
                usedInRecipeOnly.value
                && (recipesByStockItem.value.get(item.stock_item_id)?.length ?? 0) === 0
            ) {
                return false;
            }
            if (tokens.length > 0) {
                const haystack = item.name.toLowerCase();
                if (!tokens.some((t) => haystack.includes(t))) return false;
            }
            if (cartFilter.value !== 'all') {
                const state = cartStateById.value.get(item.stock_item_id) ?? 'none';
                const onList = state !== 'none';
                if (cartFilter.value === 'on_list' && !onList) return false;
                if (cartFilter.value === 'off_list' && onList) return false;
            }
            return true;
        });

        const collator = new Intl.Collator('en', { sensitivity: 'base' });
        const sorted = [...matches];
        switch (sortBy.value) {
            case 'name_desc':
                sorted.sort((a, b) => collator.compare(b.name, a.name));
                break;
            case 'level_lowest':
                sorted.sort(
                    (a, b) =>
                        levelSequence(b.stock_level_id) - levelSequence(a.stock_level_id) ||
                        collator.compare(a.name, b.name),
                );
                break;
            case 'level_highest':
                sorted.sort(
                    (a, b) =>
                        levelSequence(a.stock_level_id) - levelSequence(b.stock_level_id) ||
                        collator.compare(a.name, b.name),
                );
                break;
            case 'updated_recent':
                sorted.sort((a, b) =>
                    (b.stock_level_last_updated ?? '').localeCompare(
                        a.stock_level_last_updated ?? '',
                    ),
                );
                break;
            case 'updated_oldest':
                sorted.sort((a, b) =>
                    (a.stock_level_last_updated ?? '').localeCompare(
                        b.stock_level_last_updated ?? '',
                    ),
                );
                break;
            case 'name_asc':
            default:
                sorted.sort((a, b) => collator.compare(a.name, b.name));
                break;
        }
        return sorted;
    });

    // ── Imperative helpers ──────────────────────────────────────────────
    function toggleLevelFilter(id: string) {
        levelFilter.value = levelFilter.value === id ? null : id;
    }
    function clearFilters() {
        searchText.value = '';
        levelFilter.value = null;
        locationFilter.value = null;
        groupFilter.value = null;
        essentialsOnly.value = false;
        openOnly.value = false;
        hasAlertOnly.value = false;
        usedInRecipeOnly.value = false;
        cartFilter.value = 'all';
    }

    return {
        // state
        searchText,
        levelFilter,
        locationFilter,
        groupFilter,
        essentialsOnly,
        openOnly,
        hasAlertOnly,
        usedInRecipeOnly,
        cartFilter,
        sortBy,
        // option lists
        locationOptions,
        groupOptions,
        // derived
        summaryCounts,
        countByLevel,
        filteredStockItems,
        // helpers
        toggleLevelFilter,
        clearFilters,
    };
}
