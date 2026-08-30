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
// choice (a phone and a desktop reasonably want different answers).
// Since 2026-08-29 it is also the *only* photo-density control the
// cookbook has — the `show_recipe_images` preference it used to sit
// beside is cut.
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
