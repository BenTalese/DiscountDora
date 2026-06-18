import {
    isLowStockSequence,
    isOutOfStockSequence,
    OUT_OF_STOCK_SEQUENCE,
    SUFFICIENT_STOCK_SEQUENCE,
    LOW_STOCK_SEQUENCE,
    WELL_STOCKED_SEQUENCE,
} from 'src/helpers/stockStatus';
import type { PageCount } from 'src/components/PageCountsFooter.vue';
import { cartStateFor, type CartState, type Membership } from 'src/models/shoppingList';
import type { Recipe } from 'src/models/recipe';
import type { StockGroup } from 'src/models/stockGroup';
import type { StockItem } from 'src/models/stockItem';
import type { LocationNode } from 'src/models/location';
import type { StockLevel } from 'src/models/stockLevel';
import { computed, ref, watch, type DeepReadonly } from 'vue';

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
    locationTree: () => ReadList<LocationNode>;
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
    // X5 — "items that will silently jump onto my list when low". Surfaced
    // as its own chip so users can audit / find auto-add-prone items.
    const autoAddOnly = ref(false);
    const cartFilter = ref<StockCartFilter>('all');
    const sortBy = ref<StockSortKey>('name_asc');

    // ── Lookup maps ─────────────────────────────────────────────────────
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

    const cartStateById = computed(() => {
        const map = new Map<string, CartState>();
        const m = sources.membership();
        for (const item of sources.stockItems()) {
            map.set(item.stock_item_id, cartStateFor(item.stock_item_id, m));
        }
        return map;
    });

    // ── Per-item attention check ────────────────────────────────────────
    // Model C (2026-06-18 round 8): the "Needs attention" count and the
    // row outline share ONE rule so the user can trust the highlighting
    // matches the count. Two tiers with unified meaning:
    //   • WARN (amber): essential AND Low, OR expiring within 7 days.
    //   • ALERT (red):  essential AND Out, OR already expired.
    // Anything that hits either tier is "needing attention". Non-essential
    // Low/Out is intentionally silent — Dora caring about everything is
    // worse than caring loudly about the things you flagged.
    function isExpiringSoon(item: StockItem): boolean {
        if (!item.expiry_date) return false;
        const days = (new Date(item.expiry_date).getTime() - Date.now()) / 86_400_000;
        return days > 0 && days <= 7;
    }
    function isExpired(item: StockItem): boolean {
        if (!item.expiry_date) return false;
        return new Date(item.expiry_date).getTime() < Date.now();
    }
    function hasAlert(item: StockItem): boolean {
        const seq = levelSequence(item.stock_level_id);
        const isLow = item.is_low_stock ?? isLowStockSequence(seq);
        const isOut = item.is_out_of_stock ?? isOutOfStockSequence(seq);
        const isEssential = item.is_flagged === true;
        return (isEssential && (isLow || isOut)) || isExpired(item) || isExpiringSoon(item);
    }

    // ── Dropdown option lists ───────────────────────────────────────────
    // Full-path location labels ("Pantry › Middle shelf › Left side"), built
    // once from the tree. `allLocationOptions` is the canonical full list
    // (consumers that need the unfiltered set — e.g. the bulk-move dialog —
    // read this); `locationOptions` is the narrowing ref bound to the
    // searchable q-select via `filterLocations` (same UX as the detail page).
    type LocationOption = { label: string; value: string };
    const allLocationOptions = computed<LocationOption[]>(() => {
        const out: LocationOption[] = [];
        const walk = (nodes: ReadList<LocationNode>, prefix: string) => {
            for (const n of nodes) {
                const path = prefix ? `${prefix} › ${n.name}` : n.name;
                out.push({ label: path, value: n.location_id });
                walk(n.children, path);
            }
        };
        walk(sources.locationTree(), '');
        return out.sort((a, b) => a.label.localeCompare(b.label));
    });
    const locationOptions = ref<LocationOption[]>([]);
    watch(allLocationOptions, (v) => { locationOptions.value = v; }, { immediate: true });
    function filterLocations(val: string, update: (cb: () => void) => void) {
        update(() => {
            const needle = val.toLowerCase();
            locationOptions.value = needle
                ? allLocationOptions.value.filter((o) => o.label.toLowerCase().includes(needle))
                : allLocationOptions.value;
        });
    }
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
            const seq =
                item.stock_level_sequence ?? levelSequence(item.stock_level_id);
            if (item.is_low_stock ?? isLowStockSequence(seq)) low++;
            if (item.is_out_of_stock ?? isOutOfStockSequence(seq)) out++;
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
            // A4: explicit "empty = off". A blank/null selection must skip the
            // predicate entirely, never exclude rows. (Was relying on
            // truthiness, which would break if a default were ever non-null.)
            if (levelFilter.value !== null && item.stock_level_id !== levelFilter.value)
                return false;
            if (locationFilter.value !== null && item.stock_location_id !== locationFilter.value)
                return false;
            if (groupFilter.value !== null && item.stock_group_id !== groupFilter.value)
                return false;
            if (essentialsOnly.value && !item.is_flagged) return false;
            if (autoAddOnly.value && !item.auto_add_when_low) return false;
            if (openOnly.value && !item.is_open) return false;
            if (hasAlertOnly.value && !hasAlert(item)) return false;
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

    // ── Active-filter count (for the FilterBar badge; excludes search) ──
    const activeFilterCount = computed(() => {
        let n = 0;
        if (levelFilter.value !== null) n++;
        if (locationFilter.value !== null) n++;
        if (groupFilter.value !== null) n++;
        if (essentialsOnly.value) n++;
        if (autoAddOnly.value) n++;
        if (openOnly.value) n++;
        if (hasAlertOnly.value) n++;
        if (cartFilter.value !== 'all') n++;
        return n;
    });

    // ── Sticky-footer counts (A7) — reflect the FILTERED view ───────────
    // Feedback 2026-06-18 (round 2): the footer level palette now mirrors
    // the picker palette in `stockLevelLogic.colourForSequence` exactly:
    // Well-stocked = positive (green), Sufficient = warning (yellow),
    // Low = negative (red), Out = muted (grey). Anything else maps to
    // muted so a renamed/custom level reads consistently with the picker.
    function toneForLevelSequence(seq: number): NonNullable<PageCount['tone']> {
        switch (seq) {
            case WELL_STOCKED_SEQUENCE: return 'positive';
            case SUFFICIENT_STOCK_SEQUENCE: return 'warning';
            case LOW_STOCK_SEQUENCE: return 'negative';
            case OUT_OF_STOCK_SEQUENCE: return 'muted';
            default: return 'muted';
        }
    }
    const footerCounts = computed<PageCount[]>(() => {
        const items = filteredStockItems.value;
        const byLevel = new Map<string, number>();
        const cartMap = cartStateById.value;
        let flagged = 0;
        let autoAdd = 0;
        let attention = 0;
        let onAnyList = 0;
        for (const it of items) {
            if (it.stock_level_id)
                byLevel.set(it.stock_level_id, (byLevel.get(it.stock_level_id) ?? 0) + 1);
            if (it.is_flagged) flagged++;
            if (it.auto_add_when_low) autoAdd++;
            if (hasAlert(it)) attention++;
            // Round-10: count items present on at least one active shopping
            // list — once per item, not per line/list. Anything other than
            // `none` qualifies (on_target / on_other / on_multiple).
            if ((cartMap.get(it.stock_item_id) ?? 'none') !== 'none') onAnyList++;
        }
        // C-1 Chunk 2 / L93 — minified labels; matches the plan's order
        // Shown · Well-stocked · Sufficient · Low · Out · Flagged ·
        // Auto-add · Needs-attention. Stock-level names are shortened
        // for the chip ("Sufficient Stock" → "Sufficient", "Low Stock"
        // → "Low", "Out of Stock" → "Out") so they fit in a single
        // sticky row.
        const shortLabel = (name: string): string =>
            name
                .replace(/\bWell-Stocked\b/i, 'Well-stocked')
                .replace(/\bSufficient Stock\b/i, 'Sufficient')
                .replace(/\bLow Stock\b/i, 'Low')
                .replace(/\bOut of Stock\b/i, 'Out');
        // `hideOnMobile: true` on the level + essential + auto-add stats:
        // narrow viewports get only Shown + Needs attention so the
        // sticky footer doesn't eat vertical space (round-6 feedback).
        const levelStats: PageCount[] = sources.stockLevels().map((l) => ({
            label: shortLabel(l.name),
            value: byLevel.get(l.stock_level_id) ?? 0,
            tone: toneForLevelSequence(l.sequence),
            group: 'levels' as const,
            hideOnMobile: true,
        }));
        // Feedback 2026-06-18 (round 2):
        //   • "Shown" stays neutral (default text colour).
        //   • Essential keeps the warning tone (same colour as the row
        //     stripe + flag icon).
        //   • Auto-add now reads neutral — it's an *info* count, not a
        //     status. Matches the "Shown" tone the user asked for.
        //   • Order is Essential → Auto-add → Needs attention (Essential
        //     above Auto-add per the feedback).
        //   • Label is "Essential" (not "Flagged") so the wording stays
        //     consistent with the field on the detail page + the row's
        //     tooltip + the filter chip.
        // `group` drives PageCountsFooter's three-cluster justify-evenly
        // layout: [Shown] · [stock levels] · [other counts].
        return [
            { label: 'Shown', value: items.length, group: 'shown' as const },
            ...levelStats,
            { label: 'Essential', value: flagged, tone: 'warning' as const, group: 'other' as const, hideOnMobile: true },
            { label: 'Auto-add', value: autoAdd, group: 'other' as const, hideOnMobile: true },
            { label: 'On a list', value: onAnyList, group: 'other' as const, hideOnMobile: true },
            { label: 'Needs attention', value: attention, tone: 'negative' as const, group: 'other' as const },
        ];
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
        autoAddOnly.value = false;
        openOnly.value = false;
        hasAlertOnly.value = false;
        cartFilter.value = 'all';
    }

    return {
        // state
        searchText,
        levelFilter,
        locationFilter,
        groupFilter,
        essentialsOnly,
        autoAddOnly,
        openOnly,
        hasAlertOnly,
        cartFilter,
        sortBy,
        // option lists
        locationOptions,
        allLocationOptions,
        filterLocations,
        groupOptions,
        // derived
        summaryCounts,
        countByLevel,
        filteredStockItems,
        activeFilterCount,
        footerCounts,
        // helpers
        toggleLevelFilter,
        clearFilters,
    };
}
