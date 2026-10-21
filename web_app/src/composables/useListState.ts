// A8 §3 nav-state policy — filters / search / sort on list pages persist
// within the session and reset on full reload.
//
// Module-level Map holds a bag of refs per scope key. Because the Map
// lives in this module's closure, it survives route changes for the
// life of the SPA tab and is wiped on hard reload (fresh JS bundle,
// fresh module scope). No localStorage — a full reload should feel
// like a clean slate.
//
// Scroll position is handled separately by the router's scrollBehavior
// (Vue Router's savedPosition on browser back/forward).
//
// Usage:
//   const filters = useListState('stock-overview', () => ({
//       searchText: ref(''),
//       sortBy: ref<StockSortKey>('name_asc'),
//       essentialsOnly: ref(false),
//   }));
//   // filters.searchText is a Ref<string> and survives navigation.
//
// The factory only runs on the first `useListState` call per scope; on
// subsequent calls the cached refs are returned directly, preserving
// their values.

const CACHE = new Map<string, unknown>();

export function useListState<T>(scope: string, factory: () => T): T {
    const cached = CACHE.get(scope) as T | undefined;
    if (cached !== undefined) return cached;
    const created = factory();
    CACHE.set(scope, created);
    return created;
}

// Escape hatch for tests and hard-reset UX (e.g. sign-out).
export function clearAllListState(): void {
    CACHE.clear();
}
