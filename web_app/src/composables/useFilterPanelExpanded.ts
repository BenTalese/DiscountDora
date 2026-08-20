import { ref, watch } from 'vue';

/**
 * Filter-panel expanded state, shared between `FilterToggleButton` (in a
 * page's toolbar) and `FilterBar` (the panel below it).
 *
 * **The rule (owner call 2026-08-20): the panel is open when there is
 * something in it.** Land on a page with filters active — including the
 * filters a page persists across navigation — and the panel is open so you
 * can see what's narrowing the list; land on it with nothing set and the
 * panel is collapsed. Toggling by hand wins for as long as you're on the
 * page, and is forgotten on the way out.
 *
 * This replaces a localStorage-persisted preference (desktop-only, mobile
 * always collapsed). The owner tried both and preferred this one: *"upon
 * playing more with it it seems stock overview is more smart and I prefer it
 * (adopt elsewhere), where it remains open if filters are active otherwise it
 * stays collapsed across navigation to and from the page"*. A remembered
 * "open" with nothing in it is chrome you didn't ask for, and a remembered
 * "closed" hides filters that ARE narrowing what you're looking at — which is
 * the state worth spending screen on.
 *
 * `pageKey` is kept for call-site legibility (and so a page-scoped variation
 * has somewhere to hang); nothing is persisted under it any more.
 */
export function useFilterPanelExpanded(
    pageKey: string,
    /** Live "is anything filtered?" for this page — usually
     *  `() => filters.activeFilterCount.value > 0`. Omit only if the page has
     *  no filter state to read, in which case the panel just starts closed. */
    hasActiveFilters?: () => boolean,
) {
    void pageKey;
    const active = () => (hasActiveFilters ? hasActiveFilters() : false);
    const expanded = ref(active());

    // Filters can arrive a tick or two after setup — a deep-link query param
    // applied on mount, or a persisted filter set restored once its options
    // have hydrated. Open the panel when that happens, but never close it
    // again from here: clearing the last filter usually happens *inside* the
    // open panel, and yanking it shut under the user's cursor is the one
    // behaviour neither variant of this composable ever wanted.
    watch(active, (isActive) => {
        if (isActive) expanded.value = true;
    });

    return expanded;
}
