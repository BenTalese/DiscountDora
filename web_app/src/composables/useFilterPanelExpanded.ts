import { ref, watch } from 'vue';
import { useQuasar } from 'quasar';

// FU-121 — per-page persisted filter-panel expanded state shared between
// FilterToggleButton (in the page toolbar) and FilterBar (the panel
// below). Persists across reloads via localStorage so a user who likes
// the panel open on Stock Overview gets it back on next visit. Mobile
// (`<md`) always starts hidden regardless of saved state, and toggles on
// mobile do NOT update the persisted value — toolbar real-estate is too
// tight to default-open there, and the desktop preference is what we
// want to remember.
export function useFilterPanelExpanded(pageKey: string) {
    const $q = useQuasar();
    const storageKey = `dora.filterPanel.expanded.${pageKey}`;
    const isMobile = () => $q.screen.lt.md;

    let initial = false;
    if (!isMobile()) {
        try {
            initial = localStorage.getItem(storageKey) === '1';
        } catch {
            // localStorage may be unavailable (private mode) — best effort.
        }
    }
    const expanded = ref(initial);

    watch(expanded, (v) => {
        if (isMobile()) return;
        try {
            localStorage.setItem(storageKey, v ? '1' : '0');
        } catch {
            // best effort
        }
    });

    return expanded;
}
