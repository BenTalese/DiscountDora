/**
 * Tiny utility for the temporary A/B view toggle on the meal planner
 * (IMPL_PLAN_MEAL_PLANS_REBUILD §8.2). One source of truth for whether the
 * user prefers Direction A (`list`, the vertical-carousel page at
 * `/meal-plans`) or Direction B (`grid`, the week-board page at
 * `/meal-plans/board`). Persisted to localStorage so refresh keeps the
 * choice; an explicit `?view=` query param overrides storage so links can
 * pin a layout.
 *
 * The whole module is deleted in the "later — pick a winner" phase along
 * with whichever page lost.
 */

export type PlannerView = 'list' | 'grid';

const STORAGE_KEY = 'dora.meal-planner.view';

export function readStoredPlannerView(): PlannerView | null {
    try {
        const raw = window.localStorage.getItem(STORAGE_KEY);
        if (raw === 'list' || raw === 'grid') return raw;
    } catch {
        // Private mode / disabled storage — fall through to the page default.
    }
    return null;
}

export function setPlannerView(view: PlannerView): void {
    try {
        window.localStorage.setItem(STORAGE_KEY, view);
    } catch {
        // Swallow — persistence is best-effort, the URL still carries intent.
    }
}

/**
 * Resolve which view the user wants right now. `?view=` wins, then storage,
 * then the page's own default (so the A page calling this without args still
 * gets `list` back when nothing has been set yet).
 */
export function resolvePlannerView(
    query: Record<string, unknown>,
    pageDefault: PlannerView,
): PlannerView {
    const fromQuery = query['view'];
    if (fromQuery === 'list' || fromQuery === 'grid') return fromQuery;
    return readStoredPlannerView() ?? pageDefault;
}
