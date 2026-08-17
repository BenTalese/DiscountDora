import { ref, watch } from 'vue';

export type ListViewMode = 'grid' | 'compact';

// Per-page persisted "how do I want this list drawn" preference — the
// card grid, or one row per record (the Stock Overview shape).
//
// Persisted in localStorage rather than session state (`useListState`)
// because the ask was explicitly that the choice is *remembered*: a user
// who prefers dense rows should get dense rows on their next visit, not
// just their next route change. Sibling of `useFilterPanelExpanded`,
// which persists the same way for the same reason.
//
// Deliberately NOT a per-user server setting: it's a device-shaped
// choice (a phone and a desktop reasonably want different answers), and
// `show_recipe_images` — which is a genuine cross-device preference —
// stays where it is on /api/users/me.
export function useListViewMode(pageKey: string, fallback: ListViewMode = 'grid') {
    const storageKey = `dora.listView.${pageKey}`;

    let initial = fallback;
    try {
        const saved = localStorage.getItem(storageKey);
        if (saved === 'grid' || saved === 'compact') initial = saved;
    } catch {
        // localStorage may be unavailable (private mode) — best effort.
    }
    const mode = ref<ListViewMode>(initial);

    watch(mode, (v) => {
        try {
            localStorage.setItem(storageKey, v);
        } catch {
            // best effort
        }
    });

    return mode;
}
